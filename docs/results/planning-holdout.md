# Planning holdout

Design: [back-test design](../model/planning.md#back-test-design).

## By setting

Source: `lake/curated/evaluation_results.json` (`diagnostics`; `twin evaluate`).

| Setting | WMAPE | Bias | MAE | RMSE | Inputs |
| :--- | :---: | :---: | :---: | :---: | :--- |
| International planning | 27.31% | +1.74% | 2,447.2 | 3,887.9 | Scheduled seats + calibrated seasonal priors |
| International realized chain | 24.36% | −5.72% | 2,183.5 | 3,276.2 | Realized P2P × calibrated multiplier × stay factor |
| Domestic forecast | 16.04% | +13.05% | 17,485.2 | 21,078.9 | Calibrated seasonal prior; no holdout arrivals |
| Combined planning | 23.00% | +6.06% | 3,173.7 | 5,987.5 | International + domestic |
| Combined realized chain | 21.18% | +1.45% | 2,922.7 | 5,628.5 | International + domestic |

## Benchmark

Source: `lake/curated/evaluation_results.json` (`benchmark`, `benchmark_leaders`). All markets.

| Model | WMAPE | Bias | MAE | RMSE |
| :--- | :---: | :---: | :---: | :---: |
| 1. Historical seasonal prior (market-season mean) | 23.00% | −6.60% | 3,172.8 | 6,156.5 |
| 2. Calendar only (per-market ridge, no aviation) | 22.00% | −8.50% | 3,035.6 | 5,839.0 |
| 3. Structural only (planning mode) | 23.00% | +6.06% | 3,173.7 | 5,987.5 |
| 4. Hybrid (structural + residual) | 20.29% | +5.91% | 2,799.5 | 5,251.9 |

The hybrid leads on all four metrics (bias by absolute value), 1.71 pp ahead of the calendar-only model.

## By season

Source: `lake/curated/evaluation_results.json` (`season_breakdown`). Combined planning mode.

| Season | Market-weeks | WMAPE | Bias |
| :--- | :---: | :---: | :---: |
| Winter_Peak | 292 | 27.68% | +9.89% |
| Spring_Shoulder | 168 | 21.22% | +4.87% |
| Summer_Trough | 161 | 16.33% | +0.30% |

Autumn_Shoulder is not in the holdout window. Per-market results: `market_breakdown`.

## Coverage and events

| Measurement | Source | Result |
| --- | --- | --- |
| Holdout market-weeks inside structural prediction × (1 ± conformal margin), nominal 80% | `evaluation_results.json` (`demonstrated_coverage_pct`) | 65.7% |
| Hybrid with the calendar residual alone (no event shares) | earlier `twin evaluate` run | 21.74% WMAPE, bias +5.36% |
| Event shares in the residual, weekly WAPE on validation origins | `compare` | −0.7 pp [−1.55, −0.16], 7/7 origins |
| Weekly back-test reproduced in the web engine | `web/src/engine/parity.test.ts` | Same WMAPE as the benchmark hybrid |

Nowcast and planning numbers are not comparable: the nowcast uses the predicted period's new arrivals, the planning model does not.
