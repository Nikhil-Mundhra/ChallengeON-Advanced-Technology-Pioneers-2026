"""Out-of-sample residual checks of link 0: r = log(actual P2P) - log(predicted P2P) on each fold's test
window, at market-day and market-week grain. A market-day in several overlapping folds keeps one
residual per fold for autocorrelation (one series per market and fold) and their mean elsewhere.

1. bias: mean residual per bin of each input and of time, 95% CI clustered on market x 28-day block;
   a bin is flagged when its CI clears 0 by more than FLAG (log points, about 2%).
2. memory: ACF to lag 28 days / 8 weeks and Ljung-Box per market-fold series.
3. spread: residual sd per quintile of fitted level and of seat deviation.
4. shape: skew, excess kurtosis, share beyond 3 sd, Q-Q plot.
Passing: check 1 with no flagged bin; check 2 with Ljung-Box p >= 0.05 in at least half of the
weekly market-fold series.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

from tourism_twin.domain.events import DEFAULT_KERNEL_EVENTS, load_event_calendar  # noqa: E402
from tourism_twin.features.events import event_offsets  # noqa: E402

import data  # noqa: E402
from passengers_link import seat_deviation  # noqa: E402

FLAG = 0.02
LAGS = {"day": 28, "week": 8}
LF_BANDS = (0.0, 0.75, 0.85, 0.92, 2.0)


def _usual_lf(panel: pd.DataFrame, train_end: pd.Timestamp) -> pd.Series:
    train = panel[(panel["date"] < train_end) & (panel["seats"] > 0)]
    cells = train.groupby(["market", "season"])
    lf = cells["pax"].sum() / cells["seats"].sum()
    return pd.Series([lf.get(k, np.nan) for k in zip(panel["market"], panel["season"])], index=panel.index)


def daily_residuals(panel: pd.DataFrame, runs: List[dict]) -> pd.DataFrame:
    """One row per fold x test market-day with positive actual and predicted P2P."""
    deviation = seat_deviation(panel)
    event_day = event_offsets(panel["date"], load_event_calendar(), DEFAULT_KERNEL_EVENTS).notna().any(axis=1)
    rows = []
    for i, run in enumerate(runs):
        fold = run["fold"]
        inside = (panel["date"] >= fold.test_start) & (panel["date"] <= fold.test_end)
        pred = run["pred"]["p2p"]
        ok = inside & (panel["p2p"] > 0) & (pred > 0)
        part = panel.loc[ok, ["market", "date", "p2p", "seats"]].assign(
            fold=i, pred=pred[ok], resid=np.log(panel.loc[ok, "p2p"] / pred[ok]), deviation=deviation[ok],
            usual_lf=_usual_lf(panel, fold.train_end)[ok], event_day=event_day[ok],
            horizon=((panel.loc[ok, "date"] - fold.test_start).dt.days // 30).clip(upper=5))
        rows.append(part)
    out = pd.concat(rows)
    return out.assign(week_start=data.week_start(out["date"]), month=out["date"].dt.month, weekday=out["date"].dt.weekday,
                      year=out["date"].dt.year, block=(out["date"] - out["date"].min()).dt.days // 28)


def weekly_residuals(daily: pd.DataFrame) -> pd.DataFrame:
    grouped = daily.groupby(["fold", "market", "week_start"])
    weekly = grouped.agg(p2p=("p2p", "sum"), pred=("pred", "sum"), days=("p2p", "size"), deviation=("deviation", "mean"),
                         usual_lf=("usual_lf", "mean"), horizon=("horizon", "min"), block=("block", "min")).reset_index()
    weekly = weekly[weekly["days"] == 7]
    return weekly.assign(resid=np.log(weekly["p2p"] / weekly["pred"]), month=weekly["week_start"].dt.month,
                         year=weekly["week_start"].dt.year)


def _dedupe(frame: pd.DataFrame, keys: List[str]) -> pd.DataFrame:
    """One row per key: the mean over the overlapping folds that scored it."""
    numeric = [c for c in frame.columns if c not in (*keys, "fold") and pd.api.types.is_numeric_dtype(frame[c])]
    out = frame.groupby(keys, as_index=False)[numeric].mean()
    return out.assign(block=out["block"].round())


def _binned(frame: pd.DataFrame, by: pd.Series) -> pd.DataFrame:
    """Mean residual per bin with a cluster-robust (market x 28-day block) 95% CI."""
    rows = []
    for label, part in frame.groupby(by, observed=True):
        mean = part["resid"].mean()
        clusters = (part["resid"] - mean).groupby([part["market"], part["block"]]).sum()
        se = np.sqrt(float(clusters @ clusters)) / len(part)
        rows.append({"bin": str(label), "n": len(part), "mean": mean, "low": mean - 1.96 * se, "high": mean + 1.96 * se})
    out = pd.DataFrame(rows)
    out["flag"] = (out["low"] > FLAG) | (out["high"] < -FLAG)
    return out


def bias_bins(daily: pd.DataFrame, weekly: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    day, week = _dedupe(daily, ["market", "date"]), _dedupe(weekly, ["market", "week_start"])
    edges = np.quantile(day["deviation"].dropna(), np.linspace(0, 1, 6))
    return {
        "day: seat deviation (quintile)": _binned(day, pd.cut(day["deviation"], edges, include_lowest=True)),
        "day: usual LF band": _binned(day, pd.cut(day["usual_lf"], LF_BANDS)),
        "day: month": _binned(day, day["month"].round().astype(int)),
        "day: weekday": _binned(day, day["weekday"].round().astype(int)),
        "day: event window": _binned(day, day["event_day"] > 0.5),
        "day: market": _binned(day, day["market"]),
        "day: year": _binned(day, day["year"].round().astype(int)),
        "day: horizon (months)": _binned(day, day["horizon"].round().astype(int)),
        "week: seat deviation (quintile)": _binned(week, pd.cut(week["deviation"], edges, include_lowest=True)),
        "week: month": _binned(week, week["week_start"].dt.month),
        "week: market": _binned(week, week["market"]),
    }


def _acf(series: np.ndarray, lags: int) -> np.ndarray:
    x = series - series.mean()
    denominator = float(x @ x)
    return np.array([float(x[k:] @ x[:-k]) / denominator for k in range(1, lags + 1)])


def memory(frame: pd.DataFrame, time_column: str, lags: int) -> Dict[str, object]:
    """Pooled ACF (mean over market-fold series, weighted by length) and Ljung-Box per series."""
    acfs, weights, pvalues, q_total, df_total = [], [], [], 0.0, 0
    per_market: Dict[str, List[float]] = {}
    for (market, _), part in frame.sort_values(time_column).groupby(["market", "fold"]):
        x = part["resid"].to_numpy()
        n = len(x)
        if n <= lags + 5:
            continue
        rho = _acf(x, lags)
        q = n * (n + 2) * float(np.sum(rho ** 2 / (n - np.arange(1, lags + 1))))
        p = float(stats.chi2.sf(q, lags))
        acfs.append(rho), weights.append(n), pvalues.append(p)
        per_market.setdefault(market, []).append(p)
        q_total, df_total = q_total + q, df_total + lags
    acf = np.average(np.vstack(acfs), axis=0, weights=weights)
    return {"acf": acf, "share_p_ok": float(np.mean(np.array(pvalues) >= 0.05)), "pooled_p": float(stats.chi2.sf(q_total, df_total)),
            "per_market_share_p_ok": {m: float(np.mean(np.array(v) >= 0.05)) for m, v in per_market.items()}}


def spread(frame: pd.DataFrame) -> Dict[str, pd.Series]:
    level = pd.qcut(np.log(frame["pred"]), 5, labels=False)
    seat = pd.qcut(frame["deviation"], 5, labels=False, duplicates="drop")
    return {"by fitted level": frame.groupby(level)["resid"].std(), "by seat deviation": frame.groupby(seat)["resid"].std()}


def shape(resid: pd.Series) -> Dict[str, float]:
    z = (resid - resid.mean()) / resid.std()
    return {"skew": float(stats.skew(resid)), "excess_kurtosis": float(stats.kurtosis(resid)), "beyond_3sd": float((z.abs() > 3).mean())}


def charts(name: str, bins: Dict[str, pd.DataFrame], mem_day: dict, mem_week: dict, spreads: dict, weekly: pd.DataFrame, folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(3, 4, figsize=(20, 12))
    for ax, (title, table) in zip(axes.ravel(), bins.items()):
        ax.errorbar(range(len(table)), table["mean"], yerr=[table["mean"] - table["low"], table["high"] - table["mean"]], fmt="o")
        ax.axhline(0, color="grey"), ax.axhline(FLAG, ls=":", color="grey"), ax.axhline(-FLAG, ls=":", color="grey")
        ax.set_xticks(range(len(table)), table["bin"], rotation=60, fontsize=6)
        ax.set_title(title, fontsize=9)
    fig.suptitle(f"{name}: link-0 residual by bin (log points, 95% CI)")
    fig.tight_layout(), fig.savefig(folder / f"{name}_bias.png", dpi=80), plt.close(fig)
    fig, axes = plt.subplots(1, 4, figsize=(20, 4))
    axes[0].bar(range(1, LAGS["day"] + 1), mem_day["acf"]), axes[0].set_title("ACF daily")
    axes[1].bar(range(1, LAGS["week"] + 1), mem_week["acf"]), axes[1].set_title("ACF weekly")
    for ax, (title, sd) in zip(axes[2:3], spreads.items()):
        ax.plot(sd.index, sd.to_numpy(), "o-"), ax.set_title(f"sd {title} (weekly)")
    stats.probplot(weekly["resid"], plot=axes[3]), axes[3].set_title("Q-Q weekly")
    fig.tight_layout(), fig.savefig(folder / f"{name}_memory_spread_qq.png", dpi=80), plt.close(fig)


def check(name: str, panel: pd.DataFrame, runs: List[dict], folder: Path) -> Dict[str, object]:
    daily = daily_residuals(panel, runs)
    weekly = weekly_residuals(daily)
    bins = bias_bins(daily, weekly)
    mem_day, mem_week = memory(daily, "date", LAGS["day"]), memory(weekly, "week_start", LAGS["week"])
    spreads = spread(weekly)
    charts(name, bins, mem_day, mem_week, spreads, weekly, folder)
    flagged = [f"{title} = {row.bin} ({row.mean:+.3f})" for title, table in bins.items() for row in table[table["flag"]].itertuples()]
    ratio = {k: float(v.max() / v.min()) for k, v in spreads.items()}
    return {"flagged": flagged, "check1": not flagged, "check2": mem_week["share_p_ok"] >= 0.5,
            "acf_day_1": mem_day["acf"][0], "acf_day_7": mem_day["acf"][6], "acf_week_1": mem_week["acf"][0], "acf_week_4": mem_week["acf"][3],
            "lb_ok_day": mem_day["share_p_ok"], "lb_ok_week": mem_week["share_p_ok"],
            "sd_ratio_level": ratio["by fitted level"], "sd_ratio_seat": ratio["by seat deviation"],
            "day": shape(daily.groupby(["market", "date"])["resid"].mean()), "week": shape(weekly.groupby(["market", "week_start"])["resid"].mean()),
            "bins": bins}
