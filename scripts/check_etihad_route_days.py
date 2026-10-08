"""Check selected challenge route-days against Etihad's published 2024 timetables.

This checks schedule compatibility, not observed operation or passenger counts.
"""

from __future__ import annotations

import datetime as dt
import json

import duckdb

from engine.config import SETTINGS


ROOT = SETTINGS.root
OUT = ROOT / "research" / "real_world_validation" / "etihad_2024_route_checks.json"
CHECKS = [
    {"city": "Gassim", "airport": "ELQ", "flight": "EY0628", "start": "2024-06-24", "end": "2024-10-26", "weekdays": [0, 2, 4, 5], "local_arrival": "13:20", "source": "https://www.etihad.com/en-us/news/etihad-airways-explores-new-horizons-in-the-middle-east-with-the-launch-of-its-newest-destination"},
    {"city": "Jaipur", "airport": "JAI", "flight": "EY0367", "start": "2024-06-16", "end": "2024-07-26", "weekdays": [0, 2, 4, 6], "local_arrival": "13:00", "source": "https://www.etihad.com/en-in/news/etihad-airways-adds-new-route-to-northwest-india-with-four-weekly-flights-to-jaipur"},
    {"city": "Antalya", "airport": "AYT", "flight": "EY0540", "start": "2024-06-15", "end": "2024-09-14", "weekdays": [1, 3, 5], "local_arrival": "19:45", "source": "https://www.etihad.com/en-ae/news/etihad-airways-expands-schedule-with-two-stunning-new-destinations-and-additional-flights"},
]


def main() -> None:
    con = duckdb.connect()
    source = str(SETTINGS.flight_daily_path)
    results = []
    for check in CHECKS:
        start = dt.date.fromisoformat(check["start"])
        end = dt.date.fromisoformat(check["end"])
        expected = {start + dt.timedelta(days=i) for i in range((end - start).days + 1) if (start + dt.timedelta(days=i)).weekday() in check["weekdays"]}
        observed = {row[0] for row in con.execute("SELECT date FROM read_parquet(?) WHERE airline_name = 'Etihad Airways' AND departure_city = ? AND date BETWEEN ? AND ?", [source, check["city"], start, end]).fetchall()}
        results.append({**check, "scheduled_days_in_window": len(expected), "challenge_route_days": len(observed), "scheduled_days_missing_in_challenge": sorted(str(x) for x in expected - observed), "challenge_days_outside_published_weekdays": sorted(str(x) for x in observed - expected)})
    OUT.write_text(json.dumps({"interpretation": "Route-day schedule overlap only; challenge workbook has no flight number or timestamp, so exact flight operation is unverified.", "checks": results}, indent=2) + "\n")
    for row in results:
        print(row["city"], row["challenge_route_days"], "/", row["scheduled_days_in_window"], "missing", len(row["scheduled_days_missing_in_challenge"]), "extra", len(row["challenge_days_outside_published_weekdays"]))


if __name__ == "__main__":
    main()
