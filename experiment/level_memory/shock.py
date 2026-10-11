"""Arrival collapse at the end of a training window: mean new arrivals over the last 90 training days
divided by the mean over the same 90 days a year earlier. Year on year, so Ramadan and the summer
low do not count as a collapse. Near 1 or above in normal times; Israel after 7 October 2023 falls
to about 0.1."""

from __future__ import annotations

import pandas as pd

RECENT_DAYS, YEAR_DAYS = 90, 364  # 364: same weekdays a year earlier


def recent_ratio(panel: pd.DataFrame, market: str, fit_end: pd.Timestamp) -> float:
    """Uses only rows with date < fit_end (the training window)."""
    rows = panel[panel["market"] == market].set_index("date")["new_arrivals_filled"]
    start = fit_end - pd.Timedelta(days=RECENT_DAYS)
    year = pd.Timedelta(days=YEAR_DAYS)
    recent = rows[(rows.index >= start) & (rows.index < fit_end)]
    before = rows[(rows.index >= start - year) & (rows.index < fit_end - year)]
    if before.empty or before.mean() <= 0:
        return 1.0
    return float(recent.mean() / before.mean())
