"""Score every model on the natural-experiment weeks and on ordinary weeks, export the SHORT-RUN
betas, draw the response curves and write results.md (aggregates only).

    python experiment/scenario_response/report.py     (needs chain_runs.py done)
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

import curves
import data
import lever
import scenario_engines
import short_run
import weekly_runs
from tourism_twin.config import SETTINGS
from tourism_twin.data.panel import training_window
from tourism_twin.models.backtest import compare
from tourism_twin.planning.residual import ResidualMLEngine
from tourism_twin.planning.structural import StructuralEngine

RESULTS = Path(__file__).resolve().parent / "results.md"
MODELS = weekly_runs.MODELS
FLIGHT_MODELS = [m for m in MODELS if m != "TIME-ONLY"]


def md(frame: pd.DataFrame, digits: int = 3) -> str:
    frame = frame.reset_index() if not isinstance(frame.index, pd.RangeIndex) else frame

    def cell(column, v):
        if isinstance(v, (float, np.floating)):
            return "" if np.isnan(v) else (f"{v:.0f}" if column in ("n", "n_weeks", "folds") else f"{v:.{digits}f}")
        return str(v)

    head = "| " + " | ".join(str(c) for c in frame.columns) + " |"
    rule = "| " + " | ".join("---" for _ in frame.columns) + " |"
    return "\n".join([head, rule, *("| " + " | ".join(cell(c, v) for c, v in zip(frame.columns, row)) + " |" for row in frame.itertuples(index=False))])


def checks() -> pd.DataFrame:
    full = training_window(pd.read_parquet(SETTINGS.panel_path))
    refit, shipped = StructuralEngine.calibrate(full), StructuralEngine.load()
    return pd.DataFrame([
        {"check": "refit calibration vs shipped structural_calibration.json (max relative gap)", "value": scenario_engines.calibration_gap(refit, shipped)},
        {"check": "refit residual season means vs shipped residual_engine.pkl (max relative gap)",
         "value": scenario_engines.season_residual_gap(ResidualMLEngine().fit(full, refit), ResidualMLEngine.load())},
        {"check": "flagged scenario copy, all on, vs shipped _international_scenario (max gap / base guests)",
         "value": scenario_engines.shipped_matches_copy(shipped)}])


def rows_by_model(runs: List[dict], mode: str) -> Dict[str, pd.DataFrame]:
    """Per model: every fold's test weeks, restricted to market-week-folds every model scores."""
    weekly = weekly_runs.with_references(data.weekly_panel())
    actual = lever.actual_changes(weekly, mode)
    out = {m: pd.concat([lever.fold_rows(mode, weekly, actual, r[mode]["pred"][m], r[mode]["cf"][m], r["fold"]) for r in runs])
           for m in MODELS}
    keys = None
    for frame in out.values():
        k = set(zip(frame["fold"], frame["market"], frame["week_start"]))
        keys = k if keys is None else keys & k
    for m, frame in out.items():
        mask = [key in keys for key in zip(frame["fold"], frame["market"], frame["week_start"])]
        out[m] = frame[np.array(mask)]
    return out


def event_tables(rows: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    unique = {m: lever.unique_weeks(f[f["event"]]) for m, f in rows.items()}
    summary = pd.DataFrame([{"model": m, "part": part, **lever.summary(g)} for m, ev in unique.items() for part, g in lever.parts(ev).items()])
    by_market = []
    for market, g in unique["LINEAR"].groupby("market"):
        entry = {"market": market, "n": len(g), "up": int((g["ds"] > 0).sum()), "slope actual": lever.summary(g)["slope actual"]}
        for m in MODELS:
            entry[f"{m} slope"] = lever.summary(unique[m][unique[m]["market"] == market])["slope predicted"]
        for m in MODELS:
            entry[f"{m} MAE"] = lever.summary(unique[m][unique[m]["market"] == market])["MAE"]
        by_market.append(entry)
    paired = pd.DataFrame([{"comparison": f"{b} - {a}", "part": part,
                            **lever.paired_difference(lever.parts(unique[a])[part], lever.parts(unique[b])[part])}
                           for a, b in [("LINEAR", "S-CURVE"), ("LINEAR", "S-CURVE %"), ("LINEAR", "SHORT-RUN"), ("LINEAR", "CHAIN"),
                                        ("TIME-ONLY", "LINEAR"), ("TIME-ONLY", "S-CURVE"), ("TIME-ONLY", "SHORT-RUN"), ("TIME-ONLY", "CHAIN")]
                           for part in ("all", "increases", "cuts")])
    levels = []
    for m, ev in unique.items():
        actual = ev["guests"].sum()
        levels.append({"model": m, "n": len(ev), "baseline WAPE": (ev["base"] - ev["guests"]).abs().sum() / actual * 100,
                       "scenario WAPE": (ev["pred"] - ev["guests"]).abs().sum() / actual * 100,
                       "scenario level bias (pct)": (ev["pred"].sum() / actual - 1) * 100})
    return {"summary": summary, "by_market": pd.DataFrame(by_market), "paired": paired, "levels": pd.DataFrame(levels),
            "compare": compare_table(rows, event=True)}


def scored(rows: Dict[str, pd.DataFrame], event: bool) -> pd.DataFrame:
    frames = [f[f["event"] == event].assign(model=m) for m, f in rows.items()]
    out = pd.concat(frames)
    return pd.DataFrame({"fold": out["fold"], "row": out["market"] + "|" + out["week_start"].astype(str), "model": out["model"],
                         "market": out["market"], "date": out["week_start"], "actual": out["guests"], "pred": out["pred"]})


def compare_table(rows: Dict[str, pd.DataFrame], event: bool) -> pd.DataFrame:
    frame = scored(rows, event)
    pairs = [("TIME-ONLY", m) for m in FLIGHT_MODELS] + [("LINEAR", "S-CURVE"), ("LINEAR", "S-CURVE %"), ("LINEAR", "SHORT-RUN"), ("LINEAR", "CHAIN")]
    out = []
    for a, b in pairs:
        c = compare(frame, a, b)
        out.append({"candidate - baseline": f"{b} - {a}", "WAPE diff pp [90% CI]": f"{c['difference_pp']:+.2f} [{c['ci_low']:+.2f}, {c['ci_high']:+.2f}]",
                    "folds same sign": f"{c['share_folds_same_sign']:.2f}"})
    return pd.DataFrame(out)


def ordinary_table(rows: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Ordinary weeks (|ds| <= 15%): weekly level accuracy, unique weeks; R2 against TIME-ONLY."""
    unique = {m: lever.unique_weeks(f[~f["event"]]) for m, f in rows.items()}
    sse_time = float(((unique["TIME-ONLY"]["pred"] - unique["TIME-ONLY"]["guests"]) ** 2).sum())
    out = []
    for m, g in unique.items():
        err = g["pred"] - g["guests"]
        out.append({"model": m, "n": len(g), "WAPE": err.abs().sum() / g["guests"].sum() * 100, "MAE": err.abs().mean(),
                    "RMSE": float(np.sqrt((err ** 2).mean())), "R2 vs TIME-ONLY": 1 - float((err ** 2).sum()) / sse_time})
    return pd.DataFrame(out)


def main() -> None:
    warnings.filterwarnings("ignore")
    weekly = data.weekly_panel()
    sections = ["# Scenario response: results", "",
                "Aggregates only. International markets, VALIDATION_ORIGINS (7 folds, test weeks 2024-02-01 to 2025-01-31). "
                "Every model refitted per fold on weeks before the fold's train_end. FROZEN_TEST is not read.", ""]
    sections += ["## Checks", "", md(checks().assign(value=lambda f: f["value"].map(lambda v: f"{v:.2e}"))), ""]

    ridges = short_run.choose_ridge(weekly, data.folds())
    ridge = float(ridges.loc[ridges["MAE"].idxmin(), "ridge"])
    sections += ["## SHORT-RUN ridge (chosen on VALIDATION_ORIGINS)", "",
                 "MAE of log(guests / centred guest trend) - beta x log(seats / centred seat trend) on every test week.", "",
                 md(ridges, 5), "", f"Chosen ridge: {ridge}.", ""]

    runs = weekly_runs.all_folds(ridge)
    betas = pd.DataFrame({r["fold"].name: r["beta"] for r in runs})
    for mode in weekly_runs.MODES:
        rows = rows_by_model(runs, mode)
        tables = event_tables(rows)
        title = "same week a year earlier" if mode == "yoy" else "centred 13-week trend"
        sections += [f"## Natural experiments against the {title}", "",
                     "MAE and bias on log guest change; slopes against log seat change (through 0); 'actual on predicted' is the "
                     "slope of the actual change on the predicted one (1 is calibrated). Unique market-weeks.", "",
                     md(tables["summary"]), "", "### Paired differences (block bootstrap, 4-week blocks, 90%)", "",
                     md(tables["paired"]), "", "### Levels on the same weeks", "", md(tables["levels"], 2), "",
                     "compare() on scenario-week guest levels (per-fold rows, 28-day blocks):", "", md(tables["compare"]), "",
                     "### Per market (all event weeks)", "", md(tables["by_market"], 2), ""]
        if mode == "yoy":
            sections += ["## Ordinary weeks (|seat change vs last year| <= 15%)", "",
                         "Weekly guest levels on unique market-weeks; R2 = 1 - SSE / SSE of TIME-ONLY.", "",
                         md(ordinary_table(rows), 3), "", "compare() on the same weeks:", "", md(compare_table(rows, event=False)), ""]

    export = short_run.ShortRun(ridge).fit(weekly)
    table = export.bootstrap()
    table.to_csv(data.OUT / "short_run_beta.csv", index=False)
    sections += ["## SHORT-RUN betas", "",
                 "Fitted on every week up to 2025-01-31, 90% moving-block bootstrap (4-week blocks within market). "
                 f"Markets under {short_run.MIN_WEEKS} usable weeks take the pooled value. Exported to out/short_run_beta.csv.", "",
                 md(table, 2), "", "Per fold (training window of each origin):", "", md(betas.round(2).rename_axis("market"), 2), ""]
    sections += ["## Co-movement of guest trend with seat trend (association, not effect)", "",
                 "Slope of the 52-week change in log centred 13-week guest trend on the same change in seats; 90% block bootstrap, "
                 "13-week blocks. Weeks overlap heavily, so the effective sample is small.", "",
                 md(short_run.co_movement(weekly), 2), ""]

    frame = curves.curves(ridge)
    paths = [curves.chart(frame, mode) for mode in weekly_runs.MODES]
    pivot = frame[frame["seat_change"].isin([-0.5, -0.2, -0.1, 0.1, 0.2, 0.5, 1.0])].set_index(["market", "seat_change"])
    sections += ["## Response curves (last fold)", "", "Guest change for a seat change applied to the whole test period.", "",
                 md(pivot.reset_index(), 3), "", *[f"- `{Path(p).relative_to(Path(__file__).resolve().parent)}`" for p in paths], ""]
    RESULTS.write_text("\n".join(sections))
    print("wrote", RESULTS)



if __name__ == "__main__":
    main()
