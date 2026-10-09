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
            result = minimize(
                lambda p: np.sum((system @ p - system_target) ** 2) / len(target),
                start_params, jac=lambda p: 2 * system.T @ (system @ p - system_target) / len(target),
                method="SLSQP", bounds=[(0, None)] * design.shape[1],
                constraints=[{"type": "ineq", "fun": lambda p: 1.0 - p[:k].sum(), "jac": lambda p: np.r_[-np.ones(k), np.zeros(len(p) - k)]}],
                options={"maxiter": 500, "ftol": 1e-12},
            )
            start_params = result.x
        d, self.c_ = np.clip(start_params[:k], 0, None), np.clip(start_params[k:], 0, None)
        self.w_ = np.cumsum(d[::-1])[::-1]  # w_k = sum_{j>=k} d_j
        flow = self._flow(panel)
        self.floor_ = max(1e-6, 0.01 * float(np.mean(flow[flow > 0])) if (flow > 0).any() else 1e-6)
        return self

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
            "w0": float(self.w_[0]),
            "base_stock_by_knot": {str(k.date()): float(c) for k, c in zip(self.knots_, self.c_)},
            "floored_rows_last_call": self.floored_rows_,
        }
