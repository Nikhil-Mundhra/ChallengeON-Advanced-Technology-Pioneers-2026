"""ResidualGBM: gradient boosting on what the other components leave unexplained.

Fitted once, after the other components have converged (final stage), on y - offset with the
named feature columns; its contribution is centred over the training rows. Whether it stays in a
spec is decided by the back-test (an ablation spec without it), not by the component.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from tourism_twin.models.components.base import ComponentBase


class ResidualGBM(ComponentBase):
    owns_level = False
    final_stage = True
    group = "residual"

    def __init__(self, features: Iterable[str], name: str = "gbm", max_iter: int = 200, learning_rate: float = 0.05,
                 max_leaf_nodes: int = 15, random_state: int = 0) -> None:
        self.name = name
        self.requires = tuple(features)
        self.params = dict(max_iter=max_iter, learning_rate=learning_rate, max_leaf_nodes=max_leaf_nodes, random_state=random_state)
        self.reset()

    def reset(self) -> None:
        self.model_: HistGradientBoostingRegressor | None = None
        self.centre_ = 0.0

    def fit(self, panel: pd.DataFrame, offset: pd.Series, y: pd.Series,
            weights: Optional[np.ndarray] = None) -> "ResidualGBM":
        X = panel[list(self.requires)].to_numpy(dtype=float)
        self.model_ = HistGradientBoostingRegressor(**self.params).fit(X, (y - offset).to_numpy(), sample_weight=weights)
        self.centre_ = float(np.mean(self.model_.predict(X)))
        return self

    def contribution(self, panel: pd.DataFrame) -> pd.Series:
        if self.model_ is None:
            raise RuntimeError(f"Component {self.name!r} is not fitted")
        X = panel[list(self.requires)].to_numpy(dtype=float)
        return pd.Series(self.model_.predict(X) - self.centre_, index=panel.index, name=self.name)

    def explain(self) -> Dict[str, Any]:
        if self.model_ is None:
            raise RuntimeError(f"Component {self.name!r} is not fitted")
        return {"features": list(self.requires), "n_iter": int(self.model_.n_iter_)}
