"""Structural Scenario Engine for Abu Dhabi Tourism Digital Twin.

Computes the predictive structural conversion chain:
    Aviation Levers (Seats, Freq, Gauge)
       -> Total Pax (Load Factor)
       -> P2P Pax (P2P Share)
       -> Hotel New Arrivals (Effective Response Multiplier M_m,s)
       -> Hotel Guests (guests-per-arrival factor L_m,s: calibrated guests / arrivals, not a measured stay)

Includes:
- Exact waterfall attribution decomposition with zero residual discrepancy.
- Hierarchical cold-start fallback for unmodeled source markets.
- The response of guests to a schedule change, read off the fitted planning chain (planning/schedule_response.py).
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, NamedTuple, Optional, Tuple

import numpy as np
import pandas as pd

from tourism_twin.config import SETTINGS
from tourism_twin.data.panel import TRAINING_CUTOFF, training_window
from tourism_twin.domain.archetypes import (
    MarketArchetype,
    get_cold_start_prior,
    get_market_archetype,
)
from tourism_twin.domain.markets import DOMESTIC
from tourism_twin.domain.scenario import (
    Chain,
    MarketSeasonParams,
    ScenarioLever,
    SimulationResult,
)
from tourism_twin.domain.seasons import SEASONS
from tourism_twin.planning.schedule_response import ScheduleResponse, schedule_factor


class StructuralEngine:
    """Calibrated structural scenario engine mapping aviation decisions to hotel demand."""

    def __init__(self, calibration_data: Optional[Dict[str, Any]] = None, schedule: Optional[ScheduleResponse] = None):
        self.params: Dict[str, Dict[str, MarketSeasonParams]] = {}
        self.schedule = schedule
        if calibration_data:
            self._load_from_dict(calibration_data)

    def elasticity(self, market: str, season: str) -> float:
        """The market's schedule elasticity in the season; 1 (guests scale with seats) for an engine
        built without a fitted response."""
        return self.schedule.for_market(market, season).epsilon if self.schedule else 1.0

    @classmethod
    def calibrate_from_panel(
        cls,
        panel_path: Path = SETTINGS.panel_path,
        save_path: Optional[Path] = SETTINGS.calibration_path,
        max_date: str = TRAINING_CUTOFF,
        market_recency: Optional[Dict[str, float]] = None,
    ) -> "StructuralEngine":
        """Calibrate baseline parameters from complete training weeks."""
        train_df = training_window(pd.read_parquet(panel_path), max_date)
        return cls.calibrate(train_df, save_path=save_path, market_recency=market_recency)

    @classmethod
    def calibrate(
        cls,
        train_df: pd.DataFrame,
        save_path: Optional[Path] = None,
        market_recency: Optional[Dict[str, float]] = None,
    ) -> "StructuralEngine":
        """Calibrate seasonal baseline parameters per market from a window of weekly panel rows.

        `market_recency` specifies optional exponential half-life in days per market (e.g. {"CHINA": 365.0})
        to account for regime shifts without altering unweighted baselines.
        """
        recency_map = {"CHINA": 365.0} if market_recency is None else dict(market_recency)
        engine = cls()
        calibration_dict: Dict[str, Any] = {}

        markets = sorted(train_df["market"].unique())
        max_date = pd.to_datetime(train_df["week_start"]).max() if "week_start" in train_df.columns else None

        for market in markets:
            engine.params[market] = {}
            calibration_dict[market] = {}
            m_df = train_df[train_df["market"] == market]
            archetype = get_market_archetype(market).value

            for season in SEASONS:
                s_df = m_df[m_df["season"] == season]
                n_weeks = len(s_df)
                if n_weeks == 0:
                    continue

                if market in recency_map and max_date is not None and "week_start" in s_df.columns:
                    week_dates = pd.to_datetime(s_df["week_start"])
                    dt_days = (max_date - week_dates).dt.days
                    half_life = recency_map[market]
                    w = (0.5 ** (dt_days / half_life)).to_numpy(dtype=float)
                    w_norm = w / w.sum()
                    avg_seats = float(np.sum(s_df["seats"].to_numpy(dtype=float) * w_norm))
                    avg_pax = float(np.sum(s_df["pax"].to_numpy(dtype=float) * w_norm))
                    avg_p2p = float(np.sum(s_df["p2p"].to_numpy(dtype=float) * w_norm))
                    avg_arrivals = float(np.sum(s_df["new_arrivals"].to_numpy(dtype=float) * w_norm))
                    avg_guests = float(np.sum(s_df["guests"].to_numpy(dtype=float) * w_norm))
                else:
                    avg_seats = float(s_df["seats"].mean())
                    avg_pax = float(s_df["pax"].mean())
                    avg_p2p = float(s_df["p2p"].mean())
                    avg_arrivals = float(s_df["new_arrivals"].mean())
                    avg_guests = float(s_df["guests"].mean())

                # Operational ratios
                lf = avg_pax / avg_seats if avg_seats > 0 else 0.80
                p2p_share = avg_p2p / avg_pax if avg_pax > 0 else 0.50
                # Predictive response multiplier (P2P arrivals -> Hotel arrivals)
                multiplier = avg_arrivals / avg_p2p if avg_p2p > 0 else 1.0
                los = avg_guests / avg_arrivals if avg_arrivals > 0 else 3.5

                param = MarketSeasonParams(
                    market=market,
                    season=season,
                    archetype=archetype,
                    baseline_weekly_seats=avg_seats,
                    baseline_load_factor=lf,
                    baseline_p2p_share=p2p_share,
                    effective_response_multiplier=multiplier,
                    baseline_los=los,
                    baseline_weekly_arrivals=avg_arrivals,
                    baseline_weekly_guests=avg_guests,
                    historical_weeks=n_weeks,
                    is_cold_start=False,
                )
                engine.params[market][season] = param
                calibration_dict[market][season] = asdict(param)

        if save_path:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(calibration_dict, f, indent=2)

        return engine

    @classmethod
    def load(cls, calibration_path: Path = SETTINGS.calibration_path,
             flight_response_path: Path = SETTINGS.flight_response_path) -> "StructuralEngine":
        """Load calibrated engine and its schedule elasticities from saved JSON."""
        with open(calibration_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        schedule = None
        if flight_response_path.exists():
            schedule = ScheduleResponse.from_dict(json.loads(flight_response_path.read_text(encoding="utf-8"))["schedule"])
        return cls(data, schedule)

    def _load_from_dict(self, data: Dict[str, Any]) -> None:
        """Internal helper to populate params from dictionary."""
        for market, seasons in data.items():
            self.params[market] = {}
            for season, p in seasons.items():
                self.params[market][season] = MarketSeasonParams(**p)

    def get_or_create_params(self, market: str, season: str) -> MarketSeasonParams:
        """Return parameters for a market, using cold-start regional priors if unmodeled."""
        market_norm = market.upper().strip()
        if market_norm in self.params and season in self.params[market_norm]:
            return self.params[market_norm][season]

        # Cold-start fallback via hierarchical regional priors
        prior = get_cold_start_prior(market_norm)
        return MarketSeasonParams(
            market=market_norm,
            season=season,
            archetype=prior.archetype.value,
            baseline_weekly_seats=0.0,
            baseline_load_factor=prior.default_load_factor,
            baseline_p2p_share=prior.default_p2p_share,
            effective_response_multiplier=prior.default_multiplier,
            baseline_los=prior.default_los,
            baseline_weekly_arrivals=0.0,
            baseline_weekly_guests=0.0,
            historical_weeks=0,
            is_cold_start=True,
        )

    def schedule_range(self, market: str, season: str, lever: ScenarioLever) -> Tuple[float, float]:
        """Scenario guests at the two ends of the market's elasticity interval, lower first."""
        elasticity = self.schedule.for_market(market, season) if self.schedule else None
        ends = (elasticity.low, elasticity.high) if elasticity else (1.0, 1.0)
        guests = sorted(self.simulate(market, season, lever, epsilon=e).sim_guests for e in ends)
        return guests[0], guests[1]

    def planning_guests(self, market: str, season: str, seats: float) -> float:
        """Weekly hotel guests predicted from scheduled seats and the calibrated seasonal priors.

        The conversion chain simulate() applies to its baseline, evaluated at an arbitrary seat
        count: realized load factor and P2P share are never used, which is what makes it valid
        before flights operate. DOMESTIC ignores seats.
        """
        market_norm = market.upper().strip()
        p = self.get_or_create_params(market_norm, season)
        if _is_domestic(market_norm, p):
            return p.baseline_weekly_arrivals * p.baseline_los
        p2p = seats * p.baseline_load_factor * p.baseline_p2p_share
        return p.arrivals_from(p2p, p.effective_response_multiplier) * p.baseline_los

    def planning_guests_for(self, frame: pd.DataFrame) -> np.ndarray:
        """planning_guests for every row of a frame with market, season and seats columns."""
        return np.array([
            self.planning_guests(market, season, seats)
            for market, season, seats in zip(frame["market"], frame["season"], frame["seats"])
        ], dtype=float)

    def simulate(
        self,
        market: str,
        season: str,
        lever: Optional[ScenarioLever] = None,
        epsilon: Optional[float] = None,
    ) -> SimulationResult:
        """Simulate the forward conversion chain under a scenario lever, with its waterfall.
        `epsilon` overrides the market's schedule elasticity (the ends of its range give the range)."""
        market_norm = market.upper().strip()
        p = self.get_or_create_params(market_norm, season)
        lever = lever or ScenarioLever(market=market_norm)
        domestic = _is_domestic(market_norm, p)
        base = _baseline_chain(p, domestic)
        if domestic:
            sim, schedule = _domestic_scenario(base, lever), Schedule(base.arrivals)
        else:
            sim, schedule = _international_scenario(p, base, lever, self.elasticity(market_norm, season) if epsilon is None else epsilon)
        waterfall = _waterfall(base, sim, schedule, domestic)

        attributed, lift = sum(waterfall), sim.guests - base.guests
        if not math.isclose(attributed, lift, rel_tol=1e-9, abs_tol=1e-6):  # relative: guests reach 1e7
            raise ArithmeticError(
                f"Waterfall attribution {attributed:.6f} does not reconcile to delta_guests {lift:.6f} "
                f"for market={market_norm!r}, season={season!r}."
            )
        return SimulationResult(
            market=market_norm,
            season=season,
            is_cold_start=p.is_cold_start,
            base_seats=base.seats, base_pax=base.pax, base_p2p=base.p2p, base_arrivals=base.arrivals,
            base_guests=base.guests, base_lf=base.lf, base_p2p_share=base.p2p_share,
            base_multiplier=base.multiplier, base_los=base.los,
            sim_seats=sim.seats, sim_pax=sim.pax, sim_p2p=sim.p2p, sim_arrivals=sim.arrivals,
            sim_guests=sim.guests, sim_lf=sim.lf, sim_p2p_share=sim.p2p_share,
            sim_multiplier=sim.multiplier, sim_los=sim.los,
            delta_seats=sim.seats - base.seats, delta_pax=sim.pax - base.pax, delta_p2p=sim.p2p - base.p2p,
            delta_arrivals=sim.arrivals - base.arrivals, delta_guests=sim.guests - base.guests,
            waterfall_seats=waterfall[0], waterfall_lf=waterfall[1], waterfall_p2p=waterfall[2],
            waterfall_multiplier=waterfall[3], waterfall_los=waterfall[4],
        )


def _is_domestic(market: str, p: MarketSeasonParams) -> bool:
    return market == DOMESTIC or p.archetype == MarketArchetype.DOMESTIC_STAYCATION.value


def _baseline_chain(p: MarketSeasonParams, domestic: bool) -> Chain:
    """The calibrated chain; DOMESTIC has no aviation stage and keeps its calibrated arrivals."""
    seats, lf, share = (0.0, 0.0, 0.0) if domestic else (p.baseline_weekly_seats, p.baseline_load_factor, p.baseline_p2p_share)
    pax = seats * lf
    p2p = pax * share
    multiplier = p.effective_response_multiplier
    arrivals = p.baseline_weekly_arrivals if domestic else p.arrivals_from(p2p, multiplier)
    return Chain(seats, lf, pax, share, p2p, multiplier, arrivals, p.baseline_los, arrivals * p.baseline_los)


def _shifted_los(base: Chain, lever: ScenarioLever) -> float:
    return max(1.0, base.los + lever.delta_los) if lever.delta_los != 0.0 else base.los


def _domestic_scenario(base: Chain, lever: ScenarioLever) -> Chain:
    """Flight levers are inactive; only the response multiplier and the stay move."""
    if lever.delta_multiplier_pct != 0.0:
        multiplier = base.multiplier * (1.0 + lever.delta_multiplier_pct)
        arrivals = max(0.0, base.arrivals * (1.0 + lever.delta_multiplier_pct))
    else:
        multiplier, arrivals = base.multiplier, base.arrivals
    los = _shifted_los(base, lever)
    return Chain(0.0, 0.0, 0.0, 0.0, 0.0, multiplier, arrivals, los, arrivals * los)


def _marginal(multiplier: float) -> float:
    """Hotel arrivals per added (or removed) point-to-point passenger: the response multiplier, at
    most 1. The calibrated multiplier is an average ratio of a market's hotel arrivals to the P2P
    passengers on its flights; above 1 it carries visitors arriving by other routes, who do not
    scale with this route's seats."""
    return min(multiplier, 1.0)


class Schedule(NamedTuple):
    """What the new schedule brings with load factor, P2P share and multiplier at baseline: its
    arrivals (the waterfall's seats step), and `conversion`, the hotel arrivals per P2P passenger
    relative to today's marginal rate (ratio ** (epsilon - 1) on a served route, else 1)."""

    arrivals: float
    conversion: float = 1.0


def _international_scenario(p: MarketSeasonParams, base: Chain, lever: ScenarioLever, epsilon: float) -> Tuple[Chain, Schedule]:
    """The scenario chain and its schedule part.

    A schedule change on a served route moves arrivals by (new seats / baseline seats) ** epsilon, the
    fitted chain's elasticity (planning/schedule_response.py). A new route has no baseline to scale, so
    its added P2P passengers convert at the marginal rate (_marginal). The load-factor, P2P-share,
    multiplier and stay levers are assumptions applied on top; load factor and P2P share move
    passengers at the schedule's own conversion, so a shift on many added seats cannot outgrow the
    guests those seats bring. A zero delta keeps the baseline value exactly."""
    gauge = lever.aircraft_gauge if lever.aircraft_gauge > 0 else 250.0
    seats = max(0.0, (base.seats + lever.delta_frequency * gauge) * (1.0 + lever.delta_seats_pct))
    multiplier = max(0.01, base.multiplier * (1.0 + lever.delta_multiplier_pct)) if lever.delta_multiplier_pct != 0.0 else base.multiplier
    los = _shifted_los(base, lever)

    if seats <= 0.0:  # closure: only visitors arriving by other routes stay
        arrivals = max(0.0, base.p2p * max(multiplier - 1.0, 0.0))
        schedule = Schedule(base.p2p * max(base.multiplier - 1.0, 0.0))
        return Chain(0.0, base.lf, 0.0, base.p2p_share, 0.0, multiplier, arrivals, los, arrivals * los), schedule

    lf = float(np.clip(base.lf + lever.delta_load_factor, 0.05, 1.0)) if lever.delta_load_factor != 0.0 else base.lf
    share = float(np.clip(base.p2p_share + lever.delta_p2p_share, 0.01, 1.0)) if lever.delta_p2p_share != 0.0 else base.p2p_share
    pax = seats * lf
    p2p = pax * share
    scheduled_p2p = seats * base.lf * base.p2p_share

    factor = schedule_factor(base.seats, seats, epsilon)
    if factor is None:  # new route
        schedule = Schedule(p.arrivals_from(base.p2p, base.multiplier) + scheduled_p2p * _marginal(base.multiplier))
        carried = p.arrivals_from(base.p2p, multiplier) + scheduled_p2p * _marginal(multiplier)
    else:
        schedule = Schedule(base.arrivals * factor, factor * base.seats / seats)
        carried = schedule.arrivals * (multiplier / base.multiplier) if base.multiplier > 0.0 else schedule.arrivals
    arrivals = max(0.0, carried + (p2p - scheduled_p2p) * _marginal(multiplier) * schedule.conversion)
    return Chain(seats, lf, pax, share, p2p, multiplier, arrivals, los, arrivals * los), schedule


def _waterfall(base: Chain, sim: Chain, schedule: Schedule, domestic: bool) -> tuple:
    """Sequential attribution of the guest change to seats, load factor, P2P share, multiplier and
    stay; each step changes one stage with the earlier stages at their scenario values. The seats
    step is the schedule response; load-factor and P2P-share steps convert at the marginal rate
    (_marginal) times the schedule's conversion; the multiplier step takes the rest of the arrivals
    change."""
    rate = _marginal(base.multiplier) * base.los * schedule.conversion
    seats = 0.0 if domestic else (schedule.arrivals - base.arrivals) * base.los
    lf = sim.seats * (sim.lf - base.lf) * base.p2p_share * rate
    p2p = sim.pax * (sim.p2p_share - base.p2p_share) * rate
    if domestic:  # arrivals do not come from P2P, so the multiplier step is the whole arrivals change
        multiplier = (sim.arrivals - base.arrivals) * base.los
    else:
        multiplier = (sim.arrivals - base.arrivals) * base.los - (seats + lf + p2p)
    return seats, lf, p2p, multiplier, sim.arrivals * (sim.los - base.los)
