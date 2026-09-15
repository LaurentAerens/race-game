import os
import tempfile
import unittest

from src.data.teams import load_career_teams_and_drivers
from src.database.career_db import CareerDatabase
from src.management.engineering_manager import EngineeringManager
from src.management.game_manager import GameManager


class TestNextGenRegulations(unittest.TestCase):
    def setUp(self):
        self.tmp_db_fd, self.tmp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.tmp_db_fd)
        self.db = CareerDatabase(self.tmp_db_path)
        self.em = EngineeringManager(self.db)
        self.gm = GameManager(self.db)
        self.team_id = self.gm.team_id  # Player team (Tier 3)

    def tearDown(self):
        del self.gm
        del self.em
        del self.db
        import gc

        gc.collect()
        try:
            if os.path.exists(self.tmp_db_path):
                os.remove(self.tmp_db_path)
        except Exception:
            pass

    def test_schema_and_allocation(self):
        """Verify new columns exist and allocation slider updates properly."""
        status = self.em.get_team_next_gen_status(self.team_id)
        self.assertIn("allocation_pct", status)
        self.assertEqual(status["allocation_pct"], 0.0)

        success, msg = self.em.set_next_gen_allocation(self.team_id, 50.0)
        self.assertTrue(success)
        status = self.em.get_team_next_gen_status(self.team_id)
        self.assertEqual(status["allocation_pct"], 50.0)

        # Clamped test
        self.em.set_next_gen_allocation(self.team_id, 120.0)
        status = self.em.get_team_next_gen_status(self.team_id)
        self.assertEqual(status["allocation_pct"], 80.0)

    def test_weekly_progression_and_telemetry_dampening(self):
        """Verify points accumulate weekly and telemetry knowledge is dampened by allocation %."""
        self.em.set_next_gen_allocation(self.team_id, 50.0)
        res = self.em.process_weekly_next_gen_rnd(self.team_id, current_week=10)
        self.assertGreater(res["points_added"], 0.0)
        self.assertGreater(res["total_points"], 0.0)

        # Check telemetry dampening
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, knowledge_max FROM car_components WHERE team_id = ? AND car_slot = 1 LIMIT 1;",
                (self.team_id,),
            )
            comp = cur.fetchone()
            initial_k = comp["knowledge_max"]

        self.em.process_post_race_telemetry(self.team_id, driver_tech_skill=80.0, driver_comm_skill=80.0)

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT knowledge_max FROM car_components WHERE id = ?;", (comp["id"],))
            new_k = cur.fetchone()[0]

        self.assertGreater(new_k, initial_k)

    def test_week_9_regulations_evaluation(self):
        """Verify parity detection, safety ceilings, and mandatory cycles."""
        # Case 1: Normal parity -> STATUS_QUO
        reg = self.em.evaluate_season_regulations(tier=3, current_week=9, season_num=1)
        self.assertEqual(reg["upcoming_package"], "STATUS_QUO")
        self.assertTrue(reg["is_announced"])

        # Case 2: Runaway Points (>35% lead)
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE teams SET points = 100 WHERE id = ?;", (self.team_id,))
            cur.execute("UPDATE season_regulations SET is_announced = 0 WHERE tier = 3 AND season_num = 2;")
            conn.commit()

        reg2 = self.em.evaluate_season_regulations(tier=3, current_week=9, season_num=2)
        self.assertIn(
            reg2["upcoming_package"], ["AERO_SHAKEUP", "MECHANICAL_TWEAKS", "POWERTRAIN_DIRECTIVE", "MAJOR_OVERHAUL"]
        )

        # Case 3: Tier 3 Performance Ceiling (> 3000 total score)
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE car_components SET performance = 600.0 WHERE team_id = ?;", (self.team_id,))
            cur.execute("UPDATE season_regulations SET is_announced = 0 WHERE tier = 3 AND season_num = 3;")
            conn.commit()

        reg3 = self.em.evaluate_season_regulations(tier=3, current_week=9, season_num=3)
        self.assertEqual(reg3["upcoming_package"], "MAJOR_OVERHAUL")

        # Case 4: Mandatory Cycle (Tier 3 = 5 seasons)
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            # Reset performance to baseline
            cur.execute("UPDATE car_components SET performance = 75.0 WHERE team_id = ?;", (self.team_id,))
            cur.execute("UPDATE teams SET points = 10 WHERE tier = 3;")
            cur.execute("""
            INSERT OR REPLACE INTO season_regulations (season_num, tier, consecutive_stable_seasons, is_announced, upcoming_package)
            VALUES (4, 3, 5, 0, 'STATUS_QUO');
            """)
            conn.commit()

        reg4 = self.em.evaluate_season_regulations(tier=3, current_week=9, season_num=4)
        self.assertIn(
            reg4["upcoming_package"], ["MECHANICAL_TWEAKS", "AERO_SHAKEUP", "POWERTRAIN_DIRECTIVE", "MAJOR_OVERHAUL"]
        )

    def test_in_season_port_back_upgrade(self):
        """Verify port-back upgrades: 2/3 boost, 2-week cooldown, 3-week rel bonus."""
        # Accumulate some points
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE teams SET next_gen_rnd_points = 50000.0, chassis_perf_boost = 0.0, chassis_rel_boost = 0.0 WHERE id = ?;",
                (self.team_id,),
            )
            cur.execute(
                "INSERT OR REPLACE INTO season_regulations (season_num, tier, is_announced, upcoming_package, port_back_used) VALUES (1, 3, 1, 'STATUS_QUO', 0);"
            )
            conn.commit()

        # Try too early (week 10)
        success, msg = self.em.execute_port_back_upgrade(self.team_id, current_week=10)
        self.assertFalse(success)

        # Successful port-back at week 14
        success, msg = self.em.execute_port_back_upgrade(self.team_id, current_week=14)
        self.assertTrue(success)

        status = self.em.get_team_next_gen_status(self.team_id)
        # 50,000 pts / 25000 = 2.0 projected perf boost -> 2/3 = 1.3
        self.assertAlmostEqual(status["active_chassis_perf_boost"], 1.3, delta=0.1)
        self.assertEqual(status["port_back_cooldown_weeks"], 2)
        self.assertEqual(status["port_back_bonus_weeks"], 3)

        # Process weekly cycle during cooldown (week 1): 0 points added
        w1 = self.em.process_weekly_next_gen_rnd(self.team_id, current_week=15)
        self.assertEqual(w1["points_added"], 0.0)
        self.assertEqual(w1["cooldown_left"], 1)

        # Process weekly cycle during cooldown (week 2): 0 points added
        w2 = self.em.process_weekly_next_gen_rnd(self.team_id, current_week=16)
        self.assertEqual(w2["points_added"], 0.0)
        self.assertEqual(w2["cooldown_left"], 0)

        # Process weekly cycle post-cooldown (week 3): bonus reliability applied!
        w3 = self.em.process_weekly_next_gen_rnd(self.team_id, current_week=17)
        self.assertGreater(w3["bonus_rel_applied"], 0.0)

    def test_season_rollover_resets_and_boosts(self):
        """Verify season rollover: rule changes wipe prior chassis boosts, reset affected parts, and elevate spec parts."""
        # Set team with custom parts and accumulated points
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE teams SET next_gen_rnd_points = 75000.0, chassis_perf_boost = 5.0 WHERE id = ?;",
                (self.team_id,),
            )
            cur.execute(
                "UPDATE car_components SET performance = 120.0, generation = 3 WHERE team_id = ? AND category = 'FRONT_WING';",
                (self.team_id,),
            )
            cur.execute(
                "UPDATE car_components SET performance = 110.0, generation = 2 WHERE team_id = ? AND category = 'BRAKES';",
                (self.team_id,),
            )
            cur.execute(
                "INSERT OR REPLACE INTO season_regulations (season_num, tier, upcoming_package) VALUES (1, 3, 'AERO_SHAKEUP');"
            )
            conn.commit()

        rollover = self.em.apply_season_rollover_regulations(tier=3, season_num=1)
        self.assertTrue(rollover["is_rule_change"])

        # Check that FRONT_WING reset to base spec (66.0 for Tier 3 Mk 1)
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT performance, generation FROM car_components WHERE team_id = ? AND category = 'FRONT_WING' AND car_slot = 1;",
                (self.team_id,),
            )
            fw = cur.fetchone()
            self.assertEqual(fw["generation"], 1)
            self.assertEqual(fw["performance"], 66.0)

            # BRAKES was NOT in Aero Shakeup -> preserves custom performance (110.0)
            cur.execute(
                "SELECT performance, generation FROM car_components WHERE team_id = ? AND category = 'BRAKES' AND car_slot = 1;",
                (self.team_id,),
            )
            brk = cur.fetchone()
            self.assertEqual(brk["generation"], 2)
            self.assertEqual(brk["performance"], 110.0)

            # Non-Status Quo wipes prior chassis boost (5.0 wiped), only newly earned (75000/25000 = 3.0) applied
            cur.execute(
                "SELECT chassis_perf_boost, chassis_tire_preservation_base FROM teams WHERE id = ?;", (self.team_id,)
            )
            t_row = cur.fetchone()
            self.assertAlmostEqual(t_row["chassis_perf_boost"], 3.0, delta=0.1)
            self.assertGreater(t_row["chassis_tire_preservation_base"], 85.0)

        # Test teams.py CarAttributes uplift: all mounted parts, even spec ones, inherit chassis_perf_boost!
        results = load_career_teams_and_drivers(career_db=self.db, tier=3)
        player_driver, player_car_attrs = next((d, c) for d, c in results if d.is_player)
        # Brakes score should include 110.0 + 3.0 = 113.0
        self.assertAlmostEqual(player_car_attrs.braking_efficiency, 113.0, delta=0.2)


if __name__ == "__main__":
    unittest.main()
