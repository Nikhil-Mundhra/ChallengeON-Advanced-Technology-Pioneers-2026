"""Summarize 2024 Statistics Canada air-exit survey air-route and hotel use.

Source: Statistics Canada Visitor Travel Survey, 2024 Air Exit Survey PUMF.
The same survey record contains route of entry (VRTEN), province of entry
(VGPRVENP), and hotel use at up to ten visit locations (VACCVxxA).
"""

from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "meta" / "research" / "real_world_validation"
ZIP = OUT / "sources" / "statcan_vts_2024_air_exit_csv.zip"
URL = "https://www150.statcan.gc.ca/n1/pub/24-25-0002/2021001/2024/CSV.zip"
CSV_PATH = "CSV/Data_Données/aes_2024_pumf.csv"
ROUTES = {"1": "From United States only", "2": "Directly from non-US country", "3": "From non-US country via United States"}
PROVINCES = {"12": "Nova Scotia", "19": "Newfoundland, PEI and New Brunswick", "24": "Quebec", "35": "Ontario", "46": "Manitoba", "47": "Saskatchewan", "48": "Alberta", "59": "British Columbia and territories"}


def summarize(frame: pd.DataFrame, group_col: str, labels: dict[str, str]) -> list[dict]:
    result = []
    for code, subset in frame.groupby(group_col, sort=True):
        weighted = subset["weight"].sum()
        hotel_weighted = subset.loc[subset["hotel_any"], "weight"].sum()
        result.append({"dimension": group_col, "code": code, "label": labels.get(code, code), "sample_records": len(subset), "weighted_air_visitors": round(weighted), "weighted_hotel_users": round(hotel_weighted), "hotel_use_share": round(hotel_weighted / weighted, 4)})
    return result


def main() -> None:
    if not ZIP.exists():
        raise FileNotFoundError(f"Download {URL} to {ZIP}")
    hotel_cols = [f"VACCV{i:02d}A" for i in range(1, 11)]
    cols = ["VRTEN", "VGPRVENP", "VWEIGHTP", *hotel_cols]
    with zipfile.ZipFile(ZIP).open(CSV_PATH) as source:
        data = pd.read_csv(source, usecols=cols, dtype=str)
    if data["VRTEN"].isin(ROUTES).sum() != len(data):
        raise ValueError("Unexpected route-of-entry codes")
    data["weight"] = pd.to_numeric(data["VWEIGHTP"], errors="raise")
    if data["weight"].isna().any() or (data["weight"] <= 0).any():
        raise ValueError("Missing or nonpositive survey weights")
    answers = data[hotel_cols]
    data["hotel_any"] = answers.eq("1").any(axis=1)
    data["hotel_answered"] = answers.isin(["1", "2"]).any(axis=1)
    valid = data.loc[data["hotel_answered"]]
    rows = summarize(valid, "VRTEN", ROUTES) + summarize(valid, "VGPRVENP", PROVINCES)
    path = OUT / "statcan_2024_air_hotel_summary.csv"
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    metadata = {"source_url": URL, "source_sha256": hashlib.sha256(ZIP.read_bytes()).hexdigest(), "source_zip_bytes": ZIP.stat().st_size, "sample_records": len(data), "hotel_answered_records": len(valid), "weighted_air_visitors": round(data["weight"].sum()), "weighted_answered_visitors": round(valid["weight"].sum()), "weighted_hotel_user_share": round(valid.loc[valid["hotel_any"], "weight"].sum() / valid["weight"].sum(), 4), "fields": {"VRTEN": "route of entry into Canada, not flight number", "VGPRVENP": "Canadian province or region of entry", "VACCVxxA": "hotel used at visit location xx; 1=yes, 2=no", "VWEIGHTP": "survey weight"}, "limitation": "Canada air arrivals, not Abu Dhabi; survey record connects broad air-entry route and accommodation use, but does not identify a flight or hotel booking."}
    (OUT / "statcan_2024_air_hotel_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))
    print(path)


if __name__ == "__main__":
    main()
