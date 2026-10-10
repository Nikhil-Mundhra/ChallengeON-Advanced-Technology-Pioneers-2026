"""Presentation deck: meta/deck/deck.yaml (content) → output/deck/deck.pptx (+ deck.pdf).

Teammates edit only the YAML: slide titles, one-line messages, check-icon lists (parent →
detail lines), stat tiles, cards, figure and table names, speaker notes; `layout: cover` for the
title slide. Numbers are `{name}` placeholders filled from artifacts
(numbers.py); figures come from figures.py; layout from layout.py.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pptx.util import Inches

from tourism_twin.config import SETTINGS
from tourism_twin.reporting.deck import figures, layout, numbers

DEFAULT_CONTENT = SETTINGS.root / "meta" / "deck" / "deck.yaml"


@dataclass
class DeckResult:
    pptx: Path
    pdf: Optional[Path]
    slides: int
    fallback_numbers: List[str]


def _fill_tree(nodes, table, used):
    out = []
    for node in nodes or []:
        if isinstance(node, str):
            out.append(numbers.fill(node, table, used))
        else:
            out.append({"text": numbers.fill(node["text"], table, used),
                        "children": _fill_tree(node.get("children", []), table, used)})
    return out


def _table_rows(spec: Dict[str, Any], table, used) -> tuple[List[str], List[List[str]]]:
    header = [numbers.fill(h, table, used) for h in spec["header"]]
    rows = [[numbers.fill(cell, table, used) for cell in row] for row in spec["rows"]]
    return header, rows


def build_deck(content: Path = DEFAULT_CONTENT, out_dir: Optional[Path] = None, pdf: bool = True,
               validation_summary: Optional[Path] = None, planning_evaluation: Optional[Path] = None,
               outlook: Optional[Path] = None) -> DeckResult:
    content = Path(content)
    deck = yaml.safe_load(content.read_text())
    out_dir = Path(out_dir or SETTINGS.output_dir / "deck")
    fig_dir = out_dir / "figures"
    assets_dir = content.parent / "assets"
    table = numbers.collect(deck.get("numbers", {}),
                            validation_summary or SETTINGS.output_dir / "validation_summary.json",
                            planning_evaluation or SETTINGS.evaluation_results_path,
                            outlook or SETTINGS.output_dir / "outlook.json")
    used: set = set()

    prs = layout.new_presentation()
    slides = deck["slides"]
    footer = deck.get("footer", "")
    fill = lambda text: numbers.fill(text, table, used)  # noqa: E731
    for page, spec in enumerate(slides, start=1):
        title, message = fill(spec["title"]), fill(spec.get("message", ""))
        tiles = [{**s, "value": fill(s["value"]), "label": fill(s["label"])} for s in spec.get("stats", [])]
        tiles_cards = [{**c, "title": fill(c["title"]), "lines": [fill(x) for x in c.get("lines", [])]} for c in spec.get("cards", [])]
        if spec.get("layout") == "cover":
            slide = layout.cover_slide(prs, title, message, fill(spec.get("kicker", "")), footer)
            if tiles_cards:
                left = Inches(5.9)
                layout.cards(slide, tiles_cards, left, Inches(4.45), layout.WIDTH - left - layout.MARGIN, Inches(2.2))
            layout.notes(slide, fill(spec.get("notes", "")))
            continue
        slide = layout.frame_slide(prs, title, message, page, len(slides), footer)
        bullets = _fill_tree(spec.get("bullets"), table, used)
        visual = spec.get("figure")
        grid = spec.get("table")
        top, bottom = layout.BODY_TOP, layout.BODY_BOTTOM
        if tiles or tiles_cards:  # a band of stat tiles or cards, full width
            draw = layout.stat_tiles if tiles else layout.cards
            alone = not (bullets or visual or grid)
            band_h = min(bottom - top, Inches(3.6)) if alone else (Inches(1.35) if tiles else Inches(2.2))
            x, _, w, _ = layout.body_box()
            if spec.get("band_position") == "top" or alone:
                draw(slide, tiles or tiles_cards, x, top, w, band_h)
                top += band_h + layout.GAP
            else:
                draw(slide, tiles or tiles_cards, x, bottom - band_h, w, band_h)
                bottom -= band_h + layout.GAP
        if bullets and visual and spec.get("figure_position") == "top":
            x, y, w, h = layout.body_box(top=top, bottom=bottom)
            region = (x, y, w, int(h * 0.5))
            layout.check_list(slide, bullets, x, y + int(h * 0.54), w, int(h * 0.46))
        elif bullets and (visual or grid):
            left, right = layout.body_box(split="right", top=top, bottom=bottom)
            layout.check_list(slide, bullets, *left)
            region = right
        elif bullets:
            layout.check_list(slide, bullets, *layout.body_box(top=top, bottom=bottom))
            region = None
        elif visual or grid:
            region = layout.body_box(top=top, bottom=bottom)
        else:
            region = None
        if visual and region is not None:
            path = figures.render(visual, fig_dir, {k: v.value for k, v in table.items()}, assets_dir)
            layout.picture(slide, path, *region)
        elif grid and region is not None:
            x, y, w, _ = region
            header, rows = _table_rows(grid, table, used)
            layout.table(slide, header, rows, x, y, w, grid.get("highlight_row"), grid.get("widths"))
        layout.notes(slide, fill(spec.get("notes", "")))

    out_dir.mkdir(parents=True, exist_ok=True)
    pptx_path = out_dir / "deck.pptx"
    prs.save(pptx_path)
    pdf_path = to_pdf(pptx_path) if pdf else None
    return DeckResult(pptx_path, pdf_path, len(slides), numbers.fallback_numbers(table, used, deck.get("numbers", {})))


def to_pdf(pptx_path: Path) -> Optional[Path]:
    """Convert with LibreOffice if it is installed; None otherwise."""
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice is None:
        return None
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(pptx_path.parent), str(pptx_path)],
                   check=True, capture_output=True, timeout=300)
    pdf = pptx_path.with_suffix(".pdf")
    return pdf if pdf.exists() else None
