"""Same-day guests: a separate count target (docs/model_design.md §5.7), modelled per market with a
Poisson GLM on day of week, holiday weeks and log new arrivals.

A suppressed nationality value ('*') counts as 0. Evidence in the training data: no observed
value is 0, observed counts fall monotonically from 1 (1: 6,814 rows, 2: 5,179, 3: 2,967), and
suppressed days have lower arrivals than observed ones (CHINA median 328 vs 501). Treating '*'
as missing instead keeps only the high days and leaves pooled markets with almost no rows.
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd
from sklearn.linear_model import PoissonRegressor

from tourism_twin.domain.markets import DOMESTIC
from tourism_twin.models.backtest import HoldoutSplit, RollingOrigin

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
    """Mean Poisson deviance per fold and segment (domestic / international) for SameDayPoisson
    and SameDayNaive, each fitted on rows before the fold's origin."""
    y = same_day_target(panel)
    rows: List[Dict[str, object]] = []
    for fold in splitter.folds(panel["date"]):
        train = panel[(panel["date"] < fold.train_end) & y.notna()]
        test = panel[(panel["date"] >= fold.test_start) & (panel["date"] <= fold.test_end) & y.notna()]
        if train.empty or test.empty:
            continue
        test = test[test["market"].isin(set(train["market"]))]
        segment = np.where(test["market"] == DOMESTIC, "domestic", "international")
        for name, model in (("poisson_glm", SameDayPoisson()), ("naive_mean", SameDayNaive())):
            pred = model.fit(train).predict(test)
            for seg in ("domestic", "international"):
                mask = segment == seg
                if mask.any():
                    rows.append({"fold": fold.name, "model": name, "segment": seg, "rows": int(mask.sum()),
                                 "deviance": poisson_deviance(y[test.index][mask], pred[mask])})
    return pd.DataFrame(rows)
