"""Competition predictions for the test split (2025-08-01 to 2026-02-28).

The chosen daily spec is fitted on every training day and predicts each test (market, date).
Markets that pool several nationalities are split by each nationality's share of the market's
new arrivals that day (new_arrivals_filled; shares are taken over all nationality-days, including
those absent from the test file, because the market model's arrivals include them). Prediction
intervals come from a NoiseModel fitted on the spec's rolling-origin back-test; the horizon is
counted from the first test day. Floors, workbook files and validation: nowcast/submission.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from tourism_twin.data.daily_panel import build_daily_panel, build_nationality_rows
from tourism_twin.data.repository import LakeRepository
from tourism_twin.domain.markets import DOMESTIC
from tourism_twin.models.backtest import RollingOrigin, backtest
from tourism_twin.models.noise import NoiseModel
from tourism_twin.nowcast.disaggregation import split_market_predictions, split_shares
from tourism_twin.nowcast.pooling import predict_pooled_nationalities
from tourism_twin.nowcast.specs import DAILY_SPECS
from tourism_twin.nowcast.submission import apply_guest_floor, build_submission

NOISE_ORIGINS = RollingOrigin("2024-07-01", "2025-02-01", horizon_months=7)  # test horizon is 7 months
TOTAL = "TOTAL"  # domestic + international guests, with its own error series in the noise model
INTERNATIONAL = "INTERNATIONAL"  # the 20 international markets summed, likewise


@dataclass
class TestPredictions:
    domestic: pd.DataFrame        # domestic test workbook + Guests
    international: pd.DataFrame   # international test workbook + Guests
    intervals: pd.DataFrame       # Date, Nationality, Residence (groups), Guests_p10, Guests_p50, Guests_p90
    market_daily: pd.DataFrame    # market, date, pred, lower, upper (before disaggregation)
    model: object = None          # the fitted spec (for decomposition and explain())
    backtest_predictions: pd.DataFrame = None  # the interval back-test's predictions (None without intervals)
    noise: Optional[NoiseModel] = None         # fitted on backtest_predictions plus their TOTAL series
    total: pd.DataFrame = None    # date, pred, lower, upper: daily total guests over all markets
    test_panel: pd.DataFrame = None  # the daily test panel the model predicted (for decompositions)


def predict_test_split(
    spec: str = "twin_daily",
    repository: Optional[LakeRepository] = None,
    coverage: float = 0.8,
    with_intervals: bool = True,
) -> TestPredictions:
    panel = build_daily_panel(repository)
    train, test = panel[panel["dataset_split"] == "train"], panel[panel["dataset_split"] == "test"]
    model = DAILY_SPECS[spec]().fit(train)
    market = test[["market", "date"]].assign(pred=model.predict(test))
    market["horizon_days"] = (market["date"] - market["date"].min()).dt.days
    total = total_series(market)
    backtest_predictions, noise = None, None
    if with_intervals:
        backtest_predictions = backtest({spec: DAILY_SPECS[spec]}, panel, NOISE_ORIGINS).predictions
        # The total's errors are correlated across markets (shared calendar shocks), so its
        # interval comes from the back-test errors of the summed series, not from adding bounds.
        aggregates = [total_series(backtest_predictions), total_series(backtest_predictions, INTERNATIONAL)]
        noise = NoiseModel().fit(pd.concat([backtest_predictions, *aggregates], ignore_index=True))
        market = market.join(noise.intervals(market, coverage))
        total = total.join(noise.intervals(total, coverage))
    else:
        market = market.assign(lower=np.nan, upper=np.nan)
        total = total.assign(lower=np.nan, upper=np.nan)
    total = total.drop(columns=["horizon_days", "market"])

    rows = build_nationality_rows(repository)
    rows["share"] = split_shares(rows)
    rows = split_market_predictions(rows, market, coverage, with_intervals)
    pooled = predict_pooled_nationalities(NOISE_ORIGINS, coverage, with_intervals, repository)
    rows = rows.merge(pooled.rename(columns={"pred": "pooled_pred", "lower": "pooled_lower", "upper": "pooled_upper"}),
                      on=["nationality", "date"], how="left")
    use = rows["pooled_pred"].notna()
    for column in ("pred", "lower", "upper"):
        rows.loc[use, column] = rows.loc[use, f"pooled_{column}"]
    rows = apply_guest_floor(rows.drop(columns=["pooled_pred", "pooled_lower", "pooled_upper"]))
    domestic, international, intervals = build_submission(rows, with_intervals)
    return TestPredictions(domestic, international, intervals, market, model, backtest_predictions, noise, total, test)


def total_series(predictions: pd.DataFrame, name: str = TOTAL) -> pd.DataFrame:
    """Predictions summed per day (and per fold for back-test rows) over every market (TOTAL) or
    over the international markets (INTERNATIONAL), labelled as that market."""
    if name == INTERNATIONAL:
        predictions = predictions[predictions["market"] != DOMESTIC]
    keys = [c for c in ("fold", "origin", "model", "date", "horizon_days") if c in predictions.columns]
    values = [c for c in ("pred", "actual") if c in predictions.columns]
    return predictions.groupby(keys, as_index=False)[values].sum().assign(market=name)
