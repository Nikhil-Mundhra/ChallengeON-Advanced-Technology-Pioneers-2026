"""Operational ratios of the aviation-to-hotel chain. Kind.RATIO: compute from the (summed)
parts at the grain in use; never sum or average a ratio across rows."""

from __future__ import annotations

import numpy as np
import pandas as pd

from tourism_twin.features.registry import PANEL_FEATURES, Kind


@PANEL_FEATURES.feature(Kind.RATIO, requires=["pax", "seats"])
def load_factor_raw(frame: pd.DataFrame, **_) -> np.ndarray:
    """Passengers per seat, unclipped: values above 1 are real source anomalies, kept and flagged."""
    return np.where(frame["seats"] > 0, frame["pax"] / frame["seats"], np.nan)


@PANEL_FEATURES.feature(Kind.RATIO, requires=["load_factor_raw"])
def load_factor(frame: pd.DataFrame, **_) -> np.ndarray:
    return np.clip(frame["load_factor_raw"], 0.0, 1.0)


@PANEL_FEATURES.feature(Kind.RATIO, requires=["p2p", "pax"])
def p2p_share(frame: pd.DataFrame, **_) -> np.ndarray:
    return np.where(frame["pax"] > 0, np.clip(frame["p2p"] / frame["pax"], 0.0, 1.0), np.nan)


@PANEL_FEATURES.feature(Kind.RATIO, requires=["guests", "new_arrivals"])
def implied_los(frame: pd.DataFrame, **_) -> np.ndarray:
    """Guests per new arrival: the length of stay implied by the stock-flow identity."""
    return np.where(
        (frame["new_arrivals"] > 0) & frame["guests"].notnull(),
        frame["guests"] / frame["new_arrivals"],
        np.nan,
    )


@PANEL_FEATURES.feature(Kind.RATIO, requires=["new_arrivals", "p2p"])
def effective_response_multiplier(frame: pd.DataFrame, **_) -> np.ndarray:
    """Hotel new arrivals per point-to-point passenger."""
    return np.where(frame["p2p"] > 0, frame["new_arrivals"] / frame["p2p"], np.nan)
