"""Presentation deck: report/deck/deck.yaml (content) → output/deck/deck.pptx (+ deck.pdf).

Teammates edit only the YAML: slide titles, one-line messages, bullet trees (parent → children),
figure and table names, speaker notes. Numbers are `{name}` placeholders filled from artifacts
(numbers.py); figures come from figures.py; layout from layout.py.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from tourism_twin.config import SETTINGS
from tourism_twin.reporting.deck import figures, layout, numbers

DEFAULT_CONTENT = SETTINGS.root / "report" / "deck" / "deck.yaml"


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
    for page, spec in enumerate(slides, start=1):
        title = numbers.fill(spec["title"], table, used)
        message = numbers.fill(spec.get("message", ""), table, used)
        slide = layout.frame_slide(prs, title, message, page, len(slides), deck.get("footer", ""))
        bullets = _fill_tree(spec.get("bullets"), table, used)
        visual = spec.get("figure")
        grid = spec.get("table")
        if bullets and visual and spec.get("figure_position") == "top":
            x, y, w, h = layout.body_box()
            region = (x, y, w, int(h * 0.48))
            layout.bullet_tree(slide, bullets, x, y + int(h * 0.52), w, int(h * 0.48))
        elif bullets and (visual or grid):
            left, right = layout.body_box(split="right")
            layout.bullet_tree(slide, bullets, *left)
            region = right
        elif bullets:
            layout.bullet_tree(slide, bullets, *layout.body_box())
            region = None
        else:
            region = layout.body_box()
        if visual and region is not None:
            path = figures.render(visual, fig_dir, {k: v.value for k, v in table.items()}, assets_dir)
            if grid:  # figure on top, table below
                x, y, w, h = region
                layout.picture(slide, path, x, y, w, int(h * 0.55))
                header, rows = _table_rows(grid, table, used)
                layout.table(slide, header, rows, x, y + int(h * 0.58), w, grid.get("highlight_row"))
            else:
                layout.picture(slide, path, *region)
        elif grid and region is not None:
            x, y, w, _ = region
            header, rows = _table_rows(grid, table, used)
            layout.table(slide, header, rows, x, y, w, grid.get("highlight_row"))
        layout.notes(slide, numbers.fill(spec.get("notes", ""), table, used))

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
