---
name: feature-store-and-ml-data-pipelines
description: Guides agents through machine-learning data pipelines and feature serving workflows. Use when designing feature generation, offline and online consistency, training-serving parity, point-in-time correctness, or ML-oriented data product contracts.
---

# Feature Store And ML Data Pipelines

## When to Use

- Building training datasets or reusable features.
- Supporting online and offline feature access.
- Preventing leakage and training-serving mismatch.
- Publishing model-ready data products.

Do not treat feature pipelines as ordinary marts; leakage and parity are distinct risks.

## In this repo

- Define derived columns once in `tourism_twin/features` (`@PANEL_FEATURES.feature(kind, requires=[...])`) and request them by name with `PANEL_FEATURES.apply`.
- Recompute ratios from summed parts at each grain; never sum or average them.
- Lags shift within one market's series only; check that no planning-mode feature uses values unknown at decision time.

## Workflow

1. Define the feature contract: entity key, meaning, update cadence, online/offline use, freshness.
2. Enforce point-in-time correctness: training rows use only information available at prediction time.
3. Share definitions and validation between offline and online paths.
4. Assign lifecycle: producer, consumers, deprecation path, quality monitoring.
5. Detect stale or missing features before they reach a model.

## Red Flags

- Training on the latest value instead of the as-of value.
- Point-in-time logic undefined.
- Offline and online definitions diverge, or parity is left to the model team.
- Internal features with no documented meaning.
- Stale features unmonitored; ownership unclear.

## Verification

- [ ] Feature meaning, keys, and freshness are documented
- [ ] Point-in-time correctness is enforced
- [ ] Offline/online parity expectations are explicit
- [ ] Stale, missing, or drifting features are monitored
