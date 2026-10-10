"""Component interface: one additive term of a log-scale model.

A component explains part of y = log(target). It is fitted against an offset (the summed
contributions of every other component), so components are independent in code and joint in
fitting. Periodic terms are centred over the training rows; the one component that owns the
level is not, and neither are sparse terms such as events (zero contribution when inactive), so
the parts stay identifiable and an event's contribution reads as its effect.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, Sequence, Tuple, runtime_checkable

import numpy as np
import pandas as pd

from tourism_twin.models.linear_solve import solve_linear_block


@runtime_checkable
class Component(Protocol):
    name: str
    requires: Tuple[str, ...]
    owns_level: bool
    group: str  # model block: flow, time, holiday, flight or residual (docs/model/nowcast.md#blocks)

    def fit(self, panel: pd.DataFrame, offset: pd.Series, y: pd.Series,
            weights: Optional[np.ndarray] = None) -> "Component":
        """Fit on y - offset. `weights` (positive, one per row) weight each row's squared error;
        None means every row counts once."""
        ...

    def contribution(self, panel: pd.DataFrame) -> pd.Series:
        """Log-scale contribution, indexed like `panel`."""
        ...

    def explain(self) -> Dict[str, Any]:
        """Fitted parameters in plain form."""
        ...

    # Hooks the model and fitters call on every component (defaults in ComponentBase):
    final_stage: bool  # fitted once after the others converge (residual learners)

    def reset(self) -> None: ...

    def penalty(self) -> float: ...

    def set_default_origin(self, origin: pd.Timestamp) -> None: ...


class ComponentBase:
    """Defaults for the hooks AdditiveLogModel and the fitters call on every component, so they
    never probe with hasattr/getattr. Subclasses override what they use."""

    name: str = "component"
    requires: Tuple[str, ...] = ()
    owns_level: bool = False
    group: str = "time"
    final_stage: bool = False

    def reset(self) -> None:
        """Forget fitted state (each market fit starts from a fresh copy)."""

    def penalty(self) -> float:
        """Penalty value at the current fit; part of the backfitting objective."""
        return 0.0

    def set_default_origin(self, origin: pd.Timestamp) -> None:
        """Common date origin for date-based terms (no-op unless overridden)."""


class LinearComponent(ComponentBase):
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

    def fit(self, panel: pd.DataFrame, offset: pd.Series, y: pd.Series,
            weights: Optional[np.ndarray] = None) -> "LinearComponent":
        solve_linear_block([self], panel, y - offset, weights)
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
