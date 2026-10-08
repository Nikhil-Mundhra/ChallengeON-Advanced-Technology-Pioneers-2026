"""Completeness and quality flags, and attributes derived from the market key."""

from __future__ import annotations

import pandas as pd

from tourism_twin.domain.archetypes import get_market_archetype
from tourism_twin.features.registry import PANEL_FEATURES, Kind


@PANEL_FEATURES.feature(Kind.FLAG, requires=["load_factor_raw"])
def is_load_factor_outlier(frame: pd.DataFrame, **_) -> pd.Series:
    return (frame["load_factor_raw"] > 1.0).astype(int)


@PANEL_FEATURES.feature(Kind.FLAG, requires=["days_in_week"])
def is_complete_week(frame: pd.DataFrame, **_) -> pd.Series:
    return (frame["days_in_week"] == 7).astype(int)


@PANEL_FEATURES.feature(Kind.FLAG, requires=["present_source_records", "total_grid_records", "missing_arrival_records"])
def is_complete_guest_inputs(frame: pd.DataFrame, **_) -> pd.Series:
    return (
        (frame["present_source_records"] == frame["total_grid_records"])
        & (frame["missing_arrival_records"] == 0)
    ).astype(int)


@PANEL_FEATURES.feature(Kind.ATTRIBUTE, requires=["market"])
def archetype(frame: pd.DataFrame, **_) -> pd.Series:
    return frame["market"].apply(lambda m: get_market_archetype(m).value)


@PANEL_FEATURES.feature(Kind.ATTRIBUTE, requires=["market"])
def is_domestic(frame: pd.DataFrame, **_) -> pd.Series:
    return (frame["market"] == "DOMESTIC").astype(int)
