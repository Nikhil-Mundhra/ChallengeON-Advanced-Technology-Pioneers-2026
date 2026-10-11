"""Capacity growth: how guests follow a yearly seat trend. The data cannot tell growth caused by
seats from growth caused by demand, so the guest effect is an assumption between 0 (guests do not
follow) and 1 (guests grow as fast as seats). The central value is the historical co-movement of
the guest trend with the seat trend, an association, not an effect:

    dlog trend_52(guests) = a_m + gamma * dlog trend_52(seats)

52-week changes of each market's centred 13-week trend, pooled over markets with a market intercept
a_m (the market's own guest growth with flat seats).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict

import numpy as np
import pandas as pd

TREND_WEEKS = 13
YEAR_WEEKS = 52
COVERAGE = 0.9
N_BOOT = 1000
SEED = 0
EFFECT_RANGE = (0.0, 1.0)   # guests do not follow seats .. guests grow one for one with seats


@dataclass(frozen=True)
class CoMovement:
    gamma: float        # guest-trend growth per unit of seat-trend growth (log points)
    low: float
    high: float
    intercept: float    # mean over markets of the yearly guest-trend growth with flat seats (log points)
    n_pairs: int
    n_markets: int

    @property
    def central(self) -> float:
        """gamma inside the assumed effect range: the line the simulator draws."""
        return float(np.clip(self.gamma, *EFFECT_RANGE))

    def to_dict(self) -> Dict[str, object]:
        return {**asdict(self), "central": self.central, "effect_range": list(EFFECT_RANGE), "coverage": COVERAGE}


def _weekly(panel: pd.DataFrame, market: str) -> pd.DataFrame:
    """One market's seats and guests on a gap-free weekly index, so a missing week is never bridged
    by the trend; non-positive values count as missing, since both enter in log."""
    rows = panel[panel["market"] == market].assign(week_start=lambda f: pd.to_datetime(f["week_start"]))
    frame = rows.set_index("week_start").sort_index()[["seats", "guests"]].asfreq("7D")
    return frame.where(frame > 0)


def trend_growth(panel: pd.DataFrame) -> pd.DataFrame:
    """market, gs, gq: 52-week log changes of the centred seat and guest trends, markets with seats only."""
    frames = []
    for market in sorted(panel["market"].unique()):
        trend = np.log(_weekly(panel, market).rolling(TREND_WEEKS, center=True, min_periods=TREND_WEEKS).mean())
        growth = (trend - trend.shift(YEAR_WEEKS)).dropna().rename(columns={"seats": "gs", "guests": "gq"})
        if len(growth):
            frames.append(growth.assign(market=market))
    return pd.concat(frames, ignore_index=True)


def _fit(growth: pd.DataFrame):
    """Slope with market means removed, and the mean market intercept."""
    centred = growth[["gs", "gq"]] - growth.groupby("market")[["gs", "gq"]].transform("mean")
    gamma = float((centred["gs"] * centred["gq"]).sum() / (centred["gs"] ** 2).sum())
    means = growth.groupby("market")[["gs", "gq"]].mean()
    return gamma, float((means["gq"] - gamma * means["gs"]).mean())


def fit_comovement(panel: pd.DataFrame, n_boot: int = N_BOOT, seed: int = SEED) -> CoMovement:
    """Pooled slope with a market-cluster bootstrap interval (the 52-week changes overlap within a
    market, so markets, not weeks, are the independent draws)."""
    growth = trend_growth(panel)
    gamma, intercept = _fit(growth)
    groups = [g for _, g in growth.groupby("market")]
    rng = np.random.default_rng(seed)
    draws = [_fit(pd.concat([groups[i].assign(market=k) for k, i in enumerate(rng.integers(0, len(groups), len(groups)))]))[0]
             for _ in range(n_boot)]
    tail = (1 - COVERAGE) / 2
    low, high = np.quantile(draws, [tail, 1 - tail])
    return CoMovement(gamma, float(low), float(high), intercept, len(growth), len(groups))


def capacity_guest_factor(growth_pct: float, years: float, effect: float) -> float:
    """Guests with the seat trend / guests without it, `years` after the trend starts, when guests
    follow seats with elasticity `effect`."""
    return (1.0 + growth_pct / 100.0) ** (max(0.0, years) * effect)
