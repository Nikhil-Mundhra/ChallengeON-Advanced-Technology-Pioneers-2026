# Abu Dhabi Tourism Digital Twin — Solution and Technical Specification

**Challenge:** DCT Abu Dhabi — Advanced Technology Pioneers 2026 ([challenge statement](https://challengeon.atrc.ae/en/challenges/atp2026/pages/dct-challenge-statement?lang=en))
**Status:** working prototype: CLI, web UI and JSON API, PDF reports, forward-holdout back-test, 78 automated tests.
**Run instructions:** [README](../README.md) and [user guide](user_guide.md).

## 1. Summary

The twin estimates how a change in air connectivity changes weekly hotel guests for a source market and season. A planner changes weekly frequency, aircraft gauge, seat capacity, load factor, P2P share, response multiplier or length of stay and gets:

- baseline vs. scenario at every step of the seats → guests chain;
- the lift attributed to each lever (waterfall);
- the structural lift plus a residual ML adjustment (hybrid);
- a P10/P50/P90 range and a tornado ranking of lever sensitivity;
- a plain-language briefing.

Two model layers: a structural conversion chain calibrated per market and season, and a per-market residual model on calendar and event features only.

## 2. Problem

Flight data records departure country; hotel data records guest nationality. Arriving passengers may transfer, transit, be returning residents, stay with friends or relatives, or arrive overland. A change in seats therefore does not map one-to-one to hotel demand. Questions the tool answers:

- Hotel demand from a new twice-weekly route.
- Effect of a change in aircraft size or load factor.
- Guests generated per added seat, by market and season.
- Exposure of a market-season to a capacity cut.
- Which assumption drives the result most.

**Not in scope:** individual-traveler prediction or profiling; passenger itinerary reconstruction; causal claims from observational data; occupancy (no room-inventory data); identifying nationality, purpose or hotel choice from flight aggregates.

## 3. Challenge requirements

| Requirement | Implementation |
| --- | --- |
| Working simulator | `twin simulate`, `twin serve` (web UI + JSON API), Python API |
| Adjustable conversion chain | 7 levers over seats → passengers → P2P → hotel arrivals → guests; every stage shown baseline vs. scenario |
| Historical validation | Forward holdout (104 calibration weeks, 30 holdout weeks): WMAPE, bias, MAE, RMSE, interval coverage; 4-model benchmark |
| Sensitivity analysis | Tornado ranking; Monte Carlo P10/P50/P90 |
| Granularity | 21 markets × 4 seasons; weekly grain; market and season error breakdowns |
| Decision relevance | Generated briefing naming the lift, range and top driver |
| Reproducibility | Source hashes in `lake/manifest.json`, env-configurable paths, `make all` from raw workbooks, seeded deterministic Monte Carlo, tests |

## 4. Data

Source workbooks are read from `01a - DCT Dataset/` (organizer-provided, not redistributed; SHA-256 of each file in `lake/manifest.json`).

| Dataset | Grain and coverage | Fields | Use |
| --- | --- | --- | --- |
| International guests, train | Nationality-day, 2022-01-01 to 2025-07-31 | Guests, new arrivals, same-day guests | Calibration, back-test |
| International guests, test | Nationality-day, 2025-08-01 to 2026-02-28 | New arrivals, same-day guests (Guests withheld) | Competition forecast inputs |
| Domestic guests, train/test | Day | Guests, new arrivals, same-day guests | Separate domestic prior |
| Flights | Route-airline-date, 2022 (monthly) and 2023-01-01 to 2026-02-28 (daily) | Seats, pax, P2P, transfer, transit, load factor, frequency, origin, airline | Structural chain |
| Data dictionary | 8-page PDF; documents the two test guest files and the flight file only, lists `Guests` in the test files (absent there), lists 6 international / 5 domestic columns (the files have 5 / 4) and calls the flight file monthly (daily from 2023) | Field definitions | Reference |

### 4.1 Lake (`twin build-lake`)

| Check (`lake/manifest.json`) | Value |
| --- | --- |
| `guest_daily` rows (1,520 dates × 45 nationalities + domestic) | 69,920 |
| Source-present guest rows / absent grid rows | 69,344 / 576 |
| Present rows, train / test | 59,930 / 9,414 |
| Flight rows total / daily (2023+) / monthly (2022) | 117,608 / 116,395 / 1,213 |
| Flight rows with load factor > 100% (kept, flagged) | 9,896 |
| Duplicate candidate keys (guest, flight) | 0, 0 |
| Passenger identity mismatches (`Total PAX = P2P + Transfer + Transit`) | 0 |

`twin build-lake` aborts unless duplicate keys, train rows missing `Guests`, test rows with `Guests`, passenger identity mismatches, rows with `new_arrivals > guests` and negative guest or arrival counts are all 0, and load factor equals pax ÷ seats within 1e-9 (`data/validation.py`).

### 4.2 Data findings that shape the model

1. Guests: 1,308 labeled days followed by 212 test days.
2. 45 guest nationalities vs. 33 flight departure countries; the fields are not semantically equivalent even when labels match. 12 nationalities have no flight-origin rows: Australia, Brazil, Czechia, Denmark, Finland, Mexico, Morocco, Norway, Pakistan, Romania, South Africa, Sweden.
3. 2022 flights exist on only 12 month-start dates; daily flights start 2023-01-01. Joint flight–guest modeling starts in 2023; 2022 flights are isolated in `flight_monthly.parquet`, so the `guest_flight_daily` view (joined to `flight_daily`) has NULL flight measures for 2022 dates (its load-factor outlier count is 0).
4. `*` in the source (suppressed / unavailable) is kept as null, never zero: 264 new-arrival and 39,428 same-day values, flagged by `is_suppressed_arrival` / `is_suppressed_same_day` (840 and 40,004 including the 576 absent grid rows, which are flagged too). Same-day guests never exceed guests.
5. Domestic demand is modeled separately; international flight changes do not create domestic guests.
6. Realized pax, P2P, load factor and new arrivals are valid for calibration but unknown before a future flight operates.
7. International train-split guests ÷ new arrivals = 3.61 (stock-to-flow ratio, not a measured length of stay).

### 4.3 Modeling panels

| Panel | Command | Grain | Contract |
| --- | --- | --- | --- |
| `weekly_market_panel.parquet` | `twin build-panel` | Market × Monday–Sunday week × split; 3,507 rows, 39 columns, week starts 2022-12-26 to 2026-02-23 | Flights and guests matched by date and market before weekly aggregation; weeks crossing the train/test boundary are split, not merged; `is_complete_week`, `is_complete_guest_inputs` flags; `load_factor_raw` kept unclipped with `is_load_factor_outlier`, `load_factor` clipped to [0, 1] |
| `daily_market_panel.parquet` (not committed) | `twin build-daily-panel [--max-lag K]` | Market × day, both splits; 31,920 rows (21 × 1,520) | Arrival lags `arrivals_lag_0..K` (default K = 21) built over the concatenated train + test series, so the first test days take lags from the last train days; `lag_complete` marks rows with a full lag window. Suppressed or absent nationality-day arrivals are linearly interpolated within each nationality's series into `new_arrivals_filled` (counts in `n_arrivals_interpolated`, `n_absent_records`); observed `new_arrivals` leaves them missing, so weekly sums of daily `guests` and `new_arrivals` equal the weekly panel exactly (tested) |

Markets: the top 15 nationalities by training guest volume, 5 regional clusters (`OTHER_EUROPE`, `OTHER_ASIA_PACIFIC`, `OTHER_MENA`, `OTHER_AMERICAS_AFRICA`, `OTHER_EURASIA`) and `DOMESTIC`. Both panels use the same SQL market mapping (`build_market_case`).

The daily panel is input for a planned stock-flow guest model (§11); no shipped model reads it yet.

Derived columns of both panels (ratios, flags, calendar fields, archetype, arrival lags) are defined once in `src/tourism_twin/features/` and resolved by `FeatureRegistry` in dependency order. Ratios are computed from summed parts at the panel's grain, never averaged. Both panel builders read the lake through `LakeRepository` (`data/repository.py`); the weekly panel's SQL runs on in-memory DuckDB views over the curated Parquet, so `twin build-panel` does not need `lake/analytics.duckdb`. `models/` (structural, training, evaluation) read `weekly_market_panel.parquet` directly.

## 5. Architecture

```mermaid
flowchart LR
    A[Source workbooks] --> B[Validated lake: Parquet + manifest]
    B --> C[Weekly and daily panels via FeatureRegistry]
    C --> D[Structural engine]
    C --> E[Residual ML]
    D --> F[Hybrid prediction]
    E --> F
    F --> G[Uncertainty and sensitivity]
    G --> H[CLI / web UI / API / PDF]
```

Package layout: [README §2](../README.md#2-architecture).

## 6. Operating modes

| Mode | Purpose | Allowed inputs |
| --- | --- | --- |
| Planning | Pre-flight decisions; what the simulator serves | Scheduled seats, planner levers, calibrated seasonal priors. No realized pax, P2P or hotel arrivals for the predicted period |
| Realized-chain (diagnostic) | Isolates error in the downstream stages | Realized P2P × calibrated multiplier × LOS |
| Forecast | Predicting the withheld competition `Guests` | May use test-period new arrivals, which the test files contain |

Results from different modes are reported separately.

## 7. Model

### 7.1 Structural chain (`models/structural.py`)

Per market $m$ and season $s$, calibrated from the mean of weekly seats, pax, P2P, arrivals and guests in the training window:

```text
LF        = mean pax / mean seats
P2PShare  = mean P2P / mean pax
M[m,s]    = mean hotel arrivals / mean P2P        (effective response multiplier)
L[m,s]    = mean guests / mean hotel arrivals     (stay factor)

Guests = Seats × LF × P2PShare × M × L
```

- **Market bridge.** Departure country $k$ is linked to nationality $k$. $M_{m,s}$ absorbs non-national passengers, indirect connections and overland arrivals (e.g. via DXB). A full 45 × 33 country-to-nationality matrix (1,485 parameters) is not identifiable from aggregate weekly series and is not estimated.
- **Planning prediction** (`planning_guests`): scheduled seats × calibrated LF, P2P share, $M$, $L$. A served market with zero seats has zero aviation arrivals; an unserved market keeps its calibrated arrivals; `DOMESTIC` = calibrated arrivals × $L$, independent of seats.
- **Cold start.** A country without calibration gets its archetype's default LF, P2P share, $M$ and $L$ (`domain/archetypes.py`; unknown countries map to Emerging / Sparse).
- **Waterfall.** The scenario lift is attributed sequentially: seats, load factor, P2P share, multiplier, LOS. The five parts sum to the total lift (tested to < 1e-9 for every calibrated market, a cold-start market, all seasons and 6 lever sets).

### 7.2 Residual ML (`models/residual.py`, `models/features.py`)

```text
Hybrid = max(0, planning_guests + residual)
```

One `RidgeCV` per market. Features: two week-of-year sine/cosine harmonic pairs, quarter dummies, winter and summer flags, holiday-week flag (Eid al-Fitr, Eid al-Adha, UAE National Day, New Year / festive weeks) and major-event-week flag (e.g. ADIPEC, Formula 1). Target: actual guests − `planning_guests`, so training and serving use the same structural prediction. No aviation inputs: the residual does not change with a capacity lever, so the hybrid lift equals the structural lift unless the max(0, ·) floor binds (tested: lift ≥ 0 for +2 flights in 5 markets).

### 7.3 Domestic demand

`DOMESTIC` uses its calibrated seasonal arrivals × LOS. Seat, frequency, load-factor and P2P levers have no effect; multiplier and LOS levers do (tested).

### 7.4 Uncertainty and sensitivity (`models/uncertainty.py`, `models/conformal.py`, `services/sensitivity.py`)

| Component | Method |
| --- | --- |
| Monte Carlo (1,500 draws default) | Load factor and P2P share ~ Beta (method-of-moments, sd 0.03 and 0.04); multiplier and LOS × Normal(1, 0.06) and Normal(1, 0.04); residuals by 4-week block bootstrap of the market's weekly training residuals. Seed derived from the scenario via SHA-256, so identical inputs give identical bands |
| Conformal margin | Per market: (1 − α) quantile of in-sample relative planning-mode error on the training window, α = 0.2 |
| Tornado | Guest swing for ±15% seats, ±4 pp LF, ±5 pp P2P share, ±10% multiplier, ±0.5 days LOS; cold-start markets use a reference route |

## 8. Archetypes

Seven archetypes assigned per market in `domain/archetypes.py`: Direct Leisure, Resident / VFR, Regional GCC, Hub-Mediated, Highly Seasonal, Emerging / Sparse, Domestic Staycation. Each carries default LF, P2P share, multiplier and LOS used for cold start. They describe aggregate market behavior, not traveler demographics. Per-market assignment: [user guide §4](user_guide.md#4-market-directory).

## 9. Validation

### 9.1 Design

- Single forward split over complete train-split weeks with complete guest inputs: calibration 2023-01-02 to 2024-12-23 week starts (104 weeks, 2,132 market-weeks); holdout 2024-12-30 to 2025-07-21 week starts (30 weeks, 621 market-weeks, 21 markets). No random splits.
- `twin evaluate` fits the shipped trainers (`StructuralEngine.calibrate`, `ResidualMLEngine.fit`, `calibrate_conformal`) on the calibration window only.
- WMAPE = Σ|actual − predicted| / Σ actual. Bias = (Σ predicted − Σ actual) / Σ actual; positive = over-forecast.
- Baselines: (1) market-season mean of training guests; (2) per-market ridge on calendar features only; (3) structural planning prediction; (4) hybrid.
- Output: `lake/curated/evaluation_results.json`.

### 9.2 Results

| Setting | WMAPE | Bias | MAE | RMSE |
| :--- | :---: | :---: | :---: | :---: |
| International planning | 27.52% | +1.52% | 2,466.5 | 3,920.7 |
| International realized-chain | 24.54% | −5.67% | 2,199.9 | 3,308.7 |
| Domestic forecast | 16.04% | +13.05% | 17,485.2 | 21,078.9 |
| Combined planning | 23.14% | +5.93% | 3,192.1 | 6,007.8 |
| Combined realized-chain | 21.30% | +1.48% | 2,938.3 | 5,646.6 |

| Model (all markets) | WMAPE | Bias | MAE | RMSE |
| :--- | :---: | :---: | :---: | :---: |
| 1. Historical seasonal prior | 23.00% | −6.60% | 3,172.8 | 6,156.5 |
| 2. Pure ML / calendar | 22.00% | −8.50% | 3,035.6 | 5,839.0 |
| 3. Structural only | 23.14% | +5.93% | 3,192.1 | 6,007.8 |
| 4. Hybrid digital twin | **21.74%** | **+5.36%** | **2,999.2** | **5,673.6** |

Combined planning mode by season (structural prediction):

| Season | Market-weeks | WMAPE | Bias |
| :--- | :---: | :---: | :---: |
| Winter_Peak | 292 | 27.92% | +9.65% |
| Spring_Shoulder | 168 | 21.24% | +4.86% |
| Summer_Trough | 161 | 16.40% | +0.23% |

Autumn_Shoulder is not in the holdout window. Per-market results are in `market_breakdown` of `evaluation_results.json`.

Findings:

1. The hybrid model is best on all four metrics (`benchmark_leaders`; bias by absolute value). Its WMAPE lead over the calendar-only model is 0.26 pp.
2. The structural-only engine (23.14%) does not beat the seasonal prior (23.00%) on WMAPE.
3. International planning mode, which uses no realized operational data, has 27.52% WMAPE and +1.52% bias.
4. The domestic prior over-forecast the holdout by 13.05%: 2025 domestic guests were below the 2023–2024 seasonal level.
5. Interval coverage: 65.2% of holdout market-weeks fall inside structural prediction × (1 ± conformal margin), against a nominal 80%.

## 10. Tests

78 tests: 54 in `tests/test_tourism_twin.py` (lake grain contract, feature registry, weekly and daily panel contracts, daily-to-weekly reconciliation, waterfall identity, route closure, domestic decoupling, monotonicity, cold start, deterministic uncertainty, API validation, model components, event registry, back-test harness) and 24 in `tests/test_audit_agent.py`. On a fresh clone 77 pass and 1 skips (`test_monthly_flights_are_isolated_to_2022` needs `flight_monthly.parquet` from `twin build-lake`). Details: [user guide §9](user_guide.md#9-tests).

## 11. Limitations and planned work

| Limitation | Consequence | Current handling |
| --- | --- | --- |
| Departure country used as proxy for nationality | Misallocated market impact | Calibrated effective multiplier; planner-adjustable; documented |
| Interval coverage 65.2% vs. 80% nominal | P10–P90 ranges are too narrow on the 2025 holdout | Coverage reported with every briefing |
| Domestic prior over-forecast 2025 by 13.05% | Domestic baseline too high for 2025 conditions | Reported; domestic modeled separately |
| Stay factor $L$ is a stock-to-flow ratio, not a measured length of stay | LOS lever is an approximation | Planned stock-flow model (below) |
| Structural-only accuracy does not beat the seasonal prior | Structural chain is for scenario attribution more than for point forecasting | Hybrid reported alongside |
| Cold-start markets use archetype defaults | Weak estimates for new origins | Flagged `is_cold_start` in results |
| No room inventory | Occupancy cannot be reported | Output is guests, not occupancy |
| No bookings, room rates, marketing spend, airfares, visa or macroeconomic data | Demand drivers beyond arrivals and the calendar are not modelled | Stated as a scope limit |
| Single forward split | One holdout period; no Autumn_Shoulder weeks | Season breakdown reported |
| Observational data | No causal identification | Results described as planning estimates |

**Planned: stock-flow guest model.** Model daily guests as a convolution of past new arrivals, $\text{Guests}_t = \sum_{k=0}^{K} w_k \cdot \text{Arrivals}_{t-k}$, with $w_k$ the share of arrivals still in a hotel after $k$ nights. `daily_market_panel.parquet` supplies the lag inputs. Not implemented. Design, measured results and proposed code structure: [model design](model_design.md).

## 12. Open questions for the organizers

1. Are the 2022 flight records intended to be monthly and later records daily?
2. Does an absent nationality-day row mean zero guests or a missing report? (The dictionary does not say; 576 grid rows are absent.)
3. Will room inventory, occupancy, events, aircraft type or schedule files be provided?
4. Is the competition forecast scored on international and domestic guests jointly or separately?
5. Is hotel `Guests` an end-of-day stock, a daily occupied-guest count, or another convention?
6. Should a new route be allocated to nationality markets by planner input, a comparable-market prior, or both?

## 13. Responsible use

The data is aggregated and contains no passenger-level information. Outputs describe expected aggregate relationships and must not be used to infer individual behavior or protected characteristics. The simulator supports planning; it does not establish causal effects.

## 14. References

- [DCT Abu Dhabi challenge statement](https://challengeon.atrc.ae/en/challenges/atp2026/pages/dct-challenge-statement?lang=en)
- `01a - DCT Dataset/Data_Dictionary.pdf` (organizer-provided; not in the repository)
- [`../lake/manifest.json`](../lake/manifest.json)
- [`../README.md`](../README.md)
