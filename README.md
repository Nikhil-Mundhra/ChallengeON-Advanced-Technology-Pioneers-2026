# ChallengeON DCT Analytics Lake & Abu Dhabi Tourism Digital Twin

Analytics lake, daily guest nowcast and scenario simulator for the [ChallengeON DCT Abu Dhabi Hackathon](https://challengeon.atrc.ae/en/challenges/atp2026/pages/dct-challenge-statement?lang=en).

| Model | Question | Grain | Command |
| :--- | :--- | :--- | :--- |
| Daily nowcast (`twin_daily`) | Hotel guests on the withheld test days (2025-08-01 to 2026-02-28), given that period's new arrivals | Market-day, written per test-file row | `twin predict` |
| Weekly planning model | Guest effect of aviation levers (weekly frequency, aircraft gauge, seats, load factor, P2P share, response multiplier, stay factor) | Market × season, weekly | `twin simulate`, web app `/simulate` |

- Method, data contract, results, limitations: [docs/solution_documentation.md](docs/solution_documentation.md)
- CLI, web app, Python API, outputs: [docs/user_guide.md](docs/user_guide.md)

---

## 1. Quickstart

```bash
make install                      # python3 -m venv .venv && .venv/bin/pip install -e ".[report,dev]"
source .venv/bin/activate         # 'report' = reportlab (PDFs), 'dev' = pytest
```

The raw competition workbooks are not in the repository. Place the organizer-provided files in `01a - DCT Dataset/` (or set `TWIN_SOURCE_DIR`). `twin build-lake` and `twin predict` read them. `lake/curated/{guest_daily,flight_daily,weekly_market_panel}.parquet` and the weekly model artifacts are committed, so `simulate`, `serve`, `charts`, `report solution` and the tests run without the raw files.

`make all` rebuilds the lake, panels, weekly evaluation and training, charts and report, then runs the tests. With default settings it overwrites the committed lake artifacts; see [Configuration](#configuration) for a scratch rebuild. `make all` does not run `twin predict`, which builds the daily panel in memory from `guest_daily.parquet` (no `daily_market_panel.parquet` needed).

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
| — | `twin predict [--spec S] [--no-intervals]` | `output/predictions/` (§5) |
| — | `twin evaluate-model --spec S --start D --end D [--frozen-test]` | `output/models/*.pkl`, `output/evaluations/*.json`: a spec fitted up to `--start` minus 21 days, scored without refitting |
| — | `twin validate` (`make validate`) | `output/validation_summary.json`: the §3.1 numbers (segment WAPE per spec, `compare` rows, nationality results) on `VALIDATION_ORIGINS` |
| — | `twin outlook [--winter Y] [--spec S]` | `output/outlook.json`: guests for Dec Y – Feb Y+1 (default 2026/27) under flat and trend arrivals scenarios, with the procedure's back-test |
| — | `twin export [--out web/public/data] [--spec twin_daily]` (`make export`) | Versioned JSON bundle the web app reads (§2) |
| — | `twin ablate-blocks` | `output/nowcast_block_ablation.json`: WAPE of each block combination on 13 origins 2024-02..2025-02 (exploratory: they overlap the frozen test) |

Other commands (each also `python -m tourism_twin <command>`; `twin <command> --help` lists options):

```bash
twin simulate --market "UNITED KINGDOM" --season Winter_Peak --delta-freq 2.0 --gauge 290.0 --delta-lf 0.02
make up                                             # web app http://localhost:5180, Python API :8090 (make down/status/logs)
twin query "SELECT COUNT(*) FROM guest_daily_totals"  # SQL on lake/analytics.duckdb (created by build-lake)
twin report database                                # schema & database PDF (needs lake/analytics.duckdb)
```

**Tests:** 91 Python tests in folders that mirror the packages (`tests/{data,features,models,nowcast,planning,reporting,app,audit}/`; run one area with `pytest tests/<area>`); all pass (the prediction-validator test skips without the raw test workbooks). `make web-test`: 7 parity tests of the web engine against the bundle. `make backend` = test + export; `make frontend` = web install, test, build.

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
│   │                 AnnualFourier, DayOfWeek, LocalLevel, ArrivalsConvolution, GroupScale, ResidualGBM
│   ├── spec.py, registry.py, handler.py, weighting.py   ModelSpec; component/fitter names; row rules; weights
│   ├── composite.py, fitters.py, linear_solve.py         AdditiveLogModel; JointLinear, Backfitting; least squares
│   └── backtest.py, evaluate.py, noise.py                harness and #11 protocol; scoring a saved model; intervals
├── nowcast/       daily competition model: specs (twin_daily), routing, baselines, predict (`twin predict`),
│                  pooled nationalities, disaggregation, submission, weekly, outputs, serving, same-day GLM
├── planning/      weekly scenario model: structural chain, residual, conformal, Monte Carlo, tornado
│                  sensitivity, simulator, briefing, training, weekly benchmark specs and evaluation
├── reporting/     scenario charts, test-prediction plot, solution PDF, schema & database PDF, deck
├── export/        the web bundle (`twin export`); sibling of reporting/
└── cli/           the `twin` command
```

**Web app** (`web/`: Vite 6, React 19, TypeScript, Recharts 3, react-router 7): a static site with no backend at request time (Vercel-ready via `web/vercel.json`). Routes: `/report` (long-form report, copy in `web/src/content/report.ts`), `/simulate` (levers, conversion chain, waterfall, tornado, weekly back-test and 3-year projection), `/nowcast` (daily nowcast, range intervals, arrivals what-if). It reads `web/public/data/manifest.json` → `<version>/{nowcast,whatif,planning,weekly,golden}.json`; `web/src/engine/` ports the model maths to TypeScript and `parity.test.ts` checks it against `golden.json` (1e-9; what-if and range cases 1e-6). The model outputs are read-only and versioned, so the bundle is the store; the Python closure (pandas, scikit-learn, scipy, duckdb) is too large for a serverless function. `src/app/` (`server.py` + `static/index.html`; `twin serve --port`, or `python -m app.server` with `PORT`, default 8080) is the earlier web UI and JSON API; it calls `config`, `domain`, `planning` and `nowcast.serving`. `src/audit_agent/` is a separate LLM data-audit tool ([manual](src/audit_agent/README.md)) and does not import `tourism_twin`.

Model parts:

| Part | Module | What it does |
| :--- | :--- | :--- |
| Daily nowcast | `nowcast/specs.py` (`twin_daily`) | Per market, log guests = log(c_t + Σ_{k=0..21} w_k · arrivals_{t−k}) + season + weekday (+ events for international, + centred slope for domestic). `w` is a non-increasing lag-weight curve with w₀ ≤ 1: a fitting device, not a measured stay distribution. |
| Nationality model | `nowcast/pooling.py` (`POOLED_NATIONALITIES`) | The 30 pooled-market nationalities: one fit per stay family on each nationality's own arrivals, shared kernel and calendar, per-nationality scale (`GroupScale`, ridge 100), recency weights (half-life 365 days). |
| Noise model | `models/noise.py` | AR(1) log errors along the horizon, fitted on rolling-origin back-test errors; Gaussian intervals in log; `range_interval` for sums over days. |
| Structural chain | `planning/structural.py` | Seats × load factor → passengers × P2P share → P2P × response multiplier $M_{m,s}$ → hotel arrivals × stay factor $L_{m,s}$ (guests ÷ hotel arrivals) → weekly guests, per market $m$ and season $s$. Sequential waterfall over 5 levers; the parts sum to the total lift (tested to < 1e-9). |
| Residual ML | `planning/residual.py`, `planning/calendar_features.py` | One RidgeCV per market on week-of-year harmonics, quarter, season, holiday-week and major-event-week flags. No aviation inputs. Target: actual guests − planning-mode structural prediction. |
| Archetypes | `domain/archetypes.py` | 7 archetypes; unmodeled countries (e.g. `SWEDEN`) get their archetype's default parameters (cold start). |
| Weekly uncertainty & sensitivity | `planning/uncertainty.py`, `planning/conformal.py`, `planning/sensitivity.py` | Monte Carlo P10/P50/P90, per-market conformal margins, tornado ranking. |

**Market bridge.** The data has no passenger-level link between departure country and guest nationality; a 45 × 33 nationality-by-country matrix (1,485 parameters) is not identifiable from aggregate weekly series. The planning model links departure country $k$ to nationality $k$ and calibrates $M_{m,s} = \text{arrivals}_{m,s} / \text{P2P}_{m,s}$.

---

## 3. Results

### 3.1 Daily nowcast (validation, issue #11 protocol)

Validation origins: monthly 2024-02-01 to 2024-08-01, horizon up to 6 months ending by 2025-01-31, training ending 21 days before each origin (expanding window). The frozen test (2025-02-01 to 2025-07-31) is scored once, after all choices. Grain: WAPE % of **daily segment totals**, mean over the 7 folds.

| Spec | Domestic | International |
| :--- | :---: | :---: |
| `naive_364` (same weekday 364 days earlier) | 16.91% | 22.97% |
| `arrivals_ratio` (arrivals × training guests / arrivals) | 17.93% | 8.86% |
| `time_only` (level + season + weekday + events, no arrivals) | 10.10% | 10.68% |
| `flow_only` (arrivals kernel alone) | 9.55% | 5.44% |
| `flow_time` (kernel + calendar, no events) | 4.18% | 4.42% |
| **`twin_daily`** (shipped) | **4.18%** | **4.59%** |

At market grain (row-level, `models/backtest.compare`, 90% moving-block bootstrap), `twin_daily` beats `naive_364` by 12.71 pp [10.43, 15.45] (domestic) and 18.42 pp [16.87, 19.98] (international), 7/7 folds; removing the events costs international markets 0.37 pp [0.11, 0.67], 7/7 folds. On segment totals events partly cancel across markets, hence `flow_time` ≤ `twin_daily` for the international total. Nationality grain (#16): pooled-market nationalities predicted by `POOLED_NATIONALITIES`, international nationality WAPE 12.24% vs 12.79% for the arrival-share split on validation, frozen test 11.16% vs 11.38%. Earlier 8-origin figures overlap the frozen test and are exploratory ([solution documentation §9.3](docs/solution_documentation.md#93-daily-nowcast)).

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

The hybrid is lowest on all four metrics; its WMAPE margin over the calendar model is 0.26 pp. Interval coverage: 65.2% of holdout market-weeks fall inside structural prediction × (1 ± per-market conformal margin), against a nominal 80%. The two tables are not comparable: the nowcast uses the predicted period's new arrivals, the planning model does not.

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
| `src/tourism_twin/domain/events.csv` | Event occurrence | 63 | Event, kind, anchor date, window offsets, scope (all, international, a market or a pooled-market nationality), label, source; 2021–2027 |

---

## 5. Outputs

| Output | Command |
| :--- | :--- |
| `output/predictions/`: `{domestic,international}_test_guests.csv` (test workbooks row for row + `Guests`), `test_total_guests.csv` (daily total with its own P10/P90), `test_predictions.png`; with intervals only: `test_guests_intervals.csv` (P10/P50/P90), `market_outputs.json`, `nowcast_serving.json` (read by `/api/nowcast/*`) | `twin predict` |
| `output/evaluations/*.json` | `twin evaluate-model` |
| `output/figures/{waterfall_attribution,tornado_sensitivity,model_benchmark}.png` | `twin charts` |
| `output/pdf/challengeon_solution_report.pdf` | `twin report solution` |
| `output/pdf/challengeon_schema_database_report.pdf` | `twin report database` |
| `output/validation_summary.json` | `twin validate` |
| `output/outlook.json` | `twin outlook` |
| `web/public/data/` (committed): `manifest.json` + one versioned folder | `twin export` (`make export` replaces the folder) |
| Earlier web UI and JSON API at `http://127.0.0.1:8080` | `twin serve --port 8080` |
