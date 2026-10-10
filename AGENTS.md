# AGENTS.md

Rules for coding agents in this repository. If this file disagrees with the code, trust the code and fix this file.

Project: Abu Dhabi Tourism Digital Twin (ChallengeON ATP 2026, DCT challenge). Raw DCT workbooks → DuckDB/Parquet lake → weekly and daily market panels → structural seats → pax → P2P → hotel arrivals → guests chain with a residual ML layer and conformal intervals → CLI, static web app (`web/`), JSON API, PDF reports. Competition output: daily guest nowcast from composable log-scale components (`twin predict`). Human docs: `README.md`, `docs/`; model design (implemented vs. measured vs. proposed): `docs/model_design.md`.

## Setup

- Install with `make install` (creates `.venv`, runs `pip install -e ".[report,dev]"`).
- Use an editable install; otherwise set `TWIN_ROOT` so default paths resolve.
- Declare dependencies only in `pyproject.toml` (no `requirements.txt`). Extras: `report` (reportlab, PDFs), `dev` (pytest).

## Commands

Entry point `twin` (same as `python -m tourism_twin`); run `twin <cmd> --help` for options.

| Command | Does | Writes |
|---|---|---|
| `twin build-lake` | Raw workbooks → curated Parquet + `analytics.duckdb` + manifest | lake |
| `twin build-panel` | Curated Parquet → weekly market panel | lake |
| `twin build-daily-panel [--max-lag K]` | Daily (market, date) panel with arrival lags 0..K (default 21) | lake |
| `twin train [--max-date D] [--panel-path P]` | Structural, residual, conformal artifacts | lake |
| `twin evaluate` | Weekly benchmarks through the back-test harness → `evaluation_results.json` (run before `train`, which reads its coverage) | lake |
| `twin predict [--spec S] [--no-intervals]` | Daily nowcast of the test split (default spec `twin_daily`); refuses output failing `validate_predictions` | output (`predictions/`) |
| `twin validate` | #11 validation table and `compare` rows on `VALIDATION_ORIGINS` | output (`validation_summary.json`) |
| `twin outlook [--winter Y] [--spec S]` | Guests for Dec Y – Feb Y+1 (default 2026) under flat and trend arrivals scenarios (same weekday 364 days earlier × growth), the model's year-earlier estimate, and the procedure's back-test on the latest same-span window ≥ 2 years earlier that starts before the frozen test (cut at its start; empty under 1 year of training guests) | output (`outlook.json`) |
| `twin export [--out D] [--spec S]` | Fit, predict, write the web bundle: `manifest.json` + `<version>/{nowcast,whatif,planning,weekly,golden}.json` | `web/public/data` (default) |
| `twin ablate-blocks` | Nowcast block ablation on 13 exploratory origins (~10 min) | output (`nowcast_block_ablation.json`) |
| `twin evaluate-model [--spec S \| --model P] --start D --end D [--frozen-test]` | Fit a `DAILY_SPECS` name or `pooled_nationalities` up to `--start` minus 21 days (or load a model), score without refitting; frozen test only with `--frozen-test` | output (`models/`, `evaluations/`) |
| `twin simulate --market M --season S [levers]` | Print a scenario briefing | — |
| `twin charts` | Waterfall, tornado, benchmark figures | output |
| `twin report {solution,database}` | PDF report (needs `report` extra) | output |
| `twin report deck [--content P] [--no-pdf]` | 10-slide presentation from `meta/deck/deck.yaml` → `deck/deck.pptx` (+ PDF via LibreOffice); reads `validation_summary.json` and `outlook.json` (run `twin validate` and `twin outlook` first); needs `report` extra | output |
| `twin serve [--port 8080]` | Earlier web UI + JSON API (`python -m app.server` reads `PORT`) | — |
| `twin query "SQL" [--database P] [--limit N]` | Read-only SQL on `analytics.duckdb` | — |

- `twin query` and `twin report database` need `lake/analytics.duckdb` (gitignored; built by `twin build-lake`).
- `twin predict` needs the raw test workbooks; it writes `{domestic,international}_test_guests.csv`, `test_total_guests.csv`, `test_predictions.png`, and, except with `--no-intervals`, `test_guests_intervals.csv`, `market_outputs.json`, `nowcast_serving.json`.
- Makefile targets: `install`, `lake`, `panel` (weekly + daily), `evaluate`, `train`, `charts`, `report` (solution), `test`, `all` (lake → panel → evaluate → train → charts → report → test), `clean`; `validate`, `export` (rm -rf `web/public/data`, then `twin export`), `backend` (test + export), `frontend` (`web-install`, `web-test`, `web-build`), `web-dev`, `deploy` (`web-test`, then `vercel deploy --prod --yes` from `web/` to project `abu-dhabi-hotel-outlook`; needs `vercel login`; `web/.vercel` and `.env*` are gitignored); `up`/`down`/`status`/`logs` (Vite on `WEB_PORT`=5180, `src/app/server.py` on `API_PORT`=8090; each pid file in `.run/` holds the server's own pid via `exec`), `api-up`/`api-down`/`web-up`/`web-down`.

## Tests

- Run `.venv/bin/pytest -q` (or `make test`); web: `make web-test` (vitest) and `npx tsc --noEmit` in `web/`. If you report counts, run pytest and quote its actual output.
- Tests mirror the packages: `tests/{data,features,models,nowcast,planning,reporting,app,audit}/` plus `tests/test_architecture.py`; run one area with `pytest tests/<area>` (CI scoping).
- Put a test in the folder of the package it guards, in an existing file when one fits; never create a top-level product test file other than `test_architecture.py`.
- Shared fixtures live in `tests/conftest.py` (`twin`, `weekly_panel`, `daily_panel`, `kernel_frame`: session-built, copied per test); synthetic generators with a known answer live in `tests/synthetic.py`. Reuse them instead of rebuilding data or refitting the same model in each test.
- Test behaviour: known-answer recovery, leakage, reconciliation, invariants, regressions. Do not test constants, registry membership, constructor errors or message text.
- Extend an existing test that already builds the same objects before adding a new one; a new test must fail on the code it guards (check by breaking it).
- `test_benchmarks_through_the_harness_reproduce_the_committed_evaluation` pins `evaluation_results.json`; a diff there is a metric change.

## Layout and layering

Non-code material lives under `meta/`: `meta/deck/` (slide content, fonts, assets), `meta/research/` (research outputs written by `scripts/`), `meta/audits/` (audit checklist and dated records). Code, `lake/`, `docs/`, `scripts/` and `web/` stay at the root; example `twin query` SQL lives in `src/tourism_twin/data/sql/`.

Packages under `src/`: `tourism_twin` (pipeline and model), `app` (`server.py` + `static/index.html`, the earlier UI), `audit_agent` (LLM data-audit tool, run via `scripts/run_data_issues_audit.py`; input `meta/audits/data_issues/checklist.json`, output `audit/issues.md`). Committed audit inputs and dated snapshots live in `meta/audits/`, never in the repo root; run state and fresh output go to `audit/` (gitignored).

`src/tourism_twin/`, lowest layer first; a module imports only from its own layer or layers above it (enforced by `test_packages_import_only_lower_layers`):

```text
config.py   all filesystem paths (stdlib only)
domain/     markets, archetypes, seasons, events, scenario types
features/   registry + ratios, flags, calendar, lags (imports domain only)
data/       ingest, validation, lake_writer, manifest, lake, repository, imputation, panel, daily_panel
models/     shared model kernel, no use case: protocol, registry (component/fitter names), spec (ModelSpec),
            handler (DataHandler, RowRule), weighting, components/ (base + one module per component),
            linear_solve, fitters, composite, backtest, evaluate, noise
nowcast/    daily competition model: specs, routing, baselines, predict (orchestration), pooling,
            disaggregation, submission (floor, workbook files, validation), weekly, outputs,
            serving, evaluation, same_day, outlook (future-winter scenario)
planning/   weekly scenario model: structural, residual, calendar_features, conformal, uncertainty,
            sensitivity, simulator, briefing, training, evaluation, specs, baselines
reporting/  charts, predictions_plot, solution_report, database_report/, deck/, palette, pdf_palette
export/     bundle.py: the web bundle (sibling of reporting/; neither imports the other)
cli/        the `twin` command
```

- `nowcast/` and `planning/` never import each other; shared model code goes in `models/`.
- Place code by role: vocabulary/constants → `domain/`; derived columns → `features/`; reading/writing raw or lake data → `data/`; reusable model parts → `models/`; the daily competition model and its outputs → `nowcast/`; the scenario simulator → `planning/`; figures/PDFs → `reporting/`; the web bundle → `export/`.
- Keep `cli/` to argument parsing and printing; register new subcommands in `tourism_twin/cli/`.
- Never import a later layer from an earlier one (e.g. `features/` must not import `data/`).

## Data access and features

- Read lake data in new code only through `tourism_twin.data.repository.LakeRepository`; do not add new `pd.read_parquet`/`duckdb.connect` calls on lake paths elsewhere.
- Never hard-code paths; use `tourism_twin.config.SETTINGS` (`lake_dir`, `curated_dir`, `panel_path`, `daily_panel_path`, `output_dir`, ...). Overrides, read once at import: `TWIN_ROOT`, `TWIN_SOURCE_DIR`, `TWIN_LAKE_DIR`, `TWIN_OUTPUT_DIR`.
- Define every derived column once in `tourism_twin/features` with `@PANEL_FEATURES.feature(kind, requires=[...])` and request it by name via `PANEL_FEATURES.apply(frame, [names])`.
- Never recompute a ratio inline. Recompute ratios from summed parts at each grain; never sum or average a ratio.
- Lags shift within one market's series only; never across markets.

## Modeling (guest model)

- Read `docs/model_design.md` (§3 form, §4 evidence, §5 structure, §5.7 rules) before changing any model. When a measured result changes a modeling rule, update the rule here and its evidence in `docs/model_design.md` in the same change.
- No general neural networks (MLP/CNN/RNN): ~1,300 daily rows; MLPs lost to seasonal naive.
- No interaction or power terms by default (weekday × season, seasonal kernels, `flow^α`): none passed the gate (`docs/model_design.md` §4.2).
- Add a model part as: one module in `models/components/` (`Component` protocol or `LinearComponent`, `fit(panel, offset, y, weights=None)`), its export in `components/__init__.py`, one `COMPONENTS.register(name, cls)` line in `models/registry.py`, a synthetic test in `tests/models/test_components.py` that recovers a known truth, and its name in a `ModelSpec` in `nowcast/specs.py` (weekly: `planning/specs.py`). Edit nothing else; never hard-wire a model into `training.py` or `evaluation.py`.
- Declare models as `ModelSpec` data (`models/spec.py`: components by registered name, fitter, row rules, weighting); never build component lists inside functions. Make variants with `adding` / `without` / `replace_component` / `with_weighting`, and route domestic/international with `routed(domestic_spec, international_spec)`. An ablation is a new spec entry, never a code branch.
- Subclass `ComponentBase` (or `LinearComponent`) for a new component: it supplies the hooks the model and fitters call (`reset`, `penalty`, `final_stage`, `set_default_origin`); never probe for those hooks with `hasattr`/`getattr`.
- Least-squares fitting math lives in `models/linear_solve.py`; components only provide designs and penalty rows. Solve through `least_squares` (gelsy fallback when Accelerate's gelsd fails).
- Put every data step that is not math (features, training-row filters, target transform, weights) in `models/handler.py` as a `RowRule` or in `models/weighting.py` as a `Weighting`; never inside a component, fitter or `AdditiveLogModel`. (`AdditiveLogModel`'s `exclude_flag` / `include_flag` are shorthands that only create the same `RowRule`s; prefer `rules=`.)
- A training-weight axis (recency, nationality, …) is one `Weighting` class; combine axes with `Product`. Weights must be positive; only relative values matter. Weightings compare and hash by their settings (specs are cache keys). Ship a weighting only if it passes the gate below.
- Compose components only via `AdditiveLogModel` (`models/composite.py`); exactly one component per model sets `owns_level=True` (it raises otherwise).
- Mark residual learners `final_stage = True` (fitted once, after the rest converge).
- Blocks (flow, time, holiday, flight) are parallel terms of one log-additive model, fitted jointly; never chain them (`docs/model_design.md` §3.1).
- Refitting only some components against frozen others is for experiments only; ship a fully refitted model (§3.2).
- Domestic and international differ only by spec: route with `MarketRouter`, never subclass a model per series. Evaluate each series separately.
- Fit components jointly (`models/fitters.py`); centre periodic contributions; the one level owner and event terms (zero outside their windows) are not centred.
- Nowcast guests equation inputs: test-split hotel New Arrivals (kernel) + calendar blocks only; never a feature derived from `Guests`, never flight, transfer, premium or seat features (§4.9).
- Planning chain: one equation per link (flights → hotel arrivals → guests), simulated end to end; never put flights and arrivals in the same guests equation.
- Calendar terms go in every equation; never de-seasonalize a variable separately before fitting.
- A new input enters as a mixing weight inside the arrivals kernel or as a centred ratio, with one pooled coefficient; never as a free additive log term, never fitted per country.
- Kernel weights, their sum and guests ÷ arrivals ratios are fitting quantities: never output, export or label them as length of stay; label the planning factor L "guests-per-arrival factor".
- Nowcast specs are per series (`docs/model_design.md` §4.6): the arrivals kernel owns the level; DOMESTIC adds a centred slope and no events; INTERNATIONAL has events and no slope. DOMESTIC trains on all history (2022-07 start failed validation).
- Predict pooled-market nationalities with `POOLED_NATIONALITIES`; single-nationality markets keep the market model; never pool all 45 (+3.6 pp).
- Before changing a nowcast model, reproduce the reference evaluation in `docs/model_design.md` §5.7 and compare with its expected values.
- Score a fitted model on later data only through `models/evaluate.evaluate_fitted` (no refitting); compare model choices with `models/backtest.compare` on `VALIDATION_ORIGINS`; score `FROZEN_TEST` once, after every choice is final. A result counts only if `compare`'s interval excludes 0 and its sign holds in most folds.
- Compare models only through `models/backtest.backtest` with `RollingOrigin`/`HoldoutSplit`; pass `period_days=7` for weekly panels (else look-ahead leakage).
- Never rank `DIAGNOSTIC_SPECS` with forecast specs; they read realized test-period data.
- Judge event components only on back-test folds that contain their windows.
- Decide specs on `VALIDATION_ORIGINS`, never on the two reference folds or on origins overlapping the frozen test (8-origin 2024-07..2025-02, 13-origin 2024-02..2025-02); label those exploratory.
- Arrivals kernel: non-negative, non-increasing (`w = triu(ones) @ d`, `d >= 0`), `w_0 <= 1`.
- Encode categoricals one-hot, season as Fourier terms, continuous inputs in log, lunar holidays from explicit dates.
- Tune hyperparameters on validation folds with time-ordered splits only, never on the reported folds; compute calibration statistics (z-scores, conformal margins, σ) from training folds only.
- Fit `models/noise.NoiseModel` on out-of-sample back-test errors only. Interval for a sum (week, date range, total over markets): `NoiseModel.range_interval` or the summed series' own errors; never add bounds.
- Report domestic and international separately. Ship a component only if it lowers validation WAPE by ≥ 0.3 pp on both; among variants within 0.2 pp of the best, keep the simplest. `ResidualGBM` failed, keep it out of `twin_daily`.
- Add event occurrences to `domain/events.csv` (with `scope`: all, international, a market or a pooled-market nationality); `kind=one_off` rows are masked from training via `is_one_off_period`. Keep scoped events (`chinese_new_year`, `morocco_winter_block`) out of `DEFAULT_KERNEL_EVENTS` until they pass validation.
- Never derive legacy `HOLIDAY_WEEKS` / `MAJOR_EVENT_WEEKS` from `events.csv`; that moves shipped weekly results.
- Before `twin outlook --winter Y`, add that window's event occurrences to `events.csv` (unconfirmed lunar dates labelled `(expected)`); an event without a row in the window contributes nothing.
- No `.iterrows(` anywhere in `models/` (a test enforces it).

## Web app (`web/`)

- Layout: `src/app/routes.tsx` (every route, once), `src/engine/` (pure TS: ports `planning`, `weekly`, `whatif`, `noise`, `range`; page arithmetic `insights`, `nowcastViews`, `playback`, `periods` (`periodAt`, `summarise`), `questions` (the five planning answers), `weekly.totalTimeline` (all markets summed); `parity.test.ts`), `src/data/` (bundle loader, `format.ts`), `src/components/{ui,layout,charts}`, `src/features/{landing,simulate,nowcast,report,questions}`, `src/theme/tokens.css`, `src/content/{labels,landing,geo,report,questions}.ts`.
- `/simulate` (`src/features/simulate/`): `SimulatePage.tsx` is a thin container holding the shared state (market, levers reducer, week on the map, forecast start and growth); panes are `LeverPanel.tsx`, `MapPlayback.tsx` (controlled week), `ResultsPanel.tsx`, `SeasonViews.tsx` (`ChainView`, `LeversView`), `TimelinePanel.tsx`. Keep it a container: new UI goes in its own pane component. Which slider applies to which market is decided only in `levers.sliderAvailability` (tested). Scenario levers never change real weeks; changes start after the real data by default.
- Market names only via `content/labels.marketName`.
- The five planning answers are computed only in `engine/questions.ts` and rendered only by the shared `features/questions/QuestionAnswers` (landing and report); never write their numbers into copy.
- After any model or artifact change, run `make export` and commit `web/public/data` with the change; never hand-edit bundle files.
- Static site, no request-time backend: never add an API or BFF for model numbers (the bundle is the store). Compute model numbers only in `src/engine/`; components and features contain no model arithmetic, only call it and format. Every new engine function gets a vitest case.
- Define routes only in `src/app/routes.tsx`. Format numbers and dates only through `src/data/format.ts`; style charts only through `components/charts/theme.ts`. Sliders use `SliderRow` with a `defaultValue`.
- CSS used by more than one feature lives in `components/*` or `theme/`, never in a lazy-loaded feature's CSS. Colours only via the semantic tokens in `theme/tokens.css`: no hex outside it, no `--brand-*` outside the brand surfaces (top nav, pills, landing, report hero); every new colour token gets a dark-mode value.
- UI copy is plain language: no statistical terms beyond "±X% error", no em dashes. A landing statement calls a change up or down only when it exceeds the forecast's own error (`engine/insights.ts`); otherwise "about the same".
- "Leaving" on the moving map is check-ins minus the change in guests staying (`engine/playback.ts`), never a stay-length model.
- Every engine port needs golden cases in `export/bundle.golden_part` (or `planning_golden`) and a parity test; keep tolerances at 1e-9 where the maths is exact.
- The bundle exports derived terms (what-if base/pre/in/floor/multiplier), never raw arrivals (licensed data).
- Report copy lives in `web/src/content/report.ts`, each number with its source (solution documentation §9.2 weekly holdout, §9.3 daily validation, §11 limitations); keep those section numbers stable.

## Presentation deck

- Edit slide content only in `meta/deck/deck.yaml` (exactly 10 slides; one `type` each: cover, columns, rows, hero, stats, flow, table, chart; inline `**bold**` and `==teal==` accents). Design tokens (colours, type sizes, spacing, grid ratios) live only in `reporting/deck/theme.py`; every box comes from `grid.py`; text is fitted in `typeset.py` (overflow fails the build); shapes in `canvas.py`; one renderer per type in `slides/`; background art in `art.py`; the tornado chart in `figures.py`. `reporting/palette.py` stays for the PDF reports. Build and export only through `build_deck`.
- Result numbers on slides (errors, gains, shares, effects) are `{name}` placeholders filled from artifacts (`validation_summary.json`, `outlook.json`, `evaluation_results.json`; `reporting/deck/numbers.py`); never type a result into slide text, and every fallback entry names its `source`. Design facts (e.g. 7 validation origins, a 21-day lag window) may be written directly.
- Plain language: a technical term only with its job; a detail always under its parent bullet.

## Data and artifacts

- `01a - DCT Dataset/` holds the raw workbooks: gitignored, supplied locally (or via `TWIN_SOURCE_DIR`). Never edit or commit them.
- Committed despite `.gitignore`: `lake/manifest.json` and tracked files in `lake/curated/` (check with `git ls-files lake`). `build-lake`, `build-panel`, `build-daily-panel`, `train`, `evaluate`, and `make all` overwrite lake artifacts with default dirs; `charts`/`report`/`predict`/`evaluate-model`/`ablate-blocks`/`outlook` write `output/`.
- Run those against scratch dirs, never the checkout: `TWIN_LAKE_DIR=/tmp/lake TWIN_OUTPUT_DIR=/tmp/out make all`; `twin predict` with a scratch `TWIN_OUTPUT_DIR`.
- `make clean` removes only uncommitted generated files (figures, PDFs, `analytics.duckdb`, staging leftovers); it honours the same dir overrides.
- Never use a submission file unless `validate_predictions` returns no problems.
- Floor nationality Guests at max(New Arrivals, 10); absent test days get below-threshold arrivals, not interpolation.
- Read same-day `*` as 0; never publish Poisson same-day intervals (dispersion 8–10).
- Narration and LLM text read `market_outputs.json` fields only and never compute numbers; add new numbers in `nowcast/outputs.py`.
- `residual_engine.pkl` must pickle a plain dict of scikit-learn estimators, never a project class (survives module moves).

## Change discipline

- Refactors must prove unchanged outputs: rebuild into a scratch dir and compare against the committed artifacts.
- Ship metric or behaviour changes as a separate change and report them explicitly; never silently.
- Dated records keep historical paths; do not "fix" them: `meta/audits/data_issues/` (checklist and the dated issues snapshot), `meta/research/real_world_validation/*.md`, evidence strings in `scripts/direct_audit_runner.py`.

## Agent skills (`.agents/skills/`)

| Skill | Use for |
|---|---|
| `dct-tourism-hackathon-reviewer` | Review, score, and improve submissions for this DCT flight-to-hotel-demand challenge |
| `data-lake-and-zone-architecture` | Raw/refined/curated/publish zones, storage layout, retention |
| `data-quality-and-contract-testing` | Contracts, assertions, and validation evidence for data changes |
| `data-reconciliation-and-financial-controls` | Source-to-target totals, control balances, exception tracking |
| `duckdb-local-analytics-and-dev` | DuckDB-based local prototyping and validation |
| `feature-store-and-ml-data-pipelines` | Feature generation, training-serving parity, point-in-time correctness |
| `file-and-partner-feed-ingestion` | Landing flat files/partner feeds with validation and replay safety |
| `master-data-and-entity-resolution` | Canonical entities, matching, golden records |
| `notebook-to-production-hardening` | Turning notebooks into tested, packaged jobs |
| `python-data-engineering-and-pipeline-packaging` | Python ingestion jobs, packaging, dependencies, CLIs |
| `semantic-layer-and-metric-governance` | Governed metric definitions and shared dimensions |
| `warehouse-and-schema-design` | Fact/dimension models, keys, grain, serving schemas |

`.opencode/agents/audit-escalation.md`: read-only escalation agent used by the data-issues audit (`src/audit_agent/escalation.py`).
