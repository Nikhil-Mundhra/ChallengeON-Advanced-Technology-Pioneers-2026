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
- Monotonically bounded scenario responses.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional

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


class StructuralEngine:
    """Calibrated structural scenario engine mapping aviation decisions to hotel demand."""

    def __init__(self, calibration_data: Optional[Dict[str, Any]] = None):
        self.params: Dict[str, Dict[str, MarketSeasonParams]] = {}
        if calibration_data:
            self._load_from_dict(calibration_data)

    @classmethod
    def calibrate_from_panel(
        cls,
        panel_path: Path = SETTINGS.panel_path,
        save_path: Optional[Path] = SETTINGS.calibration_path,
        max_date: str = TRAINING_CUTOFF,
    ) -> "StructuralEngine":
        """Calibrate baseline parameters from complete training weeks."""
        train_df = training_window(pd.read_parquet(panel_path), max_date)
        return cls.calibrate(train_df, save_path=save_path)

    @classmethod
    def calibrate(
        cls,
        train_df: pd.DataFrame,
        save_path: Optional[Path] = None,
    ) -> "StructuralEngine":
        """Calibrate seasonal baseline parameters per market from a window of weekly panel rows."""
        engine = cls()
        calibration_dict: Dict[str, Any] = {}

        markets = sorted(train_df["market"].unique())

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
    def load(cls, calibration_path: Path = SETTINGS.calibration_path) -> "StructuralEngine":
        """Load calibrated engine from saved JSON."""
        with open(calibration_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(data)

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
    ) -> SimulationResult:
        """Simulate the forward conversion chain under a scenario lever, with its waterfall."""
        market_norm = market.upper().strip()
        p = self.get_or_create_params(market_norm, season)
        lever = lever or ScenarioLever(market=market_norm)
        domestic = _is_domestic(market_norm, p)
        base = _baseline_chain(p, domestic)
        sim = _domestic_scenario(base, lever) if domestic else _international_scenario(p, base, lever)
        waterfall = _waterfall(base, sim, domestic)

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


def _international_scenario(p: MarketSeasonParams, base: Chain, lever: ScenarioLever) -> Chain:
    """Each lever shifts its stage; a zero delta keeps the baseline value exactly. Closing a served
    route removes its arrivals; an unserved market gains aviation arrivals only from new capacity."""
    seats = max(0.0, (base.seats + lever.delta_frequency * lever.aircraft_gauge) * (1.0 + lever.delta_seats_pct))
    lf = float(np.clip(base.lf + lever.delta_load_factor, 0.05, 1.0)) if lever.delta_load_factor != 0.0 else base.lf
    pax = seats * lf
    share = float(np.clip(base.p2p_share + lever.delta_p2p_share, 0.01, 1.0)) if lever.delta_p2p_share != 0.0 else base.p2p_share
    p2p = pax * share
    multiplier = max(0.01, base.multiplier * (1.0 + lever.delta_multiplier_pct)) if lever.delta_multiplier_pct != 0.0 else base.multiplier
    arrivals = p.arrivals_from(p2p, multiplier)
    los = _shifted_los(base, lever)
    return Chain(seats, lf, pax, share, p2p, multiplier, arrivals, los, arrivals * los)


def _waterfall(base: Chain, sim: Chain, domestic: bool) -> tuple:
    """Sequential attribution of the guest change to seats, load factor, P2P share, multiplier and
    stay; each step changes one stage with the earlier stages at their scenario values."""
    seats = (sim.seats - base.seats) * base.lf * base.p2p_share * base.multiplier * base.los
    lf = sim.seats * (sim.lf - base.lf) * base.p2p_share * base.multiplier * base.los
    p2p = sim.pax * (sim.p2p_share - base.p2p_share) * base.multiplier * base.los
    if domestic:  # arrivals do not come from P2P, so the multiplier step is the whole arrivals change
        multiplier = (sim.arrivals - base.arrivals) * base.los
    else:
        multiplier = sim.p2p * (sim.multiplier - base.multiplier) * base.los
    return seats, lf, p2p, multiplier, sim.arrivals * (sim.los - base.los)
