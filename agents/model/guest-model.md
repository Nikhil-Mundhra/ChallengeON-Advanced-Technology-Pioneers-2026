# Guest model

## Calls
- `agents/model/evaluation.md` : how a model change is compared, gated and reported
- `docs/model/nowcast.md` : model form, blocks, components, specs, events
- `docs/model/planning.md` : weekly structural chain and residual
- `docs/model/intervals.md` : noise model and sums
- `docs/evidence/index.md` : the measurements behind the rules below
- `docs/architecture/layers.md` : model kernel layers (registry, spec, handler, fitter, component)

## Rules
- rule change: when a measured result changes a rule here, update the rule and its evidence file in `docs/evidence/` in the same change.
- model family: no general neural networks (MLP, CNN, RNN).
- terms: no interaction or power terms by default (weekday × season, seasonal kernels, `flow^α`); never fit a power α together with a free kernel; estimate α with the kernel fixed.
- new component: one module in `models/components/` (subclass `ComponentBase` or `LinearComponent`, `fit(panel, offset, y, weights=None)`), its export in `components/__init__.py`, one `COMPONENTS.register(name, cls)` line in `models/registry.py`, a synthetic test in `tests/models/test_components.py` that recovers a known kernel, bump or sine, and its name in a `ModelSpec` in `nowcast/specs.py` (weekly: `planning/specs.py`); edit nothing else; never hard-wire a model into `training.py` or `evaluation.py`.
- hooks: the model and fitters call `reset`, `penalty`, `final_stage`, `set_default_origin` from `ComponentBase`; never probe for them with `hasattr` or `getattr`.
- specs: models are `ModelSpec` data (`models/spec.py`: components by registered name, fitter, row rules, weighting); never build component lists inside functions; variants come from `adding`, `without`, `replace_component`, `with_weighting`; an ablation is a new spec entry, never a code branch.
- series: domestic and international differ only by spec, routed with `routed(domestic_spec, international_spec)` or `MarketRouter`; never subclass a model per series.
- nowcast specs: the arrivals kernel owns the level; DOMESTIC adds a centred slope and no events and trains on all history; INTERNATIONAL has events and no slope; `ResidualGBM` stays out of `twin_daily`.
- nationalities: pooled-market nationalities use `POOLED_NATIONALITIES`; single-nationality markets keep the market model; never pool all 45 nationalities.
- solving: least-squares maths lives in `models/linear_solve.py`, solved through `least_squares`; components only provide designs and penalty rows.
- data steps: features, training-row filters, target transform and weights are a `RowRule` in `models/handler.py` or a `Weighting` in `models/weighting.py`; never inside a component, fitter or `AdditiveLogModel`; prefer `rules=` over the `exclude_flag` and `include_flag` shorthands.
- weighting: one `Weighting` class per axis (recency, nationality, ...), combined with `Product`; weights positive, only relative values matter; a weighting compares and hashes by its settings.
- composition: components compose only through `AdditiveLogModel` (`models/composite.py`); exactly one component per model sets `owns_level=True`; residual learners set `final_stage = True`.
- fitting: blocks (flow, time, holiday, flight) are parallel terms of one log-additive model, fitted jointly by backfitting to convergence (`models/fitters.py`); never chained, never one greedy pass.
- centring: centre periodic calendar terms on the training window after every calendar step; the level owner and event terms (zero outside their windows) are not centred.
- partial refit: refitting some components against frozen others is for experiments only; a shipped model is fully refitted.
- nowcast inputs: test-split hotel New Arrivals (kernel) and calendar blocks only; lags of New Arrivals are allowed in both splits; never a feature derived from `Guests`; never flight, transfer, premium or seat features.
- planning chain: one equation per link (flights → hotel arrivals → guests), simulated end to end; never flights and arrivals in the same guests equation.
- calendar: calendar terms go in every equation; never de-seasonalize a variable separately before fitting.
- new input: enters as a mixing weight inside the arrivals kernel or as a centred ratio, with one pooled coefficient; never a free additive log term, never fitted per country.
- kernel: non-negative and non-increasing, `w = triu(ones) @ d` with `d >= 0` (never `triu(ones).T`), `w_0 <= 1`, base stock `c >= 0`.
- labels: kernel weights, their sum and guests ÷ arrivals ratios are fitting quantities; never output, export or label them as length of stay; the planning factor L is the "guests-per-arrival factor".
- encoding: categoricals (day of week, month, market, holiday type) one-hot, never integer-coded; annual season as Fourier terms on day of year; continuous inputs (arrivals, P2P, seats) in log; load factor as spline or bins.
- lunar holidays: explicit dates per year, never a fixed month.
- events: occurrences go in `domain/events.csv` with `scope` (all, international, a market or a pooled-market nationality); `kind=one_off` rows are masked from training through `is_one_off_period`; scoped events (`chinese_new_year`, `morocco_winter_block`) stay out of `DEFAULT_KERNEL_EVENTS` until they pass the gate.
- legacy weeks: never derive `HOLIDAY_WEEKS` or `MAJOR_EVENT_WEEKS` from `events.csv`.
- outlook: before `twin outlook --winter Y`, add that window's event occurrences to `events.csv`, unconfirmed lunar dates labelled `(expected)`.
- intervals: fit `models/noise.NoiseModel` on out-of-sample back-test errors only; the interval of a sum (week, date range, total over markets) comes from `NoiseModel.range_interval` or the summed series' own errors; never add bounds.
