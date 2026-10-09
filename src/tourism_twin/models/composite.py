"""AdditiveLogModel: target = exp(sum of component contributions), fitted per group.

Components declare the columns they need; names registered in PANEL_FEATURES are computed on
demand. Exactly one component must own the level. `anchor` is the date column used both for
registered calendar features and by date-aware components.

predict() returns exp(Σ contributions), the conditional median on the original scale. With
bias_correction="smearing" it is multiplied by each group's mean exp(training residual)
(Duan's smearing), an estimate of the conditional mean; use that when comparing with
level-scale models or summing groups.
"""

from __future__ import annotations

import copy
from typing import Any, Dict, Hashable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from tourism_twin.features import PANEL_FEATURES
from tourism_twin.models.components.base import Component
from tourism_twin.models.fitters import Backfitting, FitReport, JointLinear

BIAS_CORRECTIONS = ("none", "smearing")


class AdditiveLogModel:
    def __init__(
        self,
        components: Sequence[Component],
        fitter: Optional[JointLinear | Backfitting] = None,
        group_by: Optional[str] = "market",
        target: str = "guests",
        anchor: str = "date",
        feature_params: Optional[Dict[str, Any]] = None,
        exclude_flag: Optional[str] = None,
        include_flag: Optional[str] = None,
        bias_correction: str = "none",
    ) -> None:
        names = [c.name for c in components]
        if len(set(names)) != len(names):
            raise ValueError(f"Component names must be unique: {names}")
        level_owners = [c.name for c in components if c.owns_level]
        if len(level_owners) != 1:
            raise ValueError(f"Exactly one component must own the level; got {level_owners}")
        mismatched = [c.name for c in components if getattr(c, "date_column", anchor) != anchor]
        if mismatched:
            raise ValueError(f"Components {mismatched} use a date column other than anchor={anchor!r}")
        if bias_correction not in BIAS_CORRECTIONS:
            raise ValueError(f"bias_correction must be one of {BIAS_CORRECTIONS}")
        self.components = list(components)
        self.fitter = fitter or Backfitting()
        self.group_by = group_by
        self.target = target
        self.anchor = anchor
        self.feature_params = {"anchor": anchor, **(feature_params or {})}
        self.exclude_flag = exclude_flag
        self.include_flag = include_flag
        self.bias_correction = bias_correction
        self.fitted_: Dict[Hashable, Tuple[List[Component], FitReport]] = {}
        self.smearing_: Dict[Hashable, float] = {}

    def _with_features(self, panel: pd.DataFrame) -> pd.DataFrame:
        if not panel.index.is_unique:
            raise ValueError("Panel index must be unique (reset_index after concatenating frames)")
        needed = {r for c in self.components for r in c.requires if r not in panel.columns}
        for flag in (self.exclude_flag, self.include_flag):
            if flag and flag not in panel.columns:
                needed.add(flag)
        registered = [name for name in needed if name in PANEL_FEATURES]
        missing = needed - set(registered)
        if missing:
            raise KeyError(f"Columns not in panel and not registered features: {sorted(missing)}")
        return PANEL_FEATURES.apply(panel, registered, **self.feature_params) if registered else panel

    def _groups(self, panel: pd.DataFrame):
        if self.group_by is None:
            return [(None, panel)]
        if panel[self.group_by].isna().any():
            raise ValueError(f"{int(panel[self.group_by].isna().sum())} rows have no {self.group_by!r}")
        return list(panel.groupby(self.group_by, sort=True))

    def fit(self, panel: pd.DataFrame) -> "AdditiveLogModel":
        panel = self._with_features(panel)
        train = panel[panel[self.target].notna()]
        if self.exclude_flag:
            train = train[train[self.exclude_flag] != 1]
        if self.include_flag:
            train = train[train[self.include_flag].astype(bool)]
        non_positive = int((train[self.target] <= 0).sum())
        if non_positive:
            raise ValueError(f"{non_positive} training rows have {self.target} <= 0; the log target needs positive values")
        origin = pd.to_datetime(train[self.anchor]).min() if self.anchor in train.columns else None
        self.fitted_, self.smearing_ = {}, {}
        for key, rows in self._groups(train):
            components = copy.deepcopy(self.components)
            for component in components:
                if hasattr(component, "reset"):
                    component.reset()
                if origin is not None and hasattr(component, "set_default_origin"):
                    component.set_default_origin(origin)
            y = np.log(rows[self.target])
            report = self.fitter.fit(components, rows, y)
            self.fitted_[key] = (components, report)
            fitted = sum(c.contribution(rows) for c in components)
            self.smearing_[key] = float(np.mean(np.exp(y - fitted)))
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
        decomposition = pd.concat(parts).reindex(panel.index)
        missing = decomposition.isna().sum()
        if missing.any():
            raise ValueError(f"Missing contributions: {missing[missing > 0].to_dict()}")
        return decomposition

    def decompose_by_group(self, panel: pd.DataFrame) -> pd.DataFrame:
        """Log-scale contribution of each block (flow, time, holiday, flight, residual)."""
        groups = {c.name: c.group for c in self.components}
        parts = self.decompose(panel)
        return parts.T.groupby(parts.columns.map(groups), sort=False).sum().T

    def predict(self, panel: pd.DataFrame) -> pd.Series:
        decomposition = self.decompose(panel)
        prediction = np.exp(decomposition.sum(axis=1, skipna=False))
        if self.bias_correction == "smearing":
            if self.group_by is None:
                prediction = prediction * self.smearing_[None]
            else:
                prediction = prediction * panel[self.group_by].map(self.smearing_).astype(float)
        return prediction.rename(f"{self.target}_pred")

    def diagnostics(self) -> Dict[str, int]:
        """Counts the back-test harness records per fold: fits, and fits that hit max_iter."""
        reports = [report for _, report in self.fitted_.values()]
        return {"fits": len(reports), "non_converged": sum(not r.converged for r in reports)}

    def explain(self) -> Dict[Hashable, Dict[str, Any]]:
        return {
            key: {
                "fit": {**vars(report), "rank_deficient": report.rank_deficient},
                "smearing_factor": self.smearing_.get(key),
                **{c.name: c.explain() for c in components},
            }
            for key, (components, report) in self.fitted_.items()
        }
