# Flow linearity

Source: full-window fits and a validation re-run of the shipped specs at commit 6ec8831 (analysis, outside the repository).

Partial residuals: log(guests ÷ calendar multiplier) regressed on log flow of the fitted kernel, full training window.

| Series | Slope | Quadratic coefficient |
| --- | ---: | ---: |
| `UNITED KINGDOM` | 1.005 | 0.03 |
| `INDIA` | 1.023 | 0.11 |
| `DOMESTIC` | 1.027 | 0.21 |

Learned transforms of flow in place of the identity, on `VALIDATION_ORIGINS`. WAPE % of daily segment totals, mean over 7 folds. Difference: candidate − `twin_daily` from `compare()`, market-day grain, pp WAPE, 90% interval, folds with the same sign.

| Transform | Full-window fit | Domestic WAPE | International WAPE | Domestic difference | International difference |
| --- | --- | ---: | ---: | --- | --- |
| Identity (shipped) | n/a | 4.18 | 4.59 | n/a | n/a |
| Power: flow^β with a learned scale | β 1.008 (UK), 1.032 (India), 1.048 (domestic) | 4.12 | 4.24 | −0.06 [−0.12, +0.01], 6/7 | −0.32 [−0.38, −0.25], 7/7 |
| Monotone spline on log flow | n/a | 4.37 | 3.89 | +0.20 [−0.07, +0.48], 6/7 | −0.58 [−0.83, −0.33], 7/7 |

| Finding |
| --- |
| With calendar effects removed, guests are proportional to flow: slopes 1.005 to 1.027 |
| Both learned curves lower international WAPE in every fold; both domestic intervals include 0 |
