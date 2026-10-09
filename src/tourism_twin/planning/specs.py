"""Named weekly planning specs: each name maps to a factory returning an unfitted Model run on the
weekly market panel (date column "week_start")."""

from __future__ import annotations

from typing import Callable, Dict

from tourism_twin.models.protocol import Model
from tourism_twin.planning.baselines import (
    CalendarRidge,
    LegacyHybrid,
    RealizedChain,
    SeasonalPrior,
    StructuralPlanning,
)

WEEKLY_SPECS: Dict[str, Callable[[], Model]] = {
    "seasonal_prior": SeasonalPrior,
    "calendar_ridge": CalendarRidge,
    "structural_planning": StructuralPlanning,
    "hybrid_legacy": LegacyHybrid,
}

# Diagnostics that read realized test-period data (oracle covariates); never rank them with
# planning or nowcast models.
DIAGNOSTIC_SPECS: Dict[str, Callable[[], Model]] = {
    "realized_chain": RealizedChain,
}
