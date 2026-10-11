import { describe, expect, it } from "vitest";
import { activePreset, DEFAULT_INPUT, fromLever, leverReducer, scenarioFromQuery, scenarioQuery, startOptions, toLever } from "./levers";

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

describe("scenario links", () => {
  const known = { markets: ["JAPAN", "INDIA"], seasons: ["Winter_Peak", "Summer_Trough"], starts: ["2026-01-05"] };
  const read = (query: string) => scenarioFromQuery(new URLSearchParams(query), known);

  it("carries a model's lever into the sliders a planner moves, without float noise", () => {
    expect(fromLever({ ...toLever(DEFAULT_INPUT), delta_frequency: 3, aircraft_gauge: 300 })).toMatchObject({ frequency: 3, gauge: 300 });
    expect(fromLever({ ...toLever(DEFAULT_INPUT), delta_seats_pct: 0.1, delta_load_factor: 0.05, delta_los: 0.4 }))
      .toMatchObject({ seatsPct: 10, loadFactorPts: 5, factor: 0.4 });
  });

  it("writes only what the user changed, so an untouched workbench keeps a clean URL", () => {
    expect(scenarioQuery({ market: "ALL" }, DEFAULT_INPUT)).toBe("");
    expect(scenarioQuery({ market: "JAPAN", season: "Winter_Peak" }, { ...DEFAULT_INPUT, frequency: 3, gauge: 300 }))
      .toBe("market=JAPAN&season=Winter_Peak&frequency=3&gauge=300");
  });

  it("opens the workbench on the market, season and levers the link names", () => {
    const opened = read("market=INDIA&season=Summer_Trough&seatsPct=10");
    expect(opened.market).toBe("INDIA");
    expect(opened.season).toBe("Summer_Trough");
    expect(opened.input.seatsPct).toBe(10);
    expect(scenarioQuery({ market: opened.market, season: opened.season ?? undefined }, opened.input)).toBe("market=INDIA&season=Summer_Trough&seatsPct=10");
  });

  it("falls back to the defaults for anything the workbench cannot show", () => {
    const opened = read("market=ATLANTIS&season=Wet_Season&start=1999-01-04&frequency=999&gauge=nonsense");
    expect(opened.market).toBe("ALL");
    expect(opened.season).toBeNull();
    expect(opened.start).toBeNull();
    expect(opened.input.frequency).toBe(14);
    expect(opened.input.gauge).toBe(250);
    expect(read("start=2026-01-05").start).toBe("2026-01-05");
  });

  it("offers the first week after the data, then every third month", () => {
    expect(startOptions(["2025-07-21", "2025-07-28", "2025-10-06", "2026-01-05", "2026-01-12"], "2025-07-28"))
      .toEqual(["2025-10-06", "2026-01-05"]);
  });
});
