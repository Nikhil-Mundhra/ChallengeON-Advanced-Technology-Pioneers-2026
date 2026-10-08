"""Calendar and event features for the residual layer. Flight levers are deliberately absent,
which is what keeps the hybrid model monotonic in aviation capacity."""

from __future__ import annotations

import numpy as np


def extract_calendar_features(
    iso_week: int,
    quarter: int,
    month: int,
    is_holiday_week: int,
    is_major_event_week: int,
) -> np.ndarray:
    """Extract regularized calendar and event features for a single observation."""
    sin_w1 = np.sin(2.0 * np.pi * iso_week / 52.1775)
    cos_w1 = np.cos(2.0 * np.pi * iso_week / 52.1775)
    sin_w2 = np.sin(4.0 * np.pi * iso_week / 52.1775)
    cos_w2 = np.cos(4.0 * np.pi * iso_week / 52.1775)

    q1 = 1.0 if quarter == 1 else 0.0
    q2 = 1.0 if quarter == 2 else 0.0
    q3 = 1.0 if quarter == 3 else 0.0
    q4 = 1.0 if quarter == 4 else 0.0

    winter = 1.0 if month in (11, 12, 1, 2, 3) else 0.0
    summer = 1.0 if month in (6, 7, 8) else 0.0

    return np.array([
        sin_w1,
        cos_w1,
        sin_w2,
        cos_w2,
        float(is_holiday_week),
        float(is_major_event_week),
        q1,
        q2,
        q3,
        q4,
        winter,
        summer,
    ], dtype=float)


FEATURE_NAMES = [
    "sin_week1",
    "cos_week1",
    "sin_week2",
    "cos_week2",
    "is_holiday_week",
    "is_major_event_week",
    "q1",
    "q2",
    "q3",
    "q4",
    "is_winter",
    "is_summer",
]
