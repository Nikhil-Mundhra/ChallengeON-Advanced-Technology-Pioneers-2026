import { describe, expect, it } from "vitest";
import { advance, jumpTo, lifetimeMs, MAX_CARDS, tick } from "./eventCards";

const wk = (week: string, ...codes: string[]) => ({ week, events: codes.map((code) => ({ code, markets: ["UNITED KINGDOM"] })) });

describe("event card stack", () => {
  it("puts new events on top, extends a continuing one, and caps the stack", () => {
    let s = advance([], wk("2025-03-03", "ramadan"), 1);
    s = advance(s, wk("2025-03-10", "ramadan"), 1);
    expect(s).toHaveLength(1);
    expect(s[0]).toMatchObject({ firstWeek: "2025-03-03", lastWeek: "2025-03-10" });
    s = advance(s, wk("2025-03-31", "eid_al_fitr"), 1);
    expect(s.map((c) => c.code)).toEqual(["eid_al_fitr", "ramadan"]);
    for (const code of ["a", "b", "c", "d"]) s = advance(s, wk("2025-04-07", code), 1);
    expect(s).toHaveLength(MAX_CARDS);
  });
  it("fades faster at 4x, freezes while paused, and a jump shows only the landed week", () => {
    expect(lifetimeMs(4)).toBeLessThan(lifetimeMs(1));
    const s = advance([], wk("2025-03-03", "ramadan"), 4);
    expect(tick(s, 10_000, false)).toEqual(s);
    expect(tick(s, lifetimeMs(4) + 1, true)).toHaveLength(0);
    expect(jumpTo(wk("2025-06-02", "eid_al_adha"), 1).map((c) => c.code)).toEqual(["eid_al_adha"]);
  });
});
