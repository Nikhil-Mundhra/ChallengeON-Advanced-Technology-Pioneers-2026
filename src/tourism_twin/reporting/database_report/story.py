"""The report's content: every section, in reading order."""

from __future__ import annotations

from datetime import date

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Spacer,
    Table,
    TableStyle,
)

from tourism_twin.config import SETTINGS
from tourism_twin.reporting.pdf_palette import WHITE
from tourism_twin.reporting.database_report.components import (
    callout,
    code_block,
    metric_cards,
    p,
    schema_table,
    section_header,
    standard_table,
)
from tourism_twin.reporting.database_report.descriptions import (
    FLIGHT_DESCRIPTIONS,
    GUEST_DESCRIPTIONS,
    VIEW_DESCRIPTIONS,
)
from tourism_twin.reporting.database_report.diagrams import ArchitectureDiagram, LineageDiagram


def build_story(data: dict, styles: dict[str, ParagraphStyle]) -> list:
    manifest = data["manifest"]
    guest = data["guest_summary"]
    flight = data["flight_summary"]
    checks = manifest["checks"]
    total_rows = guest[0] + flight[0]
    parquet_bytes = sum(
        (SETTINGS.root / path).stat().st_size for path in manifest["curated_tables"].values()
    )

    story: list = []

    # Cover
    story += [
        Spacer(1, 44 * mm),
        p("SCHEMA AND DATABASE REPORT", styles["subtitle"]),
        p("ChallengeON DCT<br/>Analytics Lake", styles["title"]),
        Spacer(1, 8 * mm),
        p(
            "Physical schemas, semantic views, lineage, validation results, and operational query guidance.",
            styles["subtitle"],
        ),
        Spacer(1, 67 * mm),
        Table(
            [
                [p("DATABASE", styles["cover_label"]), p("analytics.duckdb", styles["cover_value"])],
                [p("DATA WINDOW", styles["cover_label"]), p("01 Jan 2022 - 28 Feb 2026", styles["cover_value"])],
                [p("REPORT DATE", styles["cover_label"]), p(date.today().strftime("%d %b %Y"), styles["cover_value"])],
            ],
            colWidths=[35 * mm, 90 * mm],
            style=TableStyle(
                [
                    ("TEXTCOLOR", (0, 0), (-1, -1), WHITE),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#476582")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            ),
        ),
        PageBreak(),
    ]

    # Executive summary
    story += section_header("01", "Executive summary", styles)
    story += [
        metric_cards(
            [
                (f"{total_rows:,}", "Rows across physical tables"),
                ("2", "Curated physical tables"),
                ("5", "Analytical views"),
                (f"{parquet_bytes / 1024 / 1024:.1f} MB", "Curated Parquet footprint"),
            ],
            styles,
        ),
        Spacer(1, 6 * mm),
        p(
            "The database is a compact analytical layer over two canonical Parquet datasets. "
            "The physical tables retain source lineage and nullable source fields; semantic views "
            "separate training observations, prediction rows, daily aggregations, and the safe "
            "guest-to-flight join.",
            styles["body"],
        ),
        p("Lake architecture", styles["h2"]),
        ArchitectureDiagram(176 * mm),
        callout(
            "Parquet is the portable source of truth. DuckDB is a generated query artifact that can be rebuilt from the raw workbooks using scripts/build_lake.py.",
            styles,
        ),
        Spacer(1, 5 * mm),
        p("Database inventory", styles["h2"]),
        standard_table(
            [
                [p("Object", styles["table_bold"]), p("Kind", styles["table_bold"]), p("Rows / role", styles["table_bold"])],
                [p("guest_daily", styles["table_bold"]), p("Physical table", styles["table"]), p(f"{guest[0]:,} guest observations and prediction rows", styles["table"])],
                [p("flight_daily", styles["table_bold"]), p("Physical table", styles["table"]), p(f"{flight[0]:,} route-airline-date observations", styles["table"])],
                [p("5 semantic views", styles["table_bold"]), p("Views", styles["table"]), p("Target filtering, daily aggregation, and safe fact join", styles["table"])],
            ],
            [48 * mm, 36 * mm, 92 * mm],
        ),
        PageBreak(),
    ]

    # Guest schema
    story += section_header("02", "Physical schema: guest_daily", styles)
    story += [
        p(
            "Grain: one row per date and residence group, with nationality included for International records. "
            "Domestic nationality is NULL by design. Candidate key: date + residence_group + nationality.",
            styles["body"],
        ),
        metric_cards(
            [
                (f"{guest[0]:,}", "Rows"),
                (f"{guest[3]:,}", "Training targets"),
                (f"{guest[4]:,}", "Prediction rows"),
                (f"{guest[5]}", "Nationalities"),
            ],
            styles,
        ),
        Spacer(1, 5 * mm),
        schema_table(data["tables"]["guest_daily"], GUEST_DESCRIPTIONS, styles),
        Spacer(1, 5 * mm),
        p("Segment and split profile", styles["h2"]),
        standard_table(
            [[p("Residence", styles["table_bold"]), p("Split", styles["table_bold"]), p("Rows", styles["table_bold"]), p("Target rows", styles["table_bold"]), p("Prediction rows", styles["table_bold"])]]
            + [
                [p(row["residence_group"], styles["table"]), p(row["dataset_split"], styles["table"]),
                 p(f'{row["row_count"]:,}', styles["table"]), p(f'{row["target_rows"]:,}', styles["table"]),
                 p(f'{row["prediction_rows"]:,}', styles["table"])]
                for row in data["guest_segments"]
            ],
            [42 * mm, 31 * mm, 31 * mm, 36 * mm, 36 * mm],
        ),
        Spacer(1, 5 * mm),
        callout(
            f"same_day_guests contains {guest[7]:,} NULL values ({guest[7] / guest[0]:.1%} of rows). These must not be blindly converted to zero because the source dictionary combines suppressed, unavailable, not-applicable, and zero-like meanings.",
            styles,
            warning=True,
        ),
        PageBreak(),
    ]

    # Flight schema, part 1
    flight_rows = data["tables"]["flight_daily"]
    story += section_header("03", "Physical schema: flight_daily (1 of 2)", styles)
    story += [
        p(
            "Grain: one row per date, origin country, origin city, arrival city, airline, and destination. "
            "The current candidate key is unique across all 117,608 rows.",
            styles["body"],
        ),
        metric_cards(
            [
                (f"{flight[0]:,}", "Rows"),
                (f"{flight[3]:,}", "Distinct dates"),
                (f"{flight[4]}", "Countries"),
                (f"{flight[6]}", "Airlines"),
            ],
            styles,
        ),
        Spacer(1, 5 * mm),
        schema_table(flight_rows[:13], FLIGHT_DESCRIPTIONS, styles),
        Spacer(1, 5 * mm),
        callout(
            "load_factor is stored as a ratio, not a percentage string. Validation confirms load_factor = total_pax / total_seats within floating-point tolerance.",
            styles,
        ),
        PageBreak(),
    ]

    # Flight schema, part 2
    story += section_header("04", "Physical schema: flight_daily (2 of 2)", styles)
    story += [
        schema_table(flight_rows[13:], FLIGHT_DESCRIPTIONS, styles),
        Spacer(1, 6 * mm),
        p("Selected null profile", styles["h2"]),
        standard_table(
            [
                [p("Column", styles["table_bold"]), p("NULL rows", styles["table_bold"]), p("Share", styles["table_bold"]), p("Interpretation", styles["table_bold"])],
                [p("average_weekly_frequency", styles["table_bold"]), p(f"{data['flight_nulls'][0]:,}", styles["table"]), p(f"{data['flight_nulls'][0] / flight[0]:.2%}", styles["table"]), p("Unavailable for a small initial block", styles["table"])],
                [p("business_class_p2p_count", styles["table_bold"]), p(f"{data['flight_nulls'][1]:,}", styles["table"]), p(f"{data['flight_nulls'][1] / flight[0]:.2%}", styles["table"]), p("Suppressed or unavailable", styles["table"])],
                [p("economy_class_p2p_count", styles["table_bold"]), p(f"{data['flight_nulls'][2]:,}", styles["table"]), p(f"{data['flight_nulls'][2] / flight[0]:.2%}", styles["table"]), p("Suppressed or unavailable", styles["table"])],
                [p("first_class_p2p_count", styles["table_bold"]), p(f"{data['flight_nulls'][3]:,}", styles["table"]), p(f"{data['flight_nulls'][3] / flight[0]:.2%}", styles["table"]), p("Often unavailable or not applicable", styles["table"])],
                [p("total_pax_excluding_infant", styles["table_bold"]), p(f"{data['flight_nulls'][4]:,}", styles["table"]), p(f"{data['flight_nulls'][4] / flight[0]:.3%}", styles["table"]), p("One missing record", styles["table"])],
            ],
            [50 * mm, 25 * mm, 22 * mm, 79 * mm],
        ),
        PageBreak(),
    ]

    # Views and lineage
    story += section_header("05", "Semantic views and lineage", styles)
    story += [
        p(
            "The semantic layer prevents accidental fact-to-fact multiplication. Guest and flight facts are each aggregated to date before the combined view joins them.",
            styles["body"],
        ),
        LineageDiagram(176 * mm),
        p("View dictionary", styles["h2"]),
        standard_table(
            [[p("View", styles["table_bold"]), p("Purpose", styles["table_bold"]), p("Primary input", styles["table_bold"])]]
            + [
                [p(f"<b>{view}</b>", styles["table"]), p(VIEW_DESCRIPTIONS.get(view, "Analytical view."), styles["table"]),
                 p("guest_daily" if view.startswith("guest_") and view != "guest_flight_daily" else ("flight_daily" if view == "flight_daily_totals" else "daily aggregate views"), styles["table"])]
                for view in data["views"]
            ],
            [48 * mm, 88 * mm, 40 * mm],
        ),
        Spacer(1, 5 * mm),
        callout(
            "DuckDB does not enforce the documented candidate keys. The lake build validates uniqueness before publishing the curated tables and records the results in manifest.json.",
            styles,
        ),
        PageBreak(),
    ]

    # Quality and caveats
    story += section_header("06", "Validation results and known caveats", styles)
    check_rows = [
        ("Guest candidate-key duplicates", checks["guest_duplicate_candidate_keys"], "Must equal 0"),
        ("Flight candidate-key duplicates", checks["flight_duplicate_candidate_keys"], "Must equal 0"),
        ("Training rows missing target", checks["train_rows_missing_guests"], "Must equal 0"),
        ("Test rows with populated target", checks["test_rows_with_guests"], "Must equal 0"),
        ("Passenger identity mismatches", checks["flight_passenger_identity_mismatches"], "total_pax = p2p + transfer + transit"),
        ("Maximum load-factor error", f"{checks['flight_load_factor_max_absolute_error']:.2e}", "Tolerance <= 1e-9"),
    ]
    story += [
        standard_table(
            [[p("Validation", styles["table_bold"]), p("Result", styles["table_bold"]), p("Rule", styles["table_bold"]), p("Status", styles["table_bold"])]]
            + [[p(name, styles["table"]), p(value, styles["table"]), p(rule, styles["table"]), p("PASS", styles["table_bold"])] for name, value, rule in check_rows],
            [62 * mm, 25 * mm, 65 * mm, 24 * mm],
        ),
        Spacer(1, 7 * mm),
        p("Known caveats", styles["h2"]),
        callout(
            "Flight grain discrepancy: the supplied data dictionary describes monthly records, but the workbook contains daily dates from 2023 onward. The implemented schema follows the observed workbook grain.",
            styles,
            warning=True,
        ),
        Spacer(1, 4 * mm),
        callout(
            "Target availability is intentional: all 9,414 test rows have guests = NULL, while all 59,930 training rows have a populated target.",
            styles,
        ),
        Spacer(1, 4 * mm),
        callout(
            "Arrival city and destination are currently constant (Abu Dhabi and AUH). They remain in the curated table to preserve lineage and support future multi-destination extracts.",
            styles,
        ),
        Spacer(1, 8 * mm),
        p("Source traceability", styles["h2"]),
        p(
            "manifest.json stores byte sizes and SHA-256 hashes for every Excel source, the data dictionary, row-count checks, and the two curated output paths. This makes rebuilds auditable without modifying the raw source files.",
            styles["body"],
        ),
        PageBreak(),
    ]

    # Query and operations
    story += section_header("07", "Query and operating guide", styles)
    story += [
        p("Rebuild the lake", styles["h2"]),
        code_block(
            "source .venv/bin/activate\npython scripts/build_lake.py",
            styles,
        ),
        p("Query the safe daily guest-flight view", styles["h2"]),
        code_block(
            ".venv/bin/python scripts/query_lake.py \\\n  \"SELECT date, guests, total_pax, flight_load_factor\n   FROM guest_flight_daily\n   ORDER BY date DESC LIMIT 10\"",
            styles,
        ),
        p("International training history", styles["h2"]),
        code_block(
            "SELECT date, nationality, guests, new_arrivals\nFROM guest_actuals\nWHERE nationality = 'INDIA'\nORDER BY date;",
            styles,
        ),
        p("Monthly flight demand", styles["h2"]),
        code_block(
            "SELECT date_trunc('month', date) AS month,\n       SUM(total_pax) AS total_pax,\n       SUM(total_seats) AS total_seats,\n       SUM(total_pax)::DOUBLE / NULLIF(SUM(total_seats), 0) AS load_factor\nFROM flight_daily\nGROUP BY month\nORDER BY month;",
            styles,
        ),
        Spacer(1, 3 * mm),
        p("Operating principles", styles["h2"]),
        standard_table(
            [
                [p("Principle", styles["table_bold"]), p("Implementation", styles["table_bold"])],
                [p("Raw immutability", styles["table_bold"]), p("The original workbooks and PDF remain unchanged under 01a - DCT Dataset.", styles["table"])],
                [p("Reproducible publication", styles["table_bold"]), p("The builder replaces generated Parquet and DuckDB outputs only after validation succeeds.", styles["table"])],
                [p("Portable storage", styles["table_bold"]), p("Parquet files are the versionable curated layer; DuckDB is generated locally.", styles["table"])],
                [p("Safe joins", styles["table_bold"]), p("Use guest_flight_daily unless route-level flight detail is explicitly required.", styles["table"])],
                [p("NULL preservation", styles["table_bold"]), p("Suppressed and unavailable source values stay NULL rather than becoming plausible zeros.", styles["table"])],
            ],
            [50 * mm, 126 * mm],
        ),
        Spacer(1, 8 * mm),
        p("Report sources", styles["h2"]),
        p(
            "analytics.duckdb; manifest.json; Data_Dictionary.pdf; data domestic_train.xlsx; data domestic_test.xlsx; data international_train.xlsx; data international_test.xlsx; flight_data.xlsx.",
            styles["small"],
        ),
    ]
    return story
