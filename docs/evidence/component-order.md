# Component order

Source: `analysis/hybrid_order_test.py` (outside the repository). Daily totals (domestic; international summed over nationalities) from the train workbooks. Folds: test 2024-02-01 to 2024-07-31 (train 2023-01-01 to 2024-01-31) and test 2025-02-01 to 2025-07-31 (train 2023-01-01 to 2025-01-31). Fixed hyperparameters: K = 21, H = 4, ridge α = 1. WAPE %, mean of the two folds.

| Model | DOM | INTL |
| --- | ---: | ---: |
| Seasonal naive (same weekday, 364 days earlier) | 16.3 | 18.6 |
| Calendar only (log ridge: trend, Fourier, weekday, events) | 11.3 | 11.2 |
| Arrivals kernel only | 8.1 | 6.1 |
| Sequential kernel → calendar | 6.1 | 4.8 |
| Sequential calendar → kernel | 9.8 | 13.3 |
| Joint backfit (Guests = flow × calendar multiplier) | 4.9 | 4.7 |
| Multi-resolution greedy (level → year → week → days) | 6.9 | 5.7 |
| Joint + GBM on log residual | 5.0 | 4.7 |

| Finding |
| --- |
| Greedy order changes the answer by up to 8.6 points |
| The joint backfit converges to the same WAPE from both starting orders (equal to 6 decimal places) |
| GBM on the joint residual: worse on both 2024 folds, better on both 2025 folds |
| Joint kernel Σw: domestic 1.6 to 2.2, international 3.3 to 3.5 across folds (c unconstrained); with c ≥ 0 a probe got international Σw = 2.34 with c ≈ 6.9k ([vertical-slice probe](vertical-slice-probe.md)) |
| Event windows in the script are hard-coded 2023 to 2025 date lists |
