from enum import Enum
from typing import Any, Optional, Tuple


class FlagStatus(Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    VSC = "VSC"
    SAFETY_CAR = "SAFETY_CAR"
    RED = "RED"


class SafetyCar:
    """
    Physical Safety Car entity that navigates the circuit, regulates pack pace,
    and returns to the pit lane when called in.
    """

    def __init__(self, speed: float = 36.0):
        self.s: float = 0.0
        self.speed: float = speed  # m/s (~130 km/h)
        self.lateral_offset: float = 0.0
        self.world_x: float = 0.0
        self.world_y: float = 0.0
        self.heading: float = 0.0
        self.is_active: bool = False
        self.state: str = "IDLE"  # "IDLE", "DEPLOYING", "ON_TRACK", "ENTERING_PIT"
        self.strobe_timer: float = 0.0
        self.strobe_on: bool = False
        self.color_rgb: Tuple[int, int, int] = (255, 204, 0)
        self.laps_led: int = 0

    def update(self, dt: float, circuit: Any, leader_car: Optional[Any] = None):
        if not self.is_active or not circuit or circuit.length <= 0:
            return

        # Advance along circuit
        new_s = self.s + self.speed * dt
        if new_s >= circuit.length:
            new_s = new_s % circuit.length
            self.laps_led += 1

        # Check for pit lane entry when called in
        if self.state == "ENTERING_PIT" and getattr(circuit, "pit_lane_enabled", False):
            dist_to_pit = (circuit.pit_entry_s - self.s) % circuit.length
            if dist_to_pit <= 8.0 or (self.s <= circuit.pit_entry_s <= (self.s + self.speed * dt)):
                # Pulled into pit lane, mission accomplished
                self.is_active = False
                self.state = "IDLE"
                self.s = circuit.pit_entry_s
                return

        self.s = new_s
        self.world_x, self.world_y = circuit.get_position(self.s, self.lateral_offset)
        self.heading = circuit.get_heading(self.s)

        # Flashing emergency strobe light on roof (alternates every 0.15s)
        self.strobe_timer += dt
        if self.strobe_timer >= 0.15:
            self.strobe_timer = 0.0
            self.strobe_on = not self.strobe_on


class RaceControl:
    """Manages flags, Safety Car interventions, DRS enabling/disabling, sector yellow zones and session rules."""

    def __init__(self):
        self.flag: FlagStatus = FlagStatus.GREEN
        self.yellow_sector: Optional[int] = None
        self.yellow_timer: float = 0.0
        self.vsc_timer: float = 0.0
        self.sc_cleanup_timer: float = 0.0
        self.safety_car: SafetyCar = SafetyCar(speed=36.0)
        self.drs_enabled: bool = False
        self.safety_car_speed: float = 36.0  # m/s (~130 km/h)
        self.vsc_speed_delta: float = 0.60  # Cars must slow to 60% pace
        self.incident_message: str = "RACE START"
        self.message_timer: float = 4.0
        self.incident_car_id: Optional[int] = None

    def update(
        self,
        dt: float,
        current_lap: int,
        track_wetness: float,
        circuit: Optional[Any] = None,
        leader_car: Optional[Any] = None,
    ):
        if self.message_timer > 0:
            self.message_timer -= dt

        # DRS rule: Disabled under Safety Car, VSC, Yellow, or Wet track (>0.25)
        if current_lap >= 2 and self.flag == FlagStatus.GREEN and track_wetness < 0.20:
            if not self.drs_enabled:
                self.drs_enabled = True
                self.set_message("DRS ENABLED")
        else:
            if self.drs_enabled:
                self.drs_enabled = False
                self.set_message("DRS DISABLED")

        # Flag timers and state transitions
        if self.flag == FlagStatus.YELLOW:
            self.yellow_timer -= dt
            if self.yellow_timer <= 0:
                self.clear_flags()

        elif self.flag == FlagStatus.VSC:
            self.vsc_timer -= dt
            if self.vsc_timer <= 0:
                self.clear_flags()

        elif self.flag == FlagStatus.SAFETY_CAR:
            if circuit:
                self.safety_car.update(dt, circuit, leader_car)

            if self.safety_car.state == "ON_TRACK":
                self.sc_cleanup_timer -= dt
                if self.sc_cleanup_timer <= 0:
                    self.call_in_safety_car()
            elif not self.safety_car.is_active:
                # Safety car has entered pit lane, resume racing
                self.clear_flags()

    def deploy_local_yellow(self, sector: int, duration: float = 10.0, message: Optional[str] = None):
        if self.flag in (FlagStatus.SAFETY_CAR, FlagStatus.VSC, FlagStatus.RED):
            return  # Higher neutralization already in effect
        self.flag = FlagStatus.YELLOW
        self.yellow_sector = sector
        self.yellow_timer = duration
        self.drs_enabled = False
        msg = message or f"YELLOW FLAG IN SECTOR {sector}"
        self.set_message(msg)

    def deploy_vsc(self, duration_seconds: float = 16.0, message: str = "VIRTUAL SAFETY CAR"):
        if self.flag in (FlagStatus.SAFETY_CAR, FlagStatus.RED):
            return
        self.flag = FlagStatus.VSC
        self.yellow_sector = None
        self.vsc_timer = duration_seconds
        self.drs_enabled = False
        self.set_message(message)

    def deploy_safety_car(
        self,
        cleanup_duration: float = 25.0,
        message: str = "SAFETY CAR DEPLOYED",
        circuit: Optional[Any] = None,
        leader_s: float = 0.0,
    ):
        self.flag = FlagStatus.SAFETY_CAR
        self.yellow_sector = None
        self.sc_cleanup_timer = cleanup_duration
        self.drs_enabled = False
        self.safety_car.is_active = True
        self.safety_car.state = "ON_TRACK"
        self.safety_car.laps_led = 0

        if circuit and getattr(circuit, "pit_lane_enabled", False):
            self.safety_car.s = circuit.pit_exit_s
        else:
            c_len = circuit.length if circuit else 1000.0
            self.safety_car.s = (leader_s + 40.0) % c_len

        if circuit:
            self.safety_car.world_x, self.safety_car.world_y = circuit.get_position(
                self.safety_car.s, self.safety_car.lateral_offset
            )
            self.safety_car.heading = circuit.get_heading(self.safety_car.s)

        self.set_message(message)

    def call_in_safety_car(self):
        if self.safety_car.is_active:
            self.safety_car.state = "ENTERING_PIT"
            self.set_message("SAFETY CAR IN THIS LAP")

    def clear_flags(self):
        self.flag = FlagStatus.GREEN
        self.yellow_sector = None
        self.yellow_timer = 0.0
        self.vsc_timer = 0.0
        self.sc_cleanup_timer = 0.0
        self.safety_car.is_active = False
        self.safety_car.state = "IDLE"
        self.set_message("TRACK CLEAR - GREEN FLAG")

    def set_message(self, msg: str):
        self.incident_message = msg
        self.message_timer = 5.0
