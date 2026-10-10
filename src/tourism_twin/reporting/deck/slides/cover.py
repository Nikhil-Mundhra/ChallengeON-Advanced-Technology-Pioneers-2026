"""Cover: kicker, a large title and one line under it, on the dark background."""

from __future__ import annotations

from tourism_twin.reporting.deck import canvas, grid, theme, typeset
from tourism_twin.reporting.deck.grid import Box


def render(slide, spec, frame) -> None:
    width = grid.CONTENT_W
    title_h = canvas.fit(spec["title"], "cover_title", width)
    sub_w = grid.span(1, 8)[1]
    sub_h = canvas.fit(spec.get("subtitle", ""), "cover_subtitle", sub_w) if spec.get("subtitle") else 0.0
    title_y = theme.COVER_TITLE_Y
    sub_y = title_y + title_h + 0.5 * typeset.STYLES["cover_subtitle"].size / 72
    canvas.text(slide, "title", Box(theme.MARGIN, title_y, width, title_h), spec["title"], "cover_title")
    if sub_h:
        canvas.text(slide, "subtitle", Box(theme.MARGIN, sub_y, sub_w, sub_h), spec["subtitle"], "cover_subtitle")
    if spec.get("line"):
        line_h = canvas.fit(spec["line"], "subtitle", sub_w)
        y = grid.snap(sub_y + sub_h + theme.RHYTHM)
        canvas.text(slide, "line", Box(theme.MARGIN, y, sub_w, line_h), spec["line"], "subtitle")
