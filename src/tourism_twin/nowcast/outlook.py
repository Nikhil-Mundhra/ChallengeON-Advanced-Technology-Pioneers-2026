"""Seasonal outlook beyond the test split: guests for a future window under an arrivals scenario.

Guests are known up to the end of the training split; new arrivals up to the end of the test
split. A future window has neither, so its arrivals are a stated scenario: each market's arrivals
on the same weekday 364 days earlier, times a per-market growth factor: the ratio of the market's
arrivals over the last 365 known days to the 365 days before ("trend"), or 1.0 ("flat"). The chosen daily spec, fitted on
every training day, converts the scenario into guests; calendar effects (season, weekday, events
in domain/events.csv) are the future window's own.

`backtest_outlook` scores the same procedure on past winters, with guests cut at the same distance
before the window as in the live outlook, so its error is the outlook's own error.
"""

from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from itertools import repeat
from typing import Dict, List, Optional

import pandas as pd

from tourism_twin.data.daily_panel import DAILY_FEATURES, build_daily_panel
from tourism_twin.data.repository import LakeRepository
from tourism_twin.domain.markets import DOMESTIC
from tourism_twin.features import PANEL_FEATURES
from tourism_twin.nowcast.specs import DAILY_SPECS

SHIFT_DAYS = 364  # same weekday one year earlier
BASE_COLUMNS = ["market", "date", "dataset_split", "guests", "new_arrivals_filled"]
FROZEN_TEST = (pd.Timestamp("2025-02-01"), pd.Timestamp("2025-07-31"))
MIN_BACKTEST_HISTORY_DAYS = 365
SEGMENTS = ("TOTAL", "INTERNATIONAL", "DOMESTIC")
HORIZON_MONTHS = 12  # monthly outlook: the 12 months after the last known arrivals
BAND_COVERAGE = 0.8  # central share of back-test misses the monthly band spans


@dataclass(frozen=True)
class Window:
    name: str
    start: pd.Timestamp
    end: pd.Timestamp

    @classmethod
    def winter(cls, year: int) -> "Window":
        """December of `year` to the end of February of `year` + 1."""
        return cls(f"winter {year}/{str(year + 1)[-2:]}", pd.Timestamp(f"{year}-12-01"),
                   pd.Timestamp(f"{year + 1}-03-01") - pd.Timedelta(days=1))


@dataclass
class Outlook:
    window: Window
    scenario: str
    growth: pd.Series                     # market -> arrivals growth factor used
    market_daily: pd.DataFrame            # market, date, pred
    previous: pd.DataFrame                # market, date, pred: the same procedure one year earlier
    months: pd.DataFrame = field(default=None)  # month, guests, previous, change


SCENARIOS = ("trend", "flat")


def arrivals_growth(panel: pd.DataFrame, scenario: str) -> pd.Series:
    """Per-market yearly growth factor of new arrivals at the end of `panel`."""
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown arrivals scenario {scenario!r}; expected one of {SCENARIOS}")
    markets = panel["market"].unique()
    if scenario == "flat":
        return pd.Series(1.0, index=markets)
    end = panel["date"].max()
    days = (end - panel["date"]).dt.days
    last = panel[days < 365].groupby("market")["new_arrivals_filled"].sum()
    before = panel[(days >= 365) & (days < 730)].groupby("market")["new_arrivals_filled"].sum()
    return (last / before).reindex(markets).fillna(1.0)


def _extend_arrivals(panel: pd.DataFrame, until: pd.Timestamp, scenario: str) -> pd.DataFrame:
    """Append scenario days after the last known arrivals: day d takes the known day d − SHIFT_DAYS·k
    (k ≥ 1, the smallest that reaches known data) × the market's growth factor ** k."""
    growth = arrivals_growth(panel, scenario)
    base = panel[BASE_COLUMNS].copy()
    last = base["date"].max()
    if until > last:
        dates = pd.Series(pd.date_range(last + pd.Timedelta(days=1), until), name="date")
        years = -(-(dates - last).dt.days // SHIFT_DAYS)
        days = pd.DataFrame({"date": dates, "years": years, "source": dates - pd.to_timedelta(SHIFT_DAYS * years, unit="D")})
        known = base[["market", "date", "new_arrivals_filled"]].rename(columns={"date": "source"})
        future = days.merge(known, on="source")
        future["new_arrivals_filled"] *= future["market"].map(growth) ** future["years"]
        future = future.assign(dataset_split="scenario", guests=float("nan"))[BASE_COLUMNS]
        base = pd.concat([base, future], ignore_index=True)
    return PANEL_FEATURES.apply(base.sort_values(["market", "date"]).reset_index(drop=True), DAILY_FEATURES, anchor="date")


def _predict(panel: pd.DataFrame, train_end: pd.Timestamp, arrivals_end: pd.Timestamp,
             window: Window, spec: str, scenario: str) -> pd.DataFrame:
    known = panel[panel["date"] <= arrivals_end]
    extended = _extend_arrivals(known, window.end, scenario)
    train = extended[(extended["date"] <= train_end) & extended["guests"].notna()]
    model = DAILY_SPECS[spec]().fit(train)
    rows = extended[(extended["date"] >= window.start) & (extended["date"] <= window.end)]
    return rows[["market", "date"]].assign(pred=model.predict(rows))


def _scenario_predictions(panel: pd.DataFrame, train_end: pd.Timestamp, arrivals_end: pd.Timestamp,
                          start: pd.Timestamp, end: pd.Timestamp, spec: str) -> Dict[str, pd.DataFrame]:
    """_predict for every scenario over [start, end]. Scenario days lie after the training rows, so the
    training frame is normally the same in every scenario and the model is fitted once (checked)."""
    known = panel[panel["date"] <= arrivals_end]
    extended = {scenario: _extend_arrivals(known, end, scenario) for scenario in SCENARIOS}
    trains = {scenario: frame[(frame["date"] <= train_end) & frame["guests"].notna()] for scenario, frame in extended.items()}
    shared = all(train.equals(trains[SCENARIOS[0]]) for train in trains.values())
    model = DAILY_SPECS[spec]().fit(trains[SCENARIOS[0]].copy()) if shared else None
    out = {}
    for scenario, frame in extended.items():
        fitted = model if shared else DAILY_SPECS[spec]().fit(trains[scenario])
        rows = frame[(frame["date"] >= start) & (frame["date"] <= end)]
        out[scenario] = rows[["market", "date"]].assign(pred=fitted.predict(rows))
    return out



def segment_months(daily: pd.DataFrame, value: str) -> pd.DataFrame:
    """Monthly sums of `value` (month index; TOTAL, INTERNATIONAL, DOMESTIC columns); NaN for a month
    with any missing day."""
    month = daily["date"].dt.to_period("M")
    domestic = daily["market"] == DOMESTIC
    parts = {"TOTAL": daily, "INTERNATIONAL": daily[~domestic], "DOMESTIC": daily[domestic]}
    return pd.DataFrame({name: part.groupby(month[part.index])[value].sum(min_count=1)
                                .where(part[value].notna().groupby(month[part.index]).all())
                         for name, part in parts.items()})


def _origin_scores(panel: pd.DataFrame, origin: pd.Timestamp, guests_gap_days: int, spec: str) -> pd.DataFrame:
    """One back-test origin: arrivals known to `origin`, guests to `guests_gap_days` before it (the live
    distances); each later whole month up to HORIZON_MONTHS that ends before the frozen test, per
    scenario and segment, with its actual."""
    end = min(origin + pd.offsets.MonthEnd(HORIZON_MONTHS), FROZEN_TEST[0] - pd.Timedelta(days=1))
    predictions = _scenario_predictions(panel, origin - pd.Timedelta(days=guests_gap_days), origin,
                                        origin + pd.Timedelta(days=1), end, spec)
    actual = segment_months(panel[(panel["date"] > origin) & (panel["date"] <= end)], "guests")
    rows = []
    for scenario, daily in predictions.items():
        pred = segment_months(daily, "pred")
        for month in pred.index:
            horizon = (month - origin.to_period("M")).n
            for segment in SEGMENTS:
                rows.append({"origin": origin.date().isoformat(), "horizon_months": horizon, "month": str(month),
                             "scenario": scenario, "segment": segment, "pred": float(pred.at[month, segment]),
                             "actual": float(actual.at[month, segment])})
    return pd.DataFrame(rows)


def horizon_backtest(spec: str = "twin_daily", repository: Optional[LakeRepository] = None,
                     workers: Optional[int] = None) -> pd.DataFrame:
    """The monthly outlook scored at every month-end origin it can be formed from: guests cut at the live
    distance before the arrivals cut, at least MIN_BACKTEST_HISTORY_DAYS of training guests, target
    months ending before the frozen test. One row per origin, horizon, scenario and segment."""
    panel = build_daily_panel(repository)
    guests_end = panel.loc[panel["dataset_split"] == "train", "date"].max()
    gap = (panel["date"].max() - guests_end).days
    first = panel["date"].min() + pd.Timedelta(days=gap + MIN_BACKTEST_HISTORY_DAYS)
    origins = [o for o in pd.date_range(first, FROZEN_TEST[0], freq="ME") if o + pd.offsets.MonthEnd(1) < FROZEN_TEST[0]]
    with ProcessPoolExecutor(max_workers=workers or min(6, os.cpu_count() or 1)) as pool:
        frames = list(pool.map(_origin_scores, repeat(panel), origins, repeat(gap), repeat(spec)))
    return pd.concat(frames, ignore_index=True)


def horizon_errors(scores: pd.DataFrame) -> pd.DataFrame:
    """Error of the monthly outlook by horizon, scenario and segment: WAPE and bias (prediction minus
    actual over actual) in %, and the actual / prediction - 1 ratios (miss) that set the band and its
    median (the calibrated middle)."""
    scores = scores.assign(miss=scores["actual"] / scores["pred"] - 1)

    def summary(group: pd.DataFrame) -> pd.Series:
        return pd.Series({
            "n": len(group),
            "wape_pct": 100 * (group["pred"] - group["actual"]).abs().sum() / group["actual"].sum(),
            "bias_pct": 100 * (group["pred"] - group["actual"]).sum() / group["actual"].sum(),
            "miss_min": group["miss"].min(), "miss_max": group["miss"].max(),
            "miss_low": group["miss"].quantile((1 - BAND_COVERAGE) / 2),
            "miss_mid": group["miss"].median(),
            "miss_high": group["miss"].quantile((1 + BAND_COVERAGE) / 2),
        })

    return scores.groupby(["scenario", "segment", "horizon_months"]).apply(summary, include_groups=False).reset_index()



def monthly_outlook(spec: str = "twin_daily", repository: Optional[LakeRepository] = None) -> Dict[str, pd.DataFrame]:
    """Monthly guests for the HORIZON_MONTHS months after the last known arrivals, per scenario (month
    index; TOTAL, INTERNATIONAL, DOMESTIC columns). Guests are known only to the end of the training
    split, so the model is the one fitted there, as in seasonal_outlook."""
    panel = build_daily_panel(repository)
    train_end = panel.loc[panel["dataset_split"] == "train", "date"].max()
    arrivals_end = panel["date"].max()
    predictions = _scenario_predictions(panel, train_end, arrivals_end, arrivals_end + pd.Timedelta(days=1),
                                        arrivals_end + pd.offsets.MonthEnd(HORIZON_MONTHS), spec)
    return {scenario: segment_months(daily, "pred") for scenario, daily in predictions.items()}


def _months(current: pd.DataFrame, previous: pd.DataFrame) -> pd.DataFrame:
    now = current.groupby(current["date"].dt.to_period("M"))["pred"].sum()
    before = previous.groupby((previous["date"] + pd.DateOffset(years=1)).dt.to_period("M"))["pred"].sum()
    out = pd.DataFrame({"guests": now, "previous": before.reindex(now.index)})
    out["change"] = out["guests"] / out["previous"] - 1
    return out.rename_axis("month").reset_index()


def seasonal_outlook(
    window: Window,
    spec: str = "twin_daily",
    scenario: str = "trend",
    repository: Optional[LakeRepository] = None,
) -> Outlook:
    """Guests in `window` under the arrivals scenario, and the same model's guests one year earlier.

    The year-earlier window is predicted from its actual arrivals (all known), so the change is the
    model's own year-on-year change, not model minus actual."""
    panel = build_daily_panel(repository)
    train_end = panel.loc[panel["dataset_split"] == "train", "date"].max()
    arrivals_end = panel["date"].max()
    current = _predict(panel, train_end, arrivals_end, window, spec, scenario)
    year_before = Window(window.name, window.start - pd.DateOffset(years=1), window.end - pd.DateOffset(years=1))
    previous = _predict(panel, train_end, arrivals_end, year_before, spec, "flat")
    growth = arrivals_growth(panel, scenario)
    return Outlook(window, scenario, growth, current, previous, _months(current, previous))


def backtest_outlook(
    windows: List[Window],
    train_gap_days: int,
    arrivals_gap_days: int,
    spec: str = "twin_daily",
    scenario: str = "trend",
    repository: Optional[LakeRepository] = None,
) -> pd.DataFrame:
    """Score the outlook procedure on past windows: guests cut `train_gap_days` and arrivals cut
    `arrivals_gap_days` before each window starts, as in the live outlook. Refuses a window that
    overlaps the frozen test."""
    for window in windows:
        if window.start <= FROZEN_TEST[1] and window.end >= FROZEN_TEST[0]:
            raise ValueError(f"{window.name} overlaps the frozen test {FROZEN_TEST[0].date()}..{FROZEN_TEST[1].date()}")
    panel = build_daily_panel(repository)
    rows: List[Dict] = []
    for window in windows:
        train_end = window.start - pd.Timedelta(days=train_gap_days)
        arrivals_end = window.start - pd.Timedelta(days=arrivals_gap_days)
        pred = _predict(panel, train_end, arrivals_end, window, spec, scenario)
        actual = panel[(panel["date"] >= window.start) & (panel["date"] <= window.end)][["market", "date", "guests"]]
        scored = pred.merge(actual, on=["market", "date"])
        for segment, part in (("total", scored), ("international", scored[scored["market"] != DOMESTIC]),
                              ("domestic", scored[scored["market"] == DOMESTIC])):
            daily = part.groupby("date")[["pred", "guests"]].sum()
            rows.append({
                "window": window.name, "scenario": scenario, "segment": segment, "train_end": train_end.date().isoformat(),
                "arrivals_end": arrivals_end.date().isoformat(),
                "season_error_pct": 100 * (daily["pred"].sum() / daily["guests"].sum() - 1),
                "daily_wape_pct": 100 * (daily["pred"] - daily["guests"]).abs().sum() / daily["guests"].sum(),
            })
    return pd.DataFrame(rows)


def outlook_document(window: Window, spec: str = "twin_daily", repository: Optional[LakeRepository] = None) -> Dict:
    """Both arrivals scenarios for `window`, and the procedure's back-test on the latest past window
    of the same calendar span (at least two years earlier) that starts before the frozen test and is
    cut at its start, at the live outlook's distances. The back-test is empty when that window would
    train on less than MIN_BACKTEST_HISTORY_DAYS of guests."""
    outlooks = {scenario: seasonal_outlook(window, spec, scenario, repository) for scenario in SCENARIOS}
    panel = build_daily_panel(repository)
    train_end = panel.loc[panel["dataset_split"] == "train", "date"].max()
    gaps = ((window.start - train_end).days, (window.start - panel["date"].max()).days)
    years = 2
    while window.start - pd.DateOffset(years=years) >= FROZEN_TEST[0]:
        years += 1
    start, end = window.start - pd.DateOffset(years=years), min(window.end - pd.DateOffset(years=years), FROZEN_TEST[0] - pd.Timedelta(days=1))
    past = Window(f"winter {start.year}/{str(start.year + 1)[-2:]} ({start:%b}–{end:%b})", start, end)
    history_days = (start - pd.Timedelta(days=gaps[0]) - panel["date"].min()).days
    if history_days >= MIN_BACKTEST_HISTORY_DAYS:
        scores = pd.concat([backtest_outlook([past], *gaps, spec=spec, scenario=s, repository=repository) for s in SCENARIOS])
    else:  # the past window's training data would be shorter than a year
        scores = pd.DataFrame()
    flat = outlooks["flat"]
    previous_total = float(flat.previous["pred"].sum())

    def summary(outlook: Outlook) -> Dict:
        total = float(outlook.market_daily["pred"].sum())
        by_market = outlook.market_daily.groupby("market")["pred"].sum().sort_values(ascending=False)
        source_markets = by_market[(by_market.index != DOMESTIC) & ~by_market.index.str.startswith("OTHER_")]
        return {
            "guest_nights": total,
            "change_pct": 100 * (total / previous_total - 1),
            "domestic_share_pct": 100 * float(by_market.get(DOMESTIC, 0.0)) / total,
            "top_source_markets": [{"market": m, "share_pct": 100 * v / total} for m, v in source_markets.head(5).items()],
            "months": [{"month": str(r.month), "guest_nights": float(r.guests), "change_pct": 100 * float(r.change)}
                       for r in outlook.months.itertuples()],
            "arrivals_growth": {m: float(g) for m, g in outlook.growth.items()},
        }

    return {
        "window": window.name, "start": window.start.date().isoformat(), "end": window.end.date().isoformat(),
        "spec": spec, "guests_known_to": train_end.date().isoformat(), "arrivals_known_to": panel["date"].max().date().isoformat(),
        "previous": {"window": f"{window.start.year - 1}/{str(window.start.year)[-2:]}", "guest_nights": previous_total,
                     "months": [{"month": str(r.month - 12), "guest_nights": float(r.previous)} for r in flat.months.itertuples()]},
        "scenarios": {scenario: summary(outlook) for scenario, outlook in outlooks.items()},
        "backtest": scores.to_dict(orient="records"),
    }
