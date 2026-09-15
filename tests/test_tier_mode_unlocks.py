import unittest

import pygame

from src.core.car import Car
from src.core.driver import Driver
from src.database.db_manager import CarAttributes
from src.ui.driver_panel import DriverStrategyPanel


class TestTierModeUnlocks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.NOFRAME)

    def test_tier3_car_mode_restrictions(self):
        driver = Driver(
            id=1, name="Player", code="PLY", number=1, team_name="Team", color_rgb=(255, 0, 0), is_player=True
        )
        attrs = CarAttributes(braking_efficiency=600.0, engine_power=600.0, aero_downforce=600.0)
        car = Car(car_id=1, driver=driver, car_attributes=attrs, league_tier=3)

        self.assertEqual(car.ers_pct, 0.0)

        car.pace_mode = "ATTACK"
        self.assertEqual(car.pace_mode, "PUSH")

        car.pace_mode = "CONSERVE"
        self.assertEqual(car.pace_mode, "NORMAL")

        car.engine_mode = "RICH"
        self.assertEqual(car.engine_mode, "STANDARD")

        car.engine_mode = "LEAN"
        self.assertEqual(car.engine_mode, "STANDARD")

        car.ers_mode = "OVERTAKE"
        self.assertEqual(car.ers_mode, "NONE")

    def test_tier1_car_full_unlocks(self):
        driver = Driver(
            id=1, name="Player", code="PLY", number=1, team_name="Team", color_rgb=(255, 0, 0), is_player=True
        )
        attrs = CarAttributes(braking_efficiency=600.0, engine_power=600.0, aero_downforce=600.0)
        car = Car(car_id=1, driver=driver, car_attributes=attrs, league_tier=1)

        car.pace_mode = "ATTACK"
        self.assertEqual(car.pace_mode, "ATTACK")

        car.engine_mode = "RICH"
        self.assertEqual(car.engine_mode, "RICH")

        car.ers_mode = "OVERTAKE"
        self.assertEqual(car.ers_mode, "OVERTAKE")

    def test_driver_panel_tier3_click_rejection(self):
        panel = DriverStrategyPanel(x=200, y=620, width=880, height=95, on_box_click=lambda c: None)
        driver = Driver(
            id=1, name="Player", code="PLY", number=1, team_name="Team", color_rgb=(255, 0, 0), is_player=True
        )
        attrs = CarAttributes(braking_efficiency=600.0, engine_power=600.0, aero_downforce=600.0)
        car_t3 = Car(car_id=1, driver=driver, car_attributes=attrs, league_tier=3)
        car_t3.pace_mode = "NORMAL"
        car_t3.engine_mode = "STANDARD"
        car_t3.ers_mode = "NONE"

        # Coordinates for ATTACK button in card 0:
        # Dynamic layout coordinates in new driver panel:
        # cx = 208, cy = 626, strat_x = 360, btn_w = 44, btn_gap = 5, p_idx = 3 -> b_rect = Rect(507, 648, 44, 20)
        atk_pos = (529, 658)

        click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": atk_pos})
        panel.handle_event(click_event, [car_t3], league_tier=3)

        # In Tier 3, clicking ATTACK should be ignored/rejected
        self.assertNotEqual(car_t3.pace_mode, "ATTACK")
        self.assertEqual(car_t3.pace_mode, "NORMAL")

        # Now test that on a Tier 1 car and league_tier=1, clicking ATTACK succeeds
        car_t1 = Car(car_id=2, driver=driver, car_attributes=attrs, league_tier=1)
        car_t1.pace_mode = "NORMAL"
        panel.handle_event(click_event, [car_t1], league_tier=1)
        self.assertEqual(car_t1.pace_mode, "ATTACK")


if __name__ == "__main__":
    unittest.main()
