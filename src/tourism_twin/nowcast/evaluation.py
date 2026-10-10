"""Nowcast evaluations on rolling origins, segment by segment (domestic and international are
never pooled): the block ablation of docs/model/nowcast.md#blocks, and the week-to-week direction
back-test of the outputs document."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from tourism_twin.data.daily_panel import build_daily_panel
from tourism_twin.models.backtest import VALIDATION_ORIGINS, RollingOrigin, backtest, compare, segment_of
from tourism_twin.features.calendar import week_monday
from tourism_twin.models.noise import NoiseModel
from tourism_twin.nowcast.specs import BLOCK_ABLATION, DAILY_SPECS
from tourism_twin.nowcast.weekly import weekly_forecast

PROB_BUCKETS = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

ABLATION_ORIGINS = RollingOrigin("2024-02-01", "2025-02-01", horizon_months=6)


def segment_wape(predictions: pd.DataFrame) -> pd.DataFrame:
    """Mean over folds of WAPE (%) on daily totals, per model and segment."""
    totals = (predictions.assign(segment=segment_of(predictions["market"]))
              .groupby(["model", "segment", "fold", "date"])[["pred", "actual"]].sum())
    wape = totals.groupby(["model", "segment", "fold"]).apply(
        lambda g: (g["pred"] - g["actual"]).abs().sum() / g["actual"].sum() * 100)
    return wape.groupby(["model", "segment"]).mean().unstack("segment")


def block_ablation(panel: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """WAPE on daily totals for each block combination in BLOCK_ABLATION, 13 rolling origins."""
    panel = build_daily_panel() if panel is None else panel
    result = backtest({name: DAILY_SPECS[name] for name in BLOCK_ABLATION}, panel, ABLATION_ORIGINS)
    table = segment_wape(result.predictions).reindex(list(BLOCK_ABLATION))
    return {
        "origins": f"{len(result.predictions['fold'].unique())} monthly, 2024-02-01..2025-02-01, 6-month horizon",
        "metric": "WAPE % of daily segment totals, mean over folds",
        "wape": table.astype(float).round(2).to_dict("index"),
        "non_converged_fits": int(result.diagnostics["non_converged"].sum()) if len(result.diagnostics) else 0,
    }


VALIDATION_SPECS = ("naive_364", "arrivals_ratio", "time_only", "flow_only", "flow_time", "twin_daily")
VALIDATION_COMPARISONS = (("naive_364", "twin_daily"), ("time_only", "twin_daily"), ("flow_time", "twin_daily"))
# Measured once by other scripts; recorded here with their commit so a report reads one file.
NATIONALITY_RESULTS = {
    "pooled_nationalities_vs_split": {"grain": "international nationality-day WAPE %", "commit": "26f2059",
                                      "validation": {"split": 12.79, "pooled": 12.24, "difference_pp": -0.55, "ci_90": [-0.79, -0.32], "folds_same_sign": "7/7"},
                                      "frozen_test": {"split": 11.38, "pooled": 11.16, "difference_pp": -0.22, "ci_90": [-0.45, 0.02]}},
    "pooled_recency_365_vs_unweighted": {"grain": "guest-weighted WAPE %, 30 pooled-market nationalities", "commit": "4a3468b",
                                         "validation": {"unweighted": 14.23, "recency_365": 13.83, "difference_pp": -0.40, "ci_90": [-0.64, -0.19], "folds_same_sign": "7/7"}},
}


def validation_summary(panel: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """The headline validation numbers (issue #11 protocol): WAPE of daily segment totals per spec,
    and market-grain compare() of twin_daily against its baselines, per segment."""
    panel = build_daily_panel() if panel is None else panel
    predictions = backtest({name: DAILY_SPECS[name] for name in VALIDATION_SPECS}, panel, VALIDATION_ORIGINS).predictions
    table = segment_wape(predictions).reindex(list(VALIDATION_SPECS))
    comparisons = []
    for segment in ("domestic", "international"):
        part = predictions[segment_of(predictions["market"]) == segment]
        for baseline, candidate in VALIDATION_COMPARISONS:
            result = compare(part, baseline, candidate)
            comparisons.append({"segment": segment, "baseline": baseline, "candidate": candidate,
                                **{key: (round(value, 3) if isinstance(value, float) else value) for key, value in result.items()}})
    folds = sorted(predictions["fold"].unique())
    return {
        "protocol": "issue #11: monthly origins 2024-02-01..2024-08-01, horizon to 2025-01-31, 21-day gap, expanding window",
        "folds": folds,
        "segment_wape": {"grain": "WAPE % of daily segment totals, mean over folds",
                         "values": table.astype(float).round(2).to_dict("index")},
        "compare": {"grain": "market-day rows, candidate - baseline WAPE pp, 90% moving-block bootstrap (28-day blocks)",
                    "rows": comparisons},
        "nationalities": NATIONALITY_RESULTS,
    }


def _sign(values: pd.Series) -> pd.Series:
    return np.sign(values).replace(0, np.nan)


def direction_backtest(backtest_predictions: pd.DataFrame, history: pd.DataFrame, noise: NoiseModel,
                       coverage: float = 0.8) -> Dict[str, Any]:
    """Week-to-week direction on the back-test folds, each market-week scored once (from the
    earliest origin that forecasts it, i.e. the longest horizon). Baselines: the direction of the
    week's observed new arrivals, the same weeks a year earlier, and each market's most common
    training direction. Also the reliability of direction_prob and the weekly band coverage; the
    noise model is fitted on these same folds, so both are in-sample for the error model."""
    by_week = history.assign(week_start=week_monday(history["date"])).groupby(["market", "week_start"])
    actual_weekly = by_week["guests"].agg(["sum", "size"])
    actual_weekly = actual_weekly[actual_weekly["size"] == 7]["sum"]
    arrivals_weekly = by_week["new_arrivals_filled"].sum()
    rows: List[pd.DataFrame] = []
    for fold, group in backtest_predictions.groupby("fold"):
        origin = group["origin"].iloc[0]
        daily = group.join(noise.intervals(group, coverage))
        weekly = weekly_forecast(daily, noise, coverage)
        actual = (group.assign(week_start=week_monday(group["date"])).groupby(["market", "week_start"])["actual"]
                  .agg(["sum", "size"]))
        weekly = weekly.join(actual, on=["market", "week_start"])
        weekly = weekly[weekly["size"] == 7].drop(columns="size").rename(columns={"sum": "actual"})
        g = weekly.groupby("market")
        weekly["pred_dir"] = weekly["direction"].map({"increase": 1.0, "decrease": -1.0})
        weekly["actual_dir"] = _sign(g["actual"].shift(-1) - weekly["actual"])
        this_week = pd.MultiIndex.from_frame(weekly[["market", "week_start"]])
        next_week = pd.MultiIndex.from_arrays([weekly["market"], weekly["week_start"] + pd.Timedelta(7, unit="D")])
        weekly["arrivals_dir"] = _sign(pd.Series(arrivals_weekly.reindex(next_week).to_numpy()
                                                 - arrivals_weekly.reindex(this_week).to_numpy(), index=weekly.index))
        last_year = pd.MultiIndex.from_arrays([weekly["market"], weekly["week_start"] - pd.Timedelta(364, unit="D")])
        next_last_year = pd.MultiIndex.from_arrays([weekly["market"], weekly["week_start"] - pd.Timedelta(357, unit="D")])
        weekly["last_year_dir"] = _sign(pd.Series(actual_weekly.reindex(next_last_year).to_numpy()
                                                  - actual_weekly.reindex(last_year).to_numpy(), index=weekly.index))
        train = actual_weekly[actual_weekly.index.get_level_values("week_start") + pd.Timedelta(6, unit="D") < origin]
        train_dir = _sign(train.groupby(level="market").diff())
        majority = train_dir.groupby(level="market").agg(lambda s: 1.0 if (s > 0).sum() >= (s < 0).sum() else -1.0)
        weekly["majority_dir"] = weekly["market"].map(majority)
        weekly["covered"] = (weekly["actual"] >= weekly["p10"]) & (weekly["actual"] <= weekly["p90"])
        rows.append(weekly.assign(origin=origin))
    every = pd.concat(rows, ignore_index=True)
    coverage_rate = float(every.sort_values("origin").drop_duplicates(["market", "week_start"])["covered"].mean())
    scored = (every.dropna(subset=["pred_dir", "actual_dir"]).sort_values("origin")
              .drop_duplicates(["market", "week_start"]))
    accuracy = {name: float((scored[column] == scored["actual_dir"]).mean())
                for name, column in (("model", "pred_dir"), ("arrivals_direction", "arrivals_dir"),
                                     ("same_direction_as_last_year", "last_year_dir"),
                                     ("majority_direction", "majority_dir"))}
    hit = scored["pred_dir"] == scored["actual_dir"]
    bucket = pd.cut(scored["direction_prob"], PROB_BUCKETS, include_lowest=True)
    reliability = [{"prob_range": f"{interval.left:.1f}-{interval.right:.1f}", "weeks": int(len(hits)),
                    "mean_prob": round(float(scored.loc[hits.index, "direction_prob"].mean()), 3),
                    "share_right": round(float(hits.mean()), 3)}
                   for interval, hits in hit.groupby(bucket, observed=True)]
    return {"weeks_scored": int(len(scored)), "accuracy": accuracy, "direction_prob_reliability": reliability,
            "weekly_band_coverage": coverage_rate}
