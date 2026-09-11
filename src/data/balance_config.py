"""
Centralized Game Balance & AppSettings Registry.
Provides a single source of truth for all game mechanics:
- Micro Physics & Strategy (Tire degradation, pit stop deltas, speed/braking factors)
- Macro Economy (Tier prize pools, sponsor retainers, starting budgets, staff/driver payroll)
- Tier Strategy Weights (Driver skill vs. Car engineering dominance across Tiers 1-5)
- Equipment & Facility Scaling Formulas (Diminishing returns, cost multipliers)
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Tuple, Any

# =============================================================================
# 1. TIER STRATEGY DOMINANCE WEIGHTS
# =============================================================================
# Controls how much Driver Talent vs. Car Engineering influences race outcome.
# Tier 5 (Karting) & 4 (Junior): Spec-like machinery -> Driver Talent is dominant.
# Tier 3 (National): Balanced transition -> 50/50 parity.
# Tier 2 (Continental): Aerodynamic & mechanical focus -> Engineering advantage.
# Tier 1 (World Super Formula): Extreme constructor war -> Engineering dominates.
@dataclass
class TierDominanceWeight:
    tier: int
    tier_name: str
    driver_weight: float          # Share of performance determined by driver stats
    car_weight: float             # Share of performance determined by car attributes & R&D
    benchmark_driver_skill: float # Baseline driver skill for this tier
    benchmark_car_perf: float     # Baseline car performance rating for this tier

TIER_DOMINANCE: Dict[int, TierDominanceWeight] = {
    1: TierDominanceWeight(1, "World Super Formula", driver_weight=0.18, car_weight=0.82, benchmark_driver_skill=85.0, benchmark_car_perf=235.0),
    2: TierDominanceWeight(2, "Continental Championship", driver_weight=0.32, car_weight=0.68, benchmark_driver_skill=70.0, benchmark_car_perf=145.0),
    3: TierDominanceWeight(3, "National Open Cup", driver_weight=0.50, car_weight=0.50, benchmark_driver_skill=55.0, benchmark_car_perf=75.0),
    4: TierDominanceWeight(4, "Junior Talent Series", driver_weight=0.70, car_weight=0.30, benchmark_driver_skill=40.0, benchmark_car_perf=45.0),
    5: TierDominanceWeight(5, "Karting Masters Academy", driver_weight=0.82, car_weight=0.18, benchmark_driver_skill=28.0, benchmark_car_perf=25.0)
}

# =============================================================================
# 2. MACRO ECONOMY & PRIZE POOLS
# =============================================================================
@dataclass
class EconomySettings:
    # Constructor Prize Pools by Tier (10 positions each)
    # Calibrated so that backmarkers (P9-P10) in Tier 3 receive minimal/zero prize money,
    # requiring tight financial management to survive, while winners earn capital to reinvest.
    prize_pools: Dict[int, List[float]] = field(default_factory=lambda: {
        1: [140_000_000, 115_000_000, 95_000_000, 80_000_000, 68_000_000, 58_000_000, 50_000_000, 42_000_000, 36_000_000, 20_000_000],
        2: [48_000_000, 38_000_000, 30_000_000, 24_000_000, 18_000_000, 14_000_000, 10_000_000, 7_000_000, 4_500_000, 1_500_000],
        3: [4_500_000, 3_200_000, 2_400_000, 1_700_000, 1_200_000, 800_000, 500_000, 250_000, 100_000, 0],
        4: [1_200_000, 950_000, 780_000, 640_000, 520_000, 420_000, 340_000, 270_000, 220_000, 180_000],
        5: [350_000, 280_000, 220_000, 180_000, 140_000, 110_000, 85_000, 65_000, 50_000, 40_000]
    })

    # Starting Budgets by Tier
    starting_budgets: Dict[int, float] = field(default_factory=lambda: {
        1: 35_000_000.0,
        2: 12_000_000.0,
        3: 5_000_000.0,
        4: 1_200_000.0,
        5: 320_000.0
    })

    # Driver Salary scaling: salary_per_race = base_multiplier * (skill ** exponent)
    driver_salary_multiplier: float = 380.0
    driver_salary_skill_exponent: float = 1.15
    driver_salary_tier_scale: Dict[int, float] = field(default_factory=lambda: {
        1: 3.5,
        2: 2.0,
        3: 1.0,
        4: 0.35,
        5: 0.12
    })

    # Personnel / Staff Salary base rates
    staff_head_salary_mult: float = 180.0
    staff_specialist_salary_mult: float = 110.0
    staff_intern_salary: float = 1200.0

    # Facility & Equipment Monthly Upkeep fractions
    facility_upkeep_base: float = 12_000.0
    facility_tier_multiplier: float = 1.65
    equipment_upkeep_rate_of_cost: float = 0.025  # ~2.5% of equipment base cost per month

ECONOMY_CONFIG = EconomySettings()

# =============================================================================
# 3. SPONSOR SYSTEM CONFIG
# =============================================================================
@dataclass
class SponsorBalanceConfig:
    # Appeal baseline points by tier
    tier_appeal_points: Dict[int, float] = field(default_factory=lambda: {
        1: 35.0, 2: 18.0, 3: 4.0, 4: 2.0, 5: 1.0
    })
    # Tier cash payout multipliers applied to catalog base values
    tier_payout_multipliers: Dict[int, float] = field(default_factory=lambda: {
        1: 4.5, 2: 2.2, 3: 1.0, 4: 0.35, 5: 0.12
    })

SPONSOR_CONFIG = SponsorBalanceConfig()

# =============================================================================
# 4. TIRE MODEL & COMPOUND BALANCING
# =============================================================================
@dataclass
class CompoundConfig:
    name: str
    code: str
    tier: str
    color_rgb: Tuple[int, int, int]
    base_grip: float
    deg_per_lap: float
    cliff_wear_pct: float
    optimal_temp: float
    wet_suitability: float
    wet_capability: float = 0.10

TIRE_CONFIGS: Dict[str, CompoundConfig] = {
    "HYPERSOFT": CompoundConfig("Hypersoft", "HS", "C5", (255, 105, 180), base_grip=1.14, deg_per_lap=24.0, cliff_wear_pct=60.0, optimal_temp=105.0, wet_suitability=0.05, wet_capability=0.20),
    "SUPERSOFT": CompoundConfig("Supersoft", "SS", "C4", (225, 30, 80),   base_grip=1.10, deg_per_lap=18.0, cliff_wear_pct=64.0, optimal_temp=100.0, wet_suitability=0.05, wet_capability=0.18),
    "SOFT":      CompoundConfig("Soft",      "S",  "C3", (245, 50, 50),   base_grip=1.06, deg_per_lap=13.0, cliff_wear_pct=68.0, optimal_temp=98.0,  wet_suitability=0.05, wet_capability=0.16),
    "MEDIUM":    CompoundConfig("Medium",    "M",  "C2", (245, 205, 30),  base_grip=1.00, deg_per_lap=8.2,  cliff_wear_pct=72.0, optimal_temp=95.0,  wet_suitability=0.05, wet_capability=0.13),
    "HARD":      CompoundConfig("Hard",      "H",  "C1", (240, 240, 240), base_grip=0.93, deg_per_lap=5.5,  cliff_wear_pct=75.0, optimal_temp=90.0,  wet_suitability=0.05, wet_capability=0.10),
    "INTER":     CompoundConfig("Intermediate", "I", "WET", (40, 195, 70), base_grip=0.94, deg_per_lap=8.5, cliff_wear_pct=72.0, optimal_temp=85.0,  wet_suitability=0.65, wet_capability=0.80),
    "WET":       CompoundConfig("Full Wet",  "W",  "WET", (30, 130, 230), base_grip=0.93, deg_per_lap=9.0,  cliff_wear_pct=75.0, optimal_temp=80.0,  wet_suitability=1.00, wet_capability=1.00)
}

# Pit Strategy Timings
@dataclass
class PitStrategyConfig:
    pit_lane_delta_seconds: float = 14.5  # Base time lost driving pit lane speed limit vs track
    base_stop_seconds: float = 2.4        # Base stationary tire change time
    error_stop_seconds: float = 3.2       # Additional delay on pit blunder
    error_chance: float = 0.038           # 3.8% base chance of wheel nut/jack mistake

PIT_CONFIG = PitStrategyConfig()

# =============================================================================
# 5. EQUIPMENT & TECH TREE FORMULA SCALING
# =============================================================================
@dataclass
class EquipmentScalingFormula:
    """
    Computes equipment costs, upkeep, and bonuses using diminishing-return curves.
    Formula:
      Cost(level) = BaseCost * (1 + 0.35 * (level - 1))
      MonthlyUpkeep(level) = BaseUpkeep * (1 + 0.20 * (level - 1))
      PerformanceBonus(level) = BasePerf * (level ** 0.65)
      ReliabilityBonus(level) = BaseRel * (level ** 0.65)
    """
    cost_level_exponent: float = 0.38
    upkeep_level_exponent: float = 0.22
    bonus_diminishing_power: float = 0.68

    def calculate_cost(self, base_cost: float, target_level: int) -> float:
        if target_level <= 1:
            return float(base_cost)
        return float(round(base_cost * (1.0 + self.cost_level_exponent * (target_level - 1)), -3))

    def calculate_upkeep(self, base_upkeep: float, level: int) -> float:
        if level <= 1:
            return float(base_upkeep)
        return float(round(base_upkeep * (1.0 + self.upkeep_level_exponent * (level - 1)), -2))

    def calculate_bonus(self, base_bonus: float, level: int) -> float:
        return float(round(base_bonus * (level ** self.bonus_diminishing_power), 2))

EQUIPMENT_FORMULA = EquipmentScalingFormula()

# =============================================================================
# 6. PART MANUFACTURING & BUILD CADENCE
# =============================================================================
# Building parts must be cheap enough to do regularly (every 1-3 races),
# but expensive enough that you cannot build every single category every week.
# Tier 3: Custom R&D restricted to BRAKES and FRONT_WING only (spec supplier for the rest).
# Tier 2: Custom R&D unlocks REAR_WING, SUSPENSION, and ENGINE fine-tuning (5 parts).
# Tier 1: Full Constructor Freedom across all 7 components.
# Feeder Leagues (T4/T5): Strict Spec series (no custom R&D).
@dataclass
class PartBuildConfig:
    tier_category_costs: Dict[int, Dict[str, float]] = field(default_factory=lambda: {
        1: {
            "BRAKES": 1_200_000.0,
            "FRONT_WING": 1_500_000.0,
            "REAR_WING": 1_650_000.0,
            "SUSPENSION": 1_850_000.0,
            "FLOOR": 2_400_000.0,
            "ERS": 2_800_000.0,
            "ENGINE": 3_500_000.0
        },
        2: {
            "BRAKES": 280_000.0,
            "FRONT_WING": 360_000.0,
            "REAR_WING": 400_000.0,
            "SUSPENSION": 450_000.0,
            "ENGINE": 550_000.0
        },
        3: {
            "BRAKES": 85_000.0,
            "FRONT_WING": 120_000.0
        },
        4: {},
        5: {}
    })


PART_BUILD_CONFIG = PartBuildConfig()

# =============================================================================
# 7. PAY DRIVER & SPONSORED DRIVER BALANCING
# =============================================================================
# Pay drivers provide significant financial backing in Tiers 3 & 2,
# covering ~40-60% of part build costs and operational upkeep in exchange for skill deficit.
@dataclass
class PayDriverBalanceConfig:
    tier_sponsor_payout_base: Dict[int, float] = field(default_factory=lambda: {
        1: 1_800_000.0,
        2: 750_000.0,
        3: 280_000.0,
        4: 85_000.0,
        5: 30_000.0
    })

PAY_DRIVER_CONFIG = PayDriverBalanceConfig()

# =============================================================================
# 8. YOUNG DRIVER DEVELOPMENT & OVERPOWERED INVESTMENT SCALING
# =============================================================================
# Prodigies (potential >= 85, age <= 20) receive massive growth acceleration
# when academy and training facilities are upgraded.
@dataclass
class YoungDriverBalanceConfig:
    prodigy_potential_threshold: int = 85
    prodigy_max_age: int = 20
    prodigy_growth_multiplier: float = 1.45       # +45% base growth rate for prodigies
    facility_synergy_boost_rate: float = 0.12     # Additional growth boost per active driver training facility tier
    feeder_seat_cost_range: Dict[int, Tuple[float, float]] = field(default_factory=lambda: {
        5: (24_000.0, 95_000.0),      # Tier 5 Karting Masters: Pure talent development (~$24k - $95k/yr)
        4: (110_000.0, 480_000.0),    # Tier 4 Junior Talent Series: Single-seater feeder (~$110k - $480k/yr)
        3: (550_000.0, 3_200_000.0),  # Tier 3 National Open Cup (Pro-Am)
        2: (2_100_000.0, 11_500_000.0)# Tier 2 Continental Championship
    })

YOUNG_DRIVER_CONFIG = YoungDriverBalanceConfig()

# =============================================================================
# 9. APPSETTINGS REGISTRY & DB SYNCHRONIZATION
# =============================================================================
class BalanceSettingsRegistry:
    """Provides dynamic key-value lookup and database override capabilities."""
    def __init__(self):
        self.economy = ECONOMY_CONFIG
        self.tier_dominance = TIER_DOMINANCE
        self.sponsor = SPONSOR_CONFIG
        self.tire = TIRE_CONFIGS
        self.pit = PIT_CONFIG
        self.equipment = EQUIPMENT_FORMULA
        self.part_build = PART_BUILD_CONFIG
        self.pay_driver = PAY_DRIVER_CONFIG
        self.young_driver = YOUNG_DRIVER_CONFIG

    def get_tier_weights(self, tier: int) -> Tuple[float, float]:
        """Returns (driver_weight, car_weight) for the specified tier."""
        tw = self.tier_dominance.get(tier, self.tier_dominance[3])
        return tw.driver_weight, tw.car_weight

    def get_tier_prize_pool(self, tier: int) -> List[float]:
        return self.economy.prize_pools.get(tier, self.economy.prize_pools[3])

    def get_starting_budget(self, tier: int) -> float:
        return self.economy.starting_budgets.get(tier, 5_000_000.0)

    def get_part_build_cost(self, tier: int, category: str) -> float:
        """Returns the base build cost for a component category at a specific tier."""
        tier_costs = self.part_build.tier_category_costs.get(tier, self.part_build.tier_category_costs[3])
        return tier_costs.get(category.upper(), 150_000.0)

    def get_pay_driver_base_income(self, tier: int) -> float:
        """Returns the base per-race sponsor income brought by a pay driver."""
        return self.pay_driver.tier_sponsor_payout_base.get(tier, 280_000.0)

    def get_feeder_seat_cost_range(self, tier: int) -> Tuple[float, float]:
        """Returns the (min_cost, max_cost) annual seat fee range for junior drivers in this feeder tier."""
        return self.young_driver.feeder_seat_cost_range.get(tier, (24_000.0, 95_000.0))

    def to_dict(self) -> Dict[str, Any]:
        """Exports full settings tree to a JSON-serializable dictionary."""
        return {
            "tier_dominance": {k: asdict(v) for k, v in self.tier_dominance.items()},
            "economy": {
                "prize_pools": self.economy.prize_pools,
                "starting_budgets": self.economy.starting_budgets,
                "driver_salary_multiplier": self.economy.driver_salary_multiplier,
                "facility_upkeep_base": self.economy.facility_upkeep_base,
                "equipment_upkeep_rate_of_cost": self.economy.equipment_upkeep_rate_of_cost
            },
            "pit": asdict(self.pit),
            "sponsor": {
                "tier_appeal_points": self.sponsor.tier_appeal_points,
                "tier_payout_multipliers": self.sponsor.tier_payout_multipliers
            },
            "part_build": {
                "tier_category_costs": self.part_build.tier_category_costs
            },
            "pay_driver": {
                "tier_sponsor_payout_base": self.pay_driver.tier_sponsor_payout_base
            },
            "young_driver": asdict(self.young_driver)
        }

# Global Singleton Instance
BALANCE_REGISTRY = BalanceSettingsRegistry()
