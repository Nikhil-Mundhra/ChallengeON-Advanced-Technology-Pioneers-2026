"""Lake manifest: source file hashes, validation results, and the data-contract guarantees."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tourism_twin.config import SETTINGS
from tourism_twin.data.ingest import DATA_DICTIONARY_FILE, FLIGHT_FILE, GUEST_FILES


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_manifest(checks: dict[str, int | float]) -> None:
    source_files = [SETTINGS.source_dir / spec[0] for spec in GUEST_FILES]
    source_files.extend(
        [SETTINGS.source_dir / FLIGHT_FILE, SETTINGS.source_dir / DATA_DICTIONARY_FILE]
    )
    manifest = {
        "format_version": 2,
        "raw_location": SETTINGS.display_path(SETTINGS.source_dir),
        "curated_tables": {
            "guest_daily": SETTINGS.display_path(SETTINGS.guest_daily_path),
            "flight_daily": SETTINGS.display_path(SETTINGS.flight_daily_path),
            "flight_monthly": SETTINGS.display_path(SETTINGS.flight_monthly_path),
        },
        "database": SETTINGS.display_path(SETTINGS.database_path),
        "sources": {
            path.name: {"bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in source_files
        },
        "checks": checks,
        "data_contract_guarantees": [
            "flight_daily contains strictly daily observations from 2023-01-01 onward (116,395 rows).",
            "flight_monthly isolates the 2022 monthly observations (1,213 rows on 12 distinct month-start dates).",
            "guest_daily provides a complete 1,520-date x 45-nationality grid (68,400 intl + 1,520 domestic = 69,920 rows) with is_source_present and missingness flags.",
            "Load factors > 100% are preserved raw with is_load_factor_outlier flag; no silent truncation in curated store.",
            "All partial sums and suppressed records are transparently traceable via is_suppressed_arrival and is_suppressed_same_day.",
            # P1-E: real gates, enforced in validate()
            "new_arrivals <= guests for all present source rows (guest_arrivals_exceeds_guests_violations == 0).",
            "guests and new_arrivals are non-negative for all present source rows.",
        ],
    }
    SETTINGS.manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
