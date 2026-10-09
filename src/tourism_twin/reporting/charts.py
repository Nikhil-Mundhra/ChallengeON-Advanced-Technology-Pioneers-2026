"""Generate presentation charts for the Abu Dhabi Tourism Digital Twin.

Produces:
1. waterfall_attribution.png - Decomposition of incremental hotel guest lift
2. tornado_sensitivity.png - Decision lever elasticity ranking
3. model_benchmark.png - Back-test performance comparison (read dynamically from evaluation_results.json)
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from tourism_twin.config import SETTINGS
from tourism_twin.domain.scenario import ScenarioLever
from tourism_twin.reporting.palette import AMBER, BLUE, NAVY, TEAL
from tourism_twin.planning.simulator import TourismDigitalTwin

OUTPUT_DIR = SETTINGS.figures_dir
RESULTS_PATH = SETTINGS.evaluation_results_path

plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.titlesize": 15,
})



def plot_waterfall(report, out_path: Path) -> Path:
    s = report.structural_result
    labels = [
        "1. Added Seats",
        "2. Load Factor",
        "3. P2P Mix",
        "4. Multiplier",
        "5. Guests/Arrival",
        "TOTAL LIFT",
    ]
    values = [
        s.waterfall_seats,
        s.waterfall_lf,
        s.waterfall_p2p,
        s.waterfall_multiplier,
        s.waterfall_los,
        s.delta_guests,
    ]
    colors = [BLUE, TEAL, AMBER, "#7C3AED", "#EC4899", NAVY]

    fig, ax = plt.subplots(figsize=(9, 4.8))
    bars = ax.bar(labels, values, color=colors, width=0.55, edgecolor="none")

    ax.set_ylabel("Incremental Weekly Hotel Guest-Days")
    ax.set_title(
        f"Waterfall Attribution: {report.market} ({report.season})\n"
        f"Scenario: +2 Weekly Flights & +2% Load Factor Lift (+{s.delta_guests:,.0f} Total Guests)",
        pad=15,
        fontweight="bold",
        color=NAVY,
    )
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")

    for bar in bars:
        h = bar.get_height()
        if abs(h) > 1:
            ax.annotate(
                f"{h:+,.1f}",
                xy=(bar.get_x() + bar.get_width() / 2, h),
                xytext=(0, 4 if h >= 0 else -12),
                textcoords="offset points",
                ha="center",
                va="bottom" if h >= 0 else "top",
                fontweight="bold",
                fontsize=9.5,
            )

    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    return out_path


def plot_tornado(report, out_path: Path) -> Path:
    tornado = report.tornado_sensitivity
    labels = [r["lever_name"].split(" (")[0] for r in reversed(tornado)]
    spreads = [r["swing_spread"] for r in reversed(tornado)]
    elasticities = [r["relative_sensitivity"] * 100 for r in reversed(tornado)]

    fig, ax = plt.subplots(figsize=(9, 4.8))
    bars = ax.barh(labels, spreads, color=TEAL, height=0.5, edgecolor="none")

    ax.set_xlabel("Scenario Swing Spread (Guest-Days)")
    ax.set_title(
        f"Tornado Sensitivity Analysis: {report.market}\n"
        f"Ranking Decision Levers by Hotel Demand Elasticity",
        pad=15,
        fontweight="bold",
        color=NAVY,
    )

    for bar, el in zip(bars, elasticities):
        w = bar.get_width()
        ax.annotate(
            f"{w:,.0f} ({el:.1f}% swing)",
            xy=(w, bar.get_y() + bar.get_height() / 2),
            xytext=(6, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontweight="bold",
            fontsize=9.5,
        )

    plt.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    return out_path


def plot_model_benchmark(out_path: Path) -> Path | None:
    """Plot the back-test benchmark; None when evaluation results do not exist yet."""
    # Read dynamically from evaluation_results.json
    if not RESULTS_PATH.exists():
        return None

    with open(RESULTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    bench = data["benchmark"]
    labels = list(bench)
    wmapes = [m["wmape"] * 100 for m in bench.values()]
    biases = [m["bias"] * 100 for m in bench.values()]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax1 = plt.subplots(figsize=(9.5, 4.8))
    rects1 = ax1.bar(x - width / 2, wmapes, width, label="WMAPE (%) [Lower is better]", color=BLUE)

    ax2 = ax1.twinx()
    rects2 = ax2.bar(x + width / 2, [abs(b) for b in biases], width, label="|Bias| (%) [Lower is better]", color=AMBER)

    ax1.set_ylabel("WMAPE (%)", color=BLUE, fontweight="bold")
    ax2.set_ylabel("Absolute Directional Bias (%)", color=AMBER, fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=15, ha="right")
    ax1.set_ylim(0, 30)
    ax2.set_ylim(0, 15)

    leader = data["benchmark_leaders"]["wmape"]
    baseline = next(iter(bench))
    gap_pp = (bench[baseline]["wmape"] - bench[leader]["wmape"]) * 100
    ax1.set_title(
        f"Strict Forward Holdout Benchmark (Jan 2025 – Jul 2025)\n"
        f"Lowest WMAPE: {leader.split('. ', 1)[-1]}, {gap_pp:.2f} pp below the {baseline.split('. ', 1)[-1]}",
        pad=15,
        fontweight="bold",
        color=NAVY,
    )

    for rect in rects1:
        h = rect.get_height()
        ax1.annotate(f"{h:.2f}%", xy=(rect.get_x() + rect.get_width() / 2, h), xytext=(0, 3), textcoords="offset points", ha="center", fontsize=9, fontweight="bold")

    for rect in rects2:
        h = rect.get_height()
        ax2.annotate(f"{h:.2f}%", xy=(rect.get_x() + rect.get_width() / 2, h), xytext=(0, 3), textcoords="offset points", ha="center", fontsize=9, fontweight="bold")

    fig.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    return out_path


def generate_charts() -> list[Path]:
    """Render the presentation figures; returns the paths written."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    twin = TourismDigitalTwin()
    lever = ScenarioLever(
        market="UNITED KINGDOM",
        delta_frequency=2.0,
        aircraft_gauge=290.0,
        delta_load_factor=0.02,
    )
    report = twin.run_scenario("UNITED KINGDOM", "Winter_Peak", lever)

    written = [
        plot_waterfall(report, OUTPUT_DIR / "waterfall_attribution.png"),
        plot_tornado(report, OUTPUT_DIR / "tornado_sensitivity.png"),
        plot_model_benchmark(OUTPUT_DIR / "model_benchmark.png"),
    ]
    return [path for path in written if path is not None]
