"""Numbers shown in the deck, by name, each with its source.

Order of precedence: artifacts (output/validation_summary.json from `twin validate`; the
committed planning evaluation lake/curated/evaluation_results.json), then the deck's own
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
    """val.<spec>.<segment> (WAPE %, daily segment totals) and cmp.<spec>_vs_<baseline>.<segment>.*"""
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    source = f"{path.name} (validation origins, #11)"
    out: Dict[str, Number] = {}
    for spec, segments in data.get("segment_wape", {}).items():
        for segment, value in segments.items():
            out[f"val.{spec}.{segment}"] = Number(_fmt(float(value)), source)
    for key, segments in data.get("compare", {}).items():
        for segment, result in segments.items():
            for field in ("difference_pp", "ci_low", "ci_high", "share_folds_same_sign"):
                if field in result:
                    out[f"cmp.{key}.{segment}.{field}"] = Number(_fmt(float(result[field]), 2), source)
    for key, value in data.get("constants", {}).items():
        out[f"const.{key}"] = Number(_fmt(value, 2) if isinstance(value, float) else str(value), source)
    return out


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


def collect(deck_numbers: Dict[str, Dict[str, Any]], validation_summary: Path, planning_evaluation: Path) -> Dict[str, Number]:
    table = from_deck(deck_numbers)
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
