"""Calendar and event features for the residual layer. Flight levers are deliberately absent,
which is what keeps the hybrid model monotonic in aviation capacity."""

from __future__ import annotations

import numpy as np

from tourism_twin.domain.seasons import assign_season


CALENDAR_COLUMNS = ("iso_week", "quarter", "month", "is_holiday_week", "is_major_event_week")


def calendar_feature_matrix(frame) -> np.ndarray:
    """Regularised calendar and event features, one row per observation: two week-of-year
    harmonic pairs, holiday and major-event flags, quarter dummies, winter and summer flags."""
    week = frame["iso_week"].to_numpy(dtype=float)
    quarter = frame["quarter"].to_numpy()
    season = np.array([assign_season(m) for m in frame["month"].to_numpy()])
    return np.column_stack([
        np.sin(2.0 * np.pi * week / 52.1775), np.cos(2.0 * np.pi * week / 52.1775),
        np.sin(4.0 * np.pi * week / 52.1775), np.cos(4.0 * np.pi * week / 52.1775),
        frame["is_holiday_week"].to_numpy(dtype=float), frame["is_major_event_week"].to_numpy(dtype=float),
        *[(quarter == q).astype(float) for q in (1, 2, 3, 4)],
        (season == "Winter_Peak").astype(float), (season == "Summer_Trough").astype(float),
    ])
