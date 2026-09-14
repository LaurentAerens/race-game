import os
import unittest

from src.core.car import Car
from src.core.osm_importer import OSMImporter
from src.core.race_control import RaceControl
from src.core.simulation import Simulation
from src.core.tires import TireSet
from src.data.default_tracks import create_emerald_ring
from src.data.teams import load_teams_and_drivers_from_db


class TestRaceSimulator(unittest.TestCase):
    def setUp(self):
        import tempfile

        self.circuit = create_emerald_ring()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_race_game.db")
        self.pairs = load_teams_and_drivers_from_db(self.db_path)

    def tearDown(self):
        import gc

        gc.collect()
        if hasattr(self, "temp_dir"):
            try:
                self.temp_dir.cleanup()
            except Exception:
                pass

    def test_database_persistence_and_seeding(self):
        self.assertEqual(len(self.pairs), 20)
        driver, car_attrs = self.pairs[0]
        self.assertGreater(driver.speed, 0.0)
        self.assertGreater(driver.braking, 0.0)
        self.assertGreater(car_attrs.engine_power, 50.0)
        self.assertGreater(car_attrs.braking_efficiency, 50.0)
        self.assertGreater(car_attrs.aero_downforce, 50.0)

    def test_car_brakes_and_engine_physics(self):
        driver, car_attrs = self.pairs[0]
        car = Car(car_id=1, driver=driver, car_attributes=car_attrs, initial_compound="MEDIUM")
        rc = RaceControl()

        # Advance physics
        car.update_physics(
            dt=1.0, circuit=self.circuit, race_control=rc, track_wetness=0.0, car_ahead=None, car_behind=None
        )
        self.assertGreater(car.speed, 0.0)
        self.assertGreater(car.s, 0.0)

    def test_simulation_coordinator(self):
        sim = Simulation(self.circuit, self.pairs, total_laps=10)
        self.assertEqual(len(sim.cars), 20)
        self.assertEqual(sim.current_lap, 1)

        # Advance simulation
        sim.update(5.0)
        self.assertGreater(sim.race_time, 0.0)
        self.assertIsNotNone(sim.cars[0])

    def test_tire_wear_and_compounds(self):
        soft_set = TireSet("SOFT")
        self.assertEqual(soft_set.compound.code, "S")
        initial_grip = soft_set.get_effective_grip(track_wetness=0.0)

        soft_set.apply_wear(dt=60.0, pace_multiplier=1.9, aggressive_driving=1.2)
        self.assertGreater(soft_set.wear_pct, 0.0)
        worn_grip = soft_set.get_effective_grip(track_wetness=0.0)
        self.assertLess(worn_grip, initial_grip)

    def test_osm_mercator_projection(self):
        coords = [(43.7347, 7.4205), (43.7360, 7.4215), (43.7352, 7.4230), (43.7340, 7.4220)]
        osm_circuit = OSMImporter.from_coordinates_list("Monaco Loop", coords)
        self.assertGreater(osm_circuit.length, 50.0)
        self.assertEqual(len(osm_circuit.control_points), 4)

    def test_car_collision_side_by_side_separation(self):
        sim = Simulation(self.circuit, self.pairs[:2], total_laps=5)
        c1, c2 = sim.cars[0], sim.cars[1]
        c1.s = 100.0
        c1.lateral_offset = 0.0
        c1.world_x, c1.world_y = self.circuit.get_position(c1.s, c1.lateral_offset)

        c2.s = 100.0
        c2.lateral_offset = 0.2
        c2.world_x, c2.world_y = self.circuit.get_position(c2.s, c2.lateral_offset)

        sim._resolve_car_collisions(0.1)
        lat_diff = abs(c2.lateral_offset - c1.lateral_offset)
        self.assertGreaterEqual(lat_diff, 0.9)

    def test_car_collision_rear_end_non_penetration(self):
        sim = Simulation(self.circuit, self.pairs[:2], total_laps=5)
        leader, chaser = sim.cars[0], sim.cars[1]
        leader.s = 102.0
        leader.lateral_offset = 0.0
        leader.speed = 30.0
        leader.world_x, leader.world_y = self.circuit.get_position(leader.s, leader.lateral_offset)

        chaser.s = 101.0
        chaser.lateral_offset = 0.0
        chaser.speed = 60.0
        chaser.world_x, chaser.world_y = self.circuit.get_position(chaser.s, chaser.lateral_offset)

        sim._resolve_car_collisions(0.1)
        self.assertLessEqual(chaser.speed, leader.speed)
        s_gap = (leader.s - chaser.s) % self.circuit.length
        self.assertGreaterEqual(s_gap, 2.5)


if __name__ == "__main__":
    unittest.main()
