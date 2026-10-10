/**
 * Totals over a period of the moving map's weeks: the week being shown, its month or year, or
 * every week since a chosen date. Weeks belong to the month and year of their Monday.
 */
import type { Playback } from "./playback";

export type PeriodMode = "week" | "month" | "year" | "since";
export interface Period { from: number; to: number }   // inclusive week indices

export function periodAt(weeks: string[], w: number, mode: PeriodMode, sinceIndex = 0): Period {
  if (mode === "week") return { from: w, to: w };
  if (mode === "since") return { from: Math.min(sinceIndex, w), to: w };
  const key = mode === "month" ? weeks[w].slice(0, 7) : weeks[w].slice(0, 4);
  const keyOf = (week: string) => (mode === "month" ? week.slice(0, 7) : week.slice(0, 4));
  let from = w, to = w;
  while (from > 0 && keyOf(weeks[from - 1]) === key) from -= 1;
  while (to < weeks.length - 1 && keyOf(weeks[to + 1]) === key) to += 1;
  return { from, to };
}

export interface MarketTotal { market: string; visitors: number; visitorsBase: number }
export interface PeriodSummary {
  weeks: number;
  visitors: number;        // hotel check-ins
  visitorsBase: number;    // the same without the changes
  guests: number;          // hotel guest nights
  guestsBase: number;
  data: "real" | "forecast" | "mixed";
  byMarket: MarketTotal[]; // largest first
}

/** Sums over the period for `markets` (default: every market). */
export function summarise(pb: Playback, period: Period, requested: string[] = Object.keys(pb.markets)): PeriodSummary {
  const markets = requested.filter((m) => pb.markets[m]);   // markets without weekly history add nothing
  const sum = (xs: number[]) => xs.slice(period.from, period.to + 1).reduce((a, b) => a + b, 0);
  const byMarket = markets.map((market) => {
    const s = pb.markets[market];
    return { market, visitors: sum(s.checkIns), visitorsBase: sum(s.checkInsBase) };
  }).sort((a, b) => b.visitors - a.visitors);
  const guests = markets.reduce((t, m) => t + sum(pb.markets[m].guests), 0);
  const extra = markets.reduce((t, m) => t + sum(pb.markets[m].extra), 0);
  const kinds = new Set(pb.kind.slice(period.from, period.to + 1).map((k) => (k === "history" ? "real" : "forecast")));
  return {
    weeks: period.to - period.from + 1,
    visitors: byMarket.reduce((t, m) => t + m.visitors, 0),
    visitorsBase: byMarket.reduce((t, m) => t + m.visitorsBase, 0),
    guests, guestsBase: guests - extra,
    data: kinds.size > 1 ? "mixed" : (kinds.values().next().value as "real" | "forecast"),
    byMarket,
  };
}
