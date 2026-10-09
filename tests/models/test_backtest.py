"""Back-test harness (leakage, segments, the #11 protocol) and the noise model."""

from __future__ import annotations

import json
import numpy as np
import pandas as pd
import pytest
from scipy.stats import norm
from tourism_twin.config import SETTINGS
from tourism_twin.models.backtest import RollingOrigin, backtest
from tourism_twin.planning.evaluation import evaluate
from tourism_twin.models.noise import NoiseModel, held_out_coverage
from synthetic import _synthetic, _ar1_backtest, _LastTrainDate


def test_benchmarks_through_the_harness_reproduce_the_committed_evaluation():
    from tourism_twin.nowcast.specs import DAILY_SPECS
    from tourism_twin.planning.specs import DIAGNOSTIC_SPECS, WEEKLY_SPECS

    assert evaluate() == json.loads(SETTINGS.evaluation_results_path.read_text())
    assert not set(DIAGNOSTIC_SPECS) & (set(WEEKLY_SPECS) | set(DAILY_SPECS))  # oracle diagnostics are never ranked


def test_rolling_origin_never_trains_on_the_future_and_scores_segments():
    frame = pd.concat([_synthetic(market="DOMESTIC"), _synthetic(market="UNITED KINGDOM", level=6.0, seed=1)], ignore_index=True)
    _LastTrainDate.seen = []
    result = backtest({"mean": _LastTrainDate}, frame, RollingOrigin("2024-03-01", "2024-05-01", horizon_months=2))
    folds = result.predictions.groupby("fold")["date"].agg(["min", "max"])
    assert list(folds.index) == ["origin_2024-03-01", "origin_2024-04-01", "origin_2024-05-01"]
    for last_train, (fold, row) in zip(_LastTrainDate.seen, folds.iterrows()):
        assert last_train < row["min"] == pd.Timestamp(fold.removeprefix("origin_"))
        assert row["max"] == row["min"] + pd.DateOffset(months=2) - np.timedelta64(1, "D")
    _LastTrainDate.seen = []  # the protocol's gap: training ends 21 days before each origin
    backtest({"mean": _LastTrainDate}, frame, RollingOrigin("2024-03-01", "2024-03-01", horizon_months=1, gap_days=21))
    assert _LastTrainDate.seen[0] < pd.Timestamp("2024-03-01") - np.timedelta64(20, "D")
    first = result.metrics[result.metrics["fold"] == "origin_2024-03-01"].set_index("segment")
    domestic = result.predictions[(result.predictions["fold"] == "origin_2024-03-01") & (result.predictions["market"] == "DOMESTIC")]
    assert first.loc["domestic", "n"] == first.loc["international", "n"] == len(domestic)
    assert first.loc["domestic", "mae"] == pytest.approx((domestic["actual"] - domestic["pred"]).abs().mean())


def test_weekly_rows_straddling_an_origin_never_train():
    weeks = pd.date_range("2024-01-01", periods=60, freq="W-MON")
    frame = pd.DataFrame({"market": "UNITED KINGDOM", "date": weeks, "guests": 100.0})
    _LastTrainDate.seen = []
    backtest({"mean": _LastTrainDate}, frame, RollingOrigin("2024-10-01", "2024-10-01", horizon_months=1), period_days=7)
    assert _LastTrainDate.seen[0] + np.timedelta64(6, "D") < pd.Timestamp("2024-10-01")  # week of 2024-09-30 excluded


class _BadIndex(_LastTrainDate):
    def predict(self, panel):
        return pd.Series(self.mean, index=range(len(panel)))


class _Gaps(_LastTrainDate):
    def predict(self, panel):
        return pd.Series(np.nan, index=panel.index)


def test_block_bootstrap_compare_detects_a_real_difference_and_not_a_null_one():
    from tourism_twin.models.backtest import compare

    rng = np.random.default_rng(3)
    dates = np.tile(pd.date_range("2024-01-01", periods=180, freq="D"), 3)
    folds = np.repeat(["f1", "f2", "f3"], 180)
    actual = 1000 * np.exp(rng.normal(0, 0.05, len(dates)))
    error = rng.normal(0, 0.10, len(dates))
    frame = lambda model, scale: pd.DataFrame({"fold": folds, "row": np.arange(len(dates)), "model": model, "date": dates,  # noqa: E731
                                               "actual": actual, "pred": actual * np.exp(scale * error)})
    predictions = pd.concat([frame("base", 1.0), frame("better", 0.5), frame("same", 1.0)], ignore_index=True)
    better = compare(predictions, "base", "better")
    assert better["difference_pp"] < 0 and better["ci_high"] < 0 and better["share_folds_same_sign"] == 1.0
    same = compare(predictions, "base", "same")
    assert same["difference_pp"] == 0 and same["ci_low"] <= 0 <= same["ci_high"]


def test_harness_rejects_misindexed_or_missing_predictions_and_reports_skipped_folds():
    frame = _synthetic()
    with pytest.raises(ValueError, match="indexed like the test rows"):
        backtest({"bad": _BadIndex}, frame, RollingOrigin("2024-03-01", "2024-03-01", 1))
    with pytest.raises(ValueError, match="missing predictions"):
        backtest({"gaps": _Gaps}, frame, RollingOrigin("2024-03-01", "2024-03-01", 1))
    with pytest.warns(UserWarning, match="Skipped folds"):
        result = backtest({"mean": _LastTrainDate}, frame, RollingOrigin("2022-11-01", "2023-02-01", 1))
    assert result.skipped == ["origin_2022-11-01", "origin_2022-12-01", "origin_2023-01-01"]
    with pytest.raises(ValueError, match="No fold"):
        backtest({"mean": _LastTrainDate}, frame, RollingOrigin("2030-01-01", "2030-01-01", 1))


def test_noise_model_recovers_ar1_errors_and_widens_with_the_horizon():
    model = NoiseModel().fit(_ar1_backtest(phi=0.8, sigma=0.05))
    phi, sigma, v0 = model.phi_["UNITED KINGDOM"], model.sigma_eta_["UNITED KINGDOM"], model.v0_["UNITED KINGDOM"]
    assert phi == pytest.approx(0.8, abs=0.03) and sigma == pytest.approx(0.05, abs=0.003)
    assert v0 == pytest.approx(0.05 ** 2, rel=0.3)  # e_0 = eta_0
    horizon = pd.Series([0, 5, 60])
    expected = v0 * phi ** (2 * horizon) + sigma ** 2 * (1 - phi ** (2 * horizon)) / (1 - phi ** 2)
    np.testing.assert_allclose(model.variance(pd.Series(["UNITED KINGDOM"] * 3), horizon), expected, rtol=1e-12)
    frame = pd.DataFrame({"market": "UNITED KINGDOM", "horizon_days": horizon, "pred": 1000.0})
    width = (model.intervals(frame)["upper"] / frame["pred"]).to_numpy()
    assert width[0] < width[1] < width[2] and width[2] == pytest.approx(width[1], rel=0.1)
    with pytest.raises(ValueError, match="non-positive or non-finite"):
        NoiseModel().fit(_ar1_backtest(0.8, 0.05).assign(actual=0.0))
    # A range total (e.g. 14 days) uses the AR(1) covariance: wider than one day's relative band,
    # narrower than adding the daily bounds (which assumes perfectly correlated days).
    days = np.arange(30.0, 44.0)
    covariance = model.covariance("UNITED KINGDOM", days)
    lower, upper = model.range_interval("UNITED KINGDOM", days, np.full(14, 1000.0))
    z = norm.ppf(0.9)
    assert np.log(upper / 14000) == pytest.approx(z * np.sqrt(covariance.mean()))  # equal weights 1/14
    daily = model.intervals(pd.DataFrame({"market": "UNITED KINGDOM", "horizon_days": days, "pred": 1000.0}))
    assert upper - 14000 < daily["upper"].sum() - 14000


def test_held_out_coverage_is_close_to_nominal_and_ignores_the_held_out_fold():
    coverage = held_out_coverage(_ar1_backtest(phi=0.8, sigma=0.05), coverage=0.8, exclude_months=3)
    assert np.average(coverage["covered"], weights=coverage["n"]) == pytest.approx(0.8, abs=0.04)
    noisy = held_out_coverage(_ar1_backtest(phi=0.8, sigma=0.05, scale={20: 5.0}), coverage=0.8)
    assert noisy.set_index("fold").loc["origin_20", "covered"] < 0.5  # its own large errors did not widen its bounds
