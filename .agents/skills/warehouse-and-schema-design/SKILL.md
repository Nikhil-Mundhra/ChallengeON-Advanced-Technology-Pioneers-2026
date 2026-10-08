---
name: warehouse-and-schema-design
description: Guides agents through data warehouse and schema design. Use when defining fact and dimension models, keys, grain, normalization versus denormalization, serving-layer schema boundaries, and downstream-friendly table design.
---

# Warehouse And Schema Design

## When to Use

- Designing marts, warehouse schemas, or curated serving tables.
- Choosing fact/dimension boundaries, grain, surrogate keys, relationships.
- Balancing normalization and denormalization; restructuring analytics datasets.

Schema design covers behavior, meaning, and query ergonomics, not just column names.

## In this repo

- Keep grains separate: daily vs monthly flights (`source_grain`), weekly panel (market, week_start, dataset_split), daily panel (market, date).
- Keep missing, absent, suppressed, imputed, and genuine-zero values distinguishable (existing flag columns such as `is_suppressed_arrival`, `is_source_present`).

## Workflow

1. Define grain first: what one row is, the primary questions, how time and change are represented.
2. Choose the pattern: dimensional, data-vault integration layer, normalized operational serving, or denormalized marts.
3. Define keys and relationships: business keys, surrogate keys where needed, slowly changing behavior, null/unknown-member handling.
4. Optimize for consumers as well as model purity.
5. Check fit with performance, governance, and metric use.

## Red Flags

- Grain deferred or undocumented.
- Wide tables that hide conflicting grains.
- Normalization (or denormalization) applied by default rather than by trade-off.
- Fact tables mix incompatible event types.
- Keys inconsistent across domains.
- Schema driven only by current dashboard convenience.

## Verification

- [ ] Row grain and key strategy are explicit
- [ ] Schema pattern matches the use case
- [ ] Consumer usability and performance are considered
- [ ] Change-over-time behavior is documented where relevant
