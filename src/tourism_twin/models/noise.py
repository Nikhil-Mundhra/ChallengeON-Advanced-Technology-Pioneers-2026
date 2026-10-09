"""Forecast-error model for prediction intervals, fitted on out-of-sample back-test errors.

Errors are taken on the log scale, e = log(actual) - log(pred), from BacktestResult.predictions.
Within each (fold, market) error series ordered by horizon, e_h = phi * e_{h-1} + eta_h. Given only
what is known at the origin, the error variance h days ahead is

    var(h) = sigma_eta^2 * (1 - phi^(2(h+1))) / (1 - phi^2)

so intervals widen with the horizon and level off. phi and sigma_eta are estimated per market;
a calendar-month factor (pooled per segment: domestic / international) scales the variance for
months whose errors are larger. Intervals are Gaussian in log:
pred * exp(+-z * sqrt(var)).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from scipy.stats import norm

DOMESTIC = "DOMESTIC"
MAX_PHI = 0.995  # keeps the stationary variance finite


def _segment(markets: pd.Series) -> pd.Series:
    return np.where(markets == DOMESTIC, "domestic", "international")


@dataclass
class NoiseModel:
    phi_: Dict[str, float] = field(default_factory=dict)
    sigma_eta_: Dict[str, float] = field(default_factory=dict)
    month_factor_: Dict[Tuple[str, int], float] = field(default_factory=dict)

    def fit(self, predictions: pd.DataFrame) -> "NoiseModel":
        """predictions: rows of BacktestResult.predictions (fold, market, date, horizon_days, actual, pred)."""
        errors = predictions.assign(error=np.log(predictions["actual"]) - np.log(predictions["pred"]))
        errors = errors.sort_values(["fold", "market", "horizon_days"])
        errors["lagged"] = errors.groupby(["fold", "market"])["error"].shift(1)
        self.phi_, self.sigma_eta_ = {}, {}
        for market, rows in errors.groupby("market"):
            pairs = rows.dropna(subset=["lagged"])
            phi = float(np.clip((pairs["error"] @ pairs["lagged"]) / (pairs["lagged"] @ pairs["lagged"]), 0.0, MAX_PHI))
            innovations = pairs["error"] - phi * pairs["lagged"]
            self.phi_[market] = phi
            self.sigma_eta_[market] = float(np.sqrt(np.mean(innovations ** 2)))
        errors["standardised"] = errors["error"] / np.sqrt(self._variance(errors["market"], errors["horizon_days"], None))
        errors["segment"] = _segment(errors["market"])
        errors["month"] = pd.to_datetime(errors["date"]).dt.month
        factors = errors.groupby(["segment", "month"])["standardised"].apply(lambda s: float(np.mean(s ** 2)))
        self.month_factor_ = factors.to_dict()
        return self

    def _variance(self, markets: pd.Series, horizon: pd.Series, dates: pd.Series | None) -> np.ndarray:
        unknown = sorted(set(markets) - set(self.phi_))
        if unknown:
            raise ValueError(f"NoiseModel has no errors for markets {unknown}")
        phi = markets.map(self.phi_).to_numpy(dtype=float)
        sigma = markets.map(self.sigma_eta_).to_numpy(dtype=float)
        h = np.asarray(horizon, dtype=float)
        growth = np.where(phi > 0, (1 - phi ** (2 * (h + 1))) / (1 - phi ** 2), 1.0)
        variance = sigma ** 2 * growth
        if dates is not None:
            keys = zip(_segment(markets), pd.to_datetime(dates).dt.month)
            variance = variance * np.array([self.month_factor_.get(key, 1.0) for key in keys])
        return variance

    def intervals(self, frame: pd.DataFrame, coverage: float = 0.8) -> pd.DataFrame:
        """Lower and upper bounds of the central `coverage` interval for frame[pred]; frame needs
        market, date, horizon_days and pred columns."""
        sd = np.sqrt(self._variance(frame["market"], frame["horizon_days"], frame["date"]))
        z = norm.ppf(0.5 + coverage / 2)
        return pd.DataFrame({"lower": frame["pred"] * np.exp(-z * sd), "upper": frame["pred"] * np.exp(z * sd)}, index=frame.index)


def leave_one_origin_out_coverage(predictions: pd.DataFrame, coverage: float = 0.8) -> pd.DataFrame:
    """Empirical coverage when each fold's intervals come from a noise model fitted on the other
    folds only; one row per (fold, market) with n and covered share.

    Rolling folds overlap in calendar time, so the other folds share some target dates with the
    held-out one; the estimate is out-of-origin, not fully independent."""
    rows = []
    for fold, held_out in predictions.groupby("fold"):
        model = NoiseModel().fit(predictions[predictions["fold"] != fold])
        bounds = model.intervals(held_out, coverage)
        inside = (held_out["actual"] >= bounds["lower"]) & (held_out["actual"] <= bounds["upper"])
        for market, hits in inside.groupby(held_out["market"]):
            rows.append({"fold": fold, "market": market, "n": len(hits), "covered": float(hits.mean())})
    return pd.DataFrame(rows)
