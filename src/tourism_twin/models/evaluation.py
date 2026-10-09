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

import pandas as pd

from tourism_twin.config import SETTINGS
from tourism_twin.data.panel import training_window
from tourism_twin.domain.markets import DOMESTIC
from tourism_twin.domain.seasons import SEASONS
from tourism_twin.models.backtest import HoldoutSplit, backtest, forecast_metrics
from tourism_twin.models.conformal import calibrate_conformal
from tourism_twin.models.specs import DIAGNOSTIC_SPECS, WEEKLY_SPECS
from tourism_twin.models.structural import StructuralEngine

# First Monday of the forward holdout; everything before it is the calibration window.
HOLDOUT_START = "2024-12-30"

# Interval half-width used for a market the conformal calibrator has not seen.
FALLBACK_CONFORMAL_MARGIN = 0.35

# Neutral names only: which model leads on which metric is computed (benchmark_leaders),
# never written into a label, so no report can claim a ranking the numbers contradict.
# Each benchmark row is a weekly model spec run through the back-test harness.
BENCHMARK_SPECS = {
    "1. Historical Seasonal Prior": "seasonal_prior",
    "2. Pure ML / Calendar Model": "calendar_ridge",
    "3. Structural-Only Engine": "structural_planning",
    "4. Hybrid Digital Twin": "hybrid_legacy",
}


def benchmark_leaders(benchmark: Dict[str, Dict[str, float]]) -> Dict[str, str]:
    """Best model per metric: lowest WMAPE, MAE, RMSE, and lowest absolute bias."""
    leaders = {metric: min(benchmark, key=lambda name: benchmark[name][metric]) for metric in ("wmape", "mae", "rmse")}
    leaders["bias"] = min(benchmark, key=lambda name: abs(benchmark[name]["bias"]))
    return leaders


def evaluate(panel_path: Path = SETTINGS.panel_path) -> Dict[str, Any]:
    """Run the back-test and return the results payload (see save_evaluation)."""
    complete = training_window(pd.read_parquet(panel_path))
    result = backtest(
        {**{spec: WEEKLY_SPECS[spec] for spec in BENCHMARK_SPECS.values()}, "realized_chain": DIAGNOSTIC_SPECS["realized_chain"]},
        complete, HoldoutSplit(HOLDOUT_START), date_column="week_start", period_days=7,
    )
    predictions = result.predictions.pivot(index="row", columns="model", values="pred")
    test = complete.loc[result.predictions.loc[result.predictions["model"] == "structural_planning", "row"]].copy()
    test = test.join(predictions)
    train = complete[pd.to_datetime(complete["week_start"]) < HOLDOUT_START]

    structural = StructuralEngine.calibrate(train)
    conformal = calibrate_conformal(train, structural)

    intl = test[test["market"] != DOMESTIC]
    dom = test[test["market"] == DOMESTIC]
    diagnostics = {
        "international_planning_mode": forecast_metrics(intl["guests"].values, intl["structural_planning"].values),
        "international_realized_chain": forecast_metrics(intl["guests"].values, intl["realized_chain"].values),
        "domestic_forecast_mode": forecast_metrics(dom["guests"].values, dom["structural_planning"].values),
        "combined_planning_mode": forecast_metrics(test["guests"].values, test["structural_planning"].values),
        "combined_realized_chain": forecast_metrics(test["guests"].values, test["realized_chain"].values),
    }
    benchmark = {name: forecast_metrics(test["guests"].values, test[spec].values) for name, spec in BENCHMARK_SPECS.items()}

    margins = test["market"].map(lambda m: conformal.get(m, FALLBACK_CONFORMAL_MARGIN))
    low = test["structural_planning"] * (1.0 - margins)
    high = test["structural_planning"] * (1.0 + margins)
    demonstrated_coverage = float(((low <= test["guests"]) & (test["guests"] <= high)).mean())

    market_breakdown = {}
    for m in sorted(test["market"].unique()):
        m_test = test[test["market"] == m]
        market_breakdown[m] = {
            "archetype": str(m_test["archetype"].iloc[0]),
            "observations": len(m_test),
            **forecast_metrics(m_test["guests"].values, m_test["structural_planning"].values),
        }

    season_breakdown = {}
    for s in SEASONS:
        s_test = test[test["season"] == s]
        if len(s_test) == 0:
            continue
        season_breakdown[s] = {
            "observations": len(s_test),
            **forecast_metrics(s_test["guests"].values, s_test["structural_planning"].values),
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


def save_evaluation(payload: Dict[str, Any], results_path: Path = SETTINGS.evaluation_results_path) -> Path:
    """Write the results JSON. Holdout results are never written into a calibrator: `twin train`
    reads the demonstrated coverage from this file."""
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return results_path
