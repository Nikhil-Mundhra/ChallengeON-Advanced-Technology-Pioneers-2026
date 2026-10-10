"""Same-day guests: a separate count target (docs/model/nowcast.md), modelled per market with a
Poisson GLM on day of week, holiday weeks and log new arrivals.

A suppressed nationality value ('*') counts as 0. Evidence in the training data: no observed
value is 0, observed counts fall monotonically from 1 (1: 6,814 rows, 2: 5,179, 3: 2,967), and
suppressed days have lower arrivals than observed ones (CHINA median 328 vs 501). Treating '*'
as missing instead keeps only the high days and leaves pooled markets with almost no rows.
"""

from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd
from sklearn.linear_model import PoissonRegressor

from tourism_twin.models.backtest import HoldoutSplit, RollingOrigin, backtest

TARGET = "same_day_guests"


def _design(panel: pd.DataFrame) -> np.ndarray:
    dow = pd.to_datetime(panel["date"]).dt.dayofweek.to_numpy()
    columns = [(dow == d).astype(float) for d in range(1, 7)]
    columns += [panel["is_holiday_week"].to_numpy(dtype=float), np.log1p(panel["new_arrivals_filled"].to_numpy(dtype=float))]
    return np.column_stack(columns)


def same_day_target(panel: pd.DataFrame) -> pd.Series:
    """Market same-day guests with suppressed nationality values as 0; NaN where nothing was reported."""
    reported = panel[TARGET].notna() | (panel["n_same_day_suppressed"] > 0)
    return panel[TARGET].fillna(0.0).where(reported)


class SameDayPoisson:
    def __init__(self, alpha: float = 1e-4, min_rows: int = 60) -> None:
        self.alpha, self.min_rows = alpha, min_rows

    def fit(self, panel: pd.DataFrame) -> "SameDayPoisson":
        y = same_day_target(panel)
        rows, y = panel[y.notna()], y.dropna()
        self.models_: Dict[str, PoissonRegressor] = {}
        self.fallback_: Dict[str, float] = y.groupby(rows["market"]).mean().to_dict()
        for market, group in rows.groupby("market"):
            if len(group) >= self.min_rows:
                self.models_[market] = PoissonRegressor(alpha=self.alpha, max_iter=1000).fit(_design(group), y[group.index].to_numpy())
        return self

    def predict(self, panel: pd.DataFrame) -> pd.Series:
        out = pd.Series(np.nan, index=panel.index, dtype=float)
        for market, group in panel.groupby("market"):
            if market in self.models_:
                out.loc[group.index] = self.models_[market].predict(_design(group))
            elif market in self.fallback_:
                out.loc[group.index] = self.fallback_[market]
        unseen = sorted(set(panel.loc[out.isna(), "market"]))
        if unseen:
            raise ValueError(f"SameDayPoisson has no data for markets {unseen}")
        return out


class SameDayNaive:
    """Baseline: the market's mean same-day count in the training rows."""

    def fit(self, panel: pd.DataFrame) -> "SameDayNaive":
        y = same_day_target(panel)
        self.means_ = y.groupby(panel["market"]).mean().to_dict()
        return self

    def predict(self, panel: pd.DataFrame) -> pd.Series:
        return panel["market"].map(self.means_).astype(float)


def poisson_deviance(actual: np.ndarray, pred: np.ndarray) -> float:
    """Mean Poisson deviance (lower is better); predictions are floored at 1e-9."""
    actual, pred = np.asarray(actual, float), np.maximum(np.asarray(pred, float), 1e-9)
    term = np.where(actual > 0, actual * np.log(np.where(actual > 0, actual, 1.0) / pred), 0.0)
    return float(np.mean(2 * (term - (actual - pred))))


def same_day_backtest(panel: pd.DataFrame, splitter: HoldoutSplit | RollingOrigin) -> pd.DataFrame:
    """Mean Poisson deviance per fold and segment (domestic / international) for SameDayPoisson and
    SameDayNaive, through the back-test harness (fresh fit per fold on rows before its origin)."""
    panel = panel.assign(same_day_target=same_day_target(panel))
    result = backtest({"poisson_glm": SameDayPoisson, "naive_mean": SameDayNaive}, panel, splitter,
                      target="same_day_target", metrics=lambda actual, pred: {"deviance": poisson_deviance(actual, pred)})
    scored = result.metrics[(result.metrics["segment"] != "all") & (result.metrics["n"] > 0)]
    return scored.rename(columns={"n": "rows"})[["fold", "model", "segment", "rows", "deviance"]].reset_index(drop=True)
