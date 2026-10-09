"""LinearTrend: intercept plus slope per year. Owns the level."""

from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from tourism_twin.models.components.base import LinearComponent


class LinearTrend(LinearComponent):
    owns_level = True

    def __init__(self, name: str = "trend", date_column: str = "date", origin: Optional[str] = None) -> None:
        super().__init__()
        self.name = name
        self.date_column = date_column
        self.requires = (date_column,)
        self.origin = origin
        self.origin_: pd.Timestamp | None = pd.Timestamp(origin) if origin else None

    def set_default_origin(self, origin: pd.Timestamp) -> None:
        """Use a common origin (e.g. the earliest training date of all groups) unless one was given,
        so intercepts are comparable across groups."""
        if self.origin_ is None:
            self.origin_ = pd.Timestamp(origin)

    def design(self, panel: pd.DataFrame) -> pd.DataFrame:
        dates = pd.to_datetime(panel[self.date_column])
        if self.origin_ is None:
            self.origin_ = dates.min()
        years = (dates - self.origin_).dt.days / 365.25
        return pd.DataFrame({"intercept": 1.0, "slope_per_year": years}, index=panel.index)

    def explain(self) -> Dict[str, Any]:
        self._require_fitted()
        intercept, slope = self.coef_
        return {"intercept": float(intercept), "slope_per_year": float(slope), "origin": str(self.origin_.date())}

    def reset(self) -> None:
        super().reset()
        self.origin_ = pd.Timestamp(self.origin) if self.origin else None


class CentredSlope(LinearComponent):
    """A log-linear trend that does not own the level: years since the first training day,
    centred over the training rows. Used with a level-owning component such as the arrivals kernel.

    Beyond the last training day the trend is damped when damping_days is set: time advances as
    H * (1 - exp(-d / H)) after d days (H = damping_days), so the extrapolated change levels off at
    H days' worth of slope; damping_days=0 (default) holds the trend flat; None extrapolates linearly.
    Flat won on 13 domestic rolling origins: daily WAPE 5.46 vs 5.97 linear (90-day damping 5.66),
    bias -0.36% vs -2.61%; the 2023-24 decline it was fitted on levelled off in 2025."""

    def __init__(self, name: str = "slope", date_column: str = "date", damping_days: float | None = 0.0) -> None:
        super().__init__()
        self.name = name
        self.date_column = date_column
        self.damping_days = damping_days
        self.requires = (date_column,)
        self.origin_: pd.Timestamp | None = None
        self.end_: pd.Timestamp | None = None

    def design(self, panel: pd.DataFrame) -> pd.DataFrame:
        dates = pd.to_datetime(panel[self.date_column])
        if self.origin_ is None:  # the first call is the fit
            self.origin_, self.end_ = dates.min(), dates.max()
        days = (dates - self.origin_).dt.days.to_numpy(dtype=float)
        if self.damping_days is not None:
            end = (self.end_ - self.origin_).days
            beyond = np.maximum(days - end, 0.0)
            damped = self.damping_days * (1 - np.exp(-beyond / self.damping_days)) if self.damping_days > 0 else 0.0 * beyond
            days = np.where(days > end, end + damped, days)
        return pd.DataFrame({"slope_per_year": days / 365.25}, index=panel.index)

    def explain(self) -> Dict[str, Any]:
        self._require_fitted()
        return {"slope_log_per_year": float(self.coef_[0])}

    def reset(self) -> None:
        super().reset()
        self.origin_ = None
        self.end_ = None
