/** Report copy: facts only, with the source of every number. Edit text here, not in components.
 *  Numbers: docs/results/nowcast-validation.md (daily validation, issue #11 protocol),
 *  docs/results/planning-holdout.md (weekly planning holdout), docs/results/limitations.md,
 *  docs/evidence/scenario-response.md and experiment/scenario_response/README.md (schedule response),
 *  and the `twin simulate` UK case (README.md, "Try a scenario"). */

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
      "Department of Culture and Tourism – Abu Dhabi asks for a simulator that turns air-connectivity decisions into hotel demand, with a clear conversion chain, validation against history and sensitivity analysis.",
      "This prototype answers with two models built on the same lake of DCT flight and hotel data: a weekly planning model for flight scenarios, and a daily nowcast of hotel guests from hotel new arrivals.",
      "For a planner the simulator gives a schedule response learned per market and season from the data, a waterfall that splits a scenario's guest change across five levers, estimates for new routes from seven market archetypes, and a ranking of the levers by how far they move guests.",
    ],
  },
  {
    id: "chain", kicker: "Transparent conversion chain", title: "Seats → passengers → point-to-point → arrivals → guests",
    body: [
      "The weekly baseline for a source market and season is one equation: seats × load factor × point-to-point share × response multiplier × guests-per-arrival factor. Each ratio is the market's average for that season over the training weeks; none is fitted by optimisation. A calendar model (RidgeCV on season, holiday and event features, no flight inputs) adds what the ratios miss. The two together are the hybrid model.",
      "A schedule change (extra flights, larger aircraft, more seats on existing flights) scales guests by (new seats ÷ current seats)^ε. ε comes from a daily model fitted to the data, in which seats drive hotel new arrivals and new arrivals drive guests. Seats are raised and cut by 10% and 25% over the last training year, the model is re-run, and the guest change gives ε per market and season: 0.31 for the UK in the winter peak, for example. The same reading on 7 refits to earlier data gives the range (UK winter peak 0.31 to 0.48).",
      "Every market's ε and its range are above 0, so added seats never lower guests in the model. A market without its own response uses the median over markets for the season, with the widest range among them. A new route adds its point-to-point passengers at no more than one hotel arrival each.",
      "Load factor, point-to-point share, the multiplier and the guests-per-arrival factor are planner assumptions applied on top. Seat growth over several years is an assumption too: guests follow it with an effect from 0 (not at all) to 1 (one for one), and the central line is the past co-movement of guest and seat trends (0.60). That line is an association: the data cannot tell whether seats drew guests or guests drew seats.",
      "The change in guests is split step by step across seats (the schedule response), load factor, point-to-point share, multiplier and guests-per-arrival factor. The five parts add up to the total change, tested to within 1e-9 for every calibrated market, a cold-start market, every season and six lever sets.",
      "Markets without flights in the data use their archetype's default ratios (cold start) and are flagged with `is_cold_start`. The seven archetypes are Direct Leisure, Resident/VFR, Regional GCC, Hub-Mediated, Highly Seasonal, Emerging/Sparse and Domestic Staycation.",
      "On the 30-week holdout the ratio chain alone has the same error as the seasonal average (23.00% WMAPE each). The hybrid has the lowest error of the four weekly models on all four measures, at 20.49% WMAPE.",
    ],
  },
  {
    id: "case-study", kicker: "Case study", title: "UK winter: 2 more flights a week add 227 guest-nights a week",
    body: [
      "Scenario: 2 more weekly flights from the UK in the winter peak on 290-seat aircraft (+580 seats), with the load factor unchanged at 91.0%.",
      "Chain from `twin simulate`: seats 13,844 to 14,424 (+4.2%), passengers +528, point-to-point passengers +149, hotel new arrivals +49 (+1.3%), guests 17,645 to 17,872 (+227, +1.3%). The UK winter ε of 0.31 turns the 4.2% seat increase into a 1.3% guest increase, and the whole change sits on the seats step of the waterfall.",
      "At the low and high ends of the UK winter range (0.31 to 0.48) the same change adds 224 to 354 guests a week.",
      "The wider range in the simulator and the briefing is scenario guests ± the market's error margin: the 80th percentile of its relative planning error on training weeks, 38% for the UK. For this lift that is −6,563 to +7,018. On the 2025 holdout these ranges held the actual week 65.7% of the time against an 80% target, so they are too narrow. The Python engine also runs 1,500 Monte Carlo draws (Beta for load factor and point-to-point share, normal shocks for multiplier and guests-per-arrival factor, 4-week block bootstrap for residuals); the briefing and the site show the margin range.",
      "The tornado ranks the five levers by guest swing (±15% seats, ±4 pp load factor, ±5 pp point-to-point share, ±10% multiplier, ±0.5 guests-per-arrival factor). For the UK in winter the point-to-point share moves guests most (5,869 a week) and seats come fourth (1,658).",
    ],
  },
  {
    id: "nowcast", kicker: "Daily guests", title: "The nowcast: hotel arrivals plus calendar",
    body: [
      "Daily guests per market = (base stock + Σ w_k × new arrivals k days earlier, k = 0 to 21) × exp(season + weekday + events). The weights w are non-negative, never rise with k, and w0 is at most 1; they are fitted by constrained least squares. The base stock bends at knots every 45 days for international markets and every 365 days for domestic. The blocks are fitted in turn (backfitting) on one log-scale objective. Domestic has a slope term and no event terms.",
      "The 30 nationalities inside the six pooled markets are predicted from their own arrivals by a model shared within two stay groups (short and long), with each nationality's scale shrunk toward its group and recent days weighted more (365-day half-life).",
      "Validation (7 monthly origins from Feb to Aug 2024, 21-day gap): the shipped nowcast has 4.18% WAPE domestic and 4.07% international on daily totals. Per market and day it is 12.71 pp (domestic) and 19.87 pp (international) below the same-weekday-last-year baseline, in all 7 folds. Event terms lower international market-day error by 0.42 pp, and knots every 45 days instead of 365 lower it by 1.45 pp, both in 7 of 7 folds.",
      "Intervals: 80% daily ranges cover 81.4% of back-test days when fitted on the other origins; domestic coverage falls with horizon (89% at 13 days or less, 74% beyond 120 days). Week-to-week direction is right 87.2% of the time, against 83.4% for the direction of new arrivals and 63.1% for last year's direction.",
    ],
  },
  {
    id: "validation", kicker: "Validation against history", title: "Time-ordered validation, never shuffled",
    body: [
      "Every model choice was made on validation origins (monthly, Feb to Aug 2024, horizons to Jan 2025, 21 days between the last training day and each origin). A frozen test period (Feb to Jul 2025) is scored once, after every choice is fixed.",
      "A difference counts only if its 90% moving-block bootstrap interval (28-day blocks shared by both models and every fold) excludes 0 and its sign holds in most folds. A nowcast component ships only if it lowers error by at least 0.3 percentage points.",
      "Planning holdout: one forward split over complete weeks, with 104 calibration weeks (2023-01-02 to 2024-12-23, 2,132 market-weeks) and 30 holdout weeks (2024-12-30 to 2025-07-21, 621 market-weeks, 21 markets). The holdout has no Autumn_Shoulder weeks; results are also reported by season.",
      "The schedule response was tested on the 7 validation folds, on 717 market-weeks where seats moved more than 15% against the same week a year earlier (624 increases, 93 cuts). On the log change in guests, the fitted chain's mean error is 0.066 lower than the calendar-only model [0.043, 0.093]: 0.054 lower on increases and 0.142 lower on cuts. The previous ratio-chain response was no better than the calendar-only model (+0.002 [−0.018, +0.018]), and a short-run elasticity fitted per market was worse (+0.066).",
      "On 48 market-weeks where seats moved against their own 13-week trend, no flight model beat the calendar-only model; every interval includes 0.",
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
    id: "decision-utility", kicker: "Decision utility", title: "What planners get from it",
    body: [
      "`market_outputs.json` holds weekly forecasts, P10/P50/P90 ranges, direction probabilities, year-on-year change and top drivers (block effects of at least 0.5%) for other tools to read.",
      "Simulator: the planner changes extra flights, aircraft size, seats on existing flights, seat growth, load factor, point-to-point share, multiplier or guests-per-arrival factor, and sees the schedule response with its range, the waterfall, the lever ranking and the error range. `twin simulate` prints the same scenario as a briefing.",
      "New routes from markets without flights get an estimate from their archetype's defaults, flagged `is_cold_start` in every output.",
      "`make all` rebuilds the lake, refits the models and reruns the holdout back-test; `make export` writes the versioned bundle this site reads. The site recomputes scenarios in the browser and is checked against Python reference cases.",
    ],
  },
  {
    id: "limits", kicker: "Limitations", title: "What the model does not cover",
    body: [
      "Departure country stands in for nationality; the calibrated multiplier absorbs the mismatch and the planner can adjust it.",
      "Weekly planning ranges cover 65.7% of holdout weeks against an 80% target: they are too narrow. Coverage is printed with every briefing.",
      "The guests-per-arrival factor is a stock-to-flow ratio, not a measured length of stay. The nowcast weight sum Σw is a fitting quantity, not a stay distribution, and the simulator does not use it.",
      "Domestic planning over-forecast 2025 by 13.05% on the holdout; 2025 domestic guests were below the 2023 to 2024 seasonal level. Domestic is modelled separately and uses no holdout arrivals.",
      "The ratio chain alone matches the seasonal average on accuracy (23.00% vs 23.00%). The hybrid (20.49% WMAPE) is reported alongside.",
      "The full-fit ε sits at or near the low end of its refit range in most markets; refits on data to January to July 2024 give higher values.",
      "Cold-start markets use archetype defaults (seven archetypes; unknown countries map to Emerging/Sparse). Estimates for new origins are weak and flagged `is_cold_start`.",
      "No room inventory, so no occupancy; output is guests. No bookings, room rates, marketing spend, airfares, visa or macroeconomic data.",
      "The planning model is validated on a single forward split with no Autumn_Shoulder weeks. Projected years repeat the seasonal profile; growth is a user assumption on projected weeks only.",
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
    { spec: "Calendar only (no arrivals)", domestic: 10.09, international: 10.68 },
    { spec: "Arrivals kernel only", domestic: 9.55, international: 5.44 },
    { spec: "Kernel + calendar, no events", domestic: 4.18, international: 4.05 },
    { spec: "Shipped nowcast", domestic: 4.18, international: 4.07, shipped: true },
  ],
};

export const PLANNING_HOLDOUT = {
  grain: "WMAPE, 30 holdout weeks (2024-12-30 to 2025-07-21 week starts), 21 markets",
  rows: [
    { model: "Historical seasonal prior (market-season mean)", wmape: 23.0, bias: -6.6 },
    { model: "Calendar only (per-market ridge, no aviation)", wmape: 22.0, bias: -8.5 },
    { model: "Structural chain only (planning mode)", wmape: 23.00, bias: 6.06, note: "Same error as the seasonal prior" },
    { model: "Structural + calendar residual (hybrid)", wmape: 20.49, bias: 5.68, shipped: true, note: "Lowest error on all four holdout measures" },
  ],
};

export const SUCCESS_CRITERIA = [
  { number: "01", title: "Working simulator", text: "Flight levers in, weekly guests out, per market and season." },
  { number: "02", title: "Exact waterfall attribution", text: "Five levers, step by step; the parts add up to the total change within 1e-9." },
  { number: "03", title: "Learned schedule response", text: "Each market's guest response to seats, per season, from the fitted flight-to-hotel chain, with a range from refits." },
  { number: "04", title: "Validated on history", text: "Time-ordered origins, frozen test period, bootstrap intervals, 0.3 pp shipment bar." },
  { number: "05", title: "Tornado sensitivity", text: "Live ranking of five levers by guest swing for any market and season." },
  { number: "06", title: "New routes", text: "Seven market archetypes with default ratios; a new route gets an estimate, flagged as cold start." },
  { number: "07", title: "Decision-relevant output", text: "Scenario lift, P10/P50/P90 ranges, year-on-year change and top drivers per market." },
  { number: "08", title: "Reproducible", text: "One command line rebuilds the lake, the models and this site's data." },
];

export const LIMITATIONS = [
  "Departure country stands in for nationality; the calibrated multiplier absorbs the mismatch.",
  "Weekly planning intervals cover 65.7% of holdout weeks against 80% nominal: they are too narrow.",
  "The guests-per-arrival factor is a stock-to-flow ratio, not a measured length of stay.",
  "Markets without flights use archetype defaults (cold start).",
  "The weekly model has no growth term: multi-year projections repeat the fitted seasonal profile. Seat growth and demand growth are assumptions the user sets. Holiday-week flags end with the week of 8 February 2027.",
  "No bookings, room rates, marketing spend, airfares, visa or macroeconomic data; no room inventory, so no occupancy.",
  "A schedule change moves guests by each market's response in the fitted flight-to-hotel chain, with a range from refits on earlier data. Seat growth over years is an assumption: the data cannot tell whether seats drew guests or guests drew seats.",
  "Observational data: results are planning estimates, not causal effects.",
];
