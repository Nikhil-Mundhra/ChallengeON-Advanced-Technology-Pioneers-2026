"""`twin export`: write the static, versioned serving bundle (export/bundle.py)."""

from __future__ import annotations

import argparse
from pathlib import Path

from tourism_twin.config import SETTINGS


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("export", help="Fit, predict and write the static versioned bundle the web dashboard reads")
    parser.add_argument("--out", type=Path, default=SETTINGS.root / "web" / "public" / "data", help="bundle directory")
    parser.add_argument("--spec", default="twin_daily")
    parser.set_defaults(func=export)


def export(args: argparse.Namespace) -> None:
    import pandas as pd

    from tourism_twin.data.daily_panel import build_daily_panel
    from tourism_twin.export.bundle import write_bundle
    from tourism_twin.nowcast.predict import predict_test_split

    predictions = predict_test_split(spec=args.spec)
    target = write_bundle(predictions, build_daily_panel(), pd.read_parquet(SETTINGS.panel_path), args.out, spec=args.spec)
    print(f"bundle {target}  (manifest {args.out / 'manifest.json'})")
