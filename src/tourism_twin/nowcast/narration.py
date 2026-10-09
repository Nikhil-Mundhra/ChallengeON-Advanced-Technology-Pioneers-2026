"""Plain-language text for the nowcast outputs document; formats its fields, computes nothing."""

from __future__ import annotations

from typing import Any, Dict


def weekly_nowcast_summary(market: str, market_outputs: Dict[str, Any], week: Dict[str, Any]) -> str:
    """One-paragraph summary of a market's week, using only fields of the outputs document
    (nowcast/outputs.py); it formats numbers, never computes them."""
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
    if week.get("trend_vs_training_pct") is not None:
        text += f" Trend {week['trend_vs_training_pct']:+.0f}% against the training average."
    if market_outputs.get("implied_mean_stay_days") is not None:
        text += (f" Arrivals kernel: mean stay {market_outputs['implied_mean_stay_days']:.1f} nights, "
                 f"{market_outputs['short_stay_share']:.0%} gone within two nights "
                 f"({market_outputs['base_stock_share']:.0%} of guests outside the kernel).")
    return text
