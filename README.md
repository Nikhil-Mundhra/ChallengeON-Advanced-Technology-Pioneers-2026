# ChallengeON DCT Analytics Lake & Abu Dhabi Tourism Digital Twin

Analytics lake and scenario simulator for the [ChallengeON DCT Abu Dhabi Hackathon](https://challengeon.atrc.ae/en/challenges/atp2026/pages/dct-challenge-statement?lang=en). The twin converts aviation levers (weekly frequency, aircraft gauge, seats, load factor, P2P share, response multiplier, length of stay) into weekly hotel-guest effects by source market and season.

- Method, data contract, results, limitations: [docs/solution_documentation.md](docs/solution_documentation.md)
- CLI, web UI, Python API, outputs: [docs/user_guide.md](docs/user_guide.md)

---

## 1. Quickstart

```bash
make install                      # python3 -m venv .venv && .venv/bin/pip install -e ".[report,dev]"
source .venv/bin/activate         # 'report' = reportlab (PDFs), 'dev' = pytest
```

The raw competition workbooks are not in the repository. Place the organizer-provided files in `01a - DCT Dataset/` (or set `TWIN_SOURCE_DIR`) before `twin build-lake`. The curated lake tables and model artifacts in `lake/` are committed, so `simulate`, `serve`, `charts`, `report solution` and the tests run without the raw files.

`make all` rebuilds everything from the raw workbooks: lake → panels → evaluate → train → charts → report → test. With default settings it overwrites the committed lake artifacts; see [Configuration](#configuration) for a scratch rebuild.

| Step | Command (`make` target) | Writes |
| :--- | :--- | :--- |
| 1 | `twin build-lake` (`make lake`) | `lake/curated/{guest_daily,flight_daily,flight_monthly}.parquet`, `lake/analytics.duckdb`, `lake/manifest.json` |
| 2 | `twin build-panel` (`make panel`) | `lake/curated/weekly_market_panel.parquet` (reads the curated Parquet; no `analytics.duckdb` needed) |
| 2 | `twin build-daily-panel [--max-lag K]` (`make panel`) | `lake/curated/daily_market_panel.parquet` (gitignored; default K = 21) |
| 3 | `twin evaluate` (`make evaluate`) | `lake/curated/evaluation_results.json`; copies holdout coverage into `conformal_calibrator.json` |
| 4 | `twin train [--max-date 2025-07-27] [--panel-path P]` (`make train`) | `structural_calibration.json`, `residual_engine.pkl`, `conformal_calibrator.json` |
| 5 | `twin charts` (`make charts`) | `output/figures/*.png` |
| 6 | `twin report solution` (`make report`) | `output/pdf/challengeon_solution_report.pdf` |
| 7 | `pytest tests/ -v` (`make test`) | — |

Other commands:

```bash
twin simulate --market "UNITED KINGDOM" --season Winter_Peak --delta-freq 2.0 --gauge 290.0 --delta-lf 0.02
twin serve --port 8080                              # web UI + JSON API at http://127.0.0.1:8080
twin query "SELECT COUNT(*) FROM guest_daily_totals"  # SQL on lake/analytics.duckdb (created by build-lake)
twin report database                                # schema & database PDF (needs lake/analytics.duckdb)
```

Every command is also available as `python -m tourism_twin <command>`; `twin <command> --help` lists options.

**Tests:** 78 tests (54 in `tests/test_tourism_twin.py`, 24 in `tests/test_audit_agent.py`). On a fresh clone 77 pass and 1 skips: `test_monthly_flights_are_isolated_to_2022` needs `lake/curated/flight_monthly.parquet`, which `twin build-lake` creates and which is not committed.

### Configuration

All paths are defined in [`src/tourism_twin/config.py`](src/tourism_twin/config.py) and can be overridden by environment variables (read once at import):

| Variable | Default | Holds |
| :--- | :--- | :--- |
| `TWIN_ROOT` | repository root | Base for the defaults below |
| `TWIN_SOURCE_DIR` | `01a - DCT Dataset/` | Raw competition workbooks |
| `TWIN_LAKE_DIR` | `lake/` | DuckDB database, manifest, curated tables, model artifacts |
| `TWIN_OUTPUT_DIR` | `output/` | Figures and PDF reports |

```bash
TWIN_LAKE_DIR=/tmp/lake TWIN_OUTPUT_DIR=/tmp/output make all   # rebuild without touching the checkout
```

`make clean` removes only uncommitted generated files (`output/figures`, `output/pdf`, `lake/analytics.duckdb`, staging leftovers), honours the same variables, and never deletes committed lake artifacts.

---

## 2. Architecture

`src/tourism_twin/` is layered. Listed from the bottom up; each layer imports only from layers above it in this list:

```text
src/tourism_twin/
├── config.py      every file location (env-overridable, stdlib only)
├── domain/        value types and reference data: markets, archetypes, seasons, event weeks, scenario types
├── features/      FeatureRegistry: derived columns (ratios, flags, calendar, arrival lags) declared once
│                  with their inputs and resolved in dependency order
├── data/          raw workbooks → validated lake; LakeRepository (lake reader for the panel builders;
│                  DuckDB views over the curated Parquet); weekly and daily panels; imputation policy
├── models/        structural chain, residual calendar features, residual ML, uncertainty, conformal, training, evaluation
├── services/      simulator, tornado sensitivity, executive briefing
├── reporting/     scenario charts, solution PDF, schema & database PDF
└── cli/           the `twin` command
```

`src/app/` (`server.py` + `static/index.html`) is the web server; it calls `config`, `domain` and `services`. `src/audit_agent/` is a separate LLM data-audit tool ([manual](src/audit_agent/README.md)) and does not import `tourism_twin`.

Model components:

| Component | Module | What it does |
| :--- | :--- | :--- |
| Structural chain | `models/structural.py` | Seats × load factor → passengers × P2P share → P2P × response multiplier $M_{m,s}$ → hotel arrivals × length of stay $L_{m,s}$ → weekly guests, per market $m$ and season $s$. Sequential waterfall attribution over 5 levers; the parts sum to the total lift (tested to < 1e-9). |
| Residual ML | `models/residual.py`, `models/features.py` | One RidgeCV per market on week-of-year harmonics, quarter, season, holiday-week and major-event-week flags. No aviation inputs, so the residual does not change with capacity levers. Target: actual guests − planning-mode structural prediction (`StructuralEngine.planning_guests`: scheduled seats × calibrated seasonal priors), the same prediction the simulator serves. |
| Archetypes | `domain/archetypes.py` | 7 archetypes (Direct Leisure, Resident/VFR, Regional GCC, Hub-Mediated, Highly Seasonal, Emerging/Sparse, Domestic Staycation). Unmodeled countries (e.g. `SWEDEN`) get the default parameters of their archetype (cold start). |
| Uncertainty & sensitivity | `models/uncertainty.py`, `models/conformal.py`, `services/sensitivity.py` | Monte Carlo P10/P50/P90 from Beta draws of load factor and P2P share, parameter shocks and 4-week block-bootstrap residuals; per-market conformal margins; tornado ranking of lever swings. |

**Market bridge.** The data has no passenger-level link between departure country and guest nationality, and an unrestricted 45 × 33 nationality-by-country matrix (1,485 parameters) is not identifiable from aggregate weekly series. The twin links departure country $k$ to nationality $k$ and calibrates $M_{m,s} = \text{arrivals}_{m,s} / \text{P2P}_{m,s}$, which absorbs non-national passengers, indirect connections and overland arrivals.

---

## 3. Forward-holdout results

Calibration: 104 complete weeks (2023-01-02 to 2024-12-23 week starts, 2,132 market-weeks). Holdout: 30 complete weeks (2024-12-30 to 2025-07-21 week starts, 621 market-weeks, 21 markets). Only weeks with complete guest inputs are used. The back-test fits the shipped structural, residual and conformal trainers on the calibration window only. Bias = (Σ predicted − Σ actual) / Σ actual; positive means over-forecast. Source: `lake/curated/evaluation_results.json`.

| Setting | WMAPE | Bias | MAE | RMSE | Inputs |
| :--- | :---: | :---: | :---: | :---: | :--- |
| International planning | 27.52% | +1.52% | 2,466.5 | 3,920.7 | Scheduled seats + calibrated seasonal priors |
| International realized-chain | 24.54% | −5.67% | 2,199.9 | 3,308.7 | Realized P2P × calibrated multiplier × LOS |
| Domestic forecast | 16.04% | +13.05% | 17,485.2 | 21,078.9 | Calibrated seasonal prior; no holdout arrivals |
| Combined planning | 23.14% | +5.93% | 3,192.1 | 6,007.8 | International + domestic |
| Combined realized-chain | 21.30% | +1.48% | 2,938.3 | 5,646.6 | International + domestic |

| Model (all markets) | WMAPE | Bias | MAE | RMSE |
| :--- | :---: | :---: | :---: | :---: |
| 1. Historical seasonal prior (market-season mean) | 23.00% | −6.60% | 3,172.8 | 6,156.5 |
| 2. Pure ML / calendar (per-market ridge, no aviation) | 22.00% | −8.50% | 3,035.6 | 5,839.0 |
| 3. Structural only (planning mode) | 23.14% | +5.93% | 3,192.1 | 6,007.8 |
| 4. Hybrid digital twin (structural + residual) | **21.74%** | **+5.36%** | **2,999.2** | **5,673.6** |

The hybrid model is lowest on all four metrics (`benchmark_leaders`; bias by absolute value). Its WMAPE margin over the calendar model is 0.26 pp; the structural-only engine does not beat the seasonal prior on WMAPE.

Interval coverage on the holdout: 65.2% of market-weeks fall inside structural prediction × (1 ± per-market conformal margin), against a nominal 80%.

---

## 4. Data assets

| File | Grain | Rows | Contents |
| :--- | :--- | :--- | :--- |
| `lake/curated/guest_daily.parquet` | Nationality-day | 69,920 | 1,520 dates × (45 nationalities + domestic); presence and suppression flags |
| `lake/curated/flight_daily.parquet` | Route-airline-day | 116,395 | Daily flights from 2023-01-01; load-factor outlier flag |
| `lake/curated/flight_monthly.parquet` | Monthly | 1,213 | 2022 records on 12 month-start dates (built by `build-lake`; not committed) |
| `lake/curated/weekly_market_panel.parquet` | Market-week | 3,507 | 21 markets (top 15 + 5 regional clusters + `DOMESTIC`), both splits, 39 columns |
| `lake/curated/daily_market_panel.parquet` | Market-day | 31,920 | 21 markets × 1,520 days, both splits, arrival lags 0–21 (not committed) |
| `lake/curated/structural_calibration.json` | Market-season | 21 markets × 4 seasons | Calibrated seats, load factor, P2P share, multiplier, LOS |
| `lake/curated/residual_engine.pkl` | — | 21 models | RidgeCV residual models (plain dict of scikit-learn estimators) |
| `lake/curated/conformal_calibrator.json` | Market | 21 markets | Conformal margins, target alpha 0.2, demonstrated coverage |
| `lake/curated/evaluation_results.json` | — | — | Back-test metrics, benchmark leaders, market and season breakdowns |
| `lake/analytics.duckdb` | — | — | Query database with analytical views (built by `build-lake`; not committed) |

---

## 5. Deliverables

- Solution specification: [`docs/solution_documentation.md`](docs/solution_documentation.md)
- User guide and market directory: [`docs/user_guide.md`](docs/user_guide.md)
- Solution PDF: `output/pdf/challengeon_solution_report.pdf` (`twin report solution`)
- Schema & database PDF: `output/pdf/challengeon_schema_database_report.pdf` (`twin report database`)
- Web UI: `twin serve --port 8080`, then open `http://127.0.0.1:8080`
