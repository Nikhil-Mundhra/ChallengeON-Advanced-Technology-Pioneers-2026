"""Background art: a faint square grid and a flight-route motif (dotted arcs converging on Abu Dhabi
with small vector planes), drawn with matplotlib as transparent full-slide PNG bytes.

All geometry is fixed in theme.py (no randomness), so builds are reproducible. Any art pixel that
falls inside a text box is capped at theme.ART_OPACITY_UNDER_TEXT, so text always stays readable.
Nothing here writes files; the build places the bytes behind each slide's content.
"""

from __future__ import annotations

import math
from functools import lru_cache
from io import BytesIO
from typing import Iterable, List, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Polygon
from PIL import Image

from tourism_twin.reporting.deck import theme
from tourism_twin.reporting.deck.grid import Box

# Plane silhouette pointing along +x, length 1, centred on the origin (upper half; mirrored below).
_PLANE_UPPER = [(0.50, 0.00), (0.45, 0.035), (0.30, 0.055), (0.08, 0.06), (-0.12, 0.42), (-0.21, 0.42),
                (-0.09, 0.06), (-0.31, 0.05), (-0.41, 0.19), (-0.48, 0.19), (-0.44, 0.035), (-0.50, 0.00)]
PLANE = _PLANE_UPPER + [(x, -y) for x, y in reversed(_PLANE_UPPER[1:-1])]


def _rgb(color: str) -> Tuple[float, float, float]:
    return theme.hex_rgb(color)


def _canvas(w: float = theme.SLIDE_W, h: float = theme.SLIDE_H):
    fig = plt.figure(figsize=(w, h), dpi=theme.DPI)
    fig.patch.set_alpha(0)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.patch.set_alpha(0)
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)          # slide coordinates: inches from the top-left corner
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def _png(fig, clear: Iterable[Box] = ()) -> bytes:
    """Rasterise; cap the opacity of pixels inside the `clear` boxes."""
    fig.canvas.draw()
    pixels = np.asarray(fig.canvas.buffer_rgba()).copy()
    plt.close(fig)
    scale = pixels.shape[1] / theme.SLIDE_W
    cap = int(255 * theme.ART_OPACITY_UNDER_TEXT)
    for box in clear:
        x0, x1 = max(0, int(box.x * scale)), int(math.ceil(box.right * scale))
        y0, y1 = max(0, int(box.y * scale)), int(math.ceil(box.bottom * scale))
        alpha = pixels[y0:y1, x0:x1, 3]
        np.minimum(alpha, cap, out=alpha)
    buffer = BytesIO()
    Image.fromarray(pixels, "RGBA").save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


@lru_cache(maxsize=None)
def grid(tone: str) -> bytes:
    """The background square grid, aligned to the left margin and to the top edge."""
    color = theme.INK if tone == "light" else theme.ON_DARK
    fig, ax = _canvas()
    x = theme.MARGIN % theme.CELL
    while x < theme.SLIDE_W:
        ax.plot([x, x], [0, theme.SLIDE_H], color=_rgb(color), alpha=theme.GRID_OPACITY, linewidth=theme.GRID_LINE_PT)
        x += theme.CELL
    y = theme.CELL
    while y < theme.SLIDE_H:
        ax.plot([0, theme.SLIDE_W], [y, y], color=_rgb(color), alpha=theme.GRID_OPACITY, linewidth=theme.GRID_LINE_PT)
        y += theme.CELL
    return _png(fig)


def _arc(origin: Tuple[float, float], hub: Tuple[float, float], bend: float, n: int = 120) -> np.ndarray:
    """Quadratic Bézier from `origin` to `hub`, bowed sideways by `bend` × its length."""
    (x0, y0), (x1, y1) = origin, hub
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    cx, cy = (x0 + x1) / 2 - dy / length * bend * length, (y0 + y1) / 2 + dx / length * bend * length
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 2 * np.array([x0, y0]) + 2 * (1 - t) * t * np.array([cx, cy]) + t ** 2 * np.array([x1, y1])


def _plane(ax, at: Tuple[float, float], heading: float, size: float, color: str, alpha: float) -> None:
    c, s = math.cos(heading), math.sin(heading)
    points = [(at[0] + size * (x * c - y * s), at[1] + size * (x * s + y * c)) for x, y in PLANE]
    ax.add_patch(Polygon(points, closed=True, facecolor=_rgb(color), edgecolor="none", alpha=alpha))


def routes(tone: str, clear: Sequence[Box] = (), corner: bool = True) -> bytes:
    """Dotted arcs from off-slide origins into the hub, planes riding some of them. Light slides:
    a faint top-right corner version; dark slides: bold, in the corner or (`corner=False`, the
    cover) across the right half."""
    layout = theme.ART_LIGHT if tone == "light" else (theme.ART_DARK_CORNER if corner else theme.ART_DARK)
    if tone == "light":
        line_colors = [(theme.INK, theme.ART_OPACITY_LIGHT)]
        plane_color, hub_alpha = (theme.ACCENT, theme.ART_OPACITY_LIGHT), theme.ART_OPACITY_LIGHT
    else:
        white, accent = theme.ART_OPACITY_DARK
        line_colors = [(theme.ON_DARK, white), (theme.ACCENT_ON_DARK, accent)]
        plane_color, hub_alpha = (theme.ACCENT_ON_DARK, accent), accent
    hub = layout["hub"]
    fig, ax = _canvas()
    for i, (ox, oy, bend) in enumerate(layout["origins"]):
        path = _arc((ox, oy), hub, bend)
        color, alpha = line_colors[i % len(line_colors)]
        ax.plot(path[:, 0], path[:, 1], color=_rgb(color), alpha=alpha, linewidth=theme.ART_LINE_PT,
                linestyle=(0, (0.1, 2.6)), dash_capstyle="round", solid_capstyle="round")
        if i < len(layout["plane_at"]):
            k = int(layout["plane_at"][i] * (len(path) - 1))
            heading = math.atan2(path[k + 1, 1] - path[k - 1, 1], path[k + 1, 0] - path[k - 1, 0])
            _plane(ax, tuple(path[k]), heading, theme.ART_PLANE, *plane_color)
    for radius, fill in zip(theme.ART_HUB, (False, True)):
        ax.add_patch(Circle(hub, radius, facecolor=_rgb(plane_color[0]) if fill else "none",
                            edgecolor=_rgb(plane_color[0]), linewidth=theme.HUB_LINE_PT, alpha=hub_alpha))
    return _png(fig, clear)


@lru_cache(maxsize=None)
def light_routes() -> bytes:
    return routes("light")


@lru_cache(maxsize=None)
def plane_icon(color: str = theme.ACCENT) -> bytes:
    """A small plane pointing right, for the kicker."""
    fig = plt.figure(figsize=(theme.ICON, theme.ICON), dpi=theme.DPI * 2)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(-0.55, 0.55)
    ax.set_ylim(-0.55, 0.55)
    ax.set_aspect("equal")
    ax.axis("off")
    _plane(ax, (0, 0), 0.0, 1.0, color, 1.0)
    buffer = BytesIO()
    fig.savefig(buffer, format="png", transparent=True)
    plt.close(fig)
    return buffer.getvalue()


def layers(tone: str, clear: Sequence[Box], cover: bool = False) -> List[Tuple[str, bytes]]:
    """(shape name, PNG) for a slide's background, back to front."""
    art = light_routes() if tone == "light" else routes(tone, clear, corner=not cover)
    return [("bg.grid", grid(tone)), ("bg.routes", art)]
