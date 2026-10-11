"""CHAIN: fit CHAIN_SPECS["seat_chain"] on each VALIDATION_ORIGINS fold's training days and cache its
weekly guest predictions on actual seats and on two counterfactual schedules for the fold's test days:
last year's seats (same weekday, 364 days earlier) and seats scaled to the market's centred 13-week
seat trend. The last fold's fitted chain is kept for the response curves.

    python experiment/scenario_response/chain_runs.py      (NPROC workers, default 7)
"""

from __future__ import annotations

import os
import pickle
import sys
import time
import warnings
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import data  # noqa: E402
from tourism_twin.planning.specs import CHAIN_SPECS  # noqa: E402

RUNS = data.OUT / "chain"
CURVE_FOLD = 6


def last_year_seats(frame: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """`frame` with seats on start..end replaced by the seats 364 days earlier."""
    earlier = frame[["market", "date", "seats"]].assign(date=frame["date"] + pd.Timedelta(days=364))
    joined = frame[["market", "date"]].merge(earlier, on=["market", "date"], how="left")
    inside = (frame["date"] >= start) & (frame["date"] <= end) & joined["seats"].notna().to_numpy()
    out = frame.copy()
    out.loc[inside, "seats"] = joined.loc[inside.to_numpy(), "seats"].to_numpy()
    return out


def trend_seats(frame: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """`frame` with each test-period day's seats scaled by its week's centred 13-week seat trend /
    week seats (the weekday pattern stays)."""
    weekly = data.weekly_sums(frame, ["seats"])
    weekly["ratio"] = data.centred_trend(weekly, "seats") / weekly["seats"]
    keyed = frame[["market"]].assign(week_start=data.week_start(frame["date"]))
    ratio = keyed.merge(weekly[["market", "week_start", "ratio"]], on=["market", "week_start"], how="left")["ratio"].to_numpy()
    inside = (frame["date"] >= start) & (frame["date"] <= end) & pd.notna(ratio) & (frame["seats"] > 0)
    out = frame.copy()
    out.loc[inside, "seats"] = frame.loc[inside, "seats"] * ratio[inside.to_numpy()]
    return out


def weekly_guests(frame: pd.DataFrame, guests: pd.Series) -> pd.Series:
    """Weekly sums of a daily guest prediction, complete weeks only, by (market, week_start)."""
    sums = data.weekly_sums(frame[["market", "date"]].assign(g=guests.to_numpy()), ["g"])
    return sums.set_index(["market", "week_start"])["g"]


def job(i: int) -> tuple:
    path = RUNS / f"fold{i}.pkl"
    if path.exists():
        return i, "cached"
    warnings.filterwarnings("ignore")
    frame = data.daily()
    fold = data.folds()[i]
    train = frame[frame["guests"].notna() & (frame["date"] < fold.train_end)]
    started = time.time()
    model = CHAIN_SPECS["seat_chain"].build().fit(train)
    seconds = time.time() - started
    record = {"fold": fold, "fit_s": seconds,
              "pred": weekly_guests(frame, model.predict(frame)),
              "cf_yoy": weekly_guests(frame, model.predict(last_year_seats(frame, fold.test_start, fold.test_end))),
              "cf_trend": weekly_guests(frame, model.predict(trend_seats(frame, fold.test_start, fold.test_end)))}
    if i == CURVE_FOLD:
        record["model"] = model
    with open(path, "wb") as handle:
        pickle.dump(record, handle)
    return i, round(seconds, 1)


def load() -> list:
    out = []
    for i in range(len(data.folds())):
        with open(RUNS / f"fold{i}.pkl", "rb") as handle:
            out.append(pickle.load(handle))
    return out


if __name__ == "__main__":
    RUNS.mkdir(parents=True, exist_ok=True)
    data.daily()
    with Pool(int(os.environ.get("NPROC", 7))) as pool:
        for result in pool.imap_unordered(job, range(len(data.folds()))):
            print(*result, flush=True)
