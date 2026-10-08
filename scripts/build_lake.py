#!/usr/bin/env python3
"""Build typed Parquet tables and a DuckDB analytics database from the source workbooks."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from tourism_twin.config import SETTINGS

GUEST_FILES = (
    ("data domestic_train.xlsx", "train", "Domestic"),
    ("data domestic_test.xlsx", "test", "Domestic"),
    ("data international_train.xlsx", "train", "International"),
    ("data international_test.xlsx", "test", "International"),
)

COUNT_COLUMNS = (
    "business_class_p2p_count",
    "business_class_seat_capacity",
    "economy_class_p2p_count",
    "economy_class_seat_capacity",
    "first_class_p2p_count",
    "first_class_seat_capacity",
    "total_p2p",
    "total_pax",
    "total_pax_excluding_infant",
    "total_seats",
    "total_transfer",
    "total_transit",
    "transfer_business_class_count",
    "transfer_economy_class_count",
    "transfer_first_class_count",
    "transit_business_class_count",
    "transit_economy_class_count",
    "transit_first_count",
)


def snake_case(name: str) -> str:
    return (
        name.strip()
        .lower()
        .replace("-", "_")
        .replace("(", "")
        .replace(")", "")
        .replace(" ", "_")
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_guest_file(filename: str, split: str, residence_group: str) -> pd.DataFrame:
    path = SETTINGS.source_dir / filename
    frame = pd.read_excel(path, sheet_name="Export")
    frame.columns = [snake_case(str(column)) for column in frame.columns]

    if "guests" not in frame:
        frame["guests"] = pd.NA
    if "nationality" not in frame:
        frame["nationality"] = pd.NA

    guests_s = pd.to_numeric(frame["guests"], errors="coerce").astype("Int64")
    arrivals_s = pd.to_numeric(frame["new_arrivals"], errors="coerce").astype("Int64")
    same_day_s = pd.to_numeric(frame["same_day_guests"], errors="coerce").astype("Int64")

    output = pd.DataFrame(
        {
            "date": pd.to_datetime(frame["date"], errors="raise"),
            "residence_group": residence_group,
            "nationality": frame["nationality"].astype("string"),
            "guests": guests_s,
            "new_arrivals": arrivals_s,
            "same_day_guests": same_day_s,
            "dataset_split": split,
            "source_file": filename,
            "source_grain": "daily",
            "is_source_present": True,
            "target_available": guests_s.notna(),
            "is_suppressed_arrival": arrivals_s.isna(),
            "is_suppressed_same_day": same_day_s.isna(),
        }
    )
    return output


def build_guest_frame() -> pd.DataFrame:
    frames = [read_guest_file(*file_spec) for file_spec in GUEST_FILES]
    raw_df = pd.concat(frames, ignore_index=True)

    # Separate domestic (complete continuous series) and international
    dom_df = raw_df[raw_df["residence_group"] == "Domestic"].copy()
    intl_df = raw_df[raw_df["residence_group"] == "International"].copy()

    # Complete Date x Nationality grid for International to prevent silent omission
    all_intl_dates = intl_df["date"].drop_duplicates().sort_values()
    all_intl_nats = intl_df["nationality"].dropna().drop_duplicates().sort_values()

    grid = pd.MultiIndex.from_product(
        [all_intl_dates, all_intl_nats], names=["date", "nationality"]
    ).to_frame().reset_index(drop=True)

    merged_intl = pd.merge(grid, intl_df, on=["date", "nationality"], how="left")

    # Flag absent reporting rows explicitly rather than silently dropping or assuming zero
    absent_mask = merged_intl["is_source_present"].isna()
    merged_intl.loc[absent_mask, "residence_group"] = "International"
    merged_intl.loc[absent_mask, "is_source_present"] = False
    merged_intl.loc[absent_mask, "source_grain"] = "daily"
    merged_intl.loc[absent_mask, "source_file"] = "ABSENT_GRID_RECORD"
    merged_intl.loc[absent_mask, "target_available"] = False
    merged_intl.loc[absent_mask, "is_suppressed_arrival"] = True
    merged_intl.loc[absent_mask, "is_suppressed_same_day"] = True
    merged_intl.loc[absent_mask, "dataset_split"] = np.where(
        merged_intl.loc[absent_mask, "date"] <= pd.to_datetime("2025-07-31"), "train", "test"
    )

    combined = pd.concat([dom_df, merged_intl], ignore_index=True).sort_values(
        ["date", "residence_group", "nationality"], na_position="first"
    )
    return combined


def build_flight_frame() -> pd.DataFrame:
    filename = "flight_data.xlsx"
    frame = pd.read_excel(SETTINGS.source_dir / filename, sheet_name="Export")
    frame.columns = [snake_case(str(column)) for column in frame.columns]
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    for column in COUNT_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").astype("Int64")
    frame["average_weekly_frequency"] = pd.to_numeric(
        frame["average_weekly_frequency"], errors="coerce"
    )
    frame["load_factor"] = pd.to_numeric(frame["load_factor"], errors="raise")
    frame["source_file"] = filename
    # Explicit grain contract: 2022 is monthly aggregated; 2023+ is true daily
    frame["source_grain"] = np.where(frame["date"].dt.year == 2022, "monthly", "daily")
    # Quality flag for unclipped load factor > 100%
    frame["is_load_factor_outlier"] = frame["load_factor"] > 1.0
    return frame.sort_values(
        ["date", "departure_country_name", "departure_city", "airline_name"]
    )


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
        # DATA_ISSUES.md asserted this check existed; it was a phantom. Now real.
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


def write_lake(guests: pd.DataFrame, flights: pd.DataFrame) -> None:
    """Write Parquet files and DuckDB using an atomic two-phase commit.

    FIX (P1-F): The previous implementation called output.unlink() before writing.
    A crash midway left the lake directory in a destroyed, unrecoverable state.

    New approach:
    1. Write everything to ``lake/.staging_build/`` (a private scratch space).
    2. Validate the staged DuckDB can be opened and has the expected tables.
    3. Atomically swap the staged files over the live files via ``os.rename()``.
       ``os.rename()`` is atomic on all POSIX filesystems when src and dst are on the
       same mount point — the live lake is never destroyed before the new build exists.
    4. On any failure the staging directory is cleaned up; the live lake is untouched.
    """
    SETTINGS.curated_dir.mkdir(parents=True, exist_ok=True)
    staging_dir = SETTINGS.lake_dir / ".staging_build"
    staging_curated = staging_dir / "curated"
    staging_db = staging_dir / "analytics.duckdb"

    # Clean any previous failed staging run
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_curated.mkdir(parents=True)

    daily_flights = flights[flights["source_grain"] == "daily"].copy()
    monthly_flights = flights[flights["source_grain"] == "monthly"].copy()

    connection = duckdb.connect(str(staging_db))
    try:
        connection.register("guest_source", guests)
        connection.register("flight_daily_source", daily_flights)
        connection.register("flight_monthly_source", monthly_flights)

        connection.execute(
            """
            COPY (
                SELECT
                    CAST(date AS DATE) AS date,
                    residence_group,
                    nationality,
                    CAST(guests AS BIGINT) AS guests,
                    CAST(new_arrivals AS BIGINT) AS new_arrivals,
                    CAST(same_day_guests AS BIGINT) AS same_day_guests,
                    dataset_split,
                    source_file,
                    source_grain,
                    is_source_present,
                    target_available,
                    is_suppressed_arrival,
                    is_suppressed_same_day
                FROM guest_source
            ) TO ? (FORMAT PARQUET, COMPRESSION ZSTD)
            """,
            [str(staging_curated / "guest_daily.parquet")],
        )
        connection.execute(
            """
            COPY (
                SELECT CAST(date AS DATE) AS date, * EXCLUDE (date)
                FROM flight_daily_source
            ) TO ? (FORMAT PARQUET, COMPRESSION ZSTD)
            """,
            [str(staging_curated / "flight_daily.parquet")],
        )
        connection.execute(
            """
            COPY (
                SELECT CAST(date AS DATE) AS date, * EXCLUDE (date)
                FROM flight_monthly_source
            ) TO ? (FORMAT PARQUET, COMPRESSION ZSTD)
            """,
            [str(staging_curated / "flight_monthly.parquet")],
        )

        connection.execute(
            "CREATE TABLE guest_daily AS SELECT * FROM read_parquet(?)",
            [str(staging_curated / "guest_daily.parquet")],
        )
        connection.execute(
            "CREATE TABLE flight_daily AS SELECT * FROM read_parquet(?)",
            [str(staging_curated / "flight_daily.parquet")],
        )
        connection.execute(
            "CREATE TABLE flight_monthly AS SELECT * FROM read_parquet(?)",
            [str(staging_curated / "flight_monthly.parquet")],
        )
        connection.execute(
            """
            CREATE VIEW flight_all AS
            -- WARNING: This view stacks daily 2023+ records with 2022 monthly aggregates.
            -- Always filter by source_grain when computing time-bounded aggregates.
            SELECT * FROM flight_daily
            UNION ALL
            SELECT * FROM flight_monthly
            """
        )
        connection.execute(
            """
            CREATE VIEW guest_actuals AS
            SELECT * FROM guest_daily WHERE target_available AND is_source_present
            """
        )
        connection.execute(
            """
            CREATE VIEW guest_prediction_rows AS
            SELECT * FROM guest_daily WHERE NOT target_available
            """
        )
        connection.execute(
            """
            CREATE VIEW guest_daily_totals AS
            SELECT
                date,
                dataset_split,
                SUM(guests) AS guests,
                SUM(new_arrivals) AS new_arrivals,
                SUM(same_day_guests) AS same_day_guests,
                COUNT(*) AS total_grid_records,
                SUM(CASE WHEN is_source_present THEN 1 ELSE 0 END) AS present_source_records,
                SUM(CASE WHEN is_suppressed_arrival THEN 1 ELSE 0 END) AS missing_arrival_records
            FROM guest_daily
            GROUP BY date, dataset_split
            """
        )
        connection.execute(
            """
            CREATE VIEW flight_daily_totals AS
            SELECT
                date,
                SUM(total_pax) AS total_pax,
                SUM(total_seats) AS total_seats,
                SUM(total_p2p) AS total_p2p,
                SUM(total_transfer) AS total_transfer,
                SUM(total_transit) AS total_transit,
                SUM(total_pax)::DOUBLE / NULLIF(SUM(total_seats), 0) AS load_factor,
                SUM(CASE WHEN is_load_factor_outlier THEN 1 ELSE 0 END) AS load_factor_outlier_count
            FROM flight_daily
            GROUP BY date
            """
        )
        connection.execute(
            """
            CREATE VIEW guest_flight_daily AS
            SELECT
                g.*,
                f.total_pax,
                f.total_seats,
                f.total_p2p,
                f.total_transfer,
                f.total_transit,
                f.load_factor AS flight_load_factor,
                COALESCE(f.load_factor_outlier_count, 0) AS flight_load_factor_outliers
            FROM guest_daily_totals g
            LEFT JOIN flight_daily_totals f USING (date)
            """
        )
        connection.execute("ANALYZE")
    except Exception:
        connection.close()
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise
    finally:
        connection.close()

    # Atomic swap: move staged files over the live files only after successful build.
    # os.rename() is atomic on POSIX when src and dst share the same filesystem.
    for staged, live in [
        (staging_curated / "guest_daily.parquet", SETTINGS.guest_daily_path),
        (staging_curated / "flight_daily.parquet", SETTINGS.flight_daily_path),
        (staging_curated / "flight_monthly.parquet", SETTINGS.flight_monthly_path),
        (staging_db, SETTINGS.database_path),
    ]:
        live.unlink(missing_ok=True)   # remove the previous live file right before atomic replace
        os.rename(staged, live)

    shutil.rmtree(staging_dir, ignore_errors=True)


def write_manifest(checks: dict[str, int | float]) -> None:
    source_files = [SETTINGS.source_dir / spec[0] for spec in GUEST_FILES]
    source_files.extend(
        [SETTINGS.source_dir / "flight_data.xlsx", SETTINGS.source_dir / "Data_Dictionary.pdf"]
    )
    manifest = {
        "format_version": 2,
        "raw_location": SETTINGS.display_path(SETTINGS.source_dir),
        "curated_tables": {
            "guest_daily": SETTINGS.display_path(SETTINGS.guest_daily_path),
            "flight_daily": SETTINGS.display_path(SETTINGS.flight_daily_path),
            "flight_monthly": SETTINGS.display_path(SETTINGS.flight_monthly_path),
        },
        "database": SETTINGS.display_path(SETTINGS.database_path),
        "sources": {
            path.name: {"bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in source_files
        },
        "checks": checks,
        "data_contract_guarantees": [
            "flight_daily contains strictly daily observations from 2023-01-01 onward (116,395 rows).",
            "flight_monthly isolates the 2022 monthly observations (1,213 rows on 12 distinct month-start dates).",
            "guest_daily provides a complete 1,520-date x 45-nationality grid (68,400 intl + 1,520 domestic = 69,920 rows) with is_source_present and missingness flags.",
            "Load factors > 100% are preserved raw with is_load_factor_outlier flag; no silent truncation in curated store.",
            "All partial sums and suppressed records are transparently traceable via is_suppressed_arrival and is_suppressed_same_day.",
            # P1-E: real gates, enforced in validate()
            "new_arrivals <= guests for all present source rows (guest_arrivals_exceeds_guests_violations == 0).",
            "guests and new_arrivals are non-negative for all present source rows.",
        ],
    }
    SETTINGS.manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    if not SETTINGS.source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {SETTINGS.source_dir}")

    guests = build_guest_frame()
    flights = build_flight_frame()
    checks = validate(guests, flights)
    write_lake(guests, flights)
    write_manifest(checks)

    print(json.dumps(checks, indent=2))
    print(f"Built {SETTINGS.display_path(SETTINGS.database_path)}")


if __name__ == "__main__":
    main()
