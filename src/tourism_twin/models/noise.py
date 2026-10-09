"""Forecast-error model for prediction intervals, fitted on out-of-sample back-test errors.

Errors are taken on the log scale, e = log(actual) - log(pred), from BacktestResult.predictions.
Horizon h counts days from the first forecast day (h = 0 is the forecast origin's own date).
Within each (fold, market) error series ordered by horizon, e_h = phi * e_{h-1} + eta_h, and the
error on the first day carries its own variance v0 (the level error at the origin). Given only
what is known at the origin, the error variance h days ahead is

    var(h) = v0 * phi^(2h) + sigma_eta^2 * (1 - phi^(2h)) / (1 - phi^2)

starting at v0 and moving to the stationary sigma_eta^2 / (1 - phi^2). phi, sigma_eta and v0 are
estimated per market. Intervals are Gaussian in log: pred * exp(+-z * sqrt(var)). No month or
bias adjustment: with a handful of origins per month they fit noise (see the review notes in the
commit history), and bias belongs in the forecaster.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

import numpy as np
import pandas as pd
from scipy.stats import norm

MAX_PHI = 0.995  # keeps the stationary variance finite


def _log_errors(predictions: pd.DataFrame) -> pd.Series:
    values = predictions[["actual", "pred"]].to_numpy(dtype=float)
    bad = ~np.isfinite(values).all(axis=1) | (values <= 0).any(axis=1)
    if bad.any():
        raise ValueError(f"{int(bad.sum())} rows have non-positive or non-finite actual/pred")
    return pd.Series(np.log(values[:, 0]) - np.log(values[:, 1]), index=predictions.index)


@dataclass
class NoiseModel:
    phi_: Dict[str, float] = field(default_factory=dict)
    sigma_eta_: Dict[str, float] = field(default_factory=dict)
    v0_: Dict[str, float] = field(default_factory=dict)

    def fit(self, predictions: pd.DataFrame) -> "NoiseModel":
        """predictions: rows of BacktestResult.predictions (fold, market, horizon_days, actual, pred)."""
        errors = predictions.assign(error=_log_errors(predictions)).sort_values(["fold", "market", "horizon_days"])
        steps = errors.groupby(["fold", "market"])["horizon_days"].diff()
        errors["lagged"] = errors.groupby(["fold", "market"])["error"].shift(1).where(steps == 1)
        self.phi_, self.sigma_eta_, self.v0_ = {}, {}, {}
        for market, rows in errors.groupby("market"):
            pairs = rows.dropna(subset=["lagged"])
            phi = float(np.clip((pairs["error"] @ pairs["lagged"]) / (pairs["lagged"] @ pairs["lagged"]), 0.0, MAX_PHI))
            self.phi_[market] = phi
            self.sigma_eta_[market] = float(np.sqrt(np.mean((pairs["error"] - phi * pairs["lagged"]) ** 2)))
            first = rows.loc[rows["horizon_days"] == rows.groupby("fold")["horizon_days"].transform("min"), "error"]
            self.v0_[market] = float(np.mean(first ** 2))
        return self

    def variance(self, markets: pd.Series, horizon: pd.Series) -> np.ndarray:
        unknown = sorted(set(markets) - set(self.phi_))
        if unknown:
            raise ValueError(f"NoiseModel has no errors for markets {unknown}")
        h = np.asarray(horizon, dtype=float)
        if not np.isfinite(h).all() or (h < 0).any():
            raise ValueError("horizon_days must be finite and >= 0 (0 = first forecast day)")
        phi = markets.map(self.phi_).to_numpy(dtype=float)
        sigma = markets.map(self.sigma_eta_).to_numpy(dtype=float)
        v0 = markets.map(self.v0_).to_numpy(dtype=float)
        decay = phi ** (2 * h)
        stationary = np.where(phi < 1, sigma ** 2 / (1 - phi ** 2), np.inf)
        return v0 * decay + stationary * (1 - decay)

    def intervals(self, frame: pd.DataFrame, coverage: float = 0.8) -> pd.DataFrame:
        """Bounds of the central `coverage` interval around frame["pred"]; frame needs market,
        horizon_days (0 = first forecast day) and pred columns."""
        if not (frame["pred"] > 0).all():
            raise ValueError("pred must be positive")
        sd = np.sqrt(self.variance(frame["market"], frame["horizon_days"]))
        z = norm.ppf(0.5 + coverage / 2)
        return pd.DataFrame({"lower": frame["pred"] * np.exp(-z * sd), "upper": frame["pred"] * np.exp(z * sd)}, index=frame.index)


def held_out_coverage(predictions: pd.DataFrame, coverage: float = 0.8, exclude_months: int = 0) -> pd.DataFrame:
    """Empirical coverage when each fold's intervals come from a noise model fitted on other folds
    only, excluding folds whose origin is within `exclude_months` of the held-out origin (blocked
    cross-validation; rolling folds overlap in calendar time, so exclude_months >= 3 is the honest
    setting for 6-month horizons). One row per (fold, market) with n and covered share."""
    origins = predictions.groupby("fold")["origin"].first()
    rows = []
    for fold, held_out in predictions.groupby("fold"):
        months_apart = ((origins - origins[fold]).dt.days.abs() / 30.44).round()
        keep = months_apart[months_apart > exclude_months].index
        if len(keep) == 0:
            continue
        model = NoiseModel().fit(predictions[predictions["fold"].isin(keep)])
        bounds = model.intervals(held_out, coverage)
        inside = (held_out["actual"] >= bounds["lower"]) & (held_out["actual"] <= bounds["upper"])
        for market, hits in inside.groupby(held_out["market"]):
            rows.append({"fold": fold, "market": market, "n": len(hits), "covered": float(hits.mean())})
    return pd.DataFrame(rows)
