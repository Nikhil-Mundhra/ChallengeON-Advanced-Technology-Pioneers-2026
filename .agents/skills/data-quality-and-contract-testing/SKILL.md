---
name: data-quality-and-contract-testing
description: Drives data implementation with contracts, assertions, and validation evidence. Use when adding or changing ingestion logic, transformations, schemas, or published data products.
---

# Data Quality And Contract Testing

Data work is done only when contracts and checks prove the output is correct, not when the job runs.

## When to Use

- New source ingestion, schema changes, transformation changes.
- New or changed published tables.
- Fixes for bad data or broken metrics.

Apply from the start of implementation, not as final cleanup.

## Workflow

1. Define the contract first: required fields, key constraints, types, null behavior, freshness, reconciliation rules.
2. Write the validation plan first: uniqueness, non-null thresholds, referential integrity, accepted values, row-count deltas, source-to-target totals.
3. Reproduce every data bug with a failing check before changing the pipeline.
4. Implement the smallest change that satisfies the contract.
5. Run the validations and capture evidence: test output, query results, reconciliation output, dry-run logs.

## Bundled examples

- `checks/null_rate.py`, `checks/freshness.py`, `checks/contract_completeness.py`: generic CLI checks (`--help` for usage); `--contract` YAML needs PyYAML, which is not a project dependency.
- `anti-patterns/no_quality_gate_before_publish.py`: a pipeline that publishes without a quality gate, for diagnosis practice.

## Red Flags

- A published dataset has no contract.
- Correctness judged by eyeballing a query.
- Checks deferred "until the model stabilizes".
- A successful job treated as proof of valid data.
- An incident fix ships without a failing reproduction check.
- Only happy-path sample data is validated.
- Freshness or completeness expectations are absent.

## Verification

- [ ] Contracts are written before or alongside implementation
- [ ] Checks cover correctness, completeness, and freshness
- [ ] Defects are reproduced with a failing validation before the fix
- [ ] Validation evidence is captured and reviewable
