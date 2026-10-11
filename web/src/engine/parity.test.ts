/** The TS engine must reproduce the Python model: golden cases are computed by `twin export`
 *  (export/bundle.golden_part) through the fitted model and NoiseModel. */
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { rangeInterval } from "./noise";
import { DIRECTION_THRESHOLD, summariseRange } from "./range";
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

  it("summarises range direction respecting DIRECTION_THRESHOLD (8%)", () => {
    const summary = summariseRange(nowcast, "TOTAL", 0, 27, nowcast.z[String(manifest.coverage)]);
    expect(summary.guests).toBeGreaterThan(0);
    expect(summary.low).toBeLessThanOrEqual(summary.guests);
    expect(summary.high).toBeGreaterThanOrEqual(summary.guests);
    if (summary.change !== null) {
      if (Math.abs(summary.change) < DIRECTION_THRESHOLD) {
        expect(summary.direction).toBe("no clear change");
      } else {
        expect(["up", "down"]).toContain(summary.direction);
      }
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

  it("reproduces the published 30-week holdout WMAPE (docs/results/planning-holdout.md: 20.62%)", () => {
    const points = Object.keys(weekly.markets).flatMap((m) => timeline(planning, weekly, m, NO_CHANGE, { start: "9999" }));
    expect(holdoutWmape(points)).toBeCloseTo(20.62, 2);
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

describe("moving map", () => {
  it("guests match the timeline, check-ins rebuild guests, and in minus out equals the change in guests staying", async () => {
    const { playback, frameAt } = await import("./playback");
    const { paramsFor } = await import("./planning");
    const weekly = read<Weekly>(manifest.files.weekly);
    const planning = read<Planning>(manifest.files.planning);
    const lever = { ...NO_CHANGE, delta_frequency: 2, aircraft_gauge: 290 };
    const start = weekly.last_actual_week;
    const pb = playback(planning, weekly, "UNITED KINGDOM", lever, { start });
    const uk = pb.markets["UNITED KINGDOM"];
    const points = timeline(planning, weekly, "UNITED KINGDOM", lever, { start });
    points.forEach((p, w) => expect(uk.guests[w]).toBeCloseTo(p.actual ?? p.scenario ?? p.model, 6));
    const season = weekly.markets["UNITED KINGDOM"].season;
    uk.checkIns.forEach((c, w) => expect(c * paramsFor(planning, "UNITED KINGDOM", season[w]).baseline_los).toBeCloseTo(uk.guests[w], 6));
    for (let w = 1; w < uk.guests.length; w += 1) {
      if (uk.checkOuts[w] > 0) expect(uk.checkIns[w] - uk.checkOuts[w]).toBeCloseTo((uk.guests[w] - uk.guests[w - 1]) / 7, 6);
    }
    points.forEach((p, w) => { if (p.actual !== null) expect(uk.extra[w]).toBe(0); });   // changes never alter real weeks
    const last = frameAt(pb, pb.weeks.length - 1, "UNITED KINGDOM");
    expect(last.extraSoFar).toBeGreaterThan(0);
    expect(last.topArrivals).toHaveLength(3);
  });
});

describe("period totals", () => {
  it("week, month and since periods add up, and all-market totals match the sum of markets", async () => {
    const { playback } = await import("./playback");
    const { periodAt, summarise } = await import("./periods");
    const { totalTimeline } = await import("./weekly");
    const weekly = read<Weekly>(manifest.files.weekly);
    const planning = read<Planning>(manifest.files.planning);
    const opts = { start: weekly.last_actual_week };
    const pb = playback(planning, weekly, "ALL", NO_CHANGE, opts);
    const w = pb.weeks.indexOf("2025-12-01");
    const month = periodAt(pb.weeks, w, "month");
    expect([...month.weights.values()].reduce((a, b) => a + b, 0) * 7).toBeCloseTo(31, 9);   // December: 31 days of weeks
    expect(month.first).toBe("2025-12-01");
    const weekSum = summarise(pb, periodAt(pb.weeks, w, "week"));
    expect(weekSum.guests).toBeCloseTo(pb.total[w], 6);
    expect(weekSum.visitorsBase).toBeCloseTo(weekSum.visitors, 6);   // no changes
    expect(summarise(pb, periodAt(pb.weeks, w, "week"), ["ARMENIA"]).visitors).toBe(0);   // no weekly history: nothing, not a crash
    const since = summarise(pb, periodAt(pb.weeks, w, "since", w - 3));
    expect(since.weeks).toBe(4);
    expect(summarise(pb, periodAt(pb.weeks, w, "since", w + 5)).weeks).toBe(0);   // the map is before the start date
    const totals = totalTimeline(planning, weekly, "ALL", NO_CHANGE, opts);
    totals.forEach((p, i) => expect(p.model).toBeCloseTo(Object.keys(weekly.markets).reduce((t, m) => t + timeline(planning, weekly, m, NO_CHANGE, opts)[i].model, 0), 6));
  });
});

describe("five questions", () => {
  it("answers come from the simulator and the weekly forecast, and season shares are proper shares", async () => {
    const { answerQuestions, seasonMix } = await import("./questions");
    const weekly = read<Weekly>(manifest.files.weekly);
    const planning = read<Planning>(manifest.files.planning);
    const a = answerQuestions(planning, weekly);
    expect(a.frequency.perWeek).toBeCloseTo(simulate(planning, "UNITED KINGDOM", "Winter_Peak", a.frequency.lever).delta_guests, 6);
    expect(a.frequency.perYear).toBeGreaterThan(0);
    expect(a.newRoute.perYear).toBeNull();            // no weekly history for a new route
    expect(a.newRoute.perWeek).toBeGreaterThan(0);
    const all = seasonMix(planning, "Winter_Peak", 99).top.reduce((t, r) => t + r.share, 0);
    expect(all).toBeCloseTo(1, 9);
  });
});

describe("growth assumption", () => {
  it("starts at the first projected week without a step", () => {
    const weekly = read<Weekly>(manifest.files.weekly);
    const planning = read<Planning>(manifest.files.planning);
    const flat = timeline(planning, weekly, "UNITED KINGDOM", NO_CHANGE, { start: "9999", growthPct: 0 });
    const grown = timeline(planning, weekly, "UNITED KINGDOM", NO_CHANGE, { start: "9999", growthPct: 10 });
    const i = flat.findIndex((p) => p.kind === "projected");
    expect(grown[i].model).toBeCloseTo(flat[i].model, 9);
    expect(grown[i + 52].model / flat[i + 52].model).toBeCloseTo(1.1, 2);
  });
});
