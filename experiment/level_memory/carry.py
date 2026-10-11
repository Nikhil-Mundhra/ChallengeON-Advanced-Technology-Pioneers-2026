"""Error carry-forward (experiment 1): forecast = model x exp(e_0 rho^h [+ weekday echo]).

e_0 is the mean log(actual / model) over the last k known days per market, measured in-sample (the
fit that is scored) or on a held-back block (a fit that ends 28 days earlier, scored on those 28 days).
h counts days since the last known day. Every input is from rows before the fold's training end.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np
import pandas as pd

import data

KS = (7, 14, 28)
E0_SOURCES = ("in", "hb")
RHO_SOURCES = ("mkt", "pool", "hb", "one")
MAX_RHO = 0.995


@dataclass(frozen=True)
class Setting:
    k: int
    e0: str             # "in": the scored fit's in-sample residuals; "hb": the held-back fit's errors
    rho: str            # "mkt", "pool" (training residual lag-1 ACF), "hb" (held-back errors), "one", "wk" (weekly)
    echo: bool = False  # add the weekday deviation of the last k days, decaying at the excess lag-7 ACF

    @property
    def name(self) -> str:
        return f"cf_k{self.k}_{self.e0}_{self.rho}{'_echo' if self.echo else ''}"


def grid(weekly: bool) -> list:
    settings = [Setting(k, e0, rho, echo) for k in KS for e0 in E0_SOURCES for rho in RHO_SOURCES for echo in (False, True)]
    return settings + ([Setting(k, e0, "wk") for k in KS for e0 in E0_SOURCES] if weekly else [])


def residuals(panel: pd.DataFrame, pred: pd.Series, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """log(actual / pred) on training-type rows with start <= date < end, with market, date, actual, pred."""
    rows = panel[data.training_rows(panel) & (panel["date"] >= start) & (panel["date"] < end)]
    rows = rows.loc[rows.index.intersection(pred.index)]
    out = rows[["market", "date", "guests"]].rename(columns={"guests": "actual"}).assign(pred=pred.reindex(rows.index))
    return out.assign(e=np.log(out["actual"] / out["pred"]))


def _lag_pairs(frame: pd.DataFrame, lag: int) -> pd.DataFrame:
    keyed = frame.set_index(["market", "date"])["e"]
    shifted = frame.assign(date=frame["date"] + pd.Timedelta(days=lag)).set_index(["market", "date"])["e"]
    pairs = pd.DataFrame({"e": keyed, "prev": shifted.reindex(keyed.index)}).dropna()
    return pairs.reset_index()


def acf(frame: pd.DataFrame, lag: int, by_market: bool) -> pd.Series | float:
    """Uncentred lag ACF (as models/noise.py), per market or pooled, clipped to [0, MAX_RHO]."""
    pairs = _lag_pairs(frame, lag)
    ratio = lambda p: float(np.clip((p["e"] @ p["prev"]) / (p["prev"] @ p["prev"]), 0.0, MAX_RHO))  # noqa: E731
    return pairs.groupby("market").apply(ratio) if by_market else ratio(pairs)


def weekly_acf(frame: pd.DataFrame) -> float:
    """Pooled lag-1 ACF of log(weekly actual / weekly pred) over complete weeks."""
    weeks = frame.assign(week=data.week_start(frame["date"])).groupby(["market", "week"])
    sums = weeks[["actual", "pred"]].sum()[weeks.size() == 7].reset_index()
    weekly = pd.DataFrame({"market": sums["market"], "date": sums["week"], "e": np.log(sums["actual"] / sums["pred"])})
    return acf(weekly, 7, by_market=False)


@dataclass
class Memory:
    """What carry-forward needs per fold and series, measured once."""

    last_known: pd.Timestamp
    recent: Dict[str, pd.DataFrame]  # e0 source -> residuals of the last 28 known days
    rho_mkt: pd.Series
    rho_pool: float
    rho_hb: float
    rho_wk: float
    echo_rho: float


def memory(panel: pd.DataFrame, window: data.Window, pred: pd.Series, held_back_pred: pd.Series) -> Memory:
    end = window.fold.train_end
    block_start = end - pd.Timedelta(days=data.HELD_BACK_DAYS)
    training = residuals(panel, pred, pd.Timestamp("2000-01-01"), end)
    held_back = residuals(panel, held_back_pred, block_start, end)
    rho_pool = acf(training, 1, by_market=False)
    return Memory(window.last_known, {"in": training[training["date"] >= block_start], "hb": held_back},
                  acf(training, 1, by_market=True), rho_pool, acf(held_back, 1, by_market=False), weekly_acf(training),
                  max(acf(training, 7, by_market=False) - rho_pool ** 7, 0.0))


def adjust(test: pd.DataFrame, mem: Memory, setting: Setting) -> np.ndarray:
    """Log adjustment for each test row (market, date)."""
    recent = mem.recent[setting.e0]
    recent = recent[recent["date"] > mem.last_known - pd.Timedelta(days=setting.k)]
    if setting.rho == "wk":
        sums = recent.groupby("market")[["actual", "pred"]].sum()
        e0 = np.log(sums["actual"] / sums["pred"])
    else:
        e0 = recent.groupby("market")["e"].mean()
    rho: Optional[pd.Series | float] = {"mkt": mem.rho_mkt, "pool": mem.rho_pool, "hb": mem.rho_hb, "one": 1.0,
                                        "wk": mem.rho_wk ** (1 / 7)}[setting.rho]
    h = (test["date"] - mem.last_known).dt.days.to_numpy()
    rho_rows = test["market"].map(rho).to_numpy(dtype=float) if isinstance(rho, pd.Series) else np.full(len(test), rho)
    out = test["market"].map(e0).fillna(0.0).to_numpy() * rho_rows ** h
    if setting.echo:
        by_weekday = recent.groupby(["market", recent["date"].dt.weekday])["e"].mean()
        deviation = by_weekday - e0.reindex(by_weekday.index.get_level_values(0)).to_numpy()
        keys = pd.MultiIndex.from_arrays([test["market"], test["date"].dt.weekday])
        out = out + deviation.reindex(keys).fillna(0.0).to_numpy() * mem.echo_rho ** (h / 7)
    return out
