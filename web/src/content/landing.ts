/** Landing page chapters: plain titles, one idea each. Numbers come from the engine at render time. */
export const CHAPTERS = [
  { id: "months", number: "01", label: "Month by month", kicker: "The coming months" },
  { id: "markets", number: "02", label: "Where visitors come from", kicker: "Source markets" },
  { id: "questions", number: "03", label: "What if…?", kicker: "Five planning questions" },
  { id: "trust", number: "04", label: "How sure we are", kicker: "Accuracy" },
] as const;

/** Daily accuracy on validation periods (docs/results/nowcast-validation.md, shipped nowcast), as shown on the report page. */
export const DAILY_ERROR = { domestic: 4.18, international: 4.07 };

/** The arrivals assumption behind each outlook scenario (src/tourism_twin/nowcast/outlook.py), completing "Projected from ...". */
export const SCENARIO_ASSUMPTION: Record<string, string> = {
  flat: "arrivals held at last year's level",
  trend: "arrivals kept on their growth over the last year of data",
};
/** Years the outlook back-test windows fall in (`twin export` outlook bands); a growth period, so the correction leans up. */
export const OUTLOOK_BACKTEST_YEARS = "2023 to 2024";
