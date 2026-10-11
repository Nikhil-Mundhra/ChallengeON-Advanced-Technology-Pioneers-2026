"""Schedule response: the elasticity of hotel guests to a market's seats, read off the fitted
planning chain (CHAIN_SPECS["seat_chain"], planning/chain.py) rather than estimated separately.

For each fit, seats change by each of CHANGES on every day of the last WINDOW_DAYS of its training
data; both links re-run, and per market and season

    epsilon(change) = log(sum scenario guests / sum baseline guests) / log(1 + change)

over the window's days after WARMUP_DAYS (the seat and arrival kernels have filled). The chain's
response is close to linear in log, so a scenario scales guests by (seats ratio) ** epsilon, epsilon
the mean over CHANGES; `curvature` records how far the four points stray from it. The range is the
lowest and highest epsilon over the full fit and the VALIDATION_ORIGINS refits.
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from tourism_twin.data.daily_panel import build_daily_panel, with_scheduled_seats
from tourism_twin.domain.markets import DOMESTIC
from tourism_twin.domain.seasons import SEASONS, assign_season
from tourism_twin.models.backtest import VALIDATION_ORIGINS

CHAIN = "seat_chain"
CHANGES = (-0.25, -0.10, 0.10, 0.25)
WINDOW_DAYS = 365
WARMUP_DAYS = 28   # 7 seat lags + 21 arrival lags: from then on guests carry the change in full


@dataclass(frozen=True)
class Elasticity:
    epsilon: float
    low: float
    high: float
    pooled: bool
    points: tuple = ()        # epsilon at each of CHANGES, full fit
    curvature: float = 0.0    # largest |point - epsilon|


@dataclass
class ScheduleResponse:
    markets: Dict[str, Dict[str, Elasticity]]
    pooled: Dict[str, Elasticity]

    def for_market(self, market: str, season: str) -> Elasticity:
        """The market's elasticity for the season, or the pooled one (no seats of its own, cold start)."""
        own = self.markets.get(market.upper().strip(), {})
        return own.get(season, self.pooled[season])

    def to_dict(self) -> Dict[str, object]:
        return {"source": CHAIN, "changes": list(CHANGES), "window_days": WINDOW_DAYS, "warmup_days": WARMUP_DAYS,
                "range": "min to max over the full fit and the VALIDATION_ORIGINS refits",
                "pooled": {s: asdict(e) for s, e in self.pooled.items()},
                "markets": {m: {s: asdict(e) for s, e in seasons.items()} for m, seasons in sorted(self.markets.items())}}

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "ScheduleResponse":
        def read(e):
            return Elasticity(**{**e, "points": tuple(e.get("points", ()))})
        return cls(markets={m: {s: read(e) for s, e in seasons.items()} for m, seasons in data["markets"].items()},
                   pooled={s: read(e) for s, e in data["pooled"].items()})


def chain_panel(max_date: str) -> pd.DataFrame:
    """International daily panel with scheduled seats, up to `max_date`."""
    daily = with_scheduled_seats(build_daily_panel())
    return daily[(daily["market"] != DOMESTIC) & (daily["date"] <= pd.Timestamp(max_date))].reset_index(drop=True)


def response_points(chain, daily: pd.DataFrame, end: pd.Timestamp) -> pd.DataFrame:
    """market, season, change, epsilon for a fitted chain, seats changed on the WINDOW_DAYS up to `end`."""
    start = end - pd.Timedelta(days=WINDOW_DAYS + WARMUP_DAYS)
    rows: List[tuple] = []
    for market, frame in daily[daily["date"] <= end].groupby("market"):
        inside = (frame["date"] >= start).to_numpy()
        counted = (frame["date"] >= start + pd.Timedelta(days=WARMUP_DAYS)).to_numpy()
        season = frame["date"].dt.month.map(assign_season).to_numpy()
        base = chain.predict_frame(frame)["guests"].to_numpy()
        for change in CHANGES:
            scenario = chain.predict_frame(frame.assign(seats=np.where(inside, frame["seats"] * (1 + change), frame["seats"])))
            for s in SEASONS:
                days = counted & (season == s) & np.isfinite(base) & np.isfinite(scenario["guests"].to_numpy())
                total = base[days].sum()
                if total > 0:
                    ratio = scenario["guests"].to_numpy()[days].sum() / total
                    rows.append((market, s, change, float(np.log(ratio) / np.log1p(change))))
    return pd.DataFrame(rows, columns=["market", "season", "change", "epsilon"])


def _fit_and_respond(daily: pd.DataFrame, train_end: pd.Timestamp) -> pd.DataFrame:
    """Fit the chain on guest days before `train_end` and read its response (one worker's job)."""
    from tourism_twin.planning.specs import CHAIN_SPECS

    train = daily[daily["guests"].notna() & (daily["date"] < train_end)]
    chain = CHAIN_SPECS[CHAIN].build().fit(train)
    return response_points(chain, daily, train["date"].max())


def fit_schedule_response(daily: pd.DataFrame, workers: Optional[int] = None) -> ScheduleResponse:
    """Full fit (every guest day in `daily`) and the VALIDATION_ORIGINS refits, in parallel."""
    guest_days = daily.loc[daily["guests"].notna(), "date"]
    ends = [guest_days.max() + pd.Timedelta(days=1), *[f.train_end for f in VALIDATION_ORIGINS.folds(guest_days)]]
    with ProcessPoolExecutor(max_workers=workers or len(ends)) as pool:
        runs = list(pool.map(_fit_and_respond, [daily] * len(ends), ends))
    return summarise(runs[0], runs[1:])


def summarise(full: pd.DataFrame, refits: List[pd.DataFrame]) -> ScheduleResponse:
    """Per market and season: epsilon and points from the full fit, the range over every fit. The
    pooled elasticity per season is the median over markets with the widest range among them."""
    central = full.groupby(["market", "season"])["epsilon"].mean().rename("epsilon")
    every = pd.concat([f.groupby(["market", "season"])["epsilon"].mean() for f in [full, *refits]], axis=1)
    markets: Dict[str, Dict[str, Elasticity]] = {}
    for (market, season), epsilon in central.items():
        points = tuple(full[(full["market"] == market) & (full["season"] == season)].sort_values("change")["epsilon"])
        spread = every.loc[(market, season)].dropna()
        markets.setdefault(market, {})[season] = Elasticity(
            float(epsilon), float(spread.min()), float(spread.max()), pooled=False, points=points,
            curvature=float(max(abs(p - epsilon) for p in points)))
    pooled = {}
    for season in SEASONS:
        own = [seasons[season] for seasons in markets.values() if season in seasons]
        pooled[season] = Elasticity(float(np.median([e.epsilon for e in own])), min(e.low for e in own),
                                    max(e.high for e in own), pooled=True)
    return ScheduleResponse(markets, pooled)


def schedule_factor(base_seats: float, seats: float, epsilon: float) -> Optional[float]:
    """Guests with the schedule change / guests without it; None when there is no baseline
    schedule to scale (a new route) or no seats left (a closure)."""
    if base_seats <= 0.0 or seats <= 0.0:
        return None
    return (seats / base_seats) ** epsilon
