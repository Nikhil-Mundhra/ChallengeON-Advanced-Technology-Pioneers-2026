# Scenario response

## Back-test of the flight levers

Source: `experiment/scenario_response/` ([README](../../experiment/scenario_response/README.md), [results](../../experiment/scenario_response/results.md)), run at commit e015fdd. International markets, `VALIDATION_ORIGINS` (7 folds), panels cut at 2025-01-31. Natural experiments: 717 market-weeks whose seats moved more than 15% against the same week a year earlier (624 increases, 93 cuts). Paired MAE differences on log guest change, 90% moving-block bootstrap intervals.

| Comparison | All | Increases | Cuts |
| --- | --- | --- | --- |
| Chain − linear chain | −0.067 [−0.095, −0.043] | −0.048 [−0.070, −0.029] | −0.198 [−0.316, −0.092] |
| Chain − calendar only | −0.066 [−0.093, −0.043] | −0.054 [−0.084, −0.030] | −0.142 [−0.258, −0.080] |
| Hand-set adjustments − linear chain | −0.018 [−0.032, −0.003] | −0.020 [−0.037, −0.005] | −0.000 [−0.010, +0.017] |
| Short-run elasticity − calendar only | +0.066 [+0.043, +0.084] | +0.070 [+0.052, +0.085] | +0.042 [−0.180, +0.167] |

| Fact |
| --- |
| Ordinary weeks (yoy seat change at most 15%, 265 market-weeks): chain R² 0.61 against calendar only; linear chain 0.21; short-run elasticity 0.10 |
| Short-run elasticity per market: −0.73 (India) to 3.50 (Kuwait); signs flip across folds (UK +0.80 to −0.22, Saudi Arabia +0.41 to −2.72) |
| Chain response near linear in log: about 0.37 of the seat change for UK and India, 0.12 for China, 0.71 for Germany and Kuwait (last fold) |
| Co-movement of the 52-week guest-trend change with the seat-trend change: 0.65 [0.38, 0.70] (pooled, an association) |

## Shipped schedule elasticity

Source: `lake/curated/flight_response.json`, written by `twin train`.

ε per market and season from the full fit, range [lowest, highest] over the full fit and the 7 `VALIDATION_ORIGINS` refits ([flight response](../model/planning.md#flight-response)).

| Market | Winter peak | Spring shoulder | Summer trough | Autumn shoulder |
| --- | --- | --- | --- | --- |
| China | 0.10 [0.10, 0.19] | 0.12 [0.12, 0.16] | 0.13 [0.13, 0.16] | 0.14 [0.12, 0.14] |
| Egypt | 0.27 [0.27, 0.44] | 0.25 [0.24, 0.44] | 0.28 [0.28, 0.44] | 0.31 [0.31, 0.45] |
| France | 0.25 [0.18, 0.28] | 0.30 [0.11, 0.30] | 0.27 [0.09, 0.27] | 0.26 [0.10, 0.26] |
| Germany | 0.62 [0.62, 0.76] | 0.63 [0.62, 0.72] | 0.56 [0.56, 0.74] | 0.54 [0.54, 0.76] |
| India | 0.44 [0.34, 0.50] | 0.46 [0.34, 0.53] | 0.45 [0.34, 0.48] | 0.44 [0.34, 0.49] |
| Israel | 0.59 [0.58, 0.81] | 0.76 [0.59, 0.97] | 0.57 [0.57, 0.80] | 0.41 [0.41, 0.89] |
| Italy | 0.48 [0.48, 0.70] | 0.48 [0.48, 0.71] | 0.39 [0.39, 0.68] | 0.42 [0.42, 0.66] |
| Kazakhstan | 0.58 [0.57, 0.77] | 0.64 [0.43, 0.71] | 0.53 [0.50, 0.73] | 0.47 [0.47, 0.78] |
| Kuwait | 0.84 [0.84, 0.98] | 0.68 [0.68, 0.98] | 0.76 [0.76, 0.99] | 0.75 [0.75, 0.97] |
| Oman | 0.20 [0.05, 0.65] | 0.18 [0.03, 0.59] | 0.26 [0.04, 0.65] | 0.24 [0.04, 0.66] |
| Other Americas and Africa | 0.15 [0.14, 0.16] | 0.15 [0.13, 0.15] | 0.15 [0.13, 0.15] | 0.15 [0.14, 0.17] |
| Other Asia-Pacific | 0.31 [0.31, 0.44] | 0.37 [0.29, 0.44] | 0.36 [0.29, 0.42] | 0.33 [0.31, 0.42] |
| Other Eurasia | 0.35 [0.35, 0.75] | 0.36 [0.36, 0.69] | 0.31 [0.31, 0.73] | 0.31 [0.31, 0.74] |
| Other Europe | 0.55 [0.55, 0.69] | 0.51 [0.51, 0.70] | 0.51 [0.51, 0.68] | 0.56 [0.54, 0.68] |
| Other MENA | 0.53 [0.45, 0.66] | 0.48 [0.46, 0.64] | 0.53 [0.49, 0.70] | 0.55 [0.46, 0.68] |
| Philippines | 0.19 [0.19, 0.34] | 0.15 [0.15, 0.34] | 0.16 [0.16, 0.34] | 0.17 [0.17, 0.32] |
| Russian Federation | 0.56 [0.46, 0.59] | 0.49 [0.46, 0.53] | 0.40 [0.36, 0.46] | 0.41 [0.35, 0.44] |
| Saudi Arabia | 0.75 [0.50, 0.77] | 0.71 [0.53, 0.76] | 0.70 [0.51, 0.79] | 0.73 [0.47, 0.73] |
| United Kingdom | 0.31 [0.31, 0.48] | 0.31 [0.27, 0.47] | 0.32 [0.28, 0.46] | 0.31 [0.30, 0.47] |
| United States of America | 0.46 [0.40, 0.55] | 0.44 [0.43, 0.53] | 0.42 [0.39, 0.55] | 0.45 [0.41, 0.56] |
| Pooled (cold start, no seats) | 0.45 [0.05, 0.98] | 0.45 [0.03, 0.98] | 0.39 [0.04, 0.99] | 0.41 [0.04, 0.97] |

| Fact |
| --- |
| Linearity: ε at −25%, −10%, +10% and +25% seats differs from its mean by at most 0.034 in every market and season |
| Seasons: 11 of 20 markets have seasonal ε more than 0.05 apart (Israel 0.35, Kazakhstan 0.17, Kuwait 0.16, Russian Federation 0.16, Italy 0.10, Germany 0.09, Oman 0.09, Other MENA 0.08, Egypt 0.07, Other Asia-Pacific 0.06, Saudi Arabia 0.06); ε is kept per season for every market |
| Full fit against refits: the full fit's ε is at or near the low end of the range in most markets; refits on data to January to July 2024 give higher ε |
| Capacity co-movement on the full training window (shipped central line): γ 0.60 [0.26, 0.79], mean market intercept 0.074 log points a year; on weeks to 2025-01-31: 0.64 |

