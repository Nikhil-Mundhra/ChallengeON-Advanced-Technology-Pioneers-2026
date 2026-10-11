"""SeasonalSeatKernel: the chain's seat kernel with a strength that depends on the calendar.

    arrivals_t = c_t + exp(s(t)) * sum_k w_k Seats_{t-k},   s(t) = B(t) theta

B(t) is either a one-hot of the project season of day t (form "season", domain/seasons.py) or
`harmonics` annual sine/cosine pairs (form "fourier"). theta is constrained so s has mean zero over
the training rows (sum(w) keeps the average strength) and shrunk toward 0 by the ridge
strength_ridge * n * |theta|^2 in log units. s is a calendar function, so it carries into any
prediction date unchanged.

Each backfitting call runs a kernel step (the parent's fit on lags scaled by exp(s)) and an s step
(w, c fixed); each keeps its result only if the penalised log objective does not rise. The block
structure is copied from experiment/level_memory/drift.py, where it converged on every fit.

The cap bounds sum(w), not exp(s) sum(w): in a season with s > 0 the arrivals per seat may exceed the
P2P-per-seat bound by exp(s).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
from scipy.linalg import null_space
from scipy.optimize import minimize

from tourism_twin.domain.seasons import SEASONS, assign_season
from tourism_twin.models.components.seat_kernel import SeatKernel
from tourism_twin.models.registry import COMPONENTS
from tourism_twin.planning.chain import ChainSpec

NAME = "seasonal_seat_kernel"
FORMS = ("season", "fourier")
MONTH_MIDS = pd.Series(pd.to_datetime([f"2024-{m:02d}-15" for m in range(1, 13)]))


def strength_basis(dates: pd.Series, form: str, harmonics: int) -> np.ndarray:
    dates = pd.to_datetime(pd.Series(dates))
    if form == "season":
        season = dates.dt.month.map(assign_season).to_numpy()
        return np.column_stack([(season == s).astype(float) for s in SEASONS])
    phase = 2 * np.pi * dates.dt.dayofyear.to_numpy() / 365.25
    return np.column_stack([f(h * phase) for h in range(1, harmonics + 1) for f in (np.sin, np.cos)])


class SeasonalSeatKernel(SeatKernel):
    def __init__(self, max_lag: int = 7, knot_days: int = 365, base_smoothing: float = 1.0, name: str = "seats",
                 date_column: str = "date", cap_factor: Optional[float] = None, share_target: Optional[float] = None,
                 share_ridge: float = 0.0, form: str = "season", harmonics: int = 1, strength_ridge: float = 1.0) -> None:
        if form not in FORMS:
            raise ValueError(f"form must be one of {FORMS}")
        self.form = form
        self.harmonics = harmonics
        self.strength_ridge = strength_ridge
        super().__init__(max_lag=max_lag, knot_days=knot_days, base_smoothing=base_smoothing, name=name,
                         date_column=date_column, cap_factor=cap_factor, share_target=share_target, share_ridge=share_ridge)

    def reset(self) -> None:
        super().reset()
        self.theta_: np.ndarray | None = None
        self.null_: np.ndarray | None = None
        self.strength_penalty_ = 0.0
        self.prescaled_ = False

    def log_strength(self, dates: pd.Series) -> np.ndarray:
        return strength_basis(dates, self.form, self.harmonics) @ self.theta_

    def _flow(self, panel: pd.DataFrame) -> np.ndarray:
        if self.prescaled_:
            return super()._flow(panel)
        kernel = panel[self.lag_columns].to_numpy(dtype=float) @ self.w_
        return kernel * np.exp(self.log_strength(panel[self.date_column])) + self._base_design(panel) @ self.c_

    def fit(self, panel: pd.DataFrame, offset: pd.Series, y: pd.Series,
            weights: Optional[np.ndarray] = None) -> "SeasonalSeatKernel":
        basis = strength_basis(panel[self.date_column], self.form, self.harmonics)
        if self.theta_ is None:
            self.null_ = null_space(basis.mean(axis=0)[None, :])  # theta = null_ @ beta: s has mean zero over the training rows
            self.theta_ = np.zeros(basis.shape[1])
        scaled = panel.copy()
        scaled[self.lag_columns] = panel[self.lag_columns].to_numpy(dtype=float) * np.exp(basis @ self.theta_)[:, None]
        self.prescaled_ = True
        try:
            super().fit(scaled, offset, y, weights)
        finally:
            self.prescaled_ = False
        self._fit_strength(panel, basis, (y - offset).to_numpy(), weights)
        return self

    def _fit_strength(self, panel: pd.DataFrame, basis: np.ndarray, z: np.ndarray, weights: Optional[np.ndarray]) -> None:
        kernel = panel[self.lag_columns].to_numpy(dtype=float) @ self.w_
        base = self._base_design(panel) @ self.c_
        strength = self.strength_ridge * len(z)
        floor = 1e-9 * max(float(np.exp(z).mean()), 1.0)
        row_w = np.ones(len(z)) if weights is None else weights

        def objective(beta: np.ndarray) -> tuple:
            theta = self.null_ @ beta
            scale = np.exp(basis @ theta)
            flow = np.maximum(base + scale * kernel, floor)
            residual = z - np.log(flow)
            value = float(residual @ (row_w * residual) + strength * theta @ theta)
            d_s = -2 * row_w * residual * scale * kernel / flow * (flow > floor)
            return value, self.null_.T @ (basis.T @ d_s + 2 * strength * theta)

        start = self.null_.T @ self.theta_
        before, _ = objective(start)
        result = minimize(objective, start, jac=True, method="L-BFGS-B", options={"maxiter": 500})
        if result.fun <= before:
            self.theta_ = self.null_ @ result.x
        self.strength_penalty_ = float(strength * self.theta_ @ self.theta_)

    def penalty(self) -> float:
        return super().penalty() + self.strength_penalty_

    def explain(self) -> Dict[str, Any]:
        out = super().explain()
        by_month = np.exp(self.log_strength(MONTH_MIDS))
        days = pd.Series(pd.date_range("2024-01-01", "2024-12-31", freq="D"))
        season = days.dt.month.map(assign_season).to_numpy()
        s = self.log_strength(days)
        out["strength"] = {"by_month": [float(v) for v in by_month],
                           "by_season": {name: float(np.exp(s[season == name].mean())) for name in SEASONS}}
        return out


if NAME not in COMPONENTS.names():
    COMPONENTS.register(NAME, SeasonalSeatKernel)


@dataclass(frozen=True)
class SeasonalChainSpec(ChainSpec):
    """ChainSpec whose link 1 uses the seasonal seat kernel (the pooled refit looks it up by name)."""

    def _seat_kernel_params(self) -> Dict[str, Any]:
        entry = next(e for e in self.arrivals.components if (e if isinstance(e, str) else e[0]) == NAME)
        return {} if isinstance(entry, str) else dict(entry[1])

    def arrivals_pooled_toward(self, base_share: float):
        params = {**self._seat_kernel_params(), "share_target": base_share, "share_ridge": self.pooled_share_ridge}
        return self.arrivals.replace_component(NAME, (NAME, params))
