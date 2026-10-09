"""Named model specs: each name maps to a factory returning an unfitted Model.

An ablation is another entry with one component removed; no code change elsewhere.
Weekly specs run on the weekly market panel (date column "week_start"); daily specs on the
daily panel (date column "date").
"""

from __future__ import annotations

from typing import Callable, Dict

from tourism_twin.features.lags import lag_column
from tourism_twin.models.baselines import (
    CalendarRidge,
    LegacyHybrid,
    MarketRouter,
    RealizedChain,
    SeasonalNaive,
    SeasonalPrior,
    StructuralPlanning,
)
from tourism_twin.models.components import AnnualFourier, ArrivalsConvolution, DayOfWeek, EventKernel, LocalLevel, ResidualGBM
from tourism_twin.models.composite import AdditiveLogModel
from tourism_twin.models.fitters import Backfitting, JointLinear
from tourism_twin.models.protocol import Model

WEEKLY_SPECS: Dict[str, Callable[[], Model]] = {
    "seasonal_prior": SeasonalPrior,
    "calendar_ridge": CalendarRidge,
    "structural_planning": StructuralPlanning,
    "hybrid_legacy": LegacyHybrid,
    "realized_chain": RealizedChain,
}

GBM_FEATURES = ("dow", "month", "iso_week", "is_holiday_week", lag_column(0), lag_column(7))


def intl_nowcast(gbm: bool = False) -> AdditiveLogModel:
    """International: arrivals kernel (owns the level) + season + weekday + events (+ residual GBM).

    Backfitting is capped at 20 passes: the kernel's constrained solve jitters by ~1e-2 between
    passes while out-of-sample error stays flat (UK 2024-07 fold: 5.0% at 5 to 100 passes)."""
    components = [ArrivalsConvolution(max_lag=21), AnnualFourier(4), DayOfWeek(), EventKernel()]
    if gbm:
        components.append(ResidualGBM(GBM_FEATURES))
    return AdditiveLogModel(components, fitter=Backfitting(max_iter=20, tol=1e-3),
                            exclude_flag="is_one_off_period", include_flag="lag_complete")


def domestic_time() -> AdditiveLogModel:
    """Domestic: local level + season + weekday by season + events (no arrivals); all linear, so
    one exact joint solve."""
    components = [LocalLevel(), AnnualFourier(4), DayOfWeek(by_season=True), EventKernel()]
    return AdditiveLogModel(components, fitter=JointLinear(), exclude_flag="is_one_off_period")


# twin_daily_gbm is the gated ablation: the residual GBM is kept only if it improves back-test WMAPE
# by >= 0.3 pp on both domestic and international. Rolling-origin result (8 monthly origins,
# 6-month horizon): +0.14 pp international, 0 domestic, so twin_daily ships without it.
DAILY_SPECS: Dict[str, Callable[[], Model]] = {
    "naive_364": SeasonalNaive,
    "twin_daily": lambda: MarketRouter(domestic_time, lambda: intl_nowcast(gbm=False)),
    "twin_daily_gbm": lambda: MarketRouter(domestic_time, lambda: intl_nowcast(gbm=True)),
}

MODEL_SPECS: Dict[str, Callable[[], Model]] = {**WEEKLY_SPECS, **DAILY_SPECS}
