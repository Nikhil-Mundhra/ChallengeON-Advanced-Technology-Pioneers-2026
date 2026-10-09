"""`twin evaluate-model`: score a fitted model on a later window, without refitting it."""

from __future__ import annotations

import argparse
import json


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "evaluate-model",
        help="Fit a spec up to a date (or load a saved model) and score it on a later window",
    )
    parser.add_argument("--spec", default="twin_daily", help="Daily spec name (nowcast/specs.py DAILY_SPECS)")
    parser.add_argument("--model", help="Path of a saved model (.pkl from a previous run); skips fitting")
    parser.add_argument("--start", help="First evaluated date (YYYY-MM-DD)")
    parser.add_argument("--end", help="Last evaluated date (YYYY-MM-DD)")
    parser.add_argument("--gap-days", type=int, default=21,
                        help="Days between the last training day and --start when fitting (default 21, the #11 protocol)")
    parser.add_argument("--frozen-test", action="store_true",
                        help="Score the frozen test window 2025-02-01..2025-07-31 (protocol: once, after every choice is final)")
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> None:
    import pandas as pd

    from tourism_twin.config import SETTINGS
    from tourism_twin.data.daily_panel import build_daily_panel
    from tourism_twin.models.backtest import FROZEN_TEST
    from tourism_twin.models.evaluate import card_for, evaluate_fitted, load_model, save_model
    from tourism_twin.nowcast.specs import DAILY_SPECS

    frozen_start, frozen_end = FROZEN_TEST.start, FROZEN_TEST.end
    if args.frozen_test:
        start, end = frozen_start, frozen_end
    else:
        if not (args.start and args.end):
            raise SystemExit("Give --start and --end, or --frozen-test")
        start, end = pd.Timestamp(args.start), pd.Timestamp(args.end)
        if start <= frozen_end and end >= frozen_start:
            raise SystemExit(f"Window overlaps the frozen test {frozen_start.date()}..{frozen_end.date()}; "
                             "pass --frozen-test to score it (once, after every choice is final)")

    panel = build_daily_panel()
    dates = pd.to_datetime(panel["date"])
    if args.model:
        model, card = load_model(args.model)
        model_path = args.model
    else:
        if args.spec not in DAILY_SPECS:
            raise SystemExit(f"Unknown spec {args.spec!r}; choose from {sorted(DAILY_SPECS)}")
        train_end = start - pd.Timedelta(days=args.gap_days + 1)
        train = panel[(dates <= train_end) & panel["guests"].notna()]
        model = DAILY_SPECS[args.spec]().fit(train)
        card = card_for(args.spec, train)
        model_path = save_model(model, card, SETTINGS.output_dir / "models" / f"{args.spec}_{card.train_end}.pkl")

    window = panel[(dates >= start) & (dates <= end)]
    scorecard = evaluate_fitted(model, window, card)

    out = SETTINGS.output_dir / "evaluations" / f"{card.spec}_{start.date()}_{end.date()}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({**scorecard.to_dict(), "model_path": str(model_path)}, indent=2))

    print(f"Model {card.spec}: trained {card.train_start}..{card.train_end} ({card.rows} rows); "
          f"scored {start.date()}..{end.date()}")
    table = scorecard.metrics.assign(wmape=lambda m: m["wmape"] * 100, bias=lambda m: m["bias"] * 100)
    print(table[["segment", "grain", "n", "wmape", "bias", "rmse", "mse"]].round(2).to_string(index=False))
    if not scorecard.direction.empty:
        print(scorecard.direction.round(3).to_string(index=False))
    print(f"Saved {out}")
