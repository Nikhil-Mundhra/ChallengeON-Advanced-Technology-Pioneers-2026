"""Build the analytics lake: ingest the workbooks, gate them, write the lake, record the manifest."""

from __future__ import annotations

from tourism_twin.config import SETTINGS
from tourism_twin.data.ingest import build_flight_frame, build_guest_frame
from tourism_twin.data.lake_writer import write_lake
from tourism_twin.data.manifest import write_manifest
from tourism_twin.data.validation import validate


def build_lake() -> dict[str, int | float]:
    """Run the full raw-to-lake build and return the validation checks."""
    if not SETTINGS.source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {SETTINGS.source_dir}")

    guests = build_guest_frame()
    flights = build_flight_frame()
    checks = validate(guests, flights)
    write_lake(guests, flights)
    write_manifest(checks)
    return checks
