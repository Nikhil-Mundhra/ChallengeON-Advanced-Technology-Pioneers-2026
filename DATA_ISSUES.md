# Data issues and remediation plan

Audit date: 2026-09-28

Scope:

- Raw guest and flight workbooks in `01a - DCT Dataset/`
- `Data_Dictionary.pdf`
- Curated Parquet tables and the weekly market panel
- Lake and panel construction logic
- Current forward-holdout evaluation

The source data passes several basic integrity checks, but the current weekly
panel contains semantic and aggregation risks that materially limit
market-level aviation-to-hotel conclusions. The largest problem is not a simple
cleaning defect: guest nationality and flight departure country describe
different populations and cannot be treated as a direct join key.

## Executive summary

| Priority | Issue | Consequence |
|---|---|---|
| Critical | Guest nationality is joined to flight departure country | Market-level conversion rates and aviation effects are not reliably identified |
| Critical | Flight data changes from monthly in 2022 to daily in 2023 | The `flight_daily` table can misrepresent 2022 monthly totals as single-day observations |
| High | Missing guest inputs are silently aggregated | Weekly totals can look complete while omitting missing `new_arrivals` or `same_day_guests` values |
| High | Missing nationality-date rows have no defined meaning | Absent combinations are implicitly treated as zero even though they may be missing reports |
| High | The configured top 15 is not the observed top 15 | Philippines is pooled into `OTHER INTERNATIONAL`; lower-ranked Armenia is modeled separately |
| High | Domestic demand has no aviation counterpart | Domestic aviation metrics are zero, so aviation levers are not meaningful for this segment |
| Medium | Load factors above 100% are clipped in the panel | Genuine source behavior and possible quality problems are hidden |
| Medium | Route-level frequency is averaged across routes | The resulting market metric is not total weekly flight frequency |
| Medium | Test targets are unavailable | Performance after July 2025 cannot be evaluated |
| Medium | Documentation and reported benchmarks are stale | Consumers cannot reproduce the documented schema or headline performance |

## Verified clean checks

These checks passed and should remain in the automated quality gate:

| Check | Result |
|---|---|
| Guest candidate-key duplicates | 0 |
| Flight candidate-key duplicates | 0 |
| Missing `guests` in training rows | 0 |
| Populated `guests` in test rows | 0, as expected for the prediction split |
| Negative guest measures | 0 |
| `new_arrivals > guests` in labeled data | 0 |
| `same_day_guests > guests` in labeled data | 0 |
| `total_pax = total_p2p + total_transfer + total_transit` failures | 0 |
| Load-factor arithmetic mismatches | 0 beyond floating-point tolerance |
| Domestic date coverage | 1,308 train days followed by 212 test days, with no gaps |
| Flight date coverage from 2023 onward | Complete daily dates through 2026-02-28 |

## Detailed findings

### 1. Nationality and departure country are not a valid direct bridge

The guest files segment demand by passport nationality. The flight file
segments supply and passengers by the country from which a flight departed.
The weekly panel maps both fields to a common `market` label and joins them by
date and label in [`engine/panel.py`](engine/panel.py).

This is a semantic mismatch, even when the strings are identical. For example:

- An Indian national can arrive through London, Doha, or another hub.
- A flight from India can carry passengers of several nationalities.
- Transfer and transit traffic further weaken the equivalence between origin
  airport and hotel-guest nationality.

The mismatch is visible in the source coverage:

- Guest data contains 45 nationalities.
- Flight data contains 33 departure countries.
- Twelve guest nationalities have no direct-flight origin rows: Australia,
  Brazil, Czechia, Denmark, Finland, Mexico, Morocco, Norway, Pakistan,
  Romania, South Africa, and Sweden.

A manually invented bridge matrix would add assumptions rather than recover the
missing relationship. The preferred missing input is passenger nationality or
true origin-and-destination data for P2P passengers. Until that exists,
market-level outputs should be labeled as proxy associations, or both sources
should be aggregated to a defensible common level such as total international.

### 2. Flight data contains two incompatible grains

| Period | Rows | Distinct dates | Observed grain |
|---|---:|---:|---|
| 2022 | 1,213 | 12 | Monthly, recorded on the first day of each month |
| 2023 | 33,349 | 365 | Daily |
| 2024 | 37,607 | 366 | Daily |
| 2025 | 39,126 | 365 | Daily |
| Jan-Feb 2026 | 6,313 | 59 | Daily |

The dictionary describes the flight file as monthly. The lake instead exposes
all 117,608 rows through `flight_daily` without a `source_grain` field. The
weekly panel filters to 2023 onward, which avoids this problem in that artifact,
but the general curated table remains unsafe for unrestricted daily analysis.

Required action: split the monthly and daily observations into separate tables,
or add an explicit grain field and prevent 2022 rows from entering daily joins.

### 3. Missing guest values become understated aggregates

International `new_arrivals` contains 264 missing values:

| Split | Missing | Rows | Rate |
|---|---:|---:|---:|
| Train | 262 | 58,622 | 0.45% |
| Test | 2 | 9,202 | 0.02% |

Ninety-two of these missing values occur from 2023 onward. They affect 53
market-weeks in the panel: 50 `OTHER INTERNATIONAL` weeks and 3 Armenia weeks.
SQL `SUM` ignores individual null values when other records are present, so
these weeks receive plausible-looking but incomplete totals.

International `same_day_guests` has much larger missingness:

| Split | Missing | Rows | Rate |
|---|---:|---:|---:|
| Train | 35,026 | 58,622 | 59.75% |
| Test | 4,402 | 9,202 | 47.84% |

The source asterisk combines zero, suppressed, unavailable, and not applicable.
These meanings cannot safely be collapsed to zero or imputed as one numeric
process. Preserve a value-status field and propagate completeness flags into
every aggregate.

### 4. Nationality-date coverage is incomplete

The combined international period contains 1,519 calendar days and 45 observed
nationalities, implying 68,355 possible nationality-date combinations. The
files contain 67,824 rows, leaving 531 absent combinations.

Some nationalities therefore have fewer observations than the period permits;
for example, Finland has 1,379 of 1,519 possible dates and Norway has 1,407.
The dictionary does not say whether a missing row means zero activity or a
missing report. This must be resolved with the data owner. Until then, absence
must not be silently converted to zero.

### 5. The configured top 15 is not the actual top 15

The hard-coded list in [`engine/archetypes.py`](engine/archetypes.py) includes
Armenia, ranked 18th by international training guest volume, while excluding
the Philippines, ranked 14th.

The resulting `OTHER INTERNATIONAL` segment contains 30 nationalities and
25.9% of international training guests. It also pools different regions,
flight-connectivity patterns, lengths of stay, and travel purposes into one
archetype. This is too heterogeneous for a single conversion parameter.

Required action: define the ranking metric and calibration window, derive the
market list programmatically, and split the remainder by region or a validated
behavioral segmentation.

### 6. Domestic observations cannot support aviation scenarios

The weekly panel contains 167 domestic market-weeks. All have zero seats,
passengers, and P2P traffic because the flight source only covers arrivals at
AUH and has no domestic market equivalent. Domestic guest demand is therefore
not connected to the aviation chain.

Domestic forecasting should be a separate staycation model. Domestic results
must not expose frequency, aircraft-gauge, load-factor, or P2P scenario levers.

### 7. Load-factor clipping hides source behavior

The flight workbook contains 9,896 rows above 100% load factor, or 8.4% of all
flight rows. The maximum is 185.7%. The dictionary says values above 100% may
occur because of overbooking or infant-counting differences.

After weekly aggregation, 24 market-weeks remain above 100%, with a maximum of
101.53%. [`engine/panel.py`](engine/panel.py) clips these values to 100%. The
clipping is small in aggregate, but it removes the ability to distinguish valid
source behavior from a quality problem.

Preserve both `load_factor_raw` and a modeling version. Add flags for values
above 100%, large infant adjustments, and any extreme record requiring source
confirmation.

### 8. `Average Weekly Frequency` is not aggregated as market frequency

The source field is route/airline-level average weekly frequency. The panel
calculates an average across route rows. This under-represents markets with
multiple cities or airlines and cannot be interpreted as the total number of
weekly flights serving a market.

Required action: define the field's exact temporal meaning, deduplicate it at
its native route-period grain, and sum compatible service frequencies to the
market level. Do not use the current `avg_frequency` to calibrate frequency
scenario levers.

### 9. Recent targets and important explanatory variables are absent

The `guests` target ends on 2025-07-31. The August 2025-February 2026 test rows
contain predictors only, so recent accuracy, drift, and interval coverage cannot
be measured.

The available sources also omit several variables needed for causal or
operational scenario claims:

- Hotel rooms and inventory, room nights, occupancy, ADR, and RevPAR
- Booking lead times, cancellations, and forward reservations
- Visitor purpose and accommodation type
- Marketing spend and campaign exposure by source market
- Event attendance and event-specific room demand
- Airfares, route launches, schedule changes, and visa-policy changes
- Macroeconomic indicators and source-market exchange rates

Without these inputs, scenario outputs are calibrated sensitivities rather than
causal forecasts.

### 10. The data dictionary does not match the delivered files

`Data_Dictionary.pdf` documents only the two test guest files and the flight
file, despite the presence of two additional train workbooks. It says the test
files contain the `Guests` target and reports six international/five domestic
columns. The actual test files omit `Guests` and contain five international/four
domestic columns. It also labels the entire flight file as monthly even though
the grain changes in 2023.

The dictionary should be regenerated directly from the delivered schemas and
include split purpose, coverage, grain, missing-value semantics, primary keys,
units, and aggregation rules.

### 11. Published evaluation results are stale

The benchmark table in [`README.md`](README.md) reports hybrid WMAPE of 17.13%
and bias of -1.51%. Running the current `scripts/evaluate_models.py` against the
current panel produced:

| Model | WMAPE | Bias | MAE | RMSE |
|---|---:|---:|---:|---:|
| Historical seasonal prior | 22.62% | -7.05% | 3,845.0 | 7,074.2 |
| Pure calendar ML | 22.01% | -8.98% | 3,740.7 | 6,742.6 |
| Structural-only planning mode | 21.85% | +5.44% | 3,714.0 | 6,698.1 |
| Hybrid digital twin | 20.64% | +4.92% | 3,507.6 | 6,307.5 |

The demonstrated nominal 80% interval coverage was 68.4%. The current hybrid
model is best on WMAPE and RMSE in this run, but the README improvements are not
reproducible from the current code and artifacts.

Required action: version the raw-data hashes, panel, code revision, calibration,
evaluation output, and published metrics as one reproducible release.

## Remediation plan

### Phase 1: Establish a reliable data contract

1. Regenerate the dictionary for all five source workbooks.
2. Add explicit fields for source grain, split, target availability, suppression,
   unavailability, and not-applicable status.
3. Separate 2022 monthly flights from 2023+ daily flights.
4. Record the meaning of an absent nationality-date row with the data owner.

Exit criterion: every field has a defined grain, unit, key, missing-value policy,
and permitted aggregation.

### Phase 2: Make incompleteness visible

1. Generate the expected date-nationality grid.
2. Classify missing rows separately from reported zero values.
3. Propagate `is_complete_*` flags through daily, weekly, and market aggregates.
4. Reject calibration records missing any required structural input.
5. Add source-to-curated reconciliation totals by date, split, and market.

Exit criterion: no partial aggregate can appear as a complete observation.

### Phase 3: Correct the market model

1. Obtain passenger-nationality or true origin-and-destination P2P data.
2. Until then, restrict the structural relationship to a compatible aggregate
   level and label country-level results as proxies.
3. Recompute the top markets from a versioned calibration window.
4. Model Philippines separately and reassess Armenia.
5. Replace the single `OTHER INTERNATIONAL` group with validated regional or
   behavioral segments.
6. Split domestic forecasting from international aviation scenarios.

Exit criterion: every modeled market has a defensible relationship between the
aviation population and the hotel-demand population.

### Phase 4: Correct transformations and outlier handling

1. Preserve raw and modeling versions of load factor.
2. Add quality flags instead of silently clipping source values.
3. Rebuild flight frequency at its native route-period grain before aggregation.
4. Review the meaning of `guests / new_arrivals`; do not present it as observed
   average length of stay without validation.
5. Test partial weeks, split-boundary weeks, missing routes, and zero-service
   markets explicitly.

Exit criterion: each derived metric has a documented formula and passes
independent reconciliation checks.

### Phase 5: Rebuild evaluation and reporting

1. Freeze a reproducible data and code version for every benchmark.
2. Use complete, strictly forward holdouts with separate domestic and
   international reporting.
3. Report planning-mode and realized-input performance separately.
4. Calibrate uncertainty to achieve its stated coverage, or lower the claimed
   coverage level.
5. Generate README benchmark tables from saved evaluation output.
6. Add drift monitoring once post-July-2025 targets become available.

Exit criterion: a clean checkout can regenerate the documented metrics from the
recorded raw-data hashes with no manual edits.

## Recommended automated quality gates

- Schema and data-type checks for every source file
- Source hash and row-count reconciliation
- Mixed-grain detection
- Candidate-key uniqueness
- Complete expected date-grid coverage
- Null, suppression, and absent-row counts by market and period
- Missing-value propagation into aggregates
- Passenger and cabin arithmetic identities
- Load-factor and infant-adjustment outlier flags
- Flight-to-guest join coverage by market and date
- Programmatic top-market ranking and drift detection
- Domestic/international feature-availability checks
- Source-to-panel total reconciliation
- Train/test boundary and partial-week checks
- Reproducible benchmark and uncertainty-coverage checks

## Current decision

Do not treat the current country-level panel as a causal aviation-to-hotel
conversion dataset. It is suitable for exploratory proxy modeling from 2023
onward if incomplete observations are flagged, domestic is separated, and the
nationality/departure-country limitation is stated prominently. Resolve the
semantic bridge and missingness policy before using the results for route,
capacity, or marketing investment decisions.
