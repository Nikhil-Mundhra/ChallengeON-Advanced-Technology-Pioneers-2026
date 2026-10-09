"""Component interface: one additive term of a log-scale model.

A component explains part of y = log(target). It is fitted against an offset (the summed
contributions of every other component), so components are independent in code and joint in
fitting. Periodic terms are centred over the training rows; the one component that owns the
level is not, and neither are sparse terms such as events (zero contribution when inactive), so
the parts stay identifiable and an event's contribution reads as its effect.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Protocol, Sequence, Tuple, runtime_checkable

import numpy as np
import pandas as pd


@runtime_checkable
class Component(Protocol):
    name: str
    requires: Tuple[str, ...]
    owns_level: bool
    group: str  # model block: flow, time, holiday, flight or residual (docs/model_design.md §3.1)

    def fit(self, panel: pd.DataFrame, offset: pd.Series, y: pd.Series) -> "Component": ...

    def contribution(self, panel: pd.DataFrame) -> pd.Series:
        """Log-scale contribution, indexed like `panel`."""
        ...

    def explain(self) -> Dict[str, Any]:
        """Fitted parameters in plain form."""
        ...


class LinearComponent:
    """A component whose contribution is design(panel) @ coef. JointLinear stacks the designs of
    all linear components and solves them in one least-squares problem."""

    name: str = "linear"
    requires: Tuple[str, ...] = ()
    owns_level: bool = False
    centred: bool = True
    group: str = "time"

    def __init__(self) -> None:
        self.coef_: np.ndarray | None = None
        self.column_means_: pd.Series | None = None
        self.unidentified_: List[str] = []

    def design(self, panel: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError

    def prepare(self, panel: pd.DataFrame) -> pd.DataFrame:
        """Design matrix as fitted. Centred on the training means for centred components; the
        means are captured on the first (fitting) call and reused afterwards."""
        design = self.design(panel)
        non_numeric = [c for c in design.columns if not pd.api.types.is_numeric_dtype(design[c])]
        if non_numeric:
            raise TypeError(f"Component {self.name!r}: non-numeric design columns {non_numeric}; encode them first")
        design = design.astype(float)
        bad = {c: int(n) for c, n in (~np.isfinite(design)).sum().items() if n}
        if bad:
            raise ValueError(f"Component {self.name!r}: non-finite values in design columns {bad}")
        if self.owns_level or not self.centred:
            return design
        if self.column_means_ is None:
            self.column_means_ = design.mean()
        return design - self.column_means_

    def penalty_rows(self) -> np.ndarray | None:
        """Rows D of a quadratic penalty |D @ coef|^2 added to the least squares; None = unpenalised."""
        return None

    def penalty(self) -> float:
        """Value of |D @ coef|^2 at the current fit (part of the backfitting objective)."""
        rows = self.penalty_rows()
        return float(np.sum((rows @ self.coef_) ** 2)) if rows is not None and self.coef_ is not None else 0.0

    def set_coef(self, coef: np.ndarray) -> None:
        self.coef_ = np.asarray(coef, dtype=float)

    def fit(self, panel: pd.DataFrame, offset: pd.Series, y: pd.Series) -> "LinearComponent":
        solve_linear_block([self], panel, y - offset)
        return self

    def _require_fitted(self) -> None:
        if self.coef_ is None:
            raise RuntimeError(f"Component {self.name!r} is not fitted")

    def contribution(self, panel: pd.DataFrame) -> pd.Series:
        self._require_fitted()
        return pd.Series(self.prepare(panel).to_numpy() @ self.coef_, index=panel.index, name=self.name)

    def explain(self) -> Dict[str, Any]:
        self._require_fitted()
        out: Dict[str, Any] = {"coef": self.coef_.tolist()}
        if self.unidentified_:
            out["unidentified"] = list(self.unidentified_)
        return out

    def reset(self) -> None:
        self.coef_ = None
        self.column_means_ = None
        self.unidentified_ = []


@dataclass
class BlockDiagnostics:
    rank: int
    columns: int
    unidentified: List[str] = field(default_factory=list)

    @property
    def rank_deficient(self) -> bool:
        return self.rank < self.columns


def solve_linear_block(components: Sequence[LinearComponent], panel: pd.DataFrame, target: pd.Series) -> BlockDiagnostics:
    """One least squares over the stacked designs, with each component's penalty rows appended.

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
    system, system_rhs = stacked, rhs
    if penalty_blocks:
        system = np.vstack([stacked, *penalty_blocks])
        system_rhs = np.concatenate([rhs, np.zeros(sum(b.shape[0] for b in penalty_blocks))])
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
