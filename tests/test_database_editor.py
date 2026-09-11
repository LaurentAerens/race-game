import unittest
import os
import tempfile
import gc
import sqlite3
from src.database.db_manager import DatabaseManager
from src.database.career_db import CareerDatabase
from src.editor.database_editor import DatabaseEditor
from src.editor.admin_hub import AdminHub
import pygame

class TestDatabaseEditorAndAdminHub(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((200, 200))
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.exhibition_db_path = os.path.join(cls.temp_dir.name, "test_admin_db.db")
        cls.career_db_path = os.path.join(cls.temp_dir.name, "test_career.db")

    @classmethod
    def tearDownClass(cls):
        gc.collect()
        if hasattr(cls, "temp_dir"):
            try:
                cls.temp_dir.cleanup()
            except Exception:
                pass

    def test_database_manager_editing(self):
        db = DatabaseManager(self.exhibition_db_path)
        teams = db.get_teams()
        self.assertGreater(len(teams), 0)
        t_id = teams[0]["id"]
        
        # Test updating car attributes
        car_attrs = db.get_car_attributes(t_id)
        self.assertIsNotNone(car_attrs)
        new_attrs = {"engine_power": 99.0, "aero_downforce": 95.0, "braking_efficiency": 92.0, "tire_preservation": 88.0, "fuel_efficiency": 85.0, "reliability": 94.0}
        self.assertTrue(db.update_car_attributes(t_id, new_attrs))
        updated_car = db.get_car_attributes(t_id)
        self.assertEqual(updated_car["engine_power"], 99.0)

        # Test updating driver attributes
        drivers = db.get_drivers(t_id)
        self.assertGreater(len(drivers), 0)
        d_id = drivers[0]["id"]
        new_stats = {"speed": 97.0, "braking": 96.0, "cornering": 95.0, "overtaking": 92.0, "defending": 90.0, "tire_management": 89.0, "consistency": 94.0, "wet_skill": 91.0}
        self.assertTrue(db.update_driver_attributes(d_id, drivers[0]["name"], "TST", 99, new_stats))

        # Test reset
        db.reset_and_reseed()
        reset_car = db.get_car_attributes(t_id)
        self.assertIsNotNone(reset_car)

    def test_career_database_summary_and_update(self):
        cdb = CareerDatabase(self.career_db_path)
        summary = cdb.get_career_summary()
        self.assertIsNotNone(summary)
        self.assertIn("team_name", summary)
        self.assertIn("tier", summary)
        self.assertIn("cash", summary)
        self.assertIn("completed_races", summary)

    def test_database_editor_instantiation(self):
        ed = DatabaseEditor(1280, 720, exhibition_db_path=self.exhibition_db_path, career_db_path=self.career_db_path)
        self.assertGreater(len(ed.teams), 0)
        self.assertIn(ed.active_subtab, ["CAR", "DRIVER", "CALENDAR", "FACTORY"])

        # Test rendering all tabs to a pygame surface without exceptions
        surf = pygame.Surface((1280, 720))
        for tab in ["CAR", "DRIVER", "CALENDAR", "FACTORY"]:
            ed.active_subtab = tab
            ed.render(surf)

    def test_career_calendar_and_facility_modding(self):
        cdb = CareerDatabase(self.career_db_path)
        rounds = cdb.get_calendar_rounds()
        self.assertGreater(len(rounds), 0)
        first_rnd = rounds[0]

        # Test updating a round
        success = cdb.update_calendar_round(first_rnd["round"], "Custom Test GP", "emerald_ring.json", 18, "RAIN")
        self.assertTrue(success)
        updated_r = [r for r in cdb.get_calendar_rounds() if r["round"] == first_rnd["round"]][0]
        self.assertEqual(updated_r["track_name"], "Custom Test GP")
        self.assertEqual(updated_r["total_laps"], 18)
        self.assertEqual(updated_r["weather_profile"], "RAIN")

        # Restore original round
        cdb.update_calendar_round(first_rnd["round"], first_rnd["track_name"], first_rnd["circuit_file"], first_rnd["total_laps"], first_rnd["weather_profile"])

        # Test setting facility tier
        facilities = cdb.get_team_facilities(1)
        self.assertGreater(len(facilities), 0)
        fac_id = facilities[0]["id"]
        self.assertTrue(cdb.set_team_facility_tier(1, fac_id, 2, True))
        fac_after = [f for f in cdb.get_team_facilities(1) if f["id"] == fac_id][0]
        self.assertEqual(fac_after["current_tier"], 2)
        self.assertEqual(fac_after["is_unlocked"], 1)

    def test_custom_facility_node_crud(self):
        cdb = CareerDatabase(self.career_db_path)
        test_node_id = "test_custom_windtunnel_rig"
        
        # 1. Create custom facility node
        created = cdb.create_facility_node(
            node_id=test_node_id,
            department="ENGINEERING",
            name="Supersonic Aero Chamber",
            description="Ultra high-speed aerodynamic scale tunnel",
            parent_id="eng_workshop",
            tier=1,
            max_tier=3,
            base_cost=15000000.0,
            base_upkeep=350000.0
        )
        self.assertTrue(created)

        # Verify existence
        nodes = cdb.get_all_facility_nodes()
        match = [n for n in nodes if n["id"] == test_node_id]
        self.assertEqual(len(match), 1)
        self.assertEqual(match[0]["name"], "Supersonic Aero Chamber")

        # Verify auto-initialization for team 1
        team_facs = cdb.get_team_facilities(1)
        team_match = [f for f in team_facs if f["id"] == test_node_id]
        self.assertEqual(len(team_match), 1)
        self.assertEqual(team_match[0]["current_tier"], 0)

        # 2. Update custom facility node
        updated = cdb.update_facility_node(
            node_id=test_node_id,
            department="TESTING",
            name="Supersonic Aero Chamber Mk2",
            description="Upgraded chamber",
            parent_id=None,
            base_cost=18000000.0,
            base_upkeep=400000.0
        )
        self.assertTrue(updated)
        match_upd = [n for n in cdb.get_all_facility_nodes() if n["id"] == test_node_id][0]
        self.assertEqual(match_upd["department"], "TESTING")
        self.assertEqual(match_upd["name"], "Supersonic Aero Chamber Mk2")

        # 3. Delete custom facility node
        deleted = cdb.delete_facility_node(test_node_id)
        self.assertTrue(deleted)
        match_del = [n for n in cdb.get_all_facility_nodes() if n["id"] == test_node_id]
        self.assertEqual(len(match_del), 0)

    def test_admin_hub_instantiation(self):
        hub = AdminHub(1280, 720, lambda: None, lambda c: None, exhibition_db_path=self.exhibition_db_path, career_db_path=self.career_db_path)
        self.assertIn(hub.active_tab, ["TRACK", "DATABASE"])
        hub.active_tab = "DATABASE"
        self.assertEqual(hub.active_tab, "DATABASE")

        # Test modal rendering
        hub.database_editor.active_subtab = "FACTORY"
        hub.database_editor.show_node_modal = True
        surf = pygame.Surface((1280, 720))
        hub.render(surf)

if __name__ == "__main__":
    unittest.main()


