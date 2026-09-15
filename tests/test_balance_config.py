import gc
import os
import tempfile
import unittest

from src.data.balance_config import BALANCE_REGISTRY, TIER_DOMINANCE, TIRE_CONFIGS
from src.database.career_db import CareerDatabase


class TestBalanceConfigAndDominance(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_balance.db")
        self.db = CareerDatabase(self.db_path)

    def tearDown(self):
        if hasattr(self, "db"):
            del self.db
        gc.collect()
        if hasattr(self, "temp_dir"):
            try:
                self.temp_dir.cleanup()
            except Exception:
                pass

    def test_tier_dominance_weights_scale_properly(self):
        """Tier 5 should have highest driver weight, Tier 1 should have highest car weight."""
        t5 = TIER_DOMINANCE[5]
        t1 = TIER_DOMINANCE[1]
        self.assertGreater(t5.driver_weight, 0.80)
        self.assertLess(t5.car_weight, 0.20)
        self.assertGreater(t1.car_weight, 0.80)
        self.assertLess(t1.driver_weight, 0.20)

    def test_database_balance_settings_table(self):
        """Ensures balance_settings table exists and holds valid JSON configurations."""
        settings = self.db.get_all_balance_settings()
        self.assertIn("economy", settings)
        self.assertIn("tier_dominance", settings)
        self.assertIn("pit", settings)

        # Test getter / setter
        val = self.db.get_balance_setting("pit")
        self.assertIsNotNone(val)
        self.assertIn("pit_lane_delta_seconds", val)

        # Update test
        self.db.set_balance_setting("custom_test_key", {"multiplier": 1.25})
        read_back = self.db.get_balance_setting("custom_test_key")
        self.assertEqual(read_back["multiplier"], 1.25)

    def test_tire_compounds_calibration(self):
        """Soft should have higher base grip than Medium and Hard."""
        soft = TIRE_CONFIGS["SOFT"]
        medium = TIRE_CONFIGS["MEDIUM"]
        hard = TIRE_CONFIGS["HARD"]
        self.assertGreater(soft.base_grip, medium.base_grip)
        self.assertGreater(medium.base_grip, hard.base_grip)
        self.assertGreater(soft.deg_per_lap, medium.deg_per_lap)
        self.assertGreater(medium.deg_per_lap, hard.deg_per_lap)

    def test_part_build_costs_scale_with_tier(self):
        """Tier 1 parts should cost significantly more than Tier 2 and Tier 3 parts."""
        t1_brakes = BALANCE_REGISTRY.get_part_build_cost(1, "BRAKES")
        t2_brakes = BALANCE_REGISTRY.get_part_build_cost(2, "BRAKES")
        t3_brakes = BALANCE_REGISTRY.get_part_build_cost(3, "BRAKES")
        self.assertGreater(t1_brakes, t2_brakes * 2.0)
        self.assertGreater(t2_brakes, t3_brakes * 2.0)
        # Tier 3 brakes should be affordable frequently (~$95k)
        self.assertLess(t3_brakes, 150_000.0)

    def test_pay_driver_income_tiers(self):
        """Pay drivers should provide strong financial relief in Tier 3 and Tier 2."""
        t3_income = BALANCE_REGISTRY.get_pay_driver_base_income(3)
        t2_income = BALANCE_REGISTRY.get_pay_driver_base_income(2)
        self.assertGreaterEqual(t3_income, 250_000.0)
        self.assertGreaterEqual(t2_income, 600_000.0)

    def test_facility_nodes_tier_pricing_gradient(self):
        """Facility nodes should have natural pricing jumps across T3, T2, and T1 brackets."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, base_cost, base_upkeep FROM facility_nodes;")
            nodes = {r[0]: (r[1], r[2]) for r in cur.fetchall()}

            # Tier 3 starter node
            t3_cost, t3_upk = nodes["eng_workshop"]
            self.assertLessEqual(t3_cost, 3_000_000.0)
            self.assertLessEqual(t3_upk, 100_000.0)

            # Tier 2 gateway
            t2_cost, t2_upk = nodes["eng_tuning"]
            self.assertGreater(t2_cost, 8_000_000.0)
            self.assertGreater(t2_upk, 200_000.0)

            # Tier 1 apex facility
            t1_cost, t1_upk = nodes["eng_windtunnel"]
            self.assertGreater(t1_cost, 30_000_000.0)
            self.assertGreater(t1_upk, 800_000.0)

    def test_feeder_seat_cost_ranges_and_youth_development(self):
        """Feeder seats in Tier 5 (Karting) and Tier 4 (Junior Single) must be accessible for parent constructors."""
        t5_min, t5_max = BALANCE_REGISTRY.get_feeder_seat_cost_range(5)
        t4_min, t4_max = BALANCE_REGISTRY.get_feeder_seat_cost_range(4)
        t3_budget = BALANCE_REGISTRY.get_starting_budget(3)

        # Tier 5 karting seat should be affordable ($20k-$100k)
        self.assertLessEqual(t5_min, 30_000.0)
        self.assertLessEqual(t5_max, 100_000.0)

        # Tier 4 junior seat should be accessible ($100k-$500k)
        self.assertLessEqual(t4_min, 120_000.0)
        self.assertLessEqual(t4_max, 500_000.0)

        # Combined cost for sponsoring both seats should take < 10% of a Tier 3 starting budget
        combined_cost = (t5_max + t4_max) / 2.0
        self.assertLess(combined_cost, t3_budget * 0.10)


if __name__ == "__main__":
    unittest.main()
