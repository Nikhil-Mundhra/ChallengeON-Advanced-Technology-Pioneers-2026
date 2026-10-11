"""Refit the international nowcast one market at a time, so the fitted components (w, c_t, s(t)) can
be read and the held drift can be changed after the fit.

The international model fits each market on its own rows, so a one-market fit gives the same
prediction as the full fit cached by run.py (checked on Israel: max relative difference 0).
Fitted models are cached in out/refits/<variant>/<market>__<fold>.pkl.

    python experiment/level_memory/refit.py VARIANT[,VARIANT...]   (variants from fixes.FIT_SPECS)
"""

from __future__ import annotations

import os
import pickle
import sys
import warnings
from multiprocessing import Pool
from typing import Callable, Dict, List, Tuple

import pandas as pd

from tourism_twin.domain.markets import DOMESTIC

import data
from drift import DriftingKernel

REFITS = data.OUT / "refits"
LAST_TEST_DAY = pd.Timestamp("2025-01-31")  # never predict into FROZEN_TEST


def international_markets(panel: pd.DataFrame) -> List[str]:
    return sorted(m for m in panel["market"].unique() if m != DOMESTIC)


def path(variant: str, market: str, fold: int):
    return REFITS / variant / f"{market}__{fold}.pkl"


def fit(build: Callable, market: str, fold: int):
    """The international spec fitted on one market's rows of the protocol fold's window."""
    panel = data.panel()
    window = data.Window("protocol", data.folds("protocol", panel)[fold], False)
    train = panel[panel["guests"].notna() & (panel["date"] < window.fit_end) & (panel["market"] == market)]
    return build().fit(train)


def load(variant: str, market: str, fold: int, build: Callable = None):
    """The cached fit, fitting and caching it first when `build` is given."""
    target = path(variant, market, fold)
    if target.exists():
        with open(target, "rb") as handle:
            return pickle.load(handle)
    if build is None:
        raise FileNotFoundError(target)
    warnings.filterwarnings("ignore")
    model = fit(build, market, fold)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "wb") as handle:
        pickle.dump(model, handle)
    return model


def kernel(model, market: str):
    """The arrivals kernel (shipped or drifting) of one market's fit."""
    components, _ = model.fitted_[market]
    return components[0]


def predict(model, market: str) -> pd.Series:
    """Guest predictions on every lag-complete day of the market up to LAST_TEST_DAY."""
    panel = data.panel()
    rows = panel[(panel["market"] == market) & (panel["date"] <= LAST_TEST_DAY) & panel["lag_complete"].astype(bool)]
    return model.predict(rows)


def parts(model, market: str) -> pd.DataFrame:
    """Per day: base stock c_t, kernel flow sum_k w_k A_{t-k}, s(t) (0 when the kernel does not drift)."""
    panel = data.panel()
    rows = panel[(panel["market"] == market) & (panel["date"] <= LAST_TEST_DAY) & panel["lag_complete"].astype(bool)]
    k = kernel(model, market)
    s = k.drift(rows["date"]) if isinstance(k, DriftingKernel) else 0.0
    return pd.DataFrame({"date": rows["date"].to_numpy(), "c": k._base_design(rows) @ k.c_,
                         "kernel": rows[k.lag_columns].to_numpy(dtype=float) @ k.w_, "s": s}, index=rows.index)


def _job(task: Tuple[str, str, int]) -> Tuple[str, str, int]:
    from fixes import FIT_SPECS
    variant, market, fold = task
    load(variant, market, fold, FIT_SPECS[variant])
    return task


def ensure(variants: List[str], markets: List[str] = None) -> None:
    """Fit and cache every (variant, market, fold) that is missing, in parallel."""
    markets = markets or international_markets(data.panel())
    tasks = [(v, m, i) for v in variants for m in markets for i in range(7) if not path(v, m, i).exists()]
    if not tasks:
        return
    with Pool(int(os.environ.get("NPROC", 8))) as pool:
        for done in pool.imap_unordered(_job, tasks):
            print(*done, flush=True)


if __name__ == "__main__":
    data.panel()
    ensure(sys.argv[1].split(","))
