"""LinearTrend: intercept plus slope per year. Owns the level."""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from tourism_twin.models.components.base import LinearComponent


class LinearTrend(LinearComponent):
    owns_level = True

    def __init__(self, name: str = "trend", date_column: str = "date") -> None:
        super().__init__()
        self.name = name
        self.date_column = date_column
        self.requires = (date_column,)
        self.origin_: pd.Timestamp | None = None

    def design(self, panel: pd.DataFrame) -> pd.DataFrame:
        dates = pd.to_datetime(panel[self.date_column])
        if self.origin_ is None:
            self.origin_ = dates.min()
        years = (dates - self.origin_).dt.days / 365.25
        return pd.DataFrame({"intercept": 1.0, "slope_per_year": years}, index=panel.index)

    def explain(self) -> Dict[str, Any]:
        intercept, slope = self.coef_
        return {"intercept": float(intercept), "slope_per_year": float(slope), "origin": str(self.origin_.date())}

    def reset(self) -> None:
        super().reset()
        self.origin_ = None
