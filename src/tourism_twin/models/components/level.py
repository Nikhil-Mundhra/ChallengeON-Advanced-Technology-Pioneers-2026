"""LocalLevel: a slowly varying level, the smoothed state of a local linear trend.

One coefficient per day between the first and last training day, with a second-difference penalty
of strength `smoothing`: minimise |r - z|^2 + smoothing * |D2 z|^2. This is the Whittaker
(Hodrick-Prescott) smoother, equal to the Kalman-smoothed level of an integrated-random-walk trend
with signal-to-noise ratio 1/smoothing, without a state-space dependency. Being linear, it is
solved jointly with the other linear components (one exact solve instead of backfitting).
Owns the level. After the last training day the level stays flat; with extrapolate_slope=True
it continues along the slope of the last `slope_window` days. The end slope of the smoother is
its least stable estimate (over a 6-month horizon it moved forecasts by -26% to +8% across
back-test folds), so flat is the default. The split between this level and the season depends on
`smoothing` (the penalty, not the data, fixes it), so read their explain() values together.
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd

from tourism_twin.models.components.base import LinearComponent


class LocalLevel(LinearComponent):
    owns_level = True

    def __init__(self, smoothing: float = 1e5, slope_window: int = 28, extrapolate_slope: bool = False,
                 name: str = "level", date_column: str = "date") -> None:
        super().__init__()
        self.smoothing = smoothing
        self.slope_window = slope_window
        self.extrapolate_slope = extrapolate_slope
        self.name = name
        self.date_column = date_column
        self.requires = (date_column,)
        self.days_: pd.DatetimeIndex | None = None

    def reset(self) -> None:
        super().reset()
        self.days_ = None

    def design(self, panel: pd.DataFrame) -> pd.DataFrame:
        """One-hot of each row's day on the training-day grid (fixed by the first, fitting call)."""
        dates = pd.to_datetime(panel[self.date_column])
        if self.days_ is None:
            self.days_ = pd.date_range(dates.min(), dates.max(), freq="D")
        position = self.days_.get_indexer(dates)
        if (position < 0).any():
            raise ValueError(f"Component {self.name!r}: design() only covers training days; use contribution()")
        onehot = np.zeros((len(dates), len(self.days_)))
        onehot[np.arange(len(dates)), position] = 1.0
        return pd.DataFrame(onehot, index=panel.index, columns=self.days_.strftime("%Y-%m-%d"))

    def penalty_rows(self) -> np.ndarray | None:
        n = len(self.days_)
        return np.sqrt(self.smoothing) * np.diff(np.eye(n), 2, axis=0) if n >= 3 else None

    def _slope(self) -> float:
        tail = self.coef_[-min(self.slope_window, len(self.coef_)):]
        return float(np.polyfit(np.arange(len(tail)), tail, 1)[0]) if len(tail) > 1 else 0.0

    def contribution(self, panel: pd.DataFrame) -> pd.Series:
        self._require_fitted()
        dates = pd.to_datetime(panel[self.date_column])
        first, last = self.days_[0], self.days_[-1]
        level = pd.Series(self.coef_, index=self.days_).reindex(dates.clip(first, last)).to_numpy()
        ahead = np.clip((dates - last).dt.days.to_numpy(), 0, None)
        slope = self._slope() if self.extrapolate_slope else 0.0
        return pd.Series(level + slope * ahead, index=panel.index, name=self.name)

    def explain(self) -> Dict[str, Any]:
        self._require_fitted()
        return {"last_level_log": float(self.coef_[-1]), "slope_log_per_day": self._slope(),
                "smoothing": self.smoothing, "fitted_through": str(self.days_[-1].date())}
