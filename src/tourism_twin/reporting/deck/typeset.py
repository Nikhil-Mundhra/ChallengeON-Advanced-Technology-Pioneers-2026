"""Text styles, inline markup and measured line wrapping (no python-pptx here).

Markup in deck.yaml strings: `**text**` is bold in the strong colour (ink, white on dark slides),
`==text==` is bold in the accent colour. Wrapping measures each word with the real Open Sans
files, so the overflow check matches what PowerPoint and LibreOffice draw.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Tuple

from PIL import ImageFont

from tourism_twin.reporting.deck import theme

MARKUP = re.compile(r"(\*\*.+?\*\*|==.+?==)")
WRAP_SAFETY = 0.99      # wrap a hair early: PIL measures without kerning, so it already runs wide


class DeckOverflow(ValueError):
    """Text does not fit its box."""


@dataclass(frozen=True)
class Style:
    size: float
    weight: str = "regular"      # regular | semibold | bold
    role: str = "muted"          # colour role, see PALETTES
    leading: float = theme.SNUG
    align: str = "left"          # left | right | center
    caps: bool = False

    @property
    def line(self) -> float:
        return self.size * self.leading / 72


PALETTES: Dict[str, Dict[str, str]] = {
    "light": {"background": theme.BACKGROUND, "strong": theme.INK, "accent": theme.ACCENT, "muted": theme.MUTED,
              "hairline": theme.HAIRLINE, "card": theme.CARD},
    "dark": {"background": theme.INK, "strong": theme.ON_DARK, "accent": theme.ACCENT_ON_DARK,
             "muted": theme.MUTED_ON_DARK, "hairline": theme.HAIRLINE_ON_DARK, "card": theme.INK},
}

STYLES: Dict[str, Style] = {
    "kicker": Style(theme.KICKER, "semibold", "muted"),
    "title": Style(theme.TITLE, "bold", "strong", theme.TIGHT),
    "cover_title": Style(theme.COVER_TITLE, "bold", "strong", theme.TIGHT),
    "subtitle": Style(theme.SUBTITLE, "regular", "accent"),
    "cover_subtitle": Style(theme.HERO_LABEL, "regular", "muted"),
    "hero": Style(theme.HERO, "bold", "accent", theme.TIGHT),
    "hero_label": Style(theme.HERO_LABEL, "bold", "strong"),
    "stat": Style(theme.STAT, "bold", "accent", theme.TIGHT),
    "stat_label": Style(theme.BODY_SMALL, "regular", "muted"),
    "column_number": Style(theme.COLUMN_NUMBER, "bold", "accent", theme.TIGHT),
    "column_head": Style(theme.COLUMN_HEAD, "bold", "strong"),
    "row_number": Style(theme.ROW_NUMBER, "bold", "accent"),
    "row_head": Style(theme.ROW_HEAD, "bold", "strong"),
    "side": Style(theme.SIDE, "regular", "muted"),
    "body": Style(theme.BODY, "regular", "muted", theme.BODY_LEADING),
    "body_small": Style(theme.BODY_SMALL, "regular", "muted", theme.SNUG),
    "cell": Style(theme.BODY_SMALL, "regular", "strong", theme.SNUG),
    "flow_head": Style(theme.FLOW_HEAD, "bold", "strong", theme.SNUG, "center"),
    "flow_detail": Style(theme.FLOW_DETAIL, "regular", "muted", theme.SNUG, "center"),
    "label": Style(theme.LABEL, "bold", "muted", theme.SNUG, caps=True),
    "footnote": Style(theme.FOOTNOTE, "regular", "muted"),
    "footer": Style(theme.FOOTER, "regular", "muted"),
    "page": Style(theme.FOOTER, "regular", "muted", align="right"),
}


@dataclass(frozen=True)
class Run:
    text: str
    weight: str
    role: str


def parse(text: str, style: Style) -> List[Run]:
    """Split markup into runs; plain text keeps the style's weight and colour."""
    runs = []
    for part in MARKUP.split(text):
        if not part:
            continue
        if part.startswith("**"):
            runs.append(Run(part[2:-2], "bold", "strong"))
        elif part.startswith("=="):
            runs.append(Run(part[2:-2], "bold", "accent"))
        else:
            runs.append(Run(part, style.weight, style.role))
    return [Run(r.text.upper(), r.weight, r.role) for r in runs] if style.caps else runs


def plain(text: str) -> str:
    return MARKUP.sub(lambda m: m.group(0)[2:-2], text)


@lru_cache(maxsize=None)
def _font(weight: str) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(theme.FONT_DIR / theme.FONT_FILES[weight]), 1000)


def width(text: str, size: float, weight: str = "regular") -> float:
    """Advance width in inches."""
    return _font(weight).getlength(text) / 1000 * size / 72


def _words(runs: List[Run]) -> List[Tuple[str, str]]:
    """(word, weight) pairs, one per space-separated word; a word keeps its run's weight."""
    out: List[Tuple[str, str]] = []
    glue = False
    for run in runs:
        pieces = run.text.split(" ")
        for i, piece in enumerate(pieces):
            if i == 0 and glue and out and piece:
                out[-1] = (out[-1][0] + piece, out[-1][1] if run.weight == "regular" else run.weight)
            elif piece:
                out.append((piece, run.weight))
        glue = not run.text.endswith(" ")
    return out


def wrap(text: str, style: Style, box_w: float) -> List[str]:
    """Lines as drawn in a box `box_w` inches wide; explicit '\\n' starts a new line. Raises
    DeckOverflow when a single word is wider than the box."""
    limit = box_w * WRAP_SAFETY
    lines: List[str] = []
    for paragraph in text.split("\n"):
        line, line_w = "", 0.0
        for word, weight in _words(parse(paragraph, style)):
            w = width(word, style.size, weight)
            if w > limit:
                raise DeckOverflow(f"word {word!r} is wider than its {box_w:.2f} in box")
            space = width(" ", style.size) if line else 0.0
            if line and line_w + space + w > limit:
                lines.append(line)
                line, line_w = word, w
            else:
                line, line_w = (f"{line} {word}" if line else word), line_w + space + w
        lines.append(line)
    return lines


def height(text: str, style: Style, box_w: float) -> float:
    return len(wrap(text, style, box_w)) * style.line
