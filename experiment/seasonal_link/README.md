# Seasonal link

## Question

`eda_coupling` found the P2P to arrivals slope about twice as strong in January to June as in July to December. Does the flight to hotel-arrival link change strength with the season? If so, does a seasonal strength on the chain's seat kernel (link 1) improve the planning chain and its seat lever?

Run at commit a1cb579. The shipped chain reproduces exactly at a1cb579 and at 67c6a48 (fold 0 predictions, max difference 0). The new market events of f8117fa are not in the chain's event list. International markets. Every panel is cut at 2025-01-31, the end of VALIDATION_ORIGINS. FROZEN_TEST is not read, so the 2025 H1 half of `eda_coupling` is not used here.

## Method

Step 1 (graphs). Weekly market series, 20 international markets, 2023-01 to 2025-01-31. Log residual = log - centred 13-week mean - 4-harmonic annual season, per market and series. The week-of-year season of `eda_coupling` is kept as a check. With two years it makes the 2023 and 2024 residuals mirror images. Slopes are pooled over markets. Intervals are 90% bootstraps that resample calendar weeks, all markets of a week together. Lunar weeks touch a Ramadan, Eid al-Fitr or Eid al-Adha window in `events.csv`. Step 1(d) fits the shipped chain to 2025-01-31. It regresses the weekly arrival deviation from its 13-week trend on the seat deviation, for observed arrivals, link-1 arrivals and their log ratio (the residual).

Step 2 (model). Link 1 becomes `arrivals = c_t + exp(s(t)) * sum_k w_k seats_{t-k}`. s(t) is a one-hot of the project season (`season`) or 1 or 2 annual sine/cosine pairs (`fourier1`, `fourier2`). It has mean zero over the training rows and a ridge `r * n * |theta|^2`, r in {0.001, 0.01, 0.1, 1}. Everything else is `CHAIN_SPECS["seat_chain"]`. `SeasonalSeatKernel` subclasses `SeatKernel`. Backfitting alternates a kernel step and an s step, as `level_memory/drift.py` does. Nothing in `src/` changed.

Gate: `compare()` against the shipped chain on VALIDATION_ORIGINS, daily and weekly WAPE. A pass needs -0.3 pp or better, an interval below 0 and 4 of 7 folds better. The choice is the best mean daily WAPE, then the simplest within 0.2 pp. Back-test: the natural-experiment design and lever code of `scenario_response` (copied). TIME-ONLY is `CalendarRidge`, refitted per fold.

## How to run

```bash
export PYTHONPATH=<repo>/src TWIN_LAKE_DIR=<repo>/lake      # daily_market_panel.parquet must be in the lake
cd experiment/seasonal_link
python graphs.py             # step 1 (a) to (c): out/1_pooled.png, 2_markets.png, 3_robustness.png
python chain_residual.py     # step 1 (d): out/4_chain_residual.png (one chain fit, about 3 min)
python run.py shipped,season_r0.001,season_r0.01,season_r0.1,season_r1,fourier1_r0.001,fourier1_r0.01,fourier1_r0.1,fourier1_r1,fourier2_r0.001,fourier2_r0.01,fourier2_r0.1,fourier2_r1
python run.py fourier1_r0.001,season_r0.1,season_r0.001 full   # strengths on every day to 2025-01-31
python report.py             # results.md
```

The grid is 91 chain fits, about 4 hours on 9 workers. Seasonal fits take 1.2 to 13 times longer than the shipped fit.

| File | Responsibility |
| --- | --- |
| `data.py` | daily and weekly panels cut at 2025-01-31, folds, lunar-event weeks, centred trends |
| `residuals.py` | time-removed weekly residuals (Fourier and week-of-year season) |
| `slopes.py` | slopes by group and contrasts with the week-cluster bootstrap |
| `graphs.py` | step 1 (a) to (c) charts and tables |
| `chain_residual.py` | step 1 (d): link-1 residual against seat deviation |
| `seasonal_kernel.py` | `SeasonalSeatKernel` and the chain spec that uses it |
| `variants.py` | shipped chain and the seasonal grid |
| `schedules.py` | counterfactual seat schedules (copied from `scenario_response/chain_runs.py`) |
| `run.py` | fits per variant and fold, cached predictions and strengths |
| `lever.py` | natural-experiment weeks and scoring (copied from `scenario_response`) |
| `scoring.py` | gate scores, compare(), choice and selection check |
| `backtest.py` | natural-experiment back-test with TIME-ONLY and by season |
| `strengths.py` | learned strengths per season with intervals |
| `report.py` | results.md |

## Results

Full tables in [results.md](results.md).

### Step 1: graphs

Pooled residual slope by project season, 90% intervals:

| Link | Winter peak | Spring shoulder | Summer trough | Autumn shoulder | Jan-Jun minus Jul-Dec |
| --- | --- | --- | --- | --- | --- |
| P2P to arrivals | 0.82 [0.71, 0.93] | 0.74 [0.63, 0.86] | 0.43 [0.32, 0.54] | 0.45 [0.30, 0.57] | +0.37 [+0.25, +0.50] |
| Seats to arrivals | 0.94 [0.58, 1.30] | 1.00 [0.56, 1.50] | 0.90 [0.57, 1.24] | 0.01 [-0.28, 0.33] | +0.88 [+0.49, +1.30] |
| Arrivals to guests | 0.82 | 0.81 | 0.85 | 0.84 | -0.05 [-0.09, -0.01] |

- `1_pooled.png`. P2P to arrivals is a smooth annual curve: about 1.0 in January to March, 0.70 to 0.79 in April to June, 0.24 in July and August, 0.43 to 0.64 in September to December. Seats to arrivals is noisy (correlation 0.1 to 0.35 per month). It is 0.76 to 1.71 from February to August, near 0 in September and October, and 0.34 to 0.46 in November and December. Arrivals to guests is flat at 0.74 to 0.90.
- Half-years, seats to arrivals: 2023 H1 0.67, 2023 H2 0.47, 2024 H1 1.56, 2024 H2 0.05. The gap is small in 2023 and large in 2024. P2P to arrivals: 0.86, 0.62, 0.82, 0.30.
- `2_markets.png`. Six largest markets, P2P link. Weaker in summer for the UK (0.52 against 0.85 to 1.01), India (0.20) and Russia (-0.05). Germany: Jan-Jun minus Jul-Dec +0.35 [+0.13, +0.56]. China and Saudi Arabia show no pattern. Per market, the seats link has intervals several units wide: seat residual sd is 0.01 to 0.04 for the UK, India and Saudi Arabia.
- `3_robustness.png`. Not driven by one market or by lunar events. Leaving out one market, the Jan-Jun minus Jul-Dec contrast stays at 0.33 to 0.42 (P2P) and 0.74 to 1.00 (seats). Without lunar weeks it is +0.41 [+0.29, +0.55] and +0.80 [+0.37, +1.19]. With the week-of-year season, the P2P contrast shrinks to +0.19 [+0.04, +0.33].
- `4_chain_residual.png`. The chain already responds by season. Its link-1 slope on seat deviation is 1.24 in winter, 1.10 in spring, 0.54 in summer and 0.45 in autumn: the base stock c_t changes the kernel share. What it misses is summer +0.36 [+0.07, +0.61] (too little response) and autumn -0.28 [-0.54, -0.04] (too much). Winter is +0.10 and spring +0.06, both intervals include 0. The residual's Jan-Jun minus Jul-Dec contrast is +0.17 [-0.05, +0.39].

Verdict on step 1. A seasonal strength is supported for P2P to arrivals, as a smooth annual curve or by season. Monthly values are too noisy to use one by one. For seats, the simulator's input, only autumn is weak, and the pattern differs between 2023 and 2024. The chain's fixed kernel already gives a seasonal elasticity. Its residual asks for more summer response and less autumn response, not the January-to-June against July-to-December split. Step 2 was run because those two residual intervals exclude 0.

### Gate (VALIDATION_ORIGINS, international, 7 folds)

| Variant | Daily WAPE | Delta pp [90%] | Folds better | Weekly WAPE | Delta pp [90%] | Level bias % | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| shipped | 20.67 | | | 18.69 | | -6.0 | |
| fourier1_r0.001 (chosen) | 20.59 | -0.08 [-0.17, +0.01] | 4/7 | 18.64 | -0.06 [-0.15, +0.04] | -6.1 | fail |
| season_r0.1 | 20.64 | -0.02 [-0.12, +0.09] | 5/7 | 18.66 | -0.02 [-0.15, +0.10] | -5.5 | fail |
| season_r0.01 | 20.99 | +0.33 [-0.11, +0.78] | 2/7 | 18.96 | +0.28 [-0.23, +0.81] | -3.2 | fail |
| season_r0.001 | 21.19 | +0.53 [+0.09, +1.01] | 0/7 | 19.23 | +0.55 [+0.02, +1.10] | -3.6 | fail |
| fourier2_r0.001 | 20.83 | +0.14 [-0.01, +0.33] | 3/7 | 18.88 | +0.18 [-0.03, +0.41] | -5.7 | fail |

Fourier ridges 0.01 to 1 and the season ridge 1 are within 0.01 pp of the shipped chain: the strength stays at 1. Chosen on the first 4 folds only (`season_r0.1`), the last 3 folds give +0.08 pp [-0.04, +0.17]. The least-shrunk variants lose up to 0.5 pp. Backfitting stops at the iteration cap more often: 164 of 280 market-link fits for `fourier1_r0.001`, 32 for the shipped chain.

### Learned strengths, exp(a) per season

Full fit to 2025-01-31, median over 20 markets [90% bootstrap over markets]. Last column: what the step 1(d) graph asks for (actual / chain slope).

| Season | fourier1_r0.001 | season_r0.1 | season_r0.001 | Fold medians, season_r0.001 | Graph |
| --- | --- | --- | --- | --- | --- |
| Winter peak | 0.99 [0.99, 1.01] | 1.00 [0.99, 1.00] | 0.94 [0.91, 1.01] | 0.93 to 0.98 | 1.09 |
| Spring shoulder | 1.13 [0.88, 1.18] | 1.00 [1.00, 1.01] | 1.04 [0.88, 1.05] | 0.94 to 1.06 | 1.05 |
| Summer trough | 1.01 [0.99, 1.01] | 1.00 [0.99, 1.02] | 1.04 [0.90, 1.29] | 0.96 to 1.03 | 1.84 |
| Autumn shoulder | 0.89 [0.85, 1.13] | 1.01 [1.00, 1.01] | 1.08 [1.02, 1.27] | 1.16 to 1.21 | 0.35 |

The pooled strengths stay within 0.89 to 1.13. They do not match the graphs: the summer boost is absent, and the least-shrunk fit raises autumn instead of cutting it. Per market they disagree in sign. In winter `season_r0.001` gives the UK 0.68 and India 1.34; in summer Saudi Arabia 0.62 and Russia 1.26. Under `fourier1_r0.001`, China's fold fits range from 0.10 to 16.9. With 12 to 18 months of seat history per fold, s(t) competes with the annual season and the 60-day base knots for the same calendar variation.

### Natural-experiment back-test, same week a year earlier

MAE on log guest change, 717 market-weeks (624 increases, 93 cuts). The shipped CHAIN and TIME-ONLY rows reproduce `scenario_response`.

| Model | All | Increases | Cuts | Winter | Spring | Summer | Autumn |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TIME-ONLY | 0.276 | 0.240 | 0.515 | 0.327 | 0.290 | 0.219 | 0.240 |
| CHAIN (shipped) | 0.210 | 0.186 | 0.373 | 0.239 | 0.195 | 0.166 | 0.235 |
| fourier1_r0.001 | 0.211 | 0.188 | 0.369 | 0.237 | 0.192 | 0.169 | 0.243 |
| season_r0.1 | 0.211 | 0.187 | 0.372 | 0.240 | 0.197 | 0.167 | 0.236 |
| season_r0.001 | 0.214 | 0.188 | 0.387 | 0.238 | 0.209 | 0.166 | 0.241 |

Paired MAE differences, 90% block bootstrap:

| Comparison | All | Increases | Cuts |
| --- | --- | --- | --- |
| fourier1_r0.001 - CHAIN | +0.001 [-0.003, +0.005] | +0.002 [-0.002, +0.007] | -0.004 [-0.022, +0.020] |
| season_r0.1 - CHAIN | +0.001 [+0.001, +0.002] | +0.001 [+0.001, +0.002] | -0.000 [-0.002, +0.001] |
| season_r0.001 - CHAIN | +0.003 [-0.002, +0.010] | +0.002 [-0.003, +0.008] | +0.014 [-0.007, +0.032] |
| CHAIN - TIME-ONLY | -0.066 [-0.093, -0.043] | -0.054 [-0.084, -0.030] | -0.142 [-0.258, -0.080] |
| fourier1_r0.001 - TIME-ONLY | -0.065 [-0.092, -0.041] | -0.053 [-0.079, -0.030] | -0.147 [-0.259, -0.078] |

By season, `fourier1_r0.001` - CHAIN: spring -0.003 [-0.007, -0.001], summer +0.003 [+0.001, +0.003], autumn +0.008 [+0.004, +0.011], winter -0.001 [-0.011, +0.009]. In autumn no chain beats TIME-ONLY: CHAIN - TIME-ONLY is -0.005 [-0.009, +0.015].

Centred 13-week trend test (48 weeks, half from Israel): CHAIN 0.368, `fourier1_r0.001` 0.382 (+0.014 [+0.000, +0.024]), `season_r0.001` 0.361 (-0.008 [-0.021, +0.005]), TIME-ONLY 0.395.

## Conclusion

- The seasonal pattern is real for P2P to arrivals: strong January to June, weakest in July and August. It holds without any single market and without lunar weeks. For seats to arrivals only September and October are weak, and the split differs between 2023 and 2024.
- The shipped chain already has a seasonal seat elasticity (link-1 slope 1.24 in winter, 0.45 in autumn). Its remaining error is summer under-response and autumn over-response, not a January-to-June split.
- A learned seasonal strength fails the gate in every form and ridge. The best is -0.08 pp [-0.17, +0.01] daily. Less shrinkage lowers the level bias (-3.2% daily at season r 0.01, against -6.0%) but raises WAPE, up to +0.53 pp.
- The learned strengths do not reproduce the graphs, and per market they flip sign between markets and folds. Two years of seats cannot separate a seasonal kernel strength from the season term and the base stock.
- The back-test shows no gain on the lever. Every seasonal variant is within 0.003 MAE of the shipped chain on yoy experiments, and none beats it on increases or cuts with an interval below 0.
- Keep `CHAIN_SPECS["seat_chain"]` unchanged. The simulator's season-specific elasticities already come from the chain (`planning/schedule_response.py`).

| Setting | Value | Class |
| --- | --- | --- |
| Strength form exp(s(t)) on the seat flow, mean zero | | TAUGHT |
| s per market and fold | from training rows | LEARNED (fit) |
| Form and ridge | fourier1, r 0.001 (best; fails the gate) | LEARNED (tuned on validation) |
