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


def intl_nowcast(gbm: bool = False, base: str = "knots", events: bool = True) -> AdditiveLogModel:
    """International nowcast (docs/model_design.md §3, §4.6): arrivals kernel (owns the level) +
    season + weekday + events, no trend (+ residual GBM, gated). Every block minimises the same
    log-scale objective, so backfitting descends and converges; results do not depend on the pass cap."""
    components = [ArrivalsConvolution(max_lag=21, base=base), AnnualFourier(4), DayOfWeek(), *([EventKernel()] if events else [])]
    if gbm:
        components.append(ResidualGBM(GBM_FEATURES))
    return AdditiveLogModel(components, fitter=Backfitting(max_iter=BACKFIT_MAX_ITER, tol=BACKFIT_TOL),
                            exclude_flag="is_one_off_period", include_flag="lag_complete")


def domestic_nowcast(base: str = "knots") -> AdditiveLogModel:
    """Domestic nowcast (docs/model_design.md §3, §4.6): arrivals kernel (owns the level) + centred
    log-slope + season + weekday; no event kernels. Weekday × season beat plain weekday by only 0.07 pp
    daily WAPE on 13 rolling origins (scripts/compare_domestic_weekday.py), under the 0.3 pp gate, so
    the simpler one ships."""
    components = [ArrivalsConvolution(max_lag=21, base=base), CentredSlope(), AnnualFourier(4), DayOfWeek()]
    return AdditiveLogModel(components, fitter=Backfitting(max_iter=BACKFIT_MAX_ITER, tol=BACKFIT_TOL),
                            exclude_flag="is_one_off_period", include_flag="lag_complete")


def domestic_time() -> AdditiveLogModel:
    """Domestic time-only model for when arrivals are unknown (planning): local level (flat
    beyond the training days) + season + weekday by season + events; all linear, so one exact
    joint solve."""
    components = [LocalLevel(), AnnualFourier(4), DayOfWeek(by_season=True), EventKernel()]
    return AdditiveLogModel(components, fitter=JointLinear(), exclude_flag="is_one_off_period")


def intl_time() -> AdditiveLogModel:
    """International time-only model (no arrivals): local level + season + weekday + events; the
    counterpart of domestic_time and the "time" row of the block ablation."""
    components = [LocalLevel(), AnnualFourier(4), DayOfWeek(), EventKernel()]
    return AdditiveLogModel(components, fitter=JointLinear(), exclude_flag="is_one_off_period")


def flow_only() -> AdditiveLogModel:
    """The arrivals kernel alone: the "flow" row of the block ablation."""
    return AdditiveLogModel([ArrivalsConvolution(max_lag=21)], fitter=Backfitting(max_iter=BACKFIT_MAX_ITER, tol=BACKFIT_TOL),
                            exclude_flag="is_one_off_period", include_flag="lag_complete")


# Block ablation (docs/model_design.md §3.1): time only, flow only, flow + time, and twin_daily
# (flow + time + holiday; domestic has no holiday block, so its last two rows coincide).
BLOCK_ABLATION = ("naive_364", "time_only", "flow_only", "flow_time", "twin_daily")

# Gated ablations (8 monthly origins 2024-07..2025-02, 6-month horizon, mean fold WMAPE):
# twin_daily_gbm adds the residual GBM: international 9.09 vs 9.42, domestic unchanged, so it fails
# the >= 0.3 pp-on-both rule. twin_daily_base90 ties the base stock to trailing 90-day arrivals (to
# follow a carrier exit): domestic 11.23 vs 6.49, international 13.39 vs 9.42, so it is not shipped;
# the knot base already follows a 0.55x arrival shock in the Wizz markets within 1.5%.
DAILY_SPECS: Dict[str, Callable[[], Model]] = {
    "naive_364": SeasonalNaive,
    "arrivals_ratio": ArrivalsRatio,
    "twin_daily": lambda: MarketRouter(domestic_nowcast, lambda: intl_nowcast(gbm=False)),
    "twin_daily_gbm": lambda: MarketRouter(domestic_nowcast, lambda: intl_nowcast(gbm=True)),
    "twin_daily_base90": lambda: MarketRouter(lambda: domestic_nowcast(base="arrivals"), lambda: intl_nowcast(base="arrivals")),
    "domestic_time": domestic_time,
    "time_only": lambda: MarketRouter(domestic_time, intl_time),
    "flow_only": lambda: MarketRouter(flow_only, flow_only),
    "flow_time": lambda: MarketRouter(domestic_nowcast, lambda: intl_nowcast(events=False)),
}
