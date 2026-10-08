"""Vector diagrams drawn into the report: lake architecture and data lineage."""

from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
)

from tourism_twin.reporting.pdf_palette import BLUE, INK, MINT, MUTED, NAVY, PALE, SKY, TEAL


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
