"""Evaluate an already-fitted model on new rows, without refitting.

    fitted model + ModelCard ──► save_model / load_model (pickle, with the card)
    load ──► evaluate_fitted(model, rows, card) ──► Scorecard
                 predict only; rows on or before card.train_end are refused (no leakage)
                 metrics per segment (domestic / international, never pooled) at three grains:
                 day, ISO week total, calendar month total; error by horizon; direction of
                 consecutive period totals; interval coverage when intervals are given;
                 optionally per entity (market or nationality) via group_column

Training lives in the fitters and the back-test harness (models/backtest.py refits per fold);
this module only measures a fixed model, so the score is the score of exactly what was saved.
"""

from __future__ import annotations

import pickle
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

from tourism_twin.models.backtest import forecast_metrics, segment_of
from tourism_twin.models.protocol import Model

GRAINS = {"day": None, "week": "W-SUN", "month": "M"}
HORIZON_BUCKETS = (0, 30, 60, 90, 120, 150, 185)  # days after the first evaluated day


@dataclass(frozen=True)
class ModelCard:
    """What a saved model was trained on; travels with the pickle."""

    spec: str
    train_start: str
    train_end: str          # last training date (inclusive)
    rows: int
    markets: Tuple[str, ...]  # entities the model was trained on (markets, or nationalities)
    fitted_at: str


def card_for(spec: str, train: pd.DataFrame, date_column: str = "date", entity_column: str = "market") -> ModelCard:
    dates = pd.to_datetime(train[date_column])
    return ModelCard(spec=spec, train_start=str(dates.min().date()), train_end=str(dates.max().date()),
                     rows=int(len(train)), markets=tuple(sorted(train[entity_column].astype(str).unique())),
                     fitted_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))


def save_model(model: Model, card: ModelCard, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        pickle.dump({"card": asdict(card), "model": model}, handle)
    return path


def load_model(path: Path) -> Tuple[Model, ModelCard]:
    with Path(path).open("rb") as handle:
        payload = pickle.load(handle)
    card = payload["card"]
    return payload["model"], ModelCard(**{**card, "markets": tuple(card["markets"])})


def error_metrics(actual: np.ndarray, pred: np.ndarray) -> Dict[str, float]:
    """WAPE, bias, MAE, RMSE (forecast_metrics) plus MSE and MSE of log values."""
    actual, pred = np.asarray(actual, dtype=float), np.asarray(pred, dtype=float)
    out = forecast_metrics(actual, pred)
    out["mse"] = float(np.mean((actual - pred) ** 2))
    positive = (actual > 0) & (pred > 0)
    out["log_mse"] = float(np.mean((np.log(actual[positive]) - np.log(pred[positive])) ** 2)) if positive.any() else float("nan")
    return out


@dataclass
class Scorecard:
    card: Optional[ModelCard]
    rows: pd.DataFrame        # market, segment, date, horizon_days, actual, pred (+ lower, upper)
    metrics: pd.DataFrame     # segment, grain, n, wmape, bias, mae, rmse, mse, log_mse
    by_horizon: pd.DataFrame  # segment, horizon bucket, n, wmape
    direction: pd.DataFrame   # segment, grain, n, hit_rate (sign of change between consecutive totals)
    coverage: pd.DataFrame    # segment, n, coverage (empty without intervals)
    by_group: pd.DataFrame = None  # group, n, metrics on daily values per entity (when group_column is given)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "card": asdict(self.card) if self.card else None,
            "window": [str(self.rows["date"].min().date()), str(self.rows["date"].max().date())],
            "metrics": self.metrics.round(6).to_dict("records"),
            "by_horizon": self.by_horizon.round(6).to_dict("records"),
            "direction": self.direction.round(6).to_dict("records"),
            "coverage": self.coverage.round(6).to_dict("records"),
            "by_group": [] if self.by_group is None else self.by_group.round(6).to_dict("records"),
        }


def _totals(rows: pd.DataFrame, grain: str) -> pd.DataFrame:
    """Segment totals per period; weeks and months are kept only if every day is present."""
    freq = GRAINS[grain]
    daily = rows.groupby(["segment", "date"])[["actual", "pred"]].sum().reset_index()
    if freq is None:
        return daily.rename(columns={"date": "period"})
    daily["period"] = daily["date"].dt.to_period(freq)
    grouped = daily.groupby(["segment", "period"])
    totals = grouped[["actual", "pred"]].sum()
    days = grouped["date"].nunique()
    expected = totals.index.get_level_values("period").map(lambda p: (p.end_time.normalize() - p.start_time.normalize()).days + 1)
    return totals[days.to_numpy() == np.asarray(expected)].reset_index()


def evaluate_fitted(
    model: Model,
    panel: pd.DataFrame,
    card: Optional[ModelCard] = None,
    target: str = "guests",
    date_column: str = "date",
    intervals: Optional[pd.DataFrame] = None,
    allow_overlap: bool = False,
    group_column: Optional[str] = None,
) -> Scorecard:
    """Score a fitted model on `panel` rows with an observed target. `intervals` (optional) is
    indexed like `panel` with columns lower and upper. `group_column` (e.g. "nationality") adds a
    per-entity table of daily metrics; segments come from `market` when present, else
    every row counts as international (nationality-grain panels)."""
    rows = panel[panel[target].notna()]
    dates = pd.to_datetime(rows[date_column])
    if card is not None and not allow_overlap:
        overlap = int((dates <= pd.Timestamp(card.train_end)).sum())
        if overlap:
            raise ValueError(f"{overlap} rows are on or before the model's last training day {card.train_end}; "
                             "evaluate on later rows (or pass allow_overlap=True for an in-sample check)")
    if rows.empty:
        raise ValueError("No rows with an observed target to evaluate")
    pred = model.predict(rows)
    if pred.isna().any():
        raise ValueError(f"Model returned {int(pred.isna().sum())} missing predictions")
    start = pd.Timestamp(card.train_end) + np.timedelta64(1, "D") if card is not None else dates.min()
    scored = pd.DataFrame({
        "market": rows["market"].to_numpy() if "market" in rows else np.full(len(rows), "INTERNATIONAL"),
        "segment": segment_of(rows["market"]) if "market" in rows else np.full(len(rows), "international"),
        "date": dates.to_numpy(),
        "horizon_days": (dates - start).dt.days.to_numpy(), "actual": rows[target].to_numpy(dtype=float),
        "pred": pred.to_numpy(dtype=float),
    }, index=rows.index)
    if intervals is not None:
        scored = scored.join(intervals[["lower", "upper"]], how="left")

    metrics, direction = [], []
    for grain in GRAINS:
        totals = _totals(scored, grain)
        for segment, part in totals.groupby("segment"):
            metrics.append({"segment": segment, "grain": grain, "n": len(part), **error_metrics(part["actual"], part["pred"])})
            if len(part) > 1:
                actual_change, pred_change = np.sign(np.diff(part["actual"])), np.sign(np.diff(part["pred"]))
                direction.append({"segment": segment, "grain": grain, "n": len(actual_change),
                                  "hit_rate": float((actual_change == pred_change).mean())})

    bucket = pd.cut(scored["horizon_days"], HORIZON_BUCKETS, right=False)
    horizon = (scored.assign(bucket=bucket.astype(str)).groupby(["segment", "bucket", "date"])[["actual", "pred"]].sum()
               .groupby(level=["segment", "bucket"])
               .apply(lambda g: pd.Series({"n": len(g), "wmape": (g["pred"] - g["actual"]).abs().sum() / g["actual"].sum()}))
               .reset_index())

    coverage = pd.DataFrame(columns=["segment", "n", "coverage"])
    if intervals is not None:
        covered = scored.dropna(subset=["lower", "upper"])
        inside = (covered["actual"] >= covered["lower"]) & (covered["actual"] <= covered["upper"])
        coverage = inside.groupby(covered["segment"]).agg(["size", "mean"]).rename(columns={"size": "n", "mean": "coverage"}).reset_index()

    by_group = None
    if group_column is not None:
        scored[group_column] = rows[group_column].to_numpy()
        by_group = pd.DataFrame([{group_column: key, "n": len(part), **error_metrics(part["actual"], part["pred"])}
                                 for key, part in scored.groupby(group_column)])

    return Scorecard(card, scored, pd.DataFrame(metrics), horizon, pd.DataFrame(direction), coverage, by_group)
