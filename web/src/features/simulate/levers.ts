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
    { key: "factor", label: "Hotel guests per visitor", hint: "Nights and repeat stays", min: -1, max: 2, step: 0.1, format: unit("") },
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

/** Markets with flight history first, then countries without direct flights (estimated from similar markets). */
export function marketOptions(planning: Planning): Array<{ value: string; label: string }> {
  const calibrated = Object.keys(planning.calibration).sort();
  const cold = Object.keys(planning.archetypes.country).filter((c) => !(c in planning.calibration)).sort();
  return [...calibrated.map((m) => ({ value: m, label: m })), ...cold.map((m) => ({ value: m, label: `${m} (no direct flights)` }))];
}
