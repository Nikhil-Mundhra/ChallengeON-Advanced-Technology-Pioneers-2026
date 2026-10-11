"""Write results.md: the Step 1 tables (from graphs.py and chain_residual.py), the gate on
VALIDATION_ORIGINS, the selection check, the learned strengths and the natural-experiment back-test.

    python experiment/seasonal_link/report.py      (needs graphs.py, chain_residual.py and run.py done)
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd

import backtest
import data
import scoring
import strengths
from tourism_twin.domain.seasons import SEASONS
from variants import SHIPPED, SPECS

RESULTS = Path(__file__).resolve().parent / "results.md"
FOLDS = [str(i) for i in range(7)]
SEASONAL = [name for name in SPECS if name != SHIPPED]
# The least-shrunk season variant is shown too: it learns the largest strengths, so it tests whether a
# strong seasonal response helps the lever even where it costs level accuracy.
FREEST = "season_r0.001"


def md(frame: pd.DataFrame, digits: int = 2) -> str:
    def cell(v):
        if isinstance(v, (float, np.floating)):
            return "" if np.isnan(v) else f"{v:.{digits}f}"
        return str(v)
    head = "| " + " | ".join(str(c) for c in frame.columns) + " |"
    rule = "| " + " | ".join("---" for _ in frame.columns) + " |"
    return "\n".join([head, rule, *("| " + " | ".join(cell(v) for v in row) + " |" for row in frame.itertuples(index=False))])


def interval(frame: pd.DataFrame, value: str, low: str, high: str, label: str, digits: int = 2, sign: str = "+") -> pd.DataFrame:
    frame = frame.copy()
    f = f"{sign}.{digits}f"
    frame[label] = [f"{v:{f}} [{lo:{f}}, {hi:{f}}]" if pd.notna(v) else ""
                    for v, lo, hi in zip(frame[value], frame[low], frame[high])]
    return frame.drop(columns=[value, low, high])


def step_one() -> list:
    read = lambda name: pd.read_csv(data.OUT / f"step1_{name}.csv")  # noqa: E731
    season = read("pooled_season")
    season = season[season["link"] != "arrivals->guests"].assign(season=lambda f: pd.Categorical(f["season"], SEASONS)).sort_values(["link", "season"])
    month = read("pooled_month")
    month = month[month["link"] != "arrivals->guests"]
    chain = read("chain_residual")
    chain = chain[chain["by"] == "season"].assign(group=lambda f: pd.Categorical(f["group"], SEASONS)).sort_values(["target", "group"])
    return ["## Step 1: graphs", "",
            "Weekly residuals after a centred 13-week trend and a 4-harmonic annual season, per market, 2023-01 to 2025-01-31. "
            "Slopes pooled over 20 markets, 90% week-cluster bootstrap.", "",
            "### By season", "", md(interval(season, "slope", "low", "high", "slope [90%]")[["link", "season", "n", "slope [90%]", "corr", "sd x"]]), "",
            "### By month", "", md(interval(month, "slope", "low", "high", "slope [90%]")[["link", "month", "n", "slope [90%]", "corr"]]), "",
            "### Contrasts", "", md(interval(read("contrasts"), "difference", "low", "high", "difference [90%]")), "",
            "### Robustness by season", "", "LOMO: leave one market out, range over the 20 runs. No lunar: weeks touching Ramadan or an Eid window removed.", "",
            md(read("robustness")), "",
            "### Six largest markets", "", md(interval(read("markets"), "slope", "low", "high", "slope [90%]")
                                             [["market", "link", "season", "n", "slope [90%]", "H1-H2"]]), "",
            "### Chain link 1 in sample, by season", "",
            "Slope on the weekly seat deviation from its centred 13-week trend. actual = model + residual.", "",
            md(interval(chain, "slope", "low", "high", "slope [90%]")[["target", "group", "n", "slope [90%]"]]), ""]


def gate() -> tuple:
    names = [SHIPPED, *SEASONAL]
    daily = scoring.daily_rows(names)
    weekly = scoring.weekly_rows(daily)
    folds_daily, folds_weekly = scoring.by_fold(daily), scoring.by_fold(weekly)
    pick = scoring.choose(folds_daily, SEASONAL)
    grid = pd.DataFrame({"variant": SEASONAL, "daily WAPE": folds_daily[SEASONAL].mean().to_numpy(),
                         "weekly WAPE": folds_weekly[SEASONAL].mean().to_numpy()})
    shown = list(dict.fromkeys([SHIPPED, pick["best"], pick["simplest"]]))
    d = interval(scoring.table(daily, SHIPPED, names), "delta", "low", "high", "delta pp [90%]")
    w = interval(scoring.table(weekly, SHIPPED, names), "delta", "low", "high", "delta pp [90%]")
    check = scoring.selection_check(daily, SHIPPED, SEASONAL)
    bias = scoring.level_bias(daily, shown).reset_index()
    lines = ["## Step 2: gate on VALIDATION_ORIGINS (international, 7 folds)", "",
             f"Shipped chain: daily WAPE {folds_daily[SHIPPED].mean():.2f}, weekly {folds_weekly[SHIPPED].mean():.2f}. "
             f"Best seasonal variant `{pick['best']}`, simplest within {scoring.SIMPLER_WITHIN_PP} pp `{pick['simplest']}`. "
             "delta: compare() against the shipped chain, pp, negative is better. Gate: delta <= -0.3 pp, interval below 0, 4 of 7 folds better.", "",
             "### Grid, mean WAPE over folds", "", md(grid), "",
             "### Daily market-day WAPE", "", md(d), "", "### Weekly market-week WAPE", "", md(w), "",
             f"Selection check: chosen on the first 4 folds only, `{check['pick']}`; on the last 3 folds "
             f"{check['delta']:+.2f} pp [{check['low']:+.2f}, {check['high']:+.2f}].", "",
             "### Level bias % by fold (daily rows)", "", md(bias, 1), "",
             "### WAPE by fold (daily)", "", md(folds_daily[shown].reset_index()), ""]
    return lines, {**pick, "early": check["pick"]}


def implied_by_graphs() -> pd.Series:
    """Per season, the strength the step 1(d) graph asks for: actual / chain-model slope of the weekly
    arrival deviation on the seat deviation (above 1: the chain responds too little in that season)."""
    chain = pd.read_csv(data.OUT / "step1_chain_residual.csv")
    chain = chain[chain["by"] == "season"].pivot(index="group", columns="target", values="slope").loc[SEASONS]
    return chain["actual"] / chain["model"]


def strength_lines(variant: str) -> list:
    pooled = strengths.pooled(variant, FOLDS)
    pooled["graph: actual / model slope"] = implied_by_graphs().to_numpy()
    pooled = interval(pooled, "median", "low", "high", "median [90% over markets]", sign="")
    month = strengths.median_with_interval(strengths.by_month(variant, "full"))
    month = interval(month.rename_axis("month").reset_index(), "median", "low", "high", "median [90%]", sign="")
    return [f"## Learned strengths, `{variant}`", "",
            "exp(a) per season on the full fit (every guest day to 2025-01-31), median over 20 markets with a 90% bootstrap over "
            "markets; fold min and max: range of the 7 fold-fit medians.", "", md(pooled), "",
            "By month (mid-month value, full fit):", "", md(month), "",
            "Six largest markets, full fit (min to max over the 7 fold fits):", "", md(strengths.markets(variant, FOLDS)), ""]


def back_test(models: dict) -> list:
    lines = ["## Natural-experiment back-test", "",
             "Lever code from experiment/scenario_response. MAE and bias on log guest change; paired differences use a 4-week "
             "moving-block bootstrap, 90%. Season of the week's Thursday.", ""]
    shipped_label = "CHAIN"
    pairs = [(shipped_label, label) for label in models if label != shipped_label]
    pairs += [(backtest.TIME_ONLY, label) for label in models]
    for mode in backtest.MODES:
        rows = backtest.rows_by_model(models, mode)
        events = backtest.event_weeks(rows)
        title = "same week a year earlier" if mode == "yoy" else "centred 13-week trend"
        table = backtest.summary(events)[["model", "part", "n", "MAE", "bias", "slope actual", "slope predicted", "slope seat-only"]]
        lines += [f"### Against the {title}", "", md(table, 3), "", "Paired MAE differences:", "",
                  md(backtest.paired(events, pairs)[["comparison", "part", "n", "MAE diff [90% CI]"]]), ""]
    return lines


def main() -> None:
    warnings.filterwarnings("ignore")
    out = ["# Seasonal link: results", "",
           "Aggregates only. International markets. Data to 2025-01-31; FROZEN_TEST is not read. Written by `report.py`.", ""]
    out += step_one()
    lines, pick = gate()
    out += lines
    shown = list(dict.fromkeys([pick["simplest"], pick["best"], pick["early"], FREEST]))
    for variant in shown:
        if (data.OUT / "runs" / f"{variant}__full.pkl").exists():
            out += strength_lines(variant)
    models = {"CHAIN": SHIPPED, **{f"SEASONAL {v}": v for v in shown}}
    out += back_test(models)
    RESULTS.write_text("\n".join(out))
    print("\n".join(out))


if __name__ == "__main__":
    main()
