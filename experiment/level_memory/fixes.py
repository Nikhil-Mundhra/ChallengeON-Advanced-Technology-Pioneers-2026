"""International fit specs for the Israel follow-up and the held-value rules for s(t) beyond the
training days. Every rule is applied after the fit of the chosen drift (drift_k182_l0.1); the fit
itself is unchanged, so only test days move.

Rules (s_last: the last knot; r: shock.recent_ratio at the fold's training end, last 90 days of
arrivals over the same days a year earlier):
  drift         s_last (the current drift)
  shock_zero    0 when r < 0.5, else s_last: after an arrival collapse, hold the window mean (s is
                mean zero over training). Israel folds 1-6 have r 0.11 to 0.48; every other market-fold
                is at 0.78 or above. Any threshold from 0.36 to 0.78 resets Israel folds 1-5 (the
                only ones with |s_last| above 0.005) and no other market.
  shock_shrink  s_last * min(r, 1): shrink the held value by the size of the collapse
  cap_008       s_last clipped to +-0.08 (a control: graph d does not support a cap; see README)
"""

from __future__ import annotations

from typing import Callable, Dict

import numpy as np

from tourism_twin.nowcast.specs import INTL_NOWCAST

from variants import _drifting

CHOSEN_KNOTS, CHOSEN_LAMBDA = 182, 0.1
SHOCK_RATIO = 0.5
CAP = 0.08  # most markets keep s within +-0.08 (README, identifiability)

FIT_SPECS: Dict[str, Callable] = {
    "shipped": INTL_NOWCAST.build,
    "drift": _drifting(INTL_NOWCAST, 45, CHOSEN_KNOTS, CHOSEN_LAMBDA).build,
}

HOLDS: Dict[str, Callable[[float, float], float]] = {
    "drift": lambda s_last, r: s_last,
    "shock_zero": lambda s_last, r: 0.0 if r < SHOCK_RATIO else s_last,
    "shock_shrink": lambda s_last, r: s_last * min(r, 1.0),
    "cap_008": lambda s_last, r: float(np.clip(s_last, -CAP, CAP)),
}
