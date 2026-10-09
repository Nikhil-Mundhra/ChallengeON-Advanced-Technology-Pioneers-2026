"""One back-test harness for every model: splitters define folds, models are fitted on each
fold's training rows and scored on its test rows, domestic and international separately."""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Union

import numpy as np
import pandas as pd

from tourism_twin.models.protocol import Model

DOMESTIC = "DOMESTIC"


@dataclass(frozen=True)
class Fold:
    name: str
    train_end: pd.Timestamp   # training rows: date < train_end
    test_start: pd.Timestamp  # test rows: test_start <= date <= test_end
    test_end: pd.Timestamp


class HoldoutSplit:
    """A single forward split: train before `start`, test from `start` to `end` (or the last date)."""

    def __init__(self, start: str, end: str | None = None) -> None:
        self.start, self.end = pd.Timestamp(start), pd.Timestamp(end) if end else None

    def folds(self, dates: pd.Series) -> List[Fold]:
        end = self.end or pd.to_datetime(dates).max()
        return [Fold(f"holdout_{self.start.date()}", self.start, self.start, end)]


class RollingOrigin:
    """Monthly origins from `first` to `last`; each fold trains before its origin and tests the
    next `horizon_months` months."""

    def __init__(self, first: str, last: str, horizon_months: int = 6) -> None:
        self.first, self.last, self.horizon_months = pd.Timestamp(first), pd.Timestamp(last), horizon_months

    def folds(self, dates: pd.Series) -> List[Fold]:
        folds = []
        for origin in pd.date_range(self.first, self.last, freq="MS"):
            end = origin + pd.DateOffset(months=self.horizon_months) - np.timedelta64(1, "D")
            folds.append(Fold(f"origin_{origin.date()}", origin, origin, end))
        return folds


def forecast_metrics(actual: np.ndarray, pred: np.ndarray) -> Dict[str, float]:
    err = actual - pred
    tot_act = float(np.sum(actual))
    wmape = float(np.sum(np.abs(err)) / tot_act) if tot_act > 0 else 0.0
    bias = float((np.sum(pred) - tot_act) / tot_act) if tot_act > 0 else 0.0
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err ** 2)))
    return {"wmape": wmape, "bias": bias, "mae": mae, "rmse": rmse}


@dataclass
class BacktestResult:
    predictions: pd.DataFrame  # fold, origin, model, row, market, date, horizon_days, actual, pred
    metrics: pd.DataFrame      # fold, model, segment (all | domestic | international), n, wmape, bias, mae, rmse
    skipped: List[str] = field(default_factory=list)  # folds with no training or no test rows

    def summary(self) -> pd.DataFrame:
        """Mean of the per-fold metrics per model and segment. Folds overlap (a row is scored by
        several origins), so this is a mean over forecast origins, not a pooled error over rows."""
        scored = self.metrics[self.metrics["n"] > 0]
        return scored.groupby(["model", "segment"])[["wmape", "bias", "mae", "rmse"]].mean()


def backtest(
    models: Dict[str, Callable[[], Model]],
    panel: pd.DataFrame,
    splitter: Union[HoldoutSplit, RollingOrigin],
    date_column: str = "date",
    target: str = "guests",
    period_days: int = 1,
) -> BacktestResult:
    """Fit a fresh model per (model, fold) on rows before the fold and score its test rows.

    Each row covers `period_days` days starting at its date (7 for the weekly panel). A row
    trains only if its whole period ends before the origin, and is tested if its period starts
    inside the test window, so a week straddling an origin is never seen in training. Rows
    without a target are never used. Calibration happens inside fit(), on training rows only.
    """
    if not panel.index.is_unique:
        raise ValueError("Panel index must be unique")
    dates = pd.to_datetime(panel[date_column])
    period_end = dates + pd.to_timedelta(period_days - 1, unit="D")
    observed = panel[target].notna()
    records: List[pd.DataFrame] = []
    skipped: List[str] = []
    for fold in splitter.folds(dates[observed]):
        train = panel[observed & (period_end < fold.train_end)]
        test = panel[observed & (dates >= fold.test_start) & (dates <= fold.test_end)]
        if train.empty or test.empty:
            skipped.append(fold.name)
            continue
        for name, factory in models.items():
            pred = factory().fit(train).predict(test)
            if not isinstance(pred, pd.Series) or not pred.index.equals(test.index):
                raise ValueError(f"Model {name!r} must return a Series indexed like the test rows (fold {fold.name})")
            if pred.isna().any():
                raise ValueError(f"Model {name!r} returned {int(pred.isna().sum())} missing predictions (fold {fold.name})")
            records.append(pd.DataFrame({
                "fold": fold.name, "origin": fold.test_start, "model": name, "row": test.index,
                "market": test["market"].to_numpy(), "date": dates[test.index].to_numpy(),
                "horizon_days": (dates[test.index] - fold.test_start).dt.days.to_numpy(),
                "actual": test[target].to_numpy(), "pred": pred.to_numpy(),
            }))
    if not records:
        raise ValueError(f"No fold had both training and test rows; skipped: {skipped}")
    if skipped:
        warnings.warn(f"Skipped folds without training or test rows: {skipped}", stacklevel=2)
    predictions = pd.concat(records, ignore_index=True)
    return BacktestResult(predictions, score(predictions), skipped)


def score(predictions: pd.DataFrame) -> pd.DataFrame:
    """Metrics per fold, model and segment; an empty segment gets n=0 and no metrics."""
    rows = []
    segments: Iterable = (("all", None), ("domestic", True), ("international", False))
    for (fold, model), group in predictions.groupby(["fold", "model"], sort=False):
        for segment, domestic in segments:
            part = group if domestic is None else group[(group["market"] == DOMESTIC) == domestic]
            metrics = forecast_metrics(part["actual"].to_numpy(), part["pred"].to_numpy()) if len(part) else {}
            rows.append({"fold": fold, "model": model, "segment": segment, "n": len(part), **metrics})
    return pd.DataFrame(rows)
