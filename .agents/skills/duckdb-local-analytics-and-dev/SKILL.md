---
name: duckdb-local-analytics-and-dev
description: Guides agents through DuckDB-based local analytics and development workflows. Use when prototyping models locally, validating transformations, reproducing data issues quickly, or building lightweight analytical tooling without a full warehouse.
---

# DuckDB Local Analytics And Dev

## When to Use

- Prototyping models and transformations locally before a warehouse.
- Reproducing data issues with sample datasets.
- Running analytical queries, CLI tools, validators, or test harnesses without remote infrastructure.
- Validating dbt models locally with `dbt-duckdb`; embedded-analytics proofs of concept.

Do not use it where the workload needs production durability, concurrent access, or distributed processing.

## In this repo

- Query curated tables through `LakeRepository().sql()` (in-memory DuckDB views over the curated Parquet); do not open lake files directly.
- Ad-hoc read-only SQL: `twin query "SQL"` (needs `lake/analytics.duckdb` from `twin build-lake`).
- DuckDB is pinned in `pyproject.toml`; change the pin deliberately.

## Workflow

1. Scope it: the question answered, the sample data and its origin, one-off vs repeatable, the promotion path.
2. Make inputs reproducible:
   - Use committed or script-downloaded sample files (CSV/Parquet/JSON), read directly by DuckDB.
   - Document how samples were generated; keep them representative but small.
   - Use anonymized or synthetic samples for sensitive data.
3. Write transformations that map to production:
   - Use standard SQL; avoid DuckDB-only functions unless the workflow stays local.
   - Mirror the production layering (staging → intermediate → marts); with `dbt-duckdb`, reuse the production model structure and tests.
   - Document DuckDB-specific features that need replacing.
4. Validate locally: row counts, null assertions, key uniqueness, golden-file comparisons, `SUMMARIZE` sanity checks, the project's validation framework.
5. Document the promotion path: single-node/in-process/file-based assumptions, target platform and dialect differences, operations needing distributed execution. Promote deliberately.
6. Keep it maintainable: a Makefile or script that runs from scratch, a pinned DuckDB version, cleanup of temporary databases, documented expected runtime; retire unused workflows.

## Red Flags

- Local DuckDB treated as production, or a prototype deployed without validation on the target platform.
- Sample data contains real PII or secrets, or full production-scale files are pulled onto a laptop.
- DuckDB-specific functions used without documented equivalents.
- No Makefile or script reproduces the workflow from scratch.
- Temporary databases accumulate without cleanup.
- DuckDB version unpinned.

## Verification

- [ ] Purpose and scope are documented
- [ ] Sample data is reproducible, appropriately sized, and free of sensitive content
- [ ] SQL uses standard patterns that map to the target platform
- [ ] Local assertions and contract checks validate correctness
- [ ] The promotion path lists dialect differences
- [ ] A Makefile or script reproduces the workflow from a clean state
- [ ] DuckDB version is pinned
