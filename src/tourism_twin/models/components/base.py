"""Component interface: one additive term of a log-scale model.

A component explains part of y = log(target). It is fitted against an offset (the summed
contributions of every other component), so components are independent in code and joint in
fitting. Contributions are centred over the training rows, except for the one component that
owns the level; this keeps the parts identifiable.
"""

from __future__ import annotations

from typing import Any, Dict, Protocol, Tuple, runtime_checkable

import numpy as np
import pandas as pd


@runtime_checkable
class Component(Protocol):
    name: str
    requires: Tuple[str, ...]
    owns_level: bool

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

    def __init__(self) -> None:
        self.coef_: np.ndarray | None = None
        self.column_means_: pd.Series | None = None

    def design(self, panel: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError

    def prepare(self, panel: pd.DataFrame) -> pd.DataFrame:
        """Design matrix as fitted: centred on the training means unless this component owns the level."""
        design = self.design(panel).astype(float)
        if self.owns_level:
            return design
        if self.column_means_ is None:
            self.column_means_ = design.mean()
        return design - self.column_means_

    def set_coef(self, coef: np.ndarray) -> None:
        self.coef_ = np.asarray(coef, dtype=float)

    def fit(self, panel: pd.DataFrame, offset: pd.Series, y: pd.Series) -> "LinearComponent":
        design = self.prepare(panel)
        coef, *_ = np.linalg.lstsq(design.to_numpy(), (y - offset).to_numpy(), rcond=None)
        self.set_coef(coef)
        return self

    def contribution(self, panel: pd.DataFrame) -> pd.Series:
        if self.coef_ is None:
            raise RuntimeError(f"Component {self.name!r} is not fitted")
        return pd.Series(self.prepare(panel).to_numpy() @ self.coef_, index=panel.index, name=self.name)

    def explain(self) -> Dict[str, Any]:
        columns = list(self.column_means_.index) if self.column_means_ is not None else None
        return {"coef": dict(zip(columns, self.coef_.tolist())) if columns else self.coef_.tolist()}

    def reset(self) -> None:
        self.coef_ = None
        self.column_means_ = None
