import random
import sqlite3
from typing import Any, Dict, List, Optional

from ..data.balance_config import BALANCE_REGISTRY
from ..database.career_db import CareerDatabase

POINTS_TABLE = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]

TEAM_SPECIALTIES = {
    # Tier 1: World Super Formula
    "Storm Racing": "SPEED",
    "Scuderia Veloce": "BRAKES",
    "Apex Dynamics": "AERO",
    "Solaris GP": "SPEED",
    "AeroStar GP": "AERO",
    "Vanguard Motorsport": "BALANCED",
    "Titan GP": "SPEED",
    "Nexus Racing": "BALANCED",
    "Kestrel F1": "BRAKES",
    "Neon Velocity": "BALANCED",
    # Tier 2: Continental Championship
    "Nordic Velocity": "SPEED",
    "Bavaria Sport": "AERO",
    "Riviera Corse": "BRAKES",
    "Silverstone Engineering": "AERO",
    "Iberia Grand Prix": "BALANCED",
    "Alps Dynamics": "BRAKES",
    "Danube GP": "BALANCED",
    "Baltic Motorsport": "SPEED",
    "Apennine Racing": "BRAKES",
    "Caledonia Speed": "BALANCED",
    # Tier 3: National Open Cup
    "Horizon Racing": "BALANCED",
    "Vortex Sprint": "SPEED",
    "Apex Club Sport": "BRAKES",
    "Phoenix GP": "SPEED",
    "Falcon Dynamics": "AERO",
    "Mirage Motorsport": "BALANCED",
    "Pulse Racing Team": "BRAKES",
    "Zephyr Cup": "AERO",
    "Stratos Autosport": "BALANCED",
    "Obsidian GP": "SPEED",
    # Tier 4: Junior Talent Series
    "JTS Academy Blue": "SPEED",
    "JTS Academy Red": "BALANCED",
    "Future Stars GP": "BRAKES",
    "Nova Talent Cup": "AERO",
    "Pioneer Junior GP": "BALANCED",
    "Ascent Autosport": "SPEED",
    "Velocity Youth": "BALANCED",
    "Vector Pro-Junior": "BRAKES",
    "Rookie Vanguard": "AERO",
    "Zenith Junior": "BALANCED",
    # Tier 5: Karting Masters
    "KMA Elite Alpha": "BALANCED",
    "KMA Elite Beta": "SPEED",
    "EuroKart Masters": "BRAKES",
    "Nordic Karting": "AERO",
    "Monza Kart Club": "SPEED",
    "Silverstone Kart Cadets": "BALANCED",
    "Spa Young Drivers": "AERO",
    "Suzuka Karting School": "BRAKES",
    "Interlagos Juniors": "SPEED",
    "Apex Karting Academy": "BALANCED",
}

TRACK_RAIN_CHANCES = {
    "oasis": 0.02,
    "autodromo": 0.10,
    "harbor": 0.12,
    "riviera": 0.18,
    "emerald": 0.25,
    "apex": 0.30,
    "vortex": 0.40,
    "ardennes": 0.60,
    "silverstone": 0.40,
    "brands_hatch": 0.35,
    "oulton": 0.35,
    "knockhill": 0.55,
    "donington": 0.35,
    "snetterton": 0.30,
}


class LeagueSimulator:
    """
    Simulates weekly championship rounds across all 5 tiers.
    Uses clean, transparent simulation math:
    - Base expected team outcome + team track specialty alignment.
    - AI drivers perform around team baseline with small variance.
    - Player's young drivers are the real variable: their attributes (pace, braking,
      rain mastery, consistency, morale) create direct performance deltas against the car's baseline!
    """

    def __init__(self, db: CareerDatabase):
        self.db = db

    def simulate_background_round(self, round_num: int, player_race_results: Optional[List[Dict[str, Any]]] = None):
        """Backward-compatibility bridge calling simulate_weekly_series for all series in round_num."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT week FROM calendar WHERE round = ? ORDER BY week ASC;", (round_num,))
            weeks = [r[0] for r in cur.fetchall()]

        if not weeks:
            weeks = [round_num]

        last_res = {}
        for w in weeks:
            last_res = self.simulate_weekly_series(w, player_race_results=player_race_results)
        return last_res

    def simulate_weekly_series(
        self, week: int, player_race_results: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Simulates all series racing in the specified calendar week.
        Records full driver classifications in series_race_results, awards points to
        drivers and constructors, and updates academy driver development & morale.
        """
        summary: Dict[str, Any] = {"week": week, "tiers_simulated": [], "results_by_tier": {}, "academy_highlights": []}

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            season_num = self.db.get_current_season_num()

            # Find all scheduled rounds for this calendar week across tiers
            cur.execute("SELECT * FROM calendar WHERE week = ? AND is_completed = 0 ORDER BY tier ASC;", (week,))
            scheduled_rounds = [dict(r) for r in cur.fetchall()]

            if not scheduled_rounds:
                return summary

            for cal_round in scheduled_rounds:
                tier = cal_round["tier"]
                round_num = cal_round["round"]
                track_name = cal_round["track_name"]
                track_char = cal_round.get("characteristic", "BALANCED")
                weather = cal_round.get("weather_profile", "DYNAMIC")
                c_file = str(cal_round.get("circuit_file", "")).lower()
                t_lower = str(track_name).lower()
                rain_prob = 0.20
                for k, v in TRACK_RAIN_CHANCES.items():
                    if k in c_file or k in t_lower:
                        rain_prob = v
                        break
                is_rain = (random.random() < rain_prob) if weather == "DYNAMIC" else (weather == "RAIN")
                summary["tiers_simulated"].append(tier)

                # Simulate AI intra-season R&D packages (every 3 rounds in Tiers 1-3)
                self._process_ai_in_season_development(cur, tier, round_num)

                # Fetch all teams in this tier
                cur.execute(
                    "SELECT id, name, is_player, reputation, is_relegated_titan FROM teams WHERE tier = ? ORDER BY reputation DESC;",
                    (tier,),
                )
                teams = [dict(r) for r in cur.fetchall()]

                # Fetch any player academy drivers racing in this tier
                cur.execute(
                    """
                SELECT * FROM drivers 
                WHERE is_academy_driver = 1 AND academy_tier_placement = ?;
                """,
                    (tier,),
                )
                academy_drivers = [dict(r) for r in cur.fetchall()]
                academy_by_team = {d["academy_team_name"]: d for d in academy_drivers if d.get("academy_team_name")}

                driver_entries = []

                for rank_idx, t in enumerate(teams):
                    t_name = t["name"]
                    is_player_team = bool(t["is_player"])
                    specialty = TEAM_SPECIALTIES.get(t_name, "BALANCED")

                    # Load tier dominance weights and benchmarks from central config
                    w_driver, w_car = BALANCE_REGISTRY.get_tier_weights(tier)
                    tw = BALANCE_REGISTRY.tier_dominance.get(tier, BALANCE_REGISTRY.tier_dominance[3])

                    # Calculate car performance from mounted components or reputation baseline
                    cur.execute(
                        """
                    SELECT AVG(performance), AVG(current_durability) 
                    FROM car_components 
                    WHERE team_id = ? AND car_slot > 0;
                    """,
                        (t["id"],),
                    )
                    comp_row = cur.fetchone()
                    avg_dur = 100.0
                    if comp_row and comp_row[0] is not None:
                        avg_perf = float(comp_row[0])
                        avg_dur = float(comp_row[1] or 100.0)
                        dur_penalty = max(0.0, (80.0 - avg_dur) * 0.40) if avg_dur < 80.0 else 0.0
                        car_rating = avg_perf - dur_penalty
                    else:
                        rep_bonus = (float(t.get("reputation", 50)) - 50.0) * 0.22
                        car_rating = tw.benchmark_car_perf + rep_bonus - (rank_idx * 1.5)

                    car_delta = car_rating - tw.benchmark_car_perf

                    # Relegated Titan: Starts slightly behind on setup adaptations, but improves aggressively!
                    titan_bonus = 0.0
                    if bool(t.get("is_relegated_titan", 0)):
                        season_progress = min(1.0, float(week) / 16.0)
                        titan_bonus = -3.5 + season_progress * 10.0

                    # Fetch drivers for this team
                    cur.execute("SELECT * FROM drivers WHERE team_id = ? AND is_academy_driver = 0;", (t["id"],))
                    team_drivers = [dict(r) for r in cur.fetchall()]

                    # In Tier 4/5 feeder teams, substitute assigned academy driver into seat #1
                    if t_name in academy_by_team:
                        acad_d = academy_by_team[t_name]
                        # Replace or prepend academy driver
                        team_drivers = [acad_d] + [d for d in team_drivers if d["id"] != acad_d["id"]][:2]

                    # If team has no drivers generated, create stand-ins
                    if not team_drivers:
                        team_drivers = [
                            {
                                "id": None,
                                "name": f"{t_name} Driver A",
                                "pace": tw.benchmark_driver_skill,
                                "consistency": 50,
                                "morale": 75.0,
                                "is_academy_driver": 0,
                                "is_player_driver": 0,
                            },
                            {
                                "id": None,
                                "name": f"{t_name} Driver B",
                                "pace": tw.benchmark_driver_skill - 2,
                                "consistency": 50,
                                "morale": 75.0,
                                "is_academy_driver": 0,
                                "is_player_driver": 0,
                            },
                        ]

                    for d_idx, d in enumerate(team_drivers):
                        is_academy = bool(d.get("is_academy_driver", 0))
                        is_player_driver = bool(d.get("is_player_driver", 0))

                        # If player completed live race and this is the player's primary car
                        if is_player_team and player_race_results and d_idx == 0:
                            p_pos = player_race_results[0].get("position", 1)
                            # Huge score to force exact player finish position
                            driver_score = 10000.0 - p_pos
                        elif is_player_team and player_race_results and len(player_race_results) > 1 and d_idx == 1:
                            p_pos2 = player_race_results[1].get("position", 2)
                            driver_score = 10000.0 - p_pos2
                        else:
                            # -------------------------------------------------------------
                            # Tier Dominance Synthesis: Driver vs. Car Weighting
                            # -------------------------------------------------------------
                            d_pace = float(d.get("pace") or tw.benchmark_driver_skill)
                            d_braking = float(d.get("braking") or tw.benchmark_driver_skill)
                            d_defending = float(d.get("defending") or tw.benchmark_driver_skill)
                            d_wet = float(d.get("wet_weather") or tw.benchmark_driver_skill)
                            d_cons = float(d.get("consistency") or 50.0)
                            d_morale = float(d.get("morale") or 75.0)

                            # Track characteristic demand bonus
                            track_skill_bonus = 0.0
                            if track_char == "BRAKES":
                                track_skill_bonus = (d_braking - tw.benchmark_driver_skill) * 0.20
                            elif track_char == "SPEED":
                                track_skill_bonus = (d_pace - tw.benchmark_driver_skill) * 0.20
                            elif track_char == "AERO":
                                track_skill_bonus = (d_defending - tw.benchmark_driver_skill) * 0.20

                            wet_bonus = (d_wet - tw.benchmark_driver_skill) * 0.45 if is_rain else 0.0
                            avg_skill = (
                                d_pace * 0.45
                                + d_braking * 0.25
                                + d_defending * 0.15
                                + (d_wet if is_rain else d_pace) * 0.15
                            )
                            driver_delta = (avg_skill - tw.benchmark_driver_skill) + track_skill_bonus + wet_bonus

                            # Track affinity specialty bonus
                            affinity_bonus = 3.5 if specialty == track_char else 0.0
                            morale_mod = (d_morale - 75.0) * 0.08

                            # Normalized percentage deltas relative to tier benchmark
                            car_norm = (car_delta / max(1.0, tw.benchmark_car_perf)) * 48.0
                            driver_norm = (driver_delta / 100.0) * 48.0

                            # Race-day form variance influenced by driver consistency
                            cons_factor = (100.0 - d_cons) / 100.0  # 0.20 for 80 cons, 0.55 for 45 cons
                            form_var = random.gauss(0.0, 1.4 + cons_factor * 4.2)

                            # Race incident / mishap probability (pitstop blunder, yellow flag, or mechanical wear)
                            mech_risk = max(0.0, (75.0 - avg_dur) * 0.006)
                            incident_chance = 0.045 + mech_risk
                            incident_penalty = -random.uniform(4.0, 9.0) if random.random() < incident_chance else 0.0
                            seat_offset = -1.0 if d_idx > 0 else 0.6

                            # TIER STRATEGY SYNTHESIS:
                            # Tier 5 (Karting): w_driver ~ 0.82, w_car ~ 0.18 -> Driver Talent dominates
                            # Tier 1 (WSF):     w_driver ~ 0.22, w_car ~ 0.78 -> Car Engineering dominates
                            # Tier 3 (NOC):     w_driver ~ 0.50, w_car ~ 0.50 -> Balanced parity
                            perf_contribution = (w_driver * driver_norm) + (w_car * car_norm)
                            driver_score = (
                                80.0
                                + perf_contribution
                                + affinity_bonus
                                + titan_bonus
                                + morale_mod
                                + form_var
                                + incident_penalty
                                + seat_offset
                            )

                        driver_entries.append(
                            {
                                "driver_id": d.get("id"),
                                "driver_name": d.get("name", f"Driver {d_idx + 1}"),
                                "team_id": t["id"],
                                "team_name": t_name,
                                "is_academy_driver": is_academy,
                                "is_player": is_player_team or is_player_driver,
                                "score": driver_score,
                                "driver_obj": d,
                                "expected_pos": rank_idx + 1,
                            }
                        )

                # Sort drivers to determine final race classification
                driver_entries.sort(key=lambda x: x["score"], reverse=True)

                tier_results = []
                for pos, de in enumerate(driver_entries, 1):
                    pts = POINTS_TABLE[pos - 1] if pos <= len(POINTS_TABLE) else 0

                    # Record race result
                    cur.execute(
                        """
                    INSERT INTO series_race_results (
                        tier, round_num, week, track_name, position, driver_name,
                        team_name, team_id, driver_id, is_academy_driver, is_player, points, season_num
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                        (
                            tier,
                            round_num,
                            week,
                            track_name,
                            pos,
                            de["driver_name"],
                            de["team_name"],
                            de["team_id"],
                            de["driver_id"],
                            1 if de["is_academy_driver"] else 0,
                            1 if de["is_player"] else 0,
                            pts,
                            season_num,
                        ),
                    )

                    # Award points to driver
                    if de["driver_id"]:
                        cur.execute("UPDATE drivers SET points = points + ? WHERE id = ?;", (pts, de["driver_id"]))

                    # Award points to constructor
                    if pts > 0 and de["team_id"]:
                        cur.execute("UPDATE teams SET points = points + ? WHERE id = ?;", (pts, de["team_id"]))

                    # Handle Young Driver Post-Race Morale & Highlights
                    if de["is_academy_driver"]:
                        exp = de["expected_pos"]
                        # Compare actual finish vs expected team position
                        if pos <= 3:
                            morale_change = 8.0
                            status_desc = f"Sensational P{pos} Podium!"
                        elif pos < exp:
                            morale_change = 4.0
                            status_desc = f"Outperformed car (P{pos} vs expected P{exp})!"
                        elif pos == exp or pos == exp + 1:
                            morale_change = 1.0
                            status_desc = f"Solid drive matching car potential (P{pos})."
                        else:
                            morale_change = -3.0
                            status_desc = f"Tough race below car potential (P{pos})."

                        new_morale = max(40.0, min(100.0, float(de["driver_obj"].get("morale", 75.0)) + morale_change))
                        cur.execute("UPDATE drivers SET morale = ? WHERE id = ?;", (new_morale, de["driver_id"]))

                        highlight = {
                            "driver_name": de["driver_name"],
                            "tier": tier,
                            "round_num": round_num,
                            "track_name": track_name,
                            "position": pos,
                            "points": pts,
                            "morale": new_morale,
                            "message": f"Tier {tier} Round {round_num} ({track_name}): {de['driver_name']} finished P{pos} ({pts} PTS). {status_desc}",
                        }
                        summary["academy_highlights"].append(highlight)

                    tier_results.append(
                        {
                            "position": pos,
                            "driver_name": de["driver_name"],
                            "team_name": de["team_name"],
                            "is_academy_driver": de["is_academy_driver"],
                            "is_player": de["is_player"],
                            "points": pts,
                        }
                    )

                summary["results_by_tier"][tier] = tier_results

                # Mark calendar round completed
                cur.execute("UPDATE calendar SET is_completed = 1 WHERE tier = ? AND round = ?;", (tier, round_num))

            conn.commit()

        return summary

    TIER_PRIZE_POOLS = BALANCE_REGISTRY.economy.prize_pools

    def calculate_season_finale_data(self, player_team_id: int, prize_cash_multiplier: float = 1.0) -> Dict[str, Any]:
        """
        Gathers all end-of-season championship data for preview in the End of Season Menu:
        - Constructors standings per tier with prize amounts
        - Drivers standings per tier
        - Crowned Driver Champions & bonuses
        - Promotion & Relegation candidates
        - Player choice flags (can choose promotion if P1, P10 Tier 3 lifeline)
        """
        season_num = self.db.get_current_season_num()

        constructor_standings: Dict[int, List[Dict[str, Any]]] = {}
        driver_standings: Dict[int, List[Dict[str, Any]]] = {}
        champions: Dict[int, Dict[str, Any]] = {}

        player_tier = 3
        player_constructor_finish: Optional[Dict[str, Any]] = None

        with self.db.get_connection() as conn:
            cur = conn.cursor()

            # 1. Query Player Team Tier
            cur.execute("SELECT tier, name FROM teams WHERE id = ?;", (player_team_id,))
            p_row = cur.fetchone()
            if p_row:
                player_tier = p_row[0]

            # 2. Build Constructor Standings & Prize Pools
            for tier in [1, 2, 3]:
                cur.execute(
                    "SELECT id, name, color_hex, is_player, points, reputation FROM teams WHERE tier = ? ORDER BY points DESC, reputation DESC;",
                    (tier,),
                )
                teams = [dict(r) for r in cur.fetchall()]
                prizes = self.TIER_PRIZE_POOLS.get(tier, [1000000] * 10)

                for idx, t in enumerate(teams):
                    t["position"] = idx + 1
                    payout = prizes[idx] * prize_cash_multiplier if idx < len(prizes) else 1000000.0
                    t["prize_money"] = payout
                    if t["id"] == player_team_id:
                        player_constructor_finish = t

                constructor_standings[tier] = teams

            # 3. Build Driver Standings & Top Champion
            for tier in [1, 2, 3, 4, 5]:
                drivers = self.db.get_driver_standings(tier)
                for idx, d in enumerate(drivers):
                    d["position"] = idx + 1
                driver_standings[tier] = drivers

                if drivers:
                    champ = dict(drivers[0])
                    is_player_driver = bool(champ.get("is_player_driver", 0)) or (
                        champ.get("team_id") == player_team_id
                    )
                    champ["is_player_champion"] = is_player_driver
                    if tier in [1, 2, 3]:
                        champ["bonus_summary"] = (
                            "+100 Morale (Champion Mood), +2 Pace, +2 Consistency, +2 Defending, +12 Marketability, High Pressure Immunity"
                        )
                        if is_player_driver:
                            champ["royalty_bonus"] = 2500000.0
                    else:
                        # Feeder Series (Tier 4 & Tier 5)
                        champ["bonus_summary"] = (
                            "+5 Pace, +4 Braking, +4 Consistency, +4 Defending, +15 Marketability, +100 Morale"
                        )
                        if is_player_driver:
                            # Pure driver prize bonus (Tier 5: $10k, Tier 4: $25k) & team marketing/reputation boost
                            champ["prize_money"] = 25000.0 if tier == 4 else 10000.0
                            champ["reputation_boost"] = 5 if tier == 4 else 3

                            # Mandatory graduation check if old enough
                            # Karting (T5) -> T4 requires age >= 16; Junior (T4) -> T3 requires age >= 18
                            driver_age = int(champ.get("age", 15))
                            grad_needed = (tier == 5 and driver_age >= 16) or (tier == 4 and driver_age >= 18)
                            champ["forced_graduation"] = grad_needed
                            champ["next_tier"] = (tier - 1) if grad_needed else tier
                    champions[tier] = champ

            # Academy Champions won by player
            player_academy_champions = []
            for ft in [4, 5]:
                c = champions.get(ft)
                if c and (c.get("is_academy_driver") or c.get("team_id") == player_team_id):
                    player_academy_champions.append(c)

        # 4. Promotion & Relegation Logic
        t3_teams = constructor_standings.get(3, [])
        t2_teams = constructor_standings.get(2, [])
        t1_teams = constructor_standings.get(1, [])

        t3_p1 = t3_teams[0] if len(t3_teams) > 0 else None
        t3_p2 = t3_teams[1] if len(t3_teams) > 1 else None
        t3_p10 = t3_teams[-1] if len(t3_teams) >= 10 else None

        t2_p1 = t2_teams[0] if len(t2_teams) > 0 else None
        t2_p2 = t2_teams[1] if len(t2_teams) > 1 else None
        t2_p10 = t2_teams[-1] if len(t2_teams) >= 10 else None

        t1_p1 = t1_teams[0] if len(t1_teams) > 0 else None
        t1_p10 = t1_teams[-1] if len(t1_teams) >= 10 else None

        # Check if player won their tier
        can_player_choose_promotion = False
        if player_tier == 3 and t3_p1 and t3_p1.get("is_player"):
            can_player_choose_promotion = True
        elif player_tier == 2 and t2_p1 and t2_p1.get("is_player"):
            can_player_choose_promotion = True

        # Tier 3 P10 player protection lifeline
        is_player_p10_tier3 = False
        if player_tier == 3 and t3_p10 and t3_p10.get("is_player"):
            is_player_p10_tier3 = True

        return {
            "season_num": season_num,
            "player_tier": player_tier,
            "player_team_id": player_team_id,
            "constructor_standings": constructor_standings,
            "driver_standings": driver_standings,
            "driver_champions": champions,
            "player_driver_champion": champions.get(player_tier),
            "player_academy_champions": player_academy_champions,
            "player_constructor_finish": player_constructor_finish,
            "can_player_choose_promotion": can_player_choose_promotion,
            "is_player_p10_tier3": is_player_p10_tier3,
            "candidates": {
                "t3_p1": t3_p1,
                "t3_p2": t3_p2,
                "t3_p10": t3_p10,
                "t2_p1": t2_p1,
                "t2_p2": t2_p2,
                "t2_p10": t2_p10,
                "t1_p1": t1_p1,
                "t1_p10": t1_p10,
            },
        }

    def commit_season_finale(
        self,
        player_team_id: int,
        player_choice_promote: bool = True,
        selected_engine: Optional[str] = None,
        prize_cash_multiplier: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Applies end-of-season rewards, awards Driver Champion bonuses, executes promotion/relegation
        with player choice, signs new engine contract, and rolls over regulations and calendar to Season N+1.
        """
        data = self.calculate_season_finale_data(player_team_id, prize_cash_multiplier)
        season_num = data["season_num"]
        player_tier = data["player_tier"]

        results = {
            "promotions": [],
            "relegations": [],
            "season_payouts": [],
            "driver_champion_awarded": None,
            "academy_champions_awarded": [],
            "engine_signed": None,
            "new_season": season_num + 1,
            "new_player_tier": player_tier,
        }

        with self.db.get_connection() as conn:
            cur = conn.cursor()

            # 1. Award Constructors' Championship Prize Money
            for tier, teams in data["constructor_standings"].items():
                for t in teams:
                    payout = t["prize_money"]
                    pos = t["position"]
                    cur.execute("UPDATE teams SET cash = cash + ? WHERE id = ?;", (payout, t["id"]))
                    cur.execute(
                        """
                    INSERT INTO ledger (team_id, week, category, description, amount)
                    VALUES (?, 18, 'PRIZE_MONEY', ?, ?);
                    """,
                        (t["id"], f"Season {season_num} Constructors P{pos} Prize Money", payout),
                    )

                    cur.execute(
                        """
                    INSERT INTO season_history (team_id, season_num, championship_position, points_total, tier)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                        (t["id"], season_num, pos, t["points"], tier),
                    )

                    if t["id"] == player_team_id:
                        results["season_payouts"].append(
                            {"team": t["name"], "position": pos, "payout": payout, "tier": tier}
                        )

            # Record Driver Season History across all 5 tiers
            for tier, drivers_list in data.get("driver_standings", {}).items():
                for pos_idx, d in enumerate(drivers_list, 1):
                    d_id = d.get("id")
                    d_name = d.get("name", "Driver")
                    t_id = d.get("team_id")
                    t_name = d.get("team_name", "Team")
                    pts = d.get("points", 0)
                    is_ply = bool(d.get("is_player_driver", 0))
                    is_acad = bool(d.get("is_academy_driver", 0))

                    cur.execute(
                        """
                    SELECT COUNT(*),
                           SUM(CASE WHEN position = 1 THEN 1 ELSE 0 END),
                           SUM(CASE WHEN position <= 3 THEN 1 ELSE 0 END)
                    FROM series_race_results
                    WHERE (driver_id = ? OR driver_name = ?) AND season_num = ? AND tier = ?;
                    """,
                        (d_id, d_name, season_num, tier),
                    )
                    stat_row = cur.fetchone()
                    starts = stat_row[0] if stat_row and stat_row[0] else 0
                    wins = stat_row[1] if stat_row and stat_row[1] else 0
                    pods = stat_row[2] if stat_row and stat_row[2] else 0

                    cur.execute(
                        """
                    INSERT INTO driver_season_history (
                        driver_id, driver_name, team_id, team_name, tier, season_num,
                        championship_position, points, race_starts, wins, podiums,
                        is_player_driver, is_academy_driver
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                        (
                            d_id,
                            d_name,
                            t_id,
                            t_name,
                            tier,
                            season_num,
                            pos_idx,
                            pts,
                            starts,
                            wins,
                            pods,
                            is_ply,
                            is_acad,
                        ),
                    )

            # 2. Award Drivers' Championship Ratings & Champion Mood for player's tier (and other tiers)
            for tier, champ in data["driver_champions"].items():
                if champ and champ.get("id"):
                    d_id = champ["id"]
                    is_ply = champ.get("is_player_champion")

                    if tier in [1, 2, 3]:
                        new_pace = min(99, int(champ.get("pace", 75)) + 2)
                        new_cons = min(99, int(champ.get("consistency", 75)) + 2)
                        new_def = min(99, int(champ.get("defending", 75)) + 2)
                        new_mkt = min(99, int(champ.get("marketability", 75)) + 12)
                        titles = int(champ.get("champion_titles", 0)) + 1

                        cur.execute(
                            """
                        UPDATE drivers 
                        SET morale = 100.0,
                            is_champion = 1,
                            champion_titles = ?,
                            champion_mood = 'WORLD_CHAMPION',
                            pace = ?,
                            consistency = ?,
                            defending = ?,
                            marketability = ?
                        WHERE id = ?;
                        """,
                            (titles, new_pace, new_cons, new_def, new_mkt, d_id),
                        )

                        if is_ply:
                            royalty_awarded = 2500000.0
                            cur.execute(
                                "UPDATE teams SET cash = cash + ?, reputation = MIN(100, reputation + 8) WHERE id = ?;",
                                (royalty_awarded, player_team_id),
                            )
                            cur.execute(
                                """
                            INSERT INTO ledger (team_id, week, category, description, amount)
                            VALUES (?, 18, 'SPONSOR', ?, ?);
                            """,
                                (
                                    player_team_id,
                                    f"Driver Championship Merchandising Royalty ({champ['name']})",
                                    royalty_awarded,
                                ),
                            )

                        if tier == player_tier:
                            results["driver_champion_awarded"] = champ
                    else:
                        # Feeder Series Championship (Tier 4 or Tier 5)
                        # Big stat boost for young driver
                        new_pace = min(99, int(champ.get("pace", 65)) + 5)
                        new_braking = min(99, int(champ.get("braking", 65)) + 4)
                        new_cons = min(99, int(champ.get("consistency", 65)) + 4)
                        new_def = min(99, int(champ.get("defending", 65)) + 4)
                        new_mkt = min(99, int(champ.get("marketability", 60)) + 15)
                        titles = int(champ.get("champion_titles", 0)) + 1

                        cur.execute(
                            """
                        UPDATE drivers 
                        SET morale = 100.0,
                            is_champion = 1,
                            champion_titles = ?,
                            champion_mood = 'FEEDER_CHAMPION',
                            pace = ?,
                            braking = ?,
                            consistency = ?,
                            defending = ?,
                            marketability = ?
                        WHERE id = ?;
                        """,
                            (titles, new_pace, new_braking, new_cons, new_def, new_mkt, d_id),
                        )

                        if is_ply or champ.get("is_academy_driver"):
                            # Pure driver prize bonus (Tier 5: $10k, Tier 4: $25k) and marketing reputation for the team
                            pz = champ.get("prize_money", 25000.0 if tier == 4 else 10000.0)
                            rep_gain = champ.get("reputation_boost", 5 if tier == 4 else 3)
                            cur.execute(
                                "UPDATE teams SET cash = cash + ?, reputation = MIN(100, reputation + ?) WHERE id = ?;",
                                (pz, rep_gain, player_team_id),
                            )
                            cur.execute(
                                """
                            INSERT INTO ledger (team_id, week, category, description, amount)
                            VALUES (?, 18, 'PRIZE_MONEY', ?, ?);
                            """,
                                (
                                    player_team_id,
                                    f"Academy Feeder Series T{tier} Champion Driver Bonus ({champ['name']})",
                                    pz,
                                ),
                            )

                            # Forced graduation if old enough
                            driver_age = int(champ.get("age", 15))
                            graduated = False
                            target_tier = tier
                            if tier == 5 and driver_age >= 16:
                                graduated = True
                                target_tier = 4
                            elif tier == 4 and driver_age >= 18:
                                graduated = True
                                target_tier = 3

                            if graduated:
                                cur.execute(
                                    """
                                UPDATE drivers
                                SET academy_tier_placement = ?,
                                    academy_team_name = 'Graduated Ready',
                                    academy_seat_rating = 4,
                                    academy_seat_expected_pos = 'P1 - P3'
                                WHERE id = ?;
                                """,
                                    (target_tier, d_id),
                                )

                            results["academy_champions_awarded"].append(
                                {
                                    "driver_id": d_id,
                                    "name": champ["name"],
                                    "tier": tier,
                                    "prize_money": pz,
                                    "reputation_boost": rep_gain,
                                    "graduated": graduated,
                                    "target_tier": target_tier,
                                }
                            )

            # 3. Promotion & Relegation Execution
            # Determine Tier 2 <-> Tier 3
            t3_p1 = data["candidates"]["t3_p1"]
            t3_p2 = data["candidates"]["t3_p2"]
            t2_last = data["candidates"]["t2_p10"]

            promoted_t3 = None
            if t3_p1:
                if t3_p1["id"] == player_team_id:
                    promoted_t3 = t3_p1 if player_choice_promote else t3_p2
                else:
                    promoted_t3 = t3_p1

            if promoted_t3 and t2_last:
                cur.execute(
                    "UPDATE teams SET tier = 2, is_relegated_titan = 0, relegated_rnd_boost = 1.0 WHERE id = ?;",
                    (promoted_t3["id"],),
                )
                # Relegated titan starts with adapted parts and aggressive development drive
                cur.execute(
                    "UPDATE teams SET tier = 3, is_relegated_titan = 1, relegated_rnd_boost = 1.4 WHERE id = ?;",
                    (t2_last["id"],),
                )
                results["promotions"].append(
                    {
                        "team": promoted_t3["name"],
                        "from_tier": 3,
                        "to_tier": 2,
                        "is_player": (promoted_t3["id"] == player_team_id),
                    }
                )
                results["relegations"].append(
                    {
                        "team": t2_last["name"],
                        "from_tier": 2,
                        "to_tier": 3,
                        "is_player": (t2_last["id"] == player_team_id),
                    }
                )

                if promoted_t3["id"] == player_team_id:
                    results["new_player_tier"] = 2
                elif t2_last["id"] == player_team_id:
                    results["new_player_tier"] = 3

                # Reset promoted team components to Tier 2 baseline specs (Regulation Change)
                from .engineering_manager import FACTORY_PART_SPECS

                t2_specs = FACTORY_PART_SPECS[2]
                for cat, spec in t2_specs.items():
                    cur.execute(
                        """
                    UPDATE car_components 
                    SET generation = 1, performance = ?, max_durability = ?, current_durability = ?, wear_pct = 0.0,
                        knowledge_min = 0.0, knowledge_max = 0.0, rel_knowledge_min = 0.0, rel_knowledge_max = 0.0, races_on_concept = 0
                    WHERE team_id = ? AND category = ?;
                    """,
                        (spec["perf"], spec["durability"], spec["durability"], promoted_t3["id"], cat),
                    )

                # Adapt relegated team's components: starts slightly behind on setup (~72.0 vs 75.0 baseline) but with aggressive R&D!
                cur.execute(
                    """
                UPDATE car_components 
                SET generation = 1, performance = 72.0, max_durability = 65.0, current_durability = 65.0, wear_pct = 0.0,
                    knowledge_min = 0.0, knowledge_max = 0.0, rel_knowledge_min = 0.0, rel_knowledge_max = 0.0, races_on_concept = 0
                WHERE team_id = ? AND car_slot IN (1, 2);
                """,
                    (t2_last["id"],),
                )

                # Sponsor Escalator Adjustment: Active contracts promote with the team
                # T3 (1.0x) -> T2 (2.2x): Gap is 2.2x. Existing sponsors escalate by 2.2 * 0.85 = ~1.87x (discount vs fresh T2 contracts)
                escalator_mult = (2.2 / 1.0) * 0.85
                cur.execute(
                    """
                UPDATE active_sponsors 
                SET per_race_payment = round(per_race_payment * ?, -3),
                    target_bonus = round(target_bonus * ?, -3)
                WHERE team_id = ?;
                """,
                    (escalator_mult, escalator_mult, promoted_t3["id"]),
                )

            # Determine Tier 1 <-> Tier 2
            t2_p1 = data["candidates"]["t2_p1"]
            t2_p2 = data["candidates"]["t2_p2"]
            t1_last = data["candidates"]["t1_p10"]

            promoted_t2 = None
            if t2_p1:
                if t2_p1["id"] == player_team_id:
                    promoted_t2 = t2_p1 if player_choice_promote else t2_p2
                else:
                    promoted_t2 = t2_p1

            if promoted_t2 and t1_last:
                cur.execute(
                    "UPDATE teams SET tier = 1, is_relegated_titan = 0, relegated_rnd_boost = 1.0 WHERE id = ?;",
                    (promoted_t2["id"],),
                )
                cur.execute(
                    "UPDATE teams SET tier = 2, is_relegated_titan = 1, relegated_rnd_boost = 1.4 WHERE id = ?;",
                    (t1_last["id"],),
                )
                results["promotions"].append(
                    {
                        "team": promoted_t2["name"],
                        "from_tier": 2,
                        "to_tier": 1,
                        "is_player": (promoted_t2["id"] == player_team_id),
                    }
                )
                results["relegations"].append(
                    {
                        "team": t1_last["name"],
                        "from_tier": 1,
                        "to_tier": 2,
                        "is_player": (t1_last["id"] == player_team_id),
                    }
                )

                if promoted_t2["id"] == player_team_id:
                    results["new_player_tier"] = 1
                elif t1_last["id"] == player_team_id:
                    results["new_player_tier"] = 2

                # Reset promoted team components to Tier 1 baseline specs (Regulation Change)
                from .engineering_manager import FACTORY_PART_SPECS

                t1_specs = FACTORY_PART_SPECS[1]
                for cat, spec in t1_specs.items():
                    cur.execute(
                        """
                    UPDATE car_components 
                    SET generation = 1, performance = ?, max_durability = ?, current_durability = ?, wear_pct = 0.0,
                        knowledge_min = 0.0, knowledge_max = 0.0, rel_knowledge_min = 0.0, rel_knowledge_max = 0.0, races_on_concept = 0
                    WHERE team_id = ? AND category = ?;
                    """,
                        (spec["perf"], spec["durability"], spec["durability"], promoted_t2["id"], cat),
                    )

                # Adapt relegated T1 team components to Tier 2 adapted baseline
                cur.execute(
                    """
                UPDATE car_components 
                SET generation = 1, performance = 92.0, max_durability = 72.0, current_durability = 72.0, wear_pct = 0.0,
                    knowledge_min = 0.0, knowledge_max = 0.0, rel_knowledge_min = 0.0, rel_knowledge_max = 0.0, races_on_concept = 0
                WHERE team_id = ? AND car_slot IN (1, 2);
                """,
                    (t1_last["id"],),
                )

                # Sponsor Escalator Adjustment: T2 (2.2x) -> T1 (5.0x): Gap is 2.27x. Existing sponsors escalate by 2.27 * 0.85 = ~1.93x
                escalator_mult_t1 = (5.0 / 2.2) * 0.85
                cur.execute(
                    """
                UPDATE active_sponsors 
                SET per_race_payment = round(per_race_payment * ?, -3),
                    target_bonus = round(target_bonus * ?, -3)
                WHERE team_id = ?;
                """,
                    (escalator_mult_t1, escalator_mult_t1, promoted_t2["id"]),
                )

            # Reset points and calendar for next season
            cur.execute("UPDATE teams SET points = 0;")
            cur.execute("UPDATE drivers SET points = 0, age = age + 1;")
            cur.execute("UPDATE calendar SET is_completed = 0;")
            # Ensure fresh series_race_results for incoming season
            cur.execute("DELETE FROM series_race_results WHERE season_num = ?;", (season_num + 1,))
            # Reset part wear & restore durability across all teams
            cur.execute("UPDATE car_components SET wear_pct = 0.0, current_durability = max_durability;")
            # Reset engine contract races left to 10
            cur.execute("UPDATE teams SET engine_contract_races_left = 10, engine_locked_for_season = 1;")

            conn.commit()

        # 4. Sign Next Season Engine Supplier for Player Team
        from .engineering_manager import EngineeringManager

        em = EngineeringManager(self.db)
        if selected_engine:
            success, msg = em.set_engine_supplier(player_team_id, selected_engine, force_new_season=True)
            results["engine_signed"] = selected_engine if success else msg

        # 5. Apply Technical Regulations and Chassis Next-Gen Rollover across all playable tiers
        reg_results = {}
        for tier_num in [1, 2, 3]:
            reg_results[tier_num] = em.apply_season_rollover_regulations(tier_num, season_num=season_num)
        results["regulations"] = reg_results

        return results

    def process_season_finale_promotion_relegation(self, prize_cash_multiplier: float = 1.0) -> Dict[str, Any]:
        """Backward-compatible wrapper for automated execution."""
        player = self.db.get_player_team()
        p_id = player.get("id", 21)
        return self.commit_season_finale(
            player_team_id=p_id, player_choice_promote=True, prize_cash_multiplier=prize_cash_multiplier
        )

    def _process_ai_in_season_development(self, cur: sqlite3.Cursor, tier: int, round_num: int) -> None:
        """
        Simulates intra-season AI constructor R&D packages:
        - Only runs in playable leagues (Tiers 1, 2, 3); Tiers 4 & 5 are spec feeder leagues.
        - Triggers every 2-3 rounds (rounds 3, 5, 8, 11, 14).
        - AI teams invest capital into allowed custom parts based on archetype / difficulty:
          * TECH_TITAN: Aggressive development (+3.0 to +6.0 pts, small reliability risk)
          * BALANCED: Steady development (+2.0 to +4.0 pts, high reliability)
          * DRIVER_SCOUT: Minimal car development (+0.8 to +1.8 pts)
          * HOARDER: Saves cash (+0 pts)
          * HIGH_ROLLER: Extreme risk (+4.0 to +8.5 pts, -3% reliability)
        - Respects allowed custom parts per tier (T3: Brakes & Front Wing only; T2: 5 parts; T1: 7 parts).
        - Respects the 3.0x tier baseline performance cap.
        - Deducts build costs from AI cash reserves.
        """
        if tier not in [1, 2, 3]:
            return

        # Trigger on scheduled development rounds (every ~3 rounds)
        if round_num not in [3, 6, 9, 12, 15]:
            return

        allowed_cats = {
            3: ["BRAKES", "FRONT_WING"],
            2: ["BRAKES", "FRONT_WING", "REAR_WING", "SUSPENSION", "ENGINE"],
            1: ["BRAKES", "FRONT_WING", "REAR_WING", "SUSPENSION", "ENGINE", "FLOOR", "ERS"],
        }.get(tier, [])

        if not allowed_cats:
            return

        cur.execute(
            """
        SELECT id, name, difficulty, cash, is_relegated_titan 
        FROM teams 
        WHERE tier = ? AND is_player = 0;
        """,
            (tier,),
        )
        ai_teams = [dict(r) for r in cur.fetchall()]

        from ..data.balance_config import BALANCE_REGISTRY
        from .engineering_manager import FACTORY_PART_SPECS

        tier_specs = FACTORY_PART_SPECS.get(tier, FACTORY_PART_SPECS[3])

        for t in ai_teams:
            t_id = t["id"]
            cash = float(t["cash"])
            arch = t.get("difficulty") or "BALANCED"
            is_titan = bool(t.get("is_relegated_titan", 0))

            if arch == "HOARDER" and not is_titan:
                continue

            # Pick 1 random allowed component to upgrade (TECH_TITAN / Titan may upgrade 2)
            num_updates = 2 if (arch in ["TECH_TITAN", "HIGH_ROLLER"] or is_titan) else 1
            chosen_cats = random.sample(allowed_cats, min(num_updates, len(allowed_cats)))

            for cat in chosen_cats:
                part_cost = BALANCE_REGISTRY.get_part_build_cost(tier, cat) * 0.75
                if cash < part_cost:
                    continue

                cur.execute(
                    """
                SELECT id, performance, reliability 
                FROM car_components 
                WHERE team_id = ? AND category = ? AND car_slot IN (1, 2);
                """,
                    (t_id, cat),
                )
                comp_rows = cur.fetchall()
                if not comp_rows:
                    continue

                base_perf = tier_specs.get(cat, {}).get("perf", 65.0)
                max_perf = base_perf * 3.0

                if arch == "TECH_TITAN" or is_titan:
                    gain = random.uniform(3.0, 5.5)
                    rel_delta = random.uniform(-1.0, 1.0)
                elif arch == "HIGH_ROLLER":
                    gain = random.uniform(3.5, 7.5)
                    rel_delta = random.uniform(-3.0, 0.5)
                elif arch == "DRIVER_SCOUT":
                    gain = random.uniform(0.8, 1.6)
                    rel_delta = random.uniform(0.5, 1.5)
                else:  # BALANCED
                    gain = random.uniform(1.8, 3.5)
                    rel_delta = random.uniform(0.0, 1.2)

                for c in comp_rows:
                    new_perf = min(max_perf, round(float(c["performance"]) + gain, 1))
                    new_rel = max(45.0, min(99.0, round(float(c["reliability"]) + rel_delta, 1)))
                    cur.execute(
                        """
                    UPDATE car_components 
                    SET performance = ?, reliability = ? 
                    WHERE id = ?;
                    """,
                        (new_perf, new_rel, c["id"]),
                    )

                # Deduct cost from team cash
                cash -= part_cost
                cur.execute("UPDATE teams SET cash = ? WHERE id = ?;", (cash, t_id))
