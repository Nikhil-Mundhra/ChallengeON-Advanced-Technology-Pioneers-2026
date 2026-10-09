"""Same-day guests: a separate count target (docs/decisions.md D17), modelled per market with a
Poisson GLM on day of week, holiday weeks and log new arrivals.

Fitted only on market-days whose same-day count is complete (no suppressed nationality value);
pooled markets with frequent suppression therefore train on fewer days.
"""

from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd
from sklearn.linear_model import PoissonRegressor

TARGET = "same_day_guests"


def _design(panel: pd.DataFrame) -> np.ndarray:
    dow = pd.to_datetime(panel["date"]).dt.dayofweek.to_numpy()
    columns = [(dow == d).astype(float) for d in range(1, 7)]
    columns += [panel["is_holiday_week"].to_numpy(dtype=float), np.log1p(panel["new_arrivals_filled"].to_numpy(dtype=float))]
    return np.column_stack(columns)


def complete_same_day(panel: pd.DataFrame) -> pd.Series:
    """Rows whose same-day count has no suppressed component."""
    return panel[TARGET].notna() & (panel["n_same_day_suppressed"] == 0)


class SameDayPoisson:
    def __init__(self, alpha: float = 1e-4, min_rows: int = 60) -> None:
        self.alpha, self.min_rows = alpha, min_rows

    def fit(self, panel: pd.DataFrame) -> "SameDayPoisson":
        rows = panel[complete_same_day(panel)]
        self.models_: Dict[str, PoissonRegressor] = {}
        self.fallback_: Dict[str, float] = rows.groupby("market")[TARGET].mean().to_dict()
        for market, group in rows.groupby("market"):
            if len(group) >= self.min_rows:
                self.models_[market] = PoissonRegressor(alpha=self.alpha, max_iter=1000).fit(_design(group), group[TARGET].to_numpy())
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
    """Baseline: the market's mean complete same-day count in the training rows."""

    def fit(self, panel: pd.DataFrame) -> "SameDayNaive":
        self.means_ = panel[complete_same_day(panel)].groupby("market")[TARGET].mean().to_dict()
        return self

    def predict(self, panel: pd.DataFrame) -> pd.Series:
        return panel["market"].map(self.means_).astype(float)


def poisson_deviance(actual: np.ndarray, pred: np.ndarray) -> float:
    """Mean Poisson deviance (lower is better)."""
    actual, pred = np.asarray(actual, float), np.asarray(pred, float)
    term = np.where(actual > 0, actual * np.log(np.where(actual > 0, actual, 1.0) / pred), 0.0)
    return float(np.mean(2 * (term - (actual - pred))))
