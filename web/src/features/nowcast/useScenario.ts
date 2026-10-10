import { useMemo } from "react";
import { dailyInterval } from "../../engine/noise";
import { summariseRange, type RangeSummary } from "../../engine/range";
import type { Bundle } from "../../engine/types";
import { whatIfGuests } from "../../engine/whatif";

export const AGGREGATES = ["TOTAL", "INTERNATIONAL"] as const;

export interface ScenarioInput {
  series: string;          // a market, INTERNATIONAL or TOTAL
  startIndex: number;      // first predicted day of the range
  length: number;          // days in the range
  coverage: string;        // "0.5" | "0.8" | "0.9"
  domestic: number;        // arrivals factor for DOMESTIC
  international: number;   // arrivals factor for every international market
  market: number;          // extra factor for the selected market (when `series` is one market)
}

export interface Scenario {
  dates: string[];
  pred: number[];
  whatIf: number[];
  band: Array<[number, number]>;
  predicted: RangeSummary;
  scenario: RangeSummary;
  changed: boolean;
  lastYear: Array<number | null>;
}

const DAY = 86_400_000;
const shiftYear = (date: string) => new Date(Date.parse(`${date}T00:00:00Z`) - 364 * DAY).toISOString().slice(0, 10);

/** Everything the dashboard shows for one set of slider values, computed from the bundle only. */
export function useScenario(bundle: Bundle, input: ScenarioInput): Scenario {
  return useMemo(() => {
    const { nowcast, whatif } = bundle;
    const z = nowcast.z[input.coverage];
    const factorFor = (market: string) =>
      (market === "DOMESTIC" ? input.domestic : input.international) * (market === input.series ? input.market : 1);
    const members = input.series === "TOTAL" ? Object.keys(whatif.markets)
      : input.series === "INTERNATIONAL" ? Object.keys(whatif.markets).filter((m) => m !== "DOMESTIC") : [input.series];
    const series = nowcast.series[input.series];
    const whatIf = new Array<number>(series.pred.length).fill(0);
    for (const market of members) {
      whatIfGuests(whatif.markets[market], factorFor(market)).forEach((g, t) => { whatIf[t] += g; });
    }
    const changed = members.some((m) => factorFor(m) !== 1);
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
      changed,
      lastYear: series.date.map((d) => actual.get(shiftYear(d)) ?? null),
    };
  }, [bundle, input]);
}
