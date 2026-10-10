import { rangeInterval } from "./noise";
import type { Nowcast } from "./types";

/** |change| below this is reported as "no clear change": over 2-week ranges the size of a change
 *  is off by 3-4 pp (docs/model_design.md §4.8). */
export const DIRECTION_THRESHOLD = 0.08;

export type Direction = "up" | "down" | "no clear change";

export interface RangeSummary {
  guests: number;
  low: number;
  high: number;
  previousGuests: number | null;
  change: number | null;
  direction: Direction | null;
}

const DAY = 86_400_000;
const toTime = (date: string) => Date.parse(`${date}T00:00:00Z`);

/**
 * A range total with its interval, and its change against the same-length range just before it
 * (actual guests where they exist, predictions otherwise). `pred` may be a what-if replacement of
 * the series' predictions; the interval keeps the series' relative uncertainty.
 */
export function summariseRange(nowcast: Nowcast, name: string, startIndex: number, endIndex: number, z: number,
                               pred: number[] = nowcast.series[name].pred): RangeSummary {
  const series = nowcast.series[name];
  const days = pred.slice(startIndex, endIndex + 1);
  const [low, high] = rangeInterval(series.noise, series.horizon_days.slice(startIndex, endIndex + 1), days, z);
  const guests = days.reduce((sum, p) => sum + p, 0);
  const length = endIndex - startIndex + 1;
  const firstPrevious = toTime(series.date[startIndex]) - length * DAY;
  const known = new Map<number, number>();
  const history = nowcast.history[name];
  history?.date.forEach((d, i) => known.set(toTime(d), history.guests[i]));
  series.date.forEach((d, i) => known.set(toTime(d), pred[i]));
  let previous: number | null = 0;
  for (let i = 0; i < length; i += 1) {
    const value = known.get(firstPrevious + i * DAY);
    if (value === undefined) { previous = null; break; }
    previous += value;
  }
  const change = previous ? guests / previous - 1 : null;
  const direction: Direction | null = change === null ? null
    : Math.abs(change) < DIRECTION_THRESHOLD ? "no clear change" : change > 0 ? "up" : "down";
  return { guests, low, high, previousGuests: previous, change, direction };
}
