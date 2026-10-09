"""New-arrival lags within each market's daily series (the stock-flow model's inputs)."""

from __future__ import annotations

import pandas as pd

from tourism_twin.features.registry import PANEL_FEATURES, Kind

DEFAULT_MAX_LAG = 21
BASE_WINDOW_DAYS = 90


def lag_column(k: int) -> str:
    return f"arrivals_lag_{k}"


@PANEL_FEATURES.feature(Kind.LAG, requires=["market", "date", "new_arrivals_filled"])
def arrival_lags(frame: pd.DataFrame, max_lag: int = DEFAULT_MAX_LAG, series: str = "market", **_) -> pd.DataFrame:
    """arrivals_lag_0..max_lag plus lag_complete. Expects rows sorted by (series, date) with a
    contiguous daily series per `series` (market, or nationality); shifts never cross series."""
    by_series = frame.groupby(series)["new_arrivals_filled"]
    lags = pd.DataFrame({lag_column(k): by_series.shift(k) for k in range(max_lag + 1)}, index=frame.index)
    lags["lag_complete"] = frame.groupby(series).cumcount() >= max_lag
    return lags


@PANEL_FEATURES.feature(Kind.LAG, requires=["market", "date", "new_arrivals_filled"])
def arrivals_mean_90(frame: pd.DataFrame, series: str = "market", **_) -> pd.Series:
    """Trailing BASE_WINDOW_DAYS mean of new arrivals within each series (market, or nationality),
    today included (shorter at a series' start). Expects rows sorted by (series, date), contiguous."""
    return frame.groupby(series)["new_arrivals_filled"].transform(lambda s: s.rolling(BASE_WINDOW_DAYS, min_periods=1).mean())
