"""Compare a source-linked sample of announced 2024 Etihad routes with route-days.

The catalog is intentionally finite and manually verified from Etihad releases.
It is a route presence audit, not a complete network or flight-operation audit.
"""

from __future__ import annotations

import csv

import duckdb

from tourism_twin.config import SETTINGS


ROOT = SETTINGS.root
OUTPUT = ROOT / "research/real_world_validation/etihad_2024_coverage_matrix.csv"
SUMMER = "https://www.etihad.com/en-us/news/etihad-airways-celebrates-launch-flights-to-eight-more-destinations-this-june"
SCHEDULE = "https://www.etihad.com/en-us/news/etihad-unleashes-sizzling-summer-schedule"
ROUTES = [
    ("Kozhikode", "Kozhikode", "2024-01-01", "2024-12-31", "https://www.etihad.com/en/news/new-year-new-flights-as-etihad-welcomes-2024-with-more-destinations-to-india"),
    ("Thiruvananthapuram", "Trivandrum", "2024-01-01", "2024-12-31", "https://www.etihad.com/en/news/new-year-new-flights-as-etihad-welcomes-2024-with-more-destinations-to-india"),
    ("Copenhagen", "Copenhagen", "2024-03-31", "2024-12-31", SCHEDULE),
    ("Boston", "Boston", "2024-03-31", "2024-12-31", "https://www.etihad.com/en-ae/news/etihad-airways-celebrates-inaugural-flight-to-boston"),
    ("Malaga", "Malaga", "2024-06-02", "2024-09-30", SUMMER),
    ("Antalya", "Antalya", "2024-06-15", "2024-09-30", SUMMER),
    ("Santorini", "Santorini", "2024-06-15", "2024-09-30", SUMMER),
    ("Nice", "Nice", "2024-06-15", "2024-09-30", SUMMER),
    ("Jaipur", "Jaipur", "2024-06-16", "2024-12-31", SUMMER),
    ("Mykonos", "Mykonos", "2024-06-17", "2024-09-30", SUMMER),
    ("Al Qassim", "Gassim", "2024-06-24", "2024-12-31", "https://www.etihad.com/en-qa/news/etihad-airways-operates-first-flight-to-al-qassim"),
    ("Bali / Denpasar", "Denpasar", "2024-06-25", "2024-12-31", "https://www.etihad.com/en-de/news/etihad-airways-celebrates-launch-of-direct-flights-to-bali"),
]


def main() -> None:
    con = duckdb.connect()
    source = str(SETTINGS.flight_daily_path)
    rows = []
    for name, city_label, start, end, url in ROUTES:
        count, first, last, pax = con.execute(
            """SELECT count(*), min(date), max(date), sum(total_pax)
               FROM read_parquet(?)
               WHERE airline_name = 'Etihad Airways' AND departure_city = ?
                 AND date BETWEEN ? AND ?""",
            [source, city_label, start, end],
        ).fetchone()
        rows.append({
            "published_destination": name,
            "challenge_city_label": city_label,
            "source_window_start": start,
            "source_window_end": end,
            "route_days_in_challenge": count,
            "first_challenge_date": first or "",
            "last_challenge_date": last or "",
            "challenge_total_pax": pax if pax is not None else "",
            "status": "present" if count else "absent_in_challenge",
            "etihad_source_url": url,
        })
    with OUTPUT.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} published routes checked; {sum(r['status'] == 'absent_in_challenge' for r in rows)} absent in challenge")


if __name__ == "__main__":
    main()
