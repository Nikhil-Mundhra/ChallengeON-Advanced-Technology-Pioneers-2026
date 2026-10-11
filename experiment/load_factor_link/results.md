# Load factor link: results

International markets, VALIDATION_ORIGINS (7 folds), each variant fitted on the fold's training window. Aggregate metrics only. Written by `report.py` from the runs cached by `run.py`.

## Guests: chain accuracy against BASE

Delta is candidate minus BASE WAPE (pp, negative is better) from compare(). Gate: delta <= -0.3 pp, CI excludes 0, better in at least 4 of 7 folds, on both grains. A_oracle reads realized P2P and is not deployable.

| variant | daily WAPE | weekly WAPE | level bias (pct) | daily delta pp [90% CI] | daily folds better | weekly delta pp [90% CI] | weekly folds better | gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASE | 21.05 | 19.18 | -7.18 |  |  |  |  |  |
| A | 21.05 | 19.16 | -7.87 | -0.00 [-0.23, +0.12] | 6/7 | -0.02 [-0.23, +0.15] | 5/7 | fail |
| A_updown | 21.05 | 19.16 | -7.81 | -0.01 [-0.23, +0.11] | 6/7 | -0.03 [-0.24, +0.14] | 5/7 | fail |
| A2 | 21.06 | 19.17 | -7.69 | +0.00 [-0.23, +0.13] | 6/7 | -0.02 [-0.24, +0.15] | 5/7 | fail |
| L | 21.00 | 19.09 | -8.30 | -0.07 [-0.32, +0.08] | 5/7 | -0.11 [-0.37, +0.07] | 5/7 | fail |
| TS | 21.25 | 19.38 | -8.69 | +0.19 [-0.06, +0.34] | 2/7 | +0.19 [-0.06, +0.38] | 3/7 | fail |
| B | 21.39 | 19.42 | -4.64 | +0.32 [+0.07, +0.64] | 2/7 | +0.22 [-0.04, +0.58] | 2/7 | fail |
| C | 21.09 | 19.24 | -8.71 | +0.03 [-0.41, +0.27] | 5/7 | +0.05 [-0.40, +0.32] | 6/7 | fail |
| A_oracle | 20.41 | 18.76 | -6.58 | -0.68 [-1.40, +0.09] | 6/7 | -0.46 [-1.18, +0.26] | 6/7 | diagnostic |

## Link 0: P2P accuracy on test days

LF here is P2P per seat (the rate link 0 predicts); error in percentage points per market-week.

| variant | P2P WAPE daily | P2P WAPE weekly | P2P bias (pct) | LF error MAE (pp) | LF error bias (pp) |
| --- | --- | --- | --- | --- | --- |
| A | 16.81 | 14.28 | 2.39 | 7.40 | 1.60 |
| A_updown | 16.81 | 14.27 | 2.38 | 7.40 | 1.60 |
| A2 | 16.69 | 14.13 | 2.33 | 7.33 | 1.54 |
| L | 18.74 | 16.29 | 2.17 | 7.54 | 1.96 |
| TS | 17.35 | 14.75 | 0.11 | 7.39 | 0.95 |
| B | 40.75 | 38.22 | 6.78 | 18.88 | 6.20 |
| C | 16.64 | 14.32 | 2.30 | 7.20 | 1.34 |
| A_oracle | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

## Lever: guests

Weeks with seats moved more than 15% against a year earlier, each market-week once (prediction averaged over the folds that score it). Drift baseline: same market-year quiet weeks when at least 8, else the trailing 52-week median. Only weeks every variant scores. slope_seat_only: the model's pure seat response (test period re-predicted on last year's schedule). The down weeks come from a few episodes (Israel, Oman, China, Kuwait, France); treat them as a guard against harm, not a ranking.

### BASE

| weeks | n | MAE | bias | slope_act | slope_pred | slope_seat_only |
| --- | --- | --- | --- | --- | --- | --- |
| all | 704 | 0.204 | -0.036 | 0.138 | 0.203 | 0.494 |
| up | 610 | 0.176 | -0.012 | 0.261 | 0.257 | 0.442 |
| down | 94 | 0.388 | -0.193 | -0.318 | 0.002 | 0.685 |
| down oman | 18 | 0.283 | 0.058 | 0.254 | 0.108 | 0.149 |
| down kuwait | 14 | 0.231 | 0.121 | 1.596 | 1.172 | 0.801 |
| down china | 14 | 0.336 | -0.336 | 0.045 | 0.527 | 0.126 |
| down israel | 33 | 0.653 | -0.514 | -0.629 | -0.247 | 0.937 |
| down france | 11 | 0.134 | 0.076 | 0.853 | 0.620 | 0.211 |
| down other | 4 | 0.096 | -0.002 | 0.149 | 0.178 | 0.277 |

### A

| weeks | n | MAE | bias | slope_act | slope_pred | slope_seat_only |
| --- | --- | --- | --- | --- | --- | --- |
| all | 704 | 0.206 | -0.028 | 0.138 | 0.210 | 0.423 |
| up | 610 | 0.176 | 0.000 | 0.261 | 0.265 | 0.370 |
| down | 94 | 0.403 | -0.212 | -0.318 | 0.006 | 0.621 |
| down oman | 18 | 0.296 | 0.086 | 0.254 | 0.036 | 0.189 |
| down kuwait | 14 | 0.221 | 0.107 | 1.596 | 1.226 | 0.795 |
| down china | 14 | 0.247 | -0.247 | 0.045 | 0.393 | 0.087 |
| down israel | 33 | 0.728 | -0.627 | -0.629 | -0.190 | 0.844 |
| down france | 11 | 0.141 | 0.109 | 0.853 | 0.518 | 0.252 |
| down other | 4 | 0.099 | 0.001 | 0.149 | 0.173 | 0.303 |

### A_updown

| weeks | n | MAE | bias | slope_act | slope_pred | slope_seat_only |
| --- | --- | --- | --- | --- | --- | --- |
| all | 704 | 0.206 | -0.028 | 0.138 | 0.209 | 0.425 |
| up | 610 | 0.176 | 0.001 | 0.261 | 0.265 | 0.369 |
| down | 94 | 0.401 | -0.210 | -0.318 | 0.003 | 0.633 |
| down oman | 18 | 0.296 | 0.086 | 0.254 | 0.036 | 0.189 |
| down kuwait | 14 | 0.221 | 0.107 | 1.596 | 1.226 | 0.795 |
| down china | 14 | 0.245 | -0.245 | 0.045 | 0.390 | 0.086 |
| down israel | 33 | 0.724 | -0.623 | -0.629 | -0.192 | 0.864 |
| down france | 11 | 0.141 | 0.109 | 0.853 | 0.518 | 0.250 |
| down other | 4 | 0.099 | 0.001 | 0.149 | 0.173 | 0.303 |

### A2

| weeks | n | MAE | bias | slope_act | slope_pred | slope_seat_only |
| --- | --- | --- | --- | --- | --- | --- |
| all | 704 | 0.206 | -0.026 | 0.138 | 0.214 | 0.427 |
| up | 610 | 0.176 | 0.002 | 0.261 | 0.270 | 0.370 |
| down | 94 | 0.402 | -0.211 | -0.318 | 0.004 | 0.640 |
| down oman | 18 | 0.296 | 0.082 | 0.254 | 0.045 | 0.202 |
| down kuwait | 14 | 0.223 | 0.107 | 1.596 | 1.226 | 0.817 |
| down china | 14 | 0.244 | -0.243 | 0.045 | 0.387 | 0.086 |
| down israel | 33 | 0.726 | -0.625 | -0.629 | -0.191 | 0.872 |
| down france | 11 | 0.141 | 0.107 | 0.853 | 0.524 | 0.244 |
| down other | 4 | 0.099 | -0.001 | 0.149 | 0.183 | 0.310 |

### L

| weeks | n | MAE | bias | slope_act | slope_pred | slope_seat_only |
| --- | --- | --- | --- | --- | --- | --- |
| all | 704 | 0.213 | -0.030 | 0.138 | 0.234 | 0.484 |
| up | 610 | 0.179 | 0.001 | 0.261 | 0.287 | 0.434 |
| down | 94 | 0.437 | -0.232 | -0.318 | 0.037 | 0.669 |
| down oman | 18 | 0.298 | 0.085 | 0.254 | 0.035 | 0.185 |
| down kuwait | 14 | 0.216 | 0.092 | 1.596 | 1.295 | 0.726 |
| down china | 14 | 0.248 | -0.246 | 0.045 | 0.389 | 0.079 |
| down israel | 33 | 0.807 | -0.707 | -0.629 | -0.129 | 0.932 |
| down france | 11 | 0.201 | 0.193 | 0.853 | 0.285 | 0.095 |
| down other | 4 | 0.101 | 0.001 | 0.149 | 0.179 | 0.303 |

### TS

| weeks | n | MAE | bias | slope_act | slope_pred | slope_seat_only |
| --- | --- | --- | --- | --- | --- | --- |
| all | 704 | 0.206 | -0.032 | 0.138 | 0.204 | 0.409 |
| up | 610 | 0.176 | -0.004 | 0.261 | 0.257 | 0.352 |
| down | 94 | 0.403 | -0.212 | -0.318 | 0.006 | 0.621 |
| down oman | 18 | 0.296 | 0.085 | 0.254 | 0.037 | 0.189 |
| down kuwait | 14 | 0.221 | 0.107 | 1.596 | 1.226 | 0.795 |
| down china | 14 | 0.247 | -0.247 | 0.045 | 0.393 | 0.087 |
| down israel | 33 | 0.728 | -0.627 | -0.629 | -0.190 | 0.844 |
| down france | 11 | 0.141 | 0.109 | 0.853 | 0.518 | 0.253 |
| down other | 4 | 0.099 | -0.001 | 0.149 | 0.184 | 0.328 |

### B

| weeks | n | MAE | bias | slope_act | slope_pred | slope_seat_only |
| --- | --- | --- | --- | --- | --- | --- |
| all | 704 | 0.207 | -0.024 | 0.138 | 0.223 | 0.537 |
| up | 610 | 0.177 | 0.004 | 0.261 | 0.276 | 0.483 |
| down | 94 | 0.397 | -0.204 | -0.318 | 0.024 | 0.737 |
| down oman | 18 | 0.303 | 0.106 | 0.254 | -0.036 | 0.036 |
| down kuwait | 14 | 0.235 | 0.026 | 1.596 | 1.576 | 1.155 |
| down china | 14 | 0.432 | -0.432 | 0.045 | 0.668 | 0.270 |
| down israel | 33 | 0.628 | -0.489 | -0.629 | -0.259 | 0.965 |
| down france | 11 | 0.129 | 0.067 | 0.853 | 0.642 | 0.278 |
| down other | 4 | 0.092 | -0.015 | 0.149 | 0.243 | 0.359 |

### C

| weeks | n | MAE | bias | slope_act | slope_pred | slope_seat_only |
| --- | --- | --- | --- | --- | --- | --- |
| all | 704 | 0.209 | -0.023 | 0.138 | 0.238 | 0.481 |
| up | 610 | 0.178 | 0.008 | 0.261 | 0.300 | 0.425 |
| down | 94 | 0.411 | -0.221 | -0.318 | 0.007 | 0.688 |
| down oman | 18 | 0.304 | 0.103 | 0.254 | -0.013 | 0.157 |
| down kuwait | 14 | 0.231 | 0.107 | 1.596 | 1.242 | 0.913 |
| down china | 14 | 0.256 | -0.252 | 0.045 | 0.401 | 0.115 |
| down israel | 33 | 0.742 | -0.639 | -0.629 | -0.195 | 0.924 |
| down france | 11 | 0.134 | 0.059 | 0.853 | 0.657 | 0.417 |
| down other | 4 | 0.112 | -0.033 | 0.149 | 0.307 | 0.560 |

### A_oracle

| weeks | n | MAE | bias | slope_act | slope_pred | slope_seat_only |
| --- | --- | --- | --- | --- | --- | --- |
| all | 704 | 0.179 | -0.042 | 0.138 | 0.125 | 0.515 |
| up | 610 | 0.161 | -0.026 | 0.261 | 0.193 | 0.419 |
| down | 94 | 0.295 | -0.150 | -0.318 | -0.129 | 0.871 |
| down oman | 18 | 0.263 | -0.014 | 0.254 | 0.317 | 0.352 |
| down kuwait | 14 | 0.165 | 0.042 | 1.596 | 1.469 | 1.697 |
| down china | 14 | 0.255 | -0.253 | 0.045 | 0.405 | -0.020 |
| down israel | 33 | 0.463 | -0.330 | -0.629 | -0.452 | 1.188 |
| down france | 11 | 0.145 | -0.008 | 0.853 | 0.850 | 0.528 |
| down other | 4 | 0.056 | 0.031 | 0.149 | 0.027 | 0.349 |

## Lever: P2P

Same weeks and rules on P2P itself. Actual slopes of pax and P2P on the lever weeks:

| series | weeks | n | slope_act |
| --- | --- | --- | --- |
| pax | up | 665 | 0.301 |
| pax | down | 97 | 0.112 |
| p2p | up | 665 | 0.264 |
| p2p | down | 97 | 0.143 |

### A (P2P)

| weeks | n | MAE | bias | slope_act | slope_pred | slope_seat_only |
| --- | --- | --- | --- | --- | --- | --- |
| all | 759 | 0.246 | 0.037 | 0.241 | 0.296 | 0.903 |
| up | 662 | 0.204 | 0.040 | 0.271 | 0.299 | 0.907 |
| down | 97 | 0.535 | 0.010 | 0.143 | 0.287 | 0.890 |
| down oman | 18 | 0.672 | 0.672 | 4.391 | 2.463 | 0.949 |
| down kuwait | 14 | 0.258 | 0.226 | 2.144 | 1.281 | 0.963 |
| down china | 14 | 0.243 | -0.192 | 0.972 | 1.263 | 0.715 |
| down israel | 36 | 0.627 | -0.584 | -0.626 | -0.226 | 0.919 |
| down france | 11 | 0.892 | 0.892 | 5.530 | 3.036 | 0.935 |
| down other | 4 | 0.096 | -0.090 | 0.600 | 0.977 | 0.888 |

### A_updown (P2P)

| weeks | n | MAE | bias | slope_act | slope_pred | slope_seat_only |
| --- | --- | --- | --- | --- | --- | --- |
| all | 759 | 0.246 | 0.037 | 0.241 | 0.293 | 0.904 |
| up | 662 | 0.203 | 0.040 | 0.271 | 0.297 | 0.904 |
| down | 97 | 0.534 | 0.015 | 0.143 | 0.280 | 0.907 |
| down oman | 18 | 0.672 | 0.672 | 4.391 | 2.463 | 0.949 |
| down kuwait | 14 | 0.258 | 0.226 | 2.144 | 1.281 | 0.963 |
| down china | 14 | 0.244 | -0.180 | 0.972 | 1.244 | 0.698 |
| down israel | 36 | 0.623 | -0.579 | -0.626 | -0.229 | 0.947 |
| down france | 11 | 0.900 | 0.900 | 5.530 | 3.014 | 0.913 |
| down other | 4 | 0.096 | -0.090 | 0.600 | 0.977 | 0.888 |

### A2 (P2P)

| weeks | n | MAE | bias | slope_act | slope_pred | slope_seat_only |
| --- | --- | --- | --- | --- | --- | --- |
| all | 759 | 0.244 | 0.036 | 0.241 | 0.294 | 0.900 |
| up | 662 | 0.202 | 0.040 | 0.271 | 0.299 | 0.895 |
| down | 97 | 0.534 | 0.015 | 0.143 | 0.278 | 0.919 |
| down oman | 18 | 0.658 | 0.658 | 4.391 | 2.497 | 0.985 |
| down kuwait | 14 | 0.257 | 0.221 | 2.144 | 1.306 | 0.993 |
| down china | 14 | 0.251 | -0.172 | 0.972 | 1.230 | 0.715 |
| down israel | 36 | 0.622 | -0.579 | -0.626 | -0.229 | 0.958 |
| down france | 11 | 0.917 | 0.917 | 5.530 | 2.963 | 0.863 |
| down other | 4 | 0.095 | -0.089 | 0.600 | 0.970 | 0.881 |

### L (P2P)

| weeks | n | MAE | bias | slope_act | slope_pred | slope_seat_only |
| --- | --- | --- | --- | --- | --- | --- |
| all | 759 | 0.247 | 0.040 | 0.241 | 0.344 | 0.994 |
| up | 662 | 0.200 | 0.044 | 0.271 | 0.357 | 0.989 |
| down | 97 | 0.569 | 0.011 | 0.143 | 0.299 | 1.013 |
| down oman | 18 | 0.672 | 0.672 | 4.391 | 2.459 | 1.024 |
| down kuwait | 14 | 0.267 | 0.245 | 2.144 | 1.172 | 0.887 |
| down china | 14 | 0.311 | -0.184 | 0.972 | 1.242 | 0.576 |
| down israel | 36 | 0.648 | -0.634 | -0.626 | -0.183 | 1.130 |
| down france | 11 | 1.030 | 1.030 | 5.530 | 2.643 | 0.543 |
| down other | 4 | 0.093 | -0.085 | 0.600 | 0.953 | 0.882 |

### TS (P2P)

| weeks | n | MAE | bias | slope_act | slope_pred | slope_seat_only |
| --- | --- | --- | --- | --- | --- | --- |
| all | 759 | 0.245 | 0.028 | 0.241 | 0.282 | 0.878 |
| up | 662 | 0.203 | 0.030 | 0.271 | 0.281 | 0.875 |
| down | 97 | 0.535 | 0.011 | 0.143 | 0.286 | 0.889 |
| down oman | 18 | 0.672 | 0.672 | 4.391 | 2.463 | 0.949 |
| down kuwait | 14 | 0.258 | 0.226 | 2.144 | 1.281 | 0.963 |
| down china | 14 | 0.242 | -0.190 | 0.972 | 1.260 | 0.711 |
| down israel | 36 | 0.627 | -0.584 | -0.626 | -0.226 | 0.918 |
| down france | 11 | 0.892 | 0.892 | 5.530 | 3.036 | 0.935 |
| down other | 4 | 0.099 | -0.094 | 0.600 | 0.996 | 0.917 |

### B (P2P)

| weeks | n | MAE | bias | slope_act | slope_pred | slope_seat_only |
| --- | --- | --- | --- | --- | --- | --- |
| all | 759 | 0.260 | 0.059 | 0.241 | 0.376 | 1.231 |
| up | 662 | 0.235 | 0.081 | 0.271 | 0.373 | 1.285 |
| down | 97 | 0.435 | -0.096 | 0.143 | 0.386 | 1.058 |
| down oman | 18 | 0.466 | 0.466 | 4.391 | 3.039 | 1.273 |
| down kuwait | 14 | 0.222 | 0.084 | 2.144 | 1.898 | 1.498 |
| down china | 14 | 0.399 | -0.337 | 0.972 | 1.492 | 0.989 |
| down israel | 36 | 0.554 | -0.495 | -0.626 | -0.259 | 1.007 |
| down france | 11 | 0.401 | 0.401 | 5.530 | 4.431 | 1.890 |
| down other | 4 | 0.173 | -0.173 | 0.600 | 1.376 | 1.389 |

### C (P2P)

| weeks | n | MAE | bias | slope_act | slope_pred | slope_seat_only |
| --- | --- | --- | --- | --- | --- | --- |
| all | 759 | 0.243 | 0.038 | 0.241 | 0.353 | 0.996 |
| up | 662 | 0.206 | 0.053 | 0.271 | 0.350 | 0.981 |
| down | 97 | 0.498 | -0.066 | 0.143 | 0.360 | 1.044 |
| down oman | 18 | 0.634 | 0.634 | 4.391 | 2.538 | 1.044 |
| down kuwait | 14 | 0.257 | 0.196 | 2.144 | 1.434 | 1.095 |
| down china | 14 | 0.308 | -0.280 | 0.972 | 1.408 | 0.948 |
| down israel | 36 | 0.623 | -0.602 | -0.626 | -0.216 | 1.021 |
| down france | 11 | 0.518 | 0.518 | 5.530 | 4.105 | 1.948 |
| down other | 4 | 0.209 | -0.178 | 0.600 | 1.330 | 1.397 |

### A_oracle (P2P)

| weeks | n | MAE | bias | slope_act | slope_pred | slope_seat_only |
| --- | --- | --- | --- | --- | --- | --- |
| all | 759 | 0.000 | 0.000 | 0.241 | 0.241 | 1.189 |
| up | 662 | 0.000 | 0.000 | 0.271 | 0.271 | 1.083 |
| down | 97 | 0.000 | 0.000 | 0.143 | 0.143 | 1.534 |
| down oman | 18 | 0.000 | 0.000 | 4.391 | 4.391 | 2.660 |
| down kuwait | 14 | 0.000 | -0.000 | 2.144 | 2.144 | 1.952 |
| down china | 14 | 0.000 | 0.000 | 0.972 | 0.972 | -0.117 |
| down israel | 36 | 0.000 | 0.000 | -0.626 | -0.626 | 1.739 |
| down france | 11 | 0.000 | 0.000 | 5.530 | 5.530 | 2.800 |
| down other | 4 | 0.000 | 0.000 | 0.600 | 0.600 | 1.226 |

## Link 0 coefficients

Descriptive: market-weeks against their own centred 13-week trend, before 2025-02 (no model). rate_move: change of pax or P2P per seat, pp per +10% seats.

| series | weeks | n | slope | rate_move_pp_per_10pct_seats |
| --- | --- | --- | --- | --- |
| p2p | all | 1920 | 1.555 | 1.626 |
| p2p | increases | 941 | 1.016 | 1.210 |
| p2p | cuts | 936 | 1.844 | 1.849 |
| pax | all | 1920 | 1.022 | -0.049 |
| pax | increases | 941 | 0.973 | 0.334 |
| pax | cuts | 936 | 1.048 | -0.253 |

Fitted per fold (median over markets; markets at 1: beta on its upper bound):

| variant | fold | median beta | markets at 1 (beta) | median beta_up | markets at 1 (beta_up) | median beta_down | markets at 1 (beta_down) | gamma | median beta_long | markets at 1 (beta_long) | median b (logit) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 0 | 0.925 | 9 |  |  |  |  |  |  |  |  |
| A | 1 | 1.000 | 11 |  |  |  |  |  |  |  |  |
| A | 2 | 0.962 | 8 |  |  |  |  |  |  |  |  |
| A | 3 | 1.000 | 12 |  |  |  |  |  |  |  |  |
| A | 4 | 1.000 | 12 |  |  |  |  |  |  |  |  |
| A | 5 | 1.000 | 12 |  |  |  |  |  |  |  |  |
| A | 6 | 1.000 | 11 |  |  |  |  |  |  |  |  |
| A_updown | 0 |  |  | 0.960 | 9 | 0.970 | 9 |  |  |  |  |
| A_updown | 1 |  |  | 1.000 | 11 | 0.990 | 9 |  |  |  |  |
| A_updown | 2 |  |  | 0.976 | 8 | 0.943 | 8 |  |  |  |  |
| A_updown | 3 |  |  | 1.000 | 11 | 0.955 | 9 |  |  |  |  |
| A_updown | 4 |  |  | 1.000 | 11 | 0.989 | 10 |  |  |  |  |
| A_updown | 5 |  |  | 1.000 | 11 | 0.977 | 10 |  |  |  |  |
| A_updown | 6 |  |  | 0.991 | 10 | 0.954 | 10 |  |  |  |  |
| A2 | 0 |  |  | 1.000 | 11 | 1.000 | 12 | -3.000 |  |  |  |
| A2 | 1 |  |  | 1.000 | 12 | 0.887 | 8 | -1.000 |  |  |  |
| A2 | 2 |  |  | 1.000 | 12 | 0.875 | 8 | -1.000 |  |  |  |
| A2 | 3 |  |  | 1.000 | 14 | 0.844 | 10 | -0.500 |  |  |  |
| A2 | 4 |  |  | 1.000 | 13 | 1.000 | 11 | -1.250 |  |  |  |
| A2 | 5 |  |  | 1.000 | 13 | 1.000 | 11 | -0.750 |  |  |  |
| A2 | 6 |  |  | 1.000 | 12 | 1.000 | 11 | -0.750 |  |  |  |
| TS | 0 | 0.925 | 9 |  |  |  |  |  | 1.000 | 19 |  |
| TS | 1 | 1.000 | 11 |  |  |  |  |  | 0.967 | 8 |  |
| TS | 2 | 0.962 | 8 |  |  |  |  |  | 1.000 | 14 |  |
| TS | 3 | 1.000 | 11 |  |  |  |  |  | 0.866 | 8 |  |
| TS | 4 | 1.000 | 12 |  |  |  |  |  | 0.987 | 10 |  |
| TS | 5 | 1.000 | 12 |  |  |  |  |  | 0.976 | 10 |  |
| TS | 6 | 0.999 | 10 |  |  |  |  |  | 1.000 | 11 |  |
| L | 0 |  |  |  |  |  |  |  |  |  | -0.023 |
| L | 1 |  |  |  |  |  |  |  |  |  | -0.150 |
| L | 2 |  |  |  |  |  |  |  |  |  | -0.220 |
| L | 3 |  |  |  |  |  |  |  |  |  | -0.240 |
| L | 4 |  |  |  |  |  |  |  |  |  | -0.302 |
| L | 5 |  |  |  |  |  |  |  |  |  | -0.092 |
| L | 6 |  |  |  |  |  |  |  |  |  | -0.187 |

Intervals on the last fold's training window (to 2024-07-11), 90%, delete-half 28-day block jackknife, 100 draws:

### A

| coefficient | estimate | low | high |
| --- | --- | --- | --- |
| median beta | 1.000 | 0.763 | 1.069 |
| mean beta | 0.812 | 0.678 | 0.901 |

### A_updown

| coefficient | estimate | low | high |
| --- | --- | --- | --- |
| median beta_up | 0.991 | 0.770 | 1.068 |
| median beta_down | 0.954 | 0.749 | 1.044 |
| mean beta_up | 0.808 | 0.686 | 0.894 |
| mean beta_down | 0.793 | 0.674 | 0.878 |

### A2

| coefficient | estimate | low | high |
| --- | --- | --- | --- |
| median beta_up | 1.000 | 0.680 | 1.066 |
| median beta_down | 1.000 | 0.620 | 1.105 |
| mean beta_up | 0.816 | 0.635 | 0.927 |
| mean beta_down | 0.673 | 0.502 | 0.783 |
| gamma | -0.750 | -2.987 | 3.275 |

### TS

| coefficient | estimate | low | high |
| --- | --- | --- | --- |
| median beta | 0.999 | 0.785 | 1.071 |
| median beta_long | 1.000 | 0.795 | 1.041 |
| mean beta | 0.813 | 0.710 | 0.889 |
| mean beta_long | 0.894 | 0.755 | 0.976 |

### L

| coefficient | estimate | low | high |
| --- | --- | --- | --- |
| median b | -0.187 | -0.775 | 0.476 |

### C

| coefficient | estimate | low | high |
| --- | --- | --- | --- |
| median flights | 0.928 | 0.872 | 0.989 |
| median gauge | 0.778 | 0.529 | 0.966 |
| median airlines | 0.276 | 0.136 | 0.388 |
| median premium_share | -1.797 | -3.665 | -0.341 |
| mean flights | 0.946 | 0.874 | 1.022 |
| mean gauge | 0.808 | 0.565 | 0.990 |
| mean airlines | 0.311 | 0.156 | 0.436 |
| mean premium_share | -2.093 | -3.353 | -1.060 |

Per market, last fold (A beta with and without pooling; A_updown; A2 beta_down at the market's usual LF; C coefficients):

| market | A beta | A beta_unpooled | A_updown beta_up | A_updown beta_down | A_updown beta_up_unpooled | A_updown beta_down_unpooled | A2 beta_up | A2 beta_down_at_market_lf | TS beta | TS beta_long | L b | C flights | C gauge | C airlines | C premium_share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CHINA | 0.54 | 0.22 | 0.59 | 0.40 | 0.28 | 0.10 | 0.82 | 0.12 | 0.53 | 1.00 | -0.92 | 0.88 | 1.41 | 0.53 | 3.34 |
| EGYPT | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.99 | 1.00 | 0.96 | -0.15 | 0.91 | 0.64 | 0.19 | -1.06 |
| FRANCE | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.96 | 1.00 | 1.00 | -0.45 | 1.04 | 0.31 | 0.20 | -2.18 |
| GERMANY | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.97 | 1.00 | 0.91 | 0.18 | 1.11 | 0.95 | 0.31 | -5.13 |
| INDIA | 0.76 | 0.55 | 0.75 | 0.72 | 0.55 | 0.52 | 0.81 | -0.04 | 0.64 | 0.77 | -0.05 | 0.93 | 0.48 | -0.01 | -2.02 |
| ISRAEL | 0.65 | 0.26 | 0.62 | 0.64 | 0.28 | 0.23 | 0.58 | 0.76 | 0.63 | 1.00 | 0.62 | 0.85 | 0.93 | 0.52 | -5.61 |
| ITALY | 1.00 | 1.00 | 1.00 | 0.88 | 1.00 | 0.87 | 1.00 | 0.36 | 1.00 | 0.80 | 0.11 | 1.00 | 0.85 | 0.54 | -5.98 |
| KAZAKHSTAN | 0.95 | 0.91 | 0.95 | 0.91 | 0.92 | 0.88 | 1.00 | 0.63 | 0.93 | 0.96 | 0.64 | 0.99 | 1.39 | 0.29 | -1.57 |
| KUWAIT | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.11 | 1.00 | 1.00 | -0.24 | 0.92 | 1.59 | 0.35 | 0.13 |
| OMAN | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.07 | 1.00 | 1.00 | 0.37 | 0.94 | 2.18 | 0.18 | 0.10 |
| OTHER_AMERICAS_AFRICA | 0.71 | 0.47 | 0.71 | 0.62 | 0.48 | 0.40 | 0.80 | -0.10 | 0.69 | 1.00 | -1.30 | 0.90 | 0.60 | 0.24 | -1.00 |
| OTHER_ASIA_PACIFIC | 0.17 | 0.00 | 0.16 | 0.16 | 0.00 | 0.00 | 0.16 | 0.21 | 0.40 | 0.62 | -0.87 | 0.79 | 0.40 | 0.46 | -4.72 |
| OTHER_EURASIA | 0.89 | 0.80 | 0.93 | 0.80 | 0.86 | 0.74 | 1.00 | 0.55 | 0.87 | 1.00 | -0.81 | 0.90 | 1.07 | 0.08 | -2.17 |
| OTHER_EUROPE | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.95 | 1.00 | 0.60 | 1.22 | 1.30 | -0.17 | 0.39 | -8.29 |
| OTHER_MENA | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.09 | 1.00 | 1.00 | -0.50 | 1.24 | 0.72 | 0.27 | 0.84 |
| PHILIPPINES | 0.56 | 0.38 | 0.46 | 0.72 | 0.25 | 0.57 | 0.19 | 0.91 | 0.57 | 0.76 | -0.22 | 0.75 | 0.78 | 0.24 | 2.97 |
| RUSSIAN FEDERATION | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.01 | 1.00 | 1.00 | 0.70 | 1.03 | 0.05 | 0.26 | -6.05 |
| SAUDI ARABIA | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.04 | 1.00 | 1.00 | 1.68 | 0.97 | 0.77 | 0.53 | -1.09 |
| UNITED KINGDOM | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | -0.03 | 0.00 | 1.00 | -0.61 | 0.68 | 0.41 | 0.21 | -0.25 |
| UNITED STATES OF AMERICA | 1.00 | 1.00 | 0.98 | 1.00 | 0.98 | 1.00 | 0.97 | 0.95 | 1.00 | 0.51 | -0.53 | 0.80 | 0.81 | 0.44 | -2.09 |

## C: independence of the detrended inputs

Last fold's training window, daily deviations from each input's trailing 91-day mean.

pooled correlation:

| input | flights | gauge | airlines | premium_share |
| --- | --- | --- | --- | --- |
| flights | 1.00 | -0.09 | 0.49 | -0.21 |
| gauge | -0.09 | 1.00 | -0.13 | 0.20 |
| airlines | 0.49 | -0.13 | 1.00 | -0.34 |
| premium_share | -0.21 | 0.20 | -0.34 | 1.00 |

VIF:

| input | VIF |
| --- | --- |
| flights | 1.32 |
| gauge | 1.05 |
| airlines | 1.42 |
| premium_share | 1.16 |

median within-market correlation:

| input | flights | gauge | airlines | premium_share |
| --- | --- | --- | --- | --- |
| flights | 1.00 | -0.08 | 0.45 | -0.16 |
| gauge | -0.08 | 1.00 | -0.17 | 0.40 |
| airlines | 0.45 | -0.17 | 1.00 | -0.22 |
| premium_share | -0.16 | 0.40 | -0.22 | 1.00 |

## L: does the sigmoid alone give the cut and increase asymmetry?

Implied P2P slope for a 14% seat cut and increase at each market's training P2P rate, by usual total-pax LF band (last fold). Measured total-pax cut slopes by band were 0.51 / 0.77 / 0.93 / 0.97, increases 0.89 to 0.98.

| usual LF | markets | usual_lf | p2p_rate | b | slope_cut | slope_increase |
| --- | --- | --- | --- | --- | --- | --- |
| <75 | 4 | 0.695 | 0.414 | -0.322 | 0.768 | 0.759 |
| 75-85 | 7 | 0.799 | 0.474 | 0.181 | 1.116 | 1.093 |
| 85-92 | 7 | 0.877 | 0.365 | 0.058 | 0.985 | 0.976 |
| >92 | 2 | 0.951 | 0.166 | -0.759 | 0.331 | 0.321 |

## Guests level bias

Per fold (pct):

| model | origin_2024-02-01 | origin_2024-03-01 | origin_2024-04-01 | origin_2024-05-01 | origin_2024-06-01 | origin_2024-07-01 | origin_2024-08-01 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BASE | -7.5 | -7.5 | -7.3 | -7.1 | -8.4 | -6.9 | -5.7 |
| A | -8.7 | -9.9 | -8.1 | -7.6 | -8.7 | -7.3 | -5.3 |
| A_updown | -8.2 | -9.9 | -8.1 | -7.6 | -8.8 | -7.3 | -5.3 |
| A2 | -8.4 | -9.7 | -7.9 | -7.4 | -8.7 | -7.1 | -5.1 |
| L | -10.3 | -9.8 | -8.9 | -8.3 | -8.5 | -7.4 | -5.5 |
| TS | -8.7 | -11.1 | -8.6 | -8.8 | -9.5 | -8.2 | -6.4 |
| B | -0.6 | -5.4 | -4.2 | -5.5 | -5.5 | -5.6 | -5.4 |
| C | -8.8 | -11.2 | -9.0 | -7.6 | -9.7 | -8.6 | -6.5 |
| A_oracle | -9.1 | -6.8 | -7.0 | -5.3 | -7.4 | -5.7 | -5.1 |

Per market, all folds (pct):

| model | CHINA | OTHER_EURASIA | PHILIPPINES | UNITED KINGDOM |
| --- | --- | --- | --- | --- |
| BASE | -14.2 | -31.8 | -21.1 | -17.0 |
| A | -20.0 | -32.2 | -20.3 | -15.4 |
| A_updown | -20.0 | -32.2 | -20.4 | -15.3 |
| A2 | -20.2 | -32.4 | -20.5 | -15.4 |
| L | -19.2 | -32.7 | -20.8 | -17.8 |
| TS | -20.0 | -32.2 | -21.4 | -16.4 |
| B | -14.1 | -28.9 | -20.1 | -15.5 |
| C | -23.5 | -32.3 | -20.5 | -15.0 |
| A_oracle | -10.9 | -32.2 | -19.9 | -0.5 |

## B: the learned U (last fold)

| seats_rel_from | seats_rel_to | p2p_per_seat |
| --- | --- | --- |
| 0.000 | 0.654 | 0.430 |
| 0.654 | 0.779 | 0.368 |
| 0.779 | 0.840 | 0.329 |
| 0.840 | 0.935 | 0.403 |
| 0.935 | 0.998 | 0.324 |
| 0.998 | 1.064 | 0.297 |
| 1.064 | 1.123 | 0.399 |
| 1.123 | 1.203 | 0.376 |
| 1.203 | 1.346 | 0.527 |
| 1.346 | inf | 0.434 |

## Link 0 residual checks

1. bias: mean residual per bin of each input and of time, 95% CI clustered on market x 28-day block; a bin is flagged when its CI clears 0 by more than FLAG (log points, about 2%). 2. memory: ACF to lag 28 days / 8 weeks and Ljung-Box per market-fold series. 3. spread: residual sd per quintile of fitted level and of seat deviation. 4. shape: skew, excess kurtosis, share beyond 3 sd, Q-Q plot. Passing: check 1 with no flagged bin; check 2 with Ljung-Box p >= 0.05 in at least half of the weekly market-fold series.

Charts: `out/residuals/<variant>_*.png` (not committed).

| variant | 1 bias: flagged bins | 1 pass | 2 ACF day 1 / 7 | 2 ACF week 1 / 4 | 2 LB p>=0.05 share (week) | 2 pass | 3 sd ratio level / seat | 4 skew / ex.kurt (week) | 4 beyond 3 sd (week) | clean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 39 | False | 0.48 / 0.37 | 0.49 / -0.08 | 0.46 | False | 2.60 / 1.22 | -0.13 / 1.78 | 0.01 | False |
| A_updown | 39 | False | 0.48 / 0.37 | 0.49 / -0.08 | 0.46 | False | 2.61 / 1.22 | -0.14 / 1.78 | 0.01 | False |
| A2 | 39 | False | 0.48 / 0.37 | 0.49 / -0.08 | 0.46 | False | 2.64 / 1.22 | -0.14 / 1.84 | 0.01 | False |
| L | 49 | False | 0.51 / 0.42 | 0.54 / -0.04 | 0.44 | False | 2.11 / 1.24 | -0.60 / 2.32 | 0.02 | False |
| TS | 28 | False | 0.48 / 0.37 | 0.49 / -0.08 | 0.45 | False | 2.50 / 1.22 | -0.23 / 1.93 | 0.01 | False |
| B | 79 | False | 0.40 / 0.48 | 0.57 / -0.00 | 0.31 | False | 1.70 / 1.22 | -0.46 / -0.60 | 0.00 | False |
| C | 29 | False | 0.52 / 0.36 | 0.48 / -0.08 | 0.50 | True | 2.18 / 1.10 | -0.11 / 2.10 | 0.01 | False |

A: 39 flagged bins, the largest (mean log residual):

- day: market = ISRAEL (-0.626)
- week: market = CHINA (+0.374)
- day: market = CHINA (+0.290)
- day: market = ITALY (-0.275)
- week: market = ITALY (-0.272)
- day: market = OTHER_ASIA_PACIFIC (-0.244)
- week: month = 1 (-0.232)
- week: market = OTHER_ASIA_PACIFIC (-0.222)

A_updown: 39 flagged bins, the largest (mean log residual):

- day: market = ISRAEL (-0.628)
- week: market = CHINA (+0.376)
- day: market = CHINA (+0.289)
- day: market = ITALY (-0.274)
- week: market = ITALY (-0.271)
- day: market = OTHER_ASIA_PACIFIC (-0.244)
- week: month = 1 (-0.231)
- week: market = OTHER_ASIA_PACIFIC (-0.222)

A2: 39 flagged bins, the largest (mean log residual):

- day: market = ISRAEL (-0.645)
- week: market = CHINA (+0.411)
- day: market = CHINA (+0.315)
- day: market = ITALY (-0.264)
- week: market = ITALY (-0.260)
- day: market = OTHER_ASIA_PACIFIC (-0.240)
- week: month = 1 (-0.232)
- week: market = OTHER_ASIA_PACIFIC (-0.218)

L: 49 flagged bins, the largest (mean log residual):

- day: market = ISRAEL (-1.009)
- week: market = ISRAEL (-0.710)
- week: market = CHINA (+0.413)
- day: market = ITALY (-0.277)
- week: market = ITALY (-0.272)
- day: month = 11 (-0.260)
- day: market = CHINA (+0.256)
- week: month = 11 (-0.252)

TS: 28 flagged bins, the largest (mean log residual):

- day: market = ISRAEL (-0.623)
- week: market = CHINA (+0.374)
- day: market = CHINA (+0.289)
- day: market = ITALY (-0.259)
- week: market = ITALY (-0.257)
- week: month = 1 (-0.211)
- day: month = 1 (-0.184)
- day: year = 2025 (-0.184)

B: 79 flagged bins, the largest (mean log residual):

- day: market = UNITED STATES OF AMERICA (-1.567)
- week: market = UNITED STATES OF AMERICA (-1.551)
- day: market = OTHER_AMERICAS_AFRICA (-1.295)
- day: market = OTHER_ASIA_PACIFIC (-1.248)
- week: market = OTHER_ASIA_PACIFIC (-1.242)
- week: market = OTHER_AMERICAS_AFRICA (-1.230)
- day: market = ISRAEL (-0.809)
- day: usual LF band = (0.92, 2.0] (-0.714)

C: 29 flagged bins, the largest (mean log residual):

- day: market = ISRAEL (-0.715)
- week: market = CHINA (+0.387)
- day: market = CHINA (+0.359)
- week: month = 1 (-0.243)
- day: market = ITALY (-0.238)
- week: market = ITALY (-0.233)
- day: market = OTHER_ASIA_PACIFIC (-0.223)
- day: month = 1 (-0.216)

## Scenario sanity

Last fold's models, seats +-10% on 2024-10-01..2024-10-28. P2P and LF (P2P per seat) over the window; arrivals and guests over the window plus 28 days (pct). via: C reads flights and gauge separately; other variants see seats only.

| variant | market | seats | via | p2p_pct | lf_base_pct | lf_pp | arrivals_pct | guests_pct | u_position |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASE | UNITED KINGDOM | +10% | gauge |  |  |  | 1.76 | 1.75 |  |
| BASE | UNITED KINGDOM | -10% | gauge |  |  |  | -1.76 | -1.75 |  |
| BASE | INDIA | +10% | gauge |  |  |  | 2.12 | 2.20 |  |
| BASE | INDIA | -10% | gauge |  |  |  | -2.12 | -2.20 |  |
| BASE | CHINA | +10% | gauge |  |  |  | 0.81 | 0.67 |  |
| BASE | CHINA | -10% | gauge |  |  |  | -0.81 | -0.67 |  |
| A | UNITED KINGDOM | +10% | gauge | 2.52 | 23.49 | -1.60 | 1.47 | 1.33 |  |
| A | UNITED KINGDOM | -10% | gauge | -2.59 | 23.49 | 1.93 | -1.47 | -1.33 |  |
| A | INDIA | +10% | gauge | 8.16 | 49.57 | -0.83 | 2.38 | 2.41 |  |
| A | INDIA | -10% | gauge | -8.29 | 49.57 | 0.94 | -2.42 | -2.45 |  |
| A | CHINA | +10% | gauge | 6.53 | 15.45 | -0.49 | 0.47 | 0.37 |  |
| A | CHINA | -10% | gauge | -6.70 | 15.45 | 0.57 | -0.48 | -0.37 |  |
| A_updown | UNITED KINGDOM | +10% | gauge | 2.52 | 23.49 | -1.60 | 1.47 | 1.33 |  |
| A_updown | UNITED KINGDOM | -10% | gauge | -2.59 | 23.49 | 1.93 | -1.47 | -1.33 |  |
| A_updown | INDIA | +10% | gauge | 8.08 | 49.58 | -0.87 | 2.39 | 2.41 |  |
| A_updown | INDIA | -10% | gauge | -8.04 | 49.58 | 1.08 | -2.37 | -2.40 |  |
| A_updown | CHINA | +10% | gauge | 6.65 | 15.40 | -0.47 | 0.50 | 0.38 |  |
| A_updown | CHINA | -10% | gauge | -6.06 | 15.40 | 0.67 | -0.46 | -0.35 |  |
| A2 | UNITED KINGDOM | +10% | gauge | 2.48 | 23.50 | -1.61 | 1.53 | 1.38 |  |
| A2 | UNITED KINGDOM | -10% | gauge | -2.25 | 23.50 | 2.02 | -1.39 | -1.25 |  |
| A2 | INDIA | +10% | gauge | 7.04 | 49.85 | -1.34 | 2.78 | 2.68 |  |
| A2 | INDIA | -10% | gauge | -2.99 | 49.85 | 3.88 | -1.41 | -1.29 |  |
| A2 | CHINA | +10% | gauge | 7.64 | 15.23 | -0.33 | 0.59 | 0.45 |  |
| A2 | CHINA | -10% | gauge | -4.39 | 15.23 | 0.95 | -0.36 | -0.28 |  |
| L | UNITED KINGDOM | +10% | gauge | 6.42 | 23.49 | -0.76 | 2.69 | 2.64 |  |
| L | UNITED KINGDOM | -10% | gauge | -6.64 | 23.49 | 0.88 | -2.76 | -2.72 |  |
| L | INDIA | +10% | gauge | 9.80 | 51.09 | -0.09 | 3.50 | 3.64 |  |
| L | INDIA | -10% | gauge | -9.82 | 51.09 | 0.10 | -3.51 | -3.65 |  |
| L | CHINA | +10% | gauge | 3.90 | 11.71 | -0.65 | 0.31 | 0.23 |  |
| L | CHINA | -10% | gauge | -4.09 | 11.71 | 0.77 | -0.32 | -0.24 |  |
| TS | UNITED KINGDOM | +10% | gauge | 2.52 | 23.49 | -1.60 | 1.47 | 1.33 |  |
| TS | UNITED KINGDOM | -10% | gauge | -2.59 | 23.49 | 1.93 | -1.47 | -1.33 |  |
| TS | INDIA | +10% | gauge | 6.92 | 46.88 | -1.31 | 1.83 | 1.88 |  |
| TS | INDIA | -10% | gauge | -7.12 | 46.88 | 1.50 | -1.87 | -1.93 |  |
| TS | CHINA | +10% | gauge | 6.39 | 15.46 | -0.51 | 0.47 | 0.36 |  |
| TS | CHINA | -10% | gauge | -6.57 | 15.46 | 0.59 | -0.48 | -0.37 |  |
| B | UNITED KINGDOM | +10% | gauge | 46.73 | 37.62 | 12.56 | 2.07 | 2.13 | 1.11 -> 1.22 |
| B | UNITED KINGDOM | -10% | gauge | -23.10 | 37.62 | -5.47 | -1.03 | -1.05 | 1.11 -> 1.00 |
| B | INDIA | +10% | gauge | 2.60 | 47.44 | -3.19 | 0.32 | 0.33 | 1.32 -> 1.45 |
| B | INDIA | -10% | gauge | -14.53 | 47.44 | -2.39 | -1.84 | -1.90 | 1.32 -> 1.18 |
| B | CHINA | +10% | gauge | 24.32 | 39.65 | 5.16 | 4.17 | 3.48 | 0.95 -> 1.05 |
| B | CHINA | -10% | gauge | -11.46 | 39.65 | -0.64 | -1.96 | -1.64 | 0.95 -> 0.86 |
| C | UNITED KINGDOM | +10% | gauge | 5.03 | 22.83 | -1.03 | 1.68 | 1.56 |  |
| C | UNITED KINGDOM | +10% | flights | 7.29 | 22.83 | -0.56 | 1.98 | 1.87 |  |
| C | UNITED KINGDOM | -10% | gauge | -5.20 | 22.83 | 1.22 | -1.73 | -1.60 |  |
| C | UNITED KINGDOM | -10% | flights | -7.44 | 22.83 | 0.65 | -2.02 | -1.91 |  |
| C | INDIA | +10% | gauge | 5.55 | 48.52 | -1.96 | 1.76 | 1.74 |  |
| C | INDIA | +10% | flights | 9.41 | 48.52 | -0.26 | 2.27 | 2.34 |  |
| C | INDIA | -10% | gauge | -5.73 | 48.52 | 2.30 | -1.80 | -1.78 |  |
| C | INDIA | -10% | flights | -9.45 | 48.52 | 0.29 | -2.28 | -2.35 |  |
| C | CHINA | +10% | gauge | 13.56 | 15.49 | 0.50 | 0.86 | 0.74 |  |
| C | CHINA | +10% | flights | 8.97 | 15.49 | -0.14 | 0.62 | 0.53 |  |
| C | CHINA | -10% | gauge | -13.17 | 15.49 | -0.54 | -0.84 | -0.71 |  |
| C | CHINA | -10% | flights | -9.04 | 15.49 | 0.16 | -0.63 | -0.54 |  |
