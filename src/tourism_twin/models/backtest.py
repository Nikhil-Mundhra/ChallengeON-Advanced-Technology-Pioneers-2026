"""One back-test harness for every model: splitters define folds, models are fitted on each
fold's training rows and scored on its test rows, domestic and international separately."""

from __future__ import annotations

from dataclasses import dataclass
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
    predictions: pd.DataFrame  # fold, model, row index, market, date, actual, pred
    metrics: pd.DataFrame      # fold, model, segment (all | domestic | international), n, wmape, bias, mae, rmse


def backtest(
    models: Dict[str, Callable[[], Model]],
    panel: pd.DataFrame,
    splitter: Union[HoldoutSplit, RollingOrigin],
    date_column: str = "date",
    target: str = "guests",
) -> BacktestResult:
    """Fit a fresh model per (model, fold) on rows before the fold and score its test rows.

    Rows without a target are never used. Any per-fold calibration happens inside fit(), so it
    only sees the fold's training rows.
    """
    dates = pd.to_datetime(panel[date_column])
    observed = panel[target].notna()
    records: List[pd.DataFrame] = []
    for fold in splitter.folds(dates[observed]):
        train = panel[observed & (dates < fold.train_end)]
        test = panel[observed & (dates >= fold.test_start) & (dates <= fold.test_end)]
        if train.empty or test.empty:
            continue
        for name, factory in models.items():
            pred = factory().fit(train).predict(test)
            records.append(pd.DataFrame({
                "fold": fold.name, "model": name, "row": test.index, "market": test["market"].to_numpy(),
                "date": dates[test.index].to_numpy(), "actual": test[target].to_numpy(), "pred": pred.reindex(test.index).to_numpy(),
            }))
    predictions = pd.concat(records, ignore_index=True)
    return BacktestResult(predictions, score(predictions))


def score(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    segments: Iterable = (("all", None), ("domestic", True), ("international", False))
    for (fold, model), group in predictions.groupby(["fold", "model"], sort=False):
        for segment, domestic in segments:
            part = group if domestic is None else group[(group["market"] == DOMESTIC) == domestic]
            if part.empty:
                continue
            rows.append({"fold": fold, "model": model, "segment": segment, "n": len(part),
                         **forecast_metrics(part["actual"].to_numpy(), part["pred"].to_numpy())})
    return pd.DataFrame(rows)
