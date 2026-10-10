# Nationality groups for pooling and profiles (issue #2)

A `nationality → group` table so small markets can borrow strength from
similar ones: partial pooling in `nowcast/pooling.py` (the `group_scale`
component pools within `family`) and the nationality profiles.

Reproduce with:

```bash
python scripts/build_nationality_groups.py
```

Writes `nationality_group_evidence.csv` (measured discriminators per
nationality) and `nationality_group_table.csv` (the proposed mapping with
per-member basis and borderline notes). All measurements are on the train
split only.

## Discriminators measured

| Column | Definition | What it discriminates |
| --- | --- | --- |
| `guest_nights_per_arrival` | Σ guests ÷ Σ new arrivals | Turnover intensity — how many guest-nights each arrival carries. **Not** a stay-length estimate (stay-length outputs were removed in 7b6db76 and this is deliberately not labelled as one). |
| `thu_fri_arrival_pct` | 100 × Thu+Fri arrivals ÷ all arrivals | The GCC weekend-trip signature — regional visitors arriving for weekends. |
| `same_day_guest_pct` (+ `same_day_missing_pct`) | Σ same-day ÷ Σ guests, with suppression rate | Day-visit share. Reported alongside its missing share because suppression is heavy (0–95%) and the column cannot carry decisions on its own. |

## What the evidence shows

`guest_nights_per_arrival` is a **continuum** (1.61 Oman → 5.13 Sweden), not
two separated modes — so the grouping needs a second discriminator, and the
Thu/Fri arrival share provides it:

- **Short family — the GCC five.** Oman 1.61, Qatar 2.13, Saudi 2.45 anchor the
  bottom of the continuum and are the only block with a materially elevated
  Thu/Fri arrival share (35.6–37.4%). Bahrain (2.97) and Kuwait (3.26) sit in a
  ratio band shared with several non-GCC nationalities (Israel 2.81,
  Uzbekistan 3.04, S. Korea 3.07, Poland 3.18, Pakistan 3.22, Australia 3.27);
  they are kept in the family on the weekend signature (Thu/Fri 32.6% and
  31.4% vs ~28–31% for the band) and regional coherence — flagged as
  borderline in the table.
- **Domestic** (2.46) is included in the short family for the profiles per the
  issue's candidate split. It is a residence group, not a nationality, so it
  is not consumed by `POOLED_NATIONALITIES` — documented for completeness.
- **China is flagged, not grouped.** Its turnover (2.25) is low enough to look
  "short", but its weekday profile is flat (Thu/Fri 28.1%, *below* average) —
  the low ratio has a different mechanism than GCC weekend trips. Whether it
  pools better in the short family is a kernel-shape question: §4.7 measured
  that one shared shape fits long-haul markets but not Oman or domestic, so
  family membership should ultimately be confirmed by the shared-kernel WAPE
  cost per nationality, not the turnover ratio alone. That test is the
  follow-up; the ratio is the screen the issue asked for.
- The remaining 34 nationalities are `long` by default — mid-to-high turnover
  (3.3–5.1) with no weekend signature.

## Proposed table

`short`: OMAN, QATAR, SAUDI ARABIA, BAHRAIN, KUWAIT, DOMESTIC
`long`: all other nationalities.

This matches the shipped `SHORT_STAY_FAMILY` in `nowcast/specs.py` (the GCC
five) plus domestic for profile use — the current code is *consistent with*
the evidence, and this table now records the basis for each member.

## Limits

- Turnover ratios pool the full training window; §4.7 shows guests-per-arrival
  drifts within markets (Egypt +33%, Philippines +43%), so memberships near the
  boundary should be rechecked if the panel extends.
- `same_day_guests` suppression makes that column unusable as a discriminator
  for most nationalities (median missing share ~49%); it is reported for
  completeness only.
- The grouping is a modelling convenience for borrowing strength — it does not
  claim the members share passenger purpose or origin mechanics.
