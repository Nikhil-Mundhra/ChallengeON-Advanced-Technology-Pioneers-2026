"""Numbers shown in the deck, by name, each with its source.

Sources, later ones overriding earlier: the deck's own `numbers:` block (fallbacks; each entry
names its source), outlook.json (`twin outlook`: outlook.*), the committed weekly planning
evaluation (plan.*), the planning simulator (scen.<id>.* for the deck's named `scenarios:`),
validation_summary.json (`twin validate`: val.*, cmp.*, nat.*).
`{name}` placeholders in slide text are filled from the table; an unknown name is an error, and
every name filled is recorded so the build can list numbers still taken from the fallback block.
"""

from __future__ import annotations

import calendar
import json
import re
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

PLACEHOLDER = re.compile(r"\{([a-zA-Z0-9_.]+)\}")


@dataclass(frozen=True)
class Number:
    value: str
    source: str


@dataclass
class DeckNumbers:
    """The filled-in table plus each named scenario's simulator report (the figures draw from it)."""
    table: Dict[str, Number]
    reports: Dict[str, Any] = field(default_factory=dict)
    used: set = field(default_factory=set)

    def fill(self, text: str) -> str:
        return fill(text, self.table, self.used)

    def fallbacks(self, deck_numbers: Dict[str, Any]) -> List[str]:
        return fallback_numbers(self.table, self.used, deck_numbers)


def _fmt(value: Any, digits: int = 1) -> str:
    return f"{value:.{digits}f}" if isinstance(value, float) else str(value)


def _count(value: float) -> str:
    return f"{value:,.0f}"


def _signed(value: float) -> str:
    return f"{value:+,.0f}"


def from_validation_summary(path: Path) -> Dict[str, Number]:
    """`twin validate` output: val.<spec>.<segment> (WAPE %, daily segment totals),
    cmp.<candidate>_vs_<baseline>.<segment>.<field> (difference = candidate − baseline, pp), and
    nat.<comparison>.<path> for every number under "nationalities"."""
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    source = f"{path.name} (validation origins, #11)"
    out: Dict[str, Number] = {}
    for spec, segments in data.get("segment_wape", {}).get("values", {}).items():
        for segment, value in segments.items():
            out[f"val.{spec}.{segment}"] = Number(_fmt(float(value)), source)
    for row in data.get("compare", {}).get("rows", []):
        key = f"cmp.{row['candidate']}_vs_{row['baseline']}.{row['segment']}"
        for name in ("difference_pp", "ci_low", "ci_high", "share_folds_same_sign"):
            if name in row:
                out[f"{key}.{name}"] = Number(_fmt(float(row[name]), 2), source)

    def leaves(prefix: str, node: Any) -> None:
        if isinstance(node, dict):
            for name, child in node.items():
                leaves(f"{prefix}.{name}", child)
        elif isinstance(node, (int, float)) and not isinstance(node, bool):
            out[prefix] = Number(_fmt(float(node), 2), source)
    leaves("nat", data.get("nationalities", {}))
    return out


def _market_name(market: str) -> str:
    names = {"UNITED KINGDOM": "the UK", "UNITED STATES OF AMERICA": "the US", "RUSSIAN FEDERATION": "Russia"}
    return names.get(market, market.title())


def _month(period: str) -> str:
    """'2026-12' → 'Dec 2026'."""
    year, month = period.split("-")
    return f"{calendar.month_abbr[int(month)]} {year}"


def from_outlook(path: Path) -> Dict[str, Number]:
    """`twin outlook` output: outlook.window / previous_window, outlook.previous.guests (millions),
    outlook.<scenario>.{guests, change, domestic_share, top1..3, top1..3_share, m1..3_guests,
    m1..3_change}, outlook.month1..3, outlook.bt.<scenario>.<segment> (season error %, back-test)
    and outlook.bt.window."""
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    source = f"{path.name} ({data['spec']}, guests known to {data['guests_known_to']}, arrivals to {data['arrivals_known_to']})"
    out = {"outlook.window": Number(data["window"].replace("winter ", ""), source),
           "outlook.previous_window": Number(data["previous"]["window"], source),
           "outlook.previous.guests": Number(_fmt(data["previous"]["guest_nights"] / 1e6, 2), source),
           "outlook.guests_known_to": Number(data["guests_known_to"], source),
           "outlook.arrivals_known_to": Number(data["arrivals_known_to"], source)}
    for i, month in enumerate(data["previous"]["months"], start=1):
        out[f"outlook.previous.m{i}_guests"] = Number(_fmt(month["guest_nights"] / 1e6, 2), source)
    for scenario, summary in data["scenarios"].items():
        key = f"outlook.{scenario}"
        out[f"{key}.change"] = Number(f"{summary['change_pct']:+.0f}", source)
        out[f"{key}.guests"] = Number(_fmt(summary["guest_nights"] / 1e6, 2), source)
        out[f"{key}.difference"] = Number(f"{(summary['guest_nights'] - data['previous']['guest_nights']) / 1e3:+,.0f}", source)
        out[f"{key}.domestic_share"] = Number(f"{summary['domestic_share_pct']:.0f}", source)
        for rank, market in enumerate(summary["top_source_markets"][:3], start=1):
            out[f"{key}.top{rank}"] = Number(_market_name(market["market"]), source)
            out[f"{key}.top{rank}_share"] = Number(f"{market['share_pct']:.0f}", source)
        for i, month in enumerate(summary["months"], start=1):
            out[f"outlook.month{i}"] = Number(_month(month["month"]), source)
            out[f"{key}.m{i}_guests"] = Number(_fmt(month["guest_nights"] / 1e6, 2), source)
            out[f"{key}.m{i}_change"] = Number(f"{month['change_pct']:+.0f}", source)
    for row in data.get("backtest", []):
        out["outlook.bt.window"] = Number(row["window"].replace("winter ", "").replace("–", " to "), source)
        out[f"outlook.bt.{row['scenario']}.{row['segment']}"] = Number(f"{row['season_error_pct']:+.0f}", source)
    return out


PLAN_MODELS = {"1. Historical Seasonal Prior": "prior", "2. Pure ML / Calendar Model": "calendar",
               "3. Structural-Only Engine": "structural", "4. Hybrid Digital Twin": "hybrid"}


def from_planning_evaluation(path: Path) -> Dict[str, Number]:
    """plan.<model>.wmape (%) for the four weekly benchmark models and plan.coverage_pct (share of
    held-out weeks inside the stated range)."""
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    source = f"{path.name} (weekly planning back-test)"
    out = {f"plan.{short}.wmape": Number(_fmt(data["benchmark"][long]["wmape"] * 100), source)
           for long, short in PLAN_MODELS.items() if long in data.get("benchmark", {})}
    if "demonstrated_coverage_pct" in data:
        out["plan.coverage_pct"] = Number(f"{float(data['demonstrated_coverage_pct']):.0f}", source)
    return out


# Lever names as the deck says them (tornado labels and scen.<id>.lever* placeholders).
LEVER_NAMES = {
    "P2P Share": "stopover share",
    "Seat Capacity": "seats",
    "Load Factor": "load factor",
    "Response Multiplier": "hotel capture",
    "Guests-per-arrival factor": "nights per visitor",
}


def lever_name(row: Dict[str, Any]) -> str:
    short = row["lever_name"].split(" (")[0]
    return LEVER_NAMES.get(short, short.lower())


def run_scenario(twin, spec: Dict[str, Any]):
    """One named deck scenario through the planning simulator."""
    from tourism_twin.domain.scenario import ScenarioLever

    levers = {k: v for k, v in spec.items() if k not in ("market", "season")}
    known = {f.name for f in fields(ScenarioLever)} - {"market"}
    unknown = set(levers) - known
    if unknown:
        raise ValueError(f"Unknown scenario levers {sorted(unknown)}; known: {sorted(known)}")
    market = spec["market"].upper()
    return twin.run_scenario(market, spec["season"], ScenarioLever(market=market, **levers))


def scenario_numbers(name: str, report) -> Dict[str, Number]:
    """scen.<name>.*: visitors are weekly hotel check-ins (arrivals), nights are weekly hotel guest
    nights (the hybrid model); p10/p90 bound the scenario's weekly nights; lever1..3 name the levers
    that move nights most around this scenario (tornado, largest swing first) and lever1..3_share
    their share of the total swing (%)."""
    s, h, bands = report.structural_result, report.hybrid_result, report.uncertainty_bands
    source = f"planning simulator: {report.market.title()}, {report.season}"
    values = {"visitors_base": _count(s.base_arrivals), "visitors_sim": _count(s.sim_arrivals),
              "visitors_delta": _signed(s.sim_arrivals - s.base_arrivals),
              "nights_base": _count(h["hybrid_base"]), "nights_sim": _count(h["hybrid_sim"]),
              "nights_delta": _signed(h["hybrid_delta"]), "p10": _count(bands.p10), "p90": _count(bands.p90)}
    ranked = sorted(report.tornado_sensitivity, key=lambda r: -r["swing_spread"])
    total = sum(r["swing_spread"] for r in ranked) or 1.0
    for rank, row in enumerate(ranked[:3], start=1):
        values[f"lever{rank}"] = lever_name(row)
        values[f"lever{rank}_share"] = f"{row['swing_spread'] / total * 100:.0f}"
    return {f"scen.{name}.{k}": Number(v, source) for k, v in values.items()}


def from_scenarios(scenarios: Dict[str, Dict[str, Any]], twin) -> Tuple[Dict[str, Number], Dict[str, Any]]:
    """Numbers and simulator reports for the deck's named scenarios."""
    table: Dict[str, Number] = {}
    reports = {name: run_scenario(twin, spec) for name, spec in (scenarios or {}).items()}
    for name, report in reports.items():
        table.update(scenario_numbers(name, report))
    return table, reports


def from_deck(block: Dict[str, Dict[str, Any]]) -> Dict[str, Number]:
    out = {}
    for name, entry in (block or {}).items():
        if "source" not in entry or "value" not in entry:
            raise ValueError(f"Deck number {name!r} needs both 'value' and 'source'")
        out[name] = Number(str(entry["value"]), str(entry["source"]))
    return out


def _twin_or_none(make_twin: Callable[[], Any]):
    try:
        return make_twin()
    except FileNotFoundError:  # planning artifacts not built
        return None


def collect(deck: Dict[str, Any], validation_summary: Path, planning_evaluation: Path, outlook: Optional[Path] = None,
            make_twin: Optional[Callable[[], Any]] = None) -> DeckNumbers:
    """Every number the deck can show. `deck` is the parsed deck.yaml (its `numbers:` fallbacks and
    `scenarios:`)."""
    table = from_deck(deck.get("numbers", {}))
    if outlook is not None:
        table.update(from_outlook(outlook))
    table.update(from_planning_evaluation(planning_evaluation))
    reports: Dict[str, Any] = {}
    if make_twin is None:
        from tourism_twin.planning.simulator import TourismDigitalTwin as make_twin  # noqa: N813
    twin = _twin_or_none(make_twin) if deck.get("scenarios") else None
    if twin is not None:
        scenario_table, reports = from_scenarios(deck["scenarios"], twin)
        table.update(scenario_table)
    table.update(from_validation_summary(validation_summary))  # artifacts override deck fallbacks
    return DeckNumbers(table, reports)


def fill(text: str, table: Dict[str, Number], used: Optional[set] = None) -> str:
    def replace(match: re.Match) -> str:
        name = match.group(1)
        if name not in table:
            raise KeyError(f"Unresolved number {{{name}}}")
        if used is not None:
            used.add(name)
        return table[name].value
    return PLACEHOLDER.sub(replace, text)


def fallback_numbers(table: Dict[str, Number], used, deck_numbers: Dict[str, Any]) -> List[str]:
    """Names shown in the deck whose value still comes from the deck's own block."""
    return sorted(name for name in used if name in (deck_numbers or {}) and table[name].source == str(deck_numbers[name]["source"]))
