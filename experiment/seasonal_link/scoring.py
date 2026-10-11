"""Gate scores on VALIDATION_ORIGINS: daily and weekly WAPE per fold, compare() against the shipped
chain, folds better, level bias, and the variant choice (best, then simplest within 0.2 pp)."""

from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

import data
import run
from tourism_twin.models.backtest import compare
from variants import complexity

GATE_PP = 0.3
SIMPLER_WITHIN_PP = 0.2


def daily_rows(names: List[str]) -> pd.DataFrame:
    """compare() rows on each fold's test days, kept only where every model predicts."""
    frame = data.daily()
    frames = []
    for name in names:
        for i, fold in enumerate(data.folds()):
            pred = run.load(name, str(i))["daily"]
            test = frame[frame["guests"].notna() & (frame["date"] >= fold.test_start) & (frame["date"] <= fold.test_end)]
            frames.append(pd.DataFrame({"fold": fold.name, "row": test.index, "model": name, "market": test["market"].to_numpy(),
                                        "date": test["date"].to_numpy(), "actual": test["guests"].to_numpy(),
                                        "pred": pred.reindex(test.index).to_numpy()}))
    out = pd.concat(frames, ignore_index=True)
    return out[out.groupby(["fold", "row"])["pred"].transform(lambda s: s.notna().all())]


def weekly_rows(daily: pd.DataFrame) -> pd.DataFrame:
    """Market-week sums over complete test weeks, in compare() row form."""
    keyed = daily.assign(week=data.week_start(daily["date"]))
    out = keyed.groupby(["fold", "model", "market", "week"]).agg(actual=("actual", "sum"), pred=("pred", "sum"),
                                                                 days=("pred", "size")).reset_index()
    out = out[out["days"] == 7].drop(columns="days").rename(columns={"week": "date"})
    return out.assign(row=out["market"] + "|" + out["date"].astype(str))


def wape(frame: pd.DataFrame) -> float:
    return float((frame["pred"] - frame["actual"]).abs().sum() / frame["actual"].sum() * 100)


def by_fold(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.groupby(["model", "fold"]).apply(wape).unstack("model")


def table(frame: pd.DataFrame, base: str, names: List[str]) -> pd.DataFrame:
    folds = by_fold(frame)
    rows = []
    for name in names:
        part = frame[frame["model"] == name]
        row = {"model": name, "WAPE": folds[name].mean(), "bias %": (part["pred"].sum() / part["actual"].sum() - 1) * 100}
        if name != base:
            c = compare(frame, base, name)
            better = int((folds[name] < folds[base]).sum())
            row.update({"delta": c["difference_pp"], "low": c["ci_low"], "high": c["ci_high"], "folds better": better,
                        "gate": "pass" if c["difference_pp"] <= -GATE_PP and c["ci_high"] < 0 and better >= 4 else "fail"})
        rows.append(row)
    return pd.DataFrame(rows)


def level_bias(frame: pd.DataFrame, names: List[str]) -> pd.DataFrame:
    sums = frame[frame["model"].isin(names)].groupby(["model", "fold"])[["pred", "actual"]].sum()
    return ((sums["pred"] / sums["actual"] - 1) * 100).unstack("fold")


def choose(folds: pd.DataFrame, candidates: List[str]) -> Dict[str, str]:
    means = folds[candidates].mean()
    best = means.idxmin()
    close = [c for c in candidates if means[c] <= means[best] + SIMPLER_WITHIN_PP]
    return {"best": best, "simplest": min(close, key=lambda c: (complexity(c), means[c]))}


def selection_check(frame: pd.DataFrame, base: str, candidates: List[str]) -> Dict[str, object]:
    """Choose on the first 4 folds only, score the choice on the last 3."""
    folds = by_fold(frame)
    early, late = folds.index[:4], folds.index[4:]
    pick = folds.loc[early, candidates].mean().idxmin()
    c = compare(frame[frame["fold"].isin(late)], base, pick)
    return {"pick": pick, "delta": c["difference_pp"], "low": c["ci_low"], "high": c["ci_high"]}

