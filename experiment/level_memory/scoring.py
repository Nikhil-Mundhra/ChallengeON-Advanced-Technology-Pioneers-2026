"""Scores on test rows: WAPE by fold, compare() against the shipped model, bias, MAE, RMSE,
out-of-sample R^2 against the time-only control, WAPE by horizon, weekly sums and bias by market."""

from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

from tourism_twin.models.backtest import compare  # noqa: F401 (re-exported for report.py)

import data

GATE_PP = 0.3
HORIZONS = {"1-7": (1, 7), "8-30": (8, 30), "31+": (31, 10_000)}  # days since the origin, origin = day 1


def scored(panel: pd.DataFrame, preds: Dict[str, List[tuple]]) -> pd.DataFrame:
    """compare() rows on each fold's test days, kept only where every model predicts.
    preds: model -> [(fold, prediction Series indexed like panel), ...]."""
    frames = []
    for name, folds in preds.items():
        for fold, pred in folds:
            test = panel[panel["guests"].notna() & (panel["date"] >= fold.test_start) & (panel["date"] <= fold.test_end)]
            frames.append(pd.DataFrame({"fold": fold.name, "row": test.index, "model": name, "market": test["market"].to_numpy(),
                                        "date": test["date"].to_numpy(), "horizon_days": (test["date"] - fold.test_start).dt.days.to_numpy(),
                                        "actual": test["guests"].to_numpy(), "pred": pred.reindex(test.index).to_numpy()}))
    out = pd.concat(frames, ignore_index=True)
    everyone = out.groupby(["fold", "row"])["pred"].transform(lambda s: s.notna().all())
    return out[everyone]


def series(frame: pd.DataFrame, name: str) -> pd.DataFrame:
    return frame[data.series_of(frame["market"]) == name]


def wape(frame: pd.DataFrame) -> float:
    return float((frame["pred"] - frame["actual"]).abs().sum() / frame["actual"].sum() * 100)


def wape_by_fold(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.groupby(["model", "fold"]).apply(wape).unstack("model")


def weekly(frame: pd.DataFrame) -> pd.DataFrame:
    """Market-week sums over complete weeks, in compare() row form."""
    keyed = frame.assign(week=data.week_start(frame["date"]))
    grouped = keyed.groupby(["fold", "model", "market", "week"])
    out = grouped.agg(actual=("actual", "sum"), pred=("pred", "sum"), days=("pred", "size"),
                      horizon_days=("horizon_days", "min")).reset_index()
    out = out[out["days"] == 7].drop(columns="days").rename(columns={"week": "date"})
    return out.assign(row=out["market"] + "|" + out["date"].astype(str))


def table(frame: pd.DataFrame, base: str, names: List[str], control: str) -> pd.DataFrame:
    """One row per model: WAPE (mean over folds), compare() against `base`, folds better, bias,
    MAE, RMSE, R^2 against `control` (1 - SSE / SSE_control on the same rows), WAPE by horizon."""
    by_fold = wape_by_fold(frame)
    sse_control = None
    if control in frame["model"].unique():
        c = frame[frame["model"] == control]
        sse_control = float(((c["pred"] - c["actual"]) ** 2).sum())
    rows = []
    for name in names:
        part = frame[frame["model"] == name]
        err = part["pred"] - part["actual"]
        row = {"model": name, "WAPE": by_fold[name].mean(), "bias %": (part["pred"].sum() / part["actual"].sum() - 1) * 100,
               "MAE": err.abs().mean(), "RMSE": float(np.sqrt((err ** 2).mean())),
               "R2 vs time": 1 - float((err ** 2).sum()) / sse_control if sse_control else np.nan}
        days = part["horizon_days"] + 1
        for label, (lo, hi) in HORIZONS.items():
            row[f"WAPE h{label}"] = wape(part[(days >= lo) & (days <= hi)])
        if name != base:
            c = compare(frame, base, name)
            row.update({"delta pp": c["difference_pp"], "ci low": c["ci_low"], "ci high": c["ci_high"],
                        "folds better": int((by_fold[name] < by_fold[base]).sum())})
            row["gate"] = "pass" if (c["difference_pp"] <= -GATE_PP and c["ci_high"] < 0 and row["folds better"] >= 4) else "fail"
        rows.append(row)
    return pd.DataFrame(rows)


def bias_by_market(frame: pd.DataFrame, names: List[str]) -> pd.DataFrame:
    """Pooled bias % per market (all folds) and folds with a same-sign bias above 5%."""
    out = {}
    for name in names:
        part = frame[frame["model"] == name]
        sums = part.groupby("market")[["pred", "actual"]].sum()
        out[f"{name} bias %"] = (sums["pred"] / sums["actual"] - 1) * 100
        fold = part.groupby(["market", "fold"])[["pred", "actual"]].sum()
        per_fold = (fold["pred"] / fold["actual"] - 1) * 100
        out[f"{name} folds >5%"] = per_fold.groupby("market").apply(lambda s: max((s > 5).sum(), (s < -5).sum()))
    return pd.DataFrame(out)
