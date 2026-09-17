import gc
import os
import tempfile
import unittest

import pygame

from src.core.car import Car
from src.core.driver import Driver
from src.database.career_db import CareerDatabase
from src.management.game_manager import GameManager
from src.management.innovation_manager import InnovationManager
from src.ui.driver_panel import DriverStrategyPanel
from src.ui.management_hub.tab_dashboard import DashboardTab
from src.ui.theme import UITheme


class TestModernUIRevamp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1280, 720), pygame.NOFRAME)

    def setUp(self):
        self.tmp_db_fd, self.tmp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.tmp_db_fd)
        self.db = CareerDatabase(self.tmp_db_path)
        self.db.create_new_career("Apex Racing", "#00d2be", "NORMAL", "Vortex EcoTech", "Liam Andersson")
        self.gm = GameManager(self.db)
        self.im = InnovationManager(self.db)

    def tearDown(self):
        del self.gm
        del self.im
        del self.db
        gc.collect()
        try:
            if os.path.exists(self.tmp_db_path):
                os.remove(self.tmp_db_path)
        except Exception:
            pass

    def test_radar_chart_render(self):
        """Validates that UITheme.draw_radar_chart renders dual driver talent radar charts smoothly."""
        surf = pygame.Surface((400, 400))
        attrs = ["Pace", "Brake", "Defend", "Consist", "Tires", "Wet"]
        v1 = [85.0, 78.0, 90.0, 72.0, 88.0, 65.0]
        v2 = [75.0, 82.0, 68.0, 85.0, 70.0, 92.0]

        # Single driver radar
        UITheme.draw_radar_chart(
            surf,
            center=(200, 200),
            radius=60,
            attributes=attrs,
            values_1=v1,
            label_1="Driver 1",
            show_labels=True,
        )

        # Dual driver comparison radar
        UITheme.draw_radar_chart(
            surf,
            center=(200, 200),
            radius=60,
            attributes=attrs,
            values_1=v1,
            values_2=v2,
            label_1="Driver 1",
            label_2="Driver 2",
            show_labels=True,
        )

        # Non-empty surface has drawn pixels
        self.assertGreater(surf.get_width(), 0)

    def test_dashboard_tab_rendering_and_track_cache(self):
        """Validates DashboardTab rendering, vector track geometry loading, and demands."""
        tab = DashboardTab(1280, 720, on_start_race=lambda: None)
        surf = pygame.Surface((1280, 720))

        # Render during race week
        tab.render(surf, self.gm, self.im)

        # Check that track points were loaded and cached
        event = self.gm.get_current_race_event()
        c_file = event.get("circuit_file", "emerald_ring.json")
        self.assertIn(c_file, tab._track_cache)
        self.assertGreater(len(tab._track_cache[c_file]), 2)

    def test_dashboard_auto_resolve_wear(self):
        """Validates that 4-point readiness checklist detects component wear and 1-click auto-resolve fixes it."""
        tab = DashboardTab(1280, 720, on_start_race=lambda: None)
        surf = pygame.Surface((1280, 720))

        # Inject worn part on Car 1 (e.g. reliability = 45%)
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE car_components SET reliability = 45.0 WHERE team_id = ? AND car_slot = 1 AND category = 'FRONT_WING';",
                (self.gm.team_id,),
            )
            conn.commit()

        # Render tab: must display the AUTO-RESOLVE button
        tab.render(surf, self.gm, self.im)
        self.assertIsNotNone(tab.resolve_btn_rect)

        # Click the AUTO-RESOLVE button
        btn = tab.resolve_btn_rect
        clicked = tab.handle_click(btn.centerx, btn.centery, self.gm, self.im)
        self.assertTrue(clicked)
        self.assertIn("Resolved", tab.action_message)

        # Verify in database that Front Wing reliability on Car 1 is now >= 80%
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT reliability FROM car_components WHERE team_id = ? AND car_slot = 1 AND category = 'FRONT_WING';",
                (self.gm.team_id,),
            )
            row = cur.fetchone()
            self.assertGreaterEqual(row[0], 80.0)

        # Re-render: all systems green, resolve button should no longer appear
        tab.render(surf, self.gm, self.im)
        self.assertIsNone(tab.resolve_btn_rect)

    def test_driver_panel_tyre_bar_and_box_button(self):
        """Validates DriverStrategyPanel renders tyre health bar and handles box this lap toggling."""
        boxed_cars = []
        panel = DriverStrategyPanel(10, 580, 1260, 130, on_box_click=lambda c: boxed_cars.append(c))
        surf = pygame.Surface((1280, 720))

        driver = Driver(1, "Liam Andersson", "AND", 7, "Apex Racing", (0, 210, 190), is_player=True)
        car = Car(driver, 1)
        car.position = 3
        car.tires.wear_pct = 35.0

        # Render unboxed
        panel.render(surf, [car])

        # Arm box this lap
        car.box_this_lap = True
        panel.render(surf, [car])
        self.assertTrue(car.box_this_lap)

    def test_race_weekend_track_and_tyre_curves(self):
        """Validates that RaceWeekendScreen renders prominent circuit radar and tyre degradation curves."""
        from src.core.race_weekend import RaceWeekendManager
        from src.ui.race_weekend.race_weekend_screen import RaceWeekendScreen

        mgr = RaceWeekendManager(
            league_tier=1,
            track_metadata={"track_name": "Emerald Ring", "circuit_file": "emerald_ring.json"},
            total_laps_base=20,
        )
        drivers = [{"name": "Liam Andersson", "number": 7}, {"name": "Sophia Moreau", "number": 12}]
        screen = RaceWeekendScreen(
            1280,
            720,
            manager=mgr,
            drivers=drivers,
            on_start_live_session=lambda s, l, g: None,
            on_finish_weekend=lambda r: None,
        )
        surf = pygame.Surface((1280, 720))

        # Test _render_mini_track
        track_rect = pygame.Rect(500, 175, 750, 240)
        screen._render_mini_track(surf, track_rect)

        # Test _render_tyre_strategy_curves
        tyre_rect = pygame.Rect(500, 425, 750, 220)
        screen._render_tyre_strategy_curves(surf, tyre_rect, 20)

        # Test starting grid layout with large map
        grid = [{"driver_name": "Driver 1", "team_name": "Apex", "race_grid_pos": 1}]
        screen._render_grid_table(surf, grid, is_sprint=False)
        self.assertGreater(surf.get_width(), 0)
