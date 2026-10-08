"""Forward-holdout back-test of the shipped models against simpler baselines.

Strict full-week temporal split of the complete training weeks:
- Calibration: Jan 2023 - Dec 2024 (104 complete 7-day weeks)
- Forward holdout: Jan 2025 - Jul 2025 (30 complete 7-day weeks)

The structural, residual, and conformal components are fitted with the same trainers that
produce the shipped artifacts (StructuralEngine.calibrate, ResidualMLEngine.fit,
calibrate_conformal), restricted to the calibration window, so the benchmark measures the
model the simulator actually serves.

Reported settings:
1. International Planning Mode (pre-flight: scheduled seats + calibrated priors only).
2. International Realized-Chain Mode (downstream conversion from realized P2P).
3. Domestic Forecast Mode (calibrated seasonal prior; no holdout arrivals).
4. Combined Planning and Realized-Chain diagnostics.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeCV

from tourism_twin.config import SETTINGS
from tourism_twin.data.panel import training_window
from tourism_twin.domain.seasons import SEASONS
from tourism_twin.models.conformal import calibrate_conformal
from tourism_twin.models.features import extract_calendar_features
from tourism_twin.models.residual import ResidualMLEngine
from tourism_twin.models.structural import StructuralEngine

# First Monday of the forward holdout; everything before it is the calibration window.
HOLDOUT_START = "2024-12-30"

# Interval half-width used for a market the conformal calibrator has not seen.
FALLBACK_CONFORMAL_MARGIN = 0.35

# Neutral names only: which model leads on which metric is computed (benchmark_leaders),
# never written into a label, so no report can claim a ranking the numbers contradict.
BENCHMARK_NAMES = (
    "1. Historical Seasonal Prior",
    "2. Pure ML / Calendar Model",
    "3. Structural-Only Engine",
    "4. Hybrid Digital Twin",
)


def forecast_metrics(actual: np.ndarray, pred: np.ndarray) -> Dict[str, float]:
    err = actual - pred
    tot_act = float(np.sum(actual))
    wmape = float(np.sum(np.abs(err)) / tot_act) if tot_act > 0 else 0.0
    bias = float((np.sum(pred) - tot_act) / tot_act) if tot_act > 0 else 0.0
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err ** 2)))
    return {"wmape": wmape, "bias": bias, "mae": mae, "rmse": rmse}


def benchmark_leaders(benchmark: Dict[str, Dict[str, float]]) -> Dict[str, str]:
    """Best model per metric: lowest WMAPE, MAE, RMSE, and lowest absolute bias."""
    leaders = {metric: min(benchmark, key=lambda name: benchmark[name][metric]) for metric in ("wmape", "mae", "rmse")}
    leaders["bias"] = min(benchmark, key=lambda name: abs(benchmark[name]["bias"]))
    return leaders


def _calendar_features(row: pd.Series) -> np.ndarray:
    return extract_calendar_features(
        row["iso_week"], row["quarter"], row["month"], row["is_holiday_week"], row["is_major_event_week"]
    )


def _pure_calendar_predictions(train: pd.DataFrame, test: pd.DataFrame) -> list[float]:
    """Benchmark 2: a per-market ridge on calendar features alone, ignoring aviation entirely."""
    models = {}
    for m in train["market"].unique():
        m_df = train[train["market"] == m]
        X = np.stack([_calendar_features(r) for _, r in m_df.iterrows()])
        models[m] = RidgeCV(alphas=np.logspace(-2, 4, 20)).fit(X, m_df["guests"].values)
    return [
        max(0.0, float(models[r["market"]].predict(_calendar_features(r).reshape(1, -1))[0]))
        for _, r in test.iterrows()
    ]


def evaluate(panel_path: Path = SETTINGS.panel_path) -> Dict[str, Any]:
    """Run the back-test and return the results payload (see save_evaluation)."""
    complete = training_window(pd.read_parquet(panel_path))
    week_start = pd.to_datetime(complete["week_start"])
    train = complete[week_start < HOLDOUT_START].copy()
    test = complete[week_start >= HOLDOUT_START].copy()

    structural = StructuralEngine.calibrate(train)
    residual = ResidualMLEngine().fit(train, structural)
    conformal = calibrate_conformal(train, structural)

    test["pred_structural"] = [
        structural.planning_guests(r["market"], r["season"], r["seats"]) for _, r in test.iterrows()
    ]
    test["pred_realized"] = [
        (
            r["p2p"] * p.effective_response_multiplier * p.baseline_los
            if r["market"] != "DOMESTIC"
            else r["pred_structural"]
        )
        for (_, r), p in (
            ((i, r), structural.get_or_create_params(r["market"], r["season"])) for i, r in test.iterrows()
        )
    ]
    test["pred_hybrid"] = [
        max(
            0.0,
            r["pred_structural"]
            + residual.predict_residual(
                r["market"], r["iso_week"], r["quarter"], r["month"], r["is_holiday_week"], r["is_major_event_week"]
            ),
        )
        for _, r in test.iterrows()
    ]
    season_priors = train.groupby(["market", "season"])["guests"].mean().to_dict()
    overall_prior = train["guests"].mean()
    test["pred_baseline"] = [season_priors.get((r["market"], r["season"]), overall_prior) for _, r in test.iterrows()]
    test["pred_ml_only"] = _pure_calendar_predictions(train, test)

    intl = test[test["market"] != "DOMESTIC"]
    dom = test[test["market"] == "DOMESTIC"]
    diagnostics = {
        "international_planning_mode": forecast_metrics(intl["guests"].values, intl["pred_structural"].values),
        "international_realized_chain": forecast_metrics(intl["guests"].values, intl["pred_realized"].values),
        "domestic_forecast_mode": forecast_metrics(dom["guests"].values, dom["pred_structural"].values),
        "combined_planning_mode": forecast_metrics(test["guests"].values, test["pred_structural"].values),
        "combined_realized_chain": forecast_metrics(test["guests"].values, test["pred_realized"].values),
    }

    benchmark_columns = ("pred_baseline", "pred_ml_only", "pred_structural", "pred_hybrid")
    benchmark = {
        name: forecast_metrics(test["guests"].values, test[column].values)
        for name, column in zip(BENCHMARK_NAMES, benchmark_columns)
    }

    margins = test["market"].map(lambda m: conformal.get(m, FALLBACK_CONFORMAL_MARGIN))
    low = test["pred_structural"] * (1.0 - margins)
    high = test["pred_structural"] * (1.0 + margins)
    demonstrated_coverage = float(((low <= test["guests"]) & (test["guests"] <= high)).mean())

    market_breakdown = {}
    for m in sorted(test["market"].unique()):
        m_test = test[test["market"] == m]
        market_breakdown[m] = {
            "archetype": str(m_test["archetype"].iloc[0]),
            "observations": len(m_test),
            **forecast_metrics(m_test["guests"].values, m_test["pred_structural"].values),
        }

    season_breakdown = {}
    for s in SEASONS:
        s_test = test[test["season"] == s]
        if len(s_test) == 0:
            continue
        season_breakdown[s] = {
            "observations": len(s_test),
            **forecast_metrics(s_test["guests"].values, s_test["pred_structural"].values),
        }

    return {
        "evaluation_window": {
            "train_weeks": int(train["week_start"].nunique()),
            "test_weeks": int(test["week_start"].nunique()),
            "train_range": [str(train["week_start"].min()), str(train["week_start"].max())],
            "test_range": [str(test["week_start"].min()), str(test["week_start"].max())],
            "observations_train": len(train),
            "observations_test": len(test),
        },
        "diagnostics": diagnostics,
        "benchmark": benchmark,
        "benchmark_leaders": benchmark_leaders(benchmark),
        "demonstrated_coverage_pct": round(demonstrated_coverage * 100.0, 1),
        "market_breakdown": market_breakdown,
        "season_breakdown": season_breakdown,
    }


def save_evaluation(
    payload: Dict[str, Any],
    results_path: Path = SETTINGS.evaluation_results_path,
    conformal_path: Path = SETTINGS.conformal_path,
) -> bool:
    """Write the results JSON and copy the demonstrated coverage into an existing conformal
    calibrator. Returns whether the calibrator was updated."""
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    if not conformal_path.exists():
        return False
    with open(conformal_path, "r", encoding="utf-8") as f:
        conf_data = json.load(f)
    conf_data["_demonstrated_holdout_coverage"] = payload["demonstrated_coverage_pct"]
    with open(conformal_path, "w", encoding="utf-8") as f:
        json.dump(conf_data, f, indent=2)
    return True
