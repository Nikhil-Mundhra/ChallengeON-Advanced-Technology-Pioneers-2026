"""Layout geometry: every box on every slide comes from these functions and the tokens in theme.py.

A 12-column grid with a fixed gutter spans the content width between the two margins; vertical
positions sit on a rhythm of half a background cell. Equal elements (numbered columns, stat
columns, flow boxes, side panels) take their boxes from the same calls, so they share sizes and
positions on every slide. Units: inches.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Sequence, Tuple

from tourism_twin.reporting.deck import theme

CONTENT_W = theme.SLIDE_W - 2 * theme.MARGIN
COLUMN_W = (CONTENT_W - (theme.COLUMNS - 1) * theme.GUTTER) / theme.COLUMNS
SIDE_COLUMNS = 4          # a side panel (hero, table, chart) spans the last 4 grid columns


@dataclass(frozen=True)
class Box:
    x: float
    y: float
    w: float
    h: float

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def bottom(self) -> float:
        return self.y + self.h

    def below(self, y: float, h: float | None = None) -> "Box":
        """Same columns, starting at `y` (to the bottom of this box unless `h` is given)."""
        return Box(self.x, y, self.w, self.bottom - y if h is None else h)


def line_height(size_pt: float, leading: float) -> float:
    return size_pt * leading / 72


def snap(y: float) -> float:
    """The next rhythm line at or below `y`."""
    return math.ceil(round(y / theme.RHYTHM, 6)) * theme.RHYTHM


def span(first: int, count: int) -> Tuple[float, float]:
    """(x, width) of `count` grid columns starting at column `first` (1-based)."""
    x = theme.MARGIN + (first - 1) * (COLUMN_W + theme.GUTTER)
    return x, count * COLUMN_W + (count - 1) * theme.GUTTER


def columns(n: int, top: float, height: float, gap: float = theme.GUTTER, x: float = theme.MARGIN,
            width: float = CONTENT_W) -> List[Box]:
    """`n` equal boxes across `width`; with the default gap they sit exactly on the 12-column grid
    when n divides 12."""
    w = (width - (n - 1) * gap) / n
    return [Box(x + i * (w + gap), top, w, height) for i in range(n)]


def stack(top: float, heights: Sequence[float], gap: float) -> List[float]:
    """Tops of blocks laid one under another with a fixed gap."""
    tops, y = [], top
    for h in heights:
        tops.append(y)
        y += h + gap
    return tops


def body_region(top: float) -> Box:
    """Full content width from `top` to the body bottom."""
    return Box(theme.MARGIN, top, CONTENT_W, theme.BODY_BOTTOM - top)


def main_and_side(region: Box) -> Tuple[Box, float, Box]:
    """Split a body region into a main box, the x of the dividing hairline (centred in the gutter
    before the side panel) and the side panel."""
    main_cols = theme.COLUMNS - SIDE_COLUMNS
    x, w = span(1, main_cols - 1)
    side_x, side_w = span(main_cols + 1, SIDE_COLUMNS)
    rule_x = side_x - theme.GUTTER - COLUMN_W / 2
    return Box(x, region.y, w, region.h), rule_x, Box(side_x, region.y, side_w, region.h)


def header(title_lines: int, subtitle_lines: int, title_pt: float = theme.TITLE,
           title_y: float = theme.TITLE_Y) -> Tuple[Box, Box, Box]:
    """Kicker, title and subtitle boxes: the kicker half a rhythm step above the title, the subtitle
    directly under the title's measured lines."""
    kicker = Box(theme.MARGIN, theme.KICKER_Y, CONTENT_W, line_height(theme.KICKER, theme.SNUG))
    title = Box(theme.MARGIN, title_y, CONTENT_W, title_lines * line_height(title_pt, theme.TIGHT))
    sub_y = title.bottom + theme.SUBTITLE_GAP
    subtitle = Box(theme.MARGIN, sub_y, CONTENT_W, subtitle_lines * line_height(theme.SUBTITLE, theme.SNUG))
    return kicker, title, subtitle


def body_top(subtitle_bottoms: Sequence[float]) -> float:
    """One body top for every content slide: one rhythm step under the lowest subtitle, snapped."""
    return snap(max(subtitle_bottoms) + theme.RHYTHM)
