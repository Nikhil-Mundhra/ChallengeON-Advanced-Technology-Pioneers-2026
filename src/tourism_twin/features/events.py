"""Event features from the event registry (domain/events.csv)."""

from __future__ import annotations

from typing import Iterable, Optional

import numpy as np
import pandas as pd

from tourism_twin.domain.events import load_event_calendar
from tourism_twin.features.registry import PANEL_FEATURES, Kind


def offset_column(event: str) -> str:
    return f"event_offset__{event}"


def event_offsets(dates: pd.Series, calendar: pd.DataFrame, events: Optional[Iterable[str]] = None) -> pd.DataFrame:
    """Days from each event's anchor for dates inside that event's window; NaN elsewhere."""
    dates = pd.to_datetime(dates)
    events = list(events) if events is not None else sorted(calendar.loc[calendar["kind"] != "one_off", "event"].unique())
    out = pd.DataFrame(np.nan, index=dates.index, columns=[offset_column(e) for e in events])
    for row in calendar[calendar["event"].isin(events)].itertuples():
        inside = (dates >= row.window_start) & (dates <= row.window_end)
        out.loc[inside, offset_column(row.event)] = (dates[inside] - row.anchor_date).dt.days
    return out


@PANEL_FEATURES.feature(Kind.CALENDAR, requires=["@anchor"])
def event_day_offsets(frame: pd.DataFrame, anchor: str, **_) -> pd.DataFrame:
    return event_offsets(frame[anchor], load_event_calendar())


@PANEL_FEATURES.feature(Kind.FLAG, requires=["@anchor"])
def is_one_off_period(frame: pd.DataFrame, anchor: str, **_) -> pd.Series:
    """1 inside a one-off shock window (masked from training, not used as a feature)."""
    dates = pd.to_datetime(frame[anchor])
    calendar = load_event_calendar()
    inside = np.zeros(len(frame), dtype=bool)
    for row in calendar[calendar["kind"] == "one_off"].itertuples():
        inside |= ((dates >= row.window_start) & (dates <= row.window_end)).to_numpy()
    return pd.Series(inside.astype(int), index=frame.index)
