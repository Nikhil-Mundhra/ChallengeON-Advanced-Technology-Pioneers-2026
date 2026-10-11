"""Synthetic data with a known answer, shared by the model tests."""

from __future__ import annotations

import numpy as np
import pandas as pd
from tourism_twin.features import PANEL_FEATURES
from tourism_twin.models.components import LinearRegressors, LinearTrend


def _synthetic(level=8.0, slope=0.05, season=0.3, event=0.5, noise=0.01, market="M", seed=0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2023-01-01", periods=730, freq="D")
    years = (dates - dates[0]).days.to_numpy() / 365.25
    sin = np.sin(2 * np.pi * dates.dayofyear.to_numpy() / 365.25)
    bump = ((dates.dayofyear >= 100) & (dates.dayofyear < 110)).astype(float)
    log_y = level + slope * years + season * sin + event * bump + rng.normal(0.0, noise, len(dates))
    return pd.DataFrame({"market": market, "date": dates, "sin": sin, "bump": bump, "guests": np.exp(log_y)})


def _components():
    return [LinearTrend(), LinearRegressors(["sin"], name="season"), LinearRegressors(["bump"], name="event")]


def _calendar(event: str, anchors, start: int, end: int, kind: str = "solar", scope: str = "all") -> pd.DataFrame:
    calendar = pd.DataFrame({"event": event, "kind": kind, "anchor_date": pd.to_datetime(anchors),
                             "window_start_offset": start, "window_end_offset": end, "scope": scope})
    calendar["window_start"] = calendar["anchor_date"] + pd.to_timedelta(start, unit="D")
    calendar["window_end"] = calendar["anchor_date"] + pd.to_timedelta(end, unit="D")
    return calendar


def _daily(log_y: np.ndarray, start: str = "2023-01-01", **columns) -> pd.DataFrame:
    dates = pd.date_range(start, periods=len(log_y), freq="D")
    return pd.DataFrame({"market": "M", "date": dates, "guests": np.exp(log_y), **columns})


def _conv_frame(true_w: np.ndarray, base: float, noise: float, n: int = 900, seed: int = 5) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    max_lag = len(true_w) - 1
    arrivals = 1000 * np.exp(0.3 * np.sin(2 * np.pi * np.arange(n) / 365.25) + rng.normal(0, 0.15, n))
    lags = np.column_stack([np.r_[np.full(k, np.nan), arrivals[:n - k]] for k in range(max_lag + 1)])
    guests = (base + np.nan_to_num(lags) @ true_w) * np.exp(rng.normal(0, noise, n))
    return PANEL_FEATURES.apply(_daily(np.log(guests), new_arrivals_filled=arrivals), ["arrival_lags"], max_lag=max_lag)


def _calendar_conv_frame(seed: int = 11, noise: float = 0.05) -> pd.DataFrame:
    """Guests = (base + kernel * arrivals) * exp(strong season and weekend multipliers + noise), w0 = 1.4."""
    rng = np.random.default_rng(seed)
    n, true_w = 900, 1.4 * np.exp(-np.arange(8) / 2.5)
    arrivals = 1000 * np.exp(0.4 * np.sin(2 * np.pi * np.arange(n) / 365.25) + rng.normal(0, 0.2, n))
    lags = np.column_stack([np.r_[np.full(k, np.nan), arrivals[:n - k]] for k in range(len(true_w))])
    dates = pd.date_range("2022-01-01", periods=n, freq="D")
    calendar = 0.4 * (np.cos(2 * np.pi * dates.dayofyear / 365.25) + (dates.dayofweek >= 4))
    guests = (200.0 + np.nan_to_num(lags) @ true_w) * np.exp(calendar + rng.normal(0, noise, n))
    return PANEL_FEATURES.apply(_daily(np.log(guests), new_arrivals_filled=arrivals), ["arrival_lags"], max_lag=7)


def _seat_chain_frame(n: int = 800, seed: int = 3, markets=("A", "B")) -> pd.DataFrame:
    """Two-link truth per market: arrivals = (base + seat kernel * seats) x weekday multiplier, guests =
    arrivals kernel * arrivals. Seats switch between schedules (step changes) so the kernel is identified."""
    rng = np.random.default_rng(seed)
    frames = []
    for i, market in enumerate(markets):
        dates = pd.date_range("2023-01-01", periods=n, freq="D")
        schedule = np.repeat(rng.uniform(800, 2000, n // 30 + 1), 30)[:n] * (1 + i)
        seats = schedule * rng.choice([0.0, 1.0, 1.0, 1.2], n)  # days without a flight, and extra rotations
        lags = np.column_stack([np.r_[np.full(k, np.nan), seats[:n - k]] for k in range(len(SEAT_W))])
        arrivals = (SEAT_BASE + np.nan_to_num(lags) @ SEAT_W) * np.exp(0.1 * ((dates.dayofweek >= 4) - 3 / 7) + rng.normal(0, 0.01, n))  # centred weekday
        arrival_lags = np.column_stack([np.r_[np.full(k, np.nan), arrivals[:n - k]] for k in range(len(GUEST_W))])
        guests = 300.0 + np.nan_to_num(arrival_lags) @ GUEST_W
        frames.append(pd.DataFrame({"market": market, "date": dates, "seats": seats, "p2p": 0.5 * seats,
                                    "new_arrivals_filled": arrivals, "guests": guests}))
    return pd.concat(frames, ignore_index=True)


SEAT_W = np.array([0.30, 0.15, 0.08, 0.04])
SEAT_BASE = 200.0
GUEST_W = np.exp(-np.arange(8) / 3.0)


def _ar1_backtest(phi: float, sigma: float, folds: int = 40, horizon: int = 120, seed: int = 11, scale: dict | None = None) -> pd.DataFrame:
    """Back-test-shaped predictions whose log errors follow an AR(1) along the horizon."""
    rng = np.random.default_rng(seed)
    frames = []
    for f in range(folds):
        s = sigma * (scale or {}).get(f, 1.0)
        error = np.zeros(horizon)
        for h in range(horizon):
            error[h] = (phi * error[h - 1] if h else 0.0) + rng.normal(0, s)
        origin = pd.Timestamp("2021-01-01") + pd.DateOffset(months=f)
        frames.append(pd.DataFrame({"fold": f"origin_{f:02d}", "origin": origin, "market": "UNITED KINGDOM",
                                    "horizon_days": np.arange(horizon), "date": origin + pd.to_timedelta(np.arange(horizon), unit="D"),
                                    "pred": 1000.0, "actual": 1000.0 * np.exp(error)}))
    return pd.concat(frames, ignore_index=True)


class _LastTrainDate:
    """Records the latest training date it saw; predicts the training mean."""
    seen: list = []

    def fit(self, panel):
        _LastTrainDate.seen.append(pd.to_datetime(panel["date"]).max())
        self.mean = panel["guests"].mean()
        return self

    def predict(self, panel):
        return pd.Series(self.mean, index=panel.index)
