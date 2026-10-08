#!/usr/bin/env python3
"""Build and validate the curated weekly market panel from analytics.duckdb."""



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


if __name__ == "__main__":
    main()
