"""SHORT-RUN: a learned short-run elasticity of weekly guests to weekly seats, per market.

Training (each origin's training weeks only): y = log(guests / centred 13-week guest trend),
x = log(seats / centred 13-week seat trend); the trend is computed on the training weeks alone and
needs all 13 weeks, so the last 6 training weeks drop out and nothing after the cutoff is read.
Per market, after removing the market mean of x and y:
    beta_m = (Sxy + ridge x beta_pool) / (Sxx + ridge),   beta_pool = median of the unpooled beta_m
Markets with fewer than MIN_WEEKS usable weeks get beta_pool. The ridge is chosen on VALIDATION_ORIGINS.
Prediction: baseline x (seats / reference seats) ^ beta_m. In the simulator the reference is the
trailing 13-week seat mean (data.trailing_trend); in the back-test it is the reference of each test
(last year's week, or the centred seat trend), the same reference every model gets.

Co-movement (information only, an association): per market, 52-week change in log centred guest trend
regressed on the 52-week change in log centred seat trend.
"""

from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd

import data

MIN_WEEKS = 26
RIDGES = (0.0, 0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 100.0)
BLOCK_WEEKS = 4
N_BOOT = 2000


def deviations(weekly: pd.DataFrame) -> pd.DataFrame:
    """market, week_start, x, y on weeks where both centred trends exist and seats, guests > 0."""
    frame = weekly[["market", "week_start", "seats", "guests"]].sort_values(["market", "week_start"]).reset_index(drop=True)
    frame["seat_trend"] = data.centred_trend(frame, "seats")
    frame["guest_trend"] = data.centred_trend(frame, "guests")
    ok = (frame[["seats", "guests", "seat_trend", "guest_trend"]] > 0).all(axis=1)
    frame = frame[ok]
    return frame.assign(x=np.log(frame["seats"] / frame["seat_trend"]), y=np.log(frame["guests"] / frame["guest_trend"]))[["market", "week_start", "x", "y"]]


def _moments(x: np.ndarray, y: np.ndarray) -> tuple:
    xc, yc = x - x.mean(), y - y.mean()
    return float(xc @ xc), float(xc @ yc)


def pooled(moments: Dict[str, tuple], counts: Dict[str, int], ridge: float) -> tuple:
    """(beta per market, beta_pool) from per-market (Sxx, Sxy)."""
    raw = {m: sxy / sxx for m, (sxx, sxy) in moments.items() if counts[m] >= MIN_WEEKS and sxx > 0}
    pool = float(np.median(list(raw.values())))
    beta = {m: ((sxy + ridge * pool) / (sxx + ridge) if m in raw else pool) for m, (sxx, sxy) in moments.items()}
    return beta, pool


class ShortRun:
    def __init__(self, ridge: float = 0.1) -> None:
        self.ridge = ridge

    def fit(self, weekly: pd.DataFrame) -> "ShortRun":
        dev = deviations(weekly)
        self.moments_ = {m: _moments(g["x"].to_numpy(), g["y"].to_numpy()) for m, g in dev.groupby("market")}
        self.counts_ = dev.groupby("market").size().to_dict()
        self.beta_, self.pool_ = pooled(self.moments_, self.counts_, self.ridge)
        self.dev_ = dev
        return self

    def beta(self, market: str) -> float:
        return self.beta_.get(market, self.pool_)

    def response(self, markets: pd.Series, log_seat_ratio: np.ndarray) -> np.ndarray:
        """log guest change for a log seat change, per row."""
        return np.array([self.beta(m) for m in markets]) * log_seat_ratio

    def bootstrap(self, seed: int = 0) -> pd.DataFrame:
        """beta per market with a 90% moving-block bootstrap interval (blocks of BLOCK_WEEKS weeks,
        resampled within each market; the pool is recomputed on every draw)."""
        rng = np.random.default_rng(seed)
        groups = {m: g.sort_values("week_start") for m, g in self.dev_.groupby("market")}
        draws = {m: np.empty(N_BOOT) for m in groups}
        pools = np.empty(N_BOOT)
        for b in range(N_BOOT):
            moments = {}
            for m, g in groups.items():
                n = len(g)
                starts = rng.integers(0, max(n - BLOCK_WEEKS, 0) + 1, size=int(np.ceil(n / BLOCK_WEEKS)))
                idx = (starts[:, None] + np.arange(BLOCK_WEEKS)).ravel()[:n]
                idx = idx[idx < n]
                moments[m] = _moments(g["x"].to_numpy()[idx], g["y"].to_numpy()[idx])
            beta, pools[b] = pooled(moments, self.counts_, self.ridge)
            for m in groups:
                draws[m][b] = beta[m]
        rows = [{"market": m, "beta": self.beta_[m], "ci_low": np.quantile(draws[m], 0.05), "ci_high": np.quantile(draws[m], 0.95),
                 "n_weeks": self.counts_[m], "pooled_only": self.counts_[m] < MIN_WEEKS} for m in sorted(groups)]
        rows.append({"market": "POOLED", "beta": self.pool_, "ci_low": np.quantile(pools, 0.05), "ci_high": np.quantile(pools, 0.95),
                     "n_weeks": int(sum(self.counts_.values())), "pooled_only": True})
        return pd.DataFrame(rows)


def choose_ridge(weekly: pd.DataFrame, folds: list) -> pd.DataFrame:
    """Mean absolute error of y - beta x on each fold's test weeks (centred trends over all weeks up to
    the cut), per ridge, pooled over the folds."""
    dev = deviations(weekly)
    rows = []
    for ridge in RIDGES:
        errors = []
        for fold in folds:
            model = ShortRun(ridge).fit(weekly[weekly["week_start"] + pd.Timedelta(days=6) < fold.train_end])
            test = dev[(dev["week_start"] >= fold.test_start) & (dev["week_start"] + pd.Timedelta(days=6) <= fold.test_end)]
            errors.append(np.abs(test["y"] - model.response(test["market"], test["x"].to_numpy())))
        rows.append({"ridge": ridge, "MAE": float(np.concatenate(errors).mean())})
    return pd.DataFrame(rows)


def co_movement(weekly: pd.DataFrame, seed: int = 0) -> pd.DataFrame:
    """Association of the guest trend with the seat trend: slope of the 52-week change in log centred
    guest trend on that of the seat trend, per market and pooled (market means removed), with a 90%
    moving-block bootstrap interval in blocks of 13 weeks."""
    frame = weekly[["market", "week_start", "seats", "guests"]].sort_values(["market", "week_start"]).reset_index(drop=True)
    frame["ts"], frame["tg"] = np.log(data.centred_trend(frame, "seats")), np.log(data.centred_trend(frame, "guests"))
    earlier = frame[["market", "week_start", "ts", "tg"]].assign(week_start=frame["week_start"] + pd.Timedelta(days=364))
    joined = frame.merge(earlier, on=["market", "week_start"], suffixes=("", "_ly"))
    joined = joined.assign(zs=joined["ts"] - joined["ts_ly"], zg=joined["tg"] - joined["tg_ly"]).dropna(subset=["zs", "zg"])
    joined = joined[np.isfinite(joined["zs"]) & np.isfinite(joined["zg"])]
    rng = np.random.default_rng(seed)

    def slope(g):
        sxx, sxy = _moments(g["zs"].to_numpy(), g["zg"].to_numpy())
        return sxy / sxx if sxx > 0 else np.nan

    def interval(g):
        n, block = len(g), 13
        values = []
        for _ in range(N_BOOT):
            starts = rng.integers(0, max(n - block, 0) + 1, size=int(np.ceil(n / block)))
            idx = (starts[:, None] + np.arange(block)).ravel()[:n]
            values.append(slope(g.iloc[idx[idx < n]]))
        return np.nanquantile(values, [0.05, 0.95])

    rows = []
    for m, g in joined.groupby("market"):
        g = g.sort_values("week_start")
        low, high = interval(g)
        rows.append({"market": m, "slope": slope(g), "ci_low": low, "ci_high": high, "n_weeks": len(g), "sd seat-trend change": g["zs"].std()})
    demeaned = joined.assign(zs=joined["zs"] - joined.groupby("market")["zs"].transform("mean"),
                             zg=joined["zg"] - joined.groupby("market")["zg"].transform("mean")).sort_values("week_start")
    by_week = [g for _, g in demeaned.groupby("week_start")]
    values = []
    for _ in range(N_BOOT):
        starts = rng.integers(0, max(len(by_week) - 13, 0) + 1, size=int(np.ceil(len(by_week) / 13)))
        idx = (starts[:, None] + np.arange(13)).ravel()[:len(by_week)]
        values.append(slope(pd.concat([by_week[i] for i in idx if i < len(by_week)])))
    low, high = np.nanquantile(values, [0.05, 0.95])
    rows.append({"market": "POOLED", "slope": slope(demeaned), "ci_low": low, "ci_high": high, "n_weeks": len(demeaned),
                 "sd seat-trend change": demeaned["zs"].std()})
    return pd.DataFrame(rows)
