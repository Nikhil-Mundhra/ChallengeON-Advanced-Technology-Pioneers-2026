"""DayOfWeek: one effect per weekday (Monday is the reference), optionally per season."""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from tourism_twin.domain.seasons import SEASONS, assign_season
from tourism_twin.models.components.base import LinearComponent

DAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


class DayOfWeek(LinearComponent):
    def __init__(self, by_season: bool = False, name: str = "weekday", date_column: str = "date") -> None:
        super().__init__()
        self.by_season = by_season
        self.name = name
        self.date_column = date_column
        self.requires = (date_column,)

    def design(self, panel: pd.DataFrame) -> pd.DataFrame:
        dates = pd.to_datetime(panel[self.date_column])
        dow = dates.dt.dayofweek
        columns = {f"{DAY_NAMES[d]}": (dow == d).astype(float) for d in range(1, 7)}
        if self.by_season:
            season = dates.dt.month.map(assign_season)
            for s in SEASONS[1:]:
                for d in range(1, 7):
                    columns[f"{DAY_NAMES[d]}x{s}"] = ((dow == d) & (season == s)).astype(float)
        return pd.DataFrame(columns, index=panel.index)

    def explain(self) -> Dict[str, Any]:
        self._require_fitted()
        columns = list(self.design(pd.DataFrame({self.date_column: pd.date_range("2024-01-01", periods=1)})).columns)
        return {"effect_log_vs_monday": dict(zip(columns, self.coef_.tolist()))}
