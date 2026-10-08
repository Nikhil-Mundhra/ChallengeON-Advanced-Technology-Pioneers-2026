"""Schema and database report for the ChallengeON analytics lake."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate

from tourism_twin.config import SETTINGS
from tourism_twin.reporting.database_report.components import cover_background, make_styles, page_header_footer
from tourism_twin.reporting.database_report.data import load_data
from tourism_twin.reporting.database_report.story import build_story


OUTPUT = SETTINGS.pdf_dir / "challengeon_schema_database_report.pdf"


def build_database_report() -> Path:
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
    return OUTPUT
