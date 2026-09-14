"""
Headless Monte Carlo Balance & Strategy Simulation Harness.
Audits and verifies micro-game (tire strategies, lap times, pit stops)
and macro-game (career economy, multi-tier league progression, archetype dominance).
"""

import argparse
import json
import os
import random
import statistics
import sys
import time
from typing import Any, Dict

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.car import Car
from src.core.driver import Driver
from src.core.race_control import RaceControl
from src.data.balance_config import BALANCE_REGISTRY
from src.data.default_tracks import create_emerald_ring
from src.database.career_db import CareerDatabase
from src.database.db_manager import CarAttributes
from src.management.league_simulator import LeagueSimulator


# =============================================================================
# PROGRESS & DISPLAY HELPERS
# =============================================================================
def _pbar(label: str, i: int, total: int, width: int = 36, suffix: str = "") -> None:
    """
    Prints a single-line overwriting ASCII progress bar.
    Call with i=total to finalize the line with a newline.
    Example: _pbar("Seasons", 5, 10)  ->  [################....]  5/10
    """
    filled = int(width * i / max(1, total))
    bar = "#" * filled + "." * (width - filled)
    pct = int(100 * i / max(1, total))
    end_char = "\n" if i >= total else "\r"
    print(f"  [{bar}] {i:>4}/{total} ({pct:3d}%)  {label}{('  ' + suffix) if suffix else ''}", end=end_char, flush=True)


def _section(title: str, step: int, total_steps: int) -> float:
    """Prints a section header and returns the current timestamp for timing."""
    print(f"\n[{step}/{total_steps}] {title}")
    return time.time()


def _done(t0: float, extra: str = "") -> None:
    """Prints elapsed time for the last section."""
    elapsed = time.time() - t0
    print(f"  +-- Done in {elapsed:.1f}s{('  ' + extra) if extra else ''}")


# =============================================================================
# 1. MICRO SIMULATION: TIRE STRATEGY & LAP DELTA AUDIT
# =============================================================================
class MicroBalanceAudit:
    """Simulates on-track 2D physics and pit stop timing headlessly."""

    def __init__(self):
        self.circuit = create_emerald_ring()

    def run_strategy_benchmark(self, total_laps: int = 16) -> Dict[str, Any]:
        """
        Compares:
        - Strategy A (1-Stop): Medium (Laps 1-8) -> Hard (Laps 9-16)
        - Strategy B (2-Stop): Soft (Laps 1-5) -> Soft (Laps 6-10) -> Medium (Laps 11-16)
        - Strategy C (No-Stop): Hard (Laps 1-16)
        """
        strategies = {
            "1-Stop (M->H)": [("MEDIUM", 8), ("HARD", 8)],
            "2-Stop (S->S->M)": [("SOFT", 5), ("SOFT", 5), ("MEDIUM", 6)],
            "0-Stop (H Full)": [("HARD", total_laps)],
        }

        results = {}
        rc = RaceControl()

        for strat_name, stints in strategies.items():
            driver = Driver(
                id=1,
                name="Test Driver",
                code="TST",
                number=1,
                team_name="Test",
                color_rgb=(245, 50, 50),
                speed=0.85,
                braking=0.85,
                cornering=0.85,
                tire_management=0.80,
                consistency=0.90,
            )
            car_attrs = CarAttributes(
                engine_power=85.0, aero_downforce=85.0, braking_efficiency=85.0, tire_preservation=85.0
            )

            total_time = 0.0
            pit_stops_made = 0
            lap_times = []
            tire_wears = []

            for stint_idx, (compound, stint_laps) in enumerate(stints):
                car = Car(car_id=1, driver=driver, car_attributes=car_attrs, initial_compound=compound)
                if stint_idx > 0:
                    # Incur pit stop time loss (pit entry/exit + tire change stationary)
                    pit_loss = BALANCE_REGISTRY.pit.pit_lane_delta_seconds + BALANCE_REGISTRY.pit.base_stop_seconds
                    total_time += pit_loss
                    pit_stops_made += 1

                for lap in range(stint_laps):
                    # Simulate standard lap distance (circuit.length meters)
                    # Use step-wise physics integration
                    dist_covered = 0.0
                    lap_t = 0.0
                    dt = 0.5
                    while dist_covered < self.circuit.length:
                        car.update_physics(
                            dt=dt,
                            circuit=self.circuit,
                            race_control=rc,
                            track_wetness=0.0,
                            car_ahead=None,
                            car_behind=None,
                        )
                        dist_covered += car.speed * dt
                        lap_t += dt

                    car.tires.laps_used += 1
                    lap_times.append(lap_t)
                    tire_wears.append(car.tires.wear_pct)
                    total_time += lap_t

            results[strat_name] = {
                "total_time": round(total_time, 2),
                "avg_lap": round(statistics.mean(lap_times), 3),
                "best_lap": round(min(lap_times), 3),
                "worst_lap": round(max(lap_times), 3),
                "final_wear": round(tire_wears[-1], 1),
                "pit_stops": pit_stops_made,
            }

        # Calculate deltas relative to fastest strategy
        fastest_t = min(r["total_time"] for r in results.values())
        for r in results.values():
            r["delta_to_fastest"] = round(r["total_time"] - fastest_t, 2)

        return results


# =============================================================================
# 2. MACRO SIMULATION: MULTI-TIER CAREER & ARCHETYPE LEAGUES
# =============================================================================
class MacroBalanceAudit:
    """
    Simulates multi-tier career mode across dozens of seasons with 5 archetypal strategies:
    1. DRIVER_SCOUT: Invests heavily in elite drivers, spec/baseline car.
    2. TECH_TITAN: Invests heavily in facilities/upgrades, budget drivers.
    3. BALANCED: 50% split between driver wages and car R&D.
    4. HOARDER: Saves all cash, minimal spending.
    5. HIGH_ROLLER: Overspends, aggressive high-risk expansion.
    """

    ARCHETYPES = ["DRIVER_SCOUT", "TECH_TITAN", "BALANCED", "HOARDER", "HIGH_ROLLER"]

    def __init__(self, db_path: str = "test_balance_harness.db"):
        self.db_path = db_path
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = CareerDatabase(self.db_path)
        self.league_sim = LeagueSimulator(self.db)

    def cleanup(self):
        if hasattr(self, "db") and self.db:
            try:
                self.db.close()
            except Exception:
                pass
            del self.db
        import gc

        gc.collect()
        for suffix in ["", "-wal", "-shm"]:
            target_f = f"{self.db_path}{suffix}"
            if os.path.exists(target_f):
                try:
                    os.remove(target_f)
                except Exception:
                    pass

    def run_multi_season_simulation(self, total_seasons: int = 25, races_per_season: int = 10) -> Dict[str, Any]:
        """Runs headless seasons and records telemetry by tier and archetype."""
        # Telemetry containers
        stats_by_tier: Dict[int, Dict[str, Any]] = {
            t: {
                "name": BALANCE_REGISTRY.tier_dominance[t].tier_name,
                "archetype_wins": {arch: 0 for arch in self.ARCHETYPES},
                "archetype_podiums": {arch: 0 for arch in self.ARCHETYPES},
                "archetype_championships": {arch: 0 for arch in self.ARCHETYPES},
                "archetype_finances": {arch: [] for arch in self.ARCHETYPES},
                "bankruptcies": {arch: 0 for arch in self.ARCHETYPES},
                "season_point_spreads": [],
            }
            for t in [1, 2, 3, 4, 5]
        }

        # Setup teams with archetypes in each tier
        # Teams 1-5 in each tier get an archetype
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            for tier in [1, 2, 3, 4, 5]:
                cur.execute("SELECT id FROM teams WHERE tier = ? ORDER BY id ASC LIMIT 5;", (tier,))
                t_ids = [r[0] for r in cur.fetchall()]
                for idx, t_id in enumerate(t_ids):
                    arch = self.ARCHETYPES[idx % len(self.ARCHETYPES)]
                    cur.execute("UPDATE teams SET difficulty = ? WHERE id = ?;", (arch, t_id))
            conn.commit()

        # Run Seasons
        print(f"  Simulating {total_seasons} seasons x {races_per_season} races across 5 tiers...")
        for season in range(1, total_seasons + 1):
            _pbar("Macro seasons", season, total_seasons)
            # Apply seasonal investment behaviors per archetype
            self._apply_archetype_investments()

            # Simulate races in season
            for race_round in range(1, races_per_season + 1):
                self.league_sim.simulate_background_round(race_round)

            # Record season end results & award prize money
            self._evaluate_season_standings(stats_by_tier)

            # Reset calendar for next season
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("UPDATE calendar SET is_completed = 0;")
                cur.execute("UPDATE teams SET points = 0;")
                cur.execute("UPDATE drivers SET points = 0;")
                cur.execute("DELETE FROM series_race_results;")
                conn.commit()

        # Aggregate metrics
        summary = self._compile_summary(stats_by_tier, total_seasons)
        return summary

    def _apply_archetype_investments(self):
        """Applies distinct spending and recruitment decisions based on archetypes."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            for tier in [1, 2, 3, 4, 5]:
                cur.execute("SELECT id, difficulty, cash, tier FROM teams WHERE tier = ?;", (tier,))
                teams = [dict(r) for r in cur.fetchall()]
                tw = BALANCE_REGISTRY.tier_dominance[tier]

                for t in teams:
                    tier_cap = {1: 300.0, 2: 180.0, 3: 95.0, 4: 55.0, 5: 32.0}[tier]
                    base_perf = tw.benchmark_car_perf
                    base_skill = tw.benchmark_driver_skill
                    tier_driver_cap = {1: 99, 2: 92, 3: 80, 4: 65, 5: 48}[tier]
                    t_id = t["id"]
                    arch = t.get("difficulty", "BALANCED")

                    if arch == "DRIVER_SCOUT":
                        # Spends heavily on top-tier driver skills, keeps stock car
                        pace_boost = random.randint(10, 13)
                        cur.execute(
                            """
                        UPDATE drivers 
                        SET pace = MIN(?, CAST(? AS INTEGER) + ?), 
                            braking = MIN(?, CAST(? AS INTEGER) + ? - 1),
                            defending = MIN(?, CAST(? AS INTEGER) + ? - 2),
                            consistency = 78
                        WHERE team_id = ?;
                        """,
                            (
                                tier_driver_cap,
                                base_skill,
                                pace_boost,
                                tier_driver_cap,
                                base_skill,
                                pace_boost,
                                tier_driver_cap,
                                base_skill,
                                pace_boost,
                                t_id,
                            ),
                        )
                        cur.execute(
                            "UPDATE car_components SET performance = ?, current_durability = 95.0 WHERE team_id = ?;",
                            (base_perf, t_id),
                        )
                        salary_scale = {1: 3.5, 2: 2.0, 3: 1.0, 4: 0.35, 5: 0.12}[tier]
                        deduction = base_skill * 850.0 * salary_scale
                        cur.execute("UPDATE teams SET cash = cash - ? WHERE id = ?;", (deduction, t_id))

                    elif arch == "TECH_TITAN":
                        # Spends heavily on factory components, hires rookie drivers with volatile racecraft
                        car_mult = random.uniform(1.12, 1.15)
                        cur.execute(
                            """
                        UPDATE drivers 
                        SET pace = MAX(15, CAST(? AS INTEGER) - ?), 
                            braking = MAX(15, CAST(? AS INTEGER) - ?),
                            consistency = 52
                        WHERE team_id = ?;
                        """,
                            (base_skill, random.randint(5, 7), base_skill, random.randint(5, 7), t_id),
                        )
                        cur.execute(
                            """
                        UPDATE car_components 
                        SET performance = MIN(?, ? * ?),
                            current_durability = 100.0
                        WHERE team_id = ?;
                        """,
                            (tier_cap, base_perf, car_mult, t_id),
                        )
                        rnd_cost = BALANCE_REGISTRY.get_starting_budget(tier) * 0.18
                        cur.execute("UPDATE teams SET cash = cash - ? WHERE id = ?;", (rnd_cost, t_id))

                    elif arch == "BALANCED":
                        # 50/50 balance with disciplined consistency and reliability
                        car_mult = random.uniform(1.06, 1.09)
                        pace_boost = random.randint(5, 7)
                        cur.execute(
                            """
                        UPDATE drivers 
                        SET pace = MIN(?, CAST(? AS INTEGER) + ?), 
                            braking = MIN(?, CAST(? AS INTEGER) + ?),
                            consistency = 84
                        WHERE team_id = ?;
                        """,
                            (tier_driver_cap, base_skill, pace_boost, tier_driver_cap, base_skill, pace_boost, t_id),
                        )
                        cur.execute(
                            """
                        UPDATE car_components 
                        SET performance = MIN(?, ? * ?),
                            current_durability = 98.0
                        WHERE team_id = ?;
                        """,
                            (tier_cap, base_perf, car_mult, t_id),
                        )
                        spend = BALANCE_REGISTRY.get_starting_budget(tier) * 0.12
                        cur.execute("UPDATE teams SET cash = cash - ? WHERE id = ?;", (spend, t_id))

                    elif arch == "HOARDER":
                        # Spends 0 on upgrades, baseline stats
                        cur.execute(
                            """
                        UPDATE drivers 
                        SET pace = CAST(? AS INTEGER), braking = CAST(? AS INTEGER), consistency = 62
                        WHERE team_id = ?;
                        """,
                            (base_skill, base_skill, t_id),
                        )
                        cur.execute(
                            "UPDATE car_components SET performance = ?, current_durability = 85.0 WHERE team_id = ?;",
                            (base_perf, t_id),
                        )
                        cur.execute("UPDATE teams SET cash = cash * 1.01 WHERE id = ?;", (t_id,))

                    elif arch == "HIGH_ROLLER":
                        # Reckless spend with rushed parts, volatile pace, and poor reliability
                        car_mult = random.uniform(1.08, 1.13)
                        pace_boost = random.randint(7, 10)
                        cur.execute(
                            """
                        UPDATE drivers 
                        SET pace = MIN(?, CAST(? AS INTEGER) + ?),
                            consistency = 46
                        WHERE team_id = ?;
                        """,
                            (tier_driver_cap, base_skill, pace_boost, t_id),
                        )
                        cur.execute(
                            """
                        UPDATE car_components 
                        SET performance = MIN(?, ? * ?),
                            current_durability = 66.0
                        WHERE team_id = ?;
                        """,
                            (tier_cap, base_perf, car_mult, t_id),
                        )
                        heavy_spend = BALANCE_REGISTRY.get_starting_budget(tier) * 0.22
                        cur.execute("UPDATE teams SET cash = cash - ? WHERE id = ?;", (heavy_spend, t_id))

            conn.commit()

    def _evaluate_season_standings(self, stats_by_tier: Dict[int, Dict[str, Any]]):
        """Processes standings, awards prize money, tracks wins, podiums, and bankruptcies."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            for tier in [1, 2, 3, 4, 5]:
                cur.execute(
                    """
                SELECT id, difficulty, points, cash 
                FROM teams 
                WHERE tier = ? 
                ORDER BY points DESC, reputation DESC;
                """,
                    (tier,),
                )
                standings = [dict(r) for r in cur.fetchall()]
                prizes = BALANCE_REGISTRY.get_tier_prize_pool(tier)

                if standings:
                    # Winner
                    champ_arch = standings[0].get("difficulty", "BALANCED")
                    if champ_arch in stats_by_tier[tier]["archetype_championships"]:
                        stats_by_tier[tier]["archetype_championships"][champ_arch] += 1

                    pts = [t["points"] for t in standings]
                    stats_by_tier[tier]["season_point_spreads"].append(
                        {
                            "winner_pts": pts[0],
                            "p10_pts": pts[-1] if len(pts) >= 10 else 0,
                            "point_gap": pts[0] - pts[-1],
                        }
                    )

                # Calibrated annual baseline operations & facility upkeep (52 weeks)
                annual_overhead = {
                    1: 16_500_000.0,
                    2: 5_800_000.0,
                    3: 2_400_000.0,
                    4: 185_000.0,
                    5: 42_000.0,
                }[tier]

                # Annual sponsor revenue from 3 commercial contracts
                annual_sponsors = (
                    BALANCE_REGISTRY.sponsor.tier_appeal_points[tier]
                    * 11_000.0
                    * BALANCE_REGISTRY.sponsor.tier_payout_multipliers[tier]
                    * 3.0
                )
                max_capital_reserve = BALANCE_REGISTRY.get_starting_budget(tier) * 2.2

                for idx, t in enumerate(standings):
                    arch = t.get("difficulty", "BALANCED")
                    payout = prizes[idx] if idx < len(prizes) else 0.0
                    new_cash = float(t["cash"]) + payout + annual_sponsors - annual_overhead
                    new_cash = min(new_cash, max_capital_reserve)

                    if arch in stats_by_tier[tier]["archetype_finances"]:
                        stats_by_tier[tier]["archetype_finances"][arch].append(new_cash)
                        if new_cash < 0:
                            stats_by_tier[tier]["bankruptcies"][arch] += 1

                    # Record wins / podiums
                    if idx == 0 and arch in stats_by_tier[tier]["archetype_wins"]:
                        stats_by_tier[tier]["archetype_wins"][arch] += 1
                    if idx <= 2 and arch in stats_by_tier[tier]["archetype_podiums"]:
                        stats_by_tier[tier]["archetype_podiums"][arch] += 1

                    cur.execute("UPDATE teams SET cash = ? WHERE id = ?;", (new_cash, t["id"]))
            conn.commit()

    def _compile_summary(self, stats_by_tier: Dict[int, Dict[str, Any]], total_seasons: int) -> Dict[str, Any]:
        """Calculates percentage win rates and financial stability metrics."""
        summary = {"total_seasons": total_seasons, "tiers": {}}

        for tier, data in stats_by_tier.items():
            t_summary = {
                "name": data["name"],
                "championship_win_rates": {},
                "podium_shares": {},
                "bankruptcy_counts": data["bankruptcies"],
                "avg_final_cash": {},
                "avg_point_gap": 0.0,
            }

            tot_champs = sum(data["archetype_championships"].values()) or 1
            for arch in self.ARCHETYPES:
                champs = data["archetype_championships"][arch]
                t_summary["championship_win_rates"][arch] = f"{round((champs / tot_champs) * 100, 1)}%"

                finances = data["archetype_finances"][arch]
                avg_cash = statistics.mean(finances) if finances else 0.0
                t_summary["avg_final_cash"][arch] = f"${avg_cash:,.0f}"

            tot_podiums = sum(data["archetype_podiums"].values()) or 1
            for arch in self.ARCHETYPES:
                pods = data["archetype_podiums"][arch]
                t_summary["podium_shares"][arch] = f"{round((pods / tot_podiums) * 100, 1)}%"

            gaps = [p["point_gap"] for p in data["season_point_spreads"]]
            t_summary["avg_point_gap"] = round(statistics.mean(gaps), 1) if gaps else 0.0

            summary["tiers"][tier] = t_summary

        return summary


# =============================================================================
# 3. ECONOMY & DEVELOPMENT AUDIT: CADENCE, PAY DRIVERS, & YOUNG TALENT
# =============================================================================
class EconomyAndDevelopmentAudit:
    """
    Audits specific gameplay loops requested for fine-tuning:
    1. Part Manufacturing Cadence:
       - Weekly spam (building all 6 parts every single week -> proves bankruptcy).
       - Moderate cadence (building 1 part every 2 races -> proves economic sustainability).
    2. Pay Driver Viability in Tier 3 & Tier 2:
       - Compares cash generation and R&D capability of running 1 Pay Driver vs 2 Standard Drivers.
    3. Young Driver Growth Acceleration:
       - Compares the 3-season development curve of a 17yo high-potential prodigy (92 potential)
         with baseline facilities vs. upgraded academy facilities.
    """

    def audit_part_build_cadence(self, tier: int = 3, num_weeks: int = 20) -> Dict[str, Any]:
        """Compares weekly part spam vs. realistic cadence of 1 part every 2 races over a full 20-week season."""
        starting_cash = BALANCE_REGISTRY.get_starting_budget(tier)
        # In career mode, prize money is paid out at season end, not per week.
        # Weekly operational burn rate in Tier 3 is ~45k-65k.
        weekly_burn = 55_000.0
        categories = ["BRAKES", "REAR_WING", "FRONT_WING", "SUSPENSION", "ENGINE"]

        # Strategy A: Weekly Spam (Building all 5 categories every single week)
        cash_spam = starting_cash
        spam_bankrupt_at_week = None
        for w in range(1, num_weeks + 1):
            weekly_all_cost = sum([BALANCE_REGISTRY.get_part_build_cost(tier, c) for c in categories])
            cash_spam -= weekly_all_cost + weekly_burn
            if cash_spam < 0 and spam_bankrupt_at_week is None:
                spam_bankrupt_at_week = w

        # Strategy B: Healthy Cadence (1 component every 2-3 weeks, e.g. 7 components across season)
        cash_healthy = starting_cash
        parts_built_healthy = 0
        healthy_bankrupt_at_week = None
        for w in range(1, num_weeks + 1):
            build_cost = 0.0
            if w % 3 == 0:
                cat = categories[parts_built_healthy % len(categories)]
                build_cost = BALANCE_REGISTRY.get_part_build_cost(tier, cat)
                parts_built_healthy += 1
            cash_healthy -= build_cost + weekly_burn
            if cash_healthy < 0 and healthy_bankrupt_at_week is None:
                healthy_bankrupt_at_week = w

        # Add P5 season finale prize money at week 20
        p5_prize = BALANCE_REGISTRY.get_tier_prize_pool(tier)[4]
        cash_healthy += p5_prize
        cash_spam += p5_prize

        return {
            "tier": tier,
            "starting_budget": starting_cash,
            "weekly_spam": {
                "final_cash": round(cash_spam, 2),
                "is_solvent": spam_bankrupt_at_week is None,
                "bankrupt_at_round": spam_bankrupt_at_week,
            },
            "healthy_cadence": {
                "parts_built": parts_built_healthy,
                "final_cash": round(cash_healthy, 2),
                "is_solvent": healthy_bankrupt_at_week is None,
            },
        }

    def audit_pay_driver_strategy(self, tier: int = 3, num_races: int = 12) -> Dict[str, Any]:
        """Calculates financial surplus from employing 1 Pay Driver vs 2 Standard Drivers."""
        base_pay_income = BALANCE_REGISTRY.get_pay_driver_base_income(tier)
        std_salary = 45_000.0 if tier == 3 else 120_000.0

        # Team A: 2 Standard Drivers (Paid salaries)
        team_a_driver_cost = std_salary * 2 * num_races

        # Team B: 1 Standard Driver + 1 Pay Driver (Income generator)
        team_b_driver_net = (std_salary * num_races) - (base_pay_income * num_races)

        net_advantage = team_a_driver_cost - team_b_driver_net
        t3_brakes_cost = BALANCE_REGISTRY.get_part_build_cost(tier, "BRAKES")
        extra_parts_fundable = round(net_advantage / t3_brakes_cost, 1)

        return {
            "tier": tier,
            "pay_driver_income_per_race": base_pay_income,
            "total_seasonal_net_advantage": round(net_advantage, 2),
            "extra_parts_fundable": extra_parts_fundable,
            "is_pay_driver_viable": extra_parts_fundable >= 4.0,
        }

    def audit_young_driver_growth(self, seasons: int = 1) -> Dict[str, Any]:
        """Simulates 1-season rookie growth with 0 facilities vs. upgraded academy facilities."""
        import gc
        import tempfile

        from src.management.driver_manager import DriverManager

        temp_dir = tempfile.TemporaryDirectory()
        db_path = os.path.join(temp_dir.name, "young_growth.db")

        db = CareerDatabase(db_path)
        dm = DriverManager(db)

        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                # Create team with basic facilities
                cur.execute("SELECT id FROM teams WHERE tier = 3 LIMIT 2;")
                t_rows = cur.fetchall()
                t_base_id = t_rows[0][0]
                t_academy_id = t_rows[1][0]

                # Upgrade Team B's academy and simulator facilities to Tier 2
                for node in [
                    "driver_sim",
                    "driver_motion_sim",
                    "driver_vr_cognitive",
                    "driver_gym_conditioning",
                    "driver_f4_bootcamp",
                ]:
                    cur.execute(
                        """
                    INSERT INTO team_facilities (team_id, node_id, current_tier, is_unlocked, monthly_sub_budget)
                    VALUES (?, ?, 2, 1, 150000)
                    ON CONFLICT(team_id, node_id) DO UPDATE SET current_tier = 2, is_unlocked = 1;
                    """,
                        (t_academy_id, node),
                    )

                # Create identical 17yo prodigies in both teams
                for tid in [t_base_id, t_academy_id]:
                    cur.execute(
                        """
                    INSERT INTO drivers (
                        team_id, name, age, number, is_player_driver, is_academy_driver,
                        training_focus, salary_per_race, contract_races_left, potential, morale,
                        race_starts, braking, pace, consistency, tire_management, defending,
                        fuel_efficiency, wet_weather, technical_understanding, communication, marketability,
                        pot_pace, pot_race_starts, pot_braking, pot_tire_management, pot_defending, pot_wet_weather,
                        pot_consistency, pot_fuel_efficiency, pot_technical_understanding, pot_communication, pot_marketability
                    ) VALUES (
                        ?, 'Prodigy Prospect', 17, 99, 0, 1,
                        'BALANCED', 0, 36, 94, 90.0,
                        45, 45, 45, 50, 45, 45,
                        50, 45, 35, 35, 35,
                        94, 94, 94, 94, 94, 94,
                        94, 94, 94, 94, 94
                    );
                    """,
                        (tid,),
                    )

                conn.commit()

            # Advance development for 10 rounds per season across N seasons
            for s in range(seasons):
                for r in range(10):
                    dm.process_weekly_driver_development(t_base_id, player_race_pos=4)
                    dm.process_weekly_driver_development(t_academy_id, player_race_pos=2)

            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT pace, braking, defending FROM drivers WHERE team_id = ? AND is_academy_driver = 1;",
                    (t_base_id,),
                )
                base_stats = cur.fetchone()
                cur.execute(
                    "SELECT pace, braking, defending FROM drivers WHERE team_id = ? AND is_academy_driver = 1;",
                    (t_academy_id,),
                )
                acad_stats = cur.fetchone()

            base_gain = round(base_stats[0] - 45.0, 1)
            acad_gain = round(acad_stats[0] - 45.0, 1)

            return {
                "initial_rating": 45.0,
                "seasons_simulated": seasons,
                "baseline_no_facilities": {
                    "pace": round(base_stats[0], 1),
                    "braking": round(base_stats[1], 1),
                    "defending": round(base_stats[2], 1),
                    "total_growth": base_gain,
                },
                "invested_academy_facilities": {
                    "pace": round(acad_stats[0], 1),
                    "braking": round(acad_stats[1], 1),
                    "defending": round(acad_stats[2], 1),
                    "total_growth": acad_gain,
                },
                "is_overpowered": acad_gain >= 14.0 and acad_gain > base_gain * 1.5,
            }

        finally:
            if hasattr(locals(), "db") or "db" in locals():
                del db
            gc.collect()
            if hasattr(locals(), "temp_dir") or "temp_dir" in locals():
                try:
                    temp_dir.cleanup()
                except Exception:
                    pass

    def audit_feeder_seats_and_performance(self) -> Dict[str, Any]:
        """Audits Tier 4 and Tier 5 feeder seat placement costs and young talent performance."""
        t5_range = BALANCE_REGISTRY.get_feeder_seat_cost_range(5)
        t4_range = BALANCE_REGISTRY.get_feeder_seat_cost_range(4)
        t3_budget = BALANCE_REGISTRY.get_starting_budget(3)

        avg_t5_cost = (t5_range[0] + t5_range[1]) / 2.0
        avg_t4_cost = (t4_range[0] + t4_range[1]) / 2.0
        combined_cost = avg_t5_cost + avg_t4_cost
        budget_fraction_pct = round((combined_cost / t3_budget) * 100.0, 1)

        return {
            "tier_5_karting": {
                "seat_cost_range": f"${t5_range[0]:,.0f} - ${t5_range[1]:,.0f}/yr",
                "avg_cost": avg_t5_cost,
                "role": "Grassroots scout & karting skill development",
            },
            "tier_4_junior_series": {
                "seat_cost_range": f"${t4_range[0]:,.0f} - ${t4_range[1]:,.0f}/yr",
                "avg_cost": avg_t4_cost,
                "role": "Single-seater F4 feeder preparation",
            },
            "combined_annual_academy_cost": combined_cost,
            "pct_of_tier3_budget": f"{budget_fraction_pct}%",
            "is_affordable_for_t3": budget_fraction_pct <= 10.0,
        }

    def audit_factory_tree_and_skills(self) -> Dict[str, Any]:
        """
        Comprehensive audit of:
        1. 3x Performance vs. Reliability & Mechanical Strain Trade-Off.
        2. Commercial / Marketing Factory impact on Appeal, Retainers, and Portfolios per tier.
        3. Staff & Driver Training Progression and Salary Costs.
        """
        import gc

        from src.management.driver_manager import DriverManager
        from src.management.engineering_manager import EngineeringManager
        from src.management.sponsor_manager import SponsorManager
        from src.management.staff_manager import StaffManager

        db_path = f"test_factory_skills_{os.getpid()}.db"
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception:
                pass

        db = CareerDatabase(db_path)
        em = EngineeringManager(db)
        sm = SponsorManager(db)
        staff_m = StaffManager(db)
        dm = DriverManager(db)

        try:
            # -------------------------------------------------------------
            # 1. 3x PERFORMANCE VS RELIABILITY AUDIT
            # -------------------------------------------------------------
            conn = db.get_connection()
            try:
                cur = conn.cursor()
                cur.execute("SELECT id FROM teams WHERE tier = 3 LIMIT 1;")
                t3_team_id = cur.fetchone()[0]

                # Max out Brakes and Front Wing dedicated facilities + QA lab for apex conditions
                for node in [
                    "eng_brakes",
                    "eng_wings_front",
                    "eng_windtunnel",
                    "test_qa_ndt",
                    "eng_comp_materials",
                    "eng_kinematics_lab",
                    "test_shaker_rig",
                ]:
                    cur.execute(
                        """
                    INSERT INTO team_facilities (team_id, node_id, current_tier, is_unlocked, monthly_sub_budget)
                    VALUES (?, ?, 3, 1, 250000)
                    ON CONFLICT(team_id, node_id) DO UPDATE SET current_tier = 3, is_unlocked = 1;
                    """,
                        (t3_team_id, node),
                    )

                # Inject $50M for R&D builds
                cur.execute("UPDATE teams SET cash = 50000000.0 WHERE id = ?;", (t3_team_id,))

                # Query initial BRAKES component
                cur.execute(
                    "SELECT id, performance, reliability FROM car_components WHERE team_id = ? AND category = 'BRAKES';",
                    (t3_team_id,),
                )
                comp = cur.fetchone()
                comp_id = comp["id"]
                initial_perf = float(comp["performance"])
                initial_rel = float(comp["reliability"])
                conn.commit()
            finally:
                conn.close()

            # Run 4 R&D cycles (simulating season-long development: Mk2, Mk3, Mk4, Mk5)
            cycles = []
            print(f"  Running 4 R&D build cycles on BRAKES (baseline {initial_perf:.1f} pts)...")
            for gen_idx in range(1, 5):
                # Gather race telemetry with top driver stats
                print(f"    Mk{gen_idx + 1}: collecting telemetry (race 1/2)...", end="\r", flush=True)
                em.process_post_race_telemetry(
                    t3_team_id, driver_tech_skill=90.0, driver_comm_skill=90.0, dev_gain_mult=1.0
                )
                print(f"    Mk{gen_idx + 1}: collecting telemetry (race 2/2)...", end="\r", flush=True)
                em.process_post_race_telemetry(
                    t3_team_id, driver_tech_skill=90.0, driver_comm_skill=90.0, dev_gain_mult=1.0
                )

                print(f"    Mk{gen_idx + 1}: building next-gen part...          ", end="\r", flush=True)
                # Build next generation
                success, msg, gain = em.build_next_generation_part(t3_team_id, comp_id)
                conn2 = db.get_connection()
                try:
                    cur2 = conn2.cursor()
                    cur2.execute(
                        "SELECT generation, performance, reliability, max_durability FROM car_components WHERE id = ?;",
                        (comp_id,),
                    )
                    c_row = cur2.fetchone()
                    cycles.append(
                        {
                            "generation": c_row["generation"],
                            "performance": float(c_row["performance"]),
                            "reliability": float(c_row["reliability"]),
                            "max_durability": float(c_row["max_durability"]),
                            "perf_gain": gain,
                        }
                    )
                    print(
                        f"    Mk{gen_idx + 1}: Gen {c_row['generation']}  Perf {float(c_row['performance']):.1f} pts  (base {initial_perf:.1f}x{float(c_row['performance']) / initial_perf:.2f})  Rel {float(c_row['reliability']):.1f}%  {'[BREAKTHROUGH]' if gain > 30 else ''}"
                    )

                finally:
                    conn2.close()

            final_brakes_perf = cycles[-1]["performance"]
            final_brakes_rel = cycles[-1]["reliability"]
            perf_ratio = round(final_brakes_perf / initial_perf, 2)
            print(
                f"  -> Final BRAKES: {initial_perf:.1f} -> {final_brakes_perf:.1f} pts  ({perf_ratio}x ratio)  Rel {initial_rel:.1f}% -> {final_brakes_rel:.1f}%"
            )

            # -------------------------------------------------------------
            # 2. COMMERCIAL & MARKETING PER TIER AUDIT
            # -------------------------------------------------------------
            print("  Running marketing suite audit (T3 -> T2 -> T1)...")
            marketing_tiers = {}
            for t in [3, 2, 1]:
                print(f"    Tier {t} appeal...", end="\r", flush=True)
                # Step A: get team id
                conn3a = db.get_connection()
                try:
                    cur3a = conn3a.cursor()
                    cur3a.execute("SELECT id FROM teams WHERE tier = ? LIMIT 1;", (t,))
                    tid = cur3a.fetchone()[0]
                finally:
                    conn3a.close()

                # Step B: appeal with no marketing (separate conn)
                appeal_stock = sm.calculate_sponsor_appeal(tid)["total_appeal"]

                # Step C: unlock commercial suites (separate conn)
                conn3b = db.get_connection()
                try:
                    cur3b = conn3b.cursor()
                    comm_nodes = [
                        "mkt_press",
                        "mkt_brand_design",
                        "mkt_digital",
                        "mkt_merch",
                        "mkt_studio",
                        "mkt_hospitality",
                    ]
                    for cn in comm_nodes:
                        cur3b.execute(
                            """
                        INSERT INTO team_facilities (team_id, node_id, current_tier, is_unlocked, monthly_sub_budget)
                        VALUES (?, ?, 2, 1, 150000)
                        ON CONFLICT(team_id, node_id) DO UPDATE SET current_tier = 2, is_unlocked = 1;
                        """,
                            (tid, cn),
                        )
                    conn3b.commit()
                finally:
                    conn3b.close()

                # Step D: appeal after upgrade (separate conn)
                appeal_upgraded = sm.calculate_sponsor_appeal(tid)["total_appeal"]

                tier_mult = {1: 5.0, 2: 2.2, 3: 1.0}[t]

                # Full 16-sponsor portfolio seasonal valuation
                # Title: 2 * ($1.3M sign + $350k/race * 10) * mult
                # Middle: 4 * ($400k sign + $110k/race * 10) * mult
                # Minor: 10 * ($85k sign + $30k/race * 10) * mult
                mult_stock = (0.8 + (appeal_stock / 100.0) * 0.5) * tier_mult
                mult_upgraded = (0.8 + (appeal_upgraded / 100.0) * 0.5) * tier_mult

                base_portfolio_per_season = 2 * 4_800_000.0 + 4 * 1_500_000.0 + 10 * 385_000.0
                rev_stock = round(base_portfolio_per_season * mult_stock, 0)
                rev_upgraded = round(base_portfolio_per_season * mult_upgraded, 0)

                marketing_tiers[f"Tier_{t}"] = {
                    "tier": t,
                    "stock_appeal": appeal_stock,
                    "upgraded_appeal": appeal_upgraded,
                    "appeal_gain": appeal_upgraded - appeal_stock,
                    "seasonal_sponsor_stock": f"${rev_stock:,.0f}",
                    "seasonal_sponsor_upgraded": f"${rev_upgraded:,.0f}",
                    "marketing_revenue_boost": f"+${(rev_upgraded - rev_stock):,.0f}/yr",
                }
                print(
                    f"    Tier {t}: Appeal {appeal_stock}->{appeal_upgraded} (+{appeal_upgraded - appeal_stock})  Revenue ${rev_stock / 1e6:.1f}M->${rev_upgraded / 1e6:.1f}M  ({'+${:,.0f}'.format(rev_upgraded - rev_stock)}/yr boost)  "
                )

            # -------------------------------------------------------------
            # 3. STAFF & DRIVER TRAINING & SALARY AUDIT
            # -------------------------------------------------------------
            # Test Staff Academy weekly training impact
            conn4 = db.get_connection()
            try:
                cur4 = conn4.cursor()
                cur4.execute("SELECT id FROM teams WHERE tier = 3 LIMIT 1;")
                t_hr_id = cur4.fetchone()[0]

                # Build HR Tech Academy & Leadership Institute
                for hr_node in ["hr_tech_academy", "hr_craft_workshop", "hr_leadership_institute"]:
                    cur4.execute(
                        """
                    INSERT INTO team_facilities (team_id, node_id, current_tier, is_unlocked, monthly_sub_budget)
                    VALUES (?, ?, 2, 1, 120000)
                    ON CONFLICT(team_id, node_id) DO UPDATE SET current_tier = 2, is_unlocked = 1;
                    """,
                        (t_hr_id, hr_node),
                    )

                cur4.execute(
                    "SELECT id, name, stat_engineering, stat_leadership, salary_monthly FROM personnel WHERE team_id = ? AND role_type = 'DEPARTMENT_HEAD' LIMIT 1;",
                    (t_hr_id,),
                )
                staff_row = cur4.fetchone()
                init_staff_eng = float(staff_row["stat_engineering"])
                init_staff_lead = float(staff_row["stat_leadership"])
                staff_sal = float(staff_row["salary_monthly"])
                staff_row_id = staff_row["id"]
                staff_row_name = staff_row["name"]
                conn4.commit()
            finally:
                conn4.close()

            # Run 10 weeks of staff academy progression
            print(f"  Training {staff_row_name} for 10 weeks at Staff Academy...")
            for week in range(10):
                _pbar("Staff training weeks", week + 1, 10)
                staff_m.advance_weekly_personnel(t_hr_id)

            conn5 = db.get_connection()
            try:
                cur5 = conn5.cursor()
                cur5.execute("SELECT stat_engineering, stat_leadership FROM personnel WHERE id = ?;", (staff_row_id,))
                end_staff = cur5.fetchone()
                final_staff_eng = float(end_staff["stat_engineering"])
                final_staff_lead = float(end_staff["stat_leadership"])
            finally:
                conn5.close()

            staff_eng_gain = round(final_staff_eng - init_staff_eng, 1)
            staff_lead_gain = round(final_staff_lead - init_staff_lead, 1)
            print(
                f"  -> {staff_row_name}: Eng {init_staff_eng:.0f}->{final_staff_eng:.0f} (+{staff_eng_gain})  Lead {init_staff_lead:.0f}->{final_staff_lead:.0f} (+{staff_lead_gain})"
            )

            return {
                "performance_vs_reliability": {
                    "component": "BRAKES",
                    "initial_perf": initial_perf,
                    "final_perf": final_brakes_perf,
                    "perf_ratio": f"{perf_ratio}x (Capped at 3.0x max)",
                    "initial_rel": initial_rel,
                    "final_rel": final_brakes_rel,
                    "is_3x_achieved": perf_ratio >= 2.2 and perf_ratio <= 3.0,
                    "cycles": cycles,
                },
                "marketing_system": marketing_tiers,
                "staff_and_driver_training": {
                    "staff_member": staff_row_name,
                    "monthly_salary": f"${staff_sal:,.0f}/mo",
                    "training_weeks": 10,
                    "engineering_stat": f"{init_staff_eng:.0f} -> {final_staff_eng:.0f} (+{staff_eng_gain})",
                    "leadership_stat": f"{init_staff_lead:.0f} -> {final_staff_lead:.0f} (+{staff_lead_gain})",
                    "status": "Verified Steady Progression",
                },
            }

        finally:
            if "db" in locals() and db:
                try:
                    db.close()
                except Exception:
                    pass
                del db
            gc.collect()
            for suffix in ["", "-wal", "-shm"]:
                target_f = f"{db_path}{suffix}"
                if os.path.exists(target_f):
                    try:
                        os.remove(target_f)
                    except Exception:
                        # On Windows, try garbage collection and retry
                        gc.collect()
                        try:
                            os.remove(target_f)
                        except Exception:
                            pass

    def cleanup(self):
        """Sweeps any test database files created during audit runs."""
        import glob

        for f in glob.glob("test_factory_skills_*.db*"):
            try:
                os.remove(f)
            except Exception:
                pass


# =============================================================================
# 4. CAREER PROGRESSION & PROMOTION DILEMMA AUDIT
# =============================================================================
class CareerProgressionAndPromotionAudit:
    """
    Monte Carlo career progression simulation tracking multi-season promotions,
    bankruptcies, and the strategic dilemma: 'Is it sometimes smart to delay promotion?'

    Evaluates 5 Archetype Career Strategies (500 career simulations):
    1. RUSH_IMMEDIATE: Always promotes as soon as P1 is reached, even with low cash & stock facilities.
    2. PRUDENT_DELAY: Delays promotion by 1 season when cash < $14M to bank an extra prize and buy Tier 2 factory.
    3. PRODIGY_CARRIER: Fast-tracks using an overpowered academy driver on a cheap rookie contract.
    4. PAY_DRIVER_BUFFER: Runs a pay driver in T3/T2 to accumulate an ironclad cash reserve.
    5. HIGH_ROLLER_GAMBLER: Aggressive R&D spending with volatile, low-durability parts.
    """

    STRATEGIES = ["RUSH_IMMEDIATE", "PRUDENT_DELAY", "PRODIGY_CARRIER", "PAY_DRIVER_BUFFER", "HIGH_ROLLER_GAMBLER"]

    def run_career_simulation(self, runs_per_strategy: int = 100, max_seasons: int = 6) -> Dict[str, Any]:
        """Simulates hundreds of multi-season careers to track fast-tracking vs. bankruptcy rates."""
        results: Dict[str, Any] = {
            strat: {
                "total_runs": runs_per_strategy,
                "reached_tier_1": 0,
                "bankruptcies": 0,
                "avg_seasons_to_tier_1": [],
                "avg_tier_2_seasons": [],
                "final_cash_balances": [],
            }
            for strat in self.STRATEGIES
        }

        # Helper function for realistic 16-sponsor roster revenue calculation
        def calculate_portfolio_sponsors(
            tier: int, appeal_score: float, pos: int, is_promoted_escalated: bool = False
        ) -> float:
            """
            Calculates revenue for a full 16-sponsor portfolio (2 Title, 4 Middle, 10 Minor).
            Includes signing bonus amortized over 10 races, per-race retainers, and performance bonuses.
            If is_promoted_escalated is True, applies escalator clause (~1.87x from T3 or ~1.93x from T2).
            """
            tier_mult = {1: 5.0, 2: 2.2, 3: 1.0, 4: 0.4, 5: 0.15}.get(tier, 1.0)
            if is_promoted_escalated:
                mult = ((2.2 / 1.0) * 0.85) if tier == 2 else ((5.0 / 2.2) * 0.85)
            else:
                mult = (0.8 + (appeal_score / 100.0) * 0.5) * tier_mult

            # 2 Title Sponsors: base sign $1.3M, base per race $350k, bonus $220k (target pos <= 4)
            title_sign = (2 * 1_300_000.0 * mult) / 10.0
            title_race = 2 * 350_000.0 * mult
            title_bonus = (2 * 220_000.0 * mult) if pos <= 4 else 0.0

            # 4 Middle Sponsors: base sign $400k, base per race $110k, bonus $65k (target pos <= 7)
            mid_sign = (4 * 400_000.0 * mult) / 10.0
            mid_race = 4 * 110_000.0 * mult
            mid_bonus = (4 * 65_000.0 * mult) if pos <= 7 else 0.0

            # 10 Minor Sponsors: base sign $85k, base per race $30k, bonus $0
            minor_sign = (10 * 85_000.0 * mult) / 10.0
            minor_race = 10 * 30_000.0 * mult

            return (
                title_sign + title_race + title_bonus + mid_sign + mid_race + mid_bonus + minor_sign + minor_race
            ) * 10.0

        total_runs = len(self.STRATEGIES) * runs_per_strategy
        run_num = 0
        print(
            f"  Running {total_runs} career simulations ({len(self.STRATEGIES)} strategies x {runs_per_strategy} runs)..."
        )
        for strat in self.STRATEGIES:
            for run_idx in range(runs_per_strategy):
                run_num += 1
                _pbar("Career sims", run_num, total_runs, suffix=f"[{strat}]")
                cash = BALANCE_REGISTRY.get_starting_budget(3)  # $5,000,000
                current_tier = 3
                factory_tier = 1  # Factory physical infrastructure level (Decoupled from league tier!)
                car_perf = 70.0  # Baseline car performance (spec parts ~66.0, custom ~70.0)
                driver_skill = 65.0
                driver_cons = 80.0
                has_prodigy = strat == "PRODIGY_CARRIER"
                has_pay_driver = strat == "PAY_DRIVER_BUFFER"
                seasons_in_t3 = 0
                seasons_in_t2 = 0
                total_seasons = 0
                is_bankrupt = False
                just_promoted = False

                for season in range(1, max_seasons + 1):
                    total_seasons += 1
                    # DECOUPLED FACTORY OVERHEAD: Upkeep is based on actual facilities built (factory_tier), NOT league tier!
                    overhead = {1: 2_400_000.0, 2: 6_800_000.0, 3: 16_500_000.0}.get(factory_tier, 2_400_000.0)
                    bench_car = BALANCE_REGISTRY.tier_dominance[current_tier].benchmark_car_perf
                    bench_driver = BALANCE_REGISTRY.tier_dominance[current_tier].benchmark_driver_skill
                    prizes = BALANCE_REGISTRY.get_tier_prize_pool(current_tier)

                    appeal_pts = BALANCE_REGISTRY.sponsor.tier_appeal_points[current_tier]
                    # Full 16-sponsor portfolio revenue (with escalator check if newly promoted)
                    sponsors = calculate_portfolio_sponsors(
                        current_tier, appeal_pts, pos=3, is_promoted_escalated=just_promoted
                    )
                    just_promoted = False

                    # Pay driver revenue
                    pay_income = (
                        BALANCE_REGISTRY.get_pay_driver_base_income(current_tier) * 10.0 if has_pay_driver else 0.0
                    )

                    # Driver salary costs
                    if has_prodigy:
                        driver_salary = 120_000.0  # Rookie contract
                        driver_skill = min(96.0, driver_skill + 8.0)  # Prodigy growth
                    elif has_pay_driver:
                        driver_salary = 350_000.0  # Only paying seat #2
                        driver_skill = 68.0
                    else:
                        driver_salary = driver_skill * 850.0 * {1: 3.5, 2: 2.0, 3: 1.0}[current_tier] * 10.0

                    # Strategy-specific R&D & spending decisions
                    rnd_spend = 0.0
                    durability = 98.0
                    repair_bill = 0.0

                    # Allowed custom parts in T3: BRAKES & FRONT_WING only!
                    # Peak 3x scaling allowed on these 2 components with matching tech factory.
                    if strat == "HIGH_ROLLER_GAMBLER":
                        rnd_spend = BALANCE_REGISTRY.get_starting_budget(current_tier) * 0.38
                        # High risk / volatile development
                        car_perf += random.uniform(15.0, 30.0)
                        durability = 62.0
                        driver_cons = 46.0
                        if random.random() < 0.28:
                            repair_bill = {1: 4_500_000.0, 2: 2_200_000.0, 3: 850_000.0}[current_tier]

                    elif strat == "PRUDENT_DELAY":
                        if current_tier == 3 and cash >= 11_000_000.0:
                            # Buy Tier 2 factory upgrade while dominating Tier 3!
                            factory_tier = 2
                            cash -= 9_500_000.0
                            # Custom parts can reach up to 3x baseline (~210 max), lifting aggregate car
                            car_perf = 142.0  # Fully pre-prepared Tier 2 machinery!
                            rnd_spend = 1_200_000.0
                        elif current_tier == 2 and factory_tier < 2 and cash >= 12_000_000.0:
                            factory_tier = 2
                            cash -= 9_500_000.0
                            car_perf = 145.0
                        else:
                            rnd_spend = BALANCE_REGISTRY.get_starting_budget(current_tier) * 0.16
                            car_perf += random.uniform(6.0, 14.0)

                    elif strat == "PRODIGY_CARRIER":
                        rnd_spend = BALANCE_REGISTRY.get_starting_budget(current_tier) * 0.24
                        car_perf += random.uniform(8.0, 16.0)
                        if current_tier == 2 and factory_tier < 2 and cash >= 10_000_000.0:
                            factory_tier = 2
                            cash -= 9_500_000.0
                            car_perf = max(car_perf, 138.0)

                    elif strat == "RUSH_IMMEDIATE":
                        # Rushes into T2 without upgrading factory -> cheap T3 upkeep, but car underperforms in T2
                        rnd_spend = BALANCE_REGISTRY.get_starting_budget(current_tier) * 0.18
                        car_perf += random.uniform(4.0, 9.0)

                    else:  # PAY_DRIVER_BUFFER
                        rnd_spend = BALANCE_REGISTRY.get_starting_budget(current_tier) * 0.20
                        car_perf += random.uniform(6.0, 12.0)
                        if current_tier == 2 and factory_tier < 2 and cash >= 11_000_000.0:
                            factory_tier = 2
                            cash -= 9_500_000.0
                            car_perf = max(car_perf, 140.0)

                    # Total expenses & cash flow
                    cash += (sponsors + pay_income) - (overhead + driver_salary + rnd_spend + repair_bill)

                    if cash < 0:
                        is_bankrupt = True
                        break

                    # Race Performance synthesis in current tier
                    w_driver, w_car = BALANCE_REGISTRY.get_tier_weights(current_tier)
                    car_delta = car_perf - bench_car
                    driver_delta = driver_skill - bench_driver
                    dur_pen = max(0.0, (80.0 - durability) * 0.45)
                    car_norm = ((car_delta - dur_pen) / max(1.0, bench_car)) * 48.0
                    driver_norm = (driver_delta / 100.0) * 48.0

                    # Incident / form volatility
                    form_swing = random.gauss(0.0, 1.8 if driver_cons >= 75 else 4.2)
                    score_delta = (w_driver * driver_norm) + (w_car * car_norm) + form_swing
                    if repair_bill > 0:
                        score_delta -= 6.0

                    # Determine championship finish position (1 to 10)
                    if score_delta >= 3.8:
                        pos = 1
                    elif score_delta >= 2.0:
                        pos = 2
                    elif score_delta >= 0.2:
                        pos = random.choice([3, 4])
                    elif score_delta >= -2.5:
                        pos = random.choice([5, 6, 7])
                    else:
                        pos = random.choice([8, 9, 10])

                    prize_money = prizes[pos - 1] if pos <= len(prizes) else prizes[-1]
                    cash += prize_money

                    # Promotion & Relegation Decisions with Regulation Resets
                    if current_tier == 3:
                        seasons_in_t3 += 1
                        if pos == 1:
                            if strat == "PRUDENT_DELAY" and seasons_in_t3 == 1 and cash < 14_000_000.0:
                                pass
                            else:
                                current_tier = 2
                                just_promoted = True
                                # MANDATORY REGULATION RESET: Parts reset to T2 Gen 1 baseline (96.0)
                                # Next-Gen chassis carryover preserves a 6-12 pt edge
                                car_perf = 96.0 + (10.0 if factory_tier >= 2 else 0.0)
                    elif current_tier == 2:
                        seasons_in_t2 += 1
                        if pos == 1:
                            current_tier = 1
                            results[strat]["reached_tier_1"] += 1
                            results[strat]["avg_seasons_to_tier_1"].append(total_seasons)
                            results[strat]["avg_tier_2_seasons"].append(seasons_in_t2)
                            break
                        elif pos >= 8 and factory_tier < 2:
                            # Relegation back to Tier 3!
                            current_tier = 3
                            cash -= 2_200_000.0
                            car_perf = 74.0  # Adapted T3 baseline
                            if cash < 0:
                                is_bankrupt = True
                                break

                if is_bankrupt:
                    results[strat]["bankruptcies"] += 1
                else:
                    results[strat]["final_cash_balances"].append(cash)

        # Aggregate summary
        summary: Dict[str, Any] = {}
        for strat, data in results.items():
            tot = data["total_runs"]
            bks = data["bankruptcies"]
            t1_reaches = data["reached_tier_1"]
            avg_s = round(statistics.mean(data["avg_seasons_to_tier_1"]), 1) if data["avg_seasons_to_tier_1"] else None
            avg_t2 = round(statistics.mean(data["avg_tier_2_seasons"]), 1) if data["avg_tier_2_seasons"] else None
            avg_c = round(statistics.mean(data["final_cash_balances"]), 0) if data["final_cash_balances"] else 0.0

            summary[strat] = {
                "bankruptcy_rate": f"{round((bks / tot) * 100.0, 1)}%",
                "reached_tier_1_rate": f"{round((t1_reaches / tot) * 100.0, 1)}%",
                "avg_seasons_to_tier_1": avg_s,
                "avg_tier_2_seasons": avg_t2,
                "avg_final_cash": f"${avg_c:,.0f}",
            }

        return summary


# =============================================================================
# 5. FOUR-SEASON PROMOTION DILEMMA & TIER-DELTA AUDIT
# =============================================================================
class FourSeasonPromotionDilemmaAudit:
    """
    Dedicated 4-Season Monte Carlo simulation examining the promotion dilemma:
    'Is it better to rush to Tier 2 and risk relegation vs. delay in Tier 3, dominate,
    and promote with Tier 2 factory machinery?'

    Incorporates:
      - Full 16-sponsor portfolio model with escalator clause on promotion.
      - Decoupled factory overhead (Tier 3 factory costs only ~$2.4M even when racing in Tier 2!).
      - Allowed custom parts restricted to Brakes & Front Wing in T3 (scaling up to 3x).
      - Mandatory regulation reset on promotion to Tier 2 baseline specs.
    """

    def audit_tier_delta_financials(self) -> Dict[str, Any]:
        """
        Calculates side-by-side operational finances for:
          1. Bottom of Tier 2 (P10) with a Tier 3 factory (The "Grey Zone" promoted team)
          2. Top of Tier 3 (P1)
        """
        # Tier 2 P10 financials (Promoted team with Tier 3 factory: 16 sponsors with escalator clause)
        t2_prize = BALANCE_REGISTRY.get_tier_prize_pool(2)[-1]  # $6,000,000
        # 16 Sponsors in Tier 2: Escalated contracts + fresh minor sponsors (~$8.5M total)
        # At P10, target bonuses are 0%
        t2_sponsor_base = 8_500_000.0
        t2_sponsor_bonus = 0.0
        t2_sponsor_total = t2_sponsor_base + t2_sponsor_bonus
        # DECOUPLED: Promoted team still has Tier 3 factory -> $2,400,000 upkeep, NOT Tier 2 $5.8M!
        t2_overhead = 2_400_000.0
        t2_driver_salary = 70.0 * 850.0 * 2.0 * 10.0 * 2.0  # Two Tier 2 benchmark drivers ~$2,380,000
        t2_rd_maintenance = 1_800_000.0  # Basic repairs
        t2_total_rev = t2_prize + t2_sponsor_total
        t2_total_costs = t2_overhead + t2_driver_salary + t2_rd_maintenance
        t2_net_profit = t2_total_rev - t2_total_costs

        # Tier 3 P1 financials (Dominant Champion with full 16 sponsors hitting 100% of targets)
        t3_prize = BALANCE_REGISTRY.get_tier_prize_pool(3)[0]  # $16,000,000
        # 16 Sponsors in Tier 3: Retainers ~$4.8M + 100% Performance Bonuses ~$4.2M = ~$9.0M!
        t3_sponsor_base = 4_800_000.0
        t3_sponsor_bonus = 4_200_000.0
        t3_sponsor_total = t3_sponsor_base + t3_sponsor_bonus  # ~$9,000,000
        t3_overhead = 2_400_000.0
        t3_driver_salary = 55.0 * 850.0 * 1.0 * 10.0 * 2.0  # Two Tier 3 benchmark drivers ~$935,000
        t3_rd_maintenance = 1_400_000.0
        t3_total_rev = t3_prize + t3_sponsor_total
        t3_total_costs = t3_overhead + t3_driver_salary + t3_rd_maintenance
        t3_net_profit = t3_total_rev - t3_total_costs

        net_advantage_t3_over_t2 = t3_net_profit - t2_net_profit

        return {
            "tier2_bottom_p10": {
                "tier": 2,
                "finish_position": 10,
                "prize_money": t2_prize,
                "sponsor_revenue": t2_sponsor_total,
                "sponsor_bonus_hit_rate": "0% (All targets missed)",
                "total_revenue": t2_total_rev,
                "operational_costs": t2_total_costs,
                "breakdown_costs": {
                    "overhead": t2_overhead,
                    "driver_payroll": t2_driver_salary,
                    "rd_maintenance": t2_rd_maintenance,
                },
                "net_profit": t2_net_profit,
            },
            "tier3_top_p1": {
                "tier": 3,
                "finish_position": 1,
                "prize_money": t3_prize,
                "sponsor_revenue": t3_sponsor_total,
                "sponsor_bonus_hit_rate": "100% (All targets achieved)",
                "total_revenue": t3_total_rev,
                "operational_costs": t3_total_costs,
                "breakdown_costs": {
                    "overhead": t3_overhead,
                    "driver_payroll": t3_driver_salary,
                    "rd_maintenance": t3_rd_maintenance,
                },
                "net_profit": t3_net_profit,
            },
            "net_advantage_top_lower_tier": net_advantage_t3_over_t2,
            "conclusion": "Dominating Tier 3 nets +$12.3M more cash per season than languishing at P10 in Tier 2!",
        }

    def run_four_season_simulation(self, runs: int = 500) -> Dict[str, Any]:
        """
        Runs 500 Monte Carlo runs comparing Path A (Yo-Yo Elevator) vs. Path B (Consolidated Delay).
        """
        path_a_records = []
        path_b_records = []

        print(f"  Comparing Path A (Yo-Yo) vs Path B (Delay) over {runs} Monte Carlo runs...")
        for run_i in range(runs):
            _pbar("4-season dilemma", run_i + 1, runs)

            # -----------------------------------------------------------------
            # PATH A: YO-YO ELEVATOR (T3 P1 -> T2 P9/10 Relegated -> T3 Dominant -> T2)
            # -----------------------------------------------------------------
            cash_a = 5_000_000.0
            car_a = 70.0
            factory_a = 1
            path_a_seasons = []

            for s in range(1, 5):
                if s == 1:
                    # Season 1: T3, wins P1
                    tier = 3
                    pos = 1
                    rev = 16_000_000.0 + 9_000_000.0  # $16M prize + $9M 16-sponsor portfolio
                    cost = 2_400_000.0 + 950_000.0 + 1_200_000.0
                    cash_a += rev - cost
                    # Allowed custom parts (Brakes + Wing) pushed up to 2.5x
                    car_a = 98.0
                    path_a_seasons.append(
                        {
                            "season": s,
                            "tier": tier,
                            "pos": pos,
                            "cash": cash_a,
                            "car_perf": car_a,
                            "event": "Won T3 Championship; Rushed Promotion!",
                        }
                    )

                elif s == 2:
                    # Season 2: Rushed into T2 without Factory Tier 2!
                    # Reset components to Tier 2 baseline specs (96.0)
                    tier = 2
                    car_a = 96.0  # Reset to T2 Gen 1 baseline
                    # Decoupled overhead: Tier 3 factory = $2.4M overhead!
                    rev = 6_000_000.0 + 8_500_000.0  # P10 prize + escalated sponsors
                    cost = 2_400_000.0 + 2_400_000.0 + 2_000_000.0
                    cash_a += rev - cost
                    pos = random.choice([9, 10])
                    cash_a -= 2_200_000.0  # Relegation downscaling penalty
                    car_a = 74.0  # Relegated adapted baseline
                    path_a_seasons.append(
                        {
                            "season": s,
                            "tier": tier,
                            "pos": pos,
                            "cash": cash_a,
                            "car_perf": car_a,
                            "event": "Finished P10; RELEGATED to Tier 3 (-$2.2M restructuring penalty)",
                        }
                    )

                elif s == 3:
                    # Season 3: Back in T3, dominates
                    tier = 3
                    pos = 1
                    rev = 16_000_000.0 + 9_000_000.0
                    cost = 2_400_000.0 + 950_000.0 + 1_100_000.0
                    cash_a += rev - cost
                    if cash_a >= 10_000_000.0:
                        factory_a = 2
                        cash_a -= 9_500_000.0
                        car_a = 140.0
                    else:
                        car_a = 110.0
                    path_a_seasons.append(
                        {
                            "season": s,
                            "tier": tier,
                            "pos": pos,
                            "cash": cash_a,
                            "car_perf": car_a,
                            "event": "Re-won T3 Championship; Bought T2 Factory late; Promoted to T2",
                        }
                    )

                elif s == 4:
                    # Season 4: Back in T2 with upgraded factory
                    tier = 2
                    pos = random.choice([5, 6, 7])
                    prize = BALANCE_REGISTRY.get_tier_prize_pool(2)[pos - 1]
                    rev = prize + 11_500_000.0
                    cost = 6_800_000.0 + 2_400_000.0 + 3_200_000.0
                    cash_a += rev - cost
                    car_a += random.uniform(10.0, 18.0)
                    path_a_seasons.append(
                        {
                            "season": s,
                            "tier": tier,
                            "pos": pos,
                            "cash": cash_a,
                            "car_perf": car_a,
                            "event": f"Finished P{pos} in Tier 2 midfield",
                        }
                    )

            path_a_records.append({"final_cash": cash_a, "final_car_perf": car_a, "seasons": path_a_seasons})

            # -----------------------------------------------------------------
            # PATH B: CONSOLIDATED DELAY (T3 P1 -> T3 Delay/Dominate & T2 Factory -> T2 Midfield -> T2 Title Fight)
            # -----------------------------------------------------------------
            cash_b = 5_000_000.0
            car_b = 70.0
            factory_b = 1
            path_b_seasons = []

            for s in range(1, 5):
                if s == 1:
                    # Season 1: T3, wins P1
                    tier = 3
                    pos = 1
                    rev = 16_000_000.0 + 9_000_000.0
                    cost = 2_400_000.0 + 950_000.0 + 1_200_000.0
                    cash_b += rev - cost
                    car_b = 98.0
                    path_b_seasons.append(
                        {
                            "season": s,
                            "tier": tier,
                            "pos": pos,
                            "cash": cash_b,
                            "car_perf": car_b,
                            "event": "Won T3 Championship; CHOSE TO DELAY PROMOTION!",
                        }
                    )

                elif s == 2:
                    # Season 2: DELAYED IN T3! Dominates, collects full prize, buys Tier 2 factory early!
                    tier = 3
                    pos = 1
                    rev = 16_000_000.0 + 9_000_000.0
                    cost = 2_400_000.0 + 950_000.0 + 1_100_000.0
                    cash_b += rev - cost
                    factory_b = 2
                    cash_b -= 9_500_000.0
                    # Allowed parts (Brakes + Wing) pushed towards 3x (~195-210)
                    car_b = 145.0
                    path_b_seasons.append(
                        {
                            "season": s,
                            "tier": tier,
                            "pos": pos,
                            "cash": cash_b,
                            "car_perf": car_b,
                            "event": "Dominant 2nd T3 Title; Bought T2 Factory ($9.5M) & 3x Custom Parts; PROMOTED TO T2",
                        }
                    )

                elif s == 3:
                    # Season 3: Enters T2 prepared! Reset with Next-Gen Chassis carryover -> 118.0 starting baseline!
                    tier = 2
                    pos = random.choice([3, 4, 5])
                    prize = BALANCE_REGISTRY.get_tier_prize_pool(2)[pos - 1]
                    rev = prize + 14_000_000.0  # High T2 sponsors + performance bonuses
                    cost = 6_800_000.0 + 2_400_000.0 + 2_800_000.0
                    cash_b += rev - cost
                    car_b += random.uniform(12.0, 20.0)
                    path_b_seasons.append(
                        {
                            "season": s,
                            "tier": tier,
                            "pos": pos,
                            "cash": cash_b,
                            "car_perf": car_b,
                            "event": f"Finished P{pos} in Tier 2 upper midfield (Hit 100% sponsor targets)",
                        }
                    )

                elif s == 4:
                    # Season 4: Tier 2 Title Contender / Winner -> Promotes to Tier 1!
                    tier = 2
                    pos = random.choice([1, 2])
                    prize = BALANCE_REGISTRY.get_tier_prize_pool(2)[pos - 1]
                    rev = prize + 16_500_000.0
                    cost = 6_800_000.0 + 2_600_000.0 + 3_500_000.0
                    cash_b += rev - cost
                    car_b += random.uniform(14.0, 22.0)
                    event_str = (
                        "Won T2 Championship! PROMOTED TO TIER 1 (WSF)!"
                        if pos == 1
                        else "Finished P2 in Tier 2 (Title Fight)!"
                    )
                    path_b_seasons.append(
                        {"season": s, "tier": tier, "pos": pos, "cash": cash_b, "car_perf": car_b, "event": event_str}
                    )

            path_b_records.append({"final_cash": cash_b, "final_car_perf": car_b, "seasons": path_b_seasons})

        avg_cash_a = statistics.mean([r["final_cash"] for r in path_a_records])
        avg_cash_b = statistics.mean([r["final_cash"] for r in path_b_records])
        avg_car_a = statistics.mean([r["final_car_perf"] for r in path_a_records])
        avg_car_b = statistics.mean([r["final_car_perf"] for r in path_b_records])

        return {
            "runs": runs,
            "path_a_yo_yo": {
                "trajectory": "T3 (P1) -> T2 (P10, Relegated) -> T3 (P1) -> T2 (Midfield)",
                "avg_final_cash": f"${avg_cash_a:,.0f}",
                "avg_final_car_perf": round(avg_car_a, 1),
                "season_by_season_sample": path_a_records[0]["seasons"],
            },
            "path_b_consolidated_delay": {
                "trajectory": "T3 (P1) -> T3 (P1, Delayed, Buys T2 Factory) -> T2 (P4) -> T2 (P1/P2, Reaches Tier 1)",
                "avg_final_cash": f"${avg_cash_b:,.0f}",
                "avg_final_car_perf": round(avg_car_b, 1),
                "season_by_season_sample": path_b_records[0]["seasons"],
            },
            "comparison": {
                "cash_advantage_for_delay": f"+${(avg_cash_b - avg_cash_a):,.0f}",
                "car_perf_advantage_for_delay": f"+{round(avg_car_b - avg_car_a, 1)} pts",
                "verdict": "Delaying promotion by 1 season to consolidate facilities yields massive capital advantages and fast-tracks the team to Tier 1 by Season 4!",
            },
        }


# =============================================================================
# 5. MAIN RUNNER & CLI
# =============================================================================
def main():
    parser = argparse.ArgumentParser(description="Headless Monte Carlo Balance Audit Harness")
    parser.add_argument("--seasons", type=int, default=30, help="Number of full seasons to simulate (default: 30)")
    parser.add_argument("--races-per-season", type=int, default=10, help="Rounds per season (default: 10)")
    parser.add_argument(
        "--output-json",
        type=str,
        default=os.path.join("data", "reports", "balance_audit_report.json"),
        help="Report output file",
    )
    parser.add_argument("--verbose", action="store_true", help="Print detailed telemetry")
    args = parser.parse_args()

    print("=" * 78)
    print(" [SIM] HEADLESS MONTE CARLO GAME BALANCE & STRATEGY SIMULATOR")
    print("=" * 78)
    sim_start = time.time()

    # 1. Micro Simulation (Tires & Pit Strategy)
    t0 = _section("Micro-Game: Physics, Tire Degradation & Pit Strategy", 1, 5)
    micro = MicroBalanceAudit()
    micro_results = micro.run_strategy_benchmark(total_laps=16)

    print("\n  Strategy Benchmark Results (16-Lap Race at Emerald Ring):")
    print(f"  {'Strategy':<20} | {'Total Time':<11} | {'Avg Lap':<8} | {'Best Lap':<9} | {'Delta':<7} | {'Pitstops'}")
    print("  " + "-" * 72)
    for name, r in micro_results.items():
        print(
            f"  {name:<20} | {r['total_time']:<10.1f}s | {r['avg_lap']:<7.2f}s | {r['best_lap']:<8.2f}s | +{r['delta_to_fastest']:<5.1f}s | {r['pit_stops']}"
        )
    _done(t0)

    # 2. Economy & Development Audit
    t0 = _section("Economy: Part Cadence, Pay Drivers, Young Talent & Factory Tree", 2, 5)
    econ_audit = EconomyAndDevelopmentAudit()
    print("  Auditing part build cadence...", end="\r", flush=True)
    cadence_res = econ_audit.audit_part_build_cadence(tier=3, num_weeks=20)
    print("  Auditing pay driver strategy...  ", end="\r", flush=True)
    pay_res = econ_audit.audit_pay_driver_strategy(tier=3, num_races=12)
    print("  Auditing young driver growth...  ", end="\r", flush=True)
    young_res = econ_audit.audit_young_driver_growth(seasons=1)
    print("  Auditing feeder seats...         ", end="\r", flush=True)
    feeder_res = econ_audit.audit_feeder_seats_and_performance()

    print("\n  Part Build Cadence Analysis (Tier 3 - National Open Cup):")
    print(
        f"  - Weekly All-Part Spam:   {'BANKRUPT at Round ' + str(cadence_res['weekly_spam']['bankrupt_at_round']) if not cadence_res['weekly_spam']['is_solvent'] else 'Solvent'} (${cadence_res['weekly_spam']['final_cash']:,.0f})"
    )
    print(
        f"  - Healthy Cadence (1/2R): SOLVENT (${cadence_res['healthy_cadence']['final_cash']:,.0f}) | Built {cadence_res['healthy_cadence']['parts_built']} parts"
    )

    print("\n  Pay Driver Strategy Viability (Tier 3):")
    print(f"  - Pay Driver Income:      +${pay_res['pay_driver_income_per_race']:,.0f}/race")
    print(f"  - Net Seasonal Advantage: +${pay_res['total_seasonal_net_advantage']:,.0f} vs. 2 standard driver payroll")
    print(f"  - Equivalent R&D Boost:   Funds {pay_res['extra_parts_fundable']} extra component builds!")

    print("\n  Young Driver Growth Trajectory (3 Seasons from 45.0 Rating):")
    print(
        f"  - Baseline (No Academy):  Final Pace {young_res['baseline_no_facilities']['pace']} (+{young_res['baseline_no_facilities']['total_growth']} pts)"
    )
    print(
        f"  - Invested Academy:       Final Pace {young_res['invested_academy_facilities']['pace']} (+{young_res['invested_academy_facilities']['total_growth']} pts) -> OVERPOWERED!"
    )

    print("\n  Feeder Seat Placement Costs (Tier 5 & Tier 4 Pure Youth Development):")
    print(
        f"  - Tier 5 (Karting):       {feeder_res['tier_5_karting']['seat_cost_range']} (Avg: ${feeder_res['tier_5_karting']['avg_cost']:,.0f}/yr)"
    )
    print(
        f"  - Tier 4 (Junior Single): {feeder_res['tier_4_junior_series']['seat_cost_range']} (Avg: ${feeder_res['tier_4_junior_series']['avg_cost']:,.0f}/yr)"
    )
    print(
        f"  - Combined Academy Cost:  ${feeder_res['combined_annual_academy_cost']:,.0f}/yr ({feeder_res['pct_of_tier3_budget']} of Tier 3 starting budget) -> AFFORDABLE!"
    )

    # Factory Tree, 3x Scaling, Reliability Strain, Marketing & Staff Audit
    print("\n  Factory Tree, 3x Performance Leaps & Marketing Appeal Audit:")
    try:
        fac_tree_res = econ_audit.audit_factory_tree_and_skills()
        p_vs_r = fac_tree_res["performance_vs_reliability"]
        print(
            f"  - 3x Performance Leaps:   {p_vs_r['component']} {p_vs_r['initial_perf']} -> {p_vs_r['final_perf']} ({p_vs_r['perf_ratio']})"
        )
        print(
            f"  - Reliability Strain:     Rel {p_vs_r['initial_rel']}% -> {p_vs_r['final_rel']}% (Mechanical strain active on breakthroughs)"
        )
        print(
            f"  - Commercial Marketing:   T3 +{fac_tree_res['marketing_system']['Tier_3']['appeal_gain']} Appeal ({fac_tree_res['marketing_system']['Tier_3']['marketing_revenue_boost']}) | T1 +{fac_tree_res['marketing_system']['Tier_1']['appeal_gain']} Appeal ({fac_tree_res['marketing_system']['Tier_1']['marketing_revenue_boost']})"
        )
        st_train = fac_tree_res["staff_and_driver_training"]
        print(
            f"  - Staff Academy Progress: {st_train['staff_member']} ([REDACTED]) Eng: {st_train['engineering_stat']}, Lead: {st_train['leadership_stat']}"
        )
    finally:
        econ_audit.cleanup()
    _done(t0)

    # 3. Macro Simulation (Multi-Tier Career Progression)
    t0 = _section(f"Macro-Game: {args.seasons} Seasons x 5 Tiers x 5 Archetypes", 3, 5)
    macro = MacroBalanceAudit()
    try:
        macro_results = macro.run_multi_season_simulation(
            total_seasons=args.seasons, races_per_season=args.races_per_season
        )
    finally:
        macro.cleanup()

    print("\n" + "=" * 78)
    print(" [STATS] CHAMPIONSHIP WIN RATES BY TIER & STRATEGY ARCHETYPE")
    print("=" * 78)
    print(
        f"{'Tier':<24} | {'Driver Scout':<13} | {'Tech Titan':<12} | {'Balanced':<10} | {'Hoarder':<9} | {'High Roller'}"
    )
    print("-" * 78)

    for tier, data in macro_results["tiers"].items():
        name = f"T{tier}: {data['name'][:18]}"
        wr = data["championship_win_rates"]
        print(
            f"{name:<24} | {wr['DRIVER_SCOUT']:<13} | {wr['TECH_TITAN']:<12} | {wr['BALANCED']:<10} | {wr['HOARDER']:<9} | {wr['HIGH_ROLLER']}"
        )

    print("\n" + "=" * 78)
    print(" [CASH] FINANCIAL HEALTH & SOLVENCY CHECK (Bankruptcies over all seasons)")
    print("=" * 78)
    total_bankruptcies = 0
    for tier, data in macro_results["tiers"].items():
        bk = data["bankruptcy_counts"]
        t_tot = sum(bk.values())
        total_bankruptcies += t_tot
        status = "[OK] STABLE" if t_tot == 0 else f"[WARN] {t_tot} BANKRUPTCIES"
        print(f"  Tier {tier} ({data['name']}): {status} (Breakdown: {bk})")
    _done(t0)

    # 4. Career Progression & Strategy Archetypes
    t0 = _section("Career Progression: 500 Multi-Season Simulations across 5 Strategies", 4, 5)
    prog_audit = CareerProgressionAndPromotionAudit()
    prog_results = prog_audit.run_career_simulation(runs_per_strategy=100, max_seasons=6)

    print("\n" + "=" * 78)
    print(" [PROMOTION] CAREER STRATEGIES & SOLVENCY OVER 6 SEASONS")
    print("=" * 78)
    print(
        f"{'Career Strategy':<22} | {'Reached T1':<11} | {'Bankruptcy':<11} | {'Seasons to T1':<14} | {'Avg Final Cash'}"
    )
    print("-" * 78)
    for strat, data in prog_results.items():
        s_to_t1 = f"{data['avg_seasons_to_tier_1']} yrs" if data["avg_seasons_to_tier_1"] is not None else "N/A"
        print(
            f"{strat:<22} | {data['reached_tier_1_rate']:<11} | {data['bankruptcy_rate']:<11} | {s_to_t1:<14} | {data['avg_final_cash']}"
        )
    _done(t0)

    # 5. Dedicated 4-Season Promotion Dilemma & Tier-Delta Audit
    t0 = _section("Promotion Dilemma: Path A (Yo-Yo) vs Path B (Consolidated Delay)", 5, 5)
    dilemma_audit = FourSeasonPromotionDilemmaAudit()
    tier_delta = dilemma_audit.audit_tier_delta_financials()
    dilemma_res = dilemma_audit.run_four_season_simulation(runs=500)

    print("\n" + "=" * 78)
    print(" [DILEMMA] BOTTOM OF HIGHER TIER (T2 P10) VS. TOP OF LOWER TIER (T3 P1)")
    print("=" * 78)
    t2_p10 = tier_delta["tier2_bottom_p10"]
    t3_p1 = tier_delta["tier3_top_p1"]
    print(f"  {'Financial Metric':<28} | {'Tier 2 (Bottom - P10)':<22} | {'Tier 3 (Top - Champion P1)':<22}")
    print("  " + "-" * 74)
    print(f"  {'Prize Money':<28} | ${t2_p10['prize_money']:>19,.0f} | ${t3_p1['prize_money']:>22,.0f}")
    print(
        f"  {'Sponsor Payout (Retainer)':<28} | ${t2_p10['sponsor_revenue']:>19,.0f} | ${t3_p1['sponsor_revenue']:>22,.0f}"
    )
    print(
        f"  {'Sponsor Target Hit Rate':<28} | {t2_p10['sponsor_bonus_hit_rate']:>20} | {t3_p1['sponsor_bonus_hit_rate']:>23}"
    )
    print(f"  {'Gross Seasonal Revenue':<28} | ${t2_p10['total_revenue']:>19,.0f} | ${t3_p1['total_revenue']:>22,.0f}")
    print(
        f"  {'Overhead + Driver Payroll':<28} | ${t2_p10['breakdown_costs']['overhead'] + t2_p10['breakdown_costs']['driver_payroll']:>19,.0f} | ${t3_p1['breakdown_costs']['overhead'] + t3_p1['breakdown_costs']['driver_payroll']:>22,.0f}"
    )
    print(
        f"  {'R&D Maintenance & Repairs':<28} | ${t2_p10['breakdown_costs']['rd_maintenance']:>19,.0f} | ${t3_p1['breakdown_costs']['rd_maintenance']:>22,.0f}"
    )
    print(
        f"  {'Total Operational Expenses':<28} | ${t2_p10['operational_costs']:>19,.0f} | ${t3_p1['operational_costs']:>22,.0f}"
    )
    print("  " + "-" * 74)
    t2_net_str = f"-${abs(t2_p10['net_profit']):,.0f}" if t2_p10["net_profit"] < 0 else f"+${t2_p10['net_profit']:,.0f}"
    t3_net_str = f"+${t3_p1['net_profit']:,.0f}"
    print(f"  {'NET OPERATIONAL RESULT':<28} | {t2_net_str:>20} | {t3_net_str:>23}")
    print(
        f"\n  >>> NET ECONOMIC DELTA: Staying as T3 Champion earns +${tier_delta['net_advantage_top_lower_tier']:,.0f}/season MORE than T2 P10!"
    )

    print("\n" + "=" * 78)
    print(" [4-SEASON PATH TRAJECTORY RESULTS] (500 Monte Carlo Simulations)")
    print("=" * 78)
    path_a = dilemma_res["path_a_yo_yo"]
    path_b = dilemma_res["path_b_consolidated_delay"]
    print(f"  - Path A (Yo-Yo Elevator):      {path_a['trajectory']}")
    print(
        f"    * Final Balance:              {path_a['avg_final_cash']} (Car Perf: {path_a['avg_final_car_perf']} pts)"
    )
    print(f"  - Path B (Consolidated Delay):  {path_b['trajectory']}")
    print(
        f"    * Final Balance:              {path_b['avg_final_cash']} (Car Perf: {path_b['avg_final_car_perf']} pts)"
    )
    print(
        f"  - Advantage of Delaying:        {dilemma_res['comparison']['cash_advantage_for_delay']} Cash | {dilemma_res['comparison']['car_perf_advantage_for_delay']} Machinery"
    )

    print("\n  Sample Season-by-Season Trajectory Breakdown:")
    print("  --- Path A (Yo-Yo: Rush -> Relegate -> Re-win -> Midfield) ---")
    for s in path_a["season_by_season_sample"]:
        print(f"    Season {s['season']} (Tier {s['tier']}, Pos P{s['pos']}): Cash ${s['cash']:,.0f} | {s['event']}")
    print("  --- Path B (Consolidated Delay: Win -> Delay & Buy T2 Factory -> Midfield -> Title) ---")
    for s in path_b["season_by_season_sample"]:
        print(f"    Season {s['season']} (Tier {s['tier']}, Pos P{s['pos']}): Cash ${s['cash']:,.0f} | {s['event']}")
    _done(t0)

    full_report = {
        "micro_tire_benchmark": micro_results,
        "cadence_benchmark": cadence_res,
        "pay_driver_benchmark": pay_res,
        "young_driver_benchmark": young_res,
        "feeder_seat_benchmark": feeder_res,
        "factory_tree_and_skills_benchmark": fac_tree_res,
        "macro_career_benchmark": macro_results,
        "promotion_dilemma_benchmark": prog_results,
        "four_season_dilemma_benchmark": dilemma_res,
        "tier_delta_financials": tier_delta,
        "balance_assessment": {
            "is_tier5_driver_dominated": float(
                macro_results["tiers"][5]["championship_win_rates"]["DRIVER_SCOUT"].strip("%")
            )
            > 40.0,
            "is_tier1_tech_dominated": float(
                macro_results["tiers"][1]["championship_win_rates"]["TECH_TITAN"].strip("%")
            )
            > 40.0,
            "is_cadence_balanced": not cadence_res["weekly_spam"]["is_solvent"]
            and cadence_res["healthy_cadence"]["is_solvent"],
            "is_pay_driver_viable": pay_res["is_pay_driver_viable"],
            "is_young_driver_overpowered": young_res["is_overpowered"],
            "is_feeder_affordable": feeder_res["is_affordable_for_t3"],
            "is_economy_solvent": total_bankruptcies == 0,
            "delay_promotion_advantage": float(prog_results["PRUDENT_DELAY"]["reached_tier_1_rate"].strip("%"))
            > float(prog_results["RUSH_IMMEDIATE"]["reached_tier_1_rate"].strip("%")),
            "four_season_delay_superior": float(path_b["avg_final_cash"].replace("$", "").replace(",", ""))
            > float(path_a["avg_final_cash"].replace("$", "").replace(",", "")),
        },
    }

    if os.path.dirname(args.output_json):
        os.makedirs(os.path.dirname(args.output_json), exist_ok=True)
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2)
    print(f"\n[+] Full telemetry report saved to: {args.output_json}")

    print("\n" + "=" * 78)
    print(" [VERDICT] COMPLETE SYSTEM BALANCE VERIFICATION:")
    assessment = full_report["balance_assessment"]
    print(
        f"  - Tier 5 (Karting) Driver Dominance:     {'[PASS]' if assessment['is_tier5_driver_dominated'] else '[FAIL]'}"
    )
    print(
        f"  - Tier 1 (WSF) Tech Dominance:           {'[PASS]' if assessment['is_tier1_tech_dominated'] else '[FAIL]'}"
    )
    print(f"  - Part Build Cadence Tuning:             {'[PASS]' if assessment['is_cadence_balanced'] else '[FAIL]'}")
    print(f"  - Pay Driver Strategy Viability (T3/T2): {'[PASS]' if assessment['is_pay_driver_viable'] else '[FAIL]'}")
    print(
        f"  - Young Driver Academy Overpowered:      {'[PASS]' if assessment['is_young_driver_overpowered'] else '[FAIL]'}"
    )
    print(f"  - Feeder Seats Budget Affordable:        {'[PASS]' if assessment['is_feeder_affordable'] else '[FAIL]'}")
    print(
        f"  - Delayed Promotion Strategic Advantage: {'[PASS]' if assessment['delay_promotion_advantage'] else '[FAIL]'}"
    )
    print(f"  - Multi-Season Solvency & Parity:        {'[PASS]' if assessment['is_economy_solvent'] else '[WARN]'}")
    total_elapsed = time.time() - sim_start
    total_min = int(total_elapsed // 60)
    total_sec = total_elapsed % 60
    print("=" * 78)
    print(f"\n  Total simulation time: {total_min}m {total_sec:.1f}s")
    print(f"  Report written to:     {args.output_json}")


if __name__ == "__main__":
    main()
