# Level memory

## Question

Out-of-sample log errors remember (lag-1 ACF 0.59 domestic, 0.77 international market-day) and several international markets keep a same-sign bias across folds. Can the forecast use that memory?

1. Error carry-forward: scale the forecast by the recent error, decaying with the horizon. Tried on the daily nowcast (`twin_daily`) and the planning chain (`CHAIN_SPECS["seat_chain"]`).
2. Drifting strength: let the arrivals kernel's total weight drift slowly, so guests per arrival can move over time. Tried on the daily nowcast.

Run at commit e015fdd. Shipped specs: `INTL_NOWCAST` with 45-day base knots, `DOMESTIC_NOWCAST` with 365-day knots, chain link 1 at 60 days and link 2 at 45 days.

## Variants

Carry-forward: forecast = model x exp(e_0 rho^h), h = days since the last known day.

| Setting | Grid |
| --- | --- |
| k: days in e_0 | 7, 14, 28 |
| e_0 source | `in`: the scored fit's in-sample residuals; `hb`: a fit that ends 28 days earlier, scored on those 28 days |
| rho | `mkt`: training-residual lag-1 ACF per market; `pool`: pooled per series; `hb`: lag-1 ACF of the held-back errors; `one`: no decay; `wk` (chain): log of weekly sums, weekly ACF |
| echo | adds each weekday's deviation from e_0, decaying at the lag-7 ACF in excess of rho^7 |

Drift: flow_t = c_t + exp(s(t)) x sum_k w_k A_{t-k}. s(t) is piecewise linear on knots every 90 or 182 days, mean zero over the training rows, with a first-difference penalty lambda x n / knots in {0.01, 0.1, 1, 10}. Beyond the training days s is held at its last value or decays to 0 with a half-life of 30 or 90 days. It is a subclass of the arrivals kernel (`drift.py`); nothing in `src/` changed. Each backfitting call runs a kernel step with s fixed, then an s step with w and c fixed; each step keeps its result only if the objective does not rise.

Control: the time-only specs (`DOMESTIC_TIME`, `INTL_TIME`, no arrivals) on the same folds. R2 vs time is 1 - SSE / SSE of the control on the same rows.

The protocol trains 21 days before each origin, not at the origin. So h is at least 22 on the first test day, and carry-forward decays before it is scored. `gap0` reruns the same origins with training up to the day before the origin. That matches production, where guests are known up to the test period. It is exploratory and is not gated.

## How to run

```bash
export PYTHONPATH=src:experiment/level_memory TWIN_LAKE_DIR=<repo>/lake
python experiment/level_memory/run.py base,drift   # 126 fits, caches out/runs/ (about 1.5 h on 9 workers)
python experiment/level_memory/run.py combined     # optional: held-back fits of CHOSEN_DRIFT for drift + carry
python experiment/level_memory/report.py           # writes results.md
python experiment/level_memory/refit.py shipped,drift  # one-market international refits, caches out/refits/ (about 3 min)
python experiment/level_memory/graphs.py           # Israel graphs, out/israel/*.png
python experiment/level_memory/fix_report.py       # held-value rules; appends the Israel section to results.md
```

| File | Responsibility |
| --- | --- |
| `data.py` | panel, splitters (protocol, gap0), fit windows, training-row rule |
| `variants.py` | shipped nowcast and chain, time-only control, drift grid |
| `drift.py` | `DriftingKernel`: the arrivals kernel with a drifting strength |
| `carry.py` | e_0, rho and the carry-forward adjustment |
| `run.py` | fits per fold and window, caches predictions and fit reports |
| `scoring.py` | WAPE, compare(), bias, MAE, RMSE, R2 vs time, horizons, weekly sums, bias by market |
| `report.py` | carry-forward grid, drift grid, selection, identifiability, results.md |
| `refit.py` | one-market refits of the international nowcast and drift, to read w, c_t and s(t) |
| `graphs.py` | the Israel graphs (a to d) |
| `shock.py` | arrival collapse: last 90 days of arrivals over the same days a year earlier |
| `fixes.py` | held-value rules for s(t) beyond the training days |
| `fix_report.py` | scores the rules, the Israel section of results.md |

## Results

VALIDATION_ORIGINS, 7 folds, market-day WAPE (mean over folds). Delta from `compare()` against the shipped model, pp, negative is better. Full tables in [results.md](results.md).

### Daily nowcast

| Series | Model | WAPE | Delta [90% CI] | Folds better | Bias % | MAE | RMSE | R2 vs time | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Domestic | shipped | 4.18 | | | -0.6 | 695 | 1102 | 0.76 | |
| Domestic | carry `cf_k7_in_pool` | 4.18 | -0.00 [-0.00, +0.00] | 3/7 | -0.6 | 695 | 1102 | 0.76 | fail |
| Domestic | drift `drift_k182_l1` | 4.14 | -0.04 [-0.08, -0.01] | 6/7 | -0.4 | 689 | 1085 | 0.76 | fail |
| Domestic | time only | 10.09 | +5.88 [+4.23, +7.72] | 0/7 | +6.0 | 1674 | 2234 | 0 | |
| International | shipped | 9.62 | | | -2.3 | 110 | 169 | 0.93 | |
| International | carry `cf_k28_in_one` | 9.54 | -0.08 [-0.25, +0.10] | 4/7 | -1.5 | 109 | 167 | 0.93 | fail |
| International | drift `drift_k182_l0.1` | 9.30 | -0.33 [-0.47, -0.19] | 7/7 | -1.7 | 106 | 164 | 0.93 | pass |
| International | time only | 29.74 | +20.04 [+18.64, +21.44] | 0/7 | -0.8 | 339 | 627 | 0 | |

WAPE by horizon (days since the origin), international:

| Model | 1-7 | 8-30 | 31+ |
| --- | --- | --- | --- |
| shipped | 7.91 | 8.71 | 9.78 |
| carry `cf_k28_in_one` | 8.04 | 8.84 | 9.65 |
| drift `drift_k182_l0.1` | 7.71 | 8.40 | 9.44 |

### Planning chain (international)

| Model | Daily WAPE | Delta [90% CI] | Weekly WAPE | Level bias % | R2 vs time | Gate |
| --- | --- | --- | --- | --- | --- | --- |
| shipped | 20.67 | | 18.69 | -6.0 | 0.57 | |
| carry `cf_k7_in_pool` (best) | 20.67 | -0.00 [-0.00, +0.00] | 18.69 | -6.0 | 0.57 | fail |
| carry `cf_k28_hb_one` | 29.99 | +9.15 [+6.12, +12.21] | 28.39 | +5.3 | -0.10 | fail |
| time only | 29.74 | +8.93 [+7.10, +10.68] | 28.36 | -0.8 | 0 | |

Level bias by fold stays -3.3 to -8.6% under every carry setting.

### gap0 (exploratory)

| Series | Shipped | Best carry | Delta [90% CI] | WAPE days 1-7, shipped / carry |
| --- | --- | --- | --- | --- |
| Domestic | 4.18 | 4.11 `cf_k7_in_hb_echo` | -0.07 [-0.20, +0.02] | 3.37 / 2.37 |
| International | 9.28 | 9.25 `cf_k7_in_hb` | -0.03 [-0.04, -0.01] | 6.86 / 6.53 |
| Chain | 20.32 | 20.31 `cf_k7_in_pool` | -0.00 [-0.05, +0.03] | 16.14 / 15.95 |

### Memory at the window end

| Series | rho in-sample | rho held back | mean abs e_0 in-sample (k 28) | mean abs e_0 held back | corr(e_0 held back, test error days 1-30) |
| --- | --- | --- | --- | --- | --- |
| Domestic | 0.74 | 0.64 | 0.024 | 0.034 | -0.17 |
| International | 0.69 | 0.82 | 0.026 | 0.067 | -0.02 |
| Chain | 0.81 | 0.91 | 0.034 | 0.177 | -0.17 |

### Drift identifiability (international, `drift_k182_l0.1`)

s(t) stays within -0.14 and +0.15 (Israel and Oman are widest; most markets within +-0.08). corr(c_t, s(t)) over training days ranges from -0.61 (Germany) to +0.83 (Kuwait); the median is +0.20. Backfitting needs more passes (China 58 vs 26, Russia 79 vs 51), and every fit converged.

## Conclusion

- Carry-forward fails the gate on every series and on the chain. Under the protocol the 21-day gap decays e_0 to almost nothing. Without decay (rho = 1) it gains 0.08 pp international with an interval that includes 0.
- In-sample e_0 is small because the 45-day base knots already sit on the recent level. The held-back e_0 is 2 to 5 times larger, but it does not predict the test error (correlation -0.17 to -0.02). Carrying it forward makes every series worse (chain +9 pp).
- Without the gap, carry-forward helps the first week (domestic days 1-7: 3.37 to 2.37) but not the six-month WAPE. The error memory lives inside the forecast path, not across the origin.
- The drift passes the international gate: -0.33 pp [-0.47, -0.19], 7/7 folds. It is the best of 24 grid points on the same folds. Chosen on the first 4 folds alone it is the same setting, and it gains -0.37 pp [-0.64, -0.10] on the last 3.
- The drift fails on domestic (-0.04 pp). A ship would scope it to international, with domestic predictions identical to the shipped ones.
- Holding s at its last value beats decaying it. Decay with a 30-day half-life is worse than the shipped model.
- The drift and the base stock share the slow level (|corr| up to 0.8) but converge. The drift removes little of the persistent market bias: China, India, Philippines and Other Eurasia stay below -8% in 5 to 7 folds, and Israel goes from +1.5% to +11.1%. The Israel follow-up below fixes Israel.
- Combined: not run, because carry-forward does not help. `run.py combined` and `report.py` support it.

Bias here is sum pred / sum actual - 1, so negative means under-prediction. The background figures used log(actual / pred), the opposite sign.

| Setting | Value | Class |
| --- | --- | --- |
| Carry form exp(e_0 rho^h) | | TAUGHT |
| e_0, rho per fold | from training residuals | LEARNED (fit) |
| k, e_0 source, rho source | 7 / in / pool (domestic), 28 / in / one (international) | LEARNED (tuned on validation) |
| Drift form, mean zero, held beyond the training days | | TAUGHT |
| s(t) knot values | per market and fold | LEARNED (fit) |
| Drift knots 182 days, lambda 0.1 (international) | | LEARNED (tuned on validation) |

## Israel follow-up

### What the graphs show

Graphs are in `out/israel/` (licensed data, not committed).

- a, `a_series.png`: Israel guests per arrival rose from about 2.2 in early 2023 to 3.3 to 3.9 from April to September 2023. After 7 October 2023 arrivals fell to about 10% of the year before for four months, and the ratio stayed near 3.25. From April 2024 volumes recovered and the ratio settled at 2.6 to 3.1. The war is not flagged: Israel's only `is_one_off_period` rows are January 2022. Folds 1 to 4 end their training inside the collapse (11 January to 10 April 2024).
- b, `b_folds.png`: in folds 1 to 4 s(t) rises through 2023 and its last knot (+0.12 to +0.135) sits on war rows, which are a tenth of the normal volume but count equally in the log objective. Held flat, it lifts every test week by about 13%. Drift bias is +16% to +22% where shipped is +2% to +8%. In folds 5 to 7 a knot after the recovery pulls s back to +0.04, 0.00 and 0.00. Fold 5 is still +4.8% (shipped -1.7%); folds 6 and 7 match shipped. The base stock c_t is small (about 60 guests a day at most) in both models and is not the cause.
- c, `c_contrast.png`: Saudi Arabia, China and Other Eurasia (largest WAPE gains) have s(t) that moves steadily and keeps its direction after the training end, so holding the last value is right. In Israel the held value sits on a level the market leaves within weeks.
- d, `d_last_knot.png`: across 140 market-folds, corr(|last knot|, WAPE change) is +0.49, but 0.00 without Israel. Saudi Arabia holds +0.09 to +0.12 in folds 5 to 7 and still gains. One other point is harmful: Oman fold 5, last knot +0.15, +4.2 pp, with no collapse (arrivals 0.78 of the year before).

Supported: a held value fitted on a collapse period does not carry into the recovery. Not supported: a general harm from large last knots (cap, shrink toward the window mean), or a per-market lambda (Israel's s is smooth; its problem is where the last knot sits). Dropping the war rows from the fit alone would likely not help: the knot before it, July 2023, is +0.09, and holding +0.09 still gives +13% to +16% bias on folds 1 to 4.

### Fix

`shock_zero`: hold s at 0 (the window mean) when arrivals over the last 90 training days are below half of the same days a year earlier. Only Israel folds 1 to 6 are below 0.5 (0.11 to 0.48); every other market-fold is 0.78 or above. The fit does not change, only the held value.

| International | WAPE | Delta [90% CI] | Folds better | Bias % | Israel bias % (folds >5%) | Gate |
| --- | --- | --- | --- | --- | --- | --- |
| shipped | 9.62 | | | -2.3 | +1.5 (1) | |
| drift (held last knot) | 9.30 | -0.33 [-0.47, -0.19] | 7/7 | -1.7 | +11.1 (4) | pass |
| `shock_zero` | 9.23 | -0.39 [-0.54, -0.25] | 7/7 | -1.8 | +2.6 (2) | pass |
| `shock_shrink` (s x min(ratio, 1)) | 9.23 | -0.39 [-0.54, -0.25] | 7/7 | -1.8 | +3.8 (3) | pass |
| `cap_008` (control, clip to +-0.08) | 9.23 | -0.39 [-0.54, -0.26] | 7/7 | -1.8 | +8.0 (4) | pass |

Chosen on the first 4 folds: `shock_zero`, -0.41 pp [-0.53, -0.34], 4/4. On the last 3 folds: -0.37 pp [-0.64, -0.10], 3/3. Domestic predictions are identical to shipped. No other market's bias changes under `shock_zero`; the full table is in results.md.

Limits:

- The rule was designed after seeing Israel on these folds, and only one market-period triggers it. The gate numbers do not test it out of sample. The last-3-fold check mostly measures the drift itself.
- Israel folds 2 and 3 stay above 5% (+5.9%, +6.6%), as shipped does (+4.6%, +7.5%).
- Oman fold 5 (+11.8% bias, no collapse) is not fixed. The cap helps it but leaves Israel at +8.0%.

| Setting | Value | Class |
| --- | --- | --- |
| Hold s at 0 after an arrival collapse | | TAUGHT |
| Collapse measure: 90 days, year on year | | TAUGHT |
| Threshold 0.5 | any value from 0.36 to 0.78 gives the same Israel resets | TAUGHT (round value, not tuned) |
