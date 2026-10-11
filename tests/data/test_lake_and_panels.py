"""Lake grain contract, weekly and daily panels, and the test-file row rules."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from tourism_twin.config import SETTINGS
from tourism_twin.data.panel import build_weekly_panel
from tourism_twin.features.lags import DEFAULT_MAX_LAG, lag_column
from tourism_twin.domain.markets import MODELED_MARKETS


EXPECTED_MARKETS = set(MODELED_MARKETS)


def test_lake_tables_keep_their_grain_contract():
    flights = pd.read_parquet(SETTINGS.flight_daily_path)
    assert (flights["source_grain"] == "daily").all()
    assert pd.to_datetime(flights["date"]).min() >= pd.Timestamp("2023-01-01")
    if SETTINGS.flight_monthly_path.exists():  # built by `twin build-lake`, not committed
        monthly = pd.read_parquet(SETTINGS.flight_monthly_path)
        assert (monthly["source_grain"] == "monthly").all() and pd.to_datetime(monthly["date"]).max().year == 2022

    guests = pd.read_parquet(SETTINGS.guest_daily_path)
    assert {"is_source_present", "target_available", "is_suppressed_arrival", "source_grain"} <= set(guests.columns)
    assert len(guests) == 69_920  # 1,520 dates x (45 international nationalities + domestic)


def test_weekly_panel_contract(weekly_panel: pd.DataFrame):
    assert set(weekly_panel["market"]) == EXPECTED_MARKETS
    assert not weekly_panel.duplicated(["week_start", "market", "dataset_split"]).any()
    assert (weekly_panel.loc[weekly_panel["is_complete_week"] == 1, "days_in_week"] == 7).all()
    # Load factors above 100% are kept raw and flagged; only the modelling column is clipped.
    assert weekly_panel["load_factor_raw"].max() > 1.0
    assert weekly_panel["load_factor"].max() <= 1.0
    assert (weekly_panel["is_load_factor_outlier"] == 1).sum() > 0


def test_weekly_panel_rebuilds_from_the_lake_exactly(weekly_panel: pd.DataFrame):
    assert build_weekly_panel().equals(weekly_panel)


def test_daily_panel_contract(daily_panel: pd.DataFrame):
    assert set(daily_panel["market"]) == EXPECTED_MARKETS
    incomplete = daily_panel[~daily_panel["lag_complete"]]
    assert (incomplete.groupby("market").size() == DEFAULT_MAX_LAG).all()
    assert incomplete[lag_column(DEFAULT_MAX_LAG)].isna().all()
    lag_columns = [lag_column(k) for k in range(DEFAULT_MAX_LAG + 1)]
    assert daily_panel.loc[daily_panel["lag_complete"], lag_columns].notna().all().all()
    assert daily_panel["new_arrivals_filled"].notna().all()

    assert daily_panel.loc[daily_panel["dataset_split"] == "test", "guests"].isna().all()
    train = daily_panel[daily_panel["dataset_split"] == "train"]
    assert (train["guests"].isna() == (train["n_absent_records"] == train["n_records"])).all()


@pytest.mark.parametrize("market", ["UNITED KINGDOM", "DOMESTIC", "OTHER_EUROPE"])
def test_daily_lags_cross_the_train_test_boundary(daily_panel: pd.DataFrame, market: str):
    series = daily_panel[daily_panel["market"] == market].set_index("date")
    day = series.index[series["dataset_split"] == "test"].min()
    row = series.loc[day]
    for k in range(DEFAULT_MAX_LAG + 1):
        assert row[lag_column(k)] == series.loc[day - np.timedelta64(k, "D"), "new_arrivals_filled"], f"lag {k}"
    assert series.loc[day - np.timedelta64(1, "D"), "dataset_split"] == "train"
    assert bool(row["lag_complete"])


def test_daily_panel_sums_to_the_weekly_panel(daily_panel: pd.DataFrame, weekly_panel: pd.DataFrame):
    from tourism_twin.data.daily_panel import with_scheduled_seats

    daily = with_scheduled_seats(daily_panel[daily_panel["date"] >= "2023-01-01"])
    daily = daily.assign(week_start=daily["date"].dt.to_period("W-SUN").dt.start_time.dt.date)
    sums = (
        daily.groupby(["week_start", "dataset_split", "market"])
        .agg(guests=("guests", lambda s: s.sum(min_count=1)), new_arrivals=("new_arrivals", lambda s: s.sum(min_count=1)),
             seats=("seats", "sum"), p2p=("p2p", "sum"))  # DOMESTIC has no flights: 0, as in the weekly panel
        .reset_index()
    )
    merged = weekly_panel.merge(sums, on=["week_start", "dataset_split", "market"], how="outer", suffixes=("_weekly", "_daily"), indicator=True)
    assert (merged["_merge"] == "both").all()
    for column in ("guests", "new_arrivals", "seats", "p2p"):
        weekly_values, daily_values = merged[f"{column}_weekly"], merged[f"{column}_daily"]
        assert (weekly_values.isna() == daily_values.isna()).all(), column
        both = weekly_values.notna()
        np.testing.assert_allclose(weekly_values[both], daily_values[both], rtol=0, atol=1e-6, err_msg=column)


def test_test_days_missing_from_the_file_get_below_threshold_arrivals():
    from tourism_twin.data.daily_panel import PUBLICATION_MIN, _fill_suppressed_arrivals

    dates = pd.date_range("2025-07-28", periods=8, freq="D")
    rows = pd.DataFrame({
        "residence_group": "International", "nationality": "X", "date": dates,
        "dataset_split": ["train"] * 4 + ["test"] * 4,
        "new_arrivals": [4.0, np.nan, 50.0, 4.0, np.nan, np.nan, 11.0, 90.0],
        "is_source_present": [True, False, True, True, False, True, True, True],  # absent: train day 1, test day 4; '*': test day 5
        "same_day_guests": 1.0,
    })
    filled = _fill_suppressed_arrivals(rows)["new_arrivals_filled"].to_numpy()
    assert filled[1] == pytest.approx(27.0)  # a training absence keeps the interpolation (back-test unchanged)
    assert filled[4] == pytest.approx(4.0)  # a test absence gets the mean of train days below 10
    assert filled[5] == PUBLICATION_MIN  # a published test row had >= 10 arrivals: interpolated 8.67 is clipped
