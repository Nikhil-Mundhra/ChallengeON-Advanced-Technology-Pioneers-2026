# Scenario response: results

Aggregates only. International markets, VALIDATION_ORIGINS (7 folds, test weeks 2024-02-01 to 2025-01-31). Every model refitted per fold on weeks before the fold's train_end. FROZEN_TEST is not read.

## Checks

| check | value |
| --- | --- |
| refit calibration vs shipped structural_calibration.json (max relative gap) | 0.00e+00 |
| refit residual season means vs shipped residual_engine.pkl (max relative gap) | 1.75e-12 |
| flagged scenario copy, all on, vs shipped _international_scenario (max gap / base guests) | 0.00e+00 |

## SHORT-RUN ridge (chosen on VALIDATION_ORIGINS)

MAE of log(guests / centred guest trend) - beta x log(seats / centred seat trend) on every test week.

| ridge | MAE |
| --- | --- |
| 0.00000 | 0.20313 |
| 0.01000 | 0.20302 |
| 0.03000 | 0.20320 |
| 0.10000 | 0.20361 |
| 0.30000 | 0.20480 |
| 1.00000 | 0.20584 |
| 3.00000 | 0.20608 |
| 10.00000 | 0.20598 |
| 100.00000 | 0.20586 |

Chosen ridge: 0.01.

## Natural experiments against the same week a year earlier

MAE and bias on log guest change; slopes against log seat change (through 0); 'actual on predicted' is the slope of the actual change on the predicted one (1 is calibrated). Unique market-weeks.

| model | part | n | MAE | bias | slope actual | slope predicted | slope seat-only | actual on predicted |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TIME-ONLY | all | 717 | 0.276 | -0.059 | 0.081 | -0.016 | 0.000 | 0.210 |
| TIME-ONLY | increases | 624 | 0.240 | -0.040 | 0.190 | -0.016 | 0.000 | 0.256 |
| TIME-ONLY | cuts | 93 | 0.515 | -0.180 | -0.271 | -0.017 | 0.000 | -0.343 |
| HYBRID | all | 717 | 0.287 | -0.018 | 0.081 | 0.351 | 1.026 | 0.532 |
| HYBRID | increases | 624 | 0.227 | 0.062 | 0.190 | 0.361 | 1.034 | 0.684 |
| HYBRID | cuts | 93 | 0.686 | -0.551 | -0.271 | 0.316 | 1.000 | 0.549 |
| LINEAR | all | 717 | 0.277 | -0.008 | 0.081 | 0.274 | 0.902 | 0.522 |
| LINEAR | increases | 624 | 0.234 | 0.045 | 0.190 | 0.383 | 1.013 | 0.544 |
| LINEAR | cuts | 93 | 0.572 | -0.360 | -0.271 | -0.082 | 0.541 | 0.601 |
| S-CURVE | all | 717 | 0.260 | -0.061 | 0.081 | 0.099 | 0.672 | 0.636 |
| S-CURVE | increases | 624 | 0.213 | -0.016 | 0.190 | 0.154 | 0.703 | 0.692 |
| S-CURVE | cuts | 93 | 0.571 | -0.364 | -0.271 | -0.078 | 0.570 | 0.612 |
| S-CURVE % | all | 717 | 0.256 | -0.068 | 0.081 | 0.071 | 0.634 | 0.654 |
| S-CURVE % | increases | 624 | 0.214 | -0.030 | 0.190 | 0.126 | 0.662 | 0.691 |
| S-CURVE % | cuts | 93 | 0.542 | -0.326 | -0.271 | -0.109 | 0.541 | 0.635 |
| SHORT-RUN | all | 717 | 0.342 | -0.112 | 0.081 | 0.140 | 0.684 | 0.469 |
| SHORT-RUN | increases | 624 | 0.310 | -0.052 | 0.190 | 0.055 | 0.501 | 0.435 |
| SHORT-RUN | cuts | 93 | 0.557 | -0.512 | -0.271 | 0.418 | 1.280 | 0.830 |
| CHAIN | all | 717 | 0.210 | -0.024 | 0.081 | 0.148 | 0.474 | 0.877 |
| CHAIN | increases | 624 | 0.186 | -0.002 | 0.190 | 0.199 | 0.410 | 0.827 |
| CHAIN | cuts | 93 | 0.373 | -0.169 | -0.271 | -0.018 | 0.680 | 1.174 |

### Paired differences (block bootstrap, 4-week blocks, 90%)

| comparison | part | n | MAE diff [90% CI] | slope diff [90% CI] |
| --- | --- | --- | --- | --- |
| S-CURVE - LINEAR | all | 717 | -0.0176 [-0.0315, -0.0033] | -0.174 [-0.233, -0.108] |
| S-CURVE - LINEAR | increases | 624 | -0.0202 [-0.0370, -0.0046] | -0.229 [-0.297, -0.143] |
| S-CURVE - LINEAR | cuts | 93 | -0.0004 [-0.0100, +0.0167] | +0.004 [-0.006, +0.027] |
| S-CURVE % - LINEAR | all | 717 | -0.0211 [-0.0377, -0.0054] | -0.203 [-0.264, -0.137] |
| S-CURVE % - LINEAR | increases | 624 | -0.0198 [-0.0374, -0.0041] | -0.258 [-0.324, -0.174] |
| S-CURVE % - LINEAR | cuts | 93 | -0.0299 [-0.0403, -0.0122] | -0.026 [-0.061, -0.008] |
| SHORT-RUN - LINEAR | all | 717 | +0.0646 [+0.0458, +0.0785] | -0.134 [-0.303, -0.030] |
| SHORT-RUN - LINEAR | increases | 624 | +0.0764 [+0.0604, +0.0942] | -0.329 [-0.453, -0.245] |
| SHORT-RUN - LINEAR | cuts | 93 | -0.0146 [-0.1065, +0.0162] | +0.500 [+0.043, +0.650] |
| CHAIN - LINEAR | all | 717 | -0.0673 [-0.0949, -0.0434] | -0.126 [-0.321, +0.010] |
| CHAIN - LINEAR | increases | 624 | -0.0478 [-0.0696, -0.0285] | -0.184 [-0.360, -0.039] |
| CHAIN - LINEAR | cuts | 93 | -0.1982 [-0.3156, -0.0918] | +0.064 [-0.459, +0.272] |
| LINEAR - TIME-ONLY | all | 717 | +0.0016 [-0.0176, +0.0179] | +0.290 [+0.003, +0.616] |
| LINEAR - TIME-ONLY | increases | 624 | -0.0065 [-0.0298, +0.0102] | +0.400 [+0.090, +0.693] |
| LINEAR - TIME-ONLY | cuts | 93 | +0.0566 [-0.1061, +0.1913] | -0.065 [-0.361, +0.474] |
| S-CURVE - TIME-ONLY | all | 717 | -0.0160 [-0.0359, +0.0021] | +0.116 [-0.112, +0.394] |
| S-CURVE - TIME-ONLY | increases | 624 | -0.0267 [-0.0569, -0.0027] | +0.170 [-0.053, +0.405] |
| S-CURVE - TIME-ONLY | cuts | 93 | +0.0562 [-0.0970, +0.1911] | -0.061 [-0.347, +0.479] |
| SHORT-RUN - TIME-ONLY | all | 717 | +0.0663 [+0.0433, +0.0838] | +0.157 [-0.110, +0.395] |
| SHORT-RUN - TIME-ONLY | increases | 624 | +0.0699 [+0.0516, +0.0853] | +0.071 [-0.191, +0.322] |
| SHORT-RUN - TIME-ONLY | cuts | 93 | +0.0420 [-0.1801, +0.1670] | +0.435 [+0.002, +0.719] |
| CHAIN - TIME-ONLY | all | 717 | -0.0656 [-0.0926, -0.0427] | +0.165 [-0.013, +0.329] |
| CHAIN - TIME-ONLY | increases | 624 | -0.0543 [-0.0835, -0.0299] | +0.216 [+0.005, +0.390] |
| CHAIN - TIME-ONLY | cuts | 93 | -0.1417 [-0.2582, -0.0796] | -0.001 [-0.261, +0.159] |

### Levels on the same weeks

| model | n | baseline WAPE | scenario WAPE | scenario level bias (pct) |
| --- | --- | --- | --- | --- |
| TIME-ONLY | 717 | 30.62 | 30.62 | -24.09 |
| HYBRID | 717 | 30.50 | 26.89 | 2.19 |
| LINEAR | 717 | 30.50 | 25.50 | -1.33 |
| S-CURVE | 717 | 30.50 | 23.52 | -8.70 |
| S-CURVE % | 717 | 30.50 | 23.34 | -10.14 |
| SHORT-RUN | 717 | 30.50 | 34.47 | -12.10 |
| CHAIN | 717 | 22.79 | 19.98 | -5.02 |

compare() on scenario-week guest levels (per-fold rows, 28-day blocks):

| candidate - baseline | WAPE diff pp [90% CI] | folds same sign |
| --- | --- | --- |
| HYBRID - TIME-ONLY | -3.66 [-6.26, -0.42] | 0.71 |
| LINEAR - TIME-ONLY | -5.52 [-7.42, -3.31] | 1.00 |
| S-CURVE - TIME-ONLY | -6.74 [-8.09, -5.00] | 1.00 |
| S-CURVE % - TIME-ONLY | -6.88 [-8.02, -5.35] | 1.00 |
| SHORT-RUN - TIME-ONLY | +3.68 [+1.44, +5.92] | 0.71 |
| CHAIN - TIME-ONLY | -9.95 [-11.70, -7.91] | 1.00 |
| S-CURVE - LINEAR | -1.22 [-2.01, -0.37] | 1.00 |
| S-CURVE % - LINEAR | -1.35 [-2.27, -0.35] | 1.00 |
| SHORT-RUN - LINEAR | +9.20 [+7.60, +10.65] | 1.00 |
| CHAIN - LINEAR | -4.43 [-5.83, -3.17] | 1.00 |

### Per market (all event weeks)

| market | n | up | slope actual | TIME-ONLY slope | HYBRID slope | LINEAR slope | S-CURVE slope | S-CURVE % slope | SHORT-RUN slope | CHAIN slope | TIME-ONLY MAE | HYBRID MAE | LINEAR MAE | S-CURVE MAE | S-CURVE % MAE | SHORT-RUN MAE | CHAIN MAE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CHINA | 43 | 30 | -0.17 | -0.00 | 0.44 | -0.27 | -0.31 | -0.31 | -0.20 | -0.03 | 0.28 | 0.49 | 0.23 | 0.23 | 0.23 | 0.33 | 0.27 |
| EGYPT | 40 | 39 | 0.03 | -0.01 | -0.19 | -0.15 | -0.32 | -0.34 | -0.27 | -0.03 | 0.12 | 0.18 | 0.19 | 0.21 | 0.21 | 0.21 | 0.09 |
| FRANCE | 49 | 38 | 0.03 | -0.01 | 0.17 | 0.07 | -0.05 | -0.10 | -0.16 | -0.02 | 0.16 | 0.30 | 0.27 | 0.29 | 0.27 | 0.24 | 0.12 |
| GERMANY | 30 | 28 | 1.16 | -0.01 | 0.92 | 1.05 | 0.86 | 0.72 | 1.44 | 0.82 | 0.41 | 0.17 | 0.16 | 0.18 | 0.20 | 0.20 | 0.17 |
| INDIA | 49 | 49 | 0.16 | -0.01 | -0.08 | -0.07 | -0.16 | -0.16 | -1.03 | -0.28 | 0.15 | 0.16 | 0.16 | 0.17 | 0.17 | 0.33 | 0.18 |
| ISRAEL | 49 | 13 | 0.20 | -0.03 | 0.46 | 0.62 | 0.33 | 0.32 | 0.67 | 0.40 | 1.07 | 0.59 | 0.87 | 0.70 | 0.68 | 0.77 | 0.56 |
| ITALY | 24 | 24 | -0.07 | -0.08 | 0.04 | 0.08 | -0.05 | -0.12 | -0.36 | -0.01 | 0.15 | 0.16 | 0.16 | 0.16 | 0.16 | 0.19 | 0.12 |
| KAZAKHSTAN | 45 | 45 | -0.17 | -0.04 | -0.15 | -0.12 | -0.30 | -0.33 | -0.78 | -0.14 | 0.23 | 0.22 | 0.22 | 0.21 | 0.22 | 0.41 | 0.24 |
| KUWAIT | 28 | 15 | 0.71 | 0.02 | 1.35 | 1.24 | 1.19 | 1.05 | 2.77 | 0.56 | 0.44 | 0.42 | 0.41 | 0.40 | 0.38 | 0.54 | 0.25 |
| OMAN | 49 | 32 | 0.14 | -0.01 | 0.59 | 0.61 | 0.35 | 0.31 | -0.00 | 0.04 | 0.34 | 0.44 | 0.44 | 0.40 | 0.39 | 0.42 | 0.28 |
| OTHER_AMERICAS_AFRICA | 24 | 24 | 0.49 | 0.01 | 1.08 | 0.21 | 0.17 | 0.17 | 0.40 | 0.43 | 0.15 | 0.16 | 0.11 | 0.11 | 0.11 | 0.09 | 0.07 |
| OTHER_ASIA_PACIFIC | 42 | 42 | 0.07 | -0.00 | 0.18 | -0.05 | -0.08 | -0.12 | -0.25 | -0.01 | 0.12 | 0.13 | 0.10 | 0.10 | 0.11 | 0.15 | 0.09 |
| OTHER_EURASIA | 27 | 27 | 0.23 | 0.01 | -0.27 | -0.22 | -0.33 | -0.35 | -0.54 | -0.18 | 0.17 | 0.25 | 0.25 | 0.25 | 0.25 | 0.30 | 0.22 |
| OTHER_EUROPE | 18 | 18 | -0.38 | 0.03 | -0.14 | -0.09 | -0.28 | -0.30 | -0.52 | -0.29 | 0.14 | 0.11 | 0.11 | 0.09 | 0.09 | 0.12 | 0.09 |
| OTHER_MENA | 21 | 21 | 0.36 | 0.04 | 0.87 | 0.89 | 0.71 | 0.71 | 2.93 | 0.87 | 0.19 | 0.17 | 0.17 | 0.16 | 0.16 | 0.50 | 0.17 |
| PHILIPPINES | 15 | 15 | -0.13 | -0.33 | 0.58 | 0.64 | 0.43 | 0.35 | -0.65 | 0.10 | 0.16 | 0.18 | 0.19 | 0.16 | 0.15 | 0.17 | 0.13 |
| RUSSIAN FEDERATION | 42 | 42 | -0.08 | -0.01 | 0.54 | 0.24 | 0.17 | 0.10 | 0.34 | 0.20 | 0.17 | 0.27 | 0.17 | 0.16 | 0.14 | 0.19 | 0.14 |
| SAUDI ARABIA | 50 | 50 | -0.22 | 0.00 | 0.14 | 0.13 | -0.02 | -0.03 | -1.17 | -0.04 | 0.40 | 0.39 | 0.39 | 0.39 | 0.39 | 0.54 | 0.26 |
| UNITED KINGDOM | 29 | 29 | -0.28 | -0.00 | 0.98 | 1.03 | 0.77 | 0.74 | 0.45 | 0.81 | 0.12 | 0.36 | 0.37 | 0.30 | 0.29 | 0.21 | 0.35 |
| UNITED STATES OF AMERICA | 43 | 43 | 0.24 | 0.01 | 0.89 | 0.50 | 0.42 | 0.38 | 2.04 | 0.11 | 0.13 | 0.20 | 0.14 | 0.13 | 0.13 | 0.47 | 0.12 |

## Ordinary weeks (|seat change vs last year| <= 15%)

Weekly guest levels on unique market-weeks; R2 = 1 - SSE / SSE of TIME-ONLY.

| model | n | WAPE | MAE | RMSE | R2 vs TIME-ONLY |
| --- | --- | --- | --- | --- | --- |
| TIME-ONLY | 265 | 25.427 | 2125.400 | 3519.968 | 0.000 |
| HYBRID | 265 | 21.172 | 1769.693 | 3119.949 | 0.214 |
| LINEAR | 265 | 21.423 | 1790.684 | 3138.766 | 0.205 |
| S-CURVE | 265 | 21.295 | 1779.998 | 3116.180 | 0.216 |
| S-CURVE % | 265 | 21.509 | 1797.925 | 3165.821 | 0.191 |
| SHORT-RUN | 265 | 23.212 | 1940.203 | 3347.423 | 0.096 |
| CHAIN | 265 | 16.535 | 1382.135 | 2206.871 | 0.607 |

compare() on the same weeks:

| candidate - baseline | WAPE diff pp [90% CI] | folds same sign |
| --- | --- | --- |
| HYBRID - TIME-ONLY | -3.68 [-5.23, -2.14] | 1.00 |
| LINEAR - TIME-ONLY | -3.43 [-4.86, -2.04] | 1.00 |
| S-CURVE - TIME-ONLY | -3.45 [-4.85, -2.13] | 1.00 |
| S-CURVE % - TIME-ONLY | -3.31 [-4.65, -2.05] | 1.00 |
| SHORT-RUN - TIME-ONLY | -0.70 [-2.75, +1.67] | 0.71 |
| CHAIN - TIME-ONLY | -7.49 [-10.49, -4.11] | 1.00 |
| S-CURVE - LINEAR | -0.02 [-0.24, +0.18] | 0.57 |
| S-CURVE % - LINEAR | +0.12 [-0.13, +0.36] | 0.86 |
| SHORT-RUN - LINEAR | +2.73 [+1.75, +4.26] | 1.00 |
| CHAIN - LINEAR | -4.06 [-6.17, -1.56] | 0.86 |

## Natural experiments against the centred 13-week trend

MAE and bias on log guest change; slopes against log seat change (through 0); 'actual on predicted' is the slope of the actual change on the predicted one (1 is calibrated). Unique market-weeks.

| model | part | n | MAE | bias | slope actual | slope predicted | slope seat-only | actual on predicted |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TIME-ONLY | all | 48 | 0.395 | 0.091 | 0.991 | 0.351 | 0.000 | 0.412 |
| TIME-ONLY | increases | 16 | 0.341 | -0.143 | 0.671 | 0.216 | 0.000 | -1.000 |
| TIME-ONLY | cuts | 32 | 0.422 | 0.208 | 1.123 | 0.407 | 0.000 | 0.196 |
| HYBRID | all | 48 | 0.372 | -0.024 | 0.991 | 1.248 | 1.027 | 0.513 |
| HYBRID | increases | 16 | 0.349 | 0.074 | 0.671 | 1.038 | 0.933 | -0.040 |
| HYBRID | cuts | 32 | 0.383 | -0.072 | 1.123 | 1.334 | 1.065 | 0.106 |
| LINEAR | all | 48 | 0.375 | -0.039 | 0.991 | 1.502 | 1.313 | 0.450 |
| LINEAR | increases | 16 | 0.386 | 0.088 | 0.671 | 1.174 | 1.157 | -0.341 |
| LINEAR | cuts | 32 | 0.369 | -0.102 | 1.123 | 1.637 | 1.377 | 0.112 |
| S-CURVE | all | 48 | 0.368 | -0.045 | 0.991 | 1.424 | 1.261 | 0.483 |
| S-CURVE | increases | 16 | 0.373 | 0.058 | 0.671 | 1.022 | 0.865 | -0.297 |
| S-CURVE | cuts | 32 | 0.366 | -0.096 | 1.123 | 1.589 | 1.424 | 0.146 |
| S-CURVE % | all | 48 | 0.368 | -0.037 | 0.991 | 1.393 | 1.224 | 0.474 |
| S-CURVE % | increases | 16 | 0.375 | 0.055 | 0.671 | 1.012 | 0.854 | -0.329 |
| S-CURVE % | cuts | 32 | 0.364 | -0.083 | 1.123 | 1.550 | 1.377 | 0.116 |
| SHORT-RUN | all | 48 | 0.352 | -0.020 | 0.991 | 1.433 | 1.205 | 0.544 |
| SHORT-RUN | increases | 16 | 0.412 | 0.097 | 0.671 | 1.180 | 1.139 | -0.363 |
| SHORT-RUN | cuts | 32 | 0.322 | -0.079 | 1.123 | 1.537 | 1.232 | 0.369 |
| CHAIN | all | 48 | 0.368 | -0.080 | 0.991 | 1.412 | 0.502 | 0.419 |
| CHAIN | increases | 16 | 0.364 | -0.014 | 0.671 | 0.803 | 0.480 | 0.164 |
| CHAIN | cuts | 32 | 0.371 | -0.113 | 1.123 | 1.663 | 0.511 | 0.197 |

### Paired differences (block bootstrap, 4-week blocks, 90%)

| comparison | part | n | MAE diff [90% CI] | slope diff [90% CI] |
| --- | --- | --- | --- | --- |
| S-CURVE - LINEAR | all | 48 | -0.0065 [-0.0212, +0.0096] | -0.079 [-0.125, -0.044] |
| S-CURVE - LINEAR | increases | 16 | -0.0130 [-0.0370, +0.0105] | -0.152 [-0.200, -0.142] |
| S-CURVE - LINEAR | cuts | 32 | -0.0032 [-0.0183, +0.0113] | -0.049 [-0.092, +0.003] |
| S-CURVE % - LINEAR | all | 48 | -0.0065 [-0.0186, +0.0060] | -0.109 [-0.143, -0.085] |
| S-CURVE % - LINEAR | increases | 16 | -0.0108 [-0.0371, +0.0121] | -0.162 [-0.203, -0.154] |
| S-CURVE % - LINEAR | cuts | 32 | -0.0043 [-0.0158, +0.0064] | -0.088 [-0.114, -0.056] |
| SHORT-RUN - LINEAR | all | 48 | -0.0226 [-0.0600, +0.0169] | -0.069 [-0.219, +0.040] |
| SHORT-RUN - LINEAR | increases | 16 | +0.0261 [-0.0214, +0.0896] | +0.006 [-0.224, +0.128] |
| SHORT-RUN - LINEAR | cuts | 32 | -0.0470 [-0.0834, -0.0025] | -0.100 [-0.260, +0.030] |
| CHAIN - LINEAR | all | 48 | -0.0063 [-0.0607, +0.0493] | -0.090 [-0.420, +0.134] |
| CHAIN - LINEAR | increases | 16 | -0.0223 [-0.0756, +0.0339] | -0.371 [-0.820, +0.050] |
| CHAIN - LINEAR | cuts | 32 | +0.0018 [-0.0595, +0.0854] | +0.025 [-0.280, +0.292] |
| LINEAR - TIME-ONLY | all | 48 | -0.0208 [-0.1310, +0.1243] | +1.151 [+0.862, +1.444] |
| LINEAR - TIME-ONLY | increases | 16 | +0.0449 [-0.0601, +0.1598] | +0.958 [+0.666, +1.365] |
| LINEAR - TIME-ONLY | cuts | 32 | -0.0536 [-0.2233, +0.1733] | +1.230 [+0.799, +1.558] |
| S-CURVE - TIME-ONLY | all | 48 | -0.0273 [-0.1256, +0.1091] | +1.073 [+0.800, +1.338] |
| S-CURVE - TIME-ONLY | increases | 16 | +0.0318 [-0.0515, +0.1271] | +0.807 [+0.504, +1.187] |
| S-CURVE - TIME-ONLY | cuts | 32 | -0.0568 [-0.2141, +0.1556] | +1.182 [+0.797, +1.469] |
| SHORT-RUN - TIME-ONLY | all | 48 | -0.0434 [-0.1500, +0.0961] | +1.082 [+0.802, +1.338] |
| SHORT-RUN - TIME-ONLY | increases | 16 | +0.0710 [+0.0202, +0.1541] | +0.964 [+0.714, +1.285] |
| SHORT-RUN - TIME-ONLY | cuts | 32 | -0.1006 [-0.2523, +0.1132] | +1.130 [+0.716, +1.413] |
| CHAIN - TIME-ONLY | all | 48 | -0.0271 [-0.1331, +0.1134] | +1.061 [+0.734, +1.343] |
| CHAIN - TIME-ONLY | increases | 16 | +0.0226 [-0.0757, +0.1355] | +0.587 [+0.350, +0.895] |
| CHAIN - TIME-ONLY | cuts | 32 | -0.0519 [-0.2013, +0.1749] | +1.256 [+0.823, +1.575] |

### Levels on the same weeks

| model | n | baseline WAPE | scenario WAPE | scenario level bias (pct) |
| --- | --- | --- | --- | --- |
| TIME-ONLY | 48 | 48.97 | 48.97 | -6.56 |
| HYBRID | 48 | 50.15 | 47.66 | -8.72 |
| LINEAR | 48 | 50.15 | 50.00 | -6.66 |
| S-CURVE | 48 | 50.15 | 48.12 | -8.92 |
| S-CURVE % | 48 | 50.15 | 48.75 | -8.29 |
| SHORT-RUN | 48 | 50.15 | 49.83 | -5.67 |
| CHAIN | 48 | 33.08 | 33.04 | -20.14 |

compare() on scenario-week guest levels (per-fold rows, 28-day blocks):

| candidate - baseline | WAPE diff pp [90% CI] | folds same sign |
| --- | --- | --- |
| HYBRID - TIME-ONLY | +7.12 [-12.34, +19.04] | 0.71 |
| LINEAR - TIME-ONLY | +11.90 [-8.42, +26.58] | 0.71 |
| S-CURVE - TIME-ONLY | +9.46 [-11.88, +23.55] | 0.71 |
| S-CURVE % - TIME-ONLY | +10.36 [-11.05, +25.18] | 0.71 |
| SHORT-RUN - TIME-ONLY | +10.92 [-7.88, +23.40] | 0.71 |
| CHAIN - TIME-ONLY | -9.01 [-23.41, -0.31] | 0.86 |
| S-CURVE - LINEAR | -2.45 [-4.89, -0.85] | 1.00 |
| S-CURVE % - LINEAR | -1.54 [-3.32, -0.60] | 1.00 |
| SHORT-RUN - LINEAR | -0.99 [-5.90, +3.62] | 0.71 |
| CHAIN - LINEAR | -20.92 [-33.71, -9.01] | 1.00 |

### Per market (all event weeks)

| market | n | up | slope actual | TIME-ONLY slope | HYBRID slope | LINEAR slope | S-CURVE slope | S-CURVE % slope | SHORT-RUN slope | CHAIN slope | TIME-ONLY MAE | HYBRID MAE | LINEAR MAE | S-CURVE MAE | S-CURVE % MAE | SHORT-RUN MAE | CHAIN MAE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CHINA | 8 | 3 | 1.86 | -0.06 | 2.43 | 1.18 | 1.19 | 1.17 | 1.24 | 0.41 | 0.42 | 0.43 | 0.29 | 0.28 | 0.29 | 0.30 | 0.32 |
| FRANCE | 3 | 0 | 0.02 | -0.01 | 1.31 | 0.69 | 0.68 | 0.68 | 0.62 | -0.35 | 0.17 | 0.35 | 0.34 | 0.34 | 0.34 | 0.30 | 0.14 |
| ISRAEL | 25 | 9 | 0.69 | 0.38 | 0.97 | 1.55 | 1.43 | 1.41 | 1.36 | 1.46 | 0.42 | 0.44 | 0.47 | 0.46 | 0.45 | 0.43 | 0.49 |
| KUWAIT | 2 | 0 | 4.86 | 2.05 | 4.51 | 4.32 | 4.58 | 4.31 | 5.25 | 6.02 | 0.65 | 0.36 | 0.34 | 0.37 | 0.34 | 0.27 | 0.25 |
| OMAN | 3 | 2 | 1.88 | 0.34 | 1.29 | 1.15 | 1.07 | 1.03 | 0.89 | 0.02 | 0.36 | 0.33 | 0.34 | 0.34 | 0.34 | 0.35 | 0.33 |
| OTHER_MENA | 2 | 1 | 2.58 | 0.01 | 1.91 | 1.83 | 1.73 | 1.71 | 3.92 | 3.55 | 0.50 | 0.14 | 0.15 | 0.17 | 0.17 | 0.24 | 0.17 |
| PHILIPPINES | 1 | 0 | 0.30 | -0.26 | 0.50 | 0.40 | 0.55 | 0.38 | -0.66 | 0.07 | 0.09 | 0.03 | 0.02 | 0.04 | 0.01 | 0.16 | 0.04 |
| RUSSIAN FEDERATION | 4 | 1 | 1.64 | 0.26 | 1.15 | 0.49 | 0.59 | 0.48 | 0.87 | 1.59 | 0.26 | 0.12 | 0.23 | 0.21 | 0.23 | 0.16 | 0.15 |

## SHORT-RUN betas

Fitted on every week up to 2025-01-31, 90% moving-block bootstrap (4-week blocks within market). Markets under 26 usable weeks take the pooled value. Exported to out/short_run_beta.csv.

| market | beta | ci_low | ci_high | n_weeks | pooled_only |
| --- | --- | --- | --- | --- | --- |
| CHINA | 0.58 | 0.10 | 1.10 | 96 | False |
| EGYPT | 0.30 | -0.21 | 0.87 | 96 | False |
| FRANCE | 0.48 | 0.12 | 1.15 | 96 | False |
| GERMANY | 1.24 | 0.52 | 2.21 | 96 | False |
| INDIA | -0.73 | -1.41 | -0.16 | 96 | False |
| ISRAEL | 0.79 | 0.28 | 1.26 | 96 | False |
| ITALY | 0.73 | -0.18 | 1.70 | 96 | False |
| KAZAKHSTAN | -0.23 | -0.86 | 0.48 | 96 | False |
| KUWAIT | 3.50 | 2.50 | 4.39 | 96 | False |
| OMAN | 1.50 | 0.64 | 2.39 | 96 | False |
| OTHER_AMERICAS_AFRICA | 0.73 | 0.24 | 1.10 | 51 | False |
| OTHER_ASIA_PACIFIC | 0.22 | -0.04 | 0.51 | 96 | False |
| OTHER_EURASIA | 0.04 | -0.95 | 1.07 | 69 | False |
| OTHER_EUROPE | 0.58 | 0.31 | 0.91 | 13 | True |
| OTHER_MENA | 2.89 | 2.16 | 3.60 | 96 | False |
| PHILIPPINES | -0.24 | -0.76 | 0.21 | 96 | False |
| RUSSIAN FEDERATION | 0.98 | 0.56 | 1.72 | 96 | False |
| SAUDI ARABIA | -0.49 | -4.06 | 2.89 | 96 | False |
| UNITED KINGDOM | -0.20 | -1.84 | 1.44 | 96 | False |
| UNITED STATES OF AMERICA | 1.76 | 0.95 | 2.44 | 96 | False |
| POOLED | 0.58 | 0.31 | 0.91 | 1765 | True |

Per fold (training window of each origin):

| market | origin_2024-02-01 | origin_2024-03-01 | origin_2024-04-01 | origin_2024-05-01 | origin_2024-06-01 | origin_2024-07-01 | origin_2024-08-01 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CHINA | 0.12 | 0.12 | 0.16 | 0.52 | 0.64 | 0.64 | 0.57 |
| EGYPT | 0.95 | 0.84 | 0.70 | 0.74 | 0.83 | 0.66 | 0.49 |
| FRANCE | 0.40 | 0.33 | 0.32 | 0.41 | 0.41 | 0.45 | 0.47 |
| GERMANY | 1.43 | 1.47 | 1.45 | 1.45 | 1.44 | 1.51 | 1.66 |
| INDIA | -0.33 | -0.32 | -0.49 | -0.50 | -0.52 | -0.62 | -0.68 |
| ISRAEL | 1.53 | 1.29 | 1.19 | 1.16 | 1.21 | 1.31 | 1.25 |
| ITALY | 0.26 | 0.22 | 0.44 | 0.34 | 0.35 | 0.42 | 0.45 |
| KAZAKHSTAN | 0.23 | 0.14 | -0.13 | -0.25 | -0.23 | -0.23 | -0.23 |
| KUWAIT | 2.75 | 2.66 | 2.93 | 3.07 | 3.30 | 3.49 | 3.51 |
| OMAN | -0.01 | -0.17 | -0.16 | -0.09 | 0.59 | 0.94 | 1.02 |
| OTHER_AMERICAS_AFRICA | 0.41 | 0.33 | 0.32 | 0.46 | 0.60 | 0.56 | 0.49 |
| OTHER_ASIA_PACIFIC | 0.19 | 0.21 | 0.17 | 0.21 | 0.12 | 0.10 | 0.12 |
| OTHER_EURASIA | 0.41 | 0.33 | 0.32 | 0.64 | 0.07 | 0.01 | 0.09 |
| OTHER_MENA | 2.88 | 3.09 | 2.99 | 3.01 | 3.38 | 3.23 | 3.19 |
| PHILIPPINES | -0.04 | -0.02 | -0.31 | -0.39 | -0.27 | -0.24 | -0.22 |
| RUSSIAN FEDERATION | 0.48 | 0.46 | 0.67 | 0.70 | 0.69 | 0.72 | 0.87 |
| SAUDI ARABIA | 0.41 | 0.33 | 0.23 | -0.07 | -2.03 | -2.72 | -2.03 |
| UNITED KINGDOM | 0.80 | 0.73 | 0.09 | -0.28 | -0.05 | -0.14 | -0.22 |
| UNITED STATES OF AMERICA | 2.51 | 2.36 | 2.18 | 2.03 | 2.18 | 2.20 | 2.19 |
| OTHER_EUROPE |  | 0.33 | 0.32 | 0.46 | 0.59 | 0.56 | 0.49 |

## Co-movement of guest trend with seat trend (association, not effect)

Slope of the 52-week change in log centred 13-week guest trend on the same change in seats; 90% block bootstrap, 13-week blocks. Weeks overlap heavily, so the effective sample is small.

| market | slope | ci_low | ci_high | n_weeks | sd seat-trend change |
| --- | --- | --- | --- | --- | --- |
| CHINA | 0.38 | -0.16 | 0.81 | 44 | 0.46 |
| EGYPT | -0.01 | -0.33 | 0.21 | 44 | 0.15 |
| FRANCE | 0.25 | 0.17 | 0.95 | 44 | 0.34 |
| GERMANY | 1.06 | 0.81 | 1.48 | 44 | 0.18 |
| INDIA | 0.52 | 0.45 | 1.32 | 44 | 0.03 |
| ISRAEL | 1.25 | 1.16 | 1.58 | 44 | 0.61 |
| ITALY | 0.12 | -0.23 | 0.50 | 44 | 0.05 |
| KAZAKHSTAN | 0.35 | 0.22 | 0.49 | 44 | 0.23 |
| KUWAIT | 0.84 | 0.29 | 1.10 | 44 | 0.17 |
| OMAN | 0.05 | -0.25 | 0.20 | 44 | 0.38 |
| OTHER_AMERICAS_AFRICA | 0.76 | 0.76 | 0.76 | 11 | 0.15 |
| OTHER_ASIA_PACIFIC | 0.49 | -0.07 | 0.66 | 44 | 0.14 |
| OTHER_EURASIA | 2.60 | 2.29 | 2.84 | 17 | 0.07 |
| OTHER_EUROPE | -0.27 | -0.27 | -0.27 | 3 | 0.01 |
| OTHER_MENA | 0.26 | -1.53 | 2.10 | 44 | 0.02 |
| PHILIPPINES | 0.41 | -0.28 | 1.68 | 44 | 0.04 |
| RUSSIAN FEDERATION | -0.13 | -0.15 | 0.23 | 44 | 0.15 |
| SAUDI ARABIA | 1.78 | -0.81 | 3.68 | 44 | 0.02 |
| UNITED KINGDOM | 0.14 | -1.08 | 0.65 | 44 | 0.11 |
| UNITED STATES OF AMERICA | 0.64 | 0.31 | 1.80 | 44 | 0.06 |
| POOLED | 0.65 | 0.38 | 0.70 | 779 | 0.24 |

## Response curves (last fold)

Guest change for a seat change applied to the whole test period.

| market | seat_change | TIME-ONLY | SHORT-RUN | LINEAR | S-CURVE | S-CURVE % | CHAIN |
| --- | --- | --- | --- | --- | --- | --- | --- |
| UNITED KINGDOM | -0.500 | 0.000 | 0.161 | -0.425 | -0.476 | -0.425 | -0.187 |
| UNITED KINGDOM | -0.200 | 0.000 | 0.049 | -0.170 | -0.189 | -0.170 | -0.075 |
| UNITED KINGDOM | -0.100 | 0.000 | 0.023 | -0.085 | -0.095 | -0.085 | -0.037 |
| UNITED KINGDOM | 0.100 | 0.000 | -0.020 | 0.085 | 0.077 | 0.069 | 0.037 |
| UNITED KINGDOM | 0.200 | 0.000 | -0.039 | 0.170 | 0.142 | 0.129 | 0.075 |
| UNITED KINGDOM | 0.500 | 0.000 | -0.084 | 0.425 | 0.293 | 0.270 | 0.187 |
| UNITED KINGDOM | 1.000 | 0.000 | -0.139 | 0.850 | 0.455 | 0.427 | 0.375 |
| INDIA | -0.500 | 0.000 | 0.602 | -0.367 | -0.369 | -0.367 | -0.190 |
| INDIA | -0.200 | 0.000 | 0.164 | -0.147 | -0.148 | -0.147 | -0.076 |
| INDIA | -0.100 | 0.000 | 0.074 | -0.073 | -0.074 | -0.073 | -0.038 |
| INDIA | 0.100 | 0.000 | -0.063 | 0.073 | 0.060 | 0.059 | 0.038 |
| INDIA | 0.200 | 0.000 | -0.117 | 0.147 | 0.111 | 0.110 | 0.076 |
| INDIA | 0.500 | 0.000 | -0.241 | 0.367 | 0.231 | 0.230 | 0.190 |
| INDIA | 1.000 | 0.000 | -0.376 | 0.734 | 0.363 | 0.362 | 0.380 |
| CHINA | -0.500 | 0.000 | -0.326 | -0.112 | -0.129 | -0.112 | -0.062 |
| CHINA | -0.200 | 0.000 | -0.119 | -0.045 | -0.064 | -0.045 | -0.025 |
| CHINA | -0.100 | 0.000 | -0.058 | -0.022 | -0.032 | -0.022 | -0.012 |
| CHINA | 0.100 | 0.000 | 0.056 | 0.022 | 0.029 | 0.019 | 0.012 |
| CHINA | 0.200 | 0.000 | 0.110 | 0.045 | 0.057 | 0.038 | 0.025 |
| CHINA | 0.500 | 0.000 | 0.260 | 0.112 | 0.131 | 0.090 | 0.062 |
| CHINA | 1.000 | 0.000 | 0.485 | 0.225 | 0.216 | 0.168 | 0.124 |
| GERMANY | -0.500 | 0.000 | -0.685 | -0.469 | -0.540 | -0.469 | -0.360 |
| GERMANY | -0.200 | 0.000 | -0.310 | -0.188 | -0.232 | -0.188 | -0.144 |
| GERMANY | -0.100 | 0.000 | -0.161 | -0.094 | -0.116 | -0.094 | -0.072 |
| GERMANY | 0.100 | 0.000 | 0.172 | 0.094 | 0.095 | 0.076 | 0.072 |
| GERMANY | 0.200 | 0.000 | 0.355 | 0.188 | 0.174 | 0.142 | 0.144 |
| GERMANY | 0.500 | 0.000 | 0.964 | 0.469 | 0.350 | 0.296 | 0.360 |
| GERMANY | 1.000 | 0.000 | 2.170 | 0.939 | 0.530 | 0.467 | 0.720 |
| KUWAIT | -0.500 | 0.000 | -0.912 | -0.440 | -0.485 | -0.440 | -0.354 |
| KUWAIT | -0.200 | 0.000 | -0.543 | -0.186 | -0.206 | -0.186 | -0.142 |
| KUWAIT | -0.100 | 0.000 | -0.309 | -0.093 | -0.104 | -0.093 | -0.071 |
| KUWAIT | 0.100 | 0.000 | 0.397 | 0.096 | 0.086 | 0.077 | 0.071 |
| KUWAIT | 0.200 | 0.000 | 0.897 | 0.193 | 0.159 | 0.144 | 0.142 |
| KUWAIT | 0.500 | 0.000 | 3.153 | 0.481 | 0.322 | 0.298 | 0.354 |
| KUWAIT | 1.000 | 0.000 | 10.403 | 0.963 | 0.492 | 0.464 | 0.708 |

- `out/response_curves_yoy.png`
- `out/response_curves_trend.png`
