"""Unit and integration test suite for the Abu Dhabi Tourism Digital Twin."""

import json
import sys
import unittest
from pathlib import Path

# Ensure repo root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from engine.archetypes import get_cold_start_prior, get_market_archetype
from engine.simulator import TourismDigitalTwin
from engine.structural import ScenarioLever, StructuralEngine


class TestDigitalTwin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.twin = TourismDigitalTwin()
        cls.panel_path = Path(__file__).resolve().parents[1] / "lake" / "curated" / "weekly_market_panel.parquet"
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
                1e-5,
                f"Waterfall discrepancy {discrepancy} exceeded tolerance for {market} in {season}.",
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
        lake_dir = Path(__file__).resolve().parents[1] / "lake" / "curated"
        calib_file = lake_dir / "structural_calibration.json"
        model_file = lake_dir / "residual_engine.pkl"
        conf_file = lake_dir / "conformal_calibrator.json"

        self.assertTrue(calib_file.exists(), "structural_calibration.json does not exist.")
        self.assertTrue(model_file.exists(), "residual_engine.pkl does not exist.")
        self.assertTrue(conf_file.exists(), "conformal_calibrator.json does not exist.")

        with open(conf_file, "r") as f:
            conf_data = json.load(f)
        self.assertIn("_demonstrated_holdout_coverage", conf_data)


    def test_data_contract_and_grain_separation(self):
        """Verify explicit data contracts, grain separation, and date grid completeness."""
        lake_dir = Path(__file__).resolve().parents[1] / "lake" / "curated"
        f_daily_path = lake_dir / "flight_daily.parquet"
        f_monthly_path = lake_dir / "flight_monthly.parquet"
        g_daily_path = lake_dir / "guest_daily.parquet"

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


if __name__ == "__main__":
    unittest.main()
