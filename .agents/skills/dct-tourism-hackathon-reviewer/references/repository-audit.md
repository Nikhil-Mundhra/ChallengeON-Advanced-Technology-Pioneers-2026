# Repository and Model Audit

Use this reference when source code, data products, models, tests, or the live application are in scope. Preserve existing user changes and do not mutate the repository unless the user asks for fixes.

## Start with repository instructions

Read applicable `AGENTS.md`, `CLAUDE.md`, or equivalent instructions before acting. Inspect repository status so user changes are not mistaken for generated or committed state.

Prefer existing project commands. Do not install dependencies or rebuild expensive artifacts merely to satisfy a checklist when static inspection answers the question. If execution is feasible, record the exact command and distinguish reproduced results from inspected claims.

## Trace one vertical slice

For at least one representative market-season scenario, trace:

```text
raw source
→ parsing and quality rules
→ curated table
→ modelling panel
→ train/calibration split
→ saved parameters/model
→ scenario calculation
→ API response
→ interface output
```

Check units, grain, key definitions, fallbacks, clipping, and labels at every transition. Include a cold-start or `Other` market when it is central to the claim.

## Data-contract checks

- Date ranges, timezone/date parsing, daily versus monthly grain, and complete-period rules.
- Unique keys before and after aggregation or joining.
- Missing, absent, suppressed, imputed, and genuine-zero values remain distinguishable.
- Raw quality anomalies are retained or auditable when modelling versions are clipped or corrected.
- `Other` aggregation is consistent across flight and guest datasets.
- Train, validation, calibration, and test membership is explicit and reproducible.
- No target-bearing rows or future-derived aggregates enter planning features, priors, scaling, hyperparameter selection, or conformal calibration.

## Origin-to-nationality checks

Treat a same-label join between flight country and guest nationality as an assumption, not proof of identity.

Inspect whether the implementation uses:

- an explicit origin × nationality × season allocation matrix;
- a constrained low-rank, hierarchical, regional, or diagonal-prior approximation;
- an effective response multiplier that absorbs several unidentified stages;
- planner overrides and uncertainty around weak mappings.

Verify that code, UI, and presentation describe the same method. If an effective multiplier absorbs origin allocation, visitor purpose, hotel capture, and other effects, do not allow the presentation to claim each component was separately measured.

## Decision-time leakage review

For every input feature or prior, ask: "Would this exact value be known on the date the planner makes the decision?"

Common leakage paths include:

- future realized passengers, load factor, P2P, transfer/transit, or hotel arrivals;
- lags computed before the split and accidentally reaching across it;
- global normalization, imputation, feature selection, or hyperparameter tuning using holdout data;
- random cross-validation for seasonal time series;
- conformal scores computed on the evaluation holdout and then evaluated on the same observations;
- competition test fields used to support a planning-mode claim.

Allow realized variables for explicitly labeled stage diagnostics or competition forecast mode. Do not conflate those results with planning performance.

## Statistical validation

Inspect:

- chronological split construction and complete-period isolation;
- multiple rolling-origin folds where data volume permits;
- overall, international, domestic, market, season, volume-tier, and cold-start results;
- WMAPE denominator and zero/low-volume handling;
- signed bias, MAE/RMSE where useful, interval coverage, and interval width;
- baseline definitions and whether every model receives comparable information;
- residual-model ablations and monotonic scenario behavior;
- sensitivity to cutoffs, priors, aggregation grain, and outlier handling.

Large domestic volumes can make a combined metric look strong while hiding weaker aviation performance. Require separate international planning results.

## Uncertainty review

- Use a temporally separate calibration set or a valid rolling/cross-conformal design.
- Match the interval to the quantity being claimed: future level, incremental scenario effect, or parameter uncertainty.
- Test empirical coverage out of sample and report interval width.
- Check correlation between uncertain inputs; independent draws may understate or distort risk.
- Verify bounded distributions remain within physical limits.
- Confirm residual resampling preserves relevant temporal or market dependence.
- Treat nominal coverage materially above demonstrated coverage as undercalibration, not a successful calibrated range.

## Scenario invariants and adversarial cases

Test or inspect:

- no-change scenario reproduces the baseline;
- positive capacity has coherent, explainable effects;
- route closure and negative levers do not create demand;
- passenger components reconcile and shares remain in `[0, 1]`;
- guest outputs remain non-negative;
- waterfall components sum to the displayed total change;
- domestic demand ignores international flight levers unless a separately justified relationship exists;
- frequency and gauge are not double-counted with direct seat changes;
- extreme scenarios produce warnings or wider uncertainty;
- unsupported markets use a documented fallback and are visibly labeled;
- the residual layer does not reverse or double-count structural flight effects without explanation.

## Software and product checks

- Clean startup from documented commands.
- Pinned or bounded dependencies appropriate to reproducibility needs.
- Deterministic seeds and artifact metadata where randomness is used.
- Model, schema, and data version compatibility checks.
- Actionable errors for missing artifacts or invalid inputs.
- API validation for units, ranges, enum values, and unknown markets.
- UI accessibility, responsive behavior, loading/error states, and terminology understandable to planners.
- No raw restricted dataset is exposed through static files, logs, downloadable endpoints, or committed public artifacts.

## Minimum useful test coverage

Look for tests of:

- data contracts and unique grains;
- chronological split and leakage barriers;
- conversion identities and physical bounds;
- domestic/international separation;
- cold-start behavior and wider uncertainty;
- empirical interval coverage procedure;
- metric regeneration from fixtures or artifacts;
- API request/response behavior;
- at least one end-to-end scenario;
- clean rebuild or deterministic artifact production when feasible.

Passing unit tests demonstrate only what they assert. Do not infer statistical validity, UI operability, or reproducibility from a small invariant-only suite.

## Consistency sweep

Search for every headline metric and claim across source, JSON, reports, README files, slides, figures, and UI defaults. Treat differences in values, date windows, populations, modes, or units as a credibility finding until reconciled.

The final audit should make clear which items were executed, inspected, claimed, or not verified.
