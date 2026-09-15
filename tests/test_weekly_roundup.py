import gc
import os
import tempfile
import unittest

import pygame

from src.database.career_db import CareerDatabase
from src.management.game_manager import GameManager
from src.ui.management_hub.management_hub import ManagementHub
from src.ui.management_hub.weekly_roundup_modal import WeeklyRoundupModal


class TestWeeklyRoundup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.db_path = os.path.join(cls.temp_dir.name, "test_career.db")
        cls.db = CareerDatabase(cls.db_path)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "db"):
            del cls.db
        gc.collect()
        if hasattr(cls, "temp_dir"):
            try:
                cls.temp_dir.cleanup()
            except Exception:
                pass
        pygame.quit()

    def test_new_career_has_no_season_1_race_results(self):
        """At start of season 1, series_race_results must have 0 rows for season 1."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM series_race_results WHERE season_num = 1;")
            count = cur.fetchone()[0]
            self.assertEqual(count, 0, "New career must have 0 series_race_results for Season 1.")

        results_week_1 = self.db.get_weekly_race_results(1)
        self.assertEqual(results_week_1, {}, "get_weekly_race_results(1) should be empty before race 1.")

    def test_create_new_career_clears_series_race_results(self):
        """create_new_career must reset series_race_results so old career results don't leak into new career."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT INTO series_race_results (
                tier, round_num, week, track_name, position, driver_name,
                team_name, team_id, driver_id, is_academy_driver, is_player, points, season_num
            ) VALUES (3, 1, 1, 'Emerald Ring', 1, 'Dummy Driver', 'Dummy Team', 1, 1, 0, 0, 25, 1);
            """)
            conn.commit()

        self.db.create_new_career("Test Team", "#00FF00")
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM series_race_results WHERE season_num = 1;")
            self.assertEqual(cur.fetchone()[0], 0, "create_new_career must purge series_race_results for Season 1.")

    def test_orphaned_results_purged_when_no_races_completed(self):
        """If orphaned rows exist for current season while calendar has 0 completed races, init_schema purges them."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT INTO series_race_results (
                tier, round_num, week, track_name, position, driver_name,
                team_name, team_id, driver_id, is_academy_driver, is_player, points, season_num
            ) VALUES (1, 1, 1, 'Emerald Ring', 1, 'Ghost Driver', 'Ghost Team', 1, 1, 0, 0, 25, 1);
            """)
            conn.commit()

        self.db.init_schema()
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM series_race_results WHERE season_num = 1;")
            self.assertEqual(
                cur.fetchone()[0], 0, "init_schema must purge orphaned race results for uncompleted season."
            )

    def test_modal_season_opener_state(self):
        """WeeklyRoundupModal handles is_season_start state cleanly without displaying fake tier results."""
        modal = WeeklyRoundupModal(1024, 768)
        summary = {
            "week": 1,
            "is_season_start": True,
            "tiers_simulated": [],
            "results_by_tier": {},
            "academy_highlights": [],
        }
        modal.open(summary)
        self.assertTrue(modal.is_open)

        surf = pygame.Surface((1024, 768))
        modal.render(surf)

        modal_w = min(820, 1024 - 60)
        modal_h = min(540, 768 - 60)
        modal_x = (1024 - modal_w) // 2
        modal_y = (768 - modal_h) // 2
        dismiss_click_x = modal_x + modal_w - 100
        dismiss_click_y = modal_y + modal_h - 25
        clicked = modal.handle_click(dismiss_click_x, dismiss_click_y)
        self.assertTrue(clicked)
        self.assertFalse(modal.is_open)

    def test_management_hub_roundup_trigger_at_season_start(self):
        """ManagementHub._handle_open_roundup_trigger at Week 1 with no races opens season opener state."""
        hub = ManagementHub(1024, 768, on_start_race_weekend=lambda ev: None, on_switch_mode=lambda m: None)
        hub.db = self.db
        hub.gm = GameManager(self.db)
        hub.last_roundup_summary = {}

        hub._handle_open_roundup_trigger()
        self.assertTrue(hub.roundup_modal.is_open)
        self.assertTrue(hub.roundup_modal.summary_data.get("is_season_start"))
        self.assertEqual(hub.roundup_modal.summary_data.get("results_by_tier"), {})

        # Clean up hub references
        del hub
        gc.collect()


if __name__ == "__main__":
    unittest.main()
