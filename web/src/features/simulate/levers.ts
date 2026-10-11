import { formatSigned } from "../../data/format";
import { NO_CHANGE, type Lever, type Planning } from "../../engine/planning";

/** Slider state in display units (percent and points); `toLever` converts to the engine's fractions.
 *  Ranges match the original app (src/app/static/index.html). */
export interface LeverInput { frequency: number; gauge: number; seatsPct: number; loadFactorPts: number; p2pPts: number; multiplierPct: number; factor: number }

export const DEFAULT_INPUT: LeverInput = { frequency: 0, gauge: NO_CHANGE.aircraft_gauge, seatsPct: 0, loadFactorPts: 0, p2pPts: 0, multiplierPct: 0, factor: 0 };

export interface SliderSpec { key: keyof LeverInput; label: string; hint: string; min: number; max: number; step: number; format: (v: number) => string }
export interface LeverGroup { id: "flights" | "visitors"; title: string; sliders: SliderSpec[] }

const unit = (u: string) => (v: number) => formatSigned(v, (x) => `${Number(x.toFixed(1))}${u}`);

/** Grouped as a planner thinks: what airlines fly, then what the passengers do. */
export const LEVER_GROUPS: ReadonlyArray<LeverGroup> = [
  { id: "flights", title: "Flights", sliders: [
    { key: "frequency", label: "Extra flights per week", hint: "Round trips added or removed", min: -14, max: 14, step: 1, format: unit("") },
    { key: "gauge", label: "Seats per extra flight", hint: "Aircraft size", min: 150, max: 450, step: 10, format: String },
    { key: "seatsPct", label: "Seats on existing flights", hint: "Bigger or smaller aircraft", min: -50, max: 50, step: 5, format: unit("%") },
    { key: "loadFactorPts", label: "How full flights are", hint: "Share of seats sold", min: -10, max: 10, step: 1, format: unit(" pts") },
  ] },
  { id: "visitors", title: "Visitors", sliders: [
    { key: "p2pPts", label: "Passengers who stop in Abu Dhabi", hint: "Rather than connecting onward", min: -10, max: 10, step: 1, format: unit(" pts") },
    { key: "multiplierPct", label: "Visitors who book a hotel", hint: "Marketing, packages, events", min: -20, max: 20, step: 1, format: unit("%") },
    { key: "factor", label: "Hotel nights per visitor", hint: "Longer or repeat stays", min: -1, max: 2, step: 0.1, format: unit("") },
  ] },
];

/** One-tap starting points (the same values the export's golden cases exercise where they overlap). */
export const PRESETS = [
  { value: "today", label: "Today", input: DEFAULT_INPUT },
  { value: "more_flights", label: "2 more flights a week", input: { ...DEFAULT_INPUT, frequency: 2, gauge: 290, loadFactorPts: 2 } },
  { value: "stopover", label: "Stopover campaign", input: { ...DEFAULT_INPUT, p2pPts: 3, multiplierPct: 5 } },
  { value: "longer_stays", label: "Longer stays", input: { ...DEFAULT_INPUT, factor: 0.4 } },
] as const;
export type PresetId = (typeof PRESETS)[number]["value"];

export type LeverAction =
  | { type: "set"; key: keyof LeverInput; value: number }
  | { type: "resetGroup"; group: LeverGroup["id"] }
  | { type: "preset"; id: PresetId };

export function leverReducer(state: LeverInput, action: LeverAction): LeverInput {
  switch (action.type) {
    case "set": return { ...state, [action.key]: action.value };
    case "resetGroup": {
      const keys = LEVER_GROUPS.find((g) => g.id === action.group)!.sliders.map((s) => s.key);
      return { ...state, ...Object.fromEntries(keys.map((k) => [k, DEFAULT_INPUT[k]])) };
    }
    case "preset": return { ...PRESETS.find((p) => p.value === action.id)!.input };
  }
}

export const activePreset = (input: LeverInput): PresetId | null =>
  PRESETS.find((p) => (Object.keys(DEFAULT_INPUT) as Array<keyof LeverInput>).every((k) => p.input[k] === input[k]))?.value ?? null;

export const groupChanged = (input: LeverInput, group: LeverGroup) => group.sliders.some((s) => input[s.key] !== DEFAULT_INPUT[s.key]);

export function toLever(input: LeverInput): Lever {
  return { ...NO_CHANGE, delta_frequency: input.frequency, aircraft_gauge: input.gauge, delta_seats_pct: input.seatsPct / 100,
           delta_load_factor: input.loadFactorPts / 100, delta_p2p_share: input.p2pPts / 100,
           delta_multiplier_pct: input.multiplierPct / 100, delta_los: input.factor };
}

const SLIDERS = LEVER_GROUPS.flatMap((g) => g.sliders);
const pct = (x: number) => Math.round(x * 10_000) / 100;   // a fraction back to points, without float noise

/** The slider state behind an engine lever: `toLever` in reverse, so a scenario worked out in the
 *  model can be handed to the workbench as an example (the question cards link to the simulator). */
export function fromLever(lever: Lever): LeverInput {
  return { frequency: lever.delta_frequency, gauge: lever.aircraft_gauge, seatsPct: pct(lever.delta_seats_pct),
           loadFactorPts: pct(lever.delta_load_factor), p2pPts: pct(lever.delta_p2p_share),
           multiplierPct: pct(lever.delta_multiplier_pct), factor: Math.round(lever.delta_los * 10) / 10 };
}

/** The weeks the "changes start" picker offers: the week after the real data, then the first week
 *  of every third month after it. Also what a link may ask for as a start. */
export function startOptions(weeks: string[], firstWeek: string): string[] {
  return weeks.filter((w) => w > firstWeek && Number(w.slice(5, 7)) % 3 === 1 && Number(w.slice(8, 10)) <= 7);
}

export interface ScenarioTarget { market: string; season?: string; start?: string }

/** A scenario as a link: the market, its season, when the changes start and every slider that moved.
 *  Values are display units, so the link reads like the panel; defaults are left out, so a workbench
 *  nobody has touched keeps a clean URL. */
export function scenarioQuery(target: ScenarioTarget, input: LeverInput): string {
  const params = new URLSearchParams();
  if (target.market !== ALL_MARKETS) {
    params.set("market", target.market);
    if (target.season) params.set("season", target.season);
  }
  if (target.start) params.set("start", target.start);
  for (const { key } of SLIDERS) if (input[key] !== DEFAULT_INPUT[key]) params.set(key, String(input[key]));
  return params.toString();
}

export interface ScenarioStart { market: string; season: string | null; start: string | null; input: LeverInput }

/** The scenario a link asks for. Anything the workbench cannot show (an unknown market or season, a
 *  start week it does not offer) falls back to the default, so a hand-edited URL never breaks it. */
export function scenarioFromQuery(params: URLSearchParams, known: { markets: string[]; seasons: string[]; starts: string[] }): ScenarioStart {
  const market = params.get("market")?.toUpperCase() ?? "";
  const season = params.get("season");
  const start = params.get("start");
  const input = { ...DEFAULT_INPUT };
  for (const { key, min, max } of SLIDERS) {
    const value = Number(params.get(key));
    if (params.has(key) && Number.isFinite(value)) input[key] = Math.min(Math.max(value, min), max);
  }
  return {
    market: known.markets.includes(market) ? market : ALL_MARKETS,
    season: season !== null && known.seasons.includes(season) ? season : null,
    start: start !== null && known.starts.includes(start) ? start : null,
    input,
  };
}

/** The market picker's first option: every market together; flight changes need one market. */
export const ALL_MARKETS = "ALL";

export interface SliderAvailability { disabled: boolean; hint?: string }

/** Whether a slider applies to the chosen market, and why not. UAE residents have no flight
 *  route, so flight levers and the stopover share do not apply; aircraft size only matters once
 *  extra flights are added; with all markets, flight changes need a market first. */
export function sliderAvailability(market: string, input: LeverInput, key: keyof LeverInput): SliderAvailability {
  if (market === ALL_MARKETS) return { disabled: true };
  const flightKeys = LEVER_GROUPS.find((g) => g.id === "flights")!.sliders.map((s) => s.key);
  if (market === "DOMESTIC" && (flightKeys.includes(key) || key === "p2pPts")) {
    return { disabled: true, hint: key === "p2pPts" ? "Not applicable to UAE residents" : undefined };
  }
  if (key === "gauge" && input.frequency === 0) return { disabled: true, hint: "Applies when extra flights are added" };
  return { disabled: false };
}

/** Presets that do something for the chosen market. */
export const presetAvailable = (market: string, id: PresetId) =>
  market !== ALL_MARKETS && !(market === "DOMESTIC" && id === "more_flights");

/** Calibrated markets first, then countries with no data of their own (estimated from similar markets). */
export function marketOptions(planning: Planning): Array<{ value: string; label: string }> {
  const calibrated = Object.keys(planning.calibration).sort();
  const cold = Object.keys(planning.archetypes.country).filter((c) => !(c in planning.calibration)).sort();
  return [...calibrated.map((m) => ({ value: m, label: m })), ...cold.map((m) => ({ value: m, label: `${m} (estimated from similar markets)` }))];
}
