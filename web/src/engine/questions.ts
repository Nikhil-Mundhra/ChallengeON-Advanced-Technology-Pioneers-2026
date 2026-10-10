/**
 * Worked answers to the challenge's five planning questions, computed from the bundle so the text
 * on the landing and report pages always matches the model. Each lever answer gives the change in
 * weekly hotel guests for one market and season, its error, and (when the market has weekly
 * history) the extra guests over a forecast year with the change applied from its first week.
 */
import { hybrid, NO_CHANGE, simulate, weeklyHeadline, type Lever, type Planning } from "./planning";
import { timeline, type Weekly } from "./weekly";

export interface LeverAnswer {
  market: string; season: string; lever: Lever;
  perWeek: number;            // extra hotel guests a week in that season
  errorPct: number;           // likely error of the weekly figure, as a share
  year: string | null;        // forecast year summed
  perYear: number | null;     // extra hotel guests over that year
}
export interface MixAnswer { season: string; top: Array<{ market: string; share: number }> }

const lever = (patch: Partial<Lever>): Lever => ({ ...NO_CHANGE, ...patch });

export function leverAnswer(planning: Planning, weekly: Weekly, market: string, season: string, change: Lever, year: string): LeverAnswer {
  const h = weeklyHeadline(planning, market, season, change);
  let perYear: number | null = null;
  if (weekly.markets[market]) {
    const points = timeline(planning, weekly, market, change, { start: `${year}-01-01` });
    perYear = points.filter((p) => p.week.startsWith(year) && p.scenario !== null && p.actual === null)
      .reduce((t, p) => t + (p.scenario! - p.model), 0);
  }
  return { market, season, lever: change, perWeek: h.change, errorPct: h.errorPct, year: perYear === null ? null : year, perYear };
}

/** Share of weekly hotel guests by source market in a season (visitors only, residents excluded). */
export function seasonMix(planning: Planning, season: string, top = 3): MixAnswer {
  const rows = Object.keys(planning.calibration).filter((m) => m !== "DOMESTIC")
    .map((market) => ({ market, guests: hybrid(planning, simulate(planning, market, season)).base }));
  const total = rows.reduce((t, r) => t + r.guests, 0);
  return { season, top: rows.sort((a, b) => b.guests - a.guests).slice(0, top).map((r) => ({ market: r.market, share: r.guests / total })) };
}

/** The five questions with the example each answer uses. */
export function answerQuestions(planning: Planning, weekly: Weekly, year = "2026") {
  return {
    newRoute: leverAnswer(planning, weekly, "JAPAN", "Winter_Peak", lever({ delta_frequency: 3, aircraft_gauge: 300 }), year),
    frequency: leverAnswer(planning, weekly, "UNITED KINGDOM", "Winter_Peak", lever({ delta_frequency: 2, aircraft_gauge: 290 }), year),
    seats: leverAnswer(planning, weekly, "INDIA", "Winter_Peak", lever({ delta_seats_pct: 0.1 }), year),
    fuller: leverAnswer(planning, weekly, "GERMANY", "Winter_Peak", lever({ delta_load_factor: 0.05 }), year),
    mix: [seasonMix(planning, "Winter_Peak"), seasonMix(planning, "Summer_Trough")],
  };
}
