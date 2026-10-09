"""Business outputs derived from the guest model (stock-flow plan step 8), as one JSON document.

Per market and test week: forecast, p10/p90, direction to the next week with a probability,
year-on-year change, and the calendar drivers.
Narration (briefings, LLM text) reads this document only and never computes numbers.

Weekly sums, bounds and directions: nowcast/weekly.py (AR(1) daily errors, NoiseModel); the
direction back-test: nowcast/evaluation.py.
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd

from tourism_twin.features.calendar import week_monday
from tourism_twin.nowcast.evaluation import direction_backtest
from tourism_twin.nowcast.predict import TestPredictions
from tourism_twin.nowcast.weekly import weekly_forecast

DRIVER_BLOCKS = ("time", "holiday", "flight", "residual")  # every block except the flow (the level)
ASSUMPTIONS = [
    "Direction accuracy is a nowcast skill: the model sees each week's observed new arrivals; compare it with arrivals_direction.",
    "Weekly p10/p90 and direction_prob come from AR(1) daily log errors (per-market phi) fitted on the rolling-origin back-test.",
    "top_drivers are model blocks other than the arrivals flow (time: season, weekday and the slope held at its "
    "last training value; holiday: events), as % against the training average or an ordinary day.",
]


def build_outputs(predictions: TestPredictions, history: pd.DataFrame, spec: str, coverage: float = 0.8) -> Dict[str, Any]:
    """The JSON document: assumptions, the direction back-test, and per-market weekly outputs.
    history: the daily training panel (guests, new_arrivals_filled)."""
    if predictions.noise is None:
        raise ValueError("build_outputs needs predictions with intervals (a fitted noise model)")
    weekly = weekly_forecast(predictions.market_daily, predictions.noise, coverage)
    actual_weekly = (history.assign(week_start=week_monday(history["date"]))
                     .groupby(["market", "week_start"])["guests"].sum(min_count=7))
    markets: Dict[str, Any] = {}
    for market, rows in weekly.groupby("market"):
        markets[market] = {"weeks": [
            {
                "week_start": str(record.week_start.date()),
                "forecast": round(float(record.forecast), 1),
                "p10": round(float(record.p10), 1) if np.isfinite(record.p10) else None,
                "p90": round(float(record.p90), 1) if np.isfinite(record.p90) else None,
                "direction": record.direction,
                "direction_prob": round(float(record.direction_prob), 3) if np.isfinite(record.direction_prob) else None,
                "yoy_change": _yoy(record.forecast, actual_weekly.get((market, record.week_start - pd.Timedelta(364, unit="D")), np.nan)),
            }
            for record in rows.itertuples()
        ]}
    _attach_drivers(markets, predictions)
    document: Dict[str, Any] = {"spec": spec, "coverage": coverage, "assumptions": ASSUMPTIONS, "markets": markets}
    if predictions.backtest_predictions is not None:
        document["direction_backtest"] = direction_backtest(predictions.backtest_predictions, history, predictions.noise, coverage)
    return document


def _yoy(forecast: float, last_year: float) -> float | None:
    return round(float(forecast / last_year - 1), 4) if np.isfinite(last_year) and last_year > 0 else None


def _attach_drivers(markets: Dict[str, Any], predictions: TestPredictions, top: int = 3) -> None:
    """Per week: each block's mean log contribution over the week, as %, largest first (blocks
    under 0.5% omitted)."""
    model, test = predictions.model, predictions.test_panel
    if model is None or test is None or not hasattr(model, "decompose_by_group"):
        return
    blocks = model.decompose_by_group(test)
    blocks = blocks[[c for c in blocks.columns if c in DRIVER_BLOCKS]]
    weekly = blocks.assign(market=test["market"].to_numpy(), week_start=week_monday(test["date"]).to_numpy()).groupby(["market", "week_start"]).mean()
    for market, detail in markets.items():
        for week in detail["weeks"]:
            key = (market, pd.Timestamp(week["week_start"]))
            effects = weekly.loc[key].dropna() if key in weekly.index else pd.Series(dtype=float)
            effects = effects[np.abs(np.expm1(effects)) >= 0.005]
            ranked = effects.reindex(effects.abs().sort_values(ascending=False).index)[:top]
            week["top_drivers"] = [{"block": name, "effect_pct": round(float(np.expm1(value)) * 100, 1)} for name, value in ranked.items()]
