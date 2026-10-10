# Abu Dhabi Tourism Digital Twin — User Guide

How to write the test-split predictions, run scenarios, read the output, retrain, evaluate, and rebuild the reports. Setup and the full pipeline are in the [README](../README.md); method and results are in the [solution documentation](solution_documentation.md).

---

## 1. Test-split predictions: `twin predict`

```bash
twin predict                       # default spec twin_daily, with intervals
twin predict --no-intervals        # skip the interval back-test; no intervals file, market_outputs.json or nowcast_serving.json
twin predict --spec arrivals_ratio # any name in DAILY_SPECS (nowcast/specs.py)
```

Needs the raw test workbooks (`data domestic_test.xlsx`, `data international_test.xlsx`) in `01a - DCT Dataset/` (or `TWIN_SOURCE_DIR`) and the committed `lake/curated/guest_daily.parquet`. Writes to `output/predictions/` (`TWIN_OUTPUT_DIR/predictions`).

Steps:

1. Build the daily market panel in memory; fit the spec on every training day; predict each test market-day.
2. With intervals: run the spec's rolling-origin back-test (8 monthly origins 2024-07-01 to 2025-02-01, 7-month horizon), fit the noise model on its errors, and add 80% bounds with the horizon counted from 2025-08-01.
3. Predict the 30 nationalities of the pooled markets (`OTHER_*` clusters) directly with the pooled nationality model (one fit per stay family, shared shape, per-nationality scale; `nowcast/pooling.py`), with intervals from its own back-test errors per nationality. The arrival-share split (trailing 7-day new arrivals × the nationality's training guests ÷ new arrivals ratio) remains the fallback.
4. Validate, then write. If validation fails, nothing is written and the command exits with the list of problems. Checks: rows, keys, column order and source values equal the test workbooks; every `Guests` finite and ≥ max(New Arrivals, 10) (the published rows keep Guests ≥ New Arrivals ≥ 10; predictions are floored there); interval rows and keys match; P10 ≤ P50 ≤ P90.

| File | Rows | Columns |
| :--- | :---: | :--- |
| `domestic_test_guests.csv` | 212 | `Date`, `New Arrivals`, `Same-Day Guests`, `Residence (groups)`, `Guests` |
| `international_test_guests.csv` | 9,202 | `Date`, `New Arrivals`, `Same-Day Guests`, `Nationality`, `Residence (groups)`, `Guests` |
| `test_guests_intervals.csv` | 9,414 | `Date`, `Nationality` (empty for domestic), `Residence (groups)`, `Guests_p10`, `Guests_p50`, `Guests_p90`; international rows first, then domestic. `Guests_p50` equals `Guests`. Not written with `--no-intervals` |
| `test_total_guests.csv` | 212 | `Date`, `Guests_total` (domestic + international), `Guests_total_p10`, `Guests_total_p90`: the total's own 80% interval from the back-test errors of the summed series (empty bounds with `--no-intervals`) |
| `nowcast_serving.json` | — | Serving bundle for the API (daily predictions per market, `INTERNATIONAL` and `TOTAL`, recent actual guests, the noise model's AR(1) parameters, nationality predictions); not written with `--no-intervals` |
| `market_outputs.json` | — | Per-market weekly outputs (below) |
| `test_predictions.png` | — | One panel per market: last 365 training days of actual guests, test predictions, 80% band |

The CSVs are the test workbooks row for row with a `Guests` column appended. `Guests` is the model's median on the original scale (exp of the log prediction), floored at max(New Arrivals, 10): every training row has Guests ≥ New Arrivals (59,668 rows, no exception) and Guests ≥ 10, and the test file keeps only rows with New Arrivals ≥ 10. The console prints the direction back-test accuracy, each written path and the row counts.

### 1.1 `market_outputs.json`

```text
spec, coverage, assumptions[]
markets.<MARKET>:
  weeks[]:
    week_start               Monday; only full Monday–Sunday test weeks
    forecast                 sum of daily predicted guests (guest-nights)
    p10, p90                 NoiseModel.range_interval over the week: AR(1) covariance of the daily log errors
    direction                "increase" / "decrease" to the next week; null for the last week
    direction_prob           probability of that direction from the s.d. of the two weeks' log-error difference
    yoy_change               forecast ÷ actual guests of the week 364 days earlier − 1 (null if not in training)
    top_drivers[]            model blocks other than the flow, ≥ 0.5%, by |mean log contribution|: {block, effect_pct}
direction_backtest:
  weeks_scored               distinct market-weeks, each from the earliest origin that forecasts it
  accuracy.{model, arrivals_direction, same_direction_as_last_year, majority_direction}
  direction_prob_reliability[]  per probability range: weeks, mean_prob, share_right
  weekly_band_coverage       share of back-test weeks inside p10–p90
```

Blocks: `time` (season, weekday, and for domestic the slope held at its last training value) is relative to the training average; `holiday` (events) to a day outside every event window. The model sees each test week's observed new arrivals, so direction accuracy is a nowcast skill; `arrivals_direction` is the sign of the change in new arrivals. The noise model is fitted on the same back-test folds, so `direction_prob_reliability` and `weekly_band_coverage` are in-sample for the error model. `assumptions` states these in the file.

### 1.2 Scoring a model: `twin evaluate-model`

`twin evaluate-model --spec S --start D --end D` fits a `DAILY_SPECS` name or `pooled_nationalities` on rows dated up to `--start` − (`--gap-days` + 1) days (default gap 21), or loads `--model P`, and scores the window without refitting (`models/evaluate.evaluate_fitted`): WAPE, bias, MAE, RMSE, MSE, log-MSE per segment at day, complete-week and complete-month grain, error by horizon, direction of consecutive totals; `pooled_nationalities` adds a per-nationality table. A window overlapping 2025-02-01..2025-07-31 needs `--frozen-test` (score once, after every choice). Writes `output/models/<spec>_<train_end>.pkl` and `output/evaluations/<spec>_<start>_<end>.json`.

---

## 2. What the simulator does

For one source market and one season, the twin compares a baseline week with a scenario week and reports:

| Output | Content |
| :--- | :--- |
| Conversion chain | Seats → passengers → P2P passengers → hotel new arrivals → hotel guests, baseline vs. scenario |
| Waterfall | Guest lift split sequentially across 5 levers; the parts sum to the total (tested to < 1e-9) |
| Hybrid lift | Structural lift plus the residual ML adjustment |
| Uncertainty | P10 / P50 / P90 of total guests and of the lift (Monte Carlo) |
| Tornado | Swing in guests for a fixed up/down shock to each lever |
| Briefing | One-paragraph plain-language summary |

---

## 3. CLI: `twin simulate`

Installed by `pip install -e ".[report,dev]"`; also `python -m tourism_twin simulate`. Source: [`src/tourism_twin/cli/simulate.py`](../src/tourism_twin/cli/simulate.py).

```bash
twin simulate --market "UNITED KINGDOM" --season Winter_Peak \
  --delta-freq 2.0 --gauge 290.0 --delta-lf 0.02
```

| Argument | Default | Meaning |
| :--- | :---: | :--- |
| `--market` | `UNITED KINGDOM` | One of the 21 modeled markets (§5), or an unmodeled country (e.g. `SWEDEN`, `BRAZIL`), which uses its archetype's default parameters (cold start) |
| `--season` | `Winter_Peak` | `Winter_Peak` (Nov–Mar), `Spring_Shoulder` (Apr–May), `Summer_Trough` (Jun–Aug), `Autumn_Shoulder` (Sep–Oct) |
| `--delta-freq` | `2.0` | Added weekly round-trip flights; each adds `--gauge` inbound seats per week |
| `--gauge` | `290.0` | Seats per added flight (e.g. 290 B787-9, 180 A320) |
| `--delta-seats-pct` | `0.0` | Proportional change in existing seats (`0.15` = +15%; `-1.0` = route closure) |
| `--delta-lf` | `0.02` | Absolute change in load factor (`0.02` = +2 pp) |
| `--delta-p2p` | `0.0` | Absolute change in P2P share |
| `--delta-mult-pct` | `0.0` | Proportional change in response multiplier (e.g. marketing; `0.05` = +5%) |
| `--delta-los` | `0.0` | Absolute change in the stay factor L (guests ÷ hotel arrivals) |

`DOMESTIC` has no aviation input: seat, frequency, load-factor and P2P levers have no effect; only `--delta-mult-pct` and `--delta-los` change domestic guests.

---

## 4. Reading the simulator output

`twin simulate` prints five sections.

1. **Executive recommendation** — weekly guest lift, % vs. baseline, P10–P90 range of the lift, holdout coverage (65.2%), and the top tornado driver.
2. **Conversion chain** — weekly seats, passengers, P2P, hotel new arrivals and hotel guests (guest-days), plus load factor, P2P share and response multiplier, baseline vs. scenario.
3. **Waterfall** — lift attributed in this order: seats, load factor, P2P share, response multiplier, stay factor. Because the attribution is sequential, a lever's share depends on its position in the order.
4. **Uncertainty** — P10/P50/P90 of simulated total guests and of the lift. Draws: Beta-distributed load factor and P2P share, normal shocks to multiplier and stay factor, and 4-week block-bootstrap of the market's historical weekly residuals. Results are deterministic for identical inputs. The P10 of the lift can be negative even when capacity is added.
5. **Tornado** — swing in guests for ±15% seats, ±4 pp load factor, ±5 pp P2P share, ±10% multiplier, ±0.5 stay factor, ranked.

---

## 5. Market directory

Archetypes come from `src/tourism_twin/domain/archetypes.py`. Guests per new arrival and arrivals per P2P passenger are ratios of sums over the train split of `weekly_market_panel.parquet`. Guests per new arrival is a stock-to-flow ratio, not a measured length of stay; pooled markets mix nationalities.

| Market | Archetype | Guests per new arrival | Arrivals per P2P pax |
| :--- | :--- | :---: | :---: |
| INDIA | Resident / VFR | 3.25 | 0.169 |
| RUSSIAN FEDERATION | Direct Leisure | 4.96 | 1.484 |
| UNITED KINGDOM | Direct Leisure | 4.79 | 0.994 |
| UNITED STATES OF AMERICA | Hub-Mediated | 3.84 | 2.094 |
| GERMANY | Direct Leisure | 4.94 | 0.989 |
| CHINA | Hub-Mediated | 2.12 | 6.011 |
| SAUDI ARABIA | Regional GCC | 2.47 | 0.399 |
| FRANCE | Direct Leisure | 3.55 | 1.236 |
| EGYPT | Resident / VFR | 5.01 | 0.116 |
| KUWAIT | Regional GCC | 3.28 | 0.594 |
| ITALY | Direct Leisure | 3.70 | 0.493 |
| KAZAKHSTAN | Highly Seasonal | 3.84 | 0.465 |
| ISRAEL | Direct Leisure | 2.92 | 0.877 |
| PHILIPPINES | Resident / VFR | 3.25 | 0.582 |
| OMAN | Regional GCC | 1.63 | 0.423 |
| OTHER_EUROPE | Direct Leisure | 3.83 | 0.764 |
| OTHER_ASIA_PACIFIC | Hub-Mediated | 3.18 | 2.218 |
| OTHER_MENA | Regional GCC | 3.14 | 0.174 |
| OTHER_AMERICAS_AFRICA | Hub-Mediated | 3.96 | 6.395 |
| OTHER_EURASIA | Highly Seasonal | 3.77 | 0.165 |
| DOMESTIC | Domestic Staycation | 2.32 | — (no flights) |

The five `OTHER_*` clusters pool the remaining nationalities (membership in `src/tourism_twin/domain/markets.py`). A multiplier above 1 means more hotel arrivals of that nationality than P2P passengers from the same-named country, i.e. many arrive via other origins. The simulator uses the per-season calibrated values in `structural_calibration.json`, not these all-season ratios.

---

## 6. Python API

```python
from tourism_twin.planning.simulator import TourismDigitalTwin
from tourism_twin.domain.scenario import ScenarioLever

twin = TourismDigitalTwin()   # loads the calibrated artifacts from lake/curated/

lever = ScenarioLever(
    market="GERMANY",
    delta_frequency=1.0,      # +1 weekly flight
    aircraft_gauge=250.0,     # seats per added flight
    delta_load_factor=0.03,   # +3 pp load factor
)
report = twin.run_scenario(market="GERMANY", season="Winter_Peak", lever=lever, n_draws=1500)

print(f"Incremental guests: {report.structural_result.delta_guests:+,.0f}")
print(f"P10 lift:           {report.uncertainty_bands.delta_p10:+,.0f}")
print(f"P90 lift:           {report.uncertainty_bands.delta_p90:+,.0f}")
print(report.recommendation_summary)
```

Other `ScenarioLever` fields: `delta_seats_pct`, `delta_p2p_share`, `delta_multiplier_pct`, `delta_los` (see `src/tourism_twin/domain/scenario.py`).

---

## 7. Web simulator

```bash
twin serve --port 8080      # open http://localhost:8080
```

Single page (`src/app/static/index.html`) served by `src/app/server.py`; no frontend build step.

- **Controls:** market, season, added weekly flights, aircraft gauge, load-factor shift, P2P shift, response-multiplier shift, guests-per-arrival ratio shift, and a reset-to-baseline button. (Seat-percentage shift is CLI/API only.)
- **Panels:** executive recommendation; KPI cards (baseline weekly guests, structural lift, hybrid lift, conformal range, simulated total); waterfall chart; conversion-chain table; tornado chart.
- **JSON API:** `GET /api/simulate` with query parameters `market`, `season`, `delta_freq`, `gauge`, `delta_seats_pct`, `delta_lf`, `delta_p2p`, `delta_mult_pct`, `delta_los` (an invalid season returns 400); `GET /api/benchmark`.

### 7.1 Nowcast API

Answers come from `output/predictions/nowcast_serving.json` (written by `twin predict`); nothing is refitted per request. Without the bundle the endpoints return 503; ranges outside the predicted period return 400.

| Endpoint | Returns |
| --- | --- |
| `GET /api/nowcast/series` | Series names (21 markets, `INTERNATIONAL`, `TOTAL`), the predicted period, interval coverage |
| `GET /api/nowcast/range?series=TOTAL&start=YYYY-MM-DD&end=YYYY-MM-DD` | `guests` (predicted total), `p10`, `p90` (`NoiseModel.range_interval`: AR(1) covariance across the range; `INTERNATIONAL` and `TOTAL` have their own error series), `previous_guests` for the same-length range just before (actual guests for training days, predictions for test days), `change`, `direction`: `up` / `down` when \|change\| ≥ 0.08, else `no clear change` (over 2-week ranges the size of a change is off by 3–4 pp, docs/model_design.md §4.8) |
| `GET /api/nowcast/nationalities?start=&end=` | Predicted guests per international nationality and its share of the international total (point predictions, no interval) |

---

## 8. Retraining (weekly planning model)

```bash
twin train          # or: make train; options: --max-date (default 2025-07-27), --panel-path
```

Trains on complete train-split weeks with complete guest inputs up to `--max-date`, and writes:

| File | Contents |
| :--- | :--- |
| `lake/curated/structural_calibration.json` | Seats, load factor, P2P share, response multiplier, stay factor and baseline guests for 21 markets × 4 seasons |
| `lake/curated/residual_engine.pkl` | One RidgeCV per market on week-of-year harmonics, quarter, season, holiday-week and major-event-week flags; no aviation inputs. Target: actual guests − planning-mode structural prediction (scheduled seats × calibrated seasonal priors). Also stores the mean fitted residual per market and season, used by the simulator |
| `lake/curated/conformal_calibrator.json` | Per-market conformal margins (target alpha 0.2) and the demonstrated holdout coverage, read from `evaluation_results.json` (run `twin evaluate` first) |

---

## 9. Weekly back-test

```bash
twin evaluate       # or: make evaluate
```

Calibrates on 104 complete weeks (2023-01-02 to 2024-12-23 week starts, 2,132 market-weeks) and scores 30 complete holdout weeks (2024-12-30 to 2025-07-21 week starts, 621 market-weeks), using the same trainers as `twin train`. Writes `lake/curated/evaluation_results.json` (diagnostics, benchmark, `benchmark_leaders`, coverage, market and season breakdowns). It writes no calibrator; `twin train` reads the coverage from this file. The four benchmark models run as specs (`WEEKLY_SPECS`) through the back-test harness in `models/backtest.py`.

| Setting | Prediction |
| :--- | :--- |
| International planning | Scheduled seats × calibrated seasonal load factor, P2P share, multiplier, stay factor. No holdout load factor, P2P or arrivals |
| International realized-chain | Realized holdout P2P × calibrated multiplier × stay factor |
| Domestic forecast | Calibrated domestic seasonal prior |
| Combined | International + domestic |

Results are in the [README](../README.md#32-weekly-planning-model-forward-holdout). Bias is (Σ predicted − Σ actual) / Σ actual, so a positive bias is an over-forecast. The domestic forecast over-predicted the 2025 holdout by 13.05%: domestic guests fell below their 2023–2024 seasonal level.

---

## 10. Tests

```bash
pytest tests/ -v    # or: make test, or .venv/bin/pytest -q
```

87 tests: 63 product tests in folders that mirror the packages, and 24 for the audit tool; all pass (the prediction-validator test skips without the raw test workbooks). Run one area with `pytest tests/<area>`:

| Folder | Tests | Covers |
| :--- | ---: | :--- |
| `tests/data/` | 9 | lake grain, weekly and daily panels, test-file row rules |
| `tests/features/` | 4 | feature registry, event registry and offsets, one-off masking |
| `tests/models/` | 37 | components (known-answer recovery), fitting and weights, specs, back-test harness and noise model, fitted-model evaluation |
| `tests/nowcast/` | 6 | baselines, submission validator, outputs, serving, same-day guests |
| `tests/planning/` | 4 | waterfall identity, planning rules, scenario residual |
| `tests/app/` | 1 | web API |
| `tests/test_architecture.py` | 2 | layering, no row loops |
| `tests/audit/` | 24 | audit tool |

Shared fixtures are in `tests/conftest.py` and synthetic data with a known answer in `tests/synthetic.py`. The daily panel is built in memory by a fixture, so `daily_market_panel.parquet` is not required; the prediction-validator test needs the raw test workbooks; `twin predict` itself is not run by the tests. Product checks, by area:

| Section | Asserts |
| :--- | :--- |
| Lake | `flight_daily` is daily from 2023-01-01 (monthly flights only in 2022 when built); `guest_daily` has 69,920 rows and its flag columns |
| Feature registry | Dependencies resolve first and once; missing inputs and cycles raise |
| Panels | Exactly 21 markets, unique keys, load factor capped and flagged; the weekly panel rebuilds from the lake exactly; daily lags continue across the train→test boundary; weekly sums of daily guests and arrivals equal the weekly panel |
| Model components | Each component recovers a known synthetic truth; backfitting matches the joint solution and never raises the penalised objective; the kernel's log gradient matches finite differences and it beats its raw-scale warm start; w₀ ≤ 1 holds when it binds; the knot base is flat beyond training; an arrivals-proportional base follows a 0.55× shock; `GroupScale` recovers each series' scale; weights follow a favoured regime; least squares falls back to QR when gelsd fails; invalid inputs that would give silent nonsense raise |
| Event registry | Golden dates; windows do not overlap; Ramadan and Eid al-Fitr never share a day; the one-off 2022 shock is masked |
| Back-test harness | No fold trains on the future (daily and weekly rows); segment metrics; misindexed or missing predictions raise; skipped folds reported; the block-bootstrap `compare` detects a real difference and not a null one; the harness reproduces `evaluation_results.json`; a saved model scores identically and refuses its training window |
| Noise model | AR(1) recovery and its closed-form variance; a fold's own errors never set its own bounds |
| Architecture | `nowcast` and `planning` never import each other; packages import only lower layers (any import form); no row loops in model packages |
| Competition predictions | The validator accepts mirrored files and flags bad ones (including Guests below max(New Arrivals, 10)); absent test days get below-threshold arrivals; full weeks with an AR(1)-based direction probability; the direction back-test scores each week once against its baselines; the serving bundle answers range questions; the same-day GLM recovers a weekday effect and reads `*` as 0 |
| Simulator and API | The API rejects an invalid season and serves a scenario; waterfall = lift within 1e-9 for every calibrated market + `SWEDEN`, season and 6 lever sets, and relatively for 1e7-guest scenarios; route closure, domestic decoupling, added capacity never lowers demand, cold-start priors (SWEDEN, PAKISTAN) and tornado, deterministic Monte Carlo; planning and simulation share one arrivals rule; the scenario residual is the season's mean fit |

---

## 11. Charts and PDF

```bash
twin charts              # output/figures/{waterfall_attribution,tornado_sensitivity,model_benchmark}.png
twin report solution     # output/pdf/challengeon_solution_report.pdf (3 pages; needs the 'report' extra)
twin report database     # output/pdf/challengeon_schema_database_report.pdf (needs lake/analytics.duckdb)
```

`model_benchmark.png` reads `lake/curated/evaluation_results.json`.
