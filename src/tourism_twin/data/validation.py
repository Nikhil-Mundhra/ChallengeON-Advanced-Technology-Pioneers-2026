"""Data-contract gates on the ingested frames; a non-zero gate aborts the lake build."""

from __future__ import annotations

import pandas as pd


def validate(guests: pd.DataFrame, flights: pd.DataFrame) -> dict[str, int | float]:
    guest_key = ["date", "residence_group", "nationality"]
    flight_key = [
        "date",
        "departure_country_name",
        "departure_city",
        "arrival_city",
        "airline_name",
        "destination",
    ]

    checks: dict[str, int | float] = {
        "guest_rows_total": len(guests),
        "guest_source_rows_present": int(guests["is_source_present"].sum()),
        "guest_grid_absent_rows": int((guests["is_source_present"] == False).sum()),
        "flight_rows_total": len(flights),
        "flight_daily_rows": int((flights["source_grain"] == "daily").sum()),
        "flight_monthly_rows": int((flights["source_grain"] == "monthly").sum()),
        "flight_load_factor_outliers_count": int(flights["is_load_factor_outlier"].sum()),
        "guest_duplicate_candidate_keys": int(guests.duplicated(guest_key).sum()),
        "flight_duplicate_candidate_keys": int(flights.duplicated(flight_key).sum()),
        "train_rows_missing_guests": int(
            guests.loc[
                (guests["dataset_split"] == "train") & (guests["is_source_present"]), "guests"
            ].isna().sum()
        ),
        "test_rows_with_guests": int(
            guests.loc[guests["dataset_split"] == "test", "guests"].notna().sum()
        ),
        "flight_passenger_identity_mismatches": int(
            (
                flights["total_pax"]
                != flights["total_p2p"]
                + flights["total_transfer"]
                + flights["total_transit"]
            ).sum()
        ),
        "flight_load_factor_max_absolute_error": float(
            (
                flights["load_factor"]
                - flights["total_pax"] / flights["total_seats"]
            )
            .abs()
            .max()
        ),
        # FIX (P1-E): Implement the new_arrivals <= guests invariant gate.
        # Data dictionary: New Arrivals is always a subset of Guests.
        "guest_arrivals_exceeds_guests_violations": int(
            (
                guests["is_source_present"]
                & guests["guests"].notna()
                & guests["new_arrivals"].notna()
                & (guests["new_arrivals"] > guests["guests"])
            ).sum()
        ),
        # Non-negativity guard: guests and arrivals must never be negative counts.
        "guest_negative_guests_count": int(
            (guests["guests"].notna() & (guests["guests"] < 0)).sum()
        ),
        "guest_negative_arrivals_count": int(
            (guests["new_arrivals"].notna() & (guests["new_arrivals"] < 0)).sum()
        ),
    }

    required_zero_checks = (
        "guest_duplicate_candidate_keys",
        "flight_duplicate_candidate_keys",
        "train_rows_missing_guests",
        "test_rows_with_guests",
        "flight_passenger_identity_mismatches",
        # P1-E gates — must be zero for a clean build
        "guest_arrivals_exceeds_guests_violations",
        "guest_negative_guests_count",
        "guest_negative_arrivals_count",
    )
    failures = {name: checks[name] for name in required_zero_checks if checks[name] != 0}
    if checks["flight_load_factor_max_absolute_error"] > 1e-9:
        failures["flight_load_factor_max_absolute_error"] = checks[
            "flight_load_factor_max_absolute_error"
        ]
    if failures:
        raise ValueError(f"Data validation failed: {failures}")
    return checks
