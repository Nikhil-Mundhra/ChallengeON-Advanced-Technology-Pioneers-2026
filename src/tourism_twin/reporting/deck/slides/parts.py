"""Building blocks shared by several slide types, so equal elements look the same everywhere."""

from __future__ import annotations

from typing import List, Sequence

from tourism_twin.reporting.deck import canvas, grid, theme, typeset
from tourism_twin.reporting.deck.grid import Box


def max_height(texts: Sequence[str], style: str, w: float) -> float:
    """Height of the tallest text: equal elements get equal boxes."""
    return max((canvas.fit(t, style, w) for t in texts if t), default=0.0)


def side_panel(slide, name: str, box: Box, rule_x: float, lines: Sequence[str], note: str = "") -> float:
    """Right-hand panel: short lines, an optional smaller note under them, and a vertical hairline
    in the gutter before the panel. Returns the panel's bottom."""
    y = box.y
    for i, line in enumerate(lines):
        h = canvas.fit(line, "side", box.w)
        canvas.text(slide, f"{name}.line{i + 1}", Box(box.x, y, box.w, h), line, "side")
        y += h + theme.GAP_M
    if note:
        h = canvas.fit(note, "body_small", box.w)
        canvas.text(slide, f"{name}.note", Box(box.x, y, box.w, h), note, "body_small")
        y += h
    else:
        y -= theme.GAP_M
    if y > box.bottom + 1e-6:
        raise typeset.DeckOverflow(f"{name}: side panel needs {y - box.y:.2f} in, has {box.h:.2f} in")
    canvas.rule(slide, f"{name}.rule", rule_x, box.y, max(y, box.y + box.h * 0.6) - box.y, vertical=True)
    return y


def numbered_columns(slide, region: Box, items: Sequence[dict], prefix: str = "col") -> None:
    """2-4 columns: a big accent number, a hairline, a head and a short body, aligned across columns."""
    boxes = grid.columns(len(items), region.y, region.h)
    w = boxes[0].w
    number_h = typeset.STYLES["column_number"].line
    head_h = max_height([i["head"] for i in items], "column_head", w)
    body_h = max_height([i.get("body", "") for i in items], "body", w)
    number_y, rule_y = grid.stack(region.y, [number_h, 0.0], theme.GAP_S)
    head_y, body_y = grid.stack(rule_y + theme.GAP_M, [head_h, body_h], theme.GAP_S)
    if body_y + body_h > region.bottom + 1e-6:
        raise typeset.DeckOverflow(f"{prefix}: columns need {body_y + body_h - region.y:.2f} in, have {region.h:.2f} in")
    for i, (box, item) in enumerate(zip(boxes, items), start=1):
        canvas.text(slide, f"{prefix}{i}.number", Box(box.x, number_y, w, number_h), f"{i:02d}", "column_number")
        canvas.rule(slide, f"{prefix}{i}.rule", box.x, rule_y, w)
        canvas.text(slide, f"{prefix}{i}.head", Box(box.x, head_y, w, head_h), item["head"], "column_head")
        if item.get("body"):
            canvas.text(slide, f"{prefix}{i}.body", Box(box.x, body_y, w, body_h), item["body"], "body")


def lines(value) -> List[str]:
    return [value] if isinstance(value, str) else list(value or [])
