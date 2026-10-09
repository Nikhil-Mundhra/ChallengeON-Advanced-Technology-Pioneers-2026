"""Named daily nowcast specs: each name maps to a factory returning an unfitted Model.

An ablation is another entry with one component removed; no code change elsewhere. Daily specs run
on the daily panel (date column "date").
"""

from __future__ import annotations

from typing import Callable, Dict

from tourism_twin.features.lags import lag_column
from tourism_twin.models.components import (
    AnnualFourier,
    ArrivalsConvolution,
    CentredSlope,
    DayOfWeek,
    EventKernel,
    LocalLevel,
    ResidualGBM,
)
from tourism_twin.models.composite import AdditiveLogModel
from tourism_twin.models.fitters import Backfitting, JointLinear
from tourism_twin.models.protocol import Model
from tourism_twin.nowcast.baselines import ArrivalsRatio, SeasonalNaive
from tourism_twin.nowcast.routing import MarketRouter


BACKFIT_MAX_ITER, BACKFIT_TOL = 200, 1e-6  # converged fits stop well before the cap
GBM_FEATURES = ("dow", "month", "iso_week", "is_holiday_week", lag_column(0), lag_column(7))


def intl_nowcast(gbm: bool = False) -> AdditiveLogModel:
    """International nowcast (docs/model_design.md §3, §4.6): arrivals kernel (owns the level) +
    season + weekday + events, no trend (+ residual GBM, gated). Every block minimises the same
    log-scale objective, so backfitting descends and converges; results do not depend on the pass cap."""
    components = [ArrivalsConvolution(max_lag=21), AnnualFourier(4), DayOfWeek(), EventKernel()]
    if gbm:
        components.append(ResidualGBM(GBM_FEATURES))
    return AdditiveLogModel(components, fitter=Backfitting(max_iter=BACKFIT_MAX_ITER, tol=BACKFIT_TOL),
                            exclude_flag="is_one_off_period", include_flag="lag_complete")


def domestic_nowcast() -> AdditiveLogModel:
    """Domestic nowcast (docs/model_design.md §3, §4.6): arrivals kernel (owns the level) + centred
    log-slope + season + weekday; no event kernels. Weekday × season lost to plain weekday by 0.07 pp
    on 13 rolling origins (under the 0.3 pp gate), so the simpler one ships."""
    components = [ArrivalsConvolution(max_lag=21), CentredSlope(), AnnualFourier(4), DayOfWeek()]
    return AdditiveLogModel(components, fitter=Backfitting(max_iter=BACKFIT_MAX_ITER, tol=BACKFIT_TOL),
                            exclude_flag="is_one_off_period", include_flag="lag_complete")


def domestic_time() -> AdditiveLogModel:
    """Domestic time-only model for when arrivals are unknown (planning): local level (flat
    beyond the training days) + season + weekday by season + events; all linear, so one exact
    joint solve."""
    components = [LocalLevel(), AnnualFourier(4), DayOfWeek(by_season=True), EventKernel()]
    return AdditiveLogModel(components, fitter=JointLinear(), exclude_flag="is_one_off_period")


# twin_daily_gbm is the gated ablation: the residual GBM is kept only if it improves back-test WMAPE
# by >= 0.3 pp on both domestic and international. Rolling-origin result (8 monthly origins,
# 6-month horizon): +0.14 pp international, 0 domestic, so twin_daily ships without it.
DAILY_SPECS: Dict[str, Callable[[], Model]] = {
    "naive_364": SeasonalNaive,
    "arrivals_ratio": ArrivalsRatio,
    "twin_daily": lambda: MarketRouter(domestic_nowcast, lambda: intl_nowcast(gbm=False)),
    "twin_daily_gbm": lambda: MarketRouter(domestic_nowcast, lambda: intl_nowcast(gbm=True)),
    "domestic_time": domestic_time,
}
