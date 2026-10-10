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

  it("handles cold start market naming correctly", async () => {
    const mockPlanning = {
      calibration: { "UNITED KINGDOM": {} as any },
      archetypes: { country: { "UNITED KINGDOM": "Major Hub", "ARMENIA": "Highly Seasonal" } } as any,
    } as any;
    const { marketOptions } = await import("./levers");
    const options = marketOptions(mockPlanning);
    expect(options).toEqual([
      { value: "UNITED KINGDOM", label: "UNITED KINGDOM" },
      { value: "ARMENIA", label: "ARMENIA (estimated from similar markets)" },
    ]);
  });
});

describe("slider availability", () => {
  it("matches each market: all markets locks levers, residents have no flights, aircraft size needs extra flights", async () => {
    const { ALL_MARKETS, DEFAULT_INPUT, presetAvailable, sliderAvailability } = await import("./levers");
    expect(sliderAvailability(ALL_MARKETS, DEFAULT_INPUT, "multiplierPct").disabled).toBe(true);
    expect(sliderAvailability("DOMESTIC", DEFAULT_INPUT, "frequency").disabled).toBe(true);
    expect(sliderAvailability("DOMESTIC", DEFAULT_INPUT, "p2pPts").disabled).toBe(true);
    expect(sliderAvailability("DOMESTIC", DEFAULT_INPUT, "multiplierPct").disabled).toBe(false);
    expect(sliderAvailability("UNITED KINGDOM", DEFAULT_INPUT, "gauge").disabled).toBe(true);
    expect(sliderAvailability("UNITED KINGDOM", { ...DEFAULT_INPUT, frequency: 2 }, "gauge").disabled).toBe(false);
    expect(presetAvailable("DOMESTIC", "more_flights")).toBe(false);
    expect(presetAvailable(ALL_MARKETS, "stopover")).toBe(false);
  });
});
