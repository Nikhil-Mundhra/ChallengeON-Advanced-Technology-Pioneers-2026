# ChallengeON DCT Analytics Lake & Abu Dhabi Tourism Digital Twin

Analytics lake, daily guest nowcast and scenario simulator for the [ChallengeON DCT Abu Dhabi Hackathon](https://challengeon.atrc.ae/en/challenges/atp2026/pages/dct-challenge-statement?lang=en).

| Model | Question | Grain | Command |
| :--- | :--- | :--- | :--- |
| Daily nowcast (`twin_daily`) | Hotel guests on the withheld test days (2025-08-01 to 2026-02-28), given that period's new arrivals | Market-day, written per test-file row | `twin predict` |
| Weekly planning model | Guest effect of aviation levers (weekly frequency, aircraft gauge, seats, load factor, P2P share, response multiplier, stay factor) | Market × season, weekly | `twin simulate`, `twin serve` |

- Method, data contract, results, limitations: [docs/solution_documentation.md](docs/solution_documentation.md)
- CLI, web UI, Python API, outputs: [docs/user_guide.md](docs/user_guide.md)

---

## 1. Quickstart

```bash
make install                      # python3 -m venv .venv && .venv/bin/pip install -e ".[report,dev]"
source .venv/bin/activate         # 'report' = reportlab (PDFs), 'dev' = pytest
```

The raw competition workbooks are not in the repository. Place the organizer-provided files in `01a - DCT Dataset/` (or set `TWIN_SOURCE_DIR`). `twin build-lake` and `twin predict` read them. `lake/curated/{guest_daily,flight_daily,weekly_market_panel}.parquet` and the weekly model artifacts are committed, so `simulate`, `serve`, `charts`, `report solution` and the tests run without the raw files.

`make all` rebuilds the lake, panels, weekly evaluation and training, charts and report, then runs the tests. With default settings it overwrites the committed lake artifacts; see [Configuration](#configuration) for a scratch rebuild. `make all` does not run `twin predict`.

| Step | Command (`make` target) | Writes |
| :--- | :--- | :--- |
| 1 | `twin build-lake` (`make lake`) | `lake/curated/{guest_daily,flight_daily,flight_monthly}.parquet`, `lake/analytics.duckdb`, `lake/manifest.json` |
| 2 | `twin build-panel` (`make panel`) | `lake/curated/weekly_market_panel.parquet` |
| 2 | `twin build-daily-panel [--max-lag K]` (`make panel`) | `lake/curated/daily_market_panel.parquet` (not committed; default K = 21) |
| 3 | `twin evaluate` (`make evaluate`) | `lake/curated/evaluation_results.json` |
| 4 | `twin train [--max-date 2025-07-27] [--panel-path P]` (`make train`) | `structural_calibration.json`, `residual_engine.pkl`, `conformal_calibrator.json` (coverage read from `evaluation_results.json`) |
| 5 | `twin charts` (`make charts`) | `output/figures/*.png` |
| 6 | `twin report solution` (`make report`) | `output/pdf/challengeon_solution_report.pdf` |
| 7 | `pytest tests/ -v` (`make test`) | — |
| — | `twin predict [--spec S] [--no-intervals]` | `output/predictions/`: test-split Guests CSVs, P10/P50/P90 CSV, `market_outputs.json`, `test_predictions.png` |
| — | `twin ablate-blocks` | `output/nowcast_block_ablation.json`: WAPE of each block combination on 13 rolling origins |

`twin predict` builds the daily panel in memory from `guest_daily.parquet`; it does not need `daily_market_panel.parquet`.

Other commands:

```bash
twin simulate --market "UNITED KINGDOM" --season Winter_Peak --delta-freq 2.0 --gauge 290.0 --delta-lf 0.02
twin serve --port 8080                              # web UI + JSON API at http://127.0.0.1:8080
twin query "SELECT COUNT(*) FROM guest_daily_totals"  # SQL on lake/analytics.duckdb (created by build-lake)
twin report database                                # schema & database PDF (needs lake/analytics.duckdb)
```

Every command is also available as `python -m tourism_twin <command>`; `twin <command> --help` lists options.

**Tests:** 85 tests in folders that mirror the packages (`tests/{data,features,models,nowcast,planning,app,audit}/`; run one area with `pytest tests/<area>`); all pass on a fresh clone.

### Configuration

All paths are defined in [`src/tourism_twin/config.py`](src/tourism_twin/config.py) and can be overridden by environment variables (read once at import):

| Variable | Default | Holds |
| :--- | :--- | :--- |
| `TWIN_ROOT` | repository root | Base for the defaults below |
| `TWIN_SOURCE_DIR` | `01a - DCT Dataset/` | Raw competition workbooks |
| `TWIN_LAKE_DIR` | `lake/` | DuckDB database, manifest, curated tables, model artifacts |
| `TWIN_OUTPUT_DIR` | `output/` | Figures, PDF reports, predictions |

```bash
TWIN_LAKE_DIR=/tmp/lake TWIN_OUTPUT_DIR=/tmp/output make all   # rebuild without touching the checkout
TWIN_OUTPUT_DIR=/tmp/output twin predict                       # predictions outside the checkout
```

`make clean` removes only uncommitted generated files (`output/figures`, `output/pdf`, `lake/analytics.duckdb`, staging leftovers), honours the same variables, and never deletes committed lake artifacts.

---

## 2. Architecture

`src/tourism_twin/` is layered. Listed from the bottom up; each layer imports only from layers above it in this list:

```text
src/tourism_twin/
├── config.py      every file location (env-overridable, stdlib only)
├── domain/        value types and reference data: markets, archetypes, seasons, scenario types,
│                  event registry (events.csv) and the legacy holiday / major-event weeks
├── features/      FeatureRegistry: derived columns (ratios, flags, calendar, arrival lags, event-day
│                  offsets) declared once with their inputs and resolved in dependency order
├── data/          raw workbooks → validated lake; LakeRepository; weekly and daily panels; imputation
├── models/        shared model kernel
│   ├── components/   additive log-scale terms: LinearTrend, CentredSlope, LinearRegressors, EventKernel,
│   │                 AnnualFourier, DayOfWeek, LocalLevel, ArrivalsConvolution, ResidualGBM
│   ├── composite.py, fitters.py, protocol.py   AdditiveLogModel; JointLinear, Backfitting; Model (fit/predict)
│   └── backtest.py, noise.py                   harness (HoldoutSplit, RollingOrigin); interval model
├── nowcast/       daily competition model: specs (twin_daily), routing, baselines, predict (`twin predict`),
│                  nationality disaggregation, outputs JSON, same-day guests Poisson GLM
├── planning/      weekly scenario model: structural chain, residual, conformal, Monte Carlo, tornado
│                  sensitivity, simulator, briefing, training, weekly benchmark specs and evaluation
├── reporting/     scenario charts, test-prediction plot, solution PDF, schema & database PDF
└── cli/           the `twin` command
```

`src/app/` (`server.py` + `static/index.html`) is the web server; it calls `config`, `domain` and `planning`. `src/audit_agent/` is a separate LLM data-audit tool ([manual](src/audit_agent/README.md)) and does not import `tourism_twin`.

Model parts:

| Part | Module | What it does |
| :--- | :--- | :--- |
| Daily nowcast | `nowcast/specs.py` (`twin_daily`) | Per market, log guests = log(c_t + Σ_{k=0..21} w_k · arrivals_{t−k}) + season + weekday (+ events for international, + centred slope for domestic). `w` is a non-increasing lag-weight curve with w₀ ≤ 1: a fitting device, not a measured stay distribution. |
| Noise model | `models/noise.py` | AR(1) log errors along the horizon, fitted on rolling-origin back-test errors; Gaussian intervals in log. |
| Structural chain | `planning/structural.py` | Seats × load factor → passengers × P2P share → P2P × response multiplier $M_{m,s}$ → hotel arrivals × stay factor $L_{m,s}$ (guests ÷ hotel arrivals) → weekly guests, per market $m$ and season $s$. Sequential waterfall over 5 levers; the parts sum to the total lift (tested to < 1e-9). |
| Residual ML | `planning/residual.py`, `planning/calendar_features.py` | One RidgeCV per market on week-of-year harmonics, quarter, season, holiday-week and major-event-week flags. No aviation inputs. Target: actual guests − planning-mode structural prediction. |
| Archetypes | `domain/archetypes.py` | 7 archetypes; unmodeled countries (e.g. `SWEDEN`) get their archetype's default parameters (cold start). |
| Weekly uncertainty & sensitivity | `planning/uncertainty.py`, `planning/conformal.py`, `planning/sensitivity.py` | Monte Carlo P10/P50/P90, per-market conformal margins, tornado ranking. |

**Market bridge.** The data has no passenger-level link between departure country and guest nationality; a 45 × 33 nationality-by-country matrix (1,485 parameters) is not identifiable from aggregate weekly series. The planning model links departure country $k$ to nationality $k$ and calibrates $M_{m,s} = \text{arrivals}_{m,s} / \text{P2P}_{m,s}$.

---

## 3. Results

### 3.1 Daily nowcast (rolling-origin back-test)

8 monthly origins (2024-07-01 to 2025-02-01), 6-month horizon, model refitted before each origin. Mean fold WMAPE:

| Spec | Domestic | International |
| :--- | :---: | :---: |
| `naive_364` (same weekday 364 days earlier) | 20.4% | 26.6% |
| `arrivals_ratio` (arrivals × training guests / arrivals) | 15.9% | 19.2% |
| **`twin_daily`** | **6.2%** | **9.4%** |
| `twin_daily_gbm` (+ residual GBM; not shipped) | 6.2% | 9.1% |

80% interval coverage of `twin_daily`: 81.4% with each origin's intervals fitted on the other origins; 79.2% when origins within ±3 months are also excluded. Week-to-week direction accuracy (1,154 market-weeks, a nowcast given observed arrivals): 87.2% vs 83.4% for the direction of new arrivals and 63.1% for last year's direction. Details: [solution documentation §9.3](docs/solution_documentation.md#93-daily-nowcast).

### 3.2 Weekly planning model (forward holdout)

Calibration: 104 complete weeks (2023-01-02 to 2024-12-23 week starts, 2,132 market-weeks). Holdout: 30 complete weeks (2024-12-30 to 2025-07-21 week starts, 621 market-weeks, 21 markets). Bias = (Σ predicted − Σ actual) / Σ actual; positive means over-forecast. Source: `lake/curated/evaluation_results.json`.

| Setting | WMAPE | Bias | MAE | RMSE | Inputs |
| :--- | :---: | :---: | :---: | :---: | :--- |
| International planning | 27.52% | +1.52% | 2,466.5 | 3,920.7 | Scheduled seats + calibrated seasonal priors |
| International realized-chain | 24.54% | −5.67% | 2,199.9 | 3,308.7 | Realized P2P × calibrated multiplier × stay factor |
| Domestic forecast | 16.04% | +13.05% | 17,485.2 | 21,078.9 | Calibrated seasonal prior; no holdout arrivals |
| Combined planning | 23.14% | +5.93% | 3,192.1 | 6,007.8 | International + domestic |
| Combined realized-chain | 21.30% | +1.48% | 2,938.3 | 5,646.6 | International + domestic |

| Model (all markets) | WMAPE | Bias | MAE | RMSE |
| :--- | :---: | :---: | :---: | :---: |
| 1. Historical seasonal prior (market-season mean) | 23.00% | −6.60% | 3,172.8 | 6,156.5 |
| 2. Pure ML / calendar (per-market ridge, no aviation) | 22.00% | −8.50% | 3,035.6 | 5,839.0 |
| 3. Structural only (planning mode) | 23.14% | +5.93% | 3,192.1 | 6,007.8 |
| 4. Hybrid digital twin (structural + residual) | **21.74%** | **+5.36%** | **2,999.2** | **5,673.6** |

The hybrid is lowest on all four metrics; its WMAPE margin over the calendar model is 0.26 pp. Interval coverage: 65.2% of holdout market-weeks fall inside structural prediction × (1 ± per-market conformal margin), against a nominal 80%.

The two tables are not comparable: the nowcast uses the predicted period's new arrivals, the planning model does not.

---

## 4. Data assets

| File | Grain | Rows | Contents |
| :--- | :--- | :--- | :--- |
| `lake/curated/guest_daily.parquet` | Nationality-day | 69,920 | 1,520 dates × (45 nationalities + domestic); presence and suppression flags |
| `lake/curated/flight_daily.parquet` | Route-airline-day | 116,395 | Daily flights from 2023-01-01; load-factor outlier flag |
| `lake/curated/flight_monthly.parquet` | Monthly | 1,213 | 2022 records on 12 month-start dates (built by `build-lake`; not committed) |
| `lake/curated/weekly_market_panel.parquet` | Market-week | 3,507 | 21 markets (top 15 + 5 regional clusters + `DOMESTIC`), both splits, 39 columns |
| `lake/curated/daily_market_panel.parquet` | Market-day | 31,920 | 21 markets × 1,520 days, both splits, arrival lags 0–21 (not committed) |
| `lake/curated/structural_calibration.json` | Market-season | 21 markets × 4 seasons | Calibrated seats, load factor, P2P share, multiplier, stay factor |
| `lake/curated/residual_engine.pkl` | — | 21 models | RidgeCV residual models |
| `lake/curated/conformal_calibrator.json` | Market | 21 markets | Conformal margins, target alpha 0.2, demonstrated coverage |
| `lake/curated/evaluation_results.json` | — | — | Weekly back-test metrics, benchmark leaders, market and season breakdowns |
| `lake/analytics.duckdb` | — | — | Query database with analytical views (built by `build-lake`; not committed) |
| `src/tourism_twin/domain/events.csv` | Event occurrence | 52 | Event, kind, anchor date, window offsets, market scope, label, source; 2022–2026 |

---

## 5. Outputs

| Output | Command |
| :--- | :--- |
| `output/predictions/domestic_test_guests.csv`, `international_test_guests.csv` | `twin predict` (test workbooks row for row + `Guests`) |
| `output/predictions/test_guests_intervals.csv` | `twin predict` (P10/P50/P90; not written with `--no-intervals`, nor is `market_outputs.json`) |
| `output/predictions/test_total_guests.csv` | `twin predict` (daily total guests with its own P10/P90) |
| `output/predictions/nowcast_serving.json` | `twin predict` (read by `/api/nowcast/*`) |
| `output/predictions/market_outputs.json`, `test_predictions.png` | `twin predict` |
| `output/figures/{waterfall_attribution,tornado_sensitivity,model_benchmark}.png` | `twin charts` |
| `output/pdf/challengeon_solution_report.pdf` | `twin report solution` |
| `output/pdf/challengeon_schema_database_report.pdf` | `twin report database` |
| Web UI and JSON API at `http://127.0.0.1:8080` | `twin serve --port 8080` |
