"""The competition submission: nationality predictions floored to what a published row allows,
joined onto the test workbooks row for row, the intervals file, and the checks a usable
submission must pass."""

from __future__ import annotations

import numpy as np
import pandas as pd

from tourism_twin.data.daily_panel import PUBLICATION_MIN
from tourism_twin.data.ingest import read_raw_workbook

DOMESTIC_TEST_FILE = "data domestic_test.xlsx"
INTERNATIONAL_TEST_FILE = "data international_test.xlsx"
INTERVAL_COLUMNS = ["Date", "Nationality", "Residence (groups)", "Guests_p10", "Guests_p50", "Guests_p90"]


def guest_floor(new_arrivals: pd.Series) -> pd.Series:
    """Lowest admissible Guests for a published row: its New Arrivals, and at least PUBLICATION_MIN
    (every training row has Guests >= New Arrivals and Guests >= 10)."""
    return np.maximum(pd.to_numeric(new_arrivals, errors="coerce").fillna(PUBLICATION_MIN), PUBLICATION_MIN)


def apply_guest_floor(rows: pd.DataFrame) -> pd.DataFrame:
    """Floor pred and its bounds at guest_floor, keeping lower <= pred <= upper."""
    floor = guest_floor(rows["new_arrivals"])
    pred = np.maximum(rows["pred"], floor)
    return rows.assign(pred=pred, lower=np.maximum(rows["lower"], floor), upper=np.maximum(rows["upper"], pred))


def build_submission(rows: pd.DataFrame, with_intervals: bool) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """(domestic, international, intervals): the test workbooks with Guests, and P10/P50/P90 rows
    (international first, then domestic; empty without intervals)."""
    domestic = _attach(read_raw_workbook(DOMESTIC_TEST_FILE), rows[rows["residence_group"] == "Domestic"], ["Date"])
    international = _attach(read_raw_workbook(INTERNATIONAL_TEST_FILE), rows[rows["residence_group"] == "International"], ["Date", "Nationality"])
    intervals = pd.concat([
        international[["Date", "Nationality", "Residence (groups)"]].assign(
            Guests_p10=international["_lower"], Guests_p50=international["Guests"], Guests_p90=international["_upper"]),
        domestic[["Date", "Residence (groups)"]].assign(
            Nationality=pd.NA, Guests_p10=domestic["_lower"], Guests_p50=domestic["Guests"], Guests_p90=domestic["_upper"]),
    ], ignore_index=True)[INTERVAL_COLUMNS]
    if not with_intervals:
        intervals = intervals.iloc[0:0]
    return domestic.drop(columns=["_lower", "_upper"]), international.drop(columns=["_lower", "_upper"]), intervals


def _attach(raw: pd.DataFrame, rows: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """The raw test workbook with Guests (and interval bounds) joined on its own keys, in its order."""
    values = rows.rename(columns={"date": "Date", "nationality": "Nationality"})[[*keys, "pred", "lower", "upper"]]
    out = raw.merge(values, on=keys, how="left", validate="one_to_one")
    return out.rename(columns={"pred": "Guests", "lower": "_lower", "upper": "_upper"})


def validate_predictions(predictions) -> list[str]:
    """Problems that would make a submission invalid (TestPredictions or any object with domestic,
    international and intervals frames); empty when the outputs are usable."""
    problems = []
    keys_by_part = []
    for name, frame, filename in (("domestic", predictions.domestic, DOMESTIC_TEST_FILE),
                                  ("international", predictions.international, INTERNATIONAL_TEST_FILE)):
        raw = read_raw_workbook(filename)
        if list(frame.columns) != [*raw.columns, "Guests"] or not frame.drop(columns="Guests").reset_index(drop=True).equals(raw):
            problems.append(f"{name}: columns or source values differ from {filename}")
        guests = frame["Guests"].to_numpy(dtype=float)
        if not np.isfinite(guests).all():
            problems.append(f"{name}: {int((~np.isfinite(guests)).sum())} missing or infinite Guests")
        below = guests < guest_floor(frame["New Arrivals"]).to_numpy(dtype=float)
        if below.any():
            problems.append(f"{name}: {int(below.sum())} Guests below max(New Arrivals, {PUBLICATION_MIN})")
        keys_by_part.append(raw.reindex(columns=["Date", "Nationality"]))
    intervals = predictions.intervals
    if len(intervals):
        expected = pd.concat(keys_by_part[::-1], ignore_index=True)
        if not intervals[["Date", "Nationality"]].reset_index(drop=True).equals(expected):
            problems.append("intervals: rows or keys differ from the test workbooks")
        bounds = intervals[["Guests_p10", "Guests_p50", "Guests_p90"]].to_numpy(dtype=float)
        ordered = np.isfinite(bounds).all(axis=1) & (bounds[:, 0] <= bounds[:, 1]) & (bounds[:, 1] <= bounds[:, 2])
        if not ordered.all():
            problems.append(f"intervals: {int((~ordered).sum())} rows not finite with p10 <= p50 <= p90")
    return problems
