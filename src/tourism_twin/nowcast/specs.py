"""Named daily nowcast specs: each name maps to a factory returning an unfitted Model.

An ablation is another entry with one component removed; no code change elsewhere. Daily specs run
on the daily panel (date column "date").
"""

from __future__ import annotations

from typing import Callable, Dict

from tourism_twin.features.lags import lag_column
from tourism_twin.models.handler import flagged, not_flagged, on_or_after
from tourism_twin.models.protocol import Model
from tourism_twin.models.spec import ModelSpec
from tourism_twin.nowcast.baselines import ArrivalsRatio, SeasonalNaive
from tourism_twin.nowcast.routing import MarketRouter


BACKFIT = ("backfitting", {"max_iter": 200, "tol": 1e-6})  # converged fits stop well before the cap
GBM_FEATURES = ("dow", "month", "iso_week", "is_holiday_week", lag_column(0), lag_column(7))

# Training-row rules (models/handler.py): one-off shocks never train; the arrivals kernel needs a
# full lag window.
TIME_ROWS = (not_flagged("is_one_off_period"),)
NOWCAST_ROWS = (not_flagged("is_one_off_period"), flagged("lag_complete"))

KERNEL = ("arrivals_kernel", {"max_lag": 21, "base": "knots"})
KERNEL_BASE90 = ("arrivals_kernel", {"max_lag": 21, "base": "arrivals"})  # base stock tied to 90-day arrivals
SEASON = ("annual_fourier", {"harmonics": 4})
GBM = ("residual_gbm", {"features": GBM_FEATURES})

# Every block minimises the same log-scale objective, so backfitting descends and converges;
# results do not depend on the pass cap.
INTL_NOWCAST = ModelSpec(components=(KERNEL, SEASON, "weekday", "events"), fitter=BACKFIT, rules=NOWCAST_ROWS)
# Weekday x season beat plain weekday by only 0.07 pp daily WAPE on 13 rolling origins
# (scripts/compare_domestic_weekday.py), under the 0.3 pp gate, so the simpler one ships.
# Domestic trains from 2022-07-01: guests per arrival fell 3.55 (2022Q1) -> ~2.5 (2022Q4), a one-off
# post-COVID normalisation the slope would read as trend. Published 8 origins: 4.85 vs 6.23 mean fold WAPE.
DOMESTIC_ROWS = (*NOWCAST_ROWS, on_or_after("date", "2022-07-01"))
DOMESTIC_NOWCAST = ModelSpec(components=(KERNEL, "slope", SEASON, "weekday"), fitter=BACKFIT, rules=DOMESTIC_ROWS)
# Time only (arrivals unknown, planning): local level (flat beyond the training days) + season +
# weekday + events; all linear, so one exact joint solve.
DOMESTIC_TIME = ModelSpec(components=("local_level", SEASON, ("weekday", {"by_season": True}), "events"),
                          fitter="joint_linear", rules=TIME_ROWS)
INTL_TIME = ModelSpec(components=("local_level", SEASON, "weekday", "events"), fitter="joint_linear", rules=TIME_ROWS)
FLOW_ONLY = ModelSpec(components=(KERNEL,), fitter=BACKFIT, rules=NOWCAST_ROWS)

# Nationalities inside the pooled markets (issue #16): one fit per stay family on every
# international nationality's own arrivals, sharing kernel, season, weekday and events, with a
# per-nationality scale shrunk toward the family (GroupScale) and a base stock tied to the
# nationality's 90-day arrivals. Validation (#11 protocol, 7 origins): international nationality
# WAPE 12.24 vs 12.79 for the market model + arrival-share split, -0.55 pp [-0.79, -0.32], 7/7
# folds; frozen test 11.16 vs 11.38, -0.22 pp [-0.45, +0.02].
SHORT_STAY_FAMILY = ("SAUDI ARABIA", "KUWAIT", "OMAN", "BAHRAIN", "QATAR")
POOLED_NATIONALITIES = ModelSpec(
    components=(KERNEL_BASE90, ("group_scale", {"column": "nationality", "ridge": 100.0}), SEASON, "weekday", "events"),
    fitter=BACKFIT, rules=NOWCAST_ROWS, options=(("group_by", "family"),))

# Variants: one spec each, derived from the shipped ones.
INTL_NOWCAST_GBM = INTL_NOWCAST.adding(GBM)
INTL_NOWCAST_BASE90 = INTL_NOWCAST.replace_component("arrivals_kernel", KERNEL_BASE90)
DOMESTIC_NOWCAST_BASE90 = DOMESTIC_NOWCAST.replace_component("arrivals_kernel", KERNEL_BASE90)
INTL_FLOW_TIME = INTL_NOWCAST.without("events")


def routed(domestic: ModelSpec, international: ModelSpec) -> Callable[[], Model]:
    """A factory for MarketRouter over two specs (DOMESTIC rows, every other market)."""
    return lambda: MarketRouter(domestic.build, international.build)


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
    "twin_daily": routed(DOMESTIC_NOWCAST, INTL_NOWCAST),
    "twin_daily_gbm": routed(DOMESTIC_NOWCAST, INTL_NOWCAST_GBM),
    "twin_daily_base90": routed(DOMESTIC_NOWCAST_BASE90, INTL_NOWCAST_BASE90),
    "domestic_time": DOMESTIC_TIME.build,
    "time_only": routed(DOMESTIC_TIME, INTL_TIME),
    "flow_only": routed(FLOW_ONLY, FLOW_ONLY),
    "flow_time": routed(DOMESTIC_NOWCAST, INTL_FLOW_TIME),
}
