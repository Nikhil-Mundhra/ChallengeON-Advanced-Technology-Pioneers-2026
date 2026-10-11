"""SeatKernel: new hotel arrivals as the flow fed by scheduled seats (planning chain, link 1).

    arrivals_t = c_t + sum_{k=0..K} w_k * Seats_{t-k},   contribution = log(arrivals_t)

Same constrained kernel as ArrivalsConvolution (models/components/convolution.py): w_k >= 0,
non-increasing, w_0 <= 1, a non-negative knot base c_t that is flat beyond the training days. The
input is the market's own daily scheduled seats (seats_lag_k, feature `seat_lags`), so the share of
arrivals carried by the kernel is the arrivals' elasticity to seats, and sum(w) is arrivals per seat
in steady state: a fitting quantity, not a conversion rate measured on passengers.

cap_factor bounds sum(w) by cap_factor x (P2P passengers / seats) over the fit's training rows
(load factor x point-to-point share, a ratio of summed parts): arrivals per seat cannot exceed
the passengers per seat who end their trip at the airport. Departure country is not nationality, so
the bound is approximate; markets that arrive through hubs (China) bind first.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

from tourism_twin.features.lags import seat_lag_column
from tourism_twin.models.components.convolution import ConvolutionKernel


class SeatKernel(ConvolutionKernel):
    def __init__(self, max_lag: int = 7, knot_days: int = 365, base_smoothing: float = 1.0, name: str = "seats",
                 date_column: str = "date", cap_factor: Optional[float] = None,
                 share_target: Optional[float] = None, share_ridge: float = 0.0) -> None:
        self.cap_factor = cap_factor
        super().__init__([seat_lag_column(k) for k in range(max_lag + 1)], knot_days=knot_days, base_smoothing=base_smoothing,
                         name=name, date_column=date_column, extra_requires=("p2p", "seats") if cap_factor is not None else (),
                         share_target=share_target, share_ridge=share_ridge)

    def kernel_cap(self, panel: pd.DataFrame) -> Optional[float]:
        if self.cap_factor is None:
            return None
        seats = float(panel["seats"].sum())
        return self.cap_factor * float(panel["p2p"].sum()) / seats if seats > 0 else None

    def explain(self) -> Dict[str, Any]:
        out = super().explain()
        return {**out, "kernel_sum": float(sum(out["survival_w"])), "kernel_cap": self.cap_, "cap_binds": self.cap_binds_}
