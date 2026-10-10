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
| Market bridge | Departure country k is linked to nationality k; M absorbs non-national passengers, indirect connections and overland arrivals. A 45 × 33 country-to-nationality matrix (1,485 parameters) is not estimated |
| Planning prediction (`planning_guests`) | Scheduled seats × calibrated LF, P2P share, M, L. A served market whose seats carry no P2P passengers has zero aviation arrivals; an unserved market keeps its calibrated arrivals. The simulator baseline uses the same rule (`MarketSeasonParams.arrivals_from`) |
| Domestic | `DOMESTIC` = calibrated seasonal arrivals × L, independent of seats; seat, frequency, load-factor and P2P levers have no effect; multiplier and stay-factor levers do (tested) |
| Cold start | A country without calibration gets its archetype's default LF, P2P share, M and L (`domain/archetypes.py`); unknown countries map to Emerging / Sparse |
| Waterfall | Lift attributed sequentially: seats, load factor, P2P share, multiplier, stay factor. The five parts sum to the total lift (tested to < 1e-9 for every calibrated market, a cold-start market, all seasons and 6 lever sets); `simulate` raises above a relative 1e-9 (absolute 1e-6) |

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
| `RidgeCV` uses non-temporal CV |
| Holiday flags are the legacy `is_holiday_week` and `is_major_event_week`, which lump Eid al-Fitr, Eid al-Adha, National Day and New Year |

## Uncertainty and sensitivity (`planning/uncertainty.py`, `planning/conformal.py`, `planning/sensitivity.py`)

| Component | Method |
| --- | --- |
| Monte Carlo (1,500 draws default) | Load factor and P2P share ~ Beta (method of moments, sd 0.03 and 0.04); multiplier and stay factor × Normal(1, 0.06) and Normal(1, 0.04); residuals by 4-week block bootstrap of the market's weekly training residuals; seed from the scenario via SHA-256 |
| Conformal margin | Per market: (1 − α) quantile of in-sample relative planning-mode error on the training window, α = 0.2 |
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
