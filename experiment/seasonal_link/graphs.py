"""Step 1 charts and tables: does the seats -> arrivals link change strength with the calendar?

  1_pooled.png      pooled residual slope by calendar month and by project season, seats -> arrivals and
                    P2P -> arrivals (arrivals -> guests as a control), both residual forms
  2_markets.png     the same by season for the 6 largest markets
  3_robustness.png  by season: leave one market out, and without Ramadan and Eid weeks

    python experiment/seasonal_link/graphs.py
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import data  # noqa: E402
import residuals  # noqa: E402
import slopes  # noqa: E402
from tourism_twin.domain.seasons import SEASONS  # noqa: E402

LINKS = [("seats", "arrivals"), ("p2p", "arrivals"), ("arrivals", "guests")]
COLOURS = {"seats": "#457b9d", "p2p": "#2a9d8f", "arrivals": "#e76f51"}
FIRST_HALF, SECOND_HALF = list(range(1, 7)), list(range(7, 13))
OUTLIER = 1.0  # |log residual| above this is a data break (a week with almost no seats), not a deviation


def frames() -> dict:
    weekly = data.weekly_series()
    out = {}
    for method in ("fourier", "woy"):
        r = residuals.decompose(weekly, method)
        cols = [f"{s}_res" for s in residuals.SERIES]
        r = r.dropna(subset=cols)
        out[method] = r[(r[cols].abs() < OUTLIER).all(axis=1)].copy()
    return out


def half_label(frame: pd.DataFrame) -> pd.Series:
    return frame["week_start"].dt.year.astype(str) + np.where(frame["month"] <= 6, " H1", " H2")


def pooled_tables(r: pd.DataFrame) -> dict:
    tables = {}
    for x, y in LINKS:
        key = f"{x}->{y}"
        tables[("month", key)] = slopes.by_group(r, f"{x}_res", f"{y}_res", "month")
        tables[("season", key)] = slopes.by_group(r, f"{x}_res", f"{y}_res", "season")
        tables[("half", key)] = slopes.by_group(r.assign(half=half_label(r)), f"{x}_res", f"{y}_res", "half")
    return tables


def contrasts(r: pd.DataFrame, label: str) -> list:
    rows = []
    for x, y in LINKS:
        c = slopes.contrast(r, f"{x}_res", f"{y}_res", "month", FIRST_HALF, SECOND_HALF)
        rows.append({"data": label, "link": f"{x}->{y}", "contrast": "Jan-Jun minus Jul-Dec", **c})
        c = slopes.contrast(r, f"{x}_res", f"{y}_res", "season", ["Winter_Peak", "Spring_Shoulder"], ["Summer_Trough", "Autumn_Shoulder"])
        rows.append({"data": label, "link": f"{x}->{y}", "contrast": "Winter+Spring minus Summer+Autumn", **c})
    return rows


def chart_pooled(tables: dict, woy: dict) -> None:
    fig, ax = plt.subplots(1, 2, figsize=(17, 5.5), gridspec_kw={"width_ratios": [2.2, 1]})
    for i, (x, y) in enumerate(LINKS):
        key = f"{x}->{y}"
        t = tables[("month", key)]
        shift = (i - 1) * 0.18
        ax[0].errorbar(t["month"] + shift, t["slope"], yerr=[t["slope"] - t["low"], t["high"] - t["slope"]], fmt="o-",
                       capsize=3, color=COLOURS[x], label=f"{x} -> {y}")
        w = woy[("month", key)]
        ax[0].plot(w["month"] + shift, w["slope"], "x:", color=COLOURS[x], alpha=0.7)
        t = tables[("season", key)].set_index("season").loc[SEASONS]
        ax[1].errorbar(np.arange(4) + shift, t["slope"], yerr=[t["slope"] - t["low"], t["high"] - t["slope"]], fmt="o",
                       capsize=3, color=COLOURS[x], label=f"{x} -> {y}")
    ax[0].set_xticks(range(1, 13), ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    ax[0].set_ylabel("slope on time-removed weekly residuals (90% week bootstrap)")
    ax[0].set_title("Pooled over 20 markets by calendar month (dotted x: week-of-year residual form)")
    ax[1].set_xticks(range(4), [s.replace("_", "\n") for s in SEASONS])
    ax[1].set_title("By project season")
    for a in ax:
        a.axhline(0, color="k", lw=0.5)
        a.grid(alpha=0.3)
        a.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(data.OUT / "1_pooled.png", dpi=95)


def market_tables(r: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for market in data.BIG_SIX:
        part = r[r["market"] == market]
        for x, y in LINKS[:2]:
            t = slopes.by_group(part, f"{x}_res", f"{y}_res", "season")
            h = slopes.contrast(part, f"{x}_res", f"{y}_res", "month", FIRST_HALF, SECOND_HALF)
            rows += [{"market": market, "link": f"{x}->{y}", **row, "H1-H2": h["difference"], "H1-H2 low": h["low"], "H1-H2 high": h["high"]}
                     for row in t.to_dict("records")]
    return pd.DataFrame(rows)


def chart_markets(table: pd.DataFrame) -> None:
    fig, ax = plt.subplots(2, 3, figsize=(18, 8), sharey=True)
    for a, market in zip(ax.flat, data.BIG_SIX):
        for i, (x, y) in enumerate(LINKS[:2]):
            t = table[(table["market"] == market) & (table["link"] == f"{x}->{y}")].set_index("season").loc[SEASONS]
            a.errorbar(np.arange(4) + (i - 0.5) * 0.2, t["slope"], yerr=[t["slope"] - t["low"], t["high"] - t["slope"]],
                       fmt="o-", capsize=3, color=COLOURS[x], label=f"{x} -> {y}")
        a.set_xticks(range(4), [s.split("_")[0] for s in SEASONS])
        a.axhline(0, color="k", lw=0.5)
        a.grid(alpha=0.3)
        a.set_title(market.title())
    ax[0, 0].legend(fontsize=8)
    ax[0, 0].set_ylabel("residual slope (90% week bootstrap)")
    ax[1, 0].set_ylabel("residual slope (90% week bootstrap)")
    plt.tight_layout()
    plt.savefig(data.OUT / "2_markets.png", dpi=95)


def robustness(r: pd.DataFrame) -> tuple:
    """By season: every leave-one-market-out slope, and the slope without lunar-event weeks."""
    rows, contrast_rows = [], []
    for x, y in LINKS[:2]:
        for market in sorted(r["market"].unique()):
            t = slopes.by_group(r[r["market"] != market], f"{x}_res", f"{y}_res", "season")
            rows += [{"link": f"{x}->{y}", "left out": market, "season": s, "slope": v} for s, v in zip(t["season"], t["slope"])]
            c = slopes.contrast(r[r["market"] != market], f"{x}_res", f"{y}_res", "month", FIRST_HALF, SECOND_HALF)
            contrast_rows.append({"link": f"{x}->{y}", "left out": market, **c})
    lomo = pd.DataFrame(rows)
    no_lunar = r[~r["lunar"]]
    return lomo, pd.DataFrame(contrast_rows), no_lunar


def chart_robustness(r: pd.DataFrame, lomo: pd.DataFrame, no_lunar: pd.DataFrame) -> pd.DataFrame:
    fig, ax = plt.subplots(1, 2, figsize=(16, 5.5), sharey=True)
    rows = []
    for a, (x, y) in zip(ax, LINKS[:2]):
        key = f"{x}->{y}"
        full = slopes.by_group(r, f"{x}_res", f"{y}_res", "season").set_index("season").loc[SEASONS]
        lunar = slopes.by_group(no_lunar, f"{x}_res", f"{y}_res", "season").set_index("season").loc[SEASONS]
        spread = lomo[lomo["link"] == key].pivot(index="season", columns="left out", values="slope").loc[SEASONS]
        for column in spread:
            a.plot(range(4), spread[column], "-", color="#bbb", lw=0.8)
        a.errorbar(np.arange(4) - 0.05, full["slope"], yerr=[full["slope"] - full["low"], full["high"] - full["slope"]],
                   fmt="o-", capsize=3, color=COLOURS[x], label="all weeks, all markets")
        a.errorbar(np.arange(4) + 0.05, lunar["slope"], yerr=[lunar["slope"] - lunar["low"], lunar["high"] - lunar["slope"]],
                   fmt="s--", capsize=3, color="k", label="without Ramadan and Eid weeks")
        a.set_xticks(range(4), [s.replace("_", "\n") for s in SEASONS])
        a.set_title(f"{x} -> {y}: grey lines leave one market out")
        a.axhline(0, color="k", lw=0.5)
        a.grid(alpha=0.3)
        a.legend(fontsize=8)
        for s in SEASONS:
            rows.append({"link": key, "season": s, "all": full.loc[s, "slope"], "LOMO min": spread.loc[s].min(),
                         "LOMO max": spread.loc[s].max(), "no lunar": lunar.loc[s, "slope"], "no lunar low": lunar.loc[s, "low"],
                         "no lunar high": lunar.loc[s, "high"], "n no lunar": lunar.loc[s, "n"]})
    plt.tight_layout()
    plt.savefig(data.OUT / "3_robustness.png", dpi=95)
    return pd.DataFrame(rows)


def main() -> None:
    data.OUT.mkdir(exist_ok=True)
    r = frames()
    main_tables, woy_tables = pooled_tables(r["fourier"]), pooled_tables(r["woy"])
    chart_pooled(main_tables, woy_tables)
    markets = market_tables(r["fourier"])
    chart_markets(markets)
    lomo, lomo_contrast, no_lunar = robustness(r["fourier"])
    robust = chart_robustness(r["fourier"], lomo, no_lunar)
    contrast_rows = contrasts(r["fourier"], "fourier, all") + contrasts(no_lunar, "fourier, no lunar weeks") + contrasts(r["woy"], "woy, all")
    out = {"pooled_month": pd.concat([t.assign(link=k) for (g, k), t in main_tables.items() if g == "month"]),
           "pooled_season": pd.concat([t.assign(link=k) for (g, k), t in main_tables.items() if g == "season"]),
           "pooled_half": pd.concat([t.assign(link=k) for (g, k), t in main_tables.items() if g == "half"]),
           "woy_month": pd.concat([t.assign(link=k) for (g, k), t in woy_tables.items() if g == "month"]),
           "markets": markets, "robustness": robust, "lomo_contrast": lomo_contrast, "contrasts": pd.DataFrame(contrast_rows)}
    for name, table in out.items():
        table.to_csv(data.OUT / f"step1_{name}.csv", index=False)
        print(f"\n== {name}\n{table.round(3).to_string(index=False)}")
    print("\nrows", len(r["fourier"]), "markets", r["fourier"]["market"].nunique(), "lunar weeks", int(r["fourier"]["lunar"].sum()))


if __name__ == "__main__":
    main()
