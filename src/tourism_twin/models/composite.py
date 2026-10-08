"""AdditiveLogModel: target = exp(sum of component contributions), fitted per group.

Components declare the columns they need; names registered in PANEL_FEATURES are computed on
demand. Exactly one component must own the level (the others are centred).
"""

from __future__ import annotations

import copy
from typing import Any, Dict, Hashable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from tourism_twin.features import PANEL_FEATURES
from tourism_twin.models.components.base import Component
from tourism_twin.models.fitters import Backfitting, FitReport, JointLinear


class AdditiveLogModel:
    def __init__(
        self,
        components: Sequence[Component],
        fitter: Optional[JointLinear | Backfitting] = None,
        group_by: Optional[str] = "market",
        target: str = "guests",
        feature_params: Optional[Dict[str, Any]] = None,
    ) -> None:
        names = [c.name for c in components]
        if len(set(names)) != len(names):
            raise ValueError(f"Component names must be unique: {names}")
        level_owners = [c.name for c in components if c.owns_level]
        if len(level_owners) != 1:
            raise ValueError(f"Exactly one component must own the level; got {level_owners}")
        self.components = list(components)
        self.fitter = fitter or Backfitting()
        self.group_by = group_by
        self.target = target
        self.feature_params = feature_params or {"anchor": "date"}
        self.fitted_: Dict[Hashable, Tuple[List[Component], FitReport]] = {}

    def _with_features(self, panel: pd.DataFrame) -> pd.DataFrame:
        needed = {r for c in self.components for r in c.requires if r not in panel.columns}
        registered = [name for name in needed if name in PANEL_FEATURES]
        missing = needed - set(registered)
        if missing:
            raise KeyError(f"Columns not in panel and not registered features: {sorted(missing)}")
        return PANEL_FEATURES.apply(panel, registered, **self.feature_params) if registered else panel

    def _groups(self, panel: pd.DataFrame):
        if self.group_by is None:
            return [(None, panel)]
        return list(panel.groupby(self.group_by, sort=True))

    def fit(self, panel: pd.DataFrame) -> "AdditiveLogModel":
        panel = self._with_features(panel)
        train = panel[panel[self.target].notna()]
        self.fitted_ = {}
        for key, rows in self._groups(train):
            components = copy.deepcopy(self.components)
            for component in components:
                if hasattr(component, "reset"):
                    component.reset()
            report = self.fitter.fit(components, rows, np.log(rows[self.target]))
            self.fitted_[key] = (components, report)
        return self

    def decompose(self, panel: pd.DataFrame) -> pd.DataFrame:
        """Log-scale contribution of each component, one column per component."""
        panel = self._with_features(panel)
        parts = []
        for key, rows in self._groups(panel):
            if key not in self.fitted_:
                raise KeyError(f"No fitted model for group {key!r}")
            components, _ = self.fitted_[key]
            parts.append(pd.DataFrame({c.name: c.contribution(rows) for c in components}, index=rows.index))
        return pd.concat(parts).reindex(panel.index)

    def predict(self, panel: pd.DataFrame) -> pd.Series:
        return np.exp(self.decompose(panel).sum(axis=1)).rename(f"{self.target}_pred")

    def explain(self) -> Dict[Hashable, Dict[str, Any]]:
        return {
            key: {"fit": vars(report), **{c.name: c.explain() for c in components}}
            for key, (components, report) in self.fitted_.items()
        }
