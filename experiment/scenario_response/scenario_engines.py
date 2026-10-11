"""LINEAR and S-CURVE: the shipped weekly scenario path (StructuralEngine.simulate + the residual
layer's weekly baseline), with the three hand-set adjustments of `_international_scenario` (frequency
S-curve, capacity dilution, saturation; commit 3af6a13) switched off or on. The switch lives here only:
LinearEngine swaps the module's scenario function for a copy with the adjustments off during simulate().

Lever mapping for an observed seat change from a reference week (last year, or the seat trend) to
this week, both ways reaching the same scenario seats = calibrated seats x seats / reference seats:
  seats lever:      delta_seats_pct = seats / ref_seats - 1
  frequency lever:  aircraft_gauge g = ref_seats / ref_flights (the reference week's seats per flight),
                    delta_frequency = (calibrated seats / g) x (flights / ref_flights - 1),
                    delta_seats_pct = (seats / flights) / g - 1 (the gauge change).
The S-curve only acts through delta_frequency, so the frequency lever is the one that exercises it.
"""

from __future__ import annotations

from functools import partial

import numpy as np

from tourism_twin.domain.scenario import Chain, MarketSeasonParams, ScenarioLever
from tourism_twin.planning import structural
from tourism_twin.planning.structural import StructuralEngine, _marginal, _shifted_los

SHIPPED = structural._international_scenario


def international_scenario(p: MarketSeasonParams, base: Chain, lever: ScenarioLever,
                           scurve: bool = True, dilution: bool = True, saturation: bool = True) -> Chain:
    """Copy of structural._international_scenario with each adjustment behind a flag (all on = shipped)."""
    gauge = lever.aircraft_gauge if lever.aircraft_gauge > 0 else 250.0
    seats = max(0.0, (base.seats + lever.delta_frequency * gauge) * (1.0 + lever.delta_seats_pct))
    if seats <= 0.0:
        multiplier = max(0.01, base.multiplier * (1.0 + lever.delta_multiplier_pct)) if lever.delta_multiplier_pct != 0.0 else base.multiplier
        arrivals = max(0.0, base.p2p * max(multiplier - 1.0, 0.0))
        los = _shifted_los(base, lever)
        return Chain(0.0, base.lf, 0.0, base.p2p_share, 0.0, multiplier, arrivals, los, arrivals * los)

    m_freq = 1.0
    if scurve and lever.delta_frequency != 0.0:
        f_base = base.seats / gauge if base.seats > 0 else 0.0
        f_sim = max(0.0, f_base + lever.delta_frequency)
        gamma, f0 = 1.5, 7.0
        s_sim = (f_sim ** gamma) / (f_sim ** gamma + f0 ** gamma)
        if f_base > 0.0:
            m_freq = float(np.clip(s_sim / ((f_base ** gamma) / (f_base ** gamma + f0 ** gamma)), 0.85, 1.15))
        else:
            m_freq = float(np.clip(s_sim / 0.5, 0.75, 1.0))

    lf_decay = p2p_decay = 1.0
    if dilution and base.seats > 0.0 and seats > base.seats:
        expansion = (seats - base.seats) / base.seats
        lf_decay, p2p_decay = (1.0 + expansion) ** (-0.05), (1.0 + expansion) ** (-0.08)

    lf = float(np.clip(base.lf * m_freq * lf_decay + lever.delta_load_factor, 0.05, 1.0)) if (lever.delta_load_factor != 0.0 or m_freq != 1.0 or lf_decay != 1.0) else base.lf
    pax = seats * lf
    share = float(np.clip(base.p2p_share * p2p_decay + lever.delta_p2p_share, 0.01, 1.0)) if (lever.delta_p2p_share != 0.0 or p2p_decay != 1.0) else base.p2p_share
    p2p = pax * share
    multiplier = max(0.01, base.multiplier * (1.0 + lever.delta_multiplier_pct)) if lever.delta_multiplier_pct != 0.0 else base.multiplier
    arrivals = max(0.0, p.arrivals_from(base.p2p, multiplier) + (p2p - base.p2p) * _marginal(multiplier))
    los = _shifted_los(base, lever)

    if saturation:
        kappa = 2.5 if p.season in ("Winter_Peak", "Spring_Shoulder") else 2.0
        c_cap = kappa * base.guests if base.guests > 0 else 0.0
        delta_g = arrivals * los - base.guests
        if delta_g > 0.0 and c_cap > base.guests:
            arrivals = (base.guests + (c_cap - base.guests) * delta_g / ((c_cap - base.guests) + delta_g)) / los
    return Chain(seats, lf, pax, share, p2p, multiplier, arrivals, los, arrivals * los)


linear_scenario = partial(international_scenario, scurve=False, dilution=False, saturation=False)


class LinearEngine(StructuralEngine):
    """StructuralEngine whose simulate() runs the scenario with the three adjustments off."""

    def simulate(self, market, season, lever=None):
        structural._international_scenario = linear_scenario
        try:
            return super().simulate(market, season, lever)
        finally:
            structural._international_scenario = SHIPPED


def as_linear(engine: StructuralEngine) -> LinearEngine:
    out = LinearEngine()
    out.params = engine.params
    return out


def levers(engine: StructuralEngine, market: str, season: str, seats: float, flights: float,
           ref_seats: float, ref_flights: float) -> dict:
    """The observed change as a seats lever and as a frequency lever (module docstring)."""
    seats_lever = ScenarioLever(market=market, delta_seats_pct=seats / ref_seats - 1.0)
    if not (flights > 0 and ref_flights > 0):
        return {"seats": seats_lever, "frequency": seats_lever}
    gauge = ref_seats / ref_flights
    base_flights = engine.get_or_create_params(market, season).baseline_weekly_seats / gauge
    freq_lever = ScenarioLever(market=market, aircraft_gauge=gauge, delta_frequency=base_flights * (flights / ref_flights - 1.0),
                               delta_seats_pct=(seats / flights) / gauge - 1.0)
    return {"seats": seats_lever, "frequency": freq_lever}


def shipped_matches_copy(engine: StructuralEngine) -> float:
    """Largest relative gap in scenario guests between the shipped function and the all-on copy, over
    every calibrated market-season and a grid of frequency and seat levers (should be 0)."""
    worst = 0.0
    for market, seasons in engine.params.items():
        for season, p in seasons.items():
            base = structural._baseline_chain(p, False)
            if base.guests <= 0:
                continue
            for df in (-20.0, -3.0, 0.0, 2.0, 15.0):
                for pct in (-0.5, -0.1, 0.0, 0.2, 1.0):
                    lever = ScenarioLever(market=market, delta_frequency=df, aircraft_gauge=300.0, delta_seats_pct=pct)
                    a, b = SHIPPED(p, base, lever).guests, international_scenario(p, base, lever).guests
                    worst = max(worst, abs(a - b) / max(base.guests, 1.0))
    return worst


def calibration_gap(refit: StructuralEngine, shipped: StructuralEngine) -> float:
    """Largest relative difference in any calibrated parameter between two engines."""
    worst = 0.0
    for market, seasons in shipped.params.items():
        for season, p in seasons.items():
            q = refit.params[market][season]
            for field in ("baseline_weekly_seats", "baseline_load_factor", "baseline_p2p_share", "effective_response_multiplier",
                          "baseline_los", "baseline_weekly_arrivals", "baseline_weekly_guests"):
                a, b = getattr(p, field), getattr(q, field)
                worst = max(worst, abs(a - b) / max(abs(a), 1e-12))
    return worst


def season_residual_gap(refit, shipped) -> float:
    worst = 0.0
    for market, seasons in shipped.season_residual_.items():
        for season, value in seasons.items():
            worst = max(worst, abs(value - refit.season_residual_[market][season]) / max(abs(value), 1.0))
    return worst

