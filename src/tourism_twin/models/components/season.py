"""AnnualFourier: smooth yearly seasonality as H sine/cosine pairs of the day of year."""

from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd

from tourism_twin.models.components.base import LinearComponent

YEAR_DAYS = 365.25


class AnnualFourier(LinearComponent):
    def __init__(self, harmonics: int = 4, name: str = "season", date_column: str = "date") -> None:
        super().__init__()
        self.harmonics = harmonics
        self.name = name
        self.date_column = date_column
        self.requires = (date_column,)

    def design(self, panel: pd.DataFrame) -> pd.DataFrame:
        day = pd.to_datetime(panel[self.date_column]).dt.dayofyear.to_numpy()
        columns = {}
        for h in range(1, self.harmonics + 1):
            angle = 2 * np.pi * h * day / YEAR_DAYS
            columns[f"sin{h}"], columns[f"cos{h}"] = np.sin(angle), np.cos(angle)
        return pd.DataFrame(columns, index=panel.index)

    def explain(self) -> Dict[str, Any]:
        self._require_fitted()
        amplitudes = {h: float(np.hypot(*self.coef_[2 * (h - 1):2 * h])) for h in range(1, self.harmonics + 1)}
        return {"amplitude_log_by_harmonic": amplitudes}
