# Abu Dhabi Tourism Digital Twin — User Guide

How to write the test-split predictions, run scenarios, read the output, retrain, evaluate, and rebuild the reports. Setup and the full pipeline are in the [README](../README.md); method and results are in the [solution documentation](solution_documentation.md).

---

## 1. Test-split predictions: `twin predict`

```bash
twin predict                       # default spec twin_daily, with intervals
twin predict --no-intervals        # skip the interval back-test; no intervals file, no market_outputs.json
twin predict --spec arrivals_ratio # any name in DAILY_SPECS (nowcast/specs.py)
```

Needs the raw test workbooks (`data domestic_test.xlsx`, `data international_test.xlsx`) in `01a - DCT Dataset/` (or `TWIN_SOURCE_DIR`) and the committed `lake/curated/guest_daily.parquet`. Writes to `output/predictions/` (`TWIN_OUTPUT_DIR/predictions`).

Steps:

1. Build the daily market panel in memory; fit the spec on every training day; predict each test market-day.
2. With intervals: run the spec's rolling-origin back-test (8 monthly origins 2024-07-01 to 2025-02-01, 7-month horizon), fit the noise model on its errors, and add 80% bounds with the horizon counted from 2025-08-01.
3. Split each pooled market (`OTHER_*` clusters) into nationalities: share = trailing 7-day new arrivals × the nationality's training guests ÷ new arrivals ratio, normalised within market and day. Nationality intervals add the split's own log-error variance (measured over the last 365 training days) to the market's.
4. Validate, then write. If validation fails, nothing is written and the command exits with the list of problems. Checks: rows, keys, column order and source values equal the test workbooks; every `Guests` finite and ≥ max(New Arrivals, 10) (the published rows keep Guests ≥ New Arrivals ≥ 10; predictions are floored there); interval rows and keys match; P10 ≤ P50 ≤ P90.

| File | Rows | Columns |
| :--- | :---: | :--- |
| `domestic_test_guests.csv` | 212 | `Date`, `New Arrivals`, `Same-Day Guests`, `Residence (groups)`, `Guests` |
| `international_test_guests.csv` | 9,202 | `Date`, `New Arrivals`, `Same-Day Guests`, `Nationality`, `Residence (groups)`, `Guests` |
| `test_guests_intervals.csv` | 9,414 | `Date`, `Nationality` (empty for domestic), `Residence (groups)`, `Guests_p10`, `Guests_p50`, `Guests_p90`; international rows first, then domestic. `Guests_p50` equals `Guests`. Not written with `--no-intervals` |
| `market_outputs.json` | — | Per-market weekly outputs (below) |
| `test_predictions.png` | — | One panel per market: last 365 training days of actual guests, test predictions, 80% band |

The CSVs are the test workbooks row for row with a `Guests` column appended. `Guests` is the model's median on the original scale (exp of the log prediction), floored at max(New Arrivals, 10): every training row has Guests ≥ New Arrivals (59,668 rows, no exception) and Guests ≥ 10, and the test file keeps only rows with New Arrivals ≥ 10. The console prints the direction back-test accuracy, each written path and the row counts.

### 1.1 `market_outputs.json`

```text
spec, coverage, assumptions[]
markets.<MARKET>:
  base_stock_share           share of the training stock carried by the base stock c_t, not the kernel
  implied_mean_stay_days     Σ w_k of the fitted survival curve; null when base_stock_share > 0.25
  short_stay_share           1 − w_2 / w_0: share of kernel arrivals gone after two nights; null as above
  weeks[]:
    week_start               Monday; only full Monday–Sunday test weeks
    forecast                 sum of daily predicted guests (guest-nights)
    p10, p90                 forecast × exp(∓z · s.d. of the week's log error); daily errors AR(1) with the market's φ
    direction                "increase" / "decrease" to the next week; null for the last week
    direction_prob           probability of that direction from the s.d. of the two weeks' log-error difference
    yoy_change               forecast ÷ actual guests of the week 364 days earlier − 1 (null if not in training)
    trend_vs_training_pct    domestic only: fitted slope relative to the training mean, extrapolated
    top_drivers[]            up to 3 season / event effects ≥ 0.5% by |mean log contribution|: {component, effect_pct}
direction_backtest:
  weeks_scored               distinct market-weeks, each from the earliest origin that forecasts it
  accuracy.{model, arrivals_direction, same_direction_as_last_year, majority_direction}
  direction_prob_reliability[]  per probability range: weeks, mean_prob, share_right
  weekly_band_coverage       share of back-test weeks inside p10–p90
```

Season effects are relative to the training average, event effects to a day outside every event window; weekday effects average about 0 over a week and are not listed. The model sees each test week's observed new arrivals, so direction accuracy is a nowcast skill; `arrivals_direction` is the sign of the change in new arrivals. The noise model is fitted on the same back-test folds, so `direction_prob_reliability` and `weekly_band_coverage` are in-sample for the error model. `assumptions` states these in the file.

Stay fields are withheld for 7 of 21 markets (DOMESTIC, CHINA, EGYPT, INDIA, PHILIPPINES, OTHER_ASIA_PACIFIC, UNITED STATES OF AMERICA), whose base stock carries more than 25% of the training stock.


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
| `--delta-los` | `0.0` | Absolute change in length of stay, days |

`DOMESTIC` has no aviation input: seat, frequency, load-factor and P2P levers have no effect; only `--delta-mult-pct` and `--delta-los` change domestic guests.

---

## 4. Reading the simulator output

`twin simulate` prints five sections.

1. **Executive recommendation** — weekly guest lift, % vs. baseline, P10–P90 range of the lift, holdout coverage (65.2%), and the top tornado driver.
2. **Conversion chain** — weekly seats, passengers, P2P, hotel new arrivals and hotel guests (guest-days), plus load factor, P2P share, response multiplier and LOS, baseline vs. scenario.
3. **Waterfall** — lift attributed in this order: seats, load factor, P2P share, response multiplier, length of stay. Because the attribution is sequential, a lever's share depends on its position in the order.
4. **Uncertainty** — P10/P50/P90 of simulated total guests and of the lift. Draws: Beta-distributed load factor and P2P share, normal shocks to multiplier and LOS, and 4-week block-bootstrap of the market's historical weekly residuals. Results are deterministic for identical inputs. The P10 of the lift can be negative even when capacity is added.
5. **Tornado** — swing in guests for ±15% seats, ±4 pp load factor, ±5 pp P2P share, ±10% multiplier, ±0.5 days LOS, ranked.

---

## 5. Market directory

Archetypes come from `src/tourism_twin/domain/archetypes.py`. Implied LOS (guests ÷ new arrivals) and arrivals per P2P passenger are ratios of sums over the train split of `weekly_market_panel.parquet`.

| Market | Archetype | Implied LOS (days) | Arrivals per P2P pax |
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

- **Controls:** market, season, added weekly flights, aircraft gauge, load-factor shift, P2P shift, response-multiplier shift, LOS shift, and a reset-to-baseline button. (Seat-percentage shift is CLI/API only.)
- **Panels:** executive recommendation; KPI cards (baseline weekly guests, structural lift, hybrid lift, conformal range, simulated total); waterfall chart; conversion-chain table; tornado chart.
- **JSON API:** `GET /api/simulate` with query parameters `market`, `season`, `delta_freq`, `gauge`, `delta_seats_pct`, `delta_lf`, `delta_p2p`, `delta_mult_pct`, `delta_los` (an invalid season returns 400); `GET /api/benchmark`.

---

## 8. Retraining (weekly planning model)

```bash
twin train          # or: make train; options: --max-date (default 2025-07-27), --panel-path
```

Trains on complete train-split weeks with complete guest inputs up to `--max-date`, and writes:

| File | Contents |
| :--- | :--- |
| `lake/curated/structural_calibration.json` | Seats, load factor, P2P share, response multiplier, LOS and baseline guests for 21 markets × 4 seasons |
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
| International planning | Scheduled seats × calibrated seasonal load factor, P2P share, multiplier, LOS. No holdout load factor, P2P or arrivals |
| International realized-chain | Realized holdout P2P × calibrated multiplier × LOS |
| Domestic forecast | Calibrated domestic seasonal prior |
| Combined | International + domestic |

Results are in the [README](../README.md#32-weekly-planning-model-forward-holdout). Bias is (Σ predicted − Σ actual) / Σ actual, so a positive bias is an over-forecast. The domestic forecast over-predicted the 2025 holdout by 13.05%: domestic guests fell below their 2023–2024 seasonal level.

---

## 10. Tests

```bash
pytest tests/ -v    # or: make test, or .venv/bin/pytest -q
```

76 tests: 52 in `tests/test_tourism_twin.py` (fixtures in `tests/conftest.py`), 24 in `tests/test_audit_agent.py`; all pass on a fresh clone. The daily panel is built in memory by the fixture, so `daily_market_panel.parquet` is not required. The prediction-validator test needs the raw test workbooks; `twin predict` itself is not run by the tests.

Product checks in `tests/test_tourism_twin.py`, by section:

| Section | Asserts |
| :--- | :--- |
| Lake | `flight_daily` is daily from 2023-01-01 (monthly flights only in 2022 when built); `guest_daily` has 69,920 rows and its flag columns |
| Feature registry | Dependencies resolve first and once; missing inputs and cycles raise |
| Panels | Exactly 21 markets, unique keys, load factor capped and flagged; the weekly panel rebuilds from the lake exactly; daily lags continue across the train→test boundary; weekly sums of daily guests and arrivals equal the weekly panel |
| Model components | Each component recovers a known synthetic truth; backfitting matches the joint solution and never raises the penalised objective; the kernel's log gradient matches finite differences and it beats its raw-scale warm start; w₀ ≤ 1 holds when it binds; the knot base is flat beyond training; an arrivals-proportional base follows a 0.55× shock; invalid inputs that would give silent nonsense raise |
| Event registry | Golden dates; windows do not overlap; Ramadan and Eid al-Fitr never share a day; the one-off 2022 shock is masked |
| Back-test harness | No fold trains on the future (daily and weekly rows); segment metrics; misindexed or missing predictions raise; skipped folds reported; the harness reproduces `evaluation_results.json` |
| Noise model | AR(1) recovery and its closed-form variance; a fold's own errors never set its own bounds |
| Architecture | `nowcast` and `planning` never import each other; packages import only lower layers (any import form); no row loops in model packages |
| Competition predictions | The validator accepts mirrored files and flags bad ones (including Guests below max(New Arrivals, 10)); absent test days get below-threshold arrivals; full weeks with an AR(1)-based direction probability; the direction back-test scores each week once against its baselines; stay fields withheld when the base stock dominates; the same-day GLM recovers a weekday effect and reads `*` as 0 |
| Simulator | Waterfall = lift within 1e-9 for every calibrated market + `SWEDEN`, season and 6 lever sets, and relatively for 1e7-guest scenarios; route closure, domestic decoupling, added capacity never lowers demand, cold-start priors and tornado, deterministic Monte Carlo; planning and simulation share one arrivals rule; the scenario residual is the season's mean fit |

---

## 11. Charts and PDF

```bash
twin charts              # output/figures/{waterfall_attribution,tornado_sensitivity,model_benchmark}.png
twin report solution     # output/pdf/challengeon_solution_report.pdf (3 pages; needs the 'report' extra)
twin report database     # output/pdf/challengeon_schema_database_report.pdf (needs lake/analytics.duckdb)
```

`model_benchmark.png` reads `lake/curated/evaluation_results.json`.
