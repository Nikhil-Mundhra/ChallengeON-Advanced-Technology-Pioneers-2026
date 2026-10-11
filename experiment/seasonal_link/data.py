"""Panels cut at the end of VALIDATION_ORIGINS (2025-01-31), so no FROZEN_TEST row is read: the daily
international panel with scheduled seats (chain input), its weekly sums, the weekly market panel
(TIME-ONLY), the folds, and the Ramadan and Eid windows. Cached under out/ (licensed data, gitignored)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from tourism_twin.config import SETTINGS
from tourism_twin.data.daily_panel import build_daily_panel, with_scheduled_seats
from tourism_twin.data.panel import training_window
from tourism_twin.domain.events import load_event_calendar
from tourism_twin.domain.markets import DOMESTIC
from tourism_twin.domain.seasons import assign_season
from tourism_twin.features import PANEL_FEATURES
from tourism_twin.models.backtest import VALIDATION_ORIGINS

OUT = Path(__file__).resolve().parent / "out"
CUT = VALIDATION_ORIGINS.end
SEAT_START = pd.Timestamp("2023-01-01")  # first day of the daily flight table
TREND_WEEKS = 13
LUNAR_EVENTS = ("ramadan", "eid_al_fitr", "eid_al_adha")
BIG_SIX = ["UNITED KINGDOM", "INDIA", "CHINA", "GERMANY", "SAUDI ARABIA", "RUSSIAN FEDERATION"]


def daily() -> pd.DataFrame:
    path = OUT / "daily.pkl"
    if path.exists():
        return pd.read_pickle(path)
    frame = PANEL_FEATURES.apply(with_scheduled_seats(build_daily_panel()), ["is_one_off_period"], anchor="date")
    frame = frame[(frame["market"] != DOMESTIC) & (frame["date"] <= CUT)].reset_index(drop=True)
    OUT.mkdir(exist_ok=True)
    frame.to_pickle(path)
    return frame


def folds() -> list:
    frame = daily()
    return VALIDATION_ORIGINS.folds(frame["date"][frame["guests"].notna()])


def week_start(dates: pd.Series) -> pd.Series:
    dates = pd.to_datetime(dates)
    return dates - pd.to_timedelta(dates.dt.weekday, unit="D")


def weekly_sums(frame: pd.DataFrame, columns: list) -> pd.DataFrame:
    """Sums of `columns` per market-week, only for weeks with all 7 days present and non-missing."""
    keyed = frame[["market", "date", *columns]].assign(week_start=week_start(frame["date"]))
    grouped = keyed.groupby(["market", "week_start"])
    sums = grouped[columns].sum(min_count=1)
    complete = grouped[columns].count().min(axis=1) == 7
    return sums[complete].reset_index()


def weekly_series() -> pd.DataFrame:
    """Complete market-weeks from SEAT_START to CUT: seats, p2p, arrivals (new_arrivals_filled), guests,
    month and project season of the week's Thursday, and whether the week touches a lunar event window."""
    frame = daily()
    frame = frame[frame["date"] >= SEAT_START].rename(columns={"new_arrivals_filled": "arrivals"})
    out = weekly_sums(frame, ["seats", "p2p", "arrivals", "guests"])
    mid = out["week_start"] + pd.Timedelta(days=3)
    out["month"] = mid.dt.month
    out["season"] = out["month"].map(assign_season)
    return out.assign(lunar=lunar_weeks(out["week_start"]))


def lunar_weeks(starts: pd.Series) -> np.ndarray:
    """True for a week (Monday start) that overlaps a Ramadan, Eid al-Fitr or Eid al-Adha window."""
    calendar = load_event_calendar()
    calendar = calendar[calendar["event"].isin(LUNAR_EVENTS)].drop_duplicates(["event", "anchor_date"])
    hit = np.zeros(len(starts), dtype=bool)
    begin, end = starts.to_numpy(), (starts + pd.Timedelta(days=6)).to_numpy()
    for low, high in zip(calendar["window_start"].to_numpy(), calendar["window_end"].to_numpy()):
        hit |= (begin <= high) & (end >= low)
    return hit


def weekly_panel() -> pd.DataFrame:
    """Complete training weeks of the weekly market panel (TIME-ONLY input), international, ending by CUT."""
    panel = training_window(pd.read_parquet(SETTINGS.panel_path))
    panel["week_start"] = pd.to_datetime(panel["week_start"])
    panel = panel[(panel["market"] != DOMESTIC) & (panel["week_start"] + pd.Timedelta(days=6) <= CUT)]
    return panel.reset_index(drop=True)


def centred_trend(weekly: pd.DataFrame, column: str, weeks: int = TREND_WEEKS) -> pd.Series:
    """Centred `weeks`-week mean of `column` per market on a full weekly calendar; NaN unless every
    week of the window is present. Indexed like `weekly`."""
    out = pd.Series(np.nan, index=weekly.index)
    for _, rows in weekly.groupby("market"):
        series = pd.Series(rows[column].to_numpy(dtype=float), index=pd.DatetimeIndex(rows["week_start"]))
        full = series.reindex(pd.date_range(series.index.min(), series.index.max(), freq="7D"))
        mean = full.rolling(weeks, center=True, min_periods=weeks).mean()
        out.loc[rows.index] = mean.reindex(series.index).to_numpy()
    return out
