# Nowcast validation

Protocol: [validation protocol](../model/nowcast.md#validation-protocol-modelsbacktestpy).

## Validation

Source: `output/validation_summary.json` (`twin validate`; `segment_wape`). The file is not committed; values from the last published run. WAPE % of daily segment totals, mean over 7 folds.

| Spec | Domestic | International |
| :--- | :---: | :---: |
| `naive_364` | 16.91% | 22.97% |
| `arrivals_ratio` | 17.93% | 8.86% |
| `time_only` (level + season + weekday + events, no arrivals) | 10.10% | 10.68% |
| `flow_only` (arrivals kernel alone) | 9.55% | 5.44% |
| `flow_time` (kernel + calendar, no events) | 4.18% | 4.42% |
| `twin_daily` (shipped; domestic has no holiday block) | 4.18% | 4.59% |

Source: `output/validation_summary.json` (`compare`). Market-day grain, `twin_daily` − `naive_364`: −12.71 pp [−15.45, −10.43] domestic, −18.42 [−19.98, −16.87] international, 7/7 folds. On segment totals events partly cancel across markets; at market grain removing them costs international markets 0.37 pp.

## Shipped choices

Source: `compare` runs on `VALIDATION_ORIGINS` (`models/backtest.compare`). Market-day grain, candidate − shipped, pp WAPE; n.s. = interval includes 0.

| Shipped | Candidate | Difference |
| --- | --- | --- |
| Domestic slope | No slope | +2.85 [+1.97, +3.56] |
| Domestic plain weekday | Weekday × season | +0.05, n.s. |
| Knot base stock | Base tied to 90-day arrivals | domestic −0.77, n.s.; international +5.39 |
| International events | No events | +0.37 [+0.11, +0.67], 7/7 folds |
| No residual GBM | `ResidualGBM` | −0.14, n.s. |
| No international slope | Slope | −0.27 [−0.43, −0.10], 4/7 folds |
| Domestic trains on all history | Training from 2022-07-01 | +1.19 [+0.20, +2.04], 7/7 folds (domestic 5.37 vs 4.18) |

## Nationalities

Source: `output/validation_summary.json` (`nationalities`) and `compare` on `VALIDATION_ORIGINS` and `FROZEN_TEST`. International nationality WAPE.

| Comparison | Validation | Frozen test |
| --- | --- | --- |
| `POOLED_NATIONALITIES` vs market model + arrival-share split, all international nationalities | 12.24% vs 12.79%, −0.55 pp [−0.79, −0.32], 7/7 folds | 11.16% vs 11.38%, −0.22 pp [−0.45, +0.02] |
| Same, pooled-market nationalities only | −2.18 pp [−3.13, −1.27] | −0.89 pp [−1.89, +0.06] |
| `Recency(365)` vs unweighted, 30 pooled-market nationalities (guest-weighted WAPE) | 13.83% vs 14.23%, −0.40 pp [−0.64, −0.19], 7/7 folds; mean absolute bias per nationality 6.15% vs 7.32% | n/a |
| All 45 nationalities pooled | +3.6 pp | n/a |
| Rejected on validation | Half-life 180 days (5/7 folds); ridge 1, 10, 1,000; data-driven families; `morocco_winter_block` (+0.15 pp) | n/a |

Source: arrival-share split on the last training year (`nowcast/disaggregation.py`): nationality WMAPE 14.0% vs 24.0% for shares of same-day arrivals.

## Exploratory

Origins overlap the frozen test; not decision evidence.

Source: `RollingOrigin` back-test, 8 monthly origins 2024-07-01..2025-02-01, 6-month horizon, mean fold WMAPE over each segment's market-days, domestic / international.

| Spec | Domestic / international |
| --- | --- |
| `naive_364` | 20.4 / 26.6 |
| `arrivals_ratio` | 15.9 / 19.2 |
| `twin_daily` | 6.2 / 9.4 |
| `twin_daily_gbm` | 6.2 / 9.1 |
| `twin_daily_base90` | 11.23 / 13.39 (vs 6.49 / 9.42 in the same run) |

### Intervals

Source: `twin predict` interval back-test (8 origins); each fold's bounds from a noise model fitted on other folds only. Coverage of the 80% interval, `twin_daily`.

| Folds used to fit | All | Domestic | International |
| --- | :---: | :---: | :---: |
| All other origins | 81.4% | 81.5% | 81.4% |
| Origins more than 3 months away | 79.2% | 75.9% | 79.4% |

International coverage is 79 to 83% at every horizon; domestic falls from 89% (h ≤ 13 days) to 74% (h > 120 days). The `TOTAL` series' 80% interval covers 80.9% of back-test days (leave one origin out) and 79.4% (±3 months excluded); adding the 21 markets' bounds covers 98.7%.

### Direction

Source: `market_outputs.json` (`direction_backtest`, `twin predict`). Week-to-week, the 8 interval back-test origins, 1,154 distinct market-weeks, each from its earliest origin; the model sees observed new arrivals.

| Predictor | Accuracy |
| --- | :---: |
| Model | 87.2% |
| Direction of new arrivals | 83.4% |
| Same direction as last year | 63.1% |
| Market's majority training direction | 53.6% |

Stated `direction_prob` vs share right: 0.55 → 63%, 0.65 → 78%, 0.75 → 82%, 0.85 → 91%, 0.98 → 99%. Weekly 80% bands cover 77.6% of back-test weeks. Both are in-sample for the error model.

### Other measurements

| Measurement | Source | Origins | Result |
| --- | --- | --- | --- |
| Same-day guests, mean Poisson deviance, `*` as 0 | `scripts/same_day_backtest.py` | 8, 2024-07..2025-02 | Domestic 11.77 vs 15.31 for the market mean; international 4.87 vs 5.61 |
| Same-day dispersion and coverage | same-day back-test | validation | Pearson dispersion 8.0 domestic, 10.3 international; Poisson 80% intervals cover 63.3% |
| Smeared (mean) vs median predictions | back-test | 8 | Daily WMAPE 6.22 / 9.36 vs 6.23 / 9.42; 14-day range-sum absolute error 5.14 / 8.35 vs 5.16 / 8.35; bias +0.54% / −1.31% vs +0.33% / −1.80% |
| Block ablation, WAPE of daily segment totals | `output/nowcast_block_ablation.json` (`twin ablate-blocks`) | 13, 2024-02..2025-02 | Seasonal naive 18.80 / 19.28; time only 9.23 / 9.62; flow only 8.92 / 5.06; flow + time 5.97 / 4.19; `twin_daily` 5.97 / 4.12 (domestic slope extrapolated linearly; held flat 5.46) |
| Domestic slope beyond training, daily WAPE / bias | back-test | 13 | Linear 5.97% / −2.61%; damped over 180 days 5.76% / −2.01%; over 90 days 5.66% / −1.63%; flat (default) 5.46% / −0.36%; no slope 8.72% / +7.27% |
| Chinese New Year, scope CHINA, CHINA daily WAPE without / with | back-test | folds 2024-08..2025-01 | 16.47% / 16.78% |
| Time-varying kernel | back-test | 8 | Per-regime curves 8.72% overall WMAPE vs 8.39% for one shared curve × calendar (raw-scale kernel fit; the shipped fit scores 8.31%) |
| Fit diagnostics | `BacktestResult.diagnostics` | 8; 13 | All 168 fits (21 markets × 8 origins) converge; domestic daily WAPE 5.97% at caps 20, 50, 200 and 1,000 passes |
| Analysis baselines | `model_baselines.py` (outside the repository) | single holdout 2025-02..2025-07 | Same-day GBM with Poisson loss 19.4% vs 23.8% naive; direction by logistic + spline 74% accuracy, Brier 0.18 vs 43% majority class |
