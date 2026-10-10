"""Numbers shown in the deck, by name, each with its source.

Order of precedence: artifacts (output/validation_summary.json from `twin validate`;
output/outlook.json from `twin outlook`; the committed planning evaluation
lake/curated/evaluation_results.json), then the deck's own
`numbers:` block, whose entries must name a source. `{name}` placeholders in slide text are
filled from this table; an unresolved placeholder is an error.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

PLACEHOLDER = re.compile(r"\{([a-zA-Z0-9_.]+)\}")


@dataclass(frozen=True)
class Number:
    value: str
    source: str


def _fmt(value: Any, digits: int = 1) -> str:
    return f"{value:.{digits}f}" if isinstance(value, float) else str(value)


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
        for field in ("difference_pp", "ci_low", "ci_high", "share_folds_same_sign"):
            if field in row:
                out[f"{key}.{field}"] = Number(_fmt(float(row[field]), 2), source)

    def leaves(prefix: str, node: Any) -> None:
        if isinstance(node, dict):
            for name, child in node.items():
                leaves(f"{prefix}.{name}", child)
        elif isinstance(node, (int, float)) and not isinstance(node, bool):
            out[prefix] = Number(_fmt(float(node), 2), source)
    leaves("nat", data.get("nationalities", {}))
    return out


def _title(market: str) -> str:
    names = {"UNITED KINGDOM": "the UK", "UNITED STATES OF AMERICA": "the US", "RUSSIAN FEDERATION": "Russia"}
    return names.get(market, market.title())


def from_outlook(path: Path) -> Dict[str, Number]:
    """`twin outlook` output: outlook.window / previous_window, outlook.<scenario>.{change,
    domestic_share, top1..3, top1..3_share, m1..3_change}, outlook.month1..3,
    outlook.bt.<scenario>.<segment> (season error %, back-test) and outlook.bt.window."""
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    source = f"{path.name} ({data['spec']}, guests known to {data['guests_known_to']}, arrivals to {data['arrivals_known_to']})"
    out = {"outlook.window": Number(data["window"].replace("winter ", ""), source),
           "outlook.previous_window": Number(data["previous"]["window"], source),
           "outlook.guests_known_to": Number(data["guests_known_to"], source),
           "outlook.arrivals_known_to": Number(data["arrivals_known_to"], source)}
    for i, month in enumerate(data["previous"]["months"], start=1):
        out[f"outlook.previous.m{i}_guests"] = Number(_fmt(month["guest_nights"] / 1e6, 2), source)
    for scenario, summary in data["scenarios"].items():
        key = f"outlook.{scenario}"
        out[f"{key}.change"] = Number(f"{summary['change_pct']:+.0f}", source)
        out[f"{key}.guests"] = Number(_fmt(summary["guest_nights"] / 1e6, 2), source)
        out[f"{key}.domestic_share"] = Number(f"{summary['domestic_share_pct']:.0f}", source)
        for rank, market in enumerate(summary["top_source_markets"][:3], start=1):
            out[f"{key}.top{rank}"] = Number(_title(market["market"]), source)
            out[f"{key}.top{rank}_share"] = Number(f"{market['share_pct']:.0f}", source)
        for i, month in enumerate(summary["months"], start=1):
            out[f"outlook.month{i}"] = Number(pd_month(month["month"]), source)
            out[f"{key}.m{i}_guests"] = Number(_fmt(month["guest_nights"] / 1e6, 2), source)
            out[f"{key}.m{i}_change"] = Number(f"{month['change_pct']:+.0f}", source)
    for row in data.get("backtest", []):
        out["outlook.bt.window"] = Number(row["window"], source)
        out[f"outlook.bt.{row['scenario']}.{row['segment']}"] = Number(f"{row['season_error_pct']:+.0f}", source)
    return out


def pd_month(period: str) -> str:
    """'2026-12' → 'Dec 2026'."""
    import calendar

    year, month = period.split("-")
    return f"{calendar.month_abbr[int(month)]} {year}"


def from_planning_evaluation(path: Path) -> Dict[str, Number]:
    """plan.<model>.wmape (%) for the weekly planning benchmark."""
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    names = {"1. Historical Seasonal Prior": "prior", "2. Pure ML / Calendar Model": "calendar",
             "3. Structural-Only Engine": "structural", "4. Hybrid Digital Twin": "hybrid"}
    source = f"{path.name} (weekly planning back-test)"
    out = {f"plan.{short}.wmape": Number(_fmt(data["benchmark"][long]["wmape"] * 100), source)
           for long, short in names.items() if long in data.get("benchmark", {})}
    if "demonstrated_coverage_pct" in data:
        out["plan.coverage_pct"] = Number(_fmt(float(data["demonstrated_coverage_pct"])), source)
    return out


LEVER_NAMES = {
    "P2P Share": "the share of passengers ending their trip in Abu Dhabi",
    "Seat Capacity": "seat capacity",
    "Load Factor": "load factor",
    "Response Multiplier": "the hotel capture rate",
    "Guests-per-arrival factor": "guests per arrival",
}


def from_reference_scenario() -> Dict[str, Number]:
    """tornado.top1 / top2 (plain-language lever names, largest swing first) and their shares."""
    try:
        from tourism_twin.reporting.charts import reference_scenario

        tornado = sorted(reference_scenario().tornado_sensitivity, key=lambda r: -r["swing_spread"])
    except FileNotFoundError:  # planning artifacts not built
        return {}
    source = "planning simulator, reference scenario (UK, Winter Peak)"
    total = sum(r["swing_spread"] for r in tornado) or 1.0
    out = {}
    for rank, row in enumerate(tornado[:3], start=1):
        name = row["lever_name"].split(" (")[0]
        out[f"tornado.top{rank}"] = Number(LEVER_NAMES.get(name, name.lower()), source)
        out[f"tornado.top{rank}_share"] = Number(f"{row['swing_spread'] / total * 100:.0f}", source)
    return out


def from_deck(block: Dict[str, Dict[str, Any]]) -> Dict[str, Number]:
    out = {}
    for name, entry in (block or {}).items():
        if "source" not in entry or "value" not in entry:
            raise ValueError(f"Deck number {name!r} needs both 'value' and 'source'")
        out[name] = Number(str(entry["value"]), str(entry["source"]))
    return out


def collect(deck_numbers: Dict[str, Dict[str, Any]], validation_summary: Path, planning_evaluation: Path,
            outlook: Optional[Path] = None) -> Dict[str, Number]:
    table = from_deck(deck_numbers)
    if outlook is not None:
        table.update(from_outlook(outlook))
    table.update(from_planning_evaluation(planning_evaluation))
    table.update(from_reference_scenario())
    table.update(from_validation_summary(validation_summary))  # artifacts override deck fallbacks
    return table


def fill(text: str, table: Dict[str, Number], used: Optional[set] = None) -> str:
    def replace(match: re.Match) -> str:
        name = match.group(1)
        if name not in table:
            raise KeyError(f"Unresolved number {{{name}}}")
        if used is not None:
            used.add(name)
        return table[name].value
    return PLACEHOLDER.sub(replace, text)


def fallback_numbers(table: Dict[str, Number], used: Iterable[str], deck_numbers: Dict[str, Any]) -> List[str]:
    """Names shown in the deck whose value still comes from the deck's own block."""
    return sorted(name for name in used if name in (deck_numbers or {}) and table[name].source == str(deck_numbers[name]["source"]))
