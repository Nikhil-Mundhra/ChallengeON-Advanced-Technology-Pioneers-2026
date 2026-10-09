# Refactor backlog

Surveyed 2026-10-09 (second run) · scope `src/tourism_twin` · 76 files
Baseline: tests 104 passed, 1 skipped · 6,762 lines (was 6,876) · 178 comment lines (was 205)
History window: 25 commits touching the scope (thin history; change-preventer checks found nothing).

DELTA since the first survey (2026-10-09)
  closed   R1 R2 R3 R4 R5 R6
  new      R15 (bug) R16 (dropped)
  changed  none
  stale    none

## Open

None.

## Done

### R1 · Dead code · BENCHMARK_NAMES, FEATURE_NAMES
closed 2026-10-09 by 2adb58f — deleted; `git grep -w` returns nothing

### R2 · Duplicated literal · `"DOMESTIC"`
closed 2026-10-09 by 2adb58f — one constant in domain/markets.py; the literal remains only there and as a key of the archetype table in domain/archetypes.py

### R3 · Long method + data clump · StructuralEngine.simulate
closed 2026-10-09 by 2adb58f — 71 → 12 statements; a `Chain` per state, `_baseline_chain`, `_domestic_scenario`, `_international_scenario`, `_waterfall`; outputs byte-identical for 644 checked results

### R4 · Duplicate code · planning_guests vs simulate baseline
closed 2026-10-09 by 2adb58f — answered: a served route that converts nobody brings no arrivals; both use `MarketSeasonParams.arrivals_from`

### R5 · Data clump + parameter with one value · calendar period in run_scenario / predict_hybrid
closed 2026-10-09 by e8dea0b — parameters removed; the residual comes from the scenario season (R11)

### R6 · Long method · UncertaintyEngine.run_monte_carlo
closed 2026-10-09 by e41d347 — 67 → 10 statements; `_draw` (a `Draws` record, original draw order) and vectorised `_trajectories`; outputs byte-identical for 460 checked results

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
dropped 2026-10-09 — every caller left iso_week=10, quarter=1, month=2, so every season used an early-March residual. Fixed by e8dea0b and 91a03e8: the scenario residual is the mean fit over the season's training weeks

### R12 · Large class · config.py:27 · Settings
dropped 2026-10-09 — 17 public members, all path properties; a settings table

### R13 · Large class · models/components/arrivals_conv.py:30 · ArrivalsConvolution
dropped 2026-10-09 — 15 fields, one cluster (fitted kernel state and its diagnostics, written by fit, read by contribution/explain)

### R14 · Alternative classes · models/uncertainty.py UncertaintyEngine vs models/noise.py NoiseModel
dropped 2026-10-09 — different models (weekly simulator Monte Carlo vs daily nowcast error model) in different call paths; no caller chooses between them

### R15 · bug, not a smell · services/simulator.py · scenario report central estimates
dropped 2026-10-09 — the API shows the hybrid (structural + season residual) next to conformal and Monte Carlo bands centred on the structural prediction; centring the bands on the hybrid or labelling them structural is a behaviour decision, not a refactor

### R16 · Long method · cli/pipeline.py:125 · _print_evaluation
dropped 2026-10-09 — 42 print statements formatting the evaluation; a presenter (as R8)

## Refused

None.
