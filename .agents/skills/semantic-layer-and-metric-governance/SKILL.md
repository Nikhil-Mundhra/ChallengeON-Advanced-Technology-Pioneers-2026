---
name: semantic-layer-and-metric-governance
description: Guides agents through semantic layer and shared metric design. Use when defining business metrics, reusable dimensions, governed metric contracts, or shared semantic models consumed by dashboards, analytics tools, or other teams.
---

# Semantic Layer And Metric Governance

## When to Use

- Defining or changing business metrics.
- Introducing a semantic or metric layer.
- Standardizing dimensions and filters across teams; governing shared KPIs.

Do not rely on ad hoc BI formulas for metrics that need cross-team trust.

## In this repo

- Panel metrics (load factor, P2P share, implied LOS, response multiplier) are defined once in `tourism_twin/features/ratios.py`; reuse them via `PANEL_FEATURES.apply`, never re-derive.
- Ratios are recomputed from summed parts at each grain, never summed or averaged.
- Ship metric-definition changes as a separate, explicitly reported change.

## Workflow

1. Define the metric contract: owner, exact meaning, grain, numerator/denominator, filters and exclusions.
2. Standardize shared dimensions and time logic.
3. Map consumers and use cases; govern cross-functional metrics more strictly.
4. Centralize metric logic.
5. Version or migrate breaking definition changes deliberately.

## Red Flags

- A metric's meaning assumed to be common knowledge.
- Formulas reimplemented locally in BI or downstream code.
- No named metric owner.
- Filters and exclusions implicit.
- The same KPI exists in incompatible forms.
- Definition changes shipped without communication.

## Verification

- [ ] Metric owner and meaning are explicit
- [ ] Shared dimensions and filters are standardized
- [ ] Consumer impact is assessed for metric changes
- [ ] Breaking changes have a migration or communication path
