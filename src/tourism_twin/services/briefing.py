"""Plain-language decision briefing for tourism leadership."""

from __future__ import annotations

from typing import Any, Dict, List

from tourism_twin.domain.scenario import SimulationResult
from tourism_twin.models.uncertainty import UncertaintyBands


def generate_executive_recommendation(
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


def weekly_nowcast_summary(market: str, market_outputs: Dict[str, Any], week: Dict[str, Any]) -> str:
    """One-paragraph summary of a market's week, using only fields of the outputs document
    (services/outputs.py); it formats numbers, never computes them."""
    parts = [f"{market.title()}, week of {week['week_start']}: about {week['forecast']:,.0f} guest-nights"]
    if week.get("p10") is not None and week.get("p90") is not None:
        parts.append(f"(80% range {week['p10']:,.0f}-{week['p90']:,.0f})")
    text = " ".join(parts) + "."
    if week.get("yoy_change") is not None:
        text += f" {week['yoy_change']:+.1%} on the same week last year."
    if week.get("direction"):
        text += f" Next week likely to {week['direction']} (probability {week['direction_prob']:.0%})."
    drivers = [f"{d['component']} {d['effect_pct']:+.0f}%" for d in week.get("top_drivers", []) if abs(d["effect_pct"]) >= 1]
    if drivers:
        text += " Drivers: " + ", ".join(drivers) + "."
    if market_outputs.get("implied_mean_stay_days") is not None:
        text += (f" Implied mean stay {market_outputs['implied_mean_stay_days']:.1f} nights; "
                 f"{market_outputs['short_stay_share']:.0%} of arrivals leave within two nights.")
    return text
