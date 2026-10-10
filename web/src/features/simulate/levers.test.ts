import { describe, expect, it } from "vitest";
import { activePreset, DEFAULT_INPUT, leverReducer, toLever } from "./levers";

describe("lever state", () => {
  it("presets, group resets and the matching preset agree", () => {
    const more = leverReducer(DEFAULT_INPUT, { type: "preset", id: "more_flights" });
    expect(activePreset(more)).toBe("more_flights");
    const tweaked = leverReducer(more, { type: "set", key: "p2pPts", value: 4 });
    expect(activePreset(tweaked)).toBeNull();
    const reset = leverReducer(leverReducer(tweaked, { type: "resetGroup", group: "flights" }), { type: "resetGroup", group: "visitors" });
    expect(reset).toEqual(DEFAULT_INPUT);
    expect(toLever(more)).toMatchObject({ delta_frequency: 2, aircraft_gauge: 290, delta_load_factor: 0.02 });
  });
});
