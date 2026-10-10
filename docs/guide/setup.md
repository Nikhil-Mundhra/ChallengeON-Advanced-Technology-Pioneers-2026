# Setup

## Install

```bash
make install                # python3 -m venv .venv && .venv/bin/pip install -e ".[report,dev]"
source .venv/bin/activate
make web-install            # npm ci in web/
```

| Extra | Contents |
| --- | --- |
| `report` | reportlab, python-pptx, pyyaml (PDFs, deck) |
| `dev` | pytest |

Requirements: Python 3.10+ and Node 20+. The raw workbooks are not in the repository; `twin build-lake` and `twin predict` read them from `01a - DCT Dataset/` (or `TWIN_SOURCE_DIR`): `data domestic_train.xlsx`, `data domestic_test.xlsx`, `data international_train.xlsx`, `data international_test.xlsx`, `flight_data.xlsx`. The committed lake files ([lake](../data/lake.md#data-assets)) let `simulate`, `serve`, `charts`, `report solution` and the tests run without them.

## Pipeline (`make all`)

`make all` runs the steps below and overwrites the committed lake artifacts with default settings. It does not run `twin predict` or `twin export`.

| Step | Command (`make` target) | Writes |
| :--- | :--- | :--- |
| 1 | `twin build-lake` (`make lake`) | `lake/curated/{guest_daily,flight_daily,flight_monthly}.parquet`, `lake/analytics.duckdb`, `lake/manifest.json` |
| 2 | `twin build-panel`, `twin build-daily-panel` (`make panel`) | `weekly_market_panel.parquet`, `daily_market_panel.parquet` |
| 3 | `twin evaluate` (`make evaluate`) | `evaluation_results.json` |
| 4 | `twin train` (`make train`) | `structural_calibration.json`, `residual_engine.pkl`, `conformal_calibrator.json` |
| 5 | `twin charts` (`make charts`) | `output/figures/*.png` |
| 6 | `twin report solution` (`make report`) | `output/pdf/challengeon_solution_report.pdf` |
| 7 | `pytest tests/ -v` (`make test`) | none |

## Makefile targets

| Target | Does |
| --- | --- |
| `validate` | `twin validate` |
| `export` | `rm -rf web/public/data`, then `twin export --out web/public/data` |
| `backend` | `test` + `export` |
| `frontend` | `web-install`, `web-test`, `web-build` |
| `web-dev` | Vite dev server |
| `deploy` | `web-test`, then `vercel deploy --prod --yes` from `web/` |
| `up` / `down` / `status` / `logs` | Vite on `WEB_PORT` (5180) and `src/app/server.py` on `API_PORT` (8090) in the background; pid files in `.run/` hold each server's own pid |
| `api-up` / `api-down` / `web-up` / `web-down` | One server each |
| `clean` | Removes uncommitted generated files (`output/figures`, `output/pdf`, `lake/analytics.duckdb`, staging leftovers); honours the dir overrides; never deletes committed lake artifacts |
| `docs-lint` | `scripts/docs_lint.py`: guide and docs graph checks |

## Configuration

Paths are defined in `src/tourism_twin/config.py`; environment variables override them, read once at import.

| Variable | Default | Holds |
| :--- | :--- | :--- |
| `TWIN_ROOT` | repository root | Base for the defaults below |
| `TWIN_SOURCE_DIR` | `01a - DCT Dataset/` | Raw workbooks |
| `TWIN_LAKE_DIR` | `lake/` | DuckDB database, manifest, curated tables, model artifacts |
| `TWIN_OUTPUT_DIR` | `output/` | Figures, PDFs, predictions |

```bash
TWIN_LAKE_DIR=/tmp/lake TWIN_OUTPUT_DIR=/tmp/output make all   # rebuild outside the checkout
TWIN_OUTPUT_DIR=/tmp/output twin predict                       # predictions outside the checkout
```

## Tests

| Command | Runs |
| --- | --- |
| `.venv/bin/pytest -q` (`make test`) | Python tests |
| `pytest tests/<area>` | One area |
| `make web-test` | vitest: engine parity, formatting, lever state and slider rules, map geometry |
| `npx tsc --noEmit` in `web/` | Type check |

| Folder | Covers |
| :--- | :--- |
| `tests/data/` | Lake grain, weekly and daily panels, calendar weeks, test-file row rules |
| `tests/features/` | Feature registry, event registry and offsets, one-off masking |
| `tests/models/` | Components (known-answer recovery), fitting and weights, specs, back-test harness, noise model, fitted-model evaluation |
| `tests/nowcast/` | Baselines, submission validator, outputs, serving, same-day guests, winter outlook |
| `tests/planning/` | Waterfall identity, planning rules, scenario residual, event exposure |
| `tests/reporting/` | Deck, validation and outlook numbers |
| `tests/app/` | Web API |
| `tests/audit/` | Audit tool |
| `tests/test_architecture.py` | Layering, no row loops |

Shared fixtures: `tests/conftest.py` (`twin`, `weekly_panel`, `daily_panel`, `kernel_frame`: built once per session, copied per test). Synthetic data with a known answer: `tests/synthetic.py`. The daily panel is built in memory by a fixture; the prediction-validator test skips without the raw test workbooks; `twin predict` is not run by the tests.

| Area | Asserts |
| :--- | :--- |
| Lake | `flight_daily` is daily from 2023-01-01; `guest_daily` has 69,920 rows and its flag columns |
| Feature registry | Dependencies resolve first and once; missing inputs and cycles raise |
| Panels | Exactly 21 markets, unique keys, load factor capped and flagged; the weekly panel rebuilds from the lake exactly; daily lags continue across the train/test boundary; weekly sums of daily guests and arrivals equal the weekly panel |
| Model components | Each component recovers a known synthetic truth; backfitting matches the joint solution and never raises the penalised objective; the kernel's log gradient matches finite differences and beats its raw-scale warm start; w₀ ≤ 1 holds when it binds; the knot base is flat beyond training; an arrivals-proportional base follows a 0.55× shock; `GroupScale` recovers each series' scale; weights follow a favoured regime; least squares falls back to QR when gelsd fails |
| Event registry | Golden dates; windows do not overlap; Ramadan and Eid al-Fitr never share a day; the one-off 2022 shock is masked |
| Back-test harness | No fold trains on the future (daily and weekly); segment metrics; misindexed or missing predictions raise; skipped folds reported; `compare` detects a real difference and not a null one; the harness reproduces `evaluation_results.json`; a saved model scores identically and refuses its training window |
| Noise model | AR(1) recovery and its closed-form variance; a fold's own errors never set its own bounds |
| Architecture | `nowcast` and `planning` never import each other; packages import only allowed layers; no row loops in `models`, `nowcast`, `planning` |
| Competition predictions | The validator accepts mirrored files and flags bad ones; absent test days get below-threshold arrivals; full weeks with an AR(1) direction probability; the direction back-test scores each week once; the serving bundle answers range questions; the same-day GLM recovers a weekday effect and reads `*` as 0 |
| Web engine (`parity.test.ts`) | What-if guests reproduce every market's prediction (1e-9) and the fitted model for scaled arrivals (1e-6); range intervals match `NoiseModel.range_interval`; conversion chain, waterfall, hybrid, conformal bands and tornado match Python (1e-9); the weekly back-test reproduces the published holdout WMAPE; scenario weeks move by the season's change from the start week; landing months sum the daily predictions |
| Simulator and API | Invalid season rejected; waterfall = lift within 1e-9 for every calibrated market + `SWEDEN`, season and 6 lever sets; route closure, domestic decoupling, added capacity never lowers demand, cold-start priors, tornado, deterministic Monte Carlo; planning and simulation share one arrivals rule; the scenario residual is the season's mean fit |
