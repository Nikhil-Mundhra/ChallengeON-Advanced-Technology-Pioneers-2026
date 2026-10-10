# Interactions and functional form

Source: `analysis/interactions_test.py` (outside the repository). Folds and hyperparameters as [component order](component-order.md). WAPE %, mean of the two folds.

| Model | DOM | INTL |
| --- | ---: | ---: |
| Additive, raw scale: Guests = flow + calendar | 5.11 | 4.46 |
| Multiplicative: Guests = flow × calendar multiplier | 4.97 | 4.68 |
| + day of week × season (May to Sep) | 4.92 | 4.69 |
| + separate winter and summer kernels | 4.98 | 4.73 |
| + power: Guests = flow^α × calendar multiplier (kernel fixed) | 5.22 | 4.67 |

| Finding |
| --- |
| Summer shift of the Friday/Saturday effect: −0.1% to −2.6% |
| Winter vs summer kernel Σw nearly equal (largest gap international 2025: 2.96 vs 3.28) |
| α: domestic 0.91 to 0.93, international 0.99 to 1.02 (naive SE 0.01 to 0.03) |
| No interaction lowers WAPE by ≥ 0.3 points on both series |
| Fitting α and the kernel together diverged |
| The multiplicative fit without a calendar centred on the training window collapses the kernel toward zero |
