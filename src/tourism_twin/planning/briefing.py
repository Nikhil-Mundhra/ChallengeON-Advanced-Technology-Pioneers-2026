"""Plain-language decision briefing for tourism leadership."""

from __future__ import annotations

from typing import Any, Dict, List

from tourism_twin.domain.scenario import SimulationResult
from tourism_twin.planning.uncertainty import UncertaintyBands


def generate_executive_recommendation(
    struct_res: SimulationResult,
    unc_bands: UncertaintyBands,
    tornado: List[Dict[str, Any]],
) -> str:
    """Synthesize a plain-language decision briefing for tourism leadership."""
    season_plain = {
        "Winter_Peak": "the winter peak season (November to March)",
        "Spring_Shoulder": "spring",
        "Summer_Trough": "the quiet summer season",
        "Autumn_Shoulder": "autumn",
    }
    lever_plain = {
        "Seat Capacity": (
            "how much seat capacity airlines offer",
            "discuss additional weekly flights or larger aircraft with the airlines",
        ),
        "Load Factor": (
            "how full the flights are",
            "protect seat occupancy through fares and route marketing",
        ),
        "P2P Share": (
            "what share of arriving passengers stay in Abu Dhabi rather than connect onward",
            "work with airlines on destination marketing so more passengers stop in Abu Dhabi instead of connecting through",
        ),
        "Response Multiplier": (
            "how strongly arriving visitors turn into hotel stays",
            "focus on converting visitors into hotel guests through packages and partnerships",
        ),
        "Stay Factor": (
            "how long visitors stay",
            "extend stays with multi-night offers and event programming",
        ),
        "Length of Stay": (
            "how long visitors stay",
            "extend stays with multi-night offers and event programming",
        ),
    }

    m = struct_res.market.title()
    if struct_res.is_cold_start:
        m += " (no direct service today — estimated from comparable markets)"
    s = season_plain.get(struct_res.season, struct_res.season)
    delta_pct = (struct_res.delta_guests / struct_res.base_guests) * 100.0 if struct_res.base_guests > 0 else 0.0
    direction = "add" if struct_res.delta_guests >= 0 else "remove"
    pct_clause = f" ({abs(delta_pct):.1f}% versus today)" if struct_res.base_guests > 0 else ""

    top_swing = tornado[0]["swing_spread"] if len(tornado) > 0 else 0.0
    if top_swing > 1e-3:
        lever_key = tornado[0]["lever_name"].split(" (")[0]
        plain, action = lever_plain.get(
            lever_key,
            ("the operational levers", "review the sensitivity results"),
        )
        driver_text = (
            f"The result moves most with {plain} — the most influential driver. "
            f"Recommended action: {action}."
        )
    else:
        driver_text = (
            "There are no flights on this corridor today, so the operational levers "
            "have no effect until seats exist — model a proposed schedule first."
        )

    rec = (
        f"For {m} in {s}, the scenario would {direction} about "
        f"{abs(struct_res.delta_guests):,.0f} hotel guest-nights per week"
        f"{pct_clause}. "
        f"Depending on airline operations and demand, the plausible range runs from "
        f"{unc_bands.delta_p10:+,.0f} to {unc_bands.delta_p90:+,.0f} guest-nights; "
        f"in back-tests on held-out weeks, ranges like this captured the real outcome "
        f"about {unc_bands.demonstrated_coverage_pct:.0f}% of the time. "
        f"{driver_text}"
    )
    return rec
