# Python code

## Calls
- `agents/code/comments.md` : comment rules for every changed line
- `docs/architecture/layers.md` : package layers and what each holds
- `docs/guide/setup.md` : install, pipeline, configuration, Makefile targets, test folders
- `docs/guide/cli.md` : every `twin` command and what it writes

## Rules
- setup: install with `make install`; keep the install editable, otherwise set `TWIN_ROOT`.
- dependencies: declared only in `pyproject.toml`; no `requirements.txt`.
- layering: a module imports only from its own layer or a lower one (`docs/architecture/layers.md`); `nowcast/` and `planning/` never import each other, shared model code goes in `models/`.
- placement: vocabulary and constants → `domain/`; derived columns → `features/`; reading or writing raw or lake data → `data/`; reusable model parts → `models/`; the daily competition model and its outputs → `nowcast/`; the scenario simulator → `planning/`; figures and PDFs → `reporting/`; the web bundle → `export/`.
- cli: `cli/` holds argument parsing and printing only; a new subcommand registers in `tourism_twin/cli/`.
- paths: never hard-coded; use `tourism_twin.config.SETTINGS` (`lake_dir`, `curated_dir`, `panel_path`, `daily_panel_path`, `output_dir`, ...).
- lake reads: new code reads lake data only through `tourism_twin.data.repository.LakeRepository`; no new `pd.read_parquet` or `duckdb.connect` on lake paths elsewhere.
- features: every derived column is defined once in `tourism_twin/features` with `@PANEL_FEATURES.feature(kind, requires=[...])` and requested by name through `PANEL_FEATURES.apply(frame, [names])`.
- ratios: never recomputed inline; recompute from summed parts at each grain; never sum or average a ratio.
- lags: shift within one market's series only, never across markets.
- row loops: no `.iterrows(` in `models/`, `nowcast/` or `planning/`.
- tests, run: `.venv/bin/pytest -q` or `make test`; one area with `pytest tests/<area>`; a reported count quotes pytest's actual output.
- tests, placement: a test lives in the folder of the package it guards, in an existing file when one fits; no new top-level product test file besides `tests/test_architecture.py`.
- tests, fixtures: reuse `tests/conftest.py` fixtures and `tests/synthetic.py` generators instead of rebuilding data or refitting the same model per test.
- tests, content: test behaviour (known-answer recovery, leakage, reconciliation, invariants, regressions); never constants, registry membership, constructor errors or message text.
- tests, new: extend an existing test that already builds the same objects before adding one; a new test fails on the code it guards (check by breaking it).
- tests, pinned: a diff in `test_benchmarks_through_the_harness_reproduce_the_committed_evaluation` is a metric change (AGENTS.md `metrics`).
