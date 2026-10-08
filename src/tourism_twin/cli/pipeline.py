"""Pipeline commands: `twin build-lake`, `build-panel`, `train`, `evaluate`."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from tourism_twin.config import SETTINGS
from tourism_twin.data.panel import TRAINING_CUTOFF


def register(subparsers: argparse._SubParsersAction) -> None:
    subparsers.add_parser("build-lake", help="Build the Parquet tables and DuckDB lake from the raw workbooks").set_defaults(func=build_lake)
    subparsers.add_parser("build-panel", help="Build the curated weekly market panel from the lake").set_defaults(func=build_panel)

    train_parser = subparsers.add_parser("train", help="Calibrate and save the structural, residual, and conformal artifacts")
    train_parser.add_argument("--max-date", dest="max_date", default=TRAINING_CUTOFF, help="Training cutoff date")
    train_parser.add_argument("--panel-path", dest="panel_path", type=Path, default=SETTINGS.panel_path, help="Path to weekly panel")
    train_parser.set_defaults(func=train)

    subparsers.add_parser("evaluate", help="Run the forward-holdout back-test and write evaluation results").set_defaults(func=evaluate)


def build_lake(args: argparse.Namespace) -> None:
    from tourism_twin.data.lake import build_lake as run_build

    checks = run_build()
    print(json.dumps(checks, indent=2))
    print(f"Built {SETTINGS.display_path(SETTINGS.database_path)}")


def build_panel(args: argparse.Namespace) -> None:
    from tourism_twin.data.panel import save_weekly_panel

    print(f"Building weekly market panel...")
    saved_path = save_weekly_panel()
    df = pd.read_parquet(saved_path)

    print(f"Successfully generated: {saved_path}")
    print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")
    print(f"Date range: {df['week_start'].min()} to {df['week_start'].max()}")
    print(f"Markets ({df['market'].nunique()}): {sorted(df['market'].unique())}")
    print(f"Splits: {df['dataset_split'].value_counts().to_dict()}")

    # Print sample metrics for top 5 markets in train split
    train_df = df[df["dataset_split"] == "train"]
    print("\n=== TRAIN SPLIT SUMMARY BY MARKET (Top 5 + Domestic) ===")
    # FIX (P1-A): Ratio metrics (LOS, multiplier, LF) must be computed as ratio-of-sums,
    # not mean-of-ratios. Using mean() violates Jensen's inequality: in low-volume weeks,
    # implied_los and effective_response_multiplier blow up, biasing the arithmetic mean
    # far above the capacity-weighted average. Correct form: sum(numerator) / sum(denominator).
    summary_raw = (
        train_df.groupby("market")
        .agg(
            total_guests=("guests", "sum"),
            total_arrivals=("new_arrivals", "sum"),
            total_p2p=("p2p", "sum"),
            total_pax=("pax", "sum"),
            total_seats=("seats", "sum"),
        )
        .sort_values("total_guests", ascending=False)
        .head(6)
    )
    summary_raw["weighted_los"] = summary_raw["total_guests"] / summary_raw["total_arrivals"].replace(0, float("nan"))
    summary_raw["weighted_multiplier"] = summary_raw["total_arrivals"] / summary_raw["total_p2p"].replace(0, float("nan"))
    summary_raw["weighted_lf"] = summary_raw["total_pax"] / summary_raw["total_seats"].replace(0, float("nan"))
    summary = summary_raw[["total_guests", "total_arrivals", "weighted_los", "total_p2p", "weighted_multiplier", "weighted_lf"]]
    print(summary.to_string())



def train(args: argparse.Namespace) -> None:
    from tourism_twin.models.training import train_models

    print("=" * 80)
    print("TRAINING ABU DHABI TOURISM DIGITAL TWIN MODELS")
    print(f"Panel Source: {args.panel_path}")
    print(f"Training Cutoff Date: {args.max_date} (Complete 7-day weeks)")
    print("=" * 80)

    result = train_models(panel_path=args.panel_path, max_date=args.max_date)

    print("\n1. Calibrating Structural Scenario Engine...")
    print(f"   Calibrated {len(result.structural.params)} markets saved to: {result.calibration_path}")
    print("\n2. Fitting Monotonic Residual ML Engine (RidgeCV)...")
    print(f"   Trained {len(result.residual.models)} residual models saved to: {result.residual_model_path}")
    print("\n3. Calibrating Conformal Uncertainty Bounds...")
    print(f"   Conformal calibrator saved to: {result.conformal_path} (demonstrated coverage: {result.conformal['_demonstrated_holdout_coverage']}%)")

    print("\n" + "=" * 80)
    print("MODEL TRAINING & ARTIFACT REBUILD COMPLETE")
    print("=" * 80)


def evaluate(args: argparse.Namespace) -> None:
    from tourism_twin.models.evaluation import evaluate as run_evaluation

    run_evaluation()
