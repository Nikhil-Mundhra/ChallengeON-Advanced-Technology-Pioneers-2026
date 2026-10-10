"""Three stat columns: a label, a big number and a caption, aligned across columns."""

from __future__ import annotations

from tourism_twin.reporting.deck import canvas, grid, theme, typeset
from tourism_twin.reporting.deck.grid import Box
from tourism_twin.reporting.deck.slides.parts import max_height


def render(slide, spec, frame) -> None:
    items = spec["stats"]
    region = grid.body_region(frame.body_top)
    boxes = grid.columns(len(items), region.y, region.h)
    w = boxes[0].w
    label_h = max_height([s["label"] for s in items], "stat_label", w)
    value_h = typeset.STYLES["stat"].line
    caption_h = max_height([s.get("caption", "") for s in items], "body", w)
    for text, style in [(s["label"], "stat_label") for s in items] + [(s.get("caption", ""), "body") for s in items]:
        if text and len(typeset.wrap(text, typeset.STYLES[style], w)) > theme.STAT_TEXT_LINES:
            raise typeset.DeckOverflow(f"stats: {typeset.plain(text)!r} runs over {theme.STAT_TEXT_LINES} lines")
    label_y, value_y, caption_y = grid.stack(region.y, [label_h, value_h, caption_h], theme.GAP_S)
    if caption_y + caption_h > region.bottom + 1e-6:
        raise typeset.DeckOverflow(f"stats: need {caption_y + caption_h - region.y:.2f} in, have {region.h:.2f} in")
    for i, (box, stat) in enumerate(zip(boxes, items), start=1):
        canvas.text(slide, f"stat{i}.label", Box(box.x, label_y, w, label_h), stat["label"], "stat_label")
        canvas.text(slide, f"stat{i}.value", Box(box.x, value_y, w, value_h), stat["value"], "stat")
        if stat.get("caption"):
            canvas.text(slide, f"stat{i}.caption", Box(box.x, caption_y, w, caption_h), stat["caption"], "body")
