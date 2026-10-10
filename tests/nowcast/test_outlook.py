"""Seasonal outlook (nowcast/outlook): the arrivals scenario beyond the last known day."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tourism_twin.nowcast.outlook import FROZEN_TEST, Window, _extend_arrivals, arrivals_growth, backtest_outlook


def _panel(days: int = 800) -> pd.DataFrame:
    dates = pd.date_range("2022-01-01", periods=days, freq="D")
    frames = []
    for market, level, growth in (("UNITED KINGDOM", 100.0, 1.2), ("DOMESTIC", 50.0, 1.0)):
        arrivals = level * growth ** (np.arange(days) / 365)
        frames.append(pd.DataFrame({"market": market, "date": dates, "dataset_split": "train",
                                    "guests": arrivals * 3, "new_arrivals_filled": arrivals}))
    return pd.concat(frames, ignore_index=True)


def test_trend_growth_is_the_ratio_of_the_last_two_years_and_flat_is_one():
    panel = _panel()
    trend = arrivals_growth(panel, "trend")
    assert trend["UNITED KINGDOM"] == pytest.approx(1.2, rel=1e-3) and trend["DOMESTIC"] == pytest.approx(1.0)
    assert (arrivals_growth(panel, "flat") == 1.0).all()
    with pytest.raises(ValueError, match="Unknown arrivals scenario"):
        arrivals_growth(panel, "boom")


def test_scenario_days_repeat_the_same_weekday_a_year_earlier_times_growth_and_stay_contiguous():
    panel = _panel()
    last = panel["date"].max()
    until = last + pd.Timedelta(days=500)  # beyond one year: the growth compounds
    extended = _extend_arrivals(panel, until, "trend")
    uk = extended[extended["market"] == "UNITED KINGDOM"].set_index("date")["new_arrivals_filled"]
    assert uk.index.max() >= until and (uk.index.to_series().diff().dropna().dt.days == 1).all()
    day = last + pd.Timedelta(days=10)
    assert uk[day] == pytest.approx(uk[day - pd.Timedelta(days=364)] * 1.2, rel=1e-3)
    later = last + pd.Timedelta(days=400)
    assert uk[later] == pytest.approx(uk[later - pd.Timedelta(days=728)] * 1.2 ** 2, rel=1e-3)
    assert extended.loc[extended["date"] > last, "guests"].isna().all()
    assert {"arrivals_lag_21", "dow", "is_holiday_week"} <= set(extended.columns)


def test_backtest_refuses_the_frozen_test():
    window = Window("frozen", FROZEN_TEST[0], FROZEN_TEST[0] + pd.Timedelta(days=30))
    with pytest.raises(ValueError, match="frozen test"):
        backtest_outlook([window], 400, 200, repository=None)


def test_winter_window_spans_december_to_february():
    window = Window.winter(2026)
    assert (window.start, window.end) == (pd.Timestamp("2026-12-01"), pd.Timestamp("2027-02-28"))
