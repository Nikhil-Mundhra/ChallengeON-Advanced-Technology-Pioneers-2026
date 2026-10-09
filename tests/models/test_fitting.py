"""Composite model, fitters, row rules and training weights."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from tourism_twin.models.components import AnnualFourier, ArrivalsConvolution, DayOfWeek, EventKernel, LinearRegressors, LinearTrend, ResidualGBM
from tourism_twin.models.composite import AdditiveLogModel
from tourism_twin.models.fitters import Backfitting, JointLinear
from synthetic import _synthetic, _components, _conv_frame


def test_joint_linear_recovers_known_coefficients_in_and_out_of_sample():
    frame = _synthetic(noise=0.0)
    model = AdditiveLogModel(_components(), fitter=JointLinear()).fit(frame.iloc[:500])
    fitted = model.explain()["M"]
    assert fitted["trend"]["slope_per_year"] == pytest.approx(0.05, abs=1e-9)
    assert fitted["season"]["coef"]["sin"] == pytest.approx(0.3, abs=1e-9)
    assert fitted["event"]["coef"]["bump"] == pytest.approx(0.5, abs=1e-9)
    np.testing.assert_allclose(model.predict(frame), frame["guests"], rtol=1e-9)  # fit state carries out of sample
    np.testing.assert_allclose(model.predict(frame.iloc[[600]]), frame["guests"].iloc[[600]], rtol=1e-9)  # and to one row


def test_backfitting_matches_the_joint_solution_and_parts_are_identifiable_and_centred():
    frame = _synthetic(noise=0.02)
    joint = AdditiveLogModel(_components(), fitter=JointLinear()).fit(frame)
    cycled = AdditiveLogModel(_components(), fitter=Backfitting(joint_linear=False, tol=1e-12, max_iter=500)).fit(frame)
    report = cycled.fitted_["M"][1]
    assert report.converged and report.iterations > 1
    parts = cycled.decompose(frame)
    np.testing.assert_allclose(parts, joint.decompose(frame), atol=1e-9)
    assert (parts["season"] - 0.3 * (frame["sin"] - frame["sin"].mean())).abs().max() < 0.01
    assert (parts["event"] - 0.5 * (frame["bump"] - frame["bump"].mean())).abs().max() < 0.01
    assert abs(parts["season"].mean()) < 1e-12 and abs(parts["event"].mean()) < 1e-12  # only the trend owns the level


def test_composite_fits_each_market_separately_and_resolves_registered_features():
    frame = pd.concat([_synthetic(level=8.0, season=0.3, event=0.0, market="A"), _synthetic(level=6.0, season=-0.2, event=0.0, market="B", seed=1)], ignore_index=True)
    model = AdditiveLogModel([LinearTrend(), LinearRegressors(["sin"], name="season"), LinearRegressors(["month"], name="month")]).fit(frame)
    assert model.explain()["A"]["season"]["coef"]["sin"] == pytest.approx(0.3, abs=0.02)
    assert model.explain()["B"]["season"]["coef"]["sin"] == pytest.approx(-0.2, abs=0.02)
    np.testing.assert_allclose(np.log(model.predict(frame)), model.decompose(frame).sum(axis=1))
    blocks = model.decompose_by_group(frame)  # trend -> time; the two regressors -> flight
    assert list(blocks.columns) == ["time", "flight"]
    np.testing.assert_allclose(blocks.sum(axis=1), model.decompose(frame).sum(axis=1))
    with pytest.raises(KeyError, match="No fitted model"):
        model.predict(frame.assign(market="C"))


def test_composite_rejects_inputs_that_would_give_silent_nonsense():
    frame = _synthetic()
    model = AdditiveLogModel(_components(), fitter=JointLinear())
    with pytest.raises(ValueError, match="<= 0"):
        model.fit(frame.assign(guests=frame["guests"].where(frame.index != 3, 0.0)))
    with pytest.raises(ValueError, match="non-finite values in design columns"):
        model.fit(frame.assign(sin=frame["sin"].where(frame.index != 3, np.nan)))
    with pytest.raises(ValueError, match="index must be unique"):
        model.fit(pd.concat([frame, frame]))
    with pytest.raises(ValueError, match="own the level"):  # two level owners would split the level arbitrarily
        AdditiveLogModel([LinearTrend(), LinearTrend(name="trend2")])
    with pytest.raises(ValueError, match="unique"):  # contributions are keyed by name
        AdditiveLogModel([LinearTrend(), LinearRegressors(["sin"], name="trend")])
    with pytest.raises(TypeError, match="Use Backfitting"):  # a joint least squares cannot fit a non-linear part
        AdditiveLogModel([LinearTrend(), ResidualGBM(["sin"])], fitter=JointLinear()).fit(frame)


def test_fit_report_flags_overlapping_and_unidentified_columns():
    frame = _synthetic().assign(sin_copy=lambda f: f["sin"], never=0.0)
    overlap = AdditiveLogModel([LinearTrend(), LinearRegressors(["sin"], name="a"), LinearRegressors(["sin_copy"], name="b")], fitter=JointLinear()).fit(frame)
    assert overlap.explain()["M"]["fit"]["rank_deficient"]
    constant = AdditiveLogModel([LinearTrend(), LinearRegressors(["never"], name="ghost")], fitter=JointLinear()).fit(frame)
    assert constant.explain()["M"]["ghost"]["unidentified"] == ["never"]


def test_trend_origin_is_shared_across_markets_and_smearing_corrects_the_mean():
    early, late = _synthetic(market="A", noise=0.5), _synthetic(market="B", noise=0.5, seed=1).iloc[200:]
    model = AdditiveLogModel(_components(), fitter=JointLinear(), bias_correction="smearing").fit(pd.concat([early, late], ignore_index=True))
    assert model.explain()["A"]["trend"]["origin"] == model.explain()["B"]["trend"]["origin"] == "2023-01-01"
    assert model.smearing_["A"] == pytest.approx(np.exp(0.5 ** 2 / 2), rel=0.03)  # 1.13; no correction would be 1.0


def test_backfitting_with_the_arrivals_kernel_never_increases_the_objective(kernel_frame):
    # Every block, the kernel included, must minimise the same penalised log-scale objective; a
    # kernel fitted on the raw scale made it cycle and the domestic fit depend on the pass cap (#13).
    # With training weights the weighted penalised objective must descend the same way.
    from tourism_twin.models.weighting import ByColumn

    kernel_frame["half"] = np.where(np.arange(len(kernel_frame)) < len(kernel_frame) // 2, "early", "late")
    for weighting in (None, ByColumn("half", {"late": 4.0})):
        components = [ArrivalsConvolution(max_lag=7), AnnualFourier(2), DayOfWeek(), EventKernel()]
        model = AdditiveLogModel(components, fitter=Backfitting(max_iter=40, tol=0.0), include_flag="lag_complete",
                                 weighting=weighting).fit(kernel_frame)
        objective = model.fitted_["M"][1].objective
        assert len(objective) == 40
        assert all(later <= earlier * (1 + 1e-10) for earlier, later in zip(objective, objective[1:])), weighting


def test_row_rules_match_the_flag_shorthands(kernel_frame):
    from tourism_twin.models.handler import DataHandler, flagged, not_flagged

    frame = kernel_frame
    frame["is_one_off_period"] = (np.arange(len(frame)) % 50 == 0).astype(int)
    shorthand = AdditiveLogModel([LinearTrend()], exclude_flag="is_one_off_period", include_flag="lag_complete").handler
    rules = DataHandler(rules=[not_flagged("is_one_off_period"), flagged("lag_complete")])
    kept = rules.training_rows(frame).index
    assert shorthand.training_rows(frame).index.equals(kept)
    assert not frame.loc[kept, "is_one_off_period"].any() and frame.loc[kept, "lag_complete"].all()


def test_uniform_or_constant_weights_reproduce_the_unweighted_fit(kernel_frame):
    from tourism_twin.models.weighting import ByColumn, Uniform

    frame = kernel_frame

    def predict(weighting):
        components = [ArrivalsConvolution(max_lag=7), AnnualFourier(2), DayOfWeek()]
        model = AdditiveLogModel(components, fitter=Backfitting(), include_flag="lag_complete", weighting=weighting)
        return model.fit(frame).predict(frame[frame["lag_complete"].astype(bool)]).to_numpy()

    unweighted = predict(None)
    np.testing.assert_allclose(predict(Uniform()), unweighted, rtol=1e-9)
    np.testing.assert_allclose(predict(ByColumn("market", {"M": 3.0})), unweighted, rtol=1e-9)  # w and 3w fit alike


def test_recency_weighting_follows_a_recent_regime():
    from tourism_twin.models.weighting import Product, Recency, Uniform

    rng = np.random.default_rng(3)
    dates = pd.date_range("2023-01-01", periods=730, freq="D")
    x = rng.uniform(1.0, 2.0, len(dates))
    effect = np.where(np.arange(len(dates)) < 365, 1.0, 2.0)  # the relation doubles in year two
    frame = pd.DataFrame({"market": "M", "date": dates, "x": x, "guests": np.exp(5.0 + effect * x)})

    def coef(weighting):
        model = AdditiveLogModel([LinearTrend(), LinearRegressors(["x"])], fitter=JointLinear(), weighting=weighting)
        return model.fit(frame).explain()["M"]["regressors"]["coef"]["x"]

    assert coef(None) == pytest.approx(1.5, abs=0.1)
    assert coef(Recency(half_life_days=30)) > 1.9
    weights = Product(Recency(90), Uniform()).weights(frame)
    assert weights.mean() == pytest.approx(1.0) and weights.iloc[-1] > weights.iloc[0]


def test_weighted_kernel_follows_the_favoured_regime():
    from tourism_twin.models.weighting import ByColumn

    early, late = 1.0 * np.exp(-np.arange(8) / 1.5), 1.0 * np.exp(-np.arange(8) / 4.0)  # stays lengthen
    halves = [_conv_frame(true_w, base=50.0, noise=0.01, n=600, seed=s) for true_w, s in ((early, 1), (late, 2))]
    frame = pd.concat(halves, ignore_index=True)
    frame["date"] = pd.date_range("2022-01-01", periods=len(frame), freq="D")
    frame["regime"] = np.repeat(["early", "late"], 600)

    def kernel_sum(weighting):
        model = AdditiveLogModel([ArrivalsConvolution(max_lag=7)], fitter=Backfitting(), include_flag="lag_complete",
                                 weighting=weighting).fit(frame)
        return sum(model.explain()["M"]["arrivals"]["survival_w"])

    unweighted, favour_late = kernel_sum(None), kernel_sum(ByColumn("regime", {"late": 50.0}))
    assert early.sum() < unweighted < late.sum()
    assert abs(favour_late - late.sum()) < abs(unweighted - late.sum()) / 3
