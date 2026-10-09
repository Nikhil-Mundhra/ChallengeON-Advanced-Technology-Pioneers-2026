"""Business outputs derived from the guest model (stock-flow plan step 8), as one JSON document.

Per market and test week: forecast, p10/p90, direction to the next week with a probability,
year-on-year change, and the calendar drivers; per market: implied mean stay and short-stay share
from the fitted survival curve. Narration (briefings, LLM text) reads this document only and
never computes numbers.

Approximations, stated in the document:
- Weekly bounds are sums of daily bounds (days move together; the error persistence phi is about
  0.9).
- direction_prob treats consecutive weeks as independent, which makes it conservative (closer to
  0.5).
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd
from scipy.stats import norm

from tourism_twin.services.predictions import TestPredictions

LEVEL_COMPONENTS = {"arrivals", "level", "trend"}
ASSUMPTIONS = [
    "Weekly p10/p90 are sums of daily bounds (errors move together across days of a week).",
    "direction_prob assumes independent consecutive weeks, so it is conservative.",
    "short_stay_share = 1 - w2 / w0: the share of arrivals gone after two nights.",
    "top_drivers are the non-level components (calendar, events, trend) relative to the training average or an ordinary day, as % effects.",
]


def _week_start(dates: pd.Series) -> pd.Series:
    dates = pd.to_datetime(dates)
    return (dates - pd.to_timedelta(dates.dt.dayofweek, unit="D")).dt.normalize()


def _sign(values: pd.Series) -> pd.Series:
    return np.sign(values).replace(0, np.nan)


def weekly_forecast(market_daily: pd.DataFrame, coverage: float = 0.8) -> pd.DataFrame:
    """Full Monday-Sunday weeks per market: forecast, bounds, direction to the next week."""
    frame = market_daily.assign(week_start=_week_start(market_daily["date"]))
    weekly = frame.groupby(["market", "week_start"]).agg(days=("pred", "size"), forecast=("pred", "sum"),
                                                         p10=("lower", "sum"), p90=("upper", "sum")).reset_index()
    weekly = weekly[weekly["days"] == 7].drop(columns="days")
    z = norm.ppf(0.5 + coverage / 2)
    sd = np.log(weekly["p90"] / weekly["forecast"]) / z
    step = np.log(weekly.groupby("market")["forecast"].shift(-1)) - np.log(weekly["forecast"])
    sd_next = sd.groupby(weekly["market"]).shift(-1)
    joint_sd = np.sqrt(sd ** 2 + sd_next ** 2)
    weekly["direction"] = np.where(step.isna(), None, np.where(step >= 0, "increase", "decrease"))
    prob_up = norm.cdf(step / joint_sd)
    weekly["direction_prob"] = np.where(step.isna(), np.nan, np.where(step >= 0, prob_up, 1 - prob_up))
    return weekly


def direction_backtest(backtest_predictions: pd.DataFrame, history: pd.DataFrame) -> Dict[str, Any]:
    """Accuracy of the week-to-week direction on back-test folds, against two baselines: the
    same weeks' direction a year earlier, and each market's most common direction in training."""
    actual_weekly = (history.assign(week_start=_week_start(history["date"]))
                     .groupby(["market", "week_start"])["guests"].agg(["sum", "size"]))
    actual_weekly = actual_weekly[actual_weekly["size"] == 7]["sum"]
    rows: List[pd.DataFrame] = []
    for fold, group in backtest_predictions.groupby("fold"):
        origin = group["origin"].iloc[0]
        weekly = (group.assign(week_start=_week_start(group["date"]))
                  .groupby(["market", "week_start"]).agg(pred=("pred", "sum"), actual=("actual", "sum"), days=("pred", "size")))
        weekly = weekly[weekly["days"] == 7].reset_index()
        g = weekly.groupby("market")
        weekly["pred_dir"] = _sign(g["pred"].shift(-1) - weekly["pred"])
        weekly["actual_dir"] = _sign(g["actual"].shift(-1) - weekly["actual"])
        last_year = pd.MultiIndex.from_arrays([weekly["market"], weekly["week_start"] - pd.to_timedelta(364, unit="D")])
        next_last_year = pd.MultiIndex.from_arrays([weekly["market"], weekly["week_start"] - pd.to_timedelta(357, unit="D")])
        weekly["last_year_dir"] = _sign(pd.Series(actual_weekly.reindex(next_last_year).to_numpy() - actual_weekly.reindex(last_year).to_numpy(), index=weekly.index))
        train = actual_weekly[actual_weekly.index.get_level_values("week_start") + pd.to_timedelta(6, unit="D") < origin]
        train_dir = _sign(train.groupby(level="market").diff())
        majority = train_dir.groupby(level="market").agg(lambda s: 1.0 if (s > 0).sum() >= (s < 0).sum() else -1.0)
        weekly["majority_dir"] = weekly["market"].map(majority)
        rows.append(weekly.dropna(subset=["pred_dir", "actual_dir"]))
    scored = pd.concat(rows, ignore_index=True)
    accuracy = {name: float((scored[column] == scored["actual_dir"]).mean())
                for name, column in (("model", "pred_dir"), ("same_direction_as_last_year", "last_year_dir"),
                                     ("majority_direction", "majority_dir"))}
    return {"weeks_scored": int(len(scored)), "accuracy": accuracy}


def build_outputs(predictions: TestPredictions, history: pd.DataFrame, spec: str, coverage: float = 0.8) -> Dict[str, Any]:
    """The JSON document: assumptions, the direction back-test, and per-market weekly outputs."""
    weekly = weekly_forecast(predictions.market_daily, coverage)
    actual_weekly = (history.assign(week_start=_week_start(history["date"]))
                     .groupby(["market", "week_start"])["guests"].sum(min_count=7))
    explain = predictions.model.explain() if predictions.model is not None else {}
    markets: Dict[str, Any] = {}
    for market, rows in weekly.groupby("market"):
        survival = explain.get(market, {}).get("arrivals", {}).get("survival_w")
        stay = {
            "implied_mean_stay_days": float(np.sum(survival)) if survival else None,
            "short_stay_share": float(1 - survival[2] / survival[0]) if survival and survival[0] > 0 else None,
        }
        weeks = []
        for record in rows.itertuples():
            last_year = actual_weekly.get((market, record.week_start - pd.Timedelta(364, unit="D")), np.nan)
            weeks.append({
                "week_start": str(record.week_start.date()),
                "forecast": round(float(record.forecast), 1),
                "p10": round(float(record.p10), 1) if np.isfinite(record.p10) else None,
                "p90": round(float(record.p90), 1) if np.isfinite(record.p90) else None,
                "direction": record.direction,
                "direction_prob": round(float(record.direction_prob), 3) if np.isfinite(record.direction_prob) else None,
                "yoy_change": round(float(record.forecast / last_year - 1), 4) if np.isfinite(last_year) and last_year > 0 else None,
            })
        markets[market] = {**stay, "weeks": weeks}
    _attach_drivers(markets, predictions)
    document: Dict[str, Any] = {"spec": spec, "coverage": coverage, "assumptions": ASSUMPTIONS, "markets": markets}
    if predictions.backtest_predictions is not None:
        document["direction_backtest"] = direction_backtest(predictions.backtest_predictions, history)
    return document


def _attach_drivers(markets: Dict[str, Any], predictions: TestPredictions, top: int = 3) -> None:
    """Top calendar drivers per week: mean log contribution of each non-level component, as %."""
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
            if key not in weekly.index:
                week["top_drivers"] = []
                continue
            effects = weekly.loc[key].dropna()
            ranked = effects.reindex(effects.abs().sort_values(ascending=False).index)[:top]
            week["top_drivers"] = [{"component": name, "effect_pct": round(float(np.expm1(value)) * 100, 1)} for name, value in ranked.items()]
