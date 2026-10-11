"""PassengerChain: seats -> P2P passengers (link 0) -> new arrivals (link 1) -> guests (link 2).

Links 1 and 2 are the shipped SeatChain (src/tourism_twin/planning/chain.py) fed predicted P2P in the
`seats` column. Its kernel cap, cap_factor x P2P / seats of the training rows, then becomes
cap_factor x 1: at most one hotel arrival per P2P passenger, the same physical bound as the shipped
arrivals-per-seat <= P2P-per-seat cap. Link 1 trains on link 0's in-sample P2P, the input it reads in
prediction (the shipped chain does the same for link 2).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from tourism_twin.domain.markets import DOMESTIC
from tourism_twin.planning.chain import ChainSpec, SeatChain


class PassengerChain:
    def __init__(self, passengers: Any, spec: ChainSpec) -> None:
        self.passengers = passengers
        self.spec = spec

    def _fed(self, frame: pd.DataFrame, p2p: pd.Series) -> pd.DataFrame:
        return frame.assign(seats=p2p.to_numpy(), p2p=p2p.to_numpy())

    def fit(self, panel: pd.DataFrame) -> "PassengerChain":
        rows = panel[panel["market"] != DOMESTIC]
        self.passengers.fit(rows)
        self.chain_ = SeatChain(self.spec).fit(self._fed(rows, self.passengers.predict(rows)))
        return self

    def predict_frame(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Daily `p2p`, `arrivals` and `guests` per row of `frame` (NaN in lag warm-ups and for DOMESTIC)."""
        rows = frame[frame["market"] != DOMESTIC]
        p2p = self.passengers.predict(rows)
        out = self.chain_.predict_frame(self._fed(rows, p2p)).reindex(frame.index)
        out.insert(0, "p2p", p2p.reindex(frame.index))
        return out

    def explain(self) -> dict:
        return self.chain_.explain()


class BaseChain:
    """The shipped chain, with the same predict_frame columns (its `p2p` is NaN: it has no link 0)."""

    def __init__(self, spec: ChainSpec) -> None:
        self.spec = spec

    def fit(self, panel: pd.DataFrame) -> "BaseChain":
        self.chain_ = SeatChain(self.spec).fit(panel)
        return self

    def predict_frame(self, frame: pd.DataFrame) -> pd.DataFrame:
        out = self.chain_.predict_frame(frame)
        out.insert(0, "p2p", np.nan)
        return out

    def explain(self) -> dict:
        return self.chain_.explain()


def scenario(model: Any, frame: pd.DataFrame, market: str, start: str, end: str, seat_change: float,
             via: str = "gauge") -> pd.DataFrame:
    """Baseline and scenario daily seats, P2P, arrivals and guests for `market` with seats scaled by
    1 + seat_change on start..end, delivered as bigger aircraft (`via="gauge"`, flights unchanged) or
    as more flights (`via="flights"`, same gauge). P2P follows from link 0; only C reads the split."""
    if via not in ("gauge", "flights"):
        raise ValueError("via must be 'gauge' or 'flights'")
    rows = frame[frame["market"] == market]
    window = (rows["date"] >= pd.Timestamp(start)) & (rows["date"] <= pd.Timestamp(end))
    factor = np.where(window, 1.0 + seat_change, 1.0)
    changed = rows.assign(seats=rows["seats"] * factor)
    if via == "flights":
        changed = changed.assign(flights=rows["flights"] * factor, premium_seats=rows["premium_seats"] * factor)
    else:
        changed = changed.assign(premium_seats=rows["premium_seats"] * factor)
    base, alt = model.predict_frame(rows), model.predict_frame(changed)
    out = pd.DataFrame({"date": rows["date"], "in_window": window, "seats": rows["seats"], "scenario_seats": changed["seats"]})
    for column in ("p2p", "arrivals", "guests"):
        out[column], out[f"scenario_{column}"] = base[column], alt[column]
    return out
