import random
import math
from typing import List, Optional, Dict, Tuple, Any
from .circuit import Circuit
from .car import Car
from .driver import Driver
from .race_control import RaceControl, FlagStatus
from .weather import WeatherSystem
from .radio_system import RadioMessageSystem
from .tires import TIRE_COMPOUNDS
from ..database.db_manager import CarAttributes


class Simulation:
    """
    Master Race Simulation coordinator.
    Manages grid starting positions, physics tick updates, dynamic overtaking,
    Safety Car deployment, tire degradation, dynamic weather, and commentary feeds.
    """
    def __init__(self, circuit: Circuit, driver_car_pairs: List[Tuple[Driver, CarAttributes]], 
                 total_laps: int = 15, session_type: str = "RACE",
                 car_setups: Optional[Dict[int, Any]] = None,
                 setup_confidences: Optional[Dict[int, float]] = None,
                 practice_bonuses: Optional[Dict[int, Dict[str, float]]] = None,
                 league_tier: int = 3,
                 car_durabilities: Optional[Dict[int, Dict[str, float]]] = None,
                 weather_profile: Optional[str] = None,
                 rain_chance: Optional[float] = None,
                 max_wetness_cap: Optional[float] = None):
        self.circuit = circuit
        self.total_laps = total_laps
        self.session_type = session_type # "PRACTICE", "QUALIFYING", "SPRINT", "RACE"
        self.car_setups = car_setups or {}
        self.setup_confidences = setup_confidences or {}
        self.practice_bonuses = practice_bonuses or {}
        self.league_tier = league_tier
        self.car_durabilities = car_durabilities or {}

        self.current_lap = 1
        self.race_time = 0.0
        self.is_paused = False
        self.sim_speed = 1.0 # 1x, 2x, 4x, 8x
        self.race_finished = False
        
        self.race_control = RaceControl()
        eff_weather = weather_profile or getattr(circuit, "weather_profile", "DYNAMIC")
        eff_rain_chance = rain_chance if rain_chance is not None else getattr(circuit, "base_rain_chance", 0.20)
        is_big_track = getattr(circuit, "length", 0.0) >= 2200.0
        self.weather = WeatherSystem(
            initial_rain=0.0,
            weather_profile=eff_weather,
            rain_chance=eff_rain_chance,
            total_laps=total_laps,
            max_wetness_cap=max_wetness_cap,
            is_big_track=is_big_track
        )
        self.radio_system = RadioMessageSystem()
        
        # Commentary / Event log
        self.event_log: List[Dict] = []
        self.fastest_lap_holder: Optional[Car] = None
        self.fastest_lap_time: float = float('inf')

        # Initialize cars on starting grid
        self.cars: List[Car] = []
        self._init_grid(driver_car_pairs)


    def _init_grid(self, driver_car_pairs: List[Tuple[Driver, CarAttributes]]):
        self.cars = []
        dry_compounds = self.circuit.get_dry_compounds() # e.g. ["MEDIUM", "SOFT", "SUPERSOFT"]
        
        # Varied compound strategy splits on the starting grid
        grid_pattern = [dry_compounds[1], dry_compounds[2], dry_compounds[1], dry_compounds[0], dry_compounds[2]]

        for i, (driver, car_attrs) in enumerate(driver_car_pairs):
            compound = grid_pattern[i % len(grid_pattern)]
            if self.weather.track_wetness >= 0.70:
                compound = "WET"
            elif self.weather.track_wetness >= 0.10:
                compound = "INTER"

            # Check if player car and map setup / bonuses / durabilities
            c_setup = None
            c_conf = 50.0
            c_bonuses = None
            c_dur = None
            if getattr(driver, "is_player", False):
                slot = 1 if getattr(driver, "number", 1) % 2 != 0 else 2
                if slot in self.car_setups:
                    c_setup = self.car_setups[slot]
                if slot in self.setup_confidences:
                    c_conf = self.setup_confidences[slot]
                if slot in self.practice_bonuses:
                    c_bonuses = self.practice_bonuses[slot]
                if slot in self.car_durabilities:
                    c_dur = self.car_durabilities[slot]

            car = Car(
                car_id=i + 1, 
                driver=driver, 
                car_attributes=car_attrs, 
                initial_compound=compound,
                setup=c_setup,
                setup_confidence=c_conf,
                practice_bonuses=c_bonuses,
                league_tier=self.league_tier,
                initial_part_durabilities=c_dur
            )


            # Grid stagger (left / right alternating)
            grid_dist = (self.circuit.length - (15.0 + i * 9.0)) % self.circuit.length
            car.s = grid_dist
            local_w = self.circuit.get_width(car.s)
            car.lateral_offset = -local_w * 0.22 if i % 2 == 0 else local_w * 0.22
            car.speed = 0.0
            car.position = i + 1
            car.lap = 1
            
            car.world_x, car.world_y = self.circuit.get_position(car.s, car.lateral_offset)
            car.heading = self.circuit.get_heading(car.s)
            
            self.cars.append(car)

        self.log_event("LIGHTS OUT AND AWAY WE GO!", "START")

    def update(self, dt: float):
        """Advances simulation by dt seconds (scaled by sim_speed)."""
        if self.is_paused or self.race_finished:
            return

        effective_dt = dt * self.sim_speed
        steps = max(1, int(self.sim_speed))
        sub_dt = effective_dt / steps

        for _ in range(steps):
            self._tick(sub_dt)

    def _tick(self, dt: float):
        self.race_time += dt
        
        # Update weather, race control, and pit wall radio
        self.weather.update(dt, self.current_lap)
        leader_car = self.cars[0] if self.cars else None
        self.race_control.update(dt, self.current_lap, self.weather.track_wetness, circuit=self.circuit, leader_car=leader_car)
        player_cars = [c for c in self.cars if c.driver.is_player]
        self.radio_system.update(dt, self.current_lap, self.weather, player_cars)

        # Track flag state changes for broadcast feed commentary & mode neutralization
        prev_flag = getattr(self, "_prev_flag", FlagStatus.GREEN)
        current_flag = self.race_control.flag
        if current_flag != prev_flag:
            if current_flag in (FlagStatus.SAFETY_CAR, FlagStatus.VSC):
                # Full track neutralization: put all cars into most conservative modes and lock manual changes
                for c in self.cars:
                    if not c.is_broken and not c.is_dnf:
                        c.enter_flag_neutralization()
            elif current_flag == FlagStatus.YELLOW:
                # Yellow Flag: cars only switch to conservative mode while physically traversing the yellow sector
                # Cars not in the yellow sector maintain normal racing pace and settings
                pass
            elif current_flag == FlagStatus.GREEN and prev_flag in (FlagStatus.SAFETY_CAR, FlagStatus.VSC, FlagStatus.YELLOW):
                # Track clear: unlock mode adjustments and restore settings from before flag
                for c in self.cars:
                    if not c.is_broken and not c.is_dnf and c.is_mode_locked:
                        c.exit_flag_neutralization()

            if current_flag == FlagStatus.GREEN and prev_flag in (FlagStatus.SAFETY_CAR, FlagStatus.VSC, FlagStatus.YELLOW):
                self.log_event("GREEN FLAG - TRACK CLEAR! RACING RESUMES!", "FLAG")
            elif current_flag == FlagStatus.YELLOW and self.race_control.yellow_sector:
                self.log_event(f"YELLOW FLAG IN SECTOR {self.race_control.yellow_sector} - REDUCE PACE", "FLAG")
            self._prev_flag = current_flag

        # Sort cars: active cars by progress, DNF cars at the bottom
        self.cars.sort(key=lambda c: (0 if c.is_dnf else 1, c.lap * self.circuit.length + c.s), reverse=True)
        
        leader = self.cars[0]
        self.current_lap = max(1, leader.lap)
        
        if leader.lap > self.total_laps:
            if not self.race_finished:
                self.race_finished = True
                self.log_event(f"CHEQUERED FLAG! {leader.driver.name} WINS THE RACE!", "WIN")
            return

        for i, car in enumerate(self.cars):
            prev_pos = car.position
            car.position = i + 1
            car_ahead = self.cars[i - 1] if i > 0 else None
            car_behind = self.cars[i + 1] if i < len(self.cars) - 1 else None

            # Calculate gap to leader & interval ahead
            if i == 0:
                car.gap_to_leader = 0.0
                car.interval_to_ahead = 0.0
            else:
                leader_dist = (leader.lap * self.circuit.length + leader.s)
                car_dist = (car.lap * self.circuit.length + car.s)
                dist_gap = max(0.0, leader_dist - car_dist)
                car.gap_to_leader = dist_gap / max(20.0, car.speed)
                
                ahead_dist = (car_ahead.lap * self.circuit.length + car_ahead.s)
                interval_dist = max(0.0, ahead_dist - car_dist)
                car.interval_to_ahead = interval_dist / max(20.0, car.speed)

            # DRS availability: within 1.0s behind car ahead
            car.drs_available = (car.interval_to_ahead <= 1.05 and car.interval_to_ahead > 0.0)

            # AI strategic tactics (Pushing / ERS / Pit stops for non-player cars)
            if not car.driver.is_player and not car.in_pit_lane:
                if not car.is_mode_locked:
                    self._ai_tactics(car, car_ahead, car_behind)
                if not car.box_this_lap:
                    self._ai_pit_strategy(car)

            # Update physics with local sector wetness
            car_sec = self.circuit.get_sector(car.s)
            local_wetness = self.weather.get_sector_wetness(car_sec)
            car.update_physics(dt, self.circuit, self.race_control, local_wetness, car_ahead, car_behind, all_cars=self.cars)

            # Check for driver mistake commentary (crash, off track, rejoin, lockup, snap oversteer, running wide)
            if car.mistake_event:
                m_type = car.mistake_event
                car.mistake_event = None
                if m_type in ("CRASH", "AQUAPLANE_CRASH"):
                    if m_type == "AQUAPLANE_CRASH":
                        self.log_event(f"AQUAPLANE CRASH! {car.driver.name} lost all grip on {car.tires.compound.name} in standing water and crashed heavily in Sector {car.current_sector}!", "CRASH")
                    else:
                        self.log_event(f"CRASH! {car.driver.name} has heavily crashed out in Sector {car.current_sector}!", "CRASH")
                    if random.random() < 0.70:
                        self.race_control.deploy_safety_car(cleanup_duration=22.0, message="SAFETY CAR DEPLOYED", circuit=self.circuit, leader_s=self.cars[0].s)
                        self.log_event("SAFETY CAR DEPLOYED - Field bunching up slowly", "FLAG")
                    else:
                        self.race_control.deploy_vsc(duration_seconds=16.0, message="VIRTUAL SAFETY CAR")
                        self.log_event("VIRTUAL SAFETY CAR DEPLOYED - Strict speed delta", "FLAG")
                elif m_type == "MECHANICAL_FAILURE":
                    part_name = (car.blunder_part_damaged or "COMPONENT").replace("_", " ")
                    self.log_event(f"TERMINAL BREAKDOWN: {car.driver.name} has stopped on track with catastrophic {part_name} failure!", "CRASH")
                    if car.driver.is_player:
                        self.radio_system.broadcast(car.driver.name, f"Engine/Telemetry warning! The {part_name.lower()} is completely dead! I have to pull over and retire!", is_engineer=False, priority=10)
                    if random.random() < 0.65:
                        self.race_control.deploy_vsc(duration_seconds=18.0, message="VIRTUAL SAFETY CAR - CAR STOPPED")
                        self.log_event("VIRTUAL SAFETY CAR DEPLOYED - Stricken car on track", "FLAG")
                    else:
                        self.race_control.deploy_local_yellow(car.current_sector, duration=12.0)
                elif m_type == "BIG_BLUNDER":
                    part_name = (car.blunder_part_damaged or "part").replace("_", " ")
                    drop_pct = car.blunder_drop_pct
                    self.log_event(f"BIG BLUNDER: {car.driver.name} butchers the corner, clobbering the curbs (-{drop_pct:.1f}% {part_name} durability)!", "INCIDENT")
                    if car.driver.is_player:
                        radio_blunders = [
                            f"I really butchered that corner! Clattered over the high kerbs, felt the {part_name.lower()} take a beating!",
                            f"Whoa, massive curb strike! I've definitely taken life out of the {part_name.lower()}!",
                            f"Sorry team, lost the rear and bounced hard over the sausage curb! Check the {part_name.lower()} telemetry!"
                        ]
                        self.radio_system.broadcast(car.driver.name, random.choice(radio_blunders), is_engineer=False, priority=9)
                elif m_type == "OFF_TRACK":
                    self.log_event(f"INCIDENT: {car.driver.name} slides off into the runoff in Sector {car.current_sector}!", "INCIDENT")
                    self.race_control.deploy_local_yellow(car.current_sector, duration=8.0)
                elif m_type == "REJOIN":
                    self.log_event(f"{car.driver.name} safely rejoins the track after dropping back.", "INFO")
                elif m_type == "RAN_WIDE":
                    opp_txt = f" under pressure from {car_behind.driver.name}" if car_behind and car.is_defending else ""
                    self.log_event(f"{car.driver.name} runs wide at the apex{opp_txt}!", "INCIDENT")
                elif m_type == "LOCKUP":
                    self.log_event(f"{car.driver.name} locks up heavily with tire smoke puffing!", "INCIDENT")
                elif m_type == "SNAP_OVERSTEER":
                    self.log_event(f"{car.driver.name} suffers a snap of oversteer on corner exit!", "INCIDENT")

            # Check if marshals cleared broken wreckage once track returns to green
            if self.race_control.flag == FlagStatus.GREEN and car.is_broken and not getattr(car, "wreckage_cleared", False):
                car.wreckage_cleared = True
                self.log_event(f"Marshals have recovered and cleared {car.driver.name}'s car from the verge.", "INFO")

            # Check for fastest lap
            if car.last_lap_time > 0 and car.last_lap_time < self.fastest_lap_time:
                self.fastest_lap_time = car.last_lap_time
                self.fastest_lap_holder = car
                self.log_event(f"FASTEST LAP: {car.driver.name} ({self.format_time(car.last_lap_time)})", "FASTEST")

            # Check for position changes to log overtakes with specific racing moves
            if car.position < prev_pos and prev_pos <= 20:
                opp_name = car_behind.driver.name if car_behind else "rival"
                move_type = car.overtake_move_type or "PASS"
                if move_type == "DIVE_BOMB":
                    txt = f"{car.driver.name} launches a dive-bomb down the inside of {opp_name} into P{car.position}!"
                elif move_type == "OUTSIDE_SWEEP":
                    txt = f"{car.driver.name} sweeps around the outside of {opp_name} with superior downforce into P{car.position}!"
                elif move_type == "STRAIGHT_DRAFT":
                    txt = f"{car.driver.name} drafts {opp_name} and powers past down the straight into P{car.position}!"
                elif move_type == "BLUE_FLAG":
                    txt = f"{opp_name} yields under blue flags to let {car.driver.name} pass cleanly."
                else:
                    txt = f"{car.driver.name} moves up to P{car.position}!"
                
                self.log_event(txt, "OVERTAKE" if move_type != "BLUE_FLAG" else "INFO")

        # Resolve physical vehicle collisions / non-penetration hitboxes
        self._resolve_car_collisions(dt)

    def _resolve_car_collisions(self, dt: float):
        """
        Physical multi-car collision separation and non-penetration pass.
        Ensures cars cannot phase through or drive over each other.
        Hitbox is slightly smaller than the visual circle radius to keep wheel-to-wheel racing thrilling.
        """
        active_cars = [
            c for c in self.cars 
            if not c.is_broken and not c.is_dnf and not c.in_pit_lane and not c.off_track
        ]
        if len(active_cars) < 2:
            return

        circuit = self.circuit
        circuit_len = circuit.length
        min_dist = 3.3          # Minimum Euclidean center-to-center distance (meters)
        min_long_gap = 3.5      # Minimum longitudinal gap when in same lane
        min_lat_gap = 1.95      # Minimum lateral gap when side-by-side
        
        # Multiple relaxation iterations for packed situations (e.g. race start, safety car restarts)
        for _ in range(2):
            for i in range(len(active_cars)):
                c1 = active_cars[i]
                for j in range(i + 1, len(active_cars)):
                    c2 = active_cars[j]

                    dx = c2.world_x - c1.world_x
                    dy = c2.world_y - c1.world_y
                    dist_sq = dx * dx + dy * dy

                    # Quick bounding-box / broadphase rejection
                    if dist_sq >= (min_dist * min_dist):
                        continue

                    dist = math.sqrt(dist_sq)

                    # Determine longitudinal ordering along circuit
                    # Progress distance = lap * circuit_len + s
                    prog1 = c1.lap * circuit_len + c1.s
                    prog2 = c2.lap * circuit_len + c2.s

                    if prog1 >= prog2:
                        leader, chaser = c1, c2
                    else:
                        leader, chaser = c2, c1

                    s_gap = (leader.s - chaser.s) % circuit_len
                    if s_gap > (circuit_len * 0.5):
                        s_gap = circuit_len - s_gap

                    lat_gap = abs(leader.lateral_offset - chaser.lateral_offset)
                    local_w = circuit.get_width(chaser.s)
                    half_w_bound = local_w * 0.46

                    # Case A: Longitudinal Rear-End Avoidance (chaser directly behind leader along track)
                    if s_gap > 0.75 and s_gap < min_long_gap and lat_gap < 1.6:
                        # Chaser cannot accelerate or phase through leader's rear
                        chaser.speed = min(chaser.speed, max(0.0, leader.speed * 0.985))
                        # Reposition chaser backward to maintain non-penetration buffer
                        overlap = min_long_gap - s_gap
                        chaser.s = (chaser.s - overlap * 0.7) % circuit_len
                        # Nudge chaser slightly laterally to seek clear air/overtaking lane
                        steer_dir = 1.0 if chaser.lateral_offset >= leader.lateral_offset else -1.0
                        chaser.lateral_offset = max(-half_w_bound, min(half_w_bound, chaser.lateral_offset + steer_dir * 0.15))
                        chaser.world_x, chaser.world_y = circuit.get_position(chaser.s, chaser.lateral_offset)

                    # Case B: Lateral Side-by-Side Overlap / Squeeze (wheel-to-wheel non-penetration)
                    elif lat_gap < min_lat_gap:
                        overlap = min_lat_gap - lat_gap
                        nudge = max(0.08, overlap * 0.55)
                        
                        # Identify who is to the left vs right on track
                        if c1.lateral_offset <= c2.lateral_offset:
                            left_car, right_car = c1, c2
                        else:
                            left_car, right_car = c2, c1

                        left_car.lateral_offset = max(-half_w_bound, left_car.lateral_offset - nudge)
                        right_car.lateral_offset = min(half_w_bound, right_car.lateral_offset + nudge)

                        left_car.world_x, left_car.world_y = circuit.get_position(left_car.s, left_car.lateral_offset)
                        right_car.world_x, right_car.world_y = circuit.get_position(right_car.s, right_car.lateral_offset)

                    # Case C: General 2D Contact Separation
                    elif dist < min_dist and dist > 0.001:
                        overlap = min_dist - dist
                        # Push apart along lateral track axis
                        if c1.lateral_offset <= c2.lateral_offset:
                            c1.lateral_offset = max(-half_w_bound, c1.lateral_offset - overlap * 0.5)
                            c2.lateral_offset = min(half_w_bound, c2.lateral_offset + overlap * 0.5)
                        else:
                            c1.lateral_offset = min(half_w_bound, c1.lateral_offset + overlap * 0.5)
                            c2.lateral_offset = max(-half_w_bound, c2.lateral_offset - overlap * 0.5)

                        c1.world_x, c1.world_y = circuit.get_position(c1.s, c1.lateral_offset)
                        c2.world_x, c2.world_y = circuit.get_position(c2.s, c2.lateral_offset)

    def _ai_tactics(self, car: Car, car_ahead: Optional[Car], car_behind: Optional[Car]):
        """Dynamic AI tactical aggression: exploiting car/driver strengths and driving technique when hunting or defending."""
        # Tier 3 restrictions for early-game simplicity: no ERS, standard fuel mix, simple normal/push pace
        if self.league_tier >= 3:
            car.engine_mode = "STANDARD"
            car.ers_mode = "AUTO"
            if (car.drs_available or car.interval_to_ahead < 0.85 or car.slipstream_active or car.is_defending):
                car.pace_mode = "PUSH"
            else:
                car.pace_mode = "NORMAL"
            return

        # 1. Attacking mode (closing in on car ahead)
        if (car.drs_available or car.interval_to_ahead < 0.90 or car.slipstream_active) and car_ahead:
            # Check if car has braking advantage or downforce advantage
            has_brake_adv = (car.norm_brakes * car.driver.braking) > (car_ahead.norm_brakes * car_ahead.driver.braking * 1.04)
            has_power_adv = car.norm_engine > car_ahead.norm_engine
            
            # Late Brakers and Aggressive Hunters commit aggressively to ATTACK mode
            if has_brake_adv or car.driver.aggression > 0.65 or car.driver.driving_style in ["LATE_BRAKER", "AGGRESSIVE_HUNTER"]:
                car.pace_mode = "ATTACK"
            else:
                car.pace_mode = "PUSH"

            if (has_power_adv or car.interval_to_ahead < 0.55 or car.driver.aggression > 0.75) and car.ers_pct > 15.0:
                car.ers_mode = "OVERTAKE"
            car.engine_mode = "RICH"

        # 2. Defending mode (under pressure from behind)
        elif car.is_defending and car_behind:
            car.pace_mode = "PUSH"
            car.engine_mode = "STANDARD"
            if car.driver.defending > 0.78 and car.ers_pct > 20.0:
                car.ers_mode = "BALANCED"
            else:
                car.ers_mode = "AUTO"

        # 3. Tire & fuel management in clear air (influenced by driver style)
        else:
            wear_threshold = 48.0 if car.driver.driving_style == "TIRE_WHISPERER" else 38.0
            if car.tires.wear_pct > wear_threshold:
                car.pace_mode = "CONSERVE"
                car.engine_mode = "LEAN" if car.fuel_kg < 10.0 else "STANDARD"
                car.ers_mode = "RECHARGE" if car.ers_pct < 60.0 else "BALANCED"
            else:
                car.pace_mode = "NORMAL"
                car.engine_mode = "STANDARD"
                car.ers_mode = "BALANCED"

    def _ai_pit_strategy(self, car: Car):
        """Simulates AI driver pit decisions for tire degradation or rain."""
        dry_compounds = self.circuit.get_dry_compounds()
        
        # 1. Weather change reaction
        avg_wet = self.weather.track_wetness
        max_sec_wet = max(self.weather.sector_wetness.values()) if hasattr(self.weather, "sector_wetness") else avg_wet

        if car.tires.compound.wet_suitability < 0.3:
            # Currently on slicks
            if max_sec_wet >= 0.75:
                car.order_pit_stop("WET" if avg_wet >= 0.65 else "INTER")
                return
            elif max_sec_wet >= 0.40 or avg_wet >= 0.12:
                car.order_pit_stop("INTER")
                return
        elif car.tires.compound_name == "INTER":
            # Currently on Intermediates (operating window 10% - 80%)
            if avg_wet >= 0.80:
                car.order_pit_stop("WET")
                return
            elif max_sec_wet < 0.08:
                car.order_pit_stop(dry_compounds[1]) # Return to slicks
                return
        elif car.tires.compound_name == "WET":
            # Currently on Full Wet (operating window 70% - 100%)
            if avg_wet < 0.68 and max_sec_wet >= 0.08:
                car.order_pit_stop("INTER")
                return
            elif max_sec_wet < 0.08:
                car.order_pit_stop(dry_compounds[1]) # Return to slicks
                return

        # 2. Tire wear cliff reaction
        if car.tires.wear_pct > car.tires.compound.cliff_wear_pct and (self.total_laps - car.lap) >= 3:
            laps_left = self.total_laps - car.lap
            if laps_left < 6:
                next_comp = dry_compounds[2] # Softest dry compound
            elif laps_left < 13:
                next_comp = dry_compounds[1] # Middle dry compound
            else:
                next_comp = dry_compounds[0] # Hardest dry compound
            car.order_pit_stop(next_comp)


    def log_event(self, text: str, event_type: str = "INFO"):
        self.event_log.insert(0, {
            "time": self.race_time,
            "lap": self.current_lap,
            "text": text,
            "type": event_type
        })
        if len(self.event_log) > 40:
            self.event_log.pop()

    @staticmethod
    def format_time(seconds: float) -> str:
        if seconds == float('inf') or seconds <= 0:
            return "--:--.---"
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}:{secs:06.3f}"
