---
name: master-data-and-entity-resolution
description: Guides agents through master data and entity resolution workflows. Use when matching identities across systems, defining canonical entities, resolving duplicates, or building golden records for shared downstream use.
---

# Master Data And Entity Resolution

## When to Use

- Building customer, product, or account golden records.
- Resolving duplicate identities across systems.
- Defining master data domains or publishing canonical reference data.

Do not resolve shared entities with ad hoc joins.

## In this repo

- Market universe: `tourism_twin/domain/markets.py`. `data/panel.py` `build_market_case` maps both panels' country/nationality labels; reuse it, never a second mapping.
- Departure country and guest nationality share labels by assumption, not observed identity; describe the link as an effective conversion.

## Workflow

1. Define the entity contract: canonical type, contributing systems, primary identifiers, match confidence logic, owner.
2. Choose matching: exact key, deterministic rules, or probabilistic/scored.
3. Define attribute-level survivorship: which system wins, under what conditions.
4. Track unresolved and ambiguous cases.
5. Publish with confidence and lineage context.

## Red Flags

- A single convenient identifier (e.g. email) assumed unique and stable.
- No explicit canonical entity definition.
- Survivorship implicit in SQL ordering.
- Ambiguous cases silently dropped or forced.
- Consumers not told the match-confidence assumptions.

## Verification

- [ ] Canonical entity and source systems are explicit
- [ ] Match and survivorship rules are documented
- [ ] Ambiguous cases have a handling path
- [ ] Published master data carries lineage or confidence context
