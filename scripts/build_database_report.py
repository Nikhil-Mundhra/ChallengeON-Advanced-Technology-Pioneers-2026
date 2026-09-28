#!/usr/bin/env python3
"""Create the schema and database report for the ChallengeON analytics lake."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import duckdb
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
DATABASE = ROOT / "lake" / "analytics.duckdb"
MANIFEST = ROOT / "lake" / "manifest.json"
OUTPUT = ROOT / "output" / "pdf" / "challengeon_schema_database_report.pdf"

NAVY = colors.HexColor("#102A43")
BLUE = colors.HexColor("#2563EB")
TEAL = colors.HexColor("#0F766E")
SKY = colors.HexColor("#EAF2FF")
MINT = colors.HexColor("#E8F5F2")
AMBER = colors.HexColor("#D97706")
AMBER_BG = colors.HexColor("#FFF7E6")
RED = colors.HexColor("#B42318")
RED_BG = colors.HexColor("#FDECEC")
INK = colors.HexColor("#243B53")
MUTED = colors.HexColor("#627D98")
LINE = colors.HexColor("#D9E2EC")
PALE = colors.HexColor("#F5F7FA")
WHITE = colors.white


GUEST_DESCRIPTIONS = {
    "date": "Calendar date for the guest observation.",
    "residence_group": "Domestic or International segment.",
    "nationality": "Guest nationality; NULL for domestic rows.",
    "guests": "Prediction target. NULL in the test/prediction split.",
    "new_arrivals": "Guests newly arriving on the date.",
    "same_day_guests": "Same-day visitors. NULL can mean suppressed, unavailable, or not applicable.",
    "dataset_split": "Train or test source classification.",
    "source_file": "Original workbook filename for lineage.",
}

FLIGHT_DESCRIPTIONS = {
    "date": "Operating date represented by the record.",
    "departure_country_name": "Country from which the flight departs.",
    "departure_city": "Origin city.",
    "arrival_city": "Arrival city; currently Abu Dhabi.",
    "airline_name": "Operating carrier name.",
    "average_weekly_frequency": "Average weekly service frequency where supplied.",
    "business_class_p2p_count": "Point-to-point Business Class passengers.",
    "business_class_seat_capacity": "Business Class seats offered.",
    "economy_class_p2p_count": "Point-to-point Economy Class passengers.",
    "economy_class_seat_capacity": "Economy Class seats offered.",
    "first_class_p2p_count": "Point-to-point First Class passengers.",
    "first_class_seat_capacity": "First Class seats offered.",
    "load_factor": "Total passengers divided by total seats.",
    "total_p2p": "All point-to-point passengers.",
    "total_pax": "All passengers, including P2P, transfer, and transit.",
    "total_pax_excluding_infant": "Passengers excluding infants.",
    "total_seats": "Total seat capacity.",
    "total_transfer": "Passengers transferring to another flight at Abu Dhabi.",
    "total_transit": "Passengers transiting through Abu Dhabi.",
    "transfer_business_class_count": "Transfer passengers in Business Class.",
    "transfer_economy_class_count": "Transfer passengers in Economy Class.",
    "transfer_first_class_count": "Transfer passengers in First Class.",
    "transit_business_class_count": "Transit passengers in Business Class.",
    "transit_economy_class_count": "Transit passengers in Economy Class.",
    "transit_first_count": "Transit passengers in First Class.",
    "destination": "Destination IATA code; currently AUH.",
    "source_file": "Original workbook filename for lineage.",
}

VIEW_DESCRIPTIONS = {
    "guest_actuals": "Guest rows with a populated target for analysis and model training.",
    "guest_prediction_rows": "Guest rows whose target must be predicted.",
    "guest_daily_totals": "Guest facts aggregated to one row per date and dataset split.",
    "flight_daily_totals": "Flight facts aggregated to daily demand, capacity, and weighted load factor.",
    "guest_flight_daily": "Safe daily join between guest totals and flight totals.",
}


class ArchitectureDiagram(Flowable):
    def __init__(self, width: float, height: float = 93 * mm):
        super().__init__()
        self.width = width
        self.height = height

    def draw(self) -> None:
        c = self.canv
        boxes = [
            (0, 54 * mm, 49 * mm, 23 * mm, SKY, BLUE, "RAW", "5 Excel files\n+ data dictionary"),
            (62 * mm, 54 * mm, 49 * mm, 23 * mm, PALE, NAVY, "BUILD", "Typed ingestion\n+ validation"),
            (124 * mm, 54 * mm, 49 * mm, 23 * mm, MINT, TEAL, "CURATED", "2 Parquet\n+ tables"),
            (31 * mm, 11 * mm, 49 * mm, 23 * mm, SKY, BLUE, "QUERY", "DuckDB\n+ physical tables"),
            (93 * mm, 11 * mm, 49 * mm, 23 * mm, MINT, TEAL, "SEMANTIC", "5 analytical\n+ views"),
        ]
        for x, y, w, h, fill, stroke, label, detail in boxes:
            c.setFillColor(fill)
            c.setStrokeColor(stroke)
            c.setLineWidth(1.2)
            c.roundRect(x, y, w, h, 5, fill=1, stroke=1)
            c.setFillColor(stroke)
            c.setFont("Helvetica-Bold", 8)
            c.drawString(x + 4 * mm, y + h - 7 * mm, label)
            c.setFillColor(INK)
            c.setFont("Helvetica", 8.5)
            lines = detail.split("\n")
            for index, line in enumerate(lines):
                c.drawString(x + 4 * mm, y + h - (13 + index * 5) * mm, line)

        self._arrow(49 * mm, 65 * mm, 62 * mm, 65 * mm)
        self._arrow(111 * mm, 65 * mm, 124 * mm, 65 * mm)
        self._arrow(148 * mm, 54 * mm, 55 * mm, 34 * mm)
        self._arrow(80 * mm, 22 * mm, 93 * mm, 22 * mm)

    def _arrow(self, x1: float, y1: float, x2: float, y2: float) -> None:
        c = self.canv
        c.setStrokeColor(MUTED)
        c.setFillColor(MUTED)
        c.setLineWidth(1.2)
        c.line(x1, y1, x2, y2)
        angle_right = x2 >= x1
        direction = 1 if angle_right else -1
        c.line(x2, y2, x2 - direction * 2.5 * mm, y2 + 1.5 * mm)
        c.line(x2, y2, x2 - direction * 2.5 * mm, y2 - 1.5 * mm)


class LineageDiagram(Flowable):
    def __init__(self, width: float, height: float = 90 * mm):
        super().__init__()
        self.width = width
        self.height = height

    def draw(self) -> None:
        c = self.canv
        nodes = {
            "guest_daily": (0, 52, 48, 20, BLUE),
            "guest_actuals": (63, 67, 50, 16, TEAL),
            "guest_prediction_rows": (63, 44, 50, 16, TEAL),
            "guest_daily_totals": (63, 20, 50, 16, TEAL),
            "flight_daily": (0, 0, 48, 20, BLUE),
            "flight_daily_totals": (63, -1, 50, 16, TEAL),
            "guest_flight_daily": (127, 9, 50, 20, NAVY),
        }
        scale = mm
        for name, (x, y, w, h, color) in nodes.items():
            c.setFillColor(colors.Color(color.red, color.green, color.blue, alpha=0.09))
            c.setStrokeColor(color)
            c.roundRect(x * scale, y * scale, w * scale, h * scale, 4, fill=1, stroke=1)
            c.setFillColor(color)
            c.setFont("Helvetica-Bold", 7.5)
            c.drawCentredString((x + w / 2) * scale, (y + h / 2 - 1) * scale, name)

        edges = [
            ((48, 62), (63, 75)),
            ((48, 62), (63, 52)),
            ((48, 62), (63, 28)),
            ((48, 10), (63, 7)),
            ((113, 28), (127, 19)),
            ((113, 7), (127, 19)),
        ]
        c.setStrokeColor(MUTED)
        c.setLineWidth(1)
        for (x1, y1), (x2, y2) in edges:
            c.line(x1 * scale, y1 * scale, x2 * scale, y2 * scale)


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


def make_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title", parent=base["Title"], fontName="Helvetica-Bold", fontSize=25,
            leading=30, textColor=WHITE, alignment=TA_LEFT, spaceAfter=8,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle", parent=base["Normal"], fontName="Helvetica", fontSize=11,
            leading=16, textColor=colors.HexColor("#D9EAF7"), spaceAfter=8,
        ),
        "cover_label": ParagraphStyle(
            "CoverLabel", parent=base["Normal"], fontName="Helvetica", fontSize=7.5,
            leading=10, textColor=colors.HexColor("#9FB3C8"),
        ),
        "cover_value": ParagraphStyle(
            "CoverValue", parent=base["Normal"], fontName="Helvetica", fontSize=8.8,
            leading=11, textColor=WHITE,
        ),
        "h1": ParagraphStyle(
            "H1", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=17,
            leading=21, textColor=NAVY, spaceBefore=0, spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "H2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=11,
            leading=14, textColor=TEAL, spaceBefore=8, spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "Body", parent=base["BodyText"], fontName="Helvetica", fontSize=8.8,
            leading=12.5, textColor=INK, spaceAfter=6,
        ),
        "small": ParagraphStyle(
            "Small", parent=base["BodyText"], fontName="Helvetica", fontSize=7.5,
            leading=10, textColor=MUTED,
        ),
        "table": ParagraphStyle(
            "Table", parent=base["BodyText"], fontName="Helvetica", fontSize=7.2,
            leading=9.4, textColor=INK,
        ),
        "table_bold": ParagraphStyle(
            "TableBold", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=7.2,
            leading=9.4, textColor=INK,
        ),
        "callout": ParagraphStyle(
            "Callout", parent=base["BodyText"], fontName="Helvetica", fontSize=8.4,
            leading=12, textColor=INK,
        ),
        "code": ParagraphStyle(
            "Code", parent=base["Code"], fontName="Courier", fontSize=7.2,
            leading=10, textColor=WHITE, leftIndent=0, rightIndent=0,
        ),
    }


def p(text: object, style: ParagraphStyle) -> Paragraph:
    return Paragraph(str(text), style)


def section_header(number: str, title: str, styles: dict[str, ParagraphStyle]) -> list:
    return [p(f"{number}  {title}", styles["h1"]), Spacer(1, 1.5 * mm)]


def standard_table(data: list[list], widths: list[float], header: bool = True) -> Table:
    if header:
        header_style = ParagraphStyle(
            "InlineTableHeader", fontName="Helvetica-Bold", fontSize=7.2,
            leading=9.4, textColor=WHITE,
        )
        data = [
            [
                Paragraph(cell.getPlainText(), header_style)
                if isinstance(cell, Paragraph)
                else Paragraph(str(cell), header_style)
                for cell in data[0]
            ]
        ] + data[1:]
    table = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -1), 0.35, LINE),
    ]
    if header:
        style += [
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("LINEBELOW", (0, 0), (-1, 0), 0.8, NAVY),
        ]
    for row in range(1 if header else 0, len(data)):
        if row % 2 == 0:
            style.append(("BACKGROUND", (0, row), (-1, row), PALE))
    table.setStyle(TableStyle(style))
    return table


def metric_cards(metrics: list[tuple[str, str]], styles: dict[str, ParagraphStyle]) -> Table:
    cells = []
    for value, label in metrics:
        cells.append(
            [
                p(f"<font size='16' color='#102A43'><b>{value}</b></font>", styles["body"]),
                p(label, styles["small"]),
            ]
        )
    table = Table([cells], colWidths=[44 * mm] * len(cells), hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PALE),
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.6, LINE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return table


def callout(text: str, styles: dict[str, ParagraphStyle], warning: bool = False) -> Table:
    fill = AMBER_BG if warning else MINT
    stroke = AMBER if warning else TEAL
    label = "DATA NOTE" if warning else "DESIGN NOTE"
    table = Table(
        [[p(f"<b>{label}</b><br/>{text}", styles["callout"])]],
        colWidths=[176 * mm],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), fill),
                ("BOX", (0, 0), (-1, -1), 0.8, stroke),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return table


def code_block(text: str, styles: dict[str, ParagraphStyle]) -> Table:
    table = Table([[Preformatted(text, styles["code"])]], colWidths=[176 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), NAVY),
                ("BOX", (0, 0), (-1, -1), 0.6, NAVY),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return table


def schema_table(rows: list[dict], descriptions: dict[str, str], styles: dict[str, ParagraphStyle]) -> Table:
    data = [
        [p("Column", styles["table_bold"]), p("Type", styles["table_bold"]),
         p("Nullable", styles["table_bold"]), p("Definition", styles["table_bold"])],
    ]
    for row in rows:
        name = row["column_name"]
        data.append(
            [
                p(f"<b>{name}</b>", styles["table"]),
                p(row["column_type"], styles["table"]),
                p(row["null"].title(), styles["table"]),
                p(descriptions[name], styles["table"]),
            ]
        )
    return standard_table(data, [43 * mm, 25 * mm, 19 * mm, 89 * mm])


def page_header_footer(canvas, doc) -> None:
    canvas.saveState()
    page = canvas.getPageNumber()
    if page > 1:
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.5)
        canvas.line(17 * mm, A4[1] - 15 * mm, A4[0] - 17 * mm, A4[1] - 15 * mm)
        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(17 * mm, A4[1] - 11.5 * mm, "ChallengeON DCT analytics lake")
        canvas.drawRightString(A4[0] - 17 * mm, A4[1] - 11.5 * mm, "Schema and database report")
        canvas.line(17 * mm, 13 * mm, A4[0] - 17 * mm, 13 * mm)
        canvas.drawString(17 * mm, 8.5 * mm, "Generated from lake/analytics.duckdb and lake/manifest.json")
        canvas.drawRightString(A4[0] - 17 * mm, 8.5 * mm, f"Page {page}")
    canvas.restoreState()


def cover_background(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    canvas.setFillColor(BLUE)
    canvas.circle(A4[0] - 17 * mm, A4[1] - 25 * mm, 34 * mm, fill=1, stroke=0)
    canvas.setFillColor(TEAL)
    canvas.circle(A4[0] - 10 * mm, 28 * mm, 47 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#173F5F"))
    canvas.circle(7 * mm, 17 * mm, 40 * mm, fill=1, stroke=0)
    canvas.restoreState()


def build_story(data: dict, styles: dict[str, ParagraphStyle]) -> list:
    manifest = data["manifest"]
    guest = data["guest_summary"]
    flight = data["flight_summary"]
    checks = manifest["checks"]
    total_rows = guest[0] + flight[0]
    parquet_bytes = sum(
        (ROOT / path).stat().st_size for path in manifest["curated_tables"].values()
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
                [p(f"<b>{view}</b>", styles["table"]), p(VIEW_DESCRIPTIONS[view], styles["table"]),
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


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    data = load_data()
    styles = make_styles()

    doc = BaseDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=17 * mm,
        rightMargin=17 * mm,
        topMargin=20 * mm,
        bottomMargin=17 * mm,
        title="ChallengeON DCT Analytics Lake - Schema and Database Report",
        author="ChallengeON project",
        subject="Database schema, lineage, quality, and query guide",
    )
    cover_frame = Frame(17 * mm, 17 * mm, 176 * mm, 263 * mm, id="cover", showBoundary=0)
    body_frame = Frame(17 * mm, 17 * mm, 176 * mm, 260 * mm, id="body", showBoundary=0)
    doc.addPageTemplates(
        [
            PageTemplate(id="cover", frames=[cover_frame], onPage=cover_background, autoNextPageTemplate="body"),
            PageTemplate(id="body", frames=[body_frame], onPage=page_header_footer),
        ]
    )
    doc.build(build_story(data, styles))
    print(OUTPUT)


if __name__ == "__main__":
    main()
