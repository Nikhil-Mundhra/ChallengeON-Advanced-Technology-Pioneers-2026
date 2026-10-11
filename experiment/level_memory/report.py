"""Score the cached runs (run.py) and write results.md: carry-forward on the nowcast and the chain,
the drift grid, the combination, the time-only control and the bias by market.

    python experiment/level_memory/report.py
"""

from __future__ import annotations

import pickle
import warnings
from pathlib import Path
from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd

import carry
import data
import scoring
from run import CHOSEN_DRIFT, path
from variants import DRIFT_HALF_LIVES, DRIFT_KNOTS, DRIFT_LAMBDAS, drift_name

RESULTS = Path(__file__).resolve().parent / "results.md"
SIMPLER_WITHIN_PP = 0.2
SERIES = ("domestic", "international")
FOLDS = range(7)


def load(model: str, splitter: str, i: int, held_back: bool = False) -> dict:
    with open(path((model, splitter, i, held_back)), "rb") as handle:
        return pickle.load(handle)


def md(frame: pd.DataFrame, digits: int = 2) -> str:
    def cell(v):
        if isinstance(v, (float, np.floating)):
            return "" if np.isnan(v) else f"{v:.{digits}f}"
        return str(v)
    head = "| " + " | ".join(str(c) for c in frame.columns) + " |"
    rule = "| " + " | ".join("---" for _ in frame.columns) + " |"
    body = ["| " + " | ".join(cell(v) for v in row) + " |" for row in frame.itertuples(index=False)]
    return "\n".join([head, rule, *body])


def display(frame: pd.DataFrame) -> pd.DataFrame:
    """compare() columns folded into one 'delta pp [90% CI]' cell."""
    frame = frame.copy()
    if "delta pp" in frame:
        frame.insert(2, "delta pp [90% CI]", [f"{d:+.2f} [{lo:+.2f}, {hi:+.2f}]" if pd.notna(d) else ""
                                               for d, lo, hi in zip(frame["delta pp"], frame["ci low"], frame["ci high"])])
        frame["folds better"] = [f"{int(v)}/7" if pd.notna(v) else "" for v in frame["folds better"]]
        frame = frame.drop(columns=["delta pp", "ci low", "ci high"])
    return frame.fillna("")


# --- carry-forward ---------------------------------------------------------------------------
def carried(panel: pd.DataFrame, model: str, splitter: str, settings: List[carry.Setting],
            main: Optional[Callable[[int], dict]] = None, held_back: Optional[Callable[[int], dict]] = None):
    """model -> [(fold, prediction)] for the model and every carry-forward setting, plus the memory per fold and series."""
    main = main or (lambda i: load(model, splitter, i))
    held_back = held_back or (lambda i: load(model, splitter, i, True))
    preds: Dict[str, list] = {model: []}
    memories = []
    for i in FOLDS:
        record, hb = main(i), held_back(i)
        window, pred = record["window"], record["pred"]["guests"]
        preds[model].append((window.fold, pred))
        later = pred[panel.loc[pred.index, "date"] > window.last_known]
        test = panel.loc[later.index, ["market", "date"]]
        adjusted = {s.name: pd.Series(0.0, index=later.index) for s in settings}
        for name in SERIES:
            markets = panel["market"].isin(test["market"][data.series_of(test["market"]) == name].unique())
            if not markets.any():
                continue
            part = panel[markets]
            mem = carry.memory(part, window, pred, hb["pred"]["guests"])
            memories.append({"fold": i, "series": name, "mem": mem})
            rows = test[test["market"].isin(part["market"].unique())]
            for s in settings:
                adjusted[s.name].loc[rows.index] = carry.adjust(rows, mem, s)
        for s in settings:
            preds.setdefault(s.name, []).append((window.fold, later * np.exp(adjusted[s.name])))
    return preds, memories


def complexity(name: str) -> int:
    if name.startswith("cf_"):
        _, _, e0, rho, *echo = name.split("_")
        return (e0 == "hb") + (rho in ("mkt", "hb", "wk")) + len(echo)
    if name.startswith("drift"):
        return ("_hl" in name) + (1 if "_k90" in name else 0)
    return 0


def by_series(panel: pd.DataFrame, preds: Dict[str, list], names: Dict[str, str]) -> list:
    """[(fold, prediction)] taking each series' rows from that series' chosen model."""
    merged = []
    for i in FOLDS:
        pieces = []
        for name, model in names.items():
            pred = preds[model][i][1]
            pieces.append(pred[data.series_of(panel.loc[pred.index, "market"]) == name])
        merged.append((preds[next(iter(names.values()))][i][0], pd.concat(pieces)))
    return merged


def choose(by_fold: pd.DataFrame, candidates: List[str]) -> tuple:
    """Best mean WAPE, and the simplest within SIMPLER_WITHIN_PP of it."""
    means = by_fold[candidates].mean()
    best = means.idxmin()
    close = [c for c in candidates if means[c] <= means[best] + SIMPLER_WITHIN_PP]
    return best, min(close, key=lambda c: (complexity(c), means[c]))


def memory_table(memories: List[dict], panel: pd.DataFrame, preds: Dict[str, list], model: str) -> pd.DataFrame:
    """Per series: the memory estimates (mean over folds), |e_0| in-sample vs held back, and how well
    e_0 predicts the mean log error of the first 30 test days (correlation over fold-markets)."""
    rows = []
    for name in SERIES:
        mems = [m for m in memories if m["series"] == name]
        if not mems:
            continue
        row = {"series": name, "rho pool (in-sample)": np.mean([m["mem"].rho_pool for m in mems]),
               "rho market median": np.mean([m["mem"].rho_mkt.median() for m in mems]),
               "rho held back": np.mean([m["mem"].rho_hb for m in mems]), "rho weekly": np.mean([m["mem"].rho_wk for m in mems]),
               "excess lag-7": np.mean([m["mem"].echo_rho for m in mems])}
        for source in ("in", "hb"):
            e0, first = [], []
            for m in mems:
                fold, pred = preds[model][m["fold"]]
                recent = m["mem"].recent[source]
                e0_k = recent.groupby("market")["e"].mean()
                test = panel[panel["market"].isin(e0_k.index) & panel["guests"].notna() & (panel["date"] >= fold.test_start)
                             & (panel["date"] < fold.test_start + pd.Timedelta(days=30))]
                err = np.log(test["guests"] / pred.reindex(test.index)).groupby(test["market"]).mean()
                e0.append(e0_k.reindex(err.index))
                first.append(err)
            e0, first = pd.concat(e0), pd.concat(first)
            row[f"mean |e0| k28 {source}"] = e0.abs().mean()
            row[f"corr(e0 {source}, test e days 1-30)"] = float(np.corrcoef(e0, first)[0, 1]) if len(e0) > 2 else np.nan
        row["mean |e| test days 1-30"] = first.abs().mean()
        rows.append(row)
    return pd.DataFrame(rows)


def experiment_one(panel: pd.DataFrame, model: str, splitter: str, control: Optional[str], weekly: bool, out: List[str]) -> dict:
    settings = carry.grid(weekly)
    preds, memories = carried(panel, model, splitter, settings)
    if control:
        preds[control] = [(load(control, splitter, i)["window"].fold, load(control, splitter, i)["pred"]["guests"]) for i in FOLDS]
    frame = scoring.scored(panel, preds)
    names = [s.name for s in settings]
    chosen = {}
    for name in SERIES:
        part = scoring.series(frame, name)
        if part.empty:
            continue
        by_fold = scoring.wape_by_fold(part)
        best, simple = choose(by_fold, names)
        chosen[name] = simple
        grid = pd.DataFrame({"setting": names, "WAPE": by_fold[names].mean().to_numpy()}).sort_values("WAPE")
        keep = list(dict.fromkeys([model, best, simple, "cf_k28_in_pool", "cf_k28_hb_one", "cf_k7_in_mkt", *([control] if control else [])]))
        table = scoring.table(part, model, keep, control or "")
        out += [f"#### {name.capitalize()}", "", f"Shipped {by_fold[model].mean():.2f}. Best setting `{best}`, simplest within "
                f"{SIMPLER_WITHIN_PP} pp `{simple}`. WAPE is market-day, mean over folds.", "",
                md(display(table)), "", "Grid, best 8 and worst 3:", "", md(pd.concat([grid.head(8), grid.tail(3)])), ""]
        if weekly:
            week = scoring.weekly(part)
            wt = scoring.table(week, model, [m for m in keep if m != control] + ([control] if control else []), control or "")
            out += ["Weekly market-week sums:", "", md(display(wt[["model", "WAPE", "delta pp", "ci low", "ci high", "folds better", "bias %", "gate"]])), ""]
        level = part.groupby(["model", "fold"])[["pred", "actual"]].sum()
        level = (level["pred"] / level["actual"] - 1).unstack("fold") * 100
        out += ["Level bias % by fold:", "", md(level.loc[[m for m in keep if m in level.index]].reset_index()), ""]
    out += ["Memory estimates, mean over folds:", "", md(memory_table(memories, panel, preds, model), 3), ""]
    return {"frame": frame, "chosen": chosen, "preds": preds}


# --- drift -----------------------------------------------------------------------------------
def drift_preds() -> Dict[str, list]:
    preds: Dict[str, list] = {}
    for k in DRIFT_KNOTS:
        for lam in DRIFT_LAMBDAS:
            for i in FOLDS:
                record = load(drift_name(k, lam), "protocol", i)
                for key, pred in record["pred"].items():
                    suffix = "" if key == "guests" else "_" + key.split("_")[1]
                    preds.setdefault(drift_name(k, lam) + suffix, []).append((record["window"].fold, pred))
    return preds


def identifiability(chosen: str) -> pd.DataFrame:
    """Per market, over folds: s range (min of knot minima, max of knot maxima), last s on the last
    fold, mean corr(base stock c_t, s(t)) over training days, passes vs the shipped fit, unconverged fits."""
    rows = {}
    for i in FOLDS:
        drift, base = load(chosen, "protocol", i)["report"], load("nowcast", "protocol", i)["report"]
        for market, entry in drift.items():
            row = rows.setdefault(market, {"s min": np.inf, "s max": -np.inf, "corr": [], "passes": [], "base passes": [], "not converged": 0})
            row["s min"] = min(row["s min"], entry["drift"]["min"])
            row["s max"] = max(row["s max"], entry["drift"]["max"])
            row["s last (last fold)"] = entry["drift"]["last"]
            row["corr"].append(entry["drift"]["corr_base_stock"])
            row["passes"].append(entry["passes"])
            row["base passes"].append(base[market]["passes"])
            row["not converged"] += not entry["converged"]
    out = pd.DataFrame([{"market": m, "s min": r["s min"], "s max": r["s max"], "s last (last fold)": r["s last (last fold)"],
                         "corr(c, s)": np.nanmean(r["corr"]), "passes": np.mean(r["passes"]), "shipped passes": np.mean(r["base passes"]),
                         "not converged": r["not converged"]} for m, r in rows.items()])
    return out.sort_values("market")


def experiment_two(panel: pd.DataFrame, out: List[str]) -> dict:
    preds = drift_preds()
    preds["nowcast"] = [(load("nowcast", "protocol", i)["window"].fold, load("nowcast", "protocol", i)["pred"]["guests"]) for i in FOLDS]
    preds["time_only"] = [(load("time_only", "protocol", i)["window"].fold, load("time_only", "protocol", i)["pred"]["guests"]) for i in FOLDS]
    frame = scoring.scored(panel, preds)
    names = [n for n in preds if n.startswith("drift")]
    chosen = {}
    for name in SERIES:
        part = scoring.series(frame, name)
        by_fold = scoring.wape_by_fold(part)
        best, simple = choose(by_fold, names)
        chosen[name] = simple
        grid = pd.DataFrame({"variant": names, "WAPE": by_fold[names].mean().to_numpy()})
        grid = grid.assign(order=grid["variant"].map(names.index)).sort_values("order").drop(columns="order")
        keep = list(dict.fromkeys(["nowcast", best, simple, "time_only"]))
        early, late = by_fold.index[:4], by_fold.index[4:]
        early_pick = by_fold.loc[early, names].mean().idxmin()
        held = scoring.compare(part[part["fold"].isin(late)], "nowcast", early_pick)
        out += [f"#### {name.capitalize()}", "", f"Selection check: chosen on the first 4 folds only, `{early_pick}`; on the last 3 folds "
                f"{held['difference_pp']:+.2f} pp [{held['ci_low']:+.2f}, {held['ci_high']:+.2f}].", "",
                f"Shipped {by_fold['nowcast'].mean():.2f}. Best `{best}`, simplest within "
                f"{SIMPLER_WITHIN_PP} pp `{simple}`.", "", md(display(scoring.table(part, "nowcast", keep, "time_only"))), "",
                "Grid (knot spacing k, lambda l, beyond the training days: held, or half-life 30 or 90 days):", "", md(grid), ""]
    return {"frame": frame, "chosen": chosen, "preds": preds}


def main() -> None:
    warnings.filterwarnings("ignore")
    panel = data.panel()
    panel = panel[panel["date"] <= pd.Timestamp("2025-01-31")]
    out = ["# Level memory: results", "",
           "VALIDATION_ORIGINS (7 folds) unless marked gap0. Aggregate metrics only. Written by `report.py` from the runs cached by `run.py`.",
           "WAPE: market-day, mean over folds. delta: compare() against the shipped model, pp, negative is better, 90% moving-block CI. "
           "R2 vs time: 1 - SSE / SSE of the time-only control (INTL_TIME / DOMESTIC_TIME) on the same rows. "
           "Horizon h: days since the origin (day 1 = origin). Bias: sum pred / sum actual - 1.", ""]
    out += ["## Experiment 1: carry-forward, daily nowcast", ""]
    for splitter in ("protocol", "gap0"):
        out += [f"### {splitter}" + (" (exploratory: training ends the day before the origin)" if splitter == "gap0" else ""), ""]
        result = experiment_one(panel, "nowcast", splitter, "time_only", False, out)
        if splitter == "protocol":
            one = result
    out += ["## Experiment 1: carry-forward, planning chain (international)", ""]
    for splitter in ("protocol", "gap0"):
        out += [f"### Chain, {splitter}", ""]
        experiment_one(panel, "chain", splitter, "time_only", True, out)
    out += ["## Experiment 2: drifting strength, daily nowcast", ""]
    two = experiment_two(panel, out)
    for name in SERIES:
        fitted = two["chosen"][name].split("_hl")[0]  # the half-life only changes prediction, not the fit
        table = identifiability(fitted)
        table = table[data.series_of(table["market"]) == name]
        out += [f"### Identifiability, {name}, `{fitted}`", "", md(table, 3), ""]

    # Combined: the chosen carry setting per series on top of the chosen drift (held-back fit of that drift).
    shipped, control = one["preds"]["nowcast"], one["preds"]["time_only"]
    shown = {"nowcast": shipped, "carry": by_series(panel, one["preds"], one["chosen"]),
             "drift": by_series(panel, two["preds"], two["chosen"])}
    labels = [f"carry: {n} `{one['chosen'][n]}`" for n in SERIES] + [f"drift: {n} `{two['chosen'][n]}`" for n in SERIES]
    if all(path((CHOSEN_DRIFT, "protocol", i, True)).exists() for i in FOLDS):
        chosen = {name: next(s for s in carry.grid(False) if s.name == one["chosen"][name]) for name in SERIES}
        preds, _ = carried(panel, CHOSEN_DRIFT, "protocol", list(set(chosen.values())))
        shown["drift+carry"] = by_series(panel, preds, {name: s.name for name, s in chosen.items()})
        labels.append(f"drift+carry: drift `{CHOSEN_DRIFT}` on both series, carry as chosen above")
    final = scoring.scored(panel, {**shown, "time_only": control})
    out += ["## Chosen settings side by side (protocol)", "", *[f"- {label}" for label in labels], ""]
    for name in SERIES:
        out += [f"#### {name.capitalize()}", "", md(display(scoring.table(scoring.series(final, name), "nowcast", [*shown, "time_only"], "time_only"))), ""]
    out += ["## Bias by market (protocol, all folds pooled)", "", "folds >5%: folds (of 7) with a same-sign bias above 5%.", "",
            md(scoring.bias_by_market(final, list(shown)).reset_index(), 1), ""]
    RESULTS.write_text("\n".join(out))
    print("\n".join(out))


if __name__ == "__main__":
    main()
