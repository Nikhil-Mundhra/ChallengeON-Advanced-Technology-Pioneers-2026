"""Deterministic training: calibrate the structural chain, fit the residual layer, calibrate
the conformal margins, and write all three artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from tourism_twin.config import SETTINGS
from tourism_twin.data.panel import TRAINING_CUTOFF, training_window
from tourism_twin.planning.conformal import calibrate_conformal, save_conformal
from tourism_twin.planning.residual import ResidualMLEngine
from tourism_twin.planning.structural import StructuralEngine


@dataclass
class TrainingResult:
    structural: StructuralEngine
    residual: ResidualMLEngine
    conformal: Dict[str, Any]
    calibration_path: Path
    residual_model_path: Path
    conformal_path: Path


def train_models(
    panel_path: Path = SETTINGS.panel_path,
    max_date: str = TRAINING_CUTOFF,
    calib_out: Path = SETTINGS.calibration_path,
    model_out: Path = SETTINGS.residual_model_path,
    conformal_out: Path = SETTINGS.conformal_path,
) -> TrainingResult:
    struct_engine = StructuralEngine.calibrate_from_panel(
        panel_path=panel_path,
        save_path=calib_out,
        max_date=max_date,
    )

    train_df = training_window(pd.read_parquet(panel_path), max_date)
    residual_engine = ResidualMLEngine().fit(train_df, struct_engine)
    saved_model_path = residual_engine.save(model_path=model_out)

    conformal_dict = calibrate_conformal(
        train_df, struct_engine, evaluation_results_path=SETTINGS.evaluation_results_path
    )
    save_conformal(conformal_dict, conformal_out)

    return TrainingResult(
        structural=struct_engine,
        residual=residual_engine,
        conformal=conformal_dict,
        calibration_path=calib_out,
        residual_model_path=saved_model_path,
        conformal_path=conformal_out,
    )
