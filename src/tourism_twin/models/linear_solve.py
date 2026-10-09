"""Least-squares solve shared by the fitters and components: one block of linear components,
stacked and solved together with their penalty rows, optionally with per-row weights.
This is fitting math; components only provide designs and penalty rows."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional, Sequence

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from tourism_twin.models.components.base import LinearComponent


@dataclass
class BlockDiagnostics:
    rank: int
    columns: int
    unidentified: List[str] = field(default_factory=list)

    @property
    def rank_deficient(self) -> bool:
        return self.rank < self.columns


def row_scale(weights: Optional[np.ndarray], n: int) -> Optional[np.ndarray]:
    """sqrt of `weights` rescaled to mean 1 (so w and 3w fit identically), or None for unweighted."""
    if weights is None:
        return None
    w = np.asarray(weights, dtype=float)
    if w.shape != (n,) or not np.isfinite(w).all() or (w <= 0).any():
        raise ValueError(f"weights must be {n} finite positive values")
    return np.sqrt(w / w.mean())


def solve_linear_block(components: Sequence["LinearComponent"], panel: pd.DataFrame, target: pd.Series,
                       weights: Optional[np.ndarray] = None) -> BlockDiagnostics:
    """One least squares over the stacked designs, with each component's penalty rows appended.
    With `weights`, data rows (not penalty rows) are scaled by sqrt(weight): weighted least squares.

    A design column with no variation in the fitted rows carries no information; its coefficient
    is the minimum-norm (penalty-driven) value and the column is reported as unidentified.
    """
    designs = [component.prepare(panel) for component in components]
    stacked = np.hstack([design.to_numpy() for design in designs])
    rhs = target.to_numpy()
    if not np.isfinite(rhs).all():
        raise ValueError(f"Non-finite target values in {int((~np.isfinite(rhs)).sum())} rows")
    rank = int(np.linalg.matrix_rank(stacked)) if stacked.size else 0
    penalty_blocks, start = [], 0
    for component, design in zip(components, designs):
        width = design.shape[1]
        rows = component.penalty_rows()
        if rows is not None:
            block = np.zeros((rows.shape[0], stacked.shape[1]))
            block[:, start:start + width] = rows
            penalty_blocks.append(block)
        start += width
    scale = row_scale(weights, len(rhs))
    system, system_rhs = (stacked, rhs) if scale is None else (stacked * scale[:, None], rhs * scale)
    if penalty_blocks:
        system = np.vstack([system, *penalty_blocks])
        system_rhs = np.concatenate([system_rhs, np.zeros(sum(b.shape[0] for b in penalty_blocks))])
    coef, *_ = np.linalg.lstsq(system, system_rhs, rcond=None)

    unidentified: List[str] = []
    start = 0
    for component, design in zip(components, designs):
        width = design.shape[1]
        component.set_coef(coef[start:start + width])
        flat = [c for c in design.columns if np.ptp(design[c].to_numpy()) == 0 and not component.owns_level]
        component.unidentified_ = flat
        unidentified += [f"{component.name}:{c}" for c in flat]
        start += width
    return BlockDiagnostics(rank=rank, columns=stacked.shape[1], unidentified=unidentified)
