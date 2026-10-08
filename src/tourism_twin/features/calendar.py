"""Calendar features of a date column chosen per call (`anchor`: "date" daily, "week_start" weekly)."""

from __future__ import annotations

import pandas as pd

from tourism_twin.domain.events import HOLIDAY_WEEKS, MAJOR_EVENT_WEEKS
from tourism_twin.domain.seasons import assign_season
from tourism_twin.features.registry import PANEL_FEATURES, Kind


def _dates(frame: pd.DataFrame, anchor: str) -> pd.Series:
    return pd.to_datetime(frame[anchor])


def _week_start_keys(frame: pd.DataFrame, anchor: str) -> pd.Series:
    """Monday of the anchor's week, formatted like the keys in domain/events.py."""
    dates = _dates(frame, anchor)
    return (dates - pd.to_timedelta(dates.dt.dayofweek, unit="D")).dt.strftime("%Y-%m-%d")


@PANEL_FEATURES.feature(Kind.CALENDAR, requires=["@anchor"])
def dow(frame: pd.DataFrame, anchor: str, **_) -> pd.Series:
    return _dates(frame, anchor).dt.dayofweek


@PANEL_FEATURES.feature(Kind.CALENDAR, requires=["@anchor"])
def iso_week(frame: pd.DataFrame, anchor: str, **_) -> pd.Series:
    return _dates(frame, anchor).dt.isocalendar().week.astype(int)


@PANEL_FEATURES.feature(Kind.CALENDAR, requires=["@anchor"])
def month(frame: pd.DataFrame, anchor: str, **_) -> pd.Series:
    return _dates(frame, anchor).dt.month.astype(int)


@PANEL_FEATURES.feature(Kind.CALENDAR, requires=["@anchor"])
def quarter(frame: pd.DataFrame, anchor: str, **_) -> pd.Series:
    return _dates(frame, anchor).dt.quarter


@PANEL_FEATURES.feature(Kind.CALENDAR, requires=["@anchor"])
def year(frame: pd.DataFrame, anchor: str, **_) -> pd.Series:
    return _dates(frame, anchor).dt.year


@PANEL_FEATURES.feature(Kind.CALENDAR, requires=["month"])
def season(frame: pd.DataFrame, **_) -> pd.Series:
    return frame["month"].apply(assign_season)


@PANEL_FEATURES.feature(Kind.CALENDAR, requires=["season"])
def is_winter_peak(frame: pd.DataFrame, **_) -> pd.Series:
    return (frame["season"] == "Winter_Peak").astype(int)


@PANEL_FEATURES.feature(Kind.CALENDAR, requires=["season"])
def is_summer_trough(frame: pd.DataFrame, **_) -> pd.Series:
    return (frame["season"] == "Summer_Trough").astype(int)


@PANEL_FEATURES.feature(Kind.CALENDAR, requires=["@anchor"])
def is_holiday_week(frame: pd.DataFrame, anchor: str, **_) -> pd.Series:
    return _week_start_keys(frame, anchor).isin(HOLIDAY_WEEKS).astype(int)


@PANEL_FEATURES.feature(Kind.CALENDAR, requires=["@anchor"])
def is_major_event_week(frame: pd.DataFrame, anchor: str, **_) -> pd.Series:
    return _week_start_keys(frame, anchor).isin(MAJOR_EVENT_WEEKS).astype(int)
