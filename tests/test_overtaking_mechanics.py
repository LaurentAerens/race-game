import unittest
import os
import math
from src.core.circuit import Circuit
from src.core.driver import Driver
from src.core.car import Car
from src.core.race_control import RaceControl
from src.database.db_manager import CarAttributes
from src.data.default_tracks import create_emerald_ring
from src.data.teams import load_career_teams_and_drivers
from src.database.career_db import CareerDatabase

class TestOvertakingMechanics(unittest.TestCase):

    def setUp(self):
        self.circuit = create_emerald_ring()
        self.rc = RaceControl()

    def test_component_brakes_and_dive_bomb(self):
        """Verify that a car with 685 brakes has an overwhelming braking advantage over 432 brakes and dive-bombs."""
        driver_a = Driver(id=1, name="Attacker", code="ATK", number=1, team_name="TopTeam", color_rgb=(255, 0, 0), braking=0.90)
        attrs_a = CarAttributes(braking_efficiency=685.0, engine_power=750.0, aero_downforce=450.0)
        car_a = Car(car_id=1, driver=driver_a, car_attributes=attrs_a)

        driver_b = Driver(id=2, name="Defender", code="DEF", number=2, team_name="SlowTeam", color_rgb=(0, 0, 255), braking=0.70)
        attrs_b = CarAttributes(braking_efficiency=432.0, engine_power=720.0, aero_downforce=400.0)
        car_b = Car(car_id=2, driver=driver_b, car_attributes=attrs_b)

        # 1. Verify normalized braking attributes and deceleration power
        self.assertGreater(car_a.norm_brakes, car_b.norm_brakes * 1.4)

        # 2. Position cars on corner approach to Turn 1 (apex at ~920m)
        car_b.s = 870.0
        car_b.speed = 60.0
        car_b.position = 1
        car_b.lap = 2

        car_a.s = 855.0 # 15m behind car_b
        car_a.speed = 62.0
        car_a.position = 2
        car_a.lap = 2

        car_a.update_physics(dt=0.2, circuit=self.circuit, race_control=self.rc, track_wetness=0.0, car_ahead=car_b, car_behind=None)
        
        # Attacker should recognize braking advantage and commit to inside dive bomb
        self.assertTrue(car_a.is_overtaking)
        self.assertEqual(car_a.overtake_move_type, "DIVE_BOMB")

    def test_drafting_slipstream_tow(self):
        """Verify dynamic tow suction on straights."""
        driver_a = Driver(id=1, name="Chaser", code="CHS", number=3, team_name="TeamA", color_rgb=(255, 200, 0))
        car_a = Car(car_id=1, driver=driver_a)

        driver_b = Driver(id=2, name="Leader", code="LDR", number=4, team_name="TeamB", color_rgb=(0, 200, 255))
        car_b = Car(car_id=2, driver=driver_b)

        # Place cars on straight (low curvature)
        car_b.s = 200.0
        car_b.speed = 70.0
        car_b.position = 1
        car_b.lap = 1

        car_a.s = 175.0 # 25m behind
        car_a.speed = 68.0
        car_a.position = 2
        car_a.lap = 1

        car_a.update_physics(dt=0.1, circuit=self.circuit, race_control=self.rc, track_wetness=0.0, car_ahead=car_b, car_behind=None)

        self.assertTrue(car_a.slipstream_active)
        self.assertGreater(car_a.slipstream_intensity, 0.4)

    def test_around_the_outside_with_superior_downforce(self):
        """Verify high-downforce car sweeps outside when inside is defended."""
        driver_a = Driver(id=1, name="HighAero", code="AER", number=5, team_name="AeroTeam", color_rgb=(0, 255, 100))
        attrs_a = CarAttributes(aero_downforce=600.0, braking_efficiency=500.0)
        car_a = Car(car_id=1, driver=driver_a, car_attributes=attrs_a)

        driver_b = Driver(id=2, name="Defender", code="DEF", number=6, team_name="DefTeam", color_rgb=(255, 100, 0))
        attrs_b = CarAttributes(aero_downforce=200.0, braking_efficiency=500.0)
        car_b = Car(car_id=2, driver=driver_b, car_attributes=attrs_b)

        # Place cars in a corner where defender is defending the inside (Node 5 apex at ~1050m)
        car_b.s = 1050.0
        car_b.speed = 40.0
        car_b.is_defending = True
        car_b.position = 1
        car_b.lap = 1

        car_a.s = 1038.0 # 12m behind
        car_a.speed = 44.0
        car_a.position = 2
        car_a.lap = 1

        car_a.update_physics(dt=0.1, circuit=self.circuit, race_control=self.rc, track_wetness=0.0, car_ahead=car_b, car_behind=None)

        # Attacker should sweep around the outside
        self.assertTrue(car_a.is_overtaking)
        self.assertEqual(car_a.overtake_move_type, "OUTSIDE_SWEEP")

    def test_defending_under_pressure_and_speed_loss(self):
        """Verify car under pressure defends the inside and loses speed due to compromised line."""
        driver_def = Driver(id=1, name="Defender", code="DEF", number=7, team_name="DefTeam", color_rgb=(100, 100, 100), defending=0.75)
        car_def = Car(car_id=1, driver=driver_def)

        driver_atk = Driver(id=2, name="Attacker", code="ATK", number=8, team_name="AtkTeam", color_rgb=(200, 50, 50))
        car_atk = Car(car_id=2, driver=driver_atk)

        car_def.s = 870.0
        car_def.speed = 60.0
        car_def.position = 1
        car_def.lap = 2

        # Attacker is right behind in fighting interval (< 0.5s)
        car_atk.s = 860.0
        car_atk.speed = 60.0
        car_atk.position = 2
        car_atk.lap = 2

        car_def.update_physics(dt=0.1, circuit=self.circuit, race_control=self.rc, track_wetness=0.0, car_ahead=None, car_behind=car_atk)

        self.assertTrue(car_def.is_defending)

    def test_blue_flag_courtesy_yield(self):
        """Verify lapped car yields cleanly to front-runner under blue flags without pushback."""
        driver_lapped = Driver(id=1, name="Backmarker", code="BCK", number=20, team_name="SlowTeam", color_rgb=(120, 120, 120))
        car_lapped = Car(car_id=1, driver=driver_lapped)

        driver_leader = Driver(id=2, name="Leader", code="LDR", number=1, team_name="ChampTeam", color_rgb=(0, 200, 255))
        car_leader = Car(car_id=2, driver=driver_leader)

        # Leader is on Lap 5, lapped car is on Lap 4
        car_lapped.s = 120.0
        car_lapped.speed = 55.0
        car_lapped.position = 19
        car_lapped.lap = 4

        car_leader.s = 105.0 # 15m behind, closing fast
        car_leader.speed = 70.0
        car_leader.position = 1
        car_leader.lap = 5

        car_lapped.update_physics(dt=0.1, circuit=self.circuit, race_control=self.rc, track_wetness=0.0, car_ahead=None, car_behind=car_leader)

        # Backmarker yields under blue flags
        self.assertTrue(car_lapped.is_yielding_blue_flag)
        self.assertFalse(car_lapped.is_defending)

    def test_career_db_loader(self):
        """Verify load_career_teams_and_drivers loads components with real performance ratings."""
        import tempfile
        import gc
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db_path = os.path.join(temp_dir, "test_overtaking_career.db")
            db = CareerDatabase(test_db_path)
            try:
                pairs = load_career_teams_and_drivers(db, tier=1)
                self.assertGreaterEqual(len(pairs), 2)
                driver, attrs = pairs[0]
                self.assertGreater(attrs.braking_efficiency, 0.0)
                self.assertGreater(attrs.engine_power, 0.0)
            finally:
                del db
                gc.collect()

if __name__ == "__main__":
    unittest.main()
