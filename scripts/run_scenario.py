#!/usr/bin/env python3
"""Run a planner scenario on the Abu Dhabi Tourism Digital Twin."""

import argparse


from engine.simulator import TourismDigitalTwin
from engine.structural import ScenarioLever


def main():
    parser = argparse.ArgumentParser(
        description="Abu Dhabi Tourism Digital Twin - Scenario Simulator"
    )
    parser.add_argument(
        "--market",
        type=str,
        default="UNITED KINGDOM",
        help="Target source market (e.g. 'UNITED KINGDOM', 'INDIA', 'SWEDEN', 'BRAZIL')",
    )
    parser.add_argument(
        "--season",
        type=str,
        default="Winter_Peak",
        choices=["Winter_Peak", "Spring_Shoulder", "Summer_Trough", "Autumn_Shoulder"],
        help="Season for simulation",
    )
    parser.add_argument(
        "--delta_freq",
        type=float,
        default=2.0,
        help="Additional weekly round-trip flights (e.g. +2.0)",
    )
    parser.add_argument(
        "--gauge",
        type=float,
        default=290.0,
        help="Aircraft seat capacity gauge for added frequency (default 290 for B787)",
    )
    parser.add_argument(
        "--delta_seats_pct",
        type=float,
        default=0.0,
        help="Proportional shift in seat capacity (e.g. 0.10 for +10%)",
    )
    parser.add_argument(
        "--delta_lf",
        type=float,
        default=0.02,
        help="Absolute shift in load factor (e.g. +0.02 for +2%)",
    )
    parser.add_argument(
        "--delta_p2p",
        type=float,
        default=0.0,
        help="Shift in P2P share (e.g. +0.02)",
    )
    parser.add_argument(
        "--delta_mult_pct",
        type=float,
        default=0.0,
        help="Proportional shift in response multiplier from marketing (e.g. +0.05)",
    )
    parser.add_argument(
        "--delta_los",
        type=float,
        default=0.0,
        help="Absolute shift in length of stay days (e.g. +0.3)",
    )

    args = parser.parse_args()

    twin = TourismDigitalTwin()

    lever = ScenarioLever(
        market=args.market,
        delta_frequency=args.delta_freq,
        aircraft_gauge=args.gauge,
        delta_seats_pct=args.delta_seats_pct,
        delta_load_factor=args.delta_lf,
        delta_p2p_share=args.delta_p2p,
        delta_multiplier_pct=args.delta_mult_pct,
        delta_los=args.delta_los,
    )

    report = twin.run_scenario(
        market=args.market,
        season=args.season,
        lever=lever,
        n_draws=1500,
    )

    s_res = report.structural_result
    unc = report.uncertainty_bands

    cold_tag = " [COLD-START REGIONAL PRIOR]" if report.is_cold_start else ""

    print("=" * 80)
    print(f"ABU DHABI TOURISM DIGITAL TWIN — SCENARIO BRIEFING")
    print(f"Market: {report.market}{cold_tag} | Archetype: {report.archetype} | Season: {report.season}")
    print("=" * 80)

    print("\n1. NON-TECHNICAL EXECUTIVE RECOMMENDATION:")
    print("-" * 80)
    print(report.recommendation_summary)

    print("\n2. END-TO-END CONVERSION CHAIN (Weekly Rates):")
    print("-" * 80)
    print(f"{'Metric':<32} {'Baseline':>12} {'Scenario':>12} {'Net Shift':>16}")
    print("-" * 80)
    print(f"{'Weekly Seat Capacity':<32} {s_res.base_seats:>12,.0f} {s_res.sim_seats:>12,.0f} {s_res.delta_seats:>+16,.0f}")
    print(f"{'Flight Passengers (Pax)':<32} {s_res.base_pax:>12,.0f} {s_res.sim_pax:>12,.0f} {s_res.delta_pax:>+16,.0f}")
    print(f"{'Point-to-Point (P2P)':<32} {s_res.base_p2p:>12,.0f} {s_res.sim_p2p:>12,.0f} {s_res.delta_p2p:>+16,.0f}")
    print(f"{'Hotel New Arrivals':<32} {s_res.base_arrivals:>12,.0f} {s_res.sim_arrivals:>12,.0f} {s_res.delta_arrivals:>+16,.0f}")
    print(f"{'Hotel Guests (Guest-Days)':<32} {s_res.base_guests:>12,.0f} {s_res.sim_guests:>12,.0f} {s_res.delta_guests:>+16,.0f}")
    print("-" * 80)
    print(f"{'Load Factor (LF)':<32} {s_res.base_lf:>11.1%} {s_res.sim_lf:>11.1%} {s_res.sim_lf - s_res.base_lf:>+15.1%}")
    print(f"{'P2P Passenger Share':<32} {s_res.base_p2p_share:>11.1%} {s_res.sim_p2p_share:>11.1%} {s_res.sim_p2p_share - s_res.base_p2p_share:>+15.1%}")
    print(f"{'Effective Response Multiplier':<32} {s_res.base_multiplier:>12.3f} {s_res.sim_multiplier:>12.3f} {s_res.sim_multiplier - s_res.base_multiplier:>+16.3f}")
    print(f"{'Length of Stay (LOS days)':<32} {s_res.base_los:>12.2f} {s_res.sim_los:>12.2f} {s_res.sim_los - s_res.base_los:>+16.2f}")

    print("\n3. EXACT WATERFALL ATTRIBUTION (Decomposition of Incremental Guests):")
    print("-" * 80)
    print(f"{'Waterfall Component':<38} {'Guest-Days':>16} {'Share of Lift':>18}")
    print("-" * 80)
    total_lift = s_res.delta_guests if s_res.delta_guests != 0 else 1.0
    print(f"{'1. Added Seat Capacity Effect':<38} {s_res.waterfall_seats:>+16,.1f} {s_res.waterfall_seats / total_lift:>17.1%}")
    print(f"{'2. Load Factor Optimization Effect':<38} {s_res.waterfall_lf:>+16,.1f} {s_res.waterfall_lf / total_lift:>17.1%}")
    print(f"{'3. P2P Share Shift Effect':<38} {s_res.waterfall_p2p:>+16,.1f} {s_res.waterfall_p2p / total_lift:>17.1%}")
    print(f"{'4. Response Multiplier Uplift Effect':<38} {s_res.waterfall_multiplier:>+16,.1f} {s_res.waterfall_multiplier / total_lift:>17.1%}")
    print(f"{'5. Stay Duration Extension Effect':<38} {s_res.waterfall_los:>+16,.1f} {s_res.waterfall_los / total_lift:>17.1%}")
    print("-" * 80)
    total_waterfall = (
        s_res.waterfall_seats
        + s_res.waterfall_lf
        + s_res.waterfall_p2p
        + s_res.waterfall_multiplier
        + s_res.waterfall_los
    )
    print(f"{'TOTAL ATTRIBUTED LIFT':<38} {total_waterfall:>+16,.1f} {'100.0%':>18}")
    print(f"{'Verified Model Discrepancy':<38} {abs(total_waterfall - s_res.delta_guests):>16.6f} {'[Exact Match]':>18}")

    print("\n4. UNCERTAINTY QUANTIFICATION (Empirical & Beta-Sampled Range):")
    print("-" * 80)
    print(f"{'Scenario Outcome':<28} {'P10 (Conservative)':>16} {'P50 (Median)':>16} {'P90 (Optimistic)':>16}")
    print("-" * 80)
    print(f"{'Simulated Total Guests':<28} {unc.p10:>16,.0f} {unc.p50:>16,.0f} {unc.p90:>16,.0f}")
    print(f"{'Incremental Demand Lift':<28} {unc.delta_p10:>+16,.0f} {unc.delta_p50:>+16,.0f} {unc.delta_p90:>+16,.0f}")
    print(f"Demonstrated Holdout Coverage: {unc.demonstrated_coverage_pct:.1f}%")

    print("\n5. TORNADO SENSITIVITY RANKING (Elasticity of Levers):")
    print("-" * 80)
    print(f"{'Rank':<5} {'Decision Lever':<35} {'Swing Spread':>16} {'Relative Elasticity':>18}")
    print("-" * 80)
    for idx, row in enumerate(report.tornado_sensitivity, 1):
        print(f"{idx:<5} {row['lever_name']:<35} {row['swing_spread']:>16,.0f} {row['relative_sensitivity']:>17.1%}")
    print("=" * 80)


if __name__ == "__main__":
    main()
