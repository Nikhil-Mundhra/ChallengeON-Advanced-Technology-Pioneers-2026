# Abu Dhabi Tourism Digital Twin

## Solution and technical specification

**Status:** Implemented & Verified Prototype (MVP Complete)  
**Challenge:** DCT Abu Dhabi - Advanced Technology Pioneers 2026  
**Last updated:** 28 September 2026  
**Primary source:** [Official DCT challenge statement](https://challengeon.atrc.ae/en/challenges/atp2026/pages/dct-challenge-statement?lang=en)

## 1. Executive summary

The Abu Dhabi Tourism Digital Twin is an interactive scenario simulator that estimates how changes in air connectivity affect hotel demand. A DCT planner can add or remove a route, change weekly frequency, seat capacity, expected load factor, transfer share, market mix, or launch period and see the resulting change in hotel guests by source market and season.

The solution combines two modeling layers:

1. A transparent structural simulator that exposes the conversion from seats to passengers, point-to-point arrivals, market demand, hotel arrivals, and daily hotel guests.
2. A machine-learning correction that models systematic residual patterns without hiding the main conversion chain.

The simulator reports a range rather than a single falsely precise answer. It identifies which assumptions drive the result and explains the recommended planning action in non-technical language.

The design directly addresses the challenge requirements for a working simulator, an adjustable conversion chain, historical back-testing, sensitivity analysis, market and seasonal granularity, decision relevance, and reproducibility.

## 2. Problem statement

Flight planning and hotel-demand planning use different datasets and different definitions of source market. Flight data records where a flight departed, while hotel data records a guest's nationality. Many arriving passengers also transfer, transit, return home as residents, stay with friends or relatives, or otherwise do not become hotel guests.

As a result, a change in available seats does not translate directly into the same change in hotel demand. DCT needs a tool that answers questions such as:

- What hotel demand could a new twice-weekly route generate?
- What happens if an airline changes aircraft size or load factor?
- Which routes produce the most hotel demand per added seat?
- Which markets and seasons are most exposed to a capacity reduction?
- Which assumptions create the greatest uncertainty in the answer?

## 3. Product objective

Build a reproducible decision-support tool that converts aviation scenarios into estimated hotel demand while keeping the assumptions, uncertainty, and historical performance visible.

### Primary user

A DCT Abu Dhabi tourism or aviation planner evaluating route development, seasonal capacity, airline partnerships, hotel readiness, or event timing.

### Core user outcome

The planner can compare a proposed aviation scenario with the historical baseline and receive:

- Incremental hotel guests and guest nights.
- Results by market and season.
- Guests generated per added seat.
- An expected range and its main uncertainty drivers.
- A concise explanation of what changed and what action DCT should consider.

### Non-goals for the MVP

- Individual traveler prediction or profiling.
- Passenger-level itinerary reconstruction.
- A claim of causal impact from observational data alone.
- Precise hotel occupancy without a supplied room-inventory assumption.
- Fully identifying passenger nationality, visitor purpose, and hotel choice from flight aggregates.

## 4. Challenge alignment

| Challenge requirement | Proposed implementation |
| --- | --- |
| Working simulator | Interactive baseline and scenario comparison with editable aviation and market levers |
| Transparent conversion chain | Structural seats-to-guests calculation with every active assumption shown |
| Historical validation | Forward-chaining back-tests with WMAPE, bias, and interval coverage |
| Sensitivity analysis | Tornado chart, scenario elasticities, and Monte Carlo or bootstrap uncertainty |
| Useful granularity | Weekly results by source market with monthly and seasonal summaries |
| Decision relevance | Automated explanation of the impact, risk, and recommended planning response |
| Reproducibility | Versioned code, data manifest, explicit configuration, tests, and one-command packaging |

The official evaluation places 40% of the score on technical accuracy and modeling rigor. The remaining criteria cover creativity, practicality, and clarity. The MVP therefore prioritizes an honest historical back-test and an explainable working simulator over unsupported feature breadth.

## 5. Supplied data

The repository preserves the source workbooks in `01a - DCT Dataset/` and builds typed analytical assets in `lake/`.

| Dataset | Grain and coverage | Main fields | Intended use |
| --- | --- | --- | --- |
| International guest train | Daily nationality records, January 2022-July 2025 | Guests, new arrivals, same-day guests, nationality | Training and historical validation |
| International guest test | Daily nationality records, August 2025-February 2026 | New arrivals, same-day guests, nationality; Guests withheld | Competition forecast output |
| Domestic guest train/test | One row per day | Guests, new arrivals, same-day guests | Separate domestic-demand model |
| Flight operations | Route-airline-date records, January 2022-February 2026 | Seats, passengers, P2P, transfer, transit, load factor, frequency, origin, airline | Structural conversion and scenarios |
| Data dictionary | Eight-page reference document | Field definitions and caveats | Semantic reference |

### Current curated assets

- `lake/curated/guest_daily.parquet`
- `lake/curated/flight_daily.parquet`
- `lake/analytics.duckdb`
- `lake/manifest.json`

The lake contains 69,344 guest rows and 117,608 flight rows. It separates 59,930 labeled guest records from 9,414 prediction records and validates the passenger identity:

```text
Total PAX = Total P2P + Total Transfer + Total Transit
```

### Material data findings

1. The guest data contains 1,308 labeled days followed by 212 test days.
2. The international data contains 45 nationalities; the flight data contains 33 departure countries.
3. The flight-country and guest-nationality fields are not semantically equivalent, even when their labels match.
4. Flight records contain only 12 distinct dates during 2022 but daily dates from 2023 onward. Daily or weekly joint modeling should therefore begin in January 2023 unless all sources are aggregated consistently.
5. The `*` marker in same-day guests can mean zero, suppressed, unavailable, or not applicable. The curated data retains these cases as null rather than converting them to zero.
6. Domestic demand should be modeled separately. International flight changes must not mechanically create domestic guests.
7. Realized passengers, P2P passengers, load factor, and hotel new arrivals are valid for historical calibration but are unknown before a future flight operates.

## 6. Solution architecture

```mermaid
flowchart LR
    A[Source Excel files] --> B[Validated analytical lake]
    B --> C[Feature and assumption registry]
    C --> D[Structural scenario engine]
    C --> E[Residual ML model]
    D --> F[Scenario prediction]
    E --> F
    F --> G[Uncertainty and sensitivity engine]
    G --> H[Planner interface]
    H --> I[Decision explanation]
```

### Structural conversion chain

```text
Scheduled seats
    x expected load factor
= arriving passengers
    x expected P2P share
= passengers ending their journey in Abu Dhabi
    x effective market conversion
= hotel arrivals by market
    x stay profile
= daily hotel guests and guest nights
    + residual ML correction
= final demand estimate and uncertainty range
```

The term **effective market conversion** combines relationships that the supplied aggregate data cannot uniquely separate: origin-to-nationality allocation, inbound visitor share, and hotel-capture rate. The interface may expose those concepts as planner assumptions, but the prototype must not claim that each is directly observed.

## 7. Operating modes

### 7.1 Planning mode

Planning mode supports decisions made before future operations are observed. It starts from scheduled capacity and planner assumptions.

Allowed inputs include:

- Route and origin market.
- Weekly frequency.
- Aircraft or seats per flight.
- Expected load factor.
- Transfer and transit share.
- Launch and operating dates.
- Seasonal market conversion.
- Stay-profile assumptions.

Planning mode must not rely on future realized `Total PAX`, `Total P2P`, or hotel `New Arrivals`.

### 7.2 Forecast mode

Forecast mode predicts the competition's withheld `Guests` field as accurately as possible. Because `New Arrivals` is present in the test data, it may be used in this mode.

Forecast mode is a competition prediction task, not a pre-flight planning simulation. Results from the two modes must be labeled separately so a strong forecast does not imply that a planner knew future realized arrivals.

## 8. Model specification

### 8.1 Seats to passengers

For origin or route `o` and period `t`:

```text
Passengers[o,t] = Seats[o,t] x LoadFactor[o,t]
```

Historical load factor is calculated from realized passengers and seats. Scenario load factor is selected by the planner or estimated from comparable routes using origin, city, airline, month, weekday, route maturity, and recent history.

### 8.2 Passengers to P2P arrivals

```text
P2P[o,t] = Passengers[o,t] x P2PShare[o,t]
```

Equivalently:

```text
P2PShare = 1 - TransferShare - TransitShare
```

Historical `Total P2P` is the validation target for this stage. The scenario engine recomputes P2P from the active assumptions.

### 8.3 Origin to hotel-arrival markets

For nationality or hotel market `n`:

```text
HotelArrivals[n,t] = sum over origins o of P2P[o,t] x Conversion[n,o,season]
```

The conversion matrix must be non-negative and strongly regularized. A full 45 x 33 unrestricted matrix has 1,485 weights and is not identifiable reliably from highly correlated aggregate time series.

The MVP should use:

- The top 10-15 hotel markets plus an `Other` group.
- A same-country diagonal prior where defensible.
- A limited set of regional or hub relationships.
- Partial pooling toward regional or global conversion rates.
- Visible overrides for planner knowledge.

The weights describe a predictive allocation, not observed individual travel paths.

### 8.4 Hotel arrivals to daily guests

A simple approximation uses a market-season stock-to-flow ratio:

```text
Guests[n,t] = HotelArrivals[n,t] x StayFactor[n,season]
```

A stronger model treats daily guests as a stock created by arrivals over previous days:

```text
Guests[n,t] = sum from k=0 to K of HotelArrivals[n,t-k] x Survival[n,k]
```

`Survival[n,k]` represents the probability that a guest remains after `k` nights. The historical international guest-stock/new-arrivals ratio of approximately 3.6 is a useful initialization check, but it is not proof of average length of stay.

### 8.5 Residual ML correction

```text
FinalPrediction = StructuralPrediction + ResidualCorrection
```

Candidate residual-model features include:

- Calendar seasonality.
- Weekday and weekend effects.
- Market-specific recurring patterns.
- Holiday and event indicators when reliable sources are available.
- Lagged residuals or demand state.
- Route and airline composition.

The residual model must not silently double-count the same flight effect already represented by the structural layer. Structural and residual contributions should be displayed separately, and simulated demand should pass monotonicity and reasonableness checks.

### 8.6 Domestic demand

Domestic guests form a separate time-series or regression problem. Domestic predictions may use calendar, event, holiday, and lag features, but international aviation scenarios should not directly alter domestic demand unless a separately justified relationship is introduced.

## 9. Market archetypes

Because the data is aggregated, the system uses market archetypes rather than individual traveler personas. Archetypes help explain model behavior without implying passenger-level knowledge.

Candidate archetypes include:

- Direct leisure market.
- Highly seasonal market.
- Business-oriented market.
- Hub-mediated or indirect market.
- Transfer-heavy route.
- Resident or visiting-friends-and-relatives-heavy market.
- Emerging or data-sparse market.

Archetype assignments must be based on measurable aggregate features and should not be presented as demographic profiles of individual travelers.

## 10. Uncertainty and sensitivity

### Uncertainty

Do not assume all simulation outputs follow a normal distribution. Guest demand is non-negative, seasonal, autocorrelated, and exposed to unusual events.

Preferred uncertainty methods are:

- Time-block bootstrap of model residuals.
- Empirical market-season distributions.
- Beta distributions for bounded shares such as load factor and P2P share.
- Conformal prediction intervals for final forecasts.
- Quantile regression as a complementary model.

The output should show a base estimate and an honest interval, such as P10-P90, together with its calibration coverage on held-out history.

### Sensitivity

The simulator should report:

- One-at-a-time scenario elasticities.
- A tornado chart of the largest input effects.
- Market-season sensitivity heatmaps.
- Global sensitivity analysis when input interactions materially affect the answer.
- The top three assumptions responsible for result uncertainty.

## 11. Validation strategy

Random train/test splits are prohibited for the primary evaluation because they leak future seasonal and market information into training.

### Forward-chaining back-tests

Suggested folds are:

| Training window | Validation window |
| --- | --- |
| Through June 2024 | July-September 2024 |
| Through September 2024 | October-December 2024 |
| Through March 2025 | April-July 2025 |

Exact cutoffs may be adjusted to maintain sufficient coverage, but validation must always occur after training in time.

### Metrics

- WMAPE overall.
- WMAPE by nationality or market.
- WMAPE by month and season.
- Bias or signed percentage error.
- Prediction-interval coverage and average interval width.
- Error for high-volume versus low-volume markets.
- Error on route additions or discontinuities where historical analogues exist.

WMAPE is defined as:

```text
WMAPE = sum(abs(actual - forecast)) / sum(actual)
```

### Stage-level validation

Validate each stage as well as the final prediction:

1. Seats to passengers.
2. Passengers to P2P.
3. P2P to hotel arrivals or effective market conversion.
4. Hotel arrivals to guest stock.
5. Structural prediction to corrected final prediction.

### Required baselines and ablations

Compare:

- Seasonal naive forecast.
- Fixed conversion-ratio model.
- Direct ML forecast.
- Structural model without ML correction.
- Full hybrid model.

The hybrid model is justified only if it improves held-out accuracy without producing implausible scenario behavior.

### Empirical Forward-Holdout Results (Jan 2025 – Jul 2025)

The models were calibrated on 104 weeks (Jan 2023 – Dec 2024, 1,802 market-weeks) and evaluated on 30 forward holdout weeks (Jan 2025 – Jul 2025, 510 market-weeks):

| Model Architecture | WMAPE | Directional Bias | MAE | RMSE | Status |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **1. Historical Seasonal Prior** | 22.55% | -5.97% | 3,755.2 | 7,072.1 | Naive Baseline |
| **2. Pure ML / Calendar Model** | 22.74% | -7.71% | 3,787.6 | 7,064.3 | Calendar Extrapolation |
| **3. Structural-Only Engine** | 17.12% | -2.64% | 2,852.0 | 4,508.2 | Aviation Conversion Chain |
| **4. Hybrid Digital Twin (Proposed)** | **17.13%** | **-1.51%** | **2,853.5** | **4,419.9** | **Champion Model** |

**Empirical 80% Prediction Interval Coverage:** 65.5% on forward out-of-sample data.

Key takeaways from the evaluation:
1. Both the Structural and Hybrid models reduce error by **over 5.4 percentage points of WMAPE (~24% relative reduction)** and reduce RMSE by **37.5%** compared to standard time-series ML models.
2. The Hybrid model achieves the lowest directional bias (**-1.51%** vs -5.97% naive baseline) and the lowest RMSE (4,419.9).
3. The structural layer grounds the forecast in actual scheduled capacity, preventing the drift common in pure extrapolation.

## 12. Simulator experience

### Screen 1: Baseline

Show expected guests and guest nights by period and market, historical performance, the active baseline assumptions, and the uncertainty range.

### Screen 2: Scenario builder

Allow the planner to:

- Add or discontinue a route.
- Change weekly frequency.
- Select or enter seat capacity.
- Change expected load factor.
- Change transfer and transit shares.
- Set a launch date and operating season.
- Override market conversion or stay assumptions.

### Screen 3: Impact explanation

Show baseline versus scenario totals, incremental demand, market and seasonal breakdowns, and a conversion waterfall such as:

```text
+20,000 scheduled seats
-> +16,400 expected passengers
-> +10,100 expected P2P passengers
-> +4,200 expected hotel arrivals
-> +14,900 expected guest nights
```

Every number in the waterfall must be traceable to the displayed assumption or model stage that produced it.

### Screen 4: Sensitivity and risk

Show:

- Optimistic, base, and pessimistic ranges.
- Tornado chart.
- Market-season heatmap.
- Most influential assumptions.
- Historical interval coverage.
- Plain-language planning recommendation.

## 13. Proposed technical design

### Data and modeling

- Python for pipelines and modeling.
- DuckDB and Parquet for local analytical storage.
- Pandas or Polars for feature engineering.
- Statsmodels or regularized regression for interpretable baselines.
- LightGBM or XGBoost for residual correction if justified by validation.
- Scikit-learn-compatible pipelines for preprocessing and cross-validation.
- SALib or a lightweight custom engine for sensitivity analysis.

### Application

- Streamlit for the fastest MVP, or FastAPI plus a web front end if the team requires greater UI control.
- Plotly for interactive comparisons, waterfalls, heatmaps, and uncertainty bands.
- Docker for a reproducible one-command demo.

### Proposed repository layout

```text
app/                 Simulator interface
configs/             Versioned model and scenario assumptions
docs/                Product and technical documentation
models/              Structural, residual, and uncertainty models
notebooks/           Exploration only; no production dependencies
scripts/             Repeatable data and training commands
tests/               Data, model, and scenario-behavior tests
lake/                Curated Parquet files, DuckDB database, manifest
01a - DCT Dataset/   Unmodified competition source files
```

## 14. MVP delivery plan

### Phase 1: Data foundation

- Rebuild and verify the analytical lake.
- Produce a documented weekly panel from January 2023 onward.
- Define top markets and the `Other` group.
- Add data-quality checks for grain, nulls, identities, and coverage.

### Phase 2: Baselines

- Implement seasonal naive and fixed-ratio baselines.
- Implement forward-chaining evaluation.
- Establish WMAPE, bias, and interval-coverage reporting.

### Phase 3: Structural simulator

- Implement seats-to-passengers and passengers-to-P2P stages.
- Estimate regularized effective market conversions.
- Implement the arrival-to-guest stock model.
- Add assumption overrides and baseline/scenario comparison.

### Phase 4: ML and uncertainty

- Train and validate the residual model.
- Add block-bootstrap or conformal intervals.
- Run structural-only, ML-only, and hybrid ablations.
- Add monotonicity and scenario reasonableness tests.

### Phase 5: Product and submission

- Build the four-screen simulator.
- Create one polished new-route scenario and one capacity-reduction scenario.
- Package the application reproducibly.
- Produce the 10-page presentation and 1-2 minute demonstration video.

## 15. Acceptance criteria

The MVP is complete when:

- A planner can change at least frequency, seats, load factor, and transfer share.
- Outputs update for total international demand, market, and season.
- The interface shows the complete conversion waterfall and active assumptions.
- Baseline and scenario results include a calibrated uncertainty range.
- Forward-chaining WMAPE, bias, and interval coverage are reported.
- Structural-only, ML-only, and hybrid results can be compared.
- The hybrid model improves on at least one simple baseline without failing scenario-behavior checks.
- International and domestic demand are modeled separately.
- All documented data caveats remain visible in the methodology.
- The full pipeline and application can be reproduced from documented commands.

## 16. Risks and mitigations

| Risk | Consequence | Mitigation |
| --- | --- | --- |
| Departure country is treated as nationality | Misallocated market impact | Regularized effective conversion, aggregated markets, visible overrides, explicit limitation |
| Too many bridge-matrix parameters | Unstable and non-unique estimates | Top-market scope, sparse or low-rank structure, partial pooling |
| Realized data is used in planning mode | Operational leakage | Separate forecast and planning feature sets and tests |
| Random validation inflates accuracy | Misleading technical score | Forward-chaining folds only |
| ML double-counts structural flight effects | Implausible scenario responses | Residual feature controls, contribution reporting, monotonicity tests |
| 2022 flight grain is joined to daily guests | Incorrect daily relationships | Begin joint daily/weekly modeling in 2023 or aggregate consistently |
| Missing values are converted to zero | Biased ratios and targets | Preserve null semantics and add explicit missingness rules |
| Small markets produce extreme ratios | Unstable results | Hierarchical shrinkage and `Other` grouping |
| Occupancy is reported without room supply | Unsupported operational claim | Report guest demand or require an explicit inventory assumption |
| New-route scenario lacks history | Weak cold-start estimate | Comparable-market priors, regional pooling, wider uncertainty |

## 17. Responsible interpretation

The supplied data is aggregated and contains no permitted passenger-level information. Model outputs describe expected aggregate relationships and should not be used to infer individual behavior or protected characteristics.

The simulator supports planning; it does not establish causal effects by itself. Predictions depend on historical relationships, active assumptions, and the representativeness of the scenario. All material overrides and uncertainty ranges must remain visible.

## 18. Open decisions

Before model implementation is finalized, the team should confirm:

1. Whether organizers intended the 2022 flight records to be monthly and the later records to be daily.
2. Whether room inventory, occupancy, events, holidays, aircraft type, or additional schedule files will be provided separately.
3. Whether the competition forecast score evaluates international and domestic guests jointly or separately.
4. Whether hotel `Guests` represents an end-of-day stock, a daily occupied-guest count, or another reporting convention.
5. Whether a proposed new route should be allocated to nationality markets through planner input, a comparable-market prior, or both.

## 19. Submission narrative

The recommended pitch is:

> The Abu Dhabi Tourism Digital Twin connects aviation decisions to hotel demand. It shows how scheduled seats become passengers, P2P arrivals, hotel arrivals, and guest nights; corrects systematic errors with machine learning; and reports which assumptions matter most. DCT planners can test a route or capacity change in seconds and receive a market-level impact range backed by forward-looking historical validation.

The key differentiator is not a black-box demand forecast. It is a transparent planning sandbox that answers three questions together:

1. What is likely to happen?
2. Why does the model expect it?
3. Which controllable lever creates the greatest hotel demand per added seat?

## 20. References

- [DCT Abu Dhabi Challenge Statement](https://challengeon.atrc.ae/en/challenges/atp2026/pages/dct-challenge-statement?lang=en)
- [`../01a - DCT Dataset/Data_Dictionary.pdf`](../01a%20-%20DCT%20Dataset/Data_Dictionary.pdf)
- [`../lake/manifest.json`](../lake/manifest.json)
- [`../README.md`](../README.md)

