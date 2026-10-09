"""Nationality predictions for the pooled markets (issue #16): instead of splitting a market's
prediction by arrival share, each nationality is predicted from its own arrivals by a model shared
within its stay family (POOLED_NATIONALITIES), with intervals from that model's own back-test
errors per nationality. Nationalities of the 15 single-nationality markets keep their market model."""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from tourism_twin.data.daily_panel import build_nationality_panel
from tourism_twin.data.repository import LakeRepository
from tourism_twin.domain.markets import REGIONAL_CLUSTERS
from tourism_twin.models.backtest import RollingOrigin, backtest
from tourism_twin.models.noise import NoiseModel
from tourism_twin.nowcast.specs import POOLED_NATIONALITIES, SHORT_STAY_FAMILY

POOLED_MARKET_NATIONALITIES = frozenset(n for nationalities in REGIONAL_CLUSTERS.values() for n in nationalities)


def nationality_panel(repository: Optional[LakeRepository] = None) -> pd.DataFrame:
    panel = build_nationality_panel(repository)
    return panel.assign(family=np.where(panel["nationality"].isin(SHORT_STAY_FAMILY), "short", "long"))


def predict_pooled_nationalities(noise_origins: RollingOrigin, coverage: float, with_intervals: bool,
                                 repository: Optional[LakeRepository] = None) -> pd.DataFrame:
    """nationality, date, pred, lower, upper for the test days of the pooled-market nationalities."""
    panel = nationality_panel(repository)
    train, test = panel[panel["dataset_split"] == "train"], panel[panel["dataset_split"] == "test"]
    test = test[test["nationality"].isin(POOLED_MARKET_NATIONALITIES)]
    out = test[["nationality", "date"]].assign(pred=POOLED_NATIONALITIES.build().fit(train).predict(test).to_numpy())
    if not with_intervals:
        return out.assign(lower=np.nan, upper=np.nan)
    errors = backtest({"pooled": POOLED_NATIONALITIES.build}, panel, noise_origins).predictions
    errors = errors.assign(market=panel.loc[errors["row"], "nationality"].to_numpy())  # one error series per nationality
    errors = errors[errors["market"].isin(POOLED_MARKET_NATIONALITIES)]
    frame = out.rename(columns={"nationality": "market"}).assign(horizon_days=(out["date"] - out["date"].min()).dt.days)
    bounds = NoiseModel().fit(errors).intervals(frame, coverage)
    return out.assign(lower=bounds["lower"].to_numpy(), upper=bounds["upper"].to_numpy())
