#!/usr/bin/env python3
"""Run the interactive web application for the Abu Dhabi Tourism Digital Twin."""

import argparse
import sys
from pathlib import Path

# Ensure repo root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.server import run_server


def main():
    parser = argparse.ArgumentParser(description="Abu Dhabi Tourism Digital Twin - Web UI")
    parser.add_argument("--port", type=int, default=8080, help="Port to serve on (default: 8080)")
    args = parser.parse_args()

    run_server(args.port)


if __name__ == "__main__":
    main()
