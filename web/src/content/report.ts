/** Report copy: facts only, with the source of every number. Edit text here, not in components.
 *  Numbers: README §3 (validation, issue #11 protocol; weekly planning holdout) and
 *  docs/solution_documentation.md §11 (limitations). */

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
    ],
  },
  {
    id: "chain", kicker: "Transparent conversion chain", title: "Seats → passengers → point-to-point → arrivals → guests",
    body: [
      "Weekly guests for a source market and season follow one equation per link: seats × load factor × point-to-point share × response multiplier × guests-per-arrival factor. Each factor is calibrated per market and season from 104 training weeks.",
      "A scenario changes one or more links. The change in guests is attributed step by step (seats, load factor, P2P share, multiplier, guests-per-arrival factor); the five parts sum to the total change exactly.",
      "Markets without flights in the data use their archetype's priors (cold start) and are flagged.",
      "Over time, the same model is back-tested week by week (fitted before 30 holdout weeks, then scored on them) and projected three years ahead from each market's calibrated seasonal service. A scenario moves every week from a chosen start date by the change for that week's season.",
    ],
  },
  {
    id: "nowcast", kicker: "Daily guests", title: "The nowcast: hotel arrivals plus calendar",
    body: [
      "Daily guests per market = (base stock + Σ over the last 21 days of a decreasing kernel × new arrivals) × season × weekday × events. The kernel is constrained non-negative and non-increasing; every block is fitted on one log-scale objective.",
      "Nationalities inside the six pooled markets are predicted from their own arrivals by a model shared within two travel groups, with each nationality's scale shrunk toward its group and recent days weighted more.",
    ],
  },
  {
    id: "validation", kicker: "Validation against history", title: "Time-ordered validation, never shuffled",
    body: [
      "Every choice was made on validation origins (monthly, Feb–Aug 2024, horizons to Jan 2025, 21 days between the last training day and each origin). A frozen test period (Feb–Jul 2025) is scored once, after all choices.",
      "A difference counts only if its 90% moving-block bootstrap interval excludes 0 and its sign holds in most origins; a new part ships only if it gains at least 0.3 points.",
    ],
  },
  {
    id: "questions", kicker: "Planning questions", title: "What if…?",
    body: ["The five questions from the challenge, answered from the model with the same numbers as the simulator."],
  },
  {
    id: "sensitivity", kicker: "Sensitivity analysis", title: "Which lever moves demand most",
    body: ["Each lever is moved up and down around the current service; the swing in weekly guests ranks the levers. The simulation page shows this live for any market and season."],
  },
  {
    id: "limits", kicker: "Limitations", title: "What this prototype does not claim",
    body: [],
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
    { model: "Historical seasonal prior", wmape: 23.0, bias: -6.6 },
    { model: "Calendar ridge (no aviation)", wmape: 22.0, bias: -8.5 },
    { model: "Structural chain only", wmape: 23.14, bias: 5.93 },
    { model: "Structural + calendar residual (before events)", wmape: 21.74, bias: 5.36 },
    { model: "Structural + calendar and event residual", wmape: 20.62, bias: 5.55, shipped: true },
  ],
};

export const SUCCESS_CRITERIA = [
  { number: "01", title: "Working simulator", text: "Flight levers in, weekly guests out, per market and season." },
  { number: "02", title: "Transparent chain", text: "One equation per link, with an exact step-by-step attribution." },
  { number: "03", title: "Validated on history", text: "Time-ordered validation origins and one frozen test period." },
  { number: "04", title: "Sensitivity", text: "Tornado ranking of the five levers for any scenario." },
  { number: "05", title: "Useful granularity", text: "15 source countries, 5 regional groups and domestic; daily and weekly; 45 nationalities." },
  { number: "06", title: "Decision relevance", text: "Scenario lift, intervals and the change against the previous period." },
  { number: "07", title: "Reproducible", text: "One command line rebuilds the lake, the models and this site's data." },
];

export const LIMITATIONS = [
  "Departure country stands in for nationality; the calibrated multiplier absorbs the mismatch.",
  "Weekly planning intervals cover 65.2% of holdout weeks against 80% nominal: they are too narrow.",
  "The guests-per-arrival factor is a stock-to-flow ratio, not a measured length of stay.",
  "Markets without flights use archetype defaults (cold start).",
  "The weekly model has no growth term: multi-year projections repeat the fitted seasonal profile, and growth is an assumption the user sets. Holiday-week flags end in November 2026.",
  "No bookings, room rates, marketing spend, airfares, visa or macroeconomic data; no room inventory, so no occupancy.",
  "Observational data: results are planning estimates, not causal effects.",
];
