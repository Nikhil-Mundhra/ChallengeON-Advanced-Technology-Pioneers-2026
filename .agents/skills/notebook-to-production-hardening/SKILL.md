---
name: notebook-to-production-hardening
description: Guides agents through converting exploratory notebooks into production-ready data jobs. Use when operationalizing notebooks from Databricks, Jupyter, or similar environments into tested, packaged, repeatable workflows.
---

# Notebook To Production Hardening

## When to Use

- Moving notebook logic into scheduled jobs.
- Hardening Databricks or Jupyter notebooks for repeated use.
- Extracting cell logic into modules or packages.

Do not treat a manually rerun notebook as production.

## Workflow

1. Separate exploration from production logic: identify reusable transforms, parameters, environment assumptions, manual steps.
2. Extract logic into versioned, testable modules.
3. Replace hidden state (widgets, manual edits, cell order) with explicit inputs and configuration.
4. Add contracts, logging, error handling, and retry-safe outputs.
5. Define deployment and monitoring.

## Red Flags

- "It already works" interactively, with no tests or observability.
- Business logic depends on cell order.
- Configuration hard-coded in cells.
- Modularization deferred.
- Outputs written with no validation or idempotency plan.
- Deployment path undefined.

## Verification

- [ ] Reusable logic is extracted from the notebook
- [ ] Inputs, configuration, and outputs are explicit
- [ ] Validation, logging, and retry-safe behavior exist
- [ ] Deployment and monitoring are defined
