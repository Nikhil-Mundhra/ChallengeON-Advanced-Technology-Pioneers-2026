# Weekly planning model

## Structural chain (`planning/structural.py`)

Per market m and season s, calibrated from the mean of weekly seats, pax, P2P, arrivals and guests in the training window:

```text
LF        = mean pax / mean seats
P2PShare  = mean P2P / mean pax
M[m,s]    = mean hotel arrivals / mean P2P        (effective response multiplier)
L[m,s]    = mean guests / mean hotel arrivals     (guests-per-arrival factor: a stock-to-flow ratio)

Guests = Seats × LF × P2PShare × M × L
```

| Part | Fact |
| --- | --- |
| Ratios | LF, P2P share, M and L are training-window means per market and season; none is fitted by optimisation |
| Market bridge | Departure country k is linked to nationality k; M absorbs non-national passengers, indirect connections and overland arrivals. A 45 × 33 country-to-nationality matrix (1,485 parameters) is not estimated |
| Planning prediction (`planning_guests`) | Scheduled seats × calibrated LF, P2P share, M, L. A served market whose seats carry no P2P passengers has zero aviation arrivals; an unserved market keeps its calibrated arrivals. The simulator baseline uses the same rule (`MarketSeasonParams.arrivals_from`) |
| Domestic | `DOMESTIC` = calibrated seasonal arrivals × L, independent of seats; seat, frequency, load-factor and P2P levers have no effect; multiplier and stay-factor levers do (tested) |
| Cold start | A country without calibration gets its archetype's default LF, P2P share, M and L (`domain/archetypes.py`); unknown countries map to Emerging / Sparse |
| Scenario response (`_international_scenario`) | A schedule change (extra flights × seats per flight, seats on existing flights) on a served route scales arrivals by (new seats ÷ baseline seats)^ε, ε the market's schedule elasticity for the season ([flight response](#flight-response)). A new route (baseline seats 0) adds its P2P passengers at the marginal rate min(M, 1) on top of the calibrated or archetype arrivals. A closure keeps only arrivals by other routes: baseline P2P × max(M − 1, 0). Load factor, P2P share, multiplier and stay factor are assumption levers applied on top; on a served route a load-factor or P2P-share shift converts at min(M, 1) × (new ÷ baseline seats)^(ε − 1) arrivals per passenger. A zero gauge counts as 250 seats |
| Waterfall | Lift attributed sequentially: seats (the schedule response), load factor, P2P share, multiplier, stay factor. The five parts sum to the total lift (tested to < 1e-9 for every calibrated market, a cold-start market, all seasons and 6 lever sets); `simulate` raises above a relative 1e-9 (absolute 1e-6) |

## Flight response

Artifact: `lake/curated/flight_response.json`, written by `twin train` (`planning/training.py`) and exported in `planning.json` as `flight_response`.

| Lever | Model | Fact |
| --- | --- | --- |
| Schedule change (`planning/schedule_response.py`) | Learned | ε per market and season from the fitted planning chain (`CHAIN_SPECS["seat_chain"]`, `planning/chain.py`): seats × (1 + c) on every day of the last 365 training days, c ∈ {−25%, −10%, +10%, +25%}; ε(c) = log(Σ scenario guests ÷ Σ baseline guests) ÷ log(1 + c) over the window's days from day 28 on, by season; ε = mean over the four c; `curvature` = largest \|ε(c) − ε\| |
| Schedule change range | Learned | Lowest and highest ε over the full fit and the 7 `VALIDATION_ORIGINS` refits, each read on the last 365 days of its own training window |
| Schedule change, no seats of its own (cold start, DOMESTIC) | Pooled | Per season: median ε over markets, range from the lowest low to the highest high |
| Capacity growth (`planning/capacity_trend.py`) | Assumption | Seat trend, % a year, from the first projected week (or the scenario start, if later); guests × (1 + g)^(years × e), e from 0 (guests do not follow seats) to 1 (one for one) |
| Capacity growth central line | Association | e = γ, the slope of the 52-week change in log centred 13-week guest trend on that of the seat trend, market intercepts removed, pooled over markets; 90% market-cluster bootstrap interval; clipped to [0, 1] |

Evidence for the chain over a short-run elasticity, the linear chain and the hand-set adjustments: [scenario response](../evidence/scenario-response.md), from `experiment/scenario_response/` ([README](../../experiment/scenario_response/README.md)).

## Residual (`planning/residual.py`, `planning/calendar_features.py`)

```text
Hybrid = max(0, planning_guests + residual)
```

| Fact |
| --- |
| One `RidgeCV` per market |
| Features: two week-of-year sine/cosine pairs, quarter dummies, winter and summer flags, holiday-week flag (Eid al-Fitr, Eid al-Adha, National Day, New Year and festive weeks), major-event-week flag (ADIPEC, Formula 1), each `events.csv` event's share of the week for the markets it covers (`event_exposure_matrix`) |
| Target: actual guests − `planning_guests` |
| In a scenario the residual is the mean fitted residual over the market's training weeks in that season (`season_residual` in `residual_engine.pkl`) |
| No aviation inputs; the hybrid lift equals the structural lift unless the max(0, ·) floor binds (tested: lift ≥ 0 for +2 flights in 5 markets) |
| `RidgeCV` picks α from 25 values, 10⁻² to 10⁴ (log-spaced), by scikit-learn's built-in leave-one-out, which ignores time order |
| Holiday flags are the legacy `is_holiday_week` and `is_major_event_week`, which lump Eid al-Fitr, Eid al-Adha, National Day and New Year |

## Uncertainty and sensitivity (`planning/uncertainty.py`, `planning/conformal.py`, `planning/sensitivity.py`)

| Component | Method |
| --- | --- |
| Monte Carlo (1,500 draws default) | Load factor and P2P share ~ Beta (method of moments, sd 0.03 and 0.04); multiplier and stay factor × Normal(1, 0.06) and Normal(1, 0.04); residuals by 4-week block bootstrap of the market's weekly training residuals; seed from the scenario via SHA-256. On a served route each draw's scenario arrivals are its baseline arrivals × the structural arrivals ratio |
| Conformal margin | Per market: (1 − α) quantile of in-sample relative planning-mode error on the training window, α = 0.2 |
| Coverage | Holdout coverage of the conformal range against its 80% target: [planning holdout](../results/planning-holdout.md) |
| Tornado | Guest swing for ±15% seats, ±4 pp LF, ±5 pp P2P share, ±10% multiplier, ±0.5 stay factor; cold-start markets use a reference route |

## Archetypes (`domain/archetypes.py`)

Seven archetypes, one per market: Direct Leisure, Resident / VFR, Regional GCC, Hub-Mediated, Highly Seasonal, Emerging / Sparse, Domestic Staycation. Each carries default LF, P2P share, multiplier and stay factor for cold start. They describe aggregate market behaviour, not traveller demographics. Assignment: [market directory](../guide/simulator.md#market-directory).

## Back-test design

| Item | Definition |
| --- | --- |
| Split | Single forward split over complete train-split weeks with complete guest inputs: calibration week starts 2023-01-02 to 2024-12-23 (104 weeks, 2,132 market-weeks); holdout 2024-12-30 to 2025-07-21 (30 weeks, 621 market-weeks, 21 markets) |
| Trainers | `twin evaluate` fits `StructuralEngine.calibrate`, `ResidualMLEngine.fit`, `calibrate_conformal` on the calibration window only |
| WMAPE | Σ\|actual − predicted\| / Σ actual |
| Bias | (Σ predicted − Σ actual) / Σ actual; positive = over-forecast |
| Baselines | (1) market-season mean of training guests; (2) per-market ridge on calendar features; (3) structural planning prediction; (4) hybrid |
| Output | `lake/curated/evaluation_results.json`; [planning holdout](../results/planning-holdout.md) |
