# Data quality notes — ChallengeON DCT datasets

Findings from profiling `lake/curated/*.parquet` on 2026-09-28. The build pipeline
(`scripts/build_lake.py`) already validates duplicates, key integrity, and the
`total_pax = p2p + transfer + transit` identity — none of those failed. The items
below are modeling decisions and caveats, not load errors.

## Verified clean (no action needed)

| Check | Result |
|---|---|
| Negative or zero `guests` | 0 rows |
| `new_arrivals > guests` or `same_day_guests > guests` | 0 rows |
| Guest train coverage | All 1,308 days, 2022-01-01 → 2025-07-31 |
| Guest test coverage | All 212 days, 2025-08-01 → 2026-02-28 |
| Flight key columns (`total_pax`, `total_p2p`, `total_seats`, `load_factor`, `departure_country_name`) | 0 NULLs across 117,608 rows |
| Flight coverage of prediction window | Complete — daily data through 2026-02-28 |

## Issues requiring a decision

### 1. Nationality ↔ departure-country mismatch — the "bridge" problem

Flight "country" means departure country; guest "country" means nationality.
**12 of 45 guest nationalities have no direct flights to AUH** and their visitors
must arrive via connections: Australia, Brazil, Czechia, Denmark, Finland, Mexico,
Morocco, Norway, Pakistan, Romania, South Africa, Sweden.

- Guests from unmatched nationalities: **1,988,750 of 25,429,132 = 7.8%** of
  international guests (train split).
- All 33 flight departure countries match a guest nationality; the mismatch is
  one-directional (guests-only markets).

**Decision needed:** a documented bridge matrix allocating these 12 nationalities
to connection hubs (e.g., Australia → Gulf hubs / UK). Without it, 7.8% of demand
is unattributed in any flights→guests model.

### 2. `same_day_guests` is ~60% NULL

| Split | Rows missing `same_day_guests` |
|---|---|
| Train | 35,026 / 59,930 (~58%) |
| Test | 4,402 / 9,414 (~47%) |

The source `*` conflates zero, suppressed, and not-applicable. The lake keeps NULL
deliberately. **Decision needed:** exclude the column from modeling, or treat NULL
as "negligible" — do not silently impute zero (the dictionary explicitly warns the
meanings are merged).

### 3. Flight data has two grains

| Year | Rows | Distinct days | Grain |
|---|---|---|---|
| 2022 | 1,213 | 12 (all day-of-month = 1) | Monthly |
| 2023–2025 | ~110k | 365/366 each | Daily |
| 2026 | 6,313 | 59 (Jan–Feb) | Daily |

The data dictionary describes the file as monthly; it is only monthly in 2022.
**Decision needed:** calibrate daily-level relationships on 2023+; use 2022 only
as monthly context or drop it for daily joins.

### 4. Load factor >100% on ~8% of flight rows

9,896 of 117,608 rows. Distribution shows this is almost entirely benign:

| Rounded load factor | Rows |
|---|---|
| 1.0 (100–105%) | 9,822 |
| 1.1 | 73 |
| 1.9 | 1 |

The dictionary notes >100% is possible via overbooking/infant counting. One ~190%
outlier exists. **Decision needed:** leave as-is, or clip the single extreme row.

### 5. `new_arrivals` sparse NULLs

262 rows in train (~0.4%), 2 rows in test. Small enough to leave or impute per
nationality; flag rather than block.

## Summary

No further cleaning is required before modeling. The highest-value remaining data
work is the **nationality → departure-country bridge matrix** (issue 1), which is
also called out in the problem statement's data catch.
