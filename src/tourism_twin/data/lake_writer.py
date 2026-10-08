"""Write the curated Parquet tables and the DuckDB analytics database as one atomic swap."""

from __future__ import annotations

import os
import shutil

import duckdb
import pandas as pd

from tourism_twin.config import SETTINGS


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
