# Scenario response

## Question

How well does each planning model predict what happens to hotel guests when a market's seats change? We test each model on weeks where seats really moved.

Run at commit e015fdd. International markets, VALIDATION_ORIGINS (7 folds, test weeks 2024-02-01 to 2025-01-31). FROZEN_TEST is never read: every panel is cut at 2025-01-31.

## Models

| Model | What it is |
| --- | --- |
| TIME-ONLY | `CalendarRidge` (the weekly calendar-only model). No flight input, so no seat response. The null every flight model must beat. |
| HYBRID | The weekly planning model on actual seats: `planning_guests` + residual ridge. Reference only. |
| LINEAR | The shipped scenario path (`StructuralEngine.simulate` + residual baseline) with the three hand-set adjustments of commit 3af6a13 off: frequency S-curve, capacity dilution, saturation. |
| S-CURVE | The same with the adjustments on, as shipped. Seat change given as a frequency lever, so the S-curve acts. |
| S-CURVE % | The same, seat change given as `delta_seats_pct`. The S-curve is then inactive; dilution and saturation act. |
| SHORT-RUN | Learned short-run elasticity: baseline x (seats / reference seats) ^ beta_m. |
| CHAIN | `CHAIN_SPECS["seat_chain"]` (`SeatChain`, link knots at 60 and 45 days). |

The adjustment switch lives in `scenario_engines.py` only. `LinearEngine` swaps `structural._international_scenario` for a flagged copy during `simulate()`. The copy with every flag on equals the shipped function exactly.

## Design

Natural-experiment weeks are market-weeks whose seats moved more than 15% against a reference. Two references, scored separately:

- yoy: the same week a year earlier. Guest and predicted changes have the market's drift removed: the median over at least 8 quiet weeks (seat change under 5%) of that year, else the trailing 52-week median. Copied from `load_factor_link/lever.py`.
- trend: the market's centred 13-week seat mean. Guests and predictions are compared with their own centred 13-week means. No drift term.

Each model predicts the week as its baseline plus the observed seat change applied as its lever:

- Baseline for LINEAR, S-CURVE, S-CURVE % and SHORT-RUN: the weekly planning model at the reference seats (`planning_guests` at reference seats + the week's residual), floored at 0.
- LINEAR and S-CURVE add `simulate(market, season, lever).delta_guests`. This is how the web timeline applies a scenario to a week.
- Seats lever: `delta_seats_pct = seats / ref_seats - 1`.
- Frequency lever: gauge g = ref_seats / ref_flights; `delta_frequency = (calibrated seats / g) x (flights / ref_flights - 1)`; `delta_seats_pct = (seats / flights) / g - 1` carries the gauge change. Both levers give the same scenario seats. Flights come from `flight_daily` (`average_weekly_frequency` x days in month / 7). The panel's `weekly_flight_services` counts route-airline-days, not flights. Weeks without flights fall back to the seats lever.
- CHAIN: baseline = the chain run with the test period's daily seats set to the reference (last year's same weekday, or each day scaled to its week's seat trend). Scenario = the chain on actual seats. Its lags carry the change into later weeks.
- TIME-ONLY: the calendar ridge. Baseline and scenario are the same.

Every model is refitted per fold on weeks that end before the fold's train_end: calibration (`StructuralEngine.calibrate`), residual ridge, calendar ridge, SHORT-RUN betas and the chain. `calibrate` is already a refit path. Refitted on the full shipped window it reproduces `structural_calibration.json` exactly (gap 0) and the residual season means to 1.8e-12.

A market-week inside several folds counts once, its values averaged over the folds. All models are scored on the same market-weeks. Metrics on log change: MAE, bias, slope of predicted and of actual change on seat change (through 0), slope of the seat-only response (log scenario / baseline), and the slope of actual on predicted change (1 is calibrated). Paired differences use a moving-block bootstrap (4-week blocks, 90%). Levels use weekly WAPE and `compare()`.

Ordinary weeks are test weeks with yoy seat change at most 15%. There we report weekly WAPE, MAE, RMSE and out-of-sample R2 against TIME-ONLY (1 - SSE / SSE of TIME-ONLY).

### SHORT-RUN

Per market, y = log(guests / centred 13-week guest mean) on x = log(seats / centred 13-week seat mean), weekly. Trends are computed on the training weeks only, so the last 6 training weeks drop out and nothing after the cutoff is read. Each beta is shrunk toward the cross-market median by a ridge: beta_m = (Sxy + ridge x median) / (Sxx + ridge). The ridge was chosen on VALIDATION_ORIGINS by the MAE of y - beta x on every test week. Markets with fewer than 26 usable weeks take the pooled value. In the back-test the seat ratio is each test's reference, the same one every model gets. For the simulator the reference would be the trailing 13-week seat mean (`data.trailing_trend`).

The co-movement check regresses the 52-week change in log guest trend on the 52-week change in log seat trend. It is an association, not an effect.

## How to run

```bash
export PYTHONPATH=src TWIN_LAKE_DIR=<repo>/lake
python experiment/scenario_response/chain_runs.py   # fits the chain on 7 folds, caches out/chain/ (about 10 min on 7 workers)
python experiment/scenario_response/report.py       # everything else: results.md, out/short_run_beta.csv, out/response_curves_*.png (about 2 min)
```

| File | Responsibility |
| --- | --- |
| `data.py` | daily and weekly panels cut at 2025-01-31, weekly flights, folds, centred and trailing trends |
| `scenario_engines.py` | LINEAR switch, lever mapping, calibration and copy checks |
| `short_run.py` | SHORT-RUN fit, pooling, ridge choice, bootstrap, co-movement |
| `chain_runs.py` | CHAIN fits and counterfactual schedules per fold |
| `weekly_runs.py` | weekly predictions and baselines of every other model per fold |
| `lever.py` | natural-experiment weeks, drift, scoring, paired bootstrap |
| `curves.py` | response curves and charts |
| `report.py` | tables and `results.md` |

## Results

Full tables in [results.md](results.md).

### Natural experiments, same week a year earlier

717 market-weeks: 624 increases, 93 cuts. Actual slope after drift: 0.08 (increases 0.19, cuts -0.27).

| Model | MAE | Bias | Slope pred. | Seat-only slope | MAE increases | MAE cuts | Baseline WAPE | Scenario WAPE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TIME-ONLY | 0.276 | -0.059 | -0.02 | 0.00 | 0.240 | 0.515 | 30.6 | 30.6 |
| HYBRID | 0.287 | -0.018 | 0.35 | 1.03 | 0.227 | 0.686 | 30.5 | 26.9 |
| LINEAR | 0.277 | -0.008 | 0.27 | 0.90 | 0.234 | 0.572 | 30.5 | 25.5 |
| S-CURVE | 0.260 | -0.061 | 0.10 | 0.67 | 0.213 | 0.571 | 30.5 | 23.5 |
| S-CURVE % | 0.256 | -0.068 | 0.07 | 0.63 | 0.214 | 0.542 | 30.5 | 23.3 |
| SHORT-RUN | 0.342 | -0.112 | 0.14 | 0.68 | 0.310 | 0.557 | 30.5 | 34.5 |
| CHAIN | 0.210 | -0.024 | 0.15 | 0.47 | 0.186 | 0.373 | 22.8 | 20.0 |

Paired MAE differences on log change, 90% intervals:

| Comparison | All | Increases | Cuts |
| --- | --- | --- | --- |
| S-CURVE - LINEAR | -0.018 [-0.032, -0.003] | -0.020 [-0.037, -0.005] | -0.000 [-0.010, +0.017] |
| S-CURVE % - LINEAR | -0.021 [-0.038, -0.005] | -0.020 [-0.037, -0.004] | -0.030 [-0.040, -0.012] |
| CHAIN - LINEAR | -0.067 [-0.095, -0.043] | -0.048 [-0.070, -0.029] | -0.198 [-0.316, -0.092] |
| LINEAR - TIME-ONLY | +0.002 [-0.018, +0.018] | -0.007 [-0.030, +0.010] | +0.057 [-0.106, +0.191] |
| S-CURVE - TIME-ONLY | -0.016 [-0.036, +0.002] | -0.027 [-0.057, -0.003] | +0.056 [-0.097, +0.191] |
| SHORT-RUN - TIME-ONLY | +0.066 [+0.043, +0.084] | +0.070 [+0.052, +0.085] | +0.042 [-0.180, +0.167] |
| CHAIN - TIME-ONLY | -0.066 [-0.093, -0.043] | -0.054 [-0.084, -0.030] | -0.142 [-0.258, -0.080] |

`compare()` on scenario-week guest levels: S-CURVE - LINEAR -1.22 pp [-2.01, -0.37], CHAIN - LINEAR -4.43 pp [-5.83, -3.17], CHAIN - TIME-ONLY -9.95 pp [-11.70, -7.91], all 7/7 folds.

### Natural experiments, centred 13-week trend

48 market-weeks: 16 increases, 32 cuts; Israel has 25. Actual slope 0.99.

| Model | MAE | Bias | Slope pred. | Seat-only slope |
| --- | --- | --- | --- | --- |
| TIME-ONLY | 0.395 | +0.091 | 0.35 | 0.00 |
| LINEAR | 0.375 | -0.039 | 1.50 | 1.31 |
| S-CURVE | 0.368 | -0.045 | 1.42 | 1.26 |
| S-CURVE % | 0.368 | -0.037 | 1.39 | 1.22 |
| SHORT-RUN | 0.352 | -0.020 | 1.43 | 1.21 |
| CHAIN | 0.368 | -0.080 | 1.41 | 0.50 |

No flight model beats TIME-ONLY on MAE here; every interval includes 0. S-CURVE - LINEAR: -0.007 [-0.021, +0.010].

### Ordinary weeks

265 market-weeks with yoy seat change at most 15%.

| Model | WAPE | MAE | RMSE | R2 vs TIME-ONLY | WAPE vs TIME-ONLY, pp [90% CI] |
| --- | --- | --- | --- | --- | --- |
| TIME-ONLY | 25.4 | 2125 | 3520 | 0 | |
| HYBRID | 21.2 | 1770 | 3120 | 0.21 | -3.68 [-5.23, -2.14] |
| LINEAR | 21.4 | 1791 | 3139 | 0.21 | -3.43 [-4.86, -2.04] |
| S-CURVE | 21.3 | 1780 | 3116 | 0.22 | -3.45 [-4.85, -2.13] |
| S-CURVE % | 21.5 | 1798 | 3166 | 0.19 | -3.31 [-4.65, -2.05] |
| SHORT-RUN | 23.2 | 1940 | 3347 | 0.10 | -0.70 [-2.75, +1.67] |
| CHAIN | 16.5 | 1382 | 2207 | 0.61 | -7.49 [-10.49, -4.11] |

### SHORT-RUN betas

Ridge chosen: 0.01, almost no pooling. Validation MAE moves only from 0.2030 to 0.2061 across ridges 0 to 100. Pooled beta 0.58 [0.31, 0.91]. Market betas range from -0.73 (India) to 3.50 (Kuwait); Other MENA 2.89, United States 1.76, Germany 1.24, UK -0.20 [-1.84, 1.44], Saudi Arabia -0.49 [-4.06, 2.89]. Table in `out/short_run_beta.csv` and results.md.

Co-movement (association): pooled slope 0.65 [0.38, 0.70]; Germany 1.06, Israel 1.25, UK 0.14 [-1.08, 0.65].

### Response curves

`out/response_curves_yoy.png` and `out/response_curves_trend.png`: guest change for a seat change from -50% to +100% applied to the last fold's test period (Aug 2024 to Jan 2025), per model, for UK, India, China, Germany and Kuwait. Grey and dark points are the market's weeks (dark: above 15%).

- LINEAR is a straight line. Its slope is the guest share carried by P2P passengers at a marginal rate of min(M, 1): 0.85 for the UK, 0.73 for India, 0.22 for China, 0.94 for Germany, 0.96 for Kuwait at +100%.
- S-CURVE bends increases down. At +100% it gives about half of LINEAR (UK +45%, Germany +53%). Cuts get a little larger than LINEAR, because the S-curve lowers load factor when frequency falls.
- CHAIN is close to linear and flatter: about 0.37 of the seat change for UK and India, 0.12 for China, 0.71 for Germany and Kuwait.
- SHORT-RUN follows its beta: falling guests for more seats in the UK and India, +1040% for Kuwait at +100%.
- History: in yoy, UK weeks with +25% to +45% seats have guests -40% to +10% after drift; Germany's weeks rise with seats near the LINEAR and CHAIN lines; India's spread from -30% to +55% at +20% to +40% seats. In trend, only China and Kuwait have weeks above 15%.

## Web engine

`web/src/engine/planning.ts` mirrors S-CURVE. `internationalScenario` has the same three adjustments with the same constants (gamma 1.5, f0 7, clips 0.85 to 1.15, decays -0.05 and -0.08, kappa 2.5 or 2.0). `parity.test.ts` checks it against Python golden cases. The live simulator shows `weeklyHeadline`: calibrated seasonal base + season residual, with the S-CURVE delta. The frequency slider exercises the S-curve; the seats % slider gives S-CURVE %. The timeline adds the same season delta to each week. The question cards use UK +2 flights at gauge 290 (S-CURVE) and India +10% seats (S-CURVE %).

## Conclusion

- CHAIN matches history best. It has the lowest MAE on yoy experiments (0.210 vs 0.277 for LINEAR), on increases and on cuts, and the lowest level WAPE on experiment and ordinary weeks. It is the only model that beats TIME-ONLY on yoy experiment changes with an interval that excludes 0 (-0.066 [-0.093, -0.043]).
- LINEAR does not beat TIME-ONLY on yoy changes (+0.002 [-0.018, +0.018]). It over-predicts increases (slope 0.38 vs actual 0.19).
- The shipped adjustments help a little on increases and are neutral on cuts. S-CURVE - LINEAR is -0.020 [-0.037, -0.005] on yoy increases and -0.000 [-0.010, +0.017] on cuts. On the trend test the difference is -0.007 [-0.021, +0.010]. On ordinary weeks it is -0.02 pp [-0.24, +0.18].
- The gain comes from dilution and saturation, not the frequency S-curve. S-CURVE % (S-curve inactive) scores the same or better (0.256 vs 0.260).
- Flight data adds value on ordinary weeks: LINEAR and S-CURVE cut WAPE by 3.4 pp against TIME-ONLY, CHAIN by 7.5 pp (R2 0.61). Much of it is level: TIME-ONLY misses 2024 growth (level bias -24% on experiment weeks).
- SHORT-RUN is not fit to drive the simulator's schedule lever in this form. It is worst on yoy experiments (MAE 0.342), worse than TIME-ONLY with an interval excluding 0. Its betas swing from -0.73 to 3.50, and several flip sign by fold (UK +0.80 to -0.22, Saudi Arabia +0.41 to -2.72). Week-to-week seat and guest deviations share calendar peaks (holiday and Eid travel), which the regression reads as a seat effect. It would need calendar controls on both sides before use. The CSV is exported as asked, with this caveat.
- Limits: the yoy drift absorbs persistent capacity growth, so the actual yoy response (0.08) is the response beyond a market's usual change that year. The trend test has 48 weeks, half from Israel, so it separates little. The additive season delta on a week's baseline inflates the percentage response when the week sits below its seasonal mean (LINEAR seat-only slope 1.31 on the trend test).
