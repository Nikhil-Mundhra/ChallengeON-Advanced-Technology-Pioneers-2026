"""Weekly country-market panel builder for ChallengeON DCT analytics lake.

Ensures strict daily alignment before weekly aggregation:
- Matches daily flight operations and daily hotel records by exact calendar date and market.
- Isolates split-boundary partial weeks so flight capacity is never duplicated.
- Provides flags for complete 7-day ISO weeks (Monday to Sunday).
- Uses defensible predictive response terminology (effective_response_multiplier).
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Optional

import duckdb
import numpy as np
import pandas as pd

from engine.archetypes import (
    TOP_15_INTERNATIONAL_MARKETS,
    get_market_archetype,
)

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT_DIR / "lake" / "analytics.duckdb"
OUTPUT_PANEL_PATH = ROOT_DIR / "lake" / "curated" / "weekly_market_panel.parquet"


HOLIDAY_WEEKS = {
    # Eid al-Fitr weeks (Monday week-start dates)
    "2023-04-17",
    "2024-04-08",
    "2025-03-31",
    # Eid al-Adha weeks
    "2023-06-26",
    "2024-06-17",
    "2025-06-02",
    # UAE National Day / Commemoration Day weeks
    "2023-11-27",
    "2024-12-02",
    "2025-12-01",
    # New Year / Festive peak weeks
    "2023-01-02",
    "2023-12-25",
    "2024-01-01",
    "2024-12-30",
    "2025-12-29",
}

MAJOR_EVENT_WEEKS = {
    # ADIPEC (Abu Dhabi International Petroleum Exhibition & Conference)
    "2023-10-02",
    "2024-11-04",
    "2025-11-03",
    # Formula 1 Etihad Airways Abu Dhabi Grand Prix (Yas Marina)
    "2023-11-20",
    "2024-12-02",
    "2025-12-01",
}


def assign_season(month: int) -> str:
    """Classify month into Abu Dhabi tourism climate seasons."""
    if month in (11, 12, 1, 2, 3):
        return "Winter_Peak"
    elif month in (4, 5):
        return "Spring_Shoulder"
    elif month in (6, 7, 8):
        return "Summer_Trough"
    else:
        return "Autumn_Shoulder"


def build_weekly_panel(db_path: Path = DEFAULT_DB_PATH) -> pd.DataFrame:
    """Build cleanly matched weekly panel from DuckDB.

    Filters to Jan 1, 2023 onward. Matches flight operations and guest records
    at the daily grain first to prevent flight total duplication across split boundaries.
    """
    con = duckdb.connect(str(db_path), read_only=True)
    top15_tuple = tuple(TOP_15_INTERNATIONAL_MARKETS)

    # 1. Join daily flights and daily guests at exact daily grain first
    matched_query = f"""
    WITH daily_f AS (
        SELECT 
            date,
            CASE 
                WHEN UPPER(departure_country_name) IN {top15_tuple} THEN UPPER(departure_country_name)
                ELSE 'OTHER INTERNATIONAL'
            END as market,
            SUM(total_seats) as seats,
            SUM(total_pax) as pax,
            SUM(total_p2p) as p2p,
            SUM(total_transfer) as transfer_pax,
            SUM(total_transit) as transit_pax,
            AVG(average_weekly_frequency) as avg_frequency
        FROM flight_daily
        WHERE date >= '2023-01-01'
        GROUP BY 1, 2
    ),
    daily_g AS (
        SELECT 
            date,
            dataset_split,
            residence_group,
            CASE 
                WHEN residence_group = 'Domestic' THEN 'DOMESTIC'
                WHEN UPPER(nationality) IN {top15_tuple} THEN UPPER(nationality)
                ELSE 'OTHER INTERNATIONAL'
            END as market,
            SUM(guests) as guests,
            SUM(new_arrivals) as new_arrivals,
            SUM(same_day_guests) as same_day_guests
        FROM guest_daily
        WHERE date >= '2023-01-01'
        GROUP BY 1, 2, 3, 4
    )
    SELECT 
        DATE_TRUNC('week', g.date) as week_start,
        g.dataset_split,
        g.market,
        COUNT(DISTINCT g.date) as days_in_week,
        MIN(g.date) as min_date,
        MAX(g.date) as max_date,
        EXTRACT(month FROM MIN(g.date)) as representative_month,
        SUM(COALESCE(f.seats, 0.0)) as seats,
        SUM(COALESCE(f.pax, 0.0)) as pax,
        SUM(COALESCE(f.p2p, 0.0)) as p2p,
        SUM(COALESCE(f.transfer_pax, 0.0)) as transfer_pax,
        SUM(COALESCE(f.transit_pax, 0.0)) as transit_pax,
        AVG(f.avg_frequency) as avg_frequency,
        SUM(g.guests) as guests,
        SUM(g.new_arrivals) as new_arrivals,
        SUM(g.same_day_guests) as same_day_guests
    FROM daily_g g
    LEFT JOIN daily_f f ON g.date = f.date AND g.market = f.market
    GROUP BY 1, 2, 3
    ORDER BY 1, 3, 2
    """
    panel = con.execute(matched_query).df()
    con.close()

    panel["week_start"] = pd.to_datetime(panel["week_start"]).dt.date
    panel["min_date"] = pd.to_datetime(panel["min_date"]).dt.date
    panel["max_date"] = pd.to_datetime(panel["max_date"]).dt.date

    # Flag strictly complete 7-day ISO weeks
    panel["is_complete_week"] = (panel["days_in_week"] == 7).astype(int)

    # Computed operational ratios
    panel["load_factor"] = np.where(
        panel["seats"] > 0,
        np.clip(panel["pax"] / panel["seats"], 0.0, 1.0),
        np.nan,
    )
    panel["p2p_share"] = np.where(
        panel["pax"] > 0,
        np.clip(panel["p2p"] / panel["pax"], 0.0, 1.0),
        np.nan,
    )
    panel["implied_los"] = np.where(
        (panel["new_arrivals"] > 0) & panel["guests"].notnull(),
        panel["guests"] / panel["new_arrivals"],
        np.nan,
    )
    # Effective response multiplier: macro predictive translation from P2P arrivals to hotel arrivals
    panel["effective_response_multiplier"] = np.where(
        panel["p2p"] > 0,
        panel["new_arrivals"] / panel["p2p"],
        np.nan,
    )

    # Calendar enrichment
    week_start_dt = pd.to_datetime(panel["week_start"])
    panel["year"] = week_start_dt.dt.year
    panel["quarter"] = week_start_dt.dt.quarter
    panel["month"] = panel["representative_month"].astype(int)
    panel["iso_week"] = week_start_dt.dt.isocalendar().week.astype(int)

    panel["season"] = panel["month"].apply(assign_season)
    panel["is_winter_peak"] = (panel["season"] == "Winter_Peak").astype(int)
    panel["is_summer_trough"] = (panel["season"] == "Summer_Trough").astype(int)

    week_str = panel["week_start"].astype(str)
    panel["is_holiday_week"] = week_str.isin(HOLIDAY_WEEKS).astype(int)
    panel["is_major_event_week"] = week_str.isin(MAJOR_EVENT_WEEKS).astype(int)

    # Market Archetype tagging
    panel["archetype"] = panel["market"].apply(lambda m: get_market_archetype(m).value)
    panel["is_domestic"] = (panel["market"] == "DOMESTIC").astype(int)

    panel = panel.sort_values(["week_start", "market", "dataset_split"]).reset_index(drop=True)
    return panel


def save_weekly_panel(
    output_path: Path = OUTPUT_PANEL_PATH,
    db_path: Path = DEFAULT_DB_PATH,
) -> Path:
    """Build and save weekly panel to Parquet."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = build_weekly_panel(db_path=db_path)
    df.to_parquet(output_path, index=False)
    return output_path
