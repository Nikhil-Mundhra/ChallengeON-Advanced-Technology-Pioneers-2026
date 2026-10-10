/**
 * Week-by-week frames for the moving map. For every market and week:
 *   guests     weekly hotel guests (guest nights): real where known, otherwise the model, with the
 *              changes applied to the selected market from `start` on (engine/weekly.timeline)
 *   checkIns   guests / guests-per-arrival factor for the week's season: the planning chain's own
 *              arrivals, so check-ins x factor = guests
 *   checkOuts  check-ins minus the change in guests staying (guests / 7 per night) since last week:
 *              people who arrived but are no longer counted must have left (an accounting identity,
 *              no stay-length assumption)
 */
import { NO_CHANGE, paramsFor, type Lever, type Planning } from "./planning";
import { timeline, type Weekly } from "./weekly";

export interface MarketSeries { guests: number[]; checkIns: number[]; checkOuts: number[]; extra: number[]; checkInsBase: number[] }
export interface Playback {
  weeks: string[];
  kind: Array<"history" | "scheduled" | "projected">;
  markets: Record<string, MarketSeries>;
  total: number[];            // all markets' guests per week
  events: Array<Array<{ code: string; markets: string[] }>>;  // events covering each week, with the markets they touch
}

export function playback(planning: Planning, weekly: Weekly, selected: string, lever: Lever,
                         options: { start: string; growthPct?: number }): Playback {
  const names = Object.keys(weekly.markets);
  const first = weekly.markets[names[0]];
  const markets: Record<string, MarketSeries> = {};
  for (const m of names) {
    const points = timeline(planning, weekly, m, m === selected ? lever : NO_CHANGE, options);
    const season = weekly.markets[m].season;
    const guests = points.map((p) => p.actual ?? p.scenario ?? p.model);
    const checkIns = guests.map((g, w) => g / paramsFor(planning, m, season[w]).baseline_los);
    const checkOuts = checkIns.map((c, w) => (w === 0 ? c : Math.max(0, c - (guests[w] - guests[w - 1]) / 7)));
    const extra = points.map((p) => (p.actual !== null || p.scenario === null ? 0 : p.scenario - p.model));  // real weeks stay real
    const checkInsBase = guests.map((g, w) => (g - extra[w]) / paramsFor(planning, m, season[w]).baseline_los);
    markets[m] = { guests, checkIns, checkOuts, extra, checkInsBase };
  }
  const total = first.week.map((_, w) => names.reduce((s, m) => s + markets[m].guests[w], 0));
  const events = first.week.map((_, w) => {
    const byCode = new Map<string, string[]>();
    for (const m of names) { const code = weekly.markets[m].event?.[w]; if (code) byCode.set(code, [...(byCode.get(code) ?? []), m]); }
    return [...byCode.entries()].map(([code, markets]) => ({ code, markets }));
  });
  return { weeks: first.week, kind: first.kind, markets, total, events };
}

export interface Frame {
  week: string;
  kind: Playback["kind"][number];
  total: number;
  vsLastYear: number | null;      // change against the same week 52 weeks earlier
  topArrivals: Array<{ market: string; checkIns: number }>;
  extraSoFar: number;             // guests added by the changes, from their start to this week
  events: Playback["events"][number];
}

export function frameAt(pb: Playback, w: number, selected: string): Frame {
  const total = pb.total[w];
  const before = w >= 52 ? pb.total[w - 52] : null;
  const topArrivals = Object.entries(pb.markets).filter(([m]) => m !== "DOMESTIC")
    .map(([market, s]) => ({ market, checkIns: s.checkIns[w] })).sort((a, b) => b.checkIns - a.checkIns).slice(0, 3);
  const extra = pb.markets[selected]?.extra ?? [];
  let extraSoFar = 0;
  for (let i = 0; i <= w; i += 1) extraSoFar += extra[i] ?? 0;
  return { week: pb.weeks[w], kind: pb.kind[w], events: pb.events[w], total, vsLastYear: before ? total / before - 1 : null, topArrivals, extraSoFar };
}
