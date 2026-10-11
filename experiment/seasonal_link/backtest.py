"""Natural-experiment back-test (design and lever code from experiment/scenario_response): market-weeks
whose seats moved more than 15% against last year's week (yoy, drift removed) or the centred 13-week
seat trend. Each chain predicts the week on actual seats and its baseline on the reference schedule;
TIME-ONLY (CalendarRidge, refitted per fold) has no seat response. Scored by part (all, increases,
cuts) and by the project season of the week."""

from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

import data
import lever
import run
from tourism_twin.domain.seasons import SEASONS, assign_season
from tourism_twin.planning.baselines import CalendarRidge

MODES = ("yoy", "trend")
TIME_ONLY = "TIME-ONLY"


def time_only(weekly: pd.DataFrame, fold) -> pd.Series:
    train = weekly[weekly["week_start"] + pd.Timedelta(days=6) < fold.train_end]
    model = CalendarRidge().fit(train)
    return pd.Series(model.predict(weekly).to_numpy(), index=pd.MultiIndex.from_frame(weekly[["market", "week_start"]]))


def rows_by_model(models: Dict[str, str], mode: str) -> Dict[str, pd.DataFrame]:
    """Per label (TIME-ONLY and each chain variant): every fold's test weeks, on market-week-folds
    every model scores."""
    weekly = data.weekly_panel()
    actual = lever.actual_changes(weekly, mode)
    out = {TIME_ONLY: []}
    for i, fold in enumerate(data.folds()):
        pred = time_only(weekly, fold)
        out[TIME_ONLY].append(lever.fold_rows(mode, weekly, actual, pred, pred, fold))
        for label, variant in models.items():
            record = run.load(variant, str(i))
            out.setdefault(label, []).append(lever.fold_rows(mode, weekly, actual, record["pred"], record[f"cf_{mode}"], fold))
    out = {label: pd.concat(frames) for label, frames in out.items()}
    keys = set.intersection(*[set(zip(f["fold"], f["market"], f["week_start"])) for f in out.values()])
    return {label: f[np.array([k in keys for k in zip(f["fold"], f["market"], f["week_start"])])] for label, f in out.items()}


def with_season(weeks: pd.DataFrame) -> pd.DataFrame:
    return weeks.assign(season=(weeks["week_start"] + pd.Timedelta(days=3)).dt.month.map(assign_season))


def parts(events: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    out = lever.parts(events)
    for season in SEASONS:
        out[season] = events[events["season"] == season]
    return out


def event_weeks(rows: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    return {label: with_season(lever.unique_weeks(f[f["event"]])) for label, f in rows.items()}


def summary(events: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    return pd.DataFrame([{"model": label, "part": part, **lever.summary(g)}
                         for label, ev in events.items() for part, g in parts(ev).items() if len(g)])


def paired(events: Dict[str, pd.DataFrame], pairs: List[tuple]) -> pd.DataFrame:
    rows = []
    for a, b in pairs:
        for part in ("all", "increases", "cuts", *SEASONS):
            pa, pb = parts(events[a])[part], parts(events[b])[part]
            if len(pa) >= 5:
                rows.append({"comparison": f"{b} - {a}", "part": part, **lever.paired_difference(pa, pb)})
    return pd.DataFrame(rows)
