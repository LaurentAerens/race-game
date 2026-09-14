import gc
import os
import tempfile
import unittest

import pygame

from src.database.career_db import CareerDatabase
from src.management.driver_manager import DriverManager
from src.management.game_manager import GameManager
from src.ui.management_hub.tab_database_explorer import DatabaseExplorerTab


class TestDatabaseExplorer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.test_db_path = os.path.join(cls.temp_dir.name, "test_database_explorer.db")
        cls.cdb = CareerDatabase(cls.test_db_path)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "cdb"):
            del cls.cdb
        gc.collect()
        if hasattr(cls, "temp_dir"):
            try:
                cls.temp_dir.cleanup()
            except Exception:
                pass

    def test_schema_and_migrations(self):
        """Verify new tables and columns exist in the database."""
        with self.cdb.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(series_race_results);")
            cols = [r[1] for r in cur.fetchall()]
            self.assertIn("season_num", cols, "series_race_results must include season_num column")

            cur.execute("SELECT COUNT(*) FROM driver_season_history;")
            dsh_cnt = cur.fetchone()[0]
            self.assertGreater(dsh_cnt, 0, "driver_season_history should be populated with historical seasons")

            cur.execute("SELECT COUNT(*) FROM team_alumni;")
            alumni_cnt = cur.fetchone()[0]
            self.assertGreaterEqual(alumni_cnt, 1, "team_alumni table should exist and have seeded alumni record")

    def test_historical_seasons_availability(self):
        """Verify multi-year seasons are available and ordered from newest to oldest."""
        seasons = self.cdb.get_available_seasons()
        self.assertGreaterEqual(len(seasons), 3, "At least 3 seasons (-1, 0, 1) should be available")
        season_nums = [s["season_num"] for s in seasons]
        self.assertIn(1, season_nums, "Current season 1 should be available")
        self.assertIn(0, season_nums, "Historical season 0 (2025) should be available")
        self.assertIn(-1, season_nums, "Historical season -1 (2024) should be available")
        self.assertTrue(seasons[0]["is_current"], "Newest active season should be marked current")

    def test_historical_constructor_and_driver_standings(self):
        """Verify standings across all 5 tiers can be queried for past seasons."""
        for tier in range(1, 6):
            c_standings = self.cdb.get_historical_constructor_standings(season_num=0, tier=tier)
            self.assertEqual(len(c_standings), 10, f"Tier {tier} must have 10 constructors in historical standings")
            self.assertEqual(
                c_standings[0]["championship_position"], 1, "P1 constructor must have championship_position = 1"
            )
            self.assertGreater(
                c_standings[0]["points"], c_standings[-1]["points"], "Points must follow descending hierarchy"
            )

            d_standings = self.cdb.get_historical_driver_standings(season_num=0, tier=tier)
            self.assertGreaterEqual(
                len(d_standings), 10, f"Tier {tier} must have at least 10 drivers in historical standings"
            )
            self.assertEqual(
                d_standings[0]["championship_position"], 1, "P1 driver must have championship_position = 1"
            )

    def test_historical_races_and_classifications(self):
        """Verify race schedules, winners, and full classifications can be inspected for past seasons."""
        for tier in [1, 2, 3]:
            races = self.cdb.get_historical_season_races(season_num=0, tier=tier)
            expected_rounds = {1: 16, 2: 12, 3: 7}[tier]
            self.assertEqual(len(races), expected_rounds, f"Tier {tier} must have {expected_rounds} rounds")
            first_race = races[0]
            self.assertIsNotNone(first_race.get("winner_driver"), "Race must have a recorded winner")
            self.assertIsNotNone(first_race.get("track_name"), "Race must have track name")

            # Check full race classification
            classif = self.cdb.get_race_classification(season_num=0, tier=tier, round_num=1)
            self.assertEqual(len(classif), 10, "Race classification must record top 10 finishers")
            self.assertEqual(classif[0]["position"], 1, "First finisher must be position 1")
            self.assertEqual(classif[0]["points"], 25, "Winner must receive 25 points")

    def test_driver_dossier_and_alumni_tracking(self):
        """Verify alumni recording when player releases a driver, and driver profile dossier."""
        dm = DriverManager(self.cdb)
        player_team = self.cdb.get_player_team()
        p_id = player_team["id"]

        primary_drivers = dm.get_primary_drivers(p_id)
        self.assertGreaterEqual(len(primary_drivers), 1, "Player team must have at least one driver")
        drv = primary_drivers[0]
        d_id = drv["id"]
        d_name = drv["name"]

        # Release driver
        success, msg = dm.release_primary_driver(p_id, d_id)
        self.assertTrue(success, f"Release driver should succeed: {msg}")

        # Check driver is now Free Agent (team_id is NULL) rather than erased
        with self.cdb.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT team_id FROM drivers WHERE id = ?;", (d_id,))
            row = cur.fetchone()
            self.assertIsNotNone(row, "Released driver must remain in database")
            self.assertIsNone(row[0], "Released driver team_id must be NULL (Free Agent)")

        # Check alumni record
        alumni = self.cdb.get_team_alumni(p_id)
        alumni_names = [a["driver_name"] for a in alumni]
        self.assertIn(d_name, alumni_names, "Released driver must appear in player team alumni")

        # Check full driver dossier
        profile = self.cdb.get_driver_profile(d_id)
        self.assertIsNotNone(profile, "Driver profile must be returned")
        self.assertTrue(profile["is_team_alumni"], "Profile must identify driver as official team alumni")
        self.assertIn("ai_analysis", profile, "Profile must include AI career analysis")
        self.assertIn("trajectory_arc", profile["ai_analysis"])
        self.assertIn("scout_assessment", profile["ai_analysis"])
        self.assertIn("alumni_insight", profile["ai_analysis"])

    def test_all_time_hall_of_fame_records(self):
        """Verify Hall of Fame queries return champions and win leaders."""
        records = self.cdb.get_all_time_records()
        self.assertIn("top_wins_drivers", records)
        self.assertIn("top_champions", records)
        self.assertIn("top_constructors", records)
        self.assertIn("top_pts_drivers", records)
        self.assertGreater(len(records["top_wins_drivers"]), 0, "Top wins drivers must not be empty")

    def test_database_explorer_ui_rendering_and_interaction(self):
        """Verify DatabaseExplorerTab renders cleanly without exceptions across all 4 subtabs."""
        gm = GameManager(self.test_db_path)
        tab = DatabaseExplorerTab(1280, 720)
        surface = pygame.Surface((1280, 720))

        # 1. Test Season Archive rendering
        tab.active_subtab = "SEASON_ARCHIVE"
        tab.render(surface, gm)

        # 2. Test Driver Dossier & Alumni rendering
        tab.active_subtab = "DRIVERS"
        tab.render(surface, gm)

        # 3. Test Constructors Directory rendering
        tab.active_subtab = "CONSTRUCTORS"
        tab.render(surface, gm)

        # 4. Test Hall of Fame rendering
        tab.active_subtab = "HALL_OF_FAME"
        tab.render(surface, gm)

        # 5. Test subtab click
        handled = tab.handle_click(30, 75, gm)  # Click first subtab
        self.assertTrue(handled or tab.active_subtab == "SEASON_ARCHIVE")

    def test_cross_element_click_navigation(self):
        """Verify that clicking driver or constructor elements navigates to their respective dossiers."""
        import pygame

        from src.ui.management_hub.tab_database_explorer import DatabaseExplorerTab

        gm = GameManager(self.test_db_path)
        tab = DatabaseExplorerTab(1280, 720)
        surface = pygame.Surface((1280, 720))

        # Start on Season Archive, switch to DRIVERS mode
        tab.active_subtab = "SEASON_ARCHIVE"
        tab.archive_mode = "DRIVERS"
        tab.render(surface, gm)

        # In DRIVERS mode, first driver row is around (x=150, y=178 + 36 + 10 = 224)
        handled = tab.handle_click(150, 224, gm)
        self.assertTrue(handled, "Driver click in Season Archive should be handled")
        self.assertEqual(tab.active_subtab, "DRIVERS")
        self.assertIsNotNone(tab.selected_driver_id)
        self.assertEqual(tab.previous_subtab, "SEASON_ARCHIVE")

        # Test Back button in Driver Dossier: Rect(width - 120, 108, 96, 24) -> (1200, 120)
        tab.render(surface, gm)
        handled_back = tab.handle_click(1200, 120, gm)
        self.assertTrue(handled_back, "Back button click in Driver Dossier should be handled")
        self.assertEqual(tab.active_subtab, "SEASON_ARCHIVE")

        # In Season Archive DRIVERS mode, click team column (x=400, y=224)
        handled_team = tab.handle_click(400, 224, gm)
        self.assertTrue(handled_team, "Team click in Season Archive should be handled")
        self.assertEqual(tab.active_subtab, "CONSTRUCTORS")
        self.assertIsNotNone(tab.selected_team_id)

        # In Constructor Dossier, clicking a driver card navigates to Driver Dossier
        tab.render(surface, gm)
        # Driver card 1 is at detail_box.x(370) + 12 + 20 = 402, detail_box.y(144) + 60 + 20 = 224
        handled_drv_card = tab.handle_click(402, 224, gm)
        self.assertTrue(handled_drv_card, "Clicking driver card in Constructor Dossier should jump to Driver Dossier")
        self.assertEqual(tab.active_subtab, "DRIVERS")

    def test_market_and_scout_driver_dossier_resolution(self):
        """Verify drivers in driver_market and scout_prospects resolve into valid dossiers with graceful 0-start stats."""
        dm = DriverManager(self.cdb)
        gm = GameManager(self.test_db_path)

        # 1. Market Driver Dossier
        market_drivers = dm.get_market_drivers(team_tier=3)
        self.assertGreater(len(market_drivers), 0, "Market drivers should exist")
        m_drv = market_drivers[0]
        profile = self.cdb.get_driver_profile(f"market_{m_drv['id']}")
        self.assertIsNotNone(
            profile, f"Market driver {m_drv['name']} (ID {m_drv['id']}) must resolve to a valid profile"
        )
        self.assertEqual(profile["name"], m_drv["name"])
        self.assertIn("career_totals", profile)
        self.assertIn(
            profile["career_totals"]["best_finish"],
            ["N/A", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10"],
        )
        self.assertIn(
            profile["ai_analysis"]["trajectory_arc"],
            [
                "ROOKIE PROSPECT",
                "UNTESTED PRODIGY",
                "GENERATIONAL PRODIGY",
                "RISING TALENT",
                "VETERAN CAMPAIGNER",
                "PROVEN RACE WINNER",
                "MIDFIELD STALWART",
            ],
        )

        # Also verify driver_type='MARKET' parameter lookup
        profile_kw = self.cdb.get_driver_profile(m_drv["id"], driver_type="MARKET")
        self.assertIsNotNone(profile_kw)
        self.assertEqual(profile_kw["name"], m_drv["name"])

        # 2. Scout Candidate Dossier (0-race young talent)
        scout_prospects = dm.get_scout_prospects(team_id=gm.team_id)
        self.assertGreater(len(scout_prospects), 0, "Scout prospects should exist")
        s_drv = scout_prospects[0]
        s_profile = self.cdb.get_driver_profile(f"scout_{s_drv['id']}")
        self.assertIsNotNone(
            s_profile, f"Scout candidate {s_drv['name']} (ID {s_drv['id']}) must resolve to a valid profile"
        )
        self.assertEqual(s_profile["career_totals"]["starts"], 0)
        self.assertEqual(s_profile["career_totals"]["best_finish"], "N/A")
        self.assertIn(s_profile["ai_analysis"]["trajectory_arc"], ["ROOKIE PROSPECT", "UNTESTED PRODIGY"])
        self.assertEqual(
            len(s_profile["season_history"]), 0, "Zero-race prospect should have empty history without error"
        )

        # Also verify driver_type='SCOUT' parameter lookup
        s_profile_kw = self.cdb.get_driver_profile(s_drv["id"], driver_type="SCOUT")
        self.assertIsNotNone(s_profile_kw)
        self.assertEqual(s_profile_kw["name"], s_drv["name"])

    def test_driver_market_to_database_explorer_navigation_and_return(self):
        """Verify clicking DOSSIER in driver market/academy navigates to Database Explorer and returns cleanly."""
        from src.ui.management_hub.tab_database_explorer import DatabaseExplorerTab
        from src.ui.management_hub.tab_drivers_academy import DriversAcademyTab

        captured_driver_id = []

        def on_view_dossier(driver_id: int):
            captured_driver_id.append(driver_id)

        tab_drivers = DriversAcademyTab(1280, 720, on_view_driver_dossier=on_view_dossier)
        gm = GameManager(self.test_db_path)
        dm = DriverManager(self.cdb)
        surface = pygame.Surface((1280, 720))

        # Test Primary Driver Dossier Click
        primary_drivers = dm.get_primary_drivers(gm.team_id)
        tab_drivers.render(surface, gm, dm)
        # Primary driver 1 dossier button is at d_rect.x + d_rect.width - 92, d_rect.y + 6
        p_rect, _ = tab_drivers._get_layout()
        d1_dos_x = p_rect.x + p_rect.width - 50
        d1_dos_y = 108 + 15
        handled_primary = tab_drivers.handle_click(d1_dos_x, d1_dos_y, gm, dm)
        self.assertTrue(handled_primary)
        self.assertEqual(len(captured_driver_id), 1)
        self.assertEqual(captured_driver_id[0], primary_drivers[0]["id"])

        # Test Driver Market Dossier Click
        tab_drivers.active_subtab = "MARKET"
        tab_drivers.render(surface, gm, dm)
        # First market driver dossier button is at card_rect.x + card_w - 60, cy + 10
        _, r_rect = tab_drivers._get_layout()
        m_dos_x = r_rect.x + (r_rect.width - 20) - 60
        m_dos_y = 108 + 10
        handled_market = tab_drivers.handle_click(m_dos_x, m_dos_y, gm, dm)
        self.assertTrue(handled_market)
        self.assertEqual(len(captured_driver_id), 2)

        # Test DatabaseExplorerTab return_hub_tab
        tab_db = DatabaseExplorerTab(1280, 720)
        target_id = captured_driver_id[-1]
        tab_db.open_driver_profile(target_id, return_hub_tab="DRIVERS")
        self.assertEqual(tab_db.active_subtab, "DRIVERS")
        self.assertEqual(tab_db.selected_driver_id, target_id)
        self.assertEqual(tab_db.return_hub_tab, "DRIVERS")

        # Click Back button: (1200, 120)
        tab_db.render(surface, gm)
        handled_back = tab_db.handle_click(1200, 120, gm)
        self.assertTrue(handled_back)
        self.assertEqual(tab_db.return_hub_tab_requested, "DRIVERS")
        self.assertIsNone(tab_db.return_hub_tab)

    def test_driver_dossier_constructor_clickable_links(self):
        """Verify constructor links in driver header and season history table navigate to constructor dossier."""
        gm = GameManager(self.test_db_path)
        tab = DatabaseExplorerTab(1280, 720)
        surface = pygame.Surface((1280, 720))

        # 1. Open driver with historical seasons
        drivers = gm.db.get_all_drivers_directory(player_team_id=gm.team_id)
        driver_with_team = next((d for d in drivers if d.get("team_id")), drivers[0])
        tab.open_driver_profile(driver_with_team["id"], return_subtab="SEASON_ARCHIVE")
        tab.render(surface, gm)

        # 2. Click header constructor button: (detail_box.x + 60, detail_box.y + 24) -> (400 + 80, 144 + 30) = (480, 174)
        handled_hdr = tab.handle_click(480, 174, gm)
        self.assertTrue(handled_hdr, "Clicking constructor button in driver header must be handled")
        self.assertEqual(tab.active_subtab, "CONSTRUCTORS")
        self.assertEqual(tab.selected_team_id, driver_with_team["team_id"])
        self.assertEqual(tab.previous_subtab, "DRIVERS")

        # 3. Click back button in Constructor Dossier returns to Driver Dossier
        tab.render(surface, gm)
        handled_back = tab.handle_click(1200, 120, gm)
        self.assertTrue(handled_back)
        self.assertEqual(tab.active_subtab, "DRIVERS")

        # 4. In driver dossier season breakdown table, click constructor link on first historical season
        profile = gm.db.get_driver_profile(driver_with_team["id"])
        self.assertTrue(len(profile.get("season_history", [])) > 0, "Driver should have historical seasons")
        first_sh = profile["season_history"][0]

        # Calculate Y for first season row in detail box
        detail_box_y = 144
        cur_y = detail_box_y + 58
        if profile.get("is_team_alumni", False):
            cur_y += 46
        cur_y += 48 + 66 + 18
        first_row_y = cur_y + 24
        # Constructor cell is at x = detail_box.x + 12 + 220 = 632
        handled_table_team = tab.handle_click(650, first_row_y + 10, gm)
        self.assertTrue(
            handled_table_team,
            "Clicking constructor column in driver season history table must jump to Constructor Dossier",
        )
        self.assertEqual(tab.active_subtab, "CONSTRUCTORS")
        self.assertEqual(tab.previous_subtab, "DRIVERS")
        self.assertEqual(tab.team_selected_tier, first_sh["tier"])


if __name__ == "__main__":
    unittest.main()
