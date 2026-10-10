# Daily nowcast

## Scope

| Problem | Known inputs for the predicted period | Withheld | Model family |
| --- | --- | --- | --- |
| Nowcast (test split, 2025-08-01 to 2026-02-28) | Daily `New Arrivals` and same-day guests per nationality, date | `Guests` | Stock-flow: guests = past arrivals still in a hotel |
| Planning ([planning model](planning.md)) | Scheduled seats, levers, calibrated seasonal priors | Everything downstream of seats | Structural chain |

| Model | Inputs | Output | Code |
| --- | --- | --- | --- |
| International guests | Daily new arrivals (lags 0..K), date | Daily guests per market; pooled-market nationalities from `POOLED_NATIONALITIES` ([nationalities](nationalities.md)) | `INTL_NOWCAST` (`intl_nowcast`) in `nowcast/specs.py`, spec `twin_daily` |
| Domestic guests | Domestic new arrivals, or date only | Daily guests | `DOMESTIC_NOWCAST` (`domestic_nowcast`) and time-only `DOMESTIC_TIME` (`domestic_time`) |
| Same-day guests | Weekday, holiday week, log new arrivals | Daily same-day guests | `nowcast/same_day.py` |
| Direction | Guests history, calendar | Up or down over the next week | `nowcast/weekly.py` |
| Winter outlook | Scenario arrivals, date | Guests for a future winter | [outlook](outlook.md) |
| Intervals | Out-of-sample back-test errors | P10/P50/P90 | [intervals](intervals.md) |

## Form

```text
Guests_t   = flow_t × m_t                                      (log: log flow_t + log m_t)

flow_t     = c_t + Σ_{k=0..K} w_k · Arrivals_{t−k}             arrivals kernel; owns the level; K = 21
m_t        = exp(   Fourier_H(day of year)                     annual season, H = 4
                  + day of week
                  + Σ_e Kernel_e(t − anchor_e) )               event kernels (INTERNATIONAL only)
                  [+ slope_t]                                  DOMESTIC only
                                                               periodic terms centred on the training window;
                                                               event terms are zero outside their windows
```

The prediction is exp of the summed log contributions (the conditional median). The form is a generalized additive model with a log link; `flow_t` is a distributed-lag (transfer-function) model, in queueing terms the occupancy of an M/G/∞ queue. "Convolution" means only the sum Σ w_k · Arrivals_{t−k}: one constrained linear filter over one series, no layers or non-linearity.

Kernel constraints (`ArrivalsConvolution`):

| Constraint | Implementation |
| --- | --- |
| w_k ≥ 0, non-increasing | w = triu(1) · d, d ≥ 0 |
| w₀ ≤ 1 | Σd ≤ 1; projected when the solver overshoots |
| c_t ≥ 0, slowly varying | Base stock, piecewise linear between knots about 365 days apart, first-difference penalty, flat beyond the training days |
| Day of week in m_t, not in w | Yes |
| Lunar events in m_t, not modulating w | Yes |

w is a fitting device, not a measured stay distribution; Σw is not reported in any output.

## Blocks

| Block | Components | Role |
| --- | --- | --- |
| Flow | `ArrivalsConvolution` | Level and short-term dynamics from arrivals |
| Time | `CentredSlope` or `LocalLevel`, `AnnualFourier`, `DayOfWeek` | Season, weekday, drift not carried by arrivals |
| Holiday | `EventKernel` (from `domain/events.csv`) | Dated windows: Ramadan, Eids, National Day, Christmas to New Year, ... |
| Flight | `LinearRegressors` on flight features | Registered; no spec uses it |

Blocks are parallel terms of one log-additive model. Each component carries its block as `group`; `decompose_by_group` splits a prediction by block (`top_drivers` in `market_outputs.json`). Block contributions: [nowcast validation](../results/nowcast-validation.md).

## Fitting

| Fact |
| --- |
| `Backfitting` (`models/fitters.py`) fits one component at a time with every other contribution held as an offset, kernel first, until the largest contribution change is < 1e-6 (cap 200 passes) |
| Every block minimises one penalised log-scale objective, Σ(y − Σ contributions)² plus each component's penalty; the base-stock penalty is made unitless by the first pass's mean target |
| The kernel starts from a least-squares solve on the original scale, is refined on the log objective under its constraints, and keeps the refinement only if the objective does not rise |
| The linear components are one jointly solved block on y − log flow |
| The penalised objective never increases; `FitReport.objective` records it per pass |
| `domestic_time` has linear components only and uses `JointLinear` (one least squares) |
| Fitting chosen components on the offset of frozen others is one valid block step from a converged fit |
| A separate weight per block is not identifiable when the block's coefficients are free; it is identifiable when the block's shape is fixed (partial pooling: `GroupScale` in `POOLED_NATIONALITIES`) |
| `scripts/compare_domestic_weekday.py` reproduces the domestic weekday and pass-cap comparison |

## Series

| Series | Spec | Terms |
| --- | --- | --- |
| `DOMESTIC` | `DOMESTIC_NOWCAST` | Kernel, `CentredSlope`, season, weekday; no events; trains on all history |
| Other 20 markets | `INTL_NOWCAST` | Kernel, season, weekday, events; no slope |

`MarketRouter` (`nowcast/routing.py`) routes `DOMESTIC` rows to one spec and every other market to the other. Each series is fitted and evaluated separately. Total guests = domestic + international predictions; its interval comes from the summed series' errors ([intervals](intervals.md)).

## Components

| Registered name | Class | Block | Contribution |
| --- | --- | --- | --- |
| `arrivals_kernel` | `ArrivalsConvolution` | flow | log(c_t + Σ w_k·A_{t−k}) under the kernel constraints; owns the level |
| `local_level` / `linear_trend` | `LocalLevel` / `LinearTrend` | time | Level (+ slope); owns the level in time-only specs; `LocalLevel` is a Whittaker smoother, flat beyond the training days |
| `slope` | `CentredSlope` | time | Log-linear slope in years since the first training day, centred on the training rows, flat beyond the last training day |
| `annual_fourier` | `AnnualFourier` | time | 4 sine/cosine pairs of day of year, centred |
| `weekday` | `DayOfWeek` | time | One effect per weekday (Monday reference), centred; optionally × season |
| `events` | `EventKernel` | holiday | One coefficient per window day per event type; second-difference smoothing for windows of 6+ days, weight scaled by occurrences; zero outside the windows; scope all, international, one market or one pooled-market nationality |
| `group_scale` | `GroupScale` | flow | Per-series log scale with a ridge toward the shared level |
| `regressors` | `LinearRegressors` | flight | Linear terms on named feature columns |
| `residual_gbm` | `ResidualGBM` | residual | Final-stage GBM on weekday, month, ISO week, holiday week, arrival lags 0 and 7 |

## Training rows and inputs

| Fact |
| --- |
| Training rows: `lag_complete` rows with guests; rows flagged `is_one_off_period` (the `international_shock_2022` window, international markets only) are excluded |
| Inputs: `arrivals_lag_0..21` from `new_arrivals_filled`; lags run across the train/test boundary |

## Daily specs (`DAILY_SPECS`)

| Name | Definition |
| --- | --- |
| `twin_daily` | Shipped: `DOMESTIC_NOWCAST` + `INTL_NOWCAST` |
| `naive_364` | Same market, same weekday 364 days earlier, stepping back whole years until the date is in training |
| `arrivals_ratio` | New arrivals × the market's training guests ÷ new arrivals |
| `twin_daily_gbm` | `twin_daily` + `ResidualGBM` (international) |
| `twin_daily_base90` | Base stock tied to 90-day arrivals |
| `domestic_time` | `LocalLevel` + season + weekday by season + events |
| `time_only`, `flow_only`, `flow_time` | Block ablations |

## Event registry

`domain/events.csv` columns: `event, kind (lunar|solar|one_off), anchor_date, window_start_offset, window_end_offset, scope, label, source`. Rows cover Ramadan, Eid al-Fitr, Eid al-Adha, National Day, Christmas to New Year, F1, ADIPEC and others, test-period dates and 2026/27 dates (unconfirmed Hijri dates labelled `(expected)`). `one_off` rows are masked from training. `is_holiday_week` and `is_major_event_week` stay legacy weekly flags. `chinese_new_year` (CHINA) and `morocco_winter_block` (MOROCCO) are not in `DEFAULT_KERNEL_EVENTS`.

Candidate windows come from `event_detector.py` (analysis): robust z on residuals, seed |z| ≥ 3, extend while |z| ≥ 1.5, recurrence by calendar date or Ramadan offset ±3 days; a recurring event has ≥ 2 occurrences.

## Validation protocol (`models/backtest.py`)

| Item | Definition |
| --- | --- |
| `backtest(spec, panel, splitter)` | Per-fold predictions and metrics; a fresh fit per fold on rows ending `gap_days` before the origin |
| `VALIDATION_ORIGINS` | Monthly 2024-02-01..2024-08-01, horizon cut at 2025-01-31, 21-day gap, expanding window; 7 folds |
| `FROZEN_TEST` | 2025-02-01..2025-07-31 |
| `compare()` | Candidate − baseline WAPE, 90% moving-block bootstrap interval (28-day date blocks shared by both models and every fold), share of folds with the same sign |
| Event folds | Christmas to New Year and National Day fall in the origin 2024-08-01 fold |
| Weekly benchmarks | The four benchmarks in `planning/evaluation.py` run as specs |
| `twin validate` | Re-runs the validation table and comparisons into `output/validation_summary.json` |

## Derived outputs (`nowcast/outputs.py`, `nowcast/weekly.py`)

`market_outputs.json` is computed from the fitted model and its intervals only.

| Output | Definition |
| --- | --- |
| Weekly forecast | Sum of daily predictions over a full Monday to Sunday week |
| p10, p90 | `NoiseModel.range_interval` over the week's days |
| Direction, probability | Sign of the log change to the next week; probability from the s.d. of the difference of the two weeks' log errors (AR(1) covariance) |
| Year-on-year change | Forecast ÷ actual guests of the week 364 days earlier − 1 |
| Top drivers | Blocks other than flow with mean log contribution ≥ 0.5% in absolute value, as % effects |

## Same-day guests (`nowcast/same_day.py`)

| Fact |
| --- |
| `SameDayPoisson`: one Poisson GLM per market on weekday, holiday week and log(1 + new arrivals); markets with fewer than 60 training days use their mean |
| A suppressed value (`*`) counts as 0: no observed value is 0; observed counts fall from 1 (6,814 rows) to 2 (5,179) to 3 (2,967); suppressed days have lower arrivals (CHINA median 328 vs 501) |
| Every nationality with a suppressed value also published a 1; the censored likelihood (count < 1) equals reading `*` as 0 |
| Counts are overdispersed; no same-day interval is produced ([nowcast validation](../results/nowcast-validation.md)) |
| `same_day_backtest` scores it on rolling origins (`scripts/same_day_backtest.py`) |
| `twin predict` does not call it; the test workbooks contain `Same-Day Guests` |
