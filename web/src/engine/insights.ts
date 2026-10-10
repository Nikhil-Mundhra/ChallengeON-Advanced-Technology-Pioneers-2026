/**
 * Plain statements for the landing page, computed from the nowcast bundle: each forecast month
 * against the same month a year earlier (actual guests), with the forecast's own error for that
 * month (NoiseModel.range_interval at the bundle's coverage). A change counts as up or down only
 * when it is larger than that error; otherwise the month is "about the same".
 */
import { rangeInterval } from "./noise";
import type { Nowcast } from "./types";

export type Trend = "up" | "down" | "same";

export interface MonthOutlook {
  month: string;            // YYYY-MM
  guests: number;           // forecast guest nights in the month
  lastYear: number | null;  // actual guest nights, same month a year earlier (full month only)
  change: number | null;    // guests / lastYear - 1
  error: number;            // half-width of the forecast range, as a share of guests
  trend: Trend | null;
}

export interface MarketMove { market: string; guests: number; lastYear: number; change: number }

function monthTotals(dates: string[], values: number[]) {
  const totals = new Map<string, { sum: number; days: number; idx: number[] }>();
  dates.forEach((d, i) => {
    const key = d.slice(0, 7);
    const row = totals.get(key) ?? { sum: 0, days: 0, idx: [] };
    row.sum += values[i]; row.days += 1; row.idx.push(i);
    totals.set(key, row);
  });
  return totals;
}

const daysInMonth = (month: string) => new Date(Date.UTC(Number(month.slice(0, 4)), Number(month.slice(5, 7)), 0)).getUTCDate();
const yearBefore = (month: string) => `${Number(month.slice(0, 4)) - 1}${month.slice(4)}`;

export function monthlyOutlook(nowcast: Nowcast, name: string, coverage: number): MonthOutlook[] {
  const series = nowcast.series[name];
  const history = nowcast.history[name];
  const z = nowcast.z[String(coverage)];
  const forecast = monthTotals(series.date, series.pred);
  const past = history ? monthTotals(history.date, history.guests) : new Map();
  return [...forecast.entries()].filter(([month, row]) => row.days === daysInMonth(month)).map(([month, row]) => {
    const [low, high] = rangeInterval(series.noise, row.idx.map((i) => series.horizon_days[i]), row.idx.map((i) => series.pred[i]), z);
    const error = (high - low) / 2 / row.sum;
    const before = past.get(yearBefore(month));
    const lastYear = before && before.days === daysInMonth(yearBefore(month)) ? before.sum : null;
    const change = lastYear ? row.sum / lastYear - 1 : null;
    const trend: Trend | null = change === null ? null : Math.abs(change) <= error ? "same" : change > 0 ? "up" : "down";
    return { month, guests: row.sum, lastYear, change, error, trend };
  });
}

/** Markets ranked by forecast change against the same months a year earlier (full months only). */
export function marketMoves(nowcast: Nowcast, coverage: number, exclude: string[] = ["TOTAL", "INTERNATIONAL"]): MarketMove[] {
  return Object.keys(nowcast.series).filter((m) => !exclude.includes(m)).map((market) => {
    let guests = 0, lastYear = 0;
    for (const o of monthlyOutlook(nowcast, market, coverage)) if (o.lastYear !== null) { guests += o.guests; lastYear += o.lastYear; }
    return { market, guests, lastYear, change: lastYear > 0 ? guests / lastYear - 1 : 0 };
  }).filter((m) => m.lastYear > 0).sort((a, b) => b.change - a.change);
}

/** The forecast month with the most guest nights. */
export function busiestMonth(outlook: MonthOutlook[]): MonthOutlook | null {
  return outlook.reduce<MonthOutlook | null>((best, o) => (best === null || o.guests > best.guests ? o : best), null);
}

/** The month to lead with: the largest change beyond its error for `name`; else the busiest month. */
export function headlineMonth(outlook: MonthOutlook[]): MonthOutlook | null {
  const clear = outlook.filter((o) => o.trend === "up" || o.trend === "down");
  if (!clear.length) return busiestMonth(outlook);
  return clear.reduce((best, o) => (Math.abs(o.change!) > Math.abs(best.change!) ? o : best));
}
