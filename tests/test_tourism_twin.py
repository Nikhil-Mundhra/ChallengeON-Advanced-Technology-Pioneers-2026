"""Product test suite, in pipeline order: domain -> lake -> panels -> simulator -> API."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from tourism_twin.config import SETTINGS
from tourism_twin.data.panel import build_weekly_panel
from tourism_twin.features import PANEL_FEATURES, FeatureRegistry, FeatureSpec, Kind
from tourism_twin.domain.events import DEFAULT_KERNEL_EVENTS, load_event_calendar
from tourism_twin.features.events import offset_column
from tourism_twin.nowcast.baselines import SeasonalNaive
from tourism_twin.models.components import (
    AnnualFourier, ArrivalsConvolution, DayOfWeek, EventKernel, LinearRegressors, LinearTrend, LocalLevel, ResidualGBM,
)
from tourism_twin.models.backtest import RollingOrigin, backtest
from tourism_twin.models.composite import AdditiveLogModel
from tourism_twin.planning.evaluation import evaluate
from tourism_twin.models.noise import NoiseModel, held_out_coverage
from tourism_twin.models.fitters import Backfitting, JointLinear
from tourism_twin.features.lags import DEFAULT_MAX_LAG, lag_column
from tourism_twin.domain.markets import REGIONAL_CLUSTERS, TOP_15_INTERNATIONAL_MARKETS
from tourism_twin.domain.scenario import ScenarioLever
from tourism_twin.domain.seasons import SEASONS, assign_season

EXPECTED_MARKETS = {*TOP_15_INTERNATIONAL_MARKETS, *REGIONAL_CLUSTERS, "DOMESTIC"}
WATERFALL_PARTS = ("waterfall_seats", "waterfall_lf", "waterfall_p2p", "waterfall_multiplier", "waterfall_los")


def waterfall_total(result) -> float:
    return sum(getattr(result, part) for part in WATERFALL_PARTS)


# --- domain ---------------------------------------------------------------------------------

# --- lake -----------------------------------------------------------------------------------

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


# --- feature registry ---------------------------------------------------------------------

def _toy_registry() -> FeatureRegistry:
    registry = FeatureRegistry()
    registry.register(FeatureSpec("ratio", Kind.RATIO, ("a", "b"), lambda f, **_: f["a"] / f["b"]))
    registry.register(FeatureSpec("ratio_flag", Kind.FLAG, ("ratio",), lambda f, **_: (f["ratio"] > 1).astype(int)))
    return registry


def test_registry_resolves_dependencies_once_and_rejects_bad_graphs():
    frame = pd.DataFrame({"a": [2.0, 1.0], "b": [1.0, 2.0]})
    registry = _toy_registry()
    out = registry.apply(frame, ["ratio_flag", "ratio"])
    assert list(out.columns) == ["a", "b", "ratio", "ratio_flag"]
    assert out["ratio_flag"].tolist() == [1, 0]
    assert list(frame.columns) == ["a", "b"]  # input frame is not mutated
    with pytest.raises(KeyError, match="missing column 'b'"):
        registry.apply(pd.DataFrame({"a": [1.0]}), ["ratio"])
    registry.register(FeatureSpec("x", Kind.FLAG, ("y",), lambda f, **_: f))
    registry.register(FeatureSpec("y", Kind.FLAG, ("x",), lambda f, **_: f))
    with pytest.raises(ValueError, match="cycle"):
        registry.apply(pd.DataFrame({"a": [1.0]}), ["x"])


# --- panels ---------------------------------------------------------------------------------

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
    daily = daily_panel[daily_panel["date"] >= "2023-01-01"]
    daily = daily.assign(week_start=daily["date"].dt.to_period("W-SUN").dt.start_time.dt.date)
    sums = (
        daily.groupby(["week_start", "dataset_split", "market"])
        .agg(guests=("guests", lambda s: s.sum(min_count=1)), new_arrivals=("new_arrivals", lambda s: s.sum(min_count=1)))
        .reset_index()
    )
    merged = weekly_panel.merge(sums, on=["week_start", "dataset_split", "market"], how="outer", suffixes=("_weekly", "_daily"), indicator=True)
    assert (merged["_merge"] == "both").all()
    for column in ("guests", "new_arrivals"):
        weekly_values, daily_values = merged[f"{column}_weekly"], merged[f"{column}_daily"]
        assert (weekly_values.isna() == daily_values.isna()).all(), column
        both = weekly_values.notna()
        np.testing.assert_allclose(weekly_values[both], daily_values[both], rtol=0, atol=1e-6, err_msg=column)


# --- model components (synthetic data with a known answer) ---------------------------------

def _synthetic(level=8.0, slope=0.05, season=0.3, event=0.5, noise=0.01, market="M", seed=0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2023-01-01", periods=730, freq="D")
    years = (dates - dates[0]).days.to_numpy() / 365.25
    sin = np.sin(2 * np.pi * dates.dayofyear.to_numpy() / 365.25)
    bump = ((dates.dayofyear >= 100) & (dates.dayofyear < 110)).astype(float)
    log_y = level + slope * years + season * sin + event * bump + rng.normal(0.0, noise, len(dates))
    return pd.DataFrame({"market": market, "date": dates, "sin": sin, "bump": bump, "guests": np.exp(log_y)})


def _components():
    return [LinearTrend(), LinearRegressors(["sin"], name="season"), LinearRegressors(["bump"], name="event")]


def test_joint_linear_recovers_known_coefficients():
    frame = _synthetic(noise=0.0)
    model = AdditiveLogModel(_components(), fitter=JointLinear()).fit(frame)
    fitted = model.explain()["M"]
    assert fitted["trend"]["slope_per_year"] == pytest.approx(0.05, abs=1e-9)
    assert fitted["season"]["coef"]["sin"] == pytest.approx(0.3, abs=1e-9)
    assert fitted["event"]["coef"]["bump"] == pytest.approx(0.5, abs=1e-9)
    np.testing.assert_allclose(model.predict(frame), frame["guests"], rtol=1e-9)


def test_backfitting_converges_to_the_joint_solution():
    frame = _synthetic()
    joint = AdditiveLogModel(_components(), fitter=JointLinear()).fit(frame)
    cycled = AdditiveLogModel(_components(), fitter=Backfitting(joint_linear=False, tol=1e-12, max_iter=500)).fit(frame)
    report = cycled.fitted_["M"][1]
    assert report.converged and report.iterations > 1
    np.testing.assert_allclose(cycled.decompose(frame), joint.decompose(frame), atol=1e-9)


def test_components_are_identifiable_and_centred():
    frame = _synthetic(noise=0.02)
    parts = AdditiveLogModel(_components(), fitter=Backfitting(joint_linear=False)).fit(frame).decompose(frame)
    truth_season = 0.3 * (frame["sin"] - frame["sin"].mean())
    truth_event = 0.5 * (frame["bump"] - frame["bump"].mean())
    assert (parts["season"] - truth_season).abs().max() < 0.01
    assert (parts["event"] - truth_event).abs().max() < 0.01
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


def test_fit_state_carries_to_out_of_sample_and_single_row_predictions():
    frame = _synthetic(noise=0.0)
    model = AdditiveLogModel(_components(), fitter=JointLinear()).fit(frame.iloc[:500])
    np.testing.assert_allclose(model.predict(frame.iloc[500:]), frame["guests"].iloc[500:], rtol=1e-9)
    np.testing.assert_allclose(model.predict(frame.iloc[[600]]), frame["guests"].iloc[[600]], rtol=1e-9)


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


def test_fit_report_flags_overlapping_and_unidentified_columns():
    frame = _synthetic().assign(sin_copy=lambda f: f["sin"], never=0.0)
    overlap = AdditiveLogModel([LinearTrend(), LinearRegressors(["sin"], name="a"), LinearRegressors(["sin_copy"], name="b")], fitter=JointLinear()).fit(frame)
    assert overlap.explain()["M"]["fit"]["rank_deficient"]
    constant = AdditiveLogModel([LinearTrend(), LinearRegressors(["never"], name="ghost")], fitter=JointLinear()).fit(frame)
    assert constant.explain()["M"]["ghost"]["unidentified"] == ["never"]


def test_trend_origin_is_shared_across_markets_and_smearing_corrects_the_mean():
    early, late = _synthetic(market="A", noise=0.2), _synthetic(market="B", noise=0.2, seed=1).iloc[200:]
    model = AdditiveLogModel(_components(), fitter=JointLinear(), bias_correction="smearing").fit(pd.concat([early, late], ignore_index=True))
    assert model.explain()["A"]["trend"]["origin"] == model.explain()["B"]["trend"]["origin"] == "2023-01-01"
    assert model.smearing_["A"] == pytest.approx(np.exp(0.2 ** 2 / 2), rel=0.02)


def _calendar(event: str, anchors, start: int, end: int, kind: str = "solar") -> pd.DataFrame:
    calendar = pd.DataFrame({"event": event, "kind": kind, "anchor_date": pd.to_datetime(anchors),
                             "window_start_offset": start, "window_end_offset": end})
    calendar["window_start"] = calendar["anchor_date"] + pd.to_timedelta(start, unit="D")
    calendar["window_end"] = calendar["anchor_date"] + pd.to_timedelta(end, unit="D")
    return calendar


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


def test_one_off_periods_are_flagged_and_masked_from_training():
    shock = load_event_calendar().query("kind == 'one_off'").iloc[0]
    assert shock["scope"] == "international"
    frame = _synthetic(season=0.0, event=0.0, noise=0.0, market="UNITED KINGDOM")
    frame["date"] = pd.date_range("2022-01-01", periods=len(frame), freq="D")
    window = (frame["date"] >= shock["window_start"]) & (frame["date"] <= shock["window_end"])
    frame.loc[window, "guests"] *= np.exp(-0.35)
    masked = AdditiveLogModel([LinearTrend()], fitter=JointLinear(), exclude_flag="is_one_off_period").fit(frame)
    unmasked = AdditiveLogModel([LinearTrend()], fitter=JointLinear()).fit(frame)
    assert masked.explain()["UNITED KINGDOM"]["trend"]["slope_per_year"] == pytest.approx(0.05, abs=1e-9)
    assert unmasked.explain()["UNITED KINGDOM"]["trend"]["slope_per_year"] != pytest.approx(0.05, abs=1e-3)
    both = pd.concat([frame, frame.assign(market="DOMESTIC")], ignore_index=True)
    flags = PANEL_FEATURES.apply(both[["date", "market"]], ["is_one_off_period"], anchor="date")["is_one_off_period"]
    assert flags[both["market"] == "UNITED KINGDOM"].sum() == 28 and flags[both["market"] == "DOMESTIC"].sum() == 0


def test_event_kernel_penalty_never_couples_two_events():
    kernel = EventKernel(["ramadan", "eid_al_fitr", "christmas_new_year"])
    rows = kernel.penalty_rows()
    blocks = np.cumsum([0] + [len(kernel.offsets[e]) for e in kernel.events])
    for row in rows:
        nonzero = np.flatnonzero(row)
        assert np.searchsorted(blocks, nonzero.min(), side="right") == np.searchsorted(blocks, nonzero.max(), side="right")
    short = EventKernel(["national_day"])  # 4-day window: unpenalised so its peak is not flattened
    assert short.penalty_rows() is None


GOLDEN_EVENT_DATES = {
    ("ramadan", "2025-03-01"), ("eid_al_fitr", "2025-03-30"), ("eid_al_adha", "2025-06-06"),
    ("ramadan", "2026-02-18"), ("eid_al_fitr", "2026-03-20"), ("eid_al_adha", "2026-05-27"),
    ("islamic_new_year", "2025-06-27"), ("prophets_birthday", "2025-09-05"), ("national_day", "2025-12-02"),
    ("f1_grand_prix", "2024-12-08"), ("f1_grand_prix", "2025-12-07"), ("f1_grand_prix", "2026-12-06"),
    ("adipec", "2025-11-03"), ("christmas_new_year", "2025-12-25"), ("international_shock_2022", "2022-01-09"),
}


def test_event_registry_matches_golden_dates_and_is_consistent():
    calendar = load_event_calendar()
    anchors = set(zip(calendar["event"], calendar["anchor_date"].dt.strftime("%Y-%m-%d")))
    assert GOLDEN_EVENT_DATES <= anchors
    assert set(DEFAULT_KERNEL_EVENTS) <= set(calendar["event"])
    for event, rows in calendar.groupby("event"):
        rows = rows.sort_values("anchor_date")
        assert (rows["window_start"].iloc[1:].to_numpy() > rows["window_end"].iloc[:-1].to_numpy()).all(), event
    assert {("national_day", "2025-12-02"), ("christmas_new_year", "2025-12-25"), ("ramadan", "2026-02-18")} <= anchors
    # Eid al-Fitr must not share a day with Ramadan, or the two kernels are not identifiable.
    ramadan, fitr = calendar[calendar["event"] == "ramadan"], calendar[calendar["event"] == "eid_al_fitr"]
    for start, end in zip(fitr["window_start"], fitr["window_end"]):
        assert not ((ramadan["window_start"] <= end) & (ramadan["window_end"] >= start)).any()


def test_event_offsets_on_the_daily_panel(daily_panel: pd.DataFrame):
    domestic = daily_panel[daily_panel["market"] == "DOMESTIC"]
    offsets = PANEL_FEATURES.apply(domestic, ["event_day_offsets"], anchor="date").set_index("date")
    ramadan = offsets[offset_column("ramadan")]
    assert ramadan.loc["2026-02-18"] == 0 and ramadan.loc["2026-02-13"] == -5 and np.isnan(ramadan.loc["2026-02-12"])
    assert offsets.loc["2025-12-02", offset_column("national_day")] == 0


def _daily(log_y: np.ndarray, start: str = "2023-01-01", **columns) -> pd.DataFrame:
    dates = pd.date_range(start, periods=len(log_y), freq="D")
    return pd.DataFrame({"market": "M", "date": dates, "guests": np.exp(log_y), **columns})


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


def test_local_level_tracks_a_slow_level_and_extrapolates_flat_by_default():
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
    assert fitted["implied_mean_stay_days"] == pytest.approx(true_w.sum(), rel=0.01)
    assert all(a >= b - 1e-12 for a, b in zip(fitted["survival_w"], fitted["survival_w"][1:])) and fitted["w0"] <= 1 + 1e-9


def _conv_frame(true_w: np.ndarray, base: float, noise: float, n: int = 900, seed: int = 5) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    max_lag = len(true_w) - 1
    arrivals = 1000 * np.exp(0.3 * np.sin(2 * np.pi * np.arange(n) / 365.25) + rng.normal(0, 0.15, n))
    lags = np.column_stack([np.r_[np.full(k, np.nan), arrivals[:n - k]] for k in range(max_lag + 1)])
    guests = (base + np.nan_to_num(lags) @ true_w) * np.exp(rng.normal(0, noise, n))
    return PANEL_FEATURES.apply(_daily(np.log(guests), new_arrivals_filled=arrivals), ["arrival_lags"], max_lag=max_lag)


def _calendar_conv_frame(seed: int = 11, noise: float = 0.05) -> pd.DataFrame:
    """Guests = (base + kernel * arrivals) * exp(strong season and weekend multipliers + noise), w0 = 1.4."""
    rng = np.random.default_rng(seed)
    n, true_w = 900, 1.4 * np.exp(-np.arange(8) / 2.5)
    arrivals = 1000 * np.exp(0.4 * np.sin(2 * np.pi * np.arange(n) / 365.25) + rng.normal(0, 0.2, n))
    lags = np.column_stack([np.r_[np.full(k, np.nan), arrivals[:n - k]] for k in range(len(true_w))])
    dates = pd.date_range("2022-01-01", periods=n, freq="D")
    calendar = 0.4 * (np.cos(2 * np.pi * dates.dayofyear / 365.25) + (dates.dayofweek >= 4))
    guests = (200.0 + np.nan_to_num(lags) @ true_w) * np.exp(calendar + rng.normal(0, noise, n))
    return PANEL_FEATURES.apply(_daily(np.log(guests), new_arrivals_filled=arrivals), ["arrival_lags"], max_lag=7)


def test_backfitting_with_the_arrivals_kernel_never_increases_the_objective():
    # Every block, the kernel included, must minimise the same penalised log-scale objective; a
    # kernel fitted on the raw scale made it cycle and the domestic fit depend on the pass cap (#13).
    components = [ArrivalsConvolution(max_lag=7), AnnualFourier(2), DayOfWeek(), EventKernel()]
    model = AdditiveLogModel(components, fitter=Backfitting(max_iter=40, tol=0.0), include_flag="lag_complete").fit(_calendar_conv_frame())
    objective = model.fitted_["M"][1].objective
    assert len(objective) == 40
    assert all(later <= earlier * (1 + 1e-10) for earlier, later in zip(objective, objective[1:]))


def test_arrivals_kernel_log_gradient_matches_finite_differences():
    from tourism_twin.models.components.arrivals_conv import log_gradient, log_objective

    rng = np.random.default_rng(2)
    design, penalty = rng.uniform(1, 50, (200, 6)), 0.1 * rng.normal(size=(3, 6))
    z, p = np.log(rng.uniform(100, 400, 200)), rng.uniform(0.5, 2.0, 6)
    numeric = np.array([(log_objective(p + h, design, penalty, z, 1e-9) - log_objective(p - h, design, penalty, z, 1e-9)) / 2e-6
                        for h in 1e-6 * np.eye(6)])
    np.testing.assert_allclose(log_gradient(p, design, penalty, z, 1e-9), numeric, rtol=1e-5)


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


def test_residual_gbm_picks_up_a_structure_the_other_parts_miss():
    rng = np.random.default_rng(7)
    flag = (rng.random(800) > 0.5).astype(float)
    frame = _daily(7.0 + 0.25 * flag + rng.normal(0, 0.01, 800), signal=flag)
    model = AdditiveLogModel([LinearTrend(), ResidualGBM(["signal"])], fitter=Backfitting()).fit(frame)
    gbm = model.decompose(frame)["gbm"]
    assert gbm[flag == 1].mean() - gbm[flag == 0].mean() == pytest.approx(0.25, abs=0.02)


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


def test_seasonal_naive_uses_the_same_weekday_a_year_earlier():
    frame = _daily(np.log(np.arange(1, 801, dtype=float)))
    model = SeasonalNaive().fit(frame.iloc[:400])
    pred = model.predict(frame.iloc[400:800])
    np.testing.assert_allclose(pred.iloc[:364], frame["guests"].iloc[36:400].to_numpy())
    np.testing.assert_allclose(pred.iloc[364:], frame["guests"].iloc[36:72].to_numpy())


# --- back-test harness ---------------------------------------------------------------------

def test_benchmarks_through_the_harness_reproduce_the_committed_evaluation():
    assert evaluate() == json.loads(SETTINGS.evaluation_results_path.read_text())


class _LastTrainDate:
    """Records the latest training date it saw; predicts the training mean."""
    seen: list = []

    def fit(self, panel):
        _LastTrainDate.seen.append(pd.to_datetime(panel["date"]).max())
        self.mean = panel["guests"].mean()
        return self

    def predict(self, panel):
        return pd.Series(self.mean, index=panel.index)


def test_rolling_origin_never_trains_on_the_future_and_scores_segments():
    frame = pd.concat([_synthetic(market="DOMESTIC"), _synthetic(market="UNITED KINGDOM", level=6.0, seed=1)], ignore_index=True)
    _LastTrainDate.seen = []
    result = backtest({"mean": _LastTrainDate}, frame, RollingOrigin("2024-03-01", "2024-05-01", horizon_months=2))
    folds = result.predictions.groupby("fold")["date"].agg(["min", "max"])
    assert list(folds.index) == ["origin_2024-03-01", "origin_2024-04-01", "origin_2024-05-01"]
    for last_train, (fold, row) in zip(_LastTrainDate.seen, folds.iterrows()):
        assert last_train < row["min"] == pd.Timestamp(fold.removeprefix("origin_"))
        assert row["max"] == row["min"] + pd.DateOffset(months=2) - np.timedelta64(1, "D")
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


def test_harness_rejects_misindexed_or_missing_predictions_and_reports_skipped_folds():
    frame = _synthetic()
    with pytest.raises(ValueError, match="indexed like the test rows"):
        backtest({"bad": _BadIndex}, frame, RollingOrigin("2024-03-01", "2024-03-01", 1))
    with pytest.raises(ValueError, match="missing predictions"):
        backtest({"gaps": _Gaps}, frame, RollingOrigin("2024-03-01", "2024-03-01", 1))
    with pytest.warns(UserWarning, match="Skipped folds"):
        result = backtest({"mean": _LastTrainDate}, frame, RollingOrigin("2022-11-01", "2023-02-01", 1))
    assert result.skipped == ["origin_2022-11-01", "origin_2022-12-01", "origin_2023-01-01"]


def _ar1_backtest(phi: float, sigma: float, folds: int = 40, horizon: int = 120, seed: int = 11, scale: dict | None = None) -> pd.DataFrame:
    """Back-test-shaped predictions whose log errors follow an AR(1) along the horizon."""
    rng = np.random.default_rng(seed)
    frames = []
    for f in range(folds):
        s = sigma * (scale or {}).get(f, 1.0)
        error = np.zeros(horizon)
        for h in range(horizon):
            error[h] = (phi * error[h - 1] if h else 0.0) + rng.normal(0, s)
        origin = pd.Timestamp("2021-01-01") + pd.DateOffset(months=f)
        frames.append(pd.DataFrame({"fold": f"origin_{f:02d}", "origin": origin, "market": "UNITED KINGDOM",
                                    "horizon_days": np.arange(horizon), "date": origin + pd.to_timedelta(np.arange(horizon), unit="D"),
                                    "pred": 1000.0, "actual": 1000.0 * np.exp(error)}))
    return pd.concat(frames, ignore_index=True)


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


def test_held_out_coverage_is_close_to_nominal_and_ignores_the_held_out_fold():
    coverage = held_out_coverage(_ar1_backtest(phi=0.8, sigma=0.05), coverage=0.8, exclude_months=3)
    assert np.average(coverage["covered"], weights=coverage["n"]) == pytest.approx(0.8, abs=0.04)
    noisy = held_out_coverage(_ar1_backtest(phi=0.8, sigma=0.05, scale={20: 5.0}), coverage=0.8)
    assert noisy.set_index("fold").loc["origin_20", "covered"] < 0.5  # its own large errors did not widen its bounds


def test_model_packages_have_no_row_loops():
    root = Path(SETTINGS.root) / "src" / "tourism_twin"
    offenders = [str(p.relative_to(root)) for package in ("models", "nowcast", "planning")
                 for p in (root / package).rglob("*.py") if ".iterrows(" in p.read_text()]
    assert offenders == []


# Allowed tourism_twin imports per package; nowcast and planning never import each other.
_BELOW_ADAPTERS = {"config", "domain", "features", "data", "models", "nowcast", "planning"}
ALLOWED_IMPORTS = {
    "domain": {"domain"},
    "features": {"domain", "features"},
    "data": {"config", "domain", "features", "data"},
    "models": {"config", "domain", "features", "models"},
    "nowcast": {"config", "domain", "features", "data", "models", "nowcast"},
    "planning": {"config", "domain", "features", "data", "models", "planning"},
    "reporting": _BELOW_ADAPTERS | {"reporting"},
    "cli": _BELOW_ADAPTERS | {"reporting", "cli"},
}


def _imported_packages(path: Path, package: str):
    """tourism_twin sub-packages a module imports, in any import form (absolute, aliased, relative)."""
    import ast

    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                if parts[0] == "tourism_twin" and len(parts) > 1:
                    yield parts[1]
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # relative: resolve against this module's package
                base = list(path.relative_to(Path(SETTINGS.root) / "src" / "tourism_twin").parts[:-1])
                base = base[:len(base) - (node.level - 1)] if node.level > 1 else base
                parts = base + (node.module.split(".") if node.module else [])
                yield parts[0] if parts else package
            elif node.module == "tourism_twin":
                yield from (alias.name for alias in node.names)
            elif node.module and node.module.startswith("tourism_twin."):
                yield node.module.split(".")[1]


def test_packages_import_only_lower_layers():
    root = Path(SETTINGS.root) / "src" / "tourism_twin"
    violations = [f"{path.relative_to(root)} imports {target}"
                  for package, allowed in ALLOWED_IMPORTS.items()
                  for path in (root / package).rglob("*.py")
                  for target in _imported_packages(path, package) if target not in allowed]
    assert violations == []


# --- competition predictions --------------------------------------------------------------

def test_prediction_validator_accepts_mirrored_files_and_flags_bad_ones():
    from tourism_twin.nowcast.predict import (
        DOMESTIC_TEST_FILE, INTERNATIONAL_TEST_FILE, TestPredictions, guest_floor, read_raw_workbook, validate_predictions,
    )

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


def test_test_days_missing_from_the_file_get_below_threshold_arrivals():
    from tourism_twin.data.daily_panel import PUBLICATION_MIN, _fill_suppressed_arrivals

    dates = pd.date_range("2025-07-28", periods=8, freq="D")
    rows = pd.DataFrame({
        "residence_group": "International", "nationality": "X", "date": dates,
        "dataset_split": ["train"] * 4 + ["test"] * 4,
        "new_arrivals": [4.0, 8.0, 50.0, 60.0, 70.0, np.nan, np.nan, 90.0],
        "is_source_present": [True, True, True, True, True, False, True, True],  # test day 6 absent, day 7 '*'
        "same_day_guests": 1.0,
    })
    filled = _fill_suppressed_arrivals(rows).set_index("date")
    assert filled.loc[dates[5], "new_arrivals_filled"] == pytest.approx(6.0)  # mean of 4 and 8: train days below 10
    assert filled.loc[dates[5], "arrivals_below_threshold"] and not filled.loc[dates[6], "arrivals_below_threshold"]
    assert filled.loc[dates[6], "new_arrivals_filled"] == pytest.approx(70 + 2 * (90 - 70) / 3)  # "*" is still interpolated between published days
    assert PUBLICATION_MIN == 10


def test_weekly_outputs_keep_full_weeks_and_give_a_direction_probability():
    from tourism_twin.nowcast.outputs import weekly_forecast

    dates = pd.date_range("2025-08-04", periods=17, freq="D")  # two full Monday weeks + 3 days
    pred = np.where(dates < "2025-08-11", 100.0, 120.0)
    daily = pd.DataFrame({"market": "M", "date": dates, "pred": pred, "lower": pred * 0.9, "upper": pred * 1.1})
    weekly = weekly_forecast(daily, {"M": 0.9})
    assert list(weekly["week_start"].dt.strftime("%Y-%m-%d")) == ["2025-08-04", "2025-08-11"]
    assert weekly["forecast"].tolist() == [700.0, 840.0]
    assert weekly["direction"].iloc[0] == "increase" and weekly["direction_prob"].iloc[0] > 0.9
    assert weekly["direction"].iloc[1] is None
    # Fully persistent errors keep the daily band; independent errors narrow it by sqrt(7).
    same = weekly_forecast(daily, {"M": 1.0})
    assert same["p90"].iloc[0] == pytest.approx(770.0)
    independent = weekly_forecast(daily, {"M": 0.0})
    assert np.log(independent["p90"].iloc[0] / 700) == pytest.approx(np.log(1.1) / np.sqrt(7))
    # Persistent errors cancel in the week-to-week difference, so the direction is surer.
    assert same["direction_prob"].iloc[0] > independent["direction_prob"].iloc[0]


def test_direction_backtest_scores_each_week_once_against_its_baselines():
    from tourism_twin.models.noise import NoiseModel
    from tourism_twin.nowcast.outputs import direction_backtest

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


def test_stay_outputs_come_from_the_kernel_and_are_withheld_when_the_base_stock_dominates():
    from tourism_twin.nowcast.outputs import _stay

    survival = [0.9, 0.6, 0.45, 0.3]
    quoted = _stay({"survival_w": survival, "base_stock_share": 0.1})
    assert quoted["implied_mean_stay_days"] == pytest.approx(2.25)
    assert quoted["short_stay_share"] == pytest.approx(0.5)
    withheld = _stay({"survival_w": survival, "base_stock_share": 0.4})
    assert withheld["implied_mean_stay_days"] is None and withheld["short_stay_share"] is None
    assert withheld["base_stock_share"] == 0.4


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


# --- simulator ------------------------------------------------------------------------------

LEVER_GRID = {
    "zero": {},
    "frequency_gauge_lf": {"delta_frequency": 2.0, "aircraft_gauge": 290.0, "delta_load_factor": 0.02},
    "seats_p2p": {"delta_seats_pct": 0.15, "delta_p2p_share": 0.03},
    "multiplier_los": {"delta_multiplier_pct": 0.05, "delta_los": 0.4},
    "small_gauge": {"delta_frequency": 1.0, "aircraft_gauge": 180.0},
    "route_closure": {"delta_seats_pct": -1.0},
}


def test_waterfall_reconciles_exactly_for_every_market_season_and_lever(twin):
    markets = [*sorted(twin.structural_engine.params), "SWEDEN"]  # all calibrated + one cold-start
    for lever_name, levers in LEVER_GRID.items():
        for market in markets:
            for season in SEASONS:
                result = twin.structural_engine.simulate(market, season, ScenarioLever(market, **levers))
                assert abs(waterfall_total(result) - result.delta_guests) < 1e-9, (lever_name, market, season)
                if lever_name == "zero":
                    assert result.sim_guests == pytest.approx(result.base_guests, abs=1e-5), (market, season)
                    assert all(getattr(result, part) == pytest.approx(0.0, abs=1e-5) for part in WATERFALL_PARTS)
    # ~1.5e7 guests: float rounding is ~2e-9 absolute, so the guard in simulate() must be relative.
    lever = ScenarioLever("GERMANY", delta_frequency=1335.0, aircraft_gauge=451.0, delta_seats_pct=17.47,
                          delta_load_factor=-0.02, delta_p2p_share=-0.01, delta_multiplier_pct=-0.46, delta_los=6.1)
    large = twin.structural_engine.simulate("GERMANY", "Autumn_Shoulder", lever)
    assert abs(waterfall_total(large) - large.delta_guests) <= 1e-9 * large.sim_guests


def test_scenarios_follow_the_planning_rules(twin):
    engine = twin.structural_engine
    for market in ("UNITED KINGDOM", "GERMANY", "INDIA"):  # closing a route removes all aviation demand
        closed = engine.simulate(market, "Winter_Peak", ScenarioLever(market, delta_seats_pct=-1.0))
        assert (closed.sim_seats, closed.sim_pax, closed.sim_p2p, closed.sim_arrivals, closed.sim_guests) == (0.0,) * 5
        assert closed.waterfall_seats == pytest.approx(-closed.base_guests, abs=1e-4)
    domestic = engine.simulate("DOMESTIC", "Winter_Peak", ScenarioLever(
        "DOMESTIC", delta_frequency=5.0, aircraft_gauge=300.0, delta_load_factor=0.05, delta_multiplier_pct=0.10, delta_los=0.2))
    assert (domestic.sim_seats, domestic.waterfall_seats, domestic.waterfall_lf, domestic.waterfall_p2p) == (0.0,) * 4
    assert domestic.waterfall_multiplier > 0.0 and domestic.waterfall_los > 0.0
    for market in ("UNITED KINGDOM", "INDIA", "CHINA"):  # added capacity never lowers demand
        report = twin.run_scenario(market, "Winter_Peak", ScenarioLever(market, delta_frequency=2.0, aircraft_gauge=250.0))
        assert report.structural_result.delta_guests >= 0.0 and report.hybrid_result["hybrid_delta"] >= -1e-6
    for country in ("SWEDEN", "PAKISTAN"):  # unmodelled countries fall back to regional priors
        report = twin.run_scenario(country, "Winter_Peak", ScenarioLever(country, delta_frequency=1.0, aircraft_gauge=200.0))
        assert report.is_cold_start and report.structural_result.sim_guests > 0.0 and report.uncertainty_bands.delta_p50 > 0.0
        assert report.tornado_sensitivity[0]["swing_spread"] > 0.0
    lever = ScenarioLever("UNITED KINGDOM", delta_frequency=2)
    assert twin.uncertainty_engine.run_monte_carlo("UNITED KINGDOM", "Winter_Peak", lever) == \
        twin.uncertainty_engine.run_monte_carlo("UNITED KINGDOM", "Winter_Peak", lever)  # same scenario, same bands


def test_a_served_route_that_converts_nobody_brings_no_aviation_arrivals():
    from tourism_twin.domain.scenario import MarketSeasonParams
    from tourism_twin.planning.structural import StructuralEngine

    params = dict(market="M", season="Winter_Peak", archetype="Long-Haul Leisure", baseline_weekly_seats=1000.0,
                  baseline_load_factor=0.8, baseline_p2p_share=0.0, effective_response_multiplier=0.5,
                  baseline_los=3.0, baseline_weekly_arrivals=200.0, baseline_weekly_guests=600.0, historical_weeks=10)
    engine = StructuralEngine({"M": {"Winter_Peak": params}})
    assert engine.planning_guests("M", "Winter_Peak", 1000.0) == 0.0
    assert engine.simulate("M", "Winter_Peak").base_arrivals == 0.0  # same rule as planning
    unserved = MarketSeasonParams(**{**params, "baseline_weekly_seats": 0.0})
    assert unserved.arrivals_from(0.0, 0.5) == 200.0  # a never-served market keeps its non-aviation arrivals


def test_scenario_residual_is_the_mean_fit_over_the_season_training_weeks():
    from tourism_twin.domain.scenario import SimulationResult
    from tourism_twin.planning.calendar_features import calendar_feature_matrix
    from tourism_twin.planning.residual import ResidualMLEngine

    class NoStructure:
        def planning_guests_for(self, frame):
            return np.zeros(len(frame))

    weeks = pd.date_range("2023-01-02", periods=104, freq="7D")
    holiday = (weeks.isocalendar().week.to_numpy() % 6 == 0).astype(int)
    frame = pd.DataFrame({"market": "M", "week_start": weeks, "iso_week": weeks.isocalendar().week.to_numpy(),
                          "quarter": weeks.quarter, "month": weeks.month, "season": [assign_season(m) for m in weeks.month],
                          "is_holiday_week": holiday, "is_major_event_week": 0,
                          "guests": 1000.0 * holiday + 50.0 * np.sin(2 * np.pi * weeks.dayofyear / 365.25)})
    engine = ResidualMLEngine().fit(frame, NoStructure())
    fitted = engine.models["M"].predict(calendar_feature_matrix(frame))
    for season in SEASONS:
        expected = fitted[(frame["season"] == season).to_numpy()].mean()  # holidays included, as in the baseline
        assert engine.season_residual("M", season) == pytest.approx(expected)
    assert engine.season_residual("UNSEEN", "Winter_Peak") == 0.0
    zeros = {name: 0.0 for name in SimulationResult.__dataclass_fields__ if name not in ("market", "season", "is_cold_start")}
    result = SimulationResult(market="M", season="Summer_Trough", is_cold_start=False, **zeros)
    assert engine.predict_hybrid(result)["residual_correction"] == pytest.approx(engine.season_residual("M", "Summer_Trough"))
