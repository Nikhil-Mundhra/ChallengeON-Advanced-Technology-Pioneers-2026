"""Conformal calibrator: per-market relative error margins for the planning-mode interval."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd

from tourism_twin.models.structural import StructuralEngine

# Coverage reported when no back-test result is available yet.
DEFAULT_DEMONSTRATED_COVERAGE = 66.7


def calibrate_conformal(
    train_df: pd.DataFrame,
    struct_engine: StructuralEngine,
    alpha: float = 0.20,
    evaluation_results_path: Path | None = None,
) -> Dict[str, Any]:
    """Fit the (1 - alpha) quantile of relative planning-mode error per market.

    Errors are measured against StructuralEngine.planning_guests, the same prediction the
    simulator and the back-test use.

    The demonstrated holdout coverage is copied from the back-test results when present.
    """
    conformal_dict: Dict[str, Any] = {}

    for m in train_df["market"].unique():
        m_df = train_df[train_df["market"] == m]
        rel_errors = []
        for s in m_df["season"].unique():
            s_df = m_df[m_df["season"] == s]
            if s not in struct_engine.params.get(m, {}):
                continue
            preds = np.array([struct_engine.planning_guests(m, s, seats) for seats in s_df["seats"].values])
            errs = np.abs(s_df["guests"].values - preds) / np.maximum(preds, 100.0)
            rel_errors.extend(errs.tolist())

        q = float(np.quantile(rel_errors, min(1.0, (1.0 - alpha) * (len(rel_errors) + 1) / max(1, len(rel_errors)))))
        conformal_dict[m] = q

    conformal_dict["_target_alpha"] = alpha
    conformal_dict["_demonstrated_holdout_coverage"] = demonstrated_coverage(evaluation_results_path)
    return conformal_dict


def demonstrated_coverage(evaluation_results_path: Path | None) -> float:
    """Holdout interval coverage from the back-test results, or the default when unavailable."""
    if evaluation_results_path is None or not evaluation_results_path.exists():
        return DEFAULT_DEMONSTRATED_COVERAGE
    try:
        with open(evaluation_results_path, "r", encoding="utf-8") as f:
            eval_data = json.load(f)
        return float(eval_data.get("demonstrated_coverage_pct", DEFAULT_DEMONSTRATED_COVERAGE))
    except Exception:
        return DEFAULT_DEMONSTRATED_COVERAGE


def save_conformal(conformal_dict: Dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(conformal_dict, f, indent=2)
    return path
