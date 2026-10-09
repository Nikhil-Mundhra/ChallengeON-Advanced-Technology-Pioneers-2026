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
from scipy.stats import norm

from tourism_twin.data.daily_panel import build_daily_panel, build_nationality_rows
from tourism_twin.data.ingest import read_raw_workbook
from tourism_twin.data.repository import LakeRepository
from tourism_twin.models.backtest import RollingOrigin, backtest
from tourism_twin.models.noise import NoiseModel
from tourism_twin.models.specs import MODEL_SPECS

DOMESTIC_TEST_FILE = "data domestic_test.xlsx"
INTERNATIONAL_TEST_FILE = "data international_test.xlsx"
NOISE_ORIGINS = RollingOrigin("2024-07-01", "2025-02-01", horizon_months=7)  # test horizon is 7 months


@dataclass
class TestPredictions:
    domestic: pd.DataFrame        # domestic test workbook + Guests
    international: pd.DataFrame   # international test workbook + Guests
    intervals: pd.DataFrame       # Date, Nationality, Residence (groups), Guests_p10, Guests_p50, Guests_p90
    market_daily: pd.DataFrame    # market, date, pred, lower, upper (before disaggregation)
    model: object = None          # the fitted spec (for decomposition and explain())
    backtest_predictions: pd.DataFrame = None  # the interval back-test's predictions (None without intervals)
    noise: Optional[NoiseModel] = None         # fitted on backtest_predictions (None without intervals)


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
    backtest_predictions, noise = None, None
    if with_intervals:
        backtest_predictions = backtest({spec: MODEL_SPECS[spec]}, panel, NOISE_ORIGINS).predictions
        noise = NoiseModel().fit(backtest_predictions)
        market = market.join(noise.intervals(market, coverage))
    else:
        market = market.assign(lower=np.nan, upper=np.nan)
    market = market.drop(columns=["horizon_days"])

    rows = build_nationality_rows(repository)
    rows["share"] = split_shares(rows)
    split_variance = split_error_variance(rows[rows["dataset_split"] == "train"])
    rows = rows[rows["dataset_split"] == "test"].merge(market, on=["market", "date"], how="left")
    if with_intervals:
        # Market log sd from its bounds, plus the split's own error for pooled markets.
        z = norm.ppf(0.5 + coverage / 2)
        market_sd = np.log(rows["upper"] / rows["pred"]) / z
        sd = np.sqrt(market_sd ** 2 + rows["market"].map(split_variance).fillna(0.0))
        nationality_pred = rows["pred"] * rows["share"]
        rows["lower"], rows["upper"] = nationality_pred * np.exp(-z * sd), nationality_pred * np.exp(z * sd)
    rows["pred"] = rows["pred"] * rows["share"]

    domestic = _attach(read_raw_workbook(DOMESTIC_TEST_FILE), rows[rows["residence_group"] == "Domestic"], ["Date"])
    international = _attach(read_raw_workbook(INTERNATIONAL_TEST_FILE), rows[rows["residence_group"] == "International"], ["Date", "Nationality"])
    intervals = pd.concat([
        international[["Date", "Nationality", "Residence (groups)"]].assign(
            Guests_p10=international["_lower"], Guests_p50=international["Guests"], Guests_p90=international["_upper"]),
        domestic[["Date", "Residence (groups)"]].assign(
            Nationality=pd.NA, Guests_p10=domestic["_lower"], Guests_p50=domestic["Guests"], Guests_p90=domestic["_upper"]),
    ], ignore_index=True)[["Date", "Nationality", "Residence (groups)", "Guests_p10", "Guests_p50", "Guests_p90"]]
    if not with_intervals:
        intervals = intervals.iloc[0:0]
    return TestPredictions(domestic.drop(columns=["_lower", "_upper"]), international.drop(columns=["_lower", "_upper"]),
                           intervals, market, model, backtest_predictions, noise)


SHARE_WINDOW_DAYS = 7
SPLIT_ERROR_DAYS = 365


def split_shares(rows: pd.DataFrame) -> pd.Series:
    """Each nationality's share of its market on a day: trailing SHARE_WINDOW_DAYS new arrivals
    times the nationality's training guests / arrivals ratio (guests are a stock of recent
    arrivals, and stay length differs by nationality), normalised within (market, date). Shares
    cover every nationality-day, including those absent from the test file."""
    rows = rows.sort_values(["nationality", "date"])
    trailing = rows.groupby(["residence_group", "nationality"], dropna=False)["new_arrivals_filled"].transform(
        lambda s: s.rolling(SHARE_WINDOW_DAYS, min_periods=1).sum())
    train = rows[(rows["dataset_split"] == "train") & rows["guests"].notna()]
    by_nationality = train.groupby("nationality")[["guests", "new_arrivals_filled"]].sum()
    by_market = train.groupby("market")[["guests", "new_arrivals_filled"]].sum()
    ratio = rows["nationality"].map(by_nationality["guests"] / by_nationality["new_arrivals_filled"])
    ratio = ratio.fillna(rows["market"].map(by_market["guests"] / by_market["new_arrivals_filled"])).fillna(1.0)
    weight = trailing * ratio
    totals = weight.groupby([rows["market"], rows["date"]]).transform("sum")
    counts = weight.groupby([rows["market"], rows["date"]]).transform("size")
    return (weight / totals).where(totals > 0, 1.0 / counts).reindex(rows.index)


def split_error_variance(train_rows: pd.DataFrame) -> pd.Series:
    """Per market, the variance of log(actual / split) when the market's actual guests are split by
    split_shares over the last SPLIT_ERROR_DAYS training days; 0 for single-nationality markets."""
    rows = train_rows[train_rows["date"] > train_rows["date"].max() - np.timedelta64(SPLIT_ERROR_DAYS, "D")]
    rows = rows[rows["guests"] > 0]
    market_guests = rows.groupby(["market", "date"])["guests"].transform("sum")
    errors = np.log(rows["guests"] / (market_guests * rows["share"]))
    return errors.groupby(rows["market"]).apply(lambda e: float(np.mean(e ** 2)) if len(e) else 0.0)



def _attach(raw: pd.DataFrame, rows: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """The raw test workbook with Guests (and interval bounds) joined on its own keys, in its order."""
    values = rows.rename(columns={"date": "Date", "nationality": "Nationality"})[[*keys, "pred", "lower", "upper"]]
    out = raw.merge(values, on=keys, how="left", validate="one_to_one")
    return out.rename(columns={"pred": "Guests", "lower": "_lower", "upper": "_upper"})


def validate_predictions(predictions: TestPredictions) -> list[str]:
    """Problems that would make a submission invalid; empty when the outputs are usable."""
    problems = []
    keys_by_part = []
    for name, frame, filename, keys in (
        ("domestic", predictions.domestic, DOMESTIC_TEST_FILE, ["Date"]),
        ("international", predictions.international, INTERNATIONAL_TEST_FILE, ["Date", "Nationality"]),
    ):
        raw = read_raw_workbook(filename)
        if list(frame.columns) != [*raw.columns, "Guests"] or not frame.drop(columns="Guests").reset_index(drop=True).equals(raw):
            problems.append(f"{name}: columns or source values differ from {filename}")
        guests = frame["Guests"].to_numpy(dtype=float)
        if not np.isfinite(guests).all():
            problems.append(f"{name}: {int((~np.isfinite(guests)).sum())} missing or infinite Guests")
        if (guests <= 0).any():
            problems.append(f"{name}: {int((guests <= 0).sum())} Guests <= 0")
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
