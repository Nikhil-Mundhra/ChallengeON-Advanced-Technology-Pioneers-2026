# Hand-set settings

Source: validation re-run of the shipped specs at commit 6ec8831, one [hand-set setting](../model/nowcast.md#fitting) changed at a time, on `VALIDATION_ORIGINS` (analysis, outside the repository). WAPE % of daily segment totals, mean over 7 folds. Difference: candidate − `twin_daily` from `compare()`, market-day grain, pp WAPE, 90% interval, folds with the same sign.

| Setting | Domestic WAPE | International WAPE | Domestic difference | International difference |
| --- | ---: | ---: | --- | --- |
| Shipped: K = 21, H = 4, knots 365 days | 4.18 | 4.59 | n/a | n/a |
| K = 10 | 4.18 | 4.62 | −0.001 [−0.003, +0.002], 4/7 | −0.003 [−0.019, +0.016], 3/7 |
| H = 2 | 4.50 | 4.60 | +0.32 [+0.02, +0.63], 7/7 | +0.10 [−0.21, +0.37], 6/7 |
| H = 6 | 4.12 | 4.58 | −0.06 [−0.15, +0.02], 5/7 | −0.01 [−0.17, +0.14], 4/7 |
| Knots 182 days | 4.20 | 4.48 | +0.02 [−0.10, +0.12], 3/7 | −0.49 [−0.56, −0.42], 7/7 |
| Knots 730 days | 4.27 | 4.74 | +0.09 [−0.00, +0.22], 6/7 | +0.22 [+0.20, +0.25], 7/7 |

| Finding |
| --- |
| No fitted kernel has weight above 0.01 beyond lag 6; K = 10 and K = 21 give the same WAPE |
| H = 2 is worse for domestic; H = 6 changes neither series |
| 182-day knots lower international WAPE in every fold and leave domestic unchanged; 730-day knots are worse for international |
| The two smoothing settings and `min_smoothed_days` were not varied |
