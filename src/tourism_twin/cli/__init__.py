"""The `twin` command line: one entry point for every pipeline, modeling, and reporting task.

Heavy dependencies are imported inside each command so `twin --help` stays fast and a
missing optional extra only breaks the command that needs it.
"""

from __future__ import annotations

import argparse

from tourism_twin.cli import pipeline, query, reports, serve, simulate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="twin", description="Abu Dhabi Tourism Digital Twin")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for module in (pipeline, simulate, reports, serve, query):
        module.register(subparsers)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)
