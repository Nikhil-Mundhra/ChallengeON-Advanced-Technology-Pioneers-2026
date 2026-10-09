"""Each model component recovers a known synthetic truth."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from tourism_twin.features import PANEL_FEATURES
from tourism_twin.models.components import AnnualFourier, ArrivalsConvolution, DayOfWeek, EventKernel, LinearRegressors, LinearTrend, LocalLevel, ResidualGBM
from tourism_twin.models.composite import AdditiveLogModel
from tourism_twin.models.fitters import Backfitting, JointLinear
from synthetic import _synthetic, _calendar, _daily, _conv_frame, _calendar_conv_frame


def test_annual_fourier_recovers_a_known_sine():
    days = pd.date_range("2022-01-01", periods=1095, freq="D").dayofyear.to_numpy()
    frame = _daily(8.0 + 0.3 * np.sin(2 * np.pi * days / 365.25))
    fitted = AdditiveLogModel([LinearTrend(), AnnualFourier(4)], fitter=JointLinear()).fit(frame).explain()["M"]["season"]
    assert fitted["amplitude_log_by_harmonic"][1] == pytest.approx(0.3, abs=1e-3)
    assert fitted["amplitude_log_by_harmonic"][2] == pytest.approx(0.0, abs=1e-3)


def test_day_of_week_recovers_known_weekday_effects():
    dates = pd.date_range("2023-01-02", periods=728, freq="D")
    effect = np.select([dates.dayofweek == 4, dates.dayofweek == 5], [0.2, 0.3], 0.0)
    fitted = AdditiveLogModel([LinearTrend(), DayOfWeek()], fitter=JointLinear()).fit(_daily(7.0 + effect, "2023-01-02")).explain()["M"]["weekday"]
    assert fitted["effect_log_vs_monday"]["Fri"] == pytest.approx(0.2, abs=1e-9)
    assert fitted["effect_log_vs_monday"]["Sat"] == pytest.approx(0.3, abs=1e-9)
    assert fitted["effect_log_vs_monday"]["Tue"] == pytest.approx(0.0, abs=1e-9)


def test_level_and_slope_extrapolate_flat_by_default():
    t = np.arange(900)
    level = 8.0 + 0.4 * np.sin(2 * np.pi * t / 700) + 0.0004 * t
    frame = _daily(level + np.random.default_rng(3).normal(0, 0.03, len(t)))
    flat = AdditiveLogModel([LocalLevel(smoothing=1e4)], fitter=JointLinear()).fit(frame.iloc[:800])
    assert np.abs(flat.decompose(frame.iloc[:800])["level"] - level[:800]).mean() < 0.02
    ahead = flat.decompose(frame.iloc[800:830])["level"].to_numpy()
    assert np.ptp(ahead) == 0.0
    sloped = AdditiveLogModel([LocalLevel(smoothing=1e4, extrapolate_slope=True)], fitter=JointLinear()).fit(frame.iloc[:800])
    true_slope = 0.4 * 2 * np.pi / 700 * np.cos(2 * np.pi * 799 / 700) + 0.0004  # derivative at the last day
    assert sloped.explain()["M"]["level"]["slope_log_per_day"] == pytest.approx(true_slope, rel=0.5)
    np.testing.assert_allclose(np.diff(sloped.decompose(frame.iloc[800:830])["level"]), sloped.explain()["M"]["level"]["slope_log_per_day"], atol=1e-12)
    # The centred slope, by default, stops at the last training day (damping_days=None keeps it linear).
    from tourism_twin.models.components import CentredSlope

    trended = _daily(8.0 + 0.2 * np.arange(900) / 365.25)
    for damping, expect_flat in ((0.0, True), (None, False)):
        model = AdditiveLogModel([LinearTrend(), CentredSlope(damping_days=damping)], fitter=JointLinear()).fit(trended.iloc[:800])
        ahead = model.decompose(trended.iloc[800:])["slope"].to_numpy()
        assert (np.ptp(ahead) == 0.0) == expect_flat


def test_event_kernel_recovers_a_known_bump():
    true_kernel = {-1: 0.1, 0: 0.4, 1: 0.6, 2: 0.3, 3: 0.1}
    calendar = _calendar("fest", ["2023-04-10", "2024-04-10"], -1, 3)
    frame = _synthetic(season=0.0, event=0.0, noise=0.005)
    for anchor in calendar["anchor_date"]:
        for k, effect in true_kernel.items():
            frame.loc[frame["date"] == anchor + np.timedelta64(k, "D"), "guests"] *= np.exp(effect)
    model = AdditiveLogModel([LinearTrend(), EventKernel(["fest"], smoothing=0.01, calendar=calendar)], fitter=JointLinear()).fit(frame)
    fitted = model.explain()["M"]["events"]["effect_pct_by_day_offset"]["fest"]
    for k, effect in true_kernel.items():
        assert np.log1p(fitted[k]) == pytest.approx(effect, abs=0.02), k
    contributions = model.decompose(frame)["events"]
    outside = ~frame["date"].isin([a + np.timedelta64(k, "D") for a in calendar["anchor_date"] for k in true_kernel])
    assert (contributions[outside] == 0).all()  # zero baseline: an event contributes nothing outside its windows
    # A market-scoped event (e.g. Chinese New Year for CHINA) is zero for every other market.
    scoped = EventKernel(["fest"], calendar=_calendar("fest", ["2023-04-10", "2024-04-10"], -1, 3, scope="M"))
    other = frame.assign(market="OTHER")
    pooled = pd.concat([frame, other], ignore_index=True)
    design = scoped.design(pooled)
    assert design.iloc[len(frame):].to_numpy().sum() == 0 and design.iloc[:len(frame)].to_numpy().sum() == 10
    # A nationality-scoped event (MOROCCO inside a pooled market) covers that nationality's rows only,
    # and nothing on a market-grain panel, which has no nationality column.
    morocco = EventKernel(["fest"], calendar=_calendar("fest", ["2023-04-10", "2024-04-10"], -1, 3, scope="MOROCCO"))
    rows = pd.concat([frame.assign(market="OTHER_AMERICAS_AFRICA", nationality=n) for n in ("MOROCCO", "BRAZIL")], ignore_index=True)
    covered = morocco.design(rows).to_numpy().sum(axis=1) > 0
    assert covered[: len(frame)].sum() == 10 and not covered[len(frame):].any()
    assert morocco.design(frame.assign(market="OTHER_AMERICAS_AFRICA")).to_numpy().sum() == 0


def test_event_kernel_penalty_never_couples_two_events():
    kernel = EventKernel(["ramadan", "eid_al_fitr", "christmas_new_year"])
    rows = kernel.penalty_rows()
    blocks = np.cumsum([0] + [len(kernel.offsets[e]) for e in kernel.events])
    for row in rows:
        nonzero = np.flatnonzero(row)
        assert np.searchsorted(blocks, nonzero.min(), side="right") == np.searchsorted(blocks, nonzero.max(), side="right")
    short = EventKernel(["national_day"])  # 4-day window: unpenalised so its peak is not flattened
    assert short.penalty_rows() is None


def test_season_and_event_kernels_are_identifiable():
    dates = pd.date_range("2022-01-01", periods=1095, freq="D")
    calendar = _calendar("fest", ["2022-06-01", "2023-05-20", "2024-05-08"], -1, 2)
    season = 0.3 * np.sin(2 * np.pi * dates.dayofyear.to_numpy() / 365.25)
    offsets = {a + np.timedelta64(k, "D"): e for a in calendar["anchor_date"] for k, e in zip(range(-1, 3), (0.2, 0.5, 0.4, 0.1))}
    event = np.array([offsets.get(d, 0.0) for d in dates])
    frame = _daily(8.0 + season + event + np.random.default_rng(9).normal(0, 0.01, len(dates)), "2022-01-01")
    model = AdditiveLogModel([LinearTrend(), AnnualFourier(4), EventKernel(["fest"], calendar=calendar)], fitter=Backfitting()).fit(frame)
    parts = model.decompose(frame)
    assert (parts["events"] - event).abs().max() < 0.03
    assert (parts["season"] - (season - season.mean())).abs().max() < 0.03


def test_arrivals_convolution_recovers_a_known_survival_kernel():
    rng = np.random.default_rng(5)
    n, max_lag = 900, 21
    arrivals = 1000 * np.exp(0.3 * np.sin(2 * np.pi * np.arange(n) / 365.25) + rng.normal(0, 0.15, n))
    true_w = np.exp(-np.arange(max_lag + 1) / 3.0)
    lags = np.column_stack([np.r_[np.full(k, np.nan), arrivals[:n - k]] for k in range(max_lag + 1)])
    guests = 500.0 + np.nan_to_num(lags) @ true_w
    frame = _daily(np.log(guests), new_arrivals_filled=arrivals)
    frame = PANEL_FEATURES.apply(frame, ["arrival_lags"], max_lag=max_lag)
    model = AdditiveLogModel([ArrivalsConvolution(max_lag=max_lag)], fitter=Backfitting(), include_flag="lag_complete").fit(frame)
    fitted = model.explain()["M"]["arrivals"]
    np.testing.assert_allclose(fitted["survival_w"], true_w, atol=0.01)
    assert sum(fitted["survival_w"]) == pytest.approx(true_w.sum(), rel=0.01)
    assert all(a >= b - 1e-12 for a, b in zip(fitted["survival_w"], fitted["survival_w"][1:])) and fitted["w0"] <= 1 + 1e-9


def test_arrivals_kernel_log_gradient_matches_finite_differences():
    from tourism_twin.models.components.arrivals_conv import log_gradient, log_objective

    rng = np.random.default_rng(2)
    design, penalty = rng.uniform(1, 50, (200, 6)), 0.1 * rng.normal(size=(3, 6))
    z, p = np.log(rng.uniform(100, 400, 200)), rng.uniform(0.5, 2.0, 6)
    for weights in (None, rng.uniform(0.2, 3.0, 200)):  # unweighted and with training weights
        extra = () if weights is None else (weights,)
        numeric = np.array([(log_objective(p + h, design, penalty, z, 1e-9, *extra) - log_objective(p - h, design, penalty, z, 1e-9, *extra)) / 2e-6
                            for h in 1e-6 * np.eye(6)])
        np.testing.assert_allclose(log_gradient(p, design, penalty, z, 1e-9, *extra), numeric, rtol=1e-5)


def test_arrivals_kernel_beats_its_raw_scale_warm_start_on_the_log_objective():
    from scipy.optimize import lsq_linear

    frame = _calendar_conv_frame(noise=0.3)
    model = AdditiveLogModel([ArrivalsConvolution(max_lag=7, base_smoothing=0.0)], fitter=Backfitting(), include_flag="lag_complete").fit(frame)
    rows = frame[frame["lag_complete"]]
    component = model.fitted_["M"][0][0]
    lags = rows[component.lag_columns].to_numpy()
    design = np.hstack([lags @ np.triu(np.ones((8, 8))), component._base(rows["date"])])
    raw = lsq_linear(design, rows["guests"].to_numpy(), bounds=(0, np.inf)).x
    raw[:8] /= max(1.0, raw[:8].sum())  # the raw fit, made feasible
    log_sse = lambda flow: float(np.sum((np.log(rows["guests"].to_numpy()) - np.log(flow)) ** 2))  # noqa: E731
    assert log_sse(component._flow(rows)) < 0.99 * log_sse(design @ raw)


def test_arrivals_convolution_keeps_its_constraints():
    true_w = 1.3 * np.exp(-np.arange(8) / 2.0)  # data generated with w0 = 1.3: an unconstrained fit lands above 1
    model = AdditiveLogModel([ArrivalsConvolution(max_lag=7)], fitter=Backfitting(), include_flag="lag_complete").fit(_conv_frame(true_w, base=0.0, noise=0.02))
    fitted = model.explain()["M"]["arrivals"]
    assert fitted["w0"] <= 1.0 + 1e-12
    assert all(a >= b - 1e-12 for a, b in zip(fitted["survival_w"], fitted["survival_w"][1:]))
    # The knot base stock is flat beyond the training days.
    frame = _conv_frame(np.exp(-np.arange(8) / 3.0), base=300.0, noise=0.0)
    model = AdditiveLogModel([ArrivalsConvolution(max_lag=7)], fitter=Backfitting(), include_flag="lag_complete").fit(frame.iloc[:600])
    component = model.fitted_["M"][0][0]
    base = component._base(frame.iloc[600:]["date"]) @ component.c_
    assert np.ptp(base) == 0.0 and base[0] == pytest.approx(list(model.explain()["M"]["arrivals"]["base_stock_by_knot"].values())[-1])


def test_an_arrivals_proportional_base_stock_follows_an_arrival_shock():
    # A carrier exit halves arrivals (Wizz Air, Sep 2025): with c_t = rho * mean arrivals over 90 days
    # the whole stock scales with arrivals; a base stock fixed in time does not.
    rng = np.random.default_rng(4)
    n, true_w = 1000, np.exp(-np.arange(8) / 3.0)
    arrivals = 1000 * np.exp(rng.normal(0, 0.1, n))
    mean_90 = pd.Series(arrivals).rolling(90, min_periods=1).mean().to_numpy()
    lags = np.column_stack([np.r_[np.full(k, np.nan), arrivals[:n - k]] for k in range(8)])
    frame = _daily(np.log(0.5 * mean_90 + np.nan_to_num(lags) @ true_w), new_arrivals_filled=arrivals)
    frame = PANEL_FEATURES.apply(frame, ["arrival_lags", "arrivals_mean_90"], max_lag=7)
    shocked = frame.assign(new_arrivals_filled=np.where(np.arange(n) >= 800, 0.55, 1.0) * arrivals)
    shocked = PANEL_FEATURES.apply(shocked.drop(columns=[c for c in frame.columns if c.startswith("arrivals_") or c == "lag_complete"]),
                                   ["arrival_lags", "arrivals_mean_90"], max_lag=7)
    late = slice(900, n)  # beyond the 90-day window after the shock
    for base, follows in (("arrivals", True), ("knots", False)):
        model = AdditiveLogModel([ArrivalsConvolution(max_lag=7, base=base)], fitter=Backfitting(), include_flag="lag_complete").fit(frame.iloc[:800])
        ratio = (model.predict(shocked.iloc[late]) / model.predict(frame.iloc[late])).to_numpy()
        assert (np.abs(ratio - 0.55) < 0.01).all() == follows, base


def test_group_scale_recovers_each_series_scale_in_a_pooled_fit():
    from tourism_twin.models.components import GroupScale

    rng = np.random.default_rng(8)
    frames = [_daily(7.0 + scale + 0.3 * np.sin(2 * np.pi * np.arange(700) / 365.25) + rng.normal(0, 0.02, 700), sin=np.sin(2 * np.pi * np.arange(700) / 365.25))
              .assign(nationality=name) for name, scale in (("A", 0.0), ("B", 0.7), ("C", -0.4))]
    pooled = pd.concat(frames, ignore_index=True).assign(family="F")
    model = AdditiveLogModel([LinearTrend(), GroupScale(ridge=1e-6), LinearRegressors(["sin"], name="season")],
                             fitter=JointLinear(), group_by="family").fit(pooled)
    scales = model.explain()["F"]["group_scale"]["scale_log"]
    assert scales["B"] - scales["A"] == pytest.approx(0.7, abs=0.01) and scales["C"] - scales["A"] == pytest.approx(-0.4, abs=0.01)
    assert model.explain()["F"]["season"]["coef"]["sin"] == pytest.approx(0.3, abs=0.01)  # one shared shape
    unseen = model.decompose(frames[0].assign(nationality="Z", family="F"))["group_scale"]
    assert np.allclose(unseen, unseen.iloc[0])  # an unseen series gets the shared level
    shrunk = AdditiveLogModel([LinearTrend(), GroupScale(ridge=1e6), LinearRegressors(["sin"], name="season")],
                              fitter=JointLinear(), group_by="family").fit(pooled)
    assert np.ptp(list(shrunk.explain()["F"]["group_scale"]["scale_log"].values())) < 0.05  # a large ridge pools the scales


def test_residual_gbm_picks_up_a_structure_the_other_parts_miss():
    rng = np.random.default_rng(7)
    flag = (rng.random(800) > 0.5).astype(float)
    frame = _daily(7.0 + 0.25 * flag + rng.normal(0, 0.01, 800), signal=flag)
    model = AdditiveLogModel([LinearTrend(), ResidualGBM(["signal"])], fitter=Backfitting()).fit(frame)
    gbm = model.decompose(frame)["gbm"]
    assert gbm[flag == 1].mean() - gbm[flag == 0].mean() == pytest.approx(0.25, abs=0.02)
