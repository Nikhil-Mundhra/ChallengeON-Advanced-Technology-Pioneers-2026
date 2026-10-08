# AGENTS.md

Instructions for coding agents working in this repository. Code is the source of
truth; if this file disagrees with the code, trust the code and fix this file.

## What this is

An Abu Dhabi Tourism Digital Twin for the ChallengeON / Advanced Technology Pioneers
2026 DCT challenge: it turns aviation scenarios (frequency, gauge, seats, load factor,
P2P share, marketing, length of stay) into hotel-demand effects by source market and
season. A DuckDB/Parquet lake is built from the raw DCT workbooks, a structural
seats → passengers → P2P passengers → hotel arrivals → hotel guests chain is calibrated with a residual ML
layer and conformal intervals, and the result is served as a CLI, a web UI/JSON API,
and PDF reports. Human-facing documentation lives in `README.md` and `docs/`.

## Setup

```bash
make install                        # creates .venv and runs: pip install -e ".[report,dev]"
```

Packaging is `pyproject.toml` only (there is no `requirements.txt`). Extras: `report`
(reportlab, needed for PDFs) and `dev` (pytest). The editable install is required for
the default repo-relative paths to resolve; otherwise set `TWIN_ROOT`.

## Commands

One console command, `twin` (equivalently `python -m tourism_twin`):

| Command | Purpose |
|---|---|
| `twin build-lake` | Raw workbooks → Parquet tables + DuckDB lake |
| `twin build-panel` | Lake → curated weekly market panel |
| `twin train [--max-date D] [--panel-path P]` | Calibrate structural, residual, conformal artifacts |
| `twin evaluate` | Forward-holdout back-test → `evaluation_results.json` |
| `twin simulate --market M --season S [--delta-freq ...]` | Run a planner scenario, print the briefing |
| `twin charts` | Waterfall, tornado, benchmark figures |
| `twin report {solution,database}` | Build a PDF report (needs the `report` extra) |
| `twin serve [--port 8080]` | Interactive web UI + JSON API |
| `twin query "SQL" [--database ...] [--limit N]` | SQL against the analytics DuckDB |

Use `twin <cmd> --help` for options. The `Makefile` wraps these (`make evaluate`,
`make train`, `make charts`, `make report`, `make test`, `make all`).

Tests: `.venv/bin/pytest -q` (or `make test`). Known failure on a clean checkout:
`test_data_contract_and_grain_separation`, because `lake/curated/flight_monthly.parquet`
was never committed.

## Code layout and layering

`src/` layout with three packages: `tourism_twin` (the model and pipeline), `app`
(`server.py` HTTP server + `static/index.html`), `audit_agent` (internal LLM data
audit tool, driven by `scripts/run_data_issues_audit.py`).

`src/tourism_twin/` is layered; imports only point downward:

```text
config.py   all filesystem paths (stdlib only)
domain/     markets, archetypes, seasons, events, scenario types — imports nothing from the package
data/       ingest, validation, lake_writer, manifest, lake, panel
models/     structural, features, residual, uncertainty, conformal, training, evaluation
services/   simulator, sensitivity, briefing
reporting/  charts, solution_report, database_report/, palettes     cli/  the `twin` command
```

Where new code goes: pure business vocabulary/constants → `domain/`; reading or
writing raw/lake data → `data/`; fitting or scoring → `models/`; scenario use cases
that compose models → `services/`; figures/PDFs → `reporting/`; argument parsing and
printing only → `cli/` (keep logic out of it). A lower layer must never import a
higher one. New CLI subcommands register in `tourism_twin/cli/`.

## Paths and configuration

Never hard-code paths. Use `tourism_twin.config.SETTINGS` (`SETTINGS.lake_dir`,
`SETTINGS.curated_dir`, `SETTINGS.panel_path`, `SETTINGS.output_dir`, ...). Overrides,
read once at import: `TWIN_ROOT`, `TWIN_SOURCE_DIR`, `TWIN_LAKE_DIR`, `TWIN_OUTPUT_DIR`.

## Data and artifact rules

- `01a - DCT Dataset/` holds the raw competition workbooks. It is gitignored (not
  redistributed): place the organizer-provided files there locally, or point
  `TWIN_SOURCE_DIR` at them. Immutable — never edit, never commit.
- `lake/`: `analytics.duckdb` is gitignored, but `lake/manifest.json` and the files in
  `lake/curated/` (parquet, json, `residual_engine.pkl`) ARE committed despite the
  `.gitignore` patterns. `build-lake`, `build-panel`, `train`, `evaluate`, `charts`,
  `report` and `make all`/`make clean` overwrite or delete them with default settings —
  don't run them casually against the checkout.
- `output/` (figures, PDFs) is gitignored and regenerable.
- `residual_engine.pkl` pickles a plain dict of scikit-learn estimators, not a project
  class, so it survives module moves. Keep it that way.
- Scratch rebuild without touching committed artifacts — point both dirs elsewhere
  and build the lake and panel first (`make all` does not run them):
  ```bash
  export TWIN_LAKE_DIR=/tmp/lake TWIN_OUTPUT_DIR=/tmp/out
  .venv/bin/twin build-lake && .venv/bin/twin build-panel && make all
  ```

## Change discipline

- No silent behaviour or metric changes. Refactors must be verified by byte-identical
  outputs (rebuild into a scratch dir and diff against the committed artifacts).
- Dated audit and research records keep their historical paths on purpose:
  `DATA_ISSUES*.md`, `research/real_world_validation/*.md`, and evidence strings in
  `scripts/direct_audit_runner.py`. Do not "fix" old paths in them.

## Agent skills (`.agents/skills/`)

| Skill | Use for |
|---|---|
| `dct-tourism-hackathon-reviewer` | Judging, scoring, and auditing this DCT flight-to-hotel-demand submission |
| `data-lake-and-zone-architecture` | Raw/refined/curated/publish zones, storage layout, retention |
| `data-quality-and-contract-testing` | Contracts, assertions, validation evidence for data changes |
| `data-reconciliation-and-financial-controls` | Source-to-target totals, control balances, exception tracking |
| `duckdb-local-analytics-and-dev` | DuckDB-based local prototyping and validation |
| `feature-store-and-ml-data-pipelines` | Feature generation, training-serving parity, point-in-time correctness |
| `file-and-partner-feed-ingestion` | Landing flat files/partner feeds with validation and replay safety |
| `master-data-and-entity-resolution` | Canonical entities, matching, golden records |
| `notebook-to-production-hardening` | Turning notebooks into tested, packaged jobs |
| `python-data-engineering-and-pipeline-packaging` | Python ingestion jobs, packaging, dependencies, CLIs |
| `semantic-layer-and-metric-governance` | Governed metric definitions and shared dimensions |
| `warehouse-and-schema-design` | Fact/dimension models, keys, grain, serving schemas |

`.opencode/agents/audit-escalation.md` is the read-only escalation agent used by the
data-issues audit.
