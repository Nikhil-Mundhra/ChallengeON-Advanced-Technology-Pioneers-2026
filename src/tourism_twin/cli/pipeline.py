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
    from tourism_twin.models.evaluation import save_evaluation

    payload = run_evaluation()
    _print_evaluation(payload)
    synced = save_evaluation(payload)
    print(f"\nSaved structured evaluation metrics to: {SETTINGS.evaluation_results_path}")
    if synced:
        print(f"Synchronized holdout coverage ({payload['demonstrated_coverage_pct']}%) into: {SETTINGS.conformal_path}")


def _metric_row(label: str, m: dict, width: int = 45) -> str:
    return f"{label:<{width}} {m['wmape']:>9.2%} {m['bias']:>+9.2%} {m['mae']:>12,.1f} {m['rmse']:>14,.1f}"


def _print_evaluation(payload: dict) -> None:
    window = payload["evaluation_window"]
    diag = payload["diagnostics"]
    print("=" * 90)
    print("STRICT FULL-WEEK FORWARD HOLDOUT BACK-TEST")
    print(f"Calibration Window: {window['train_weeks']} complete weeks ({window['train_range'][0]} to {window['train_range'][1]})")
    print(f"Forward Holdout:    {window['test_weeks']} complete weeks ({window['test_range'][0]} to {window['test_range'][1]})")
    print(f"Observations:       Train {window['observations_train']:,} | Test {window['observations_test']:,}")
    print("=" * 90)

    header = f"{'Evaluation Setting':<45} {'WMAPE':>10} {'Bias':>10} {'MAE':>12} {'RMSE':>14}"
    print("\n1. SEPARATION OF PLANNING, REALIZED-CHAIN, AND DOMESTIC DIAGNOSTICS:")
    print("-" * 90)
    print(header)
    print("-" * 90)
    print(_metric_row("International Planning Mode (Seats + Priors)", diag["international_planning_mode"]))
    print(_metric_row("International Realized-Chain (Realized P2P)", diag["international_realized_chain"]))
    print(_metric_row("Domestic Forecast Mode (Seasonal Prior)", diag["domestic_forecast_mode"]))
    print(_metric_row("Combined Planning-Mode Diagnostic", diag["combined_planning_mode"]))
    print(_metric_row("Combined Realized-Chain Diagnostic", diag["combined_realized_chain"]))
    print("-" * 90)

    print("\n2. MODEL BENCHMARK (Combined International & Domestic Forward Holdout):")
    print("-" * 90)
    print(header.replace("Evaluation Setting", "Model Architecture"))
    print("-" * 90)
    for name, m in payload["benchmark"].items():
        print(_metric_row(name, m))
    print("-" * 90)
    print(f"Demonstrated Holdout Interval Coverage: {payload['demonstrated_coverage_pct'] / 100:.1%} (Target nominal: ~80.0%)")
    print("=" * 90)

    print("\n3. MARKET-BY-MARKET ACCURACY BREAKDOWN (Combined Planning Mode):")
    print("-" * 90)
    print(f"{'Market':<30} {'Archetype':<20} {'Holdout Obs':>12} {'WMAPE':>10} {'Bias':>12}")
    print("-" * 90)
    for market, m in payload["market_breakdown"].items():
        print(f"{market:<30} {m['archetype']:<20} {m['observations']:>12} {m['wmape']:>9.2%} {m['bias']:>+11.2%}")
    print("-" * 90)

    print("\n4. SEASON-BY-SEASON ACCURACY BREAKDOWN:")
    print("-" * 75)
    print(f"{'Season':<25} {'Holdout Obs':>12} {'WMAPE':>10} {'Bias':>12}")
    print("-" * 75)
    for season, m in payload["season_breakdown"].items():
        print(f"{season:<25} {m['observations']:>12} {m['wmape']:>9.2%} {m['bias']:>+11.2%}")
    print("-" * 75)
