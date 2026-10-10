"""Numbered rows (up to 6) spread evenly over the body: number, head and body, hairlines between."""

from __future__ import annotations

from tourism_twin.reporting.deck import canvas, grid, theme, typeset
from tourism_twin.reporting.deck.grid import Box
from tourism_twin.reporting.deck.slides.parts import max_height

NUMBER_COLS, HEAD_COLS = 1, 5   # the body takes the remaining grid columns


def render(slide, spec, frame) -> None:
    items = spec["rows"]
    if not 1 <= len(items) <= 6:
        raise ValueError(f"rows: 1 to 6 rows, got {len(items)}")
    region = grid.body_region(frame.body_top)
    number_x, number_w = grid.span(1, NUMBER_COLS)
    head_x, head_w = grid.span(1 + NUMBER_COLS, HEAD_COLS)
    body_x, body_w = grid.span(1 + NUMBER_COLS + HEAD_COLS, theme.COLUMNS - NUMBER_COLS - HEAD_COLS)
    head_h = max_height([r["head"] for r in items], "row_head", head_w)
    body_h = max_height([r.get("body", "") for r in items], "body_small", body_w)
    content_h = max(head_h, body_h)
    pitch = region.h / len(items)          # rows share the body evenly
    if content_h + theme.GAP_S > pitch + 1e-6:
        raise typeset.DeckOverflow(f"rows: {len(items)} rows need {(content_h + theme.GAP_S) * len(items):.2f} in, "
                                   f"have {region.h:.2f} in")
    # Optical alignment: the head's first baseline and the body's first baseline sit together.
    head_line, body_line = typeset.STYLES["row_head"].line, typeset.STYLES["body_small"].line
    body_offset = (head_line - body_line) / 2
    number_offset = (head_line - typeset.STYLES["row_number"].line) / 2
    for i, item in enumerate(items, start=1):
        y = region.y + (i - 1) * pitch
        if i > 1:
            canvas.rule(slide, f"row{i}.rule", region.x, y, region.w)
        top = y + (pitch - content_h) / 2
        canvas.text(slide, f"row{i}.number", Box(number_x, top + number_offset, number_w, typeset.STYLES["row_number"].line),
                    f"{i:02d}", "row_number")
        canvas.text(slide, f"row{i}.head", Box(head_x, top, head_w, head_h), item["head"], "row_head")
        if item.get("body"):
            canvas.text(slide, f"row{i}.body", Box(body_x, top + body_offset, body_w, body_h), item["body"], "body_small")
