# Refactor backlog

Surveyed 2026-10-09 · scope `src/tourism_twin` · 76 files
Baseline: tests 101 passed, 1 skipped · 6,876 lines · 205 comment lines
History window: 20 commits touching the scope (thin history; change-preventer checks found nothing).

## Open

### R1 · Dead code · models/evaluation.py:50 · BENCHMARK_NAMES; models/features.py:49 · FEATURE_NAMES
status   planned
evidence `git grep -w` over src, tests, scripts, docs, app: 1 hit each (the definition)
remedy   delete (15 lines)
safety   SAFE — no edges to unlink; proof: suite + grep returns nothing
expect   -15 lines

### R2 · Duplicated literal (primitive obsession) · `"DOMESTIC"` in 6 files
status   planned
evidence 11 comparisons with the literal: baselines.py (4), structural.py (2, compound with the DOMESTIC_STAYCATION archetype), evaluation.py (2), same_day.py, features/events.py, features/flags.py; the constant `DOMESTIC` exists only in models/backtest.py:15, a layer features/ cannot import
remedy   Move the constant to domain/markets.py and replace the literal with it (no new predicate function: KISS); the structural compound predicate becomes one private method used by `planning_guests` and `simulate`
safety   SAFE — same expression; proof: suite (waterfall, route closure, domestic decoupling, back-test segments, router tests)
expect   one spelling of the domestic market, at the domain layer; structural predicate stated once

### R3 · Long method + data clump · models/structural.py:188 · StructuralEngine.simulate
status   planned
evidence 71 statements; 4 comment-introduced blocks (baseline chain, domestic, international, waterfall); the 9-value chain (seats, lf, pax, p2p_share, p2p, mult, arrivals, los, guests) appears twice as `base_*` and `sim_*` locals; envies `lever` (16 accesses vs 1 to self)
remedy   Introduce Parameter Object `Chain` (NamedTuple) + Extract Method: `_baseline_chain(p, domestic)`, `_scenario_chain(base, lever, domestic)`, `_waterfall(base, sim)` → refactor-composing-method
safety   SAFE — proof: dump `simulate()` for every calibrated market × season × lever grid before/after, byte-identical; suite pins the waterfall identity to 1e-9
reshaped by principles: four extracted methods passing 9 locals each would trade a long method for long parameter lists; the `Chain` object carries them
expect   simulate ≤ 20 statements; P0 history comments removed

### R4 · Duplicate code + feature envy · models/structural.py:158 · planning_guests vs simulate baseline
status   planned, not schedulable (ASK)
evidence `planning_guests` docstring: "The same conversion chain simulate() applies to its baseline"; 9 accesses to `p` vs 1 to self; the copies differ when seats > 0 and load factor × P2P share = 0 (planning → 0 arrivals, simulate → baseline arrivals); 0 of 84 calibrated market-seasons reach that case
remedy   Move Method: `MarketSeasonParams.arrivals_at(seats)` used by both → refactor-moving-feats-btw-objects
safety   ASK — unifying changes one copy's behaviour on the divergent case
question which semantics wins for a served route whose conversion is 0: no aviation arrivals (planning) or baseline arrivals (simulate)? Recommend planning's: a served route that converts nothing brings nobody.
blocked  R3 (same method)

### R5 · Data clump + parameter with one value · calendar period (iso_week, quarter, month, is_holiday_week, is_major_event_week)
status   planned, not schedulable (ASK)
evidence the 5 values travel together through `TourismDigitalTwin.run_scenario` → `ResidualMLEngine.predict_hybrid` → `predict_residual` → `extract_calendar_features`; all 4 `run_scenario` callers (app/server.py:87, cli/simulate.py:48, reporting/charts.py:193, reporting/solution_report.py:349) and 3 tests pass the defaults (10, 1, 2, 0, 0)
remedy   Remove Parameter from `run_scenario`/`predict_hybrid` once the period is derived from the season (see R11); a `CalendarPeriod` value object is rejected (YAGNI: one distinct argument at every call site)
safety   ASK — narrows a public signature used by the web API, and the fix is a behaviour change (R11)
question derive the residual's calendar period from the scenario season (behaviour change, simulator outputs move), or keep week 10 and just drop the unused parameters? Recommend deriving it: today every season gets February's residual.
blocked  R11

### R6 · Long method · models/uncertainty.py:74 · UncertaintyEngine.run_monte_carlo
status   open
evidence 67 statements; numbered comment blocks per uncertainty source (operational Beta draws, parameter shocks, block-bootstrap residuals); 27 accesses to `sim_res` vs 5 to self
remedy   Extract Method per source → refactor-composing-method; RNG draw order must stay identical
safety   SAFE — proof: dump bands for every market × season with fixed seeds before/after; `test_*deterministic*` pins repeatability
expect   run_monte_carlo ≤ 25 statements

## Done

None.

## Dropped

### R7 · Long method · reporting/solution_report.py:114 · build_solution_report
dropped 2026-10-09 — 83 statements but a flat, branch-free sequence of story elements (nesting 1); no reusable group

### R8 · Long method / feature envy · cli/simulate.py:34 · run
dropped 2026-10-09 — 55 print statements reading `s_res` (49 accesses); a presenter, whose job is to read the result

### R9 · Divergent change · cli/pipeline.py
dropped 2026-10-09 — 10 of 20 commits touch it, but it is the command router; listing unrelated commands is its job

### R10 · Shotgun surgery · models/{backtest,baselines,specs}.py and models/{components,composite,fitters}.py
dropped 2026-10-09 — each triple co-changed 3 times while the model layer was being built (thin history), not one concept spread out

### R11 · bug, not a smell · services/simulator.py:69 · run_scenario calendar defaults
dropped 2026-10-09 — every caller leaves iso_week=10, quarter=1, month=2, so the residual correction for any season uses a February week; fix as a behaviour change, then close R5

### R12 · Large class · config.py:27 · Settings
dropped 2026-10-09 — 17 public members, all path properties; a settings table

### R13 · Large class · models/components/arrivals_conv.py:30 · ArrivalsConvolution
dropped 2026-10-09 — 15 fields, one cluster (fitted kernel state and its diagnostics, written by fit, read by contribution/explain)

### R14 · Alternative classes · models/uncertainty.py UncertaintyEngine vs models/noise.py NoiseModel
dropped 2026-10-09 — different models (weekly simulator Monte Carlo vs daily nowcast error model) in different call paths; no caller chooses between them

## Refused

None.
