# AGENTS.md

Rules for coding agents in this repository. If this file disagrees with the code, trust the code and fix this file.

Project: Abu Dhabi Tourism Digital Twin (ChallengeON ATP 2026, DCT challenge). Raw DCT workbooks → DuckDB/Parquet lake → weekly and daily market panels → structural seats → pax → P2P → hotel arrivals → guests chain with a residual ML layer and conformal intervals → CLI, web UI/JSON API, PDF reports. Human docs: `README.md`, `docs/`; model design (implemented vs. measured vs. proposed): `docs/model_design.md`.

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
| `twin evaluate` | Forward-holdout back-test → `evaluation_results.json`; syncs coverage into `conformal_calibrator.json` | lake |
| `twin simulate --market M --season S [levers]` | Print a scenario briefing | — |
| `twin charts` | Waterfall, tornado, benchmark figures | output |
| `twin report {solution,database}` | PDF report (needs `report` extra) | output |
| `twin serve [--port 8080]` | Web UI + JSON API | — |
| `twin query "SQL" [--database P] [--limit N]` | Read-only SQL on `analytics.duckdb` | — |

- `twin query` and `twin report database` need `lake/analytics.duckdb` (gitignored; built by `twin build-lake`).
- Makefile targets: `install`, `lake`, `panel` (weekly + daily), `evaluate`, `train`, `charts`, `report` (solution), `data-issues-pdf`, `test`, `all` (lake → panel → evaluate → train → charts → report → test), `clean`.

## Tests

- Run `.venv/bin/pytest -q` (or `make test`). If you report counts, run pytest and quote its actual output.
- `test_monthly_flights_are_isolated_to_2022` skips when `lake/curated/flight_monthly.parquet` is not built (it is not committed).
- Product suite is one file: `tests/test_tourism_twin.py`; shared fixtures in `tests/conftest.py`. Audit-tool tests: `tests/test_audit_agent.py`.
- Add product tests to `test_tourism_twin.py` in the matching pipeline-order section: domain, lake, feature registry, panels, simulator, API. Never create a new product test file.

## Layout and layering

Packages under `src/`: `tourism_twin` (pipeline and model), `app` (`server.py` + `static/index.html`), `audit_agent` (LLM data-audit tool, run via `scripts/run_data_issues_audit.py`).

`src/tourism_twin/`, lowest layer first; a module imports only from its own layer or layers above it in this list:

```text
config.py   all filesystem paths (stdlib only)
domain/     markets, archetypes, seasons, events, scenario types
features/   registry + ratios, flags, calendar, lags (imports domain only)
data/       ingest, validation, lake_writer, manifest, lake, repository, imputation, panel, daily_panel
models/     structural, features, residual, uncertainty, conformal, training, evaluation
services/   simulator, sensitivity, briefing
reporting/  charts, solution_report, database_report/, palette, pdf_palette
cli/        the `twin` command
```

- Place code by role: vocabulary/constants → `domain/`; derived columns → `features/`; reading/writing raw or lake data → `data/`; fitting/scoring → `models/`; scenario use cases → `services/`; figures/PDFs → `reporting/`.
- Keep `cli/` to argument parsing and printing; register new subcommands in `tourism_twin/cli/`.
- Never import a later layer from an earlier one (e.g. `features/` must not import `data/`).

## Data access and features

- Read lake data in new code only through `tourism_twin.data.repository.LakeRepository`; do not add new `pd.read_parquet`/`duckdb.connect` calls on lake paths elsewhere.
- Never hard-code paths; use `tourism_twin.config.SETTINGS` (`lake_dir`, `curated_dir`, `panel_path`, `daily_panel_path`, `output_dir`, ...). Overrides, read once at import: `TWIN_ROOT`, `TWIN_SOURCE_DIR`, `TWIN_LAKE_DIR`, `TWIN_OUTPUT_DIR`.
- Define every derived column once in `tourism_twin/features` with `@PANEL_FEATURES.feature(kind, requires=[...])` and request it by name via `PANEL_FEATURES.apply(frame, [names])`.
- Never recompute a ratio inline. Recompute ratios from summed parts at each grain; never sum or average a ratio.
- Lags shift within one market's series only; never across markets.

## Data and artifacts

- `01a - DCT Dataset/` holds the raw workbooks: gitignored, supplied locally (or via `TWIN_SOURCE_DIR`). Never edit or commit them.
- Committed despite `.gitignore`: `lake/manifest.json` and tracked files in `lake/curated/` (check with `git ls-files lake`). `build-lake`, `build-panel`, `build-daily-panel`, `train`, `evaluate`, and `make all` overwrite lake artifacts with default dirs; `charts`/`report` overwrite `output/`.
- Do not run those commands against the checkout casually; rebuild into scratch: `TWIN_LAKE_DIR=/tmp/lake TWIN_OUTPUT_DIR=/tmp/out make all`.
- `make clean` removes only uncommitted generated files (figures, PDFs, `analytics.duckdb`, staging leftovers); it honours the same dir overrides.
- `residual_engine.pkl` must pickle a plain dict of scikit-learn estimators, never a project class (survives module moves).

## Change discipline

- Refactors must prove unchanged outputs: rebuild into a scratch dir and compare against the committed artifacts.
- Ship metric or behaviour changes as a separate change and report them explicitly; never silently.
- Dated records keep historical paths; do not "fix" them: `DATA_ISSUES*.md`, `research/real_world_validation/*.md`, evidence strings in `scripts/direct_audit_runner.py`.

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
