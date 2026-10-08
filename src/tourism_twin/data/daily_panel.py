"""Daily (market, date) modelling panel with new-arrival lags, for the stock-flow guest model.

Guests on day t are a stock; new arrivals are the flow into it. The panel carries arrival lags
0..K so a model can learn how long arrivals stay (Guests_t ~ sum_k w_k * Arrivals_{t-k}).
The competition test split withholds only Guests, so arrivals in both splits are features.

Missing-value policy (per nationality-day, before aggregating to markets):
- Present row with new_arrivals suppressed ('*'), or absent grid row (nationality not reported
  that day): arrivals are linearly interpolated within the nationality's series for the lag
  features (new_arrivals_filled). Absent rows are not zero activity: Israel, a top-15 market, is
  absent for four days in Jan 2022. The observed sum (new_arrivals) still skips both, so weekly
  sums reconcile with the weekly panel. Both cases are counted per market-day.
- same_day_guests suppressed: left missing in the observed sum; counted.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from tourism_twin.config import SETTINGS
from tourism_twin.data.panel import build_market_case
from tourism_twin.domain.events import HOLIDAY_WEEKS, MAJOR_EVENT_WEEKS
from tourism_twin.domain.markets import TOP_15_INTERNATIONAL_MARKETS
from tourism_twin.domain.seasons import assign_season

DEFAULT_MAX_LAG = 21


def lag_column(k: int) -> str:
    return f"arrivals_lag_{k}"


def _with_markets(guests: pd.DataFrame) -> pd.DataFrame:
    """Attach the market label with the exact mapping the weekly panel uses."""
    case = build_market_case(tuple(TOP_15_INTERNATIONAL_MARKETS)).format(col="nationality")
    query = f"""
        SELECT *,
            CASE
                WHEN residence_group = 'Domestic' THEN 'DOMESTIC'
{case}
            END AS market
        FROM guests
    """
    return duckdb.sql(query).df()


def _fill_suppressed_arrivals(rows: pd.DataFrame) -> pd.DataFrame:
    """Nationality-level arrivals with suppressed and absent values interpolated."""
    rows = rows.sort_values(["residence_group", "nationality", "date"], na_position="first").copy()
    present = rows["is_source_present"].astype(bool)
    rows["arrivals_interpolated"] = present & rows["new_arrivals"].isna()

    series_key = rows["residence_group"] + "|" + rows["nationality"].fillna("")
    rows["new_arrivals_filled"] = (
        rows["new_arrivals"]
        .groupby(series_key)
        .transform(lambda s: s.interpolate(method="linear", limit_direction="both"))
    )
    rows["absent_record"] = ~present
    rows["same_day_suppressed"] = present & rows["same_day_guests"].isna()
    return rows


def _add_lags(panel: pd.DataFrame, max_lag: int) -> pd.DataFrame:
    """Lags over each market's concatenated train+test series, so early test days see train days."""
    panel = panel.sort_values(["market", "date"]).reset_index(drop=True)
    by_market = panel.groupby("market")["new_arrivals_filled"]
    lags = {lag_column(k): by_market.shift(k) for k in range(max_lag + 1)}
    panel = pd.concat([panel, pd.DataFrame(lags)], axis=1)
    position = panel.groupby("market").cumcount()
    panel["lag_complete"] = position >= max_lag
    return panel


def _add_calendar(panel: pd.DataFrame) -> pd.DataFrame:
    dates = panel["date"]
    week_start = (dates - pd.to_timedelta(dates.dt.dayofweek, unit="D")).dt.strftime("%Y-%m-%d")
    panel["dow"] = dates.dt.dayofweek
    panel["iso_week"] = dates.dt.isocalendar().week.astype(int)
    panel["month"] = dates.dt.month
    panel["quarter"] = dates.dt.quarter
    panel["year"] = dates.dt.year
    panel["season"] = panel["month"].apply(assign_season)
    panel["is_holiday_week"] = week_start.isin(HOLIDAY_WEEKS).astype(int)
    panel["is_major_event_week"] = week_start.isin(MAJOR_EVENT_WEEKS).astype(int)
    return panel


def build_daily_panel(
    guest_path: Path = SETTINGS.guest_daily_path,
    max_lag: int = DEFAULT_MAX_LAG,
) -> pd.DataFrame:
    """One row per (market, date) across both splits, with arrival lags 0..max_lag."""
    rows = _with_markets(pd.read_parquet(guest_path))
    rows["date"] = pd.to_datetime(rows["date"])
    rows = _fill_suppressed_arrivals(rows)

    panel = (
        rows.groupby(["market", "date", "dataset_split"], as_index=False)
        .agg(
            guests=("guests", lambda s: s.sum(min_count=1)),
            new_arrivals=("new_arrivals", lambda s: s.sum(min_count=1)),
            new_arrivals_filled=("new_arrivals_filled", "sum"),
            same_day_guests=("same_day_guests", lambda s: s.sum(min_count=1)),
            n_records=("date", "size"),
            n_absent_records=("absent_record", "sum"),
            n_arrivals_interpolated=("arrivals_interpolated", "sum"),
            n_same_day_suppressed=("same_day_suppressed", "sum"),
        )
    )
    duplicated_days = panel.duplicated(["market", "date"])
    if duplicated_days.any():
        raise ValueError(f"{int(duplicated_days.sum())} market-days fall in both splits")

    panel["arrivals_interpolated"] = panel["n_arrivals_interpolated"] > 0
    panel["same_day_was_suppressed"] = panel["n_same_day_suppressed"] > 0
    panel["has_absent_records"] = panel["n_absent_records"] > 0

    gaps = panel.sort_values(["market", "date"]).groupby("market")["date"].diff().dt.days.dropna()
    if (gaps != 1).any():
        raise ValueError("A market's daily series is not contiguous; lags would be misaligned")

    return _add_calendar(_add_lags(panel, max_lag))


def save_daily_panel(
    output_path: Path = SETTINGS.daily_panel_path,
    guest_path: Path = SETTINGS.guest_daily_path,
    max_lag: int = DEFAULT_MAX_LAG,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    build_daily_panel(guest_path=guest_path, max_lag=max_lag).to_parquet(output_path, index=False)
    return output_path
