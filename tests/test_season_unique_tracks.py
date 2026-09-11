import unittest
import os
import pygame
from src.database.career_db import CareerDatabase
from src.data.default_tracks import (
    initialize_default_tracks_folder,
    create_emerald_ring,
    create_autodromo_velocita,
    create_oasis_grand_prix,
    create_vortex_aero_ring,
    create_apex_park,
    create_harbor_city,
    create_riviera_speedway,
    create_ardennes_forest
)
from src.core.circuit import Circuit
from src.management.game_manager import GameManager
from src.management.league_simulator import LeagueSimulator

class TestSeasonUniqueTracks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile
        import gc
        pygame.init()
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.test_db_path = os.path.join(cls.temp_dir.name, "test_season_tracks.db")
        cls.cdb = CareerDatabase(cls.test_db_path)
        initialize_default_tracks_folder("tracks")

    @classmethod
    def tearDownClass(cls):
        import gc
        if hasattr(cls, "cdb"):
            del cls.cdb
        gc.collect()
        if hasattr(cls, "temp_dir"):
            try:
                cls.temp_dir.cleanup()
            except Exception:
                pass

    def test_tier_calendar_lengths(self):
        """Verify tier 4-5 have 6 rounds, tier 3 has 7 rounds, tier 2 has 12 rounds, tier 1 has 16 rounds."""
        t1_rounds = self.cdb.get_calendar_rounds(tier=1)
        t2_rounds = self.cdb.get_calendar_rounds(tier=2)
        t3_rounds = self.cdb.get_calendar_rounds(tier=3)
        t4_rounds = self.cdb.get_calendar_rounds(tier=4)
        t5_rounds = self.cdb.get_calendar_rounds(tier=5)

        self.assertEqual(len(t1_rounds), 16, "Tier 1 must have 16 race weekends")
        self.assertEqual(len(t2_rounds), 12, "Tier 2 must have 12 race weekends")
        self.assertEqual(len(t3_rounds), 7, "Tier 3 must have 7 race weekends")
        self.assertEqual(len(t4_rounds), 6, "Tier 4 must have 6 race weekends")
        self.assertEqual(len(t5_rounds), 6, "Tier 5 must have 6 race weekends")

        self.assertEqual(self.cdb.get_total_rounds_for_tier(1), 16)
        self.assertEqual(self.cdb.get_total_rounds_for_tier(2), 12)
        self.assertEqual(self.cdb.get_total_rounds_for_tier(3), 7)
        self.assertEqual(self.cdb.get_total_rounds_for_tier(4), 6)
        self.assertEqual(self.cdb.get_total_rounds_for_tier(5), 6)

    def test_track_characteristics_diversity(self):
        """Verify calendar features diverse track characteristics: SPEED, BRAKES, AERO, BALANCED."""
        for tier in [1, 2, 3]:
            rounds = self.cdb.get_calendar_rounds(tier=tier)
            chars = {r.get("characteristic") for r in rounds}
            self.assertIn("SPEED", chars, f"Tier {tier} must include straight-line speed tracks")
            self.assertIn("BRAKES", chars, f"Tier {tier} must include heavy braking tracks")
            self.assertIn("AERO", chars, f"Tier {tier} must include wide high-downforce aero tracks")
            self.assertIn("BALANCED", chars, f"Tier {tier} must include balanced circuits")

    def test_circuit_layouts_and_archetypes(self):
        """Verify circuit generators create valid spline circuits with required archetype geometry."""
        circuits = {
            "emerald_ring": create_emerald_ring(),
            "autodromo_velocita": create_autodromo_velocita(),
            "oasis_grand_prix": create_oasis_grand_prix(),
            "vortex_aero_ring": create_vortex_aero_ring(),
            "apex_park": create_apex_park(),
            "harbor_city": create_harbor_city(),
            "riviera_speedway": create_riviera_speedway(),
            "ardennes_forest": create_ardennes_forest()
        }

        for name, c in circuits.items():
            self.assertGreater(c.length, 1000.0, f"Track {name} must have realistic track length")
            self.assertIsNotNone(c.spline_x, f"Track {name} must have valid splines")
            self.assertGreater(len(c.drs_zones), 0, f"Track {name} must have DRS zones")
            self.assertIsNotNone(c.pit_entry_node, f"Track {name} must have pit entry")
            self.assertIsNotNone(c.pit_exit_node, f"Track {name} must have pit exit")

        # Specific archetype checks
        vortex = circuits["vortex_aero_ring"]
        self.assertGreaterEqual(vortex.width, 16.0, "Vortex Aero Ring must feature wide track width (>= 16m)")

        velocita = circuits["autodromo_velocita"]
        self.assertGreater(velocita.length, 3000.0, "Autodromo Velocita must feature long power circuit layout")

    def test_game_manager_season_and_event(self):
        """Verify GameManager tracks rounds based on player tier and returns correct event metadata."""
        gm = GameManager(self.cdb)
        self.assertEqual(gm.player_tier, 3)
        self.assertEqual(gm.total_rounds, 7, "Player in Tier 3 should have 7 total rounds")

        evt = gm.get_current_race_event()
        self.assertEqual(evt["round"], 1)
        self.assertIn("characteristic", evt)
        self.assertIn("track_name", evt)
        self.assertIn("circuit_file", evt)

        # Advance rounds
        for _ in range(6):
            gm.advance_to_next_race_round()
        self.assertEqual(gm.current_round, 7)

        # Attempt to advance beyond total rounds
        gm.advance_to_next_race_round()
        self.assertEqual(gm.current_round, 7, "Should not exceed total rounds")

    def test_league_simulator_multi_tier(self):
        """Verify LeagueSimulator simulates races respecting different tier season lengths."""
        sim = LeagueSimulator(self.cdb)

        # Simulate Round 1
        sim.simulate_background_round(1)

        # All tiers should have completed round 1
        for t in range(1, 6):
            r1 = self.cdb.get_calendar_round(t, 1)
            self.assertEqual(r1["is_completed"], 1)

        # Simulate Round 7 (Tier 4 & 5 should not crash as they have only 6 rounds)
        sim.simulate_background_round(7)
        t3_r7 = self.cdb.get_calendar_round(3, 7)
        self.assertEqual(t3_r7["is_completed"], 1)

        # Test season finale reset and promotion/relegation
        res = sim.process_season_finale_promotion_relegation()
        self.assertIn("promotions", res)
        self.assertIn("relegations", res)

        # After finale, calendars should be reset
        t1_r1 = self.cdb.get_calendar_round(1, 1)
        self.assertEqual(t1_r1["is_completed"], 0)

if __name__ == "__main__":
    unittest.main()
