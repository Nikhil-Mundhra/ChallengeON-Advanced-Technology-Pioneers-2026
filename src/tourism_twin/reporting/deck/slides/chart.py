"""A figure from figures.py in the main body area, with a short side note."""

from __future__ import annotations

from tourism_twin.reporting.deck import canvas, figures, grid
from tourism_twin.reporting.deck.slides.parts import lines, side_panel


def render(slide, spec, frame) -> None:
    main, rule_x, side = grid.main_and_side(grid.body_region(frame.body_top))
    image = figures.render(spec["figure"], frame.numbers, spec, main.w, main.h)
    canvas.picture(slide, "chart.figure", image, main)
    side_panel(slide, "side", side, rule_x, lines(spec.get("side")), spec.get("side_note", ""))
