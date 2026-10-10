"""One huge number with its label, and a side panel."""

from __future__ import annotations

from tourism_twin.reporting.deck import canvas, grid, theme, typeset
from tourism_twin.reporting.deck.grid import Box
from tourism_twin.reporting.deck.slides.parts import lines, side_panel


def render(slide, spec, frame) -> None:
    hero = spec["hero"]
    main, rule_x, side = grid.main_and_side(grid.body_region(frame.body_top))
    value_h = typeset.STYLES["hero"].line
    label_h = canvas.fit(hero["label"], "hero_label", main.w)
    value_y, label_y = grid.stack(main.y, [value_h, label_h], theme.GAP_S)
    if label_y + label_h > main.bottom + 1e-6:
        raise typeset.DeckOverflow("hero: value and label do not fit the body")
    canvas.text(slide, "hero.value", Box(main.x, value_y, main.w, value_h), hero["value"], "hero")
    canvas.text(slide, "hero.label", Box(main.x, label_y, main.w, label_h), hero["label"], "hero_label")
    side_panel(slide, "side", side, rule_x, lines(spec.get("side")), spec.get("side_note", ""))
