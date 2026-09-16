import math
import os
import random
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


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


class StintType(str, Enum):
    SHORT = "SHORT"
    SPRINT = "SPRINT"
    LONG = "LONG"


@dataclass
class CarSetup:
    """Aerodynamic, mechanical, and gearing setup parameters."""

    front_wing: float = 50.0  # 0 (low drag) - 100 (high downforce / turn-in)
    rear_wing: float = 50.0  # 0 (high top speed) - 100 (high downforce / stability)
    suspension: float = 50.0  # 0 (soft / curb compliance) - 100 (stiff / aero stability)
    gear_ratio: float = 50.0  # 0 (short acceleration) - 100 (long top speed)
    brake_bias: float = 56.0  # 50% (rear bias / rotation) - 65% (front bias / stability)

    def copy(self) -> "CarSetup":
        return CarSetup(
            front_wing=self.front_wing,
            rear_wing=self.rear_wing,
            suspension=self.suspension,
            gear_ratio=self.gear_ratio,
            brake_bias=self.brake_bias,
        )


@dataclass
class OptimalTrackSetup:
    """Target sweet-spot values for a specific circuit."""

    front_wing: float = 55.0
    rear_wing: float = 58.0
    suspension: float = 50.0
    gear_ratio: float = 55.0
    brake_bias: float = 56.5
    tolerance: float = 8.0  # +/- tolerance where setup is considered optimal


@dataclass
class SliderCurve:
    """Hidden setup curve with dual sweet spots: Peak Performance vs Peak Tire Preservation."""

    perf_target: float  # Slider value that maximizes pure pace (e.g. 59.0)
    wear_target: float  # Slider value that minimizes tire degradation (e.g. 41.0)
    tolerance: float = 6.0  # Margin of near-optimal operation
    min_val: float = 0.0
    max_val: float = 100.0

    def evaluate_perf(self, value: float) -> float:
        """Returns 0.20 to 1.0 depending on distance to perf_target."""
        val_clamped = max(self.min_val, min(self.max_val, value))
        span = max(1.0, self.max_val - self.min_val)
        dist = abs(val_clamped - self.perf_target)
        norm_dist = dist / (span * 0.40)
        score = max(0.20, 1.0 - (norm_dist**1.7) * 0.80)
        return score

    def evaluate_wear(self, value: float) -> float:
        """Returns 0.20 to 1.0 depending on distance to wear_target."""
        val_clamped = max(self.min_val, min(self.max_val, value))
        span = max(1.0, self.max_val - self.min_val)
        dist = abs(val_clamped - self.wear_target)
        norm_dist = dist / (span * 0.40)
        score = max(0.20, 1.0 - (norm_dist**1.7) * 0.80)
        return score


class SessionTimeClock(dict):
    """
    Synchronized Free Practice session countdown clock shared across pit crews.
    Supports float-like operations and dict-like indexing:
      clock.time -> float
      clock[1] -> float
      clock[2] -> float
    """

    def __init__(self, initial_time: float = 60.0):
        t = round(float(initial_time), 2)
        super().__init__({1: t, 2: t})
        self._time = t

    @property
    def time(self) -> float:
        return self._time

    @time.setter
    def time(self, val: float):
        self._time = max(0.0, round(float(val), 2))
        dict.__setitem__(self, 1, self._time)
        dict.__setitem__(self, 2, self._time)

    def __getitem__(self, key):
        return self._time

    def __setitem__(self, key, val):
        self._time = max(0.0, round(float(val), 2))
        dict.__setitem__(self, 1, self._time)
        dict.__setitem__(self, 2, self._time)

    def __float__(self) -> float:
        return self._time

    def __le__(self, other):
        return self._time <= float(other)

    def __lt__(self, other):
        return self._time < float(other)

    def __ge__(self, other):
        return self._time >= float(other)

    def __gt__(self, other):
        return self._time > float(other)

    def __eq__(self, other):
        if isinstance(other, (int, float)):
            return self._time == float(other)
        return super().__eq__(other)

    def __sub__(self, other):
        return self._time - float(other)

    def __rsub__(self, other):
        return float(other) - self._time

    def __repr__(self):
        return f"SessionTimeClock({self._time:.1f}m)"

    def get(self, key, default=None):
        return self._time


class RaceWeekendManager:
    """
    Coordinates an entire Grand Prix weekend across all sessions:
    - Tier 3: FP1 -> FP2 -> QUALIFYING -> SPRINT
    - Tier 2: FP1 -> FP2 -> QUALIFYING -> RACE
    - Tier 1: FP1 -> FP2 -> FP3 -> QUALIFYING -> SPRINT (Top 10 Reverse Grid) -> RACE
    """

    SPRINT_POINTS = [8, 7, 6, 5, 4, 3, 2, 1]
    RACE_POINTS = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]

    # Free Practice Session Time Budget & Stint Costs
    SESSION_DURATION_MINUTES: float = 60.0
    GARAGE_PREP_MINUTES: float = 4.0
    MINUTES_PER_LAP: float = 1.45

    def __init__(
        self,
        league_tier: int,
        track_metadata: Dict[str, Any],
        total_laps_base: int = 22,
        facility_tiers: Optional[Dict[str, int]] = None,
        equipment_levels: Optional[Dict[str, int]] = None,
    ):
        self.tier = league_tier
        self.track_metadata = track_metadata
        self.track_name = track_metadata.get("track_name", "Grand Prix Circuit")
        self.circuit_file = track_metadata.get("circuit_file", "emerald_ring.json")
        self.total_laps_base = total_laps_base
        self.facility_tiers: Dict[str, int] = facility_tiers or {}
        self.equipment_levels: Dict[str, int] = equipment_levels or {}

        # Determine track length and estimate average lap time
        self.track_length_m: float = self._resolve_track_length(track_metadata)
        # Average racing speed across formula cars ~38 m/s (~137 km/h including low-speed corners)
        self.estimated_lap_seconds: float = max(35.0, min(140.0, self.track_length_m / 38.0))
        self.minutes_per_lap: float = round(self.estimated_lap_seconds / 60.0, 3)

        # Dynamic stint lap counts calibrated to keep stint durations consistent across all tracks:
        # SHORT: ~10 min total (4 min garage prep + ~6 min running)
        # SPRINT: ~20 min total (4 min garage prep + ~16 min running)
        # LONG: ~32 min total (4 min garage prep + ~28 min running)
        self.stint_laps: Dict[str, int] = {
            StintType.SHORT.value: max(3, int(round(6.0 / self.minutes_per_lap))),
            StintType.SPRINT.value: max(7, int(round(16.0 / self.minutes_per_lap))),
            StintType.LONG.value: max(12, int(round(28.0 / self.minutes_per_lap))),
        }

        # Calculate session lengths
        self.sprint_laps = max(7, int(round(total_laps_base * 0.38)))
        self.race_laps = max(18, total_laps_base)

        # Build session sequence based on league tier
        self.sessions: List[RaceWeekendSession] = self._build_session_schedule(self.tier)
        self.current_session_index: int = 0

        # Optimal setup baseline for this circuit
        self.optimal_setup = self._derive_optimal_setup(track_metadata)

        # Hidden Dual-Peak Setup Curves per Car (Car 1 and Car 2 have distinct sweet spots)
        self.car_curves: Dict[int, Dict[str, SliderCurve]] = {
            1: self._generate_car_curves(track_metadata, car_slot=1),
            2: self._generate_car_curves(track_metadata, car_slot=2),
        }

        # Initial setups per car (Car 1 and Car 2)
        # Pre-Weekend Virtual Rig (track_virtual_sim) seeds initial setup closer to optimal
        vsim_tier = self.facility_tiers.get("track_virtual_sim", 0)
        initial_setups = {}
        for slot in (1, 2):
            if vsim_tier > 0:
                initial_setups[slot] = self.get_factory_preset(slot)
            else:
                initial_setups[slot] = CarSetup()

        self.car_setups: Dict[int, CarSetup] = initial_setups

        # Practice Plans per car (kept for backward compatibility, mapped to stint types)
        self.practice_plans: Dict[int, Any] = {1: PracticePlan.BALANCED, 2: PracticePlan.BALANCED}

        # Shared Free Practice Session Time Clock (60:00 minutes)
        self.session_time_remaining = SessionTimeClock(self.SESSION_DURATION_MINUTES)
        self.session_laps_completed: Dict[int, int] = {1: 0, 2: 0}

        # Active stint state per car (None if in pit garage, or dict if out on circuit)
        self.active_stints: Dict[int, Optional[Dict[str, Any]]] = {1: None, 2: None}

        # Circuit representation & ambient Free Practice traffic
        self._circuit: Optional[Any] = None
        self.fp_cars: List[Dict[str, Any]] = []
        self._init_fp_traffic()

        # Setup Confidence (0.0 to 100.0) per car (boosted by virtual sim and rubber testing bench)
        base_confidence = 25.0
        if vsim_tier > 0:
            vsim_rubber_lvl = self.equipment_levels.get("eq_vsim_tire_degrade_sim", 0)
            vsim_neural_lvl = self.equipment_levels.get("eq_vsim_driver_neural_link", 0)
            base_confidence = min(
                85.0, base_confidence + (vsim_tier * 10.0) + (vsim_rubber_lvl * 4.0) + (vsim_neural_lvl * 3.0)
            )

        self.setup_confidence: Dict[int, float] = {1: base_confidence, 2: base_confidence}

        # Driver feedback log per car: list of feedback message dicts
        self.driver_feedback: Dict[int, List[Dict[str, Any]]] = {1: [], 2: []}

        # Plan bonuses accumulated during practice
        self.practice_bonuses: Dict[int, Dict[str, float]] = {
            1: {"qualy_pace_bonus": 0.0, "sprint_wear_bonus": 0.0, "race_wear_bonus": 0.0, "fuel_saving_bonus": 0.0},
            2: {"qualy_pace_bonus": 0.0, "sprint_wear_bonus": 0.0, "race_wear_bonus": 0.0, "fuel_saving_bonus": 0.0},
        }

        # Session results storage
        self.practice_results: Dict[str, List[Dict[str, Any]]] = {}
        self.qualifying_results: List[Dict[str, Any]] = []  # P1 to P20
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
                RaceWeekendSession.SPRINT,
            ]
        elif tier == 2:
            # Tier 2 (Continental): 2 Practice Sessions, 1 Qualifying, 1 Normal Race
            return [
                RaceWeekendSession.FP1,
                RaceWeekendSession.FP2,
                RaceWeekendSession.QUALIFYING,
                RaceWeekendSession.RACE,
            ]
        else:
            # Tier 1 (World Super Formula): FP1 -> FP2 -> QUALIFYING -> SPRINT (Reverse Grid) -> FP3 (Race Fine-Tuning) -> RACE
            return [
                RaceWeekendSession.FP1,
                RaceWeekendSession.FP2,
                RaceWeekendSession.QUALIFYING,
                RaceWeekendSession.SPRINT,
                RaceWeekendSession.FP3,
                RaceWeekendSession.RACE,
            ]

    def _resolve_track_length(self, track_meta: Dict[str, Any]) -> float:
        """
        Resolves track length in meters from metadata, circuit files, or fallback presets.
        """
        # 1. Explicit in track metadata
        if "track_length_m" in track_meta:
            return float(track_meta["track_length_m"])
        if "length" in track_meta:
            return float(track_meta["length"])

        # 2. Try loading from circuits JSON file in tracks directory
        c_file = track_meta.get("circuit_file", "")
        if c_file:
            track_path = os.path.join("tracks", c_file)
            if os.path.exists(track_path):
                try:
                    from .circuit import Circuit

                    c = Circuit.load_json(track_path)
                    if c.length > 50.0:
                        return float(c.length)
                except Exception:
                    # Ignore corrupted or unreadable circuit JSON and fall back to known lengths
                    pass

        # 3. Known fallback lengths based on track file name
        cf_lower = c_file.lower()
        if "harbor" in cf_lower:
            return 1792.0
        elif "apex" in cf_lower:
            return 2338.0
        elif "velocita" in cf_lower or "monza" in cf_lower:
            return 3366.0
        elif "ardennes" in cf_lower or "spa" in cf_lower:
            return 2582.0
        elif "oasis" in cf_lower:
            return 3016.0
        elif "riviera" in cf_lower:
            return 2464.0
        elif "vortex" in cf_lower:
            return 2606.0

        # Default standard circuit length (Emerald Ring baseline)
        return 2789.0

    def _derive_optimal_setup(self, track_meta: Dict[str, Any]) -> OptimalTrackSetup:
        """Derives track sweet spot from track characteristics."""
        c_file = track_meta.get("circuit_file", "").lower()

        # High downforce street circuit
        if "harbor" in c_file:
            return OptimalTrackSetup(
                front_wing=76.0,
                rear_wing=80.0,
                suspension=38.0,  # softer for street bumps
                gear_ratio=42.0,  # short gearing for tight acceleration
                brake_bias=57.5,
                tolerance=7.5,
            )
        # High speed power temple
        elif "apex" in c_file:
            return OptimalTrackSetup(
                front_wing=42.0,
                rear_wing=45.0,
                suspension=68.0,  # stiff platform for high-speed sweepers
                gear_ratio=74.0,  # long gearing for top speed
                brake_bias=55.5,
                tolerance=8.0,
            )
        # Technical balanced circuit
        else:  # Emerald Ring
            return OptimalTrackSetup(
                front_wing=58.0, rear_wing=62.0, suspension=54.0, gear_ratio=56.0, brake_bias=56.0, tolerance=8.0
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
            return 5  # Practice stint
        elif self.is_qualifying:
            return 3  # Out-lap, flying lap, in-lap
        elif self.is_sprint:
            return self.sprint_laps
        else:
            return self.race_laps

    def is_chequered_flag(self, car_slot: int = 1) -> bool:
        """Returns True if the practice session time has run out."""
        return float(self.session_time_remaining) <= 0.0

    def is_car_on_track(self, car_slot: int) -> bool:
        """Returns True if car is currently out on an active stint."""
        return self.active_stints.get(car_slot) is not None

    def _generate_car_curves(self, track_meta: Dict[str, Any], car_slot: int) -> Dict[str, SliderCurve]:
        """
        Generates distinct dual-peak curves (Performance vs Tire Preservation) for each car.
        Car 1 and Car 2 have different optimal sweet spots reflecting chassis tolerances
        and individual driver handling preferences.
        """
        opt = self.optimal_setup
        # Car 2 has a distinct offset from Car 1 (e.g. driver prefers different balance)
        slot_offset = 0.0 if car_slot == 1 else random.choice([-5.0, -3.5, 3.5, 5.0])

        def _make_curve(
            base_perf: float, wear_delta: float, min_v: float = 0.0, max_v: float = 100.0, tol: float = 6.0
        ) -> SliderCurve:
            p_tgt = max(min_v + 10.0, min(max_v - 10.0, base_perf + slot_offset + random.uniform(-1.5, 1.5)))
            # Wear target is offset (e.g. -16.0 for wing/suspension downforce trade-off)
            w_tgt = max(min_v + 5.0, min(max_v - 5.0, p_tgt + wear_delta + random.uniform(-1.5, 1.5)))
            return SliderCurve(
                perf_target=round(p_tgt, 1),
                wear_target=round(w_tgt, 1),
                tolerance=tol,
                min_val=min_v,
                max_val=max_v,
            )

        # Brake bias range: 50.0 to 65.0
        bb_opt = opt.brake_bias
        bb_perf = max(51.0, min(64.0, bb_opt + (0.0 if car_slot == 1 else random.uniform(-0.6, 0.6))))
        bb_wear = max(50.5, min(64.5, bb_perf + random.choice([-1.2, 1.2])))

        return {
            "front_wing": _make_curve(opt.front_wing, wear_delta=-16.0, tol=opt.tolerance),
            "rear_wing": _make_curve(opt.rear_wing, wear_delta=-14.0, tol=opt.tolerance),
            "suspension": _make_curve(opt.suspension, wear_delta=-18.0, tol=opt.tolerance),
            "gear_ratio": _make_curve(opt.gear_ratio, wear_delta=-10.0, tol=opt.tolerance),
            "brake_bias": SliderCurve(
                perf_target=round(bb_perf, 1),
                wear_target=round(bb_wear, 1),
                tolerance=0.7,
                min_val=50.0,
                max_val=65.0,
            ),
        }

    def get_factory_preset(self, car_slot: int) -> CarSetup:
        """
        Returns starting slider values calculated by factory pre-weekend simulations.
        Higher facility and equipment tiers produce presets closer to the optimal zone.
        """
        vsim_tier = self.facility_tiers.get("track_virtual_sim", 0)
        vsim_solver_lvl = self.equipment_levels.get("eq_vsim_cloud_cluster", 0)
        if vsim_tier <= 0:
            return CarSetup()

        drift_max = max(2.5, 18.0 - (vsim_tier * 4.5) - (vsim_solver_lvl * 1.5))
        curves = self.car_curves.get(car_slot, self.car_curves.get(1, {}))
        c_opt = self.optimal_setup

        def _preset_val(p_key: str, opt_val: float, min_v: float, max_v: float, is_bb: bool = False) -> float:
            if p_key in curves:
                curve = curves[p_key]
                # Anchor around optimal_setup to maintain compatibility with virtual sim benchmarks
                midpoint = (curve.perf_target + curve.wear_target) / 2.0
                # Blend midpoint with track optimal for reliable facility progression
                anchor = 0.60 * midpoint + 0.40 * opt_val
            else:
                anchor = opt_val
            scale = 0.15 if is_bb else 1.0
            val = anchor + random.uniform(-drift_max * scale, drift_max * scale)
            return max(min_v, min(max_v, round(val, 1)))

        return CarSetup(
            front_wing=_preset_val("front_wing", c_opt.front_wing, 0.0, 100.0),
            rear_wing=_preset_val("rear_wing", c_opt.rear_wing, 0.0, 100.0),
            suspension=_preset_val("suspension", c_opt.suspension, 0.0, 100.0),
            gear_ratio=_preset_val("gear_ratio", c_opt.gear_ratio, 0.0, 100.0),
            brake_bias=_preset_val("brake_bias", c_opt.brake_bias, 50.0, 65.0, is_bb=True),
        )

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

    def get_setup_guidance_ranges(self, car_slot: int = 1) -> Optional[Dict[str, Tuple[float, float]]]:
        """
        Calculates recommended target setup ranges ([min, max]) for each parameter
        if the Setup Analytics facility (track_setup_telemetry) is unlocked.
        Higher facility tiers and specialized equipment narrow the guidance brackets.
        """
        analytics_tier = self.facility_tiers.get("track_setup_telemetry", 0)
        if analytics_tier <= 0:
            return None

        laser_lvl = self.equipment_levels.get("eq_set_laser_ride_sensors", 0)
        pushrod_lvl = self.equipment_levels.get("eq_set_pushrod_strain_links", 0)
        pyro_lvl = self.equipment_levels.get("eq_set_brake_rotor_pyrometers", 0)

        curves = self.car_curves.get(car_slot, self.car_curves.get(1, {}))
        opt = self.optimal_setup

        base_radius = max(3.0, 18.0 - (analytics_tier * 4.5))
        aero_radius = max(2.5, base_radius - (laser_lvl * 0.8))
        susp_radius = max(2.5, base_radius - (pushrod_lvl * 0.8))
        mech_radius = max(2.5, base_radius - (pyro_lvl * 0.8))
        bb_radius = max(0.5, (base_radius * 0.15) - (pyro_lvl * 0.1))

        fw_target = curves["front_wing"].perf_target if "front_wing" in curves else opt.front_wing
        rw_target = curves["rear_wing"].perf_target if "rear_wing" in curves else opt.rear_wing
        susp_target = curves["suspension"].perf_target if "suspension" in curves else opt.suspension
        gear_target = curves["gear_ratio"].perf_target if "gear_ratio" in curves else opt.gear_ratio
        bb_target = curves["brake_bias"].perf_target if "brake_bias" in curves else opt.brake_bias

        return {
            "front_wing": (max(0.0, fw_target - aero_radius), min(100.0, fw_target + aero_radius)),
            "rear_wing": (max(0.0, rw_target - aero_radius), min(100.0, rw_target + aero_radius)),
            "suspension": (max(0.0, susp_target - susp_radius), min(100.0, susp_target + susp_radius)),
            "gear_ratio": (max(0.0, gear_target - mech_radius), min(100.0, gear_target + mech_radius)),
            "brake_bias": (max(50.0, bb_target - bb_radius), min(65.0, bb_target + bb_radius)),
        }

    def evaluate_slider_perf(self, car_slot: int, parameter: str, value: float) -> float:
        """Returns 0.20 to 1.0 performance factor for a specific slider on a given car."""
        curves = self.car_curves.get(car_slot, self.car_curves.get(1, {}))
        if parameter in curves:
            return curves[parameter].evaluate_perf(value)
        return 0.70

    def evaluate_slider_wear(self, car_slot: int, parameter: str, value: float) -> float:
        """Returns 0.20 to 1.0 tire preservation factor for a specific slider on a given car."""
        curves = self.car_curves.get(car_slot, self.car_curves.get(1, {}))
        if parameter in curves:
            return curves[parameter].evaluate_wear(value)
        return 0.70

    def evaluate_car_setup_scores(self, car_slot: int, setup: Optional[CarSetup] = None) -> Tuple[float, float]:
        """
        Calculates aggregate (perf_score, wear_score) in [0.20, 1.0]
        based on each slider's position along its hidden curves.
        """
        if setup is None:
            setup = self.car_setups.get(car_slot, CarSetup())
        curves = self.car_curves.get(car_slot, self.car_curves.get(1, {}))
        if not curves:
            return (0.75, 0.75)

        weights = {
            "front_wing": 1.2,
            "rear_wing": 1.2,
            "suspension": 0.9,
            "gear_ratio": 1.0,
            "brake_bias": 0.7,
        }
        total_w = sum(weights.values())

        p_sum = sum(
            curves[param].evaluate_perf(getattr(setup, param)) * w for param, w in weights.items() if param in curves
        )
        w_sum = sum(
            curves[param].evaluate_wear(getattr(setup, param)) * w for param, w in weights.items() if param in curves
        )

        perf_score = max(0.20, min(1.0, p_sum / total_w))
        wear_score = max(0.20, min(1.0, w_sum / total_w))
        return (perf_score, wear_score)

    def evaluate_setup_closeness(self, setup: CarSetup, car_slot: int = 1) -> float:
        """
        Calculates setup accuracy score from 0.0 to 1.0 based on distance
        from optimal track setup.
        """
        perf_score, wear_score = self.evaluate_car_setup_scores(car_slot, setup)
        return round(0.55 * perf_score + 0.45 * wear_score, 3)

    def get_circuit(self) -> Optional[Any]:
        """Loads and returns the Circuit representation for mini-map telemetry."""
        if self._circuit is not None:
            return self._circuit

        c_file = self.track_metadata.get("circuit_file", "")
        if c_file:
            track_path = os.path.join("tracks", c_file)
            if os.path.exists(track_path):
                try:
                    from .circuit import Circuit

                    self._circuit = Circuit.load_json(track_path)
                    return self._circuit
                except Exception:
                    pass

        try:
            from .circuit import Circuit

            circ = Circuit(name=self.track_name)
            pts = [
                (200.0, 400.0),
                (350.0, 600.0),
                (650.0, 600.0),
                (800.0, 400.0),
                (800.0, 200.0),
                (650.0, 100.0),
                (350.0, 100.0),
                (200.0, 200.0),
            ]
            circ.set_control_points(pts)
            self._circuit = circ
            return self._circuit
        except Exception:
            return None

    def _init_fp_traffic(self):
        """Initializes ambient AI cars circulating the track during Free Practice."""
        team_configs = [
            ("Apex Racing", (220, 50, 50)),
            ("Vortex Motorsport", (50, 150, 240)),
            ("Silverstone Speed", (220, 220, 230)),
            ("Modena Scuderia", (240, 20, 20)),
            ("Bavaria GP", (30, 90, 220)),
            ("Nordic Pole", (60, 220, 160)),
            ("Kyoto Dyno", (240, 180, 40)),
            ("Titan GP", (160, 80, 220)),
        ]
        circ_len = self.track_length_m if self.track_length_m > 0 else 2500.0
        self.fp_cars = []
        for idx, (t_name, col) in enumerate(team_configs):
            for car_idx in (1, 2):
                s_dist = (idx * (circ_len / len(team_configs)) + car_idx * (circ_len * 0.12)) % circ_len
                in_pit = (idx + car_idx) % 3 == 0
                self.fp_cars.append(
                    {
                        "car_id": f"{t_name}_{car_idx}",
                        "team_name": t_name,
                        "color": col,
                        "dist_m": float(s_dist),
                        "speed_mps": random.uniform(36.0, 44.0),
                        "in_pit": in_pit,
                        "pit_timer": random.uniform(5.0, 20.0),
                    }
                )

    def update_fp_traffic(self, dt_seconds: float):
        """Animates FP cars and active player cars circulating along the track."""
        dt_seconds = max(0.0, min(1.0, float(dt_seconds)))
        circ_len = self.track_length_m if self.track_length_m > 0 else 2500.0
        for car in self.fp_cars:
            car["pit_timer"] -= dt_seconds
            if car["pit_timer"] <= 0.0:
                car["in_pit"] = not car["in_pit"]
                car["pit_timer"] = random.uniform(15.0, 40.0) if car["in_pit"] else random.uniform(25.0, 60.0)

            if not car["in_pit"]:
                car["dist_m"] = (car["dist_m"] + car["speed_mps"] * dt_seconds) % circ_len

        for slot in (1, 2):
            stint = self.active_stints.get(slot)
            if stint is not None:
                p_dist = stint.get("dist_m", (slot - 1) * 350.0)
                stint["dist_m"] = (p_dist + 40.0 * dt_seconds) % circ_len

    def start_practice_stint(
        self,
        car_slot: int,
        driver_name: str,
        stint_type: Any = "SHORT",
        laps_run: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Launches a practice stint for a specific car slot.
        The car enters RUNNING state; feedback is deferred until the stint finishes.
        """
        st_val = stint_type.value if hasattr(stint_type, "value") else str(stint_type)
        if laps_run is None:
            laps_run = self.stint_laps.get(st_val, 5)

        rem_time = float(self.session_time_remaining)
        if rem_time <= 0.0:
            return {
                "success": False,
                "status": "EXPIRED",
                "message": "Chequered flag! Free practice session time has expired.",
                "is_expired": True,
            }

        if self.active_stints.get(car_slot) is not None:
            return {
                "success": False,
                "status": "RUNNING",
                "message": f"Car #{car_slot} is already out on track completing a stint.",
                "is_expired": False,
            }

        time_cost = round(self.GARAGE_PREP_MINUTES + laps_run * self.minutes_per_lap, 1)
        if time_cost > rem_time:
            actual_time = rem_time
            available_lap_time = max(0.0, rem_time - self.GARAGE_PREP_MINUTES)
            laps_run = max(1, int(available_lap_time / self.minutes_per_lap))
            time_cost = actual_time

        stint_record = {
            "car_slot": car_slot,
            "driver_name": driver_name,
            "stint_type": st_val,
            "laps_target": laps_run,
            "total_duration_min": time_cost,
            "time_remaining_min": time_cost,
            "setup_snapshot": self.car_setups[car_slot].copy(),
            "dist_m": (car_slot - 1) * 350.0,
        }
        self.active_stints[car_slot] = stint_record

        return {
            "success": True,
            "status": "STARTED",
            "stint_record": stint_record,
            "time_cost_min": time_cost,
            "laps_target": laps_run,
            "message": f"Car #{car_slot} dispatched on {st_val} stint ({laps_run} laps, ~{time_cost:.0f}m).",
            "is_expired": False,
        }

    def advance_session_time(self, minutes: float) -> List[Dict[str, Any]]:
        """
        Advances session time by `minutes`, progressing active stints.
        When an active stint's time remaining reaches 0, it completes, debrief comments
        are computed and appended to driver_feedback[car_slot], and confidence grows.
        """
        minutes = max(0.0, round(minutes, 2))
        if minutes <= 0.0:
            return []

        old_time = float(self.session_time_remaining)
        new_time = max(0.0, round(old_time - minutes, 2))
        actual_elapsed = round(old_time - new_time, 2)
        self.session_time_remaining.time = new_time

        completed = []
        for slot in (1, 2):
            stint = self.active_stints.get(slot)
            if stint is None:
                continue

            stint["time_remaining_min"] = max(0.0, round(stint["time_remaining_min"] - actual_elapsed, 2))
            if stint["time_remaining_min"] <= 0.0 or new_time <= 0.0:
                res = self._complete_stint(stint)
                self.active_stints[slot] = None
                completed.append(res)

        return completed

    def fast_forward_to_next_completion(self) -> float:
        """
        Fast-forwards session time to when the earliest active car completes its stint.
        If no car is running, advances session time by 5.0 minutes.
        """
        running = [s for s in self.active_stints.values() if s is not None]
        if not running:
            delta = min(5.0, float(self.session_time_remaining))
        else:
            delta = min(s["time_remaining_min"] for s in running)
            delta = min(delta, float(self.session_time_remaining))

        if delta > 0.0:
            self.advance_session_time(delta)
        return delta

    def _complete_stint(self, stint: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates debrief, confidence, and program bonuses upon stint completion."""
        car_slot = stint["car_slot"]
        driver_name = stint["driver_name"]
        stint_type = stint["stint_type"]
        laps_run = stint["laps_target"]
        time_cost = stint["total_duration_min"]
        setup = stint["setup_snapshot"]

        self.session_laps_completed[car_slot] = self.session_laps_completed.get(car_slot, 0) + laps_run

        curves = self.car_curves.get(car_slot, self.car_curves.get(1, {}))
        perf_score, wear_score = self.evaluate_car_setup_scores(car_slot, setup)
        closeness = self.evaluate_setup_closeness(setup, car_slot)

        comments = []

        # 1. Slider-by-slider performance debrief
        fw = setup.front_wing
        fw_c = curves.get("front_wing", SliderCurve(55.0, 40.0))
        fw_p_delta = fw - fw_c.perf_target
        if fw_p_delta < -fw_c.tolerance:
            comments.append("Front Wing: Mid-corner understeer; front end needs more angle for turn-in grip.")
        elif fw_p_delta > fw_c.tolerance:
            comments.append("Front Wing: Front end is twitchy; excess wing angle is causing drag.")
        else:
            comments.append("Front Wing: Turn-in bite and aero front-end balance feel dialed in for pace.")

        rw = setup.rear_wing
        rw_c = curves.get("rear_wing", SliderCurve(58.0, 44.0))
        rw_p_delta = rw - rw_c.perf_target
        if rw_p_delta < -rw_c.tolerance:
            comments.append("Rear Wing: Rear steps out under traction on corner exit; increase rear downforce.")
        elif rw_p_delta > rw_c.tolerance:
            comments.append("Rear Wing: Heavy aerodynamic drag on straights; wing angle is hurting top speed.")
        else:
            comments.append("Rear Wing: High-speed rear stability and traction are locked in.")

        susp = setup.suspension
        susp_c = curves.get("suspension", SliderCurve(50.0, 32.0))
        susp_p_delta = susp - susp_c.perf_target
        if susp_p_delta < -susp_c.tolerance:
            comments.append("Suspension: Chassis rolls excessively through high-speed sweepers; stiffen setup.")
        elif susp_p_delta > susp_c.tolerance:
            comments.append("Suspension: Violent deflection over the kerbs; platform is too stiff.")
        else:
            comments.append("Suspension: Kerb compliance and aerodynamic platform control are optimal.")

        gear = setup.gear_ratio
        gear_c = curves.get("gear_ratio", SliderCurve(55.0, 45.0))
        gear_p_delta = gear - gear_c.perf_target
        if gear_p_delta < -gear_c.tolerance:
            comments.append("Gear Ratio: Hitting the rev limiter too early down the straight; lengthen ratios.")
        elif gear_p_delta > gear_c.tolerance:
            comments.append("Gear Ratio: Sluggish acceleration out of slow corners; top gears are too tall.")
        else:
            comments.append("Gear Ratio: Acceleration cadence and top speed match the straightaways.")

        bb = setup.brake_bias
        bb_c = curves.get("brake_bias", SliderCurve(56.5, 55.5, tolerance=0.7))
        bb_p_delta = bb - bb_c.perf_target
        if bb_p_delta < -bb_c.tolerance:
            comments.append("Brake Bias: Rear brake instability during trail-braking; move bias forward.")
        elif bb_p_delta > bb_c.tolerance:
            comments.append("Brake Bias: Front wheels lock up prematurely under heavy braking; shift bias rearward.")
        else:
            comments.append("Brake Bias: Braking balance and deceleration stability are spot-on.")

        # 2. Tire Wear & Degradation Debrief
        short_lap_thresh = max(4, self.stint_laps.get(StintType.SHORT.value, 4) + 1)
        if laps_run < short_lap_thresh:
            comments.append(
                f"⚠️ Stint too short (<{short_lap_thresh} laps) to evaluate tire degradation curve. Run a Sprint or Long Stint for tire wear data."
            )
        else:
            degrade_rate = round((1.5 - wear_score * 0.70) * 2.8, 1)
            comments.append(f"Tire Degradation Rate: ~{degrade_rate:.1f}% per lap over {laps_run}-lap stint.")

            fw_w_delta = fw - fw_c.wear_target
            if fw_w_delta > fw_c.tolerance:
                comments.append(
                    f"Tire Wear: Front wing is aggressively scrubbing tires; softening toward ~{fw_c.wear_target:.0f} will extend tire life."
                )
            elif fw_w_delta < -fw_c.tolerance:
                comments.append(
                    f"Tire Wear: Front push is causing diagonal tire scrub; adjusting toward ~{fw_c.wear_target:.0f} balances thermal wear."
                )
            else:
                comments.append("Tire Wear: Front tire preservation is in the optimal window.")

            susp_w_delta = susp - susp_c.wear_target
            if susp_w_delta > susp_c.tolerance:
                comments.append("Tire Wear: Stiff suspension is spiking surface temperatures over bumps.")
            elif susp_w_delta < -susp_c.tolerance:
                comments.append("Tire Wear: Soft suspension roll is overloading outer tire shoulders.")
            else:
                comments.append("Tire Wear: Suspension kinematics provide gentle tire contact and minimal graining.")

        # Summary quote
        if perf_score > 0.88 and wear_score > 0.88:
            summary = "Incredible setup! Car is rapid on flying laps and tires barely degrade."
        elif perf_score > 0.88:
            summary = "Car is blistering fast! Pace is at its peak, though tires will wear in the race."
        elif wear_score > 0.88:
            summary = "Tires are bulletproof with exceptional degradation, though we gave up a little single-lap pace."
        elif closeness > 0.70:
            summary = "Solid baseline found. A few tweaks will optimize both pace and tire life."
        else:
            summary = "Struggling with balance. Setup is outside the optimal operating window."

        # Setup confidence growth
        growth = (12.0 + closeness * 16.0) * (laps_run / 5.0)
        new_conf = min(100.0, self.setup_confidence[car_slot] + growth)
        self.setup_confidence[car_slot] = new_conf

        # Apply program bonuses linked to stint type
        bonuses = self.practice_bonuses[car_slot]
        st_val = stint_type.value if hasattr(stint_type, "value") else str(stint_type)
        if st_val == StintType.SHORT.value:
            bonuses["qualy_pace_bonus"] = min(0.65, round(bonuses["qualy_pace_bonus"] + 0.22, 2))
        elif st_val == StintType.SPRINT.value:
            bonuses["sprint_wear_bonus"] = min(0.30, round(bonuses["sprint_wear_bonus"] + 0.10, 2))
        elif st_val == StintType.LONG.value:
            bonuses["race_wear_bonus"] = min(0.35, round(bonuses["race_wear_bonus"] + 0.12, 2))
            bonuses["fuel_saving_bonus"] = min(0.15, round(bonuses["fuel_saving_bonus"] + 0.05, 2))

        run_result = {
            "session": self.current_session.value,
            "car_slot": car_slot,
            "driver_name": driver_name,
            "plan": st_val,
            "stint_type": st_val,
            "setup_closeness_pct": round(closeness * 100.0, 1),
            "confidence_pct": round(new_conf, 1),
            "perf_score_pct": round(perf_score * 100.0, 1),
            "wear_score_pct": round(wear_score * 100.0, 1),
            "time_remaining_min": round(float(self.session_time_remaining), 1),
            "time_cost_min": time_cost,
            "summary_quote": summary,
            "feedback_points": comments,
            "laps_completed": laps_run,
            "is_expired": False,
        }

        self.driver_feedback[car_slot].append(run_result)
        return run_result

    def run_practice_run(
        self,
        car_slot: int,
        driver_name: str,
        laps_run: Optional[int] = None,
        stint_type: Any = "SHORT",
    ) -> Dict[str, Any]:
        """
        Synchronous helper for testing or direct evaluation:
        Starts stint and immediately advances session time until it finishes.
        """
        st_val = stint_type.value if hasattr(stint_type, "value") else str(stint_type)
        start_res = self.start_practice_stint(car_slot, driver_name, stint_type=st_val, laps_run=laps_run)
        if not start_res["success"]:
            return {
                "session": self.current_session.value,
                "car_slot": car_slot,
                "driver_name": driver_name,
                "plan": st_val,
                "stint_type": st_val,
                "setup_closeness_pct": round(
                    self.evaluate_setup_closeness(self.car_setups[car_slot], car_slot) * 100.0, 1
                ),
                "confidence_pct": round(self.setup_confidence[car_slot], 1),
                "perf_score_pct": 0.0,
                "wear_score_pct": 0.0,
                "time_remaining_min": round(float(self.session_time_remaining), 1),
                "time_cost_min": 0.0,
                "summary_quote": "Chequered flag! Free practice session time has expired.",
                "feedback_points": ["Session time is over. Advance to the next session on pit wall."],
                "laps_completed": 0,
                "is_expired": True,
            }

        stint = self.active_stints[car_slot]
        dur = stint["time_remaining_min"]
        completed = self.advance_session_time(dur)
        for c in completed:
            if c["car_slot"] == car_slot:
                return c
        return self.driver_feedback[car_slot][-1] if self.driver_feedback[car_slot] else {}

    def simulate_qualifying_session(self, all_drivers_cars: List[Tuple[Any, Any]]) -> List[Dict[str, Any]]:
        """
        Simulates flying laps for all 20 drivers to determine the qualifying grid.
        Takes into account car power, driver pace, setup confidence, and fast-lap bonuses.
        """
        qualy_entries = []
        base_lap_time = self.estimated_lap_seconds  # Circuit-calibrated baseline lap

        for driver, car_attrs in all_drivers_cars:
            # Power & Aero delta
            eng_val = getattr(car_attrs, "engine_power", 80.0)
            aero_val = getattr(car_attrs, "aero_downforce", 80.0)
            car_perf_bonus = (eng_val - 50.0) * 0.04 + (aero_val - 50.0) * 0.05

            # Driver speed delta
            drv_speed = getattr(driver, "speed", 0.75) * 100.0
            drv_cons = getattr(driver, "consistency", 0.75) * 100.0
            drv_bonus = (drv_speed - 50.0) * 0.035

            # If player driver, apply setup confidence, setup performance curve & practice plan bonus
            player_bonus = 0.0
            if getattr(driver, "is_player", False):
                # Car 1 or Car 2
                c_slot = 1 if getattr(driver, "number", 1) % 2 != 0 else 2
                conf = self.setup_confidence[c_slot]
                bonuses = self.practice_bonuses[c_slot]
                perf_score, _ = self.evaluate_car_setup_scores(c_slot)
                # Up to 0.40s gain from dialed-in setup performance curve (or penalty if setup is poor)
                setup_pace_bonus = (perf_score - 0.50) * 0.40
                player_bonus = (conf / 100.0) * 0.35 + setup_pace_bonus + bonuses.get("qualy_pace_bonus", 0.0)

            # Random variance filtered by consistency
            var_spread = max(0.05, 0.40 - (drv_cons / 100.0) * 0.25)
            variance = random.uniform(-var_spread, var_spread)

            final_lap_time = base_lap_time - car_perf_bonus - drv_bonus - player_bonus + variance
            final_lap_time = max(55.0, final_lap_time)

            qualy_entries.append(
                {
                    "driver": driver,
                    "driver_name": getattr(driver, "name", "Driver"),
                    "team_name": getattr(driver, "team_name", "Team"),
                    "is_player": getattr(driver, "is_player", False),
                    "number": getattr(driver, "number", 1),
                    "car_attrs": car_attrs,
                    "lap_time": final_lap_time,
                }
            )

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
            if self.is_practice:
                # Reset practice session timer and stint lap counter for both cars
                self.session_time_remaining = SessionTimeClock(self.SESSION_DURATION_MINUTES)
                self.session_laps_completed = {1: 0, 2: 0}
                self.active_stints = {1: None, 2: None}
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
