import unittest
import pygame
from src.core.driver import Driver
from src.core.car import Car
from src.core.simulation import Simulation
from src.core.race_weekend import RaceWeekendManager, RaceWeekendSession
from src.database.db_manager import CarAttributes
from src.ui.race_weekend.race_weekend_screen import RaceWeekendScreen
from src.ui.broadcast_header import BroadcastHeader
from src.ui.pit_modal import PitStrategyModal
from src.data.default_tracks import create_emerald_ring
from src.render.camera import Camera

class TestGameplayFixes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.NOFRAME)

    def test_race_weekend_screen_career_pairs(self):
        driver1 = Driver(id=1, name="Career Driver 1", code="CD1", number=1, team_name="Player Team", color_rgb=(255, 0, 0), is_player=True)
        driver2 = Driver(id=2, name="Career Driver 2", code="CD2", number=2, team_name="Player Team", color_rgb=(0, 255, 0), is_player=True)
        attrs = CarAttributes()
        pairs = [(driver1, attrs), (driver2, attrs)]

        mgr = RaceWeekendManager(
            league_tier=3,
            track_metadata={"track_name": "Emerald Ring", "circuit_file": "emerald_ring.json"},
            total_laps_base=15
        )
        screen = RaceWeekendScreen(
            1280, 720,
            manager=mgr,
            drivers=[{"name": "Career Driver 1"}, {"name": "Career Driver 2"}],
            on_start_live_session=lambda s, l, g: None,
            on_finish_weekend=lambda res: None,
            driver_car_pairs=pairs
        )
        built_pairs = screen._build_driver_car_pairs()
        self.assertEqual(len(built_pairs), 2)
        self.assertEqual(built_pairs[0][0].name, "Career Driver 1")

    def test_qualifying_shootout_click_coordinates(self):
        driver1 = Driver(id=1, name="Driver 1", code="D1", number=1, team_name="Team 1", color_rgb=(255, 0, 0), is_player=True)
        driver2 = Driver(id=2, name="Driver 2", code="D2", number=2, team_name="Team 2", color_rgb=(0, 0, 255), is_player=False)
        attrs = CarAttributes()
        pairs = [(driver1, attrs), (driver2, attrs)]

        mgr = RaceWeekendManager(
            league_tier=3,
            track_metadata={"track_name": "Emerald Ring"},
            total_laps_base=15
        )
        screen = RaceWeekendScreen(
            1280, 720,
            manager=mgr,
            drivers=[{"name": "Driver 1"}, {"name": "Driver 2"}],
            on_start_live_session=lambda s, l, g: None,
            on_finish_weekend=lambda res: None,
            driver_car_pairs=pairs
        )
        # Advance to qualifying session (index 2 in Tier 3)
        mgr.current_session_index = 2
        self.assertTrue(mgr.is_qualifying)
        self.assertEqual(mgr.qualifying_results, [])

        click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 360))
        handled = screen.handle_event(click_event)
        self.assertTrue(handled)
        self.assertEqual(len(mgr.qualifying_results), 2)

    def test_pit_modal_escape_key(self):
        modal = PitStrategyModal(1280, 720)
        driver = Driver(id=1, name="Driver 1", code="D1", number=1, team_name="Team 1", color_rgb=(255, 0, 0), is_player=True)
        car = Car(car_id=1, driver=driver, car_attributes=CarAttributes())
        modal.open(car)
        self.assertTrue(modal.is_open)

        esc_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        handled = modal.handle_event(esc_event)
        self.assertTrue(handled)
        self.assertFalse(modal.is_open)

    def test_broadcast_header_chequered_flag(self):
        circuit = create_emerald_ring()
        driver = Driver(id=1, name="Leader", code="LEA", number=1, team_name="Team", color_rgb=(255, 200, 0), is_player=True)
        pairs = [(driver, CarAttributes())]
        sim = Simulation(circuit, pairs, total_laps=5)
        sim.race_finished = True

        camera = Camera(1280, 720)
        header = BroadcastHeader(1280, 48)
        surface = pygame.Surface((1280, 48))
        header.render(surface, sim, camera)

if __name__ == "__main__":
    unittest.main()
