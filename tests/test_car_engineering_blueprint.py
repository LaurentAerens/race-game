import gc
import os
import tempfile
import unittest

import pygame

from src.database.career_db import CareerDatabase
from src.management.engineering_manager import EngineeringManager
from src.management.game_manager import GameManager
from src.ui.management_hub.tab_car_engineering import CarEngineeringTab


class TestCarEngineeringBlueprint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1280, 720), pygame.NOFRAME)

    def setUp(self):
        self.tmp_db_fd, self.tmp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.tmp_db_fd)
        self.db = CareerDatabase(self.tmp_db_path)
        self.db.create_new_career("Apex Engineering", "#00d2be", "NORMAL", "Vortex EcoTech", "Alex Hunter")
        self.gm = GameManager(self.db)
        self.em = EngineeringManager(self.db)
        self.tab = CarEngineeringTab(1280, 720)

    def tearDown(self):
        del self.gm
        del self.em
        del self.db
        gc.collect()
        try:
            if os.path.exists(self.tmp_db_path):
                os.remove(self.tmp_db_path)
        except Exception:
            pass

    def test_initial_state_and_hotspot_selection(self):
        """Validates default car slot, default selected part, and hotspot selection."""
        self.assertEqual(self.tab.selected_car_slot, 1)
        self.assertEqual(self.tab.selected_part_category, "FRONT_WING")

        tier, _, allowed_parts = self.em.get_team_allowed_parts(self.gm.team_id)
        layout = self.tab.get_layout(self.gm, self.em, tier, allowed_parts)

        # Ensure all 7 component hotspots have non-empty rects
        self.assertEqual(len(layout["hotspot_rects"]), 7)
        for cat in CarEngineeringTab.CATEGORIES:
            self.assertIn(cat, layout["hotspot_rects"])
            rect = layout["hotspot_rects"][cat]
            self.assertGreater(rect.width, 50)
            self.assertGreater(rect.height, 20)

        # Click on BRAKES hotspot
        brakes_rect = layout["hotspot_rects"]["BRAKES"]
        clicked = self.tab.handle_click(brakes_rect.centerx, brakes_rect.centery, self.gm, self.em)
        self.assertTrue(clicked)
        self.assertEqual(self.tab.selected_part_category, "BRAKES")

    def test_car_slot_toggle(self):
        """Switching between Car 1 and Car 2 updates the active car slot."""
        tier, _, allowed_parts = self.em.get_team_allowed_parts(self.gm.team_id)
        layout = self.tab.get_layout(self.gm, self.em, tier, allowed_parts)

        c2_rect = layout["c2_rect"]
        clicked = self.tab.handle_click(c2_rect.centerx, c2_rect.centery, self.gm, self.em)
        self.assertTrue(clicked)
        self.assertEqual(self.tab.selected_car_slot, 2)

        c1_rect = layout["c1_rect"]
        clicked = self.tab.handle_click(c1_rect.centerx, c1_rect.centery, self.gm, self.em)
        self.assertTrue(clicked)
        self.assertEqual(self.tab.selected_car_slot, 1)

    def test_rendering_without_crash(self):
        """Renders the entire blueprint inspector and child widgets on a surface without crashing."""
        surface = pygame.Surface((1280, 720))
        self.tab.render(surface, self.gm, self.em)

        # Resize to laptop resolution and render again
        self.tab.resize(1024, 600)
        laptop_surface = pygame.Surface((1024, 600))
        self.tab.render(laptop_surface, self.gm, self.em)

    def test_mount_spare_from_drawer(self):
        """Mounting a spare part from the warehouse drawer updates component on the car."""
        # Insert a spare into warehouse (car_slot = 0)
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO car_components (team_id, car_slot, category, generation, performance, reliability, wear_pct, current_durability, max_durability, knowledge_min, knowledge_max, races_on_concept)
                VALUES (?, 0, 'FRONT_WING', 2, 88.0, 90.0, 0.0, 100.0, 100.0, 5.0, 10.0, 0);
                """,
                (self.gm.team_id,),
            )
            spare_id = cur.lastrowid
            conn.commit()

        tier, _, allowed_parts = self.em.get_team_allowed_parts(self.gm.team_id)
        layout = self.tab.get_layout(self.gm, self.em, tier, allowed_parts)
        self.assertTrue(len(layout["spare_buttons"]) > 0)

        # Find mount button for our spare
        found = False
        for s_id, _, m_btn, _ in layout["spare_buttons"]:
            if s_id == spare_id:
                found = True
                clicked = self.tab.handle_click(m_btn.centerx, m_btn.centery, self.gm, self.em)
                self.assertTrue(clicked)
                self.assertIn("mounted", self.tab.status_message.lower())
                break
        self.assertTrue(found)
