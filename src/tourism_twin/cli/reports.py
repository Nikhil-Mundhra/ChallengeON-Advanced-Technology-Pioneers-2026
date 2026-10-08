"""Presentation outputs: `twin charts` and `twin report {solution,database}`."""

from __future__ import annotations

import argparse

from tourism_twin.config import SETTINGS


def register(subparsers: argparse._SubParsersAction) -> None:
    subparsers.add_parser("charts", help="Render the waterfall, tornado, and benchmark figures").set_defaults(func=charts)
    report_parser = subparsers.add_parser("report", help="Build a PDF report (needs the 'report' extra)")
    report_parser.add_argument("kind", choices=["solution", "database"])
    report_parser.set_defaults(func=report)


def charts(args: argparse.Namespace) -> None:
    from tourism_twin.reporting.charts import generate_charts

    if not SETTINGS.evaluation_results_path.exists():
        print("evaluation_results.json not found; skipping dynamic benchmark plot.")
    for path in generate_charts():
        print(f"Generated: {path}")


def report(args: argparse.Namespace) -> None:
    if args.kind == "solution":
        from tourism_twin.reporting.solution_report import build_solution_report

        print(f"Successfully generated dynamic PDF: {build_solution_report()}")
    else:
        from tourism_twin.reporting.database_report import build_database_report

        print(build_database_report())
