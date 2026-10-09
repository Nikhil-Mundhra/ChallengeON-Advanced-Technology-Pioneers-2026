# Abu Dhabi Tourism Digital Twin — User Guide

How to run scenarios, read the output, retrain, evaluate, and rebuild the reports. Setup and the full pipeline are in the [README](../README.md); method and results are in the [solution documentation](solution_documentation.md).

---

## 1. What the simulator does

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

## 2. CLI: `twin simulate`

Installed by `pip install -e ".[report,dev]"`; also `python -m tourism_twin simulate`. Source: [`src/tourism_twin/cli/simulate.py`](../src/tourism_twin/cli/simulate.py).

```bash
twin simulate --market "UNITED KINGDOM" --season Winter_Peak \
  --delta-freq 2.0 --gauge 290.0 --delta-lf 0.02
```

| Argument | Default | Meaning |
| :--- | :---: | :--- |
| `--market` | `UNITED KINGDOM` | One of the 21 modeled markets (§4), or an unmodeled country (e.g. `SWEDEN`, `BRAZIL`), which uses its archetype's default parameters (cold start) |
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

## 3. Reading the output

`twin simulate` prints five sections.

1. **Executive recommendation** — weekly guest lift, % vs. baseline, P10–P90 range of the lift, holdout coverage (65.2%), and the top tornado driver.
2. **Conversion chain** — weekly seats, passengers, P2P, hotel new arrivals and hotel guests (guest-days), plus load factor, P2P share, response multiplier and LOS, baseline vs. scenario.
3. **Waterfall** — lift attributed in this order: seats, load factor, P2P share, response multiplier, length of stay. Because the attribution is sequential, a lever's share depends on its position in the order.
4. **Uncertainty** — P10/P50/P90 of simulated total guests and of the lift. Draws: Beta-distributed load factor and P2P share, normal shocks to multiplier and LOS, and 4-week block-bootstrap of the market's historical weekly residuals. Results are deterministic for identical inputs. The P10 of the lift can be negative even when capacity is added.
5. **Tornado** — swing in guests for ±15% seats, ±4 pp load factor, ±5 pp P2P share, ±10% multiplier, ±0.5 days LOS, ranked.

---

## 4. Market directory

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

## 5. Python API

```python
from tourism_twin.services.simulator import TourismDigitalTwin
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

## 6. Web simulator

```bash
twin serve --port 8080      # open http://localhost:8080
```

Single page (`src/app/static/index.html`) served by `src/app/server.py`; no frontend build step.

- **Controls:** market, season, added weekly flights, aircraft gauge, load-factor shift, P2P shift, response-multiplier shift, LOS shift, and a reset-to-baseline button. (Seat-percentage shift is CLI/API only.)
- **Panels:** executive recommendation; KPI cards (baseline weekly guests, structural lift, hybrid lift, conformal range, simulated total); waterfall chart; conversion-chain table; tornado chart.
- **JSON API:** `GET /api/simulate` with query parameters `market`, `season`, `delta_freq`, `gauge`, `delta_seats_pct`, `delta_lf`, `delta_p2p`, `delta_mult_pct`, `delta_los` (an invalid season returns 400); `GET /api/benchmark`.

---

## 7. Retraining

```bash
twin train          # or: make train; options: --max-date (default 2025-07-27), --panel-path
```

Trains on complete train-split weeks with complete guest inputs up to `--max-date`, and writes:

| File | Contents |
| :--- | :--- |
| `lake/curated/structural_calibration.json` | Seats, load factor, P2P share, response multiplier, LOS and baseline guests for 21 markets × 4 seasons |
| `lake/curated/residual_engine.pkl` | One RidgeCV per market on week-of-year harmonics, quarter, season, holiday-week and major-event-week flags; no aviation inputs. Target: actual guests − planning-mode structural prediction (scheduled seats × calibrated seasonal priors) |
| `lake/curated/conformal_calibrator.json` | Per-market conformal margins (target alpha 0.2) and demonstrated holdout coverage |

---

## 8. Back-test

```bash
twin evaluate       # or: make evaluate
```

Calibrates on 104 complete weeks (2023-01-02 to 2024-12-23 week starts, 2,132 market-weeks) and scores 30 complete holdout weeks (2024-12-30 to 2025-07-21 week starts, 621 market-weeks), using the same trainers as `twin train`. Writes `lake/curated/evaluation_results.json` (diagnostics, benchmark, `benchmark_leaders`, coverage, market and season breakdowns) and copies the coverage into `conformal_calibrator.json`.

| Setting | Prediction |
| :--- | :--- |
| International planning | Scheduled seats × calibrated seasonal load factor, P2P share, multiplier, LOS. No holdout load factor, P2P or arrivals |
| International realized-chain | Realized holdout P2P × calibrated multiplier × LOS |
| Domestic forecast | Calibrated domestic seasonal prior |
| Combined | International + domestic |

Results are in the [README](../README.md#3-forward-holdout-results). Bias is (Σ predicted − Σ actual) / Σ actual, so a positive bias is an over-forecast. The domestic forecast over-predicted the 2025 holdout by 13.05%: domestic guests fell below their 2023–2024 seasonal level.

---

## 9. Tests

```bash
pytest tests/ -v    # or: make test, or .venv/bin/pytest -q
```

78 tests: 54 in `tests/test_tourism_twin.py` (fixtures in `tests/conftest.py`), 24 in `tests/test_audit_agent.py`. On a fresh clone 77 pass and 1 skips (`test_monthly_flights_are_isolated_to_2022`, until `twin build-lake` creates `flight_monthly.parquet`). The daily panel is built in memory by the fixture, so `daily_market_panel.parquet` is not required.

Product checks in `tests/test_tourism_twin.py`:

| Test | Asserts |
| :--- | :--- |
| `test_lake_tables_keep_their_grain_contract` | `flight_daily` is daily from 2023-01-01; `guest_daily` has 69,920 rows and its flag columns |
| `test_registry_*` (2) | Feature registry resolves dependencies first, computes each once, rejects missing inputs, cycles, duplicate names |
| `test_weekly_panel_contract` | Exactly the 21 markets; unique (week, market, split); load factor > 1 kept in `load_factor_raw` and flagged, `load_factor` ≤ 1 |
| `test_weekly_panel_rebuilds_from_the_lake_exactly` | Rebuilding the weekly panel from the curated Parquet equals the committed panel |
| `test_daily_panel_contract`, `test_daily_lags_cross_the_train_test_boundary`, `test_daily_panel_sums_to_the_weekly_panel` | Lag completeness, lags continue across the train→test boundary, weekly sums of daily guests and arrivals equal the weekly panel |
| `test_waterfall_reconciles_exactly_for_every_market_and_season` | For every calibrated market + `SWEDEN`, every season, 6 lever sets: waterfall sum = lift within 1e-9; zero levers give zero lift |
| `test_route_closure_removes_all_aviation_demand` | `delta_seats_pct=-1` zeroes seats through guests; all lift attributed to seats |
| `test_domestic_ignores_aviation_levers` | Domestic seats stay 0; only multiplier and LOS move guests |
| `test_added_capacity_never_lowers_demand` | +2 flights gives structural lift ≥ 0 and hybrid lift ≥ 0 for 5 markets |
| `test_cold_start_*` (2) | `SWEDEN`, `BRAZIL`, `NORWAY`, `PAKISTAN` resolve to archetype priors with positive guests; tornado works for cold start |
| `test_uncertainty_is_deterministic` | Identical inputs give identical Monte Carlo bands |
| `test_api_validates_season_and_exposes_the_hybrid_model` | API returns 400 on an invalid season and hybrid fields on success |

---

## 10. Charts and PDF

```bash
twin charts              # output/figures/{waterfall_attribution,tornado_sensitivity,model_benchmark}.png
twin report solution     # output/pdf/challengeon_solution_report.pdf (3 pages; needs the 'report' extra)
twin report database     # output/pdf/challengeon_schema_database_report.pdf (needs lake/analytics.duckdb)
```

`model_benchmark.png` reads `lake/curated/evaluation_results.json`.
