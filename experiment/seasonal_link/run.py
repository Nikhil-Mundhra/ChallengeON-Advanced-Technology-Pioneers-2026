"""Fit each chain variant on each VALIDATION_ORIGINS fold (or on every guest day up to CUT: fold "full")
and cache its daily guest prediction on actual seats, its weekly guests on actual seats and on the two
counterfactual schedules of the fold's test days, and the per-market seasonal strengths.

    python experiment/seasonal_link/run.py VARIANTS [FOLDS]    (comma lists; FOLDS default 0..6; NPROC, default 9)
"""

from __future__ import annotations

import os
import pickle
import sys
import time
import warnings
from multiprocessing import Pool

import pandas as pd

import data
import schedules
from variants import SPECS

RUNS = data.OUT / "runs"


def path(variant: str, fold: str):
    return RUNS / f"{variant}__{fold}.pkl"


def strengths(model) -> dict:
    """Per market: the seasonal strength explain() of link 1, if it has one."""
    out = {}
    for market, parts in model.arrivals_model_.explain().items():
        kernel = parts.get("seats", {})
        if "strength" in kernel:
            out[market] = {**kernel["strength"], "kernel_sum": kernel["kernel_sum"], "base_stock_share": kernel["base_stock_share"]}
    return out


def job(task: tuple) -> tuple:
    variant, fold_key = task
    if path(variant, fold_key).exists():
        return (*task, "cached")
    warnings.filterwarnings("ignore")
    frame = data.daily()
    if fold_key == "full":
        fold, end = None, data.CUT + pd.Timedelta(days=1)
    else:
        fold = data.folds()[int(fold_key)]
        end = fold.train_end
    started = time.time()
    model = SPECS[variant].build().fit(frame[frame["guests"].notna() & (frame["date"] < end)])
    seconds = time.time() - started
    guests = model.predict(frame)
    record = {"fold": fold, "fit_s": seconds, "daily": guests, "pred": schedules.weekly_guests(frame, guests),
              "strength": strengths(model), "diagnostics": model.diagnostics()}
    if fold is not None:
        record["cf_yoy"] = schedules.weekly_guests(frame, model.predict(schedules.last_year_seats(frame, fold.test_start, fold.test_end)))
        record["cf_trend"] = schedules.weekly_guests(frame, model.predict(schedules.trend_seats(frame, fold.test_start, fold.test_end)))
    with open(path(variant, fold_key), "wb") as handle:
        pickle.dump(record, handle)
    return (*task, round(seconds, 1))


def load(variant: str, fold: str) -> dict:
    with open(path(variant, fold), "rb") as handle:
        return pickle.load(handle)


if __name__ == "__main__":
    RUNS.mkdir(parents=True, exist_ok=True)
    data.daily()
    variants = sys.argv[1].split(",")
    folds = sys.argv[2].split(",") if len(sys.argv) > 2 else [str(i) for i in range(len(data.folds()))]
    tasks = [(v, f) for v in variants for f in folds]
    with Pool(int(os.environ.get("NPROC", 9))) as pool:
        for result in pool.imap_unordered(job, tasks):
            print(*result, flush=True)
