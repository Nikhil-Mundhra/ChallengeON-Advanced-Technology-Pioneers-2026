"""Deck design tokens: the only place that sets a colour, font, type size, spacing or grid ratio.

Light content slides between a dark navy cover and closing slide. One accent (teal) for numbers,
the subtitle, icons and connectors; no accent bars, no shadows. Every length is in inches and
derived from the slide width through the ratios below (measured on the ChallengeON hero image);
grid.py turns them into boxes. Deck only: the PDF reports keep reporting/palette.py.
"""

from __future__ import annotations

from tourism_twin.config import SETTINGS

# Colours (hex, no '#')
BACKGROUND = "FAF8F3"
INK = "152C3A"          # titles, heads; the dark slide background
ACCENT = "007E80"       # numbers, subtitles, icons, connectors
MUTED = "62717A"        # body, labels, footer
HAIRLINE = "D8DEDC"
CARD = "FFFFFF"
ON_DARK = "FFFFFF"            # text on the dark slides
MUTED_ON_DARK = "B4C2C9"
ACCENT_ON_DARK = "5CC4BF"     # the accent lifted for contrast on INK
HAIRLINE_ON_DARK = "33505F"

# Font (files and licence in meta/deck/fonts/)
FONT = "Open Sans"
FONT_DIR = SETTINGS.root / "meta" / "deck" / "fonts"
FONT_FILES = {"regular": "OpenSans-Regular.ttf", "semibold": "OpenSans-SemiBold.ttf", "bold": "OpenSans-Bold.ttf"}

# Type scale (pt)
HERO = 82
COVER_TITLE = 58
STAT = 44
TITLE = 38
COLUMN_NUMBER = 32
COLUMN_HEAD = 24
SUBTITLE = 20
HERO_LABEL = 24
ROW_HEAD = 20
SIDE = 20
BODY = 18
BODY_SMALL = 17
ROW_NUMBER = 16
FLOW_HEAD = 17
FLOW_DETAIL = 13
KICKER = round(0.45 * TITLE)   # muted label above the title
LABEL = 11                     # small caps labels (table header, flow row labels)
FOOTNOTE = 11
FOOTER = 9

# Line spacing (multiple of the font size)
TIGHT = 1.12      # titles, big numbers
SNUG = 1.3        # subtitles, heads
BODY_LEADING = 1.5

# Slide and grid (ratios of the slide width, from the reference image)
SLIDE_W = 13.333
SLIDE_H = 7.5
MARGIN = round(0.062 * SLIDE_W, 3)        # left and right edge of every text block
CELL = round(0.081 * SLIDE_W, 3)          # background square grid
RHYTHM = CELL / 2                         # vertical rhythm: block tops sit on half cells
COLUMNS = 12
GUTTER = 0.25
FLOW_GAP = 0.35                           # gap between flow boxes (holds the arrow)
PAD = 0.14                                # inner padding of cards and flow boxes
GAP_S = 0.12                              # between a block and its hairline or caption
GAP_M = 0.25                              # between blocks inside one element
ARROW_INSET = 0.05                        # space between a flow box and its arrow
STAT_TEXT_LINES = 2                       # max lines of a stat label or caption
FLOW_BOX_MIN = 0.9                        # minimum flow box height
SUBTITLE_GAP = 0.5 * SUBTITLE / 72        # subtitle sits this far under the title

# Vertical anchors (inches from the top)
KICKER_Y = RHYTHM
TITLE_Y = 2 * RHYTHM
FOOTER_RULE_Y = SLIDE_H - RHYTHM
FOOTER_TEXT_Y = FOOTER_RULE_Y + 0.13
FOOTNOTE_Y = FOOTER_RULE_Y - 0.4
BODY_BOTTOM = FOOTNOTE_Y - 0.15
COVER_TITLE_Y = 3 * RHYTHM

# Line weights (pt)
HAIRLINE_PT = 1.0
CONNECTOR_PT = 1.5
GRID_LINE_PT = 0.6
HUB_LINE_PT = 1.2

# Matplotlib (figures and background art)
DPI = 192
CHART_LABEL = 16
CHART_VALUE = 14
BAR_HEIGHT = 0.56                         # share of a bar's slot
MUTED_BAR_OPACITY = 0.35                  # bars after the highlighted ones
GRID_OPACITY = 0.07
ART_OPACITY_LIGHT = 0.1
ART_OPACITY_DARK = (0.28, 0.4)            # (white, accent)
ART_OPACITY_UNDER_TEXT = 0.1              # cap for any art pixel under a text box
ICON = 0.22                               # plane icon next to the kicker
ART_LINE_PT = 1.6                         # dotted route arcs
ART_PLANE = 0.32                          # plane length on the route arcs
ART_HUB = (0.16, 0.06)                    # hub ring and dot radius
# Route art: arcs from off-slide origins to the hub (Abu Dhabi); (x, y, bend) with bend the arc's
# sideways bow as a share of its length; planes ride the arcs at the listed positions (0..1).
ART_LIGHT = {"hub": (12.15, 0.72), "plane_at": (0.55, 0.62),
             "origins": [(14.2, -0.9, 0.18), (14.6, 1.9, -0.16), (10.3, -1.0, -0.2), (13.9, 3.0, 0.12)]}
ART_DARK_CORNER = ART_LIGHT                # dark slides other than the cover keep the art in the corner
ART_DARK = {"hub": (10.35, 4.75), "plane_at": (0.5, 0.42, 0.6),
            "origins": [(14.6, 0.4, 0.22), (14.8, 3.6, -0.14), (14.2, 8.6, 0.18), (9.2, 8.9, -0.22),
                        (6.8, 8.9, 0.2), (14.9, 6.4, -0.1)]}


def hex_rgb(color: str) -> tuple[float, float, float]:
    """'152C3A' → (r, g, b) in 0..1 for matplotlib."""
    return tuple(int(color[i:i + 2], 16) / 255 for i in (0, 2, 4))  # type: ignore[return-value]
