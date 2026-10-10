"""Slide renderers, one module per slide type. Each exposes `render(slide, spec, frame)`: `spec` is
the slide's deck.yaml entry with every `{name}` already filled, `frame` carries the body top shared
by all content slides and the deck numbers (figures draw from them). Renderers only draw; the
header, footnote, footer and background are added by the build.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict

from tourism_twin.reporting.deck.numbers import DeckNumbers


@dataclass(frozen=True)
class Frame:
    body_top: float
    numbers: DeckNumbers


def _registry() -> Dict[str, Callable]:
    from tourism_twin.reporting.deck.slides import chart, columns, cover, flow, hero, rows, stats, table

    return {"cover": cover.render, "columns": columns.render, "rows": rows.render, "hero": hero.render,
            "stats": stats.render, "flow": flow.render, "table": table.render, "chart": chart.render}


def renderer(kind: str) -> Callable:
    registry = _registry()
    if kind not in registry:
        raise KeyError(f"Unknown slide type {kind!r}; known: {sorted(registry)}")
    return registry[kind]
