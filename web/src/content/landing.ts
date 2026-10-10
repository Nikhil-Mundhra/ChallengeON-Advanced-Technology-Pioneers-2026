/** Landing page chapters: plain titles, one idea each. Numbers come from the engine at render time. */
export const CHAPTERS = [
  { id: "months", number: "01", label: "Month by month", kicker: "The coming months" },
  { id: "markets", number: "02", label: "Where visitors come from", kicker: "Source markets" },
  { id: "questions", number: "03", label: "What if…?", kicker: "Five planning questions" },
  { id: "trust", number: "04", label: "How sure we are", kicker: "Accuracy" },
] as const;

/** Daily accuracy on validation periods (README §3.1, shipped nowcast), as shown on the report page. */
export const DAILY_ERROR = { domestic: 4.18, international: 4.59 };
