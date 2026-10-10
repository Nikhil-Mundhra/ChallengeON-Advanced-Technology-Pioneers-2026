# Commands

Entry point `twin` (same as `python -m tourism_twin`); `twin <cmd> --help` lists options.

| Command | Does | Writes |
| --- | --- | --- |
| `twin build-lake` | Raw workbooks → curated Parquet, `analytics.duckdb`, manifest | `lake/` |
| `twin build-panel` | Curated Parquet → weekly market panel | `lake/` |
| `twin build-daily-panel [--max-lag K]` | Daily (market, date) panel with arrival lags 0..K (default 21) | `lake/` |
| `twin evaluate` | Weekly benchmarks through the back-test harness | `lake/curated/evaluation_results.json` |
| `twin train [--max-date D] [--panel-path P]` | Structural, residual and conformal artifacts; reads coverage from `evaluation_results.json` | `lake/curated/` |
| `twin predict [--spec S] [--no-intervals]` | Daily nowcast of the test split (default `twin_daily`); writes nothing if `validate_predictions` fails | `output/predictions/` |
| `twin validate` | Validation table and `compare` rows on `VALIDATION_ORIGINS` (never the frozen test) | `output/validation_summary.json` |
| `twin outlook [--winter Y] [--spec S]` | Guests for December Y to February Y+1 (default 2026) under flat and trend arrivals | `output/outlook.json` |
| `twin export [--out D] [--spec S]` | Fit, predict, write the web bundle | `web/public/data` (default) |
| `twin ablate-blocks` | Nowcast block ablation on 13 exploratory origins (about 10 min) | `output/nowcast_block_ablation.json` |
| `twin evaluate-model [--spec S \| --model P] --start D --end D [--gap-days N] [--frozen-test]` | Fit a `DAILY_SPECS` name or `pooled_nationalities` on rows up to `--start` − (gap + 1) days (default gap 21), or load a model; score the window without refitting | `output/models/<spec>_<train_end>.pkl`, `output/evaluations/<spec>_<start>_<end>.json` |
| `twin simulate --market M --season S [levers]` | Scenario briefing ([simulator](simulator.md)) | console |
| `twin charts` | Waterfall, tornado, benchmark figures | `output/figures/` |
| `twin report solution` | Solution PDF (3 pages; `report` extra) | `output/pdf/challengeon_solution_report.pdf` |
| `twin report database` | Schema and database PDF; needs `lake/analytics.duckdb` | `output/pdf/challengeon_schema_database_report.pdf` |
| `twin report deck [--content P] [--no-pdf] [--previews]` | 10-slide deck from `meta/deck/deck.yaml`; reads `validation_summary.json` and `outlook.json` | `output/deck/deck.pptx`, `deck.pdf` |
| `twin serve [--port 8080]` | Earlier web UI and JSON API ([web](web.md#earlier-web-ui-twin-serve)) | none |
| `twin query "SQL" [--database P] [--limit N]` | Read-only SQL on `lake/analytics.duckdb` | console |

## `twin predict`

| Fact |
| --- |
| Needs the raw test workbooks (`data domestic_test.xlsx`, `data international_test.xlsx`) and the committed `lake/curated/guest_daily.parquet` |
| Step 1: build the daily panel in memory; fit the spec on every training day; predict each test market-day |
| Step 2 (intervals): rolling-origin back-test on 8 monthly origins 2024-07-01 to 2025-02-01, 7-month horizon; noise model on its errors; 80% bounds with h counted from 2025-08-01 |
| Step 3: the 30 pooled-market nationalities from `POOLED_NATIONALITIES` with their own intervals; arrival-share split as fallback |
| Step 4: validate, then write. Checks: rows, keys, column order and source values equal the test workbooks; every `Guests` finite and ≥ max(New Arrivals, 10); interval rows and keys match; P10 ≤ P50 ≤ P90 |
| The console prints the direction back-test accuracy, each written path and the row counts |

Files: [outputs](outputs.md).

## `twin evaluate-model`

Scores: WAPE, bias, MAE, RMSE, MSE, log-MSE per segment at day, complete-week and complete-month grain; error by horizon; direction of consecutive totals; `pooled_nationalities` adds a per-nationality table. A window overlapping 2025-02-01..2025-07-31 needs `--frozen-test`.

## `twin train`

Trains on complete train-split weeks with complete guest inputs up to `--max-date` (default 2025-07-27).

| File | Contents |
| :--- | :--- |
| `lake/curated/structural_calibration.json` | Seats, load factor, P2P share, response multiplier, stay factor and baseline guests for 21 markets × 4 seasons |
| `lake/curated/residual_engine.pkl` | One RidgeCV per market and the mean fitted residual per market and season |
| `lake/curated/conformal_calibrator.json` | Per-market conformal margins (target alpha 0.2) and the holdout coverage read from `evaluation_results.json` |

## `twin evaluate`

Calibrates on 104 complete weeks and scores 30 holdout weeks with the same trainers as `twin train`; writes `evaluation_results.json` (diagnostics, benchmark, `benchmark_leaders`, coverage, market and season breakdowns) and no calibrator. The four benchmarks run as specs (`WEEKLY_SPECS`) through `models/backtest.py`.

| Setting | Prediction |
| :--- | :--- |
| International planning | Scheduled seats × calibrated seasonal load factor, P2P share, multiplier, stay factor; no holdout load factor, P2P or arrivals |
| International realized chain | Realized holdout P2P × calibrated multiplier × stay factor |
| Domestic forecast | Calibrated domestic seasonal prior |
| Combined | International + domestic |

Results: [planning holdout](../results/planning-holdout.md).

## Charts and reports

`model_benchmark.png` reads `lake/curated/evaluation_results.json`. The deck reads `output/validation_summary.json` and `output/outlook.json` (run `twin validate` and `twin outlook` first); PDF export needs LibreOffice; slide format: `meta/deck/README.md`.
