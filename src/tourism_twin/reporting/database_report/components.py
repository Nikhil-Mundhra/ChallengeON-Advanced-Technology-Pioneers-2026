"""Paragraph styles, table and callout builders, and page decorations for the database report."""

from __future__ import annotations


from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)

from tourism_twin.reporting.pdf_palette import AMBER, AMBER_BG, BLUE, INK, LINE, MINT, MUTED, NAVY, PALE, TEAL, WHITE


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
                p(descriptions.get(name, "Column measure or metadata attribute."), styles["table"]),
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
