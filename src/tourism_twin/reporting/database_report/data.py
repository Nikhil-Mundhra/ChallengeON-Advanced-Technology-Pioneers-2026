"""Facts for the database report, read from the lake manifest and the DuckDB catalog."""

from __future__ import annotations

import json

import duckdb

from tourism_twin.config import SETTINGS


DATABASE = SETTINGS.database_path


MANIFEST = SETTINGS.manifest_path


def load_data() -> dict:
    if not DATABASE.exists():
        raise FileNotFoundError(f"Database not found: {DATABASE}")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    connection = duckdb.connect(str(DATABASE), read_only=True)
    try:
        tables = {
            table: connection.execute(f"DESCRIBE {table}").fetchdf().to_dict("records")
            for table in ("guest_daily", "flight_daily")
        }
        guest_summary = connection.execute(
            """
            SELECT COUNT(*) AS row_count, MIN(date) AS min_date, MAX(date) AS max_date,
                   COUNT(guests) AS target_rows, COUNT(*) - COUNT(guests) AS prediction_rows,
                   COUNT(DISTINCT nationality) AS nationalities,
                   COUNT(*) - COUNT(new_arrivals) AS new_arrivals_nulls,
                   COUNT(*) - COUNT(same_day_guests) AS same_day_nulls
            FROM guest_daily
            """
        ).fetchone()
        guest_segments = connection.execute(
            """
            SELECT residence_group, dataset_split, COUNT(*) AS row_count,
                   COUNT(guests) AS target_rows, COUNT(*) - COUNT(guests) AS prediction_rows
            FROM guest_daily GROUP BY ALL ORDER BY 1, 2
            """
        ).fetchdf().to_dict("records")
        flight_summary = connection.execute(
            """
            SELECT COUNT(*) AS row_count, MIN(date) AS min_date, MAX(date) AS max_date,
                   COUNT(DISTINCT date) AS dates,
                   COUNT(DISTINCT departure_country_name) AS countries,
                   COUNT(DISTINCT departure_city) AS cities,
                   COUNT(DISTINCT airline_name) AS airlines
            FROM flight_daily
            """
        ).fetchone()
        flight_nulls = connection.execute(
            """
            SELECT COUNT(*) - COUNT(average_weekly_frequency),
                   COUNT(*) - COUNT(business_class_p2p_count),
                   COUNT(*) - COUNT(economy_class_p2p_count),
                   COUNT(*) - COUNT(first_class_p2p_count),
                   COUNT(*) - COUNT(total_pax_excluding_infant)
            FROM flight_daily
            """
        ).fetchone()
        views = connection.execute(
            """
            SELECT view_name FROM duckdb_views()
            WHERE internal = false ORDER BY view_name
            """
        ).fetchall()
    finally:
        connection.close()

    return {
        "manifest": manifest,
        "tables": tables,
        "guest_summary": guest_summary,
        "guest_segments": guest_segments,
        "flight_summary": flight_summary,
        "flight_nulls": flight_nulls,
        "views": [row[0] for row in views],
    }
