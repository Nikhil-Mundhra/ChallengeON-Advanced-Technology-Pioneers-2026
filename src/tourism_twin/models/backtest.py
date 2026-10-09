"""One back-test harness for every model: splitters define folds, models are fitted on each
fold's training rows and scored on its test rows, domestic and international separately."""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Union

import numpy as np
import pandas as pd

from tourism_twin.domain.markets import DOMESTIC
from tourism_twin.models.protocol import Model


@dataclass(frozen=True)
class Fold:
    name: str
    train_end: pd.Timestamp   # training rows: date < train_end
    test_start: pd.Timestamp  # test rows: test_start <= date <= test_end
    test_end: pd.Timestamp


class HoldoutSplit:
    """A single forward split: test from `start` to `end` (or the last date); training rows end
    `gap_days` before `start`."""

    def __init__(self, start: str, end: str | None = None, gap_days: int = 0) -> None:
        self.start, self.end, self.gap_days = pd.Timestamp(start), pd.Timestamp(end) if end else None, gap_days

    def folds(self, dates: pd.Series) -> List[Fold]:
        end = self.end or pd.to_datetime(dates).max()
        train_end = self.start - np.timedelta64(self.gap_days, "D")
        return [Fold(f"holdout_{self.start.date()}", train_end, self.start, end)]


class RollingOrigin:
    """Monthly origins from `first` to `last`; each fold trains on rows ending `gap_days` before its
    origin (expanding window) and tests the next `horizon_months` months, cut at `end`."""

    def __init__(self, first: str, last: str, horizon_months: int = 6, gap_days: int = 0, end: str | None = None) -> None:
        self.first, self.last, self.horizon_months = pd.Timestamp(first), pd.Timestamp(last), horizon_months
        self.gap_days, self.end = gap_days, pd.Timestamp(end) if end else None

    def folds(self, dates: pd.Series) -> List[Fold]:
        folds = []
        for origin in pd.date_range(self.first, self.last, freq="MS"):
            end = origin + pd.DateOffset(months=self.horizon_months) - np.timedelta64(1, "D")
            if self.end is not None:
                end = min(end, self.end)
            folds.append(Fold(f"origin_{origin.date()}", origin - np.timedelta64(self.gap_days, "D"), origin, end))
        return folds


# Evaluation protocol (issue #11): every choice (spec, hyperparameter, the 0.3 pp gate) is made on
# VALIDATION_ORIGINS; FROZEN_TEST is scored once, after all choices are fixed. Rows are never
# shuffled; training ends 21 days before each origin (kernel lags and error memory).
PROTOCOL_GAP_DAYS = 21
VALIDATION_ORIGINS = RollingOrigin("2024-02-01", "2024-08-01", horizon_months=6, gap_days=PROTOCOL_GAP_DAYS, end="2025-01-31")
FROZEN_TEST = HoldoutSplit("2025-02-01", "2025-07-31", gap_days=PROTOCOL_GAP_DAYS)


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
    diagnostics: pd.DataFrame = field(default_factory=pd.DataFrame)  # fold, model, and each model's fit counts

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
    metrics: Callable[[np.ndarray, np.ndarray], Dict[str, float]] = forecast_metrics,
) -> BacktestResult:
    """Fit a fresh model per (model, fold) on rows before the fold and score its test rows.

    Each row covers `period_days` days starting at its date (7 for the weekly panel). A row
    trains only if its whole period ends before the origin, and is tested if its period starts
    inside the test window, so a week straddling an origin is never seen in training. Rows
    without a target are never used. Calibration happens inside fit(), on training rows only.
    `metrics(actual, pred)` scores each fold and segment (default: WMAPE, bias, MAE, RMSE).
    """
    if not panel.index.is_unique:
        raise ValueError("Panel index must be unique")
    dates = pd.to_datetime(panel[date_column])
    period_end = dates + pd.to_timedelta(period_days - 1, unit="D")
    observed = panel[target].notna()
    records: List[pd.DataFrame] = []
    skipped: List[str] = []
    fit_counts: List[dict] = []
    for fold in splitter.folds(dates[observed]):
        train = panel[observed & (period_end < fold.train_end)]
        test = panel[observed & (dates >= fold.test_start) & (dates <= fold.test_end)]
        if train.empty or test.empty:
            skipped.append(fold.name)
            continue
        for name, factory in models.items():
            model = factory().fit(train)
            pred = model.predict(test)
            if hasattr(model, "diagnostics"):
                fit_counts.append({"fold": fold.name, "model": name, **model.diagnostics()})
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
    return BacktestResult(predictions, score(predictions, metrics), skipped, pd.DataFrame(fit_counts))


def segment_of(markets: pd.Series) -> np.ndarray:
    """Reporting segment of each market: "domestic" or "international" (never pooled)."""
    return np.where(markets.to_numpy() == DOMESTIC, "domestic", "international")


def score(predictions: pd.DataFrame, metrics: Callable[[np.ndarray, np.ndarray], Dict[str, float]] = forecast_metrics) -> pd.DataFrame:
    """Metrics per fold, model and segment; an empty segment gets n=0 and no metrics."""
    rows = []
    for (fold, model), group in predictions.groupby(["fold", "model"], sort=False):
        labels = segment_of(group["market"])
        for segment in ("all", "domestic", "international"):
            part = group if segment == "all" else group[labels == segment]
            values = metrics(part["actual"].to_numpy(), part["pred"].to_numpy()) if len(part) else {}
            rows.append({"fold": fold, "model": model, "segment": segment, "n": len(part), **values})
    return pd.DataFrame(rows)


def compare(predictions: pd.DataFrame, baseline: str, candidate: str, block_days: int = 28,
            n_boot: int = 2000, coverage: float = 0.9, seed: int = 0) -> Dict[str, float]:
    """WAPE difference (candidate - baseline, percentage points; negative = candidate better) over
    every fold's rows of `predictions`, with a moving-block bootstrap interval: dates are resampled
    in blocks of `block_days` consecutive days, shared by both models and every fold, so serial
    correlation and overlapping folds stay inside a block. Also the share of folds whose own
    difference has the same sign. A difference counts only if the interval excludes 0 and the sign
    holds in most folds."""
    keys = ["fold", "row"]
    a = predictions[predictions["model"] == baseline].set_index(keys)
    b = predictions[predictions["model"] == candidate].set_index(keys)
    joined = a[["date", "actual", "pred"]].join(b[["pred"]], rsuffix="_b", how="inner")
    if joined.empty:
        raise ValueError(f"No rows scored by both {baseline!r} and {candidate!r}")
    gain = (joined["pred_b"] - joined["actual"]).abs() - (joined["pred"] - joined["actual"]).abs()
    by_day = pd.DataFrame({"gain": gain.to_numpy(), "actual": joined["actual"].to_numpy()},
                          index=pd.to_datetime(joined["date"]).to_numpy()).groupby(level=0).sum()
    days = pd.date_range(by_day.index.min(), by_day.index.max(), freq="D")
    by_day = by_day.reindex(days, fill_value=0.0)
    gain_day, actual_day = by_day["gain"].to_numpy(), by_day["actual"].to_numpy()
    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(len(days) / block_days))
    starts = rng.integers(0, max(len(days) - block_days, 0) + 1, size=(n_boot, n_blocks))
    index = (starts[:, :, None] + np.arange(block_days)).reshape(n_boot, -1)[:, :len(days)]
    draws = gain_day[index].sum(axis=1) / actual_day[index].sum(axis=1) * 100
    difference = float(gain_day.sum() / actual_day.sum() * 100)
    per_fold = (gain.groupby(level="fold").sum() / joined["actual"].groupby(level="fold").sum()) * 100
    tail = (1 - coverage) / 2
    return {"difference_pp": difference, "ci_low": float(np.quantile(draws, tail)), "ci_high": float(np.quantile(draws, 1 - tail)),
            "share_folds_same_sign": float((np.sign(per_fold) == np.sign(difference)).mean()), "folds": int(len(per_fold))}
