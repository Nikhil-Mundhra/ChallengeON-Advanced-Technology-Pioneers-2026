"""Nationality grouping evidence and proposal (issue #2).

Groups nationalities so small markets can borrow strength from similar ones
(partial pooling in nowcast/pooling.py, plus the nationality profiles). The
candidate split is a short-stay family (GCC + domestic) vs long-haul; this
script measures the discriminators and writes the proposed table.

Discriminators (all computed on the train split only):
  guest_nights_per_arrival   sum(guests) / sum(new_arrivals) — turnover
                             intensity; NOT a stay-length estimate
  thu_fri_arrival_pct        share of arrivals landing Thu/Fri — the GCC
                             weekend-trip signature
  same_day_guest_pct         same-day guests / guests (heavy suppression;
                             reported with its missing share, not imputed)

Outputs in meta/research/nationality_groups/:
  nationality_group_evidence.csv  all measured discriminators
  nationality_group_table.csv     nationality -> group proposal with basis
"""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

from tourism_twin.config import SETTINGS

ROOT = SETTINGS.root
OUT_DIR = ROOT / "meta" / "research" / "nationality_groups"

EVIDENCE_QUERY = """
SELECT
    COALESCE(nationality, 'DOMESTIC') AS nationality,
    residence_group,
    SUM(guests) AS guests,
    SUM(new_arrivals) AS arrivals,
    ROUND(SUM(guests) / NULLIF(SUM(new_arrivals), 0), 2)
        AS guest_nights_per_arrival,
    ROUND(100.0 * SUM(CASE WHEN EXTRACT(dow FROM date) IN (4, 5)
                           THEN new_arrivals END)
          / NULLIF(SUM(new_arrivals), 0), 1) AS thu_fri_arrival_pct,
    ROUND(100.0 * SUM(same_day_guests) / NULLIF(SUM(guests), 0), 1)
        AS same_day_guest_pct,
    ROUND(100.0 * SUM(CASE WHEN same_day_guests IS NULL THEN 1 ELSE 0 END)
          / COUNT(*), 0) AS same_day_missing_pct
FROM guest_daily
WHERE dataset_split = 'train' AND guests IS NOT NULL
GROUP BY ALL
ORDER BY guest_nights_per_arrival
"""

# GCC five: bottom of the turnover continuum AND the only block with a
# materially elevated Thu/Fri arrival share (>= ~31%). China sits low on the
# turnover measure but has a flat weekday profile, so it is flagged as a
# candidate rather than grouped on the ratio alone.
SHORT_STAY = {"OMAN", "QATAR", "SAUDI ARABIA", "BAHRAIN", "KUWAIT", "DOMESTIC"}
BORDERLINE_NOTE = {
    "BAHRAIN": "kept: GCC + Thu/Fri 32.6%; ratio overlaps the 2.8-3.3 band",
    "KUWAIT": "kept: GCC + Thu/Fri 31.4%; ratio overlaps the 2.8-3.3 band",
    "CHINA": "candidate, not grouped: low turnover but flat weekday profile "
             "(Thu/Fri 28.1%); needs the kernel-shape test before moving",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db", type=Path, default=SETTINGS.root / "lake" / "analytics.duckdb",
        help="DuckDB lake path",
    )
    args = parser.parse_args()
    con = duckdb.connect(str(args.db), read_only=True)

    evidence = con.execute(EVIDENCE_QUERY).df()

    table = evidence.assign(
        group=lambda d: d["nationality"].isin(SHORT_STAY).map({True: "short", False: "long"}),
        basis=lambda d: [
            ("domestic" if n == "DOMESTIC" else "gcc_weekend_signature")
            if g == "short" else "long_haul_default"
            for n, g in zip(d["nationality"], d["group"])
        ],
        note=lambda d: d["nationality"].map(BORDERLINE_NOTE).fillna(""),
    )[["nationality", "group", "basis", "note"]]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    evidence.to_csv(OUT_DIR / "nationality_group_evidence.csv", index=False)
    table.to_csv(OUT_DIR / "nationality_group_table.csv", index=False)
    print(f"wrote {OUT_DIR}/nationality_group_evidence.csv ({len(evidence)} rows)")
    print(f"wrote {OUT_DIR}/nationality_group_table.csv ({len(table)} rows)")
    print(table.groupby("group").size())


if __name__ == "__main__":
    main()
