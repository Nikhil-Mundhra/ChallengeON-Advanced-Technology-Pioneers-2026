"""Rows of 3-6 boxes joined by accent arrows; each row may carry a small label above it."""

from __future__ import annotations

from tourism_twin.reporting.deck import canvas, grid, theme, typeset
from tourism_twin.reporting.deck.grid import Box
from tourism_twin.reporting.deck.slides.parts import max_height


def _row_height(steps, w: float) -> float:
    inner = w - 2 * theme.PAD
    head = max_height([s["head"] for s in steps], "flow_head", inner)
    detail = max_height([s.get("detail", "") for s in steps], "flow_detail", inner)
    return max(theme.FLOW_BOX_MIN, head + (detail + theme.GAP_S / 2 if detail else 0) + 2 * theme.PAD)


def render(slide, spec, frame) -> None:
    region = grid.body_region(frame.body_top)
    label_h = typeset.STYLES["label"].line
    rows = spec["flow"]
    plans = []
    for row in rows:
        steps = row["steps"]
        if not 3 <= len(steps) <= 6:
            raise ValueError(f"flow: 3 to 6 boxes per row, got {len(steps)}")
        boxes = grid.columns(len(steps), 0, 0, gap=theme.FLOW_GAP)
        plans.append((row, boxes, _row_height(steps, boxes[0].w)))
    heights = [(label_h + theme.GAP_S if row.get("label") else 0) + h for row, _, h in plans]
    tops = grid.stack(region.y, heights, theme.GAP_M)
    if tops[-1] + heights[-1] > region.bottom + 1e-6:
        raise typeset.DeckOverflow(f"flow: rows need {tops[-1] + heights[-1] - region.y:.2f} in, have {region.h:.2f} in")
    for r, ((row, boxes, box_h), top) in enumerate(zip(plans, tops), start=1):
        if row.get("label"):
            canvas.text(slide, f"flow{r}.label", Box(region.x, top, region.w, label_h), row["label"], "label")
            top += label_h + theme.GAP_S
        inner_w = boxes[0].w - 2 * theme.PAD
        for i, (box, step) in enumerate(zip(boxes, row["steps"]), start=1):
            name = f"flow{r}.box{i}"
            canvas.card(slide, name, Box(box.x, top, box.w, box_h))
            head_h = canvas.fit(step["head"], "flow_head", inner_w)
            detail_h = canvas.fit(step["detail"], "flow_detail", inner_w) if step.get("detail") else 0.0
            block = head_h + (detail_h + theme.GAP_S / 2 if detail_h else 0)
            y = top + (box_h - block) / 2
            canvas.text(slide, f"{name}.head", Box(box.x + theme.PAD, y, inner_w, head_h), step["head"], "flow_head")
            if detail_h:
                canvas.text(slide, f"{name}.detail", Box(box.x + theme.PAD, y + head_h + theme.GAP_S / 2, inner_w, detail_h),
                            step["detail"], "flow_detail")
            if i > 1:
                mid = top + box_h / 2
                canvas.arrow(slide, f"flow{r}.arrow{i - 1}", (boxes[i - 2].right + theme.ARROW_INSET, mid),
                             (box.x - theme.ARROW_INSET, mid))
