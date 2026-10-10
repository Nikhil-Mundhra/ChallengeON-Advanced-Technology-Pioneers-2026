"""Numbered columns (2-4): number, hairline, head, body."""

from __future__ import annotations

from tourism_twin.reporting.deck import grid
from tourism_twin.reporting.deck.slides.parts import numbered_columns


def render(slide, spec, frame) -> None:
    items = spec["columns"]
    if not 2 <= len(items) <= 4:
        raise ValueError(f"columns: 2 to 4 columns, got {len(items)}")
    numbered_columns(slide, grid.body_region(frame.body_top), items)
