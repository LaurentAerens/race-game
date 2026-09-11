from dataclasses import dataclass
from typing import Tuple, Optional

@dataclass
class Driver:
    id: int
    name: str
    code: str                  # E.g. "VER", "HAM", "LEC"
    number: int
    team_name: str
    color_rgb: Tuple[int, int, int]
    is_player: bool = False
    
    # Skills [0.0 - 1.0]
    speed: float = 0.85
    braking: float = 0.85      # Late-braking & divebomb skill
    cornering: float = 0.85    # Apex precision & minimum rolling apex speed
    overtaking: float = 0.80   # Aggressive opportunistic passes & dummy moves
    defending: float = 0.80    # Inside corridor protection & dirty air management
    tire_management: float = 0.80 # Thermal preservation & gentle sliding
    wet_skill: float = 0.80    # Wet line precision away from rubbered line
    consistency: float = 0.85  # Lap-to-lap rhythm & mistake avoidance under pressure
    aggression: float = 0.70   # Willingness to force moves and defend aggressively
    driving_style: str = "BALANCED" # LATE_BRAKER, SMOOTH_ROLLER, AGGRESSIVE_HUNTER, TIRE_WHISPERER, BALANCED
    is_champion: bool = False  # Reigning Champion mood & composure

    def __post_init__(self):
        if not self.driving_style or self.driving_style == "BALANCED":
            self.driving_style = self.infer_driving_style()

    def infer_driving_style(self) -> str:
        """Determines driver archetype from their top characteristic stats."""
        # Check primary affinities
        if self.braking >= 0.88 and self.braking >= max(self.cornering, self.tire_management):
            return "LATE_BRAKER"
        if self.cornering >= 0.88 and self.cornering > self.braking:
            return "SMOOTH_ROLLER"
        if self.tire_management >= 0.88 and self.tire_management > self.speed:
            return "TIRE_WHISPERER"
        if self.overtaking >= 0.86 and (self.aggression >= 0.72 or self.overtaking > self.consistency):
            return "AGGRESSIVE_HUNTER"
        
        # Fallback comparison if not in elite bracket
        skills = {
            "LATE_BRAKER": self.braking * 1.05 + self.aggression * 0.2,
            "SMOOTH_ROLLER": self.cornering * 1.10,
            "TIRE_WHISPERER": self.tire_management * 1.12,
            "AGGRESSIVE_HUNTER": self.overtaking * 1.02 + self.aggression * 0.25
        }
        best_style, val = max(skills.items(), key=lambda x: x[1])
        return best_style if val >= 0.84 else "BALANCED"

    def get_skill_factor(self, track_wetness: float = 0.0) -> float:
        """Returns aggregate skill multiplier for lap performance."""
        dry_skill = (self.speed * 0.40 + self.cornering * 0.30 + self.braking * 0.15 + self.consistency * 0.15)
        if self.is_champion:
            dry_skill = min(0.99, dry_skill + 0.015)
        if track_wetness > 0.1:
            return dry_skill * (1.0 - track_wetness) + (self.wet_skill * track_wetness)
        return dry_skill

    def get_apex_speed_multiplier(self) -> float:
        """Rolling corner speed multiplier based on cornering skill and technique."""
        base = 0.94 + 0.12 * self.cornering
        if self.driving_style == "SMOOTH_ROLLER":
            base += 0.035  # Smooth momentum rollers carry higher mid-corner speed
        elif self.driving_style == "LATE_BRAKER":
            base -= 0.015  # V-shaped line trades minor mid-corner speed for deep braking
        return base

    def get_brake_depth_multiplier(self) -> float:
        """Modifier on required braking distance (smaller = brakes deeper)."""
        # Elite braking allows braking 8-15% later into corners
        factor = 1.08 - 0.16 * self.braking
        if self.driving_style == "LATE_BRAKER":
            factor *= 0.92  # Extra late dive-bomb threshold
        elif self.driving_style == "TIRE_WHISPERER":
            factor *= 1.04  # Gentle threshold avoids thermal spikes
        return factor

    def get_tire_preservation_multiplier(self) -> float:
        """Wear reduction factor (lower = tires last longer)."""
        factor = 1.25 - 0.35 * self.tire_management
        if self.driving_style == "TIRE_WHISPERER":
            factor *= 0.84  # 16% extra tire life
        elif self.driving_style == "AGGRESSIVE_HUNTER":
            factor *= 1.10  # Harder on rubber due to frequent sliding and attacking
        return max(0.65, factor)

    def get_mistake_risk(self, under_pressure: bool = False) -> float:
        """Calculates chance of a micro-mistake or lockup based on consistency and composure."""
        base_risk = 0.0025 * (1.15 - self.consistency)
        if under_pressure:
            pressure_susceptibility = 1.0 + 1.5 * (1.0 - self.consistency)
            if self.is_champion:
                pressure_susceptibility *= 0.65  # Champion poise reduces error susceptibility under pressure
            base_risk *= pressure_susceptibility
        return max(0.0002, base_risk)

