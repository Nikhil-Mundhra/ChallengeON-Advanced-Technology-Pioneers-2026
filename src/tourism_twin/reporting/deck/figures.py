"""Deck figures: name → PNG. Planning charts come from reporting/charts.py (one copy); the
diagrams and the validation chart are drawn here from the deck's numbers."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from tourism_twin.reporting.palette import AMBER, BLUE, INK, LINE, MINT, MUTED, NAVY, SKY, TEAL

DPI = 200


def _box(ax, x: float, y: float, w: float, h: float, text: str, face: str = SKY, edge: str = BLUE,
         color: str = NAVY, size: int = 11, bold: bool = False) -> None:
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.02",
                                facecolor=face, edgecolor=edge, linewidth=1.4))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size, color=color,
            fontweight="bold" if bold else "normal", wrap=True)


def _arrow(ax, start: Tuple[float, float], end: Tuple[float, float], color: str = MUTED) -> None:
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=14, color=color, linewidth=1.4))


def _canvas(width: float = 12, height: float = 5.6):
    fig, ax = plt.subplots(figsize=(width, height))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    return fig, ax


def _save(fig, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def goal_tree(out: Path, numbers: Dict[str, str]) -> Path:
    """Goal → three tasks → the layers that deliver them."""
    fig, ax = _canvas(12, 5.4)
    _box(ax, 0.12, 0.80, 0.76, 0.14, "Goal: show how flight changes move hotel guests", NAVY, NAVY, "white", 14, True)
    tasks = [("1. Predict daily hotel guests\nby market and nationality", 0.03),
             ("2. Simulate flight what-ifs\n(routes, seats, load factor)", 0.36),
             ("3. Explain which factors\nmove the number most", 0.69)]
    for text, x in tasks:
        _box(ax, x, 0.48, 0.28, 0.16, text, SKY, BLUE, NAVY, 11)
        _arrow(ax, (0.5, 0.80), (x + 0.14, 0.645))
    layers = [("Data\nhotel + flight data,\ncleaned and joined", 0.03), ("Models\nconversion chain +\nguest prediction", 0.27),
              ("Validation\ntested on unseen\nlater periods", 0.51), ("Simulator\nweb app: what-ifs,\nranges, drivers", 0.75)]
    for i, (text, _) in enumerate(layers):
        x = 0.02 + i * 0.25
        _box(ax, x, 0.06, 0.20, 0.22, text, MINT, TEAL, INK, 10.5)
        if i:
            _arrow(ax, (x - 0.05, 0.17), (x, 0.17), TEAL)
    ax.text(0.5, 0.36, "delivered by four layers", ha="center", fontsize=10, color=MUTED, style="italic")
    return _save(fig, out)


def system_diagram(out: Path, numbers: Dict[str, str]) -> Path:
    """Build side (heavy, offline) feeding the serve side (static, in the browser)."""
    fig, ax = _canvas(12.5, 5.6)
    ax.text(0.0, 0.97, "BUILD  (offline, Python: run once per data refresh)", fontsize=12, color=NAVY, fontweight="bold")
    steps = [("Raw data", "hotel guests, flights", SKY, BLUE), ("Data lake", "checked, versioned", SKY, BLUE),
             ("Panels", "daily and weekly", SKY, BLUE), ("Models", "chain + guest prediction", MINT, TEAL),
             ("Validation", "held-out periods", MINT, TEAL), ("Export", "versioned bundle", "#FFF7E6", AMBER)]
    w, h, gap = 0.135, 0.20, 0.032
    for i, (name, detail, face, edge) in enumerate(steps):
        x = 0.01 + i * (w + gap)
        _box(ax, x, 0.62, w, h, f"{name}\n{detail}", face, edge, INK, 10)
        if i:
            _arrow(ax, (x - gap, 0.72), (x, 0.72))
    ax.text(0.0, 0.43, "SERVE  (static web app: no server, no training)", fontsize=12, color=NAVY, fontweight="bold")
    serve = [("Bundle", "numbers only"), ("Browser engine", "same maths, exact"), ("Planner", "what-ifs, ranges, drivers")]
    for i, (name, detail) in enumerate(serve):
        x = 0.30 + i * 0.24
        _box(ax, x, 0.08, 0.19, 0.20, f"{name}\n{detail}", "#F5F7FA", MUTED, INK, 10)
        if i:
            _arrow(ax, (x - 0.05, 0.18), (x, 0.18))
    _arrow(ax, (0.01 + 5 * (w + gap) + w / 2, 0.62), (0.395, 0.28), AMBER)
    return _save(fig, out)


def passenger_split(out: Path, numbers: Dict[str, str]) -> Path:
    """Where arriving passengers go: only one branch fills hotels."""
    fig, ax = _canvas(7, 5.2)
    _box(ax, 0.28, 0.78, 0.44, 0.15, "Arriving passengers", NAVY, NAVY, "white", 13, True)
    branches = [(f"Connect onward\n(~{numbers.get('const.transfer_share_pct', '50')}%)", 0.02, "#F5F7FA", MUTED),
                ("Residents,\nfamily visits", 0.36, "#F5F7FA", MUTED), ("Hotel guests", 0.70, MINT, TEAL)]
    for text, x, face, edge in branches:
        _box(ax, x, 0.30, 0.28, 0.18, text, face, edge, INK, 12, text == "Hotel guests")
        _arrow(ax, (0.5, 0.78), (x + 0.14, 0.485))
    ax.text(0.84, 0.18, "what we predict", ha="center", fontsize=11, color=TEAL, style="italic")
    return _save(fig, out)


def conversion_chain(out: Path, numbers: Dict[str, str]) -> Path:
    """Seats → passengers → visitors → hotel guests, with the lever at each step."""
    fig, ax = _canvas(12.5, 3.6)
    steps = [("Seats", "routes · flights/week\n· aircraft size"), ("Passengers", "× load factor"),
             ("Visitors", "minus transfer\nand transit"), ("Hotel arrivals", "× hotel capture\n(by market, season)"),
             ("Hotel guests", "× guests per\narrival")]
    w, gap = 0.16, 0.05
    for i, (name, lever) in enumerate(steps):
        x = 0.01 + i * (w + gap)
        _box(ax, x, 0.50, w, 0.32, name, NAVY if i in (0, 4) else SKY, NAVY if i in (0, 4) else BLUE,
             "white" if i in (0, 4) else NAVY, 13, True)
        ax.text(x + w / 2, 0.30, lever, ha="center", va="top", fontsize=10.5, color=TEAL)
        if i:
            _arrow(ax, (x - gap, 0.66), (x, 0.66))
    return _save(fig, out)


def validation_bars(out: Path, numbers: Dict[str, str]) -> Path:
    """WAPE on held-out validation periods, domestic vs international, simplest to full model."""
    models = [("Same day last year", "naive_364"), ("Calendar only", "time_only"),
              ("Arrivals only", "flow_only"), ("Full model", "twin_daily")]
    labels = [m[0] for m in models]
    dom = [float(numbers[f"val.{key}.domestic"]) for _, key in models]
    intl = [float(numbers[f"val.{key}.international"]) for _, key in models]
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    y = range(len(models))
    ax.barh([i + 0.2 for i in y], dom, height=0.38, color=BLUE, label="Domestic")
    ax.barh([i - 0.2 for i in y], intl, height=0.38, color=TEAL, label="International")
    for i in y:
        ax.text(dom[i] + 0.3, i + 0.2, f"{dom[i]:.1f}%", va="center", fontsize=10, color=INK)
        ax.text(intl[i] + 0.3, i - 0.2, f"{intl[i]:.1f}%", va="center", fontsize=10, color=INK)
    ax.set_yticks(list(y), labels, fontsize=11)
    ax.set_xlabel("Error on held-out periods (WMAPE %, lower is better)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.12), ncol=2)
    return _save(fig, out)


def _reference_report():
    from tourism_twin.reporting.charts import reference_scenario

    return reference_scenario()


def waterfall(out: Path, numbers: Dict[str, str]) -> Path:
    from tourism_twin.reporting.charts import plot_waterfall

    return plot_waterfall(_reference_report(), out)


def tornado(out: Path, numbers: Dict[str, str]) -> Path:
    from tourism_twin.reporting.charts import plot_tornado

    return plot_tornado(_reference_report(), out)


def asset(name: str, assets_dir: Path) -> Callable[[Path, Dict[str, str]], Path]:
    """A user-supplied image (e.g. a simulator screenshot); a labelled placeholder until it exists."""
    def build(out: Path, numbers: Dict[str, str]) -> Path:
        source = assets_dir / name
        if source.exists():
            return source
        fig, ax = _canvas(8, 4.5)
        _box(ax, 0.05, 0.1, 0.9, 0.8, f"Screenshot goes here:\nreport/deck/assets/{name}", "#F5F7FA", LINE, MUTED, 13)
        return _save(fig, out)
    return build


FIGURES: Dict[str, Callable[[Path, Dict[str, str]], Path]] = {
    "goal_tree": goal_tree,
    "passenger_split": passenger_split,
    "system_diagram": system_diagram,
    "conversion_chain": conversion_chain,
    "validation_bars": validation_bars,
    "waterfall": waterfall,
    "tornado": tornado,
}


def render(name: str, out_dir: Path, numbers: Dict[str, str], assets_dir: Path) -> Path:
    if name.startswith("asset:"):
        return asset(name.split(":", 1)[1], assets_dir)(out_dir / f"{name.split(':', 1)[1]}", numbers)
    if name not in FIGURES:
        raise KeyError(f"Unknown figure {name!r}; known: {sorted(FIGURES)} or asset:<file>")
    return FIGURES[name](out_dir / f"{name}.png", numbers)
