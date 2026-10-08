---
name: python-data-engineering-and-pipeline-packaging
description: Guides agents through Python-based data engineering implementation. Use when building or modifying Python ingestion jobs, orchestration helpers, PySpark entry points, validation code, packaging, dependency management, or operational CLI workflows.
---

# Python Data Engineering And Pipeline Packaging

## When to Use

- Building or modifying Python data pipelines.
- Packaging PySpark, ingestion, validation, or orchestration helpers.
- Moving notebooks or scripts into modules.
- Dependency, environment, or runtime issues.
- Adding CLI entry points, test harnesses, or local dev workflows.

Do not treat a script that ran once as a production design.

## In this repo

- Packaging is `pyproject.toml` only (`src/` layout, extras `report` and `dev`); install with `make install`.
- Follow the layering and placement rules in `AGENTS.md`; new `twin` subcommands go in `tourism_twin/cli/` and only parse args and print.
- Take paths from `tourism_twin.config.SETTINGS`, never literals.

## Workflow

1. Name the code's role: single-node transform, PySpark entry point, orchestration helper, validation/reconciliation tool, or integration/extraction service.
2. Package into modules: versioned packages, reusable modules, clear CLI/job entry points, isolated configuration, minimal global state.
3. Make dependencies real: environment model, pinning strategy, native/system dependencies, runtime-platform compatibility (Airflow, Spark, containers).
4. Make runtime boundaries explicit: local vs distributed, orchestration vs job package, how config/secrets/env are supplied, logging/retry/exit behavior.
5. Prove maintainability: targeted tests, representative inputs, clear interfaces/types, reproducible local execution.

## Red Flags

- Pipeline logic in one script with no reusable modules.
- Business logic kept in DAGs or notebook state.
- Notebooks, DAGs, and jobs duplicate the same transformation.
- Dependency versions implicit or environment-specific; a requirements file treated as runtime documentation.
- Local and deployed runs behave differently without explanation.
- Secrets or environment assumptions embedded in code.

## Verification

- [ ] Clear package and entry-point shape
- [ ] Runtime, dependency, and environment assumptions are explicit
- [ ] Orchestration and business logic are separated
- [ ] Important logic has tests or a reproducible execution path
