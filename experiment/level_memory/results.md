# Level memory: results

VALIDATION_ORIGINS (7 folds) unless marked gap0. Aggregate metrics only. Written by `report.py` from the runs cached by `run.py`.
WAPE: market-day, mean over folds. delta: compare() against the shipped model, pp, negative is better, 90% moving-block CI. R2 vs time: 1 - SSE / SSE of the time-only control (INTL_TIME / DOMESTIC_TIME) on the same rows. Horizon h: days since the origin (day 1 = origin). Bias: sum pred / sum actual - 1.

## Experiment 1: carry-forward, daily nowcast

### protocol

#### Domestic

Shipped 4.18. Best setting `cf_k14_hb_mkt_echo`, simplest within 0.2 pp `cf_k7_in_pool`. WAPE is market-day, mean over folds.

| model | WAPE | delta pp [90% CI] | bias % | MAE | RMSE | R2 vs time | WAPE h1-7 | WAPE h8-30 | WAPE h31+ | folds better | gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nowcast | 4.18 |  | -0.62 | 695.20 | 1102.18 | 0.76 | 3.82 | 4.94 | 4.08 |  |  |
| cf_k14_hb_mkt_echo | 4.18 | -0.00 [-0.00, -0.00] | -0.62 | 695.13 | 1102.20 | 0.76 | 3.81 | 4.94 | 4.08 | 5/7 | fail |
| cf_k7_in_pool | 4.18 | -0.00 [-0.00, +0.00] | -0.62 | 695.20 | 1102.17 | 0.76 | 3.82 | 4.94 | 4.08 | 3/7 | fail |
| cf_k28_in_pool | 4.18 | +0.00 [-0.00, +0.00] | -0.62 | 695.20 | 1102.18 | 0.76 | 3.82 | 4.94 | 4.08 | 2/7 | fail |
| cf_k28_hb_one | 5.88 | +1.71 [+1.31, +2.01] | 1.50 | 979.71 | 1351.73 | 0.63 | 6.08 | 6.03 | 5.85 | 1/7 | fail |
| cf_k7_in_mkt | 4.18 | -0.00 [-0.00, +0.00] | -0.62 | 695.20 | 1102.17 | 0.76 | 3.82 | 4.94 | 4.08 | 3/7 | fail |
| time_only | 10.09 | +5.88 [+4.23, +7.72] | 5.99 | 1673.73 | 2233.88 | 0.00 | 7.79 | 7.69 | 10.53 | 0/7 | fail |

Grid, best 8 and worst 3:

| setting | WAPE |
| --- | --- |
| cf_k14_hb_pool_echo | 4.18 |
| cf_k14_hb_mkt_echo | 4.18 |
| cf_k14_in_pool_echo | 4.18 |
| cf_k14_in_mkt_echo | 4.18 |
| cf_k28_hb_mkt_echo | 4.18 |
| cf_k28_hb_pool_echo | 4.18 |
| cf_k28_in_pool_echo | 4.18 |
| cf_k28_in_mkt_echo | 4.18 |
| cf_k28_hb_one | 5.88 |
| cf_k14_hb_one_echo | 6.06 |
| cf_k14_hb_one | 6.06 |

Level bias % by fold:

| model | origin_2024-02-01 | origin_2024-03-01 | origin_2024-04-01 | origin_2024-05-01 | origin_2024-06-01 | origin_2024-07-01 | origin_2024-08-01 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| nowcast | -0.70 | -1.74 | -2.14 | -0.89 | 0.53 | -0.23 | 0.94 |
| cf_k14_hb_mkt_echo | -0.70 | -1.74 | -2.14 | -0.89 | 0.53 | -0.23 | 0.94 |
| cf_k7_in_pool | -0.70 | -1.74 | -2.14 | -0.89 | 0.53 | -0.23 | 0.94 |
| cf_k28_in_pool | -0.70 | -1.74 | -2.14 | -0.89 | 0.53 | -0.23 | 0.94 |
| cf_k28_hb_one | 4.68 | -6.11 | -1.75 | 1.73 | 9.89 | -0.58 | 2.92 |
| cf_k7_in_mkt | -0.70 | -1.74 | -2.14 | -0.89 | 0.53 | -0.23 | 0.94 |
| time_only | 1.08 | 2.91 | -1.34 | 18.01 | 2.66 | 5.35 | 13.72 |

#### International

Shipped 9.62. Best setting `cf_k28_in_one_echo`, simplest within 0.2 pp `cf_k28_in_one`. WAPE is market-day, mean over folds.

| model | WAPE | delta pp [90% CI] | bias % | MAE | RMSE | R2 vs time | WAPE h1-7 | WAPE h8-30 | WAPE h31+ | folds better | gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nowcast | 9.62 |  | -2.25 | 109.70 | 169.18 | 0.93 | 7.91 | 8.71 | 9.78 |  |  |
| cf_k28_in_one_echo | 9.54 | -0.08 [-0.25, +0.10] | -1.54 | 108.74 | 166.89 | 0.93 | 8.04 | 8.84 | 9.65 | 4/7 | fail |
| cf_k28_in_one | 9.54 | -0.08 [-0.25, +0.10] | -1.54 | 108.74 | 166.89 | 0.93 | 8.04 | 8.84 | 9.65 | 4/7 | fail |
| cf_k28_in_pool | 9.62 | -0.00 [-0.00, +0.00] | -2.25 | 109.70 | 169.18 | 0.93 | 7.91 | 8.71 | 9.78 | 4/7 | fail |
| cf_k28_hb_one | 10.79 | +1.17 [+0.78, +1.59] | -0.28 | 123.12 | 186.73 | 0.91 | 9.40 | 10.35 | 10.87 | 1/7 | fail |
| cf_k7_in_mkt | 9.62 | -0.00 [-0.00, +0.00] | -2.25 | 109.70 | 169.18 | 0.93 | 7.91 | 8.71 | 9.78 | 4/7 | fail |
| time_only | 29.74 | +20.04 [+18.64, +21.44] | -0.84 | 339.32 | 626.92 | 0.00 | 23.14 | 26.58 | 30.36 | 0/7 | fail |

Grid, best 8 and worst 3:

| setting | WAPE |
| --- | --- |
| cf_k28_in_one_echo | 9.54 |
| cf_k28_in_one | 9.54 |
| cf_k7_hb_hb_echo | 9.62 |
| cf_k7_hb_hb | 9.62 |
| cf_k14_hb_hb | 9.62 |
| cf_k14_hb_hb_echo | 9.62 |
| cf_k28_hb_hb_echo | 9.62 |
| cf_k28_hb_hb | 9.62 |
| cf_k14_hb_one | 11.28 |
| cf_k7_hb_one_echo | 11.84 |
| cf_k7_hb_one | 11.84 |

Level bias % by fold:

| model | origin_2024-02-01 | origin_2024-03-01 | origin_2024-04-01 | origin_2024-05-01 | origin_2024-06-01 | origin_2024-07-01 | origin_2024-08-01 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| nowcast | -1.55 | -1.61 | -4.09 | -4.58 | -2.65 | -1.70 | -0.05 |
| cf_k28_in_one_echo | -0.65 | 0.01 | -5.38 | -4.80 | -0.52 | -1.60 | 1.56 |
| cf_k28_in_one | -0.65 | 0.01 | -5.38 | -4.80 | -0.52 | -1.60 | 1.56 |
| cf_k28_in_pool | -1.55 | -1.61 | -4.09 | -4.58 | -2.65 | -1.70 | -0.05 |
| cf_k28_hb_one | 1.10 | 2.28 | -7.28 | -5.12 | 3.64 | -0.98 | 3.60 |
| cf_k7_in_mkt | -1.55 | -1.60 | -4.09 | -4.58 | -2.65 | -1.70 | -0.05 |
| time_only | 17.30 | 0.34 | -14.11 | -3.90 | -8.05 | -0.42 | 2.13 |

Memory estimates, mean over folds:

| series | rho pool (in-sample) | rho market median | rho held back | rho weekly | excess lag-7 | mean |e0| k28 in | corr(e0 in, test e days 1-30) | mean |e0| k28 hb | corr(e0 hb, test e days 1-30) | mean |e| test days 1-30 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| domestic | 0.743 | 0.743 | 0.635 | 0.613 | 0.330 | 0.024 | -0.172 | 0.034 | -0.166 | 0.028 |
| international | 0.690 | 0.729 | 0.817 | 0.241 | 0.064 | 0.026 | -0.022 | 0.067 | -0.023 | 0.072 |

### gap0 (exploratory: training ends the day before the origin)

#### Domestic

Shipped 4.18. Best setting `cf_k7_in_hb_echo`, simplest within 0.2 pp `cf_k7_in_pool`. WAPE is market-day, mean over folds.

| model | WAPE | delta pp [90% CI] | bias % | MAE | RMSE | R2 vs time | WAPE h1-7 | WAPE h8-30 | WAPE h31+ | folds better | gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nowcast | 4.18 |  | -0.98 | 696.07 | 1108.68 | 0.67 | 3.37 | 4.92 | 4.11 |  |  |
| cf_k7_in_hb_echo | 4.11 | -0.07 [-0.20, +0.02] | -0.87 | 684.11 | 1089.07 | 0.68 | 2.37 | 4.70 | 4.10 | 5/7 | fail |
| cf_k7_in_pool | 4.15 | -0.04 [-0.07, -0.00] | -0.93 | 690.18 | 1103.67 | 0.67 | 2.56 | 4.89 | 4.11 | 4/7 | fail |
| cf_k28_in_pool | 4.16 | -0.02 [-0.04, +0.00] | -0.96 | 693.07 | 1106.31 | 0.67 | 2.93 | 4.91 | 4.11 | 5/7 | fail |
| cf_k28_hb_one | 5.79 | +1.62 [+1.31, +1.86] | 0.30 | 965.57 | 1371.73 | 0.49 | 3.41 | 6.86 | 5.75 | 1/7 | fail |
| cf_k7_in_mkt | 4.15 | -0.04 [-0.07, -0.00] | -0.93 | 690.18 | 1103.67 | 0.67 | 2.56 | 4.89 | 4.11 | 4/7 | fail |
| time_only | 8.52 | +4.31 [+2.61, +6.16] | 4.42 | 1412.73 | 1923.81 | 0.00 | 6.18 | 6.67 | 8.88 | 0/7 | fail |

Grid, best 8 and worst 3:

| setting | WAPE |
| --- | --- |
| cf_k7_in_hb_echo | 4.11 |
| cf_k7_in_hb | 4.12 |
| cf_k14_in_hb_echo | 4.13 |
| cf_k14_in_hb | 4.13 |
| cf_k7_hb_pool_echo | 4.14 |
| cf_k7_hb_mkt_echo | 4.14 |
| cf_k7_hb_mkt | 4.14 |
| cf_k7_hb_pool | 4.14 |
| cf_k28_hb_one | 5.79 |
| cf_k7_hb_one_echo | 6.28 |
| cf_k7_hb_one | 6.29 |

Level bias % by fold:

| model | origin_2024-02-01 | origin_2024-03-01 | origin_2024-04-01 | origin_2024-05-01 | origin_2024-06-01 | origin_2024-07-01 | origin_2024-08-01 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| nowcast | -1.84 | -1.92 | -2.70 | -0.35 | 0.06 | -0.78 | 0.81 |
| cf_k7_in_hb_echo | -2.57 | -1.89 | -1.92 | 0.31 | 0.06 | -0.77 | 0.82 |
| cf_k7_in_pool | -1.90 | -1.86 | -2.61 | -0.20 | 0.05 | -0.74 | 0.84 |
| cf_k28_in_pool | -1.89 | -1.90 | -2.71 | -0.24 | 0.08 | -0.77 | 0.84 |
| cf_k28_hb_one | -6.35 | -0.74 | -4.21 | 10.63 | 1.05 | -0.91 | 2.76 |
| cf_k7_in_mkt | -1.90 | -1.86 | -2.61 | -0.20 | 0.05 | -0.74 | 0.84 |
| time_only | -1.94 | 3.51 | 3.94 | 5.11 | 3.63 | 6.91 | 10.07 |

#### International

Shipped 9.28. Best setting `cf_k7_in_hb`, simplest within 0.2 pp `cf_k7_in_pool`. WAPE is market-day, mean over folds.

| model | WAPE | delta pp [90% CI] | bias % | MAE | RMSE | R2 vs time | WAPE h1-7 | WAPE h8-30 | WAPE h31+ | folds better | gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nowcast | 9.28 |  | -1.91 | 105.74 | 164.49 | 0.90 | 6.86 | 8.19 | 9.49 |  |  |
| cf_k7_in_hb | 9.25 | -0.03 [-0.04, -0.01] | -1.86 | 105.43 | 164.26 | 0.90 | 6.53 | 8.10 | 9.49 | 5/7 | fail |
| cf_k7_in_pool | 9.26 | -0.01 [-0.02, -0.00] | -1.90 | 105.59 | 164.42 | 0.90 | 6.55 | 8.18 | 9.49 | 6/7 | fail |
| cf_k28_in_pool | 9.27 | -0.00 [-0.01, -0.00] | -1.91 | 105.70 | 164.50 | 0.90 | 6.79 | 8.19 | 9.49 | 5/7 | fail |
| cf_k28_hb_one | 10.81 | +1.54 [+1.22, +1.86] | -0.21 | 123.40 | 190.26 | 0.87 | 8.49 | 9.68 | 11.03 | 0/7 | fail |
| cf_k7_in_mkt | 9.26 | -0.01 [-0.02, +0.00] | -1.90 | 105.59 | 164.44 | 0.90 | 6.60 | 8.17 | 9.49 | 5/7 | fail |
| time_only | 28.19 | +18.81 [+17.81, +20.17] | -1.93 | 321.25 | 524.94 | 0.00 | 19.01 | 27.13 | 28.58 | 0/7 | fail |

Grid, best 8 and worst 3:

| setting | WAPE |
| --- | --- |
| cf_k7_in_hb | 9.25 |
| cf_k7_in_hb_echo | 9.26 |
| cf_k14_in_hb | 9.26 |
| cf_k7_in_mkt | 9.26 |
| cf_k7_in_pool | 9.26 |
| cf_k14_in_hb_echo | 9.26 |
| cf_k14_in_pool | 9.27 |
| cf_k14_in_mkt | 9.27 |
| cf_k14_hb_one_echo | 11.38 |
| cf_k7_hb_one | 11.82 |
| cf_k7_hb_one_echo | 11.82 |

Level bias % by fold:

| model | origin_2024-02-01 | origin_2024-03-01 | origin_2024-04-01 | origin_2024-05-01 | origin_2024-06-01 | origin_2024-07-01 | origin_2024-08-01 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| nowcast | -0.30 | -2.30 | -4.67 | -3.43 | -2.80 | -0.62 | 0.19 |
| cf_k7_in_hb | -0.25 | -2.35 | -4.69 | -3.12 | -2.77 | -0.59 | 0.21 |
| cf_k7_in_pool | -0.28 | -2.33 | -4.68 | -3.37 | -2.78 | -0.60 | 0.20 |
| cf_k28_in_pool | -0.27 | -2.31 | -4.69 | -3.42 | -2.79 | -0.60 | 0.20 |
| cf_k28_hb_one | 4.75 | -3.75 | -8.26 | 1.30 | -2.04 | 4.84 | 0.86 |
| cf_k7_in_mkt | -0.26 | -2.36 | -4.69 | -3.37 | -2.79 | -0.60 | 0.20 |
| time_only | 4.46 | -4.21 | -6.06 | -11.80 | -1.85 | 3.35 | 1.36 |

Memory estimates, mean over folds:

| series | rho pool (in-sample) | rho market median | rho held back | rho weekly | excess lag-7 | mean |e0| k28 in | corr(e0 in, test e days 1-30) | mean |e0| k28 hb | corr(e0 hb, test e days 1-30) | mean |e| test days 1-30 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| domestic | 0.741 | 0.741 | 0.657 | 0.612 | 0.326 | 0.020 | -0.120 | 0.030 | -0.134 | 0.026 |
| international | 0.692 | 0.734 | 0.814 | 0.248 | 0.066 | 0.027 | 0.068 | 0.065 | -0.034 | 0.063 |

## Experiment 1: carry-forward, planning chain (international)

### Chain, protocol

#### International

Shipped 20.67. Best setting `cf_k7_in_wk`, simplest within 0.2 pp `cf_k7_in_pool`. WAPE is market-day, mean over folds.

| model | WAPE | delta pp [90% CI] | bias % | MAE | RMSE | R2 vs time | WAPE h1-7 | WAPE h8-30 | WAPE h31+ | folds better | gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chain | 20.67 |  | -6.04 | 236.97 | 409.71 | 0.57 | 17.87 | 20.30 | 20.87 |  |  |
| cf_k7_in_wk | 20.67 | -0.00 [-0.00, +0.00] | -6.04 | 236.97 | 409.71 | 0.57 | 17.87 | 20.30 | 20.87 | 3/7 | fail |
| cf_k7_in_pool | 20.67 | -0.00 [-0.00, +0.00] | -6.04 | 236.97 | 409.71 | 0.57 | 17.87 | 20.30 | 20.87 | 4/7 | fail |
| cf_k28_in_pool | 20.67 | +0.00 [+0.00, +0.00] | -6.04 | 236.98 | 409.71 | 0.57 | 17.87 | 20.30 | 20.87 | 1/7 | fail |
| cf_k28_hb_one | 29.99 | +9.15 [+6.12, +12.21] | 5.25 | 341.80 | 657.45 | -0.10 | 30.88 | 31.46 | 29.55 | 0/7 | fail |
| cf_k7_in_mkt | 20.68 | +0.01 [-0.00, +0.03] | -6.04 | 237.10 | 409.91 | 0.57 | 18.01 | 20.33 | 20.87 | 3/7 | fail |
| time_only | 29.74 | +8.93 [+7.10, +10.68] | -0.84 | 339.32 | 626.92 | 0.00 | 23.14 | 26.58 | 30.36 | 0/7 | fail |

Grid, best 8 and worst 3:

| setting | WAPE |
| --- | --- |
| cf_k7_in_wk | 20.67 |
| cf_k7_in_pool | 20.67 |
| cf_k7_in_pool_echo | 20.67 |
| cf_k28_in_wk | 20.67 |
| cf_k14_in_wk | 20.67 |
| cf_k28_in_pool | 20.67 |
| cf_k28_in_pool_echo | 20.67 |
| cf_k14_in_pool | 20.67 |
| cf_k14_hb_one | 34.87 |
| cf_k7_hb_one_echo | 35.11 |
| cf_k7_hb_one | 35.11 |

Weekly market-week sums:

| model | WAPE | delta pp [90% CI] | folds better | bias % | gate |
| --- | --- | --- | --- | --- | --- |
| chain | 18.69 |  |  | -6.13 |  |
| cf_k7_in_wk | 18.69 | -0.00 [-0.00, +0.00] | 4/7 | -6.13 | fail |
| cf_k7_in_pool | 18.69 | -0.00 [-0.00, +0.00] | 4/7 | -6.13 | fail |
| cf_k28_in_pool | 18.69 | +0.00 [-0.00, +0.00] | 4/7 | -6.13 | fail |
| cf_k28_hb_one | 28.39 | +9.49 [+6.33, +12.61] | 0/7 | 5.12 | fail |
| cf_k7_in_mkt | 18.70 | +0.01 [-0.00, +0.02] | 2/7 | -6.13 | fail |
| time_only | 28.36 | +9.50 [+7.68, +11.51] | 0/7 | -0.98 | fail |

Level bias % by fold:

| model | origin_2024-02-01 | origin_2024-03-01 | origin_2024-04-01 | origin_2024-05-01 | origin_2024-06-01 | origin_2024-07-01 | origin_2024-08-01 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| chain | -5.73 | -5.37 | -6.79 | -7.01 | -8.55 | -5.98 | -3.28 |
| cf_k7_in_wk | -5.73 | -5.37 | -6.79 | -7.01 | -8.55 | -5.98 | -3.28 |
| cf_k7_in_pool | -5.73 | -5.37 | -6.79 | -7.01 | -8.55 | -5.98 | -3.28 |
| cf_k28_in_pool | -5.73 | -5.37 | -6.79 | -7.01 | -8.55 | -5.98 | -3.28 |
| cf_k28_hb_one | 54.33 | 3.35 | -7.66 | -0.44 | -13.45 | -1.13 | 2.55 |
| cf_k7_in_mkt | -5.73 | -5.37 | -6.80 | -6.91 | -8.58 | -6.02 | -3.30 |
| time_only | 17.30 | 0.34 | -14.11 | -3.90 | -8.05 | -0.42 | 2.13 |

Memory estimates, mean over folds:

| series | rho pool (in-sample) | rho market median | rho held back | rho weekly | excess lag-7 | mean |e0| k28 in | corr(e0 in, test e days 1-30) | mean |e0| k28 hb | corr(e0 hb, test e days 1-30) | mean |e| test days 1-30 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| international | 0.814 | 0.790 | 0.912 | 0.195 | 0.000 | 0.034 | -0.091 | 0.177 | -0.172 | 0.148 |

### Chain, gap0

#### International

Shipped 20.32. Best setting `cf_k7_in_pool`, simplest within 0.2 pp `cf_k7_in_pool`. WAPE is market-day, mean over folds.

| model | WAPE | delta pp [90% CI] | bias % | MAE | RMSE | R2 vs time | WAPE h1-7 | WAPE h8-30 | WAPE h31+ | folds better | gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chain | 20.32 |  | -5.03 | 232.90 | 401.41 | 0.42 | 16.14 | 20.66 | 20.47 |  |  |
| cf_k7_in_pool | 20.31 | -0.00 [-0.05, +0.03] | -5.02 | 232.85 | 401.62 | 0.41 | 15.95 | 20.68 | 20.47 | 3/7 | fail |
| cf_k28_in_pool | 20.34 | +0.02 [+0.01, +0.04] | -5.06 | 233.15 | 401.86 | 0.41 | 16.61 | 20.68 | 20.47 | 1/7 | fail |
| cf_k28_hb_one | 26.29 | +5.92 [+5.10, +6.85] | -2.03 | 300.73 | 506.48 | 0.07 | 23.74 | 27.89 | 26.12 | 0/7 | fail |
| cf_k7_in_mkt | 20.36 | +0.05 [-0.05, +0.14] | -5.02 | 233.43 | 403.01 | 0.41 | 16.43 | 20.83 | 20.49 | 2/7 | fail |
| time_only | 28.19 | +7.71 [+6.64, +8.98] | -1.93 | 321.25 | 524.94 | 0.00 | 19.01 | 27.13 | 28.58 | 0/7 | fail |

Grid, best 8 and worst 3:

| setting | WAPE |
| --- | --- |
| cf_k7_in_pool | 20.31 |
| cf_k7_in_pool_echo | 20.31 |
| cf_k7_in_wk | 20.31 |
| cf_k14_in_pool_echo | 20.33 |
| cf_k14_in_pool | 20.33 |
| cf_k14_in_wk | 20.33 |
| cf_k28_in_pool_echo | 20.34 |
| cf_k28_in_pool | 20.34 |
| cf_k14_hb_one | 29.66 |
| cf_k7_hb_one | 31.28 |
| cf_k7_hb_one_echo | 31.28 |

Weekly market-week sums:

| model | WAPE | delta pp [90% CI] | folds better | bias % | gate |
| --- | --- | --- | --- | --- | --- |
| chain | 18.35 |  |  | -5.09 |  |
| cf_k7_in_pool | 18.36 | +0.01 [-0.02, +0.04] | 2/7 | -5.08 | fail |
| cf_k28_in_pool | 18.36 | +0.02 [+0.00, +0.02] | 1/7 | -5.11 | fail |
| cf_k28_hb_one | 24.73 | +6.34 [+5.59, +7.38] | 0/7 | -2.08 | fail |
| cf_k7_in_mkt | 18.41 | +0.06 [-0.03, +0.15] | 2/7 | -5.08 | fail |
| time_only | 26.87 | +8.38 [+7.21, +9.89] | 0/7 | -1.94 | fail |

Level bias % by fold:

| model | origin_2024-02-01 | origin_2024-03-01 | origin_2024-04-01 | origin_2024-05-01 | origin_2024-06-01 | origin_2024-07-01 | origin_2024-08-01 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| chain | -4.83 | -3.33 | -6.32 | -9.52 | -6.63 | -3.03 | -2.21 |
| cf_k7_in_pool | -4.83 | -3.55 | -6.25 | -9.53 | -6.45 | -3.02 | -2.17 |
| cf_k28_in_pool | -4.83 | -3.33 | -6.37 | -9.57 | -6.67 | -3.02 | -2.27 |
| cf_k28_hb_one | 3.75 | 0.88 | -5.46 | -9.55 | -6.41 | 4.14 | -2.19 |
| cf_k7_in_mkt | -4.94 | -3.76 | -6.28 | -9.60 | -6.01 | -3.08 | -2.13 |
| time_only | 4.46 | -4.21 | -6.06 | -11.80 | -1.85 | 3.35 | 1.36 |

Memory estimates, mean over folds:

| series | rho pool (in-sample) | rho market median | rho held back | rho weekly | excess lag-7 | mean |e0| k28 in | corr(e0 in, test e days 1-30) | mean |e0| k28 hb | corr(e0 hb, test e days 1-30) | mean |e| test days 1-30 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| international | 0.817 | 0.795 | 0.924 | 0.202 | 0.000 | 0.039 | -0.275 | 0.162 | -0.366 | 0.150 |

## Experiment 2: drifting strength, daily nowcast

#### Domestic

Selection check: chosen on the first 4 folds only, `drift_k182_l0.1`; on the last 3 folds +0.29 pp [+0.01, +0.53].

Shipped 4.18. Best `drift_k90_l1`, simplest within 0.2 pp `drift_k182_l1`.

| model | WAPE | delta pp [90% CI] | bias % | MAE | RMSE | R2 vs time | WAPE h1-7 | WAPE h8-30 | WAPE h31+ | folds better | gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nowcast | 4.18 |  | -0.62 | 695.20 | 1102.18 | 0.76 | 3.82 | 4.94 | 4.08 |  |  |
| drift_k90_l1 | 4.12 | -0.06 [-0.14, +0.02] | -0.18 | 686.04 | 1066.25 | 0.77 | 3.97 | 4.77 | 4.03 | 6/7 | fail |
| drift_k182_l1 | 4.14 | -0.04 [-0.08, -0.01] | -0.41 | 689.14 | 1085.25 | 0.76 | 3.85 | 4.86 | 4.04 | 6/7 | fail |
| time_only | 10.09 | +5.88 [+4.23, +7.72] | 5.99 | 1673.73 | 2233.88 | 0.00 | 7.79 | 7.69 | 10.53 | 0/7 | fail |

Grid (knot spacing k, lambda l, beyond the training days: held, or half-life 30 or 90 days):

| variant | WAPE |
| --- | --- |
| drift_k90_l0.01 | 7.79 |
| drift_k90_l0.01_hl30 | 8.41 |
| drift_k90_l0.01_hl90 | 5.97 |
| drift_k90_l0.1 | 4.84 |
| drift_k90_l0.1_hl30 | 7.10 |
| drift_k90_l0.1_hl90 | 5.37 |
| drift_k90_l1 | 4.12 |
| drift_k90_l1_hl30 | 4.48 |
| drift_k90_l1_hl90 | 4.24 |
| drift_k90_l10 | 4.16 |
| drift_k90_l10_hl30 | 4.18 |
| drift_k90_l10_hl90 | 4.17 |
| drift_k182_l0.01 | 5.82 |
| drift_k182_l0.01_hl30 | 7.16 |
| drift_k182_l0.01_hl90 | 5.22 |
| drift_k182_l0.1 | 4.24 |
| drift_k182_l0.1_hl30 | 5.00 |
| drift_k182_l0.1_hl90 | 4.36 |
| drift_k182_l1 | 4.14 |
| drift_k182_l1_hl30 | 4.20 |
| drift_k182_l1_hl90 | 4.16 |
| drift_k182_l10 | 4.17 |
| drift_k182_l10_hl30 | 4.18 |
| drift_k182_l10_hl90 | 4.17 |

#### International

Selection check: chosen on the first 4 folds only, `drift_k182_l0.1`; on the last 3 folds -0.37 pp [-0.64, -0.10].

Shipped 9.62. Best `drift_k182_l0.1`, simplest within 0.2 pp `drift_k182_l0.1`.

| model | WAPE | delta pp [90% CI] | bias % | MAE | RMSE | R2 vs time | WAPE h1-7 | WAPE h8-30 | WAPE h31+ | folds better | gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nowcast | 9.62 |  | -2.25 | 109.70 | 169.18 | 0.93 | 7.91 | 8.71 | 9.78 |  |  |
| drift_k182_l0.1 | 9.30 | -0.33 [-0.47, -0.19] | -1.69 | 105.97 | 163.50 | 0.93 | 7.71 | 8.40 | 9.44 | 7/7 | pass |
| time_only | 29.74 | +20.04 [+18.64, +21.44] | -0.84 | 339.32 | 626.92 | 0.00 | 23.14 | 26.58 | 30.36 | 0/7 | fail |

Grid (knot spacing k, lambda l, beyond the training days: held, or half-life 30 or 90 days):

| variant | WAPE |
| --- | --- |
| drift_k90_l0.01 | 11.11 |
| drift_k90_l0.01_hl30 | 10.40 |
| drift_k90_l0.01_hl90 | 10.19 |
| drift_k90_l0.1 | 9.53 |
| drift_k90_l0.1_hl30 | 10.18 |
| drift_k90_l0.1_hl90 | 9.76 |
| drift_k90_l1 | 9.39 |
| drift_k90_l1_hl30 | 9.80 |
| drift_k90_l1_hl90 | 9.62 |
| drift_k90_l10 | 9.56 |
| drift_k90_l10_hl30 | 9.64 |
| drift_k90_l10_hl90 | 9.61 |
| drift_k182_l0.01 | 9.81 |
| drift_k182_l0.01_hl30 | 10.17 |
| drift_k182_l0.01_hl90 | 9.75 |
| drift_k182_l0.1 | 9.30 |
| drift_k182_l0.1_hl30 | 9.95 |
| drift_k182_l0.1_hl90 | 9.63 |
| drift_k182_l1 | 9.49 |
| drift_k182_l1_hl30 | 9.67 |
| drift_k182_l1_hl90 | 9.60 |
| drift_k182_l10 | 9.60 |
| drift_k182_l10_hl30 | 9.63 |
| drift_k182_l10_hl90 | 9.62 |

### Identifiability, domestic, `drift_k182_l1`

| market | s min | s max | s last (last fold) | corr(c, s) | passes | shipped passes | not converged |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DOMESTIC | -0.016 | 0.019 | 0.018 | 0.541 | 18.429 | 13.000 | 0 |

### Identifiability, international, `drift_k182_l0.1`

| market | s min | s max | s last (last fold) | corr(c, s) | passes | shipped passes | not converged |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CHINA | -0.033 | 0.047 | 0.047 | 0.728 | 58.000 | 26.000 | 0 |
| EGYPT | -0.031 | 0.042 | 0.042 | 0.267 | 34.286 | 34.143 | 0 |
| FRANCE | -0.043 | 0.023 | -0.043 | -0.147 | 68.286 | 61.857 | 0 |
| GERMANY | -0.081 | 0.066 | -0.081 | -0.608 | 92.000 | 89.143 | 0 |
| INDIA | -0.036 | 0.065 | 0.065 | 0.269 | 31.571 | 18.000 | 0 |
| ISRAEL | -0.143 | 0.135 | -0.004 | 0.541 | 33.429 | 24.714 | 0 |
| ITALY | -0.075 | 0.073 | -0.004 | 0.123 | 43.714 | 49.143 | 0 |
| KAZAKHSTAN | -0.058 | 0.054 | 0.009 | 0.540 | 38.143 | 24.429 | 0 |
| KUWAIT | -0.042 | 0.063 | 0.047 | 0.825 | 96.000 | 92.571 | 0 |
| OMAN | -0.048 | 0.153 | 0.066 | -0.235 | 56.429 | 53.286 | 0 |
| OTHER_AMERICAS_AFRICA | -0.051 | 0.071 | 0.021 | -0.075 | 51.571 | 44.000 | 0 |
| OTHER_ASIA_PACIFIC | -0.027 | 0.067 | 0.061 | 0.346 | 39.000 | 26.857 | 0 |
| OTHER_EURASIA | -0.034 | 0.060 | 0.053 | -0.163 | 38.857 | 19.429 | 0 |
| OTHER_EUROPE | -0.028 | 0.047 | -0.028 | -0.509 | 140.429 | 135.143 | 0 |
| OTHER_MENA | -0.028 | 0.050 | 0.050 | 0.041 | 46.571 | 43.429 | 0 |
| PHILIPPINES | -0.060 | 0.083 | 0.083 | 0.675 | 32.571 | 34.429 | 0 |
| RUSSIAN FEDERATION | -0.073 | 0.036 | -0.058 | -0.267 | 78.857 | 50.857 | 0 |
| SAUDI ARABIA | -0.075 | 0.120 | 0.092 | -0.543 | 137.857 | 126.571 | 0 |
| UNITED KINGDOM | -0.049 | 0.072 | -0.049 | 0.313 | 41.429 | 34.571 | 0 |
| UNITED STATES OF AMERICA | -0.016 | 0.012 | -0.016 | 0.503 | 39.000 | 35.571 | 0 |

## Chosen settings side by side (protocol)

- carry: domestic `cf_k7_in_pool`
- carry: international `cf_k28_in_one`
- drift: domestic `drift_k182_l1`
- drift: international `drift_k182_l0.1`

#### Domestic

| model | WAPE | delta pp [90% CI] | bias % | MAE | RMSE | R2 vs time | WAPE h1-7 | WAPE h8-30 | WAPE h31+ | folds better | gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nowcast | 4.18 |  | -0.62 | 695.20 | 1102.18 | 0.76 | 3.82 | 4.94 | 4.08 |  |  |
| carry | 4.18 | -0.00 [-0.00, +0.00] | -0.62 | 695.20 | 1102.17 | 0.76 | 3.82 | 4.94 | 4.08 | 3/7 | fail |
| drift | 4.14 | -0.04 [-0.08, -0.01] | -0.41 | 689.14 | 1085.25 | 0.76 | 3.85 | 4.86 | 4.04 | 6/7 | fail |
| time_only | 10.09 | +5.88 [+4.23, +7.72] | 5.99 | 1673.73 | 2233.88 | 0.00 | 7.79 | 7.69 | 10.53 | 0/7 | fail |

#### International

| model | WAPE | delta pp [90% CI] | bias % | MAE | RMSE | R2 vs time | WAPE h1-7 | WAPE h8-30 | WAPE h31+ | folds better | gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nowcast | 9.62 |  | -2.25 | 109.70 | 169.18 | 0.93 | 7.91 | 8.71 | 9.78 |  |  |
| carry | 9.54 | -0.08 [-0.25, +0.10] | -1.54 | 108.74 | 166.89 | 0.93 | 8.04 | 8.84 | 9.65 | 4/7 | fail |
| drift | 9.30 | -0.33 [-0.47, -0.19] | -1.69 | 105.97 | 163.50 | 0.93 | 7.71 | 8.40 | 9.44 | 7/7 | pass |
| time_only | 29.74 | +20.04 [+18.64, +21.44] | -0.84 | 339.32 | 626.92 | 0.00 | 23.14 | 26.58 | 30.36 | 0/7 | fail |

## Bias by market (protocol, all folds pooled)

folds >5%: folds (of 7) with a same-sign bias above 5%.

| market | nowcast bias % | nowcast folds >5% | carry bias % | carry folds >5% | drift bias % | drift folds >5% |
| --- | --- | --- | --- | --- | --- | --- |
| CHINA | -11.9 | 7 | -10.0 | 6 | -10.8 | 7 |
| DOMESTIC | -0.6 | 0 | -0.6 | 0 | -0.4 | 0 |
| EGYPT | -9.7 | 5 | -7.5 | 4 | -9.1 | 5 |
| FRANCE | 1.5 | 1 | 1.4 | 1 | 0.7 | 1 |
| GERMANY | 7.5 | 6 | 6.2 | 5 | 6.2 | 5 |
| INDIA | -9.1 | 6 | -7.2 | 5 | -8.1 | 6 |
| ISRAEL | 1.5 | 1 | 2.0 | 3 | 11.1 | 4 |
| ITALY | -2.6 | 2 | -0.7 | 2 | -1.4 | 1 |
| KAZAKHSTAN | 2.9 | 1 | 2.8 | 2 | 1.3 | 1 |
| KUWAIT | -3.0 | 1 | -0.0 | 2 | -0.2 | 1 |
| OMAN | -4.9 | 3 | -2.1 | 4 | -1.3 | 3 |
| OTHER_AMERICAS_AFRICA | 0.3 | 0 | 0.5 | 2 | 0.7 | 0 |
| OTHER_ASIA_PACIFIC | -7.0 | 4 | -5.5 | 3 | -6.1 | 3 |
| OTHER_EURASIA | -10.2 | 7 | -9.0 | 6 | -8.6 | 5 |
| OTHER_EUROPE | 2.5 | 2 | 2.7 | 2 | 2.3 | 2 |
| OTHER_MENA | -0.3 | 1 | 0.6 | 1 | 0.6 | 1 |
| PHILIPPINES | -16.4 | 7 | -14.0 | 5 | -16.0 | 7 |
| RUSSIAN FEDERATION | 8.6 | 5 | 6.5 | 3 | 7.2 | 5 |
| SAUDI ARABIA | -5.6 | 4 | -2.2 | 2 | -0.3 | 3 |
| UNITED KINGDOM | 2.8 | 0 | 1.9 | 1 | 0.8 | 0 |
| UNITED STATES OF AMERICA | -2.9 | 2 | -3.4 | 3 | -3.1 | 3 |
