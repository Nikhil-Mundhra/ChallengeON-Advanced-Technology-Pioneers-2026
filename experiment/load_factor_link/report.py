"""Score the cached runs (run.py) and write results.md: chain accuracy against BASE with compare(),
link-0 accuracy, lever response, coefficients, residual checks and scenario sanity.

    python experiment/load_factor_link/report.py
"""

from __future__ import annotations

import pickle
import warnings
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from tourism_twin.models.backtest import compare

import coefficients
import data
import lever
import residuals
import scenarios
from passengers_link import LogitLoadFactor, ScheduleInputs, TrendResponse, UCurve
from run import SCENARIO_FOLD, folds
from variants import DIAGNOSTIC, LINK0

ORDER = ("BASE", "A", "A_updown", "A2", "L", "TS", "B", "C", "A_oracle")
LINK0_VARIANTS = ("A", "A_updown", "A2", "L", "TS", "B", "C")
BIAS_MARKETS = ("UNITED KINGDOM", "CHINA", "PHILIPPINES", "OTHER_EURASIA")
LF_BANDS = {"<75": (0.0, 0.75), "75-85": (0.75, 0.85), "85-92": (0.85, 0.92), ">92": (0.92, 2.0)}
SEAT_MOVE = 0.14
GATE_PP = 0.3
RESULTS = Path(__file__).resolve().parent / "results.md"


def load(name: str) -> List[dict]:
    runs = []
    for i in range(7):
        with open(data.OUT / "runs" / f"{name}__{i}.pkl", "rb") as handle:
            record = pickle.load(handle)
        record.pop("model", None)
        runs.append(record)
    return runs


def md(frame: pd.DataFrame, digits: int = 2, index: str = "") -> str:
    if not isinstance(frame.index, pd.RangeIndex):
        names = [index] if frame.index.nlevels == 1 and index else [n or index or f"key{i}" for i, n in enumerate(frame.index.names)]
        frame = frame.rename_axis(names).reset_index()
    integer = {c for c in frame.columns if c in ("n", "markets", "fold") or str(c).startswith("markets at")}

    def cell(column, v):
        if isinstance(v, (float, np.floating)):
            return "" if np.isnan(v) else (f"{v:.0f}" if column in integer else f"{v:.{digits}f}")
        return str(v)

    head = "| " + " | ".join(str(c) for c in frame.columns) + " |"
    rule = "| " + " | ".join("---" for _ in frame.columns) + " |"
    body = ["| " + " | ".join(cell(c, v) for c, v in zip(frame.columns, row)) + " |" for row in frame.itertuples(index=False)]
    return "\n".join([head, rule, *body])


# --- prediction frames -------------------------------------------------------------------------
def scored(panel: pd.DataFrame, runs: Dict[str, List[dict]], column: str, actual: str) -> pd.DataFrame:
    """compare() rows (fold, row, model, market, date, actual, pred) on each fold's test days, kept
    only where every model in `runs` predicts."""
    frames = []
    for name, records in runs.items():
        for record in records:
            fold = record["fold"]
            test = panel[panel[actual].notna() & (panel["date"] >= fold.test_start) & (panel["date"] <= fold.test_end)]
            frames.append(pd.DataFrame({"fold": fold.name, "row": test.index, "model": name, "market": test["market"].to_numpy(),
                                        "date": test["date"].to_numpy(), "actual": test[actual].to_numpy(),
                                        "pred": record["pred"][column].reindex(test.index).to_numpy()}))
    out = pd.concat(frames)
    everyone = out.groupby(["fold", "row"])["pred"].transform(lambda s: s.notna().all())
    return out[everyone]


def weekly_scored(daily: pd.DataFrame) -> pd.DataFrame:
    keyed = daily.assign(week_start=data.week_start(daily["date"]))
    grouped = keyed.groupby(["fold", "model", "market", "week_start"])
    out = grouped.agg(actual=("actual", "sum"), pred=("pred", "sum"), days=("pred", "size")).reset_index()
    out = out[out["days"] == 7].drop(columns="days").rename(columns={"week_start": "date"})
    out["row"] = out["market"] + "|" + out["date"].astype(str)
    return out


def weekly_series(panel: pd.DataFrame, daily: pd.Series) -> pd.Series:
    """Weekly sums of a daily series on `panel`'s rows, complete weeks only, by (market, week_start)."""
    keyed = pd.DataFrame({"market": panel["market"], "week_start": data.week_start(panel["date"]), "v": daily.reindex(panel.index)})
    grouped = keyed.groupby(["market", "week_start"])["v"]
    return grouped.sum()[grouped.count() == 7]


# --- tables ------------------------------------------------------------------------------------
def wape_by_fold(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.groupby(["model", "fold"]).apply(lambda x: (x["pred"] - x["actual"]).abs().sum() / x["actual"].sum() * 100).unstack("model")


def accuracy(daily: pd.DataFrame, weekly: pd.DataFrame, names: List[str]) -> pd.DataFrame:
    rows = []
    folds_d, folds_w = wape_by_fold(daily), wape_by_fold(weekly)
    for name in names:
        row = {"variant": name, "daily WAPE": folds_d[name].mean(), "weekly WAPE": folds_w[name].mean(),
               "level bias (pct)": (daily.loc[daily["model"] == name, "pred"].sum() / daily.loc[daily["model"] == name, "actual"].sum() - 1) * 100}
        if name != "BASE":
            for grain, frame, by_fold in (("daily", daily, folds_d), ("weekly", weekly, folds_w)):
                c = compare(frame, "BASE", name)
                row[f"{grain} delta pp [90% CI]"] = f"{c['difference_pp']:+.2f} [{c['ci_low']:+.2f}, {c['ci_high']:+.2f}]"
                row[f"{grain} folds better"] = f"{int((by_fold[name] < by_fold['BASE']).sum())}/{len(by_fold)}"
                row[f"_{grain}"] = c
        rows.append(row)
    return pd.DataFrame(rows)


def gate(row: pd.Series) -> str:
    if row["variant"] == "BASE":
        return ""
    if row["variant"] in DIAGNOSTIC:
        return "diagnostic"
    verdicts = []
    for grain in ("daily", "weekly"):
        c = row[f"_{grain}"]
        better = int(row[f"{grain} folds better"].split("/")[0])
        ok = c["difference_pp"] <= -GATE_PP and c["ci_high"] < 0 and better >= 4
        verdicts.append(ok)
    return "pass" if all(verdicts) else ("pass daily only" if verdicts[0] else ("pass weekly only" if verdicts[1] else "fail"))


def link0_accuracy(panel: pd.DataFrame, runs: Dict[str, List[dict]]) -> pd.DataFrame:
    p2p = scored(panel.assign(p2p_actual=panel["p2p"].where(panel["seats"].notna())), runs, "p2p", "p2p_actual")
    p2p_week = weekly_scored(p2p)
    seats_week = weekly_series(panel, panel["seats"])
    rows = []
    for name in runs:
        d, w = p2p[p2p["model"] == name], p2p_week[p2p_week["model"] == name]
        seats = seats_week.reindex(pd.MultiIndex.from_arrays([w["market"], w["date"]])).to_numpy()
        ok = seats > 0
        error_pp = 100 * (w["pred"].to_numpy()[ok] - w["actual"].to_numpy()[ok]) / seats[ok]
        rows.append({"variant": name, "P2P WAPE daily": wape_by_fold(d)[name].mean(), "P2P WAPE weekly": wape_by_fold(w)[name].mean(),
                     "P2P bias (pct)": (d["pred"].sum() / d["actual"].sum() - 1) * 100,
                     "LF error MAE (pp)": np.abs(error_pp).mean(), "LF error bias (pp)": error_pp.mean()})
    return pd.DataFrame(rows)


def lever_tables(panel: pd.DataFrame, runs: Dict[str, List[dict]], column: str, actual_column: str) -> Dict[str, pd.DataFrame]:
    weekly = data.weekly(panel[panel["seats"].notna()], ["seats", actual_column])
    windows = [(r["fold"].test_start, r["fold"].test_end) for r in next(iter(runs.values()))]
    events = {}
    for name, records in runs.items():
        preds = [weekly_series(panel, r["pred"][column]) for r in records]
        if all(p.isna().all() or p.empty for p in preds):
            continue
        cfs = [weekly_series(panel, r["cf"][column]) for r in records]
        events[name] = lever.events(weekly, actual_column, preds, cfs, windows).set_index(["market", "week_start"])
    common = set.intersection(*[set(ev.index) for ev in events.values()])  # weeks every variant scores
    return {name: lever.summarize(ev[ev.index.isin(common)].reset_index()) for name, ev in events.items()}


def actual_pax_lever(panel: pd.DataFrame) -> pd.DataFrame:
    """Actual pax and P2P response slopes on the same lever weeks (no model)."""
    weekly = data.weekly(panel[panel["seats"].notna()], ["seats", "pax", "p2p"])
    rows = {}
    for column in ("pax", "p2p"):
        changes = lever.year_on_year(weekly, column)
        changes["act"] = changes["dy"] - lever.drift(changes, "dy")
        test = changes[(changes["week_start"] >= "2024-02-01") & (changes["week_start"] <= "2025-01-31") & (changes["ds"].abs() > lever.THRESHOLD)]
        for side, part in (("up", test[test["ds"] > 0]), ("down", test[test["ds"] < 0])):
            rows[(column, side)] = {"n": len(part), "slope_act": float(part["ds"] @ part["act"] / (part["ds"] @ part["ds"]))}
    return pd.DataFrame(rows).T


def betas_by_fold(runs: Dict[str, List[dict]]) -> pd.DataFrame:
    rows = []
    for name in [n for n in ("A", "A_updown", "A2", "TS", "L") if n in runs]:
        for i, record in enumerate(runs[name]):
            if name == "L":
                b = record["link0"].slopes()["b"]
                rows.append({"variant": name, "fold": i, "median b (logit)": b.median()})
                continue
            model: TrendResponse = record["link0"]
            table = model.betas()
            row = {"variant": name, "fold": i}
            for column in [c for c in table.columns if not c.endswith("_unpooled") and c != "beta_down_at_market_lf"]:
                row[f"median {column}"] = table[column].median()
                row[f"markets at 1 ({column})"] = int((table[column] > 0.999).sum())
            if model.slopes == "usual_lf":
                row["gamma"] = model.gamma_
            rows.append(row)
    return pd.DataFrame(rows)


PER_MARKET = {
    "A": lambda m: m.betas(),
    "A_updown": lambda m: m.betas()[["beta_up", "beta_down", "beta_up_unpooled", "beta_down_unpooled"]],
    "A2": lambda m: m.betas()[["beta_up", "beta_down_at_market_lf"]],
    "TS": lambda m: m.betas()[["beta", "beta_long"]],
    "L": lambda m: m.slopes()[["b"]],
    "C": lambda m: m.coefficients()[["flights", "gauge", "airlines", "premium_share"]],
}


def per_market(runs: Dict[str, List[dict]]) -> pd.DataFrame:
    parts = [table(runs[name][SCENARIO_FOLD]["link0"]).add_prefix(f"{name} ") for name, table in PER_MARKET.items() if name in runs]
    return pd.concat(parts, axis=1)


def logit_asymmetry(panel: pd.DataFrame, model: LogitLoadFactor, train_end: pd.Timestamp) -> pd.DataFrame:
    """P2P slope implied by L's sigmoid for a 14% seat cut and increase, per market at its training P2P
    rate, averaged within the market's usual total-pax LF band."""
    train = panel[(panel["date"] < train_end) & (panel["seats"] > 0)]
    by_market = train.groupby("market")
    rate, usual = by_market["p2p"].sum() / by_market["seats"].sum(), by_market["pax"].sum() / by_market["seats"].sum()
    b = model.slopes()["b"]
    rows = []
    for market in b.index:
        row = {"market": market, "usual LF": usual[market], "P2P rate": rate[market], "b": b[market]}
        for label, move in (("cut", -SEAT_MOVE), ("increase", SEAT_MOVE)):
            x = np.log(1 + move)
            logit = np.log(rate[market] / (1 - rate[market])) + b[market] * x
            new_rate = 1 / (1 + np.exp(-logit))
            row[f"slope {label}"] = np.log((1 + move) * new_rate / rate[market]) / x
        rows.append(row)
    table = pd.DataFrame(rows)
    band = pd.cut(table["usual LF"], [v[0] for v in LF_BANDS.values()] + [2.0], labels=list(LF_BANDS))
    return table.groupby(band, observed=True).agg(markets=("market", "size"), usual_lf=("usual LF", "mean"), p2p_rate=("P2P rate", "mean"),
                                                   b=("b", "mean"), slope_cut=("slope cut", "mean"), slope_increase=("slope increase", "mean"))


def guest_bias(daily: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Guests level bias (pct): per fold, and per market for the markets with the largest BASE bias."""
    pct = lambda x: (x["pred"].sum() / x["actual"].sum() - 1) * 100  # noqa: E731
    by_fold = daily.groupby(["model", "fold"]).apply(pct).unstack("fold")
    by_market = daily[daily["market"].isin(BIAS_MARKETS)].groupby(["model", "market"]).apply(pct).unstack("market")
    order = [n for n in ORDER if n in by_fold.index]
    return {"per fold": by_fold.loc[order], "per market": by_market.loc[order]}


def residual_summary(checks: Dict[str, dict]) -> pd.DataFrame:
    rows = []
    for name, c in checks.items():
        rows.append({"variant": name, "1 bias: flagged bins": len(c["flagged"]), "1 pass": c["check1"],
                     "2 ACF day 1 / 7": f"{c['acf_day_1']:.2f} / {c['acf_day_7']:.2f}", "2 ACF week 1 / 4": f"{c['acf_week_1']:.2f} / {c['acf_week_4']:.2f}",
                     "2 LB p>=0.05 share (week)": c["lb_ok_week"], "2 pass": c["check2"],
                     "3 sd ratio level / seat": f"{c['sd_ratio_level']:.2f} / {c['sd_ratio_seat']:.2f}",
                     "4 skew / ex.kurt (week)": f"{c['week']['skew']:.2f} / {c['week']['excess_kurtosis']:.2f}",
                     "4 beyond 3 sd (week)": c["week"]["beyond_3sd"],
                     "clean": c["check1"] and c["check2"]})
    return pd.DataFrame(rows)


def main() -> None:
    warnings.filterwarnings("ignore")
    panel = data.panel()
    names = [n for n in ORDER if all((data.OUT / "runs" / f"{n}__{i}.pkl").exists() for i in range(7))]
    runs = {n: load(n) for n in names}
    sections: List[str] = ["# Load factor link: results", "",
                           "International markets, VALIDATION_ORIGINS (7 folds), each variant fitted on the fold's training window. "
                           "Aggregate metrics only. Written by `report.py` from the runs cached by `run.py`.", ""]

    daily = scored(panel, runs, "guests", "guests")
    weekly = weekly_scored(daily)
    table = accuracy(daily, weekly, names)
    table["gate"] = table.apply(gate, axis=1)
    link0 = link0_accuracy(panel, {n: runs[n] for n in names if n != "BASE"})
    sections += ["## Guests: chain accuracy against BASE", "",
                 "Delta is candidate minus BASE WAPE (pp, negative is better) from compare(). Gate: delta <= -0.3 pp, CI excludes 0, better in at least 4 of 7 folds, on both grains. A_oracle reads realized P2P and is not deployable.", "",
                 md(table[[c for c in table.columns if not c.startswith("_")]]), "",
                 "## Link 0: P2P accuracy on test days", "",
                 "LF here is P2P per seat (the rate link 0 predicts); error in percentage points per market-week.", "",
                 md(link0), ""]

    sections += ["## Lever: guests", "",
                 f"Weeks with seats moved more than 15% against a year earlier, each market-week once (prediction averaged over the folds that score it). "
                 f"Drift baseline: same market-year quiet weeks when at least {lever.MIN_QUIET}, else the trailing 52-week median. "
                 "Only weeks every variant scores. slope_seat_only: the model's pure seat response (test period re-predicted on last year's schedule). The down weeks come from a few episodes (Israel, Oman, China, Kuwait, France); treat them as a guard against harm, not a ranking.", ""]
    for name, t in lever_tables(panel, runs, "guests", "guests").items():
        sections += [f"### {name}", "", md(t, 3, "weeks"), ""]
    sections += ["## Lever: P2P", "", "Same weeks and rules on P2P itself. Actual slopes of pax and P2P on the lever weeks:", "", md(actual_pax_lever(panel).rename_axis(["series", "weeks"]), 3), ""]
    for name, t in lever_tables(panel, {n: runs[n] for n in names if n not in ("BASE",)}, "p2p", "p2p").items():
        sections += [f"### {name} (P2P)", "", md(t, 3, "weeks"), ""]

    train_end = folds(panel)[SCENARIO_FOLD].train_end
    train = panel[panel["guests"].notna() & (panel["date"] < train_end)]
    sections += ["## Link 0 coefficients", "",
                 "Descriptive: market-weeks against their own centred 13-week trend, before 2025-02 (no model). rate_move: change of pax or P2P per seat, pp per +10% seats.", "",
                 md(coefficients.descriptive_slopes(panel, pd.Timestamp("2025-02-01")).rename_axis(["series", "weeks"]), 3), "",
                 "Fitted per fold (median over markets; markets at 1: beta on its upper bound):", "",
                 md(betas_by_fold(runs), 3), "",
                 f"Intervals on the last fold's training window (to {train_end.date()}), 90%, delete-half 28-day block jackknife, {coefficients.DRAWS} draws:", ""]
    for label, make, summary in (("A", lambda: TrendResponse(**LINK0), coefficients.median_betas),
                                 ("A_updown", lambda: TrendResponse(slopes="split", **LINK0), coefficients.median_betas),
                                 ("A2", lambda: TrendResponse(slopes="usual_lf", **LINK0), coefficients.median_betas),
                                 ("TS", lambda: TrendResponse(long_run=True, **LINK0), coefficients.median_betas),
                                 ("L", lambda: LogitLoadFactor(**LINK0), lambda m: m.slopes()[["b"]].median().add_prefix("median ")),
                                 ("C", lambda: ScheduleInputs(**LINK0), coefficients.median_coefficients)):
        sections += [f"### {label}", "", md(coefficients.interval(train, make, summary), 3, "coefficient"), ""]
    sections += ["Per market, last fold (A beta with and without pooling; A_updown; A2 beta_down at the market's usual LF; C coefficients):", "",
                 md(per_market(runs), 2, "market"), ""]
    sections += ["## C: independence of the detrended inputs", "", f"Last fold's training window, daily deviations from each input's trailing 91-day mean.", ""]
    for label, frame in coefficients.independence(train).items():
        sections += [f"{label}:", "", md(frame, 2, "input"), ""]
    if "L" in runs:
        sections += ["## L: does the sigmoid alone give the cut and increase asymmetry?", "",
                     f"Implied P2P slope for a {SEAT_MOVE:.0%} seat cut and increase at each market's training P2P rate, by usual total-pax LF band (last fold). "
                     "Measured total-pax cut slopes by band were 0.51 / 0.77 / 0.93 / 0.97, increases 0.89 to 0.98.", "",
                     md(logit_asymmetry(panel, runs["L"][SCENARIO_FOLD]["link0"], train_end).reset_index(), 3), ""]
    biases = guest_bias(daily)
    sections += ["## Guests level bias", "", "Per fold (pct):", "", md(biases["per fold"], 1), "", "Per market, all folds (pct):", "", md(biases["per market"], 1), ""]
    curve = runs["B"][SCENARIO_FOLD]["link0"].curve() if "B" in runs else None
    if curve is not None:
        sections += ["## B: the learned U (last fold)", "", md(curve, 3), ""]

    checks = {n: residuals.check(n, panel, runs[n], data.OUT / "residuals") for n in LINK0_VARIANTS if n in runs}
    sections += ["## Link 0 residual checks", "", " ".join(residuals.__doc__.strip().split("\n\n")[1].split()), "",
                 "Charts: `out/residuals/<variant>_*.png` (not committed).", "", md(residual_summary(checks), 2), ""]
    for name, c in checks.items():
        if c["flagged"]:
            worst = sorted(c["flagged"], key=lambda f: -abs(float(f.rsplit("(", 1)[1].rstrip(")"))))[:8]
            sections += [f"{name}: {len(c['flagged'])} flagged bins, the largest (mean log residual):", "", *[f"- {f}" for f in worst], ""]

    scen = scenarios.table([n for n in names if n != "A_oracle"])
    sections += ["## Scenario sanity", "",
                 f"Last fold's models, seats +-10% on {scenarios.START.date()}..{scenarios.END.date()}. P2P and LF (P2P per seat) over the window; arrivals and guests over the window plus {scenarios.TAIL_DAYS} days (pct). "
                 "via: C reads flights and gauge separately; other variants see seats only.", "", md(scen, 2), ""]
    RESULTS.write_text("\n".join(sections))
    print("\n".join(sections))


if __name__ == "__main__":
    main()
