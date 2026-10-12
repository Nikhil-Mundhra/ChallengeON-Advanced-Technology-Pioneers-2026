"""The serving bundle: everything the dashboard needs, as JSON, computed once at build time.

  manifest.json   schema_version, version, git sha, spec, coverage, predicted period, file list
  nowcast.json    per series (21 markets, INTERNATIONAL, TOTAL): dates, horizons, predictions,
                  AR(1) error parameters; z for central intervals; recent actual guests;
                  nationality predictions
  whatif.json     per market and predicted day: base stock c_t, the kernel flow from arrivals before
                  the predicted period (pre_t) and from arrivals inside it (in_t), the floor and the
                  calendar multiplier m_t, so guests_t = max(c_t + pre_t + f * in_t, floor) * m_t
                  reproduces the prediction (f = 1) and any arrivals factor f exactly. No raw
                  arrivals are exported (the data is licensed for use within the competition)
  planning.json   weekly scenario model: calibrated parameters per market and season, the mean
                  calendar residual per market and season, conformal margins, the flight response
                  (per-market schedule elasticity with its interval, capacity co-movement)
  weekly.json     weekly scenario model over time, per market: actual weekly guests (training
                  weeks), the shipped model's structural part and calendar residual for every
                  panel week and PROJECTION_YEARS beyond it, and the forward-holdout back-test
                  prediction (fitted before HOLDOUT_START), and the event type covering most of each week. Scenario weeks are
                  max(0, structural_w + residual_w + scenario change for the week's season)
  outlook.json    monthly guests for the 12 months after the last known arrivals, per arrivals
                  scenario and segment, the same month a year earlier (actual guests, or the shipped
                  nowcast's estimate where guests are withheld), and the band: the central
                  BAND_COVERAGE of the same method's back-test misses (actual / projection - 1) at
                  each horizon, with their median (mid); calibrated = guests x (1 + mid)
                  (nowcast/outlook.py)
  golden.json     input -> expected output cases computed here, for parity tests of any port

The model outputs are read-only and versioned, so the bundle is the store: no database.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from scipy.stats import norm

from tourism_twin.config import SETTINGS
from tourism_twin.features import PANEL_FEATURES
from tourism_twin.features.lags import lag_column
from tourism_twin.models.noise import NoiseModel
from tourism_twin.nowcast.predict import INTERNATIONAL, TOTAL, TestPredictions, total_series

SCHEMA_VERSION = 3
COVERAGES = (0.5, 0.8, 0.9)
HISTORY_DAYS = 400
PROJECTION_YEARS = 3
CALENDAR_COLUMNS = ["iso_week", "month", "quarter", "season", "is_holiday_week", "is_major_event_week"]


def _dates(values) -> List[str]:
    return [str(pd.Timestamp(v).date()) for v in values]


def _round(values, digits: int = 12) -> List[float]:
    """Full precision for parity (ports are tested to 1e-9)."""
    return [float(f"{float(v):.{digits}g}") for v in np.asarray(values, dtype=float)]


def nowcast_part(predictions: TestPredictions, history: pd.DataFrame) -> Dict[str, Any]:
    daily = predictions.market_daily
    series = pd.concat([daily, total_series(daily), total_series(daily, INTERNATIONAL)], ignore_index=True)
    noise = predictions.noise
    actual = history[["market", "date", "guests"]].dropna()
    actual = actual[actual["date"] > actual["date"].max() - np.timedelta64(HISTORY_DAYS, "D")].rename(columns={"guests": "actual"})
    actual = pd.concat([actual, total_series(actual.assign(pred=0.0))[["market", "date", "actual"]],
                        total_series(actual.assign(pred=0.0), INTERNATIONAL)[["market", "date", "actual"]]], ignore_index=True)
    nationalities = predictions.international[["Date", "Nationality", "Guests", "Residence (groups)"]]
    return {
        "z": {str(c): float(norm.ppf(0.5 + c / 2)) for c in COVERAGES},
        "series": {name: {"date": _dates(rows["date"]), "horizon_days": rows["horizon_days"].astype(int).tolist(),
                          "pred": _round(rows["pred"]),
                          "noise": {"phi": noise.phi_[name], "sigma_eta": noise.sigma_eta_[name], "v0": noise.v0_[name]}}
                   for name, rows in series.sort_values("date").groupby("market")},
        "history": {name: {"date": _dates(rows["date"]), "guests": _round(rows["actual"])}
                    for name, rows in actual.sort_values("date").groupby("market")},
        "nationalities": {name: {"date": _dates(rows["Date"]), "pred": _round(rows["Guests"])}
                          for name, rows in nationalities.sort_values("Date").groupby("Nationality")},
    }


def _market_fits(model) -> Dict[str, list]:
    """market -> fitted components, for a MarketRouter of AdditiveLogModels grouped by market."""
    fits: Dict[str, list] = {}
    for sub in model.models_.values():
        for market, (components, _) in sub.fitted_.items():
            fits[market] = components
    return fits


def whatif_part(model, panel: pd.DataFrame) -> Dict[str, Any]:
    """Per market: guests_t = max(c_t + pre_t + f * in_t, floor) * m_t over the predicted days, where
    pre_t / in_t are the kernel flow from arrivals before / inside the predicted period."""
    test = panel[panel["dataset_split"] == "test"]
    first_test_day = test["date"].min()
    markets: Dict[str, Any] = {}
    for market, components in _market_fits(model).items():
        rows = test[test["market"] == market].sort_values("date")
        kernel, others = components[0], components[1:]
        lags = rows[[lag_column(k) for k in range(len(kernel.w_))]].to_numpy(dtype=float)
        lag_dates = rows["date"].to_numpy()[:, None] - np.arange(len(kernel.w_))[None, :] * np.timedelta64(1, "D")
        inside = lag_dates >= np.datetime64(first_test_day)
        log_multiplier = sum((c.contribution(rows) for c in others), pd.Series(0.0, index=rows.index))
        markets[market] = {
            "date": _dates(rows["date"]),
            "base": _round(kernel._base_design(rows) @ kernel.c_),
            "pre": _round((lags * ~inside) @ kernel.w_),
            "in": _round((lags * inside) @ kernel.w_),
            "floor": float(kernel.floor_),
            "multiplier": _round(np.exp(log_multiplier.to_numpy())),
        }
    return {"formula": "guests_t = max(base_t + pre_t + f * in_t, floor) * multiplier_t", "markets": markets}


PLANNING_LEVERS = {  # golden scenarios: (name, ScenarioLever fields)
    "baseline": {},
    "two_more_flights": {"delta_frequency": 2.0, "aircraft_gauge": 290.0, "delta_load_factor": 0.02},
    "seats_and_p2p": {"delta_seats_pct": 0.15, "delta_p2p_share": 0.03},
    "multiplier_and_factor": {"delta_multiplier_pct": 0.05, "delta_los": 0.4},
    "route_closure": {"delta_seats_pct": -1.0},
    "cuts": {"delta_load_factor": -0.3, "delta_multiplier_pct": -0.2, "delta_los": -1.0},
    "seats_up": {"delta_seats_pct": 0.25},
    "seats_down": {"delta_seats_pct": -0.3},
    "fewer_flights": {"delta_frequency": -3.0, "aircraft_gauge": 200.0, "delta_multiplier_pct": 0.1},
    "schedule_and_assumptions": {"delta_frequency": 4.0, "aircraft_gauge": 350.0, "delta_load_factor": 0.03,
                                 "delta_p2p_share": -0.02, "delta_los": 0.3},
}
CAPACITY_GOLDEN = ((5.0, 1.0), (5.0, 3.0), (-3.0, 2.0), (12.5, 2.5))  # (seat growth % a year, years)


def planning_part() -> Dict[str, Any]:
    """The weekly scenario model as data: calibrated parameters per market and season, the
    archetype priors for markets without calibration (cold start), the season residual, the
    conformal margins, and the flight response (schedule elasticity per market, capacity
    co-movement). The Monte Carlo spread is not exported (it depends on numpy's random stream)."""
    from dataclasses import asdict

    from tourism_twin.domain.archetypes import ARCHETYPE_PROFILES, COUNTRY_TO_REGION_MAP, MARKET_ARCHETYPE_MAP
    from tourism_twin.planning.residual import ResidualMLEngine

    residual = ResidualMLEngine.load()
    profiles = {archetype.value: {key: value for key, value in asdict(profile).items() if key.startswith("default_")}
                for archetype, profile in ARCHETYPE_PROFILES.items()}
    return {
        "calibration": json.loads(SETTINGS.calibration_path.read_text(encoding="utf-8")),
        "archetypes": {"profiles": profiles,
                       "market": {m: a.value for m, a in MARKET_ARCHETYPE_MAP.items()},
                       "country": {c: a.value for c, a in COUNTRY_TO_REGION_MAP.items()},
                       "fallback": "Emerging / Sparse"},
        "season_residual": residual.season_residual_,
        "conformal": json.loads(SETTINGS.conformal_path.read_text(encoding="utf-8")),
        "default_conformal_margin": 0.28,
        "flight_response": json.loads(SETTINGS.flight_response_path.read_text(encoding="utf-8")),
    }


def planning_golden() -> List[Dict[str, Any]]:
    """Scenario outputs a port must reproduce: the conversion chain and waterfall, the schedule
    range (scenario guests at the ends of the elasticity interval), the hybrid (structural + season
    residual), conformal bands, the tornado ranking, and the capacity-growth guest factors."""
    from dataclasses import asdict

    from tourism_twin.domain.scenario import ScenarioLever
    from tourism_twin.domain.seasons import SEASONS
    from tourism_twin.planning.capacity_trend import EFFECT_RANGE, capacity_guest_factor
    from tourism_twin.planning.sensitivity import compute_tornado_sensitivity
    from tourism_twin.planning.simulator import TourismDigitalTwin

    twin = TourismDigitalTwin()
    cases = []
    for market in ("UNITED KINGDOM", "INDIA", "DOMESTIC", "OTHER_EUROPE", "SWEDEN"):  # SWEDEN: cold start
        for season in (SEASONS[0], SEASONS[2]):
            for name, levers in PLANNING_LEVERS.items():
                lever = ScenarioLever(market, **levers)
                result = twin.structural_engine.simulate(market, season, lever)
                hybrid = twin.residual_engine.predict_hybrid(result)
                bands = twin.uncertainty_engine.run_monte_carlo(market, season, lever, n_draws=50)
                low, high = twin.structural_engine.schedule_range(market, season, lever)
                cases.append({"kind": "scenario", "market": market, "season": season, "levers": levers,
                              "schedule_low": low, "schedule_high": high,
                              "result": {k: v for k, v in asdict(result).items() if isinstance(v, (int, float)) and not isinstance(v, bool)},
                              "hybrid_sim": hybrid["hybrid_sim"], "hybrid_delta": hybrid["hybrid_delta"],
                              "p10": bands.p10, "p90": bands.p90, "delta_p10": bands.delta_p10, "delta_p90": bands.delta_p90})
            rows = compute_tornado_sensitivity(twin.structural_engine, market, season, ScenarioLever(market, delta_frequency=2.0, aircraft_gauge=250.0))
            cases.append({"kind": "tornado", "market": market, "season": season,
                          "base_lever": {"delta_frequency": 2.0, "aircraft_gauge": 250.0}, "rows": rows})
    central = json.loads(SETTINGS.flight_response_path.read_text(encoding="utf-8"))["capacity"]["central"]
    effects = [EFFECT_RANGE[0], central, EFFECT_RANGE[1]]
    for growth_pct, years in CAPACITY_GOLDEN:
        cases.append({"kind": "capacity", "growth_pct": growth_pct, "years": years, "effects": effects,
                      "factors": [capacity_guest_factor(growth_pct, years, e) for e in effects]})
    return cases


def weekly_part(weekly_panel: pd.DataFrame) -> Dict[str, Any]:
    """Back-test and projection of the weekly scenario model (the shipped structural engine and
    residual ridge, as the simulator uses them). Weeks with a schedule use its seats; projected
    weeks use the calibrated seasonal seats. The model has no growth term: projected years repeat
    the seasonal profile, and holiday flags exist only as far as domain/events.HOLIDAY_WEEKS."""
    from tourism_twin.data.panel import calendar_weeks, training_window
    from tourism_twin.domain.events import HOLIDAY_WEEKS, MAJOR_EVENT_WEEKS
    from tourism_twin.planning.baselines import LegacyHybrid
    from tourism_twin.planning.calendar_features import event_exposure_matrix
    from tourism_twin.planning.evaluation import HOLDOUT_START
    from tourism_twin.planning.simulator import TourismDigitalTwin

    twin = TourismDigitalTwin()
    structural, residual = twin.structural_engine, twin.residual_engine
    panel = weekly_panel.assign(week_start=pd.to_datetime(weekly_panel["week_start"]))
    markets = sorted(structural.params)
    last_week = panel["week_start"].max()
    future_weeks = pd.date_range(last_week + pd.Timedelta(days=7), last_week + pd.DateOffset(years=PROJECTION_YEARS), freq="7D")
    future = PANEL_FEATURES.apply(pd.DataFrame([(m, w) for m in markets for w in future_weeks], columns=["market", "week_start"]),
                                  CALENDAR_COLUMNS, anchor="week_start")
    future["seats"] = [structural.get_or_create_params(m, s).baseline_weekly_seats for m, s in zip(future["market"], future["season"])]
    observed = PANEL_FEATURES.apply(calendar_weeks(panel[panel["market"].isin(markets)]).drop(columns=["days"]), CALENDAR_COLUMNS, anchor="week_start")
    frame = pd.concat([observed[["market", "week_start", "seats", "dataset_split", *CALENDAR_COLUMNS]],
                       future.assign(dataset_split="projected")], ignore_index=True)
    frame["structural"] = structural.planning_guests_for(frame)
    frame["residual"] = residual.predict_residual(frame).to_numpy()

    complete = training_window(weekly_panel).assign(week_start=lambda f: pd.to_datetime(f["week_start"]))  # actuals: complete weeks only
    train, holdout = complete[complete["week_start"] < HOLDOUT_START], complete[complete["week_start"] >= HOLDOUT_START]
    frame = (frame.merge(complete[["market", "week_start", "guests"]], on=["market", "week_start"], how="left")
                  .merge(holdout[["market", "week_start"]].assign(holdout=LegacyHybrid().fit(train).predict(holdout).to_numpy()),
                         on=["market", "week_start"], how="left"))

    def nullable(values) -> List[Any]:
        return [None if pd.isna(v) else float(f"{float(v):.12g}") for v in values]

    def _week_events(rows, events):
        """The event type (domain/events.csv code) covering most of each week for this market, else None."""
        if not events:
            return [None] * len(rows)
        exposure = event_exposure_matrix(rows, events)
        return [events[int(i)] if row.max() > 0 else None for i, row in zip(exposure.argmax(axis=1), exposure)]

    series = {}
    for market, rows in frame.sort_values("week_start").groupby("market"):
        series[market] = {"week": _dates(rows["week_start"]), "season": rows["season"].tolist(),
                          "kind": rows["dataset_split"].map({"train": "history", "test": "scheduled", "projected": "projected"}).tolist(),
                          "actual": nullable(rows["guests"]), "structural": _round(rows["structural"]), "residual": _round(rows["residual"]),
                          "holdout": nullable(rows["holdout"]),
                          "event": _week_events(rows, residual.events)}
    return {"holdout_start": HOLDOUT_START, "last_actual_week": str(complete["week_start"].max().date()),
            "calendar_flags_until": max(max(HOLIDAY_WEEKS), max(MAJOR_EVENT_WEEKS)),
            "formula": "guests_w = max(0, structural_w + residual_w + delta_season(w))", "markets": series}


def golden_part(model, panel: pd.DataFrame, noise: NoiseModel, nowcast: Dict[str, Any]) -> Dict[str, Any]:
    """Cases a port must reproduce: what-if guests for scaled arrivals (recomputed through the
    fitted model) and range intervals (NoiseModel.range_interval)."""
    cases = []
    for market, factor in (("UNITED KINGDOM", 0.8), ("DOMESTIC", 1.1), ("OTHER_EUROPE", 0.55)):
        shocked = panel.copy()
        hit = (shocked["market"] == market) & (shocked["dataset_split"] == "test")
        shocked.loc[hit, "new_arrivals_filled"] *= factor
        lagged = [c for c in shocked.columns if c.startswith("arrivals_lag_") or c in ("lag_complete", "arrivals_mean_90")]
        shocked = PANEL_FEATURES.apply(shocked.drop(columns=lagged), ["arrival_lags", "arrivals_mean_90"],
                                       max_lag=len([c for c in lagged if c.startswith("arrivals_lag_")]) - 1)
        rows = shocked[hit].sort_values("date")
        cases.append({"kind": "whatif", "market": market, "arrivals_factor": factor,
                      "date": _dates(rows["date"]), "guests": _round(model.predict(rows))})
    for name, start, days in (("TOTAL", 0, 14), ("INTERNATIONAL", 30, 28), ("DOMESTIC", 120, 7)):
        series = nowcast["series"][name]
        horizon = np.asarray(series["horizon_days"][start:start + days], dtype=float)
        pred = np.asarray(series["pred"][start:start + days], dtype=float)
        for coverage in COVERAGES:
            low, high = noise.range_interval(name, horizon, pred, coverage)
            cases.append({"kind": "range", "series": name, "start": series["date"][start], "days": days,
                          "coverage": coverage, "guests": float(pred.sum()), "p_low": float(low), "p_high": float(high)})
    return {"cases": cases + planning_golden()}


def outlook_part(predictions: TestPredictions, panel: pd.DataFrame, spec: str) -> Dict[str, Any]:
    from tourism_twin.nowcast.outlook import (BAND_COVERAGE, SEGMENTS, horizon_backtest, horizon_errors,
                                              monthly_outlook, segment_months)

    data_end = panel["date"].max()
    guests_end = panel.loc[panel["dataset_split"] == "train", "date"].max()
    projections = monthly_outlook(spec)
    errors = horizon_errors(horizon_backtest(spec))
    total = errors[errors["segment"] == "TOTAL"]
    default = str(total.groupby("scenario")["wape_pct"].mean().idxmin())  # lower back-test error over the horizons
    actual = segment_months(panel[panel["dataset_split"] == "train"], "guests")
    estimate = segment_months(predictions.market_daily, "pred")

    def previous(month: pd.Period, segment: str):
        before = month - 12
        if before in actual.index and pd.notna(actual.at[before, segment]):
            return float(actual.at[before, segment]), "actual"
        if before in estimate.index and pd.notna(estimate.at[before, segment]):
            return float(estimate.at[before, segment]), "estimate"
        return None, None

    def months(frame: pd.DataFrame, scenario: str, segment: str) -> List[Dict[str, Any]]:
        mids = errors[(errors["scenario"] == scenario) & (errors["segment"] == segment)].set_index("horizon_months")["miss_mid"]
        rows = []
        for month, guests in frame[segment].items():
            value, kind = previous(month, segment)
            horizon = (month - data_end.to_period("M")).n
            guests = float(f"{guests:.12g}")
            rows.append({"month": str(month), "horizon_months": horizon, "guests": guests,
                         "calibrated": guests * (1 + float(mids[horizon])) if horizon in mids.index else None,
                         "previous": value, "previous_kind": kind})
        return rows

    def band(rows: pd.DataFrame) -> List[Dict[str, Any]]:
        return [{"horizon_months": int(r.horizon_months), "low": float(r.miss_low), "mid": float(r.miss_mid),
                 "high": float(r.miss_high),
                 "n": int(r.n), "miss_min": float(r.miss_min), "miss_max": float(r.miss_max),
                 "wape_pct": float(r.wape_pct), "bias_pct": float(r.bias_pct)}
                for r in rows.sort_values("horizon_months").itertuples()]

    return {
        "data_end": data_end.date().isoformat(), "guests_known_to": guests_end.date().isoformat(), "spec": spec,
        "coverage": BAND_COVERAGE, "default_scenario": default,
        "scenarios": {scenario: {segment: months(frame, scenario, segment) for segment in SEGMENTS}
                      for scenario, frame in projections.items()},
        "band": band(total[total["scenario"] == default]),
        "bands": {scenario: {segment: band(errors[(errors["scenario"] == scenario) & (errors["segment"] == segment)])
                             for segment in SEGMENTS} for scenario in projections},
    }


def outlook_golden(outlook: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The default scenario's TOTAL range and calibrated middle per month: guests x (1 + low), (1 + mid)
    and (1 + high)."""
    bands = {b["horizon_months"]: b for b in outlook["band"]}
    return [{"kind": "outlook_range", "month": m["month"], "guests": m["guests"],
             "low": m["guests"] * (1 + bands[m["horizon_months"]]["low"]),
             "mid": bands[m["horizon_months"]]["mid"],
             "calibrated": m["guests"] * (1 + bands[m["horizon_months"]]["mid"]),
             "high": m["guests"] * (1 + bands[m["horizon_months"]]["high"])}
            for m in outlook["scenarios"][outlook["default_scenario"]]["TOTAL"] if m["horizon_months"] in bands]


def _git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True,
                              cwd=SETTINGS.root).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _weights_digests() -> Dict[str, str]:
    """sha256 of each saved planning artifact the bundle was built from, so the web data can be
    traced to the exact weights (the daily nowcast is refitted at export, recorded by git_sha)."""
    paths = {"structural_calibration": SETTINGS.calibration_path, "flight_response": SETTINGS.flight_response_path,
             "residual_engine": SETTINGS.residual_model_path,
             "conformal_calibrator": SETTINGS.conformal_path, "evaluation_results": SETTINGS.evaluation_results_path}
    return {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items() if path.exists()}


def write_bundle(predictions: TestPredictions, panel: pd.DataFrame, weekly_panel: pd.DataFrame, out_dir: Path, spec: str,
                 coverage: float = 0.8) -> Path:
    """Write <out_dir>/<version>/{nowcast,whatif,planning,weekly,outlook,golden}.json and <out_dir>/manifest.json
    (pointing at that version). Earlier versions stay untouched."""
    if predictions.noise is None or predictions.model is None:
        raise ValueError("the bundle needs predictions with intervals and the fitted model")
    history = panel[panel["dataset_split"] == "train"]
    created = datetime.now(timezone.utc)
    version = f"{created:%Y%m%d-%H%M%S}-{_git_sha()}"
    nowcast = nowcast_part(predictions, history)
    parts = {"nowcast": nowcast, "whatif": whatif_part(predictions.model, panel), "planning": planning_part(),
             "weekly": weekly_part(weekly_panel), "outlook": outlook_part(predictions, panel, spec),
             "golden": golden_part(predictions.model, panel, predictions.noise, nowcast)}
    parts["golden"]["cases"] += outlook_golden(parts["outlook"])
    target = out_dir / version
    target.mkdir(parents=True, exist_ok=True)
    digests = {}
    for name, content in parts.items():
        text = json.dumps(content, separators=(",", ":"))
        (target / f"{name}.json").write_text(text, encoding="utf-8")
        digests[name] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    daily = predictions.market_daily
    manifest = {"schema_version": SCHEMA_VERSION, "version": version, "created": created.isoformat(timespec="seconds"),
                "git_sha": _git_sha(), "spec": spec, "coverage": coverage,
                "predicted_period": {"start": str(daily["date"].min().date()), "end": str(daily["date"].max().date())},
                "files": {name: f"{version}/{name}.json" for name in parts},
                "sha256": digests,
                "weights": _weights_digests()}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return target
