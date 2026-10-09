"""GroupScale: one log-scale effect per level of a column (e.g. each nationality in a pooled fit),
shrunk toward the shared level by a ridge penalty, so a model fitted on many series shares its
shape while each series keeps its own scale. A level unseen in training gets the shared level."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from tourism_twin.models.components.base import LinearComponent


class GroupScale(LinearComponent):
    group = "flow"  # scales the flow of each series

    def __init__(self, column: str = "nationality", ridge: float = 10.0, name: str = "group_scale") -> None:
        super().__init__()
        self.column = column
        self.ridge = ridge
        self.name = name
        self.requires = (column,)
        self.levels_: Optional[List[str]] = None

    def design(self, panel: pd.DataFrame) -> pd.DataFrame:
        if self.levels_ is None:  # the first call is the fit
            self.levels_ = sorted(panel[self.column].dropna().unique())
        values = panel[self.column].to_numpy()
        return pd.DataFrame({level: (values == level).astype(float) for level in self.levels_}, index=panel.index)

    def penalty_rows(self) -> np.ndarray | None:
        return np.sqrt(self.ridge) * np.eye(len(self.levels_)) if self.levels_ and self.ridge > 0 else None

    def explain(self) -> Dict[str, Any]:
        self._require_fitted()
        return {"scale_log": dict(zip(self.levels_, self.coef_.tolist())), "ridge": self.ridge}

    def reset(self) -> None:
        super().reset()
        self.levels_ = None
