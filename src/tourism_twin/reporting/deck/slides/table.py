"""A table drawn from text boxes and hairlines (header labels, rows, one highlighted row), with an
optional side panel."""

from __future__ import annotations

from tourism_twin.reporting.deck import canvas, grid, theme, typeset
from tourism_twin.reporting.deck.grid import Box
from tourism_twin.reporting.deck.slides.parts import lines, side_panel


def render(slide, spec, frame) -> None:
    table = spec["table"]
    region = grid.body_region(frame.body_top)
    if spec.get("side"):
        main, rule_x, side = grid.main_and_side(region)
        side_panel(slide, "side", side, rule_x, lines(spec["side"]), spec.get("side_note", ""))
    else:
        main = region
    widths = table.get("widths") or [1 / len(table["header"])] * len(table["header"])
    xs = [main.x + sum(widths[:i]) * main.w for i in range(len(widths))]
    ws = [f * main.w - (theme.PAD if i < len(widths) - 1 else 0) for i, f in enumerate(widths)]
    label_h = typeset.STYLES["label"].line
    for c, head in enumerate(table["header"]):
        canvas.text(slide, f"table.head.c{c + 1}", Box(xs[c] + theme.PAD, main.y, ws[c] - theme.PAD, label_h), head, "label")
    y = main.y + label_h + theme.GAP_S
    canvas.rule(slide, "table.head.rule", main.x, y, main.w)
    highlight = table.get("highlight_row")
    for r, row in enumerate(table["rows"]):
        cells = [f"**{v}**" if r == highlight and c == 0 else (f"=={v}==" if r == highlight else v) for c, v in enumerate(row)]
        row_h = max(canvas.fit(v, "cell", ws[c] - theme.PAD) for c, v in enumerate(cells)) + 2 * theme.GAP_S
        if y + row_h > main.bottom + 1e-6:
            raise typeset.DeckOverflow(f"table: row {r + 1} ends below the body")
        if r == highlight:
            canvas.card(slide, f"table.r{r + 1}.highlight", Box(main.x, y, main.w, row_h))
        for c, value in enumerate(cells):
            h = canvas.fit(value, "cell", ws[c] - theme.PAD)
            canvas.text(slide, f"table.r{r + 1}.c{c + 1}", Box(xs[c] + theme.PAD, y + theme.GAP_S, ws[c] - theme.PAD, h), value, "cell")
        y += row_h
        if r != highlight and r + 1 != highlight and r + 1 < len(table["rows"]):
            canvas.rule(slide, f"table.r{r + 1}.rule", main.x, y, main.w)
