"""Fitters for a set of components sharing one log-scale target.

JointLinear: all components linear; their designs are stacked and solved in one least squares.
Backfitting: block coordinate descent. Each block is refitted on y minus every other block's
contribution until the largest contribution change is below `tol`. With joint_linear=True the
linear components form one jointly-solved block, so only non-linear components cycle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd

from tourism_twin.models.components.base import Component, LinearComponent, solve_linear_block


@dataclass
class FitReport:
    iterations: int
    converged: bool
    max_change: float
    rank: int = 0
    columns: int = 0
    unidentified: List[str] = field(default_factory=list)

    @property
    def rank_deficient(self) -> bool:
        """The linear components' stacked design does not determine every coefficient (overlapping
        or constant columns); the decomposition then depends on penalties or fitter order."""
        return self.rank < self.columns


def _linear_diagnostics(components: Sequence[Component], panel: pd.DataFrame) -> Tuple[int, int, List[str]]:
    linear = [c for c in components if isinstance(c, LinearComponent)]
    if not linear:
        return 0, 0, []
    stacked = np.hstack([c.prepare(panel).to_numpy() for c in linear])
    unidentified = [f"{c.name}:{col}" for c in linear for col in c.unidentified_]
    return int(np.linalg.matrix_rank(stacked)), stacked.shape[1], unidentified


class JointLinear:
    def fit(self, components: Sequence[Component], panel: pd.DataFrame, y: pd.Series) -> FitReport:
        nonlinear = [c.name for c in components if not isinstance(c, LinearComponent)]
        if nonlinear:
            raise TypeError(f"JointLinear needs linear components only; got {nonlinear}. Use Backfitting.")
        diagnostics = solve_linear_block(list(components), panel, y)
        return FitReport(1, True, 0.0, diagnostics.rank, diagnostics.columns, diagnostics.unidentified)


class Backfitting:
    def __init__(self, max_iter: int = 200, tol: float = 1e-8, joint_linear: bool = True) -> None:
        self.max_iter = max_iter
        self.tol = tol
        self.joint_linear = joint_linear

    def _blocks(self, components: Sequence[Component]) -> List[List[Component]]:
        if not self.joint_linear:
            return [[c] for c in components]
        linear = [c for c in components if isinstance(c, LinearComponent)]
        others = [[c] for c in components if not isinstance(c, LinearComponent)]
        return ([linear] if linear else []) + others

    def fit(self, components: Sequence[Component], panel: pd.DataFrame, y: pd.Series) -> FitReport:
        contributions: Dict[str, pd.Series] = {c.name: pd.Series(0.0, index=panel.index) for c in components}
        max_change = np.inf
        converged, iterations = False, self.max_iter
        for iteration in range(1, self.max_iter + 1):
            max_change = 0.0
            for block in self._blocks(components):
                names = {c.name for c in block}
                offset = sum((s for n, s in contributions.items() if n not in names), pd.Series(0.0, index=panel.index))
                if self.joint_linear and all(isinstance(c, LinearComponent) for c in block):
                    solve_linear_block(block, panel, y - offset)
                else:
                    block[0].fit(panel, offset, y)
                for component in block:
                    updated = component.contribution(panel)
                    if not np.isfinite(updated.to_numpy()).all():
                        raise ValueError(f"Component {component.name!r} produced non-finite contributions")
                    max_change = max(max_change, float((updated - contributions[component.name]).abs().max()))
                    contributions[component.name] = updated
            if max_change < self.tol:
                converged, iterations = True, iteration
                break
        rank, columns, unidentified = _linear_diagnostics(components, panel)
        return FitReport(iterations, converged, max_change, rank, columns, unidentified)
