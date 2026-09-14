from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class RadioMessage:
    speaker: str  # "PIT WALL", "RACE ENGINEER", "DRIVER", "RACE CONTROL"
    text: str
    category: str  # "WEATHER", "TIRES", "INCIDENT", "STRATEGY"
    priority: int  # 1 (Low) to 3 (Urgent)
    duration: float = 6.0


class RadioMessageSystem:
    """
    Simulates authentic Motorsport Manager / F1 Pit Wall Radio communications.
    Triggers dynamic situational messages when weather shifts, tires drop off, or battles heat up.
    """

    def __init__(self):
        self.active_message: Optional[RadioMessage] = None
        self.message_timer: float = 0.0
        self.history: List[RadioMessage] = []

        # State tracking to avoid message spam
        self._last_rain_level: float = 0.0
        self._warned_rain_incoming: bool = False
        self._warned_damp: bool = False
        self._warned_local_shower: bool = False
        self._warned_intermediate_window: bool = False
        self._warned_full_wet: bool = False
        self._warned_drying: bool = False
        self._warned_tires: Dict[int, bool] = {}  # car_id -> bool

    def post_message(self, speaker: str, text: str, category: str = "INFO", priority: int = 2, duration: float = 6.0):
        """Dispatches a new radio message popup."""
        msg = RadioMessage(speaker=speaker, text=text, category=category, priority=priority, duration=duration)
        self.active_message = msg
        self.message_timer = duration
        self.history.insert(0, msg)
        if len(self.history) > 30:
            self.history.pop()

    def update(self, dt: float, current_lap: int, weather, player_cars):
        """Monitors race state and triggers contextual radio messages."""
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.active_message = None

        # 1. Weather Forecast Alerts (Look 3-5 laps ahead)
        forecast_slice = weather.get_forecast_slice(current_lap, window=4)
        rain_ahead = any(node.rain_intensity > 0.25 for node in forecast_slice[1:])

        if rain_ahead and not self._warned_rain_incoming and weather.track_wetness < 0.10:
            self._warned_rain_incoming = True
            self.post_message(
                "PIT WALL", "Weather radar alert: Rain clouds approaching track in ~3 laps!", "WEATHER", 2, 7.0
            )

        # 2. Live Rain & Track Wetness Transitions
        wet = weather.track_wetness
        if wet > 0.04 and not self._warned_damp and not (player_cars and player_cars[0].tires.compound.tier == "WET"):
            self._warned_damp = True
            drv_name = player_cars[0].driver.name.split()[0] if player_cars else "Driver"
            self.post_message(
                f"DRIVER ({drv_name})",
                "I can feel rain drops on my visor! Track is getting slippery.",
                "WEATHER",
                2,
                6.0,
            )

        # Local shower warning
        if getattr(weather, "is_local_shower", False) and not self._warned_local_shower:
            if any(weather.get_sector_wetness(s) > 0.12 for s in getattr(weather, "active_rain_sectors", [])):
                self._warned_local_shower = True
                secs = getattr(weather, "active_rain_sectors", [2])
                sec_str = "/".join(f"Sector {s}" for s in sorted(secs))
                dry_secs = [s for s in (1, 2, 3) if s not in secs]
                dry_str = f"Sector {dry_secs[0]}" if len(dry_secs) == 1 else "other sectors"
                self.post_message(
                    "PIT WALL", f"Local shower in {sec_str}! {dry_str} is dry. Softs or Inters?", "WEATHER", 3, 8.0
                )

        # Intermediate tire window: 10% - 80%
        if wet >= 0.10 and not self._warned_intermediate_window:
            self._warned_intermediate_window = True
            self.post_message(
                "RACE ENGINEER",
                "Track wetness reached 10%! Intermediate tire window is OPEN. Box to switch?",
                "WEATHER",
                3,
                8.0,
            )

        # Full Wet tire window: 70% - 100%
        if wet >= 0.70 and not self._warned_full_wet:
            self._warned_full_wet = True
            self.post_message(
                "PIT WALL",
                "Track wetness over 70%! Deep standing water detected, Full Wet tire window is OPEN.",
                "WEATHER",
                3,
                8.0,
            )

        # Track Drying down from Full Wet to Inters
        if wet < 0.68 and self._warned_full_wet:
            self._warned_full_wet = False
            self.post_message(
                "PIT WALL", "Track conditions improving! Intermediate tire crossover is open.", "WEATHER", 2, 7.0
            )

        # Track Drying down to Slicks (< 10%)
        if wet < 0.10 and self._warned_intermediate_window and not self._warned_drying:
            self._warned_drying = True
            self.post_message(
                "PIT WALL", "Racing line is drying up rapidly! Slicks crossover window approaching.", "WEATHER", 2, 7.0
            )

        # Reset rain flags if weather completely dries
        if wet == 0.0:
            self._warned_rain_incoming = False
            self._warned_damp = False
            self._warned_local_shower = False
            self._warned_intermediate_window = False
            self._warned_full_wet = False
            self._warned_drying = False

        # 3. Tire Degradation & Wear Warnings for Player Cars
        for car in player_cars:
            cid = car.id
            wear = car.tires.wear_pct
            cliff = car.tires.compound.cliff_wear_pct
            drv_first = car.driver.name.split()[0]

            if wear > cliff and not self._warned_tires.get(cid, False):
                self._warned_tires[cid] = True
                self.post_message(
                    "RACE ENGINEER",
                    f"{drv_first}, your tires have hit the wear cliff ({int(100 - wear)}% left)! Box this lap.",
                    "TIRES",
                    3,
                    7.0,
                )
            elif wear < 30.0:
                # Reset when fresh tires are fitted
                self._warned_tires[cid] = False
