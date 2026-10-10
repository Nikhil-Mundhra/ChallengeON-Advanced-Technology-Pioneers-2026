"""Premium-cabin share of Etihad P2P arrivals by departure origin (issue #4).

Descriptive flight analysis. Question: among Etihad's recorded P2P
(point-to-point) passengers arriving from each departure country, what share
travelled in business or first class, and how does that share vary over time?

Population: airline = 'Etihad Airways', daily-grain rows from 2023 onward.
2022 monthly rows carry no cabin detail; other carriers are excluded so
airline mix does not confound the comparison. Etihad-only does not remove
differences in aircraft, routes, season, or passenger purpose.

All shares are ratios of summed counts, never averages of daily percentages:
each passenger gets equal weight, not each day.

Outputs (meta/research/premium_share_by_origin/):
  premium_share_country.csv         origin x reporting period
  premium_share_country_monthly.csv origin x month
  premium_share_city.csv            origin x departure city, main period

Reporting periods: the MAIN period is 2023-01-01 to 2025-07-31, aligned with
the team's guest-training history; the EXTENDED period runs to 2026-02-28 and
is labelled separately. Jan-Feb slices let 2026 be compared like-for-like
with earlier years instead of against entire years.

Columns and definitions are documented in the folder README. In particular:
  premium_p2p_share_pct           premium P2P / total P2P (primary measure)
  premium_classified_share_pct    premium P2P / cabin-classified P2P
                                  (sensitivity: classified cabin totals do
                                  not exceed total_p2p in these aggregates;
                                  per-origin gap 0-2.08%, unexplained and
                                  NOT assumed to be economy/infants)
  unclassified_p2p_pct            1 - classified P2P / total P2P
  transfer_share_pct              total transfer / total PAX (a separate
                                  descriptor; transfer status does not
                                  establish whether the passenger entered
                                  Abu Dhabi or stayed overnight)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

from tourism_twin.config import SETTINGS

ROOT = SETTINGS.root
OUT_DIR = ROOT / "meta" / "research" / "premium_share_by_origin"
MAIN_END = "2025-07-31"

ETIHAD_DAILY = f"""
SELECT
    date,
    departure_country_name AS origin,
    departure_city,
    total_pax, total_p2p, total_transfer, total_transit,
    COALESCE(business_class_p2p_count, 0)
        + COALESCE(first_class_p2p_count, 0) AS premium_p2p,
    COALESCE(business_class_p2p_count, 0) + COALESCE(economy_class_p2p_count, 0)
        + COALESCE(first_class_p2p_count, 0) AS classified_p2p,
    COALESCE(business_class_seat_capacity, 0)
        + COALESCE(first_class_seat_capacity, 0) AS premium_seats,
    total_seats
FROM flight_daily
WHERE airline_name = 'Etihad Airways'
  AND source_grain = 'daily'
  AND total_pax > 0
"""

METRICS = """
    COUNT(*) AS n_route_days,
    COUNT(DISTINCT departure_city) AS n_cities,
    SUM(total_pax) AS total_pax,
    SUM(total_p2p) AS p2p_pax,
    SUM(total_transfer) AS transfer_pax,
    SUM(total_transit) AS transit_pax,
    SUM(premium_p2p) AS premium_p2p_pax,
    SUM(classified_p2p) AS classified_p2p_pax,
    ROUND(100.0 * SUM(premium_p2p) / NULLIF(SUM(total_p2p), 0), 1)
        AS premium_p2p_share_pct,
    ROUND(100.0 * SUM(premium_p2p) / NULLIF(SUM(classified_p2p), 0), 1)
        AS premium_classified_share_pct,
    ROUND(100.0 * (SUM(total_p2p) - SUM(classified_p2p))
          / NULLIF(SUM(total_p2p), 0), 2) AS unclassified_p2p_pct,
    ROUND(100.0 * SUM(premium_seats) / NULLIF(SUM(total_seats), 0), 1)
        AS premium_seat_share_pct,
    ROUND(100.0 * SUM(total_transfer) / NULLIF(SUM(total_pax), 0), 1)
        AS transfer_share_pct,
    MIN(date) AS first_date,
    MAX(date) AS last_date
"""

PERIODS = [
    ("main_2023-01_to_2025-07", f"date <= DATE '{MAIN_END}'"),
    ("extended_2023-01_to_2026-02", "TRUE"),
    ("2023", "YEAR(date) = 2023"),
    ("2024", "YEAR(date) = 2024"),
    ("2025", "YEAR(date) = 2025"),
    ("jan-feb_2023", "YEAR(date) = 2023 AND MONTH(date) <= 2"),
    ("jan-feb_2024", "YEAR(date) = 2024 AND MONTH(date) <= 2"),
    ("jan-feb_2025", "YEAR(date) = 2025 AND MONTH(date) <= 2"),
    ("jan-feb_2026", "YEAR(date) = 2026 AND MONTH(date) <= 2"),
]


def country_periods(con: duckdb.DuckDBPyConnection):
    parts = [
        f"SELECT '{label}' AS reporting_period, origin AS departure_origin, {METRICS} "
        f"FROM etihad WHERE {cond} GROUP BY origin"
        for label, cond in PERIODS
    ]
    order = {label: i for i, (label, _) in enumerate(PERIODS)}
    df = con.execute(" UNION ALL ".join(parts)).df()
    df["_o"] = df.reporting_period.map(order)
    return df.sort_values(["departure_origin", "_o"]).drop(columns="_o").reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db", type=Path, default=SETTINGS.root / "lake" / "analytics.duckdb",
        help="DuckDB lake path",
    )
    args = parser.parse_args()
    con = duckdb.connect(str(args.db), read_only=True)
    con.execute(f"CREATE TEMP VIEW etihad AS {ETIHAD_DAILY}")

    country = country_periods(con)
    monthly = con.execute(f"""
        SELECT origin AS departure_origin,
               STRFTIME(DATE_TRUNC('month', date), '%Y-%m') AS month,
               {METRICS}
        FROM etihad GROUP BY origin, DATE_TRUNC('month', date)
        ORDER BY departure_origin, month
    """).df()
    city = con.execute(f"""
        SELECT origin AS departure_origin, departure_city, {METRICS}
        FROM etihad WHERE date <= DATE '{MAIN_END}'
        GROUP BY origin, departure_city
        ORDER BY departure_origin, p2p_pax DESC
    """).df()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, df in [
        ("premium_share_country.csv", country),
        ("premium_share_country_monthly.csv", monthly),
        ("premium_share_city.csv", city),
    ]:
        df.to_csv(OUT_DIR / name, index=False)
        print(f"wrote {OUT_DIR / name} ({len(df)} rows)")


if __name__ == "__main__":
    main()
