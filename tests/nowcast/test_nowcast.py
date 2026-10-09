"""Competition predictions: baselines, submission, outputs, serving, same-day guests."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from tourism_twin.config import SETTINGS
from tourism_twin.nowcast.baselines import SeasonalNaive
from tourism_twin.models.noise import NoiseModel
from synthetic import _daily


def test_seasonal_naive_uses_the_same_weekday_a_year_earlier():
    frame = _daily(np.log(np.arange(1, 801, dtype=float)))
    model = SeasonalNaive().fit(frame.iloc[:400])
    pred = model.predict(frame.iloc[400:800])
    np.testing.assert_allclose(pred.iloc[:364], frame["guests"].iloc[36:400].to_numpy())
    np.testing.assert_allclose(pred.iloc[364:], frame["guests"].iloc[36:72].to_numpy())


def test_prediction_validator_accepts_mirrored_files_and_flags_bad_ones():
    from tourism_twin.data.ingest import read_raw_workbook
    from tourism_twin.nowcast.predict import TestPredictions
    from tourism_twin.nowcast.submission import DOMESTIC_TEST_FILE, INTERNATIONAL_TEST_FILE, guest_floor, validate_predictions

    if not (SETTINGS.source_dir / INTERNATIONAL_TEST_FILE).exists():
        pytest.skip("raw test workbooks are supplied locally, not committed")
    domestic = read_raw_workbook(DOMESTIC_TEST_FILE)
    domestic = domestic.assign(Guests=guest_floor(domestic["New Arrivals"]).astype(float))
    international = read_raw_workbook(INTERNATIONAL_TEST_FILE)
    international = international.assign(Guests=guest_floor(international["New Arrivals"]).astype(float))
    keys = pd.concat([international[["Date", "Nationality"]], domestic[["Date"]].assign(Nationality=np.nan)], ignore_index=True)
    intervals = keys.assign(Guests_p10=9.0, Guests_p50=10.0, Guests_p90=11.0)
    good = TestPredictions(domestic, international, intervals, pd.DataFrame())
    assert validate_predictions(good) == []
    bad = TestPredictions(domestic.assign(Guests=np.inf), international.assign(Guests=international["Guests"] - 1, **{"New Arrivals": -5.0}),
                          intervals.assign(Guests_p10=12.0).iloc[1:], pd.DataFrame())
    problems = validate_predictions(bad)
    assert any("missing or infinite" in p for p in problems)
    assert any("Guests below max(New Arrivals, 10)" in p for p in problems)
    assert any("source values differ" in p for p in problems)
    assert any("rows or keys differ" in p for p in problems)
    assert any("p10 <= p50 <= p90" in p for p in problems)


def test_nowcast_service_answers_range_questions_from_the_bundle():
    from tourism_twin.nowcast.serving import DIRECTION_THRESHOLD, NowcastService

    test_days = pd.date_range("2025-08-01", periods=42, freq="D")
    pred = np.where(test_days < "2025-08-29", 100.0, 120.0)  # last 14 days are 20% higher
    history = pd.date_range("2025-07-01", periods=31, freq="D")
    bundle = {"spec": "s", "coverage": 0.8, "test_start": "2025-08-01", "test_end": "2025-09-11",
              "series": {"M": {"date": [str(d.date()) for d in test_days], "horizon_days": list(range(42)), "pred": pred.tolist()}},
              "history": {"M": {"date": [str(d.date()) for d in history], "guests": [103.0] * 31}},
              "noise": {"M": {"phi": 0.9, "sigma_eta": 0.02, "v0": 0.001}},
              "nationalities": {"A": {"date": ["2025-08-01"], "pred": [30.0]}, "B": {"date": ["2025-08-01"], "pred": [10.0]}}}
    service = NowcastService(bundle)
    first = service.range_total("M", "2025-08-01", "2025-08-07")  # previous range: actual July guests
    assert first["guests"] == 700.0 and first["previous_guests"] == 721.0 and first["direction"] == "no clear change"
    noise = service.noise
    assert (first["p10"], first["p90"]) == tuple(round(v, 1) for v in noise.range_interval("M", np.arange(7.0), np.full(7, 100.0)))
    last = service.range_total("M", "2025-08-29", "2025-09-11")  # previous range: predictions
    assert last["change"] == pytest.approx(0.2) and last["direction"] == "up" and DIRECTION_THRESHOLD == 0.08
    with pytest.raises(ValueError, match="predicted period"):
        service.range_total("M", "2025-07-20", "2025-08-03")
    assert [row["share"] for row in service.nationalities("2025-08-01", "2025-08-01")] == [0.75, 0.25]


def test_weekly_outputs_keep_full_weeks_and_give_a_direction_probability():
    from tourism_twin.nowcast.predict import total_series
    from tourism_twin.nowcast.weekly import weekly_forecast

    dates = pd.date_range("2025-08-04", periods=17, freq="D")  # two full Monday weeks + 3 days
    pred = np.where(dates < "2025-08-11", 100.0, 120.0)
    daily = pd.DataFrame({"market": "M", "date": dates, "horizon_days": np.arange(17), "pred": pred})
    persistent = NoiseModel(phi_={"M": 0.99}, sigma_eta_={"M": 0.01}, v0_={"M": 0.01})
    weekly = weekly_forecast(daily, persistent)
    assert list(weekly["week_start"].dt.strftime("%Y-%m-%d")) == ["2025-08-04", "2025-08-11"]
    assert weekly["forecast"].tolist() == [700.0, 840.0]
    assert weekly["direction"].iloc[0] == "increase" and weekly["direction"].iloc[1] is None
    assert (weekly["p10"].iloc[0], weekly["p90"].iloc[0]) == persistent.range_interval("M", np.arange(7.0), pred[:7])
    # Persistent errors cancel in the week-to-week difference, so the direction is surer than with
    # independent errors of the same daily size.
    independent = NoiseModel(phi_={"M": 0.0}, sigma_eta_={"M": 0.1}, v0_={"M": 0.01})
    assert weekly["direction_prob"].iloc[0] > weekly_forecast(daily, independent)["direction_prob"].iloc[0]
    total = total_series(pd.concat([daily, daily.assign(market="N", pred=daily["pred"] * 2)]))
    assert (total["market"] == "TOTAL").all() and total["pred"].tolist() == (daily["pred"] * 3).tolist()


def test_direction_backtest_scores_each_week_once_against_its_baselines():
    from tourism_twin.models.noise import NoiseModel
    from tourism_twin.nowcast.evaluation import direction_backtest

    dates = pd.date_range("2023-01-02", "2024-03-31", freq="D")  # starts on a Monday
    week = (dates - dates[0]).days // 7
    flipped = dates >= "2024-01-01"  # 2024 alternates in the opposite phase to 2023
    guests = np.where((week % 2 == 0) ^ flipped, 100.0, 200.0)
    history = pd.DataFrame({"market": "M", "date": dates, "guests": guests, "new_arrivals_filled": guests[::-1]})
    test = history[history["date"] >= "2024-01-01"]
    folds = [test.assign(fold=f"f{k}", origin=pd.Timestamp("2024-01-01") + np.timedelta64(7 * k, "D"))
             .query("date >= origin") for k in range(2)]  # overlapping folds
    predictions = pd.concat(folds, ignore_index=True).assign(
        actual=lambda f: f["guests"], pred=lambda f: f["guests"],
        horizon_days=lambda f: (f["date"] - f["origin"]).dt.days)
    noise = NoiseModel(phi_={"M": 0.5}, sigma_eta_={"M": 0.1}, v0_={"M": 0.01})
    result = direction_backtest(predictions, history, noise)
    assert result["weeks_scored"] == 12  # 13 full weeks, the last has no next week; overlap counted once
    accuracy = result["accuracy"]
    assert accuracy["model"] == 1.0
    assert accuracy["same_direction_as_last_year"] == 0.0  # a year back is the opposite phase
    assert accuracy["arrivals_direction"] < 1.0  # reversed arrivals mostly disagree
    assert 0.4 <= accuracy["majority_direction"] <= 0.6  # training alternates evenly
    assert result["weekly_band_coverage"] == 1.0


def test_same_day_model_recovers_a_weekday_effect_and_reads_suppressed_values_as_zero():
    from tourism_twin.nowcast.same_day import SameDayPoisson, poisson_deviance, same_day_target

    rng = np.random.default_rng(13)
    dates = pd.date_range("2023-01-02", periods=700, freq="D")
    arrivals = rng.uniform(800, 1200, len(dates))
    rate = np.exp(1.0 + 0.5 * (dates.dayofweek == 4) + 0.5 * np.log1p(arrivals))
    frame = pd.DataFrame({"market": "M", "date": dates, "same_day_guests": rng.poisson(rate).astype(float),
                          "n_same_day_suppressed": 0, "is_holiday_week": 0, "new_arrivals_filled": arrivals})
    model = SameDayPoisson().fit(frame)
    assert model.models_["M"].coef_[3] == pytest.approx(0.5, abs=0.05)  # design: Tue..Sun, holiday, log arrivals
    suppressed = pd.DataFrame({"same_day_guests": [5.0, np.nan, 3.0, np.nan], "n_same_day_suppressed": [0, 2, 1, 0]})
    target = same_day_target(suppressed)
    assert target.iloc[:3].tolist() == [5.0, 0.0, 3.0] and np.isnan(target.iloc[3])
    assert poisson_deviance([0.0, 4.0], [2.0, 2.0]) == pytest.approx((4.0 + 2 * (4 * np.log(2) - 2)) / 2)
