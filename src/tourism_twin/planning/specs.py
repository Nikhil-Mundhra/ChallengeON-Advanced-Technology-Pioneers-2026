"""Named planning specs: weekly specs map a name to a factory returning an unfitted Model run on the
weekly market panel (date column "week_start"); chain specs declare the daily seats -> arrivals ->
guests chain (planning/chain.py) on the daily panel (date column "date")."""

from __future__ import annotations

from dataclasses import replace
from typing import Callable, Dict

from tourism_twin.models.handler import flagged, not_flagged
from tourism_twin.models.protocol import Model
from tourism_twin.models.spec import ModelSpec
from tourism_twin.planning.baselines import (
    CalendarRidge,
    LegacyHybrid,
    RealizedChain,
    SeasonalPrior,
    StructuralPlanning,
)
from tourism_twin.planning.chain import ChainSpec

WEEKLY_SPECS: Dict[str, Callable[[], Model]] = {
    "seasonal_prior": SeasonalPrior,
    "calendar_ridge": CalendarRidge,
    "structural_planning": StructuralPlanning,
    "hybrid_legacy": LegacyHybrid,
    "hybrid_calendar_only": lambda: LegacyHybrid(events=()),
}

# Diagnostics that read realized test-period data (oracle covariates); never rank them with
# planning or nowcast models.
DIAGNOSTIC_SPECS: Dict[str, Callable[[], Model]] = {
    "realized_chain": RealizedChain,
}

# Daily planning chain (planning/chain.py): seats -> hotel new arrivals -> guests, international
# markets only (DOMESTIC has no flights and keeps its weekly model). Each link is a ModelSpec.
_BACKFIT = ("backfitting", {"max_iter": 200, "tol": 1e-6})
_SEASON = ("annual_fourier", {"harmonics": 4})
_ONE_OFF = not_flagged("is_one_off_period")

# Link 2 has the component list, fitter and row rules of the shipped international guests nowcast
# (nowcast/specs.py INTL_NOWCAST). It is declared again here because planning never imports
# nowcast; change both together.
GUESTS_LINK = ModelSpec(components=(("arrivals_kernel", {"max_lag": 21, "base": "knots"}), _SEASON, "weekday", "events"),
                        fitter=_BACKFIT, rules=(_ONE_OFF, flagged("lag_complete")))
# Link 1: the market's own scheduled seats over 8 days (lags 0..7) through the same constrained kernel,
# plus the guests link's calendar; smearing turns the log fit's median into a mean.
SEATS_LINK = ModelSpec(components=(("seat_kernel", {"max_lag": 7}), _SEASON, "weekday", "events"),
                       fitter=_BACKFIT, rules=(_ONE_OFF, flagged("seat_lag_complete")),
                       options=(("target", "new_arrivals_filled"), ("bias_correction", "smearing")))

# Shipped chain (VALIDATION_ORIGINS, international, 7 folds). Structure is taught, values are learned:
# - link 1 sum(w) <= P2P passengers / seats of the market's training rows (a physical bound measured
#   from data; binds for China, the Americas/Africa and Asia-Pacific clusters, Russia, the US);
# - each market's base share is shrunk toward the median base share of the unpooled fits (learned per
#   fit); the strength 0.01 was best of {0.01, 0.1, 1} (weekly market-week WAPE 20.09 / 20.23 / 20.33);
# - link 2 is trained on link 1's in-sample arrivals (what it reads in prediction), smearing on both.
# Against the prototype (seat_chain_prototype): daily -1.30 pp [-1.74, -0.83], 7/7 folds; against
# LegacyHybrid weekly: -4.81 pp [-6.10, -3.64], 7/7 folds; level bias -9.2% (prototype -11.2%).
SEAT_CHAIN = ChainSpec(
    SEATS_LINK.replace_component("seat_kernel", ("seat_kernel", {"max_lag": 7, "cap_factor": 1.0})),
    replace(GUESTS_LINK, options=(("bias_correction", "smearing"),)),
    guests_trained_on="predicted", pooled_share_ridge=0.01)

CHAIN_SPECS: Dict[str, ChainSpec] = {
    "seat_chain_prototype": ChainSpec(SEATS_LINK, GUESTS_LINK),
    "seat_chain": SEAT_CHAIN,
}
