"""Score the held-value rules (fixes.HOLDS) against the shipped twin_daily and write the Israel
follow-up section at the end of results.md (run after report.py, which rewrites the file).

    python experiment/level_memory/fix_report.py   (needs refit.py shipped,drift and the run.py caches)

Domestic rows keep the shipped predictions, so domestic is identical to shipped by construction (checked).
International rows come from the one-market refits with the held value set by each rule.
"""

from __future__ import annotations

import warnings
from typing import Dict, List

import numpy as np
import pandas as pd

import data
import refit
import report
import scoring
import shock
from fixes import HOLDS

SECTION = "## Israel follow-up: the held drift value"
FOLDS = range(7)


def held_predictions(panel: pd.DataFrame, rule: str, fold: int, markets: List[str]) -> pd.Series:
    """International predictions for one fold with the held value of `rule`."""
    fit_end = data.folds("protocol", panel)[fold].train_end
    parts = []
    for market in markets:
        model = refit.load("drift", market, fold)
        kernel = refit.kernel(model, market)
        kernel.held = HOLDS[rule](float(kernel.theta_[-1]), shock.recent_ratio(panel, market, fit_end))
        parts.append(refit.predict(model, market))
    return pd.concat(parts)


def all_predictions(panel: pd.DataFrame) -> Dict[str, list]:
    markets = refit.international_markets(panel)
    shipped = [(report.load("nowcast", "protocol", i)["window"].fold, report.load("nowcast", "protocol", i)["pred"]["guests"]) for i in FOLDS]
    preds = {"nowcast": shipped}
    for rule in HOLDS:
        preds[rule] = []
        for i, (fold, base) in zip(FOLDS, shipped):
            domestic = base[panel.loc[base.index, "market"] == data.DOMESTIC]
            preds[rule].append((fold, pd.concat([domestic, held_predictions(panel, rule, i, markets)])))
    return preds


def held_values(panel: pd.DataFrame, market: str) -> pd.DataFrame:
    folds = data.folds("protocol", panel)
    rows = []
    for i in FOLDS:
        kernel = refit.kernel(refit.load("drift", market, i), market)
        r = shock.recent_ratio(panel, market, folds[i].train_end)
        rows.append({"fold": folds[i].name, "arrivals yoy": r,
                     **{rule: hold(float(kernel.theta_[-1]), r) for rule, hold in HOLDS.items()}})
    return pd.DataFrame(rows)


def selection(part: pd.DataFrame, rules: List[str]) -> List[str]:
    by_fold = scoring.wape_by_fold(part)
    early, late = by_fold.index[:4], by_fold.index[4:]
    pick = by_fold.loc[early, rules].mean().idxmin()
    lines = [f"Chosen on the first 4 folds: `{pick}`."]
    for label, folds in (("first 4 folds", early), ("last 3 folds", late)):
        c = scoring.compare(part[part["fold"].isin(folds)], "nowcast", pick)
        better = int((by_fold.loc[folds, pick] < by_fold.loc[folds, "nowcast"]).sum())
        lines.append(f"`{pick}` vs shipped on the {label}: {c['difference_pp']:+.2f} pp [{c['ci_low']:+.2f}, {c['ci_high']:+.2f}], "
                     f"{better}/{len(folds)} folds better.")
    return lines


def main() -> None:
    warnings.filterwarnings("ignore")
    panel = data.panel()
    panel = panel[panel["date"] <= refit.LAST_TEST_DAY]
    preds = all_predictions(panel)
    frame = scoring.scored(panel, preds)
    names = list(HOLDS)
    domestic = scoring.series(frame, "domestic")
    gap = max(np.nanmax(np.abs(domestic[domestic["model"] == r]["pred"].to_numpy() - domestic[domestic["model"] == "nowcast"]["pred"].to_numpy()))
              for r in names)
    intl = scoring.series(frame, "international")
    table = scoring.table(intl, "nowcast", ["nowcast", *names], "")
    table = table.drop(columns=["R2 vs time"])
    bias = scoring.bias_by_market(intl, ["nowcast", *names]).reset_index()
    bias.columns = [c.replace("nowcast", "shipped") for c in bias.columns]
    israel = intl[intl["market"] == "ISRAEL"].groupby(["model", "fold"])[["pred", "actual"]].sum()
    israel = ((israel["pred"] / israel["actual"] - 1) * 100).unstack("fold").reset_index().rename(columns={"model": "Israel bias %"})
    out = [SECTION, "",
           "International rows only; domestic keeps the shipped predictions (max abs difference "
           f"{gap:.1e}). Each rule changes only the value s(t) is held at beyond the training days of the "
           "chosen drift (`drift_k182_l0.1`). arrivals yoy: mean new arrivals over the last 90 training days "
           "divided by the same 90 days a year earlier (`shock.py`).", "",
           report.md(report.display(table)), "", *selection(intl, names), "",
           "Israel held values per fold:", "", report.md(held_values(panel, "ISRAEL"), 3), "",
           "Israel bias % per fold:", "", report.md(israel, 1), "",
           "Bias by market, international, all folds pooled (folds >5%: folds of 7 with a same-sign bias above 5%):", "",
           report.md(bias, 1), ""]
    text = report.RESULTS.read_text()
    text = text.split(SECTION)[0].rstrip() + "\n\n" + "\n".join(out)
    report.RESULTS.write_text(text)
    print("\n".join(out))


if __name__ == "__main__":
    main()
