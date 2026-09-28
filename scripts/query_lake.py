#!/usr/bin/env python3
"""Run a SQL query against the generated DuckDB database."""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = ROOT / "lake" / "analytics.duckdb"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sql", help="SQL query to execute")
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    if not args.database.exists():
        raise SystemExit(f"Database not found: {args.database}. Run scripts/build_lake.py first.")

    with duckdb.connect(str(args.database), read_only=True) as connection:
        result = connection.execute(args.sql).fetchdf()
    with __import__("pandas").option_context("display.max_rows", args.limit):
        print(result.head(args.limit).to_string(index=False))


if __name__ == "__main__":
    main()
