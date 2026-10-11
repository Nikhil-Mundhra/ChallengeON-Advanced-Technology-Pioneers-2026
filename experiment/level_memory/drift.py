"""DriftingKernel: the arrivals kernel with a slowly drifting strength (experiment 2).

    flow_t = c_t + exp(s(t)) * sum_k w_k A_{t-k},   contribution = log(flow_t)

s(t) is piecewise linear on its own knots, mean zero over the training rows (so sum(w) keeps the
average strength), with a first-difference penalty drift_lambda * n / knots * sum (s_j - s_{j-1})^2
in log units, the same unitless form as the base-stock penalty. Beyond the training days s is held
at its last value (or at `held` when set), or decays to 0 with a half-life.

Each backfitting call runs one block step for the kernel (w, c with s fixed: the parent's fit on
lags scaled by exp(s)) and one for s (w, c fixed). Each step keeps its result only if the penalised
log objective does not rise, so backfitting still descends.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
from scipy.linalg import null_space
from scipy.optimize import minimize

from tourism_twin.models.components.arrivals_conv import ArrivalsConvolution
from tourism_twin.models.registry import COMPONENTS

NAME = "drifting_arrivals_kernel"


def hat_basis(dates: pd.Series, knots: pd.DatetimeIndex) -> np.ndarray:
    """Piecewise-linear basis over evenly spaced knots, clamped beyond the first and last knot."""
    spacing = (knots[1] - knots[0]).days
    position = np.clip((pd.to_datetime(dates) - knots[0]).dt.days.to_numpy() / spacing, 0, len(knots) - 1)
    left = np.minimum(np.floor(position).astype(int), len(knots) - 2)
    frac = position - left
    basis = np.zeros((len(position), len(knots)))
    rows = np.arange(len(position))
    basis[rows, left] = 1 - frac
    basis[rows, left + 1] = frac
    return basis


class DriftingKernel(ArrivalsConvolution):
    def __init__(self, max_lag: int = 21, knot_days: int = 365, base_smoothing: float = 1.0, name: str = "arrivals",
                 date_column: str = "date", drift_knot_days: int = 90, drift_lambda: float = 1.0,
                 half_life: Optional[float] = None) -> None:
        self.drift_knot_days = drift_knot_days
        self.drift_lambda = drift_lambda
        self.half_life = half_life  # None: s held at its last value beyond the training days
        self.held: Optional[float] = None  # set after the fit to hold another value beyond the training days (fixes.py)
        super().__init__(max_lag=max_lag, knot_days=knot_days, base_smoothing=base_smoothing, name=name,
                         date_column=date_column, base="knots")

    def reset(self) -> None:
        super().reset()
        self.theta_: np.ndarray | None = None
        self.drift_knots_: pd.DatetimeIndex | None = None
        self.null_: np.ndarray | None = None
        self.train_end_: pd.Timestamp | None = None
        self.drift_penalty_ = 0.0
        self.prescaled_ = False
        self.c_s_corr_ = float("nan")

    # --- s(t) -----------------------------------------------------------------------------------
    def drift(self, dates: pd.Series) -> np.ndarray:
        dates = pd.to_datetime(dates)
        s = hat_basis(dates, self.drift_knots_) @ self.theta_
        beyond = np.clip((dates - self.train_end_).dt.days.to_numpy(), 0, None)
        held = getattr(self, "held", None)  # fits pickled before `held` existed have no attribute
        if held is not None:
            s = np.where(beyond > 0, held, s)
        if self.half_life is not None:
            s = s * 0.5 ** (beyond / self.half_life)
        return s

    def _setup_drift(self, dates: pd.Series) -> None:
        start, end = dates.min(), dates.max()
        n_knots = max(2, int(round((end - start).days / self.drift_knot_days)) + 1)
        self.drift_knots_ = pd.DatetimeIndex(np.linspace(start.value, end.value, n_knots).astype("datetime64[ns]")).normalize()
        self.train_end_ = end
        means = hat_basis(dates, self.drift_knots_).mean(axis=0)
        self.null_ = null_space(means[None, :])  # theta = null_ @ beta has mean zero over the training rows
        self.theta_ = np.zeros(n_knots)

    def _flow(self, panel: pd.DataFrame) -> np.ndarray:
        if self.prescaled_:
            return super()._flow(panel)
        lags = panel[self.lag_columns].to_numpy(dtype=float) @ self.w_
        return lags * np.exp(self.drift(panel[self.date_column])) + self._base_design(panel) @ self.c_

    # --- fit ------------------------------------------------------------------------------------
    def fit(self, panel: pd.DataFrame, offset: pd.Series, y: pd.Series,
            weights: Optional[np.ndarray] = None) -> "DriftingKernel":
        dates = pd.to_datetime(panel[self.date_column])
        if self.theta_ is None:
            self._setup_drift(dates)
        basis = hat_basis(dates, self.drift_knots_)
        scaled = panel.copy()
        scaled[self.lag_columns] = panel[self.lag_columns].to_numpy(dtype=float) * np.exp(basis @ self.theta_)[:, None]
        self.prescaled_ = True
        try:
            super().fit(scaled, offset, y, weights)
        finally:
            self.prescaled_ = False
        self._fit_drift(panel, basis, (y - offset).to_numpy(), weights)
        base = self._base_design(panel) @ self.c_
        s = basis @ self.theta_
        self.c_s_corr_ = float(np.corrcoef(base, s)[0, 1]) if base.std() > 0 and s.std() > 0 else float("nan")
        return self

    def _fit_drift(self, panel: pd.DataFrame, basis: np.ndarray, z: np.ndarray, weights: Optional[np.ndarray]) -> None:
        kernel = panel[self.lag_columns].to_numpy(dtype=float) @ self.w_
        base = self._base_design(panel) @ self.c_
        n_knots = len(self.drift_knots_)
        diff = np.diff(np.eye(n_knots), axis=0)
        strength = self.drift_lambda * len(z) / n_knots
        floor = 1e-9 * max(float(np.exp(z).mean()), 1.0)
        row_w = np.ones(len(z)) if weights is None else weights

        def objective(beta: np.ndarray) -> tuple:
            theta = self.null_ @ beta
            scale = np.exp(basis @ theta)
            flow = np.maximum(base + scale * kernel, floor)
            residual = z - np.log(flow)
            value = float(residual @ (row_w * residual) + strength * np.sum((diff @ theta) ** 2))
            d_s = -2 * row_w * residual * scale * kernel / flow * (flow > floor)
            grad_theta = basis.T @ d_s + 2 * strength * diff.T @ (diff @ theta)
            return value, self.null_.T @ grad_theta

        start = self.null_.T @ self.theta_
        before, _ = objective(start)
        result = minimize(objective, start, jac=True, method="L-BFGS-B", options={"maxiter": 500})
        if result.fun <= before:
            self.theta_ = self.null_ @ result.x
        self.drift_penalty_ = float(strength * np.sum((diff @ self.theta_) ** 2))

    def penalty(self) -> float:
        return super().penalty() + self.drift_penalty_

    def explain(self) -> Dict[str, Any]:
        out = super().explain()
        out["drift"] = {"by_knot": {str(k.date()): float(v) for k, v in zip(self.drift_knots_, self.theta_)},
                        "last": float(self.theta_[-1]), "min": float(self.theta_.min()), "max": float(self.theta_.max()),
                        "corr_base_stock": self.c_s_corr_}
        return out


if NAME not in COMPONENTS.names():
    COMPONENTS.register(NAME, DriftingKernel)
