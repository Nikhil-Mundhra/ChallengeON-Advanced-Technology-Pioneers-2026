"""`twin serve`: the interactive web application."""

from __future__ import annotations

import argparse


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("serve", help="Serve the interactive web UI and JSON API")
    parser.add_argument("--port", type=int, default=8080, help="Port to serve on (default: 8080)")
    parser.add_argument("--host", default="127.0.0.1",
                        help="Bind address (default: 127.0.0.1; use 0.0.0.0 in a container)")
    parser.set_defaults(func=serve)


def serve(args: argparse.Namespace) -> None:
    from app.server import run_server

    run_server(args.port, args.host)
