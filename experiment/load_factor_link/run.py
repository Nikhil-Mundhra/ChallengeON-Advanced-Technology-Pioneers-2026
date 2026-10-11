"""Fit each variant on each VALIDATION_ORIGINS fold's training window and cache its daily predictions on
every date, plus a counterfactual with the fold's test-period schedule set back to last year's.

    python experiment/load_factor_link/run.py [VARIANT,...]     (default: all; NPROC workers, default 8)
"""

from __future__ import annotations

import os
import pickle
import sys
import time
import warnings
from multiprocessing import Pool

import pandas as pd

from tourism_twin.models.backtest import VALIDATION_ORIGINS

import data
from variants import VARIANTS

RUNS = data.OUT / "runs"
SCHEDULE = ("seats", "p2p", "pax", "flights", "airlines", "premium_seats")
SCENARIO_FOLD = 6  # the last fold's fitted model is kept for scenarios.py


def folds(panel: pd.DataFrame) -> list:
    return VALIDATION_ORIGINS.folds(panel["date"][panel["guests"].notna()])


def last_year_schedule(panel: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """`panel` with every schedule column on start..end replaced by its value 364 days earlier (same
    weekday): the seat-only lever re-predicts the test period on last year's schedule."""
    earlier = panel[["market", "date", *SCHEDULE]].assign(date=panel["date"] + pd.Timedelta(days=364))
    joined = panel[["market", "date"]].merge(earlier, on=["market", "date"], how="left")
    joined.index = panel.index
    inside = (panel["date"] >= start) & (panel["date"] <= end) & joined["seats"].notna()
    out = panel.copy()
    out.loc[inside, list(SCHEDULE)] = joined.loc[inside, list(SCHEDULE)]
    return out


def job(task: tuple) -> tuple:
    name, i = task
    path = RUNS / f"{name}__{i}.pkl"
    if path.exists():
        return name, i, "cached"
    warnings.filterwarnings("ignore")
    panel = data.panel()
    fold = folds(panel)[i]
    train = panel[panel["guests"].notna() & (panel["date"] < fold.train_end)]
    started = time.time()
    model = VARIANTS[name]().fit(train)
    fit_seconds = time.time() - started
    pred = model.predict_frame(panel)
    counterfactual = model.predict_frame(last_year_schedule(panel, fold.test_start, fold.test_end))
    record = {"fold": fold, "fit_s": fit_seconds, "pred": pred, "cf": counterfactual[["p2p", "arrivals", "guests"]],
              "link0": getattr(model, "passengers", None), "explain": model.explain()}
    if i == SCENARIO_FOLD:
        record["model"] = model
    with open(path, "wb") as handle:
        pickle.dump(record, handle)
    return name, i, round(fit_seconds, 1)


if __name__ == "__main__":
    names = sys.argv[1].split(",") if len(sys.argv) > 1 else list(VARIANTS)
    RUNS.mkdir(parents=True, exist_ok=True)
    data.panel()  # build the cache once before the workers read it
    tasks = [(name, i) for name in names for i in range(len(folds(data.panel())))]
    with Pool(int(os.environ.get("NPROC", 8))) as pool:
        for result in pool.imap_unordered(job, tasks):
            print(*result, flush=True)
