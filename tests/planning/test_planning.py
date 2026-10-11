"""Weekly scenario model: waterfall identity, planning rules, residual."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from tourism_twin.domain.scenario import ScenarioLever
from tourism_twin.domain.seasons import SEASONS, assign_season
from tourism_twin.features import PANEL_FEATURES


WATERFALL_PARTS = ("waterfall_seats", "waterfall_lf", "waterfall_p2p", "waterfall_multiplier", "waterfall_los")


def waterfall_total(result) -> float:
    return sum(getattr(result, part) for part in WATERFALL_PARTS)


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
    for market in ("UNITED KINGDOM", "GERMANY", "INDIA"):  # closing a route removes its own passengers' arrivals only
        closed = engine.simulate(market, "Winter_Peak", ScenarioLever(market, delta_seats_pct=-1.0))
        assert (closed.sim_seats, closed.sim_pax, closed.sim_p2p) == (0.0,) * 3
        other_routes = closed.base_p2p * max(closed.base_multiplier - 1.0, 0.0)  # visitors arriving by other routes stay
        assert closed.sim_arrivals == pytest.approx(other_routes)
        assert closed.waterfall_seats == pytest.approx(-closed.base_p2p * min(closed.base_multiplier, 1.0) * closed.base_los)
    new = engine.simulate("SWEDEN", "Winter_Peak", ScenarioLever("SWEDEN", delta_frequency=3.0, aircraft_gauge=300.0))
    assert new.delta_arrivals <= new.sim_p2p + 1e-9  # a new route adds at most one hotel visitor per passenger who stays
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
    from tourism_twin.planning.calendar_features import residual_feature_matrix
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
    fitted = engine.models["M"].predict(residual_feature_matrix(frame, engine.events))
    for season in SEASONS:
        expected = fitted[(frame["season"] == season).to_numpy()].mean()  # holidays included, as in the baseline
        assert engine.season_residual("M", season) == pytest.approx(expected)
    assert engine.season_residual("UNSEEN", "Winter_Peak") == 0.0
    zeros = {name: 0.0 for name in SimulationResult.__dataclass_fields__ if name not in ("market", "season", "is_cold_start")}
    result = SimulationResult(market="M", season="Summer_Trough", is_cold_start=False, **zeros)
    assert engine.predict_hybrid(result)["residual_correction"] == pytest.approx(engine.season_residual("M", "Summer_Trough"))


def test_event_exposure_is_the_share_of_the_week_in_a_window_that_covers_the_market():
    from tourism_twin.domain.events import load_event_calendar
    from tourism_twin.planning.calendar_features import event_exposure_matrix

    cny = load_event_calendar().query("event == 'chinese_new_year'").iloc[0]  # scope CHINA
    week = pd.Timestamp(cny.window_start) - pd.Timedelta(days=3)  # the window covers the last 4 days
    frame = pd.DataFrame({"market": ["CHINA", "INDIA"], "week_start": [week, week]})
    exposure = event_exposure_matrix(frame, ["chinese_new_year"])
    assert exposure[0, 0] == pytest.approx(4 / 7) and exposure[1, 0] == 0.0


def test_seat_chain_recovers_both_links_and_a_scenario_reruns_them_end_to_end():
    from synthetic import GUEST_W, _seat_chain_frame
    from tourism_twin.models.handler import flagged
    from tourism_twin.models.spec import ModelSpec
    from tourism_twin.planning.chain import ChainSpec

    frame = _seat_chain_frame()
    seats_link = ModelSpec(components=(("seat_kernel", {"max_lag": 3}), "weekday"), rules=(flagged("seat_lag_complete"),),
                           options=(("target", "new_arrivals_filled"),))
    guests_link = ModelSpec(components=(("arrivals_kernel", {"max_lag": 7}),), rules=(flagged("lag_complete"),))
    spec = ChainSpec(seats_link, guests_link, seat_max_lag=3, arrival_max_lag=7)
    # Link 2 learns from observed arrival lags (in the daily panel already; built here).
    chain = spec.build().fit(PANEL_FEATURES.apply(frame[frame["date"] < "2024-09-01"], ["arrival_lags"], max_lag=7))

    later = frame["date"] >= "2024-09-01"
    predicted = chain.predict_frame(frame)
    assert np.abs(predicted.loc[later, "guests"] / frame.loc[later, "guests"] - 1).max() < 0.03
    assert predicted["guests"].isna().sum() == 2 * (3 + 7)  # each market's lag warm-up only

    result = chain.scenario(frame, "A", "2024-10-01", "2024-10-30", 0.10).dropna()
    d_arrivals = result["scenario_arrivals"] - result["arrivals"]
    d_guests = result["scenario_guests"] - result["guests"]
    days = (result["date"] - pd.Timestamp("2024-10-01")).dt.days
    assert (d_arrivals[(days < 0) | (days > 29 + 3)].abs() < 1e-9).all()  # seats reach arrivals over lags 0..3
    assert (d_guests[(days < 0) | (days > 29 + 3 + 7)].abs() < 1e-9).all()  # then guests over lags 0..7
    assert (d_arrivals[(days >= 0) & (days <= 29)] > 0).all()
    # Guests respond through link 2's kernel applied to link 1's arrival change, not a fixed ratio.
    assert d_guests.sum() == pytest.approx(GUEST_W.sum() * d_arrivals.sum(), rel=0.03)
