from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class TireCompound:
    name: str
    code: str
    tier: str  # "C1", "C2", "C3", "C4", "C5", "WET"
    color_rgb: Tuple[int, int, int]
    base_grip: float  # Peak grip multiplier
    deg_per_lap: float  # % base wear per normal clean lap
    cliff_wear_pct: float  # Wear percentage where grip falls off the cliff
    optimal_temp: float  # Ideal operating temp in °C
    wet_suitability: float  # 0.0 for slicks (unusable in rain), 1.0 for wet
    wet_capability: float = 0.10  # Max wetness threshold where tire operates well


from ..data.balance_config import TIRE_CONFIGS

# Complete 5-Compound Dry Range + 2 Wet Compounds sourced from central balance_config
TIRE_COMPOUNDS: Dict[str, TireCompound] = {
    key: TireCompound(
        name=cfg.name,
        code=cfg.code,
        tier=cfg.tier,
        color_rgb=cfg.color_rgb,
        base_grip=cfg.base_grip,
        deg_per_lap=cfg.deg_per_lap,
        cliff_wear_pct=cfg.cliff_wear_pct,
        optimal_temp=cfg.optimal_temp,
        wet_suitability=cfg.wet_suitability,
        wet_capability=getattr(cfg, "wet_capability", 0.10),
    )
    for key, cfg in TIRE_CONFIGS.items()
}

# Standard 3-compound allocations picked per circuit
TIRE_ALLOCATION_PRESETS: Dict[str, Dict] = {
    "C1-C3": {
        "name": "Hard Range (C1 - C3)",
        "desc": "High tire wear / fast sweeping corners (e.g. Spa, Silverstone)",
        "compounds": ["HARD", "MEDIUM", "SOFT"],
    },
    "C2-C4": {
        "name": "Balanced Range (C2 - C4)",
        "desc": "Standard balanced circuits (e.g. Monza, Spielberg, Emerald Ring)",
        "compounds": ["MEDIUM", "SOFT", "SUPERSOFT"],
    },
    "C3-C5": {
        "name": "Soft Range (C3 - C5)",
        "desc": "Low wear street circuits & stop-and-go tracks (e.g. Monaco, Baku)",
        "compounds": ["SOFT", "SUPERSOFT", "HYPERSOFT"],
    },
}


class TireSet:
    """Represents a fitted set of tires with live lap-scaled wear, thermal physics and cliff degradation."""

    def __init__(self, compound_name: str = "MEDIUM"):
        self.compound_name = compound_name.upper()
        self.compound = TIRE_COMPOUNDS.get(self.compound_name, TIRE_COMPOUNDS["MEDIUM"])
        self.wear_pct = 0.0  # 0.0% is brand new, 100% is completely destroyed
        self.laps_used = 0
        self.temperature = self.compound.optimal_temp
        self.is_punctured = False
        self.is_blistered = False

    def get_effective_grip(self, track_wetness: float = 0.0) -> float:
        """
        Calculates realistic grip coefficient [0.15 - 1.15].
        Accounts for compound base grip, wear degradation cliff, thermal window,
        and wet/dry crossover penalties.
        """
        if self.is_punctured:
            return 0.30

        # 1. Base grip & Wear degradation
        wear = min(100.0, self.wear_pct)
        if wear <= self.compound.cliff_wear_pct:
            # Linear gentle decay before the cliff
            wear_loss = (wear / self.compound.cliff_wear_pct) * 0.12
        else:
            # Steep progressive cliff drop-off past optimal life
            excess = (wear - self.compound.cliff_wear_pct) / (100.0 - self.compound.cliff_wear_pct)
            wear_loss = 0.12 + (excess**2.0) * 0.55

        grip = max(0.30, self.compound.base_grip - wear_loss)

        # 2. Thermal window (Overheating / Blistering vs Cold graining)
        temp_delta = self.temperature - self.compound.optimal_temp
        if temp_delta > 15.0:  # Overheating
            grip -= min(0.20, (temp_delta - 15.0) * 0.009)
        elif temp_delta < -15.0:  # Cold tires
            grip -= min(0.15, abs(temp_delta + 15.0) * 0.006)

        # 3. Track wetness penalty vs compound suitability & operating windows
        if self.compound_name == "INTER":
            # Intermediate tire window: 10% - 80% wetness
            if track_wetness < 0.10:
                # Dry track penalty (groove squirm & lack of water cooling)
                dry_factor = track_wetness / 0.10
                grip *= 0.82 + 0.18 * dry_factor
            elif track_wetness > 0.80:
                # Standing water exceeds groove capacity -> progressive aquaplaning
                aqua_factor = (track_wetness - 0.80) / 0.20
                grip *= max(0.40, 1.0 - (aqua_factor * 0.32))
            # 0.10 <= track_wetness <= 0.80: Optimal operating window
        elif self.compound_name == "WET":
            # Full Wet tire window: 70% - 100% wetness
            if track_wetness >= 0.70:
                # Optimal heavy rain window (massive water clearing capacity)
                pass
            elif track_wetness >= 0.40:
                # Moderate wet: usable but deep tread blocks squirm (inters faster)
                factor = (track_wetness - 0.40) / 0.30
                grip *= 0.84 + 0.16 * factor
            elif track_wetness >= 0.10:
                # Damp track: severe squirm and overheating
                factor = (track_wetness - 0.10) / 0.30
                grip *= 0.70 + 0.14 * factor
            else:
                # Dry track: massive overheating & tread squirm
                grip *= 0.65
        else:
            # Slicks (C1 - C5): Softer compounds perform significantly better in slightly wet / damp conditions
            # Hypersoft / Ultra soft operates up to 20% wetness, Hard struggles around 10%
            cap = getattr(self.compound, "wet_capability", 0.10)
            if track_wetness <= cap:
                # Within compound's damp operating limit:
                # Softer compounds conform to asphalt micro-texture and generate heat easily
                slip_penalty = (track_wetness / max(0.01, cap)) * (
                    0.05 if cap >= 0.18 else (0.09 if cap >= 0.14 else 0.15)
                )
                grip *= 1.0 - slip_penalty
            else:
                # Exceeding compound's wetness capability: rapid cliff and severe aquaplaning
                excess = (track_wetness - cap) / (1.0 - cap)
                base_at_cap = 0.95 if cap >= 0.18 else (0.91 if cap >= 0.14 else 0.85)
                grip *= max(0.18, base_at_cap - (excess**0.85) * 0.80)

        return max(0.18, grip)

    def apply_wear_and_thermals(
        self,
        dist_travelled: float,
        track_length: float,
        dt: float,
        pace_multiplier: float = 1.0,
        cornering_g: float = 1.0,
        fuel_weight_kg: float = 50.0,
        in_dirty_air: bool = False,
        track_wetness: float = 0.0,
    ):
        """
        Updates tire thermal evolution and wear rate proportional to actual distance covered.
        Accounts for fuel weight (+35% wear on full fuel), pace aggression, cornering load, and dirty air.
        """
        if track_length <= 0:
            track_length = 2000.0

        # Thermal heating from speed, cornering load, and dirty air sliding
        heat_gen = pace_multiplier * 1.2 + cornering_g * 0.8
        if in_dirty_air:
            heat_gen += 0.85

        cooling = 1.2 + (track_wetness * 3.0)
        target_temp = self.compound.optimal_temp + (heat_gen - cooling) * 12.0
        self.temperature += (target_temp - self.temperature) * (0.08 * dt)

        if self.temperature > 125.0:
            self.is_blistered = True

        # Fuel weight penalty: full tank (50kg) gives +35% higher wear, empty tank (5kg) ~normal
        fuel_wear_factor = 1.0 + (fuel_weight_kg / 50.0) * 0.35

        # Distance fraction of lap
        lap_fraction = dist_travelled / track_length

        # Base wear calculation for this slice of the track
        slice_wear = lap_fraction * self.compound.deg_per_lap * pace_multiplier * fuel_wear_factor

        # Extra wear penalties
        if self.is_blistered:
            slice_wear *= 1.40
        if in_dirty_air:
            slice_wear *= 1.25

        # Wear penalties on improper wetness surfaces
        if self.compound_name == "INTER":
            if track_wetness < 0.10:
                slice_wear *= 2.2 - 1.2 * (track_wetness / 0.10)
        elif self.compound_name == "WET":
            if track_wetness < 0.10:
                slice_wear *= 3.2
            elif track_wetness < 0.40:
                slice_wear *= 1.8
            elif track_wetness < 0.70:
                slice_wear *= 1.3
        elif self.compound.wet_suitability < 0.2:
            if track_wetness > 0.20:
                slice_wear *= 1.25

        self.wear_pct = min(100.0, self.wear_pct + slice_wear)
        if self.wear_pct >= 99.0 and not self.is_punctured:
            self.is_punctured = True

    def apply_wear(self, dt: float, pace_multiplier: float = 1.0, aggressive_driving: float = 1.0):
        self.wear_pct = min(
            100.0, self.wear_pct + (self.compound.deg_per_lap / 30.0) * dt * pace_multiplier * aggressive_driving
        )
