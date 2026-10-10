/**
 * The weekly scenario model over time (export/bundle.weekly_part): back-test against actual weeks
 * and a projection PROJECTION_YEARS ahead. A scenario changes weeks from `start` on by the
 * simulator's change for each week's season, so the timeline and the scenario cards agree:
 *   guests_w = max(0, structural_w + residual_w + delta_season(w)) * growth_w
 * The model has no growth term; `growthPct` is a stated assumption, compounded per year after the
 * first projected week (no flight schedule) and applied to projected weeks only, so there is no step.
 */
import { conformalBands, NO_CHANGE, simulate, type Lever, type Planning } from "./planning";

export interface WeeklyMarket {
  week: string[];
  season: string[];
  kind: Array<"history" | "scheduled" | "projected">;
  actual: Array<number | null>;
  structural: number[];
  residual: number[];
  holdout: Array<number | null>;
  event?: Array<string | null>;   // event type covering most of the week (domain/events.csv code)
}

export interface Weekly {
  holdout_start: string;
  last_actual_week: string;
  calendar_flags_until: string;
  formula: string;
  markets: Record<string, WeeklyMarket>;
}

export interface WeekPoint {
  week: string;
  kind: WeeklyMarket["kind"][number];
  actual: number | null;
  model: number;               // shipped model, current service
  holdout: number | null;      // fitted before the holdout start: out of sample
  scenario: number | null;     // from `start` on
  band: [number, number] | null;
  event: string | null;
}

const YEAR_MS = 365.25 * 86_400_000;

export function timeline(planning: Planning, weekly: Weekly, market: string, lever: Lever,
                         options: { start: string; growthPct?: number }): WeekPoint[] {
  const m = weekly.markets[market];
  if (!m) return [];
  const delta: Record<string, number> = {};
  const margin = conformalBands(planning, simulate(planning, market, m.season[0], lever)).margin;
  for (const season of new Set(m.season)) delta[season] = simulate(planning, market, season, lever).delta_guests;
  const firstProjected = m.week[m.kind.indexOf("projected")];   // growth starts here, so the forecast has no step
  const anchor = Date.parse(firstProjected ?? weekly.last_actual_week);
  const growth = 1 + (options.growthPct ?? 0) / 100;
  return m.week.map((week, w) => {
    const base = m.structural[w] + m.residual[w];
    const years = m.kind[w] === "projected" ? Math.max(0, (Date.parse(week) - anchor) / YEAR_MS) : 0;
    const scale = growth ** years;
    const model = Math.max(0, base) * scale;
    const inScenario = week >= options.start;
    const scenario = inScenario ? Math.max(0, base + delta[m.season[w]]) * scale : null;
    const spread = inScenario ? margin * Math.max(0, m.structural[w] + delta[m.season[w]]) * scale : 0;
    return { week, kind: m.kind[w], actual: m.actual[w], model, holdout: m.holdout[w], scenario,
             band: scenario === null ? null : [Math.max(0, scenario - spread), scenario + spread], event: m.event?.[w] ?? null };
  });
}

/** Weighted MAPE (%) of the out-of-sample holdout predictions over weeks with actuals. */
export function holdoutWmape(points: Array<Pick<WeekPoint, "actual" | "holdout">>): number | null {
  let error = 0, total = 0;
  for (const p of points) if (p.actual !== null && p.holdout !== null) { error += Math.abs(p.actual - p.holdout); total += p.actual; }
  return total > 0 ? (100 * error) / total : null;
}

/** Out-of-sample weekly error (WMAPE, %) over every market's held-out weeks. */
export function overallHoldoutWmape(planning: Planning, weekly: Weekly): number | null {
  return holdoutWmape(Object.keys(weekly.markets).flatMap((m) => timeline(planning, weekly, m, NO_CHANGE, { start: "9999" })));
}

/** All markets summed: each market's timeline, with the changes on `selected` only. A total is
 *  real (actual, holdout) only when every market has it that week. */
export function totalTimeline(planning: Planning, weekly: Weekly, selected: string, lever: Lever,
                              options: { start: string; growthPct?: number }): WeekPoint[] {
  const all = Object.keys(weekly.markets).map((m) => timeline(planning, weekly, m, m === selected ? lever : NO_CHANGE, options));
  return all[0].map((first, w) => {
    const pick = (f: (p: WeekPoint) => number | null) => {
      let total = 0;
      for (const series of all) { const v = f(series[w]); if (v === null) return null; total += v; }
      return total;
    };
    const model = all.reduce((t, s) => t + s[w].model, 0);
    const changed = all.some((s) => s[w].scenario !== null);
    const scenario = changed ? all.reduce((t, s) => t + (s[w].scenario ?? s[w].model), 0) : null;
    const own = all.find((s) => s[w].band !== null && s[w].scenario !== null)?.[w];
    const spread = own && own.band ? (own.band[1] - own.band[0]) / 2 : 0;
    return { week: first.week, kind: first.kind, actual: pick((p) => p.actual), model, holdout: pick((p) => p.holdout), scenario,
             band: scenario === null ? null : [Math.max(0, scenario - spread), scenario + spread], event: null };
  });
}
