"""Structural Scenario Engine for Abu Dhabi Tourism Digital Twin.

Computes the predictive structural conversion chain:
    Aviation Levers (Seats, Freq, Gauge)
       -> Total Pax (Load Factor)
       -> P2P Pax (P2P Share)
       -> Hotel New Arrivals (Effective Response Multiplier M_m,s)
       -> Hotel Guests (Length-of-Stay Multiplier L_m,s)

Includes:
- Exact waterfall attribution decomposition with zero residual discrepancy.
- Hierarchical cold-start fallback for unmodeled source markets.
- Monotonically bounded scenario responses.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from engine.archetypes import (
    MARKET_ARCHETYPE_MAP,
    TOP_15_INTERNATIONAL_MARKETS,
    MarketArchetype,
    get_cold_start_prior,
    get_market_archetype,
)

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_PANEL_PATH = ROOT_DIR / "lake" / "curated" / "weekly_market_panel.parquet"
DEFAULT_CALIBRATION_PATH = ROOT_DIR / "lake" / "curated" / "structural_calibration.json"


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


class StructuralEngine:
    """Calibrated structural scenario engine mapping aviation decisions to hotel demand."""

    def __init__(self, calibration_data: Optional[Dict[str, Any]] = None):
        self.params: Dict[str, Dict[str, MarketSeasonParams]] = {}
        if calibration_data:
            self._load_from_dict(calibration_data)

    @classmethod
    def calibrate_from_panel(
        cls,
        panel_path: Path = DEFAULT_PANEL_PATH,
        save_path: Optional[Path] = DEFAULT_CALIBRATION_PATH,
        max_date: str = "2025-07-27",
    ) -> "StructuralEngine":
        """Calibrate baseline parameters from complete training weeks."""
        df = pd.read_parquet(panel_path)
        train_df = df[
            (df["dataset_split"] == "train") &
            (df["is_complete_week"] == 1) &
            (df["is_complete_guest_inputs"] == 1) &
            (df["week_start"] <= pd.to_datetime(max_date).date())
        ].copy()

        engine = cls()
        calibration_dict: Dict[str, Any] = {}

        seasons = ["Winter_Peak", "Spring_Shoulder", "Summer_Trough", "Autumn_Shoulder"]
        markets = sorted(train_df["market"].unique())

        for market in markets:
            engine.params[market] = {}
            calibration_dict[market] = {}
            m_df = train_df[train_df["market"] == market]
            archetype = get_market_archetype(market).value

            for season in seasons:
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
    def load(cls, calibration_path: Path = DEFAULT_CALIBRATION_PATH) -> "StructuralEngine":
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

    def simulate(
        self,
        market: str,
        season: str,
        lever: Optional[ScenarioLever] = None,
    ) -> SimulationResult:
        """Simulate the forward conversion chain under a specific scenario lever."""
        market_norm = market.upper().strip()
        p = self.get_or_create_params(market_norm, season)
        if lever is None:
            lever = ScenarioLever(market=market_norm)

        is_domestic = (market_norm == "DOMESTIC") or (p.archetype == MarketArchetype.DOMESTIC_STAYCATION.value)

        # Baseline chain
        base_seats = 0.0 if is_domestic else p.baseline_weekly_seats
        base_lf = 0.0 if is_domestic else p.baseline_load_factor
        base_pax = base_seats * base_lf
        base_p2p_share = 0.0 if is_domestic else p.baseline_p2p_share
        base_p2p = base_pax * base_p2p_share
        base_mult = p.effective_response_multiplier
        base_arrivals = base_p2p * base_mult if (base_p2p > 0 and not is_domestic) else p.baseline_weekly_arrivals
        base_los = p.baseline_los
        base_guests = base_arrivals * base_los

        if is_domestic:
            # Domestic staycation domain: no aviation counterpart; flight levers are strictly inactive
            sim_seats = 0.0
            sim_lf = 0.0
            sim_pax = 0.0
            sim_p2p_share = 0.0
            sim_p2p = 0.0
            sim_mult = base_mult * (1.0 + lever.delta_multiplier_pct)
            sim_arrivals = max(0.0, base_arrivals * (1.0 + lever.delta_multiplier_pct))
            sim_los = max(1.0, base_los + lever.delta_los)
            sim_guests = sim_arrivals * sim_los

            # Waterfall attribution for domestic: purely marketing multiplier and length of stay
            waterfall_seats = 0.0
            waterfall_lf = 0.0
            waterfall_p2p = 0.0
            waterfall_mult = (sim_arrivals - base_arrivals) * base_los
            waterfall_los = sim_arrivals * (sim_los - base_los)
        else:
            # International aviation conversion chain
            added_freq_seats = lever.delta_frequency * lever.aircraft_gauge
            sim_seats = max(0.0, (base_seats + added_freq_seats) * (1.0 + lever.delta_seats_pct))
            sim_lf = np.clip(base_lf + lever.delta_load_factor, 0.10, 0.99)
            sim_pax = sim_seats * sim_lf
            sim_p2p_share = np.clip(base_p2p_share + lever.delta_p2p_share, 0.05, 0.99)
            sim_p2p = sim_pax * sim_p2p_share
            sim_mult = max(0.01, base_mult * (1.0 + lever.delta_multiplier_pct))
            sim_arrivals = sim_p2p * sim_mult if sim_p2p > 0 else base_arrivals
            sim_los = max(1.0, base_los + lever.delta_los)
            sim_guests = sim_arrivals * sim_los

            # Exact Waterfall Attribution Decomposition
            # Step 1: Seat Capacity Effect
            delta_s = sim_seats - base_seats
            waterfall_seats = delta_s * base_lf * base_p2p_share * base_mult * base_los

            # Step 2: Load Factor Effect
            delta_lf = sim_lf - base_lf
            waterfall_lf = sim_seats * delta_lf * base_p2p_share * base_mult * base_los

            # Step 3: P2P Share Mix Effect
            delta_p2p_s = sim_p2p_share - base_p2p_share
            waterfall_p2p = sim_pax * delta_p2p_s * base_mult * base_los

            # Step 4: Multiplier Effect (Marketing/Conversion Shift)
            delta_mult = sim_mult - base_mult
            waterfall_mult = sim_p2p * delta_mult * base_los

            # Step 5: Stay Duration Effect
            delta_l = sim_los - base_los
            waterfall_los = sim_arrivals * delta_l

        return SimulationResult(
            market=market_norm,
            season=season,
            is_cold_start=p.is_cold_start,
            base_seats=base_seats,
            base_pax=base_pax,
            base_p2p=base_p2p,
            base_arrivals=base_arrivals,
            base_guests=base_guests,
            base_lf=base_lf,
            base_p2p_share=base_p2p_share,
            base_multiplier=base_mult,
            base_los=base_los,
            sim_seats=sim_seats,
            sim_pax=sim_pax,
            sim_p2p=sim_p2p,
            sim_arrivals=sim_arrivals,
            sim_guests=sim_guests,
            sim_lf=sim_lf,
            sim_p2p_share=sim_p2p_share,
            sim_multiplier=sim_mult,
            sim_los=sim_los,
            delta_seats=sim_seats - base_seats,
            delta_pax=sim_pax - base_pax,
            delta_p2p=sim_p2p - base_p2p,
            delta_arrivals=sim_arrivals - base_arrivals,
            delta_guests=sim_guests - base_guests,
            waterfall_seats=waterfall_seats,
            waterfall_lf=waterfall_lf,
            waterfall_p2p=waterfall_p2p,
            waterfall_multiplier=waterfall_mult,
            waterfall_los=waterfall_los,
        )
