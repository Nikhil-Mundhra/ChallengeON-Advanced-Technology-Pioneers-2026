"""Read the raw competition workbooks into typed, grain-explicit DataFrames."""

from __future__ import annotations

import numpy as np
import pandas as pd

from tourism_twin.config import SETTINGS

FLIGHT_FILE = "flight_data.xlsx"
DATA_DICTIONARY_FILE = "Data_Dictionary.pdf"


GUEST_FILES = (
    ("data domestic_train.xlsx", "train", "Domestic"),
    ("data domestic_test.xlsx", "test", "Domestic"),
    ("data international_train.xlsx", "train", "International"),
    ("data international_test.xlsx", "test", "International"),
)


COUNT_COLUMNS = (
    "business_class_p2p_count",
    "business_class_seat_capacity",
    "economy_class_p2p_count",
    "economy_class_seat_capacity",
    "first_class_p2p_count",
    "first_class_seat_capacity",
    "total_p2p",
    "total_pax",
    "total_pax_excluding_infant",
    "total_seats",
    "total_transfer",
    "total_transit",
    "transfer_business_class_count",
    "transfer_economy_class_count",
    "transfer_first_class_count",
    "transit_business_class_count",
    "transit_economy_class_count",
    "transit_first_count",
)


def snake_case(name: str) -> str:
    return (
        name.strip()
        .lower()
        .replace("-", "_")
        .replace("(", "")
        .replace(")", "")
        .replace(" ", "_")
    )


def read_guest_file(filename: str, split: str, residence_group: str) -> pd.DataFrame:
    path = SETTINGS.source_dir / filename
    frame = pd.read_excel(path, sheet_name="Export")
    frame.columns = [snake_case(str(column)) for column in frame.columns]

    if "guests" not in frame:
        frame["guests"] = pd.NA
    if "nationality" not in frame:
        frame["nationality"] = pd.NA

    guests_s = pd.to_numeric(frame["guests"], errors="coerce").astype("Int64")
    arrivals_s = pd.to_numeric(frame["new_arrivals"], errors="coerce").astype("Int64")
    same_day_s = pd.to_numeric(frame["same_day_guests"], errors="coerce").astype("Int64")

    output = pd.DataFrame(
        {
            "date": pd.to_datetime(frame["date"], errors="raise"),
            "residence_group": residence_group,
            "nationality": frame["nationality"].astype("string"),
            "guests": guests_s,
            "new_arrivals": arrivals_s,
            "same_day_guests": same_day_s,
            "dataset_split": split,
            "source_file": filename,
            "source_grain": "daily",
            "is_source_present": True,
            "target_available": guests_s.notna(),
            "is_suppressed_arrival": arrivals_s.isna(),
            "is_suppressed_same_day": same_day_s.isna(),
        }
    )
    return output


def build_guest_frame() -> pd.DataFrame:
    frames = [read_guest_file(*file_spec) for file_spec in GUEST_FILES]
    raw_df = pd.concat(frames, ignore_index=True)

    # Separate domestic (complete continuous series) and international
    dom_df = raw_df[raw_df["residence_group"] == "Domestic"].copy()
    intl_df = raw_df[raw_df["residence_group"] == "International"].copy()

    # Complete Date x Nationality grid for International to prevent silent omission
    all_intl_dates = intl_df["date"].drop_duplicates().sort_values()
    all_intl_nats = intl_df["nationality"].dropna().drop_duplicates().sort_values()

    grid = pd.MultiIndex.from_product(
        [all_intl_dates, all_intl_nats], names=["date", "nationality"]
    ).to_frame().reset_index(drop=True)

    merged_intl = pd.merge(grid, intl_df, on=["date", "nationality"], how="left")

    # Flag absent reporting rows explicitly rather than silently dropping or assuming zero
    absent_mask = merged_intl["is_source_present"].isna()
    merged_intl.loc[absent_mask, "residence_group"] = "International"
    merged_intl.loc[absent_mask, "is_source_present"] = False
    merged_intl.loc[absent_mask, "source_grain"] = "daily"
    merged_intl.loc[absent_mask, "source_file"] = "ABSENT_GRID_RECORD"
    merged_intl.loc[absent_mask, "target_available"] = False
    merged_intl.loc[absent_mask, "is_suppressed_arrival"] = True
    merged_intl.loc[absent_mask, "is_suppressed_same_day"] = True
    merged_intl.loc[absent_mask, "dataset_split"] = np.where(
        merged_intl.loc[absent_mask, "date"] <= pd.to_datetime("2025-07-31"), "train", "test"
    )

    combined = pd.concat([dom_df, merged_intl], ignore_index=True).sort_values(
        ["date", "residence_group", "nationality"], na_position="first"
    )
    return combined


def build_flight_frame() -> pd.DataFrame:
    filename = FLIGHT_FILE
    frame = pd.read_excel(SETTINGS.source_dir / filename, sheet_name="Export")
    frame.columns = [snake_case(str(column)) for column in frame.columns]
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    for column in COUNT_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").astype("Int64")
    frame["average_weekly_frequency"] = pd.to_numeric(
        frame["average_weekly_frequency"], errors="coerce"
    )
    frame["load_factor"] = pd.to_numeric(frame["load_factor"], errors="raise")
    frame["source_file"] = filename
    # Explicit grain contract: 2022 is monthly aggregated; 2023+ is true daily
    frame["source_grain"] = np.where(frame["date"].dt.year == 2022, "monthly", "daily")
    # Quality flag for unclipped load factor > 100%
    frame["is_load_factor_outlier"] = frame["load_factor"] > 1.0
    return frame.sort_values(
        ["date", "departure_country_name", "departure_city", "airline_name"]
    )
