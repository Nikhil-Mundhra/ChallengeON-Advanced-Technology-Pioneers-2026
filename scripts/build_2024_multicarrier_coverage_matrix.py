"""Audit selected 2024 non-Etihad AUH routes against carrier publications.

Air Arabia destinations come from its 27 Dec 2024 network announcement;
IndiGo routes come from route-specific 2024 press releases. Presence in a
route-day extract does not identify a particular flight or operation date.
"""

from __future__ import annotations

import csv

import duckdb

from engine.config import SETTINGS


ROOT = SETTINGS.root
OUTPUT = ROOT / "research/real_world_validation/multicarrier_2024_coverage_matrix.csv"
AIR_ARABIA_SOURCE = "https://press.airarabia.com/air-arabia-abu-dhabi-takes-off-to-yekaterinburg/"
INDIGO_SOUTH = "https://www.goindigo.in/press-releases/indigo-brings-abu-dhabi-closer-to-southern-india.html"

# Destination in source, exact city label in challenge. The carrier's December
# source calls these popular destinations in its network; it does not give a
# date-by-date operating history for them.
AIR_ARABIA_CITIES = {
    "Ahmedabad": "Ahmedabad", "Alexandria": "Alexandria", "Almaty": "Almaty",
    "Amman": "Amman", "Baghdad": "Baghdad", "Bahrain": "Bahrain",
    "Baku": "Baku", "Beirut": "Beirut", "Cairo": "Cairo",
    "Chittagong": "Chittagong", "Chennai": "Chennai", "Colombo": "Colombo",
    "Dhaka": "Dhaka", "Faisalabad": "Faisalabad", "Kathmandu": "Kathmandu",
    "Kochi": "Kochi", "Kolkata": "Kolkata", "Kozhikode": "Kozhikode",
    "Kuwait": "Kuwait", "Moscow": "Moscow", "Multan": "Multan",
    "Muscat": "Muscat", "Salalah": "Salalah", "Sabiha": "Sabiha Gokcen",
    "Sohag": "Sohag", "Tashkent": "Tashkent", "Tbilisi": "Tbilisi",
    "Thiruvananthapuram": "Trivandrum", "Trabzon": "Trabzon",
}

# Published start is for the inbound service where the announcement states it.
INDIGO_ROUTES = [
    ("Kannur", "Kannur", "2024-05-09", "https://www.goindigo.in/press-releases/indigo-announces-direct-flights-between-abu-dhabi-and-kannur.html"),
    ("Chandigarh", "Chandigarh", "2024-05-16", "https://www.goindigo.in/press-releases/indigo-announces-daily-direct-flights-starting-from-chandigarh-rock-garden-to-the-skyscrapers-of-abu-dhabi.html"),
    ("Bengaluru", "Bengaluru", "2024-08-01", INDIGO_SOUTH),
    ("Mangaluru", "Mangalore", "2024-08-09", INDIGO_SOUTH),
    ("Coimbatore", "Coimbatore", "2024-08-10", INDIGO_SOUTH),
    ("Tiruchirappalli", "Tiruchchirappalli", "2024-08-11", INDIGO_SOUTH),
]


def main() -> None:
    con = duckdb.connect()
    source = str(SETTINGS.flight_daily_path)
    candidates = [
        ("Air Arabia Abu Dhabi", city, label, "2024-01-01", "network_list_2024_12_27", AIR_ARABIA_SOURCE)
        for city, label in AIR_ARABIA_CITIES.items()
    ]
    candidates += [
        ("IndiGo", city, label, start, "announced_inbound_start", url)
        for city, label, start, url in INDIGO_ROUTES
    ]
    rows = []
    for carrier, destination, label, start, evidence_type, url in candidates:
        count, first, last, pax = con.execute(
            """SELECT count(*), min(date), max(date), sum(total_pax)
               FROM read_parquet(?)
               WHERE airline_name = ? AND departure_city = ?
                 AND date BETWEEN ? AND '2024-12-31'""",
            [source, carrier, label, start],
        ).fetchone()
        rows.append({
            "carrier": carrier,
            "published_destination": destination,
            "challenge_city_label": label,
            "source_date_or_window_start": start,
            "source_evidence_type": evidence_type,
            "route_days_in_challenge": count,
            "first_challenge_date": first or "",
            "last_challenge_date": last or "",
            "challenge_total_pax": pax if pax is not None else "",
            "status": "present" if count else "absent_in_challenge",
            "carrier_source_url": url,
        })
    with OUTPUT.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for carrier in ("Air Arabia Abu Dhabi", "IndiGo"):
        subset = [r for r in rows if r["carrier"] == carrier]
        print(f"{carrier}: {len(subset)} checked, {sum(r['status'] == 'absent_in_challenge' for r in subset)} absent")


if __name__ == "__main__":
    main()
