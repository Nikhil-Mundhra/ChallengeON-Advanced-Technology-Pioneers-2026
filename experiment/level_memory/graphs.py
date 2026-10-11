"""Graphs for the Israel bias under the drifting strength (before any fix). PNGs go to out/israel/.

    python experiment/level_memory/graphs.py   (needs refit.py shipped,drift and the run.py caches)

a_series.png    Israel weekly guests, new arrivals and guests per arrival, war start, one-off rows, fold training ends.
b_folds.png     Israel per fold: s(t), base stock c_t (shipped vs drift), weekly actual vs predicted on the test window.
c_contrast.png  s(t) per fold for Israel and three markets where the drift helped.
d_last_knot.png Per market and fold: drift WAPE change vs the last knot of s(t), and the market-level view.
"""

from __future__ import annotations

import warnings
from typing import Dict, List

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import data  # noqa: E402
import refit  # noqa: E402
import report  # noqa: E402
import scoring  # noqa: E402

OUT = data.OUT / "israel"
WAR_START = pd.Timestamp("2023-10-07")
START, END = pd.Timestamp("2022-01-01"), pd.Timestamp("2025-01-31")
MARKET = "ISRAEL"
SHIPPED, DRIFT, ACTUAL = "#2a78d6", "#eb6834", "#52514e"  # reference palette slots 1 and 2, secondary ink
INK, GRID = "#0b0b0b", "#e4e3df"
FOLD_SHADES = plt.get_cmap("Blues")(np.linspace(0.35, 0.95, 7))


def style(ax) -> None:
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.tick_params(labelsize=8, colors=ACTUAL)


def date_axis(ax, months: int) -> None:
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=range(1, 13, months)))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))


def mark_events(ax, panel: pd.DataFrame, fold_ends: List[pd.Timestamp], market: str = MARKET) -> None:
    flagged = panel[(panel["market"] == market) & (panel["is_one_off_period"] == 1)]["date"]
    if len(flagged):
        ax.axvspan(flagged.min(), flagged.max() + pd.Timedelta(days=1), color="#d9d8d4", alpha=0.6, lw=0)
    ax.axvline(WAR_START, color="#e34948", lw=1.2)
    for end in fold_ends:
        ax.axvline(end, color=ACTUAL, lw=0.7, ls=(0, (3, 3)))


# --- data ------------------------------------------------------------------------------------
def scored_frame(panel: pd.DataFrame) -> pd.DataFrame:
    preds = {name: [(report.load(name, "protocol", i)["window"].fold, report.load(name, "protocol", i)["pred"]["guests"])
                    for i in report.FOLDS] for name in ("nowcast", "drift_k182_l0.1")}
    return scoring.series(scoring.scored(panel, preds), "international")


def market_fold_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Per market and fold: WAPE and bias for shipped and drift, and the last knot of s(t)."""
    rows = []
    for (market, fold), part in frame.groupby(["market", "fold"]):
        row = {"market": market, "fold": fold}
        for name, label in (("nowcast", "shipped"), ("drift_k182_l0.1", "drift")):
            p = part[part["model"] == name]
            row[f"wape {label}"] = scoring.wape(p)
            row[f"bias {label}"] = (p["pred"].sum() / p["actual"].sum() - 1) * 100
            row[f"actual {label}"] = p["actual"].sum()
        rows.append(row)
    out = pd.DataFrame(rows)
    folds = sorted(out["fold"].unique())
    out["fold_i"] = out["fold"].map(folds.index)
    out["s last"] = [refit.kernel(refit.load("drift", m, i), m).theta_[-1] for m, i in zip(out["market"], out["fold_i"])]
    out["wape change"] = out["wape drift"] - out["wape shipped"]
    return out


def market_table(frame: pd.DataFrame, by_fold: pd.DataFrame) -> pd.DataFrame:
    """Per market, folds pooled: WAPE change (pp) and the mean last knot."""
    rows = []
    for market, part in frame.groupby("market"):
        w = {name: scoring.wape(part[part["model"] == name]) for name in ("nowcast", "drift_k182_l0.1")}
        rows.append({"market": market, "wape change": w["drift_k182_l0.1"] - w["nowcast"]})
    out = pd.DataFrame(rows).set_index("market")
    out["s last mean"] = by_fold.groupby("market")["s last"].mean()
    out["s last abs mean"] = by_fold.groupby("market")["s last"].apply(lambda s: s.abs().mean())
    return out.reset_index()


# --- graphs ----------------------------------------------------------------------------------
def graph_a(panel: pd.DataFrame, fold_ends: List[pd.Timestamp]) -> None:
    rows = panel[(panel["market"] == MARKET) & (panel["date"] >= START) & (panel["date"] <= END)]
    weekly = rows.set_index("date")[["guests", "new_arrivals"]].resample("W-MON", label="left", closed="left").sum()
    weekly["ratio"] = weekly["guests"] / weekly["new_arrivals"].replace(0, np.nan)
    fig, axes = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
    for ax, column, title in zip(axes, ("guests", "new_arrivals", "ratio"),
                                 ("Guests (weekly sum)", "New arrivals (weekly sum)", "Guests per arrival (weekly)")):
        ax.plot(weekly.index, weekly[column], color=SHIPPED if column != "ratio" else INK, lw=1.4)
        if column == "ratio":
            monthly = rows.set_index("date")[["guests", "new_arrivals"]].resample("MS").sum()
            ax.plot(monthly.index + pd.Timedelta(days=14), monthly["guests"] / monthly["new_arrivals"], color=DRIFT, lw=2,
                    label="monthly")
            ax.legend(frameon=False, fontsize=8)
        mark_events(ax, panel, fold_ends)
        ax.set_title(title, fontsize=10, loc="left", color=INK)
        style(ax)
    axes[0].text(WAR_START, axes[0].get_ylim()[1] * 0.95, " 7 Oct 2023", color="#e34948", fontsize=8, va="top")
    axes[0].text(fold_ends[-1], axes[0].get_ylim()[1] * 0.95, " fold training ends (dashed)", color=ACTUAL, fontsize=8, va="top")
    axes[1].text(pd.Timestamp("2022-01-09"), axes[1].get_ylim()[1] * 0.95, " one-off rows (grey)", color=ACTUAL, fontsize=8, va="top")
    fig.suptitle("Israel: guests, arrivals and guests per arrival, 2022 to January 2025", fontsize=12, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(OUT / "a_series.png", dpi=130)
    plt.close(fig)


def graph_b(panel: pd.DataFrame, folds: list) -> None:
    fig, axes = plt.subplots(7, 3, figsize=(15, 20))
    actual = panel[panel["market"] == MARKET].set_index("date")["guests"]
    for i, fold in enumerate(folds):
        shipped, drift = refit.load("shipped", MARKET, i), refit.load("drift", MARKET, i)
        ps, pd_ = refit.parts(shipped, MARKET), refit.parts(drift, MARKET)
        k = refit.kernel(drift, MARKET)
        ax = axes[i, 0]
        ax.plot(pd_["date"], pd_["s"], color=DRIFT, lw=1.6)
        ax.plot(k.drift_knots_, k.theta_, "o", color=DRIFT, ms=4)
        ax.axhline(0, color=ACTUAL, lw=0.6)
        ax.axvline(fold.train_end, color=ACTUAL, ls=(0, (3, 3)), lw=0.8)
        ax.axvline(WAR_START, color="#e34948", lw=1)
        ax.axvspan(fold.test_start, fold.test_end, color="#efeeea", lw=0)
        ax.set_ylim(-0.25, 0.25)
        ax.set_title(f"{fold.name}: s(t), last knot {k.theta_[-1]:+.3f}", fontsize=9, loc="left")
        ax = axes[i, 1]
        ax.plot(ps["date"], ps["c"], color=SHIPPED, lw=1.3, label="c_t shipped")
        ax.plot(pd_["date"], pd_["c"], color=DRIFT, lw=1.3, label="c_t drift")
        ax.axvline(fold.train_end, color=ACTUAL, ls=(0, (3, 3)), lw=0.8)
        ax.axvline(WAR_START, color="#e34948", lw=1)
        ax.axvspan(fold.test_start, fold.test_end, color="#efeeea", lw=0)
        ax.set_title("base stock c_t (guests)", fontsize=9, loc="left")
        if i == 0:
            ax.legend(frameon=False, fontsize=8)
        ax = axes[i, 2]
        days = pd.date_range(fold.test_start, fold.test_end)
        test = pd.DataFrame({"actual": actual.reindex(days)})
        for model, label in ((shipped, "shipped"), (drift, "drift")):
            pred = refit.predict(model, MARKET)
            test[label] = pred.set_axis(panel.loc[pred.index, "date"]).reindex(days)
        test = test.dropna()
        weekly = test.resample("W-MON", label="left", closed="left").sum()
        bias = {c: (test[c].sum() / test["actual"].sum() - 1) * 100 for c in ("shipped", "drift")}
        ax.plot(weekly.index, weekly["actual"], color=INK, lw=1.8, label="actual")
        ax.plot(weekly.index, weekly["shipped"], color=SHIPPED, lw=1.3, label=f"shipped ({bias['shipped']:+.1f}%)")
        ax.plot(weekly.index, weekly["drift"], color=DRIFT, lw=1.3, label=f"drift ({bias['drift']:+.1f}%)")
        ax.legend(frameon=False, fontsize=8)
        ax.set_title("test window, weekly guests (bias in legend)", fontsize=9, loc="left")
        for ax in axes[i]:
            style(ax)
        for ax in axes[i, :2]:
            ax.set_xlim(START, END)
            date_axis(ax, 6)
        date_axis(axes[i, 2], 2)
    fig.suptitle("Israel per fold: drift s(t), base stock, test-window fit (red: 7 Oct 2023; dashed: training end; shaded: test)",
                 fontsize=12, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.98))
    fig.savefig(OUT / "b_folds.png", dpi=110)
    plt.close(fig)


def graph_c(contrast: List[str], folds: list) -> None:
    markets = [MARKET, *contrast]
    fig, axes = plt.subplots(len(markets), 1, figsize=(11, 3 * len(markets)), sharex=True)
    for ax, market in zip(axes, markets):
        for i, fold in enumerate(folds):
            k = refit.kernel(refit.load("drift", market, i), market)
            dates = pd.Series(pd.date_range(START, fold.test_end))
            s = k.drift(dates)
            train = dates < fold.train_end
            ax.plot(dates[train], s[train], color=FOLD_SHADES[i], lw=1.4, label=fold.name.replace("origin_", ""))
            ax.plot(dates[~train], s[~train], color=FOLD_SHADES[i], lw=1.4, ls=(0, (2, 2)))
        ax.axhline(0, color=ACTUAL, lw=0.6)
        ax.axvline(WAR_START, color="#e34948", lw=1)
        ax.set_ylim(-0.25, 0.25)
        ax.set_title(f"{market}: s(t) per fold (solid: training, dotted: held)", fontsize=9, loc="left")
        style(ax)
    axes[0].legend(frameon=False, fontsize=7, ncol=7, loc="lower right")
    fig.suptitle("Drift s(t) per fold: Israel and three markets where the drift helped", fontsize=12, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(OUT / "c_contrast.png", dpi=120)
    plt.close(fig)


def graph_d(by_fold: pd.DataFrame, by_market: pd.DataFrame) -> Dict[str, float]:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    ax = axes[0]
    other = by_fold[by_fold["market"] != MARKET]
    ax.scatter(other["s last"], other["wape change"], s=22, color=SHIPPED, alpha=0.6, label="other markets")
    isr = by_fold[by_fold["market"] == MARKET]
    ax.scatter(isr["s last"], isr["wape change"], s=40, color=DRIFT, label="Israel", zorder=3)
    ax.axhline(0, color=ACTUAL, lw=0.6)
    ax.axvline(0, color=ACTUAL, lw=0.6)
    ax.set_xlabel("last knot of s(t) (log units, held beyond training)", fontsize=9)
    ax.set_ylabel("drift WAPE - shipped WAPE (pp)", fontsize=9)
    ax.set_title("Market x fold", fontsize=10, loc="left")
    ax.legend(frameon=False, fontsize=8)
    ax = axes[1]
    ax.scatter(by_market["s last mean"], by_market["wape change"], s=30, color=SHIPPED)
    for _, row in by_market.iterrows():
        ax.annotate(row["market"].title()[:14], (row["s last mean"], row["wape change"]), fontsize=7, color=ACTUAL,
                    xytext=(3, 2), textcoords="offset points")
    ax.axhline(0, color=ACTUAL, lw=0.6)
    ax.axvline(0, color=ACTUAL, lw=0.6)
    ax.set_xlabel("mean last knot over folds", fontsize=9)
    ax.set_title("Market, folds pooled", fontsize=10, loc="left")
    for ax in axes:
        style(ax)
    stats = {"corr |s last| vs change (market x fold)": float(np.corrcoef(by_fold["s last"].abs(), by_fold["wape change"])[0, 1]),
             "corr s last vs change (market x fold)": float(np.corrcoef(by_fold["s last"], by_fold["wape change"])[0, 1]),
             "corr |s last| vs change, without Israel": float(np.corrcoef(other["s last"].abs(), other["wape change"])[0, 1])}
    fig.suptitle(f"Drift WAPE change vs the held last knot (corr with |s last|: {stats['corr |s last| vs change (market x fold)']:+.2f})",
                 fontsize=12, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(OUT / "d_last_knot.png", dpi=120)
    plt.close(fig)
    return stats


def main() -> None:
    warnings.filterwarnings("ignore")
    OUT.mkdir(parents=True, exist_ok=True)
    panel = data.panel()
    panel = panel[panel["date"] <= END]
    folds = data.folds("protocol", panel)
    frame = scored_frame(panel)
    by_fold = market_fold_table(frame)
    by_market = market_table(frame, by_fold)
    contrast = by_market[by_market["market"] != MARKET].nsmallest(3, "wape change")["market"].tolist()
    graph_a(panel, [f.train_end for f in folds])
    graph_b(panel, folds)
    graph_c(contrast, folds)
    stats = graph_d(by_fold, by_market)
    pd.set_option("display.width", 200)
    print(by_market.sort_values("wape change").round(3).to_string(index=False))
    print(by_fold[by_fold["market"] == MARKET][["fold", "s last", "wape shipped", "wape drift", "bias shipped", "bias drift"]].round(3).to_string(index=False))
    print("contrast:", contrast)
    print({k: round(v, 3) for k, v in stats.items()})


if __name__ == "__main__":
    main()
