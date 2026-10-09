"""Split pooled-market predictions into nationalities: shares from trailing arrivals and stay
ratios, and the split's own log-error variance for the nationality intervals."""

from __future__ import annotations

import numpy as np
import pandas as pd

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
