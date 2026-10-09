"""Competition predictions for the test split (2025-08-01 to 2026-02-28).

The chosen daily spec is fitted on every training day and predicts each test (market, date).
Markets that pool several nationalities are split by each nationality's share of the market's
new arrivals that day (new_arrivals_filled; shares are taken over all nationality-days, including
those absent from the test file, because the market model's arrivals include them). Prediction
intervals come from a NoiseModel fitted on the spec's rolling-origin back-test; the horizon is
counted from the first test day. Outputs mirror the test workbooks row for row with a Guests column.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from tourism_twin.data.daily_panel import build_daily_panel, build_nationality_rows
from tourism_twin.data.ingest import read_raw_workbook
from tourism_twin.data.repository import LakeRepository
from tourism_twin.models.backtest import RollingOrigin, backtest
from tourism_twin.models.noise import NoiseModel
from tourism_twin.models.specs import MODEL_SPECS

DOMESTIC_TEST_FILE = "data domestic_test.xlsx"
INTERNATIONAL_TEST_FILE = "data international_test.xlsx"
NOISE_ORIGINS = RollingOrigin("2024-07-01", "2025-02-01", horizon_months=6)


@dataclass
class TestPredictions:
    domestic: pd.DataFrame        # domestic test workbook + Guests
    international: pd.DataFrame   # international test workbook + Guests
    intervals: pd.DataFrame       # Date, Nationality, Residence (groups), Guests_p10, Guests_p50, Guests_p90
    market_daily: pd.DataFrame    # market, date, pred, lower, upper (before disaggregation)


def predict_test_split(
    spec: str = "twin_daily",
    repository: Optional[LakeRepository] = None,
    coverage: float = 0.8,
    with_intervals: bool = True,
) -> TestPredictions:
    panel = build_daily_panel(repository)
    train, test = panel[panel["dataset_split"] == "train"], panel[panel["dataset_split"] == "test"]
    model = MODEL_SPECS[spec]().fit(train)
    market = test[["market", "date"]].assign(pred=model.predict(test))
    market["horizon_days"] = (market["date"] - market["date"].min()).dt.days
    if with_intervals:
        noise = NoiseModel().fit(backtest({spec: MODEL_SPECS[spec]}, panel, NOISE_ORIGINS).predictions)
        market = market.join(noise.intervals(market, coverage))
    else:
        market = market.assign(lower=np.nan, upper=np.nan)

    rows = build_nationality_rows(repository)
    rows = rows[rows["dataset_split"] == "test"].copy()
    totals = rows.groupby(["market", "date"])["new_arrivals_filled"].transform("sum")
    counts = rows.groupby(["market", "date"])["new_arrivals_filled"].transform("size")
    rows["share"] = np.where(totals > 0, rows["new_arrivals_filled"] / totals.where(totals > 0, 1.0), 1.0 / counts)
    rows = rows.merge(market[["market", "date", "pred", "lower", "upper"]], on=["market", "date"], how="left")
    for column in ("pred", "lower", "upper"):
        rows[column] = rows[column] * rows["share"]

    domestic = _attach(read_raw_workbook(DOMESTIC_TEST_FILE), rows[rows["residence_group"] == "Domestic"], ["Date"])
    international = _attach(read_raw_workbook(INTERNATIONAL_TEST_FILE), rows[rows["residence_group"] == "International"], ["Date", "Nationality"])
    intervals = pd.concat([
        international[["Date", "Nationality", "Residence (groups)"]].assign(
            Guests_p10=international["_lower"], Guests_p50=international["Guests"], Guests_p90=international["_upper"]),
        domestic[["Date", "Residence (groups)"]].assign(
            Nationality=pd.NA, Guests_p10=domestic["_lower"], Guests_p50=domestic["Guests"], Guests_p90=domestic["_upper"]),
    ], ignore_index=True)[["Date", "Nationality", "Residence (groups)", "Guests_p10", "Guests_p50", "Guests_p90"]]
    return TestPredictions(domestic.drop(columns=["_lower", "_upper"]), international.drop(columns=["_lower", "_upper"]),
                           intervals, market.drop(columns=["horizon_days"]))


def _attach(raw: pd.DataFrame, rows: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """The raw test workbook with Guests (and interval bounds) joined on its own keys, in its order."""
    values = rows.rename(columns={"date": "Date", "nationality": "Nationality"})[[*keys, "pred", "lower", "upper"]]
    out = raw.merge(values, on=keys, how="left", validate="one_to_one")
    return out.rename(columns={"pred": "Guests", "lower": "_lower", "upper": "_upper"})


def validate_predictions(predictions: TestPredictions) -> list[str]:
    """Problems that would make a submission invalid; empty when the outputs are usable."""
    problems = []
    for name, frame, filename, keys in (
        ("domestic", predictions.domestic, DOMESTIC_TEST_FILE, ["Date"]),
        ("international", predictions.international, INTERNATIONAL_TEST_FILE, ["Date", "Nationality"]),
    ):
        raw = read_raw_workbook(filename)
        if len(frame) != len(raw) or not frame[keys].reset_index(drop=True).equals(raw[keys]):
            problems.append(f"{name}: rows or keys differ from {filename}")
        guests = frame["Guests"]
        if guests.isna().any():
            problems.append(f"{name}: {int(guests.isna().sum())} missing Guests")
        if (guests < 0).any():
            problems.append(f"{name}: {int((guests < 0).sum())} negative Guests")
    bounds = predictions.intervals[["Guests_p10", "Guests_p50", "Guests_p90"]]
    if bounds.notna().all().all() and not ((bounds["Guests_p10"] <= bounds["Guests_p50"]) & (bounds["Guests_p50"] <= bounds["Guests_p90"])).all():
        problems.append("intervals: p10 <= p50 <= p90 violated")
    return problems
