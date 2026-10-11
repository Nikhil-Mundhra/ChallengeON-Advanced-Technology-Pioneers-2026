"""Natural-experiment weeks and their scoring. Copied from experiment/load_factor_link/lever.py
(year-on-year test, robust drift baseline, unique weeks) and extended with the centred-trend test.

yoy:   ds = log(seats / seats 364 days earlier); act = log change of guests over the same 364 days
       minus the market's baseline drift; prd = the same for the model's prediction (now: the scenario
       week; a year earlier: its ordinary prediction) minus the prediction's drift.
       Drift: median log change over the market's quiet weeks (|ds| < 5%) of that year when there are
       at least MIN_QUIET of them, else the median over the market's trailing 52 weeks.
trend: ds = log(seats / centred 13-week seat mean); act = log(guests / centred 13-week guest mean);
       prd = log(prediction / centred 13-week mean of the prediction). No drift term.
A natural-experiment week has |ds| > THRESHOLD. `seat_only` = log(prediction / the model's baseline
with seats held at the reference). A market-week inside several overlapping test folds counts once,
its values averaged over those folds.
"""

from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd

import data

THRESHOLD = 0.15
QUIET = 0.05
MIN_QUIET = 8
BLOCK_WEEKS = 4
N_BOOT = 2000


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


def actual_changes(weekly: pd.DataFrame, mode: str) -> pd.DataFrame:
    """market, week_start, guests, ds, act for every week that has the mode's reference."""
    if mode == "yoy":
        out = year_on_year(weekly, "guests")
        return out.assign(act=out["dy"] - drift(out, "dy"))[["market", "week_start", "guests", "ds", "act"]]
    frame = weekly[["market", "week_start", "seats", "guests"]].sort_values(["market", "week_start"]).reset_index(drop=True)
    frame["seat_trend"], frame["guest_trend"] = data.centred_trend(frame, "seats"), data.centred_trend(frame, "guests")
    frame = frame[(frame[["seats", "guests", "seat_trend", "guest_trend"]] > 0).all(axis=1)]
    return frame.assign(ds=np.log(frame["seats"] / frame["seat_trend"]), act=np.log(frame["guests"] / frame["guest_trend"]))[
        ["market", "week_start", "guests", "ds", "act"]]


def fold_rows(mode: str, weekly: pd.DataFrame, actual: pd.DataFrame, pred: pd.Series, cf: pd.Series, fold) -> pd.DataFrame:
    """Every test week of one fold with the model's prd, seat_only and levels (pred, base)."""
    keys = pd.MultiIndex.from_frame(actual[["market", "week_start"]])
    now = pred.reindex(keys).to_numpy()
    rows = actual.assign(pred=now, base=cf.reindex(keys).to_numpy())
    if mode == "yoy":
        before = pred.reindex(pd.MultiIndex.from_arrays([keys.get_level_values(0), keys.get_level_values(1) - pd.Timedelta(days=364)])).to_numpy()
        rows["dp"] = np.log(now / before)
        rows = rows[np.isfinite(rows["dp"])]
        rows["prd"] = rows["dp"] - drift(rows, "dp")
    else:
        frame = weekly[["market", "week_start"]].sort_values(["market", "week_start"]).reset_index(drop=True)
        frame["p"] = pred.reindex(pd.MultiIndex.from_frame(frame)).to_numpy()
        trend = frame.assign(t=data.centred_trend(frame, "p")).set_index(["market", "week_start"])["t"]
        rows["prd"] = np.log(now / trend.reindex(keys).to_numpy())
    rows["seat_only"] = np.log(rows["pred"] / rows["base"])
    inside = (rows["week_start"] >= fold.test_start) & (rows["week_start"] + pd.Timedelta(days=6) <= fold.test_end) & np.isfinite(rows["prd"])
    return rows[inside].assign(fold=fold.name, event=rows["ds"].abs() > THRESHOLD)


def unique_weeks(rows: pd.DataFrame) -> pd.DataFrame:
    return rows.groupby(["market", "week_start"], as_index=False).agg(
        ds=("ds", "first"), act=("act", "first"), guests=("guests", "first"), event=("event", "first"),
        prd=("prd", "mean"), seat_only=("seat_only", "mean"), pred=("pred", "mean"), base=("base", "mean"), folds=("prd", "size"))


def summary(group: pd.DataFrame) -> Dict[str, float]:
    error = group["prd"] - group["act"]
    ds2 = float(group["ds"] @ group["ds"])
    prd_c = group["prd"] - group["prd"].mean()
    return {"n": len(group), "MAE": error.abs().mean(), "bias": error.mean(),
            "slope actual": float(group["ds"] @ group["act"]) / ds2, "slope predicted": float(group["ds"] @ group["prd"]) / ds2,
            "slope seat-only": float(group["ds"] @ group["seat_only"]) / ds2,
            "actual on predicted": float(prd_c @ (group["act"] - group["act"].mean())) / float(prd_c @ prd_c) if float(prd_c @ prd_c) > 1e-12 else np.nan}


def parts(events: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    return {"all": events, "increases": events[events["ds"] > 0], "cuts": events[events["ds"] < 0]}


def block_draws(weeks: pd.Series, seed: int = 0) -> np.ndarray:
    """N_BOOT resamples (row positions) in moving blocks of BLOCK_WEEKS calendar weeks; every market's
    row of a week moves with it."""
    order = np.sort(weeks.unique())
    position = {w: i for i, w in enumerate(order)}
    rows_of = [[] for _ in order]
    for row, week in enumerate(weeks.to_numpy()):
        rows_of[position[week]].append(row)
    rng = np.random.default_rng(seed)
    n = len(order)
    out = []
    for _ in range(N_BOOT):
        starts = rng.integers(0, max(n - BLOCK_WEEKS, 0) + 1, size=int(np.ceil(n / BLOCK_WEEKS)))
        picked = (starts[:, None] + np.arange(BLOCK_WEEKS)).ravel()[:n]
        out.append(np.concatenate([rows_of[i] for i in picked if i < n]))
    return out


def paired_difference(a: pd.DataFrame, b: pd.DataFrame) -> Dict[str, str]:
    """b minus a on the same event weeks: MAE and predicted slope, with 90% block-bootstrap intervals."""
    joined = a.merge(b, on=["market", "week_start"], suffixes=("_a", "_b"))
    ea, eb = (joined["prd_a"] - joined["act_a"]).abs().to_numpy(), (joined["prd_b"] - joined["act_b"]).abs().to_numpy()
    ds = joined["ds_a"].to_numpy()

    def stats(idx):
        return np.mean(eb[idx] - ea[idx]), (ds[idx] @ (joined["prd_b"].to_numpy()[idx] - joined["prd_a"].to_numpy()[idx])) / (ds[idx] @ ds[idx])

    point = stats(np.arange(len(joined)))
    draws = np.array([stats(idx) for idx in block_draws(joined["week_start"])])
    low, high = np.quantile(draws, 0.05, axis=0), np.quantile(draws, 0.95, axis=0)
    return {"n": len(joined), "MAE diff [90% CI]": f"{point[0]:+.4f} [{low[0]:+.4f}, {high[0]:+.4f}]",
            "slope diff [90% CI]": f"{point[1]:+.3f} [{low[1]:+.3f}, {high[1]:+.3f}]"}
