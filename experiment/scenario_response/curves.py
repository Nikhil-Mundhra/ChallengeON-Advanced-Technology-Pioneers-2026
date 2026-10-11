"""Response curves: guest change against a seat change from -50% to +100% for five markets, every
model fitted on the last VALIDATION_ORIGINS fold (train to 2024-07-10, test 2024-08-01..2025-01-31),
the change applied to every week (day) of that test period. Ratio models: sum of scenario weeks /
sum of baseline weeks (HYBRID on actual seats) - 1; S-CURVE as a frequency change at the week's own
gauge (the market's median gauge where flights are unknown); SHORT-RUN (1 + change) ^ beta; CHAIN: SeatChain.scenario on the test period, guests counted
from day 28 on (after the kernels fill). Historical points: the market's actual weeks, both tests.

    python experiment/scenario_response/curves.py    (needs chain_runs.py done)
"""

from __future__ import annotations

import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import chain_runs  # noqa: E402
import data  # noqa: E402
import lever  # noqa: E402
import scenario_engines  # noqa: E402
from short_run import ShortRun  # noqa: E402
from tourism_twin.domain.scenario import ScenarioLever  # noqa: E402
from tourism_twin.planning.residual import ResidualMLEngine  # noqa: E402
from tourism_twin.planning.structural import StructuralEngine  # noqa: E402

MARKETS = ("UNITED KINGDOM", "INDIA", "CHINA", "GERMANY", "KUWAIT")
GRID = np.round(np.arange(-0.5, 1.0001, 0.1), 2)
STYLE = {  # reference categorical palette, fixed order; TIME-ONLY is the gray null line
    "LINEAR": ("#2a78d6", "-"), "S-CURVE": ("#eb6834", "-"), "S-CURVE %": ("#eb6834", "--"),
    "SHORT-RUN": ("#1baf7a", "-"), "CHAIN": ("#4a3aa7", "-"), "TIME-ONLY": ("#898781", ":")}
OUT_CSV = data.OUT / "response_curves.csv"


def curves(short_run_ridge: float) -> pd.DataFrame:
    warnings.filterwarnings("ignore")
    fold = data.folds()[chain_runs.CURVE_FOLD]
    weekly = data.weekly_panel()
    train = weekly[weekly["week_start"] + pd.Timedelta(days=6) < fold.train_end]
    engine = StructuralEngine.calibrate(train)
    linear = scenario_engines.as_linear(engine)
    residual = ResidualMLEngine().fit(train, engine)
    short = ShortRun(short_run_ridge).fit(train)
    chain = chain_runs.load()[chain_runs.CURVE_FOLD]["model"]
    daily = data.daily()

    rows = []
    for market in MARKETS:
        test = weekly[(weekly["market"] == market) & (weekly["week_start"] >= fold.test_start)
                      & (weekly["week_start"] + pd.Timedelta(days=6) <= fold.test_end) & (weekly["seats"] > 0)]
        typical_gauge = float((test["seats"] / test["flights"]).median())
        base = np.maximum(0.0, engine.planning_guests_for(test) + residual.predict_residual(test).to_numpy())
        for change in GRID:
            out = {"market": market, "seat_change": change, "TIME-ONLY": 0.0, "SHORT-RUN": (1 + change) ** short.beta(market) - 1}
            deltas = {"LINEAR": [], "S-CURVE": [], "S-CURVE %": []}
            for row in test.itertuples(index=False):
                seats_lever = ScenarioLever(market=market, delta_seats_pct=change)
                gauge = row.seats / row.flights if row.flights > 0 else typical_gauge
                flights = engine.get_or_create_params(market, row.season).baseline_weekly_seats / gauge
                freq_lever = ScenarioLever(market=market, aircraft_gauge=gauge, delta_frequency=flights * change)
                deltas["LINEAR"].append(linear.simulate(market, row.season, seats_lever).delta_guests)
                deltas["S-CURVE"].append(engine.simulate(market, row.season, freq_lever).delta_guests)
                deltas["S-CURVE %"].append(engine.simulate(market, row.season, seats_lever).delta_guests)
            for name, values in deltas.items():
                out[name] = np.maximum(0.0, base + np.array(values)).sum() / base.sum() - 1
            scenario = chain.scenario(daily, market, str(fold.test_start.date()), str(fold.test_end.date()), float(change))
            counted = scenario[scenario["in_window"] & (scenario["date"] >= fold.test_start + pd.Timedelta(days=28))]
            out["CHAIN"] = counted["scenario_guests"].sum() / counted["guests"].sum() - 1
            rows.append(out)
    frame = pd.DataFrame(rows)
    frame.to_csv(OUT_CSV, index=False)
    return frame


def chart(frame: pd.DataFrame, mode: str) -> str:
    weekly = data.weekly_panel()
    history = lever.actual_changes(weekly, mode)
    fig, axes = plt.subplots(1, len(MARKETS), figsize=(4.2 * len(MARKETS), 4.4), sharey=True)
    for ax, market in zip(axes, MARKETS):
        points = history[history["market"] == market]
        x, y = (np.exp(points["ds"]) - 1) * 100, (np.exp(points["act"]) - 1) * 100
        event = points["ds"].abs() > lever.THRESHOLD
        ax.scatter(x[~event], y[~event], s=10, color="#c3c2b7", label="weeks, |seat change| <= 15%", zorder=1)
        ax.scatter(x[event], y[event], s=14, color="#52514e", label="natural-experiment weeks", zorder=2)
        curve = frame[frame["market"] == market]
        for name, (color, dash) in STYLE.items():
            ax.plot(curve["seat_change"] * 100, curve[name] * 100, dash, color=color, linewidth=2, label=name, zorder=3)
        ax.axhline(0, color="#e4e3dd", linewidth=1, zorder=0)
        ax.axvline(0, color="#e4e3dd", linewidth=1, zorder=0)
        ax.set_xlim(-55, 105)
        ax.set_ylim(-80, 140)
        ax.set_title(market.title(), fontsize=11, color="#0b0b0b")
        ax.set_xlabel("seat change (%)", fontsize=9, color="#52514e")
        ax.tick_params(labelsize=8, colors="#52514e")
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    axes[0].set_ylabel("guest change (%)", fontsize=9, color="#52514e")
    reference = "same week a year earlier, drift removed" if mode == "yoy" else "centred 13-week trend"
    fig.suptitle(f"Guest response to a seat change: models (last fold) and history (against the {reference})", fontsize=12)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=8, fontsize=8, frameon=False)
    fig.tight_layout(rect=(0, 0.07, 1, 0.95))
    path = data.OUT / f"response_curves_{mode}.png"
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return str(path)
