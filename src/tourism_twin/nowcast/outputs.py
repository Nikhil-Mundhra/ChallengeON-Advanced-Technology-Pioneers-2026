"""Business outputs derived from the guest model (stock-flow plan step 8), as one JSON document.

Per market and test week: forecast, p10/p90, direction to the next week with a probability,
year-on-year change, and the calendar drivers; per market: implied mean stay and short-stay share
from the fitted survival curve, with the base-stock share that the curve does not explain.
Narration (briefings, LLM text) reads this document only and never computes numbers.

Weekly uncertainty comes from the daily noise model: a week's log error is the forecast-weighted
mean of its daily log errors, and daily errors are AR(1) with the market's phi, so
cov(e_i, e_j) = sd_i * sd_j * phi^|i - j| within and across weeks. The direction probability uses
the variance of the difference of two adjacent weeks' log errors under that covariance.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping

import numpy as np
import pandas as pd
from scipy.stats import norm

from tourism_twin.models.noise import NoiseModel
from tourism_twin.nowcast.predict import TestPredictions

LEVEL_COMPONENTS = {"arrivals", "level", "trend"}
NOT_DRIVERS = {"weekday", "slope"}  # weekday averages ~0 over a week; slope is reported as a trend
MAX_BASE_STOCK_SHARE = 0.25  # above this the survival curve explains too little of the stock to quote
PROB_BUCKETS = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
ASSUMPTIONS = [
    "Direction accuracy is a nowcast skill: the model sees each week's observed new arrivals; compare it with arrivals_direction.",
    "Weekly p10/p90 and direction_prob come from AR(1) daily log errors (per-market phi) fitted on the rolling-origin back-test.",
    "short_stay_share = 1 - w2 / w0 and implied_mean_stay_days = sum(w) describe the arrivals kernel only; "
    "base_stock_share of the training stock is outside it, and both are null when that share exceeds 0.25.",
    "top_drivers are season and event effects as % of an average day; trend_vs_training_pct is the fitted slope "
    "relative to the training mean, extrapolated.",
]


def _week_start(dates: pd.Series) -> pd.Series:
    dates = pd.to_datetime(dates)
    return (dates - pd.to_timedelta(dates.dt.dayofweek, unit="D")).dt.normalize()


def _sign(values: pd.Series) -> pd.Series:
    return np.sign(values).replace(0, np.nan)


def _block_cov(w_a: np.ndarray, sd_a: np.ndarray, w_b: np.ndarray, sd_b: np.ndarray, phi: float, lag: int) -> float:
    """Covariance of the weighted mean log errors of two 7-day blocks `lag` days apart."""
    i = np.arange(7)
    corr = phi ** np.abs(lag + i[None, :] - i[:, None])
    return float((w_a * sd_a) @ corr @ (w_b * sd_b))


def weekly_forecast(market_daily: pd.DataFrame, phi: Mapping[str, float], coverage: float = 0.8) -> pd.DataFrame:
    """Full Monday-Sunday weeks per market: forecast, bounds, direction to the next week.
    market_daily: market, date, pred, lower, upper (daily `coverage` bounds); phi: daily error
    persistence per market (NoiseModel.phi_)."""
    z = norm.ppf(0.5 + coverage / 2)
    frame = market_daily.assign(week_start=_week_start(market_daily["date"]),
                                sd=np.log(market_daily["upper"] / market_daily["pred"]) / z).sort_values(["market", "date"])
    rows: List[Dict[str, Any]] = []
    for market, group in frame.groupby("market"):
        if market not in phi:
            raise ValueError(f"no error persistence (phi) for market {market!r}")
        weeks = [(start, days) for start, days in group.groupby("week_start") if len(days) == 7]
        for k, (start, days) in enumerate(weeks):
            pred, sd = days["pred"].to_numpy(float), days["sd"].to_numpy(float)
            w = pred / pred.sum()
            var = _block_cov(w, sd, w, sd, phi[market], 0)
            row = {"market": market, "week_start": start, "forecast": pred.sum(),
                   "p10": pred.sum() * np.exp(-z * np.sqrt(var)), "p90": pred.sum() * np.exp(z * np.sqrt(var)),
                   "direction": None, "direction_prob": np.nan}
            if k + 1 < len(weeks) and weeks[k + 1][0] - start == pd.Timedelta(7, unit="D"):
                nxt = weeks[k + 1][1]
                pred_n, sd_n = nxt["pred"].to_numpy(float), nxt["sd"].to_numpy(float)
                w_n = pred_n / pred_n.sum()
                var_diff = var + _block_cov(w_n, sd_n, w_n, sd_n, phi[market], 0) - 2 * _block_cov(w, sd, w_n, sd_n, phi[market], 7)
                step = np.log(pred_n.sum() / pred.sum())
                prob_up = norm.cdf(step / np.sqrt(max(var_diff, 1e-12)))
                row["direction"] = "increase" if step >= 0 else "decrease"
                row["direction_prob"] = prob_up if step >= 0 else 1 - prob_up
            rows.append(row)
    return pd.DataFrame(rows, columns=["market", "week_start", "forecast", "p10", "p90", "direction", "direction_prob"])


def direction_backtest(backtest_predictions: pd.DataFrame, history: pd.DataFrame, noise: NoiseModel,
                       coverage: float = 0.8) -> Dict[str, Any]:
    """Week-to-week direction on the back-test folds, each market-week scored once (from the
    earliest origin that forecasts it, i.e. the longest horizon). Baselines: the direction of the
    week's observed new arrivals, the same weeks a year earlier, and each market's most common
    training direction. Also the reliability of direction_prob and the weekly band coverage; the
    noise model is fitted on these same folds, so both are in-sample for the error model."""
    by_week = history.assign(week_start=_week_start(history["date"])).groupby(["market", "week_start"])
    actual_weekly = by_week["guests"].agg(["sum", "size"])
    actual_weekly = actual_weekly[actual_weekly["size"] == 7]["sum"]
    arrivals_weekly = by_week["new_arrivals_filled"].sum()
    rows: List[pd.DataFrame] = []
    for fold, group in backtest_predictions.groupby("fold"):
        origin = group["origin"].iloc[0]
        daily = group.join(noise.intervals(group, coverage))
        weekly = weekly_forecast(daily, noise.phi_, coverage)
        actual = (group.assign(week_start=_week_start(group["date"])).groupby(["market", "week_start"])["actual"]
                  .agg(["sum", "size"]))
        weekly = weekly.join(actual, on=["market", "week_start"])
        weekly = weekly[weekly["size"] == 7].drop(columns="size").rename(columns={"sum": "actual"})
        g = weekly.groupby("market")
        weekly["pred_dir"] = weekly["direction"].map({"increase": 1.0, "decrease": -1.0})
        weekly["actual_dir"] = _sign(g["actual"].shift(-1) - weekly["actual"])
        this_week = pd.MultiIndex.from_frame(weekly[["market", "week_start"]])
        next_week = pd.MultiIndex.from_arrays([weekly["market"], weekly["week_start"] + pd.Timedelta(7, unit="D")])
        weekly["arrivals_dir"] = _sign(pd.Series(arrivals_weekly.reindex(next_week).to_numpy()
                                                 - arrivals_weekly.reindex(this_week).to_numpy(), index=weekly.index))
        last_year = pd.MultiIndex.from_arrays([weekly["market"], weekly["week_start"] - pd.Timedelta(364, unit="D")])
        next_last_year = pd.MultiIndex.from_arrays([weekly["market"], weekly["week_start"] - pd.Timedelta(357, unit="D")])
        weekly["last_year_dir"] = _sign(pd.Series(actual_weekly.reindex(next_last_year).to_numpy()
                                                  - actual_weekly.reindex(last_year).to_numpy(), index=weekly.index))
        train = actual_weekly[actual_weekly.index.get_level_values("week_start") + pd.Timedelta(6, unit="D") < origin]
        train_dir = _sign(train.groupby(level="market").diff())
        majority = train_dir.groupby(level="market").agg(lambda s: 1.0 if (s > 0).sum() >= (s < 0).sum() else -1.0)
        weekly["majority_dir"] = weekly["market"].map(majority)
        weekly["covered"] = (weekly["actual"] >= weekly["p10"]) & (weekly["actual"] <= weekly["p90"])
        rows.append(weekly.assign(origin=origin))
    every = pd.concat(rows, ignore_index=True)
    coverage_rate = float(every.sort_values("origin").drop_duplicates(["market", "week_start"])["covered"].mean())
    scored = (every.dropna(subset=["pred_dir", "actual_dir"]).sort_values("origin")
              .drop_duplicates(["market", "week_start"]))
    accuracy = {name: float((scored[column] == scored["actual_dir"]).mean())
                for name, column in (("model", "pred_dir"), ("arrivals_direction", "arrivals_dir"),
                                     ("same_direction_as_last_year", "last_year_dir"),
                                     ("majority_direction", "majority_dir"))}
    hit = scored["pred_dir"] == scored["actual_dir"]
    bucket = pd.cut(scored["direction_prob"], PROB_BUCKETS, include_lowest=True)
    reliability = [{"prob_range": f"{interval.left:.1f}-{interval.right:.1f}", "weeks": int(len(hits)),
                    "mean_prob": round(float(scored.loc[hits.index, "direction_prob"].mean()), 3),
                    "share_right": round(float(hits.mean()), 3)}
                   for interval, hits in hit.groupby(bucket, observed=True)]
    return {"weeks_scored": int(len(scored)), "accuracy": accuracy, "direction_prob_reliability": reliability,
            "weekly_band_coverage": coverage_rate}


def build_outputs(predictions: TestPredictions, history: pd.DataFrame, spec: str, coverage: float = 0.8) -> Dict[str, Any]:
    """The JSON document: assumptions, the direction back-test, and per-market weekly outputs.
    history: the daily training panel (guests, new_arrivals_filled)."""
    if predictions.noise is None:
        raise ValueError("build_outputs needs predictions with intervals (a fitted noise model)")
    weekly = weekly_forecast(predictions.market_daily, predictions.noise.phi_, coverage)
    actual_weekly = (history.assign(week_start=_week_start(history["date"]))
                     .groupby(["market", "week_start"])["guests"].sum(min_count=7))
    explain = predictions.model.explain() if predictions.model is not None else {}
    markets: Dict[str, Any] = {}
    for market, rows in weekly.groupby("market"):
        markets[market] = {**_stay(explain.get(market, {}).get("arrivals", {})), "weeks": [
            {
                "week_start": str(record.week_start.date()),
                "forecast": round(float(record.forecast), 1),
                "p10": round(float(record.p10), 1) if np.isfinite(record.p10) else None,
                "p90": round(float(record.p90), 1) if np.isfinite(record.p90) else None,
                "direction": record.direction,
                "direction_prob": round(float(record.direction_prob), 3) if np.isfinite(record.direction_prob) else None,
                "yoy_change": _yoy(record.forecast, actual_weekly.get((market, record.week_start - pd.Timedelta(364, unit="D")), np.nan)),
            }
            for record in rows.itertuples()
        ]}
    _attach_drivers(markets, predictions)
    document: Dict[str, Any] = {"spec": spec, "coverage": coverage, "assumptions": ASSUMPTIONS, "markets": markets}
    if predictions.backtest_predictions is not None:
        document["direction_backtest"] = direction_backtest(predictions.backtest_predictions, history, predictions.noise, coverage)
    return document


def _stay(arrivals: Dict[str, Any]) -> Dict[str, Any]:
    survival, base_share = arrivals.get("survival_w"), arrivals.get("base_stock_share")
    quotable = bool(survival) and survival[0] > 0 and base_share is not None and base_share <= MAX_BASE_STOCK_SHARE
    return {
        "base_stock_share": round(float(base_share), 3) if base_share is not None else None,
        "implied_mean_stay_days": round(float(np.sum(survival)), 2) if quotable else None,
        "short_stay_share": round(float(1 - survival[2] / survival[0]), 3) if quotable else None,
    }


def _yoy(forecast: float, last_year: float) -> float | None:
    return round(float(forecast / last_year - 1), 4) if np.isfinite(last_year) and last_year > 0 else None


def _attach_drivers(markets: Dict[str, Any], predictions: TestPredictions, top: int = 3) -> None:
    """Per week: season and event effects (mean log contribution over the week, as %), largest
    first, and the slope separately as trend_vs_training_pct."""
    model = predictions.model
    if model is None or not hasattr(model, "decompose"):
        return
    from tourism_twin.data.daily_panel import build_daily_panel

    panel = build_daily_panel()
    test = panel[panel["dataset_split"] == "test"]
    parts = model.decompose(test)
    parts = parts[[c for c in parts.columns if c not in LEVEL_COMPONENTS]]
    parts = parts.assign(market=test["market"].to_numpy(), week_start=_week_start(test["date"]).to_numpy())
    weekly = parts.groupby(["market", "week_start"]).mean()
    for market, detail in markets.items():
        for week in detail["weeks"]:
            key = (market, pd.Timestamp(week["week_start"]))
            effects = weekly.loc[key].dropna() if key in weekly.index else pd.Series(dtype=float)
            if "slope" in effects:
                week["trend_vs_training_pct"] = round(float(np.expm1(effects["slope"])) * 100, 1)
            effects = effects.drop([c for c in NOT_DRIVERS if c in effects])
            effects = effects[np.abs(np.expm1(effects)) >= 0.005]  # drop effects below 0.5%
            ranked = effects.reindex(effects.abs().sort_values(ascending=False).index)[:top]
            week["top_drivers"] = [{"component": name, "effect_pct": round(float(np.expm1(value)) * 100, 1)}
                                   for name, value in ranked.items()]
