import os
import tempfile
import unittest

from src.core.car import Car
from src.core.driver import Driver
from src.core.race_control import RaceControl
from src.data.default_tracks import create_emerald_ring
from src.database.career_db import CareerDatabase
from src.database.db_manager import CarAttributes
from src.management.engineering_manager import EngineeringManager


class TestPartReliabilityAndBreakdown(unittest.TestCase):
    def setUp(self):
        self.circuit = create_emerald_ring()
        self.race_control = RaceControl()
        self.driver = Driver("Test Driver", 1, 80.0, 80.0, 80.0, 80.0, is_player=True)
        self.attrs = CarAttributes()

    def test_initial_part_durabilities_tier_scaled(self):
        """Verify tier-scaled initial baseline durabilities: Tier 3 = 65%, Tier 2 = 72%, Tier 1 = 80%."""
        car_t3 = Car(1, self.driver, self.attrs, league_tier=3)
        self.assertAlmostEqual(car_t3.part_durability["FRONT_WING"], 65.0)
        self.assertAlmostEqual(car_t3.part_durability["BRAKES"], 65.0)

        car_t2 = Car(2, self.driver, self.attrs, league_tier=2)
        self.assertAlmostEqual(car_t2.part_durability["FRONT_WING"], 72.0)

        car_t1 = Car(3, self.driver, self.attrs, league_tier=1)
        self.assertAlmostEqual(car_t1.part_durability["FRONT_WING"], 80.0)

    def test_custom_initial_durability_injection(self):
        """Verify custom durability values passed from previous races/database are properly assigned."""
        custom_durs = {
            "FRONT_WING": 40.0,
            "REAR_WING": 88.0,
            "BRAKES": 115.0,  # Uncapped custom R&D
            "ENGINE": 52.0,
            "SUSPENSION": 60.0,
            "FLOOR": 70.0,
        }
        car = Car(1, self.driver, self.attrs, league_tier=3, initial_part_durabilities=custom_durs)
        self.assertAlmostEqual(car.part_durability["FRONT_WING"], 40.0)
        self.assertAlmostEqual(car.part_durability["BRAKES"], 115.0)

    def test_terminal_mechanical_breakdown_at_zero(self):
        """Verify that when any component reaches <= 0.0%, catastrophic failure occurs and car retires."""
        car = Car(1, self.driver, self.attrs, league_tier=3)
        car.part_durability["ENGINE"] = 0.0
        car.speed = 40.0

        # Physics tick triggers terminal breakdown
        car.update_physics(0.1, self.circuit, self.race_control, 0.0, None, None)

        self.assertTrue(car.is_broken)
        self.assertTrue(car.is_dnf)
        self.assertEqual(car.speed, 0.0)
        self.assertEqual(car.mistake_event, "MECHANICAL_FAILURE")
        self.assertEqual(car.blunder_part_damaged, "ENGINE")

    def test_pit_front_wing_replacement_and_timing(self):
        """Verify front wing pit stop adds +4.0s and restores front wing durability to spare unit level."""
        car = Car(1, self.driver, self.attrs, league_tier=3)
        car.part_durability["FRONT_WING"] = 35.0

        # Order pit stop with front wing swap
        car.order_pit_stop(new_compound="HARD", replace_front_wing=True, front_wing_durability=95.0)
        self.assertTrue(car.box_this_lap)
        self.assertTrue(car.pit_replace_front_wing)
        self.assertEqual(car.pit_front_wing_durability, 95.0)

        # Trigger pit entry
        car.in_pit_lane = True
        car.pit_state = "APPROACH"
        car.pit_s = self.circuit.pit_length * self.circuit.pit_box_s - 1.0
        car.speed = 22.0
        car._update_pit_lane(0.1, self.circuit)

        self.assertEqual(car.pit_state, "IN_BOX")
        # Base stop is 2.4s + extra 4.0s for wing = >= 6.4s
        self.assertGreaterEqual(car.pit_timer, 6.4)

        # Simulate timer countdown in box
        car._update_pit_lane(car.pit_timer + 0.1, self.circuit)
        self.assertEqual(car.pit_state, "EXITING")
        self.assertAlmostEqual(car.part_durability["FRONT_WING"], 95.0)
        self.assertFalse(car.pit_replace_front_wing)

    def test_pit_emergency_repairs(self):
        """Verify emergency repairs adds +14.0s and brings worn parts (<55%) back up to 55-60%."""
        car = Car(1, self.driver, self.attrs, league_tier=3)
        car.part_durability["BRAKES"] = 28.0
        car.part_durability["SUSPENSION"] = 42.0
        car.part_durability["REAR_WING"] = 80.0

        car.order_pit_stop(new_compound="MEDIUM", emergency_repairs=True)
        self.assertTrue(car.pit_emergency_repairs)

        # In box trigger
        car.in_pit_lane = True
        car.pit_state = "APPROACH"
        car.pit_s = self.circuit.pit_length * self.circuit.pit_box_s - 1.0
        car.speed = 22.0
        car._update_pit_lane(0.1, self.circuit)

        # Base stop 2.4s + 14.0s = >= 16.4s
        self.assertGreaterEqual(car.pit_timer, 16.4)

        # Finish stop
        car._update_pit_lane(car.pit_timer + 0.1, self.circuit)
        self.assertGreaterEqual(car.part_durability["BRAKES"], 55.0)
        self.assertLessEqual(car.part_durability["BRAKES"], 60.0)
        self.assertGreaterEqual(car.part_durability["SUSPENSION"], 55.0)
        # Part above 55% was unaffected
        self.assertAlmostEqual(car.part_durability["REAR_WING"], 80.0)
        self.assertFalse(car.pit_emergency_repairs)

    def test_database_persistence_and_factory_purchases(self):
        """Verify durability persistence, warehouse inventory, and factory part purchases in CareerDatabase."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_db = f.name

        try:
            db = CareerDatabase(temp_db)
            db.create_new_career("Test Racing", "#FF0000", "NORMAL", "Vortex EcoTech")
            team = db.get_player_team()
            team_id = team["id"]

            # Check warehouse components seeded (spare front wing and spare brakes in warehouse car_slot=0)
            spares = db.get_team_warehouse_components(team_id, "FRONT_WING")
            self.assertGreaterEqual(len(spares), 1)
            self.assertEqual(spares[0]["car_slot"], 0)

            # Test updating and persisting car durabilities
            new_durs = {
                "FRONT_WING": 40.0,
                "REAR_WING": 55.0,
                "BRAKES": 62.0,
                "ENGINE": 70.0,
                "SUSPENSION": 58.0,
                "FLOOR": 65.0,
            }
            db.save_car_part_durabilities(team_id, car_slot=1, durabilities=new_durs)

            comps = db.get_team_components(team_id)
            c1_fw = [c for c in comps if c["car_slot"] == 1 and c["category"] == "FRONT_WING"][0]
            self.assertAlmostEqual(c1_fw["current_durability"], 40.0)
            self.assertAlmostEqual(c1_fw["wear_pct"], 60.0)

            # Test buying a factory part
            em = EngineeringManager(db)
            success, msg = em.buy_factory_part(team_id, "REAR_WING", target_car_slot=1)
            self.assertTrue(success)

            # Check mounted part updated
            comps = db.get_team_components(team_id)
            c1_rw = [c for c in comps if c["car_slot"] == 1 and c["category"] == "REAR_WING"][0]
            self.assertAlmostEqual(c1_rw["current_durability"], 65.0)

            # Test building part with uncapped durability
            # First unlock/build facility for FRONT_WING ('eng_wings_front')
            with db.get_connection() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO team_facilities (team_id, node_id, current_tier, is_unlocked, monthly_sub_budget) VALUES (?, 'eng_wings_front', 1, 1, 20000);",
                    (team_id,),
                )
                conn.commit()

            b_success, b_msg, _ = em.build_next_generation_part(team_id, c1_fw["id"])
            self.assertTrue(b_success)
            comps = db.get_team_components(team_id)
            c1_fw_new = [c for c in comps if c["id"] == c1_fw["id"]][0]
            self.assertEqual(c1_fw_new["generation"], 2)
            self.assertGreaterEqual(c1_fw_new["max_durability"], 65.0)
            self.assertAlmostEqual(c1_fw_new["current_durability"], c1_fw_new["max_durability"])

        finally:
            if os.path.exists(temp_db):
                try:
                    os.remove(temp_db)
                except Exception:
                    pass


if __name__ == "__main__":
    unittest.main()
