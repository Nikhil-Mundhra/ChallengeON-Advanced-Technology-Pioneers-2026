"""New-arrival lags within each market's daily series (the stock-flow model's inputs)."""

from __future__ import annotations

import pandas as pd

from tourism_twin.features.registry import PANEL_FEATURES, Kind

DEFAULT_MAX_LAG = 21


def lag_column(k: int) -> str:
    return f"arrivals_lag_{k}"


@PANEL_FEATURES.feature(Kind.LAG, requires=["market", "date", "new_arrivals_filled"])
def arrival_lags(frame: pd.DataFrame, max_lag: int = DEFAULT_MAX_LAG, **_) -> pd.DataFrame:
    """arrivals_lag_0..max_lag plus lag_complete. Expects rows sorted by (market, date) with a
    contiguous daily series per market; shifts never cross markets."""
    by_market = frame.groupby("market")["new_arrivals_filled"]
    lags = pd.DataFrame({lag_column(k): by_market.shift(k) for k in range(max_lag + 1)}, index=frame.index)
    lags["lag_complete"] = frame.groupby("market").cumcount() >= max_lag
    return lags
