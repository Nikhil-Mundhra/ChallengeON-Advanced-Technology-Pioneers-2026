"""Residual slopes per group with a week-cluster bootstrap: a draw resamples calendar weeks with
replacement and keeps every market's row of a drawn week, so cross-market co-movement in a week
(a holiday, an airline schedule change) stays inside one draw. Weeks next to each other are still
correlated, so the intervals are somewhat narrow."""

from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

N_BOOT = 1000
COVERAGE = 0.9


def slope(x: np.ndarray, y: np.ndarray) -> float:
    xc = x - x.mean()
    denominator = float(xc @ xc)
    return float(xc @ (y - y.mean())) / denominator if denominator > 0 else np.nan


def _draws(weeks: np.ndarray, seed: int) -> List[np.ndarray]:
    order, position = np.unique(weeks, return_inverse=True)
    rows_of = [np.flatnonzero(position == i) for i in range(len(order))]
    rng = np.random.default_rng(seed)
    return [np.concatenate([rows_of[i] for i in rng.integers(0, len(order), len(order))]) for _ in range(N_BOOT)]


def by_group(frame: pd.DataFrame, x: str, y: str, group: str, seed: int = 0) -> pd.DataFrame:
    """Per value of `group`: n, slope of y on x with its interval, correlation and the sd of x."""
    rows = []
    for value, part in frame.groupby(group, sort=True):
        X, Y = part[x].to_numpy(), part[y].to_numpy()
        boot = np.array([slope(X[i], Y[i]) for i in _draws(part["week_start"].to_numpy(), seed)])
        tail = (1 - COVERAGE) / 2
        rows.append({group: value, "n": len(part), "slope": slope(X, Y), "low": np.nanquantile(boot, tail),
                     "high": np.nanquantile(boot, 1 - tail), "corr": float(np.corrcoef(X, Y)[0, 1]), "sd x": float(X.std())})
    return pd.DataFrame(rows)


def contrast(frame: pd.DataFrame, x: str, y: str, group: str, first: list, second: list, seed: int = 0) -> Dict[str, float]:
    """Slope on rows whose `group` is in `first` minus slope on rows in `second`, with the interval
    from draws shared by both sides."""
    a, b = frame[frame[group].isin(first)], frame[frame[group].isin(second)]
    both = pd.concat([a.assign(_side=0), b.assign(_side=1)], ignore_index=True)
    X, Y, side = both[x].to_numpy(), both[y].to_numpy(), both["_side"].to_numpy()

    def stat(i: np.ndarray) -> float:
        s = side[i]
        return slope(X[i][s == 0], Y[i][s == 0]) - slope(X[i][s == 1], Y[i][s == 1])

    boot = np.array([stat(i) for i in _draws(both["week_start"].to_numpy(), seed)])
    tail = (1 - COVERAGE) / 2
    return {"difference": stat(np.arange(len(both))), "low": float(np.nanquantile(boot, tail)), "high": float(np.nanquantile(boot, 1 - tail))}
