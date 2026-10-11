"""Daily international panel with seats, P2P and total passengers per market-day, and its weekly sums.
Cached under out/ (licensed data, gitignored)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from tourism_twin.data.daily_panel import build_daily_panel, with_scheduled_seats
from tourism_twin.data.panel import build_market_case
from tourism_twin.data.repository import LakeRepository
from tourism_twin.domain.markets import DOMESTIC, TOP_15_INTERNATIONAL_MARKETS

OUT = Path(__file__).resolve().parent / "out"


def _daily_schedule() -> pd.DataFrame:
    """Per (market, date), departure country mapped as in `daily_seats`: total passengers (to report
    load factor, never a model input) and the schedule inputs of variant C. average_weekly_frequency
    x days in month is a whole number of flights per week (7, 14, 21, ...) on every row, so flights
    per day = that / 7."""
    case = build_market_case(tuple(TOP_15_INTERNATIONAL_MARKETS)).format(col="departure_country_name")
    connection = LakeRepository().sql()
    try:
        schedule = connection.execute(f"""
            SELECT date, CASE
{case}
                END AS market,
                SUM(total_pax) AS pax,
                SUM(average_weekly_frequency * dayofmonth(last_day(date)) / 7.0) AS flights,
                COUNT(average_weekly_frequency) AS rows_with_frequency, COUNT(*) AS route_rows,
                COUNT(DISTINCT airline_name) AS airlines,
                SUM(business_class_seat_capacity + first_class_seat_capacity) AS premium_seats
            FROM flight_daily GROUP BY 1, 2
        """).df()
    finally:
        connection.close()
    schedule["date"] = pd.to_datetime(schedule["date"])
    schedule["flights"] = schedule["flights"].where(schedule["rows_with_frequency"] == schedule["route_rows"])
    return schedule.drop(columns=["rows_with_frequency", "route_rows"])


def panel() -> pd.DataFrame:
    path = OUT / "panel.pkl"
    if path.exists():
        return pd.read_pickle(path)
    frame = with_scheduled_seats(build_daily_panel())
    frame = frame[frame["market"] != DOMESTIC].reset_index(drop=True)
    frame = frame.merge(_daily_schedule(), on=["market", "date"], how="left", validate="one_to_one")
    flown = frame["seats"].notna()
    frame.loc[flown & (frame["seats"] == 0), ["pax", "flights", "airlines", "premium_seats"]] = 0.0
    OUT.mkdir(exist_ok=True)
    frame.to_pickle(path)
    return frame


def week_start(dates: pd.Series) -> pd.Series:
    dates = pd.to_datetime(dates)
    return dates - pd.to_timedelta(dates.dt.weekday, unit="D")


def weekly(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Sums of `columns` per market-week, kept only for weeks with all 7 days present and non-missing."""
    keyed = frame[["market", "date", *columns]].assign(week_start=week_start(frame["date"]))
    grouped = keyed.groupby(["market", "week_start"])
    sums = grouped[columns].sum(min_count=1)
    complete = grouped[columns].count().min(axis=1) == 7
    return sums[complete].reset_index()
