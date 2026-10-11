"""Lever back-test: test weeks whose seats moved more than 15% against the same week a year earlier.

act = log change of the actual series minus its baseline drift; prd = the same for the prediction.
Baseline drift: median log change over the market's quiet weeks (|seat change| < 5%) of that year
when there are at least MIN_QUIET of them, else the median log change over the market's trailing 52
weeks (two quiet weeks in China 2024 and Oman 2024 flipped Oman's sign). A market-week inside several
overlapping test folds counts once, with its prediction averaged over those folds. `seat_only` is the
model's pure seat response: log(prediction / prediction with the test period on last year's schedule).
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

THRESHOLD = 0.15
QUIET = 0.05
MIN_QUIET = 8
EPISODES = ("OMAN", "KUWAIT", "CHINA", "ISRAEL", "FRANCE")  # every market with 10+ down weeks on daily flight seats


def year_on_year(weekly: pd.DataFrame, column: str) -> pd.DataFrame:
    """Per market-week with a week 364 days earlier: seat change ds and log change of `column`."""
    earlier = weekly[["market", "week_start", "seats", column]].assign(week_start=weekly["week_start"] + pd.Timedelta(days=364))
    out = weekly[["market", "week_start", "seats", column]].merge(earlier, on=["market", "week_start"], suffixes=("", "_ly"))
    out = out[(out["seats"] > 0) & (out["seats_ly"] > 0) & (out[column] > 0) & (out[f"{column}_ly"] > 0)]
    return out.assign(ds=np.log(out["seats"] / out["seats_ly"]), dy=np.log(out[column] / out[f"{column}_ly"]))


def drift(changes: pd.DataFrame, value: str) -> pd.Series:
    """Baseline drift of `value` per row of `changes` (market, week_start, ds)."""
    out = pd.Series(np.nan, index=changes.index)
    year = changes["week_start"].dt.year
    for market, rows in changes.groupby("market"):
        rows = rows.sort_values("week_start")
        quiet = rows["ds"].abs() < QUIET
        per_year = rows[quiet].groupby(year.loc[rows[quiet].index])[value].agg(["median", "count"])
        trailing = pd.Series(rows[value].to_numpy(), index=pd.DatetimeIndex(rows["week_start"])).rolling("364D").median().to_numpy()
        same_year = year.loc[rows.index].map(per_year["median"].where(per_year["count"] >= MIN_QUIET))
        out.loc[rows.index] = same_year.fillna(pd.Series(trailing, index=rows.index)).to_numpy()
    return out


def events(weekly: pd.DataFrame, column: str, predictions: List[pd.Series], counterfactuals: List[pd.Series],
           windows: List[tuple]) -> pd.DataFrame:
    """One row per unique lever market-week. `predictions[i]` / `counterfactuals[i]`: fold i's weekly
    prediction and last-year-schedule prediction, indexed by (market, week_start); `windows[i]`: its
    test (start, end)."""
    actual = year_on_year(weekly, column)
    actual["act"] = actual["dy"] - drift(actual, "dy")
    rows = []
    for pred, cf, (start, end) in zip(predictions, counterfactuals, windows):
        keyed = actual.set_index(["market", "week_start"])
        now = pred.reindex(keyed.index).to_numpy()
        before = pred.reindex(pd.MultiIndex.from_arrays([keyed.index.get_level_values(0), keyed.index.get_level_values(1) - pd.Timedelta(days=364)])).to_numpy()
        fold = actual.assign(dp=np.log(now / before), seat_only=np.log(now / cf.reindex(keyed.index).to_numpy()))
        fold = fold[np.isfinite(fold["dp"])]
        fold["prd"] = fold["dp"] - drift(fold, "dp")
        inside = (fold["week_start"] >= start) & (fold["week_start"] <= end) & (fold["ds"].abs() > THRESHOLD)
        rows.append(fold[inside])
    stacked = pd.concat(rows)
    return stacked.groupby(["market", "week_start"], as_index=False).agg(
        ds=("ds", "first"), act=("act", "first"), prd=("prd", "mean"), seat_only=("seat_only", "mean"), folds=("prd", "size"))


def _summary(group: pd.DataFrame) -> Dict[str, float]:
    error = group["prd"] - group["act"]
    ds2 = float(group["ds"] @ group["ds"])
    return {"n": len(group), "MAE": error.abs().mean(), "bias": error.mean(),
            "slope_act": float(group["ds"] @ group["act"]) / ds2, "slope_pred": float(group["ds"] @ group["prd"]) / ds2,
            "slope_seat_only": float(group["ds"] @ group["seat_only"]) / ds2 if group["seat_only"].notna().all() else np.nan}


def summarize(ev: pd.DataFrame) -> pd.DataFrame:
    """all / up / down, and the down weeks per episode (market) with the rest pooled as `other`."""
    down = ev[ev["ds"] < 0]
    parts = {"all": ev, "up": ev[ev["ds"] > 0], "down": down}
    for market in EPISODES:
        parts[f"down {market.lower()}"] = down[down["market"] == market]
    parts["down other"] = down[~down["market"].isin(EPISODES)]
    return pd.DataFrame({k: _summary(g) for k, g in parts.items() if len(g)}).T
