"""Weekly scenario simulator: structural chain with its waterfall, season residual, conformal
range, tornado ranking and the plain-language briefing."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from tourism_twin.config import SETTINGS
from tourism_twin.domain.archetypes import get_market_archetype
from tourism_twin.domain.scenario import ScenarioLever, SimulationResult
from tourism_twin.planning.residual import ResidualMLEngine
from tourism_twin.planning.structural import StructuralEngine
from tourism_twin.planning.uncertainty import UncertaintyBands, UncertaintyEngine
from tourism_twin.planning.briefing import generate_executive_recommendation
from tourism_twin.planning.sensitivity import compute_tornado_sensitivity


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
    ) -> ScenarioReport:
        """Run complete end-to-end scenario evaluation."""
        market_norm = market.upper().strip()
        archetype = get_market_archetype(market_norm).value

        struct_res = self.structural_engine.simulate(market_norm, season, lever)

        hybrid_res = self.residual_engine.predict_hybrid(struct_res)

        unc_bands = self.uncertainty_engine.run_monte_carlo(
            market=market_norm,
            season=season,
            lever=lever,
            n_draws=n_draws,
        )

        tornado = compute_tornado_sensitivity(self.structural_engine, market_norm, season, base_lever=lever)

        rec = generate_executive_recommendation(struct_res, unc_bands, tornado)

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
