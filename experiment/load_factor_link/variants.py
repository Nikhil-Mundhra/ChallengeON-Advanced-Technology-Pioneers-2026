"""The compared chains. Each builds an unfitted model with fit(panel) and predict_frame(frame)."""

from __future__ import annotations

from typing import Any, Callable, Dict

from tourism_twin.planning.specs import CHAIN_SPECS

from passenger_chain import BaseChain, PassengerChain
from passengers_link import LogitLoadFactor, RealizedP2P, ScheduleInputs, TrendResponse, UCurve

SEAT_CHAIN = CHAIN_SPECS["seat_chain"]
# Link-0 settings chosen on VALIDATION_ORIGINS by link-0 P2P WAPE alone (no chain refits): knots every
# 365 days beat 182 and 60; pool 0.3 beat 0 (see README.md).
LINK0 = {"knot_days": 365, "pool": 0.3}

VARIANTS: Dict[str, Callable[[], Any]] = {
    "BASE": lambda: BaseChain(SEAT_CHAIN),
    "A": lambda: PassengerChain(TrendResponse(**LINK0), SEAT_CHAIN),
    "A_updown": lambda: PassengerChain(TrendResponse(slopes="split", **LINK0), SEAT_CHAIN),
    "A2": lambda: PassengerChain(TrendResponse(slopes="usual_lf", **LINK0), SEAT_CHAIN),
    "L": lambda: PassengerChain(LogitLoadFactor(**LINK0), SEAT_CHAIN),
    # Two-speed seats on A (A's link 0 beat L's on P2P WAPE): beta on the deviation, beta_long on the trend.
    "TS": lambda: PassengerChain(TrendResponse(long_run=True, **LINK0), SEAT_CHAIN),
    "B": lambda: PassengerChain(UCurve(), SEAT_CHAIN),
    "C": lambda: PassengerChain(ScheduleInputs(**LINK0), SEAT_CHAIN),
    # Diagnostic upper bound: realized P2P of the predicted period. Not deployable; never ranked.
    "A_oracle": lambda: PassengerChain(RealizedP2P(), SEAT_CHAIN),
}
DIAGNOSTIC = ("A_oracle",)
