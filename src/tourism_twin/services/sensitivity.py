"""Tornado sensitivity: how far weekly guests swing when each decision lever moves up and down."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from tourism_twin.domain.scenario import ScenarioLever
from tourism_twin.models.structural import StructuralEngine


def compute_tornado_sensitivity(
    structural_engine: StructuralEngine,
    market: str,
    season: str,
    base_lever: Optional[ScenarioLever] = None,
) -> List[Dict[str, Any]]:
    """Compute relative demand sensitivity across 5 core decision levers (Tornado ranking)."""
    market_norm = market.upper().strip()
    base_res = structural_engine.simulate(market_norm, season)

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
        operating_res = structural_engine.simulate(market_norm, season, ref_lever)
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
        res_up = structural_engine.simulate(market_norm, season, lever_up)
        res_down = structural_engine.simulate(market_norm, season, lever_down)

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
