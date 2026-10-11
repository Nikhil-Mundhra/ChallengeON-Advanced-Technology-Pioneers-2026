"""Fit each model on each fold's window and cache its guest predictions on every day from the panel
start to the last test day (in-sample days feed the carry-forward, test days are scored).

    python experiment/level_memory/run.py PLAN     (PLAN: base, drift, combined; NPROC workers, default 8)
"""

from __future__ import annotations

import os
import pickle
import sys
import time
import warnings
from multiprocessing import Pool
from typing import Dict, List, Tuple

import pandas as pd

import data
from drift import DriftingKernel
from variants import DRIFT_HALF_LIVES, DRIFT_KNOTS, DRIFT_LAMBDAS, MODELS, drift_name

RUNS = data.OUT / "runs"
LAST_TEST_DAY = pd.Timestamp("2025-01-31")  # never predict into FROZEN_TEST
CHOSEN_DRIFT = os.environ.get("CHOSEN_DRIFT", "drift_k182_l10")  # set after the drift grid (README.md)

Task = Tuple[str, str, int, bool]  # model, splitter, fold index, held back


def plan(name: str) -> List[Task]:
    n = 7
    if name == "base":
        return ([(m, s, i, hb) for m in ("nowcast", "chain") for s in data.SPLITTERS for i in range(n) for hb in (False, True)]
                + [("time_only", s, i, False) for s in data.SPLITTERS for i in range(n)])
    if name == "drift":
        return [(drift_name(k, lam), "protocol", i, False) for k in DRIFT_KNOTS for lam in DRIFT_LAMBDAS for i in range(n)]
    if name == "combined":
        return [(CHOSEN_DRIFT, "protocol", i, True) for i in range(n)]
    raise KeyError(name)


def path(task: Task):
    model, splitter, i, held_back = task
    return RUNS / f"{model}__{splitter}__{i}{'__hb' if held_back else ''}.pkl"


def _drift_kernels(model) -> List[DriftingKernel]:
    return [c for side in model.models_.values() for components, _ in side.fitted_.values()
            for c in components if isinstance(c, DriftingKernel)]


def _predict(name: str, model, frame: pd.DataFrame) -> Dict[str, pd.Series]:
    if name == "chain":
        return {"guests": model.predict_frame(frame)["guests"].dropna()}
    rows = frame if name == "time_only" else frame[frame["lag_complete"].astype(bool)]
    if not name.startswith("drift"):
        return {"guests": model.predict(rows)}
    out = {}
    for half_life in DRIFT_HALF_LIVES:
        for kernel in _drift_kernels(model):
            kernel.half_life = half_life
        out["guests" if half_life is None else f"guests_hl{half_life}"] = model.predict(rows)
    for kernel in _drift_kernels(model):
        kernel.half_life = None
    return out


def _fit_report(model) -> dict:
    """Per market: backfitting passes, converged, and the drift summary when the kernel drifts."""
    sides = [model.arrivals_model_, model.guests_model_] if hasattr(model, "guests_model_") else list(model.models_.values())
    out: dict = {}
    for side in sides:
        for market, (components, report) in side.fitted_.items():
            entry = out.setdefault(market, {"passes": 0, "converged": True})
            entry["passes"] += report.iterations
            entry["converged"] &= report.converged
            for c in components:
                if isinstance(c, DriftingKernel):
                    entry["drift"] = c.explain()["drift"]
    return out


def job(task: Task) -> tuple:
    if path(task).exists():
        return (*task, "cached")
    warnings.filterwarnings("ignore")
    name, splitter, i, held_back = task
    panel = data.panel()
    window = data.Window(splitter, data.folds(splitter, panel)[i], held_back)
    train = panel[panel["guests"].notna() & (panel["date"] < window.fit_end)]
    started = time.time()
    model = MODELS[name]().fit(train)
    fit_seconds = time.time() - started
    frame = panel[panel["date"] <= LAST_TEST_DAY]
    record = {"window": window, "fit_s": fit_seconds, "pred": _predict(name, model, frame), "report": _fit_report(model)}
    with open(path(task), "wb") as handle:
        pickle.dump(record, handle)
    return (*task, round(fit_seconds, 1))


if __name__ == "__main__":
    RUNS.mkdir(parents=True, exist_ok=True)
    data.panel()  # build the cache once before the workers read it
    tasks = [t for name in sys.argv[1].split(",") for t in plan(name)]
    tasks.sort(key=lambda t: t[0] == "time_only")  # slow fits first
    with Pool(int(os.environ.get("NPROC", 8))) as pool:
        for result in pool.imap_unordered(job, tasks):
            print(*result, flush=True)
