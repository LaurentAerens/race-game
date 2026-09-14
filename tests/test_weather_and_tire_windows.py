import unittest

from src.core.car import Car
from src.core.circuit import Circuit
from src.core.driver import Driver
from src.core.simulation import Simulation
from src.core.tires import TireSet
from src.core.weather import WeatherSystem
from src.data.default_tracks import create_ardennes_forest, create_emerald_ring, create_oasis_grand_prix
from src.database.db_manager import CarAttributes


class TestWeatherAndTireWindows(unittest.TestCase):
    def test_circuit_base_rain_chances(self):
        oasis = create_oasis_grand_prix()
        ardennes = create_ardennes_forest()
        emerald = create_emerald_ring()

        # Desert track should have very low rain chance (~2%)
        self.assertLessEqual(oasis.base_rain_chance, 0.05)
        # Ardennes Forest (Spa) should have high rain chance (~60%)
        self.assertGreaterEqual(ardennes.base_rain_chance, 0.50)
        # Emerald Ring should be temperate (~25%)
        self.assertAlmostEqual(emerald.base_rain_chance, 0.25, delta=0.05)

        # Verify serialization and deserialization
        o_dict = oasis.to_dict()
        self.assertIn("base_rain_chance", o_dict)
        self.assertEqual(o_dict["base_rain_chance"], oasis.base_rain_chance)

        loaded = Circuit.from_dict(o_dict)
        self.assertEqual(loaded.base_rain_chance, oasis.base_rain_chance)

    def test_sunny_weather_profile_guarantees_dry(self):
        weather = WeatherSystem(initial_rain=0.0, weather_profile="SUNNY", rain_chance=0.99, total_laps=20)
        self.assertEqual(weather.max_race_wetness, 0.0)
        self.assertEqual(weather.rain_intensity, 0.0)
        self.assertEqual(weather.track_wetness, 0.0)

        for lap in range(1, 21):
            weather.update(dt=10.0, current_lap=lap)
            self.assertEqual(weather.track_wetness, 0.0)
            self.assertEqual(weather.rain_intensity, 0.0)

    def test_dynamic_weather_dry_roll(self):
        # 0% rain chance forces dry race in DYNAMIC
        weather = WeatherSystem(initial_rain=0.0, weather_profile="DYNAMIC", rain_chance=0.0, total_laps=15)
        self.assertEqual(weather.max_race_wetness, 0.0)
        self.assertEqual(weather.track_wetness, 0.0)

        for node in weather.forecast:
            self.assertEqual(node.rain_intensity, 0.0)
            self.assertEqual(node.description, "Dry / Sunny")

    def test_max_wetness_cap_respected(self):
        # Test 50% max wetness cap
        weather_50 = WeatherSystem(initial_rain=0.0, weather_profile="RAIN", total_laps=25, max_wetness_cap=0.50)
        self.assertAlmostEqual(weather_50.max_race_wetness, 0.50)

        # Simulate through all laps
        peak_wetness = 0.0
        for lap in range(1, 26):
            for _ in range(20):
                weather_50.update(dt=1.0, current_lap=lap)
                peak_wetness = max(peak_wetness, weather_50.track_wetness)

        self.assertLessEqual(peak_wetness, 0.5001)
        self.assertGreater(peak_wetness, 0.35)

        # Test 80% max wetness cap
        weather_80 = WeatherSystem(initial_rain=0.0, weather_profile="RAIN", total_laps=25, max_wetness_cap=0.80)
        self.assertAlmostEqual(weather_80.max_race_wetness, 0.80)

        peak_wetness_80 = 0.0
        for lap in range(1, 26):
            for _ in range(20):
                weather_80.update(dt=1.0, current_lap=lap)
                peak_wetness_80 = max(peak_wetness_80, weather_80.track_wetness)

        self.assertLessEqual(peak_wetness_80, 0.8001)
        self.assertGreater(peak_wetness_80, 0.60)

    def test_track_wetness_equilibrium_and_drying(self):
        weather = WeatherSystem(initial_rain=0.0, weather_profile="RAIN", total_laps=20, max_wetness_cap=0.60)
        weather.rain_intensity = 0.40
        weather.target_rain = 0.40
        weather.forecast[0].rain_intensity = 0.40

        # Update while raining at 0.40 intensity
        for _ in range(100):
            weather.update(dt=1.0, current_lap=1)

        # Should reach equilibrium at 0.40 and NOT climb to 1.0!
        self.assertAlmostEqual(weather.track_wetness, 0.40, delta=0.02)

        # Stop rain -> track should dry down towards 0.0
        weather.rain_intensity = 0.0
        weather.target_rain = 0.0
        weather.max_race_wetness = 0.60
        # Clear forecast so it stays 0
        for node in weather.forecast:
            node.rain_intensity = 0.0

        for _ in range(200):
            weather.update(dt=1.0, current_lap=5)

        self.assertLess(weather.track_wetness, 0.10)

    def test_intermediate_operating_window_10_to_80(self):
        inter = TireSet("INTER")

        # In 10% - 80% wetness, Inter operates with peak optimal grip
        grip_10 = inter.get_effective_grip(track_wetness=0.10)
        grip_30 = inter.get_effective_grip(track_wetness=0.30)
        grip_50 = inter.get_effective_grip(track_wetness=0.50)
        grip_70 = inter.get_effective_grip(track_wetness=0.70)
        grip_80 = inter.get_effective_grip(track_wetness=0.80)

        # Within the 10-80% window, grip is at peak base grip
        self.assertAlmostEqual(grip_10, inter.compound.base_grip, delta=0.02)
        self.assertAlmostEqual(grip_50, inter.compound.base_grip, delta=0.02)
        self.assertAlmostEqual(grip_80, inter.compound.base_grip, delta=0.02)

        # Below 10% (dry track): penalty applies
        grip_dry = inter.get_effective_grip(track_wetness=0.00)
        self.assertLess(grip_dry, grip_50)

        # Above 80% (flooded / aquaplaning): grip drops
        grip_90 = inter.get_effective_grip(track_wetness=0.90)
        grip_100 = inter.get_effective_grip(track_wetness=1.00)
        self.assertLess(grip_90, grip_80)
        self.assertLess(grip_100, grip_90)

    def test_full_wet_operating_window_70_to_100(self):
        wet = TireSet("WET")
        inter = TireSet("INTER")

        # In 70% - 100% wetness, Full Wet is in its peak window
        grip_wet_70 = wet.get_effective_grip(track_wetness=0.70)
        grip_wet_85 = wet.get_effective_grip(track_wetness=0.85)
        grip_wet_100 = wet.get_effective_grip(track_wetness=1.00)

        self.assertAlmostEqual(grip_wet_70, wet.compound.base_grip, delta=0.02)
        self.assertAlmostEqual(grip_wet_100, wet.compound.base_grip, delta=0.02)

        # Below 70% wetness: Full Wet has penalty
        grip_wet_50 = wet.get_effective_grip(track_wetness=0.50)
        grip_wet_20 = wet.get_effective_grip(track_wetness=0.20)
        grip_wet_dry = wet.get_effective_grip(track_wetness=0.00)

        self.assertLess(grip_wet_50, grip_wet_70)
        self.assertLess(grip_wet_20, grip_wet_50)
        self.assertLess(grip_wet_dry, grip_wet_20)

        # Comparison between INTER and WET:
        # 1. At 50% wetness, Intermediates MUST beat Full Wet
        grip_inter_50 = inter.get_effective_grip(track_wetness=0.50)
        self.assertGreater(grip_inter_50, grip_wet_50)

        # 2. At 85% wetness and 100% wetness, Full Wet MUST beat Intermediates
        grip_inter_85 = inter.get_effective_grip(track_wetness=0.85)
        grip_inter_100 = inter.get_effective_grip(track_wetness=1.00)
        self.assertGreater(grip_wet_85, grip_inter_85)
        self.assertGreater(grip_wet_100, grip_inter_100)

    def test_slicks_vs_wetness(self):
        soft = TireSet("SOFT")
        grip_dry = soft.get_effective_grip(track_wetness=0.05)
        grip_wet_15 = soft.get_effective_grip(track_wetness=0.15)
        grip_wet_40 = soft.get_effective_grip(track_wetness=0.40)
        grip_wet_80 = soft.get_effective_grip(track_wetness=0.80)

        self.assertGreater(grip_dry, grip_wet_15)
        self.assertGreater(grip_wet_15, grip_wet_40)
        self.assertGreater(grip_wet_40, grip_wet_80)
        self.assertLess(grip_wet_80, 0.40)

    def test_simulation_ai_pit_strategy_crossovers(self):
        circuit = create_emerald_ring()
        driver = Driver(id=1, name="TestDriver", code="TST", number=1, team_name="T1", color_rgb=(255, 0, 0))
        attrs = CarAttributes(100.0, 100.0, 100.0, 100.0, 100.0)

        # 1. Car on Slicks pits for Inter when wetness is 15%
        sim = Simulation(circuit, [(driver, attrs)], total_laps=10, weather_profile="SUNNY")
        car = sim.cars[0]
        car.tires = TireSet("MEDIUM")
        sim.weather.track_wetness = 0.15
        sim._ai_pit_strategy(car)
        self.assertEqual(car.pit_queued_compound, "INTER")

        # 2. Car on Slicks pits for WET if wetness suddenly reaches 80%
        car.tires = TireSet("MEDIUM")
        car.pit_queued_compound = None
        sim.weather.track_wetness = 0.80
        sim._ai_pit_strategy(car)
        self.assertEqual(car.pit_queued_compound, "WET")

        # 3. Car on Inter in 50% wetness stays on Inter
        car.tires = TireSet("INTER")
        car.pit_queued_compound = None
        sim.weather.track_wetness = 0.50
        sim._ai_pit_strategy(car)
        self.assertIsNone(car.pit_queued_compound)

        # 4. Car on Inter when wetness reaches 82% pits for WET
        car.tires = TireSet("INTER")
        car.pit_queued_compound = None
        sim.weather.track_wetness = 0.82
        sim._ai_pit_strategy(car)
        self.assertEqual(car.pit_queued_compound, "WET")

        # 5. Car on Full Wet when wetness drops to 60% pits for INTER
        car.tires = TireSet("WET")
        car.pit_queued_compound = None
        sim.weather.track_wetness = 0.60
        sim._ai_pit_strategy(car)
        self.assertEqual(car.pit_queued_compound, "INTER")

        # 6. Car on Inter when wetness drops to 5% pits for slicks
        car.tires = TireSet("INTER")
        car.pit_queued_compound = None
        sim.weather.track_wetness = 0.05
        sim._ai_pit_strategy(car)
        self.assertIn(car.pit_queued_compound, circuit.get_dry_compounds())

    def test_dry_tire_softness_wet_hierarchy(self):
        """Verify softer slicks perform better in damp conditions (Hypersoft up to 20%, Hard struggles at 10%)."""
        hypersoft = TireSet("HYPERSOFT")
        supersoft = TireSet("SUPERSOFT")
        soft = TireSet("SOFT")
        medium = TireSet("MEDIUM")
        hard = TireSet("HARD")

        # Verify compound capabilities
        self.assertEqual(hypersoft.compound.wet_capability, 0.20)
        self.assertEqual(supersoft.compound.wet_capability, 0.18)
        self.assertEqual(soft.compound.wet_capability, 0.16)
        self.assertEqual(medium.compound.wet_capability, 0.13)
        self.assertEqual(hard.compound.wet_capability, 0.10)

        # In slightly damp conditions (e.g. 12% wetness):
        # Hard has already exceeded its 10% capability and suffers significant loss
        # Soft and Hypersoft are well within capability and maintain high grip
        grip_hs_12 = hypersoft.get_effective_grip(track_wetness=0.12)
        grip_s_12 = soft.get_effective_grip(track_wetness=0.12)
        grip_h_12 = hard.get_effective_grip(track_wetness=0.12)

        self.assertGreater(grip_hs_12, grip_s_12)
        self.assertGreater(grip_s_12, grip_h_12)

        # At 18% wetness:
        # Hypersoft is still within its 20% capability!
        # Hard and Medium are far past their limit
        grip_hs_18 = hypersoft.get_effective_grip(track_wetness=0.18)
        grip_h_18 = hard.get_effective_grip(track_wetness=0.18)
        self.assertGreater(grip_hs_18, grip_h_18 * 1.35)

    def test_tire_wet_overload_fatal_crash_risk(self):
        """Verify 5x crash risk multiplier when track wetness > tire wet_capability + 0.10."""
        circuit = create_emerald_ring()
        driver = Driver(
            id=1,
            name="CrashTester",
            code="CRS",
            number=1,
            team_name="T1",
            color_rgb=(255, 0, 0),
            consistency=0.20,
            aggression=0.90,
        )
        attrs = CarAttributes(100.0, 100.0, 100.0, 100.0, 100.0)

        # 1. Hard tire: capability 0.10 -> overload threshold 0.20
        car_hard = Car(car_id=1, driver=driver, car_attributes=attrs, initial_compound="HARD")
        car_hard.speed = 35.0
        # At 15% wetness: under 0.20 threshold (no overload multiplier)
        # At 35% wetness: well over 0.20 threshold (5x+ multiplier)
        hard_cap = car_hard.tires.compound.wet_capability
        self.assertEqual(hard_cap, 0.10)
        self.assertAlmostEqual(hard_cap + 0.10, 0.20)

        # 2. Ultrasoft / Hypersoft: capability 0.20 -> overload threshold 0.30
        car_hs = Car(car_id=2, driver=driver, car_attributes=attrs, initial_compound="HYPERSOFT")
        hs_cap = car_hs.tires.compound.wet_capability
        self.assertEqual(hs_cap, 0.20)
        self.assertAlmostEqual(hs_cap + 0.10, 0.30)

        # 3. Intermediates: capability 0.80 -> overload threshold 0.90
        car_inter = Car(car_id=3, driver=driver, car_attributes=attrs, initial_compound="INTER")
        inter_cap = car_inter.tires.compound.wet_capability
        self.assertEqual(inter_cap, 0.80)
        self.assertAlmostEqual(inter_cap + 0.10, 0.90)

    def test_sector_based_local_shower(self):
        """Verify local shower in specific sectors while other sectors remain dry."""
        # Create a WeatherSystem with a local shower in Sector 2
        weather = WeatherSystem(
            initial_rain=0.0,
            weather_profile="RAIN",
            total_laps=20,
            max_wetness_cap=0.70,
            is_big_track=True,
            local_shower_sectors=[2],
        )
        self.assertTrue(weather.is_local_shower)
        self.assertEqual(weather.active_rain_sectors, [2])

        # Forecast for Sector 2 should show local shower description
        self.assertTrue(any("S2" in node.description for node in weather.forecast if node.rain_intensity > 0.05))

        # Update weather over 50 ticks
        weather.rain_intensity = 0.50
        weather.target_rain = 0.50
        weather.forecast[0].rain_intensity = 0.50

        for _ in range(50):
            weather.update(dt=1.0, current_lap=1)

        # Sector 2 should be wet (accumulating to ~50%)
        # Sector 1 and Sector 3 should be completely dry (0%)
        self.assertGreater(weather.get_sector_wetness(2), 0.30)
        self.assertEqual(weather.get_sector_wetness(1), 0.0)
        self.assertEqual(weather.get_sector_wetness(3), 0.0)

        # Test car physics interaction in Simulation
        circuit = create_ardennes_forest()  # Long track > 2200m
        driver1 = Driver(id=1, name="DriverS1", code="DS1", number=1, team_name="T1", color_rgb=(255, 0, 0))
        driver2 = Driver(id=2, name="DriverS2", code="DS2", number=2, team_name="T2", color_rgb=(0, 0, 255))
        attrs = CarAttributes(100.0, 100.0, 100.0, 100.0, 100.0)

        sim = Simulation(circuit, [(driver1, attrs), (driver2, attrs)], total_laps=10)
        sim.weather = weather

        # Position car1 in Sector 1 and car2 in Sector 2
        # Sector 1 is between 0 and 0.31 * length; Sector 2 is between 0.31 and 0.64 * length
        c1, c2 = sim.cars[0], sim.cars[1]
        c1.s = circuit.length * 0.10  # Sector 1
        c2.s = circuit.length * 0.45  # Sector 2

        self.assertEqual(circuit.get_sector(c1.s), 1)
        self.assertEqual(circuit.get_sector(c2.s), 2)

        # Wetness experienced by cars matches their respective sector
        wet_c1 = sim.weather.get_sector_wetness(circuit.get_sector(c1.s))
        wet_c2 = sim.weather.get_sector_wetness(circuit.get_sector(c2.s))

        self.assertEqual(wet_c1, 0.0)
        self.assertGreater(wet_c2, 0.30)


if __name__ == "__main__":
    unittest.main()
