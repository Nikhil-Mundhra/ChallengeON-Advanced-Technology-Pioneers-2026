"""ArrivalsConvolution: hotel guests as a stock fed by the flow of new arrivals.

    flow_t = c_t + sum_{k=0..K} w_k * Arrivals_{t-k},   contribution = log(flow_t)

w_k is the share of arrivals still staying after k nights (a survival curve): w_k >= 0,
non-increasing, w_0 <= 1, so implied mean stay = sum w_k. It is one constrained linear filter,
not a neural network. c_t >= 0 is a slowly varying base stock (long stays, residents), piecewise
linear between knots spread evenly from the first to the last training day (about one per
`knot_days`); a first-difference penalty keeps it from jumping at the ends, and it is flat
beyond the training days. Faster-moving seasonality belongs to the season component.

Fitting happens on the original scale: inside backfitting the target is exp(y - offset), the
guests left after dividing out every other component's multiplier. With w = U d (U upper
triangular ones) the constraints become d >= 0 and sum(d) <= 1, solved by SLSQP.
Owns the level. Arrival lags come from the panel (arrivals_lag_k), so the first predicted days
see the last training days' arrivals.
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd
from scipy.optimize import lsq_linear, minimize

from tourism_twin.features.lags import lag_column


def _feasible(params: np.ndarray, k: int) -> np.ndarray:
    """Clip to d >= 0, c >= 0 and scale d onto sum(d) <= 1 (SLSQP can stop short of feasibility)."""
    params = np.clip(params, 0, None)
    if params[:k].sum() > 1.0:
        params[:k] = params[:k] / params[:k].sum()
    return params


def log_objective(p: np.ndarray, design: np.ndarray, penalty: np.ndarray, z: np.ndarray, floor: float) -> float:
    """sum (z - log flow)^2 + |penalty @ p|^2 with flow = design @ p (floored at `floor`)."""
    residual = z - np.log(np.maximum(design @ p, floor))
    return float(residual @ residual + np.sum((penalty @ p) ** 2))


def log_gradient(p: np.ndarray, design: np.ndarray, penalty: np.ndarray, z: np.ndarray, floor: float) -> np.ndarray:
    flow = design @ p
    weight = np.where(flow > floor, (z - np.log(np.maximum(flow, floor))) / np.maximum(flow, floor), 0.0)
    return -2 * design.T @ weight + 2 * penalty.T @ (penalty @ p)


class ArrivalsConvolution:
    owns_level = True

    def __init__(self, max_lag: int = 21, knot_days: int = 365, base_smoothing: float = 1.0,
                 name: str = "arrivals", date_column: str = "date") -> None:
        self.max_lag = max_lag
        self.knot_days = knot_days
        self.base_smoothing = base_smoothing
        self.name = name
        self.date_column = date_column
        self.lag_columns = [lag_column(k) for k in range(max_lag + 1)]
        self.requires = (date_column, *self.lag_columns)
        self.reset()

    def reset(self) -> None:
        self.w_: np.ndarray | None = None
        self.c_: np.ndarray | None = None
        self.knots_: pd.DatetimeIndex | None = None
        self.floor_ = 1e-6
        self.floored_rows_ = 0
        self.solver_success_ = True
        self.projected_ = False
        self.params_: np.ndarray | None = None
        self.penalty_scale_: float | None = None  # fixed at the first pass of a fit
        self.penalty_value_ = 0.0
        self.floored_training_rows_ = 0

    def _base(self, dates: pd.Series) -> np.ndarray:
        """Hat-function basis for c_t over the knots (clamped beyond the first and last knot)."""
        spacing = (self.knots_[1] - self.knots_[0]).days if len(self.knots_) > 1 else 1
        position = (dates - self.knots_[0]).dt.days.to_numpy() / spacing
        position = np.clip(position, 0, len(self.knots_) - 1)
        basis = np.zeros((len(dates), len(self.knots_)))
        left = np.minimum(np.floor(position).astype(int), len(self.knots_) - 2) if len(self.knots_) > 1 else np.zeros(len(dates), int)
        frac = position - left
        rows = np.arange(len(dates))
        basis[rows, left] = 1 - frac
        if len(self.knots_) > 1:
            basis[rows, left + 1] = frac
        return basis

    def fit(self, panel: pd.DataFrame, offset: pd.Series, y: pd.Series) -> "ArrivalsConvolution":
        dates = pd.to_datetime(panel[self.date_column])
        start, end = dates.min(), dates.max()
        n_knots = max(2, int(round((end - start).days / self.knot_days)) + 1)
        self.knots_ = pd.DatetimeIndex(np.linspace(start.value, end.value, n_knots).astype("datetime64[ns]")).normalize()
        lags = panel[self.lag_columns].to_numpy(dtype=float)
        if not np.isfinite(lags).all():
            raise ValueError(f"Component {self.name!r}: arrival lags are incomplete; fit on lag_complete rows")
        target = np.exp((y - offset).to_numpy())
        survival = lags @ np.triu(np.ones((self.max_lag + 1, self.max_lag + 1)))  # column j: sum_{k<=j} A_{t-k}
        design = np.hstack([survival, self._base(dates)])
        k = self.max_lag + 1
        # First-difference penalty on the base-stock knots, weighted like the rows each knot covers.
        n_knots = design.shape[1] - k
        penalty = np.zeros((n_knots - 1, design.shape[1]))
        penalty[:, k:] = np.sqrt(self.base_smoothing * len(target) / n_knots) * np.diff(np.eye(n_knots), axis=0)
        system, system_target = np.vstack([design, penalty]), np.r_[target, np.zeros(n_knots - 1)]
        lower = np.zeros(design.shape[1])  # d >= 0 (survival curve) and c >= 0 (a base stock of guests)
        # Unit-norm columns: cumulative arrivals and the base-stock basis differ by ~10^4 in scale.
        norms = np.linalg.norm(system, axis=0)
        norms[norms == 0] = 1.0
        start_params = lsq_linear(system / norms, system_target, bounds=(lower, np.inf), method="bvls").x / norms
        if start_params[:k].sum() > 1.0:
            start_params[:k] /= start_params[:k].sum()
            start_params = minimize(
                lambda p: np.sum((system @ p - system_target) ** 2) / len(target),
                start_params, jac=lambda p: 2 * system.T @ (system @ p - system_target) / len(target),
                method="SLSQP", bounds=[(0, None)] * design.shape[1],
                constraints=[{"type": "ineq", "fun": lambda p: 1.0 - p[:k].sum(), "jac": lambda p: np.r_[-np.ones(k), np.zeros(len(p) - k)]}],
                options={"maxiter": 500, "ftol": 1e-12},
            ).x  # a warm start only; the log refinement below decides
        if self.penalty_scale_ is None:  # one scale per fit, so the penalised objective is the same function every pass
            self.penalty_scale_ = max(float(np.mean(target)), 1e-12)
        params = self._log_refine(design, penalty / self.penalty_scale_, (y - offset).to_numpy(), _feasible(start_params, k), k)
        self.projected_ = bool(np.isclose(params[:k].sum(), 1.0))  # the w0 <= 1 constraint binds at the solution
        d, self.c_ = params[:k], params[k:]
        self.params_ = params
        self.w_ = np.cumsum(d[::-1])[::-1]  # w_k = sum_{j>=k} d_j
        flow = self._flow(panel)
        base = self._base(dates) @ self.c_
        self.base_share_ = float(base.sum() / flow.sum()) if flow.sum() > 0 else 0.0
        self.floor_ = max(1e-6, 0.01 * float(np.mean(flow[flow > 0])) if (flow > 0).any() else 1e-6)
        self.floored_training_rows_ = int((flow < self.floor_).sum())  # rows where contribution() departs from the fitted objective
        return self

    def penalty(self) -> float:
        """Value of this component's penalty at the current fit (part of the backfitting objective)."""
        return self.penalty_value_

    def _log_refine(self, design: np.ndarray, penalty: np.ndarray, z: np.ndarray, start: np.ndarray, k: int) -> np.ndarray:
        """Minimise the model's own objective, sum (z - log flow)^2 plus the base-stock penalty
        (unitless: divided by the first pass's mean target), from the raw-scale solution. Every
        other component is fitted on this log-scale objective, so backfitting only descends if this
        step does too: the result is kept only if it is no worse than this fit's previous pass."""
        floor = 1e-9 * max(float(np.exp(z).mean()), 1.0)
        objective = lambda p: log_objective(p, design, penalty, z, floor)  # noqa: E731
        gradient = lambda p: log_gradient(p, design, penalty, z, floor)  # noqa: E731

        candidates = [start]
        if self.params_ is not None and len(self.params_) == len(start):
            candidates.append(self.params_)  # this fit's previous pass
        best = min(candidates, key=objective)
        result = minimize(objective, best, jac=gradient, method="SLSQP", bounds=[(0, None)] * len(start),
                          constraints=[{"type": "ineq", "fun": lambda p: 1.0 - p[:k].sum(),
                                        "jac": lambda p: np.r_[-np.ones(k), np.zeros(len(p) - k)]}],
                          options={"maxiter": 500, "ftol": 1e-12})
        refined = _feasible(result.x, k)
        chosen = refined if objective(refined) <= objective(best) else best
        # Status 8 ("positive directional derivative") at ftol 1e-12: no further descent found.
        self.solver_success_ = bool(result.success or result.status == 8)
        self.penalty_value_ = float(np.sum((penalty @ chosen) ** 2))
        return chosen

    def _flow(self, panel: pd.DataFrame) -> np.ndarray:
        dates = pd.to_datetime(panel[self.date_column])
        return panel[self.lag_columns].to_numpy(dtype=float) @ self.w_ + self._base(dates) @ self.c_

    def contribution(self, panel: pd.DataFrame) -> pd.Series:
        if self.w_ is None:
            raise RuntimeError(f"Component {self.name!r} is not fitted")
        flow = self._flow(panel)
        self.floored_rows_ = int((flow < self.floor_).sum())
        return pd.Series(np.log(np.maximum(flow, self.floor_)), index=panel.index, name=self.name)

    def explain(self) -> Dict[str, Any]:
        if self.w_ is None:
            raise RuntimeError(f"Component {self.name!r} is not fitted")
        return {
            "survival_w": [float(v) for v in self.w_],
            "implied_mean_stay_days": float(self.w_.sum()),
            # Share of the training flow carried by the base stock c_t rather than the kernel; when it
            # is large, sum(w) understates the guests / new-arrivals ratio.
            "base_stock_share": self.base_share_,
            "w0_constraint_binds": self.projected_,
            "solver_success": self.solver_success_,
            "w0": float(self.w_[0]),
            "base_stock_by_knot": {str(k.date()): float(c) for k, c in zip(self.knots_, self.c_)},
            "floored_rows_last_call": self.floored_rows_,
            "floored_training_rows": self.floored_training_rows_,
        }
