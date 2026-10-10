import { NO_CHANGE, type Lever, type Planning } from "../../engine/planning";

/** Slider state in display units (percent and points); `toLever` converts to the engine's fractions.
 *  Ranges match the original app (src/app/static/index.html). */
export interface LeverInput { frequency: number; gauge: number; seatsPct: number; loadFactorPts: number; p2pPts: number; multiplierPct: number; factor: number }

export const DEFAULT_INPUT: LeverInput = { frequency: 0, gauge: 250, seatsPct: 0, loadFactorPts: 0, p2pPts: 0, multiplierPct: 0, factor: 0 };

export const LEVER_SLIDERS: ReadonlyArray<{ key: keyof LeverInput; label: string; min: number; max: number; step: number; format: (v: number) => string }> = [
  { key: "frequency", label: "Weekly round trips added", min: -14, max: 14, step: 1, format: signed("") },
  { key: "gauge", label: "Seats per added flight", min: 150, max: 450, step: 10, format: String },
  { key: "seatsPct", label: "Seat capacity", min: -50, max: 50, step: 5, format: signed("%") },
  { key: "loadFactorPts", label: "Load factor", min: -10, max: 10, step: 1, format: signed(" pts") },
  { key: "p2pPts", label: "Point-to-point share", min: -10, max: 10, step: 1, format: signed(" pts") },
  { key: "multiplierPct", label: "Response multiplier", min: -20, max: 20, step: 1, format: signed("%") },
  { key: "factor", label: "Guests-per-arrival factor", min: -1, max: 2, step: 0.1, format: (v) => signed("")(Number(v.toFixed(1))) },
];

function signed(unit: string) {
  return (v: number) => `${v > 0 ? "+" : ""}${v}${unit}`;
}

export function toLever(input: LeverInput): Lever {
  return { ...NO_CHANGE, delta_frequency: input.frequency, aircraft_gauge: input.gauge, delta_seats_pct: input.seatsPct / 100,
           delta_load_factor: input.loadFactorPts / 100, delta_p2p_share: input.p2pPts / 100,
           delta_multiplier_pct: input.multiplierPct / 100, delta_los: input.factor };
}

/** Calibrated markets first, then archetype-mapped countries without flights (cold start). */
export function marketOptions(planning: Planning): Array<{ value: string; label: string; coldStart: boolean }> {
  const calibrated = Object.keys(planning.calibration).sort();
  const cold = Object.keys(planning.archetypes.country).filter((c) => !(c in planning.calibration)).sort();
  return [...calibrated.map((m) => ({ value: m, label: m, coldStart: false })), ...cold.map((m) => ({ value: m, label: `${m} (cold start)`, coldStart: true }))];
}
