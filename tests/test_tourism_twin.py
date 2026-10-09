"""Product test suite, in pipeline order: domain -> lake -> panels -> simulator -> API."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from tourism_twin.config import SETTINGS
from tourism_twin.data.panel import build_weekly_panel
from tourism_twin.features import PANEL_FEATURES, FeatureRegistry, FeatureSpec, Kind
from tourism_twin.domain.events import DEFAULT_KERNEL_EVENTS, load_event_calendar
from tourism_twin.features.events import offset_column
from tourism_twin.models.baselines import SeasonalNaive
from tourism_twin.models.components import (
    AnnualFourier, ArrivalsConvolution, DayOfWeek, EventKernel, LinearRegressors, LinearTrend, LocalLevel, ResidualGBM,
)
from tourism_twin.models.backtest import RollingOrigin, backtest
from tourism_twin.models.composite import AdditiveLogModel
from tourism_twin.models.evaluation import evaluate
from tourism_twin.models.noise import NoiseModel, held_out_coverage
from tourism_twin.models.fitters import Backfitting, JointLinear
from tourism_twin.features.lags import DEFAULT_MAX_LAG, lag_column
from tourism_twin.domain.archetypes import MarketArchetype, get_market_archetype
from tourism_twin.domain.markets import REGIONAL_CLUSTERS, TOP_15_INTERNATIONAL_MARKETS
from tourism_twin.domain.scenario import ScenarioLever
from tourism_twin.domain.seasons import SEASONS

EXPECTED_MARKETS = {*TOP_15_INTERNATIONAL_MARKETS, *REGIONAL_CLUSTERS, "DOMESTIC"}
WATERFALL_PARTS = ("waterfall_seats", "waterfall_lf", "waterfall_p2p", "waterfall_multiplier", "waterfall_los")


def waterfall_total(result) -> float:
    return sum(getattr(result, part) for part in WATERFALL_PARTS)


# --- domain ---------------------------------------------------------------------------------

def test_top15_membership_and_archetypes():
    assert "PHILIPPINES" in TOP_15_INTERNATIONAL_MARKETS
    assert "ARMENIA" not in TOP_15_INTERNATIONAL_MARKETS
    assert get_market_archetype("PHILIPPINES") == MarketArchetype.RESIDENT_VFR


# --- lake -----------------------------------------------------------------------------------

def test_lake_tables_keep_their_grain_contract():
    flights = pd.read_parquet(SETTINGS.flight_daily_path)
    assert (flights["source_grain"] == "daily").all()
    assert pd.to_datetime(flights["date"]).min() >= pd.Timestamp("2023-01-01")

    guests = pd.read_parquet(SETTINGS.guest_daily_path)
    assert {"is_source_present", "target_available", "is_suppressed_arrival", "source_grain"} <= set(guests.columns)
    assert len(guests) == 69_920  # 1,520 dates x (45 international nationalities + domestic)


def test_monthly_flights_are_isolated_to_2022():
    if not SETTINGS.flight_monthly_path.exists():
        pytest.skip("flight_monthly.parquet is produced by `twin build-lake` and is not committed")
    monthly = pd.read_parquet(SETTINGS.flight_monthly_path)
    assert (monthly["source_grain"] == "monthly").all()
    assert pd.to_datetime(monthly["date"]).max().year == 2022


def test_model_artifacts_exist_and_load():
    for path in (SETTINGS.calibration_path, SETTINGS.residual_model_path, SETTINGS.conformal_path):
        assert path.exists(), path
    assert "_demonstrated_holdout_coverage" in json.loads(SETTINGS.conformal_path.read_text())


# --- feature registry ---------------------------------------------------------------------

def _toy_registry() -> FeatureRegistry:
    registry = FeatureRegistry()
    registry.register(FeatureSpec("ratio", Kind.RATIO, ("a", "b"), lambda f, **_: f["a"] / f["b"]))
    registry.register(FeatureSpec("ratio_flag", Kind.FLAG, ("ratio",), lambda f, **_: (f["ratio"] > 1).astype(int)))
    return registry


def test_registry_computes_dependencies_first_and_only_once():
    frame = pd.DataFrame({"a": [2.0, 1.0], "b": [1.0, 2.0]})
    out = _toy_registry().apply(frame, ["ratio_flag", "ratio"])
    assert list(out.columns) == ["a", "b", "ratio", "ratio_flag"]
    assert out["ratio_flag"].tolist() == [1, 0]
    assert list(frame.columns) == ["a", "b"]  # input frame is not mutated


def test_registry_rejects_missing_inputs_cycles_and_duplicates():
    registry = _toy_registry()
    with pytest.raises(KeyError, match="missing column 'b'"):
        registry.apply(pd.DataFrame({"a": [1.0]}), ["ratio"])
    with pytest.raises(ValueError, match="already registered"):
        registry.register(FeatureSpec("ratio", Kind.RATIO, (), lambda f, **_: f))
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
    with pytest.raises(KeyError, match="No fitted model"):
        model.predict(frame.assign(market="C"))


def test_composite_requires_exactly_one_level_owner_and_unique_names():
    with pytest.raises(ValueError, match="own the level"):
        AdditiveLogModel([LinearRegressors(["sin"])])
    with pytest.raises(ValueError, match="own the level"):
        AdditiveLogModel([LinearTrend(), LinearTrend(name="trend2")])
    with pytest.raises(ValueError, match="unique"):
        AdditiveLogModel([LinearTrend(), LinearRegressors(["sin"], name="trend")])


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
    model.fit(frame)
    with pytest.raises(ValueError, match="non-finite values"):
        model.predict(frame.assign(sin=np.nan))
    with pytest.raises(ValueError, match="have no 'market'"):
        model.predict(frame.assign(market=None))
    with pytest.raises(TypeError, match="non-numeric"):
        AdditiveLogModel([LinearTrend(), LinearRegressors(["market"])]).fit(frame)
    with pytest.raises(ValueError, match="anchor"):
        AdditiveLogModel([LinearTrend(date_column="week_start")])
    with pytest.raises(RuntimeError, match="not fitted"):
        LinearRegressors(["sin"]).explain()


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


class _ScaledSine:
    """Non-linear-protocol stub: fits a * sin by closed form on y - offset."""
    name, requires, owns_level = "scaled_sine", ("sin",), False

    def fit(self, panel, offset, y):
        x = panel["sin"] - panel["sin"].mean()
        self.a = float(x @ (y - offset) / (x @ x))
        self.mean = panel["sin"].mean()
        return self

    def contribution(self, panel):
        return self.a * (panel["sin"] - self.mean)

    def explain(self):
        return {"a": self.a}


def test_backfitting_cycles_protocol_components_and_joint_linear_rejects_them():
    frame = _synthetic(event=0.0)
    model = AdditiveLogModel([LinearTrend(), _ScaledSine()], fitter=Backfitting()).fit(frame)
    assert model.explain()["M"]["scaled_sine"]["a"] == pytest.approx(0.3, abs=0.01)
    with pytest.raises(TypeError, match="Use Backfitting"):
        AdditiveLogModel([LinearTrend(), _ScaledSine()], fitter=JointLinear()).fit(frame)


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


def test_event_registry_matches_golden_dates():
    calendar = load_event_calendar()
    anchors = set(zip(calendar["event"], calendar["anchor_date"].dt.strftime("%Y-%m-%d")))
    assert GOLDEN_EVENT_DATES <= anchors


def test_event_registry_is_consistent_and_covers_the_test_period():
    calendar = load_event_calendar()
    assert set(DEFAULT_KERNEL_EVENTS) <= set(calendar["event"])
    for event, rows in calendar.groupby("event"):
        rows = rows.sort_values("anchor_date")
        assert (rows["window_start"].iloc[1:].to_numpy() > rows["window_end"].iloc[:-1].to_numpy()).all(), event
    anchors = set(zip(calendar["event"], calendar["anchor_date"].dt.strftime("%Y-%m-%d")))
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


def test_arrivals_convolution_enforces_w0_at_most_one_when_it_binds():
    true_w = 1.3 * np.exp(-np.arange(8) / 2.0)  # data generated with w0 = 1.3: an unconstrained fit lands above 1
    frame = _conv_frame(true_w, base=0.0, noise=0.02)
    model = AdditiveLogModel([ArrivalsConvolution(max_lag=7)], fitter=Backfitting(), include_flag="lag_complete").fit(frame)
    fitted = model.explain()["M"]["arrivals"]
    assert fitted["w0"] <= 1.0 + 1e-12
    assert all(a >= b - 1e-12 for a, b in zip(fitted["survival_w"], fitted["survival_w"][1:]))


def test_arrivals_convolution_base_stock_is_flat_beyond_the_training_days():
    frame = _conv_frame(np.exp(-np.arange(8) / 3.0), base=300.0, noise=0.0)
    model = AdditiveLogModel([ArrivalsConvolution(max_lag=7)], fitter=Backfitting(), include_flag="lag_complete").fit(frame.iloc[:600])
    component = model.fitted_["M"][0][0]
    future = frame.iloc[600:]
    base = component._base(future["date"]) @ component.c_
    assert np.ptp(base) == 0.0 and base[0] == pytest.approx(list(model.explain()["M"]["arrivals"]["base_stock_by_knot"].values())[-1])


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
    frame = pd.concat([_synthetic(market="DOMESTIC"), _synthetic(market="UNITED KINGDOM", seed=1)], ignore_index=True)
    _LastTrainDate.seen = []
    result = backtest({"mean": _LastTrainDate}, frame, RollingOrigin("2024-03-01", "2024-05-01", horizon_months=2))
    folds = result.predictions.groupby("fold")["date"].agg(["min", "max"])
    assert list(folds.index) == ["origin_2024-03-01", "origin_2024-04-01", "origin_2024-05-01"]
    for last_train, (fold, row) in zip(_LastTrainDate.seen, folds.iterrows()):
        assert last_train < row["min"] == pd.Timestamp(fold.removeprefix("origin_"))
        assert row["max"] == row["min"] + pd.DateOffset(months=2) - np.timedelta64(1, "D")
    assert set(result.metrics["segment"]) == {"all", "domestic", "international"}


def test_weekly_rows_straddling_an_origin_never_train():
    weeks = pd.date_range("2024-01-01", periods=60, freq="W-MON")
    frame = pd.DataFrame({"market": "UNITED KINGDOM", "date": weeks, "guests": 100.0})
    _LastTrainDate.seen = []
    backtest({"mean": _LastTrainDate}, frame, RollingOrigin("2024-10-01", "2024-10-01", horizon_months=1), period_days=7)
    assert _LastTrainDate.seen[0] + np.timedelta64(6, "D") < pd.Timestamp("2024-10-01")  # week of 2024-09-30 excluded


def test_segments_hold_the_right_markets():
    frame = pd.concat([_synthetic(market="DOMESTIC"), _synthetic(market="UNITED KINGDOM", level=6.0, seed=1)], ignore_index=True)
    result = backtest({"mean": _LastTrainDate}, frame, RollingOrigin("2024-03-01", "2024-03-01", horizon_months=1))
    metrics = result.metrics.set_index("segment")
    assert metrics.loc["domestic", "n"] == metrics.loc["international", "n"] == 31
    predictions = result.predictions
    domestic = predictions[predictions["market"] == "DOMESTIC"]
    assert metrics.loc["domestic", "mae"] == pytest.approx((domestic["actual"] - domestic["pred"]).abs().mean())


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
    with pytest.raises(ValueError, match="No fold"):
        backtest({"mean": _LastTrainDate}, frame, RollingOrigin("2030-01-01", "2030-01-01", 1))


def test_oracle_diagnostics_are_not_ranked_with_forecast_models():
    from tourism_twin.models.specs import DIAGNOSTIC_SPECS, MODEL_SPECS

    assert "realized_chain" in DIAGNOSTIC_SPECS and "realized_chain" not in MODEL_SPECS


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
    assert model.phi_["UNITED KINGDOM"] == pytest.approx(0.8, abs=0.03)
    assert model.sigma_eta_["UNITED KINGDOM"] == pytest.approx(0.05, abs=0.003)
    assert model.v0_["UNITED KINGDOM"] == pytest.approx(0.05 ** 2, rel=0.3)  # e_0 = eta_0
    frame = pd.DataFrame({"market": "UNITED KINGDOM", "horizon_days": [0, 5, 60], "pred": 1000.0})
    width = (model.intervals(frame)["upper"] / frame["pred"]).to_numpy()
    assert width[0] < width[1] < width[2] and width[2] == pytest.approx(width[1], rel=0.1)
    with pytest.raises(ValueError, match="no errors for markets"):
        model.intervals(frame.assign(market="ATLANTIS"))
    with pytest.raises(ValueError, match="non-positive or non-finite"):
        NoiseModel().fit(_ar1_backtest(0.8, 0.05).assign(actual=0.0))


def test_noise_variance_matches_the_closed_form():
    model = NoiseModel(phi_={"M": 0.9}, sigma_eta_={"M": 0.1}, v0_={"M": 0.04})
    variance = model.variance(pd.Series(["M"] * 3), pd.Series([0, 1, 2]))
    expected = [0.04 * 0.9 ** (2 * h) + 0.01 * (1 - 0.9 ** (2 * h)) / (1 - 0.81) for h in (0, 1, 2)]
    np.testing.assert_allclose(variance, expected, rtol=1e-12)


def test_held_out_coverage_is_close_to_nominal_and_ignores_the_held_out_fold():
    coverage = held_out_coverage(_ar1_backtest(phi=0.8, sigma=0.05), coverage=0.8, exclude_months=3)
    assert np.average(coverage["covered"], weights=coverage["n"]) == pytest.approx(0.8, abs=0.04)
    noisy = held_out_coverage(_ar1_backtest(phi=0.8, sigma=0.05, scale={20: 5.0}), coverage=0.8)
    assert noisy.set_index("fold").loc["origin_20", "covered"] < 0.5  # its own large errors did not widen its bounds


def test_models_package_has_no_row_loops():
    from pathlib import Path

    import tourism_twin.models as models_package

    offenders = [p.name for p in Path(models_package.__file__).parent.rglob("*.py") if ".iterrows(" in p.read_text()]
    assert offenders == []


# --- competition predictions --------------------------------------------------------------

def test_prediction_validator_accepts_mirrored_files_and_flags_bad_ones():
    from tourism_twin.services.predictions import (
        DOMESTIC_TEST_FILE, INTERNATIONAL_TEST_FILE, TestPredictions, read_raw_workbook, validate_predictions,
    )

    if not (SETTINGS.source_dir / INTERNATIONAL_TEST_FILE).exists():
        pytest.skip("raw test workbooks are supplied locally, not committed")
    domestic = read_raw_workbook(DOMESTIC_TEST_FILE).assign(Guests=100.0)
    international = read_raw_workbook(INTERNATIONAL_TEST_FILE).assign(Guests=10.0)
    keys = pd.concat([international[["Date", "Nationality"]], domestic[["Date"]].assign(Nationality=np.nan)], ignore_index=True)
    intervals = keys.assign(Guests_p10=9.0, Guests_p50=10.0, Guests_p90=11.0)
    good = TestPredictions(domestic, international, intervals, pd.DataFrame())
    assert validate_predictions(good) == []
    bad = TestPredictions(domestic.assign(Guests=np.inf), international.assign(Guests=0.0, **{"New Arrivals": -5.0}),
                          intervals.assign(Guests_p10=12.0).iloc[1:], pd.DataFrame())
    problems = validate_predictions(bad)
    assert any("missing or infinite" in p for p in problems)
    assert any("Guests <= 0" in p for p in problems)
    assert any("source values differ" in p for p in problems)
    assert any("rows or keys differ" in p for p in problems)
    assert any("p10 <= p50 <= p90" in p for p in problems)


def test_weekly_outputs_keep_full_weeks_and_give_a_direction_probability():
    from tourism_twin.services.outputs import weekly_forecast

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
    from tourism_twin.services.outputs import direction_backtest

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
    from tourism_twin.services.outputs import _stay

    survival = [0.9, 0.6, 0.45, 0.3]
    quoted = _stay({"survival_w": survival, "base_stock_share": 0.1})
    assert quoted["implied_mean_stay_days"] == pytest.approx(2.25)
    assert quoted["short_stay_share"] == pytest.approx(0.5)
    withheld = _stay({"survival_w": survival, "base_stock_share": 0.4})
    assert withheld["implied_mean_stay_days"] is None and withheld["short_stay_share"] is None
    assert withheld["base_stock_share"] == 0.4


def test_narration_only_formats_the_outputs_document():
    from tourism_twin.services.briefing import weekly_nowcast_summary

    week = {"week_start": "2025-12-22", "forecast": 1000.0, "p10": 900.0, "p90": 1100.0, "direction": "decrease",
            "direction_prob": 0.8, "yoy_change": 0.05, "trend_vs_training_pct": -12.0,
            "top_drivers": [{"component": "events", "effect_pct": 40.0}]}
    market = {"implied_mean_stay_days": 3.5, "short_stay_share": 0.4, "base_stock_share": 0.1}
    text = weekly_nowcast_summary("M", market, week)
    for fragment in ("1,000", "900-1,100", "+5.0%", "decrease (probability 80%)", "events +40%", "Trend -12%",
                     "3.5 nights", "40% gone", "10% of guests"):
        assert fragment in text


def test_poisson_deviance_matches_its_closed_form():
    from tourism_twin.models.same_day import poisson_deviance

    assert poisson_deviance([0.0], [2.0]) == pytest.approx(4.0)  # 2 * mu when y = 0
    assert poisson_deviance([3.0], [3.0]) == pytest.approx(0.0)
    assert poisson_deviance([4.0], [2.0]) == pytest.approx(2 * (4 * np.log(2) - 2))
    assert np.isfinite(poisson_deviance([1.0], [0.0]))


def test_suppressed_same_day_values_count_as_zero():
    from tourism_twin.models.same_day import same_day_target

    panel = pd.DataFrame({"same_day_guests": [5.0, np.nan, 3.0, np.nan], "n_same_day_suppressed": [0, 2, 1, 0]})
    target = same_day_target(panel)
    assert target.iloc[:3].tolist() == [5.0, 0.0, 3.0] and np.isnan(target.iloc[3])


def test_same_day_poisson_recovers_a_weekday_effect():
    from tourism_twin.models.same_day import SameDayPoisson

    rng = np.random.default_rng(13)
    dates = pd.date_range("2023-01-02", periods=700, freq="D")
    arrivals = rng.uniform(800, 1200, len(dates))
    rate = np.exp(1.0 + 0.5 * (dates.dayofweek == 4) + 0.5 * np.log1p(arrivals))
    frame = pd.DataFrame({"market": "M", "date": dates, "same_day_guests": rng.poisson(rate).astype(float),
                          "n_same_day_suppressed": 0, "is_holiday_week": 0, "new_arrivals_filled": arrivals})
    model = SameDayPoisson().fit(frame)
    friday_coef = model.models_["M"].coef_[3]  # design columns: Tue..Sun, holiday, log arrivals
    assert friday_coef == pytest.approx(0.5, abs=0.05)


# --- simulator ------------------------------------------------------------------------------

LEVER_GRID = {
    "zero": {},
    "frequency_gauge_lf": {"delta_frequency": 2.0, "aircraft_gauge": 290.0, "delta_load_factor": 0.02},
    "seats_p2p": {"delta_seats_pct": 0.15, "delta_p2p_share": 0.03},
    "multiplier_los": {"delta_multiplier_pct": 0.05, "delta_los": 0.4},
    "small_gauge": {"delta_frequency": 1.0, "aircraft_gauge": 180.0},
    "route_closure": {"delta_seats_pct": -1.0},
}


@pytest.mark.parametrize("lever_name", LEVER_GRID)
def test_waterfall_reconciles_exactly_for_every_market_and_season(twin, lever_name: str):
    markets = [*sorted(twin.structural_engine.params), "SWEDEN"]  # all calibrated + one cold-start
    for market in markets:
        for season in SEASONS:
            result = twin.structural_engine.simulate(market, season, ScenarioLever(market, **LEVER_GRID[lever_name]))
            assert abs(waterfall_total(result) - result.delta_guests) < 1e-9, (market, season)
            if lever_name == "zero":
                assert result.sim_guests == pytest.approx(result.base_guests, abs=1e-5), (market, season)
                for part in WATERFALL_PARTS:
                    assert getattr(result, part) == pytest.approx(0.0, abs=1e-5), (market, season, part)


def test_scenario_residual_follows_the_scenario_season():
    from tourism_twin.domain.scenario import SimulationResult
    from tourism_twin.models.residual import ResidualMLEngine

    class SummerFlag:  # residual = the is_summer calendar feature (last column)
        def predict(self, x):
            return x[:, -1]

    engine = ResidualMLEngine()
    engine.models = {"M": SummerFlag()}
    assert engine.season_residual("M", "Summer_Trough") == 1.0
    assert engine.season_residual("M", "Winter_Peak") == 0.0
    zeros = {name: 0.0 for name in SimulationResult.__dataclass_fields__ if name not in ("market", "season", "is_cold_start")}
    result = SimulationResult(market="M", season="Summer_Trough", is_cold_start=False, **zeros)
    assert engine.predict_hybrid(result)["residual_correction"] == 1.0


@pytest.mark.parametrize("market", ["UNITED KINGDOM", "GERMANY", "INDIA"])
def test_route_closure_removes_all_aviation_demand(twin, market: str):
    result = twin.structural_engine.simulate(market, "Winter_Peak", ScenarioLever(market, delta_seats_pct=-1.0))
    assert (result.sim_seats, result.sim_pax, result.sim_p2p, result.sim_arrivals, result.sim_guests) == (0.0,) * 5
    assert result.delta_guests == pytest.approx(-result.base_guests, abs=1e-4)
    assert result.waterfall_seats == pytest.approx(-result.base_guests, abs=1e-4)
    assert (result.waterfall_lf, result.waterfall_p2p, result.waterfall_multiplier, result.waterfall_los) == (0.0,) * 4


def test_domestic_ignores_aviation_levers(twin):
    lever = ScenarioLever("DOMESTIC", delta_frequency=5.0, aircraft_gauge=300.0, delta_load_factor=0.05,
                          delta_multiplier_pct=0.10, delta_los=0.2)
    result = twin.structural_engine.simulate("DOMESTIC", "Winter_Peak", lever)
    assert (result.base_seats, result.sim_seats) == (0.0, 0.0)
    assert (result.waterfall_seats, result.waterfall_lf, result.waterfall_p2p) == (0.0, 0.0, 0.0)
    assert result.waterfall_multiplier > 0.0 and result.waterfall_los > 0.0


@pytest.mark.parametrize("market", ["UNITED KINGDOM", "INDIA", "GERMANY", "SAUDI ARABIA", "CHINA"])
def test_added_capacity_never_lowers_demand(twin, market: str):
    report = twin.run_scenario(market, "Winter_Peak", ScenarioLever(market, delta_frequency=2.0, aircraft_gauge=250.0))
    assert report.structural_result.delta_guests >= 0.0
    assert report.hybrid_result["hybrid_delta"] >= -1e-6


@pytest.mark.parametrize("country", ["SWEDEN", "BRAZIL", "NORWAY", "PAKISTAN"])
def test_cold_start_markets_use_regional_priors(twin, country: str):
    report = twin.run_scenario(country, "Winter_Peak", ScenarioLever(country, delta_frequency=1.0, aircraft_gauge=200.0))
    assert report.is_cold_start
    assert report.structural_result.sim_guests > 0.0
    assert report.uncertainty_bands.delta_p50 > 0.0


def test_cold_start_tornado_uses_a_reference_route(twin):
    report = twin.run_scenario("SWEDEN", "Winter_Peak", ScenarioLever("SWEDEN", delta_frequency=0))
    assert report.tornado_sensitivity and report.tornado_sensitivity[0]["swing_spread"] > 0.0
    assert "influential driver" in report.recommendation_summary


def test_uncertainty_is_deterministic(twin):
    lever = ScenarioLever("UNITED KINGDOM", delta_frequency=2)
    first = twin.uncertainty_engine.run_monte_carlo("UNITED KINGDOM", "Winter_Peak", lever)
    second = twin.uncertainty_engine.run_monte_carlo("UNITED KINGDOM", "Winter_Peak", lever)
    assert first == second


# --- API ------------------------------------------------------------------------------------

def test_api_validates_season_and_exposes_the_hybrid_model():
    from app.server import DigitalTwinHandler

    class Recorder:
        def send_json(self, data, status=200):
            self.response, self.status = data, status

    handler = Recorder()
    DigitalTwinHandler.handle_simulate(handler, {"market": ["UNITED KINGDOM"], "season": ["InvalidSeason"]})
    assert handler.status == 400 and "Invalid season" in handler.response["error"]

    DigitalTwinHandler.handle_simulate(handler, {"market": ["UNITED KINGDOM"], "season": ["Winter_Peak"], "delta_freq": [2]})
    assert handler.status == 200
    assert {"residual_adjustment", "is_monotonic"} <= set(handler.response["hybrid"])
