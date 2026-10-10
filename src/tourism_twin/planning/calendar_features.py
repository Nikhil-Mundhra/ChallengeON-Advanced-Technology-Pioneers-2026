"""Calendar and event features for the residual layer. Flight levers are deliberately absent,
which is what keeps the hybrid model monotonic in aviation capacity."""

from __future__ import annotations

from typing import Sequence, Tuple

import numpy as np
import pandas as pd

from tourism_twin.domain.events import load_event_calendar
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


def residual_event_types() -> Tuple[str, ...]:
    """Event types from domain/events.csv that the weekly residual uses (one-off periods excluded)."""
    calendar = load_event_calendar()
    return tuple(sorted(calendar.loc[calendar["kind"] != "one_off", "event"].unique()))


def _applies(scope: str, market: str) -> bool:
    return (scope == "all" or scope == market or (scope == "international" and market != "DOMESTIC")
            or (scope == "domestic" and market == "DOMESTIC"))


def event_exposure_matrix(frame: pd.DataFrame, events: Sequence[str]) -> np.ndarray:
    """(rows x events): the share of each row's week (7 days from week_start) inside a window of
    that event whose scope covers the row's market. Validated against the calendar-only residual
    on VALIDATION_ORIGINS: -0.7 pp weekly WAPE, 90% interval [-1.55, -0.16], 7/7 origins."""
    calendar = load_event_calendar()
    starts = pd.to_datetime(frame["week_start"]).to_numpy()
    ends = starts + np.timedelta64(6, "D")
    markets = frame["market"].to_numpy()
    out = np.zeros((len(frame), len(events)))
    for j, event in enumerate(events):
        for window in calendar[calendar["event"] == event].itertuples():
            covered = np.array([_applies(window.scope, m) for m in markets])
            days = (np.minimum(ends, np.datetime64(window.window_end)) - np.maximum(starts, np.datetime64(window.window_start))) / np.timedelta64(1, "D") + 1
            out[:, j] += np.where(covered, np.clip(days, 0, 7) / 7, 0.0)
    return np.clip(out, 0.0, 1.0)


def residual_feature_matrix(frame: pd.DataFrame, events: Sequence[str] = ()) -> np.ndarray:
    """Calendar features, plus event exposure when `events` is given."""
    calendar = calendar_feature_matrix(frame)
    return np.column_stack([calendar, event_exposure_matrix(frame, events)]) if len(events) else calendar
