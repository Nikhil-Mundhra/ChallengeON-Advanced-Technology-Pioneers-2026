"""ConvolutionKernel: the shared maths of a stock (or flow) fed by lags of one input series.

    flow_t = c_t + sum_{k=0..K} w_k * x_{t-k},   contribution = log(flow_t)

w_k >= 0, non-increasing, w_0 <= 1: w = U d with U upper-triangular ones, d >= 0 and sum(d) <= 1.
It is one constrained linear filter, not a neural network. c_t >= 0 is a slowly varying base,
piecewise linear between knots spread evenly from the first to the last training day (about one per
`knot_days`); a first-difference penalty keeps it from jumping at the ends, and it is flat beyond the
training days. With a proportional base column (e.g. trailing 90-day mean of the input), c_t = rho *
column instead, rho >= 0.

Optional constraints (all off by default, so a subclass that leaves them off fits exactly as before):
- max_kernel_sum: sum(w) = sum_j (j + 1) d_j <= cap (a physical bound on output per unit of input);
  `kernel_cap(panel)` returns it and may calibrate it from the training rows.
- share_target / share_ridge: a quadratic penalty share_ridge * n * (base share - share_target)^2,
  shrinking the base share toward a pooled value instead of fixing a floor.

Fitting happens on the original scale first (bounded least squares, the warm start), then on the
model's own log objective (SLSQP), kept only if no worse than the previous backfitting pass.
Subclasses name the lag columns and what the input is; they own nothing else.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import numpy as np
import pandas as pd
from scipy.optimize import lsq_linear, minimize

from tourism_twin.models.components.base import ComponentBase
from tourism_twin.models.linear_solve import row_scale


def _feasible(params: np.ndarray, k: int) -> np.ndarray:
    """Clip to d >= 0, c >= 0 and scale d onto sum(d) <= 1 (SLSQP can stop short of feasibility)."""
    params = np.clip(params, 0, None)
    if params[:k].sum() > 1.0:
        params[:k] = params[:k] / params[:k].sum()
    return params


def log_objective(p: np.ndarray, design: np.ndarray, penalty: np.ndarray, z: np.ndarray, floor: float,
                  weights: Optional[np.ndarray] = None) -> float:
    """sum w (z - log flow)^2 + |penalty @ p|^2 with flow = design @ p (floored at `floor`); w = 1 if None."""
    residual = z - np.log(np.maximum(design @ p, floor))
    fit = residual @ residual if weights is None else residual @ (weights * residual)
    return float(fit + np.sum((penalty @ p) ** 2))


def log_gradient(p: np.ndarray, design: np.ndarray, penalty: np.ndarray, z: np.ndarray, floor: float,
                 weights: Optional[np.ndarray] = None) -> np.ndarray:
    flow = design @ p
    weight = np.where(flow > floor, (z - np.log(np.maximum(flow, floor))) / np.maximum(flow, floor), 0.0)
    if weights is not None:
        weight = weights * weight
    return -2 * design.T @ weight + 2 * penalty.T @ (penalty @ p)


class ConvolutionKernel(ComponentBase):
    owns_level = True
    group = "flow"

    def __init__(self, lag_columns: Sequence[str], knot_days: int = 365, base_smoothing: float = 1.0,
                 name: str = "kernel", date_column: str = "date", base_column: Optional[str] = None,
                 extra_requires: Sequence[str] = (), max_kernel_sum: Optional[float] = None,
                 share_target: Optional[float] = None,
                 share_ridge: float = 0.0, base_explain_key: Optional[str] = None) -> None:
        if share_ridge and (share_target is None or not 0.0 <= share_target < 1.0):
            raise ValueError("share_ridge needs a share_target in [0, 1)")
        self.lag_columns = list(lag_columns)
        self.max_lag = len(self.lag_columns) - 1
        self.knot_days = knot_days
        self.base_smoothing = base_smoothing
        self.name = name
        self.date_column = date_column
        self.base_column = base_column
        self.max_kernel_sum = max_kernel_sum
        self.share_target = share_target
        self.share_ridge = share_ridge
        self.base_explain_key = base_explain_key or f"base_stock_per_{base_column}"
        self.requires = (date_column, *self.lag_columns) + ((base_column,) if base_column else ()) + tuple(extra_requires)
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
        self.cap_: float | None = None
        self.cap_binds_ = False

    # --- hooks for subclasses ----------------------------------------------------------------
    def kernel_cap(self, panel: pd.DataFrame) -> Optional[float]:
        """Upper bound on sum(w) for this fit (None: unbounded); may be calibrated on `panel`."""
        return self.max_kernel_sum

    # --- base stock ----------------------------------------------------------------------------
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

    def _base_design(self, panel: pd.DataFrame) -> np.ndarray:
        if self.base_column:
            return panel[[self.base_column]].to_numpy(dtype=float)
        return self._base(pd.to_datetime(panel[self.date_column]))

    # --- extra linear constraints G p <= h (beyond d >= 0, c >= 0, sum d <= 1) -----------------
    def _extra_constraints(self, design: np.ndarray, k: int) -> List[tuple]:
        """(row, bound) pairs, each meaning row @ p <= bound."""
        extra = []
        if self.cap_ is not None:
            extra.append((np.r_[np.arange(1, k + 1, dtype=float), np.zeros(design.shape[1] - k)], self.cap_))
        return extra

    @staticmethod
    def _project_extra(params: np.ndarray, extra: List[tuple], k: int) -> np.ndarray:
        """Move a point onto the extra constraints (the cap on sum(w): shrink d)."""
        for row, bound in extra:
            value = row @ params
            if value > bound + 1e-12:
                params[:k] *= bound / value
        return params

    def _slsqp_constraints(self, extra: List[tuple], k: int) -> List[dict]:
        constraints = [{"type": "ineq", "fun": lambda p: 1.0 - p[:k].sum(),
                        "jac": lambda p: np.r_[-np.ones(k), np.zeros(len(p) - k)]}]
        for row, bound in extra:
            constraints.append({"type": "ineq", "fun": lambda p, r=row, b=bound: b - r @ p, "jac": lambda p, r=row: -r})
        return constraints

    def _share_penalty(self, design: np.ndarray, k: int, n: int) -> np.ndarray:
        """One penalty row: sqrt(ridge n) (mean base - target * mean flow), on the raw scale."""
        if not self.share_ridge:
            return np.zeros((0, design.shape[1]))
        s, means = self.share_target, design.mean(axis=0)
        return np.sqrt(self.share_ridge * n) * np.r_[-s * means[:k], (1 - s) * means[k:]][None, :]

    # --- fit ------------------------------------------------------------------------------------
    def fit(self, panel: pd.DataFrame, offset: pd.Series, y: pd.Series,
            weights: Optional[np.ndarray] = None) -> "ConvolutionKernel":
        dates = pd.to_datetime(panel[self.date_column])
        start, end = dates.min(), dates.max()
        n_knots = max(2, int(round((end - start).days / self.knot_days)) + 1)
        self.knots_ = pd.DatetimeIndex(np.linspace(start.value, end.value, n_knots).astype("datetime64[ns]")).normalize()
        lags = panel[self.lag_columns].to_numpy(dtype=float)
        if not np.isfinite(lags).all():
            raise ValueError(f"Component {self.name!r}: input lags are incomplete; fit on rows with a full lag window")
        if self.cap_ is None:
            self.cap_ = self.kernel_cap(panel)
        target = np.exp((y - offset).to_numpy())
        survival = lags @ np.triu(np.ones((self.max_lag + 1, self.max_lag + 1)))  # column j: sum_{k<=j} x_{t-k}
        design = np.hstack([survival, self._base_design(panel)])
        k = self.max_lag + 1
        # First-difference penalty on the base-stock knots, weighted like the rows each knot covers
        # (none for a proportional base: one coefficient).
        n_knots = design.shape[1] - k
        penalty = np.zeros((n_knots - 1 if not self.base_column else 0, design.shape[1]))
        if not self.base_column:
            penalty[:, k:] = np.sqrt(self.base_smoothing * len(target) / n_knots) * np.diff(np.eye(n_knots), axis=0)
        share_penalty = self._share_penalty(design, k, len(target))
        if len(share_penalty):
            penalty = np.vstack([penalty, share_penalty])
        extra = self._extra_constraints(design, k)
        scale = row_scale(weights, len(target))  # weighted rows: sqrt(w) on the data rows, not the penalty
        weighted_design, weighted_target = (design, target) if scale is None else (design * scale[:, None], target * scale)
        system, system_target = np.vstack([weighted_design, penalty]), np.r_[weighted_target, np.zeros(len(penalty))]
        lower = np.zeros(design.shape[1])  # d >= 0 (survival curve) and c >= 0 (a base stock)
        # Unit-norm columns: cumulative inputs and the base-stock basis differ by ~10^4 in scale.
        norms = np.linalg.norm(system, axis=0)
        norms[norms == 0] = 1.0
        start_params = lsq_linear(system / norms, system_target, bounds=(lower, np.inf), method="bvls").x / norms
        extra_violated = any(row @ start_params > bound + 1e-12 for row, bound in extra)
        if start_params[:k].sum() > 1.0 or extra_violated:
            if start_params[:k].sum() > 1.0:
                start_params[:k] /= start_params[:k].sum()
            start_params = self._project_extra(start_params, extra, k)
            start_params = minimize(
                lambda p: np.sum((system @ p - system_target) ** 2) / len(target),
                start_params, jac=lambda p: 2 * system.T @ (system @ p - system_target) / len(target),
                method="SLSQP", bounds=[(0, None)] * design.shape[1],
                constraints=self._slsqp_constraints(extra, k),
                options={"maxiter": 500, "ftol": 1e-12},
            ).x  # a warm start only; the log refinement below decides
        if self.penalty_scale_ is None:  # one scale per fit, so the penalised objective is the same function every pass
            self.penalty_scale_ = max(float(np.mean(target)), 1e-12)
        params = self._log_refine(design, penalty / self.penalty_scale_, (y - offset).to_numpy(),
                                  self._project_extra(_feasible(start_params, k), extra, k), k,
                                  None if scale is None else scale ** 2, extra)
        self.projected_ = bool(np.isclose(params[:k].sum(), 1.0))  # the w0 <= 1 constraint binds at the solution
        self.cap_binds_ = bool(self.cap_ is not None and np.isclose(np.arange(1, k + 1) @ params[:k], self.cap_, rtol=1e-6))
        d, self.c_ = params[:k], params[k:]
        self.params_ = params
        self.w_ = np.cumsum(d[::-1])[::-1]  # w_k = sum_{j>=k} d_j
        flow = self._flow(panel)
        base = self._base_design(panel) @ self.c_
        self.base_share_ = float(base.sum() / flow.sum()) if flow.sum() > 0 else 0.0
        self.floor_ = max(1e-6, 0.01 * float(np.mean(flow[flow > 0])) if (flow > 0).any() else 1e-6)
        self.floored_training_rows_ = int((flow < self.floor_).sum())  # rows where contribution() departs from the fitted objective
        return self

    def penalty(self) -> float:
        """Value of this component's penalty at the current fit (part of the backfitting objective)."""
        return self.penalty_value_

    def _log_refine(self, design: np.ndarray, penalty: np.ndarray, z: np.ndarray, start: np.ndarray, k: int,
                    weights: Optional[np.ndarray] = None, extra: Optional[List[tuple]] = None) -> np.ndarray:
        """Minimise the model's own objective, sum (z - log flow)^2 plus the base-stock penalty
        (unitless: divided by the first pass's mean target), from the raw-scale solution. Every
        other component is fitted on this log-scale objective, so backfitting only descends if this
        step does too: the result is kept only if it is no worse than this fit's previous pass."""
        extra = extra or []
        floor = 1e-9 * max(float(np.exp(z).mean()), 1.0)
        objective = lambda p: log_objective(p, design, penalty, z, floor, weights)  # noqa: E731
        gradient = lambda p: log_gradient(p, design, penalty, z, floor, weights)  # noqa: E731

        candidates = [start]
        if self.params_ is not None and len(self.params_) == len(start):
            candidates.append(self.params_)  # this fit's previous pass
        best = min(candidates, key=objective)
        result = minimize(objective, best, jac=gradient, method="SLSQP", bounds=[(0, None)] * len(start),
                          constraints=self._slsqp_constraints(extra, k),
                          options={"maxiter": 500, "ftol": 1e-12})
        refined = self._project_extra(_feasible(result.x, k), extra, k)
        chosen = refined if objective(refined) <= objective(best) else best
        # Status 8 ("positive directional derivative") at ftol 1e-12: no further descent found.
        self.solver_success_ = bool(result.success or result.status == 8)
        self.penalty_value_ = float(np.sum((penalty @ chosen) ** 2))
        return chosen

    def _flow(self, panel: pd.DataFrame) -> np.ndarray:
        return panel[self.lag_columns].to_numpy(dtype=float) @ self.w_ + self._base_design(panel) @ self.c_

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
            # Share of the training flow carried by the base stock c_t rather than the kernel.
            "base_stock_share": self.base_share_,
            "w0_constraint_binds": self.projected_,
            "solver_success": self.solver_success_,
            "w0": float(self.w_[0]),
            **({"base_stock_by_knot": {str(k.date()): float(c) for k, c in zip(self.knots_, self.c_)}} if not self.base_column
               else {self.base_explain_key: float(self.c_[0])}),
            "floored_rows_last_call": self.floored_rows_,
            "floored_training_rows": self.floored_training_rows_,
        }
