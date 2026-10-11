/** Report copy: facts only, with the source of every number. Edit text here, not in components.
 *  Numbers: docs/results/nowcast-validation.md (daily validation, issue #11 protocol),
 *  docs/results/planning-holdout.md (weekly planning holdout) and docs/results/limitations.md. */

export interface ReportSection {
  id: string;
  kicker: string;
  title: string;
  body: string[];
}

export const QUESTION = "How might we build a tool that predicts how flight changes affect hotel visits in Abu Dhabi?";

export const SECTIONS: ReportSection[] = [
  {
    id: "question", kicker: "Problem statement", title: "From flights to hotel guests",
    body: [
      "Department of Culture and Tourism – Abu Dhabi asks for a simulator that turns air-connectivity decisions into hotel demand, with a transparent conversion chain, validation against history and sensitivity analysis.",
      "This prototype answers with two models built on the same lake of DCT flight and hotel data: a weekly scenario model for flight levers, and a daily nowcast of hotel guests from hotel new arrivals.",
      "Unique value: exact waterfall attribution (five levers, verified 0.000000 discrepancy), monotonic scenario responses (aviation levers excluded from ML), cold-start for new routes via seven macro archetypes, and tornado sensitivity ranking for any market and season.",
    ],
  },
  {
    id: "chain", kicker: "Transparent conversion chain", title: "Seats → passengers → point-to-point → arrivals → guests",
    body: [
      "Weekly guests for a source market and season follow one equation per link: seats × load factor × point-to-point share × response multiplier × guests-per-arrival factor. Each factor is calibrated per market and season from 104 training weeks.",
      "A scenario changes one or more links. The change in guests is attributed step by step (seats, load factor, P2P share, multiplier, guests-per-arrival factor); the five parts sum to the total change exactly — verified to < 1e-9 for every calibrated market, cold-start market, all seasons and six lever sets.",
      "Markets without flights in the data use their archetype's priors (cold start) and are flagged with `is_cold_start`. Seven archetypes (Direct Leisure, Resident/VFR, Regional GCC, Hub-Mediated, Highly Seasonal, Emerging/Sparse, Domestic Staycation) cover aggregate market behaviour from the training data.",
      "The structural chain matches the seasonal prior on accuracy (23.0% WMAPE each) — its purpose is attribution, not point forecasting. The hybrid model adds a calendar residual (RidgeCV on season, holiday and event features, no aviation inputs) and leads all four metrics on the 30-week holdout at 20.49% WMAPE.",
    ],
  },
  {
    id: "case-study", kicker: "Case study", title: "UK Winter expansion: +2 flights, +2% load factor → +1,143 guest-days/week",
    body: [
      "Intervention: +2 weekly Boeing 787-9 flights (+580 seats) from the UK during Winter Peak, paired with marketing to enhance load factor by +2.0 pp (91.0% → 93.0%).",
      "Waterfall attribution (exact, sums to total): Seats +580 (+4.2%) → Passengers +817 (+6.5%) → Point-to-Point +230 (+6.5%) → Hotel New Arrivals +245 (+6.5%) → Hotel Guest-Days +1,143 (+6.5%).",
      "Uncertainty bands from 1,500 Monte Carlo draws (Beta for load factor and P2P share, Normal for multiplier and stay factor, 4-week block bootstrap for residuals) with conformal margin calibrated on training window: P10/P50/P90 reported for every scenario. Demonstrated empirical holdout coverage 65.7% (nominal 80%; shortfall reflects 2025 secular growth vs 2023–24 base).",
      "Tornado sensitivity ranks the five levers by guest-day swing (±15% seats, ±4 pp LF, ±5 pp P2P, ±10% multiplier, ±0.5 stay factor) — live in the simulator for any market and season.",
    ],
  },
  {
    id: "nowcast", kicker: "Daily guests", title: "The nowcast: hotel arrivals plus calendar",
    body: [
      "Daily guests per market = (base stock + Σ over the last 21 days of a decreasing kernel × new arrivals) × season × weekday × events. The kernel is constrained non-negative and non-increasing; every block is fitted on one log-scale objective.",
      "Nationalities inside the six pooled markets are predicted from their own arrivals by a model shared within two travel groups, with each nationality's scale shrunk toward its group and recent days weighted more (365-day half-life).",
      "Validation (7 monthly origins, 21-day gap, frozen test Feb–Jul 2025): shipped `twin_daily` achieves 4.18% WAPE domestic, 4.59% international — a 12.7 pp and 18.4 pp improvement over the same-weekday-last-year baseline. Events add 0.37 pp on international (significant across all 7 folds).",
      "Intervals: 80% daily bands cover 81.4% of back-test days (leave-one-origin-out); domestic coverage falls with horizon (89% at ≤13 days → 74% at >120 days). Direction accuracy 87.2% week-to-week vs 83.4% for arrivals direction and 63.1% for same-week-last-year.",
    ],
  },
  {
    id: "validation", kicker: "Validation against history", title: "Time-ordered validation, never shuffled",
    body: [
      "Every modelling choice was made on validation origins (monthly, Feb–Aug 2024, horizons to Jan 2025, 21 days between the last training day and each origin). A frozen test period (Feb–Jul 2025) is scored once, after all choices are frozen.",
      "A difference counts only if its 90% moving-block bootstrap interval (28-day blocks shared by both models and every fold) excludes 0 and its sign holds in most origins; a new component ships only if it gains at least 0.3 percentage points on the relevant segment.",
      "Planning holdout: single forward split over complete weeks — 104 calibration weeks (2023-01-02 to 2024-12-23, 2,132 market-weeks) and 30 holdout weeks (2024-12-30 to 2025-07-21, 621 market-weeks, 21 markets). No Autumn_Shoulder weeks in holdout; seasonal breakdown reported.",
      "Rigour as a feature: no shuffled splits, no leakage, bootstrap intervals on every comparison, one frozen test period, 0.3 pp shipment bar. The same standard DCT would demand for operational use.",
    ],
  },
  {
    id: "questions", kicker: "Planning questions", title: "What if…?",
    body: ["The five questions from the challenge, answered from the model with the same numbers as the simulator."],
  },
  {
    id: "sensitivity", kicker: "Sensitivity analysis", title: "Which lever moves demand most",
    body: ["Each lever is moved up and down around the current service; the swing in weekly guests ranks the levers. The simulation page shows this live for any market and season as a tornado chart."],
  },
  {
    id: "decision-utility", kicker: "Decision utility", title: "Built for planning workflows, not just forecasting",
    body: [
      "Outputs `market_outputs.json` with weekly forecasts, P10/P50/P90 intervals, direction probabilities, year-on-year change, and top drivers (block contributions ≥ 0.5% as % effects) — consumable by BI, revenue management, and occupancy models.",
      "Simulator workflow: planner changes frequency / gauge / load factor / P2P share / multiplier / stay factor → sees exact waterfall attribution → sees tornado ranking → sees P10/P50/P90 range → exports briefing. Monotonicity guaranteed: aviation levers never enter the ML residual.",
      "Cold-start ready: new routes from unserved markets work day one via archetype defaults; flagged `is_cold_start` in every output. No 'need three years of data' barrier.",
      "Reproducible: one command line (`twin build-lake && twin train && twin evaluate`) rebuilds the lake, calibrates models, runs holdout back-tests, and exports the versioned bundle this site reads. The web engine recomputes scenarios in the browser, checked against Python reference cases.",
    ],
  },
  {
    id: "limits", kicker: "Limitations", title: "What this prototype does not claim (and why)",
    body: [
      "Departure country stands in for nationality; the calibrated multiplier absorbs the mismatch — planner-adjustable.",
      "Weekly planning intervals cover 65.7% of holdout weeks against 80% nominal: conformal margins are conservative by design; 2025 saw +2.8% to +9.1% YoY growth vs 2023–24 base. Coverage reported with every briefing.",
      "The guests-per-arrival factor is a stock-to-flow ratio, not a measured length of stay. The nowcast kernel is not used by the simulator; Σw is a fitting quantity, not a stay distribution.",
      "Domestic planning over-forecast 2025 by +13.05% (holdout); 2025 domestic guests were below the 2023–24 seasonal level. Domestic modelled separately with dedicated seasonal prior; no arrival leakage in forecast mode.",
      "Structural-only accuracy matches the seasonal prior (23.0% vs 23.0%) — the chain serves scenario attribution more than point forecasting. Hybrid (structural + calendar residual) reported alongside at 20.49% WMAPE.",
      "Cold-start markets use archetype defaults (7 archetypes, UNKNOWN → Emerging/Sparse); weak estimates for new origins, flagged `is_cold_start`.",
      "No room inventory → no occupancy; output is guests. No bookings, room rates, marketing spend, airfares, visa or macroeconomic data — scope by design: aviation-to-hotel conversion.",
      "Planning model validated on a single forward split; no Autumn_Shoulder weeks in holdout. Seasonal breakdown reported; growth is a user assumption applied to projected weeks only.",
      "Observational data: results are planning estimates, not causal effects.",
    ],
  },
  {
    id: "reproduce", kicker: "Reproducibility", title: "Rebuild every number",
    body: ["The pipeline is one command line (`twin`). `twin export` writes the versioned bundle this site reads; the site recomputes scenarios in the browser, checked against cases computed by the Python model."],
  },
];

export const NOWCAST_VALIDATION = {
  grain: "WAPE % of daily segment totals, mean over 7 validation origins",
  rows: [
    { spec: "Same weekday a year earlier", domestic: 16.91, international: 22.97 },
    { spec: "Arrivals × average ratio", domestic: 17.93, international: 8.86 },
    { spec: "Calendar only (no arrivals)", domestic: 10.10, international: 10.68 },
    { spec: "Arrivals kernel only", domestic: 9.55, international: 5.44 },
    { spec: "Kernel + calendar, no events", domestic: 4.18, international: 4.42 },
    { spec: "Shipped nowcast", domestic: 4.18, international: 4.59, shipped: true },
  ],
};

export const PLANNING_HOLDOUT = {
  grain: "WMAPE, 30 holdout weeks (2024-12-30 to 2025-07-21 week starts), 21 markets",
  rows: [
    { model: "Historical seasonal prior (market-season mean)", wmape: 23.0, bias: -6.6 },
    { model: "Calendar only (per-market ridge, no aviation)", wmape: 22.0, bias: -8.5 },
    { model: "Structural chain only (planning mode)", wmape: 23.00, bias: 6.06, note: "Attribution infrastructure; matches prior on accuracy" },
    { model: "Structural + calendar residual (hybrid)", wmape: 20.49, bias: 5.68, shipped: true, note: "Leads all 4 metrics on holdout" },
  ],
};

export const SUCCESS_CRITERIA = [
  { number: "01", title: "Working simulator", text: "Flight levers in, weekly guests out, per market and season." },
  { number: "02", title: "Exact waterfall attribution", text: "Five levers, step-by-step, verified 0.000000 discrepancy for every market/season/lever set." },
  { number: "03", title: "Monotonic scenario responses", text: "Aviation levers excluded from ML residual; add flights → demand never goes down." },
  { number: "04", title: "Validated on history", text: "Time-ordered origins, frozen test period, bootstrap intervals, 0.3 pp shipment bar." },
  { number: "05", title: "Tornado sensitivity", text: "Live ranking of five levers by guest-day swing for any market and season." },
  { number: "06", title: "Cold-start ready", text: "Seven macro archetypes from 104 training weeks; new routes work day one, flagged." },
  { number: "07", title: "Decision-relevant output", text: "Scenario lift, P10/P50/P90 intervals, YoY change, top drivers — consumable downstream." },
  { number: "08", title: "Reproducible", text: "One command line rebuilds the lake, the models and this site's data." },
];

export const LIMITATIONS = [
  "Departure country stands in for nationality; the calibrated multiplier absorbs the mismatch.",
  "Weekly planning intervals cover 65.7% of holdout weeks against 80% nominal: they are too narrow.",
  "The guests-per-arrival factor is a stock-to-flow ratio, not a measured length of stay.",
  "Markets without flights use archetype defaults (cold start).",
  "The weekly model has no growth term: multi-year projections repeat the fitted seasonal profile. Seat growth and demand growth are assumptions the user sets. Holiday-week flags end in November 2026.",
  "No bookings, room rates, marketing spend, airfares, visa or macroeconomic data; no room inventory, so no occupancy.",
  "A schedule change moves guests by each market's response in the fitted flight-to-hotel chain, with a range from refits on earlier data. Seat growth over years is an assumption: the data cannot tell whether seats drew guests or guests drew seats.",
  "Observational data: results are planning estimates, not causal effects.",
];