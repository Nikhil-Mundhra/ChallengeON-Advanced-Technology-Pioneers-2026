"""The fitted models: the shipped nowcast and chain, the time-only control and the drift grid.
Each factory returns an unfitted model with fit(panel) and predict(frame)."""

from __future__ import annotations

from typing import Any, Callable, Dict

from tourism_twin.nowcast.routing import MarketRouter
from tourism_twin.nowcast.specs import DOMESTIC_NOWCAST, DOMESTIC_TIME, INTL_NOWCAST, INTL_TIME
from tourism_twin.planning.chain import SeatChain
from tourism_twin.planning.specs import CHAIN_SPECS

from drift import NAME as DRIFT


def _drifting(spec, knot_days: int, drift_knot_days: int, drift_lambda: float):
    return spec.replace_component("arrivals_kernel", (DRIFT, {"max_lag": 21, "knot_days": knot_days,
                                                              "drift_knot_days": drift_knot_days, "drift_lambda": drift_lambda}))


def drift_model(drift_knot_days: int, drift_lambda: float) -> MarketRouter:
    """twin_daily with both kernels drifting; domestic keeps its 365-day base knots, international 45."""
    return MarketRouter(_drifting(DOMESTIC_NOWCAST, 365, drift_knot_days, drift_lambda).build,
                        _drifting(INTL_NOWCAST, 45, drift_knot_days, drift_lambda).build)


DRIFT_KNOTS = (90, 182)
DRIFT_LAMBDAS = (0.01, 0.1, 1.0, 10.0)
DRIFT_HALF_LIVES = (None, 30, 90)  # None: s held at its last value


def drift_name(knots: int, lam: float) -> str:
    return f"drift_k{knots}_l{lam:g}"


MODELS: Dict[str, Callable[[], Any]] = {
    "nowcast": lambda: MarketRouter(DOMESTIC_NOWCAST.build, INTL_NOWCAST.build),
    "time_only": lambda: MarketRouter(DOMESTIC_TIME.build, INTL_TIME.build),
    "chain": lambda: SeatChain(CHAIN_SPECS["seat_chain"]),
    **{drift_name(k, lam): (lambda k=k, lam=lam: drift_model(k, lam)) for k in DRIFT_KNOTS for lam in DRIFT_LAMBDAS},
}
