"""Learned seasonal strengths exp(a_season) of link 1: per market from the full fit (every guest day to
CUT) and the 7 fold fits; pooled as the median over markets with a 90% bootstrap over markets."""

from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd

import data
import run
from tourism_twin.domain.seasons import SEASONS

N_BOOT = 2000
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def by_season(variant: str, fold: str) -> pd.DataFrame:
    """market x season strength of one fit."""
    return pd.DataFrame({m: s["by_season"] for m, s in run.load(variant, fold)["strength"].items()}).T[SEASONS]


def by_month(variant: str, fold: str) -> pd.DataFrame:
    return pd.DataFrame({m: s["by_month"] for m, s in run.load(variant, fold)["strength"].items()}, index=MONTHS).T


def median_with_interval(table: pd.DataFrame, seed: int = 0) -> pd.DataFrame:
    """Per column: median over markets (rows) and a 90% bootstrap interval over markets."""
    rng = np.random.default_rng(seed)
    values = table.to_numpy()
    draws = np.array([np.median(values[rng.integers(0, len(values), len(values))], axis=0) for _ in range(N_BOOT)])
    return pd.DataFrame({"median": np.median(values, axis=0), "low": np.quantile(draws, 0.05, axis=0),
                         "high": np.quantile(draws, 0.95, axis=0)}, index=table.columns)


def pooled(variant: str, folds: List[str]) -> pd.DataFrame:
    """Per season: full-fit median [90% over markets], the range of the fold medians, markets above 1."""
    full = by_season(variant, "full")
    out = median_with_interval(full)
    fold_medians = pd.DataFrame({f: by_season(variant, f).median() for f in folds}).T
    out["fold min"], out["fold max"] = fold_medians.min(), fold_medians.max()
    out["markets above 1"] = (full > 1).sum()
    return out.rename_axis("season").reset_index()


def markets(variant: str, folds: List[str]) -> pd.DataFrame:
    """The 6 largest markets: full-fit strength per season with the min and max over fold fits."""
    full = by_season(variant, "full")
    per_fold = [by_season(variant, f) for f in folds]
    rows = []
    for market in data.BIG_SIX:
        row = {"market": market}
        for season in SEASONS:
            values = [t.loc[market, season] for t in per_fold]
            row[season] = f"{full.loc[market, season]:.2f} ({min(values):.2f} to {max(values):.2f})"
        rows.append(row)
    return pd.DataFrame(rows)
