import random
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class WeatherForecastNode:
    lap: int
    rain_intensity: float  # 0.0 to 1.0
    description: str


class WeatherSystem:
    """
    Manages dynamic race weather, per-sector track wetness accumulation, local showers,
    drying lines, circuit-dependent rain probabilities, and forecast radar.
    """

    def __init__(
        self,
        initial_rain: float = 0.0,
        track_temp: float = 28.0,
        weather_profile: str = "DYNAMIC",
        rain_chance: float = 0.25,
        total_laps: int = 50,
        max_wetness_cap: Optional[float] = None,
        is_big_track: bool = False,
        local_shower_sectors: Optional[List[int]] = None,
    ):
        self.weather_profile = str(weather_profile).upper()
        self.rain_chance = max(0.0, min(1.0, float(rain_chance)))
        self.total_laps = total_laps
        self.track_temp = track_temp
        self.ambient_temp = track_temp - 5.0
        self.is_big_track = is_big_track

        # Maximum wetness ceiling for this race
        self.max_race_wetness = self._determine_max_wetness(max_wetness_cap, initial_rain)
        self.rain_intensity = min(self.max_race_wetness, initial_rain)
        self.target_rain = self.rain_intensity
        init_wet = min(self.max_race_wetness, initial_rain * 0.8)

        # Local shower configuration for larger circuits
        if local_shower_sectors is not None:
            self.is_local_shower = True
            self.active_rain_sectors = list(local_shower_sectors)
        elif self.is_big_track and self.max_race_wetness > 0.05 and random.random() < 0.50:
            self.is_local_shower = True
            # Rain localized to 1 or 2 sectors (e.g. S2, S1-S2, or S2-S3)
            self.active_rain_sectors = random.choice([[2], [1, 2], [2, 3]])
        else:
            self.is_local_shower = False
            self.active_rain_sectors = [1, 2, 3]

        # Per-sector wetness tracking (Sectors 1, 2, 3)
        self.sector_wetness: Dict[int, float] = {
            s: (init_wet if s in self.active_rain_sectors else 0.0) for s in (1, 2, 3)
        }
        self._track_wetness = init_wet

        # Forecast radar for upcoming laps
        self.forecast: List[WeatherForecastNode] = []
        self._generate_initial_forecast(total_laps=total_laps)

    @property
    def track_wetness(self) -> float:
        if hasattr(self, "sector_wetness") and self.sector_wetness:
            return sum(self.sector_wetness.values()) / len(self.sector_wetness)
        return getattr(self, "_track_wetness", 0.0)

    @track_wetness.setter
    def track_wetness(self, val: float):
        self._track_wetness = max(0.0, min(1.0, float(val)))
        if hasattr(self, "sector_wetness"):
            for s in (1, 2, 3):
                self.sector_wetness[s] = self._track_wetness

    def get_sector_wetness(self, sector: int) -> float:
        """Returns the current wetness for a specific sector (1, 2, or 3)."""
        if hasattr(self, "sector_wetness") and sector in self.sector_wetness:
            return self.sector_wetness[sector]
        return self.track_wetness

    def _determine_max_wetness(self, max_wetness_cap: Optional[float], initial_rain: float) -> float:
        """Determines the maximum peak wetness ceiling for the race."""
        if max_wetness_cap is not None:
            return max(0.0, min(1.0, float(max_wetness_cap)))

        if self.weather_profile == "SUNNY":
            return max(0.0, initial_rain)

        if self.weather_profile == "RAIN":
            # Guaranteed wet race: either moderate (65-80%) or heavy (85-100%)
            if random.random() < 0.50:
                cap = round(random.uniform(0.65, 0.80), 2)
            else:
                cap = round(random.uniform(0.85, 1.00), 2)
            return max(cap, initial_rain)

        # DYNAMIC weather: roll against circuit's base rain chance
        will_rain = (random.random() < self.rain_chance) or (initial_rain > 0.05)
        if not will_rain:
            return max(0.0, initial_rain)

        # Rain will occur: determine severity of this race's rain event
        # ~35% light shower (35-55%), ~45% moderate rain (65-80%), ~20% heavy storm (85-100%)
        roll = random.random()
        if roll < 0.35:
            cap = round(random.uniform(0.35, 0.55), 2)
        elif roll < 0.80:
            cap = round(random.uniform(0.65, 0.80), 2)
        else:
            cap = round(random.uniform(0.85, 1.00), 2)

        return max(cap, initial_rain)

    def _generate_initial_forecast(self, total_laps: int):
        self.forecast = []

        # If dry race or wetness cap is zero, guarantee completely dry forecast
        if self.max_race_wetness <= 0.01:
            for lap in range(1, total_laps + 1):
                self.forecast.append(WeatherForecastNode(lap=lap, rain_intensity=0.0, description="Dry / Sunny"))
            return

        # Rain event parameters
        if self.rain_intensity > 0.05 or self.weather_profile == "RAIN":
            start_lap = 1
        else:
            start_lap = random.randint(1, max(2, int(total_laps * 0.65)))

        duration = random.randint(max(3, int(total_laps * 0.30)), max(6, int(total_laps * 0.85)))
        end_lap = min(total_laps + 10, start_lap + duration)
        peak_intensity = min(1.0, self.max_race_wetness)

        curr = self.rain_intensity
        for lap in range(1, total_laps + 1):
            if start_lap <= lap <= end_lap:
                ramp_laps = max(1, int((end_lap - start_lap) * 0.25))
                if (lap - start_lap) < ramp_laps and self.weather_profile != "RAIN" and self.rain_intensity <= 0.05:
                    target = peak_intensity * ((lap - start_lap + 1) / (ramp_laps + 1))
                elif (end_lap - lap) < ramp_laps:
                    target = peak_intensity * max(0.0, (end_lap - lap) / ramp_laps)
                else:
                    target = peak_intensity * random.uniform(0.92, 1.0)

                curr = min(self.max_race_wetness, max(0.0, target))
            else:
                curr = 0.0

            if curr < 0.03:
                curr = 0.0

            desc = "Dry / Sunny"
            if curr >= 0.70:
                desc = "Heavy Rain"
            elif curr >= 0.25:
                desc = "Moderate Rain"
            elif curr > 0.03:
                desc = "Light Rain / Drizzle"

            if self.is_local_shower and curr > 0.03:
                sec_str = "/".join(f"S{s}" for s in sorted(self.active_rain_sectors))
                desc = f"{desc} ({sec_str})"

            self.forecast.append(WeatherForecastNode(lap=lap, rain_intensity=round(curr, 3), description=desc))

    def update(self, dt: float, current_lap: int):
        """Simulates rain evolution and per-sector track wetness physics."""
        # Interpolate target rain towards current lap forecast
        for node in self.forecast:
            if node.lap == current_lap:
                self.target_rain = min(self.max_race_wetness, node.rain_intensity)
                break

        # Smooth rain transition
        rate = 0.02 * dt
        if self.rain_intensity < self.target_rain:
            self.rain_intensity = min(self.target_rain, self.rain_intensity + rate)
        elif self.rain_intensity > self.target_rain:
            self.rain_intensity = max(self.target_rain, self.rain_intensity - rate)

        # Update per-sector wetness accumulation / evaporation equilibrium
        for sec in (1, 2, 3):
            if sec in self.active_rain_sectors:
                sec_target = min(self.max_race_wetness, self.rain_intensity)
            else:
                sec_target = 0.0

            cur_sec_wet = self.sector_wetness[sec]
            if cur_sec_wet < sec_target:
                # Rain accumulating in this sector towards target equilibrium
                accum_rate = max(0.02, self.rain_intensity) * 0.08 * dt
                self.sector_wetness[sec] = min(sec_target, cur_sec_wet + accum_rate)
            elif cur_sec_wet > sec_target:
                # Rain stopped or drying in this sector
                evap_rate = (0.015 + (self.track_temp / 50.0) * 0.02) * dt
                self.sector_wetness[sec] = max(sec_target, cur_sec_wet - evap_rate)

    def get_forecast_slice(
        self, current_lap: int, window: int = 8, radar_tier: int = 0, radar_eq_lvl: int = 0
    ) -> List[WeatherForecastNode]:
        """
        Returns forecast nodes for the next N laps.
        If radar_tier or radar equipment is upgraded, the lookahead window expands
        and forecast intensity certainty increases.
        """
        effective_window = window + (radar_tier * 2) + (radar_eq_lvl * 1)
        slice_nodes = [f for f in self.forecast if current_lap <= f.lap <= current_lap + effective_window]
        return slice_nodes
