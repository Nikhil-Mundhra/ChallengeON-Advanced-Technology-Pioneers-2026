/**
 * The weekly scenario model (planning/structural.py, schedule_response.py, residual.py, uncertainty.py
 * conformal bands, sensitivity.py) as pure functions over the exported planning data. Parity with
 * Python is tested against golden cases from `twin export`. The Monte Carlo spread is not ported.
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

/** Elasticity of a market's guests to its seats in one season, read off the fitted planning chain
 *  (planning/schedule_response.py); `pooled` for markets without seats of their own. */
export interface Elasticity { epsilon: number; low: number; high: number; pooled: boolean; points: number[]; curvature: number }

/** Co-movement of the guest trend with the seat trend (planning/capacity_trend.py): an association,
 *  used as the central line of the capacity-growth assumption. */
export interface CoMovement {
  gamma: number; low: number; high: number; intercept: number; n_pairs: number; n_markets: number;
  central: number; effect_range: [number, number];
}

export interface FlightResponse {
  schedule: { source: string; changes: number[]; range: string; pooled: Record<string, Elasticity>; markets: Record<string, Record<string, Elasticity>> };
  capacity: CoMovement;
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
  flight_response: FlightResponse;
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

/** Hotel arrivals per added (or removed) P2P passenger: the multiplier, at most 1 (planning/structural._marginal). */
const marginal = (multiplier: number) => Math.min(multiplier, 1);

/** The market's schedule elasticity in the season, or the pooled one for a market without seats of its own. */
export function elasticityFor(planning: Planning, market: string, season: string): Elasticity {
  const schedule = planning.flight_response.schedule;
  return schedule.markets[market.toUpperCase().trim()]?.[season] ?? schedule.pooled[season];
}

/** What the new schedule brings with the other stages at baseline: its arrivals and its hotel
 *  arrivals per P2P passenger relative to today's marginal rate (planning/structural.Schedule). */
interface Schedule { arrivals: number; conversion: number }

/** The scenario chain and its schedule part (planning/structural._international_scenario). A served
 *  route's arrivals follow (new seats / baseline seats) ** epsilon; a new route's added P2P passengers
 *  convert at the marginal rate; load-factor and P2P-share shifts convert at the schedule's own rate. */
function internationalScenario(p: MarketSeasonParams, base: Chain, lever: Lever, epsilon: number): { chain: Chain; schedule: Schedule } {
  const gauge = lever.aircraft_gauge > 0 ? lever.aircraft_gauge : 250;
  const seats = Math.max(0, (base.seats + lever.delta_frequency * gauge) * (1 + lever.delta_seats_pct));
  const multiplier = lever.delta_multiplier_pct !== 0 ? Math.max(0.01, base.multiplier * (1 + lever.delta_multiplier_pct)) : base.multiplier;
  const los = shiftedLos(base, lever);

  if (seats <= 0) {   // closure: only visitors arriving by other routes stay
    const arrivals = Math.max(0, base.p2p * Math.max(multiplier - 1, 0));
    return { chain: { seats: 0, lf: base.lf, pax: 0, p2pShare: base.p2pShare, p2p: 0, multiplier, arrivals, los, guests: arrivals * los },
             schedule: { arrivals: base.p2p * Math.max(base.multiplier - 1, 0), conversion: 1 } };
  }

  const lf = lever.delta_load_factor !== 0 ? clip(base.lf + lever.delta_load_factor, 0.05, 1) : base.lf;
  const p2pShare = lever.delta_p2p_share !== 0 ? clip(base.p2pShare + lever.delta_p2p_share, 0.01, 1) : base.p2pShare;
  const pax = seats * lf;
  const p2p = pax * p2pShare;
  const scheduledP2p = seats * base.lf * base.p2pShare;

  let schedule: Schedule, carried: number;
  if (base.seats <= 0) {   // new route
    schedule = { arrivals: arrivalsFrom(p, base.p2p, base.multiplier) + scheduledP2p * marginal(base.multiplier), conversion: 1 };
    carried = arrivalsFrom(p, base.p2p, multiplier) + scheduledP2p * marginal(multiplier);
  } else {
    const factor = Math.pow(seats / base.seats, epsilon);
    schedule = { arrivals: base.arrivals * factor, conversion: factor * base.seats / seats };
    carried = base.multiplier > 0 ? schedule.arrivals * (multiplier / base.multiplier) : schedule.arrivals;
  }
  const arrivals = Math.max(0, carried + (p2p - scheduledP2p) * marginal(multiplier) * schedule.conversion);
  return { chain: { seats, lf, pax, p2pShare, p2p, multiplier, arrivals, los, guests: arrivals * los }, schedule };
}

/** Forward conversion chain (seats -> pax -> P2P -> arrivals -> guests) and its exact waterfall.
 *  `epsilon` overrides the market's schedule elasticity (scheduleRange uses its range's ends). */
export function simulate(planning: Planning, market: string, season: string, lever: Lever = NO_CHANGE, epsilon?: number): SimulationResult {
  const name = market.toUpperCase().trim();
  const p = paramsFor(planning, name, season);
  const domestic = name === DOMESTIC || p.archetype === DOMESTIC_ARCHETYPE;
  const base = baselineChain(p, domestic);
  const { chain: sim, schedule } = domestic
    ? { chain: domesticScenario(base, lever), schedule: { arrivals: base.arrivals, conversion: 1 } }
    : internationalScenario(p, base, lever, epsilon ?? elasticityFor(planning, name, season).epsilon);
  const rate = marginal(base.multiplier) * base.los * schedule.conversion;
  const seats = domestic ? 0 : (schedule.arrivals - base.arrivals) * base.los;
  const lf = sim.seats * (sim.lf - base.lf) * base.p2pShare * rate;
  const p2p = sim.pax * (sim.p2pShare - base.p2pShare) * rate;
  const waterfall = {
    seats, lf, p2p,
    multiplier: domestic ? (sim.arrivals - base.arrivals) * base.los : (sim.arrivals - base.arrivals) * base.los - (seats + lf + p2p),
    los: sim.arrivals * (sim.los - base.los),
  };
  return { market: name, season, is_cold_start: p.is_cold_start, base, sim, delta_guests: sim.guests - base.guests, waterfall };
}

/** Scenario guests at the two ends of the market's elasticity range, lower first. */
export function scheduleRange(planning: Planning, market: string, season: string, lever: Lever): [number, number] {
  const e = elasticityFor(planning, market, season);
  const ends = [e.low, e.high].map((b) => simulate(planning, market, season, lever, b).sim.guests).sort((a, b) => a - b);
  return [ends[0], ends[1]];
}

/** What a schedule change alone does in one season: the seat change, and the guest change with its
 *  range from the elasticity's spread over refits. `kind` says how the response is known. */
export interface ScheduleEffect {
  kind: "none" | "learned" | "pooled" | "new_route" | "closed";
  seatChange: number;                // fraction
  guestChange: number;               // fraction, central
  range: [number, number];           // fraction
}

export function scheduleEffect(planning: Planning, market: string, season: string, lever: Lever): ScheduleEffect {
  const only: Lever = { ...NO_CHANGE, delta_frequency: lever.delta_frequency, aircraft_gauge: lever.aircraft_gauge, delta_seats_pct: lever.delta_seats_pct };
  const result = simulate(planning, market, season, only);
  const { base, sim } = result;
  if (sim.seats === base.seats) return { kind: "none", seatChange: 0, guestChange: 0, range: [0, 0] };
  if (base.seats <= 0) return { kind: "new_route", seatChange: 0, guestChange: 0, range: [0, 0] };
  if (sim.seats <= 0) return { kind: "closed", seatChange: -1, guestChange: base.guests > 0 ? sim.guests / base.guests - 1 : 0, range: [0, 0] };
  const [low, high] = scheduleRange(planning, market, season, only);
  const ratio = (g: number) => (base.guests > 0 ? g / base.guests - 1 : 0);
  return { kind: elasticityFor(planning, market, season).pooled ? "pooled" : "learned", seatChange: sim.seats / base.seats - 1,
           guestChange: ratio(sim.guests), range: [ratio(low), ratio(high)] };
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

/** The market's own conformal margin, or null for a market without one (cold start), whose
 *  ranges use the unmeasured default_conformal_margin. */
export function ownMargin(planning: Planning, market: string): number | null {
  return market.startsWith("_") ? null : planning.conformal[market] ?? null;
}

/** Share of the 30 holdout market-weeks inside the conformal range, in % (target 80; docs/results/planning-holdout.md). */
export function holdoutCoverage(planning: Planning): number | null {
  return planning.conformal["_demonstrated_holdout_coverage"] ?? null;
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

export interface WeeklyHeadline {
  result: SimulationResult;
  base: number;              // weekly guests today, calendar adjustment included
  sim: number;               // with the changes
  residual: number;          // calendar adjustment for the market and season
  change: number;
  changePct: number | null;  // null without current service
  errorPct: number | null;   // the market's own conformal margin, as a share; null without one (the default margin is not measured)
}

/** The simulator's headline numbers for one market, season and set of levers. */
export function weeklyHeadline(planning: Planning, market: string, season: string, lever: Lever): WeeklyHeadline {
  const result = simulate(planning, market, season, lever);
  const calendar = hybrid(planning, result);
  return {
    result, base: calendar.base, sim: calendar.sim, residual: calendar.residual, change: calendar.delta,
    changePct: calendar.base > 0 ? calendar.delta / calendar.base : null,
    errorPct: ownMargin(planning, market),
  };
}
