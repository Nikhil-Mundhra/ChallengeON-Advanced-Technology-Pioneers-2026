/**
 * The weekly scenario model (planning/structural.py, residual.py, uncertainty.py conformal bands,
 * sensitivity.py) as pure functions over the exported planning data. Parity with Python is tested
 * against golden cases from `twin export`. The Monte Carlo spread is not ported.
 */

export interface MarketSeasonParams {
  market: string;
  season: string;
  archetype: string;
  baseline_weekly_seats: number;
  baseline_load_factor: number;
  baseline_p2p_share: number;
  effective_response_multiplier: number;
  baseline_los: number;
  baseline_weekly_arrivals: number;
  baseline_weekly_guests: number;
  historical_weeks: number;
  is_cold_start: boolean;
}

export interface Planning {
  calibration: Record<string, Record<string, MarketSeasonParams>>;
  archetypes: {
    profiles: Record<string, { default_los: number; default_multiplier: number; default_load_factor: number; default_p2p_share: number }>;
    market: Record<string, string>;
    country: Record<string, string>;
    fallback: string;
  };
  season_residual: Record<string, Record<string, number>>;
  conformal: Record<string, number>;
  default_conformal_margin: number;
}

export interface Lever {
  delta_frequency: number;       // weekly round trips added
  aircraft_gauge: number;        // seats per added flight
  delta_seats_pct: number;       // proportional seat change
  delta_load_factor: number;     // absolute load-factor shift
  delta_p2p_share: number;       // absolute point-to-point share shift
  delta_multiplier_pct: number;  // proportional response-multiplier shift
  delta_los: number;             // absolute guests-per-arrival factor shift
}

export const NO_CHANGE: Lever = { delta_frequency: 0, aircraft_gauge: 250, delta_seats_pct: 0, delta_load_factor: 0,
  delta_p2p_share: 0, delta_multiplier_pct: 0, delta_los: 0 };

interface Chain { seats: number; lf: number; pax: number; p2pShare: number; p2p: number; multiplier: number; arrivals: number; los: number; guests: number }

export interface SimulationResult {
  market: string; season: string; is_cold_start: boolean;
  base: Chain; sim: Chain;
  delta_guests: number;
  waterfall: { seats: number; lf: number; p2p: number; multiplier: number; los: number };
}

const DOMESTIC = "DOMESTIC";
const DOMESTIC_ARCHETYPE = "Domestic Staycation";
const clip = (x: number, low: number, high: number) => Math.min(Math.max(x, low), high);

export function archetypeOf(planning: Planning, market: string): string {
  const name = market.toUpperCase().trim();
  return planning.archetypes.market[name] ?? planning.archetypes.country[name] ?? planning.archetypes.fallback;
}

/** Calibrated parameters, or the archetype's priors for a market without calibration (cold start). */
export function paramsFor(planning: Planning, market: string, season: string): MarketSeasonParams {
  const name = market.toUpperCase().trim();
  const calibrated = planning.calibration[name]?.[season];
  if (calibrated) return calibrated;
  const archetype = archetypeOf(planning, name);
  const prior = planning.archetypes.profiles[archetype];
  return { market: name, season, archetype, baseline_weekly_seats: 0, baseline_load_factor: prior.default_load_factor,
    baseline_p2p_share: prior.default_p2p_share, effective_response_multiplier: prior.default_multiplier,
    baseline_los: prior.default_los, baseline_weekly_arrivals: 0, baseline_weekly_guests: 0, historical_weeks: 0, is_cold_start: true };
}

/** Arrivals carried by P2P passengers: converted when there are any; none on a served route that
 *  carries none; a never-served market keeps its non-aviation arrivals. */
function arrivalsFrom(p: MarketSeasonParams, p2p: number, multiplier: number): number {
  if (p2p > 0) return p2p * multiplier;
  return p.baseline_weekly_seats > 0 ? 0 : p.baseline_weekly_arrivals;
}

function baselineChain(p: MarketSeasonParams, domestic: boolean): Chain {
  const [seats, lf, p2pShare] = domestic ? [0, 0, 0] : [p.baseline_weekly_seats, p.baseline_load_factor, p.baseline_p2p_share];
  const pax = seats * lf;
  const p2p = pax * p2pShare;
  const multiplier = p.effective_response_multiplier;
  const arrivals = domestic ? p.baseline_weekly_arrivals : arrivalsFrom(p, p2p, multiplier);
  return { seats, lf, pax, p2pShare, p2p, multiplier, arrivals, los: p.baseline_los, guests: arrivals * p.baseline_los };
}

const shiftedLos = (base: Chain, lever: Lever) => (lever.delta_los !== 0 ? Math.max(1, base.los + lever.delta_los) : base.los);

function domesticScenario(base: Chain, lever: Lever): Chain {
  let multiplier = base.multiplier;
  let arrivals = base.arrivals;
  if (lever.delta_multiplier_pct !== 0) {
    multiplier = base.multiplier * (1 + lever.delta_multiplier_pct);
    arrivals = Math.max(0, base.arrivals * (1 + lever.delta_multiplier_pct));
  }
  const los = shiftedLos(base, lever);
  return { seats: 0, lf: 0, pax: 0, p2pShare: 0, p2p: 0, multiplier, arrivals, los, guests: arrivals * los };
}

function internationalScenario(p: MarketSeasonParams, base: Chain, lever: Lever): Chain {
  const seats = Math.max(0, (base.seats + lever.delta_frequency * lever.aircraft_gauge) * (1 + lever.delta_seats_pct));
  const lf = lever.delta_load_factor !== 0 ? clip(base.lf + lever.delta_load_factor, 0.05, 1) : base.lf;
  const pax = seats * lf;
  const p2pShare = lever.delta_p2p_share !== 0 ? clip(base.p2pShare + lever.delta_p2p_share, 0.01, 1) : base.p2pShare;
  const p2p = pax * p2pShare;
  const multiplier = lever.delta_multiplier_pct !== 0 ? Math.max(0.01, base.multiplier * (1 + lever.delta_multiplier_pct)) : base.multiplier;
  const arrivals = arrivalsFrom(p, p2p, multiplier);
  const los = shiftedLos(base, lever);
  return { seats, lf, pax, p2pShare, p2p, multiplier, arrivals, los, guests: arrivals * los };
}

/** Forward conversion chain (seats -> pax -> P2P -> arrivals -> guests) and its exact waterfall. */
export function simulate(planning: Planning, market: string, season: string, lever: Lever = NO_CHANGE): SimulationResult {
  const name = market.toUpperCase().trim();
  const p = paramsFor(planning, name, season);
  const domestic = name === DOMESTIC || p.archetype === DOMESTIC_ARCHETYPE;
  const base = baselineChain(p, domestic);
  const sim = domestic ? domesticScenario(base, lever) : internationalScenario(p, base, lever);
  const waterfall = {
    seats: (sim.seats - base.seats) * base.lf * base.p2pShare * base.multiplier * base.los,
    lf: sim.seats * (sim.lf - base.lf) * base.p2pShare * base.multiplier * base.los,
    p2p: sim.pax * (sim.p2pShare - base.p2pShare) * base.multiplier * base.los,
    multiplier: domestic ? (sim.arrivals - base.arrivals) * base.los : sim.p2p * (sim.multiplier - base.multiplier) * base.los,
    los: sim.arrivals * (sim.los - base.los),
  };
  return { market: name, season, is_cold_start: p.is_cold_start, base, sim, delta_guests: sim.guests - base.guests, waterfall };
}

/** Structural prediction plus the market's mean calendar residual for the season, floored at 0. */
export function hybrid(planning: Planning, result: SimulationResult) {
  const residual = planning.season_residual[result.market]?.[result.season] ?? 0;
  const base = Math.max(0, result.base.guests + residual);
  const sim = Math.max(0, result.sim.guests + residual);
  return { residual, base, sim, delta: sim - base };
}

/** Conformal band on scenario guests and on the lift (planning/uncertainty.py). */
export function conformalBands(planning: Planning, result: SimulationResult) {
  const margin = planning.conformal[result.market] ?? planning.default_conformal_margin;
  return {
    margin,
    coverage: planning.conformal["_demonstrated_holdout_coverage"] ?? 66.7,
    p10: Math.max(0, result.sim.guests * (1 - margin)),
    p90: result.sim.guests * (1 + margin),
    deltaP10: result.delta_guests - result.sim.guests * margin,
    deltaP90: result.delta_guests + result.sim.guests * margin,
  };
}

export interface TornadoRow { lever_name: string; high_impact_delta: number; low_impact_delta: number; swing_spread: number; relative_sensitivity: number }

/** How far weekly guests swing when each lever moves up and down (planning/sensitivity.py). */
export function tornado(planning: Planning, market: string, season: string, baseLever?: Lever): TornadoRow[] {
  const name = market.toUpperCase().trim();
  const baseResult = simulate(planning, name, season);
  let refFreq = 0;
  let refGauge = 250;
  let reference = baseResult.base.guests;
  if (baseResult.base.seats === 0) {  // unserved or cold start: around the proposed or a reference service
    if (baseLever && (baseLever.delta_frequency > 0 || baseLever.delta_seats_pct !== 0)) {
      refFreq = baseLever.delta_frequency; refGauge = baseLever.aircraft_gauge;
    } else {
      refFreq = 2; refGauge = 250;
    }
    reference = simulate(planning, name, season, { ...NO_CHANGE, delta_frequency: refFreq, aircraft_gauge: refGauge }).sim.guests;
  }
  const at = (patch: Partial<Lever>): Lever => ({ ...NO_CHANGE, delta_frequency: refFreq, aircraft_gauge: refGauge, ...patch });
  const tests: Array<[string, Partial<Lever>, Partial<Lever>]> = [
    ["Seat Capacity (+15% / -15%)", { delta_seats_pct: 0.15 }, { delta_seats_pct: -0.15 }],
    ["Load Factor (+4% / -4%)", { delta_load_factor: 0.04 }, { delta_load_factor: -0.04 }],
    ["P2P Share (+5% / -5%)", { delta_p2p_share: 0.05 }, { delta_p2p_share: -0.05 }],
    ["Response Multiplier (+10% / -10%)", { delta_multiplier_pct: 0.1 }, { delta_multiplier_pct: -0.1 }],
    ["Guests-per-arrival factor (+0.5 / -0.5)", { delta_los: 0.5 }, { delta_los: -0.5 }],
  ];
  return tests.map(([lever_name, up, down]) => {
    const high = simulate(planning, name, season, at(up)).sim.guests - reference;
    const low = simulate(planning, name, season, at(down)).sim.guests - reference;
    const spread = Math.abs(high - low);
    return { lever_name, high_impact_delta: high, low_impact_delta: low, swing_spread: spread,
             relative_sensitivity: reference > 0 ? spread / reference : 0 };
  }).sort((a, b) => b.swing_spread - a.swing_spread);
}
