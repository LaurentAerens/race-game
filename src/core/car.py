import math
import random
from typing import Optional, List, Dict, Tuple
from .driver import Driver
from .tires import TireSet
from .circuit import Circuit
from .race_control import RaceControl, FlagStatus
from .race_weekend import CarSetup
from ..database.db_manager import CarAttributes

class Car:
    """
    Realistic 2D Open-Wheel Formula Car physics model.
    Features aerodynamic wake (dirty air), slipstreaming, multi-lane overtaking,
    outbraking in corner entries, fuel weight, and tire thermodynamics.
    """
    def __init__(self, car_id: int, driver: Driver, car_attributes: Optional[CarAttributes] = None, 
                 initial_compound: str = "MEDIUM", setup: Optional[CarSetup] = None, 
                 setup_confidence: float = 50.0, practice_bonuses: Optional[Dict[str, float]] = None,
                 league_tier: int = 3, initial_part_durabilities: Optional[Dict[str, float]] = None):
        self.id = car_id
        self.driver = driver
        self.attributes = car_attributes or CarAttributes()
        self.tires = TireSet(initial_compound)
        self.setup = setup or CarSetup()
        self.setup_confidence = setup_confidence
        self.practice_bonuses = practice_bonuses or {}
        self.league_tier: int = league_tier
        
        # Position & Kinematics
        self.s: float = 0.0              # Track distance (meters)
        self.lap: int = 0
        self.speed: float = 0.0          # Current velocity (m/s)
        self.lateral_offset: float = 0.0 # -left, +right relative to track width
        self.target_lateral: float = 0.0
        self.heading: float = 0.0
        self.world_x: float = 0.0
        self.world_y: float = 0.0

        # Powertrain & Energy
        self.fuel_kg: float = 50.0       # Starting fuel (kg)
        self._ers_pct: float = 0.0 if self.league_tier >= 3 else 100.0  # Hybrid battery %
        self._pace_mode: str = "NORMAL"   # CONSERVE, NORMAL, PUSH, ATTACK
        self._engine_mode: str = "STANDARD"# LEAN, STANDARD, RICH
        self._ers_mode: str = "NONE" if self.league_tier >= 3 else "AUTO"      # AUTO, RECHARGE, BALANCED, OVERTAKE

        # Flag Neutralization State & Mode Locking
        self.is_mode_locked: bool = False
        self._saved_pace_mode: Optional[str] = None
        self._saved_engine_mode: Optional[str] = None
        self._saved_ers_mode: Optional[str] = None

        # Aerodynamics & Overtaking
        self.drs_available: bool = False
        self.drs_active: bool = False
        self.slipstream_active: bool = False
        self.slipstream_intensity: float = 0.0
        self.in_dirty_air: bool = False
        self.is_overtaking: bool = False
        self.is_defending: bool = False
        self.is_yielding_blue_flag: bool = False
        self.overtake_move_type: Optional[str] = None
        self.smoke_timer: float = 0.0
        self.battle_partner_id: Optional[int] = None
        self.locked_up: bool = False
        self.lockup_timer: float = 0.0
        self.ran_wide: bool = False
        self.ran_wide_timer: float = 0.0
        self.mistake_event: Optional[str] = None

        # Incidents, Damage & Safety
        self.is_broken: bool = False
        self.is_dnf: bool = False
        self.damage_pct: float = 0.0
        self.off_track: bool = False
        self.off_track_timer: float = 0.0
        self.rejoining: bool = False
        self.rejoin_wait_timer: float = 0.0

        # Pit Stop State
        self.box_this_lap: bool = False
        self.pit_queued_compound: str = "HARD"
        self.in_pit_lane: bool = False
        self.pit_s: float = 0.0
        self.pit_state: str = "TRACK"    # TRACK, APPROACH, IN_BOX, EXITING
        self.pit_timer: float = 0.0      # Seconds remaining in box
        self.total_pit_stops: int = 0
        self.last_pit_duration: float = 0.0

        # Lap & Timing Stats
        self.position: int = 1
        self.gap_to_leader: float = 0.0
        self.interval_to_ahead: float = 0.0
        self.current_lap_time: float = 0.0
        self.last_lap_time: float = 0.0
        self.best_lap_time: float = float('inf')
        self.s1_time: float = 0.0
        self.s2_time: float = 0.0
        self.s3_time: float = 0.0
        self.current_sector: int = 1
        self.finished: bool = False

        # Component Reliability & Durability Lifecycle
        # Base durability scaled by tier: Tier 3 ~ 65%, Tier 2 ~ 72%, Tier 1 ~ 80% (or custom persisted values)
        default_durability = 65.0 if self.league_tier >= 3 else (72.0 if self.league_tier == 2 else 80.0)
        self.part_durability: Dict[str, float] = {
            "FRONT_WING": default_durability,
            "REAR_WING": default_durability,
            "BRAKES": default_durability,
            "ENGINE": default_durability,
            "SUSPENSION": default_durability,
            "FLOOR": default_durability,
        }
        if initial_part_durabilities:
            for k, v in initial_part_durabilities.items():
                self.part_durability[k] = float(v)

        # Pit Stop Part Replacement & Emergency Repairs
        self.pit_replace_front_wing: bool = False
        self.pit_front_wing_durability: float = 100.0  # Durability of spare to mount
        self.pit_emergency_repairs: bool = False
        self.blunder_part_damaged: Optional[str] = None
        self.blunder_drop_pct: float = 0.0
        
        # Trackside & Pit Crew Modifiers (from facilities and equipment)
        self.pit_modifiers: Dict[str, float] = {
            "base_stop_reduction": 0.0,       # seconds reduced from base 2.4s
            "error_rate_mult": 1.0,           # multiplier on 4% error chance
            "wing_change_time": 4.0,          # seconds for front wing swap
            "repair_time": 14.0,              # seconds for emergency on-the-fly repairs
            "repair_durability_min": 55.0,    # min restored durability %
            "repair_durability_max": 60.0,    # max restored durability %
        }

    @property
    def norm_brakes(self) -> float:
        b = self.attributes.braking_efficiency
        return (b / 500.0) if b > 120.0 else (b / 85.0)

    @property
    def norm_engine(self) -> float:
        e = self.attributes.engine_power
        return (e / 600.0) if e > 120.0 else (e / 85.0)

    @property
    def norm_aero(self) -> float:
        a = self.attributes.aero_downforce
        return (a / 380.0) if a > 120.0 else (a / 85.0)
    @property
    def ers_pct(self) -> float:
        return 0.0 if self.league_tier >= 3 else self._ers_pct

    @ers_pct.setter
    def ers_pct(self, val: float):
        self._ers_pct = 0.0 if self.league_tier >= 3 else max(0.0, min(100.0, val))

    @property
    def pace_mode(self) -> str:
        return self._pace_mode

    @pace_mode.setter
    def pace_mode(self, val: str):
        if self.is_mode_locked:
            return
        val = val.upper()
        if self.league_tier >= 3:
            # Starter Tier: only NORMAL and PUSH
            if val in ["ATTACK", "PUSH"]:
                self._pace_mode = "PUSH"
            else:
                self._pace_mode = "NORMAL"
        else:
            self._pace_mode = val

    @property
    def engine_mode(self) -> str:
        return self._engine_mode

    @engine_mode.setter
    def engine_mode(self, val: str):
        if self.is_mode_locked:
            return
        val = val.upper()
        if self.league_tier >= 3:
            # Starter Tier: only STANDARD engine mode
            self._engine_mode = "STANDARD"
        else:
            self._engine_mode = val

    @property
    def ers_mode(self) -> str:
        return self._ers_mode

    @ers_mode.setter
    def ers_mode(self, val: str):
        if self.is_mode_locked:
            return
        val = val.upper()
        if self.league_tier >= 3:
            self._ers_mode = "NONE"
        else:
            self._ers_mode = val

    def enter_flag_neutralization(self):
        """Switches car to most conservative engine/pace/ERS modes and locks manual changes."""
        if not self.is_mode_locked:
            self._saved_pace_mode = self._pace_mode
            self._saved_engine_mode = self._engine_mode
            self._saved_ers_mode = self._ers_mode

        self.is_mode_locked = True
        # Most conservative settings:
        # Tier 3 only has NORMAL and PUSH, so NORMAL is most conservative. Tier 1 & 2 have CONSERVE.
        self._pace_mode = "NORMAL" if self.league_tier >= 3 else "CONSERVE"
        # Tier 3 only has STANDARD. Tier 1 & 2 have LEAN.
        self._engine_mode = "STANDARD" if self.league_tier >= 3 else "LEAN"
        # Tier 3 has NONE. Tier 1 & 2 have RECHARGE to harvest energy under flag.
        self._ers_mode = "NONE" if self.league_tier >= 3 else "RECHARGE"

    def exit_flag_neutralization(self):
        """Unlocks manual mode changes and restores settings from before flag neutralization."""
        self.is_mode_locked = False
        if self._saved_pace_mode:
            self._pace_mode = self._saved_pace_mode
            self._saved_pace_mode = None
        if self._saved_engine_mode:
            self._engine_mode = self._saved_engine_mode
            self._saved_engine_mode = None
        if self._saved_ers_mode:
            self._ers_mode = self._saved_ers_mode
            self._saved_ers_mode = None
    def update_physics(self, dt: float, circuit: Circuit, race_control: RaceControl, 
                       track_wetness: float, car_ahead: Optional['Car'], car_behind: Optional['Car'],
                       all_cars: Optional[List['Car']] = None):
        """Advances physics based on Car and Driver attributes with multi-lane overtakes."""
        if self.finished or self.is_broken:
            self.speed = 0.0
            self.is_overtaking = False
            return

        # 1. Update timings
        self.mistake_event = None
        self.current_lap_time += dt
        self.current_sector = circuit.get_sector(self.s)

        # Off-track excursion & safe rejoin recovery
        if self.off_track:
            self.off_track_timer -= dt
            self.is_overtaking = False
            if self.off_track_timer <= 0:
                safe_gap = True
                if all_cars:
                    for oc in all_cars:
                        if oc is not self and not oc.is_broken and not oc.off_track:
                            dist_behind = (self.s - oc.s) % circuit.length
                            if 0 < dist_behind < 22.0:
                                safe_gap = False
                                break
                elif car_behind and not car_behind.is_broken and not car_behind.off_track:
                    dist_behind = (self.s - car_behind.s) % circuit.length
                    if 0 < dist_behind < 22.0:
                        safe_gap = False

                if safe_gap or self.rejoin_wait_timer >= 3.0:
                    self.off_track = False
                    self.rejoining = True
                    self.rejoin_wait_timer = 0.0
                    self.mistake_event = "REJOIN"
                    self.target_lateral = circuit.get_racing_line_offset(self.s)
                else:
                    self.rejoin_wait_timer += dt

        if self.rejoining and abs(self.lateral_offset - self.target_lateral) < 1.0:
            self.rejoining = False

        # Lockup recovery
        if self.lockup_timer > 0:
            self.lockup_timer -= dt
            if self.lockup_timer <= 0:
                self.locked_up = False

        # Ran-wide mistake recovery
        if self.ran_wide_timer > 0:
            self.ran_wide_timer -= dt
            if self.ran_wide_timer <= 0:
                self.ran_wide = False

        # 2. Pit Lane Logic
        if self.in_pit_lane:
            self._update_pit_lane(dt, circuit)
            return

        # Check for pit entry trigger
        if self.box_this_lap and circuit.pit_lane_enabled:
            dist_to_entry = (circuit.pit_entry_s - self.s) % circuit.length
            # Trigger when reaching the pit entry threshold
            if dist_to_entry <= 6.0 or (self.s <= circuit.pit_entry_s <= (self.s + self.speed * dt)):
                self.in_pit_lane = True
                self.pit_state = "APPROACH"
                self.pit_s = 0.0
                self.s = circuit.pit_entry_s
                # Seamless transition from circuit edge into pit entry spline
                self.lateral_offset = circuit.get_pit_side_sign() * (circuit.get_width(self.s) * 0.45)
                self.box_this_lap = False
                self._update_pit_lane(dt, circuit)
                return


        # Smoke timer decay
        if self.smoke_timer > 0:
            self.smoke_timer = max(0.0, self.smoke_timer - dt)

        # 3. Aerodynamics, Wake & Corner Geometry Lookahead
        self.drs_active = False
        self.slipstream_active = False
        self.slipstream_intensity = 0.0
        self.in_dirty_air = False

        curvature = circuit.get_curvature(self.s)
        local_width = circuit.get_width(self.s)
        is_corner = (curvature > 0.0035)

        dist_to_apex, apex_curv, inside_sign = circuit.get_corner_apex_ahead(self.s, lookahead_m=160.0)
        inside_offset = inside_sign * (local_width * 0.28)
        outside_offset = -inside_sign * (local_width * 0.28)
        is_corner_entry = (dist_to_apex < 60.0 and apex_curv > 0.0035)

        # 4. Drafting & Dirty Air Evaluation
        if car_ahead and not car_ahead.in_pit_lane:
            gap_dist = (car_ahead.s - self.s) % circuit.length
            if 0 < gap_dist < 60.0:
                if is_corner:
                    self.in_dirty_air = True
                elif dist_to_apex > 35.0 and gap_dist > 4.0:
                    self.slipstream_active = True
                    self.slipstream_intensity = max(0.0, 1.0 - (gap_dist - 4.0) / 56.0)

        # 5. Realistic Grip, Downforce & Setup Physics
        effective_grip = self.tires.get_effective_grip(track_wetness)
        if self.in_dirty_air:
            dirty_loss = 0.15 - (self.norm_aero * 0.06)
            effective_grip *= max(0.70, (1.0 - dirty_loss))

        # Wet line skill bonus: skilled wet drivers find grip away from polished line
        if track_wetness > 0.25:
            wet_line_bonus = 1.0 + (self.driver.wet_skill - 0.50) * 0.18 * track_wetness
            effective_grip *= wet_line_bonus

        conf_factor = 0.94 + 0.10 * (self.setup_confidence / 100.0)
        effective_grip *= conf_factor
        driver_skill = self.driver.get_skill_factor(track_wetness)

        wing_aero_factor = 0.85 + 0.15 * (self.setup.front_wing / 100.0) + 0.15 * (self.setup.rear_wing / 100.0)
        aero_mult = (1.30 + 0.70 * self.norm_aero) * wing_aero_factor

        # Radius-dependent corner speed (outside line allows wider radius and higher rolling speed)
        # Driver technique and cornering skill directly modulate apex roll-through speed
        driver_apex_factor = self.driver.get_apex_speed_multiplier()
        if curvature > 1e-4:
            base_r = 1.0 / curvature
            # Shifting toward outside line increases effective turning radius
            r_eff = max(6.0, base_r - inside_sign * self.lateral_offset)
            corner_max = math.sqrt((effective_grip * 9.81 * aero_mult) * r_eff) * driver_apex_factor
        else:
            corner_max = (80.0 + 16.0 * self.norm_engine) * (0.95 + 0.06 * self.driver.speed)

        # Lookahead Corner Entry Braking Point - adjusted by Driver braking technique
        pace_brake_mult = {"CONSERVE": 0.88, "NORMAL": 1.0, "PUSH": 1.08, "ATTACK": 1.16}.get(self.pace_mode, 1.0)
        driver_brake_factor = 0.75 + 0.35 * self.driver.braking
        decel_power = (22.0 + 16.0 * self.norm_brakes + 6.0 * self.driver.braking) * driver_brake_factor * effective_grip * pace_brake_mult
        brake_depth_mult = self.driver.get_brake_depth_multiplier()

        if is_corner_entry:
            apex_safe_speed = math.sqrt((effective_grip * 9.81 * aero_mult) / max(1e-4, apex_curv)) * driver_apex_factor
            req_brake_dist = max(0.0, (self.speed**2 - apex_safe_speed**2) / (2.0 * max(10.0, decel_power))) * brake_depth_mult
            if self.pace_mode == "ATTACK":
                req_brake_dist *= 0.88 # Late braking dive bomb!
            elif self.pace_mode == "CONSERVE":
                req_brake_dist *= 1.12 # Early braking

            if dist_to_apex <= req_brake_dist:
                interp = dist_to_apex / max(1.0, req_brake_dist)
                braking_target = apex_safe_speed + interp * (self.speed - apex_safe_speed)
                corner_max = min(corner_max, braking_target)

        # 6. Defending Under Pressure & Blue Flags
        self.is_defending = False
        self.is_yielding_blue_flag = False

        if car_behind and not car_behind.in_pit_lane:
            # Check for blue flag (car_behind is a lap ahead)
            if car_behind.lap > self.lap:
                dist_behind = (self.s - car_behind.s) % circuit.length
                if 0 < dist_behind < 40.0:
                    self.is_yielding_blue_flag = True
                    self.target_lateral = outside_offset * 1.1
                    corner_max *= 0.86 # Ease off throttle under blue flags
            else:
                # Same-lap battle: under pressure from pursuer
                dist_behind = (self.s - car_behind.s) % circuit.length
                sec_gap_behind = dist_behind / max(20.0, self.speed)
                if 0.05 < sec_gap_behind < 0.80 and not self.is_yielding_blue_flag:
                    self.is_defending = True
                    self.battle_partner_id = car_behind.id
                    # Move to inside line in braking/corner entry
                    if dist_to_apex < (60.0 + self.driver.defending * 15.0):
                        self.target_lateral = inside_offset
                        # Compromised entry and exit line penalty: loses 3-8% speed
                        defensive_speed_penalty = 0.94 - 0.04 * (1.0 - self.driver.defending)
                        corner_max *= defensive_speed_penalty

        # Tier-based powertrain and mode restrictions
        if self.league_tier >= 3:
            self.ers_pct = 0.0
            if self.engine_mode != "STANDARD":
                self.engine_mode = "STANDARD"
            if self.pace_mode not in ["NORMAL", "PUSH"]:
                self.pace_mode = "NORMAL"

        # Fuel weight & engine mix modes
        fuel_weight_factor = 1.0 - (self.fuel_kg * 0.0012)
        pace_mult = {"CONSERVE": 0.94, "NORMAL": 1.0, "PUSH": 1.035, "ATTACK": 1.07}.get(self.pace_mode, 1.0)
        engine_mix_mult = {"LEAN": 0.95, "STANDARD": 1.0, "RICH": 1.05}.get(self.engine_mode, 1.0)

        target_v = corner_max * pace_mult * fuel_weight_factor * (0.87 + driver_skill * 0.17)
        
        gear_speed_delta = (self.setup.gear_ratio - 50.0) * 0.08
        top_speed_cap = (80.0 + 13.0 * self.norm_engine + gear_speed_delta) * engine_mix_mult * fuel_weight_factor

        # DRS bonus on straight
        if circuit.is_in_drs(self.s) and race_control.drs_enabled and self.drs_available:
            self.drs_active = True
            top_speed_cap += 6.5
            target_v += 7.5

        # Dynamic Slipstream Tow bonus
        if self.slipstream_active:
            target_v += 7.5 * self.slipstream_intensity
            top_speed_cap += 6.0 * self.slipstream_intensity
            if not self.is_overtaking and car_ahead:
                # Tuck directly into the leader's wake
                self.target_lateral = car_ahead.lateral_offset

        # ERS Hybrid Modes (Tier 1 & Tier 2)
        if self.league_tier < 3:
            ers_boost_power = 4.0 if self.league_tier == 2 else 5.2 # Standardized spec ERS in Tier 2
            ers_top_cap = 2.5 if self.league_tier == 2 else 3.5
            if self.ers_mode == "OVERTAKE" and self.ers_pct > 1.5:
                target_v += ers_boost_power
                top_speed_cap += ers_top_cap
                self.ers_pct = max(0.0, self.ers_pct - 4.0 * dt)
            elif self.ers_mode == "RECHARGE":
                self.ers_pct = min(100.0, self.ers_pct + 4.5 * dt)
                target_v *= 0.96
            elif self.ers_mode == "AUTO":
                if is_corner:
                    self.ers_pct = min(100.0, self.ers_pct + 3.8 * dt)
                elif (self.drs_active or self.slipstream_active or self.is_overtaking) and self.ers_pct > 10.0:
                    target_v += ers_boost_power * 0.75
                    top_speed_cap += ers_top_cap * 0.75
                    self.ers_pct = max(0.0, self.ers_pct - 3.2 * dt)
                else:
                    if self.ers_pct > 75.0:
                        target_v += 1.2
                        self.ers_pct = max(0.0, self.ers_pct - 0.7 * dt)
                    elif self.ers_pct < 65.0:
                        self.ers_pct = min(100.0, self.ers_pct + 1.2 * dt)
            else: # BALANCED
                if self.ers_pct < 100.0:
                    self.ers_pct = min(100.0, self.ers_pct + 0.8 * dt)
        else:
            self.ers_pct = 0.0

        # Bunching & Traffic Density Incident Risk (number of cars within 25m)
        bunch_count = 0
        if all_cars:
            bunch_count = sum(1 for oc in all_cars if oc is not self and not oc.is_broken and (abs(oc.s - self.s) < 25.0 or (circuit.length - abs(oc.s - self.s)) < 25.0))
        else:
            if car_ahead and not car_ahead.is_broken and ((car_ahead.s - self.s) % circuit.length < 25.0):
                bunch_count += 1
            if car_behind and not car_behind.is_broken and ((self.s - car_behind.s) % circuit.length < 25.0):
                bunch_count += 1

        bunch_mult = 1.0 + bunch_count * 0.90
        driver_risk = (1.25 - self.driver.consistency) * (0.80 + 0.50 * self.driver.aggression)
        if self.is_defending:
            driver_risk *= 1.45
        if track_wetness > 0.25:
            driver_risk *= (1.0 + track_wetness * 0.8)

        # Tire wetness capability check:
        # If track wetness exceeds (tire_wet_capability + 0.10), car has 5x+ higher chance of fatal crash
        # (e.g. Hard at 20%, Ultrasoft at 30%, Intermediates at 90%)
        tire_wet_cap = getattr(self.tires.compound, "wet_capability", 0.10)
        wet_overload_threshold = round(tire_wet_cap + 0.10, 2)
        wet_crash_mult = 1.0
        wet_offtrack_mult = 1.0

        if track_wetness > wet_overload_threshold:
            excess_wet = track_wetness - wet_overload_threshold
            wet_crash_mult = 5.0 + (excess_wet * 15.0)
            wet_offtrack_mult = 3.0 + (excess_wet * 8.0)

        # 1. Terminal Crash Check (broken car / DNF)
        if not self.in_pit_lane and not self.off_track and not self.is_broken and self.speed > 18.0:
            p_crash = 0.000045 * driver_risk * bunch_mult * wet_crash_mult * dt
            if random.random() < p_crash:
                self.is_broken = True
                self.is_dnf = True
                self.damage_pct = 100.0
                self.speed = 0.0
                self.smoke_timer = 2.0
                self.mistake_event = "AQUAPLANE_CRASH" if wet_crash_mult > 1.0 else "CRASH"
                self.target_lateral = outside_offset * 1.35
                self.lateral_offset = self.target_lateral
                self.world_x, self.world_y = circuit.get_position(self.s, self.lateral_offset)
                return

        # 2. Off-track Incident Check (goes into runoff / grass, loses speed and positions)
        if not self.in_pit_lane and not self.off_track and not self.is_broken and not self.ran_wide and not self.locked_up:
            p_offtrack = 0.00055 * driver_risk * bunch_mult * wet_offtrack_mult * dt
            if random.random() < p_offtrack:
                self.off_track = True
                self.off_track_timer = random.uniform(2.5, 4.2)
                self.rejoin_wait_timer = 0.0
                self.speed *= 0.40
                self.target_lateral = outside_offset * 1.35
                self.mistake_event = "OFF_TRACK"
                # Incident damage across aero and chassis elements
                for p in ["FRONT_WING", "FLOOR", "SUSPENSION"]:
                    dmg = random.uniform(8.0, 15.0)
                    self.part_durability[p] = max(0.0, self.part_durability.get(p, 65.0) - dmg)

        # Flags, Safety Car, Sector Yellow & VSC Speed Control
        current_sector = circuit.get_sector(self.s)
        in_yellow_sector = (race_control.yellow_sector == current_sector and race_control.flag == FlagStatus.YELLOW)
        can_overtake = True

        # Dynamic Sector Yellow Neutralization (Conservative mode & locked strictly within yellow sector)
        if in_yellow_sector:
            if not self.is_mode_locked:
                self.enter_flag_neutralization()
        elif race_control.flag == FlagStatus.YELLOW:
            if self.is_mode_locked:
                self.exit_flag_neutralization()

        if self.off_track:
            target_v = min(target_v, 13.5)  # Slow crawl in gravel/runoff
            can_overtake = False
        elif race_control.flag == FlagStatus.SAFETY_CAR:
            target_v = min(target_v, race_control.safety_car_speed)
            can_overtake = False
            # Check proximity to physical safety car
            if getattr(race_control, "safety_car", None) and race_control.safety_car.is_active:
                dist_to_sc = (race_control.safety_car.s - self.s) % circuit.length
                if 0 < dist_to_sc < 25.0:
                    target_v = min(target_v, race_control.safety_car.speed * max(0.65, dist_to_sc / 22.0))
            if car_ahead and not car_ahead.is_broken:
                dist_to_ahead = (car_ahead.s - self.s) % circuit.length
                if 0 < dist_to_ahead < 20.0:
                    target_v = min(target_v, car_ahead.speed * max(0.70, dist_to_ahead / 18.0))
        elif race_control.flag == FlagStatus.VSC:
            target_v = min(target_v, target_v * race_control.vsc_speed_delta)
            can_overtake = False
        elif in_yellow_sector:
            target_v = min(target_v, target_v * 0.78)
            can_overtake = False

        # Pit Lane In-Lap Deceleration: Smoothly slow down approaching pit entry threshold
        if self.box_this_lap and getattr(circuit, "pit_lane_enabled", False):
            dist_to_entry = (circuit.pit_entry_s - self.s) % circuit.length
            if dist_to_entry <= 75.0:
                can_overtake = False
                # Smoothly decelerate from racing speed down toward pit limiter speed (22.2 m/s / 80 km/h)
                approach_factor = max(0.0, min(1.0, dist_to_entry / 75.0))
                pit_approach_speed = 22.2 + (target_v - 22.2) * (approach_factor ** 1.3)
                target_v = min(target_v, pit_approach_speed)

        # Driver Error / Running Wide Check (driven by consistency and pressure)
        if not self.in_pit_lane and not self.locked_up and not self.ran_wide and not self.off_track:
            mistake_chance = self.driver.get_mistake_risk(under_pressure=self.is_defending) * dt
            if random.random() < mistake_chance:
                if is_corner:
                    self.ran_wide = True
                    self.ran_wide_timer = 1.4
                    self.target_lateral = outside_offset * 1.25
                    self.speed *= 0.88
                    
                    # Reliability wear trap: variable mistake drop
                    # 25% chance of severe blunder (-6% to -10%), else minor mistake (-2% to -4%)
                    blunder_candidates = ["FRONT_WING", "FLOOR", "SUSPENSION", "BRAKES"]
                    target_part = random.choice(blunder_candidates)
                    if random.random() < 0.25:
                        drop = random.uniform(6.0, 10.0)
                        self.part_durability[target_part] = max(0.0, self.part_durability.get(target_part, 65.0) - drop)
                        self.blunder_part_damaged = target_part
                        self.blunder_drop_pct = drop
                        self.mistake_event = "BIG_BLUNDER"
                    else:
                        drop = random.uniform(2.0, 4.0)
                        self.part_durability[target_part] = max(0.0, self.part_durability.get(target_part, 65.0) - drop)
                        self.mistake_event = "RAN_WIDE"
                else:
                    self.speed *= 0.92
                    # Oversteer snap wears rear wing or suspension
                    target_part = random.choice(["REAR_WING", "SUSPENSION", "FLOOR"])
                    drop = random.uniform(1.5, 3.5)
                    self.part_durability[target_part] = max(0.0, self.part_durability.get(target_part, 65.0) - drop)
                    self.mistake_event = "SNAP_OVERSTEER"

        # 7. Acceleration and Outbraking
        target_v = min(target_v, top_speed_cap)
        if self.speed < target_v:
            engine_accel_factor = 11.0 + 5.5 * self.norm_engine
            accel = (engine_accel_factor * engine_mix_mult * effective_grip) * max(0.18, (1.0 - (self.speed / top_speed_cap)))
            self.speed = min(target_v, self.speed + accel * dt)
        else:
            effective_decel = max(decel_power, 90.0) if self.off_track else decel_power
            self.speed = max(target_v, self.speed - effective_decel * dt)

            # Lockup risk (higher with worn tires, wetness, or extreme late braking)
            if (self.tires.wear_pct > 65.0 or track_wetness > 0.25 or self.pace_mode == "ATTACK") and not self.locked_up and not self.off_track:
                lockup_prob = 0.003 * (1.1 - self.driver.consistency) * max(0.2, 1.3 - self.norm_brakes)
                if self.driver.driving_style == "LATE_BRAKER":
                    lockup_prob *= 0.70  # Master of late braking avoids locking up despite deep entry
                if random.random() < lockup_prob:
                    self.locked_up = True
                    self.lockup_timer = 1.1
                    self.smoke_timer = 1.3
                    self.mistake_event = "LOCKUP"
                    self.speed *= 0.88
                    # Severe lockups heat up and damage brakes
                    brake_drop = random.uniform(1.8, 3.5)
                    self.part_durability["BRAKES"] = max(0.0, self.part_durability.get("BRAKES", 65.0) - brake_drop)

        # 8. Dynamic Multi-Lane Overtaking Battles - Modulated by Driver Style
        if can_overtake and car_ahead and not car_ahead.in_pit_lane and not car_ahead.is_broken and not self.off_track and not self.rejoining:
            dist_to_ahead = (car_ahead.s - self.s) % circuit.length
            ahead_defending = getattr(car_ahead, "is_defending", False)
            ahead_yielding = getattr(car_ahead, "is_yielding_blue_flag", False)

            brake_ratio = (self.norm_brakes * self.driver.braking) / max(0.1, (car_ahead.norm_brakes * car_ahead.driver.braking))
            aero_ratio = (self.norm_aero * effective_grip * driver_apex_factor) / max(0.1, (car_ahead.norm_aero * car_ahead.tires.get_effective_grip(track_wetness)))

            # Extended attack reach for Aggressive Hunters
            dive_range = 36.0 if self.driver.driving_style == "AGGRESSIVE_HUNTER" else 32.0

            # 1. Blue Flag Pass (Lapped car yielding cleanly)
            if ahead_yielding:
                self.target_lateral = inside_offset
                self.is_overtaking = True
                self.overtake_move_type = "BLUE_FLAG"

            # 2. Dive Bomb into Corner Entry (Late Braker / Aggressive Hunter)
            elif is_corner_entry and 0 < dist_to_ahead < dive_range:
                # If defender is actively guarding the inside, attacker needs a massive braking delta (e.g. 685 vs 432) or LATE_BRAKER style to lunge inside
                if ahead_defending:
                    can_dive = (brake_ratio > 1.22 or (self.driver.driving_style == "LATE_BRAKER" and brake_ratio > 1.10))
                else:
                    can_dive = (brake_ratio > 1.08 or self.pace_mode in ["ATTACK", "PUSH"] or 
                                self.driver.driving_style in ["LATE_BRAKER", "AGGRESSIVE_HUNTER"] or 
                                brake_ratio > 0.95)

                if can_dive:
                    self.target_lateral = inside_offset
                    self.is_overtaking = True
                    self.overtake_move_type = "DIVE_BOMB"
                    # Huge brake advantage carries speed effortlessly
                    if brake_ratio > 1.20 or (self.driver.braking > 0.90 and brake_ratio > 1.05):
                        target_v = max(target_v, car_ahead.speed * 1.05)
                        if ahead_defending and not car_ahead.locked_up and random.random() < 0.06:
                            car_ahead.locked_up = True
                            car_ahead.lockup_timer = 1.0
                            car_ahead.smoke_timer = 1.2
                            car_ahead.mistake_event = "LOCKUP"
                else:
                    # Inside blocked by stubborn defender, sweep around outside line
                    if aero_ratio > 1.02 or self.driver.driving_style == "SMOOTH_ROLLER" or ahead_defending:
                        self.target_lateral = outside_offset
                        self.is_overtaking = True
                        self.overtake_move_type = "OUTSIDE_SWEEP"

            # 3. Around the Outside in Turn (Smooth Roller / High Downforce)
            elif is_corner and 0 < dist_to_ahead < 25.0:
                if aero_ratio > 1.02 or ahead_defending or self.driver.driving_style == "SMOOTH_ROLLER":
                    self.target_lateral = outside_offset
                    self.is_overtaking = True
                    self.overtake_move_type = "OUTSIDE_SWEEP"

            # 4. Straight-line Out-Dragging (Engine Power + Slipstream)
            elif not is_corner and dist_to_apex > 38.0 and 0 < dist_to_ahead < 28.0:
                if self.slipstream_intensity > 0.35 or self.speed > car_ahead.speed * 0.99 or self.drs_active:
                    passing_side = -1.0 if car_ahead.lateral_offset >= 0 else 1.0
                    self.target_lateral = passing_side * (local_width * 0.28)
                    self.is_overtaking = True
                    self.overtake_move_type = "STRAIGHT_DRAFT"

            # Multi-car proximity & same-lane collision prevention
            danger_cars = []
            if all_cars:
                for oc in all_cars:
                    if oc is not self and not oc.is_broken and not oc.is_dnf and not oc.in_pit_lane:
                        d_s = (oc.s - self.s) % circuit.length
                        if 0.0 < d_s < 6.5:
                            danger_cars.append((d_s, oc))
            else:
                d_s = (car_ahead.s - self.s) % circuit.length
                if 0.0 < d_s < 6.5:
                    danger_cars.append((d_s, car_ahead))

            for d_s, oc in danger_cars:
                lat_gap = abs(self.lateral_offset - oc.lateral_offset)
                if lat_gap < 1.8 and d_s < 4.5:
                    self.speed = min(self.speed, oc.speed * 0.98)
                    break

            if dist_to_ahead > 32.0 and self.is_overtaking:
                self.is_overtaking = False
                self.target_lateral = circuit.get_racing_line_offset(self.s)
        elif not self.is_overtaking and not self.is_defending and not self.slipstream_active and not self.ran_wide and not self.off_track:
            # When pitting this lap, smoothly steer toward pit entry corridor along the edge of the asphalt
            if self.box_this_lap and getattr(circuit, "pit_lane_enabled", False):
                self.target_lateral = circuit.get_pit_approach_racing_line_offset(self.s, transition_window_m=90.0)
            else:
                # Follow optimal racing line when in free air
                self.target_lateral = circuit.get_racing_line_offset(self.s)
        elif self.off_track:
            self.target_lateral = outside_offset * 1.35

        # Lateral steering interpolation - smooth rollers steer smoother and more progressively
        steer_rate = 3.2
        if self.box_this_lap and getattr(circuit, "pit_lane_enabled", False):
            dist_to_pit = (circuit.pit_entry_s - self.s) % circuit.length
            if dist_to_pit <= 90.0:
                steer_rate = 4.8  # Direct steering response to track pit entry lane cleanly
        elif self.is_overtaking or self.is_defending:
            steer_rate = 5.2 if self.driver.driving_style != "SMOOTH_ROLLER" else 4.2
        elif self.driver.driving_style == "SMOOTH_ROLLER":
            steer_rate = 2.6  # Ultra-smooth transitions minimize tire scrub
        lat_speed = steer_rate * dt

        if self.lateral_offset < self.target_lateral:
            self.lateral_offset = min(self.target_lateral, self.lateral_offset + lat_speed)
        elif self.lateral_offset > self.target_lateral:
            self.lateral_offset = max(self.target_lateral, self.lateral_offset - lat_speed)

        # 9. Update distance & Lap Timing
        dist_travelled = self.speed * dt
        new_s = self.s + dist_travelled
        
        # Sector split timing checks
        s1_dist = circuit.sectors[0] * circuit.length
        s2_dist = circuit.sectors[1] * circuit.length
        if self.s < s1_dist and new_s >= s1_dist:
            self.s1_time = self.current_lap_time
        elif self.s < s2_dist and new_s >= s2_dist:
            self.s2_time = self.current_lap_time - self.s1_time

        # Lap completion
        if new_s >= circuit.length:
            new_s = new_s % circuit.length
            self.lap += 1
            self.last_lap_time = self.current_lap_time
            self.s3_time = self.last_lap_time - (self.s1_time + self.s2_time)
            if self.last_lap_time < self.best_lap_time:
                self.best_lap_time = self.last_lap_time
            self.current_lap_time = 0.0
            self.tires.laps_used += 1

        self.s = new_s

        # 10. World coordinates
        self.world_x, self.world_y = circuit.get_position(self.s, self.lateral_offset)
        self.heading = circuit.get_heading(self.s)

        # 11. Tire Degradation, Suspension Setup & Practice Plan Bonuses
        cornering_g = (self.speed ** 2) * curvature / 9.81
        wear_mult = {"CONSERVE": 0.65, "NORMAL": 1.0, "PUSH": 1.4, "ATTACK": 1.95}.get(self.pace_mode, 1.0)
        
        chassis_preserve_factor = 1.15 - 0.30 * (self.attributes.tire_preservation / 100.0)
        driver_preserve_factor = self.driver.get_tire_preservation_multiplier()

        # Suspension stiffness modifier: stiffer setup gives slightly higher tire degradation
        suspension_wear_factor = 0.90 + 0.20 * (self.setup.suspension / 100.0)

        # Practice Plan bonuses (e.g. Sprint Stints or Long Runs tire preservation)
        plan_wear_reduction = 1.0 - (self.practice_bonuses.get("race_wear_bonus", 0.0) + self.practice_bonuses.get("sprint_wear_bonus", 0.0))
        plan_wear_reduction = max(0.65, plan_wear_reduction)

        self.tires.apply_wear_and_thermals(
            dist_travelled=dist_travelled,
            track_length=circuit.length,
            dt=dt,
            pace_multiplier=wear_mult * chassis_preserve_factor * driver_preserve_factor * suspension_wear_factor * plan_wear_reduction,
            cornering_g=cornering_g,
            fuel_weight_kg=self.fuel_kg,
            in_dirty_air=self.in_dirty_air,
            track_wetness=track_wetness
        )

        
        # 12. Fuel Consumption & Practice Plan Fuel Saving Bonus
        chassis_fuel_factor = 1.15 - 0.30 * (self.attributes.fuel_efficiency / 100.0)
        fuel_bonus_mult = max(0.85, 1.0 - self.practice_bonuses.get("fuel_saving_bonus", 0.0))
        fuel_burn = (0.018 * chassis_fuel_factor * fuel_bonus_mult * {"LEAN": 0.8, "STANDARD": 1.0, "RICH": 1.35}.get(self.engine_mode, 1.0)) * dt
        self.fuel_kg = max(0.1, self.fuel_kg - fuel_burn)

        # 13. Component Durability Continuous Degradation & Terminal Breakdown
        # Baseline continuous wear (~0.2% to 0.5% per lap)
        lap_dist = max(100.0, circuit.length)
        pace_deg_mult = {"CONSERVE": 0.7, "NORMAL": 1.0, "PUSH": 1.35, "ATTACK": 1.8}.get(self.pace_mode, 1.0)
        engine_deg_mult = {"LEAN": 0.8, "STANDARD": 1.0, "RICH": 1.4}.get(self.engine_mode, 1.0)
        continuous_wear = (0.32 * pace_deg_mult * (dist_travelled / lap_dist))
        
        for p in self.part_durability:
            p_mult = engine_deg_mult if p == "ENGINE" else 1.0
            self.part_durability[p] = max(0.0, self.part_durability[p] - continuous_wear * p_mult)

        # Terminal Breakdown Check: If ANY component drops to 0.0%, catastrophic mechanical failure occurs
        if not self.is_broken and not self.is_dnf:
            for p_name, p_dur in self.part_durability.items():
                if p_dur <= 0.0:
                    self.is_broken = True
                    self.is_dnf = True
                    self.speed = 0.0
                    self.smoke_timer = 2.0
                    self.mistake_event = "MECHANICAL_FAILURE"
                    self.blunder_part_damaged = p_name
                    # Move off line onto grass/verge
                    self.target_lateral = circuit.get_width(self.s) * 0.55
                    self.lateral_offset = self.target_lateral
                    self.world_x, self.world_y = circuit.get_position(self.s, self.lateral_offset)
                    break

    def _update_pit_lane(self, dt: float, circuit: Circuit):
        pit_limiter_speed = 22.2 # 80 km/h
        box_s = circuit.pit_length * circuit.pit_box_s

        if self.pit_state == "APPROACH":
            # Smoothly decelerate down to pit limiter speed
            if self.speed > pit_limiter_speed:
                self.speed = max(pit_limiter_speed, self.speed - 35.0 * dt)
            else:
                self.speed = pit_limiter_speed
                
            self.pit_s += self.speed * dt
            if self.pit_s >= box_s:
                self.pit_s = box_s
                self.pit_state = "IN_BOX"
                self.speed = 0.0
                # Base pit stop duration with trackside bonuses
                base_reduction = self.pit_modifiers.get("base_stop_reduction", 0.0)
                base_stop = max(1.75, 2.4 - base_reduction)
                variance = random.uniform(0.0, 0.7)
                err_prob = 0.04 * self.pit_modifiers.get("error_rate_mult", 1.0)
                error = 1.8 if random.random() < err_prob else 0.0
                extra_time = 0.0
                if self.pit_replace_front_wing:
                    extra_time += self.pit_modifiers.get("wing_change_time", 4.0)
                if self.pit_emergency_repairs:
                    extra_time += self.pit_modifiers.get("repair_time", 14.0)
                self.pit_timer = base_stop + variance + error + extra_time
                self.last_pit_duration = self.pit_timer

        elif self.pit_state == "IN_BOX":
            self.speed = 0.0
            self.pit_timer -= dt
            if self.pit_timer <= 0.0:
                self.tires = TireSet(self.pit_queued_compound)
                
                # Apply front wing replacement if ordered
                if self.pit_replace_front_wing:
                    self.part_durability["FRONT_WING"] = max(self.part_durability.get("FRONT_WING", 0.0), self.pit_front_wing_durability)
                    self.pit_replace_front_wing = False

                # Apply emergency on-the-fly repairs if ordered (brings worn parts up to target durability)
                if self.pit_emergency_repairs:
                    rep_min = self.pit_modifiers.get("repair_durability_min", 55.0)
                    rep_max = self.pit_modifiers.get("repair_durability_max", 60.0)
                    for p in self.part_durability:
                        if self.part_durability[p] < rep_min:
                            self.part_durability[p] = random.uniform(rep_min, rep_max)
                    self.pit_emergency_repairs = False

                self.total_pit_stops += 1
                self.pit_state = "EXITING"

        elif self.pit_state == "EXITING":
            self.speed = pit_limiter_speed
            self.pit_s += self.speed * dt
            if self.pit_s >= circuit.pit_length:
                self.in_pit_lane = False
                self.pit_state = "TRACK"
                self.s = circuit.pit_exit_s
                # Seamless re-entry at the track edge matching pit exit lane endpoint
                self.lateral_offset = circuit.get_pit_side_sign() * (circuit.get_width(self.s) * 0.45)
                self.speed = pit_limiter_speed

        px, py, heading = circuit.get_pit_position(self.pit_s)
        self.world_x = px
        self.world_y = py
        self.heading = heading


    def order_pit_stop(self, new_compound: str = "HARD", replace_front_wing: bool = False, 
                       front_wing_durability: float = 100.0, emergency_repairs: bool = False):
        self.box_this_lap = True
        self.pit_queued_compound = new_compound.upper()
        self.pit_replace_front_wing = replace_front_wing
        self.pit_front_wing_durability = front_wing_durability
        self.pit_emergency_repairs = emergency_repairs

    def cancel_pit_stop(self):
        self.box_this_lap = False
        self.pit_replace_front_wing = False
        self.pit_emergency_repairs = False
