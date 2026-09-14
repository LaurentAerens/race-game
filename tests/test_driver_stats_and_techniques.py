import unittest

from src.core.car import Car
from src.core.driver import Driver
from src.core.race_control import RaceControl
from src.data.default_tracks import create_emerald_ring
from src.database.db_manager import CarAttributes


class TestDriverStatsAndTechniques(unittest.TestCase):
    def setUp(self):
        self.circuit = create_emerald_ring()
        self.rc = RaceControl()

    def test_driving_style_inference(self):
        """Verify that driving styles infer correctly from stat distributions."""
        # Late braker
        d_brake = Driver(
            id=1,
            name="Braker",
            code="BRK",
            number=1,
            team_name="T1",
            color_rgb=(255, 0, 0),
            braking=0.95,
            cornering=0.82,
            tire_management=0.80,
            overtaking=0.85,
            aggression=0.80,
        )
        self.assertEqual(d_brake.driving_style, "LATE_BRAKER")

        # Smooth roller
        d_smooth = Driver(
            id=2,
            name="Smooth",
            code="SMO",
            number=2,
            team_name="T2",
            color_rgb=(0, 255, 0),
            braking=0.80,
            cornering=0.96,
            tire_management=0.82,
            overtaking=0.80,
            aggression=0.60,
        )
        self.assertEqual(d_smooth.driving_style, "SMOOTH_ROLLER")

        # Tire whisperer
        d_tire = Driver(
            id=3,
            name="Whisperer",
            code="WHS",
            number=3,
            team_name="T3",
            color_rgb=(0, 0, 255),
            speed=0.82,
            braking=0.80,
            cornering=0.82,
            tire_management=0.96,
            consistency=0.94,
        )
        self.assertEqual(d_tire.driving_style, "TIRE_WHISPERER")

        # Aggressive hunter
        d_hunt = Driver(
            id=4,
            name="Hunter",
            code="HNT",
            number=4,
            team_name="T4",
            color_rgb=(255, 255, 0),
            braking=0.84,
            cornering=0.84,
            overtaking=0.94,
            aggression=0.88,
            consistency=0.75,
        )
        self.assertEqual(d_hunt.driving_style, "AGGRESSIVE_HUNTER")

    def test_cornering_speed_and_technique_impact(self):
        """Verify Smooth Roller and higher cornering skill yield higher mid-corner rolling speed."""
        drv_smooth = Driver(
            id=1,
            name="Smooth",
            code="SMO",
            number=1,
            team_name="T1",
            color_rgb=(0, 255, 0),
            cornering=0.95,
            braking=0.80,
        )
        drv_avg = Driver(
            id=2, name="Avg", code="AVG", number=2, team_name="T2", color_rgb=(255, 0, 0), cornering=0.75, braking=0.80
        )

        attrs = CarAttributes(aero_downforce=500.0, braking_efficiency=500.0)
        car_smooth = Car(car_id=1, driver=drv_smooth, car_attributes=attrs)
        car_avg = Car(car_id=2, driver=drv_avg, car_attributes=attrs)

        # Place at corner approach entering apex (s = 910m in Emerald Ring)
        car_smooth.s = 910.0
        car_smooth.speed = 65.0
        car_avg.s = 910.0
        car_avg.speed = 65.0

        # Simulate 5 steps through corner apex
        for _ in range(5):
            car_smooth.update_physics(0.1, self.circuit, self.rc, track_wetness=0.0, car_ahead=None, car_behind=None)
            car_avg.update_physics(0.1, self.circuit, self.rc, track_wetness=0.0, car_ahead=None, car_behind=None)

        # Smooth roller carries higher apex speed
        self.assertGreater(car_smooth.speed, car_avg.speed)

    def test_tire_management_and_wear_preservation(self):
        """Verify that high tire management and Tire Whisperer style degrade tires significantly slower."""
        drv_whisperer = Driver(
            id=1, name="Whisperer", code="WHS", number=1, team_name="T1", color_rgb=(0, 0, 255), tire_management=0.96
        )
        drv_hard = Driver(
            id=2,
            name="Aggressive",
            code="AGG",
            number=2,
            team_name="T2",
            color_rgb=(255, 0, 0),
            tire_management=0.65,
            aggression=0.90,
            overtaking=0.92,
        )

        car_whisperer = Car(car_id=1, driver=drv_whisperer)
        car_hard = Car(car_id=2, driver=drv_hard)

        # Run 2 full laps for both cars
        lap_dist = self.circuit.length
        dt = 0.1
        sim_steps = int((lap_dist * 2.0) / (45.0 * dt))

        for _ in range(sim_steps):
            car_whisperer.speed = 45.0
            car_hard.speed = 45.0
            car_whisperer.update_physics(dt, self.circuit, self.rc, track_wetness=0.0, car_ahead=None, car_behind=None)
            car_hard.update_physics(dt, self.circuit, self.rc, track_wetness=0.0, car_ahead=None, car_behind=None)

        # Whisperer should have preserved much more tire life (lower wear_pct)
        self.assertLess(car_whisperer.tires.wear_pct, car_hard.tires.wear_pct)
        wear_diff = car_hard.tires.wear_pct - car_whisperer.tires.wear_pct
        self.assertGreater(wear_diff, 1.5, "Tire wear difference should be noticeably distinct")

    def test_consistency_and_mistake_susceptibility(self):
        """Verify low-consistency drivers face higher mistake risk under intense pressure."""
        drv_calm = Driver(
            id=1, name="Calm", code="CLM", number=1, team_name="T1", color_rgb=(0, 255, 0), consistency=0.96
        )
        drv_erratic = Driver(
            id=2, name="Erratic", code="ERR", number=2, team_name="T2", color_rgb=(255, 0, 0), consistency=0.65
        )

        # Compare mistake risk under pressure
        risk_calm = drv_calm.get_mistake_risk(under_pressure=True)
        risk_erratic = drv_erratic.get_mistake_risk(under_pressure=True)

        self.assertGreater(
            risk_erratic, risk_calm * 2.0, "Erratic driver should have over double the mistake risk under pressure"
        )

    def test_wet_weather_skill_impact(self):
        """Verify skilled wet weather drivers achieve higher effective grip and speed in wet conditions."""
        drv_rainmaster = Driver(
            id=1,
            name="RainMaster",
            code="RNM",
            number=1,
            team_name="T1",
            color_rgb=(0, 200, 255),
            wet_skill=0.95,
            speed=0.80,
        )
        drv_novice = Driver(
            id=2,
            name="RainNovice",
            code="NVC",
            number=2,
            team_name="T2",
            color_rgb=(100, 100, 100),
            wet_skill=0.60,
            speed=0.80,
        )

        car_rainmaster = Car(car_id=1, driver=drv_rainmaster, initial_compound="WET")
        car_novice = Car(car_id=2, driver=drv_novice, initial_compound="WET")

        car_rainmaster.s = 910.0  # Corner entry
        car_rainmaster.speed = 45.0
        car_novice.s = 910.0
        car_novice.speed = 45.0

        wetness = 0.70
        for _ in range(5):
            car_rainmaster.update_physics(
                0.1, self.circuit, self.rc, track_wetness=wetness, car_ahead=None, car_behind=None
            )
            car_novice.update_physics(
                0.1, self.circuit, self.rc, track_wetness=wetness, car_ahead=None, car_behind=None
            )

        self.assertGreater(car_rainmaster.speed, car_novice.speed)


if __name__ == "__main__":
    unittest.main()
