"""Daily panel (all 21 markets, with scheduled seats for the chain), the fold windows and the cached
outputs folder (licensed data, gitignored)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd

from tourism_twin.data.daily_panel import build_daily_panel, with_scheduled_seats
from tourism_twin.domain.markets import DOMESTIC
from tourism_twin.features import PANEL_FEATURES
from tourism_twin.models.backtest import VALIDATION_ORIGINS, Fold, RollingOrigin

OUT = Path(__file__).resolve().parent / "out"
HELD_BACK_DAYS = 28  # the held-back block at the window end; the largest k of the carry-forward grid

# The protocol trains 21 days before each origin. Production trains up to the day before the test
# period, so the same origins with no gap answer the production question (exploratory, never gated).
SPLITTERS = {
    "protocol": VALIDATION_ORIGINS,
    "gap0": RollingOrigin("2024-02-01", "2024-08-01", horizon_months=6, gap_days=0, end="2025-01-31"),
}


@dataclass(frozen=True)
class Window:
    """One fit: a fold of a splitter, trained on the full window or on the window minus the held-back block."""

    splitter: str
    fold: Fold
    held_back: bool

    @property
    def fit_end(self) -> pd.Timestamp:
        """Training rows have date < fit_end."""
        return self.fold.train_end - pd.Timedelta(days=HELD_BACK_DAYS) if self.held_back else self.fold.train_end

    @property
    def last_known(self) -> pd.Timestamp:
        """The last day whose guests the forecaster knows at the origin."""
        return self.fold.train_end - pd.Timedelta(days=1)


def panel() -> pd.DataFrame:
    path = OUT / "panel.pkl"
    if path.exists():
        return pd.read_pickle(path)
    frame = PANEL_FEATURES.apply(with_scheduled_seats(build_daily_panel()), ["is_one_off_period"], anchor="date")
    OUT.mkdir(exist_ok=True)
    frame.to_pickle(path)
    return frame


def folds(splitter: str, frame: pd.DataFrame) -> List[Fold]:
    return SPLITTERS[splitter].folds(frame["date"][frame["guests"].notna()])


def training_rows(frame: pd.DataFrame) -> pd.Series:
    """Rows the nowcast trains on (nowcast/specs.py NOWCAST_ROWS) with a known target."""
    return frame["guests"].notna() & frame["lag_complete"].astype(bool) & (frame["is_one_off_period"] != 1)


def series_of(markets: pd.Series) -> np.ndarray:
    return np.where(markets.to_numpy() == DOMESTIC, "domestic", "international")


def week_start(dates: pd.Series) -> pd.Series:
    dates = pd.to_datetime(dates)
    return dates - pd.to_timedelta(dates.dt.weekday, unit="D")
