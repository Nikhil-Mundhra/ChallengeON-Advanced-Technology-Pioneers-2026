"""Panels for the back-test, cut at the end of VALIDATION_ORIGINS (2025-01-31) so no FROZEN_TEST
row is ever read. Daily panel (international, seats per day) for the chain; the weekly market panel
for the ratio models. Cached under out/ (licensed data, gitignored)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from tourism_twin.config import SETTINGS
from tourism_twin.data.daily_panel import build_daily_panel, with_scheduled_seats
from tourism_twin.data.panel import build_market_case, training_window
from tourism_twin.data.repository import LakeRepository
from tourism_twin.domain.markets import DOMESTIC, TOP_15_INTERNATIONAL_MARKETS
from tourism_twin.models.backtest import VALIDATION_ORIGINS

OUT = Path(__file__).resolve().parent / "out"
CUT = VALIDATION_ORIGINS.end  # last day any row may come from
TREND_WEEKS = 13


def daily() -> pd.DataFrame:
    path = OUT / "daily.pkl"
    if path.exists():
        return pd.read_pickle(path)
    frame = with_scheduled_seats(build_daily_panel())
    frame = frame[(frame["market"] != DOMESTIC) & (frame["date"] <= CUT)].reset_index(drop=True)
    OUT.mkdir(exist_ok=True)
    frame.to_pickle(path)
    return frame


def weekly_flights() -> pd.DataFrame:
    """Flights per market-week from flight_daily, departure country mapped as in the weekly panel.
    A row's average_weekly_frequency x days in its month / 7 is its flights that day (a whole number
    of flights per week on every row; the panel's weekly_flight_services counts route-airline-days,
    not flights). NaN for a week with a row without frequency."""
    case = build_market_case(tuple(TOP_15_INTERNATIONAL_MARKETS)).format(col="departure_country_name")
    connection = LakeRepository().sql()
    try:
        days = connection.execute(f"""
            SELECT date, CASE
{case}
                END AS market,
                SUM(average_weekly_frequency * dayofmonth(last_day(date)) / 7.0) AS flights,
                COUNT(average_weekly_frequency) = COUNT(*) AS complete
            FROM flight_daily WHERE date <= DATE '{CUT.date()}' GROUP BY 1, 2
        """).df()
    finally:
        connection.close()
    days["date"] = pd.to_datetime(days["date"])
    days["flights"] = days["flights"].where(days["complete"])
    return days.assign(week_start=week_start(days["date"])).groupby(["market", "week_start"])["flights"].sum(min_count=7).reset_index()


def weekly_panel() -> pd.DataFrame:
    """Complete training weeks of the weekly market panel (the planning models' input), international,
    weeks ending on or before CUT, with weekly flights."""
    panel = training_window(pd.read_parquet(SETTINGS.panel_path))
    panel["week_start"] = pd.to_datetime(panel["week_start"])
    panel = panel[(panel["market"] != DOMESTIC) & (panel["week_start"] + pd.Timedelta(days=6) <= CUT)]
    panel = panel.merge(weekly_flights(), on=["market", "week_start"], how="left", validate="one_to_one")
    return panel.reset_index(drop=True)


def folds() -> list:
    """The VALIDATION_ORIGINS folds, on the daily guest dates."""
    frame = daily()
    return VALIDATION_ORIGINS.folds(frame["date"][frame["guests"].notna()])


def week_start(dates: pd.Series) -> pd.Series:
    dates = pd.to_datetime(dates)
    return dates - pd.to_timedelta(dates.dt.weekday, unit="D")


def weekly_sums(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Sums of `columns` per market-week, kept only for weeks with all 7 days present and non-missing."""
    keyed = frame[["market", "date", *columns]].assign(week_start=week_start(frame["date"]))
    grouped = keyed.groupby(["market", "week_start"])
    sums = grouped[columns].sum(min_count=1)
    complete = grouped[columns].count().min(axis=1) == 7
    return sums[complete].reset_index()


def centred_trend(weekly: pd.DataFrame, column: str, weeks: int = TREND_WEEKS) -> pd.Series:
    """Centred `weeks`-week mean of `column` per market on a full weekly calendar; NaN unless every
    week of the window is present. Indexed like `weekly`."""
    return _rolling(weekly, column, weeks, center=True)


def trailing_trend(weekly: pd.DataFrame, column: str, weeks: int = TREND_WEEKS) -> pd.Series:
    """Mean of `column` over the `weeks` weeks before each week (the week itself excluded)."""
    return _rolling(weekly, column, weeks, center=False, shift=1)


def _rolling(weekly: pd.DataFrame, column: str, weeks: int, center: bool, shift: int = 0) -> pd.Series:
    out = pd.Series(np.nan, index=weekly.index)
    for _, rows in weekly.groupby("market"):
        series = pd.Series(rows[column].to_numpy(dtype=float), index=pd.DatetimeIndex(rows["week_start"]))
        full = series.reindex(pd.date_range(series.index.min(), series.index.max(), freq="7D"))
        mean = full.shift(shift).rolling(weeks, center=center, min_periods=weeks).mean()
        out.loc[rows.index] = mean.reindex(series.index).to_numpy()
    return out
