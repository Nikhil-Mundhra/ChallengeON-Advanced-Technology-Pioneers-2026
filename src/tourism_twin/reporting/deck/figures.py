"""Deck figures: name → PNG, in the deck theme. Planning charts come from reporting/charts.py (one
copy, recoloured); the diagrams and the validation and outlook charts are drawn here from the
deck's numbers."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List, Sequence, Tuple

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch

from matplotlib import font_manager

from tourism_twin.config import SETTINGS
from tourism_twin.reporting.deck.theme import CHART_FONT, GREEN, GREEN_DARK, GREEN_LIGHT, GREY, INK, LINE, RED, SAND

DPI = 200
NAVY, BLUE, TEAL, SKY, MINT, AMBER, MUTED = GREEN_DARK, GREEN, GREEN, GREEN_LIGHT, SAND, RED, GREY
for _font in (SETTINGS.root / "report" / "deck" / "fonts").glob("*.ttf"):
    font_manager.fontManager.addfont(str(_font))
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": CHART_FONT, "axes.edgecolor": LINE,
                     "axes.labelcolor": INK, "xtick.color": GREY, "ytick.color": GREY})


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


def system_diagram(out: Path, numbers: Dict[str, str]) -> Path:
    """Build side (heavy, offline) feeding the serve side (static, in the browser)."""
    fig, ax = _canvas(12.5, 5.6)
    ax.text(0.0, 0.97, "BUILD  (offline, Python: run once per data refresh)", fontsize=12, color=NAVY, fontweight="bold")
    steps = [("Raw data", "hotel guests, flights", SKY, BLUE), ("Data lake", "checked, versioned", SKY, BLUE),
             ("Panels", "daily and weekly", SKY, BLUE), ("Models", "fit + select", MINT, TEAL),
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


def model_form(out: Path, numbers: Dict[str, str]) -> Path:
    """Guests = flow × calendar multiplier: two branches, one joint fit."""
    fig, ax = _canvas(9.5, 3.0)
    _box(ax, 0.00, 0.62, 0.17, 0.24, "New arrivals\n(last 22 days)", SKY, BLUE, NAVY, 11, True)
    _box(ax, 0.23, 0.62, 0.25, 0.24, "Distributed lag\nguests still in hotels from\neach earlier check-in day", MINT, TEAL, INK, 10.5)
    _box(ax, 0.00, 0.14, 0.17, 0.24, "Date", SKY, BLUE, NAVY, 11, True)
    _box(ax, 0.23, 0.14, 0.25, 0.24, "Calendar multiplier\nseason (Fourier) · weekday ·\nRamadan, Eid, events", MINT, TEAL, INK, 10.5)
    _arrow(ax, (0.17, 0.74), (0.23, 0.74))
    _arrow(ax, (0.17, 0.26), (0.23, 0.26))
    _box(ax, 0.56, 0.38, 0.17, 0.24, "flow × multiplier\n(fitted jointly)", "#FFF7E6", AMBER, INK, 11, True)
    _arrow(ax, (0.48, 0.74), (0.56, 0.56))
    _arrow(ax, (0.48, 0.26), (0.56, 0.44))
    _box(ax, 0.81, 0.38, 0.17, 0.24, "Hotel guests\ntonight", NAVY, NAVY, "white", 12, True)
    _arrow(ax, (0.73, 0.50), (0.81, 0.50))
    return _save(fig, out)


def protocol_timeline(out: Path, numbers: Dict[str, str]) -> Path:
    """Train → gap → validate at 7 monthly origins; frozen test scored once; test period forecast."""
    fig, ax = plt.subplots(figsize=(9.5, 3.0))
    origins = ["2024-02", "2024-03", "2024-04", "2024-05", "2024-06", "2024-07", "2024-08"]
    t0, t_end = pd.Timestamp("2022-01-01"), pd.Timestamp("2026-03-01")
    x = lambda d: (pd.Timestamp(d) - t0).days
    for i, origin in enumerate(origins):
        y = len(origins) - i
        start = pd.Timestamp(origin + "-01")
        ax.barh(y, x(start - pd.Timedelta(days=21)), left=0, color=BLUE, height=0.6)
        ax.barh(y, 21, left=x(start - pd.Timedelta(days=21)), color=LINE, height=0.6)
        end = min(start + pd.DateOffset(months=6), pd.Timestamp("2025-01-31"))
        ax.barh(y, (end - start).days, left=x(start), color=TEAL, height=0.6)
    ax.barh(0, x("2025-07-31") - x("2025-02-01"), left=x("2025-02-01"), color=AMBER, height=0.6)
    ax.barh(-1, x("2026-02-28") - x("2025-08-01"), left=x("2025-08-01"), color="#B9C3CF", height=0.6)
    ax.set_yticks([*range(1, len(origins) + 1), 0, -1],
                  [*[f"origin {o}" for o in reversed(origins)], "frozen test (once)", "test period (forecast)"], fontsize=9)
    years = [pd.Timestamp(f"{y}-01-01") for y in range(2022, 2027)]
    ax.set_xticks([x(d) for d in years], [str(d.year) for d in years])
    ax.set_xlim(0, x(t_end))
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.legend(handles=[Patch(color=BLUE, label="train (expanding)"), Patch(color=LINE, label="21-day gap"),
                       Patch(color=TEAL, label="validate (6 months)"), Patch(color=AMBER, label="frozen test")],
              frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.2), fontsize=10)
    return _save(fig, out)


def outlook_months(out: Path, numbers: Dict[str, str]) -> Path:
    """Guest-nights per winter month: last winter's model estimate vs the flat and trend scenarios."""
    months = [numbers[f"outlook.month{i}"] for i in (1, 2, 3)]
    series = [("{} (arrivals known)".format(numbers["outlook.previous_window"]), "previous", "#B9C3CF"),
              ("{}, flat arrivals".format(numbers["outlook.window"]), "flat", BLUE),
              ("{}, arrivals trend".format(numbers["outlook.window"]), "trend", TEAL)]
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    width = 0.27
    for j, (label, key, color) in enumerate(series):
        values = [float(numbers[f"outlook.{key}.m{i}_guests"]) for i in (1, 2, 3)]
        positions = [i + (j - 1) * width for i in range(3)]
        ax.bar(positions, values, width=width, color=color, label=label)
        for p, v in zip(positions, values):
            ax.text(p, v + 0.02, f"{v:.2f}", ha="center", fontsize=9, color=INK)
    ax.set_xticks(range(3), months, fontsize=11)
    ax.set_ylabel("Hotel guest-nights (millions)")
    ax.set_ylim(0, max(float(numbers[f"outlook.trend.m{i}_guests"]) for i in (1, 2, 3)) * 1.18)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.16), ncol=2, fontsize=9)
    return _save(fig, out)


def _reference_report():
    from tourism_twin.reporting.charts import reference_scenario

    return reference_scenario()


def waterfall(out: Path, numbers: Dict[str, str]) -> Path:
    from tourism_twin.reporting.charts import plot_waterfall

    return plot_waterfall(_reference_report(), out)


def tornado(out: Path, numbers: Dict[str, str]) -> Path:
    from tourism_twin.reporting.charts import plot_tornado
    from tourism_twin.reporting.deck.numbers import LEVER_NAMES

    return plot_tornado(_reference_report(), out, color=GREEN, title=False,
                        names={k: v[0].upper() + v[1:] for k, v in LEVER_NAMES.items()})


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
    "system_diagram": system_diagram,
    "conversion_chain": conversion_chain,
    "validation_bars": validation_bars,
    "model_form": model_form,
    "protocol_timeline": protocol_timeline,
    "outlook_months": outlook_months,
    "waterfall": waterfall,
    "tornado": tornado,
}


def render(name: str, out_dir: Path, numbers: Dict[str, str], assets_dir: Path) -> Path:
    if name.startswith("asset:"):
        return asset(name.split(":", 1)[1], assets_dir)(out_dir / f"{name.split(':', 1)[1]}", numbers)
    if name not in FIGURES:
        raise KeyError(f"Unknown figure {name!r}; known: {sorted(FIGURES)} or asset:<file>")
    return FIGURES[name](out_dir / f"{name}.png", numbers)
