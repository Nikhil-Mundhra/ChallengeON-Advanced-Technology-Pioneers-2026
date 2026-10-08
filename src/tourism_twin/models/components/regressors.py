"""LinearRegressors: a centred linear effect of named columns or registered features."""

from __future__ import annotations

from typing import Any, Dict, Iterable

import pandas as pd

from tourism_twin.models.components.base import LinearComponent


class LinearRegressors(LinearComponent):
    def __init__(self, features: Iterable[str], name: str = "regressors") -> None:
        super().__init__()
        self.name = name
        self.requires = tuple(features)

    def design(self, panel: pd.DataFrame) -> pd.DataFrame:
        return panel.loc[:, list(self.requires)]

    def explain(self) -> Dict[str, Any]:
        return {"coef": dict(zip(self.requires, self.coef_.tolist()))}
