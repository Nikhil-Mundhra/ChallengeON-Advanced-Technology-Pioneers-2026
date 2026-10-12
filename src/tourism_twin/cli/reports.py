"""Presentation outputs: `twin charts`, `twin outlook` and `twin report {solution,database,deck}`."""

from __future__ import annotations

import argparse

from tourism_twin.config import SETTINGS


def register(subparsers: argparse._SubParsersAction) -> None:
    subparsers.add_parser("charts", help="Render the waterfall, tornado, and benchmark figures").set_defaults(func=charts)
    outlook_parser = subparsers.add_parser("outlook", help="Guests for a future winter under flat and trend arrivals scenarios")
    outlook_parser.add_argument("--winter", type=int, default=2026, help="December of this year to February of the next (default 2026)")
    outlook_parser.add_argument("--spec", default="twin_daily", help="Daily model spec (default twin_daily)")
    outlook_parser.add_argument("--monthly", action="store_true",
                                help="Instead: the 12 months after the last known arrivals and the back-tested error by horizon")
    outlook_parser.set_defaults(func=outlook)
    report_parser = subparsers.add_parser("report", help="Build a PDF report or the slide deck (needs the 'report' extra)")
    report_parser.add_argument("kind", choices=["solution", "database", "deck"])
    report_parser.add_argument("--content", help="deck only: content YAML (default meta/deck/deck.yaml)")
    report_parser.add_argument("--no-pdf", action="store_true", help="deck only: skip the LibreOffice PDF export")
    report_parser.add_argument("--previews", action="store_true", help="deck only: also render one PNG per slide (needs pdftoppm)")
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

    if args.monthly:
        return _monthly_outlook(args.spec)
    document = outlook_document(Window.winter(args.winter), spec=args.spec)
    path = SETTINGS.output_dir / "outlook.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2), encoding="utf-8")
    print(f"{document['window']} vs {document['previous']['window']} ({document['previous']['guest_nights']:,.0f} guest-nights)")
    for name, scenario in document["scenarios"].items():
        print(f"  {name:6} {scenario['guest_nights']:,.0f} ({scenario['change_pct']:+.1f}%)")
    if not document["backtest"]:
        print("  back-test: none (the comparable past window has under a year of training guests)")
    for row in document["backtest"]:
        print(f"  back-test {row['window']} {row['scenario']} {row['segment']}: season error {row['season_error_pct']:+.1f}%")
    print(f"written {path}")


def _monthly_outlook(spec: str) -> None:
    import json

    from tourism_twin.nowcast.outlook import horizon_backtest, horizon_errors, monthly_outlook

    projections = monthly_outlook(spec)
    errors = horizon_errors(horizon_backtest(spec))
    path = SETTINGS.output_dir / "outlook_monthly.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    document = {"projections": {s: {str(m): row for m, row in frame.to_dict(orient="index").items()} for s, frame in projections.items()},
                "errors": errors.to_dict(orient="records")}
    path.write_text(json.dumps(document, indent=2), encoding="utf-8")
    total = errors[errors["segment"] == "TOTAL"].set_index(["scenario", "horizon_months"])
    for scenario, frame in projections.items():
        print(f"{scenario}, TOTAL: projection, calibrated = projection x (1 + median past miss), range")
        for horizon, (month, value) in enumerate(frame["TOTAL"].items(), start=1):
            if (scenario, horizon) not in total.index:
                print(f"  {month} h{horizon:<2} {value:,.0f}")
                continue
            r = total.loc[(scenario, horizon)]
            print(f"  {month} h{horizon:<2} {value:,.0f}  calibrated {value * (1 + r.miss_mid):,.0f}  "
                  f"range {value * (1 + r.miss_low):,.0f}..{value * (1 + r.miss_high):,.0f}")
    for r in total.reset_index().itertuples():
        print(f"  {r.scenario:5} h{r.horizon_months:<2} n={r.n:.0f} WAPE {r.wape_pct:5.1f}% bias {r.bias_pct:+6.1f}% "
              f"median miss {r.miss_mid:+.1%}, misses {r.miss_min:+.1%}..{r.miss_max:+.1%}")
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

        result = build_deck(args.content or DEFAULT_CONTENT, pdf=not args.no_pdf, previews=args.previews)
        print(f"Deck: {result.pptx} ({result.slides} slides)")
        print(f"PDF: {result.pdf}" if result.pdf else "PDF: skipped (LibreOffice `soffice` not found, or --no-pdf)")
        if result.previews:
            print(f"Previews: {result.previews[0].parent} ({len(result.previews)} PNG)")
        if result.fallback_numbers:
            print("Numbers still from the deck's fallback block (run `twin validate` and `twin outlook` to source them from artifacts):")
            print("  " + ", ".join(result.fallback_numbers))
