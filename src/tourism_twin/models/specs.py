"""Named model specs: each name maps to a factory returning an unfitted Model.

An ablation is another entry with one component removed; no code change elsewhere.
"""

from __future__ import annotations

from typing import Callable, Dict

from tourism_twin.models.baselines import CalendarRidge, LegacyHybrid, RealizedChain, SeasonalPrior, StructuralPlanning
from tourism_twin.models.protocol import Model

# Weekly specs: run on the weekly market panel (date column "week_start").
WEEKLY_SPECS: Dict[str, Callable[[], Model]] = {
    "seasonal_prior": SeasonalPrior,
    "calendar_ridge": CalendarRidge,
    "structural_planning": StructuralPlanning,
    "hybrid_legacy": LegacyHybrid,
    "realized_chain": RealizedChain,
}

MODEL_SPECS: Dict[str, Callable[[], Model]] = {**WEEKLY_SPECS}
