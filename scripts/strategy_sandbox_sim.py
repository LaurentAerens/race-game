"""
Strategy Sandbox & Outlier Analysis Engine
===========================================
Simulates 100 distinct player agents:
  - 10 Pure Base Archetypes (10%)
  - 90 Multi-Agent Combinations (90%) with up to 3 archetypes blended with random weights.

Tracks 5,000 multi-season careers (50 careers per agent, up to 10 seasons each):
  - Solvency, bankruptcies, causes of failure
  - Seasons to reach Tier 1
  - Early dominance & overpowered cheat strategies
  - Facility adoption rates & completely avoided "dead" facilities
  - Comprehensive statistical rankings & actionable telemetry
"""

import json
import os
import random
import statistics
import sys
import time
from typing import Any, Dict, List

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.data.balance_config import BALANCE_REGISTRY

# -----------------------------------------------------------------------------
# 1. ARCHETYPE DEFINITIONS
# -----------------------------------------------------------------------------
BASE_ARCHETYPES = [
    "BALANCED_PRUDENT",
    "RUSH_AGGRESSIVE",
    "PURE_AERO_TECH_TITAN",
    "COMMERCIAL_MARKETEER",
    "ACADEMY_PRODIGY_SCOUT",
    "PAY_DRIVER_HOARDER",
    "PIT_AND_TRACKSIDE_OPTIMIZER",
    "RECKLESS_SPENDER",
    "FACILITY_MINIMALIST_CHEAP_SPEC",
    "FACILITY_RUSH_EXPLOIT",
]

# Key facility nodes across categories
FACILITY_NODES = {
    # Engineering / Aero
    "eng_workshop": {"cost": 2_200_000, "upkeep": 75_000, "category": "ENGINEERING"},
    "eng_brakes": {"cost": 1_800_000, "upkeep": 55_000, "category": "ENGINEERING"},
    "eng_wings_front": {"cost": 2_200_000, "upkeep": 65_000, "category": "ENGINEERING"},
    "eng_wings_rear": {"cost": 7_500_000, "upkeep": 220_000, "category": "ENGINEERING"},
    "eng_suspension": {"cost": 8_500_000, "upkeep": 240_000, "category": "ENGINEERING"},
    "eng_tuning": {"cost": 9_500_000, "upkeep": 260_000, "category": "ENGINEERING"},
    "eng_cad_office": {"cost": 7_000_000, "upkeep": 200_000, "category": "ENGINEERING"},
    "eng_cfd": {"cost": 14_000_000, "upkeep": 420_000, "category": "ENGINEERING"},
    "eng_windtunnel": {"cost": 38_000_000, "upkeep": 950_000, "category": "ENGINEERING"},
    "eng_floor": {"cost": 8_000_000, "upkeep": 220_000, "category": "ENGINEERING"},
    "eng_ers": {"cost": 9_500_000, "upkeep": 260_000, "category": "POWERTRAIN"},
    "eng_dyno": {"cost": 24_000_000, "upkeep": 650_000, "category": "POWERTRAIN"},
    "eng_works_powertrain": {"cost": 85_000_000, "upkeep": 2_400_000, "category": "POWERTRAIN"},
    # Commercial
    "mkt_press": {"cost": 2_400_000, "upkeep": 70_000, "category": "COMMERCIAL"},
    "mkt_brand_design": {"cost": 8_500_000, "upkeep": 240_000, "category": "COMMERCIAL"},
    "mkt_digital": {"cost": 7_800_000, "upkeep": 220_000, "category": "COMMERCIAL"},
    "mkt_merch": {"cost": 11_500_000, "upkeep": 320_000, "category": "COMMERCIAL"},
    "mkt_hospitality": {"cost": 29_000_000, "upkeep": 780_000, "category": "COMMERCIAL"},
    # Driver & Academy
    "driver_sim": {"cost": 2_300_000, "upkeep": 72_000, "category": "DRIVER"},
    "driver_gym_conditioning": {"cost": 9_500_000, "upkeep": 275_000, "category": "DRIVER"},
    "driver_academy": {"cost": 16_000_000, "upkeep": 460_000, "category": "DRIVER"},
    "driver_karting_scholarship": {"cost": 19_000_000, "upkeep": 540_000, "category": "DRIVER"},
    "driver_f4_bootcamp": {"cost": 24_000_000, "upkeep": 680_000, "category": "DRIVER"},
    # Trackside & Pit
    "track_pitrig": {"cost": 2_200_000, "upkeep": 68_000, "category": "TRACKSIDE"},
    "track_telemetry": {"cost": 9_800_000, "upkeep": 280_000, "category": "TRACKSIDE"},
    "track_wheelguns": {"cost": 12_500_000, "upkeep": 360_000, "category": "TRACKSIDE"},
    "track_fast_repair": {"cost": 13_500_000, "upkeep": 390_000, "category": "TRACKSIDE"},
    # Testing & Manufacturing
    "test_qa_ndt": {"cost": 9_000_000, "upkeep": 260_000, "category": "TESTING"},
    "mfg_cnc_machining": {"cost": 11_500_000, "upkeep": 330_000, "category": "MANUFACTURING"},
    "mfg_cleanroom_autoclave": {"cost": 10_500_000, "upkeep": 300_000, "category": "MANUFACTURING"},
}


class AgentProfile:
    """Represents an agent with either a pure archetype or a blend of up to 3 archetypes."""

    def __init__(self, agent_id: int, name: str, weights: Dict[str, float]):
        self.agent_id = agent_id
        self.name = name
        self.weights = weights

    def sample_archetype(self) -> str:
        r = random.random()
        cumulative = 0.0
        for arch, w in self.weights.items():
            cumulative += w
            if r <= cumulative:
                return arch
        return list(self.weights.keys())[0]

    def describe(self) -> str:
        parts = [f"{int(round(w * 100))}% {arch.replace('_', ' ')}" for arch, w in self.weights.items()]
        return " / ".join(parts)


def generate_100_agents(seed: int = 42) -> List[AgentProfile]:
    """Generates 10 pure archetypes + 90 multi-agent combinations (up to 3 archetypes each)."""
    rng = random.Random(seed)
    agents: List[AgentProfile] = []

    # 1. 10 Pure Archetypes
    for idx, arch in enumerate(BASE_ARCHETYPES):
        agents.append(AgentProfile(agent_id=idx + 1, name=f"Agent_{idx + 1:03d} [PURE: {arch}]", weights={arch: 1.0}))

    # 2. 90 Multi-Agent Combinations
    for idx in range(10, 100):
        agent_num = idx + 1
        num_components = rng.choice([2, 2, 3, 3])  # 2 or 3 archetypes
        chosen = rng.sample(BASE_ARCHETYPES, num_components)

        if num_components == 2:
            primary_pct = rng.choice([0.80, 0.75, 0.70, 0.60, 0.50])
            secondary_pct = round(1.0 - primary_pct, 2)
            weights = {chosen[0]: primary_pct, chosen[1]: secondary_pct}
        else:
            raw = [rng.uniform(0.35, 0.70), rng.uniform(0.15, 0.35), rng.uniform(0.10, 0.25)]
            tot = sum(raw)
            w1 = round(raw[0] / tot, 2)
            w2 = round(raw[1] / tot, 2)
            w3 = round(1.0 - w1 - w2, 2)
            weights = {chosen[0]: w1, chosen[1]: w2, chosen[2]: w3}

        combo_str = "+".join([f"{int(round(w * 100))}%{a.split('_')[0]}" for a, w in weights.items()])
        agents.append(AgentProfile(agent_id=agent_num, name=f"Agent_{agent_num:03d} [{combo_str}]", weights=weights))

    return agents


# -----------------------------------------------------------------------------
# 2. SIMULATION ENGINE
# -----------------------------------------------------------------------------
def calculate_16_sponsor_revenue(tier: int, appeal_score: float, pos: int, is_escalated: bool = False) -> float:
    """Calculates seasonal revenue for 16-sponsor roster based on actual finish position."""
    # Calibrated tier multipliers:
    # Tier 1 (Super Formula): mult ~ 5.0 (Global constructor deals)
    # Tier 2 (Continental): mult ~ 1.25 (Regional sponsors)
    # Tier 3 (National Open): mult ~ 0.22 (Local/National grassroots sponsors)
    tier_mult = {1: 5.0, 2: 1.25, 3: 0.22}.get(tier, 0.22)
    if is_escalated:
        mult = ((1.25 / 0.22) * 0.85) if tier == 2 else ((5.0 / 1.25) * 0.85)
    else:
        mult = (0.70 + (appeal_score / 100.0) * 0.60) * tier_mult

    # 2 Title sponsors: 2-season amortized signing + 10 race retainers + target bonus (pos <= 4)
    title_sign = 2 * (1_200_000.0 * mult) / 2.0
    title_race = 2 * (320_000.0 * mult) * 10.0
    title_bonus = (2 * (200_000.0 * mult) * 10.0) if pos <= 4 else 0.0

    # 4 Middle sponsors:
    mid_sign = 4 * (400_000.0 * mult) / 2.0
    mid_race = 4 * (110_000.0 * mult) * 10.0
    mid_bonus = (4 * (65_000.0 * mult) * 10.0) if pos <= 7 else 0.0

    # 10 Minor sponsors:
    minor_sign = 10 * (80_000.0 * mult) / 2.0
    minor_race = 10 * (28_000.0 * mult) * 10.0

    return title_sign + title_race + title_bonus + mid_sign + mid_race + mid_bonus + minor_sign + minor_race


def simulate_single_career(agent: AgentProfile, max_seasons: int = 30) -> Dict[str, Any]:
    """Runs a single multi-season career (up to max_seasons) for an agent profile."""
    cash = 5_000_000.0  # Starting Tier 3 budget
    tier = 3
    car_perf = 68.0  # Tier 3 benchmark is 75.0 (genuine underdog start)
    driver_skill = 50.0  # Tier 3 benchmark is 55.0
    driver_cons = 74.0
    facilities_owned = {"eng_workshop": 1}  # Starter
    seasons_in_tier = {3: 0, 2: 0, 1: 0}
    history = []
    is_bankrupt = False
    bankruptcy_reason = None
    reached_t1_at_season = None
    just_promoted = False

    has_pay_driver = False
    has_prodigy = False
    academy_driver_tenure = 0

    for season in range(1, max_seasons + 1):
        seasons_in_tier[tier] += 1
        active_arch = agent.sample_archetype()

        # 0. Regulation Reset check (every 6 seasons)
        if season > 1 and season % 6 == 0:
            # Regulation reset hits car performance
            aero_protection = 0.0
            if "eng_windtunnel" in facilities_owned:
                aero_protection += 0.10
            if "eng_cfd" in facilities_owned:
                aero_protection += 0.08
            if "eng_cad_office" in facilities_owned:
                aero_protection += 0.05
            loss_pct = max(0.12, 0.32 - aero_protection)
            car_perf *= 1.0 - loss_pct

        # 1. Annual Facility Upkeep (strictly based on owned facilities)
        annual_facility_upkeep = sum(FACILITY_NODES[f]["upkeep"] for f in facilities_owned if f in FACILITY_NODES)

        bench_car = BALANCE_REGISTRY.tier_dominance[tier].benchmark_car_perf
        bench_driver = BALANCE_REGISTRY.tier_dominance[tier].benchmark_driver_skill

        # Synchronized prize pools from central balance registry
        prizes = BALANCE_REGISTRY.get_tier_prize_pool(tier)

        # 2. Driver & Staff Decisions (2 Drivers per team)
        academy_program_cost = 0.0

        if active_arch == "PAY_DRIVER_HOARDER":
            has_pay_driver = True
            has_prodigy = False
        elif active_arch == "ACADEMY_PRODIGY_SCOUT":
            has_prodigy = True
            has_pay_driver = False
        elif active_arch == "RECKLESS_SPENDER":
            has_pay_driver = False
            has_prodigy = False
            driver_skill = min(98.0, driver_skill + 5.0)

        pay_driver_income = 0.0
        if has_pay_driver:
            # Pay driver brings cash, but driver skill is severely capped and consistency is poor
            pay_driver_income = {1: 7_000_000.0, 2: 3_500_000.0, 3: 1_200_000.0}[tier]
            driver_salary = {1: 1_200_000.0, 2: 500_000.0, 3: 200_000.0}[tier]
            driver_skill = min(74.0 if tier == 1 else (65.0 if tier == 2 else 52.0), driver_skill + 0.5)
            driver_cons = 64.0
        elif has_prodigy:
            academy_driver_tenure += 1
            # Academy scouting & youth training program annual cost
            # Scaled to represent funding 2 junior seats in feeder leagues (T4 & T5)
            academy_program_cost = {1: 4_500_000.0, 2: 2_200_000.0, 3: 850_000.0}[tier]

            # Prodigy starts raw: lower early consistency, early incident risk
            if academy_driver_tenure <= 2:
                driver_cons = 66.0
                driver_salary = {1: 3_500_000.0, 2: 800_000.0, 3: 250_000.0}[tier]
            else:
                driver_cons = 80.0
                # Once driver skill reaches elite level, market compensation is demanded
                if driver_skill >= 85.0:
                    driver_salary = 12_000_000.0 if tier == 1 else 4_500_000.0
                elif driver_skill >= 72.0:
                    driver_salary = 6_000_000.0 if tier == 1 else 2_200_000.0
                else:
                    driver_salary = {1: 3_000_000.0, 2: 950_000.0, 3: 350_000.0}[tier]

            driver_skill = min(95.0, driver_skill + random.uniform(2.5, 4.8))
        elif active_arch == "RECKLESS_SPENDER":
            # Demands superstar mercenary wages
            driver_salary = {1: 38_000_000.0, 2: 12_000_000.0, 3: 2_800_000.0}[tier]
            driver_cons = 72.0
        else:
            # Standard competitive driver lineup (2 drivers)
            driver_salary = {1: 18_000_000.0, 2: 4_500_000.0, 3: 750_000.0}[tier]
            driver_skill = min(92.0, driver_skill + random.uniform(2.0, 3.2))
            driver_cons = 78.0

        # Staff, Category Directors, Logistics & Team Overhead
        staff_overhead = {1: 22_000_000.0, 2: 5_500_000.0, 3: 1_200_000.0}[tier]

        # Engine Supplier Lease (Waived if Works Powertrain facility is owned)
        if "eng_works_powertrain" in facilities_owned:
            engine_lease = 0.0
        else:
            engine_lease = {1: 35_000_000.0, 2: 4_500_000.0, 3: 800_000.0}[tier]

        # 3. Facility Investment Decisions
        facility_spend = 0.0
        rush_penalty_durability = 0.0

        def try_buy_facility(node_id: str, reserve_mult: float = 1.30, is_rush: bool = False) -> bool:
            nonlocal cash, facility_spend, rush_penalty_durability
            if node_id not in facilities_owned and node_id in FACILITY_NODES:
                cost = FACILITY_NODES[node_id]["cost"]
                if is_rush:
                    # Rushed advanced facilities suffer a 20% setup/commissioning overrun
                    total_cost = cost * 1.20
                    if cash >= total_cost * reserve_mult:
                        cash -= total_cost
                        facility_spend += total_cost
                        facilities_owned[node_id] = 1
                        rush_penalty_durability += 18.0  # Teething trouble on rushed complex parts
                        return True
                else:
                    if cash >= cost * reserve_mult:
                        cash -= cost
                        facility_spend += cost
                        facilities_owned[node_id] = 1
                        return True
            return False

        if active_arch == "BALANCED_PRUDENT":
            if tier == 3:
                if not try_buy_facility("eng_brakes", 1.40):
                    if not try_buy_facility("eng_wings_front", 1.40):
                        if not try_buy_facility("driver_sim", 1.45):
                            try_buy_facility("mkt_press", 1.45)
            elif tier == 2:
                if not try_buy_facility("eng_wings_rear", 1.40):
                    if not try_buy_facility("eng_suspension", 1.40):
                        if not try_buy_facility("test_qa_ndt", 1.45):
                            try_buy_facility("mkt_brand_design", 1.40)
            elif tier == 1:
                if not try_buy_facility("eng_windtunnel", 1.45):
                    if not try_buy_facility("mkt_hospitality", 1.40):
                        try_buy_facility("eng_works_powertrain", 1.55)

        elif active_arch == "PURE_AERO_TECH_TITAN":
            for n in [
                "eng_brakes",
                "eng_wings_front",
                "eng_wings_rear",
                "eng_floor",
                "eng_cad_office",
                "eng_cfd",
                "eng_windtunnel",
            ]:
                try_buy_facility(n, 1.15)

        elif active_arch == "COMMERCIAL_MARKETEER":
            for n in ["mkt_press", "mkt_brand_design", "mkt_digital", "mkt_merch", "mkt_hospitality"]:
                try_buy_facility(n, 1.20)

        elif active_arch == "ACADEMY_PRODIGY_SCOUT":
            for n in [
                "driver_sim",
                "driver_gym_conditioning",
                "driver_academy",
                "driver_karting_scholarship",
                "driver_f4_bootcamp",
            ]:
                try_buy_facility(n, 1.25)

        elif active_arch == "PIT_AND_TRACKSIDE_OPTIMIZER":
            for n in ["track_pitrig", "track_telemetry", "track_wheelguns", "track_fast_repair", "test_qa_ndt"]:
                try_buy_facility(n, 1.20)

        elif active_arch == "FACILITY_RUSH_EXPLOIT":
            # Tries to rush high-tier facilities with almost no cash reserve (1.02x)
            if not try_buy_facility("eng_floor", 1.02, is_rush=True):
                if not try_buy_facility("eng_ers", 1.02, is_rush=True):
                    if tier <= 2:
                        try_buy_facility("eng_dyno", 1.02, is_rush=True)

        elif active_arch == "RECKLESS_SPENDER":
            # Buys without any cash buffer (1.0x reserve)
            cand = random.choice(list(FACILITY_NODES.keys()))
            try_buy_facility(cand, 1.0)

        # 4. R&D Spending and Performance Gains
        rnd_spend = 0.0
        durability = max(40.0, 94.0 - rush_penalty_durability)
        repair_bill = 0.0

        if active_arch == "RECKLESS_SPENDER":
            rnd_spend = {1: 55_000_000.0, 2: 14_000_000.0, 3: 3_500_000.0}[tier]
            car_perf += random.uniform(18.0, 30.0)
            durability = 48.0
            # Very high chance of catastrophic failure / crash
            if random.random() < 0.48:
                repair_bill = {1: 16_000_000.0, 2: 4_500_000.0, 3: 1_400_000.0}[tier]
        elif active_arch == "FACILITY_RUSH_EXPLOIT":
            # Facility rushers spend extra trying to integrate unproven complex parts
            rnd_spend = {1: 32_000_000.0, 2: 8_500_000.0, 3: 2_200_000.0}[tier]
            car_perf += random.uniform(10.0, 18.0)
            durability = max(45.0, durability - 12.0)
            if random.random() < 0.38:
                repair_bill = {1: 12_000_000.0, 2: 3_800_000.0, 3: 1_100_000.0}[tier]
        elif active_arch == "PURE_AERO_TECH_TITAN":
            rnd_spend = {1: 32_000_000.0, 2: 8_000_000.0, 3: 1_800_000.0}[tier]
            car_perf += random.uniform(14.0, 22.0)
            durability = 90.0
        elif active_arch == "FACILITY_MINIMALIST_CHEAP_SPEC":
            rnd_spend = {1: 4_500_000.0, 2: 1_200_000.0, 3: 250_000.0}[tier]
            car_perf += random.uniform(1.2, 3.2)
            durability = 86.0
        else:
            rnd_spend = {1: 24_000_000.0, 2: 5_500_000.0, 3: 1_200_000.0}[tier]
            car_perf += random.uniform(7.0, 14.0)
            durability = 85.0

        # Academy young prodigy incident risk in first 2 seasons
        if has_prodigy and academy_driver_tenure <= 2 and random.random() < 0.28:
            repair_bill += {1: 8_000_000.0, 2: 2_500_000.0, 3: 650_000.0}[tier]

        # 5. Race Performance Simulation
        w_driver, w_car = BALANCE_REGISTRY.get_tier_weights(tier)
        car_delta = car_perf - bench_car
        driver_delta = driver_skill - bench_driver
        dur_pen = max(0.0, (75.0 - durability) * 0.55)
        car_norm = ((car_delta - dur_pen) / max(1.0, bench_car)) * 48.0
        driver_norm = (driver_delta / 100.0) * 48.0

        form_swing = random.gauss(0.0, 2.0 if driver_cons >= 75 else 4.8)
        track_bonus = 0.0
        if "track_telemetry" in facilities_owned:
            track_bonus += 1.4
        if "track_wheelguns" in facilities_owned:
            track_bonus += 1.6
        if "track_fast_repair" in facilities_owned:
            track_bonus += 1.0

        score_delta = (w_driver * driver_norm) + (w_car * car_norm) + track_bonus + form_swing
        if repair_bill > 0:
            score_delta -= 6.0  # Incident/crash penalty in race standings

        if score_delta >= 4.2:
            pos = 1
        elif score_delta >= 2.4:
            pos = 2
        elif score_delta >= 0.5:
            pos = random.choice([3, 4])
        elif score_delta >= -2.0:
            pos = random.choice([5, 6, 7])
        else:
            pos = random.choice([8, 9, 10])

        prize_money = prizes[pos - 1] if pos <= len(prizes) else prizes[-1]

        # 6. Marketing Appeal & Sponsor Revenue (Calculated with actual finish position)
        base_appeal = BALANCE_REGISTRY.sponsor.tier_appeal_points[tier]
        if "mkt_press" in facilities_owned:
            base_appeal += 6.0
        if "mkt_brand_design" in facilities_owned:
            base_appeal += 10.0
        if "mkt_merch" in facilities_owned:
            base_appeal += 8.0
        if "mkt_hospitality" in facilities_owned:
            base_appeal += 14.0
        if pos <= 3:
            base_appeal += 10.0
        elif pos <= 5:
            base_appeal += 5.0
        elif pos >= 8:
            base_appeal -= 8.0

        sponsors = calculate_16_sponsor_revenue(tier, base_appeal, pos=pos, is_escalated=just_promoted)
        just_promoted = False

        # 7. Total Operational Accounting & Solvency Check
        fixed_operating_costs = (
            annual_facility_upkeep + staff_overhead + engine_lease + driver_salary + academy_program_cost
        )
        variable_costs = rnd_spend + repair_bill
        total_costs = fixed_operating_costs + variable_costs
        total_revenue = sponsors + pay_driver_income + prize_money

        cash += total_revenue - total_costs

        if cash < 0:
            is_bankrupt = True
            if repair_bill > 0 and (cash + repair_bill) >= 0:
                bankruptcy_reason = "REPAIR_CATASTROPHE"
            elif active_arch == "RECKLESS_SPENDER":
                bankruptcy_reason = "RECKLESS_OVERSPENDING"
            elif active_arch == "FACILITY_RUSH_EXPLOIT":
                bankruptcy_reason = "FACILITY_RUSH_OVEREXTENSION"
            elif annual_facility_upkeep > (sponsors * 0.70):
                bankruptcy_reason = "FACILITY_OVERHEAD_CRUSH"
            elif rnd_spend > {1: 45_000_000.0, 2: 12_000_000.0, 3: 2_800_000.0}[tier]:
                bankruptcy_reason = "RND_SPAM_INSOLVENCY"
            else:
                bankruptcy_reason = "OPERATIONAL_DEFICIT"
            break

        history.append(
            {
                "season": season,
                "tier": tier,
                "pos": pos,
                "cash_end": round(cash, 0),
                "car_perf": round(car_perf, 1),
                "driver_skill": round(driver_skill, 1),
                "facilities_count": len(facilities_owned),
            }
        )

        # 8. Promotion / Relegation Mechanics
        if tier == 3:
            if pos == 1:
                if active_arch == "BALANCED_PRUDENT" and seasons_in_tier[3] == 1 and cash < 10_000_000.0:
                    pass
                else:
                    tier = 2
                    just_promoted = True
                    car_perf = 96.0 + (12.0 if "eng_wings_rear" in facilities_owned else 0.0)

        elif tier == 2:
            if pos == 1:
                tier = 1
                if reached_t1_at_season is None:
                    reached_t1_at_season = season
                just_promoted = True
                car_perf = 125.0 + (15.0 if "eng_windtunnel" in facilities_owned else 0.0)
            elif pos >= 8 and len(facilities_owned) <= 3:
                # Relegation to Tier 3
                tier = 3
                cash -= 2_500_000.0  # Breach / demotion penalty
                car_perf = 74.0
                if cash < 0:
                    is_bankrupt = True
                    bankruptcy_reason = "RELEGATION_CRUSH"
                    break

        elif tier == 1:
            if pos >= 9 and len(facilities_owned) <= 5:
                # Relegation from Tier 1 back to Tier 2
                tier = 2
                cash -= 12_000_000.0  # Heavy T1 demotion penalty
                car_perf = 98.0
                if cash < 0:
                    is_bankrupt = True
                    bankruptcy_reason = "RELEGATION_CRUSH"
                    break

    return {
        "agent_id": agent.agent_id,
        "name": agent.name,
        "is_pure": len(agent.weights) == 1,
        "primary_archetype": max(agent.weights.items(), key=lambda x: x[1])[0],
        "reached_tier_1": reached_t1_at_season is not None,
        "seasons_to_tier_1": reached_t1_at_season,
        "is_bankrupt": is_bankrupt,
        "bankruptcy_reason": bankruptcy_reason,
        "bankruptcy_season": season if is_bankrupt else None,
        "final_cash": round(cash, 0),
        "final_tier": tier,
        "total_seasons_survived": len(history),
        "facilities_owned": list(facilities_owned.keys()),
        "history": history,
    }


# -----------------------------------------------------------------------------
# 3. STATISTICAL ANALYSIS & OUTLIER DETECTION
# -----------------------------------------------------------------------------
def analyze_sandbox_results(all_results: List[Dict[str, Any]], agents: List[AgentProfile]) -> Dict[str, Any]:
    """Computes comprehensive statistical meta-analysis across all 100 agents."""
    agent_map = {a.agent_id: a for a in agents}
    agent_stats: Dict[int, Dict[str, Any]] = {}

    for a in agents:
        agent_stats[a.agent_id] = {
            "agent_id": a.agent_id,
            "name": a.name,
            "description": a.describe(),
            "is_pure": len(a.weights) == 1,
            "total_runs": 0,
            "tier_1_count": 0,
            "bankruptcy_count": 0,
            "bankruptcy_reasons": {},
            "seasons_to_t1_list": [],
            "final_cash_list": [],
            "facilities_acquired": {},
        }

    total_runs = len(all_results)
    for r in all_results:
        aid = r["agent_id"]
        stat = agent_stats[aid]
        stat["total_runs"] += 1
        if r["reached_tier_1"]:
            stat["tier_1_count"] += 1
            stat["seasons_to_t1_list"].append(r["seasons_to_tier_1"])
        if r["is_bankrupt"]:
            stat["bankruptcy_count"] += 1
            reas = r["bankruptcy_reason"] or "UNKNOWN"
            stat["bankruptcy_reasons"][reas] = stat["bankruptcy_reasons"].get(reas, 0) + 1
        else:
            stat["final_cash_list"].append(r["final_cash"])

        for f in r["facilities_owned"]:
            stat["facilities_acquired"][f] = stat["facilities_acquired"].get(f, 0) + 1

    ranked_agents = []
    for aid, s in agent_stats.items():
        tot = max(1, s["total_runs"])
        t1_rate = round((s["tier_1_count"] / tot) * 100.0, 1)
        bk_rate = round((s["bankruptcy_count"] / tot) * 100.0, 1)
        avg_s = round(statistics.mean(s["seasons_to_t1_list"]), 1) if s["seasons_to_t1_list"] else None
        avg_c = round(statistics.mean(s["final_cash_list"]), 0) if s["final_cash_list"] else 0.0

        entry = {
            "agent_id": aid,
            "name": s["name"],
            "description": s["description"],
            "is_pure": s["is_pure"],
            "t1_rate": t1_rate,
            "bk_rate": bk_rate,
            "avg_seasons_to_t1": avg_s,
            "avg_final_cash": avg_c,
            "bankruptcy_reasons": s["bankruptcy_reasons"],
            "facilities_acquired": s["facilities_acquired"],
        }
        ranked_agents.append(entry)

    ranked_agents.sort(key=lambda x: (x["t1_rate"], -x["bk_rate"], -(x["avg_seasons_to_t1"] or 99)), reverse=True)

    outliers = {"early_dominance_overpowered": [], "hyper_fragile_high_bankruptcy": [], "mediocre_midfield_trapped": []}
    for a in ranked_agents:
        if a["t1_rate"] >= 80.0 and (a["avg_seasons_to_t1"] is not None and a["avg_seasons_to_t1"] <= 3.2):
            outliers["early_dominance_overpowered"].append(
                {
                    "agent_id": a["agent_id"],
                    "name": a["name"],
                    "description": a["description"],
                    "t1_rate": f"{a['t1_rate']}%",
                    "avg_seasons": a["avg_seasons_to_t1"],
                }
            )
        if a["bk_rate"] >= 40.0:
            outliers["hyper_fragile_high_bankruptcy"].append(
                {
                    "agent_id": a["agent_id"],
                    "name": a["name"],
                    "description": a["description"],
                    "bk_rate": f"{a['bk_rate']}%",
                    "primary_cause": max(a["bankruptcy_reasons"].items(), key=lambda x: x[1])[0]
                    if a["bankruptcy_reasons"]
                    else "None",
                }
            )
        if a["t1_rate"] == 0.0 and a["bk_rate"] == 0.0:
            outliers["mediocre_midfield_trapped"].append(
                {"agent_id": a["agent_id"], "name": a["name"], "description": a["description"]}
            )

    facility_totals = {f: 0 for f in FACILITY_NODES}
    facility_in_t1_runs = {f: 0 for f in FACILITY_NODES}
    t1_runs_total = sum(1 for r in all_results if r["reached_tier_1"])

    for r in all_results:
        for f in r["facilities_owned"]:
            if f in facility_totals:
                facility_totals[f] += 1
                if r["reached_tier_1"]:
                    facility_in_t1_runs[f] += 1

    facility_adoption_rates = []
    for f, count in facility_totals.items():
        overall_pct = round((count / total_runs) * 100.0, 1)
        t1_pct = round((facility_in_t1_runs[f] / max(1, t1_runs_total)) * 100.0, 1)
        facility_adoption_rates.append(
            {
                "facility_node": f,
                "category": FACILITY_NODES[f]["category"],
                "base_cost": FACILITY_NODES[f]["cost"],
                "overall_adoption_rate": f"{overall_pct}%",
                "t1_champions_adoption_rate": f"{t1_pct}%",
                "is_dead_facility": overall_pct == 0.0,
            }
        )

    facility_adoption_rates.sort(key=lambda x: float(x["overall_adoption_rate"].strip("%")), reverse=True)

    return {
        "total_careers_simulated": total_runs,
        "total_agents": len(agents),
        "top_10_champions": ranked_agents[:10],
        "bottom_10_strugglers": ranked_agents[-10:],
        "outlier_analysis": outliers,
        "facility_adoption_matrix": facility_adoption_rates,
        "full_ranked_agents": ranked_agents,
    }


# -----------------------------------------------------------------------------
# 4. CLI RUNNER WITH ASCII PROGRESS & TERMINAL SUMMARY
# -----------------------------------------------------------------------------
def print_pbar(current: int, total: int, prefix: str = "", length: int = 24):
    pct = (current / total) * 100.0
    filled = int(length * current // total)
    bar = "#" * filled + "." * (length - filled)
    sys.stdout.write(f"\r  [{bar}] {pct:5.1f}% | {prefix:<32}")
    sys.stdout.flush()
    if current == total:
        sys.stdout.write("\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Multi-Strategy 100-Agent Sandbox Simulation")
    parser.add_argument(
        "--careers-per-agent", type=int, default=50, help="Careers to simulate per agent (default 50 = 5,000 total)"
    )
    parser.add_argument("--max-seasons", type=int, default=30, help="Max seasons per career (default 30)")
    parser.add_argument("--output-json", type=str, default="sandbox_analysis_report.json", help="Destination JSON path")
    args = parser.parse_args()

    print("=" * 78)
    print(" 100-AGENT MULTI-STRATEGY SANDBOX SIMULATION & OUTLIER AUDIT")
    print(" Agents: 100 (10 Base Archetypes + 90 Multi-Agent Blends of up to 3 Archetypes)")
    print(f" Careers per Agent: {args.careers_per_agent} | Max Seasons: {args.max_seasons}")
    total_careers = 100 * args.careers_per_agent
    print(f" Total Careers to Simulate: {total_careers:,} (up to {total_careers * args.max_seasons:,} seasons)")
    print("=" * 78)

    t_start = time.time()
    agents = generate_100_agents(seed=42)
    all_career_results = []

    completed = 0
    for idx, ag in enumerate(agents, 1):
        for _ in range(args.careers_per_agent):
            res = simulate_single_career(ag, max_seasons=args.max_seasons)
            all_career_results.append(res)
            completed += 1
            if completed % 250 == 0 or completed == total_careers:
                print_pbar(completed, total_careers, prefix=f"{ag.name[:30]}")

        # Periodic check-in print every 10 agents
        if idx % 10 == 0 or idx == len(agents):
            agent_runs = [r for r in all_career_results if r["agent_id"] == ag.agent_id]
            t1_hits = sum(1 for r in agent_runs if r["reached_tier_1"])
            bks = sum(1 for r in agent_runs if r["is_bankrupt"])
            print(
                f"\n  [Agent {idx:03d}/100] {ag.name[:35]:<35} | T1 Reach: {t1_hits * 100 // len(agent_runs)}% | Bankruptcies: {bks * 100 // len(agent_runs)}%"
            )

    elapsed_sim = time.time() - t_start
    print(
        f"\n[+] Completed {total_careers:,} career simulations in {elapsed_sim:.2f}s ({total_careers / elapsed_sim:.0f} careers/sec)"
    )

    print("\nRunning statistical analysis & outlier detection...")
    meta_analysis = analyze_sandbox_results(all_career_results, agents)

    if os.path.dirname(args.output_json):
        os.makedirs(os.path.dirname(args.output_json), exist_ok=True)
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(meta_analysis, f, indent=2)
    print(f"[+] Saved full telemetry report to: {args.output_json}")

    # Display Terminal Highlights
    print("\n" + "=" * 78)
    print(" TOP 10 STRONGEST AGENTS (Promoted to Tier 1)")
    print("=" * 78)
    print(f"{'Rank':<4} | {'Agent Name':<32} | {'T1 Rate':<9} | {'Bankrupt':<9} | {'Avg Yrs':<8} | {'Avg Final Cash'}")
    print("-" * 78)
    for i, a in enumerate(meta_analysis["top_10_champions"], 1):
        s_yrs = f"{a['avg_seasons_to_t1']} yrs" if a["avg_seasons_to_t1"] else "N/A"
        print(
            f"#{i:<3} | {a['name'][:32]:<32} | {a['t1_rate']:>5.1f}%   | {a['bk_rate']:>5.1f}%   | {s_yrs:<8} | ${a['avg_final_cash']:,.0f}"
        )

    print("\n" + "=" * 78)
    print(" BOTTOM 10 STRUGGLING AGENTS (Stagnant or Bankrupt)")
    print("=" * 78)
    print(
        f"{'Rank':<4} | {'Agent Name':<32} | {'T1 Rate':<9} | {'Bankrupt':<9} | {'Avg Yrs':<8} | {'Primary Breakdown'}"
    )
    print("-" * 78)
    for i, a in enumerate(meta_analysis["bottom_10_strugglers"], 91):
        s_yrs = f"{a['avg_seasons_to_t1']} yrs" if a["avg_seasons_to_t1"] else "N/A"
        top_cause = (
            max(a["bankruptcy_reasons"].items(), key=lambda x: x[1])[0] if a["bankruptcy_reasons"] else "Midfield Trap"
        )
        print(
            f"#{i:<3} | {a['name'][:32]:<32} | {a['t1_rate']:>5.1f}%   | {a['bk_rate']:>5.1f}%   | {s_yrs:<8} | {top_cause}"
        )

    print("\n" + "=" * 78)
    print(" OUTLIER DETECTION & BALANCE CHECKS")
    print("=" * 78)
    outliers = meta_analysis["outlier_analysis"]
    print(
        f"  - Hyper-Fragile High-Bankruptcy Agents (Permissible Failure): {len(outliers['hyper_fragile_high_bankruptcy'])} detected"
    )
    for o in outliers["hyper_fragile_high_bankruptcy"][:3]:
        print(f"    * {o['name']} -> {o['bk_rate']} bankruptcies ({o['primary_cause']})")

    print(
        f"\n  - Overpowered Early Dominance (Cheat / Exploit Flags): {len(outliers['early_dominance_overpowered'])} detected"
    )
    if not outliers["early_dominance_overpowered"]:
        print("    * None detected! Progression cannot be trivially bypassed in <= 3 seasons.")
    else:
        for o in outliers["early_dominance_overpowered"]:
            print(f"    * [EXPLOIT FLAG] {o['name']}: {o['t1_rate']} T1 reached in avg {o['avg_seasons']} yrs!")

    print(f"\n  - Stagnant Midfield Trapped Agents: {len(outliers['mediocre_midfield_trapped'])} detected")
    for o in outliers["mediocre_midfield_trapped"][:3]:
        print(f"    * {o['name']} ({o['description']})")

    print("\n" + "=" * 78)
    print(" FACILITY ADOPTION HEATMAP (Top 8 Most & Least Built)")
    print("=" * 78)
    facs = meta_analysis["facility_adoption_matrix"]
    print(f"{'Facility Node':<26} | {'Category':<14} | {'Overall Build Rate':<20} | {'T1 Champions Rate'}")
    print("-" * 78)
    print("  [MOST ADOPTED FACILITIES]:")
    for f in facs[:5]:
        print(
            f"  {f['facility_node']:<24} | {f['category']:<14} | {f['overall_adoption_rate']:<20} | {f['t1_champions_adoption_rate']}"
        )
    print("  ...")
    print("  [LEAST ADOPTED / NICHE FACILITIES]:")
    for f in facs[-5:]:
        dead_flag = " [DEAD NODE]" if f["is_dead_facility"] else ""
        print(
            f"  {f['facility_node']:<24} | {f['category']:<14} | {f['overall_adoption_rate']:<20} | {f['t1_champions_adoption_rate']}{dead_flag}"
        )
    print("=" * 78)
    print(f" Sandbox analysis finished in {time.time() - t_start:.2f}s total.\n")


if __name__ == "__main__":
    main()
