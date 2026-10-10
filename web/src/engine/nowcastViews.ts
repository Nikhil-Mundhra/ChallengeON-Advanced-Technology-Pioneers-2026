/**
 * Everything the nowcast page shows, as pure functions of the bundle: the forecast and the version
 * with changed check-ins for one market or total, totals over a range of days, bars against last
 * year, and nationality shares.
 */
import { dailyInterval } from "./noise";
import { summariseRange, type RangeSummary } from "./range";
import type { Bundle, Nowcast } from "./types";
import { whatIfGuests } from "./whatif";

export const AGGREGATES = ["TOTAL", "INTERNATIONAL"] as const;

export interface NowcastInput {
  series: string;          // a market, INTERNATIONAL or TOTAL
  startIndex: number;      // first forecast day of the range
  length: number;          // days in the range
  domestic: number;        // check-in factor for DOMESTIC
  international: number;   // check-in factor for every international market
  market: number;          // extra factor for the selected market (when `series` is one market)
}

export interface NowcastView {
  dates: string[];
  pred: number[];
  whatIf: number[];
  band: Array<[number, number]>;
  predicted: RangeSummary;
  scenario: RangeSummary;
  changed: boolean;
  lastYear: Array<number | null>;
  window: { from: number; to: number };
}

const DAY = 86_400_000;
const shiftYear = (date: string) => new Date(Date.parse(`${date}T00:00:00Z`) - 364 * DAY).toISOString().slice(0, 10);

/** z for the bundle's published coverage. */
export const zFor = (bundle: Bundle) => bundle.nowcast.z[String(bundle.manifest.coverage)];

export function nowcastView(bundle: Bundle, input: NowcastInput): NowcastView {
  const { nowcast, whatif } = bundle;
  const z = zFor(bundle);
  const factorFor = (market: string) =>
    (market === "DOMESTIC" ? input.domestic : input.international) * (market === input.series ? input.market : 1);
  const members = input.series === "TOTAL" ? Object.keys(whatif.markets)
    : input.series === "INTERNATIONAL" ? Object.keys(whatif.markets).filter((m) => m !== "DOMESTIC") : [input.series];
  const series = nowcast.series[input.series];
  const whatIf = new Array<number>(series.pred.length).fill(0);
  for (const market of members) whatIfGuests(whatif.markets[market], factorFor(market)).forEach((g, t) => { whatIf[t] += g; });
  const end = Math.min(input.startIndex + input.length, series.pred.length) - 1;
  const history = nowcast.history[input.series];
  const actual = new Map(history?.date.map((d, i) => [d, history.guests[i]]));
  return {
    dates: series.date,
    pred: series.pred,
    whatIf,
    band: series.pred.map((p, t) => dailyInterval(series.noise, series.horizon_days[t], p, z)),
    predicted: summariseRange(nowcast, input.series, input.startIndex, end, z),
    scenario: summariseRange(nowcast, input.series, input.startIndex, end, z, whatIf),
    changed: members.some((m) => factorFor(m) !== 1),
    lastYear: series.date.map((d) => actual.get(shiftYear(d)) ?? null),
    window: { from: input.startIndex, to: end },
  };
}

export interface BarBucket { label: string; current: number; comparison: number | null }

/** Day or week totals over the view's window, each next to the same days last year (null when any is unknown). */
export function bucketBars(view: NowcastView, grain: "day" | "week"): BarBucket[] {
  const step = grain === "week" ? 7 : 1;
  const values = view.changed ? view.whatIf : view.pred;
  const buckets: BarBucket[] = [];
  for (let i = view.window.from; i <= view.window.to; i += step) {
    let current = 0; let comparison: number | null = 0;
    for (let t = i; t <= Math.min(i + step - 1, view.window.to); t += 1) {
      current += values[t];
      const last = view.lastYear[t];
      comparison = comparison === null || last === null ? null : comparison + last;
    }
    buckets.push({ label: view.dates[i].slice(5), current, comparison });
  }
  return buckets;
}

/** Change against last year over the buckets that have a comparison; null when none do. */
export function changeVsLastYear(buckets: BarBucket[]): number | null {
  const known = buckets.filter((b) => b.comparison !== null);
  const now = known.reduce((s, b) => s + b.current, 0);
  const then = known.reduce((s, b) => s + (b.comparison ?? 0), 0);
  return then ? now / then - 1 : null;
}

/** Half-width of a range total's likely range, as a share of the total. */
export const rangeError = (summary: RangeSummary) => (summary.guests > 0 ? (summary.high - summary.low) / 2 / summary.guests : 0);

export interface NationalityTotal { name: string; guests: number; share: number }

/** International nationalities by forecast guests over [start, end], with their share of all of them. */
export function nationalityTotals(nowcast: Nowcast, start: string, end: string): NationalityTotal[] {
  const totals = Object.entries(nowcast.nationalities).map(([name, values]) => {
    let guests = 0;
    values.date.forEach((d, i) => { if (d >= start && d <= end) guests += values.pred[i]; });
    return { name, guests };
  });
  const all = totals.reduce((sum, row) => sum + row.guests, 0);
  return totals.map((row) => ({ ...row, share: all ? row.guests / all : 0 })).sort((a, b) => b.guests - a.guests);
}
