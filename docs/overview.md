# Overview

Challenge: DCT Abu Dhabi, Advanced Technology Pioneers 2026 ([challenge statement](https://challengeon.atrc.ae/en/challenges/atp2026/pages/dct-challenge-statement?lang=en)).

## Models

| Model | Inputs for the predicted period | Output | Command |
| --- | --- | --- | --- |
| Daily nowcast (`twin_daily`) | Daily new arrivals per market | Daily guests per market and nationality for 2025-08-01 to 2026-02-28 with P10/P50/P90 and weekly direction; future-winter guests under arrivals scenarios | `twin predict`, `twin outlook` |
| Weekly planning model | Scheduled seats, planner levers, calibrated seasonal priors | Weekly guest lift per market and season, waterfall by lever, P10/P50/P90, tornado, briefing; weekly back-test and 3-year projection | `twin simulate`, web app |

Details: [nowcast](model/nowcast.md), [planning model](model/planning.md).

## Problem

- Flight data records departure country; hotel data records guest nationality.
- Arriving passengers transfer, transit, return as residents, stay with friends or relatives, or arrive overland; a change in seats does not map one to one to hotel demand.

Questions the planning model answers:

- hotel demand from a new twice-weekly route;
- effect of a change in aircraft size or load factor;
- guests per added seat, by market and season;
- exposure of a market-season to a capacity cut;
- which assumption drives the result most.

Out of scope: individual-traveller prediction or profiling; itinerary reconstruction; causal claims from observational data; occupancy (no room inventory); nationality, purpose or hotel choice from flight aggregates.

## Requirements

| Requirement | Implementation |
| --- | --- |
| Working simulator | `twin simulate`, web app `/simulate`, `twin serve` (JSON API), [Python API](guide/python-api.md) |
| Competition forecast | `twin predict`: `Guests` for every test-file row, validated against the test workbooks, with P10/P50/P90 |
| Adjustable conversion chain | 7 levers over seats → passengers → P2P → hotel arrivals → guests; every stage baseline vs scenario |
| Historical validation | Nowcast: 7 validation origins, frozen test scored once, two baselines, interval coverage, direction accuracy. Planning: forward holdout (104 calibration weeks, 30 holdout weeks), 4-model benchmark. [Results](results/index.md) |
| Sensitivity analysis | Tornado ranking; Monte Carlo P10/P50/P90 |
| Granularity | Nowcast: 21 markets daily; the 30 pooled-market nationalities modelled directly. Planning: 21 markets × 4 seasons, weekly |
| Decision relevance | Generated briefing naming the lift, range and top driver |
| Reproducibility | Source hashes in `lake/manifest.json`, env-configurable paths, `make all` from the raw workbooks, seeded Monte Carlo, tests |

## Operating modes

| Mode | Purpose | Allowed inputs |
| --- | --- | --- |
| Planning | Pre-flight decisions; the simulator | Scheduled seats, planner levers, calibrated seasonal priors; no realized pax, P2P or hotel arrivals for the predicted period |
| Realized chain (diagnostic) | Error of the downstream stages | Realized P2P × calibrated multiplier × stay factor |
| Nowcast | Withheld competition `Guests` (`twin predict`) | Test-period new arrivals from the test files; no feature derived from `Guests` |

Results of different modes are reported separately.

## Responsible use

The data is aggregated and holds no passenger-level information. Outputs are expected aggregate relationships, not individual behaviour or protected characteristics. The simulator is a planning tool; it does not establish causal effects.

## References

| Reference |
| --- |
| [DCT Abu Dhabi challenge statement](https://challengeon.atrc.ae/en/challenges/atp2026/pages/dct-challenge-statement?lang=en) |
| `01a - DCT Dataset/Data_Dictionary.pdf` (organizer-provided; not in the repository) |
| [`lake/manifest.json`](../lake/manifest.json) |
