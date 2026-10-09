"""Serving the nowcast without refitting (issue #7): `twin predict` writes a small JSON bundle
(daily predictions per series, recent actual guests, the noise model's AR(1) parameters, and
nationality predictions); NowcastService answers date-range questions from it.

A range total's interval comes from NoiseModel.range_interval (AR(1) covariance across the
range's days). Its direction is stated against the same-length range just before it (actual
guests for training days, predictions for test days) only when the change is at least
DIRECTION_THRESHOLD: over 2-week ranges the direction is right about 90% of the time but the size
of the change is off by 3-4 pp (docs/model_design.md §4.8).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from tourism_twin.models.noise import NoiseModel
from tourism_twin.nowcast.predict import INTERNATIONAL, TOTAL, TestPredictions, total_series

DIRECTION_THRESHOLD = 0.08
HISTORY_DAYS = 400  # actuals kept for comparing a test range with the range before it


def build_bundle(predictions: TestPredictions, history: pd.DataFrame, spec: str, coverage: float = 0.8) -> Dict[str, Any]:
    """The serving bundle. history: the daily training panel (market, date, guests)."""
    if predictions.noise is None:
        raise ValueError("the serving bundle needs predictions with intervals (a fitted noise model)")
    daily = predictions.market_daily
    series = pd.concat([daily, total_series(daily), total_series(daily, INTERNATIONAL)], ignore_index=True)
    actual = history[["market", "date", "guests"]].dropna()
    actual = actual[actual["date"] > actual["date"].max() - np.timedelta64(HISTORY_DAYS, "D")].rename(columns={"guests": "actual"})
    actual = pd.concat([actual, total_series(actual.assign(pred=0.0))[["market", "date", "actual"]],
                        total_series(actual.assign(pred=0.0), INTERNATIONAL)[["market", "date", "actual"]]], ignore_index=True)
    noise = predictions.noise
    nationalities = predictions.international[["Date", "Nationality", "Guests"]]
    return {
        "spec": spec, "coverage": coverage,
        "test_start": str(daily["date"].min().date()), "test_end": str(daily["date"].max().date()),
        "series": {name: {"date": [str(d.date()) for d in rows["date"]], "horizon_days": rows["horizon_days"].astype(int).tolist(),
                          "pred": rows["pred"].round(3).tolist()}
                   for name, rows in series.sort_values("date").groupby("market")},
        "history": {name: {"date": [str(d.date()) for d in rows["date"]], "guests": rows["actual"].tolist()}
                    for name, rows in actual.sort_values("date").groupby("market")},
        "noise": {name: {"phi": noise.phi_[name], "sigma_eta": noise.sigma_eta_[name], "v0": noise.v0_[name]}
                  for name in series["market"].unique() if name in noise.phi_},
        "nationalities": {name: {"date": [str(pd.Timestamp(d).date()) for d in rows["Date"]], "pred": rows["Guests"].round(3).tolist()}
                          for name, rows in nationalities.sort_values("Date").groupby("Nationality")},
    }


def save_bundle(bundle: Dict[str, Any], path: Path) -> Path:
    path.write_text(json.dumps(bundle), encoding="utf-8")
    return path


class NowcastService:
    """Date-range answers from a serving bundle (no model in memory)."""

    def __init__(self, bundle: Dict[str, Any]) -> None:
        self.bundle = bundle
        self.coverage = bundle["coverage"]
        self.test_start, self.test_end = pd.Timestamp(bundle["test_start"]), pd.Timestamp(bundle["test_end"])
        self.noise = NoiseModel(phi_={k: v["phi"] for k, v in bundle["noise"].items()},
                                sigma_eta_={k: v["sigma_eta"] for k, v in bundle["noise"].items()},
                                v0_={k: v["v0"] for k, v in bundle["noise"].items()})

    @classmethod
    def load(cls, path: Path) -> "NowcastService":
        return cls(json.loads(path.read_text(encoding="utf-8")))

    def series_names(self) -> List[str]:
        return sorted(self.bundle["series"])

    def _frame(self, name: str) -> pd.DataFrame:
        if name not in self.bundle["series"]:
            raise KeyError(f"Unknown series {name!r}; one of {self.series_names()}")
        values = self.bundle["series"][name]
        return pd.DataFrame({"date": pd.to_datetime(values["date"]), "horizon_days": values["horizon_days"], "pred": values["pred"]})

    def _window(self, start: str, end: str) -> tuple:
        start_ts, end_ts = pd.Timestamp(start), pd.Timestamp(end)
        if start_ts > end_ts:
            raise ValueError("start must not be after end")
        if start_ts < self.test_start or end_ts > self.test_end:
            raise ValueError(f"the range must lie in the predicted period {self.test_start.date()}..{self.test_end.date()}")
        return start_ts, end_ts

    def range_total(self, name: str, start: str, end: str) -> Dict[str, Any]:
        """Predicted total over [start, end] with its interval, and the change against the
        same-length range just before it."""
        start_ts, end_ts = self._window(start, end)
        frame = self._frame(name)
        days = frame[(frame["date"] >= start_ts) & (frame["date"] <= end_ts)]
        lower, upper = self.noise.range_interval(name, days["horizon_days"].to_numpy(float), days["pred"].to_numpy(float), self.coverage)
        total = float(days["pred"].sum())
        previous_start, previous_end = start_ts - (end_ts - start_ts) - np.timedelta64(1, "D"), start_ts - np.timedelta64(1, "D")
        previous = self._previous_total(name, frame, previous_start, previous_end)
        change = total / previous - 1 if previous else None
        direction = None if change is None else ("no clear change" if abs(change) < DIRECTION_THRESHOLD else ("up" if change > 0 else "down"))
        return {"series": name, "start": str(start_ts.date()), "end": str(end_ts.date()), "days": int(len(days)),
                "guests": round(total, 1), "p10": round(lower, 1), "p90": round(upper, 1), "coverage": self.coverage,
                "previous_start": str(previous_start.date()), "previous_end": str(previous_end.date()),
                "previous_guests": None if previous is None else round(previous, 1),
                "change": None if change is None else round(change, 4), "direction": direction,
                "direction_threshold": DIRECTION_THRESHOLD}

    def _previous_total(self, name: str, frame: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> float | None:
        """Actual guests for days before the test period, predictions for test days; None when a
        day of the previous range has neither."""
        history = self.bundle["history"].get(name, {"date": [], "guests": []})
        actual = pd.Series(history["guests"], index=pd.to_datetime(history["date"]), dtype=float)
        predicted = frame.set_index("date")["pred"]
        values = pd.concat([actual, predicted]).reindex(pd.date_range(start, end, freq="D"))
        return None if values.isna().any() else float(values.sum())

    def nationalities(self, start: str, end: str) -> List[Dict[str, Any]]:
        """Predicted guests per international nationality over [start, end] and their share of the
        international total (point predictions; no interval)."""
        start_ts, end_ts = self._window(start, end)
        totals = {}
        for name, values in self.bundle["nationalities"].items():
            dates, pred = pd.to_datetime(values["date"]), np.asarray(values["pred"], dtype=float)
            totals[name] = float(pred[(dates >= start_ts) & (dates <= end_ts)].sum())
        overall = sum(totals.values())
        return [{"nationality": name, "guests": round(value, 1), "share": round(value / overall, 4) if overall else None}
                for name, value in sorted(totals.items(), key=lambda item: -item[1])]
