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
- Test-split row absent from the test file: the file keeps only rows with New Arrivals >= 10
  (train keeps rows with Guests >= 10), so absence means fewer than 10 arrivals. Such rows get the
  nationality's mean training arrivals on days below 10 (overall mean if it has none, about 5)
  instead of an interpolation across the gap; flagged arrivals_below_threshold.
- same_day_guests suppressed: left missing in the observed sum; counted.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import duckdb
import pandas as pd

from tourism_twin.config import SETTINGS
from tourism_twin.data.imputation import interpolate_within_series
from tourism_twin.data.panel import build_market_case
from tourism_twin.data.repository import LakeRepository
from tourism_twin.domain.markets import TOP_15_INTERNATIONAL_MARKETS
from tourism_twin.features import PANEL_FEATURES
from tourism_twin.features.lags import DEFAULT_MAX_LAG

PUBLICATION_MIN = 10  # test rows exist only where New Arrivals >= 10; train rows only where Guests >= 10

# Derived columns of the daily panel, in output order (definitions live in tourism_twin.features).
DAILY_FEATURES = [
    "arrival_lags",
    "dow",
    "iso_week",
    "month",
    "quarter",
    "year",
    "season",
    "is_holiday_week",
    "is_major_event_week",
]


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
    rows["new_arrivals_filled"] = interpolate_within_series(rows["new_arrivals"], series_key)
    rows["absent_record"] = ~present
    rows["arrivals_below_threshold"] = ~present & (rows["dataset_split"] == "test")
    rows.loc[rows["arrivals_below_threshold"], "new_arrivals_filled"] = _below_threshold_arrivals(rows).loc[rows["arrivals_below_threshold"]]
    rows["same_day_suppressed"] = present & rows["same_day_guests"].isna()
    return rows


def _below_threshold_arrivals(rows: pd.DataFrame) -> pd.Series:
    """Per row, the nationality's mean training arrivals on days below PUBLICATION_MIN (the overall
    such mean for a nationality without any)."""
    small = rows[(rows["dataset_split"] == "train") & (rows["new_arrivals"] < PUBLICATION_MIN)]
    key = rows["residence_group"] + "|" + rows["nationality"].fillna("")
    by_nationality = small["new_arrivals"].groupby(key.loc[small.index]).mean()
    return key.map(by_nationality).fillna(small["new_arrivals"].mean())


def build_nationality_rows(repository: Optional[LakeRepository] = None) -> pd.DataFrame:
    """Nationality-day rows of the guest table with their market and new_arrivals_filled."""
    rows = _with_markets((repository or LakeRepository()).guests())
    rows["date"] = pd.to_datetime(rows["date"])
    return _fill_suppressed_arrivals(rows)


def build_daily_panel(
    repository: Optional[LakeRepository] = None,
    max_lag: int = DEFAULT_MAX_LAG,
) -> pd.DataFrame:
    """One row per (market, date) across both splits, with arrival lags 0..max_lag."""
    rows = build_nationality_rows(repository)

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
            n_arrivals_below_threshold=("arrivals_below_threshold", "sum"),
            n_same_day_suppressed=("same_day_suppressed", "sum"),
        )
    )
    duplicated_days = panel.duplicated(["market", "date"])
    if duplicated_days.any():
        raise ValueError(f"{int(duplicated_days.sum())} market-days fall in both splits")

    panel["arrivals_interpolated"] = panel["n_arrivals_interpolated"] > 0
    panel["same_day_was_suppressed"] = panel["n_same_day_suppressed"] > 0
    panel["has_absent_records"] = panel["n_absent_records"] > 0

    panel = panel.sort_values(["market", "date"]).reset_index(drop=True)
    gaps = panel.groupby("market")["date"].diff().dt.days.dropna()
    if (gaps != 1).any():
        raise ValueError("A market's daily series is not contiguous; lags would be misaligned")

    return PANEL_FEATURES.apply(panel, DAILY_FEATURES, anchor="date", max_lag=max_lag)


def save_daily_panel(
    output_path: Path = SETTINGS.daily_panel_path,
    repository: Optional[LakeRepository] = None,
    max_lag: int = DEFAULT_MAX_LAG,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    build_daily_panel(repository, max_lag=max_lag).to_parquet(output_path, index=False)
    return output_path
