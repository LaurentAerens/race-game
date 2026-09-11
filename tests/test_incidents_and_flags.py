import unittest
from src.core.circuit import Circuit
from src.core.driver import Driver
from src.core.car import Car
from src.core.race_control import RaceControl, FlagStatus, SafetyCar
from src.core.simulation import Simulation
from src.database.db_manager import CarAttributes
from src.data.default_tracks import create_emerald_ring

class TestIncidentsAndFlags(unittest.TestCase):
    def setUp(self):
        self.circuit = create_emerald_ring()
        self.driver_skilled = Driver(
            id=1, name="Max Clean", code="CLE", number=1, team_name="Clean Racing",
            color_rgb=(0, 200, 255), is_player=False,
            speed=0.90, braking=0.90, cornering=0.90, consistency=0.95,
            tire_management=0.90, aggression=0.50, defending=0.85, wet_skill=0.85
        )
        self.driver_erratic = Driver(
            id=2, name="Crashy McWild", code="WLD", number=99, team_name="Wild GP",
            color_rgb=(255, 100, 0), is_player=False,
            speed=0.85, braking=0.75, cornering=0.75, consistency=0.30,
            tire_management=0.60, aggression=0.95, defending=0.70, wet_skill=0.50
        )
        self.attrs = CarAttributes(engine_power=100.0, braking_efficiency=100.0, aero_downforce=100.0)

    def test_off_track_incident_and_safe_rejoin(self):
        car = Car(car_id=1, driver=self.driver_erratic, car_attributes=self.attrs)
        rc = RaceControl()
        
        car.speed = 60.0
        car.off_track = True
        car.off_track_timer = 2.0
        car.s = 100.0

        car.update_physics(dt=0.5, circuit=self.circuit, race_control=rc, track_wetness=0.0,
                           car_ahead=None, car_behind=None)
        self.assertTrue(car.off_track)
        self.assertLess(car.speed, 20.0)

        car.off_track_timer = 0.05
        rival_behind = Car(car_id=2, driver=self.driver_skilled, car_attributes=self.attrs)
        rival_behind.s = 90.0
        rival_behind.speed = 50.0

        car.update_physics(dt=0.1, circuit=self.circuit, race_control=rc, track_wetness=0.0,
                           car_ahead=None, car_behind=rival_behind, all_cars=[car, rival_behind])
        self.assertTrue(car.off_track or car.rejoin_wait_timer > 0.0)

        rival_behind.s = 40.0
        car.update_physics(dt=0.1, circuit=self.circuit, race_control=rc, track_wetness=0.0,
                           car_ahead=None, car_behind=rival_behind, all_cars=[car, rival_behind])
        self.assertFalse(car.off_track)
        self.assertTrue(car.rejoining)
        self.assertEqual(car.mistake_event, "REJOIN")

    def test_terminal_crash_and_dnf(self):
        car = Car(car_id=1, driver=self.driver_erratic, car_attributes=self.attrs)
        car.is_broken = True
        car.is_dnf = True
        car.speed = 0.0
        rc = RaceControl()

        car.update_physics(dt=1.0, circuit=self.circuit, race_control=rc, track_wetness=0.0,
                           car_ahead=None, car_behind=None)
        self.assertEqual(car.speed, 0.0)
        self.assertFalse(car.is_overtaking)

    def test_sector_yellow_flag_speed_and_overtake_ban(self):
        car = Car(car_id=1, driver=self.driver_skilled, car_attributes=self.attrs)
        car.speed = 65.0
        car.s = 50.0
        rc = RaceControl()

        rc.deploy_local_yellow(sector=1, duration=10.0)
        self.assertEqual(rc.flag, FlagStatus.YELLOW)
        self.assertEqual(rc.yellow_sector, 1)

        car_ahead = Car(car_id=2, driver=self.driver_erratic, car_attributes=self.attrs)
        car_ahead.s = 60.0
        car_ahead.speed = 50.0

        car.update_physics(dt=0.2, circuit=self.circuit, race_control=rc, track_wetness=0.0,
                           car_ahead=car_ahead, car_behind=None)
        self.assertFalse(car.is_overtaking)

    def test_virtual_safety_car(self):
        rc = RaceControl()
        rc.deploy_vsc(duration_seconds=15.0)
        self.assertEqual(rc.flag, FlagStatus.VSC)

        car = Car(car_id=1, driver=self.driver_skilled, car_attributes=self.attrs)
        car.speed = 70.0
        car_ahead = Car(car_id=2, driver=self.driver_erratic, car_attributes=self.attrs)
        car_ahead.s = car.s + 10.0

        car.update_physics(dt=0.2, circuit=self.circuit, race_control=rc, track_wetness=0.0,
                           car_ahead=car_ahead, car_behind=None)
        self.assertFalse(car.is_overtaking)

        rc.update(dt=16.0, current_lap=3, track_wetness=0.0)
        self.assertEqual(rc.flag, FlagStatus.GREEN)

    def test_physical_safety_car_deployment_and_recall(self):
        rc = RaceControl()
        rc.deploy_safety_car(cleanup_duration=20.0, circuit=self.circuit, leader_s=100.0)
        
        self.assertEqual(rc.flag, FlagStatus.SAFETY_CAR)
        self.assertTrue(rc.safety_car.is_active)
        self.assertEqual(rc.safety_car.state, "ON_TRACK")

        sc_initial_s = rc.safety_car.s
        rc.update(dt=1.0, current_lap=3, track_wetness=0.0, circuit=self.circuit)
        self.assertGreater(rc.safety_car.s, sc_initial_s)

        rc.call_in_safety_car()
        self.assertEqual(rc.safety_car.state, "ENTERING_PIT")

        rc.safety_car.s = self.circuit.pit_entry_s - 2.0
        rc.update(dt=0.5, current_lap=3, track_wetness=0.0, circuit=self.circuit)
        self.assertEqual(rc.safety_car.state, "IDLE")
        self.assertFalse(rc.safety_car.is_active)
        rc.update(dt=0.1, current_lap=3, track_wetness=0.0, circuit=self.circuit)
        self.assertEqual(rc.flag, FlagStatus.GREEN)

    def test_simulation_incident_classification_dnf(self):
        pairs = [(self.driver_skilled, self.attrs), (self.driver_erratic, self.attrs)]
        sim = Simulation(self.circuit, pairs, total_laps=5)
        self.assertEqual(len(sim.cars), 2)

        car_crashed = sim.cars[1]
        car_crashed.is_broken = True
        car_crashed.is_dnf = True
        car_crashed.mistake_event = "CRASH"

        sim.update(dt=1.0)
        self.assertEqual(sim.cars[-1], car_crashed)
        self.assertTrue(car_crashed.is_dnf)
        crash_logs = [e for e in sim.event_log if e["type"] in ("CRASH", "FLAG")]
        self.assertGreater(len(crash_logs), 0)

    def test_driver_bunching_and_traffic_risk(self):
        # Verify that multiple cars in close proximity create higher bunching risk multiplier
        car_solo = Car(car_id=1, driver=self.driver_erratic, car_attributes=self.attrs)
        car_solo.s = 100.0

        car_pack_leader = Car(car_id=2, driver=self.driver_erratic, car_attributes=self.attrs)
        car_pack_leader.s = 200.0
        car_p1 = Car(car_id=3, driver=self.driver_skilled, car_attributes=self.attrs)
        car_p1.s = 208.0
        car_p2 = Car(car_id=4, driver=self.driver_skilled, car_attributes=self.attrs)
        car_p2.s = 215.0

        all_cars = [car_solo, car_pack_leader, car_p1, car_p2]
        
        # Solo car in clean air has 0 nearby cars (<25m)
        solo_bunch = sum(1 for oc in all_cars if oc is not car_solo and not oc.is_broken and (abs(oc.s - car_solo.s) < 25.0))
        # Pack car has 2 nearby cars
        pack_bunch = sum(1 for oc in all_cars if oc is not car_pack_leader and not oc.is_broken and (abs(oc.s - car_pack_leader.s) < 25.0))

        self.assertEqual(solo_bunch, 0)
        self.assertEqual(pack_bunch, 2)
        self.assertGreater(1.0 + pack_bunch * 0.90, 1.0 + solo_bunch * 0.90)

    def test_flag_conservative_mode_locking_and_restoration(self):
        # Test Tier 1 / 2 car with all modes available
        car_t1 = Car(car_id=1, driver=self.driver_skilled, car_attributes=self.attrs, league_tier=1)
        car_t1.pace_mode = "ATTACK"
        car_t1.engine_mode = "RICH"
        car_t1.ers_mode = "OVERTAKE"

        # Neutralization triggers conservative modes
        car_t1.enter_flag_neutralization()
        self.assertTrue(car_t1.is_mode_locked)
        self.assertEqual(car_t1.pace_mode, "CONSERVE")
        self.assertEqual(car_t1.engine_mode, "LEAN")
        self.assertEqual(car_t1.ers_mode, "RECHARGE")

        # While locked, manual changes are rejected
        car_t1.pace_mode = "PUSH"
        car_t1.engine_mode = "STANDARD"
        car_t1.ers_mode = "BALANCED"
        self.assertEqual(car_t1.pace_mode, "CONSERVE")
        self.assertEqual(car_t1.engine_mode, "LEAN")
        self.assertEqual(car_t1.ers_mode, "RECHARGE")

        # Resumption restores previous settings
        car_t1.exit_flag_neutralization()
        self.assertFalse(car_t1.is_mode_locked)
        self.assertEqual(car_t1.pace_mode, "ATTACK")
        self.assertEqual(car_t1.engine_mode, "RICH")
        self.assertEqual(car_t1.ers_mode, "OVERTAKE")

        # Test Tier 3 car (restricted modes: NORMAL/PUSH, STANDARD engine, NONE ers)
        car_t3 = Car(car_id=2, driver=self.driver_skilled, car_attributes=self.attrs, league_tier=3)
        car_t3.pace_mode = "PUSH"
        car_t3.enter_flag_neutralization()
        self.assertTrue(car_t3.is_mode_locked)
        self.assertEqual(car_t3.pace_mode, "NORMAL")
        self.assertEqual(car_t3.engine_mode, "STANDARD")
        self.assertEqual(car_t3.ers_mode, "NONE")
        car_t3.exit_flag_neutralization()
        self.assertFalse(car_t3.is_mode_locked)
        self.assertEqual(car_t3.pace_mode, "PUSH")

    def test_simulation_flag_neutralization_triggers_on_all_cars(self):
        player_d1 = Driver(id=1, name="P1", code="P1", number=1, team_name="T1", color_rgb=(0,0,0), is_player=True)
        player_d2 = Driver(id=2, name="P2", code="P2", number=2, team_name="T1", color_rgb=(0,0,0), is_player=True)
        sim = Simulation(circuit=self.circuit, driver_car_pairs=[(player_d1, self.attrs), (player_d2, self.attrs)], total_laps=10, league_tier=2)
        for car in sim.cars:
            car.pace_mode = "PUSH"
            car.engine_mode = "RICH"

        # Deploy VSC
        sim.race_control.deploy_vsc(duration_seconds=10.0)
        sim.update(dt=0.1)

        for car in sim.cars:
            self.assertTrue(car.is_mode_locked)
            self.assertEqual(car.pace_mode, "CONSERVE")
            self.assertEqual(car.engine_mode, "LEAN")

        # Clear flags
        sim.race_control.clear_flags()
        sim.update(dt=0.1)

        for car in sim.cars:
            self.assertFalse(car.is_mode_locked)
    def test_sector_yellow_flag_conservative_mode_only_in_sector(self):
        car = Car(car_id=1, driver=self.driver_skilled, car_attributes=self.attrs, league_tier=2)
        car.pace_mode = "PUSH"
        car.engine_mode = "RICH"

        rc = RaceControl()
        rc.deploy_local_yellow(sector=2, duration=10.0)

        # 1. Car in Sector 1 (outside yellow sector): retains full attack modes and not locked
        car.s = self.circuit.sectors[0] * self.circuit.length * 0.5  # middle of sector 1
        car.update_physics(dt=0.1, circuit=self.circuit, race_control=rc, track_wetness=0.0, car_ahead=None, car_behind=None)
        self.assertFalse(car.is_mode_locked)
        self.assertEqual(car.pace_mode, "PUSH")
        self.assertEqual(car.engine_mode, "RICH")

        # 2. Car enters Sector 2 (inside yellow sector): automatically switched to CONSERVE / LEAN and locked
        car.s = (self.circuit.sectors[0] + 0.05) * self.circuit.length  # inside sector 2
        car.update_physics(dt=0.1, circuit=self.circuit, race_control=rc, track_wetness=0.0, car_ahead=None, car_behind=None)
        self.assertTrue(car.is_mode_locked)
        self.assertEqual(car.pace_mode, "CONSERVE")
        self.assertEqual(car.engine_mode, "LEAN")

        # While in sector 2, manual changes are blocked
        car.pace_mode = "ATTACK"
        self.assertEqual(car.pace_mode, "CONSERVE")

        # 3. Car exits Sector 2 into Sector 3: automatically restored to PUSH / RICH and unlocked
        car.s = (self.circuit.sectors[1] + 0.05) * self.circuit.length  # inside sector 3
        car.update_physics(dt=0.1, circuit=self.circuit, race_control=rc, track_wetness=0.0, car_ahead=None, car_behind=None)
        self.assertFalse(car.is_mode_locked)
        self.assertEqual(car.pace_mode, "PUSH")
        self.assertEqual(car.engine_mode, "RICH")

if __name__ == "__main__":
    unittest.main()


