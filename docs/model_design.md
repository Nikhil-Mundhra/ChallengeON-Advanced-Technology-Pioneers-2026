# Abu Dhabi Tourism Digital Twin — Model Design

Design of the guest models: what is in `src/`, what has been measured outside it, and what is proposed. Method and shipped results: [solution documentation](solution_documentation.md). Commands: [user guide](user_guide.md). Decisions and their evidence: [decision log](decisions.md).

**Status legend** (every section is marked):

| Mark | Meaning |
| --- | --- |
| **Implemented** | Code exists in `src/tourism_twin/` and runs in the pipeline |
| **Analysis finding** | Measured with scripts outside the repository (`analysis/*.py`, local notes); not reproducible from this repository |
| **Proposed** | Not built; design only |

## 1. Problem framing — *Implemented (planning); Analysis finding (nowcast)*

Two prediction problems use different inputs:

| Problem | Known inputs for the predicted period | Withheld | Model family |
| --- | --- | --- | --- |
| Nowcast (competition test split, 2025-08-01 to 2026-02-28) | Daily `New Arrivals` and same-day guests per nationality, date | `Guests` | Stock-flow: guests = past arrivals still in a hotel |
| Planning / forecast (simulator) | Scheduled seats, planner levers, calibrated seasonal priors; no realized pax, P2P or arrivals | Everything downstream of seats | Structural chain (`models/structural.py`) |

In the nowcast, arrivals carry most of the level and the event shocks (§4.3). In planning, arrivals are unknown, so the calendar and the structural priors carry them. The two are reported separately ([solution documentation §6](solution_documentation.md#6-operating-modes)).

## 2. The models

| Model | Inputs | Output | Use | Status |
| --- | --- | --- | --- | --- |
| International Guests nowcast | Daily new arrivals (lags 0..K), date | Daily guests per market | Competition forecast of withheld `Guests` | Analysis finding (§4); the lag inputs are Implemented (`daily_market_panel.parquet`, `features/lags.py`) |
| Domestic Guests | Date (nowcast variant: also domestic new arrivals) | Daily guests | Competition forecast; domestic baseline | Implemented: per-season calibrated arrivals × LOS (`StructuralEngine.planning_guests`). Analysis finding: level + calendar and arrivals kernel models (§4) |
| Same-day guests | Calendar and arrival features | Daily same-day guests | Competition field | Analysis finding: GBM with Poisson loss, 19.4% WAPE vs 23.8% naive (`model_baselines.py`). Nothing in `src/` |
| Planning (structural) | Seats, levers, seasonal priors | Weekly guests per market × season, waterfall | Simulator, scenario attribution | Implemented (`models/structural.py`, `models/residual.py`) |
| Direction (derived) | Guests history, calendar | Up/down over +7 days | Briefing | Analysis finding: logistic + spline, 74% accuracy, Brier 0.18 vs 43% majority class (`model_baselines.py`) |
| Short-stay share / weekly stay (derived) | Fitted kernel weights, or guests and arrivals | Share of guests from short stays; weekly guests ÷ arrivals | Briefing | Analysis finding for weekly guests ÷ arrivals: ridge 3.2% vs 6.2% naive. Short-stay share: Proposed, definition not fixed |
| Intervals (derived) | Model residuals | P10/P50/P90 | Briefing, simulator | Implemented: Monte Carlo (`models/uncertainty.py`) and in-sample conformal margins (`models/conformal.py`). Proposed: noise model (§5.5) |

All `model_baselines.py` figures are on a single 6-month holdout, 2025-02 to 2025-07.

## 3. Model form — *Analysis finding (tested in `hybrid_order_test.py`); Proposed (constraints not yet tested, code structure)*

```text
Guests_t   = flow_t × m_t                                      (log: log flow_t + log m_t)

flow_t     = c_t + Σ_{k=0..K} w_k · Arrivals_{t−k}             arrivals kernel ("stock-flow"); owns the level
m_t        = exp(   Fourier_H(day of year)                     annual season, H = 4
                  + day of week [× season]
                  + Σ_e Kernel_e(t − anchor_e) )               event kernels (Ramadan, Eids, National Day, ...)
                  [+ slope_t]                                  DOMESTIC only (D19)
                                                               periodic terms centred on the training window;
                                                               event terms are zero outside their windows
```

**Trend in the nowcast is per series (decision D19, superseding D15).** The arrivals kernel owns the level in both series. DOMESTIC adds a centred log-slope to `m_t`: guests per arrival have fallen year on year (−3.9%/yr fitted), which a fixed kernel cannot follow. INTERNATIONAL has no trend: its fitted slope (+7.2%/yr) over-extrapolates and loses on the rolling back-test. Time-only specs (arrivals unknown: domestic forecast, planning) use a level component (`LinearTrend` or a local level) instead of the kernel. Evidence: §4.6.

Kernel constraints:

| Constraint | Reason | In the tested model? |
| --- | --- | --- |
| w_k ≥ 0 and non-increasing | A share of arrivals still in a hotel after k nights cannot be negative or rise. Fitted by NNLS on increments: w = triu(1) · d, d ≥ 0 | Yes |
| w₀ ≤ 1 | An arrival is counted at most once on its arrival day. An unconstrained fit gave w₀ = 1.15 | Probe only (§4.5): binds for domestic, changes WAPE < 0.2 points |
| c ≥ 0 | Base stock of guests cannot be negative | Probe only (§4.5) |
| c_t slowly varying | Base stock of long-stayers. A constant c cannot drop in Ramadan (domestic keeps a −11.5% Ramadan residual after the kernel) | No: c is a single constant |
| Day of week in m_t, not in w | Weekly spikes in an unconstrained kernel are the weekday pattern leaking in | Yes |
| Lunar events in m_t, not modulating w | Residual stay-length change after the kernel is small for international | Yes |

**Standard names.** `flow_t` is a distributed-lag (transfer-function, dynamic-regression) model; in queueing terms it is the occupancy of an M/G/∞ queue (arrivals × probability of still staying). The whole form is a generalized additive model with a log link: terms add in log, so they multiply on the guest scale.

**Not a CNN.** `flow_t` is one linear filter over one input series: a single constrained kernel, no stacked layers, no non-linearity between layers, no learned feature maps. "Convolution" refers only to the sum Σ w_k · Arrivals_{t−k}. MLPs tested in `model_baselines.py` were often worse than the seasonal naive.

**Independent in code, joint in fitting.** The kernel and the calendar explain overlapping variation (arrivals already carry most of Ramadan for international; season and events overlap in the same weeks). Each part can be its own module, but fitting them one after another on the raw target gives an order-dependent answer (§4.1). The parts are fitted jointly by backfitting: kernel on Guests / m, then calendar on log(Guests / flow), repeated until the calendar coefficients change by < 1e-6.

## 4. Evidence — *Analysis finding*

### 4.1 Component order (`analysis/hybrid_order_test.py`)

Daily totals (domestic; international summed over nationalities) read from the train workbooks. Two folds: test 2024-02-01 to 2024-07-31 (train 2023-01-01 to 2024-01-31) and test 2025-02-01 to 2025-07-31 (train 2023-01-01 to 2025-01-31). Hyperparameters fixed in advance: K = 21, H = 4, ridge α = 1. WAPE %, mean of the two folds.

| Model | DOM | INTL |
| --- | ---: | ---: |
| Seasonal naive (same weekday, 364 days earlier) | 16.3 | 18.6 |
| Calendar only (log ridge: trend, Fourier, dow, events) | 11.3 | 11.2 |
| Arrivals kernel only | 8.1 | 6.1 |
| Sequential kernel → calendar | 6.1 | 4.8 |
| Sequential calendar → kernel | 9.8 | 13.3 |
| **Joint backfit (Guests = flow × calendar multiplier)** | **4.9** | **4.7** |
| Multi-resolution greedy (level → year → week → days) | 6.9 | 5.7 |
| Joint + GBM on log residual | 5.0 | 4.7 |

- Order matters when components are fitted greedily: kernel-first 6.1 / 4.8, calendar-first 9.8 / 13.3.
- The joint backfit converges to the same WAPE from both starting orders (same WAPE to 6 decimal places): order-free at convergence.
- GBM on the joint residual gives no consistent gain (worse on both 2024 folds, better on both 2025 folds); dropped.
- Joint kernel Σw: domestic 1.6–2.2, international 3.3–3.5 across folds (c unconstrained). International Σw is close to the train-split guests ÷ new arrivals ratio of 3.61 ([solution documentation §4.2](solution_documentation.md#42-data-findings-that-shape-the-model)), which is a stock-to-flow ratio, not a measured length of stay. Σw depends on how much of the level the constant c absorbs: with c ≥ 0 the probe got international Σw = 2.34 with c ≈ 6.9k (§4.5). Read Σw as a stay estimate only together with c.
- Event windows in this script are hard-coded date lists for 2023–2025 (Ramadan, Eid al-Fitr, Eid al-Adha, National Day, 22 Dec–7 Jan).

### 4.2 Interactions and functional form (`analysis/interactions_test.py`)

Same folds and fixed hyperparameters as §4.1. WAPE %, mean of the two folds.

| Model | DOM | INTL |
| --- | ---: | ---: |
| Additive, raw scale: Guests = flow + calendar | 5.11 | 4.46 |
| Multiplicative: Guests = flow × calendar multiplier | 4.97 | 4.68 |
| + day of week × season (May–Sep) | 4.92 | 4.69 |
| + separate winter / summer kernels | 4.98 | 4.73 |
| + power: Guests = flow^α × calendar multiplier (kernel held fixed) | 5.22 | 4.67 |

- Fitted interaction sizes are small: summer shift of the Fri/Sat effect −0.1% to −2.6%; winter vs summer kernel Σw nearly equal (largest gap international 2025: 2.96 vs 3.28).
- α: domestic 0.91–0.93, international 0.99–1.02 (naive SE 0.01–0.03, too small given the autocorrelation in §4.4). Guests scale roughly proportionally with flow.
- No interaction improves WAPE by ≥ 0.3 points on both series. Additive vs multiplicative differ by ≤ 0.2 points in opposite directions per series; undecided until the rolling back-test (#10).
- Fitting α and the kernel together diverged (kernel scale and α trade off), so α is estimated with the kernel fixed. The multiplicative fit also needs the calendar centred on the training window, otherwise the kernel collapses toward zero.

### 4.3 Time effects (`seasonal_extract.py`, `seasonality_trig.py`, `ramadan_event_study.py`, `ramadan_conv_residual.py`, `event_detector.py`)

Log scale; 2023–2025.

| Component | Finding |
| --- | --- |
| Level / trend | Linear fits best against a 365-day moving average, but the level drifts: 90-day mean residual ±7% domestic, ±10% international. Extrapolating the line overshot 2025 by ~20% |
| Annual season | Fourier H = 4 on day of year; shape stable across years. Amplitude international ±25% (2023) / ±22% (2024), domestic ±8% / ±10% |
| Day of week | Domestic Fri +13%, Sat +23%, Sun −7% vs Mon; international ±5%. Domestic lag-7 residual ACF 0.42: the weekday pattern changes with season |
| Ramadan (lunar) | Domestic −24%, international −18%; starts ~5 days before Ramadan. After the arrivals kernel: international +1.3% residual, domestic −11.5% |
| Eid al-Fitr / Eid al-Adha (lunar) | Domestic +43–55% / +61–98%. Different sizes: they need separate kernels |
| Solar holidays | National Day +36–44%; Christmas–New Year international +41–43% for 12–17 days |
| One-off shocks | Jan 2022 international −29% for 28 days. Wars (Oct 2023, Apr 2024, Jun 2025) produced no detectable window |

Test period (Aug 2025 – Feb 2026) contains National Day 2025, Christmas–New Year 2025/26 and the start of Ramadan 2026 (~2026-02-18).

### 4.4 Noise (`noise_distribution.py`)

| Property | Domestic | International |
| --- | --- | --- |
| Shape, events removed | ≈ normal in log (JB p 0.08) | Normal in log (JB p 0.06) |
| Lag-1 ACF, per year | 0.72–0.82 | 0.89–0.92 |
| Spread by month | Aug 0.055 → Jan 0.091 | Sep 0.064 → May 0.121 |
| Centre (90-day mean) | Drifts ±7% | Drifts ±10% |

Noise is Gaussian in log once events are removed, but autocorrelated (effective sample size ≈ 160 domestic, ≈ 50 international, not 1,200+), with variance that changes by month and a drifting level. Independent-error p-values and intervals are therefore too narrow.

### 4.5 Reproduction by a vertical-slice probe — *Analysis finding (unmerged branch)*

An independent implementation built only from this document and AGENTS.md (panel → arrivals kernel + calendar components → back-test → test-split predictions; local branch, not merged into `main`). Same reference folds as §4.1, with w₀ ≤ 1 and c ≥ 0 enforced and box-shaped event windows.

| Spec | DOM (2024 / 2025 → mean) | INTL (2024 / 2025 → mean) | §4.1 |
| --- | --- | --- | --- |
| Seasonal naive 364 | 16.07 / 16.54 → 16.31 | 24.80 / 12.39 → 18.59 | 16.3 / 18.6 |
| Calendar only | 11.14 / 12.10 → 11.62 | 7.53 / 15.79 → 11.66 | 11.3 / 11.2 |
| Kernel only | 8.09 / 8.22 → 8.15 | 5.96 / 6.31 → 6.13 | 8.1 / 6.1 |
| Joint | 3.69 / 5.63 → **4.66** | 3.79 / 4.33 → **4.06** | 4.9 / 4.7 |
| Joint, rolling origins (13 monthly, 2024-02 → 2025-02, 6-month horizon) | **4.75** (naive 18.8) | **5.23** (naive 19.3) | — |

- Baselines reproduce within 0.4 points; the joint model reproduces and slightly improves on §4.1.
- This probe's joint spec included a centred slope for both series; on the test split the slope added +10.7% international / −6.1% domestic. The numbers in this table are therefore **with slope**; §4.6 separates the slope's effect.
- Events failed the drop-one gate (+0.06 / +0.07 points) on the Feb–Jul folds, which contain Ramadan and both Eids but no National Day or Christmas–New Year. See D16 and §4.6.

### 4.6 Slope and events in the nowcast: clean A/B — *Analysis finding (unmerged branch)*

One implementation (second probe, §5.7 reference spec with box events), one component switched at a time. WAPE %.

| Variant | DOM reference (2) | DOM rolling-13 | DOM Aug–Jan | INTL reference (2) | INTL rolling-13 | INTL Aug–Jan |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| No slope, events | 5.10 | 6.70 | 7.45 | 4.92 | 5.11 | 5.10 |
| Slope, events | 4.65 | 4.72 | 4.92 | 4.25 | 5.34 | 5.68 |
| Slope, no events | 4.72 | **4.65** | 4.74 | 4.07 | 5.16 | 5.89 |
| No slope, no events | — | — | — | 4.68 | 5.08 | 5.45 |
| Seasonal naive 364 | 16.31 | 18.8 | — | 18.59 | 19.28 | — |

Rolling-13: monthly origins 2024-02-01 → 2025-02-01, 6-month horizon. Aug–Jan: test 2024-08-01 → 2025-01-31, the only fold containing National Day and Christmas–New Year.

- **Slope:** DOMESTIC improves on every fold set (up to 2.5 points; fitted −3.9%/yr). INTERNATIONAL improves only on the two Feb–Jul reference folds and loses on rolling-13 and Aug–Jan (fitted +7.2%/yr). Decision D19.
- **Events:** DOMESTIC is better without them everywhere it matters. INTERNATIONAL gains 0.35 on the event fold and is neutral on rolling-13. Decision D20. Box windows only; the smoothed `EventKernel` is untested in the nowcast.
- The two Feb–Jul reference folds alone would have chosen the wrong international spec: check decisions on rolling origins and on folds containing the relevant windows.

## 5. Proposed code structure — *Partly implemented*

Same pattern as `features/registry.py` (declare once, request by name), applied to models. Tracked in issues [#9](https://github.com/Nikhil-Mundhra/ChallengeON-Advanced-Technology-Pioneers-2026/issues/9) (time effects), [#10](https://github.com/Nikhil-Mundhra/ChallengeON-Advanced-Technology-Pioneers-2026/issues/10) (rolling back-test), [#11](https://github.com/Nikhil-Mundhra/ChallengeON-Advanced-Technology-Pioneers-2026/issues/11) (train / validation / test split).

Status on `main` (verify with `git ls-files src/tourism_twin/models`):

| Part | Status |
| --- | --- |
| `Model` protocol (`models/protocol.py`), `Component` / `LinearComponent` (`models/components/base.py`) | Implemented |
| `LinearTrend`, `LinearRegressors` (`models/components/`) | Implemented |
| `EventKernel` (`models/components/events.py`) + event registry `domain/events.csv` (loaded by `domain/events.py`) | Implemented |
| `JointLinear`, `Backfitting` (`models/fitters.py`); `AdditiveLogModel` (`models/composite.py`) | Implemented |
| Back-test harness: `Fold`, `HoldoutSplit`, `RollingOrigin` (`models/backtest.py`); named specs (`models/specs.py`); weekly benchmark models (`models/baselines.py`) | Implemented (weekly specs only) |
| `ArrivalsConvolution`, `AnnualFourier`, `DayOfWeek`, `LocalLevel`, `ResidualGBM` components; daily nowcast specs | Proposed (a probe implementation exists on an unmerged branch, §4.5) |
| Noise model (§5.5), test-split prediction writer | Proposed |

### 5.1 Component interface

```text
Component: name, requires (feature names resolved through PANEL_FEATURES)
  fit(panel, offset, y)      y = log target; offset = sum of all other components (log)
  contribution(panel)        log-scale series; centred, except the one component that owns the level
  explain()                  fitted parameters in plain form
```

| Component | Contribution |
| --- | --- |
| `ArrivalsConvolution(K)` | log flow_t with the §3 constraints; owns the level when present |
| `LocalLevel` / `LinearTrend` | Random-walk level + slope (Kalman); owns the level otherwise |
| `AnnualFourier(H)` | Season on day of year |
| `DayOfWeek(by_season)` | Weekday, optionally × season |
| `EventKernel` | One smoothed kernel per event type, read from `events.csv` |
| `ResidualGBM` | Kept only if it passes a back-test gate |
| `StructuralComponent` | Wraps the existing `StructuralEngine` for benchmarking |

### 5.2 Specs and fitting

A spec is a named component list (`intl_nowcast`, `domestic_time`, `planning`, `naive_364`); an ablation is a spec with one component removed. A composite `AdditiveLogModel` sums contributions and returns a per-component decomposition. Fitters: one joint linear solve for the linear parts, backfitting for the kernel and GBM.

### 5.3 Event registry as data

`domain/events.csv` with columns `event, kind (lunar|solar|one_off), anchor_date, window_start_offset, window_end_offset, scope, label, source (detected|manual)`. Separate rows for Ramadan, Eid al-Fitr, Eid al-Adha, National Day, Christmas–New Year, F1, ADIPEC and the rest, including test-period dates. `one_off` rows are masked from training. `is_holiday_week` and `is_major_event_week` become features derived from the CSV so the weekly panel and its tests keep working. Candidate windows come from `event_detector.py` (robust z on residuals, seed |z| ≥ 3, extend while |z| ≥ 1.5, recurrence by calendar date or Ramadan offset ±3 days; an event needs ≥ 2 occurrences to be recurring).

### 5.4 Back-test harness (#10, #11)

`backtest(spec, panel, origins)` → per-fold metrics. Monthly rolling origins, ~6-month horizon, fit only on data before each origin, domestic and international reported separately (WAPE, MAE, bias). Any calibration (z-scores, conformal, alphas) uses the training fold only. Origins for the daily nowcast: monthly from 2024-02-01 to 2025-02-01 (13 folds). A component tied to dated windows (events) is judged only on folds whose test period contains those windows (D16); for Christmas–New Year and National Day this needs a fold such as test 2024-08-01 → 2025-01-31. Inside it, a time-ordered split: train fits parameters, validation chooses hyperparameters (K, smoothing λ, event thresholds, H), and one final test period is evaluated once after all choices are frozen. The four benchmarks in `models/evaluation.py` become four specs.

### 5.5 Noise model

Fitted on back-test residuals: Gaussian in log, σ per month, AR(1) φ for growth with horizon. Replaces the in-sample conformal margins.

### 5.6 Feature contract (analysis issues → model)

Every feature table delivered by an analysis issue has this shape, so it joins the daily panel and enters a back-test without reshaping:

| date | market | `<feature_1>` | `<feature_2>` | … |
| --- | --- | --- | --- | --- |
| 2023-01-01 | DOMESTIC | 1240 | 0.12 | |
| 2023-01-01 | INDIA | 8312 | 0.74 | |
| … | | | | |
| 2026-02-28 | UZBEKISTAN | 57 | NaN | |

- `date`: daily, `YYYY-MM-DD`, 2023-01-01 to 2026-02-28 (**includes the test period**).
- `market`: `DOMESTIC` or the nationality exactly as in the guest workbooks (uppercase). Features from departure countries are mapped to nationality, and the mapping is stated as approximate (§ solution documentation 4.2 item 2). A feature that does not vary by market uses `market = ALL`.
- One column per feature, raw values: no scaling, no one-hot, no log. Missing stays NaN; imputed values get a `<col>_imputed` flag.
- Nothing derived from `Guests`. The value for date *t* uses only data from *t* or earlier.
- Each feature is described once: kind (count / ratio 0–1 / continuous / categorical / flag), unit, range, meaning of missing.

Inside `src/`, such a feature becomes a `@PANEL_FEATURES.feature` spec (AGENTS.md "Data access and features").

### 5.7 Implementation rules for the guest model

Apply these when building any part of §3–§5. Each comes from a measured failure or result.

| Rule | Why |
| --- | --- |
| Encoding in linear/GLM parts: categoricals (day of week, month, market, holiday type) one-hot, never integer-coded; annual season as Fourier terms on day of year; continuous inputs (arrivals, P2P, seats) in log; load factor (bounded, saturating) as spline or bins | Integer-coded categoricals make a linear model look worse than a GBM for the wrong reason (*analysis*: holiday and encoding fixes cut ridge MAE 3,137 → 2,623) |
| Lunar holidays from explicit dates per year, never a fixed month | They move ~11 days earlier each year |
| Kernel: `w = triu(ones) @ d`, `d ≥ 0` (non-increasing); **not** `triu(ones).T` (non-decreasing) | Reversed matrix silently gives a non-physical kernel (*analysis*, bug found) |
| Centre periodic calendar terms on the training window after every calendar step; the kernel owns the level; event terms are zero outside their windows | Otherwise the overall scale drifts into the calendar intercept and the kernel collapses toward zero (*analysis*) |
| Never fit a power α together with a free kernel | They trade off without limit and diverge; estimate α with the kernel fixed (*analysis*) |
| Joint fit (backfitting to convergence), never one greedy pass | Greedy order changes the answer by up to 8.6 points (§4.1) |
| No feature derived from `Guests` in the nowcast; lags of `New Arrivals` are allowed in both splits | Guests is the withheld target (D2) |
| Hyperparameters (K, H, λ, event windows, detector thresholds, ridge α) chosen on validation folds only; tuning CV is time-ordered (`TimeSeriesSplit`), never shuffled | Shuffled CV leaks the future; `models/residual.py` `RidgeCV` currently uses non-temporal CV |
| Event-detector z-scores, conformal margins and noise σ computed from training-fold residuals only | Whole-series statistics leak the test period |
| Report domestic and international separately, never only pooled | Pooled raw-scale metrics are dominated by domestic (MAE 17,485 vs 2,466) |
| A new component ships with a synthetic-data test: it must recover a known kernel / bump / sine | A component that can't recover its own truth can't be trusted on real data |
| Keep a component only if it passes the acceptance gate (decision D12) | Effective sample size is small (§4.4) |

**Reference evaluation** (reproduce this before changing anything; §4.1 and §4.5 are its results):

| Item | Specification |
| --- | --- |
| Series | `DOMESTIC`, and the international total = sum of all 20 non-domestic daily-panel markets (lags summed per day) |
| Arrivals input | `new_arrivals_filled` (the column the lags are built from) |
| Training rows | date ≥ 2023-01-01, `lag_complete`, `guests` not null. 2022 guests unused |
| Folds | test 2024-02-01 → 2024-07-31 (train before 2024-02-01) and test 2025-02-01 → 2025-07-31 (train before 2025-02-01). Report each fold and the mean |
| Hyperparameters | Fixed, not tuned: K = 21, H = 4, ridge α = 1. Tuning (D11) applies to the production spec only, on validation folds (D18) |
| Kernel | `flow = c + Σ_{k=0..21} w_k·A_{t−k}`, `w = triu(ones) @ d`, `d ≥ 0`, `w_0 ≤ 1`, `c ≥ 0`; fitted on Guests / m in raw scale, rows weighted by m (minimise Σ(G − m·flow)²); `w_0 ≤ 1` enforced exactly (bounded solve when it binds) |
| Calendar (log) | Fourier on day of year / 365.25, H = 4; day of week one-hot (Monday = reference); event windows as 0/1 boxes: Ramadan (first day − 5 → day before Eid al-Fitr window), Eid al-Fitr and Eid al-Adha (−1 → +3), National Day (30 Nov → 4 Dec), Christmas–New Year (22 Dec → 7 Jan). These boxes are fixed for comparability and differ from the `domain/events.csv` windows used by `EventKernel`. Ridge α = 1 on the raw centred columns (scikit-learn `Ridge` convention); level owner and slope unpenalised. Periodic terms centred on the training rows; event boxes centred too in the reference (an implementation detail; `EventKernel` instead is zero outside its windows) |
| Per-series terms | DOMESTIC: + centred log-slope (years since 2023-01-01), no events. INTERNATIONAL: events, no slope (D19, D20) |
| Fit | Backfitting: kernel on Guests / m, calendar on log(Guests / flow), until the largest change in any log contribution < 1e-6 |
| Metric | WAPE = Σ\|actual − predicted\| / Σ actual, per series and fold |
| Expected | Per-series spec above: DOMESTIC 4.72 reference / 4.65 rolling-13; INTERNATIONAL 4.92 reference / 5.11 rolling-13 (§4.6). Same spec for both series without slope, with events: 5.10 / 4.92. Baselines: naive 16.3 / 18.6, calendar only (with trend) ≈ 11.6, kernel only 8.1 / 6.1 |
| Not inputs | Same-day guests (separate target, D17); anything derived from `Guests` |

### 5.8 Flight-side findings for feature work — *Analysis finding*

| Finding | Consequence |
| --- | --- |
| `Total PAX = P2P + Transfer + Transit` on 100% of rows; transfer ≈ 50% of passengers | Use P2P as hotel-eligible passengers (D3) |
| Etihad: 73% of passengers transfer; low-cost carriers ≈ 0% | Transfer rate is an airline-mix feature, not a cabin feature |
| Business vs economy transfer: 64% vs 49% pooled, 69% vs 74% within Etihad (reversal) | Cabin-class effects need an airline control (D4) |
| Premium share vs transfer rate across Etihad routes: r = 0.44; spread narrows above ~9% premium share | Both track route type (long-haul hub feed vs regional); not causal |
| First-class transfer share 3.6% (Etihad 6.5%) | Implausible for a hub carrier; treat first-class transfer columns as suspect |
| Cabin columns exclude infants (gap to `Total P2P`: median 1, max 28) | Not a data error |
| Load factor up to 108% in daily data | Bounded, saturating input (§5.7 encoding) |

## 6. Open items and known gaps

| Gap | Where | Status |
| --- | --- | --- |
| Domestic intercept is constant | Tested kernel: c is one constant, so domestic keeps a −11.5% Ramadan residual. `src/`: domestic planning prediction is a per-season constant (arrivals × LOS), over-forecast 2025 by 13.05% | Implemented (constant); slowly varying c_t Proposed |
| Events lumped into one flag | `domain/events.py` stores Monday week-starts; Eid al-Fitr, Eid al-Adha, National Day and New Year share `is_holiday_week`. No Ramadan window for 2023–2025; one 2026 week labelled "Lunar New Year / Spring Festival & Ramadan Start". Week 2024-12-02 is in both `HOLIDAY_WEEKS` and `MAJOR_EVENT_WEEKS` (National Day and F1) | Implemented; replacement Proposed (§5.3) |
| Single holdout | `models/evaluation.py`: one split at `HOLDOUT_START = "2024-12-30"`; no Autumn_Shoulder weeks | Implemented; rolling harness Proposed (#10) |
| In-sample conformal | `models/conformal.py` takes the (1 − α) quantile of training-window errors; holdout coverage 65.2% vs 80% nominal | Implemented; noise model Proposed (§5.5) |
| Daily panel unused | `data/daily_panel.py` builds lags 0..21; no model on `main` reads it (the §4.5 probe branch does) | Implemented (panel only) |
| Untested constraints | w₀ ≤ 1 and slowly varying c_t are not in `hybrid_order_test.py` | Proposed |
| Pooling across nationalities | The experiment uses international totals; per-nationality kernels (shared kernel + per-market scale) are untested | Proposed |
| Analysis outside the repository | `analysis/*.py` read the raw workbooks directly, not through `LakeRepository`; figures are not reproducible from this repository | Analysis finding |
| Edge effect | Decompositions disagree on residual memory (last 1–2 days vs ~1–2 weeks); centred smoothers are unreliable near series ends | Analysis finding, unresolved |
