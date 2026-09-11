import os
import random
from typing import Dict, List, Optional, Any, Tuple
from ..database.career_db import CareerDatabase
from src.management.staff_manager import StaffManager
from src.management.engineering_manager import EngineeringManager

class GameManager:
    """Central career orchestrator managing turns, calendars, seasons, and progression."""

    def __init__(self, db: Any = "career.db"):
        if isinstance(db, str):
            self.db = CareerDatabase(db)
        else:
            self.db = db
        self.staff_manager = StaffManager(self.db)
        self.engineering_manager = EngineeringManager(self.db)
        self.current_week = 1
        self.total_season_weeks = 18
        self.current_round = 1
        self.player_team = {}
        self.team_id = 21 # Horizon Racing default Player Team (Tier 3)
        self.player_tier = 3
        self.total_rounds = 7
        self.refresh_player_team()

    def refresh_player_team(self):
        """Loads latest player team record, updates round counts, and syncs calendar."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM teams WHERE is_player = 1 LIMIT 1;")
            row = cur.fetchone()
            if row:
                self.player_team = dict(row)
                self.team_id = self.player_team["id"]
                self.player_tier = self.player_team.get("tier", 3)
                tier_rounds = self.db.get_total_rounds_for_tier(self.player_tier)
                if tier_rounds > 0:
                    self.total_rounds = tier_rounds

            # Sync current round from uncompleted calendar rounds
            cur.execute("""
            SELECT round FROM calendar 
            WHERE tier = ? AND is_completed = 0 
            ORDER BY round ASC LIMIT 1;
            """, (self.player_tier,))
            r_row = cur.fetchone()
            if r_row:
                self.current_round = r_row[0]
            else:
                self.current_round = self.total_rounds

    def get_financial_summary(self) -> Dict[str, Any]:
        """Calculates exact monthly burn rate, payroll, facility upkeeps, and net balance."""
        self.refresh_player_team()
        team_id = self.team_id
        
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            
            # 1. Calculate Facility Sub-Budgets & Operational Costs
            cur.execute("""
            SELECT tf.node_id, tf.current_tier, tf.monthly_sub_budget, fn.base_upkeep
            FROM team_facilities tf
            JOIN facility_nodes fn ON tf.node_id = fn.id
            WHERE tf.team_id = ? AND tf.is_unlocked = 1;
            """, (team_id,))
            fac_rows = cur.fetchall()

            facility_budgets_total = 0.0
            facility_upkeeps_total = 0.0
            equipment_upkeeps_total = 0.0
            facility_staff_wages_total = 0.0

            for f_node, f_tier, f_sub_budget, f_base_upkeep in fac_rows:
                # Facility base upkeep
                f_upk = float(f_base_upkeep) * int(f_tier)
                facility_upkeeps_total += f_upk

                # Equipment upkeep in this facility
                cur.execute("""
                SELECT SUM(fe.base_upkeep * te.current_level)
                FROM facility_equipment fe
                JOIN team_equipment te ON fe.id = te.equipment_id
                WHERE te.team_id = ? AND fe.node_id = ? AND te.is_active = 1;
                """, (team_id, f_node))
                eq_res = cur.fetchone()[0]
                eq_upk = float(eq_res) if eq_res else 0.0
                equipment_upkeeps_total += eq_upk

                # Staff & Head salaries assigned to this facility
                cur.execute("""
                SELECT SUM(salary_monthly) FROM personnel
                WHERE team_id = ? AND facility_node_id = ?;
                """, (team_id, f_node))
                w_res = cur.fetchone()[0]
                f_wages = float(w_res) if w_res else 0.0
                facility_staff_wages_total += f_wages

                min_op_cost = f_upk + eq_upk + f_wages
                eff_budget = max(min_op_cost, float(f_sub_budget or 0.0))
                facility_budgets_total += eff_budget

            # 2. Unassigned Personnel (Category Directors, unassigned free agents)
            cur.execute("""
            SELECT SUM(salary_monthly) FROM personnel
            WHERE team_id = ? AND (facility_node_id IS NULL OR facility_node_id = '');
            """, (team_id,))
            unassigned_res = cur.fetchone()[0]
            unassigned_payroll = float(unassigned_res) if unassigned_res else 0.0

            total_payroll = facility_staff_wages_total + unassigned_payroll

            # 3. Driver Salaries (converted to monthly ~ 2 races/mo)
            cur.execute("SELECT SUM(salary_per_race) FROM drivers WHERE team_id = ? AND is_academy_driver = 0;", (team_id,))
            driver_salaries = float(cur.fetchone()[0] or 0.0) * 2.0

            # 4. Academy Feeder Subsidies
            cur.execute("""
            SELECT academy_tier_placement FROM drivers 
            WHERE team_id = ? AND is_academy_driver = 1 AND academy_tier_placement IS NOT NULL;
            """, (team_id,))
            academy_rows = cur.fetchall()
            tier_costs = {3: 95000, 4: 55000, 5: 25000}
            academy_cost = sum(tier_costs.get(r[0], 25000) for r in academy_rows)

            # Total monthly operational burn rate (exact sum of facility budgets + unassigned staff + drivers + academy)
            total_monthly_burn = facility_budgets_total + unassigned_payroll + driver_salaries + academy_cost

            # 5. Sponsor Baseline Revenue + Driver Sponsorship / Loan Stipend
            tier = self.player_team.get("tier", 3)
            # Calibrated baseline monthly retainer:
            # Tier 3 ($260k/mo = $3.12M/yr). With starter payroll ~$380k/mo ($4.56M/yr),
            # an inactive/losing team loses ~$1.4M/yr without race performance bonuses or sponsors.
            base_sponsor_rev = {1: 3200000, 2: 1100000, 3: 260000, 4: 80000, 5: 25000}[tier]
            
            cur.execute("SELECT SUM(sponsor_income_per_race) FROM drivers WHERE team_id = ? AND is_academy_driver = 0;", (team_id,))
            driver_sponsor_income = float(cur.fetchone()[0] or 0.0) * 2.0 # 2 races per month
            total_sponsor_rev = base_sponsor_rev + driver_sponsor_income

            # 6. Commercial Passive Revenue (Merchandise, Fan Club, Licensing, Museum, Customer Racing)
            cur.execute("""
            SELECT node_id, current_tier FROM team_facilities 
            WHERE team_id = ? AND is_unlocked = 1 AND node_id IN ('mkt_merch', 'mkt_fan_club', 'mkt_licensing', 'mkt_heritage', 'mkt_customer_racing');
            """, (team_id,))
            comm_facs = {r[0]: r[1] for r in cur.fetchall()}

            # Calculate Team Performance Multiplier (Championship standing & recent finishes)
            cur.execute("SELECT AVG(finish_position) FROM race_history WHERE team_id = ? ORDER BY id DESC LIMIT 5;", (team_id,))
            rh_row = cur.fetchone()
            cur.execute("SELECT championship_position FROM season_history WHERE team_id = ? ORDER BY id DESC LIMIT 1;", (team_id,))
            sh_row = cur.fetchone()
            
            recent_pos = rh_row[0] if rh_row and rh_row[0] is not None else (sh_row[0] if sh_row else 10.0)
            perf_factor = max(0.15, min(1.35, 1.45 - float(recent_pos) * 0.10))
            tier_econ = {1: 1.0, 2: 0.65, 3: 0.4, 4: 0.2, 5: 0.08}.get(tier, 0.4)

            merch_rev = 0.0
            if "mkt_merch" in comm_facs:
                m_tier = comm_facs["mkt_merch"]
                merch_rev = 12000.0 * m_tier * perf_factor * tier_econ

            fan_club_rev = 0.0
            if "mkt_fan_club" in comm_facs:
                fc_tier = comm_facs["mkt_fan_club"]
                cur.execute("SELECT AVG(marketability) FROM drivers WHERE team_id = ? AND is_academy_driver = 0;", (team_id,))
                mkt_avg = float(cur.fetchone()[0] or 50.0)
                fan_club_rev = 10000.0 * fc_tier * perf_factor * tier_econ * (mkt_avg / 50.0)

            licensing_rev = 0.0
            if "mkt_licensing" in comm_facs:
                lic_tier = comm_facs["mkt_licensing"]
                rep = float(self.player_team.get("reputation", 50.0))
                licensing_rev = 8000.0 * lic_tier * perf_factor * tier_econ * (rep / 50.0)

            museum_rev = 0.0
            if "mkt_heritage" in comm_facs:
                mus_tier = comm_facs["mkt_heritage"]
                cur.execute("SELECT COUNT(*) FROM season_history WHERE team_id = ? AND championship_position = 1;", (team_id,))
                titles_won = int(cur.fetchone()[0] or 0)
                museum_rev = (8000.0 + titles_won * 10000.0) * mus_tier * max(0.5, perf_factor) * tier_econ

            customer_racing_rev = 0.0
            if "mkt_customer_racing" in comm_facs:
                cr_tier = comm_facs["mkt_customer_racing"]
                customer_racing_rev = 25000.0 * cr_tier * perf_factor * tier_econ

            commercial_rev = merch_rev + fan_club_rev + licensing_rev + museum_rev + customer_racing_rev

            net_monthly = total_sponsor_rev + commercial_rev - total_monthly_burn

            return {
                "cash": self.player_team.get("cash", 0.0),
                "payroll": total_payroll,
                "unassigned_payroll": unassigned_payroll,
                "facility_staff_wages": facility_staff_wages_total,
                "driver_salaries": driver_salaries,
                "driver_sponsor_income": driver_sponsor_income,
                "academy_cost": academy_cost,
                "facility_upkeep": facility_upkeeps_total,
                "equipment_upkeep": equipment_upkeeps_total,
                "sub_budgets": facility_budgets_total,
                "sponsor_revenue": total_sponsor_rev,
                "commercial_revenue": commercial_rev,
                "merch_revenue": merch_rev,
                "fan_club_revenue": fan_club_rev,
                "licensing_revenue": licensing_rev,
                "museum_revenue": museum_rev,
                "customer_racing_revenue": customer_racing_rev,
                "total_monthly_burn": total_monthly_burn,
                "net_monthly": net_monthly,
                "staff_count": self.db.get_team_staff_count(team_id)
            }



    def process_weekly_cycle(self):
        """Advances career by 1 week, deducting weekly pro-rated costs, advancing personnel, and advancing R&D."""
        self.current_week += 1
        summary = self.get_financial_summary()
        weekly_net = summary["net_monthly"] / 4.0
        new_cash = summary["cash"] + weekly_net

        # Advance Personnel Engine (internships, aging, wage demands, applications)
        self.staff_manager.advance_weekly_personnel(self.team_id)

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE teams SET cash = ? WHERE id = ?;", (new_cash, self.team_id))
            
            # Log ledger
            cur.execute("""
            INSERT INTO ledger (team_id, week, category, description, amount)
            VALUES (?, ?, 'PAYROLL', 'Weekly Net Operational Cash Flow', ?);
            """, (self.team_id, self.current_week, weekly_net))

            # Fetch all playable teams to advance Next-Gen R&D
            cur.execute("SELECT id, tier, is_player, points, next_gen_rnd_pct FROM teams WHERE tier IN (1, 2, 3);")
            teams = [dict(r) for r in cur.fetchall()]

            for t in teams:
                # If Week 9+ and AI team has 0% allocation, assign realistic tier baseline
                if not t["is_player"] and self.current_week >= 9 and float(t.get("next_gen_rnd_pct", 0.0) or 0.0) == 0.0:
                    ai_alloc = 40.0 if t["points"] >= 20 else 30.0
                    cur.execute("UPDATE teams SET next_gen_rnd_pct = ? WHERE id = ?;", (ai_alloc, t["id"]))

            conn.commit()

        # Advance Next-Gen Chassis R&D for all teams
        for t in teams:
            self.engineering_manager.process_weekly_next_gen_rnd(t["id"], self.current_week)

        # Trigger Week 9 Regulation Evaluations for all 3 playable tiers
        if self.current_week == 9:
            for tier_num in [1, 2, 3]:
                self.engineering_manager.evaluate_season_regulations(tier_num, current_week=9)

        self.refresh_player_team()


    def is_race_week_for_player(self) -> bool:
        """Returns True if the player's tier has a scheduled championship race in current_week."""
        tier = self.player_team.get("tier", self.player_tier)
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM calendar WHERE tier = ? AND week = ? AND is_completed = 0;", (tier, self.current_week))
            return cur.fetchone()[0] > 0

    def get_other_series_racing_this_week(self) -> List[Dict[str, Any]]:
        """Returns metadata for all other series racing in current_week."""
        tier = self.player_team.get("tier", self.player_tier)
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM calendar WHERE week = ? AND tier != ? ORDER BY tier ASC;", (self.current_week, tier))
            return [dict(r) for r in cur.fetchall()]

    def get_current_race_event(self) -> Optional[Dict[str, Any]]:
        """Returns metadata for the championship round scheduled for the player's tier in current_week."""
        tier = self.player_team.get("tier", self.player_tier)
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            # 1. Look for scheduled race this week
            cur.execute("SELECT * FROM calendar WHERE tier = ? AND week = ?;", (tier, self.current_week))
            row = cur.fetchone()
            if row:
                cal = dict(row)
                self.current_round = cal["round"]
                return cal

            # 2. If non-race week, look ahead to the next scheduled upcoming race
            cur.execute("SELECT * FROM calendar WHERE tier = ? AND is_completed = 0 ORDER BY round ASC LIMIT 1;", (tier,))
            row = cur.fetchone()
            if row:
                return dict(row)

            # 3. Fallback to current round
            round_meta = self.db.get_calendar_round(tier, self.current_round)
            if round_meta:
                return round_meta

        return {
            "tier": tier,
            "round": self.current_round,
            "week": self.current_week,
            "track_name": "Grand Prix Round",
            "circuit_file": "emerald_ring.json",
            "total_laps": 15,
            "weather_profile": "DYNAMIC",
            "characteristic": "BALANCED"
        }

    def advance_to_next_race_round(self):
        """Advances to next calendar round if applicable."""
        if self.current_round < self.total_rounds:
            self.current_round += 1

    def advance_calendar_week(self):
        """Advances season by 1 calendar week (up to 18 weeks max)."""
        self.process_weekly_cycle()
        self.refresh_player_team()

    def is_season_finale_ready(self) -> bool:
        """Returns True if all championship rounds for the player's tier are completed or season week limit reached."""
        tier = self.player_team.get("tier", self.player_tier)
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM calendar WHERE tier = ? AND is_completed = 0;", (tier,))
            remaining = cur.fetchone()[0]
            if remaining == 0:
                return True
        return self.current_week >= self.total_season_weeks

    def reset_for_new_season(self):
        """Resets calendar weeks and current round to Week 1, Round 1 for the new season."""
        self.current_week = 1
        self.current_round = 1
        self.refresh_player_team()

