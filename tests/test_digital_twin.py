"""Unit and integration test suite for the Abu Dhabi Tourism Digital Twin."""

import json
import unittest

import numpy as np
import pandas as pd

from engine.archetypes import get_cold_start_prior, get_market_archetype
from engine.config import SETTINGS
from engine.simulator import TourismDigitalTwin
from engine.structural import ScenarioLever, StructuralEngine


class TestDigitalTwin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.twin = TourismDigitalTwin()
        cls.panel_path = SETTINGS.panel_path
        cls.df_panel = pd.read_parquet(cls.panel_path)

    def test_panel_integrity(self):
        """Verify panel has no duplicate dates per market and strict week integrity."""
        # Check markets count
        markets = self.df_panel["market"].unique()
        self.assertGreaterEqual(len(markets), 17)
        self.assertIn("DOMESTIC", markets)
        self.assertIn("UNITED KINGDOM", markets)
        self.assertIn("INDIA", markets)

        # Check complete weeks have exactly 7 days
        complete_weeks = self.df_panel[self.df_panel["is_complete_week"] == 1]
        self.assertTrue((complete_weeks["days_in_week"] == 7).all())

        # Check no duplicates on (week_start, market, dataset_split)
        dups = self.df_panel.duplicated(subset=["week_start", "market", "dataset_split"])
        self.assertEqual(dups.sum(), 0, "Found duplicate records in weekly market panel.")

    def test_waterfall_exact_identity(self):
        """Verify that waterfall components sum exactly to delta_guests (zero discrepancy)."""
        test_cases = [
            ("UNITED KINGDOM", "Winter_Peak", ScenarioLever("UNITED KINGDOM", delta_frequency=2.0, aircraft_gauge=290.0, delta_load_factor=0.02)),
            ("INDIA", "Summer_Trough", ScenarioLever("INDIA", delta_seats_pct=0.15, delta_p2p_share=0.03)),
            ("GERMANY", "Spring_Shoulder", ScenarioLever("GERMANY", delta_multiplier_pct=0.05, delta_los=0.4)),
            ("SAUDI ARABIA", "Autumn_Shoulder", ScenarioLever("SAUDI ARABIA", delta_frequency=1.0, aircraft_gauge=180.0)),
        ]

        for market, season, lever in test_cases:
            res = self.twin.structural_engine.simulate(market, season, lever)
            waterfall_sum = (
                res.waterfall_seats
                + res.waterfall_lf
                + res.waterfall_p2p
                + res.waterfall_multiplier
                + res.waterfall_los
            )
            discrepancy = abs(waterfall_sum - res.delta_guests)
            self.assertLess(
                discrepancy,
                1e-9,
                f"Waterfall discrepancy {discrepancy:.3e} exceeded 1e-9 tolerance for {market} in {season}.",
            )

    def test_monotonicity_guarantee(self):
        """Verify that increasing flight capacity strictly produces non-negative hotel demand changes."""
        markets = ["UNITED KINGDOM", "INDIA", "GERMANY", "SAUDI ARABIA", "CHINA"]
        for m in markets:
            # Positive seat increase
            pos_lever = ScenarioLever(m, delta_frequency=2.0, aircraft_gauge=250.0)
            res_pos = self.twin.run_scenario(m, "Winter_Peak", pos_lever)
            self.assertGreaterEqual(
                res_pos.structural_result.delta_guests,
                0.0,
                f"Monotonicity violation: positive capacity produced negative structural guests for {m}.",
            )
            self.assertGreaterEqual(
                res_pos.hybrid_result["hybrid_delta"],
                -1e-6,
                f"Monotonicity violation: positive capacity produced negative hybrid guests for {m}.",
            )

    def test_cold_start_fallback(self):
        """Verify unmodeled countries resolve to regional archetypes and compute valid responses."""
        unmodeled_countries = ["SWEDEN", "BRAZIL", "NORWAY", "PAKISTAN"]
        for country in unmodeled_countries:
            lever = ScenarioLever(country, delta_frequency=1.0, aircraft_gauge=200.0)
            report = self.twin.run_scenario(country, "Winter_Peak", lever)
            self.assertTrue(report.is_cold_start)
            self.assertGreater(report.structural_result.sim_guests, 0.0)
            self.assertGreater(report.uncertainty_bands.delta_p50, 0.0)

    def test_deterministic_artifacts(self):
        """Verify saved model artifacts and conformal calibrator exist and load cleanly."""
        calib_file = SETTINGS.calibration_path
        model_file = SETTINGS.residual_model_path
        conf_file = SETTINGS.conformal_path

        self.assertTrue(calib_file.exists(), "structural_calibration.json does not exist.")
        self.assertTrue(model_file.exists(), "residual_engine.pkl does not exist.")
        self.assertTrue(conf_file.exists(), "conformal_calibrator.json does not exist.")

        with open(conf_file, "r") as f:
            conf_data = json.load(f)
        self.assertIn("_demonstrated_holdout_coverage", conf_data)


    def test_data_contract_and_grain_separation(self):
        """Verify explicit data contracts, grain separation, and date grid completeness."""
        f_daily_path = SETTINGS.flight_daily_path
        f_monthly_path = SETTINGS.flight_monthly_path
        g_daily_path = SETTINGS.guest_daily_path

        self.assertTrue(f_daily_path.exists())
        self.assertTrue(f_monthly_path.exists())
        self.assertTrue(g_daily_path.exists())

        f_daily = pd.read_parquet(f_daily_path)
        f_monthly = pd.read_parquet(f_monthly_path)
        g_daily = pd.read_parquet(g_daily_path)

        # 1. Flight daily is strictly daily from 2023 onward
        self.assertTrue((f_daily["source_grain"] == "daily").all())
        self.assertGreaterEqual(pd.to_datetime(f_daily["date"]).min(), pd.to_datetime("2023-01-01"))

        # 2. Flight monthly isolates 2022 monthly data
        self.assertTrue((f_monthly["source_grain"] == "monthly").all())
        self.assertEqual(pd.to_datetime(f_monthly["date"]).max().year, 2022)

        # 3. Guest data includes contract columns
        for col in ["is_source_present", "target_available", "is_suppressed_arrival", "source_grain"]:
            self.assertIn(col, g_daily.columns)

        # 4. Total grid records (1520 dates x 45 intl nationalities + 1520 domestic)
        self.assertEqual(len(g_daily), 69920)

    def test_top15_includes_philippines_and_archetype(self):
        """Verify Philippines is promoted to Top 15 (rank 14 by volume) and Armenia is reassigned to regional priors."""
        from engine.archetypes import TOP_15_INTERNATIONAL_MARKETS, MarketArchetype
        self.assertIn("PHILIPPINES", TOP_15_INTERNATIONAL_MARKETS)
        self.assertNotIn("ARMENIA", TOP_15_INTERNATIONAL_MARKETS)
        self.assertEqual(get_market_archetype("PHILIPPINES"), MarketArchetype.RESIDENT_VFR)
        self.assertIn("PHILIPPINES", self.df_panel["market"].unique())

    def test_load_factor_outliers_preserved_and_flagged(self):
        """Verify raw load factors > 100% are preserved with quality flags rather than silently clipped."""
        self.assertIn("load_factor_raw", self.df_panel.columns)
        self.assertIn("is_load_factor_outlier", self.df_panel.columns)
        self.assertIn("load_factor", self.df_panel.columns)

        # Raw maximum should exceed 1.0
        self.assertGreater(self.df_panel["load_factor_raw"].max(), 1.0)
        # Modeling version should be clipped to 1.0
        self.assertLessEqual(self.df_panel["load_factor"].max(), 1.0)
        # Quality flag should mark all instances > 1.0
        outlier_count = (self.df_panel["is_load_factor_outlier"] == 1).sum()
        self.assertGreater(outlier_count, 0)

    def test_domestic_domain_decoupling(self):
        """Verify domestic staycation model ignores aviation levers and preserves waterfall identity."""
        lever_with_flights = ScenarioLever(
            market="DOMESTIC",
            delta_frequency=5.0,
            aircraft_gauge=300.0,
            delta_load_factor=0.05,
            delta_multiplier_pct=0.10,
            delta_los=0.2,
        )
        res = self.twin.structural_engine.simulate("DOMESTIC", "Winter_Peak", lever_with_flights)

        # Flight levers must not produce seats or pax
        self.assertEqual(res.base_seats, 0.0)
        self.assertEqual(res.sim_seats, 0.0)
        self.assertEqual(res.waterfall_seats, 0.0)
        self.assertEqual(res.waterfall_lf, 0.0)
        self.assertEqual(res.waterfall_p2p, 0.0)

        # Shifts must be driven by multiplier and stay duration
        self.assertGreater(res.waterfall_multiplier, 0.0)
        self.assertGreater(res.waterfall_los, 0.0)

        # Exact waterfall identity
        discrepancy = abs(
            (res.waterfall_seats + res.waterfall_lf + res.waterfall_p2p + res.waterfall_multiplier + res.waterfall_los)
            - res.delta_guests
        )
        self.assertLess(discrepancy, 1e-5)

    def test_route_closure_demand_loss_and_waterfall(self):
        """Verify that discontinuing an aviation route yields 100% demand loss and exact waterfall reconciliation."""
        test_markets = ["UNITED KINGDOM", "GERMANY", "INDIA"]
        for m in test_markets:
            lever_close = ScenarioLever(market=m, delta_seats_pct=-1.0)
            res = self.twin.structural_engine.simulate(m, "Winter_Peak", lever_close)

            # Simulated seats, pax, p2p, arrivals, and guests must strictly be 0
            self.assertEqual(res.sim_seats, 0.0)
            self.assertEqual(res.sim_pax, 0.0)
            self.assertEqual(res.sim_p2p, 0.0)
            self.assertEqual(res.sim_arrivals, 0.0)
            self.assertEqual(res.sim_guests, 0.0)

            # Net impact must equal negative baseline
            self.assertAlmostEqual(res.delta_guests, -res.base_guests, places=4)

            # Waterfall seats component must account for the full loss, others 0
            self.assertAlmostEqual(res.waterfall_seats, -res.base_guests, places=4)
            self.assertEqual(res.waterfall_lf, 0.0)
            self.assertEqual(res.waterfall_p2p, 0.0)
            self.assertEqual(res.waterfall_multiplier, 0.0)
            self.assertEqual(res.waterfall_los, 0.0)

            # Exact reconciliation
            wf_sum = res.waterfall_seats + res.waterfall_lf + res.waterfall_p2p + res.waterfall_multiplier + res.waterfall_los
            self.assertAlmostEqual(wf_sum, res.delta_guests, places=6)

    def test_zero_lever_invariance_across_all_markets(self):
        """Verify zero-lever scenario strictly preserves baseline across all 21 unified markets and 4 seasons (84 tests)."""
        markets = self.df_panel["market"].unique()
        seasons = ["Winter_Peak", "Spring_Shoulder", "Summer_Trough", "Autumn_Shoulder"]

        for m in markets:
            for s in seasons:
                res = self.twin.structural_engine.simulate(m, s, ScenarioLever(market=m))
                self.assertAlmostEqual(
                    res.delta_guests,
                    0.0,
                    places=5,
                    msg=f"Zero-lever invariant failed for {m} in {s}: delta_guests was {res.delta_guests}",
                )
                self.assertAlmostEqual(
                    res.sim_guests,
                    res.base_guests,
                    places=5,
                    msg=f"Base vs sim mismatch for {m} in {s}",
                )
                self.assertAlmostEqual(res.waterfall_seats, 0.0, places=5)
                self.assertAlmostEqual(res.waterfall_lf, 0.0, places=5)
                self.assertAlmostEqual(res.waterfall_p2p, 0.0, places=5)
                self.assertAlmostEqual(res.waterfall_multiplier, 0.0, places=5)
                self.assertAlmostEqual(res.waterfall_los, 0.0, places=5)

    def test_deterministic_uncertainty_requests(self):
        """Verify identical simulation calls produce identical uncertainty values (no RNG state drift)."""
        res1 = self.twin.uncertainty_engine.run_monte_carlo("UNITED KINGDOM", "Winter_Peak", ScenarioLever("UNITED KINGDOM", delta_frequency=2))
        res2 = self.twin.uncertainty_engine.run_monte_carlo("UNITED KINGDOM", "Winter_Peak", ScenarioLever("UNITED KINGDOM", delta_frequency=2))

        self.assertEqual(res1.p10, res2.p10)
        self.assertEqual(res1.p90, res2.p90)
        self.assertEqual(res1.delta_p10, res2.delta_p10)
        self.assertEqual(res1.delta_p90, res2.delta_p90)
        self.assertEqual(res1.demonstrated_coverage_pct, res2.demonstrated_coverage_pct)

    def test_cold_start_tornado_sensitivity(self):
        """Verify unserved cold-start markets evaluate non-zero sensitivity around benchmark reference route."""
        report = self.twin.run_scenario("SWEDEN", "Winter_Peak", ScenarioLever("SWEDEN", delta_frequency=0))
        tornado = report.tornado_sensitivity

        self.assertGreater(len(tornado), 0)
        self.assertGreater(tornado[0]["swing_spread"], 0.0, "Cold-start swing spread should not be zero.")
        self.assertIn("influential driver", report.recommendation_summary)

    def test_api_validation_and_hybrid_exposure(self):
        """Verify API returns 400 for invalid seasons and exposes the hybrid model in the response."""
        from app.server import DigitalTwinHandler

        class MockHandler:
            def __init__(self):
                self.response = None
                self.status = None
            def send_json(self, data, status=200):
                self.response = data
                self.status = status

        handler = MockHandler()
        # Invalid season
        DigitalTwinHandler.handle_simulate(handler, {"market": ["UNITED KINGDOM"], "season": ["InvalidSeason"]})
        self.assertEqual(handler.status, 400)
        self.assertIn("Invalid season", handler.response["error"])

        # Valid request exposes hybrid model
        DigitalTwinHandler.handle_simulate(handler, {"market": ["UNITED KINGDOM"], "season": ["Winter_Peak"], "delta_freq": [2]})
        self.assertEqual(handler.status, 200)
        self.assertIn("hybrid", handler.response)
        self.assertIn("residual_adjustment", handler.response["hybrid"])
        self.assertIn("is_monotonic", handler.response["hybrid"])


if __name__ == "__main__":
    unittest.main()

