# Detailed 100-Point Scorecard

Use the official category weights. Scores should reflect evidence quality as well as feature presence.

## 1. Technical accuracy and modelling rigour — 40 points

### Data integrity and market reconciliation — 8

- Raw-to-curated lineage, units, grains, coverage, missingness, suppression, duplicates, and outliers are handled explicitly.
- Flight origin and guest nationality are not silently equated.
- The allocation or effective-conversion approach is identifiable enough for its claimed use, regularized, and honest about limitations.

### Decision-time validity — 8

- Planning evaluation uses only information available when the decision is made.
- Realized-chain and competition-forecast modes are clearly separated from pre-flight planning.
- Temporal boundaries, features, preprocessing, calibration, and model selection avoid future leakage.

### Conversion-chain rigour — 7

- Each stage is dimensionally and mathematically coherent.
- Shares and counts obey physical bounds.
- Stages are validated separately where targets exist.
- Guest arrivals, guest stock, guest nights, occupancy, and length of stay are not conflated.

### Historical validation — 7

- Forward or rolling-origin evaluation is primary; random splits are not used for the main claim.
- WMAPE is accompanied by bias, segment results, and sample support.
- Seasonal naive, fixed-ratio, direct-ML, structural-only, and hybrid baselines or suitable equivalents are compared.
- Ablations justify complexity and expose failure modes.

### Uncertainty calibration — 5

- Intervals use a temporally valid calibration procedure.
- Empirical coverage and interval width are reported overall and for important segments.
- Claimed nominal coverage approximately matches demonstrated coverage, or undercoverage is clearly disclosed.
- Sparse markets and extrapolative scenarios receive appropriately wider uncertainty.

### Software correctness and reproducibility — 5

- A documented clean run regenerates models, metrics, charts, and app outputs deterministically where expected.
- Tests cover invariants, leakage risks, data contracts, scenario bounds, and key integration paths.
- Saved artifacts, documentation, deck, and UI agree.

## 2. Creativity and originality — 20 points

### New decision capability — 8

- The solution enables a useful decision that disconnected flight and hotel forecasts could not answer efficiently.
- Novelty is functional, not merely the use of AI, ML, Monte Carlo, or a fashionable architecture.

### Market-bridge and cold-start design — 5

- The origin-to-nationality mismatch receives a thoughtful, defensible solution.
- New routes and sparse markets use comparable-market priors, partial pooling, or other credible methods.

### Explanation, uncertainty, and sensitivity innovation — 4

- The design helps a planner understand why a result changed, what could make it wrong, and which assumption deserves attention.

### Strategic extensibility — 3

- The concept can credibly extend to additional data, markets, airports, route maturity, hotel inventory, or planning workflows without redesigning the core system.

## 3. Practicality and realism — 20 points

### Planner workflow — 7

- A non-technical user can construct, compare, interpret, and communicate a scenario without developer help.
- Inputs, defaults, units, and consequences are clear.

### Operational realism — 5

- Frequency, aircraft capacity, load factor, transfer/transit share, season, events, route maturity, and conversion assumptions have credible bounds and relationships.
- Extreme extrapolation produces warnings rather than false precision.

### Deployment and maintainability — 4

- Startup, runtime, model/data versioning, error handling, update cadence, and handover are plausible for a prototype becoming an internal tool.

### Governance and limitations — 4

- Data licensing, aggregation, privacy, access, provenance, assumptions, and known limitations are addressed.
- Outputs are decision support rather than unjustified causal certainty.

## 4. Explanation and presentation — 20 points

### Live demonstration — 6

- A judge can see a complete scenario change and result within the available time.
- The demonstrated output is computed, not prerecorded or manually substituted.

### Visual and verbal clarity — 5

- The conversion chain, baseline comparison, uncertainty, sensitivity, and recommendation are understandable without technical narration.

### Evidence consistency — 4

- Numbers and definitions match across the app, repository, report, video, and deck.
- Important metrics include the population, period, mode, and units they describe.

### Honest communication — 3

- Observed, derived, assumed, overridden, and predicted quantities are visibly distinguished.
- Limitations are concrete and paired with mitigations where possible.

### Submission discipline — 2

- Required files, page/slide limits, language, video duration, credits, and prototype access follow the current rules.

## Credibility gates

Report these separately from the numerical score:

1. **Functional prototype:** scenario inputs materially change computed outputs.
2. **Decision-time-valid evidence:** central planning claims survive leakage review.
3. **Honest market bridge:** the origin/nationality mismatch is neither ignored nor falsely presented as observed linkage.
4. **Empirical uncertainty:** ranges have demonstrated coverage or are labeled experimental/uncalibrated.
5. **Reproducible evidence:** the principal results can be regenerated and agree across deliverables.
6. **Data compliance:** restricted competition data is not exposed or used outside its permitted context.

Rate each gate `pass`, `partial`, `fail`, or `not verified`. A failed gate should materially reduce confidence even when the weighted score is otherwise high.

## Scoring calibration

- **90–100:** exceptional and operationally credible; only minor risks remain.
- **80–89:** strong finalist quality; material weaknesses are bounded and honestly handled.
- **70–79:** promising prototype with one or more substantial evidence or usability gaps.
- **60–69:** conceptually sound but not yet sufficiently validated or operational.
- **Below 60:** central claims, prototype functionality, or challenge alignment are not demonstrated.

Do not convert this calibration into a prediction of the actual panel's decision.
