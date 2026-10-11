"""Link-0 coefficients: descriptive slopes, fitted betas, gamma and C's input coefficients with
block-resampling intervals, and C's independence check.

Intervals: delete-half block jackknife on one training window: each draw keeps a random half of the
28-day blocks (all markets together, so serial correlation stays inside a block) and refits; for
half-samples the spread of the draws estimates the full-sample spread, so the 90% interval is the
estimate plus the 5% and 95% quantiles of (draw - mean of draws).
"""

from __future__ import annotations

import os
from typing import Callable, Dict

import numpy as np
import pandas as pd

import data
from passengers_link import SCHEDULE_INPUTS, ScheduleInputs, TrendResponse, schedule_deviations, schedule_inputs

BLOCK_DAYS = 28
DRAWS = int(os.environ.get("DRAWS", 100))
CENTRED_WEEKS = 13


def descriptive_slopes(panel: pd.DataFrame, end: pd.Timestamp) -> pd.DataFrame:
    """Pooled least-squares slope of log(y / centred 13-week mean y) on log(seats / centred 13-week
    mean seats), market-weeks before `end`, edge weeks (incomplete centred window) dropped."""
    weekly = data.weekly(panel[(panel["date"] < end) & panel["seats"].notna()], ["seats", "p2p", "pax"])
    weekly = weekly[(weekly[["seats", "p2p", "pax"]] > 0).all(axis=1)].sort_values(["market", "week_start"])
    rows = {}
    for column in ("p2p", "pax"):
        trend = weekly.groupby("market")[["seats", column]].transform(lambda s: s.rolling(CENTRED_WEEKS, center=True).mean())
        x, y = np.log(weekly["seats"] / trend["seats"]), np.log(weekly[column] / trend[column])
        ok = x.notna() & y.notna()
        x, y = x[ok], y[ok]
        lf_move = (weekly[column] / weekly["seats"] - trend[column] / trend["seats"])[ok]
        for label, keep in (("all", x == x), ("increases", x > 0), ("cuts", x < 0)):
            rows[(column, label)] = {"n": int(keep.sum()), "slope": float(x[keep] @ y[keep] / (x[keep] @ x[keep])),
                                     "rate_move_pp_per_10pct_seats": float(100 * (lf_move[keep] @ x[keep]) / (x[keep] @ x[keep]) * 0.1)}
    return pd.DataFrame(rows).T


def _half_sample(frame: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """`frame` with P2P zeroed outside a random half of the 28-day blocks (zero-P2P rows are not fitted;
    the trailing seat trends still see every day)."""
    block = (frame["date"] - frame["date"].min()).dt.days // BLOCK_DAYS
    blocks = block.unique()
    keep = block.isin(rng.choice(blocks, size=len(blocks) // 2, replace=False))
    return frame.assign(p2p=frame["p2p"].where(keep, 0.0))


def interval(train: pd.DataFrame, make: Callable[[], object], summary: Callable[[object], pd.Series], seed: int = 0) -> pd.DataFrame:
    estimate = summary(make().fit(train))
    rng = np.random.default_rng(seed)
    draws = pd.DataFrame([summary(make().fit(_half_sample(train, rng))) for _ in range(DRAWS)])
    centred = draws - draws.mean()
    return pd.DataFrame({"estimate": estimate, "low": estimate + centred.quantile(0.05), "high": estimate + centred.quantile(0.95)})


def median_betas(model: TrendResponse) -> pd.Series:
    table = model.betas()
    fitted = table[[c for c in table.columns if not c.endswith("_unpooled") and c != "beta_down_at_market_lf"]]
    out = pd.concat([fitted.median().add_prefix("median "), fitted.mean().add_prefix("mean ")])
    return pd.concat([out, pd.Series({"gamma": model.gamma_})]) if model.slopes == "usual_lf" else out


def median_coefficients(model: ScheduleInputs) -> pd.Series:
    fitted = model.coefficients()[list(SCHEDULE_INPUTS)]
    return pd.concat([fitted.median().add_prefix("median "), fitted.mean().add_prefix("mean ")])


def independence(train: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Correlation and VIF of C's detrended inputs on training days with seats, each market's
    deviations centred on the market (pooled), plus the median within-market correlation."""
    values = schedule_inputs(train)
    deviations = schedule_deviations(values).assign(market=train["market"]).dropna()
    centred = deviations.groupby("market")[list(SCHEDULE_INPUTS)].transform(lambda s: s - s.mean())
    corr = centred.corr()
    vif = pd.Series(np.diag(np.linalg.inv(corr.to_numpy())), index=corr.index, name="VIF")
    within = deviations.groupby("market")[list(SCHEDULE_INPUTS)].corr()
    within_median = within.groupby(level=1).median().loc[list(SCHEDULE_INPUTS), list(SCHEDULE_INPUTS)]
    return {"pooled correlation": corr, "VIF": vif.to_frame(), "median within-market correlation": within_median}
