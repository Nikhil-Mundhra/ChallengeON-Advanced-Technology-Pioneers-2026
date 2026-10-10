/** The TS engine must reproduce the Python model: golden cases are computed by `twin export`
 *  (export/bundle.golden_part) through the fitted model and NoiseModel. */
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { rangeInterval } from "./noise";
import type { Manifest, Nowcast, WhatIf } from "./types";
import { whatIfGuests } from "./whatif";
import { conformalBands, hybrid, NO_CHANGE, simulate, tornado, type Planning } from "./planning";
import { holdoutWmape, timeline, type Weekly } from "./weekly";

const DATA = join(__dirname, "../../public/data");
const read = <T>(path: string): T => JSON.parse(readFileSync(join(DATA, path), "utf-8")) as T;
const manifest = read<Manifest>("manifest.json");
const nowcast = read<Nowcast>(manifest.files.nowcast);
const whatif = read<WhatIf>(manifest.files.whatif);
const golden = read<{ cases: Array<Record<string, unknown>> }>(manifest.files.golden).cases;

const relative = (a: number, b: number) => Math.abs(a / b - 1);

describe("what-if guests", () => {
  it("reproduces every market's prediction with unchanged arrivals", () => {
    for (const [name, market] of Object.entries(whatif.markets)) {
      const guests = whatIfGuests(market);
      nowcast.series[name].pred.forEach((p, t) => expect(relative(guests[t], p)).toBeLessThan(1e-9));
    }
  });

  it("matches the fitted model for changed arrivals", () => {
    const cases = golden.filter((c) => c.kind === "whatif");
    expect(cases.length).toBeGreaterThan(0);
    for (const c of cases) {
      const guests = whatIfGuests(whatif.markets[c.market as string], c.arrivals_factor as number);
      (c.guests as number[]).forEach((g, t) => expect(relative(guests[t], g)).toBeLessThan(1e-6));
    }
  });
});

describe("range intervals", () => {
  it("match NoiseModel.range_interval", () => {
    const cases = golden.filter((c) => c.kind === "range");
    expect(cases.length).toBeGreaterThan(0);
    for (const c of cases) {
      const series = nowcast.series[c.series as string];
      const start = series.date.indexOf(c.start as string);
      const end = start + (c.days as number);
      const [low, high] = rangeInterval(series.noise, series.horizon_days.slice(start, end), series.pred.slice(start, end),
                                        nowcast.z[String(c.coverage)]);
      expect(relative(low, c.p_low as number)).toBeLessThan(1e-6);
      expect(relative(high, c.p_high as number)).toBeLessThan(1e-6);
    }
  });
});


const planning = read<Planning>(manifest.files.planning);

describe("planning simulator", () => {
  const close = (a: number, b: number) => expect(Math.abs(a - b)).toBeLessThanOrEqual(1e-9 * Math.max(1, Math.abs(b)));

  it("reproduces the conversion chain, waterfall, hybrid and conformal bands", () => {
    const cases = golden.filter((c) => c.kind === "scenario");
    expect(cases.length).toBeGreaterThan(0);
    for (const c of cases) {
      const lever = { ...NO_CHANGE, ...(c.levers as object) };
      const result = simulate(planning, c.market as string, c.season as string, lever);
      const expected = c.result as Record<string, number>;
      close(result.base.guests, expected.base_guests); close(result.sim.guests, expected.sim_guests);
      close(result.sim.seats, expected.sim_seats); close(result.sim.arrivals, expected.sim_arrivals);
      close(result.waterfall.seats, expected.waterfall_seats); close(result.waterfall.lf, expected.waterfall_lf);
      close(result.waterfall.p2p, expected.waterfall_p2p); close(result.waterfall.multiplier, expected.waterfall_multiplier);
      close(result.waterfall.los, expected.waterfall_los);
      close(hybrid(planning, result).sim, c.hybrid_sim as number);
      const bands = conformalBands(planning, result);
      close(bands.p10, c.p10 as number); close(bands.p90, c.p90 as number);
      close(bands.deltaP10, c.delta_p10 as number); close(bands.deltaP90, c.delta_p90 as number);
    }
  });

  it("ranks the tornado levers like Python", () => {
    const cases = golden.filter((c) => c.kind === "tornado");
    expect(cases.length).toBeGreaterThan(0);
    for (const c of cases) {
      const rows = tornado(planning, c.market as string, c.season as string, { ...NO_CHANGE, ...(c.base_lever as object) });
      const expected = c.rows as Array<{ lever_name: string; swing_spread: number }>;
      expect(rows.map((r) => r.lever_name)).toEqual(expected.map((r) => r.lever_name));
      rows.forEach((r, i) => close(r.swing_spread, expected[i].swing_spread));
    }
  });
});

describe("weekly timeline", () => {
  const weekly = read<Weekly>(manifest.files.weekly);
  const planning = read<Planning>(manifest.files.planning);

  it("reproduces the published 30-week holdout WMAPE (README §3.2: 21.74%)", () => {
    const points = Object.keys(weekly.markets).flatMap((m) => timeline(planning, weekly, m, NO_CHANGE, { start: "9999" }));
    expect(holdoutWmape(points)).toBeCloseTo(21.74, 2);
  });

  it("moves each week by the simulator's change for its season, from the start week on", () => {
    const lever = { ...NO_CHANGE, delta_frequency: 3, aircraft_gauge: 300 };
    const start = weekly.last_actual_week;
    const points = timeline(planning, weekly, "UNITED KINGDOM", lever, { start });
    const m = weekly.markets["UNITED KINGDOM"];
    points.forEach((p, w) => {
      if (p.week < start) expect(p.scenario).toBeNull();
      else expect(p.scenario).toBeCloseTo(Math.max(0, m.structural[w] + m.residual[w] + simulate(planning, "UNITED KINGDOM", m.season[w], lever).delta_guests), 6);
    });
  });
});

describe("landing page statements", () => {
  it("monthly totals and year-earlier comparisons add up from the bundle", async () => {
    const { monthlyOutlook } = await import("./insights");
    const months = monthlyOutlook(nowcast, "TOTAL", manifest.coverage);
    const december = months.find((m) => m.month.endsWith("-12"))!;
    const series = nowcast.series.TOTAL;
    const sum = series.date.reduce((s, d, i) => (d.slice(0, 7) === december.month ? s + series.pred[i] : s), 0);
    expect(december.guests).toBeCloseTo(sum, 6);
    for (const m of months) if (m.trend === "same") expect(Math.abs(m.change!)).toBeLessThanOrEqual(m.error);
  });
});
