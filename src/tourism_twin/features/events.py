"""Event features from the event registry (domain/events.csv)."""

from __future__ import annotations

from typing import Iterable, Optional

import numpy as np
import pandas as pd

from tourism_twin.domain.markets import DOMESTIC
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


def in_scope(markets: pd.Series, scope: str) -> pd.Series:
    """Whether each market is covered by an event scope: all, domestic, international, or one market."""
    if scope == "all":
        return pd.Series(True, index=markets.index)
    if scope not in ("domestic", "international"):
        return markets == scope
    domestic = markets == DOMESTIC
    return domestic if scope == "domestic" else ~domestic


@PANEL_FEATURES.feature(Kind.FLAG, requires=["@anchor", "market"])
def is_one_off_period(frame: pd.DataFrame, anchor: str, **_) -> pd.Series:
    """1 inside a one-off shock window for the markets it hit (masked from training)."""
    dates = pd.to_datetime(frame[anchor])
    calendar = load_event_calendar()
    inside = pd.Series(False, index=frame.index)
    for row in calendar[calendar["kind"] == "one_off"].itertuples():
        inside |= (dates >= row.window_start) & (dates <= row.window_end) & in_scope(frame["market"], row.scope)
    return inside.astype(int)
