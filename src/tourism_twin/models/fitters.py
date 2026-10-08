"""Fitters for a set of components sharing one log-scale target.

JointLinear: all components linear; their designs are stacked and solved in one least squares.
Backfitting: block coordinate descent. Each block is refitted on y minus every other block's
contribution until the largest contribution change is below `tol`. With joint_linear=True the
linear components form one jointly-solved block, so only non-linear components cycle.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence

import numpy as np
import pandas as pd

from tourism_twin.models.components.base import Component, LinearComponent, solve_linear_block


@dataclass
class FitReport:
    iterations: int
    converged: bool
    max_change: float


class JointLinear:
    def fit(self, components: Sequence[Component], panel: pd.DataFrame, y: pd.Series) -> FitReport:
        nonlinear = [c.name for c in components if not isinstance(c, LinearComponent)]
        if nonlinear:
            raise TypeError(f"JointLinear needs linear components only; got {nonlinear}. Use Backfitting.")
        solve_linear_block(list(components), panel, y)
        return FitReport(iterations=1, converged=True, max_change=0.0)


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
                    max_change = max(max_change, float((updated - contributions[component.name]).abs().max()))
                    contributions[component.name] = updated
            if max_change < self.tol:
                return FitReport(iterations=iteration, converged=True, max_change=max_change)
        return FitReport(iterations=self.max_iter, converged=False, max_change=max_change)
