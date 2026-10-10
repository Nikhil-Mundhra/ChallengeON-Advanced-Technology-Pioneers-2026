"""Presentation outputs: `twin charts`, `twin outlook` and `twin report {solution,database,deck}`."""

from __future__ import annotations

import argparse

from tourism_twin.config import SETTINGS


def register(subparsers: argparse._SubParsersAction) -> None:
    subparsers.add_parser("charts", help="Render the waterfall, tornado, and benchmark figures").set_defaults(func=charts)
    outlook_parser = subparsers.add_parser("outlook", help="Guests for a future winter under flat and trend arrivals scenarios")
    outlook_parser.add_argument("--winter", type=int, default=2026, help="December of this year to February of the next (default 2026)")
    outlook_parser.add_argument("--spec", default="twin_daily", help="Daily model spec (default twin_daily)")
    outlook_parser.set_defaults(func=outlook)
    report_parser = subparsers.add_parser("report", help="Build a PDF report or the slide deck (needs the 'report' extra)")
    report_parser.add_argument("kind", choices=["solution", "database", "deck"])
    report_parser.add_argument("--content", help="deck only: content YAML (default report/deck/deck.yaml)")
    report_parser.add_argument("--no-pdf", action="store_true", help="deck only: skip the LibreOffice PDF export")
    report_parser.set_defaults(func=report)


def charts(args: argparse.Namespace) -> None:
    from tourism_twin.reporting.charts import generate_charts

    if not SETTINGS.evaluation_results_path.exists():
        print("evaluation_results.json not found; skipping dynamic benchmark plot.")
    for path in generate_charts():
        print(f"Generated: {path}")


def outlook(args: argparse.Namespace) -> None:
    import json

    from tourism_twin.nowcast.outlook import Window, outlook_document

    document = outlook_document(Window.winter(args.winter), spec=args.spec)
    path = SETTINGS.output_dir / "outlook.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2), encoding="utf-8")
    print(f"{document['window']} vs {document['previous']['window']} ({document['previous']['guest_nights']:,.0f} guest-nights)")
    for name, scenario in document["scenarios"].items():
        print(f"  {name:6} {scenario['guest_nights']:,.0f} ({scenario['change_pct']:+.1f}%)")
    for row in document["backtest"]:
        print(f"  back-test {row['window']} {row['scenario']} {row['segment']}: season error {row['season_error_pct']:+.1f}%")
    print(f"written {path}")


def report(args: argparse.Namespace) -> None:
    if args.kind == "solution":
        from tourism_twin.reporting.solution_report import build_solution_report

        print(f"Successfully generated dynamic PDF: {build_solution_report()}")
    elif args.kind == "database":
        from tourism_twin.reporting.database_report import build_database_report

        print(build_database_report())
    else:
        from tourism_twin.reporting.deck import DEFAULT_CONTENT, build_deck

        result = build_deck(args.content or DEFAULT_CONTENT, pdf=not args.no_pdf)
        print(f"Deck: {result.pptx} ({result.slides} slides)")
        print(f"PDF: {result.pdf}" if result.pdf else "PDF: skipped (LibreOffice `soffice` not found, or --no-pdf)")
        if result.fallback_numbers:
            print("Numbers still from the deck's fallback block (run `twin validate` to source them from artifacts):")
            print("  " + ", ".join(result.fallback_numbers))
