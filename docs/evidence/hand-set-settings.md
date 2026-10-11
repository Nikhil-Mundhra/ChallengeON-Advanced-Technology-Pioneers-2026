# Hand-set settings

Source: validation re-run of the shipped specs at commit 6ec8831, one [hand-set setting](../model/nowcast.md#fitting) changed at a time, on `VALIDATION_ORIGINS` (analysis, outside the repository). WAPE % of daily segment totals, mean over 7 folds. Difference: candidate − `twin_daily` from `compare()`, market-day grain, pp WAPE, 90% interval, folds with the same sign.

| Setting | Domestic WAPE | International WAPE | Domestic difference | International difference |
| --- | ---: | ---: | --- | --- |
| Shipped at 6ec8831: K = 21, H = 4, knots 365 days | 4.18 | 4.59 | n/a | n/a |
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

Source: validation re-run of `INTL_NOWCAST` with one `knot_days` value at a time, domestic at 365 days, on `VALIDATION_ORIGINS` at commit 6779272 (analysis, outside the repository; `twin validate` reproduces the 45 and 365 daily-total WAPE). International only. Market-day WAPE and daily-total WAPE: %, mean over 7 folds. Difference: candidate − 365 days from `compare()`, market-day grain, pp WAPE, 90% interval, folds with the same sign.

| Knot spacing (days) | Market-day WAPE | Daily-total WAPE | Difference | Folds |
| ---: | ---: | ---: | --- | :---: |
| 14 | 10.00 | 4.05 | −1.09 [−1.36, −0.84] | 6/7 |
| 21 | 9.61 | 3.96 | −1.47 [−1.76, −1.19] | 7/7 |
| 30 | 9.56 | 3.96 | −1.52 [−1.77, −1.26] | 7/7 |
| 45 (shipped) | 9.62 | 4.07 | −1.45 [−1.66, −1.23] | 7/7 |
| 60 | 9.77 | 4.14 | −1.30 [−1.47, −1.12] | not recorded |
| 90 | 10.06 | 4.28 | −1.01 [−1.14, −0.88] | not recorded |
| 120 | 10.31 | 4.38 | −0.76 [−0.85, −0.67] | not recorded |
| 182 | 10.58 | 4.48 | −0.49 [−0.56, −0.42] | 7/7 |
| 365 | 11.06 | 4.60 | n/a | n/a |

Same source, 45 against 365 days by forecast day (day 1 is the origin).

| Forecast days | 365 days | 45 days | Difference | Folds |
| --- | ---: | ---: | --- | :---: |
| 1 to 7 | 9.90 | 7.89 | −1.94 [−2.86, −1.21] | 7/7 |
| 8 to 30 | 10.53 | 8.77 | −1.66 [−2.54, −1.05] | 7/7 |
| 31 and later | 11.23 | 9.85 | −1.39 [−1.59, −1.20] | 7/7 |

Same source, base-stock roughness: median over fits of the largest |Δ log c| between adjacent knots.

| Knot spacing (days) | 14 | 21 | 30 | 45 | 60 | 182 | 365 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Median max \|Δ log c\| | 0.87 | 1.14 | 0.54 | 0.31 | 0.29 | 0.20 | 0.13 |

Same source, daily planning chain (`SEAT_CHAIN`, link 1 knots every 60 days), link 2 knots every 45 days against 365 days. International, 7 folds.

| Grain | 365 days | 45 days | Difference | Folds |
| --- | ---: | ---: | --- | :---: |
| Daily market-day WAPE | 21.05 | 20.67 | −0.37 [−0.56, −0.14] | 5/7 |
| Weekly market-week WAPE | 19.46 | 19.00 | −0.45 [−0.68, −0.19] | 7/7 |
| Level bias | −7.2% | −6.0% | n/a | n/a |

| Finding |
| --- |
| Every spacing from 14 to 182 days lowers international market-day WAPE against 365 days; 30 days is lowest; 21, 30 and 45 days are within 0.2 pp of it |
| The gain holds at every forecast horizon and is largest in the first week |
| Below 45 days the base stock roughens sharply (median max \|Δ log c\| 0.54 at 30 days, 1.14 at 21 days); 9 of the 14-day fits do not converge |
| Domestic predictions are bit-identical with and without the international setting |
