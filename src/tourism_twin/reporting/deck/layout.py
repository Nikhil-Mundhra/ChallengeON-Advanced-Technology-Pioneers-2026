"""Slide primitives on python-pptx: one clean 16:9 family in the deck theme (theme.py).

Content slides share one frame: a heavy title top-left with a green bar beside it, a one-line
message, a small green/red corner mark, and a footer. Bodies are composed from: check-icon lists
(a parent line with its short detail lines), figures, tables, stat tiles (a big number and a
label) and cards (a heading and a few lines on a solid tile). The cover has its own layout.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

from tourism_twin.reporting.deck.theme import FONT, GREEN, GREEN_DARK, GREEN_LIGHT, GREY, INK, RED, SAND, WHITE

WIDTH, HEIGHT = Inches(13.333), Inches(7.5)
MARGIN = Inches(0.7)
BODY_TOP = Inches(1.85)
BODY_BOTTOM = HEIGHT - Inches(0.65)
GAP = Inches(0.3)
TONES = {"green": GREEN, "dark": GREEN_DARK, "red": RED, "sand": SAND}


def rgb(hex_color: str) -> RGBColor:
    return RGBColor.from_string(hex_color.lstrip("#"))


def new_presentation() -> Presentation:
    prs = Presentation()
    prs.slide_width, prs.slide_height = WIDTH, HEIGHT
    return prs


def _shape(slide, kind, left, top, width, height, fill: str, rotation: float = 0.0):
    shape = slide.shapes.add_shape(kind, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(fill)
    shape.line.fill.background()
    shape.shadow.inherit = False
    shape.rotation = rotation
    return shape


def _run(paragraph, text: str, size: float, color: str, bold: bool = False, heavy: bool = False) -> None:
    run = paragraph.add_run()
    run.text = text
    run.font.size, run.font.bold = Pt(size), bold or heavy
    run.font.name = FONT
    run.font.color.rgb = rgb(color)


def _text(frame, text: str, size: float, color: str, bold: bool = False, align=PP_ALIGN.LEFT,
          heavy: bool = False, anchor=MSO_ANCHOR.TOP) -> None:
    frame.word_wrap = True
    frame.vertical_anchor = anchor
    frame.margin_left = frame.margin_right = Inches(0.05)
    paragraph = frame.paragraphs[0]
    paragraph.alignment = align
    _run(paragraph, text, size, color, bold, heavy)


def _box(slide, left, top, width, height, text: str, size: float, color: str, **kw):
    box = slide.shapes.add_textbox(left, top, width, height)
    _text(box.text_frame, text, size, color, **kw)
    return box


def _lines(text: str, size: float, width: Emu) -> int:
    """Rough wrapped line count: Open Sans averages about 0.55 em per character."""
    per_line = max(1, int(width / 914400 * 72 / (size * 0.55)))
    return max(1, -(-len(text) // per_line))


def frame_slide(prs: Presentation, title: str, message: str, page: int, total: int, footer: str):
    """A blank slide with the shared frame; returns the slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    _shape(slide, MSO_SHAPE.RECTANGLE, MARGIN - Inches(0.25), Inches(0.42), Inches(0.09), Inches(0.62), GREEN)
    _box(slide, MARGIN, Inches(0.32), WIDTH - 2 * MARGIN - Inches(1.2), Inches(0.8), title, 30, GREEN_DARK, heavy=True)
    if message:
        _box(slide, MARGIN, Inches(1.1), WIDTH - 2 * MARGIN - Inches(0.6), Inches(0.6), message, 16, GREY)
    _shape(slide, MSO_SHAPE.RIGHT_TRIANGLE, WIDTH - Inches(1.1), 0, Inches(1.1), Inches(1.1), GREEN, rotation=180)
    _shape(slide, MSO_SHAPE.RIGHT_TRIANGLE, WIDTH - Inches(0.55), 0, Inches(0.55), Inches(0.55), RED, rotation=180)
    _box(slide, MARGIN, HEIGHT - Inches(0.45), WIDTH - 2 * MARGIN, Inches(0.3), footer, 9, GREY)
    _box(slide, WIDTH - MARGIN - Inches(1.0), HEIGHT - Inches(0.45), Inches(1.0), Inches(0.3), f"{page:02d} / {total:02d}", 9,
         GREY, align=PP_ALIGN.RIGHT)
    return slide


def cover_slide(prs: Presentation, title: str, message: str, kicker: str, footer: str):
    """Title slide: layered triangles on the left, a heavy title on the right."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _shape(slide, MSO_SHAPE.RIGHT_TRIANGLE, 0, 0, Inches(5.6), HEIGHT, GREEN_DARK)
    _shape(slide, MSO_SHAPE.ISOSCELES_TRIANGLE, Inches(1.2), Inches(1.9), Inches(3.2), Inches(2.6), GREEN, rotation=90)
    _shape(slide, MSO_SHAPE.ISOSCELES_TRIANGLE, Inches(0.2), Inches(0.35), Inches(1.0), Inches(0.8), RED, rotation=90)
    _shape(slide, MSO_SHAPE.RIGHT_TRIANGLE, WIDTH - Inches(1.6), 0, Inches(1.6), Inches(1.6), SAND, rotation=180)
    left = Inches(5.9)
    width = WIDTH - left - MARGIN
    _box(slide, left, Inches(0.9), width, Inches(0.5), kicker, 18, RED, bold=True, align=PP_ALIGN.RIGHT)
    _box(slide, left, Inches(1.35), width, Inches(1.9), title, 44, GREEN_DARK, heavy=True, align=PP_ALIGN.RIGHT)
    _box(slide, left + Inches(1.2), Inches(3.35), width - Inches(1.2), Inches(0.9), message, 15, INK, align=PP_ALIGN.RIGHT)
    _box(slide, left, HEIGHT - Inches(0.6), width, Inches(0.3), footer, 9, GREY, align=PP_ALIGN.RIGHT)
    return slide


def _flatten(nodes, prefix: str = "") -> List[str]:
    """Detail lines in order; a grandchild line is prefixed with '· '."""
    out: List[str] = []
    for node in nodes:
        text, children = (node, []) if isinstance(node, str) else (node["text"], node.get("children", []))
        out.append(prefix + text)
        out.extend(_flatten(children, "·  "))
    return out


def check_list(slide, items: Sequence[Dict[str, Any] | str], left: Emu, top: Emu, width: Emu, height: Emu) -> None:
    """Each top item: a green check disc and a bold line; its children as short grey lines under it."""
    icon, indent = Inches(0.34), Inches(0.52)
    y = top
    for node in items:
        text, children = (node, []) if isinstance(node, str) else (node["text"], node.get("children", []))
        disc = _shape(slide, MSO_SHAPE.OVAL, left, y + Inches(0.04), icon, icon, GREEN)
        _text(disc.text_frame, "✓", 12, WHITE, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        disc.text_frame.margin_top = disc.text_frame.margin_bottom = 0
        head_h = Inches(0.36) * _lines(text, 17, width - indent)
        _box(slide, left + indent, y, width - indent, head_h, text, 17, INK, bold=True)
        y += head_h
        for child_text in _flatten(children):
            child_h = Inches(0.29) * _lines(child_text, 14, width - indent)
            _box(slide, left + indent, y, width - indent, child_h, child_text, 14, GREY)
            y += child_h
        y += Inches(0.2)
    if y - Inches(0.2) > top + height:
        raise ValueError(f"List overflows its region by {(y - Inches(0.2) - top - height) / 914400:.2f} in: shorten it")


def stat_tiles(slide, stats: Sequence[Dict[str, str]], left: Emu, top: Emu, width: Emu, height: Emu) -> None:
    """A row of tiles: a big number over a short label; tone green (default), dark, red or sand."""
    n = len(stats)
    w = int((width - GAP * (n - 1)) / n)
    for i, stat in enumerate(stats):
        tone = TONES[stat.get("tone", "green")]
        ink = INK if tone == SAND else WHITE
        x = left + i * (w + GAP)
        _shape(slide, MSO_SHAPE.RECTANGLE, x, top, w, height, tone)
        _box(slide, x + Inches(0.2), top + Inches(0.1), w - Inches(0.4), int(height * 0.52), stat["value"], 30, ink,
             heavy=True, anchor=MSO_ANCHOR.BOTTOM)
        _box(slide, x + Inches(0.2), top + int(height * 0.6), w - Inches(0.4), int(height * 0.38), stat["label"], 12.5, ink)


def cards(slide, items: Sequence[Dict[str, Any]], left: Emu, top: Emu, width: Emu, height: Emu) -> None:
    """Solid tiles in a row: a heading and a few short lines each; tone as in stat_tiles."""
    n = len(items)
    w = int((width - GAP * (n - 1)) / n)
    for i, card in enumerate(items):
        tone = TONES[card.get("tone", "green")]
        ink = INK if tone == SAND else WHITE
        x = left + i * (w + GAP)
        _shape(slide, MSO_SHAPE.RECTANGLE, x, top, w, height, tone)
        _shape(slide, MSO_SHAPE.RECTANGLE, x, top, w, Inches(0.07), RED if tone != RED else GREEN_DARK)
        box = slide.shapes.add_textbox(x + Inches(0.22), top + Inches(0.22), w - Inches(0.44), height - Inches(0.35))
        frame = box.text_frame
        _text(frame, card["title"], 17, ink, bold=True)
        for line in card.get("lines", []):
            paragraph = frame.add_paragraph()
            paragraph.space_before = Pt(7)
            _run(paragraph, line, 13, ink)


def picture(slide, path: Path, left: Emu, top: Emu, width: Emu, height: Emu) -> None:
    """Fit the image inside the box, keeping its aspect ratio, centred."""
    from PIL import Image

    with Image.open(path) as image:
        ratio = image.width / image.height
    box_ratio = width / height
    w, h = (width, int(width / ratio)) if ratio > box_ratio else (int(height * ratio), height)
    slide.shapes.add_picture(str(path), left + (width - w) // 2, top + (height - h) // 2, w, h)


def table(slide, header: List[str], rows: List[List[str]], left: Emu, top: Emu, width: Emu,
          highlight_row: Optional[int] = None, widths: Optional[Sequence[float]] = None) -> None:
    """Dark-green header, sand banding, no borders; `widths` are column fractions."""
    shape = slide.shapes.add_table(len(rows) + 1, len(header), left, top, width, Inches(0.5) * (len(rows) + 1))
    grid = shape.table
    grid.first_row = False
    grid.horz_banding = False
    if widths:
        for col, fraction in enumerate(widths):
            grid.columns[col].width = int(width * fraction)
    for col, label in enumerate(header):
        cell = grid.cell(0, col)
        cell.fill.solid()
        cell.fill.fore_color.rgb = rgb(GREEN_DARK)
        cell.text_frame.text = ""
        _text(cell.text_frame, label, 14, WHITE, bold=True)
    for r, row in enumerate(rows, start=1):
        highlighted = r - 1 == highlight_row
        for col, value in enumerate(row):
            cell = grid.cell(r, col)
            cell.fill.solid()
            cell.fill.fore_color.rgb = rgb(GREEN_LIGHT if highlighted else (SAND if r % 2 == 0 else WHITE))
            cell.text_frame.text = ""
            _text(cell.text_frame, value, 13.5, GREEN_DARK if highlighted else INK, bold=highlighted or col == 0)


def notes(slide, text: str) -> None:
    if text:
        slide.notes_slide.notes_text_frame.text = text


def body_box(split: Optional[str] = None, top: Emu = BODY_TOP, bottom: Emu = BODY_BOTTOM):
    """Body regions: full width, or (left, right) for a list beside a figure or table."""
    width = WIDTH - 2 * MARGIN
    height = bottom - top
    if split is None:
        return (MARGIN, top, width, height)
    left_w = int(width * 0.44)
    return (MARGIN, top, left_w, height), (MARGIN + left_w + GAP, top, width - left_w - GAP, height)
