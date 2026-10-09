"""Weekly sums of the daily nowcast: full Monday-Sunday weeks per market with an interval and the
direction to the next week, both from the daily AR(1) error model (NoiseModel)."""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd
from scipy.stats import norm

from tourism_twin.features.calendar import week_monday
from tourism_twin.models.noise import NoiseModel

WEEK_COLUMNS = ["market", "week_start", "forecast", "p10", "p90", "direction", "direction_prob"]


def weekly_forecast(daily: pd.DataFrame, noise: NoiseModel, coverage: float = 0.8) -> pd.DataFrame:
    """daily: market, date, horizon_days, pred. Per full week: forecast (sum), p10/p90
    (NoiseModel.range_interval), and the direction to the next week with its probability, from the
    s.d. of the difference of the two weeks' prediction-weighted mean log errors."""
    frame = daily.assign(week_start=week_monday(daily["date"])).sort_values(["market", "date"])
    rows: List[Dict[str, Any]] = []
    for market, group in frame.groupby("market"):
        weeks = [(start, days) for start, days in group.groupby("week_start") if len(days) == 7]
        for k, (start, days) in enumerate(weeks):
            pred, horizon = days["pred"].to_numpy(float), days["horizon_days"].to_numpy(float)
            p10, p90 = noise.range_interval(market, horizon, pred, coverage)
            row = {"market": market, "week_start": start, "forecast": pred.sum(), "p10": p10, "p90": p90,
                   "direction": None, "direction_prob": np.nan}
            if k + 1 < len(weeks) and weeks[k + 1][0] - start == pd.Timedelta(7, unit="D"):
                nxt = weeks[k + 1][1]
                pred_n = nxt["pred"].to_numpy(float)
                weights = np.r_[-pred / pred.sum(), pred_n / pred_n.sum()]
                sd = noise.weighted_sd(market, np.r_[horizon, nxt["horizon_days"].to_numpy(float)], weights)
                step = np.log(pred_n.sum() / pred.sum())
                prob_up = norm.cdf(step / max(sd, 1e-6))
                row["direction"] = "increase" if step >= 0 else "decrease"
                row["direction_prob"] = prob_up if step >= 0 else 1 - prob_up
            rows.append(row)
    return pd.DataFrame(rows, columns=WEEK_COLUMNS)
