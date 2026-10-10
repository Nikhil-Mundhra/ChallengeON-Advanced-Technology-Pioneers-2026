/**
 * Totals over a period of the moving map's weeks: the week being shown, its calendar month or
 * year, or every week since a chosen date. A week that crosses a month or year boundary counts
 * toward each by the share of its 7 days inside it (as insights.ts counts calendar days).
 */
import type { Playback } from "./playback";

export type PeriodMode = "week" | "month" | "year" | "since";
/** Week index -> share of that week inside the period (0..1). */
export interface Period { weights: Map<number, number>; first: string; last: string }

const DAY = 86_400_000;
const time = (iso: string) => Date.parse(`${iso}T00:00:00Z`);
const iso = (t: number) => new Date(t).toISOString().slice(0, 10);

/** Share of the week starting `monday` that falls in [start, end) (UTC ms). */
function overlap(monday: string, start: number, end: number): number {
  const a = time(monday), b = a + 7 * DAY;
  return Math.max(0, Math.min(b, end) - Math.max(a, start)) / (7 * DAY);
}

export function periodAt(weeks: string[], w: number, mode: PeriodMode, sinceIndex = 0): Period {
  const weights = new Map<number, number>();
  if (mode === "week" || mode === "since") {
    for (let i = mode === "week" ? w : Math.min(sinceIndex, w); i <= w; i += 1) weights.set(i, 1);
    return { weights, first: weeks[Math.min(...weights.keys())], last: iso(time(weeks[w]) + 6 * DAY) };
  }
  // The calendar month or year containing the middle of the shown week.
  const mid = new Date(time(weeks[w]) + 3 * DAY);
  const start = mode === "month" ? Date.UTC(mid.getUTCFullYear(), mid.getUTCMonth(), 1) : Date.UTC(mid.getUTCFullYear(), 0, 1);
  const end = mode === "month" ? Date.UTC(mid.getUTCFullYear(), mid.getUTCMonth() + 1, 1) : Date.UTC(mid.getUTCFullYear() + 1, 0, 1);
  weeks.forEach((monday, i) => { const share = overlap(monday, start, end); if (share > 0) weights.set(i, share); });
  return { weights, first: iso(start), last: iso(end - DAY) };
}

export interface MarketTotal { market: string; visitors: number; visitorsBase: number }
export interface PeriodSummary {
  weeks: number;           // weeks touching the period
  covered: boolean;        // the data reaches both ends of the period
  visitors: number;        // hotel check-ins
  visitorsBase: number;    // the same without the changes
  guests: number;          // hotel nights
  guestsBase: number;
  data: "real" | "forecast" | "mixed";
  byMarket: MarketTotal[]; // largest first
}

/** Weighted sums over the period for `requested` markets (default: every market). */
export function summarise(pb: Playback, period: Period, requested: string[] = Object.keys(pb.markets)): PeriodSummary {
  const markets = requested.filter((m) => pb.markets[m]);   // markets without weekly history add nothing
  const entries = [...period.weights.entries()];
  const sum = (xs: number[]) => entries.reduce((t, [i, share]) => t + xs[i] * share, 0);
  const byMarket = markets.map((market) => {
    const s = pb.markets[market];
    return { market, visitors: sum(s.checkIns), visitorsBase: sum(s.checkInsBase) };
  }).sort((a, b) => b.visitors - a.visitors);
  const guests = markets.reduce((t, m) => t + sum(pb.markets[m].guests), 0);
  const extra = markets.reduce((t, m) => t + sum(pb.markets[m].extra), 0);
  const kinds = new Set(entries.map(([i]) => (pb.kind[i] === "history" ? "real" : "forecast")));
  const covered = time(pb.weeks[0]) <= time(period.first) && time(pb.weeks[pb.weeks.length - 1]) + 6 * DAY >= time(period.last);
  return {
    weeks: entries.length, covered,
    visitors: byMarket.reduce((t, m) => t + m.visitors, 0),
    visitorsBase: byMarket.reduce((t, m) => t + m.visitorsBase, 0),
    guests, guestsBase: guests - extra,
    data: kinds.size > 1 ? "mixed" : (kinds.values().next().value as "real" | "forecast"),
    byMarket,
  };
}
