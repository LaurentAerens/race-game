import math
import random
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

class RaceWeekendSession(str, Enum):
    FP1 = "FP1"
    FP2 = "FP2"
    FP3 = "FP3"
    QUALIFYING = "QUALIFYING"
    SPRINT = "SPRINT"
    RACE = "RACE"

class PracticePlan(str, Enum):
    BALANCED = "BALANCED"
    FAST_LAP = "FAST_LAP"
    SPRINT_STINTS = "SPRINT_STINTS"
    LONG_RUNS = "LONG_RUNS"

@dataclass
class CarSetup:
    """Aerodynamic, mechanical, and gearing setup parameters."""
    front_wing: float = 50.0       # 0 (low drag) - 100 (high downforce / turn-in)
    rear_wing: float = 50.0        # 0 (high top speed) - 100 (high downforce / stability)
    suspension: float = 50.0       # 0 (soft / curb compliance) - 100 (stiff / aero stability)
    gear_ratio: float = 50.0       # 0 (short acceleration) - 100 (long top speed)
    brake_bias: float = 56.0       # 50% (rear bias / rotation) - 65% (front bias / stability)

    def copy(self) -> 'CarSetup':
        return CarSetup(
            front_wing=self.front_wing,
            rear_wing=self.rear_wing,
            suspension=self.suspension,
            gear_ratio=self.gear_ratio,
            brake_bias=self.brake_bias
        )

@dataclass
class OptimalTrackSetup:
    """Target sweet-spot values for a specific circuit."""
    front_wing: float = 55.0
    rear_wing: float = 58.0
    suspension: float = 50.0
    gear_ratio: float = 55.0
    brake_bias: float = 56.5
    tolerance: float = 8.0 # +/- tolerance where setup is considered optimal

class RaceWeekendManager:
    """
    Coordinates an entire Grand Prix weekend across all sessions:
    - Tier 3: FP1 -> FP2 -> QUALIFYING -> SPRINT
    - Tier 2: FP1 -> FP2 -> QUALIFYING -> RACE
    - Tier 1: FP1 -> FP2 -> FP3 -> QUALIFYING -> SPRINT (Top 10 Reverse Grid) -> RACE
    """

    SPRINT_POINTS = [8, 7, 6, 5, 4, 3, 2, 1]
    RACE_POINTS = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]

    def __init__(self, league_tier: int, track_metadata: Dict[str, Any], total_laps_base: int = 22,
                 facility_tiers: Optional[Dict[str, int]] = None, equipment_levels: Optional[Dict[str, int]] = None):
        self.tier = league_tier
        self.track_metadata = track_metadata
        self.track_name = track_metadata.get("track_name", "Grand Prix Circuit")
        self.circuit_file = track_metadata.get("circuit_file", "emerald_ring.json")
        self.total_laps_base = total_laps_base
        self.facility_tiers: Dict[str, int] = facility_tiers or {}
        self.equipment_levels: Dict[str, int] = equipment_levels or {}

        # Calculate session lengths
        self.sprint_laps = max(7, int(round(total_laps_base * 0.38)))
        self.race_laps = max(18, total_laps_base)

        # Build session sequence based on league tier
        self.sessions: List[RaceWeekendSession] = self._build_session_schedule(self.tier)
        self.current_session_index: int = 0

        # Optimal setup for this circuit
        self.optimal_setup = self._derive_optimal_setup(track_metadata)

        # Initial setups per car (Car 1 and Car 2)
        # Pre-Weekend Virtual Rig (track_virtual_sim) seeds initial setup closer to optimal
        vsim_tier = self.facility_tiers.get("track_virtual_sim", 0)
        vsim_solver_lvl = self.equipment_levels.get("eq_vsim_cloud_cluster", 0)
        vsim_rubber_lvl = self.equipment_levels.get("eq_vsim_tire_degrade_sim", 0)
        vsim_neural_lvl = self.equipment_levels.get("eq_vsim_driver_neural_link", 0)

        initial_setups = {}
        for slot in (1, 2):
            if vsim_tier > 0:
                # Max random drift from optimal decreases with facility and equipment tiers
                drift_max = max(3.0, 18.0 - (vsim_tier * 4.5) - (vsim_solver_lvl * 1.5))
                c_opt = self.optimal_setup
                initial_setups[slot] = CarSetup(
                    front_wing=max(0.0, min(100.0, c_opt.front_wing + random.uniform(-drift_max, drift_max))),
                    rear_wing=max(0.0, min(100.0, c_opt.rear_wing + random.uniform(-drift_max, drift_max))),
                    suspension=max(0.0, min(100.0, c_opt.suspension + random.uniform(-drift_max, drift_max))),
                    gear_ratio=max(0.0, min(100.0, c_opt.gear_ratio + random.uniform(-drift_max, drift_max))),
                    brake_bias=max(50.0, min(65.0, c_opt.brake_bias + random.uniform(-drift_max * 0.15, drift_max * 0.15)))
                )
            else:
                initial_setups[slot] = CarSetup()

        self.car_setups: Dict[int, CarSetup] = initial_setups

        # Practice Plans per car
        self.practice_plans: Dict[int, PracticePlan] = {
            1: PracticePlan.BALANCED,
            2: PracticePlan.BALANCED
        }

        # Setup Confidence (0.0 to 100.0) per car (boosted by virtual sim and rubber testing bench)
        base_confidence = 25.0
        if vsim_tier > 0:
            base_confidence = min(85.0, base_confidence + (vsim_tier * 10.0) + (vsim_rubber_lvl * 4.0) + (vsim_neural_lvl * 3.0))

        self.setup_confidence: Dict[int, float] = {
            1: base_confidence,
            2: base_confidence
        }

        # Driver feedback log per car: list of feedback message dicts
        self.driver_feedback: Dict[int, List[Dict[str, Any]]] = {
            1: [],
            2: []
        }

        # Plan bonuses accumulated during practice
        self.practice_bonuses: Dict[int, Dict[str, float]] = {
            1: {"qualy_pace_bonus": 0.0, "sprint_wear_bonus": 0.0, "race_wear_bonus": 0.0, "fuel_saving_bonus": 0.0},
            2: {"qualy_pace_bonus": 0.0, "sprint_wear_bonus": 0.0, "race_wear_bonus": 0.0, "fuel_saving_bonus": 0.0}
        }

        # Session results storage
        self.practice_results: Dict[str, List[Dict[str, Any]]] = {}
        self.qualifying_results: List[Dict[str, Any]] = [] # P1 to P20
        self.sprint_results: List[Dict[str, Any]] = []
        self.race_results: List[Dict[str, Any]] = []

        # Weekend points accumulator: {driver_name: points}
        self.weekend_driver_points: Dict[str, int] = {}
        self.weekend_team_points: Dict[str, int] = {}

        self.is_weekend_completed: bool = False

    def _build_session_schedule(self, tier: int) -> List[RaceWeekendSession]:
        """Returns the specific session list based on championship tier."""
        if tier >= 3:
            # Tier 3 (National Cup): 2 Practice Sessions, 1 Qualifying, 1 Sprint
            return [
                RaceWeekendSession.FP1,
                RaceWeekendSession.FP2,
                RaceWeekendSession.QUALIFYING,
                RaceWeekendSession.SPRINT
            ]
        elif tier == 2:
            # Tier 2 (Continental): 2 Practice Sessions, 1 Qualifying, 1 Normal Race
            return [
                RaceWeekendSession.FP1,
                RaceWeekendSession.FP2,
                RaceWeekendSession.QUALIFYING,
                RaceWeekendSession.RACE
            ]
        else:
            # Tier 1 (World Super Formula): FP1 -> FP2 -> QUALIFYING -> SPRINT (Reverse Grid) -> FP3 (Race Fine-Tuning) -> RACE
            return [
                RaceWeekendSession.FP1,
                RaceWeekendSession.FP2,
                RaceWeekendSession.QUALIFYING,
                RaceWeekendSession.SPRINT,
                RaceWeekendSession.FP3,
                RaceWeekendSession.RACE
            ]

    def _derive_optimal_setup(self, track_meta: Dict[str, Any]) -> OptimalTrackSetup:
        """Derives track sweet spot from track characteristics."""
        c_file = track_meta.get("circuit_file", "").lower()
        
        # High downforce street circuit
        if "harbor" in c_file:
            return OptimalTrackSetup(
                front_wing=76.0,
                rear_wing=80.0,
                suspension=38.0, # softer for street bumps
                gear_ratio=42.0, # short gearing for tight acceleration
                brake_bias=57.5,
                tolerance=7.5
            )
        # High speed power temple
        elif "apex" in c_file:
            return OptimalTrackSetup(
                front_wing=42.0,
                rear_wing=45.0,
                suspension=68.0, # stiff platform for high-speed sweepers
                gear_ratio=74.0, # long gearing for top speed
                brake_bias=55.5,
                tolerance=8.0
            )
        # Technical balanced circuit
        else: # Emerald Ring
            return OptimalTrackSetup(
                front_wing=58.0,
                rear_wing=62.0,
                suspension=54.0,
                gear_ratio=56.0,
                brake_bias=56.0,
                tolerance=8.0
            )

    @property
    def current_session(self) -> RaceWeekendSession:
        if self.current_session_index < len(self.sessions):
            return self.sessions[self.current_session_index]
        return self.sessions[-1]

    @property
    def is_practice(self) -> bool:
        return self.current_session in [RaceWeekendSession.FP1, RaceWeekendSession.FP2, RaceWeekendSession.FP3]

    @property
    def is_qualifying(self) -> bool:
        return self.current_session == RaceWeekendSession.QUALIFYING

    @property
    def is_sprint(self) -> bool:
        return self.current_session == RaceWeekendSession.SPRINT

    @property
    def is_race(self) -> bool:
        return self.current_session == RaceWeekendSession.RACE

    def get_current_session_laps(self) -> int:
        if self.is_practice:
            return 5 # Practice stint
        elif self.is_qualifying:
            return 3 # Out-lap, flying lap, in-lap
        elif self.is_sprint:
            return self.sprint_laps
        else:
            return self.race_laps

    def set_car_setup_parameter(self, car_slot: int, parameter: str, value: float):
        """Updates a specific setup slider value for Car 1 or Car 2."""
        if car_slot not in self.car_setups:
            return
        setup = self.car_setups[car_slot]
        if parameter == "front_wing":
            setup.front_wing = max(0.0, min(100.0, value))
        elif parameter == "rear_wing":
            setup.rear_wing = max(0.0, min(100.0, value))
        elif parameter == "suspension":
            setup.suspension = max(0.0, min(100.0, value))
        elif parameter == "gear_ratio":
            setup.gear_ratio = max(0.0, min(100.0, value))
        elif parameter == "brake_bias":
            setup.brake_bias = max(50.0, min(65.0, value))

    def set_practice_plan(self, car_slot: int, plan: PracticePlan):
        """Sets active practice plan for Car 1 or Car 2."""
        if car_slot in self.practice_plans:
            self.practice_plans[car_slot] = plan

    def get_setup_guidance_ranges(self) -> Optional[Dict[str, Tuple[float, float]]]:
        """
        Calculates recommended target setup ranges ([min, max]) for each parameter
        if the Setup Analytics facility (track_setup_telemetry) is unlocked.
        Higher facility tiers and specialized equipment narrow the guidance brackets.
        """
        analytics_tier = self.facility_tiers.get("track_setup_telemetry", 0)
        if analytics_tier <= 0:
            return None

        # Equipment levels
        laser_lvl = self.equipment_levels.get("eq_set_laser_ride_sensors", 0)
        pushrod_lvl = self.equipment_levels.get("eq_set_pushrod_strain_links", 0)
        pyro_lvl = self.equipment_levels.get("eq_set_brake_rotor_pyrometers", 0)

        opt = self.optimal_setup

        # Bracket radius scales inversely with facility tier and equipment
        # Tier 1: ~14.0 radius, Tier 2: ~9.0 radius, Tier 3: ~5.0 radius
        base_radius = max(3.0, 18.0 - (analytics_tier * 4.5))
        aero_radius = max(2.5, base_radius - (laser_lvl * 0.8))
        susp_radius = max(2.5, base_radius - (pushrod_lvl * 0.8))
        mech_radius = max(2.5, base_radius - (pyro_lvl * 0.8))
        bb_radius = max(0.5, (base_radius * 0.15) - (pyro_lvl * 0.1))

        return {
            "front_wing": (max(0.0, opt.front_wing - aero_radius), min(100.0, opt.front_wing + aero_radius)),
            "rear_wing": (max(0.0, opt.rear_wing - aero_radius), min(100.0, opt.rear_wing + aero_radius)),
            "suspension": (max(0.0, opt.suspension - susp_radius), min(100.0, opt.suspension + susp_radius)),
            "gear_ratio": (max(0.0, opt.gear_ratio - mech_radius), min(100.0, opt.gear_ratio + mech_radius)),
            "brake_bias": (max(50.0, opt.brake_bias - bb_radius), min(65.0, opt.brake_bias + bb_radius)),
        }

    def evaluate_setup_closeness(self, setup: CarSetup) -> float:
        """
        Calculates setup accuracy score from 0.0 to 1.0 based on distance
        from optimal track setup.
        """
        opt = self.optimal_setup
        diff_fw = abs(setup.front_wing - opt.front_wing) / 100.0
        diff_rw = abs(setup.rear_wing - opt.rear_wing) / 100.0
        diff_susp = abs(setup.suspension - opt.suspension) / 100.0
        diff_gear = abs(setup.gear_ratio - opt.gear_ratio) / 100.0
        diff_bb = abs(setup.brake_bias - opt.brake_bias) / 15.0

        avg_error = (diff_fw * 1.2 + diff_rw * 1.2 + diff_susp * 0.9 + diff_gear * 1.0 + diff_bb * 0.7) / 5.0
        closeness = max(0.0, 1.0 - avg_error * 2.2)
        return closeness

    def run_practice_run(self, car_slot: int, driver_name: str, laps_run: int = 5) -> Dict[str, Any]:
        """
        Simulates a practice stint for a specific car slot, generating
        rich driver feedback quotes and increasing setup confidence.
        """
        setup = self.car_setups[car_slot]
        opt = self.optimal_setup
        plan = self.practice_plans[car_slot]
        closeness = self.evaluate_setup_closeness(setup)

        # Generate directional feedback comments
        comments = []
        # Front Wing
        fw_delta = setup.front_wing - opt.front_wing
        if fw_delta < -opt.tolerance:
            comments.append("Suffering from mid-corner understeer; we need more front wing angle.")
        elif fw_delta > opt.tolerance:
            comments.append("Front end is hyper-sensitive and snatchy on turn-in; front wing is too aggressive.")
        else:
            comments.append("Turn-in response and front-end bite feel positive.")

        # Rear Wing
        rw_delta = setup.rear_wing - opt.rear_wing
        if rw_delta < -opt.tolerance:
            comments.append("Rear end steps out when applying throttle out of slow corners; need more downforce.")
        elif rw_delta > opt.tolerance:
            comments.append("Car feels dragged down on the straight; rear downforce is causing too much air drag.")
        else:
            comments.append("Rear stability under high-speed traction is dialed in.")

        # Gearing
        gear_delta = setup.gear_ratio - opt.gear_ratio
        if gear_delta < -opt.tolerance:
            comments.append("Bouncing off the rev limiter before the braking zone; lengthen the gear ratios.")
        elif gear_delta > opt.tolerance:
            comments.append("Sluggish acceleration off corner exits; top gear is too tall.")
        else:
            comments.append("Gearing cadence perfectly matches the main straight and acceleration zones.")

        # Suspension
        susp_delta = setup.suspension - opt.suspension
        if susp_delta < -opt.tolerance:
            comments.append("Chassis rolls too much in high-speed transitions; stiffen the suspension.")
        elif susp_delta > opt.tolerance:
            comments.append("Car gets violently deflected over the kerbs; suspension is too stiff.")
        else:
            comments.append("Riding the kerbs smoothly with great aero platform stability.")

        # Overall summary quote
        if closeness > 0.88:
            summary = "The car feels fantastic! Balance is on rails."
        elif closeness > 0.70:
            summary = "Good baseline found. A few minor tweaks will optimize lap time."
        else:
            summary = "Struggling with balance. Setup needs significant adjustment."

        # Setup confidence growth
        # Base confidence gain based on laps run and closeness
        growth = (12.0 + closeness * 16.0) * (laps_run / 5.0)
        if plan == PracticePlan.BALANCED:
            growth += 6.0

        new_conf = min(100.0, self.setup_confidence[car_slot] + growth)
        self.setup_confidence[car_slot] = new_conf

        # Apply plan bonuses
        bonuses = self.practice_bonuses[car_slot]
        if plan == PracticePlan.FAST_LAP:
            bonuses["qualy_pace_bonus"] = min(0.65, bonuses["qualy_pace_bonus"] + 0.22)
        elif plan == PracticePlan.SPRINT_STINTS:
            bonuses["sprint_wear_bonus"] = min(0.30, bonuses["sprint_wear_bonus"] + 0.10)
        elif plan == PracticePlan.LONG_RUNS:
            bonuses["race_wear_bonus"] = min(0.35, bonuses["race_wear_bonus"] + 0.12)
            bonuses["fuel_saving_bonus"] = min(0.15, bonuses["fuel_saving_bonus"] + 0.05)
        elif plan == PracticePlan.BALANCED:
            bonuses["qualy_pace_bonus"] = min(0.30, bonuses["qualy_pace_bonus"] + 0.08)
            bonuses["race_wear_bonus"] = min(0.20, bonuses["race_wear_bonus"] + 0.08)

        run_result = {
            "session": self.current_session.value,
            "car_slot": car_slot,
            "driver_name": driver_name,
            "plan": plan.value,
            "setup_closeness_pct": round(closeness * 100.0, 1),
            "confidence_pct": round(new_conf, 1),
            "summary_quote": summary,
            "feedback_points": comments,
            "laps_completed": laps_run
        }

        self.driver_feedback[car_slot].append(run_result)
        return run_result

    def simulate_qualifying_session(self, all_drivers_cars: List[Tuple[Any, Any]]) -> List[Dict[str, Any]]:
        """
        Simulates flying laps for all 20 drivers to determine the qualifying grid.
        Takes into account car power, driver pace, setup confidence, and fast-lap bonuses.
        """
        qualy_entries = []
        base_lap_time = 72.500 # Baseline lap ~1:12.500

        for driver, car_attrs in all_drivers_cars:
            # Power & Aero delta
            eng_val = getattr(car_attrs, "engine_power", 80.0)
            aero_val = getattr(car_attrs, "aero_downforce", 80.0)
            car_perf_bonus = (eng_val - 50.0) * 0.04 + (aero_val - 50.0) * 0.05

            # Driver speed delta
            drv_speed = getattr(driver, "speed", 0.75) * 100.0
            drv_cons = getattr(driver, "consistency", 0.75) * 100.0
            drv_bonus = (drv_speed - 50.0) * 0.035

            # If player driver, apply setup confidence & practice plan bonus
            player_bonus = 0.0
            if getattr(driver, "is_player", False):
                # Car 1 or Car 2
                c_slot = 1 if getattr(driver, "number", 1) % 2 != 0 else 2
                conf = self.setup_confidence[c_slot]
                bonuses = self.practice_bonuses[c_slot]
                # Up to 0.7s gain from 100% confidence + Fast Lap program
                player_bonus = (conf / 100.0) * 0.45 + bonuses.get("qualy_pace_bonus", 0.0)

            # Random variance filtered by consistency
            var_spread = max(0.05, 0.40 - (drv_cons / 100.0) * 0.25)
            variance = random.uniform(-var_spread, var_spread)

            final_lap_time = base_lap_time - car_perf_bonus - drv_bonus - player_bonus + variance
            final_lap_time = max(55.0, final_lap_time)

            qualy_entries.append({
                "driver": driver,
                "driver_name": getattr(driver, "name", "Driver"),
                "team_name": getattr(driver, "team_name", "Team"),
                "is_player": getattr(driver, "is_player", False),
                "number": getattr(driver, "number", 1),
                "car_attrs": car_attrs,
                "lap_time": final_lap_time
            })

        # Sort by fastest flying lap time
        qualy_entries.sort(key=lambda x: x["lap_time"])
        pole_time = qualy_entries[0]["lap_time"]

        for pos, entry in enumerate(qualy_entries, 1):
            entry["position"] = pos
            entry["gap_to_pole"] = entry["lap_time"] - pole_time
            entry["lap_time_str"] = self.format_lap_time(entry["lap_time"])

        self.qualifying_results = qualy_entries
        return qualy_entries

    def get_starting_grid_for_sprint(self) -> List[Dict[str, Any]]:
        """
        Returns starting grid for the Sprint Race:
        - Tier 3: Direct Qualifying order (P1 on pole).
        - Tier 1: **Top 10 Reverse Grid**! P1-P10 reversed, P11-P20 in qualifying order.
        """
        if not self.qualifying_results:
            return []

        if self.tier == 1:
            # Top 10 reversed
            top_10 = list(reversed(self.qualifying_results[:10]))
            bottom_10 = list(self.qualifying_results[10:])
            reversed_grid = []
            
            for new_pos, entry in enumerate(top_10, 1):
                item = dict(entry)
                item["sprint_grid_pos"] = new_pos
                item["qualy_pos"] = entry["position"]
                item["is_reversed_grid"] = True
                reversed_grid.append(item)

            for new_pos, entry in enumerate(bottom_10, 11):
                item = dict(entry)
                item["sprint_grid_pos"] = new_pos
                item["qualy_pos"] = entry["position"]
                item["is_reversed_grid"] = False
                reversed_grid.append(item)

            return reversed_grid
        else:
            # Tier 3 standard qualifying order
            normal_grid = []
            for pos, entry in enumerate(self.qualifying_results, 1):
                item = dict(entry)
                item["sprint_grid_pos"] = pos
                item["qualy_pos"] = pos
                item["is_reversed_grid"] = False
                normal_grid.append(item)
            return normal_grid

    def get_starting_grid_for_main_race(self) -> List[Dict[str, Any]]:
        """
        Main Race starting grid is always determined by the Qualifying results.
        """
        grid = []
        for pos, entry in enumerate(self.qualifying_results, 1):
            item = dict(entry)
            item["race_grid_pos"] = pos
            grid.append(item)
        return grid

    def record_session_completion(self, session: RaceWeekendSession, results: List[Dict[str, Any]]):
        """Records finishing positions and awards points for Sprint or Main Race."""
        if session == RaceWeekendSession.QUALIFYING:
            self.qualifying_results = results
        elif session == RaceWeekendSession.SPRINT:
            self.sprint_results = results
            # Award Sprint points to top 8
            for pos, r in enumerate(results[:8], 1):
                pts = self.SPRINT_POINTS[pos - 1]
                d_name = r.get("driver_name", "Driver")
                t_name = r.get("team_name", "Team")
                self.weekend_driver_points[d_name] = self.weekend_driver_points.get(d_name, 0) + pts
                self.weekend_team_points[t_name] = self.weekend_team_points.get(t_name, 0) + pts
        elif session == RaceWeekendSession.RACE:
            self.race_results = results
            # Award Main Race points to top 10
            for pos, r in enumerate(results[:10], 1):
                pts = self.RACE_POINTS[pos - 1]
                d_name = r.get("driver_name", "Driver")
                t_name = r.get("team_name", "Team")
                self.weekend_driver_points[d_name] = self.weekend_driver_points.get(d_name, 0) + pts
                self.weekend_team_points[t_name] = self.weekend_team_points.get(t_name, 0) + pts

    def advance_to_next_session(self) -> bool:
        """
        Advances to the next session in the weekend schedule.
        Returns True if advanced, or False if weekend is now completed.
        """
        if self.current_session_index < len(self.sessions) - 1:
            self.current_session_index += 1
            return True
        else:
            self.is_weekend_completed = True
            return False

    @staticmethod
    def format_lap_time(seconds: float) -> str:
        if seconds <= 0 or math.isinf(seconds):
            return "--:--.---"
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}:{secs:06.3f}"
