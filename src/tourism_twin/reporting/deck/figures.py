"""Deck charts drawn with matplotlib in the deck tokens; each returns PNG bytes sized to the box it
fills, so chart text prints at true point sizes. Nothing here writes files."""

from __future__ import annotations

from io import BytesIO
from typing import Any, Callable, Dict, List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

from tourism_twin.reporting.deck import theme
from tourism_twin.reporting.deck.numbers import DeckNumbers, lever_name

for _weight, _file in theme.FONT_FILES.items():
    font_manager.fontManager.addfont(str(theme.FONT_DIR / _file))
RC = {"font.family": "sans-serif", "font.sans-serif": [theme.FONT, "DejaVu Sans"], "svg.fonttype": "none"}
HIGHLIGHT = 2   # bars drawn in the accent colour; the rest muted


def png(fig) -> bytes:
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=theme.DPI, transparent=True)
    plt.close(fig)
    return buffer.getvalue()


def tornado(numbers: DeckNumbers, spec: Dict[str, Any], w: float, h: float) -> bytes:
    """How far weekly hotel nights move between each lever's low and high setting, largest first,
    around the scenario named in the slide's `scenario`."""
    rows: List[Dict[str, Any]] = sorted(numbers.reports[spec["scenario"]].tornado_sensitivity,
                                        key=lambda r: r["swing_spread"])
    labels = [lever_name(r)[0].upper() + lever_name(r)[1:] for r in rows]
    spreads = [r["swing_spread"] for r in rows]
    colors = ["#" + theme.MUTED] * (len(rows) - HIGHLIGHT) + ["#" + theme.ACCENT] * HIGHLIGHT
    with plt.rc_context(RC):
        fig, ax = plt.subplots(figsize=(w, h))
        bars = ax.barh(labels, spreads, color=colors, height=theme.BAR_HEIGHT, edgecolor="none")
        for bar in bars[:-HIGHLIGHT]:
            bar.set_alpha(theme.MUTED_BAR_OPACITY)
        for bar, value in zip(bars, spreads):
            ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2, f"  {value:,.0f}", va="center",
                    fontsize=theme.CHART_VALUE, color="#" + theme.INK)
        ax.set_xlim(0, max(spreads) * 1.18)
        ax.tick_params(axis="y", length=0, labelsize=theme.CHART_LABEL, labelcolor="#" + theme.INK, pad=8)
        ax.set_xticks([])
        for side in ("top", "right", "bottom"):
            ax.spines[side].set_visible(False)
        ax.spines["left"].set_color("#" + theme.HAIRLINE)
        ax.set_xlabel("Weekly hotel nights between the lever's low and high setting", fontsize=theme.FOOTNOTE,
                      color="#" + theme.MUTED, loc="left", labelpad=8)
        fig.tight_layout(pad=0.2)
        return png(fig)


FIGURES: Dict[str, Callable[[DeckNumbers, Dict[str, Any], float, float], bytes]] = {"tornado": tornado}


def render(name: str, numbers: DeckNumbers, spec: Dict[str, Any], w: float, h: float) -> bytes:
    if name not in FIGURES:
        raise KeyError(f"Unknown figure {name!r}; known: {sorted(FIGURES)}")
    return FIGURES[name](numbers, spec, w, h)
