# Seasonal link: results

Aggregates only. International markets. Data to 2025-01-31; FROZEN_TEST is not read. Written by `report.py`.

## Step 1: graphs

Weekly residuals after a centred 13-week trend and a 4-harmonic annual season, per market, 2023-01 to 2025-01-31. Slopes pooled over 20 markets, 90% week-cluster bootstrap.

### By season

| link | season | n | slope [90%] | corr | sd x |
| --- | --- | --- | --- | --- | --- |
| p2p->arrivals | Winter_Peak | 692 | +0.82 [+0.71, +0.93] | 0.59 | 0.21 |
| p2p->arrivals | Spring_Shoulder | 332 | +0.74 [+0.63, +0.86] | 0.58 | 0.22 |
| p2p->arrivals | Summer_Trough | 540 | +0.43 [+0.32, +0.54] | 0.37 | 0.16 |
| p2p->arrivals | Autumn_Shoulder | 337 | +0.45 [+0.30, +0.57] | 0.39 | 0.21 |
| seats->arrivals | Winter_Peak | 692 | +0.94 [+0.58, +1.30] | 0.20 | 0.07 |
| seats->arrivals | Spring_Shoulder | 332 | +1.00 [+0.56, +1.50] | 0.25 | 0.07 |
| seats->arrivals | Summer_Trough | 540 | +0.90 [+0.57, +1.24] | 0.24 | 0.05 |
| seats->arrivals | Autumn_Shoulder | 337 | +0.01 [-0.28, +0.33] | 0.00 | 0.09 |

### By month

| link | month | n | slope [90%] | corr |
| --- | --- | --- | --- | --- |
| seats->arrivals | 1 | 80 | +0.55 [+0.00, +1.12] | 0.12 |
| seats->arrivals | 2 | 138 | +1.12 [+0.62, +1.51] | 0.23 |
| seats->arrivals | 3 | 174 | +1.71 [+0.82, +2.35] | 0.35 |
| seats->arrivals | 4 | 152 | +0.96 [+0.22, +1.87] | 0.20 |
| seats->arrivals | 5 | 180 | +1.03 [+0.62, +1.47] | 0.32 |
| seats->arrivals | 6 | 180 | +1.00 [+0.42, +1.65] | 0.23 |
| seats->arrivals | 7 | 160 | +0.76 [+0.39, +1.17] | 0.25 |
| seats->arrivals | 8 | 200 | +0.88 [+0.34, +1.32] | 0.23 |
| seats->arrivals | 9 | 158 | +0.12 [-0.34, +0.66] | 0.03 |
| seats->arrivals | 10 | 179 | -0.02 [-0.37, +0.37] | -0.01 |
| seats->arrivals | 11 | 180 | +0.46 [-0.00, +0.96] | 0.14 |
| seats->arrivals | 12 | 120 | +0.34 [-0.51, +1.18] | 0.06 |
| p2p->arrivals | 1 | 80 | +0.97 [+0.60, +1.10] | 0.66 |
| p2p->arrivals | 2 | 138 | +0.96 [+0.75, +1.13] | 0.65 |
| p2p->arrivals | 3 | 174 | +1.01 [+0.78, +1.21] | 0.66 |
| p2p->arrivals | 4 | 152 | +0.74 [+0.55, +0.93] | 0.57 |
| p2p->arrivals | 5 | 180 | +0.79 [+0.69, +0.91] | 0.61 |
| p2p->arrivals | 6 | 180 | +0.70 [+0.63, +0.80] | 0.54 |
| p2p->arrivals | 7 | 160 | +0.24 [+0.13, +0.37] | 0.19 |
| p2p->arrivals | 8 | 200 | +0.25 [+0.06, +0.44] | 0.23 |
| p2p->arrivals | 9 | 158 | +0.52 [+0.11, +0.80] | 0.40 |
| p2p->arrivals | 10 | 179 | +0.43 [+0.29, +0.58] | 0.40 |
| p2p->arrivals | 11 | 180 | +0.56 [+0.38, +0.76] | 0.38 |
| p2p->arrivals | 12 | 120 | +0.64 [+0.38, +0.83] | 0.46 |

### Contrasts

| data | link | contrast | difference [90%] |
| --- | --- | --- | --- |
| fourier, all | seats->arrivals | Jan-Jun minus Jul-Dec | +0.88 [+0.49, +1.30] |
| fourier, all | seats->arrivals | Winter+Spring minus Summer+Autumn | +0.64 [+0.25, +1.05] |
| fourier, all | p2p->arrivals | Jan-Jun minus Jul-Dec | +0.37 [+0.25, +0.50] |
| fourier, all | p2p->arrivals | Winter+Spring minus Summer+Autumn | +0.36 [+0.25, +0.48] |
| fourier, all | arrivals->guests | Jan-Jun minus Jul-Dec | -0.05 [-0.09, -0.01] |
| fourier, all | arrivals->guests | Winter+Spring minus Summer+Autumn | -0.03 [-0.07, +0.02] |
| fourier, no lunar weeks | seats->arrivals | Jan-Jun minus Jul-Dec | +0.80 [+0.37, +1.19] |
| fourier, no lunar weeks | seats->arrivals | Winter+Spring minus Summer+Autumn | +0.67 [+0.26, +1.07] |
| fourier, no lunar weeks | p2p->arrivals | Jan-Jun minus Jul-Dec | +0.41 [+0.29, +0.55] |
| fourier, no lunar weeks | p2p->arrivals | Winter+Spring minus Summer+Autumn | +0.38 [+0.24, +0.51] |
| fourier, no lunar weeks | arrivals->guests | Jan-Jun minus Jul-Dec | -0.02 [-0.07, +0.03] |
| fourier, no lunar weeks | arrivals->guests | Winter+Spring minus Summer+Autumn | +0.01 [-0.05, +0.06] |
| woy, all | seats->arrivals | Jan-Jun minus Jul-Dec | +0.72 [+0.32, +1.16] |
| woy, all | seats->arrivals | Winter+Spring minus Summer+Autumn | +0.47 [+0.07, +0.92] |
| woy, all | p2p->arrivals | Jan-Jun minus Jul-Dec | +0.19 [+0.04, +0.33] |
| woy, all | p2p->arrivals | Winter+Spring minus Summer+Autumn | +0.10 [-0.04, +0.25] |
| woy, all | arrivals->guests | Jan-Jun minus Jul-Dec | -0.05 [-0.09, -0.00] |
| woy, all | arrivals->guests | Winter+Spring minus Summer+Autumn | -0.06 [-0.10, -0.01] |

### Robustness by season

LOMO: leave one market out, range over the 20 runs. No lunar: weeks touching Ramadan or an Eid window removed.

| link | season | all | LOMO min | LOMO max | no lunar | no lunar low | no lunar high | n no lunar |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| seats->arrivals | Winter_Peak | 0.94 | 0.78 | 1.06 | 0.66 | 0.34 | 0.97 | 556 |
| seats->arrivals | Spring_Shoulder | 1.00 | 0.87 | 1.31 | 1.36 | 0.83 | 1.89 | 219 |
| seats->arrivals | Summer_Trough | 0.90 | 0.79 | 0.97 | 0.70 | 0.39 | 1.01 | 480 |
| seats->arrivals | Autumn_Shoulder | 0.01 | -0.05 | 0.11 | 0.01 | -0.28 | 0.33 | 337 |
| p2p->arrivals | Winter_Peak | 0.82 | 0.77 | 0.87 | 0.78 | 0.66 | 0.89 | 556 |
| p2p->arrivals | Spring_Shoulder | 0.74 | 0.68 | 0.82 | 0.81 | 0.72 | 0.91 | 219 |
| p2p->arrivals | Summer_Trough | 0.43 | 0.37 | 0.47 | 0.37 | 0.26 | 0.49 | 480 |
| p2p->arrivals | Autumn_Shoulder | 0.45 | 0.40 | 0.50 | 0.45 | 0.30 | 0.57 | 337 |

### Six largest markets

| market | link | season | n | slope [90%] | H1-H2 |
| --- | --- | --- | --- | --- | --- |
| UNITED KINGDOM | seats->arrivals | Autumn_Shoulder | 17 | -0.73 [-5.84, +2.18] | -2.35 |
| UNITED KINGDOM | seats->arrivals | Spring_Shoulder | 17 | -2.04 [-7.09, +2.79] | -2.35 |
| UNITED KINGDOM | seats->arrivals | Summer_Trough | 27 | -1.18 [-3.00, +0.33] | -2.35 |
| UNITED KINGDOM | seats->arrivals | Winter_Peak | 35 | -0.98 [-4.90, +2.46] | -2.35 |
| UNITED KINGDOM | p2p->arrivals | Autumn_Shoulder | 17 | +0.86 [+0.63, +0.94] | 0.04 |
| UNITED KINGDOM | p2p->arrivals | Spring_Shoulder | 17 | +0.85 [+0.68, +1.03] | 0.04 |
| UNITED KINGDOM | p2p->arrivals | Summer_Trough | 27 | +0.52 [+0.35, +0.69] | 0.04 |
| UNITED KINGDOM | p2p->arrivals | Winter_Peak | 35 | +1.01 [+0.90, +1.14] | 0.04 |
| INDIA | seats->arrivals | Autumn_Shoulder | 17 | +3.68 [-1.73, +9.67] | -0.70 |
| INDIA | seats->arrivals | Spring_Shoulder | 17 | -0.69 [-2.99, +0.69] | -0.70 |
| INDIA | seats->arrivals | Summer_Trough | 27 | +1.89 [-2.37, +7.22] | -0.70 |
| INDIA | seats->arrivals | Winter_Peak | 35 | -2.92 [-5.78, -0.89] | -0.70 |
| INDIA | p2p->arrivals | Autumn_Shoulder | 17 | +1.71 [+0.05, +3.30] | -0.76 |
| INDIA | p2p->arrivals | Spring_Shoulder | 17 | +1.06 [+0.09, +2.42] | -0.76 |
| INDIA | p2p->arrivals | Summer_Trough | 27 | +0.20 [-0.29, +0.63] | -0.76 |
| INDIA | p2p->arrivals | Winter_Peak | 35 | +1.36 [+0.33, +2.33] | -0.76 |
| CHINA | seats->arrivals | Autumn_Shoulder | 16 | +0.66 [-0.35, +2.15] | 0.22 |
| CHINA | seats->arrivals | Spring_Shoulder | 17 | -0.05 [-0.36, +0.33] | 0.22 |
| CHINA | seats->arrivals | Summer_Trough | 27 | +0.00 [-0.88, +0.62] | 0.22 |
| CHINA | seats->arrivals | Winter_Peak | 35 | +1.31 [+0.73, +1.95] | 0.22 |
| CHINA | p2p->arrivals | Autumn_Shoulder | 16 | +0.40 [-0.05, +0.92] | -0.08 |
| CHINA | p2p->arrivals | Spring_Shoulder | 17 | +0.08 [-0.13, +0.25] | -0.08 |
| CHINA | p2p->arrivals | Summer_Trough | 27 | +0.09 [-0.39, +0.34] | -0.08 |
| CHINA | p2p->arrivals | Winter_Peak | 35 | +0.42 [+0.19, +0.64] | -0.08 |
| GERMANY | seats->arrivals | Autumn_Shoulder | 17 | +0.30 [-1.54, +1.40] | 1.76 |
| GERMANY | seats->arrivals | Spring_Shoulder | 17 | +2.60 [+1.42, +4.09] | 1.76 |
| GERMANY | seats->arrivals | Summer_Trough | 27 | +3.57 [+1.50, +5.85] | 1.76 |
| GERMANY | seats->arrivals | Winter_Peak | 35 | +1.24 [+0.26, +2.42] | 1.76 |
| GERMANY | p2p->arrivals | Autumn_Shoulder | 17 | +0.38 [+0.28, +0.48] | 0.35 |
| GERMANY | p2p->arrivals | Spring_Shoulder | 17 | +0.75 [+0.51, +1.00] | 0.35 |
| GERMANY | p2p->arrivals | Summer_Trough | 27 | +0.41 [+0.02, +0.65] | 0.35 |
| GERMANY | p2p->arrivals | Winter_Peak | 35 | +0.65 [+0.48, +0.78] | 0.35 |
| SAUDI ARABIA | seats->arrivals | Autumn_Shoulder | 16 | -4.00 [-8.49, +0.95] | 1.35 |
| SAUDI ARABIA | seats->arrivals | Spring_Shoulder | 13 | +2.96 [-2.37, +6.79] | 1.35 |
| SAUDI ARABIA | seats->arrivals | Summer_Trough | 27 | +3.83 [+1.30, +5.56] | 1.35 |
| SAUDI ARABIA | seats->arrivals | Winter_Peak | 28 | -1.58 [-8.49, +5.10] | 1.35 |
| SAUDI ARABIA | p2p->arrivals | Autumn_Shoulder | 16 | +1.12 [-0.07, +3.18] | -0.06 |
| SAUDI ARABIA | p2p->arrivals | Spring_Shoulder | 13 | +1.21 [-0.37, +2.87] | -0.06 |
| SAUDI ARABIA | p2p->arrivals | Summer_Trough | 27 | +1.09 [+0.57, +1.41] | -0.06 |
| SAUDI ARABIA | p2p->arrivals | Winter_Peak | 28 | +1.88 [+1.02, +2.61] | -0.06 |
| RUSSIAN FEDERATION | seats->arrivals | Autumn_Shoulder | 17 | +0.24 [-0.33, +0.83] | 0.64 |
| RUSSIAN FEDERATION | seats->arrivals | Spring_Shoulder | 17 | +1.08 [+0.39, +1.73] | 0.64 |
| RUSSIAN FEDERATION | seats->arrivals | Summer_Trough | 27 | -0.00 [-0.62, +0.51] | 0.64 |
| RUSSIAN FEDERATION | seats->arrivals | Winter_Peak | 35 | +1.17 [+0.62, +1.69] | 0.64 |
| RUSSIAN FEDERATION | p2p->arrivals | Autumn_Shoulder | 17 | +0.36 [+0.01, +0.53] | 0.21 |
| RUSSIAN FEDERATION | p2p->arrivals | Spring_Shoulder | 17 | +0.60 [+0.36, +0.96] | 0.21 |
| RUSSIAN FEDERATION | p2p->arrivals | Summer_Trough | 27 | -0.05 [-0.24, +0.16] | 0.21 |
| RUSSIAN FEDERATION | p2p->arrivals | Winter_Peak | 35 | +0.67 [+0.48, +0.79] | 0.21 |

### Chain link 1 in sample, by season

Slope on the weekly seat deviation from its centred 13-week trend. actual = model + residual.

| target | group | n | slope [90%] |
| --- | --- | --- | --- |
| actual | Winter_Peak | 680 | +1.34 [+0.92, +1.70] |
| actual | Spring_Shoulder | 340 | +1.15 [+0.63, +1.68] |
| actual | Summer_Trough | 540 | +0.99 [+0.58, +1.40] |
| actual | Autumn_Shoulder | 340 | +0.16 [-0.08, +0.42] |
| model | Winter_Peak | 680 | +1.24 [+0.89, +1.55] |
| model | Spring_Shoulder | 340 | +1.10 [+0.68, +1.52] |
| model | Summer_Trough | 540 | +0.54 [+0.25, +0.86] |
| model | Autumn_Shoulder | 340 | +0.45 [+0.32, +0.62] |
| residual | Winter_Peak | 680 | +0.10 [-0.04, +0.24] |
| residual | Spring_Shoulder | 340 | +0.06 [-0.16, +0.30] |
| residual | Summer_Trough | 540 | +0.35 [+0.07, +0.61] |
| residual | Autumn_Shoulder | 340 | -0.28 [-0.53, -0.04] |
| residual, no lunar weeks | Winter_Peak | 540 | +0.10 [-0.09, +0.28] |
| residual, no lunar weeks | Spring_Shoulder | 220 | +0.26 [-0.03, +0.54] |
| residual, no lunar weeks | Summer_Trough | 480 | +0.44 [+0.15, +0.68] |
| residual, no lunar weeks | Autumn_Shoulder | 340 | -0.28 [-0.53, -0.04] |

## Step 2: gate on VALIDATION_ORIGINS (international, 7 folds)

Shipped chain: daily WAPE 20.67, weekly 18.69. Best seasonal variant `fourier1_r0.001`, simplest within 0.2 pp `fourier1_r0.001`. delta: compare() against the shipped chain, pp, negative is better. Gate: delta <= -0.3 pp, interval below 0, 4 of 7 folds better.

### Grid, mean WAPE over folds

| variant | daily WAPE | weekly WAPE |
| --- | --- | --- |
| season_r0.001 | 21.19 | 19.23 |
| season_r0.01 | 20.99 | 18.96 |
| season_r0.1 | 20.64 | 18.66 |
| season_r1 | 20.66 | 18.68 |
| fourier1_r0.001 | 20.59 | 18.64 |
| fourier1_r0.01 | 20.67 | 18.69 |
| fourier1_r0.1 | 20.67 | 18.69 |
| fourier1_r1 | 20.67 | 18.69 |
| fourier2_r0.001 | 20.83 | 18.88 |
| fourier2_r0.01 | 20.68 | 18.71 |
| fourier2_r0.1 | 20.67 | 18.69 |
| fourier2_r1 | 20.67 | 18.69 |

### Daily market-day WAPE

| model | WAPE | bias % | folds better | gate | delta pp [90%] |
| --- | --- | --- | --- | --- | --- |
| shipped | 20.67 | -6.04 |  |  |  |
| season_r0.001 | 21.19 | -3.55 | 0.00 | fail | +0.53 [+0.09, +1.01] |
| season_r0.01 | 20.99 | -3.25 | 2.00 | fail | +0.33 [-0.11, +0.78] |
| season_r0.1 | 20.64 | -5.47 | 5.00 | fail | -0.02 [-0.12, +0.09] |
| season_r1 | 20.66 | -5.99 | 6.00 | fail | -0.01 [-0.02, +0.00] |
| fourier1_r0.001 | 20.59 | -6.13 | 4.00 | fail | -0.08 [-0.17, +0.01] |
| fourier1_r0.01 | 20.67 | -6.05 | 3.00 | fail | +0.00 [-0.01, +0.01] |
| fourier1_r0.1 | 20.67 | -6.04 | 2.00 | fail | -0.00 [-0.00, +0.00] |
| fourier1_r1 | 20.67 | -6.04 | 2.00 | fail | +0.00 [+0.00, +0.00] |
| fourier2_r0.001 | 20.83 | -5.72 | 3.00 | fail | +0.14 [-0.01, +0.33] |
| fourier2_r0.01 | 20.68 | -6.08 | 1.00 | fail | +0.01 [-0.02, +0.04] |
| fourier2_r0.1 | 20.67 | -6.05 | 2.00 | fail | +0.00 [-0.00, +0.00] |
| fourier2_r1 | 20.67 | -6.04 | 3.00 | fail | -0.00 [-0.00, +0.00] |

### Weekly market-week WAPE

| model | WAPE | bias % | folds better | gate | delta pp [90%] |
| --- | --- | --- | --- | --- | --- |
| shipped | 18.69 | -6.13 |  |  |  |
| season_r0.001 | 19.23 | -3.66 | 1.00 | fail | +0.55 [+0.02, +1.10] |
| season_r0.01 | 18.96 | -3.34 | 3.00 | fail | +0.28 [-0.23, +0.81] |
| season_r0.1 | 18.66 | -5.56 | 5.00 | fail | -0.02 [-0.15, +0.10] |
| season_r1 | 18.68 | -6.08 | 6.00 | fail | -0.01 [-0.02, +0.00] |
| fourier1_r0.001 | 18.64 | -6.22 | 4.00 | fail | -0.06 [-0.15, +0.04] |
| fourier1_r0.01 | 18.69 | -6.13 | 2.00 | fail | +0.00 [-0.01, +0.01] |
| fourier1_r0.1 | 18.69 | -6.13 | 3.00 | fail | -0.00 [-0.00, +0.00] |
| fourier1_r1 | 18.69 | -6.13 | 2.00 | fail | +0.00 [+0.00, +0.00] |
| fourier2_r0.001 | 18.88 | -5.82 | 3.00 | fail | +0.18 [-0.03, +0.41] |
| fourier2_r0.01 | 18.71 | -6.17 | 2.00 | fail | +0.02 [-0.01, +0.05] |
| fourier2_r0.1 | 18.69 | -6.13 | 3.00 | fail | +0.00 [-0.00, +0.00] |
| fourier2_r1 | 18.69 | -6.13 | 3.00 | fail | -0.00 [-0.00, +0.00] |

Selection check: chosen on the first 4 folds only, `season_r0.1`; on the last 3 folds +0.08 pp [-0.04, +0.17].

### Level bias % by fold (daily rows)

| model | origin_2024-02-01 | origin_2024-03-01 | origin_2024-04-01 | origin_2024-05-01 | origin_2024-06-01 | origin_2024-07-01 | origin_2024-08-01 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| fourier1_r0.001 | -5.4 | -5.9 | -7.0 | -7.1 | -8.7 | -5.7 | -3.4 |
| shipped | -5.7 | -5.4 | -6.8 | -7.0 | -8.6 | -6.0 | -3.3 |

### WAPE by fold (daily)

| fold | shipped | fourier1_r0.001 |
| --- | --- | --- |
| origin_2024-02-01 | 21.81 | 22.19 |
| origin_2024-03-01 | 21.54 | 21.03 |
| origin_2024-04-01 | 20.74 | 20.66 |
| origin_2024-05-01 | 18.90 | 18.98 |
| origin_2024-06-01 | 19.71 | 19.79 |
| origin_2024-07-01 | 20.56 | 20.45 |
| origin_2024-08-01 | 21.43 | 21.05 |

## Learned strengths, `fourier1_r0.001`

exp(a) per season on the full fit (every guest day to 2025-01-31), median over 20 markets with a 90% bootstrap over markets; fold min and max: range of the 7 fold-fit medians.

| season | fold min | fold max | markets above 1 | graph: actual / model slope | median [90% over markets] |
| --- | --- | --- | --- | --- | --- |
| Winter_Peak | 1.00 | 1.05 | 9 | 1.09 | 0.99 [0.99, 1.01] |
| Spring_Shoulder | 0.95 | 0.99 | 11 | 1.05 | 1.13 [0.88, 1.18] |
| Summer_Trough | 0.94 | 1.00 | 11 | 1.84 | 1.01 [0.99, 1.01] |
| Autumn_Shoulder | 1.00 | 1.05 | 9 | 0.35 | 0.89 [0.85, 1.13] |

By month (mid-month value, full fit):

| month | median [90%] |
| --- | --- |
| Jan | 0.99 [0.99, 1.01] |
| Feb | 1.06 [0.94, 1.08] |
| Mar | 1.11 [0.90, 1.16] |
| Apr | 1.13 [0.88, 1.19] |
| May | 1.12 [0.89, 1.17] |
| Jun | 1.07 [0.93, 1.10] |
| Jul | 1.01 [0.99, 1.01] |
| Aug | 0.95 [0.93, 1.06] |
| Sep | 0.90 [0.86, 1.12] |
| Oct | 0.88 [0.84, 1.14] |
| Nov | 0.89 [0.85, 1.13] |
| Dec | 0.93 [0.91, 1.08] |

Six largest markets, full fit (min to max over the 7 fold fits):

| market | Winter_Peak | Spring_Shoulder | Summer_Trough | Autumn_Shoulder |
| --- | --- | --- | --- | --- |
| UNITED KINGDOM | 1.00 (0.98 to 1.22) | 1.10 (0.88 to 1.05) | 1.01 (0.79 to 1.03) | 0.91 (0.95 to 1.03) |
| INDIA | 1.01 (0.98 to 1.23) | 0.88 (0.67 to 1.01) | 0.99 (0.78 to 1.03) | 1.13 (1.00 to 1.30) |
| CHINA | 0.97 (0.20 to 0.93) | 1.80 (0.45 to 16.88) | 1.03 (1.09 to 7.02) | 0.56 (0.10 to 2.32) |
| GERMANY | 0.99 (1.00 to 1.12) | 1.16 (0.83 to 0.95) | 1.01 (0.87 to 1.01) | 0.87 (0.98 to 1.14) |
| SAUDI ARABIA | 1.01 (0.96 to 1.23) | 0.80 (0.77 to 1.02) | 0.99 (0.78 to 1.05) | 1.24 (1.01 to 1.18) |
| RUSSIAN FEDERATION | 0.99 (0.86 to 1.01) | 1.16 (1.03 to 1.18) | 1.01 (0.98 to 1.21) | 0.87 (0.84 to 1.01) |

## Learned strengths, `season_r0.1`

exp(a) per season on the full fit (every guest day to 2025-01-31), median over 20 markets with a 90% bootstrap over markets; fold min and max: range of the 7 fold-fit medians.

| season | fold min | fold max | markets above 1 | graph: actual / model slope | median [90% over markets] |
| --- | --- | --- | --- | --- | --- |
| Winter_Peak | 1.00 | 1.00 | 7 | 1.09 | 1.00 [0.99, 1.00] |
| Spring_Shoulder | 1.00 | 1.00 | 10 | 1.05 | 1.00 [1.00, 1.01] |
| Summer_Trough | 1.00 | 1.00 | 9 | 1.84 | 1.00 [0.99, 1.02] |
| Autumn_Shoulder | 1.01 | 1.01 | 13 | 0.35 | 1.01 [1.00, 1.01] |

By month (mid-month value, full fit):

| month | median [90%] |
| --- | --- |
| Jan | 1.00 [0.99, 1.00] |
| Feb | 1.00 [0.99, 1.00] |
| Mar | 1.00 [0.99, 1.00] |
| Apr | 1.00 [1.00, 1.01] |
| May | 1.00 [1.00, 1.01] |
| Jun | 1.00 [0.99, 1.02] |
| Jul | 1.00 [0.99, 1.02] |
| Aug | 1.00 [0.99, 1.02] |
| Sep | 1.01 [1.00, 1.01] |
| Oct | 1.01 [1.00, 1.01] |
| Nov | 1.00 [0.99, 1.00] |
| Dec | 1.00 [0.99, 1.00] |

Six largest markets, full fit (min to max over the 7 fold fits):

| market | Winter_Peak | Spring_Shoulder | Summer_Trough | Autumn_Shoulder |
| --- | --- | --- | --- | --- |
| UNITED KINGDOM | 0.97 (0.97 to 0.98) | 1.05 (1.03 to 1.07) | 0.99 (0.97 to 1.00) | 1.04 (1.03 to 1.06) |
| INDIA | 1.02 (1.00 to 1.02) | 0.99 (0.98 to 1.01) | 0.97 (0.96 to 0.97) | 1.01 (1.02 to 1.04) |
| CHINA | 1.00 (1.00 to 1.01) | 1.00 (1.00 to 1.00) | 1.00 (0.99 to 1.00) | 1.00 (1.00 to 1.00) |
| GERMANY | 0.99 (0.99 to 1.00) | 1.01 (0.99 to 1.02) | 0.98 (0.98 to 1.00) | 1.03 (1.03 to 1.04) |
| SAUDI ARABIA | 1.04 (1.02 to 1.04) | 1.01 (1.02 to 1.06) | 0.93 (0.91 to 0.95) | 0.98 (0.98 to 0.99) |
| RUSSIAN FEDERATION | 0.99 (0.98 to 0.99) | 1.00 (0.99 to 1.00) | 1.01 (1.01 to 1.02) | 1.01 (1.02 to 1.02) |

## Learned strengths, `season_r0.001`

exp(a) per season on the full fit (every guest day to 2025-01-31), median over 20 markets with a 90% bootstrap over markets; fold min and max: range of the 7 fold-fit medians.

| season | fold min | fold max | markets above 1 | graph: actual / model slope | median [90% over markets] |
| --- | --- | --- | --- | --- | --- |
| Winter_Peak | 0.93 | 0.98 | 7 | 1.09 | 0.94 [0.91, 1.01] |
| Spring_Shoulder | 0.94 | 1.06 | 11 | 1.05 | 1.04 [0.88, 1.05] |
| Summer_Trough | 0.96 | 1.03 | 11 | 1.84 | 1.04 [0.90, 1.29] |
| Autumn_Shoulder | 1.16 | 1.21 | 15 | 0.35 | 1.08 [1.02, 1.27] |

By month (mid-month value, full fit):

| month | median [90%] |
| --- | --- |
| Jan | 0.94 [0.91, 1.01] |
| Feb | 0.94 [0.91, 1.01] |
| Mar | 0.94 [0.91, 1.01] |
| Apr | 1.04 [0.88, 1.05] |
| May | 1.04 [0.88, 1.05] |
| Jun | 1.04 [0.90, 1.29] |
| Jul | 1.04 [0.90, 1.29] |
| Aug | 1.04 [0.90, 1.29] |
| Sep | 1.08 [1.02, 1.27] |
| Oct | 1.08 [1.02, 1.27] |
| Nov | 0.94 [0.91, 1.01] |
| Dec | 0.94 [0.91, 1.01] |

Six largest markets, full fit (min to max over the 7 fold fits):

| market | Winter_Peak | Spring_Shoulder | Summer_Trough | Autumn_Shoulder |
| --- | --- | --- | --- | --- |
| UNITED KINGDOM | 0.68 (0.60 to 0.73) | 1.72 (1.56 to 2.13) | 1.07 (0.94 to 1.28) | 1.47 (1.40 to 1.67) |
| INDIA | 1.34 (1.13 to 1.36) | 0.74 (0.62 to 0.82) | 0.68 (0.63 to 0.71) | 1.09 (1.40 to 1.47) |
| CHINA | 0.91 (1.27 to 2.01) | 1.44 (0.85 to 1.47) | 1.01 (0.38 to 0.61) | 0.90 (0.69 to 0.85) |
| GERMANY | 0.95 (0.92 to 0.99) | 1.04 (0.87 to 1.03) | 0.91 (0.88 to 1.06) | 1.29 (1.30 to 1.38) |
| SAUDI ARABIA | 1.42 (1.21 to 1.34) | 1.04 (1.12 to 1.39) | 0.62 (0.51 to 0.71) | 0.77 (0.72 to 0.82) |
| RUSSIAN FEDERATION | 0.84 (0.78 to 0.84) | 0.85 (0.81 to 0.89) | 1.26 (1.31 to 1.41) | 1.33 (1.52 to 1.68) |

## Natural-experiment back-test

Lever code from experiment/scenario_response. MAE and bias on log guest change; paired differences use a 4-week moving-block bootstrap, 90%. Season of the week's Thursday.

### Against the same week a year earlier

| model | part | n | MAE | bias | slope actual | slope predicted | slope seat-only |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TIME-ONLY | all | 717 | 0.276 | -0.059 | 0.081 | -0.017 | 0.000 |
| TIME-ONLY | increases | 624 | 0.240 | -0.041 | 0.190 | -0.017 | 0.000 |
| TIME-ONLY | cuts | 93 | 0.515 | -0.180 | -0.271 | -0.017 | 0.000 |
| TIME-ONLY | Winter_Peak | 262 | 0.327 | 0.001 | 0.213 | -0.025 | 0.000 |
| TIME-ONLY | Spring_Shoulder | 139 | 0.290 | -0.142 | 0.009 | 0.000 | 0.000 |
| TIME-ONLY | Summer_Trough | 193 | 0.219 | -0.103 | -0.127 | -0.007 | 0.000 |
| TIME-ONLY | Autumn_Shoulder | 123 | 0.240 | -0.022 | -0.154 | -0.027 | 0.000 |
| CHAIN | all | 717 | 0.210 | -0.024 | 0.081 | 0.147 | 0.474 |
| CHAIN | increases | 624 | 0.186 | -0.002 | 0.190 | 0.199 | 0.411 |
| CHAIN | cuts | 93 | 0.373 | -0.169 | -0.271 | -0.019 | 0.680 |
| CHAIN | Winter_Peak | 262 | 0.239 | 0.022 | 0.213 | 0.269 | 0.546 |
| CHAIN | Spring_Shoulder | 139 | 0.195 | 0.018 | 0.009 | 0.086 | 0.418 |
| CHAIN | Summer_Trough | 193 | 0.166 | -0.084 | -0.127 | -0.067 | 0.366 |
| CHAIN | Autumn_Shoulder | 123 | 0.235 | -0.073 | -0.154 | -0.037 | 0.374 |
| SEASONAL fourier1_r0.001 | all | 717 | 0.211 | -0.027 | 0.081 | 0.128 | 0.476 |
| SEASONAL fourier1_r0.001 | increases | 624 | 0.188 | -0.006 | 0.190 | 0.176 | 0.416 |
| SEASONAL fourier1_r0.001 | cuts | 93 | 0.369 | -0.173 | -0.271 | -0.029 | 0.670 |
| SEASONAL fourier1_r0.001 | Winter_Peak | 262 | 0.237 | 0.014 | 0.213 | 0.226 | 0.523 |
| SEASONAL fourier1_r0.001 | Spring_Shoulder | 139 | 0.192 | 0.021 | 0.009 | 0.078 | 0.460 |
| SEASONAL fourier1_r0.001 | Summer_Trough | 193 | 0.169 | -0.086 | -0.127 | -0.057 | 0.393 |
| SEASONAL fourier1_r0.001 | Autumn_Shoulder | 123 | 0.243 | -0.080 | -0.154 | 0.005 | 0.383 |
| SEASONAL season_r0.1 | all | 717 | 0.211 | -0.021 | 0.081 | 0.155 | 0.499 |
| SEASONAL season_r0.1 | increases | 624 | 0.187 | 0.002 | 0.190 | 0.207 | 0.442 |
| SEASONAL season_r0.1 | cuts | 93 | 0.372 | -0.173 | -0.271 | -0.015 | 0.685 |
| SEASONAL season_r0.1 | Winter_Peak | 262 | 0.240 | 0.025 | 0.213 | 0.275 | 0.565 |
| SEASONAL season_r0.1 | Spring_Shoulder | 139 | 0.197 | 0.022 | 0.009 | 0.091 | 0.446 |
| SEASONAL season_r0.1 | Summer_Trough | 193 | 0.167 | -0.081 | -0.127 | -0.057 | 0.400 |
| SEASONAL season_r0.1 | Autumn_Shoulder | 123 | 0.236 | -0.071 | -0.154 | -0.020 | 0.414 |
| SEASONAL season_r0.001 | all | 717 | 0.214 | -0.016 | 0.081 | 0.191 | 0.609 |
| SEASONAL season_r0.001 | increases | 624 | 0.188 | 0.013 | 0.190 | 0.245 | 0.575 |
| SEASONAL season_r0.001 | cuts | 93 | 0.387 | -0.213 | -0.271 | 0.016 | 0.721 |
| SEASONAL season_r0.001 | Winter_Peak | 262 | 0.238 | 0.012 | 0.213 | 0.293 | 0.616 |
| SEASONAL season_r0.001 | Spring_Shoulder | 139 | 0.209 | 0.041 | 0.009 | 0.122 | 0.577 |
| SEASONAL season_r0.001 | Summer_Trough | 193 | 0.166 | -0.070 | -0.127 | 0.011 | 0.614 |
| SEASONAL season_r0.001 | Autumn_Shoulder | 123 | 0.241 | -0.057 | -0.154 | 0.078 | 0.628 |

Paired MAE differences:

| comparison | part | n | MAE diff [90% CI] |
| --- | --- | --- | --- |
| SEASONAL fourier1_r0.001 - CHAIN | all | 717 | +0.0010 [-0.0026, +0.0052] |
| SEASONAL fourier1_r0.001 - CHAIN | increases | 624 | +0.0018 [-0.0015, +0.0069] |
| SEASONAL fourier1_r0.001 - CHAIN | cuts | 93 | -0.0042 [-0.0219, +0.0197] |
| SEASONAL fourier1_r0.001 - CHAIN | Winter_Peak | 262 | -0.0013 [-0.0107, +0.0090] |
| SEASONAL fourier1_r0.001 - CHAIN | Spring_Shoulder | 139 | -0.0031 [-0.0066, -0.0006] |
| SEASONAL fourier1_r0.001 - CHAIN | Summer_Trough | 193 | +0.0029 [+0.0007, +0.0033] |
| SEASONAL fourier1_r0.001 - CHAIN | Autumn_Shoulder | 123 | +0.0076 [+0.0035, +0.0111] |
| SEASONAL season_r0.1 - CHAIN | all | 717 | +0.0010 [+0.0006, +0.0016] |
| SEASONAL season_r0.1 - CHAIN | increases | 624 | +0.0012 [+0.0005, +0.0021] |
| SEASONAL season_r0.1 - CHAIN | cuts | 93 | -0.0004 [-0.0019, +0.0014] |
| SEASONAL season_r0.1 - CHAIN | Winter_Peak | 262 | +0.0015 [+0.0005, +0.0030] |
| SEASONAL season_r0.1 - CHAIN | Spring_Shoulder | 139 | +0.0015 [+0.0004, +0.0018] |
| SEASONAL season_r0.1 - CHAIN | Summer_Trough | 193 | +0.0002 [-0.0001, +0.0008] |
| SEASONAL season_r0.1 - CHAIN | Autumn_Shoulder | 123 | +0.0006 [-0.0006, +0.0008] |
| SEASONAL season_r0.001 - CHAIN | all | 717 | +0.0034 [-0.0017, +0.0095] |
| SEASONAL season_r0.001 - CHAIN | increases | 624 | +0.0019 [-0.0029, +0.0076] |
| SEASONAL season_r0.001 - CHAIN | cuts | 93 | +0.0137 [-0.0065, +0.0318] |
| SEASONAL season_r0.001 - CHAIN | Winter_Peak | 262 | -0.0003 [-0.0128, +0.0155] |
| SEASONAL season_r0.001 - CHAIN | Spring_Shoulder | 139 | +0.0134 [+0.0065, +0.0179] |
| SEASONAL season_r0.001 - CHAIN | Summer_Trough | 193 | +0.0000 [-0.0026, +0.0039] |
| SEASONAL season_r0.001 - CHAIN | Autumn_Shoulder | 123 | +0.0056 [-0.0075, +0.0100] |
| CHAIN - TIME-ONLY | all | 717 | -0.0657 [-0.0927, -0.0428] |
| CHAIN - TIME-ONLY | increases | 624 | -0.0543 [-0.0835, -0.0299] |
| CHAIN - TIME-ONLY | cuts | 93 | -0.1422 [-0.2583, -0.0803] |
| CHAIN - TIME-ONLY | Winter_Peak | 262 | -0.0885 [-0.1396, -0.0525] |
| CHAIN - TIME-ONLY | Spring_Shoulder | 139 | -0.0950 [-0.1506, -0.0610] |
| CHAIN - TIME-ONLY | Summer_Trough | 193 | -0.0523 [-0.0853, -0.0261] |
| CHAIN - TIME-ONLY | Autumn_Shoulder | 123 | -0.0050 [-0.0094, +0.0150] |
| SEASONAL fourier1_r0.001 - TIME-ONLY | all | 717 | -0.0647 [-0.0921, -0.0406] |
| SEASONAL fourier1_r0.001 - TIME-ONLY | increases | 624 | -0.0525 [-0.0793, -0.0297] |
| SEASONAL fourier1_r0.001 - TIME-ONLY | cuts | 93 | -0.1465 [-0.2591, -0.0782] |
| SEASONAL fourier1_r0.001 - TIME-ONLY | Winter_Peak | 262 | -0.0898 [-0.1436, -0.0524] |
| SEASONAL fourier1_r0.001 - TIME-ONLY | Spring_Shoulder | 139 | -0.0981 [-0.1517, -0.0647] |
| SEASONAL fourier1_r0.001 - TIME-ONLY | Summer_Trough | 193 | -0.0494 [-0.0830, -0.0247] |
| SEASONAL fourier1_r0.001 - TIME-ONLY | Autumn_Shoulder | 123 | +0.0026 [-0.0010, +0.0223] |
| SEASONAL season_r0.1 - TIME-ONLY | all | 717 | -0.0647 [-0.0912, -0.0421] |
| SEASONAL season_r0.1 - TIME-ONLY | increases | 624 | -0.0531 [-0.0816, -0.0292] |
| SEASONAL season_r0.1 - TIME-ONLY | cuts | 93 | -0.1427 [-0.2592, -0.0804] |
| SEASONAL season_r0.1 - TIME-ONLY | Winter_Peak | 262 | -0.0870 [-0.1369, -0.0520] |
| SEASONAL season_r0.1 - TIME-ONLY | Spring_Shoulder | 139 | -0.0935 [-0.1490, -0.0599] |
| SEASONAL season_r0.1 - TIME-ONLY | Summer_Trough | 193 | -0.0521 [-0.0848, -0.0259] |
| SEASONAL season_r0.1 - TIME-ONLY | Autumn_Shoulder | 123 | -0.0044 [-0.0086, +0.0144] |
| SEASONAL season_r0.001 - TIME-ONLY | all | 717 | -0.0623 [-0.0861, -0.0414] |
| SEASONAL season_r0.001 - TIME-ONLY | increases | 624 | -0.0524 [-0.0796, -0.0281] |
| SEASONAL season_r0.001 - TIME-ONLY | cuts | 93 | -0.1285 [-0.2533, -0.0613] |
| SEASONAL season_r0.001 - TIME-ONLY | Winter_Peak | 262 | -0.0888 [-0.1278, -0.0612] |
| SEASONAL season_r0.001 - TIME-ONLY | Spring_Shoulder | 139 | -0.0816 [-0.1342, -0.0508] |
| SEASONAL season_r0.001 - TIME-ONLY | Summer_Trough | 193 | -0.0523 [-0.0838, -0.0262] |
| SEASONAL season_r0.001 - TIME-ONLY | Autumn_Shoulder | 123 | +0.0005 [-0.0031, +0.0142] |

### Against the centred 13-week trend

| model | part | n | MAE | bias | slope actual | slope predicted | slope seat-only |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TIME-ONLY | all | 48 | 0.395 | 0.091 | 0.991 | 0.351 | 0.000 |
| TIME-ONLY | increases | 16 | 0.341 | -0.143 | 0.671 | 0.216 | 0.000 |
| TIME-ONLY | cuts | 32 | 0.422 | 0.208 | 1.123 | 0.407 | 0.000 |
| TIME-ONLY | Winter_Peak | 21 | 0.523 | 0.203 | 1.928 | 0.549 | 0.000 |
| TIME-ONLY | Spring_Shoulder | 9 | 0.346 | -0.013 | 1.266 | 0.178 | 0.000 |
| TIME-ONLY | Summer_Trough | 5 | 0.177 | -0.058 | 0.503 | 0.182 | 0.000 |
| TIME-ONLY | Autumn_Shoulder | 13 | 0.307 | 0.041 | -0.188 | 0.208 | 0.000 |
| CHAIN | all | 48 | 0.368 | -0.080 | 0.991 | 1.412 | 0.502 |
| CHAIN | increases | 16 | 0.364 | -0.014 | 0.671 | 0.803 | 0.480 |
| CHAIN | cuts | 32 | 0.371 | -0.113 | 1.123 | 1.663 | 0.511 |
| CHAIN | Winter_Peak | 21 | 0.348 | -0.050 | 1.928 | 1.551 | 0.564 |
| CHAIN | Spring_Shoulder | 9 | 0.245 | 0.058 | 1.266 | 0.936 | 0.358 |
| CHAIN | Summer_Trough | 5 | 0.189 | -0.118 | 0.503 | -0.073 | 0.295 |
| CHAIN | Autumn_Shoulder | 13 | 0.555 | -0.210 | -0.188 | 1.604 | 0.510 |
| SEASONAL fourier1_r0.001 | all | 48 | 0.382 | -0.092 | 0.991 | 1.467 | 0.514 |
| SEASONAL fourier1_r0.001 | increases | 16 | 0.359 | -0.014 | 0.671 | 0.804 | 0.497 |
| SEASONAL fourier1_r0.001 | cuts | 32 | 0.393 | -0.132 | 1.123 | 1.739 | 0.522 |
| SEASONAL fourier1_r0.001 | Winter_Peak | 21 | 0.365 | -0.059 | 1.928 | 1.582 | 0.546 |
| SEASONAL fourier1_r0.001 | Spring_Shoulder | 9 | 0.248 | 0.063 | 1.266 | 0.970 | 0.374 |
| SEASONAL fourier1_r0.001 | Summer_Trough | 5 | 0.176 | -0.113 | 0.503 | -0.078 | 0.352 |
| SEASONAL fourier1_r0.001 | Autumn_Shoulder | 13 | 0.580 | -0.245 | -0.188 | 1.703 | 0.553 |
| SEASONAL season_r0.1 | all | 48 | 0.370 | -0.081 | 0.991 | 1.422 | 0.510 |
| SEASONAL season_r0.1 | increases | 16 | 0.364 | -0.012 | 0.671 | 0.811 | 0.487 |
| SEASONAL season_r0.1 | cuts | 32 | 0.372 | -0.116 | 1.123 | 1.673 | 0.519 |
| SEASONAL season_r0.1 | Winter_Peak | 21 | 0.350 | -0.053 | 1.928 | 1.561 | 0.569 |
| SEASONAL season_r0.1 | Spring_Shoulder | 9 | 0.248 | 0.060 | 1.266 | 0.940 | 0.364 |
| SEASONAL season_r0.1 | Summer_Trough | 5 | 0.186 | -0.117 | 0.503 | -0.057 | 0.317 |
| SEASONAL season_r0.1 | Autumn_Shoulder | 13 | 0.556 | -0.212 | -0.188 | 1.615 | 0.522 |
| SEASONAL season_r0.001 | all | 48 | 0.361 | -0.085 | 0.991 | 1.468 | 0.539 |
| SEASONAL season_r0.001 | increases | 16 | 0.347 | 0.015 | 0.671 | 0.879 | 0.522 |
| SEASONAL season_r0.001 | cuts | 32 | 0.368 | -0.134 | 1.123 | 1.710 | 0.546 |
| SEASONAL season_r0.001 | Winter_Peak | 21 | 0.327 | -0.078 | 1.928 | 1.665 | 0.597 |
| SEASONAL season_r0.001 | Spring_Shoulder | 9 | 0.262 | 0.066 | 1.266 | 0.989 | 0.395 |
| SEASONAL season_r0.001 | Summer_Trough | 5 | 0.166 | -0.080 | 0.503 | 0.228 | 0.421 |
| SEASONAL season_r0.001 | Autumn_Shoulder | 13 | 0.559 | -0.200 | -0.188 | 1.566 | 0.543 |

Paired MAE differences:

| comparison | part | n | MAE diff [90% CI] |
| --- | --- | --- | --- |
| SEASONAL fourier1_r0.001 - CHAIN | all | 48 | +0.0135 [+0.0002, +0.0244] |
| SEASONAL fourier1_r0.001 - CHAIN | increases | 16 | -0.0042 [-0.0102, +0.0005] |
| SEASONAL fourier1_r0.001 - CHAIN | cuts | 32 | +0.0223 [+0.0053, +0.0417] |
| SEASONAL fourier1_r0.001 - CHAIN | Winter_Peak | 21 | +0.0170 [+0.0004, +0.0296] |
| SEASONAL fourier1_r0.001 - CHAIN | Spring_Shoulder | 9 | +0.0028 [-0.0024, +0.0091] |
| SEASONAL fourier1_r0.001 - CHAIN | Summer_Trough | 5 | -0.0131 [-0.0131, -0.0131] |
| SEASONAL fourier1_r0.001 - CHAIN | Autumn_Shoulder | 13 | +0.0254 [-0.0034, +0.0546] |
| SEASONAL season_r0.1 - CHAIN | all | 48 | +0.0013 [-0.0001, +0.0032] |
| SEASONAL season_r0.1 - CHAIN | increases | 16 | +0.0004 [-0.0009, +0.0032] |
| SEASONAL season_r0.1 - CHAIN | cuts | 32 | +0.0018 [+0.0003, +0.0040] |
| SEASONAL season_r0.1 - CHAIN | Winter_Peak | 21 | +0.0015 [-0.0008, +0.0048] |
| SEASONAL season_r0.1 - CHAIN | Spring_Shoulder | 9 | +0.0029 [+0.0015, +0.0044] |
| SEASONAL season_r0.1 - CHAIN | Summer_Trough | 5 | -0.0031 [-0.0031, -0.0031] |
| SEASONAL season_r0.1 - CHAIN | Autumn_Shoulder | 13 | +0.0017 [+0.0007, +0.0046] |
| SEASONAL season_r0.001 - CHAIN | all | 48 | -0.0075 [-0.0206, +0.0051] |
| SEASONAL season_r0.001 - CHAIN | increases | 16 | -0.0170 [-0.0262, +0.0018] |
| SEASONAL season_r0.001 - CHAIN | cuts | 32 | -0.0028 [-0.0223, +0.0142] |
| SEASONAL season_r0.001 - CHAIN | Winter_Peak | 21 | -0.0215 [-0.0594, +0.0002] |
| SEASONAL season_r0.001 - CHAIN | Spring_Shoulder | 9 | +0.0170 [+0.0064, +0.0170] |
| SEASONAL season_r0.001 - CHAIN | Summer_Trough | 5 | -0.0236 [-0.0236, -0.0236] |
| SEASONAL season_r0.001 - CHAIN | Autumn_Shoulder | 13 | +0.0043 [-0.0206, +0.0307] |
| CHAIN - TIME-ONLY | all | 48 | -0.0271 [-0.1331, +0.1134] |
| CHAIN - TIME-ONLY | increases | 16 | +0.0226 [-0.0757, +0.1355] |
| CHAIN - TIME-ONLY | cuts | 32 | -0.0519 [-0.2013, +0.1749] |
| CHAIN - TIME-ONLY | Winter_Peak | 21 | -0.1747 [-0.2836, +0.0139] |
| CHAIN - TIME-ONLY | Spring_Shoulder | 9 | -0.1008 [-0.1267, -0.0211] |
| CHAIN - TIME-ONLY | Summer_Trough | 5 | +0.0126 [+0.0126, +0.0126] |
| CHAIN - TIME-ONLY | Autumn_Shoulder | 13 | +0.2473 [+0.1284, +0.4195] |
| SEASONAL fourier1_r0.001 - TIME-ONLY | all | 48 | -0.0136 [-0.1266, +0.1299] |
| SEASONAL fourier1_r0.001 - TIME-ONLY | increases | 16 | +0.0183 [-0.0778, +0.1266] |
| SEASONAL fourier1_r0.001 - TIME-ONLY | cuts | 32 | -0.0296 [-0.1910, +0.2125] |
| SEASONAL fourier1_r0.001 - TIME-ONLY | Winter_Peak | 21 | -0.1577 [-0.2776, +0.0260] |
| SEASONAL fourier1_r0.001 - TIME-ONLY | Spring_Shoulder | 9 | -0.0980 [-0.1291, -0.0120] |
| SEASONAL fourier1_r0.001 - TIME-ONLY | Summer_Trough | 5 | -0.0005 [-0.0005, -0.0005] |
| SEASONAL fourier1_r0.001 - TIME-ONLY | Autumn_Shoulder | 13 | +0.2727 [+0.1292, +0.4752] |
| SEASONAL season_r0.1 - TIME-ONLY | all | 48 | -0.0257 [-0.1312, +0.1144] |
| SEASONAL season_r0.1 - TIME-ONLY | increases | 16 | +0.0230 [-0.0725, +0.1350] |
| SEASONAL season_r0.1 - TIME-ONLY | cuts | 32 | -0.0501 [-0.1973, +0.1770] |
| SEASONAL season_r0.1 - TIME-ONLY | Winter_Peak | 21 | -0.1732 [-0.2788, +0.0140] |
| SEASONAL season_r0.1 - TIME-ONLY | Spring_Shoulder | 9 | -0.0980 [-0.1224, -0.0192] |
| SEASONAL season_r0.1 - TIME-ONLY | Summer_Trough | 5 | +0.0095 [+0.0095, +0.0095] |
| SEASONAL season_r0.1 - TIME-ONLY | Autumn_Shoulder | 13 | +0.2490 [+0.1320, +0.4212] |
| SEASONAL season_r0.001 - TIME-ONLY | all | 48 | -0.0346 [-0.1396, +0.1042] |
| SEASONAL season_r0.001 - TIME-ONLY | increases | 16 | +0.0056 [-0.0731, +0.1130] |
| SEASONAL season_r0.001 - TIME-ONLY | cuts | 32 | -0.0547 [-0.2046, +0.1726] |
| SEASONAL season_r0.001 - TIME-ONLY | Winter_Peak | 21 | -0.1963 [-0.3040, -0.0313] |
| SEASONAL season_r0.001 - TIME-ONLY | Spring_Shoulder | 9 | -0.0838 [-0.1152, -0.0048] |
| SEASONAL season_r0.001 - TIME-ONLY | Summer_Trough | 5 | -0.0110 [-0.0110, -0.0110] |
| SEASONAL season_r0.001 - TIME-ONLY | Autumn_Shoulder | 13 | +0.2515 [+0.1562, +0.4022] |
