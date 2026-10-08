"""Integrated Abu Dhabi Tourism Digital Twin Simulator.

Combines:
1. Structural Conversion Engine (Seats -> Pax -> P2P -> Arrivals -> Guests)
2. ML Residual Correction Layer (Calendar, Holiday, Event seasonality)
3. Uncertainty Quantification Engine (Beta operational draws, Parameter shocks, Block bootstrap)
4. Tornado Sensitivity Analyzer
5. Exact Waterfall Attribution Decomposition
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from engine.archetypes import get_market_archetype
from engine.config import SETTINGS
from engine.residual import ResidualMLEngine
from engine.structural import (
    ScenarioLever,
    SimulationResult,
    StructuralEngine,
)
from engine.uncertainty import UncertaintyBands, UncertaintyEngine


@dataclass
class ScenarioReport:
    market: str
    season: str
    archetype: str
    is_cold_start: bool
    # Lever inputs
    lever: ScenarioLever
    # Core simulation
    structural_result: SimulationResult
    hybrid_result: Dict[str, Any]
    uncertainty_bands: UncertaintyBands
    # Sensitivity ranking
    tornado_sensitivity: List[Dict[str, Any]]
    # Executive recommendation
    recommendation_summary: str


class TourismDigitalTwin:
    """Unified simulator for Abu Dhabi tourism planning and demand scenario forecasting."""

    def __init__(
        self,
        structural_engine: Optional[StructuralEngine] = None,
        residual_engine: Optional[ResidualMLEngine] = None,
        conformal_path: Path = SETTINGS.conformal_path,
    ):
        self.structural_engine = structural_engine or StructuralEngine.load()
        self.residual_engine = residual_engine or ResidualMLEngine.load()

        conformal_dict = {}
        if conformal_path.exists():
            with open(conformal_path, "r", encoding="utf-8") as f:
                conformal_dict = json.load(f)

        self.uncertainty_engine = UncertaintyEngine(
            self.structural_engine,
            self.residual_engine.residual_history,
            conformal_calibrator=conformal_dict,
        )

    def run_scenario(
        self,
        market: str,
        season: str,
        lever: ScenarioLever,
        n_draws: int = 1500,
        iso_week: int = 10,
        quarter: int = 1,
        month: int = 2,
        is_holiday_week: int = 0,
        is_major_event_week: int = 0,
    ) -> ScenarioReport:
        """Run complete end-to-end scenario evaluation."""
        market_norm = market.upper().strip()
        archetype = get_market_archetype(market_norm).value

        # 1. Structural conversion chain
        struct_res = self.structural_engine.simulate(market_norm, season, lever)

        # 2. Residual correction & monotonicity validation
        hybrid_res = self.residual_engine.predict_hybrid(
            structural_result=struct_res,
            iso_week=iso_week,
            quarter=quarter,
            month=month,
            is_holiday_week=is_holiday_week,
            is_major_event_week=is_major_event_week,
        )

        # 3. Uncertainty quantification
        unc_bands = self.uncertainty_engine.run_monte_carlo(
            market=market_norm,
            season=season,
            lever=lever,
            n_draws=n_draws,
        )

        # 4. Tornado sensitivity analysis
        tornado = self.compute_tornado_sensitivity(market_norm, season, base_lever=lever)

        # 5. Non-technical Executive Recommendation
        rec = self._generate_executive_recommendation(struct_res, unc_bands, tornado)

        return ScenarioReport(
            market=market_norm,
            season=season,
            archetype=archetype,
            is_cold_start=struct_res.is_cold_start,
            lever=lever,
            structural_result=struct_res,
            hybrid_result=hybrid_res,
            uncertainty_bands=unc_bands,
            tornado_sensitivity=tornado,
            recommendation_summary=rec,
        )

    def compute_tornado_sensitivity(
        self,
        market: str,
        season: str,
        base_lever: Optional[ScenarioLever] = None,
    ) -> List[Dict[str, Any]]:
        """Compute relative demand sensitivity across 5 core decision levers (Tornado ranking)."""
        market_norm = market.upper().strip()
        base_res = self.structural_engine.simulate(market_norm, season)

        # For unserved or cold-start routes (base_seats == 0), evaluate sensitivity around
        # the proposed operating point or a benchmark reference service (2 weekly flights, gauge 250 = 500 seats)
        is_unserved = (base_res.base_seats == 0.0)
        ref_freq = 0.0
        ref_gauge = 250.0
        if is_unserved:
            if base_lever is not None and (base_lever.delta_frequency > 0 or base_lever.delta_seats_pct != 0):
                ref_freq = base_lever.delta_frequency
                ref_gauge = base_lever.aircraft_gauge
            else:
                ref_freq = 2.0
                ref_gauge = 250.0
            ref_lever = ScenarioLever(market_norm, delta_frequency=ref_freq, aircraft_gauge=ref_gauge)
            operating_res = self.structural_engine.simulate(market_norm, season, ref_lever)
            ref_baseline_guests = operating_res.sim_guests
        else:
            ref_baseline_guests = base_res.base_guests

        tests = [
            ("Seat Capacity (+15% / -15%)",
             ScenarioLever(market_norm, delta_frequency=ref_freq, aircraft_gauge=ref_gauge, delta_seats_pct=0.15),
             ScenarioLever(market_norm, delta_frequency=ref_freq, aircraft_gauge=ref_gauge, delta_seats_pct=-0.15)),
            ("Load Factor (+4% / -4%)",
             ScenarioLever(market_norm, delta_frequency=ref_freq, aircraft_gauge=ref_gauge, delta_load_factor=0.04),
             ScenarioLever(market_norm, delta_frequency=ref_freq, aircraft_gauge=ref_gauge, delta_load_factor=-0.04)),
            ("P2P Share (+5% / -5%)",
             ScenarioLever(market_norm, delta_frequency=ref_freq, aircraft_gauge=ref_gauge, delta_p2p_share=0.05),
             ScenarioLever(market_norm, delta_frequency=ref_freq, aircraft_gauge=ref_gauge, delta_p2p_share=-0.05)),
            ("Response Multiplier (+10% / -10%)",
             ScenarioLever(market_norm, delta_frequency=ref_freq, aircraft_gauge=ref_gauge, delta_multiplier_pct=0.10),
             ScenarioLever(market_norm, delta_frequency=ref_freq, aircraft_gauge=ref_gauge, delta_multiplier_pct=-0.10)),
            ("Length of Stay (+0.5d / -0.5d)",
             ScenarioLever(market_norm, delta_frequency=ref_freq, aircraft_gauge=ref_gauge, delta_los=0.5),
             ScenarioLever(market_norm, delta_frequency=ref_freq, aircraft_gauge=ref_gauge, delta_los=-0.5)),
        ]

        tornado_rows = []
        for name, lever_up, lever_down in tests:
            res_up = self.structural_engine.simulate(market_norm, season, lever_up)
            res_down = self.structural_engine.simulate(market_norm, season, lever_down)

            delta_up = res_up.sim_guests - ref_baseline_guests
            delta_down = res_down.sim_guests - ref_baseline_guests
            spread = abs(delta_up - delta_down)

            tornado_rows.append({
                "lever_name": name,
                "high_impact_delta": float(delta_up),
                "low_impact_delta": float(delta_down),
                "swing_spread": float(spread),
                "relative_sensitivity": float(spread / ref_baseline_guests) if ref_baseline_guests > 0 else 0.0,
            })

        tornado_rows.sort(key=lambda r: r["swing_spread"], reverse=True)
        return tornado_rows

    def _generate_executive_recommendation(
        self,
        struct_res: SimulationResult,
        unc_bands: UncertaintyBands,
        tornado: List[Dict[str, Any]],
    ) -> str:
        """Synthesize a concise, non-technical decision briefing for tourism leadership."""
        m = struct_res.market
        s = struct_res.season
        cold_tag = " (Cold-Start Regional Prior)" if struct_res.is_cold_start else ""
        delta_pct = (struct_res.delta_guests / struct_res.base_guests) * 100.0 if struct_res.base_guests > 0 else 0.0

        top_swing = tornado[0]["swing_spread"] if len(tornado) > 0 else 0.0
        if top_swing > 1e-3:
            primary_lever = tornado[0]["lever_name"]
            driver_text = f"Tornado sensitivity confirms that '{primary_lever}' represents the single most influential driver."
        else:
            driver_text = "With zero scheduled flight capacity, operational lever sensitivity is currently zero; allocate route capacity to evaluate lever elasticity."

        rec = (
            f"For {m}{cold_tag} in {s}, the simulated aviation intervention yields an estimated "
            f"{struct_res.delta_guests:+,.0f} weekly hotel guest-days ({delta_pct:+.1f}% vs baseline). "
            f"Accounting for operational and parameter variation, the scenario outcome range spans from a conservative "
            f"{unc_bands.delta_p10:+,.0f} guest-days (P10) to an optimistic {unc_bands.delta_p90:+,.0f} guest-days (P90) "
            f"(demonstrated historical holdout coverage: {unc_bands.demonstrated_coverage_pct:.1f}%). "
            f"{driver_text} "
            f"Recommended action: align promotional campaigns to safeguard route load factor and preserve destination conversion."
        )
        return rec

