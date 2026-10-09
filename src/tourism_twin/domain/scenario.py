"""Value types of the scenario model: calibrated market-season parameters, the planner's
aviation levers, and the simulated conversion chain with its waterfall attribution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple


@dataclass
class MarketSeasonParams:
    market: str
    season: str
    archetype: str
    baseline_weekly_seats: float
    baseline_load_factor: float
    baseline_p2p_share: float
    effective_response_multiplier: float
    baseline_los: float
    baseline_weekly_arrivals: float
    baseline_weekly_guests: float
    historical_weeks: int
    is_cold_start: bool = False

    def arrivals_from(self, p2p: float, multiplier: float) -> float:
        """Hotel arrivals carried by `p2p` passengers: converted by `multiplier` when there are
        any; none on a served route that carries none; a never-served market keeps its
        non-aviation arrivals."""
        if p2p > 0:
            return p2p * multiplier
        return 0.0 if self.baseline_weekly_seats > 0 else self.baseline_weekly_arrivals


class Chain(NamedTuple):
    """One state of the conversion chain: seats -> pax -> P2P -> arrivals -> guests."""

    seats: float
    lf: float
    pax: float
    p2p_share: float
    p2p: float
    multiplier: float
    arrivals: float
    los: float
    guests: float


@dataclass
class ScenarioLever:
    market: str
    delta_frequency: float = 0.0          # Additional weekly round-trip flights (e.g. +2.0)
    aircraft_gauge: float = 250.0         # Seats per flight for frequency delta
    delta_seats_pct: float = 0.0          # Proportional change in seats (e.g. 0.10 for +10%)
    delta_load_factor: float = 0.0        # Absolute shift in load factor (e.g. +0.02)
    delta_p2p_share: float = 0.0          # Absolute shift in P2P share (e.g. +0.02)
    delta_multiplier_pct: float = 0.0     # Proportional shift in response multiplier (e.g. 0.05 for +5%)
    delta_los: float = 0.0                # Absolute change in length of stay days (e.g. +0.3)


@dataclass
class SimulationResult:
    market: str
    season: str
    is_cold_start: bool
    # Baseline measures
    base_seats: float
    base_pax: float
    base_p2p: float
    base_arrivals: float
    base_guests: float
    base_lf: float
    base_p2p_share: float
    base_multiplier: float
    base_los: float
    # Simulated scenario measures
    sim_seats: float
    sim_pax: float
    sim_p2p: float
    sim_arrivals: float
    sim_guests: float
    sim_lf: float
    sim_p2p_share: float
    sim_multiplier: float
    sim_los: float
    # Net shifts
    delta_seats: float
    delta_pax: float
    delta_p2p: float
    delta_arrivals: float
    delta_guests: float
    # Exact Waterfall attribution components (sum exactly to delta_guests)
    waterfall_seats: float
    waterfall_lf: float
    waterfall_p2p: float
    waterfall_multiplier: float
    waterfall_los: float
