"""Presentation deck: meta/deck/deck.yaml (content) → output/deck/deck.pptx (+ deck.pdf, previews).

`build_deck` is the one entry point: it loads the YAML, collects the numbers (numbers.py), checks
the content rules, lays out the shared header, renders each slide by its `type` (slides/), puts the
background art behind it (art.py), adds speaker notes, then exports. Geometry comes from grid.py,
every colour, size and spacing from theme.py; renderers never write files.

The build fails when: the deck does not have 10 slides; a hero or stat value is not a `{name}`
placeholder (typed result numbers); a placeholder is unknown; any text overflows its box.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import yaml

from tourism_twin.config import SETTINGS
from tourism_twin.reporting.deck import art, canvas, grid, numbers, theme, typeset
from tourism_twin.reporting.deck.grid import Box
from tourism_twin.reporting.deck.slides import Frame, renderer

DEFAULT_CONTENT = SETTINGS.root / "meta" / "deck" / "deck.yaml"
SLIDE_COUNT = 10
SOFFICE_PATHS = [Path("/opt/homebrew/bin/soffice"), Path("/usr/local/bin/soffice"),
                 Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")]
NOT_TEXT = {"type", "tone", "figure", "scenario", "widths", "highlight_row"}   # spec keys never filled


@dataclass
class DeckResult:
    pptx: Path
    pdf: Optional[Path]
    previews: List[Path]
    slides: int
    fallback_numbers: List[str]


class DeckContentError(ValueError):
    """deck.yaml breaks a content rule."""


def _result_values(spec: Dict[str, Any]) -> List[str]:
    """The values that must come from placeholders: hero and stat numbers."""
    out = [spec["hero"]["value"]] if "hero" in spec else []
    return out + [s["value"] for s in spec.get("stats", [])]


def check_content(deck: Dict[str, Any]) -> None:
    slides = deck["slides"]
    if len(slides) != SLIDE_COUNT:
        raise DeckContentError(f"the deck has {len(slides)} slides; it must have {SLIDE_COUNT}")
    for page, spec in enumerate(slides, start=1):
        for value in _result_values(spec):
            typed = numbers.PLACEHOLDER.sub("", value)
            if not numbers.PLACEHOLDER.search(value) or any(ch.isdigit() for ch in typed):
                raise DeckContentError(f"slide {page}: {value!r} must be a {{name}} placeholder, not a typed number")


def _fill(node: Any, fill: Callable[[str], str]) -> Any:
    if isinstance(node, str):
        return fill(node)
    if isinstance(node, list):
        return [_fill(item, fill) for item in node]
    if isinstance(node, dict):
        return {k: (v if k in NOT_TEXT else _fill(v, fill)) for k, v in node.items()}
    return node


def _tone(spec: Dict[str, Any]) -> str:
    return "dark" if spec["type"] == "cover" or spec.get("tone") == "dark" else "light"


def _header_boxes(spec: Dict[str, Any]):
    title_lines = len(typeset.wrap(spec["title"], typeset.STYLES["title"], grid.CONTENT_W))
    subtitle_lines = len(typeset.wrap(spec["subtitle"], typeset.STYLES["subtitle"], grid.CONTENT_W))
    return grid.header(title_lines, subtitle_lines)


def _text_boxes(slide) -> List[Box]:
    emu = 914400
    return [Box(s.left / emu, s.top / emu, s.width / emu, s.height / emu)
            for s in slide.shapes if s.has_text_frame and s.text_frame.text.strip()]


def render(deck: Dict[str, Any], table: numbers.DeckNumbers):
    """The filled deck as a python-pptx Presentation (nothing written)."""
    check_content(deck)
    slides = [_fill(spec, table.fill) for spec in deck["slides"]]
    footer = table.fill(deck.get("footer", ""))
    content = [s for s in slides if s["type"] != "cover"]
    frame = Frame(grid.body_top([_header_boxes(s)[2].bottom for s in content]), table)
    prs = canvas.new_presentation()
    for page, spec in enumerate(slides, start=1):
        tone = _tone(spec)
        slide = canvas.new_slide(prs, tone)
        if spec["type"] != "cover":
            _, title, subtitle = _header_boxes(spec)
            canvas.text(slide, "title", title, spec["title"], "title")
            canvas.text(slide, "subtitle", subtitle, spec["subtitle"], "subtitle")
        icon = art.plane_icon(typeset.PALETTES[tone]["accent"])
        canvas.chrome(slide, spec.get("kicker"), footer, page, len(slides), icon)
        renderer(spec["type"])(slide, spec, frame)
        if spec.get("footnote"):
            style = typeset.STYLES["footnote"]
            box = Box(grid.body_region(0).x, theme.FOOTNOTE_Y, grid.CONTENT_W, style.line)
            canvas.text(slide, "footnote", box, spec["footnote"], style)
        page_box = Box(0, 0, theme.SLIDE_W, theme.SLIDE_H)
        art_layers = art.layers(tone, _text_boxes(slide), cover=spec["type"] == "cover")
        background = [canvas.fill(slide, "bg.fill", page_box)] + [
            canvas.picture(slide, name, png, page_box, fit_inside=False) for name, png in art_layers]
        canvas.send_to_back(slide, background)
        canvas.notes(slide, spec.get("notes", ""))
    return prs


def build_deck(content: Path = DEFAULT_CONTENT, out_dir: Optional[Path] = None, pdf: bool = True,
               previews: bool = False, validation_summary: Optional[Path] = None,
               planning_evaluation: Optional[Path] = None, outlook: Optional[Path] = None,
               deck_numbers: Optional[numbers.DeckNumbers] = None) -> DeckResult:
    """Build and export the deck. `deck_numbers` replaces the artifact numbers (tests)."""
    deck = yaml.safe_load(Path(content).read_text())
    table = deck_numbers or numbers.collect(deck, validation_summary or SETTINGS.output_dir / "validation_summary.json",
                                            planning_evaluation or SETTINGS.evaluation_results_path,
                                            outlook or SETTINGS.output_dir / "outlook.json")
    prs = render(deck, table)
    out_dir = Path(out_dir or SETTINGS.output_dir / "deck")
    pptx_path, pdf_path, preview_paths = export(prs, out_dir, pdf, previews)
    return DeckResult(pptx_path, pdf_path, preview_paths, len(prs.slides), table.fallbacks(deck.get("numbers", {})))


def export(prs, out_dir: Path, pdf: bool, previews: bool):
    """Write deck.pptx, and optionally deck.pdf (LibreOffice) and PNG previews (pdftoppm)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    pptx_path = out_dir / "deck.pptx"
    prs.save(pptx_path)
    pdf_path = to_pdf(pptx_path) if pdf or previews else None
    preview_paths = to_previews(pdf_path, out_dir / "previews") if previews and pdf_path else []
    return pptx_path, pdf_path, preview_paths


def to_pdf(pptx_path: Path) -> Optional[Path]:
    """Convert with LibreOffice if it is installed; None otherwise."""
    soffice = shutil.which("soffice") or shutil.which("libreoffice") or next(
        (str(p) for p in SOFFICE_PATHS if p.exists()), None)
    if soffice is None:
        return None
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(pptx_path.parent), str(pptx_path)],
                   check=True, capture_output=True, timeout=300)
    pdf = pptx_path.with_suffix(".pdf")
    return pdf if pdf.exists() else None


def to_previews(pdf_path: Path, out_dir: Path) -> List[Path]:
    """One PNG per slide (pdftoppm, from poppler); empty when it is not installed."""
    pdftoppm = shutil.which("pdftoppm")
    if pdftoppm is None:
        return []
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    subprocess.run([pdftoppm, "-png", "-r", "110", str(pdf_path), str(out_dir / "slide")], check=True, timeout=300)
    return sorted(out_dir.glob("slide-*.png"))
