#!/usr/bin/env python3
"""Build typed Parquet tables and a DuckDB analytics database from the source workbooks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import duckdb
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "01a - DCT Dataset"
LAKE_DIR = ROOT / "lake"
CURATED_DIR = LAKE_DIR / "curated"
DATABASE_PATH = LAKE_DIR / "analytics.duckdb"
MANIFEST_PATH = LAKE_DIR / "manifest.json"

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
    path = SOURCE_DIR / filename
    frame = pd.read_excel(path, sheet_name="Export")
    frame.columns = [snake_case(str(column)) for column in frame.columns]

    if "guests" not in frame:
        frame["guests"] = pd.NA
    if "nationality" not in frame:
        frame["nationality"] = pd.NA

    output = pd.DataFrame(
        {
            "date": pd.to_datetime(frame["date"], errors="raise"),
            "residence_group": residence_group,
            "nationality": frame["nationality"].astype("string"),
            "guests": pd.to_numeric(frame["guests"], errors="coerce").astype("Int64"),
            "new_arrivals": pd.to_numeric(frame["new_arrivals"], errors="coerce").astype("Int64"),
            "same_day_guests": pd.to_numeric(
                frame["same_day_guests"], errors="coerce"
            ).astype("Int64"),
            "dataset_split": split,
            "source_file": filename,
        }
    )
    return output


def build_guest_frame() -> pd.DataFrame:
    frames = [read_guest_file(*file_spec) for file_spec in GUEST_FILES]
    return pd.concat(frames, ignore_index=True).sort_values(
        ["date", "residence_group", "nationality"], na_position="first"
    )


def build_flight_frame() -> pd.DataFrame:
    filename = "flight_data.xlsx"
    frame = pd.read_excel(SOURCE_DIR / filename, sheet_name="Export")
    frame.columns = [snake_case(str(column)) for column in frame.columns]
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    for column in COUNT_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").astype("Int64")
    frame["average_weekly_frequency"] = pd.to_numeric(
        frame["average_weekly_frequency"], errors="coerce"
    )
    frame["load_factor"] = pd.to_numeric(frame["load_factor"], errors="raise")
    frame["source_file"] = filename
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
        "guest_rows": len(guests),
        "flight_rows": len(flights),
        "guest_duplicate_candidate_keys": int(guests.duplicated(guest_key).sum()),
        "flight_duplicate_candidate_keys": int(flights.duplicated(flight_key).sum()),
        "train_rows_missing_guests": int(
            guests.loc[guests["dataset_split"] == "train", "guests"].isna().sum()
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
    }

    required_zero_checks = (
        "guest_duplicate_candidate_keys",
        "flight_duplicate_candidate_keys",
        "train_rows_missing_guests",
        "test_rows_with_guests",
        "flight_passenger_identity_mismatches",
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
    CURATED_DIR.mkdir(parents=True, exist_ok=True)
    for output in (
        CURATED_DIR / "guest_daily.parquet",
        CURATED_DIR / "flight_daily.parquet",
        DATABASE_PATH,
    ):
        output.unlink(missing_ok=True)

    connection = duckdb.connect(str(DATABASE_PATH))
    try:
        connection.register("guest_source", guests)
        connection.register("flight_source", flights)

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
                    source_file
                FROM guest_source
            ) TO ? (FORMAT PARQUET, COMPRESSION ZSTD)
            """,
            [str(CURATED_DIR / "guest_daily.parquet")],
        )
        connection.execute(
            """
            COPY (
                SELECT CAST(date AS DATE) AS date, * EXCLUDE (date)
                FROM flight_source
            ) TO ? (FORMAT PARQUET, COMPRESSION ZSTD)
            """,
            [str(CURATED_DIR / "flight_daily.parquet")],
        )

        connection.execute(
            "CREATE TABLE guest_daily AS SELECT * FROM read_parquet(?)",
            [str(CURATED_DIR / "guest_daily.parquet")],
        )
        connection.execute(
            "CREATE TABLE flight_daily AS SELECT * FROM read_parquet(?)",
            [str(CURATED_DIR / "flight_daily.parquet")],
        )
        connection.execute(
            """
            CREATE VIEW guest_actuals AS
            SELECT * FROM guest_daily WHERE guests IS NOT NULL
            """
        )
        connection.execute(
            """
            CREATE VIEW guest_prediction_rows AS
            SELECT * FROM guest_daily WHERE guests IS NULL
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
                SUM(same_day_guests) AS same_day_guests
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
                SUM(total_pax)::DOUBLE / NULLIF(SUM(total_seats), 0) AS load_factor
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
                f.load_factor AS flight_load_factor
            FROM guest_daily_totals g
            LEFT JOIN flight_daily_totals f USING (date)
            """
        )
        connection.execute("ANALYZE")
    finally:
        connection.close()


def write_manifest(checks: dict[str, int | float]) -> None:
    source_files = [SOURCE_DIR / spec[0] for spec in GUEST_FILES]
    source_files.extend(
        [SOURCE_DIR / "flight_data.xlsx", SOURCE_DIR / "Data_Dictionary.pdf"]
    )
    manifest = {
        "format_version": 1,
        "raw_location": "01a - DCT Dataset",
        "curated_tables": {
            "guest_daily": "lake/curated/guest_daily.parquet",
            "flight_daily": "lake/curated/flight_daily.parquet",
        },
        "database": "lake/analytics.duckdb",
        "sources": {
            path.name: {"bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in source_files
        },
        "checks": checks,
        "notes": [
            "Missing same_day_guests values remain NULL because the dictionary combines zero, suppressed, unavailable, and not-applicable meanings.",
            "The flight workbook is treated as daily because it contains daily dates from 2023 onward, despite the dictionary describing monthly data.",
        ],
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    if not SOURCE_DIR.exists():
        raise FileNotFoundError(f"Source directory not found: {SOURCE_DIR}")

    guests = build_guest_frame()
    flights = build_flight_frame()
    checks = validate(guests, flights)
    write_lake(guests, flights)
    write_manifest(checks)

    print(json.dumps(checks, indent=2))
    print(f"Built {DATABASE_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
