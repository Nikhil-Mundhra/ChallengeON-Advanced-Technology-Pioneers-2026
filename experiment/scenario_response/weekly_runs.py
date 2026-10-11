"""Weekly predictions of every model on each VALIDATION_ORIGINS fold, for both natural-experiment
references ("yoy": the same week a year earlier; "trend": the centred 13-week seat trend).

Per fold, each model gives `pred` (this week's guests, the observed seat change applied as its lever
on the fold's test weeks; its ordinary prediction on actual seats elsewhere, which the year-earlier
lookups read) and `cf` (its baseline: seats held at the reference) on the test weeks.

  HYBRID     the weekly planning model on actual seats (structural planning_guests + residual ridge)
  LINEAR     baseline = HYBRID at reference seats; + simulate(lever).delta_guests with the adjustments off
  S-CURVE    the same with the shipped adjustments, frequency lever (exercises the S-curve)
  S-CURVE %  the same, seats lever (S-curve inactive; dilution and saturation only)
  SHORT-RUN  baseline x (seats / reference seats) ^ beta_m
  TIME-ONLY  CalendarRidge (calendar only, no flight input): no seat response
  CHAIN      chain_runs.py
Baselines follow the web timeline: scenario week = max(0, structural_w + residual_w + delta_season).
Calibration, residual, ridge and beta are refitted on each fold's training weeks (week ends before
the fold's train_end).
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

import chain_runs
import data
import scenario_engines
from short_run import ShortRun
from tourism_twin.planning.baselines import CalendarRidge
from tourism_twin.planning.residual import ResidualMLEngine
from tourism_twin.planning.structural import StructuralEngine

MODES = ("yoy", "trend")
MODELS = ("TIME-ONLY", "HYBRID", "LINEAR", "S-CURVE", "S-CURVE %", "SHORT-RUN", "CHAIN")


def with_references(weekly: pd.DataFrame) -> pd.DataFrame:
    """Reference seats and flights per week for each mode."""
    keys = ["market", "week_start"]
    earlier = weekly[[*keys, "seats", "flights"]].assign(week_start=weekly["week_start"] + pd.Timedelta(days=364))
    out = weekly.merge(earlier.rename(columns={"seats": "ref_seats_yoy", "flights": "ref_flights_yoy"}), on=keys, how="left")
    out = out.sort_values(keys).reset_index(drop=True)
    out["ref_seats_trend"] = data.centred_trend(out, "seats")
    out["ref_flights_trend"] = data.centred_trend(out, "flights")
    return out


def _structural(engine: StructuralEngine, frame: pd.DataFrame, seats: pd.Series) -> np.ndarray:
    return engine.planning_guests_for(frame.assign(seats=seats.to_numpy()))


def fold_predictions(weekly: pd.DataFrame, fold, short_run_ridge: float) -> Dict[str, Dict[str, pd.Series]]:
    """{mode: {model: pred}} and {mode: {model + ' cf': cf}} for one fold."""
    train = weekly[weekly["week_start"] + pd.Timedelta(days=6) < fold.train_end]
    engine = StructuralEngine.calibrate(train)
    linear = scenario_engines.as_linear(engine)
    residual = ResidualMLEngine().fit(train, engine)
    ridge = CalendarRidge().fit(train)
    short = ShortRun(short_run_ridge).fit(train)

    index = pd.MultiIndex.from_frame(weekly[["market", "week_start"]])
    resid = residual.predict_residual(weekly).to_numpy()
    hybrid = pd.Series(np.maximum(0.0, _structural(engine, weekly, weekly["seats"]) + resid), index=index)
    time_only = pd.Series(ridge.predict(weekly).to_numpy(), index=index)
    inside = ((weekly["week_start"] >= fold.test_start) & (weekly["week_start"] + pd.Timedelta(days=6) <= fold.test_end)).to_numpy()

    out = {}
    for mode in MODES:
        ref_s, ref_f = weekly[f"ref_seats_{mode}"], weekly[f"ref_flights_{mode}"]
        usable = inside & (ref_s > 0).to_numpy() & (weekly["seats"] > 0).to_numpy()
        base = pd.Series(np.maximum(0.0, _structural(engine, weekly, ref_s.fillna(weekly["seats"])) + resid), index=index)
        deltas = {"LINEAR": [], "S-CURVE": [], "S-CURVE %": []}
        for row, ok in zip(weekly.itertuples(index=False), usable):
            if not ok:
                for key in deltas:
                    deltas[key].append(0.0)
                continue
            lv = scenario_engines.levers(engine, row.market, row.season, row.seats, row.flights,
                                         getattr(row, f"ref_seats_{mode}"), getattr(row, f"ref_flights_{mode}"))
            deltas["LINEAR"].append(linear.simulate(row.market, row.season, lv["seats"]).delta_guests)
            deltas["S-CURVE"].append(engine.simulate(row.market, row.season, lv["frequency"]).delta_guests)
            deltas["S-CURVE %"].append(engine.simulate(row.market, row.season, lv["seats"]).delta_guests)
        log_ratio = np.log(weekly["seats"].to_numpy() / ref_s.to_numpy(), where=usable, out=np.zeros(len(weekly)))
        scenario = {name: np.maximum(0.0, base.to_numpy() + np.array(d)) for name, d in deltas.items()}
        scenario["SHORT-RUN"] = base.to_numpy() * np.exp(short.response(weekly["market"], log_ratio))
        scenario["HYBRID"] = hybrid.to_numpy()
        preds, cfs = {}, {}
        for name, values in scenario.items():
            preds[name] = hybrid.where(~usable, pd.Series(values, index=index))
            cfs[name] = base.where(usable)
        cfs["HYBRID"] = base.where(usable)
        preds["TIME-ONLY"], cfs["TIME-ONLY"] = time_only, time_only.where(usable)
        out[mode] = {"pred": preds, "cf": cfs}
    out["beta"] = short.beta_
    return out


def all_folds(short_run_ridge: float) -> List[dict]:
    """Every fold's predictions for every model, the chain read from its cache."""
    weekly = with_references(data.weekly_panel())
    chain = chain_runs.load()
    runs = []
    for fold, record in zip(data.folds(), chain):
        run = fold_predictions(weekly, fold, short_run_ridge)
        for mode in MODES:
            run[mode]["pred"]["CHAIN"] = record["pred"]
            run[mode]["cf"]["CHAIN"] = record[f"cf_{mode}"]
        run["fold"] = fold
        runs.append(run)
    return runs
