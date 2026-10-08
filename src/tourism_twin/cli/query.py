"""`twin query`: run read-only SQL against the DuckDB analytics database."""

from __future__ import annotations

import argparse
from pathlib import Path

from tourism_twin.config import SETTINGS


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("query", help="Run a SQL query against the analytics database")
    parser.add_argument("sql", help="SQL query to execute")
    parser.add_argument("--database", type=Path, default=SETTINGS.database_path)
    parser.add_argument("--limit", type=int, default=50)
    parser.set_defaults(func=query)


def query(args: argparse.Namespace) -> None:
    import duckdb
    import pandas as pd

    if not args.database.exists():
        raise SystemExit(f"Database not found: {args.database}. Run 'twin build-lake' first.")

    with duckdb.connect(str(args.database), read_only=True) as connection:
        result = connection.execute(args.sql).fetchdf()
    with pd.option_context("display.max_rows", args.limit):
        print(result.head(args.limit).to_string(index=False))
