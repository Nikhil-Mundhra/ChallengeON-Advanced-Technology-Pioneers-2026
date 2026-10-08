"""Missing-value policies applied before aggregation."""

from __future__ import annotations

import pandas as pd


def interpolate_within_series(values: pd.Series, series_key: pd.Series) -> pd.Series:
    """Linear interpolation inside each series (rows must be time-ordered within a key); leading
    and trailing gaps take the nearest observed value."""
    return values.groupby(series_key).transform(lambda s: s.interpolate(method="linear", limit_direction="both"))
