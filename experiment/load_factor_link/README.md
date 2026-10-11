# Load factor link

## Question

Does a learned seats-to-passengers link improve the planning chain? The chain becomes seats -> P2P passengers (link 0) -> hotel new arrivals (link 1) -> guests (link 2), and a scenario is driven by seats alone: load factor follows from the learned response.

Run at commit 5ee812f: BASE is `CHAIN_SPECS["seat_chain"]` with link 1 knots at 60 days and link 2 knots at 365 days (link 2 moved to 45 days in c99e25d).

## Variants

Every variant is a full chain, fitted on each fold's training window only. In prediction and scenarios link 0 reads seats (C: the schedule) and the calendar, never realized P2P or load factor.

| Variant | Link 0 |
| --- | --- |
| BASE | none: the shipped `CHAIN_SPECS["seat_chain"]`, seats straight into the arrivals kernel |
| A | log(P2P / seats) = knot base + season + weekday + (beta - 1) x; x = log(7-day / 91-day trailing mean seats); beta in [0, 1], per market, shrunk toward the cross-market median |
| A_updown | A with beta_up (x > 0) and beta_down (x < 0), tied toward each other by a ridge |
| A2 | A_updown with beta_down = beta0 + gamma x (usual LF - mean); usual LF = training pax / seats per market and season; gamma pooled |
| L | logit(P2P / seats) = knot base + season level + weekday + events + b x, seat-weighted; P2P = seats x sigmoid |
| TS | A plus beta_long in [0, 1] on log trend seats, so the knot base carries only what the seat trend does not |
| B | P2P / seats as a pooled decile step function of seats / market mean seats: the raw U, nothing else |
| C | log P2P on flights, gauge, airlines and premium seat share, each against its own 91-day trailing trend, one coefficient each, shrunk toward the cross-market median |
| A_oracle | realized P2P (not deployable, an upper bound) |

Links 1 and 2 are the shipped chain fed predicted P2P instead of seats, so the kernel cap becomes one arrival per P2P passenger. Trends are trailing, so prediction never reads future data; knot bases stay flat beyond the training days. Link-0 settings (knots every 365 days, pooling 0.3) were chosen on link-0 P2P WAPE alone: knots every 60, 182, 365 days gave 18.01, 17.17, 16.97; pooling 0.3 gave 16.81.

## How to run

```bash
export PYTHONPATH=src TWIN_LAKE_DIR=<repo>/lake TWIN_OUTPUT_DIR=experiment/load_factor_link/out
python experiment/load_factor_link/run.py        # fits 9 variants x 7 folds, caches out/runs/ (about 2 h on 9 workers)
python experiment/load_factor_link/report.py     # writes results.md and out/residuals/*.png
```

| File | Responsibility |
| --- | --- |
| `data.py` | daily panel with seats, P2P, pax and schedule inputs; weekly sums |
| `passengers_link.py` | link 0 models: TrendResponse (A, A_updown, A2, TS), LogitLoadFactor (L), UCurve (B), ScheduleInputs (C), RealizedP2P |
| `passenger_chain.py` | the three-link chain and the seat scenario |
| `variants.py` | the compared chains |
| `run.py` | fits per fold and caches predictions and the last-year-schedule counterfactual |
| `lever.py` | lever back-test: unique weeks, robust drift baseline, episodes, seat-only response |
| `residuals.py` | link-0 residual checks and charts |
| `coefficients.py` | descriptive slopes, coefficient intervals, C's independence check |
| `scenarios.py` | seats +-10% scenarios |
| `report.py` | scores everything and writes `results.md` |

## Results

International, VALIDATION_ORIGINS, 7 folds. Delta against BASE from `compare()`, pp, negative is better. Full tables in [results.md](results.md).

| Variant | Daily WAPE | Daily delta [90% CI] | Weekly delta [90% CI] | Folds better (d / w) | P2P WAPE | Gate |
| --- | --- | --- | --- | --- | --- | --- |
| BASE | 21.05 | | | | | |
| A | 21.05 | -0.00 [-0.23, +0.12] | -0.02 [-0.23, +0.15] | 6 / 5 | 16.81 | fail |
| A_updown | 21.05 | -0.01 [-0.23, +0.11] | -0.03 [-0.24, +0.14] | 6 / 5 | 16.81 | fail |
| A2 | 21.06 | +0.00 [-0.23, +0.13] | -0.02 [-0.24, +0.15] | 6 / 5 | 16.69 | fail |
| L | 21.00 | -0.07 [-0.32, +0.08] | -0.11 [-0.37, +0.07] | 5 / 5 | 18.74 | fail |
| TS | 21.25 | +0.19 [-0.06, +0.34] | +0.19 [-0.06, +0.38] | 2 / 3 | 17.35 | fail |
| B | 21.39 | +0.32 [+0.07, +0.64] | +0.22 [-0.04, +0.58] | 2 / 2 | 40.75 | fail (worse) |
| C | 21.09 | +0.03 [-0.41, +0.27] | +0.05 [-0.40, +0.32] | 5 / 6 | 16.64 | fail |
| A_oracle | 20.41 | -0.68 [-1.40, +0.09] | -0.46 [-1.18, +0.26] | 6 / 6 | 0 | diagnostic |

A constant load factor per market (seats x training P2P / seats) scores P2P WAPE 20.17, so link 0 itself learns something: A cuts P2P error by about 3.4 pp.

## Conclusion

- No variant passes the gate. A, A_updown, A2, L and C are within 0.1 pp of BASE; TS is slightly worse; B is worse on daily guests with an interval that excludes 0.
- Even realized P2P (A_oracle) gains only 0.68 pp and its interval includes 0. The ceiling of any passengers link is small, because link 1 puts most new arrivals on its base stock: 10% more seats moves guests by 0.4 to 3.7%.
- Beta: fitted on P2P, most markets sit on the upper bound 1 (8 to 14 of 20 per fold). The cross-market mean is 0.81 [0.68, 0.90] on the last fold; a few markets carry the response (UK 0.00, Other Asia-Pacific 0.17, China 0.54, Philippines 0.56). Freeing the bound to 2 moves the fold medians to 0.92 to 1.17 and lowers link-0 WAPE only to 16.67.
- One beta fits both directions: beta_up and beta_down differ by 0.02 in the cross-market mean, and A_updown scores like A.
- A2: gamma is negative on every fold (-0.5 to -3, interval -3.0 to +3.3), the opposite sign of the total-pax pattern, and not distinguishable from 0. On P2P, cuts do not hurt less in full markets.
- At market grain the measured response differs from the background numbers: against a centred 13-week trend, pax slope is 1.02 (increases 0.97, cuts 1.05) and P2P slope is 1.56 (cuts 1.84), n 1920 market-weeks. P2P share rises when seats rise, so P2P moves more than seats.
- L: the sigmoid does not produce the cut/increase asymmetry. P2P per seat is 0.17 to 0.47, far from the bound, so cut and increase slopes differ by less than 0.03 in every LF band.
- TS: beta_long is 0.87 to 1.00 by fold (mean 0.89 on the last fold). Level bias gets worse (-8.7 vs -7.9 for A) and the large market biases stay: UK -16.4, China -20.0, Philippines -21.4, Other Eurasia -32.2.
- C: the detrended inputs are close to independent (VIF 1.05 to 1.42); only flights and airlines correlate (0.49). Flights carry 0.93 per log point, gauge 0.78, airlines 0.28, premium share -1.8. C answers +10% seats differently by delivery: as flights, UK P2P +7.3% and India +9.4%; as gauge, +5.0% and +5.6%.
- B against A: learning the raw U hurts. B misses market levels (P2P WAPE 40.8) and its scenario response is set by the bin the market crosses: UK +10% seats gives P2P +47%, -10% gives -23%. A's response is symmetric and set by beta.
- Residual checks: no link 0 is a clean passengers model. Every variant has bins biased by more than 2% (mostly Israel, China, Italy, January) and weekly residuals remember (lag-1 ACF about 0.5). C passes the memory check at the margin.
- Lever: on unique weeks with the robust baseline, no variant changes the guest lever much. Down-week bias stays near -0.2 for every variant, driven by Israel.
