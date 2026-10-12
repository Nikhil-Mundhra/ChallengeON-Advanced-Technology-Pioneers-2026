import { describe, expect, it } from "vitest";
import { bandFor, comingRows, horizonMonths, leadRow, outlookRows, rawProjection, scenarioOf } from "./outlook";
import type { Outlook } from "./types";

/** A hand-made outlook in the schema 3 shape. Like the real flat projection, it under-forecast in
 *  every back-test, so the band sits entirely above 0. Real-bundle parity is in parity.test.ts. */
const outlook: Outlook = {
  data_end: "2026-02-28",
  coverage: 0.8,
  scenarios: {
    flat: {
      TOTAL: [
        { month: "2026-10", guests: 1_000, calibrated: 1_100, previous: 900, previous_kind: "estimate", horizon_months: 8 },
        { month: "2026-11", guests: 1_000, calibrated: 1_120, previous: 1_000, previous_kind: "actual", horizon_months: 9 },
        { month: "2026-12", guests: 1_000, calibrated: 1_120, previous: 1_100, previous_kind: "actual" },
        { month: "2027-01", guests: 1_000, calibrated: null, previous: 900, previous_kind: "actual" },
      ],
      DOMESTIC: [{ month: "2026-11", guests: 400, calibrated: 380, previous: 450, previous_kind: "actual" }],
    },
    trend: { TOTAL: [{ month: "2026-11", guests: 1_200, calibrated: 1_150, previous: 1_000, previous_kind: "actual" }] },
  },
  band: [{ horizon_months: 6, low: 0.03, high: 0.15, mid: 0.08 }, { horizon_months: 9, low: 0.059, high: 0.198, mid: 0.12 }],
  bands: { flat: { DOMESTIC: [{ horizon_months: 9, low: -0.1, high: -0.02, mid: -0.05 }] } },
};

describe("outlook", () => {
  it("counts months from the end of the data and picks the band at or after that distance", () => {
    expect(horizonMonths("2026-02-28", "2026-11")).toBe(9);
    expect(bandFor(outlook.band, 9)?.high).toBe(0.198);
    expect(bandFor(outlook.band, 3)?.horizon_months).toBe(6);
    expect(bandFor(outlook.band, 12)?.horizon_months).toBe(9);
    expect(bandFor([], 9)).toBeNull();
    expect(bandFor(undefined, 9)).toBeNull();
  });

  it("leads with the flat scenario unless the bundle names another", () => {
    expect(scenarioOf(outlook)).toBe("flat");
    expect(scenarioOf({ ...outlook, default_scenario: "trend" })).toBe("trend");
    expect(scenarioOf({ ...outlook, default_scenario: "missing" })).toBe("flat");
  });

  it("shows the calibrated figure with a range that can lie wholly above the raw projection", () => {
    const nov = outlookRows(outlook, "TOTAL").find((r) => r.month === "2026-11")!;
    expect(nov.guests).toBe(1_120);
    expect(nov.raw).toBe(1_000);
    expect(nov.calibrated).toBe(true);
    expect(nov.low).toBeCloseTo(1_059, 9);
    expect(nov.high).toBeCloseTo(1_198, 9);
    expect(nov.low!).toBeGreaterThan(nov.raw);
    expect(nov.change).toBeCloseTo(0.12, 12);
    expect(nov.trend).toBe("up");      // last year's 1,000 is below the range
  });

  it("calls a month the same when last year's figure lies inside the range", () => {
    expect(outlookRows(outlook, "TOTAL").find((r) => r.month === "2026-12")!.trend).toBe("same");
  });

  it("falls back to the raw projection with no range when there is no calibrated figure", () => {
    const jan = outlookRows(outlook, "TOTAL").find((r) => r.month === "2027-01")!;
    expect(jan.guests).toBe(1_000);
    expect(jan.calibrated).toBe(false);
    expect([jan.low, jan.high, jan.band, jan.trend]).toEqual([null, null, null, null]);
    expect(jan.change).toBeCloseTo(1_000 / 900 - 1, 12);
  });

  it("uses each segment's own bands, and none where a segment has none", () => {
    const dom = outlookRows(outlook, "DOMESTIC")[0];
    expect(dom.low).toBeCloseTo(360, 9);
    expect(dom.high).toBeCloseTo(392, 9);
    expect(dom.trend).toBe("down");
    const trend = outlookRows(outlook, "TOTAL", "trend")[0];
    expect(trend.band).toBeNull();        // the top-level band belongs to the default scenario only
    expect(outlookRows(outlook, "INTERNATIONAL")).toEqual([]);
  });

  it("gives a segment's uncorrected projection as plain numbers, with no change or trend", () => {
    const rows = rawProjection(outlook, "DOMESTIC");
    expect(rows).toEqual([{ month: "2026-11", guests: 400 }]);
    expect(Object.keys(rows[0]).sort()).toEqual(["guests", "month"]);
    expect(rawProjection(outlook, "INTERNATIONAL")).toEqual([]);
    expect(rawProjection(outlook, "TOTAL", "trend")[0].guests).toBe(1_200);
  });

  it("leads with the month after today's and keeps the months after it", () => {
    const rows = outlookRows(outlook, "TOTAL");
    expect(leadRow(rows, "2026-10-12")?.month).toBe("2026-11");
    expect(comingRows(rows, "2026-10-12").map((r) => r.month)).toEqual(["2026-11", "2026-12", "2027-01"]);
    expect(leadRow(rows, "2027-06-01")?.month).toBe("2027-01");
    expect(leadRow([], "2026-10-12")).toBeNull();
  });
});
