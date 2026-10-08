"""Weekly country-market panel builder for ChallengeON DCT analytics lake.

Ensures strict daily alignment before weekly aggregation:
- Matches daily flight operations and daily hotel records by exact calendar date and market.
- Isolates split-boundary partial weeks so flight capacity is never duplicated.
- Provides flags for complete 7-day ISO weeks (Monday to Sunday).
- Uses defensible predictive response terminology (effective_response_multiplier).
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from tourism_twin.config import SETTINGS
from tourism_twin.domain.archetypes import get_market_archetype
from tourism_twin.domain.events import HOLIDAY_WEEKS, MAJOR_EVENT_WEEKS
from tourism_twin.domain.markets import REGIONAL_CLUSTERS, TOP_15_INTERNATIONAL_MARKETS
from tourism_twin.domain.seasons import assign_season

# Last complete Monday-Sunday week of the train split; models are calibrated up to here.
TRAINING_CUTOFF = "2025-07-27"


def training_window(panel: pd.DataFrame, max_date: str = TRAINING_CUTOFF) -> pd.DataFrame:
    """Complete train-split weeks with complete guest inputs, up to and including max_date."""
    return panel[
        (panel["dataset_split"] == "train") &
        (panel["is_complete_week"] == 1) &
        (panel["is_complete_guest_inputs"] == 1) &
        (panel["week_start"] <= pd.to_datetime(max_date).date())
    ].copy()


def _build_market_case(top15_tuple: tuple) -> str:
    """Build a SQL CASE expression mapping departure country / nationality to market label.

    Priority:
    1. Top-15 individual markets — named directly.
    2. Regional cluster members — mapped to their cluster label (e.g. 'OTHER_EUROPE').
    3. Remaining nationalities — catch-all 'OTHER_INTERNATIONAL'.

    FIX (P0-D): The previous single 'OTHER INTERNATIONAL' bucket pooled 30 nationalities
    with 18 flight corridors into one blended multiplier, creating spurious aviation
    elasticity (e.g. Turkish capacity changes inflating Australian/Brazilian forecasts).
    The 5 regional clusters preserve intra-regional coherence.
    """
    lines = [f"        WHEN UPPER({{col}}) IN {top15_tuple} THEN UPPER({{col}})"]
    for cluster_name, members in REGIONAL_CLUSTERS.items():
        members_tuple = tuple(m.upper() for m in members)
        lines.append(f"        WHEN UPPER({{col}}) IN {members_tuple} THEN '{cluster_name}'")
    lines.append("        ELSE 'OTHER_INTERNATIONAL'")
    return "\n".join(lines)


def build_weekly_panel(db_path: Path = SETTINGS.database_path) -> pd.DataFrame:
    """Build cleanly matched weekly panel from DuckDB.

    Filters to Jan 1, 2023 onward. Matches flight operations and guest records
    at the daily grain first to prevent flight total duplication across split boundaries.
    Propagates grid completeness, unclipped raw load factors, and quality flags.
    """
    con = duckdb.connect(str(db_path), read_only=True)
    top15_tuple = tuple(TOP_15_INTERNATIONAL_MARKETS)

    # Build parameterised CASE expressions for flight departure country and guest nationality
    flight_market_case = _build_market_case(top15_tuple).format(col="departure_country_name")
    guest_market_case = _build_market_case(top15_tuple).format(col="nationality")

    # 1. Aggregate daily flights and daily guests at exact daily grain first
    matched_query = f"""
    WITH daily_f AS (
        SELECT 
            date,
            CASE 
{flight_market_case}
            END as market,
            SUM(total_seats) as seats,
            SUM(total_pax) as pax,
            SUM(total_p2p) as p2p,
            SUM(total_transfer) as transfer_pax,
            SUM(total_transit) as transit_pax,
            COUNT(*) as flight_services_count,
            SUM(CASE WHEN is_load_factor_outlier THEN 1 ELSE 0 END) as flight_load_factor_outliers
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
{guest_market_case}
            END as market,
            SUM(guests) as guests,
            SUM(new_arrivals) as new_arrivals,
            SUM(same_day_guests) as same_day_guests,
            COUNT(*) as total_grid_records,
            SUM(CASE WHEN is_source_present THEN 1 ELSE 0 END) as present_source_records,
            SUM(CASE WHEN is_suppressed_arrival THEN 1 ELSE 0 END) as missing_arrival_records
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
        EXTRACT(month FROM DATE_TRUNC('week', g.date)) as representative_month,
        SUM(COALESCE(f.seats, 0.0)) as seats,
        SUM(COALESCE(f.pax, 0.0)) as pax,
        SUM(COALESCE(f.p2p, 0.0)) as p2p,
        SUM(COALESCE(f.transfer_pax, 0.0)) as transfer_pax,
        SUM(COALESCE(f.transit_pax, 0.0)) as transit_pax,
        SUM(COALESCE(f.flight_services_count, 0)) as weekly_flight_services,
        SUM(COALESCE(f.flight_load_factor_outliers, 0)) as weekly_load_factor_outliers,
        SUM(g.guests) as guests,
        SUM(g.new_arrivals) as new_arrivals,
        SUM(g.same_day_guests) as same_day_guests,
        SUM(g.total_grid_records) as total_grid_records,
        SUM(g.present_source_records) as present_source_records,
        SUM(g.missing_arrival_records) as missing_arrival_records
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

    # Completeness verification
    panel["is_complete_week"] = (panel["days_in_week"] == 7).astype(int)
    panel["is_complete_guest_inputs"] = (
        (panel["present_source_records"] == panel["total_grid_records"])
        & (panel["missing_arrival_records"] == 0)
    ).astype(int)

    # Computed operational ratios: preserve unclipped raw load factor alongside bounded version
    panel["load_factor_raw"] = np.where(
        panel["seats"] > 0,
        panel["pax"] / panel["seats"],
        np.nan,
    )
    panel["is_load_factor_outlier"] = (panel["load_factor_raw"] > 1.0).astype(int)
    panel["load_factor"] = np.clip(panel["load_factor_raw"], 0.0, 1.0)

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
    output_path: Path = SETTINGS.panel_path,
    db_path: Path = SETTINGS.database_path,
) -> Path:
    """Build and save weekly panel to Parquet."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = build_weekly_panel(db_path=db_path)
    df.to_parquet(output_path, index=False)
    return output_path
