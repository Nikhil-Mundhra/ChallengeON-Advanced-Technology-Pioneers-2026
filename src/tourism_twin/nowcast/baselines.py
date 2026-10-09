"""Daily nowcast baselines behind the Model protocol."""

from __future__ import annotations

import numpy as np
import pandas as pd


class SeasonalNaive:
    """Daily: the same market's value `period` days earlier (364 keeps the weekday), stepping back
    whole periods until the source date lies in the training data."""

    def __init__(self, period: int = 364, date_column: str = "date", max_periods: int = 4) -> None:
        self.period, self.date_column, self.max_periods = period, date_column, max_periods

    def fit(self, panel: pd.DataFrame) -> "SeasonalNaive":
        dates = pd.to_datetime(panel[self.date_column])
        self.history_ = pd.Series(panel["guests"].to_numpy(), index=pd.MultiIndex.from_arrays([panel["market"], dates]))
        self.last_ = dates.groupby(panel["market"]).max().to_dict()
        return self

    def predict(self, panel: pd.DataFrame) -> pd.Series:
        dates = pd.to_datetime(panel[self.date_column])
        last = panel["market"].map(self.last_)
        out = pd.Series(np.nan, index=panel.index, dtype=float)
        for k in range(1, self.max_periods + 1):
            source = dates - pd.to_timedelta(self.period * k, unit="D")
            todo = out.isna() & (source <= last)
            if not todo.any():
                break
            keys = pd.MultiIndex.from_arrays([panel.loc[todo, "market"], source[todo]])
            out.loc[todo] = self.history_.reindex(keys).to_numpy()
        return out


class ArrivalsRatio:
    """Daily nowcast baseline: new arrivals times the market's training guests / arrivals ratio."""

    def fit(self, panel: pd.DataFrame) -> "ArrivalsRatio":
        totals = panel.groupby("market")[["guests", "new_arrivals_filled"]].sum()
        self.ratio_ = (totals["guests"] / totals["new_arrivals_filled"]).to_dict()
        return self

    def predict(self, panel: pd.DataFrame) -> pd.Series:
        unseen = sorted(set(panel["market"]) - set(self.ratio_))
        if unseen:
            raise ValueError(f"ArrivalsRatio has no ratio for markets {unseen}")
        return panel["new_arrivals_filled"] * panel["market"].map(self.ratio_)
