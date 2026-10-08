---
name: data-lake-and-zone-architecture
description: Guides agents through data lake and zone architecture design. Use when defining raw, refined, curated, or publish layers; storage organization; retention; and operational boundaries for a data lake.
---

# Data Lake And Zone Architecture

## When to Use

- Designing a new lake, or reorganizing raw/staging/refined/curated zones.
- Defining object-storage layout, lifecycle, and retention rules.
- Separating landing, transformation, and publish responsibilities.

Do not add zones that have no distinct operational purpose.

## Workflow

1. Define purpose and consumers: source landing needs, producer teams, publish consumers, compliance and retention.
2. Define the zone model: raw/landing, standardized/staging, refined/modeled, publish/serving.
3. For each zone, state who writes, who reads, its quality guarantees, and whether mutation is allowed.
4. Set storage conventions: path/catalog naming, partitioning, retention lifecycle, file sizes, ownership tags and metadata.
5. Keep publish rules separate from lake convenience; a file in the lake is not ready for shared use until it meets publish contracts.

## Red Flags

- Everything dumped in one bucket "to organize later".
- Zone meanings overlap or are undocumented.
- Dataset or zone ownership is unclear.
- Publish and landing data are mixed.
- Raw landing data consumed as if contract-checked.
- No retention, cleanup, or lifecycle policy.

## Verification

- [ ] Each zone has a clear purpose and boundary
- [ ] Ownership, read/write rights, and quality guarantees are explicit
- [ ] Storage conventions and lifecycle rules are documented
- [ ] Publish datasets are separated from raw landing data
