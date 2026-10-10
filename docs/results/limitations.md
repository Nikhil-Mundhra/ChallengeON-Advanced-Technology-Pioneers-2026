# Limitations

| Limitation | Consequence | Current handling |
| --- | --- | --- |
| Departure country is a proxy for nationality | Misallocated market impact | Calibrated effective multiplier; planner-adjustable |
| Planning-model interval coverage 65.2% vs 80% nominal ([planning holdout](planning-holdout.md)) | Simulator P10 to P90 ranges are too narrow on the 2025 holdout | Coverage reported with every briefing; the simulator keeps the conformal margins |
| Domestic prior over-forecast 2025 by 13.05% ([planning holdout](planning-holdout.md)); 2025 domestic guests were below the 2023 to 2024 seasonal level | Domestic planning baseline too high for 2025 | Reported; domestic modelled separately |
| Stay factor L is a stock-to-flow ratio | `--delta-los` shifts a guests-per-arrival ratio, not a measured stay | The nowcast kernel is not used by the simulator |
| Nowcast kernel sum Σw is a fitting quantity; it is below guests ÷ new arrivals where the base stock carries part of the stock | Σw is not a length of stay | Not reported in any output |
| Domestic nowcast interval coverage falls with horizon (89% at h ≤ 13 days, 74% at h > 120; 8 exploratory origins) | Late test-period domestic bounds are too narrow | Reported; no horizon-specific correction |
| Pooled-market nationalities come from a shared-shape model | Guest-weighted WAPE 13.83% on the 30 nationalities ([nowcast validation](nowcast-validation.md#nationalities)) | Intervals from that model's back-test errors per nationality |
| Structural-only accuracy does not beat the seasonal prior (23.14% vs 23.00%) | The structural chain serves scenario attribution more than point forecasting | Hybrid reported alongside |
| Cold-start markets use archetype defaults | Weak estimates for new origins | Flagged `is_cold_start` |
| No room inventory | No occupancy | Output is guests |
| No bookings, room rates, marketing spend, airfares, visa or macroeconomic data | Demand drivers beyond arrivals and the calendar are not modelled | Scope limit |
| Planning model validated on a single forward split | One holdout period; no Autumn_Shoulder weeks | Season breakdown reported |
| Weekly projection (web app) has no growth term; holiday flags end with the week of 2027-02-08 | Projected years repeat the seasonal profile; later holidays are missing | Growth is a user assumption, applied to projected weeks only |
| Analysis figures in [evidence](../evidence/index.md) come from scripts outside the repository | Not reproducible here | Marked per file |
| Observational data | No causal identification | Results described as planning estimates |
