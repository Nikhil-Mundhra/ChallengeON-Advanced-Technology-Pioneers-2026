# Evidence

```
docs/evidence/component-order.md : greedy order vs joint backfit (analysis)
docs/evidence/factor-chain.md : flight-side links to guests; domestic training history (analysis, back-tests)
docs/evidence/flow-linearity.md : guests against the fitted flow; learned power and spline transforms (analysis, validation)
docs/evidence/hand-set-settings.md : sensitivity to K, H and the base-stock knot spacing (analysis, validation)
docs/evidence/implementation-checks.md : faults found while building the model (analysis)
docs/evidence/interactions.md : interaction and power terms (analysis)
docs/evidence/noise.md : error distribution and autocorrelation, in-sample and out-of-sample (analysis)
docs/evidence/range-totals.md : accuracy of date-range totals (rolling back-test)
docs/evidence/reference-evaluation.md : fixed reference evaluation and its expected values
docs/evidence/scenario-response.md : flight levers against weeks where seats moved; shipped schedule elasticity (back-test, training)
docs/evidence/slope-and-events.md : slope and events per series, clean A/B (analysis, unmerged branch)
docs/evidence/test-period-data.md : test-period data findings (analysis)
docs/evidence/time-effects.md : level, season, weekday, lunar and solar events (analysis)
docs/evidence/two-stage-fit.md : calendar removed before the kernel vs the joint backfit (analysis, validation)
docs/evidence/vertical-slice-probe.md : independent reproduction of the model (analysis, unmerged branch)
experiment/README.md : experiment folders: code, README with question and conclusion, aggregate results
experiment/eda_coupling/README.md : seats, P2P, arrivals and guests after removing time, by lag (descriptive; nothing shipped)
experiment/level_memory/README.md : error carry-forward and a drifting guests-per-arrival strength (drift passes on international only; not shipped)
experiment/load_factor_link/README.md : learned seats-to-passengers link in front of the planning chain (no variant passes; not shipped)
experiment/scenario_response/README.md : flight-change back-test of the planning models (the fitted chain ships as the schedule elasticity; summary in scenario-response.md)
experiment/seasonal_link/README.md : seasonal strength of the seats-to-arrivals link (seasonal pattern in P2P to arrivals; a seasonal seat-kernel strength fails the gate; not shipped)
```
