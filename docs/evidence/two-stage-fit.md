# Two-stage fit

Source: validation re-run at commit 6ec8831 on `VALIDATION_ORIGINS` (analysis, outside the repository). WAPE % of daily segment totals, mean over 7 folds. Difference: candidate − `twin_daily` from `compare()`, market-day grain, pp WAPE, 90% interval, folds with the same sign.

| Fit | Domestic WAPE | International WAPE | Domestic difference | International difference |
| --- | ---: | ---: | --- | --- |
| Joint backfit (`twin_daily`) | 4.18 | 4.59 | n/a | n/a |
| Calendar removed from guests, then the kernel | 9.56 | 12.99 | +5.36 [+3.95, +6.80], 7/7 | +19.53 [+17.47, +21.39], 7/7 |
| Calendar removed from guests and arrivals, then the kernel | 8.85 | 5.59 | +4.72 [+2.71, +6.42], 5/7 | +2.35 [+1.49, +3.36], 6/7 |
| Calendar removed from guests and arrivals, then a plain lagged regression | 8.53 | 5.51 | +4.40 [+2.49, +6.04], 5/7 | +2.04 [+1.24, +2.88], 7/7 |

| Finding |
| --- |
| Every two-stage variant is worse than the joint fit on both series, by 2.0 to 19.5 pp |
| Removing the calendar from guests alone is the worst variant on both series |
