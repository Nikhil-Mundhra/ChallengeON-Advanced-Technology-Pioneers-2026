"""Deterministic training: calibrate the structural chain, fit the flight response (the planning
chain's schedule elasticity and the capacity co-movement), fit the residual layer, calibrate the
conformal margins, and write the four artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from tourism_twin.config import SETTINGS
from tourism_twin.data.panel import TRAINING_CUTOFF, training_window
from tourism_twin.planning.capacity_trend import fit_comovement
from tourism_twin.planning.conformal import calibrate_conformal, save_conformal
from tourism_twin.planning.residual import ResidualMLEngine
from tourism_twin.planning.schedule_response import chain_panel, fit_schedule_response
from tourism_twin.planning.structural import StructuralEngine


@dataclass
class TrainingResult:
    structural: StructuralEngine
    residual: ResidualMLEngine
    conformal: Dict[str, Any]
    calibration_path: Path
    residual_model_path: Path
    conformal_path: Path
    flight_response_path: Path


def train_models(
    panel_path: Path = SETTINGS.panel_path,
    max_date: str = TRAINING_CUTOFF,
    calib_out: Path = SETTINGS.calibration_path,
    model_out: Path = SETTINGS.residual_model_path,
    conformal_out: Path = SETTINGS.conformal_path,
    flight_response_out: Path = SETTINGS.flight_response_path,
) -> TrainingResult:
    struct_engine = StructuralEngine.calibrate_from_panel(
        panel_path=panel_path,
        save_path=calib_out,
        max_date=max_date,
    )

    train_df = training_window(pd.read_parquet(panel_path), max_date)
    struct_engine.schedule = fit_schedule_response(chain_panel(max_date))
    flight_response = {"schedule": struct_engine.schedule.to_dict(), "capacity": fit_comovement(train_df).to_dict()}
    flight_response_out.parent.mkdir(parents=True, exist_ok=True)
    flight_response_out.write_text(json.dumps(flight_response, indent=2), encoding="utf-8")

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
        flight_response_path=flight_response_out,
    )
