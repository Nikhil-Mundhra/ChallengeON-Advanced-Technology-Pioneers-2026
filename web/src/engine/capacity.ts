/**
 * Capacity growth (planning/capacity_trend.py): a yearly seat trend is an assumption, and so is how
 * far guests follow it. The guest effect runs from 0 (guests do not follow seats) to 1 (one for one);
 * the central line is the past co-movement of the guest trend with the seat trend.
 */
import type { Planning } from "./planning";

/** Guests with the seat trend / guests without it, `years` after the trend starts. */
export function capacityGuestFactor(growthPct: number, years: number, effect: number): number {
  return Math.pow(1 + growthPct / 100, Math.max(0, years) * effect);
}

/** The three guest effects the simulator draws: none, the past co-movement, one for one. */
export function capacityEffects(planning: Planning): { low: number; central: number; high: number } {
  const c = planning.flight_response.capacity;
  return { low: c.effect_range[0], central: c.central, high: c.effect_range[1] };
}

/** Guest change (fraction) `years` after the start: central, and the range from no effect to one for one. */
export function capacityOutlook(planning: Planning, growthPct: number, years: number) {
  const e = capacityEffects(planning);
  const at = (effect: number) => capacityGuestFactor(growthPct, years, effect) - 1;
  const ends = [at(e.low), at(e.high)].sort((a, b) => a - b);
  return { central: at(e.central), range: [ends[0], ends[1]] as [number, number], seatChange: at(1) };
}
