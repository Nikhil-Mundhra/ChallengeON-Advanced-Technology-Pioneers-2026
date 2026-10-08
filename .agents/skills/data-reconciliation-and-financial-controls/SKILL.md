---
name: data-reconciliation-and-financial-controls
description: Guides agents through reconciliation and control design for business-critical data. Use when validating financial, operational, or audit-sensitive metrics with source-to-target totals, control balances, exception tracking, or close-process dependencies.
---

# Data Reconciliation And Financial Controls

## When to Use

- Finance, billing, revenue, or other audit-sensitive pipelines.
- Month-end or close-process data products.
- Source-to-target control validation and exception-based review.

Do not substitute spot queries for reconciled numbers.

## Workflow

1. Define the control objective: what must reconcile, acceptable variance, frequency, exception owner.
2. Choose the pattern: row counts, control totals, aggregate balances, record-level exception matching.
3. Make timing and cutoff rules explicit (accounting windows, source close times).
4. Capture exceptions and route them to the owner.
5. Retain reviewable evidence, not only ephemeral job output.

## Red Flags

- "Simple" transformation logic trusted without independent validation.
- No defined acceptable variance; small variances waved through after the fact.
- A one-time match treated as an ongoing control.
- Cutoff timing undocumented.
- Exceptions found manually and inconsistently.
- Control evidence cannot be reproduced later.

## Verification

- [ ] Control objectives and acceptable variance are defined
- [ ] Reconciliation logic is explicit and reviewable
- [ ] Exceptions have an owner and workflow
- [ ] Control evidence is retained for audit or review
