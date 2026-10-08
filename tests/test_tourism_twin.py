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
from tourism_twin.models.components import EventKernel, LinearRegressors, LinearTrend
from tourism_twin.models.composite import AdditiveLogModel
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


def test_one_off_periods_are_flagged_and_masked_from_training():
    frame = _synthetic(season=0.0, event=0.0, noise=0.0)
    frame["date"] = pd.date_range("2022-01-01", periods=len(frame), freq="D")
    shock = (frame["date"] >= "2022-01-17") & (frame["date"] <= "2022-02-13")
    frame.loc[shock, "guests"] *= np.exp(-0.35)
    masked = AdditiveLogModel([LinearTrend()], fitter=JointLinear(), exclude_flag="is_one_off_period").fit(frame)
    unmasked = AdditiveLogModel([LinearTrend()], fitter=JointLinear()).fit(frame)
    assert masked.explain()["M"]["trend"]["slope_per_year"] == pytest.approx(0.05, abs=1e-9)
    assert unmasked.explain()["M"]["trend"]["slope_per_year"] != pytest.approx(0.05, abs=1e-3)
    flags = PANEL_FEATURES.apply(frame[["date"]], ["is_one_off_period"], anchor="date")["is_one_off_period"]
    assert flags.sum() == 28 and (flags == shock.astype(int)).all()


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
