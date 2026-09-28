#!/usr/bin/env python3
"""Build and validate the curated weekly market panel from analytics.duckdb."""

import sys
from pathlib import Path

# Ensure repo root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
from engine.panel import save_weekly_panel, OUTPUT_PANEL_PATH


def main():
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
    summary = (
        train_df.groupby("market")
        .agg(
            total_guests=("guests", "sum"),
            total_arrivals=("new_arrivals", "sum"),
            avg_los=("implied_los", "mean"),
            total_p2p=("p2p", "sum"),
            avg_multiplier=("effective_response_multiplier", "mean"),
            avg_lf=("load_factor", "mean"),
        )
        .sort_values("total_guests", ascending=False)
        .head(6)
    )
    print(summary.to_string())


if __name__ == "__main__":
    main()
