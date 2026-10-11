# Noise

Source: `noise_distribution.py` (analysis, outside the repository).

| Property | Domestic | International |
| --- | --- | --- |
| Shape, events removed | About normal in log (JB p 0.08) | Normal in log (JB p 0.06) |
| Lag-1 ACF, per year | 0.72 to 0.82 | 0.89 to 0.92 |
| Spread by month | Aug 0.055 → Jan 0.091 | Sep 0.064 → May 0.121 |
| Centre (90-day mean) | Drifts ±7% | Drifts ±10% |
| Effective sample size | About 160 | About 50 |

Independent-error p-values and intervals are too narrow on this data.

Source: out-of-sample log errors e = log(actual) − log(predicted) of `twin_daily` on the 7 `VALIDATION_ORIGINS` folds, commit 6ec8831 (analysis, outside the repository). Normal-test p-values on random subsamples of 500.

| Property | Domestic | International, market-day | International total |
| --- | ---: | ---: | ---: |
| Days | 1,284 | 25,680 | 1,284 |
| Mean (positive: under-prediction) | +0.002 | +0.036 | +0.035 |
| Standard deviation | 0.059 | 0.151 | 0.042 |
| Skew | 0.54 | 0.08 | −0.60 |
| Excess kurtosis | 3.52 | 1.30 | 0.82 |
| Shapiro p | 5e-13 | 0.02 | 5e-9 |
| Share beyond 3 sd (Gaussian 0.27%) | 1.6% | 0.8% | 0.7% |
| ACF lag 1 | 0.59 | 0.77 | n/a |
| ACF lag 6 / 7 / 8 | 0.27 / 0.35 / 0.25 | 0.34 / 0.35 / 0.28 | n/a |
| ACF lag 14 | 0.20 | 0.19 | n/a |
| Standard deviation by month, highest | Dec 0.091, Jun 0.082 | May 0.171, Apr 0.167 | n/a |
| Standard deviation by month, lowest | Jul 0.027 | Feb 0.099 | n/a |

| Finding |
| --- |
| Out-of-sample errors are not Gaussian: heavy tails, positive lag-1 autocorrelation, a bump at lag 7 and spread that varies by month |
| International predictions are below actuals by 3.6% on average |
| `NoiseModel` carries AR(1) memory only ([intervals](../model/intervals.md)) |
