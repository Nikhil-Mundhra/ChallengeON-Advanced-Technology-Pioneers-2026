"""Download and compare official SCAD 2024 hotel/transport tables with challenge data.

The SCAD URL list is pinned so the acquisition is reproducible. Source workbooks
remain untouched; only compact derived evidence is written next to them.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from statistics import correlation
from urllib.request import urlopen

import duckdb
import openpyxl

from tourism_twin.config import SETTINGS


ROOT = SETTINGS.root
OUT = ROOT / "meta" / "research" / "real_world_validation"
SOURCES = OUT / "sources"
BASE = "https://scad.gov.ae"
HOTEL_PATHS = {
    1: "/documents/20122/2313850/publication_43282_58_4_7_2024_EN.xlsx/1a54442d-47e2-13a0-9f98-a4f44e57adc3",
    2: "/documents/20122/2313850/publication_43331_58_4_8_2024_EN.xlsx/1f59c674-a395-6dad-eb7f-1bc0d9b164a5",
    3: "/documents/20122/2313850/publication_53349_58_4_9_2024_EN.xlsx/3a9c4815-6ad5-0a0e-1b55-3c54f596b719",
    4: "/documents/20122/2313850/publication_53385_58_4_10_2024_EN.xlsx/45d32d2f-ad60-0b78-b407-d03cf2dd5ecd",
    5: "/documents/20122/2313850/publication_53418_58_4_11_2024_EN.xlsx/0266c68e-e45d-8060-4f0b-062402192f18",
    6: "/documents/20122/2313850/publication_53472_58_4_12_2024_EN.xlsx/4175e25d-46eb-74c8-e8f8-11ce95ea59c8",
    7: "/documents/20122/2313850/publication_53490_58_4_13_2024_EN.xlsx/3f6a5866-4533-33ad-f350-354527845306",
    8: "/documents/20122/2313850/publication_53522_58_4_14_2024_EN.xlsx/dfe68169-ae92-9dbb-4bbd-b61e7e0193bd",
    9: "/documents/20122/2313850/publication_63565_58_4_15_2024_EN.xlsx/80feafa3-ce3a-c07c-abdc-b44d54d761ed",
    10: "/documents/20122/2313850/publication_63611_58_4_16_2024_EN.xlsx/36f3c304-6311-c903-2b32-56148f71d1b4",
    11: "/documents/20122/2313850/publication_63630_58_4_17_2024_EN.xlsx/d8b18483-d18c-9a62-b5f8-4a6d2d3e751d",
    12: "/documents/20122/2313850/publication_63661_58_4_18_2024_EN.xlsx/ace5c4e6-3d58-fb27-11e3-52d3fc8de4fd",
}
TRANSPORT_URL = BASE + "/documents/20122/2311280/publication_63732_344_1_1_2024_EN.xlsx/ed1047d7-c9a1-134b-be60-8a97c9bf9505"


def acquire(path: Path, url: str, download: bool) -> dict:
    if not path.exists():
        if not download:
            raise FileNotFoundError(f"Missing {path}; rerun with --download")
        with urlopen(url, timeout=40) as response:
            data = response.read(2_000_001)
        if len(data) > 2_000_000 or not data.startswith(b"PK"):
            raise ValueError(f"Unexpected SCAD workbook response from {url}")
        path.write_bytes(data)
    data = path.read_bytes()
    return {"file": str(path.relative_to(ROOT)), "url": url, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def hotel_month(path: Path, month: int) -> dict:
    book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    title = str(book["Index"]["D3"].value)
    expected = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][month - 1]
    if expected.lower() not in title.lower():
        raise ValueError(f"Wrong month in {path}: {title!r}")
    measures = {
        value.strip().lower(): float(row[i + 1])
        for row in book["Table 1"].values
        for i, value in enumerate(row[:-1])
        if isinstance(value, str)
        and value.strip().lower() in {"number of guests (thousand)", "number of guest nights (thousand night)", "number of guest nights (thousand nihgt)"}
    }
    total_thousands = measures["number of guests (thousand)"]
    nights_thousands = measures.get("number of guest nights (thousand night)", measures.get("number of guest nights (thousand nihgt)"))
    if nights_thousands is None:
        raise ValueError(f"Missing guest-nights measure in {path}")
    table4 = book["Table 4"]
    total_row = next(r for r in range(1, 20) if table4[f"B{r}"].value == "Total")
    groups = {str(table4[f"B{row}"].value).strip(): float(table4[f"C{row}"].value) for row in range(total_row + 1, total_row + 10)}
    group_gap = sum(groups.values()) - total_thousands
    if abs(group_gap) > 0.01:
        raise ValueError(f"Nationality groups fail to reconcile for {month}")
    return {"month": f"2024-{month:02d}", "scad_hotel_guests": round(total_thousands * 1000), "scad_guest_nights": round(nights_thousands * 1000), "scad_group_rounding_gap_guests": round(group_gap * 1000), "scad_groups": groups}


def challenge_months() -> tuple[dict[str, dict], dict[str, dict]]:
    con = duckdb.connect()
    guest = con.execute("""
        SELECT strftime(date, '%Y-%m') AS month,
               sum(new_arrivals) AS new_arrivals, sum(guests) AS guests
        FROM read_parquet(?)
        WHERE date BETWEEN '2024-01-01' AND '2024-12-31'
          AND dataset_split = 'train' AND target_available
        GROUP BY 1 ORDER BY 1
    """, [str(SETTINGS.guest_daily_path)]).fetchall()
    flight = con.execute("""
        SELECT strftime(date, '%Y-%m') AS month,
               sum(total_p2p) AS p2p, sum(total_pax) AS pax
        FROM read_parquet(?)
        WHERE date BETWEEN '2024-01-01' AND '2024-12-31'
        GROUP BY 1 ORDER BY 1
    """, [str(SETTINGS.flight_daily_path)]).fetchall()
    return ({m: {"challenge_new_arrivals": a, "challenge_guests": g} for m, a, g in guest},
            {m: {"challenge_p2p": p, "challenge_pax": x} for m, p, x in flight})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()
    SOURCES.mkdir(parents=True, exist_ok=True)
    manifest = []
    monthly = []
    guest, flight = challenge_months()
    for month, source_path in HOTEL_PATHS.items():
        path = SOURCES / f"scad_hotel_2024_{month:02d}.xlsx"
        if month == 12 and not path.exists() and (SOURCES / "scad_hotel_dec_2024.xlsx").exists():
            path = SOURCES / "scad_hotel_dec_2024.xlsx"
        manifest.append(acquire(path, BASE + source_path, args.download))
        row = hotel_month(path, month)
        row.update(guest[row["month"]])
        row.update(flight[row["month"]])
        monthly.append(row)
    transport = SOURCES / "scad_transport_2024.xlsx"
    manifest.append(acquire(transport, TRANSPORT_URL, args.download))
    book = openpyxl.load_workbook(transport, read_only=True, data_only=True)
    airport = book["Table 6"]
    airport_total = int(airport["F7"].value)
    airport_regions = {str(airport[f"B{r}"].value).strip(): int(airport[f"F{r}"].value) for r in range(8, 19)}
    if sum(airport_regions.values()) != airport_total:
        raise ValueError("SCAD airport arrival regions fail to reconcile")
    flat = [{k: v for k, v in row.items() if k != "scad_groups"} for row in monthly]
    with (OUT / "scad_2024_monthly_comparison.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(flat[0]))
        writer.writeheader()
        writer.writerows(flat)
    a = [r["scad_hotel_guests"] for r in monthly]
    b = [r["challenge_new_arrivals"] for r in monthly]
    p = [r["challenge_p2p"] for r in monthly]
    n = [r["scad_guest_nights"] for r in monthly]
    g = [r["challenge_guests"] for r in monthly]
    report = {
        "contract": {"scad_hotel_unit": "guests, monthly, all nationality groups, all establishment types in Abu Dhabi emirate", "scad_guest_nights_unit": "guest nights, monthly, all establishment types in Abu Dhabi emirate", "challenge_hotel_unit": "new arrivals and Guests, monthly sum of daily nationality rows", "challenge_flight_unit": "P2P passengers, monthly sum of inbound route-day rows", "scad_airport_unit": "arrivals via Zayed International Airport by region of embarkation, annual, excluding transit"},
        "monthly_source_urls_sha256": manifest,
        "scad_2024_hotel_guests": sum(a),
        "challenge_2024_new_arrivals": sum(b),
        "scad_2024_guest_nights": sum(n),
        "challenge_2024_guests": sum(g),
        "challenge_2024_p2p": sum(p),
        "scad_2024_airport_arrivals": airport_total,
        "scad_airport_regions": airport_regions,
        "pearson_scad_hotels_vs_challenge_new_arrivals": correlation(a, b),
        "pearson_scad_hotels_vs_challenge_p2p": correlation(a, p),
        "pearson_scad_guest_nights_vs_challenge_guests": correlation(n, g),
        "monthly": monthly,
    }
    (OUT / "scad_2024_validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in ("monthly_source_urls_sha256", "scad_airport_regions", "monthly")}, indent=2))


if __name__ == "__main__":
    main()
