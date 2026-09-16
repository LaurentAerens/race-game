"""
Staff Management Engine for Career Mode.
Implements the 1-to-1 Personnel Hierarchy mapped to the Factory Tech Tree,
including Core Stats, Domain Specialties (+50% bonus), European 6-Month Internships,
Leadership Force Multipliers, Lifelong Bell-Curve Aging (peak ~50, retire 67-77), and Rival Headhunting.
"""

import math
import random
from typing import Any, Dict, List, Optional, Tuple

from src.database.career_db import CORE_SPECIALTIES, FACILITY_SPECIALTY_MAP, FIRST_NAMES, LAST_NAMES, CareerDatabase


class StaffManager:
    """Manages organizational hierarchy, personnel stats, assignments, and weekly progressions."""

    def __init__(self, db: CareerDatabase):
        self.db = db

    def get_team_principal_name(self, team_id: int) -> str:
        """Returns the CEO / Team Principal name for the team."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT principal_name FROM teams WHERE id = ?;", (team_id,))
            row = cur.fetchone()
            return str(row[0]) if row and row[0] else "Alex Mercer"

    def get_category_directors(self, team_id: int) -> Dict[str, Optional[Dict[str, Any]]]:
        """Returns all 7 category director assignments for a team (value is None if vacant)."""
        categories = ["ENGINEERING", "COMMERCIAL", "TRACKSIDE", "POWERTRAIN", "MANUFACTURING", "TESTING", "HR"]
        directors: Dict[str, Optional[Dict[str, Any]]] = {cat: None for cat in categories}

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            SELECT tcd.category, p.*
            FROM team_category_directors tcd
            LEFT JOIN personnel p ON tcd.director_personnel_id = p.id
            WHERE tcd.team_id = ?;
            """,
                (team_id,),
            )
            rows = cur.fetchall()
            for r in rows:
                cat = r["category"]
                if r["id"] is not None:
                    directors[cat] = dict(r)
        return directors

    def get_facility_personnel(self, team_id: int, node_id: str, facility_tier: int = 1) -> Dict[str, Any]:
        """Returns Department Head, Specialists, and Interns assigned to a specific facility node."""
        max_staff_slots = 3 if facility_tier == 1 else (6 if facility_tier == 2 else 10)

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            SELECT * FROM personnel
            WHERE team_id = ? AND facility_node_id = ?
            ORDER BY 
                CASE role_type 
                    WHEN 'DEPARTMENT_HEAD' THEN 1 
                    WHEN 'STAFF' THEN 2 
                    WHEN 'INTERN' THEN 3 
                    ELSE 4 
                END ASC,
                (stat_engineering + stat_craftsmanship + stat_leadership) DESC;
            """,
                (team_id, node_id),
            )
            rows = [dict(r) for r in cur.fetchall()]

        head = None
        staff = []
        intern = None

        for p in rows:
            if p["role_type"] == "DEPARTMENT_HEAD" and head is None:
                head = p
            elif p["role_type"] == "STAFF":
                staff.append(p)
            elif p["role_type"] == "INTERN" and intern is None:
                intern = p

        vacant_slots = max(0, max_staff_slots - len(staff))
        fac_spec = FACILITY_SPECIALTY_MAP.get(node_id, "COMPOSITES")

        return {
            "node_id": node_id,
            "facility_tier": facility_tier,
            "target_specialty": fac_spec,
            "head": head,
            "staff": staff,
            "intern": intern,
            "max_staff_slots": max_staff_slots,
            "active_staff_count": len(staff),
            "vacant_staff_slots": vacant_slots,
            "is_head_vacant": head is None,
        }

    def calculate_facility_staff_output(
        self, team_id: int, node_id: str, facility_tier: int = 1, dev_gain_mult: float = 1.0
    ) -> Dict[str, Any]:
        """
        Calculates effective personnel multiplier (0.0 to 5.0x) for a facility node.
        Includes:
        - Slot-by-slot diminishing returns (1st engineer > 4th-5th engineer).
        - Diminishing returns mitigation buffer when team Communication and Head Leadership are high.
        - Primary domain stats and matching Domain Specialty (+50% bonus).
        - Composure factor (0.90 to 1.10x) and Morale scaling.
        - Dual-attribute Department Head force multiplier (Leadership + Relevant Domain Skill + Specialty).
        - Category Director division synergy (Leadership + Core Skill).
        - Bounded strictly between 0.0 and 5.0x maximum.
        """
        fac_data = self.get_facility_personnel(team_id, node_id, facility_tier)
        head = fac_data["head"]
        staff_list = fac_data["staff"]
        intern = fac_data["intern"]
        target_spec = fac_data["target_specialty"]

        # 1. Determine relevant primary stats based on facility node
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT department FROM facility_nodes WHERE id = ?;", (node_id,))
            dep_row = cur.fetchone()
            dep = dep_row[0] if dep_row else "ENGINEERING"

            # Fetch Category Director for this category
            cur.execute(
                """
            SELECT p.* FROM team_category_directors tcd
            JOIN personnel p ON tcd.director_personnel_id = p.id
            WHERE tcd.team_id = ? AND tcd.category = ?;
            """,
                (team_id, dep),
            )
            dir_row = cur.fetchone()
            director = dict(dir_row) if dir_row else None

            # Fetch Executive Boardroom (Management) tier and equipment for factory-wide leadership aura
            cur.execute(
                """
            SELECT current_tier, is_unlocked FROM team_facilities
            WHERE team_id = ? AND node_id = 'mgmt_boardroom';
            """,
                (team_id,),
            )
            mgmt_row = cur.fetchone()
            mgmt_tier = mgmt_row[0] if (mgmt_row and mgmt_row[1]) else 0

            mgmt_lead_bonus = float(mgmt_tier) * 5.0
            cur.execute(
                """
            SELECT te.equipment_id, te.current_level
            FROM team_equipment te
            JOIN facility_equipment fe ON te.equipment_id = fe.id
            WHERE te.team_id = ? AND fe.node_id = 'mgmt_boardroom' AND te.is_active = 1;
            """,
                (team_id,),
            )
            for eq_id, eq_lvl in cur.fetchall():
                if eq_id == "eq_mgmt_strategy_war_room":
                    mgmt_lead_bonus += eq_lvl * 1.5
                elif eq_id == "eq_mgmt_exec_telemetry":
                    mgmt_lead_bonus += eq_lvl * 1.0
                elif eq_id == "eq_mgmt_board_display":
                    mgmt_lead_bonus += eq_lvl * 1.5

        # If completely unstaffed (0 staff, 0 head, 0 intern) -> staff_mult is 0.0!
        if not staff_list and not head and not intern:
            return {
                "node_id": node_id,
                "department": dep,
                "target_specialty": target_spec,
                "staff_mult": 0.0,
                "raw_staff_score": 0.0,
                "head_mult": 1.0,
                "head_status": "VACANT (Unsupervised Mode)",
                "dir_mult": 0.90 if not director else 1.0,
                "dir_status": "VACANT (Coordination Drag: -10%)" if not director else "Active",
                "final_perf": 0.0,
                "final_rel": 0.0,
                "staff_count": 0,
                "staff_details": [],
                "has_intern": False,
                "is_unstaffed": True,
                "coordination_rating": 0.0,
                "diminishing_exponent": 0.50,
                "mgmt_lead_bonus": mgmt_lead_bonus,
            }

        # 2. Coordination & Diminishing Returns Buffer Calculation (Universal Leadership Aura)
        base_head_lead = head.get("stat_leadership", 30.0) if head else 30.0
        head_leadership = min(100.0, base_head_lead + mgmt_lead_bonus)
        if staff_list:
            avg_comm = sum(s.get("stat_communication", 40.0) for s in staff_list) / len(staff_list)
            avg_staff_lead = sum(
                min(100.0, s.get("stat_leadership", 30.0) + mgmt_lead_bonus) for s in staff_list
            ) / len(staff_list)
        else:
            avg_comm = 40.0
            avg_staff_lead = min(100.0, 30.0 + mgmt_lead_bonus)

        # Coordination Rating: higher head leadership + staff leadership + communication reduces diminishing returns drag
        coordination_rating = max(
            0.15, min(1.0, (head_leadership * 0.45 + avg_staff_lead * 0.20 + avg_comm * 0.35) / 100.0)
        )
        # Drag exponent gamma: 0.55 (poor comm/lead -> heavy drag) down to 0.15 (elite comm/lead -> near-linear)
        gamma = 0.55 - 0.40 * coordination_rating

        # 3. Individual Specialist Capability Calculation
        staff_details = []
        mentor_id = intern.get("intern_mentor_id") if intern else None

        scored_staff = []
        for s in staff_list:
            if dep in ["ENGINEERING", "POWERTRAIN"]:
                primary_stat = s.get("stat_engineering", 40.0)
            elif dep in ["MANUFACTURING", "TESTING", "TRACKSIDE"]:
                primary_stat = s.get("stat_craftsmanship", 40.0)
            elif dep in ["COMMERCIAL"]:
                primary_stat = s.get("stat_marketing", 40.0)
            else:
                primary_stat = s.get("stat_communication", 40.0)

            # Specialty Matching Bonus (+50%)
            has_matching_spec = s.get("specialty") == target_spec
            spec_mult = 1.50 if has_matching_spec else 1.00

            # Mentor Guidance Penalty (-15% on mentor output)
            is_mentoring = s.get("id") == mentor_id
            mentor_penalty = 0.85 if is_mentoring else 1.00
            eff_stat = primary_stat * spec_mult * mentor_penalty

            # Composure Factor (0.90 to 1.10x consistency/error buffer)
            composure_factor = 0.90 + (s.get("stat_composure", 50.0) / 100.0) * 0.20

            # Morale Factor (0.40 to 1.15x)
            morale_factor = max(0.40, min(1.15, s.get("morale", 85.0) / 100.0))

            base_spec_score = (eff_stat / 100.0) * composure_factor * morale_factor

            scored_staff.append(
                {
                    "raw_obj": s,
                    "id": s.get("id"),
                    "name": s.get("name"),
                    "specialty": s.get("specialty"),
                    "has_matching_spec": has_matching_spec,
                    "is_mentoring": is_mentoring,
                    "primary_stat": primary_stat,
                    "eff_stat": eff_stat,
                    "base_score": base_spec_score,
                }
            )

        # Sort staff by base_score descending so top talent occupies the highest-yield initial slots
        scored_staff.sort(key=lambda item: item["base_score"], reverse=True)

        # 4. Slot-by-Slot Diminishing Weight Application
        raw_staff_score = 0.0
        for slot_idx, item in enumerate(scored_staff, start=1):
            slot_weight = 1.0 / (slot_idx**gamma)
            eff_score = item["base_score"] * slot_weight
            raw_staff_score += eff_score
            staff_details.append(
                {
                    "id": item["id"],
                    "name": item["name"],
                    "specialty": item["specialty"],
                    "has_matching_spec": item["has_matching_spec"],
                    "is_mentoring": item["is_mentoring"],
                    "primary_stat": item["primary_stat"],
                    "eff_stat": item["eff_stat"],
                    "slot_idx": slot_idx,
                    "slot_weight": slot_weight,
                    "score": eff_score,
                }
            )

        # 5. European 6-Month Intern Tryout contribution
        if intern:
            intern_morale = max(0.5, min(1.1, intern.get("morale", 85.0) / 100.0))
            raw_staff_score += 0.25 * intern_morale

        # If only head is present with no staff yet: head works directly in lab
        if not staff_list and head:
            head_primary = (
                head.get("stat_engineering", 50.0)
                if dep in ["ENGINEERING", "POWERTRAIN"]
                else head.get("stat_craftsmanship", 50.0)
            )
            head_spec_match = head.get("specialty") == target_spec
            head_eff_primary = head_primary * (1.35 if head_spec_match else 1.0)
            raw_staff_score += (head_eff_primary / 100.0) * 0.85

        # 6. Department Head Force Multiplier (Dual-Attribute: Leadership + Relevant Domain Skill)
        if head:
            eff_head_lead = min(100.0, head.get("stat_leadership", 50.0) + mgmt_lead_bonus)
            lead_factor = eff_head_lead / 100.0
            if dep in ["ENGINEERING", "POWERTRAIN"]:
                head_domain = head.get("stat_engineering", 50.0)
            elif dep in ["MANUFACTURING", "TESTING", "TRACKSIDE"]:
                head_domain = head.get("stat_craftsmanship", 50.0)
            elif dep in ["COMMERCIAL"]:
                head_domain = head.get("stat_marketing", 50.0)
            else:
                head_domain = head.get("stat_communication", 50.0)

            head_spec_match = head.get("specialty") == target_spec
            head_domain_boost = (head_domain * (1.20 if head_spec_match else 1.0)) / 100.0

            # Head force multiplier ranges from ~0.75x to 1.55x
            head_mult = 0.70 + (lead_factor * 0.40) + (head_domain_boost * 0.35)
            spec_str = f" | {head.get('specialty')}" if head.get("specialty") else ""
            lead_extra_str = f" | +{mgmt_lead_bonus:.0f} Mgmt Lead" if mgmt_lead_bonus > 0 else ""
            head_status = (
                f"Active ({head.get('name')}{spec_str}{lead_extra_str} | +{(head_mult - 1.0) * 100:.1f}% Boost)"
            )
        else:
            head_mult = 1.00  # Unsupervised Mode
            head_status = "VACANT (Unsupervised Mode: +0% Bonus)"

        # 7. Category Director Synergy Multiplier (Executive Leadership + Strategy)
        if director:
            eff_dir_lead = min(100.0, director.get("stat_leadership", 50.0) + mgmt_lead_bonus)
            dir_lead = eff_dir_lead / 100.0
            dir_core = (
                director.get("stat_engineering", 50.0)
                if dep in ["ENGINEERING", "POWERTRAIN"]
                else director.get("stat_marketing", 50.0)
                if dep == "COMMERCIAL"
                else director.get("stat_craftsmanship", 50.0)
            ) / 100.0
            dir_mult = 0.85 + (dir_lead * 0.22) + (dir_core * 0.18)
            lead_extra_str = f" | +{mgmt_lead_bonus:.0f} Mgmt Lead" if mgmt_lead_bonus > 0 else ""
            dir_status = f"Active ({director.get('name')}{lead_extra_str} | +{(dir_mult - 1.0) * 100:.1f}% Synergy)"
        else:
            dir_mult = 0.90  # Coordination Drag
            dir_status = "VACANT (Coordination Drag: -10% Penalty)"

        # 8. Final Multiplier (Bounded strictly between 0.0 and 5.0x max as required)
        calc_mult = raw_staff_score * head_mult * dir_mult
        staff_mult = max(0.0, min(5.0, calc_mult))

        return {
            "node_id": node_id,
            "department": dep,
            "target_specialty": target_spec,
            "staff_mult": staff_mult,
            "raw_staff_score": raw_staff_score,
            "head_mult": head_mult,
            "head_status": head_status,
            "dir_mult": dir_mult,
            "dir_status": dir_status,
            "final_perf": staff_mult,
            "final_rel": staff_mult,
            "staff_count": len(staff_list),
            "staff_details": staff_details,
            "has_intern": intern is not None,
            "is_unstaffed": False,
            "coordination_rating": coordination_rating,
            "diminishing_exponent": gamma,
            "mgmt_lead_bonus": mgmt_lead_bonus,
        }

    def get_stat_scouting_display(self, team_id: int, stat_value: float) -> str:
        """
        Returns scouted stat string formatted with Fog-of-War uncertainty based on hr_performance_review tier.
        - Tier 0 (No Review Lab): Wide Fog-of-War range (±18 pts).
        - Tier 1: Moderate range (±10 pts).
        - Tier 2: Tight range (±4 pts).
        - Tier 3 (Max): 100% Exact Clarity.
        """
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT current_tier, is_unlocked FROM team_facilities WHERE team_id = ? AND node_id = 'hr_performance_review';",
                (team_id,),
            )
            row = cur.fetchone()
            rev_tier = row[0] if row and row[1] else 0

        val = float(stat_value)
        if rev_tier >= 3:
            return f"{val:.0f}"
        elif rev_tier == 2:
            low = max(10, round(val - 4))
            high = min(99, round(val + 4))
            return f"{low} - {high}"
        elif rev_tier == 1:
            low = max(10, round(val - 10))
            high = min(99, round(val + 10))
            return f"{low} - {high}"
        else:
            low = max(10, round(val - 18))
            high = min(99, round(val + 18))
            return f"{low} - {high}"

    def advance_weekly_personnel(self, team_id: int) -> List[str]:
        """
        Advances weekly aging, 6-month internship tryouts, wage satisfaction,
        stat training academies, and executes the autonomous HR suite.
        """
        notifications = []
        with self.db.get_connection() as conn:
            cur = conn.cursor()

            # Query HR facility tiers & automation policies
            cur.execute("SELECT node_id, current_tier, is_unlocked FROM team_facilities WHERE team_id = ?;", (team_id,))
            fac_tiers = {r[0]: (r[1] if r[2] else 0) for r in cur.fetchall()}
            policies = self.db.get_hr_policies(team_id)

            t_rec = fac_tiers.get("hr_recruitment", 0)
            t_pay = fac_tiers.get("hr_payroll", 0)
            t_team = fac_tiers.get("hr_teambuilding", 0)
            t_lead = fac_tiers.get("hr_leadership_institute", 0)
            t_cull = fac_tiers.get("hr_performance_cull", 0)
            t_tech = fac_tiers.get("hr_tech_academy", 0)
            t_craft = fac_tiers.get("hr_craft_workshop", 0)
            t_opt = fac_tiers.get("hr_workforce_optimizer", 0)
            t_proc = fac_tiers.get("hr_equipment_procurement", 0)
            t_mgmt = fac_tiers.get("mgmt_boardroom", 0)

            # Query equipment for mgmt_boardroom mentorship suite
            cur.execute(
                """
            SELECT te.equipment_id, te.current_level
            FROM team_equipment te
            JOIN facility_equipment fe ON te.equipment_id = fe.id
            WHERE te.team_id = ? AND fe.node_id = 'mgmt_boardroom' AND te.is_active = 1;
            """,
                (team_id,),
            )
            mgmt_equip_lead_gain = 0.0
            for eq_id, eq_lvl in cur.fetchall():
                if eq_id == "eq_mgmt_mentorship_suite":
                    mgmt_equip_lead_gain += eq_lvl * 0.05

            # 1. Advance Active Internships & Automated Graduation Pipeline
            cur.execute(
                """
            SELECT * FROM personnel
            WHERE team_id = ? AND is_intern = 1;
            """,
                (team_id,),
            )
            interns = [dict(r) for r in cur.fetchall()]

            for intern in interns:
                completed = intern.get("intern_months_completed", 0) + 1
                cur.execute("UPDATE personnel SET intern_months_completed = ? WHERE id = ?;", (completed, intern["id"]))

                # 6 Months Completed -> Unveil Potential & Evaluate Graduation
                if completed >= intern.get("intern_months_total", 6):
                    cur.execute(
                        """
                    UPDATE personnel
                    SET is_potential_revealed = 1,
                        stat_engineering = MIN(98, stat_engineering + 12),
                        stat_craftsmanship = MIN(98, stat_craftsmanship + 12),
                        stat_marketing = MIN(98, stat_marketing + 12),
                        stat_communication = MIN(98, stat_communication + 12),
                        stat_leadership = MIN(98, stat_leadership + 10),
                        stat_composure = MIN(98, stat_composure + 10)
                    WHERE id = ?;
                    """,
                        (intern["id"],),
                    )

                    pot = intern.get("stat_potential", 70)
                    min_pot = policies.get("min_intern_potential", 75)

                    # Tier 2 Automated Intern Pipeline Check
                    if t_rec >= 2 and bool(policies.get("auto_intern_pipeline", 1)):
                        if pot >= min_pot:
                            # Auto-sign as full specialist at entry-level minimum wage ($2,000/mo)
                            cur.execute(
                                """
                            UPDATE personnel
                            SET is_intern = 0,
                                role_type = 'STAFF',
                                salary_monthly = 2000.0,
                                market_value_monthly = 2000.0,
                                morale = 100.0
                            WHERE id = ?;
                            """,
                                (intern["id"],),
                            )
                            notifications.append(
                                f"🎓 HR PIPELINE: Intern {intern['name']} completed tryout with {pot}/100 Potential and was signed as full specialist ($2,000/mo)!"
                            )
                        else:
                            # Auto-dismiss under-potential intern
                            cur.execute("DELETE FROM personnel WHERE id = ?;", (intern["id"],))
                            notifications.append(
                                f"🎓 HR PIPELINE: Intern {intern['name']} completed tryout ({pot}/100 Potential) and was released to free the desk."
                            )
                    else:
                        rating_grade = (
                            "STAR PRODIGY" if pot >= 90 else ("SOLID PROSPECT" if pot >= 75 else "DEVELOPMENT TALENT")
                        )
                        notifications.append(
                            f"🎓 INTERNSHIP COMPLETE: {intern['name']} completed 6-month tryout! True Potential: {pot}/100 [{rating_grade}]."
                        )

            # 2. Automated Recruitment Tier 1: Auto-Fill Open Specialist Desks
            if t_rec >= 1 and bool(policies.get("auto_fill_desks", 1)):
                cur.execute("SELECT node_id FROM team_facilities WHERE team_id = ? AND is_unlocked = 1;", (team_id,))
                unlocked_nodes = [r[0] for r in cur.fetchall()]

                for node_id in unlocked_nodes:
                    p_data = self.get_facility_personnel(team_id, node_id)
                    if p_data["vacant_staff_slots"] > 0:
                        fin = self.db.get_department_financial_status(team_id, node_id)
                        if fin["surplus_or_deficit"] >= 2500.0:
                            # Look for candidate in recruitment queue
                            cur.execute(
                                """
                            SELECT pa.id, p.name, p.specialty, pa.salary_requested
                            FROM personnel_applications pa
                            JOIN personnel p ON pa.applicant_personnel_id = p.id
                            WHERE pa.team_id = ? AND pa.is_internship_tryout = 0
                            ORDER BY (p.specialty = ?) DESC, p.stat_engineering DESC LIMIT 1;
                            """,
                                (team_id, p_data["target_specialty"]),
                            )
                            cand = cur.fetchone()
                            if cand and fin["surplus_or_deficit"] >= cand[3]:
                                success, msg = self._hire_applicant_tx(cur, team_id, cand[0], node_id)
                                if success:
                                    notifications.append(
                                        f"💼 HR RECRUITMENT: Auto-hired {cand[1]} ({cand[2]}) into {node_id} (${cand[3]:,.0f}/mo)."
                                    )

            # 3. Automated Recruitment Tier 2: Auto-Assign Interns with $2,000/mo Headroom Guarantee
            if t_rec >= 2 and bool(policies.get("auto_intern_pipeline", 1)):
                cur.execute("SELECT node_id FROM team_facilities WHERE team_id = ? AND is_unlocked = 1;", (team_id,))
                unlocked_nodes = [r[0] for r in cur.fetchall()]

                for node_id in unlocked_nodes:
                    p_data = self.get_facility_personnel(team_id, node_id)
                    if not p_data["intern"]:
                        fin = self.db.get_department_financial_status(team_id, node_id)
                        # Check strictly for $2,000/mo budget headroom as required
                        if fin["surplus_or_deficit"] >= 2000.0:
                            cur.execute(
                                """
                            SELECT pa.id, p.name, p.specialty
                            FROM personnel_applications pa
                            JOIN personnel p ON pa.applicant_personnel_id = p.id
                            WHERE pa.team_id = ? AND pa.is_internship_tryout = 1
                            ORDER BY p.stat_potential DESC LIMIT 1;
                            """,
                                (team_id,),
                            )
                            intern_cand = cur.fetchone()
                            if intern_cand:
                                success, msg = self._hire_applicant_tx(cur, team_id, intern_cand[0], node_id)
                                if success:
                                    notifications.append(
                                        f"🎓 HR PIPELINE: Auto-assigned intern {intern_cand[1]} to {node_id} (Reserved $2,000/mo graduation budget)."
                                    )

            # 4. Automated Payroll & Wage Calibration Desk
            if t_pay >= 1 and bool(policies.get("auto_payroll", 1)):
                cur.execute(
                    "SELECT * FROM personnel WHERE team_id = ? AND facility_node_id IS NOT NULL AND role_type != 'INTERN';",
                    (team_id,),
                )
                staff_members = [dict(r) for r in cur.fetchall()]
                for sm in staff_members:
                    cur_sal = float(sm.get("salary_monthly", 8000.0))
                    mkt_val = float(sm.get("market_value_monthly", 8000.0))
                    if cur_sal < mkt_val * 0.95:
                        raise_diff = mkt_val - cur_sal
                        fin = self.db.get_department_financial_status(team_id, sm["facility_node_id"])
                        if fin["surplus_or_deficit"] >= raise_diff:
                            cur.execute(
                                "UPDATE personnel SET salary_monthly = ?, morale = 100.0 WHERE id = ?;",
                                (mkt_val, sm["id"]),
                            )
                            notifications.append(
                                f"📈 HR PAYROLL: Auto-adjusted wage for {sm['name']} to ${mkt_val:,.0f}/mo (100% Morale)."
                            )

            # 5. Autonomous Equipment Procurement using Department Savings
            if t_proc >= 1 and bool(policies.get("auto_equip_procure", 1)):
                cur.execute("SELECT node_id FROM team_facilities WHERE team_id = ? AND is_unlocked = 1;", (team_id,))
                unlocked_nodes = [r[0] for r in cur.fetchall()]
                for n_id in unlocked_nodes:
                    savings = self.db.get_facility_savings(team_id, n_id)
                    if savings > 1000.0:
                        eq_items = self.db.get_facility_equipment(team_id, n_id)
                        for eq in eq_items:
                            if (
                                not eq["is_tier_locked"]
                                and eq["current_level"] < eq["max_level"]
                                and eq["next_upgrade_cost"] <= savings
                            ):
                                cost = eq["next_upgrade_cost"]
                                cur.execute(
                                    "UPDATE team_facilities SET savings_balance = savings_balance - ? WHERE team_id = ? AND node_id = ?;",
                                    (cost, team_id, n_id),
                                )
                                next_lvl = eq["current_level"] + 1
                                cur.execute(
                                    """
                                INSERT INTO team_equipment (team_id, equipment_id, current_level, is_active)
                                VALUES (?, ?, ?, 1)
                                ON CONFLICT(team_id, equipment_id) DO UPDATE SET current_level = ?, is_active = 1;
                                """,
                                    (team_id, eq["id"], next_lvl, next_lvl),
                                )
                                notifications.append(
                                    f"🛠️ HR PROCUREMENT: Auto-upgraded {eq['name']} to Level {next_lvl} using ${cost:,.0f} from {n_id} Savings Account!"
                                )
                                break

            # 6. Demographic Age-Curve Performance Cull
            if t_cull >= 1 and bool(policies.get("auto_cull", 0)):
                cur.execute(
                    "SELECT * FROM personnel WHERE team_id = ? AND facility_node_id IS NOT NULL AND role_type = 'STAFF';",
                    (team_id,),
                )
                active_specialists = [dict(r) for r in cur.fetchall()]
                for spec_p in active_specialists:
                    age = spec_p.get("age", 35)
                    # Expected bell curve output: peak at 50 with sigma=14
                    expected_score = max(25.0, 75.0 * math.exp(-((age - 50.0) ** 2) / (2 * (14.0**2))))
                    primary = spec_p.get("stat_engineering", 40.0)
                    if primary < expected_score - policies.get("max_cull_underperform_deficit", 20.0):
                        cur.execute("DELETE FROM personnel WHERE id = ?;", (spec_p["id"],))
                        notifications.append(
                            f"📉 HR EXIT REVIEW: Released underperforming employee {spec_p['name']} (Age {age}, Skill {primary:.0f} vs Expected {expected_score:.0f}) to protect budget."
                        )

            # 7. Workforce Succession & Replacement Optimizer
            if t_opt >= 1 and bool(policies.get("auto_replace", 0)):
                cur.execute(
                    "SELECT * FROM personnel WHERE team_id = ? AND facility_node_id IS NOT NULL AND role_type = 'STAFF';",
                    (team_id,),
                )
                current_staff = [dict(r) for r in cur.fetchall()]
                cur.execute(
                    """
                SELECT pa.id, pa.salary_requested, p.*
                FROM personnel_applications pa
                JOIN personnel p ON pa.applicant_personnel_id = p.id
                WHERE pa.team_id = ? AND pa.is_internship_tryout = 0;
                """,
                    (team_id,),
                )
                candidates = [dict(r) for r in cur.fetchall()]

                for cur_s in current_staff:
                    cur_skill = cur_s.get("stat_engineering", 40.0)
                    cur_sal = cur_s.get("salary_monthly", 8000.0)
                    for cand in candidates:
                        cand_skill = cand.get("stat_engineering", 40.0)
                        cand_sal = cand.get("salary_requested", 8000.0)
                        if cand_skill >= cur_skill + 10.0 and cand_sal <= cur_sal:
                            # Execute auto-replacement
                            cur.execute("DELETE FROM personnel WHERE id = ?;", (cur_s["id"],))
                            self._hire_applicant_tx(cur, team_id, cand["id"], cur_s["facility_node_id"])
                            notifications.append(
                                f"🔄 HR OPTIMIZER: Replaced {cur_s['name']} ({cur_skill:.0f} Skill) with superior specialist {cand['name']} ({cand_skill:.0f} Skill) for ${cand_sal:,.0f}/mo!"
                            )
                            candidates.remove(cand)
                            break

            # 8. The Stat Improvement Academies & Management Factory Leadership
            if t_tech > 0:
                cur.execute(
                    "UPDATE personnel SET stat_engineering = MIN(99.0, stat_engineering + ?) WHERE team_id = ?;",
                    (0.12 * t_tech, team_id),
                )
            if t_craft > 0:
                cur.execute(
                    "UPDATE personnel SET stat_craftsmanship = MIN(99.0, stat_craftsmanship + ?), stat_composure = MIN(99.0, stat_composure + ?) WHERE team_id = ?;",
                    (0.12 * t_craft, 0.08 * t_craft, team_id),
                )
            if t_lead > 0:
                cur.execute(
                    "UPDATE personnel SET stat_leadership = MIN(99.0, stat_leadership + ?), stat_communication = MIN(99.0, stat_communication + ?) WHERE team_id = ? AND role_type IN ('DEPARTMENT_HEAD', 'CATEGORY_DIRECTOR');",
                    (0.18 * t_lead, 0.14 * t_lead, team_id),
                )
            if t_mgmt > 0:
                mgmt_lead_growth = 0.15 * t_mgmt + mgmt_equip_lead_gain
                cur.execute(
                    "UPDATE personnel SET stat_leadership = MIN(99.0, stat_leadership + ?) WHERE team_id = ?;",
                    (mgmt_lead_growth, team_id),
                )

            # 9. Morale & Teambuilding Evaluation
            cur.execute("SELECT * FROM personnel WHERE team_id = ?;", (team_id,))
            all_staff = [dict(r) for r in cur.fetchall()]
            morale_buff = 2.0 * t_team

            for s in all_staff:
                cur_sal = float(s.get("salary_monthly", 8000.0))
                mkt_val = float(s.get("market_value_monthly", 8000.0))
                cur_mor = float(s.get("morale", 85.0))

                # Teambuilding increases wage deficit tolerance: underpaid threshold drops from 85% to 65% with max Teambuilding
                tolerance_threshold = 0.85 - (0.06 * t_team)
                if cur_sal < mkt_val * tolerance_threshold:
                    penalty = 2.5 * max(0.3, 1.0 - (0.22 * t_team))
                    new_mor = max(15.0, cur_mor - penalty)
                else:
                    new_mor = min(100.0, cur_mor + 1.0 + morale_buff)

                cur.execute("UPDATE personnel SET morale = ? WHERE id = ?;", (new_mor, s["id"]))

            # 10. Occasional Inbound Applicant / Intern Refresh (15% chance per week)
            if random.random() < 0.15:
                cur.execute("SELECT COUNT(*) FROM personnel_applications WHERE team_id = ?;", (team_id,))
                app_count = cur.fetchone()[0]
                if app_count < 4:
                    i_age = random.randint(19, 22)
                    i_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
                    i_spec = random.choice(CORE_SPECIALTIES)
                    is_prodigy = random.random() < 0.28
                    i_pot = random.randint(90, 98) if is_prodigy else random.randint(62, 85)
                    i_base = random.randint(22, 38)

                    cur.execute(
                        """
                    INSERT INTO personnel (
                        team_id, facility_node_id, assigned_category, role_type, name, age, birth_year,
                        peak_age, retire_age, specialty, salary_monthly, market_value_monthly, morale,
                        stat_engineering, stat_craftsmanship, stat_marketing, stat_communication,
                        stat_leadership, stat_composure, stat_potential, is_intern, intern_months_completed, intern_months_total, is_potential_revealed
                    ) VALUES (
                        ?, NULL, NULL, 'INTERN', ?, ?, 2026 - ?,
                        ?, 67, ?, 1000.0, 1000.0, 95.0,
                        ?, ?, ?, ?,
                        ?, ?, ?, 1, 0, 6, 0
                    );
                    """,
                        (
                            team_id,
                            i_name,
                            i_age,
                            i_age,
                            random.randint(48, 54),
                            i_spec,
                            i_base,
                            i_base,
                            i_base,
                            i_base,
                            random.randint(20, 50),
                            random.randint(20, 50),
                            i_pot,
                        ),
                    )
                    new_app_id = cur.lastrowid
                    cur.execute(
                        """
                    INSERT INTO personnel_applications (
                        team_id, applicant_personnel_id, applied_role_type, target_facility_node_id, salary_requested, application_week, is_internship_tryout
                    ) VALUES (?, ?, 'INTERN', NULL, 1000.0, 1, 1);
                    """,
                        (team_id, new_app_id),
                    )
                    notifications.append(
                        f"📩 NEW INTERN CANDIDATE: {i_name} (Age {i_age}, {i_spec} background) applied for a 6-month tryout!"
                    )

            conn.commit()

        return notifications

    def get_inbound_applications(self, team_id: int) -> List[Dict[str, Any]]:
        """Returns all pending job applications and intern tryouts."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            SELECT pa.id as application_id, pa.applied_role_type, pa.salary_requested, pa.is_internship_tryout,
                   p.*
            FROM personnel_applications pa
            JOIN personnel p ON pa.applicant_personnel_id = p.id
            WHERE pa.team_id = ?;
            """,
                (team_id,),
            )
            return [dict(r) for r in cur.fetchall()]

    def _hire_applicant_tx(
        self, cur, team_id: int, application_id: int, target_node_id: str, mentor_id: Optional[int] = None
    ) -> Tuple[bool, str]:
        """Internal transaction helper to hire an applicant without re-opening database connection."""
        cur.execute(
            """
        SELECT pa.*, p.role_type as orig_role, p.name, p.is_intern
        FROM personnel_applications pa
        JOIN personnel p ON pa.applicant_personnel_id = p.id
        WHERE pa.id = ? AND pa.team_id = ?;
        """,
            (application_id, team_id),
        )
        row = cur.fetchone()
        if not row:
            return False, "Application not found."

        p_id = row["applicant_personnel_id"]
        is_intern = bool(row["is_intern"])
        role_to_assign = "INTERN" if is_intern else row["applied_role_type"]

        # Assign to target facility
        cur.execute(
            """
        UPDATE personnel
        SET facility_node_id = ?,
            role_type = ?,
            intern_mentor_id = ?,
            salary_monthly = ?
        WHERE id = ?;
        """,
            (target_node_id, role_to_assign, mentor_id, row["salary_requested"], p_id),
        )

        cur.execute("DELETE FROM personnel_applications WHERE id = ?;", (application_id,))
        return True, f"Successfully signed {row['name']} to {target_node_id}!"

    def hire_applicant(
        self, team_id: int, application_id: int, target_node_id: str, mentor_id: Optional[int] = None
    ) -> Tuple[bool, str]:
        """Hires an applicant or accepts an intern tryout into a facility node."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            res = self._hire_applicant_tx(cur, team_id, application_id, target_node_id, mentor_id)
            conn.commit()
            return res

    def assign_category_director(self, team_id: int, category: str, personnel_id: Optional[int]) -> Tuple[bool, str]:
        """Appoints or unassigns a Category Director."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            if personnel_id is not None:
                cur.execute("SELECT name FROM personnel WHERE id = ? AND team_id = ?;", (personnel_id, team_id))
                p_row = cur.fetchone()
                if not p_row:
                    return False, "Personnel not found."
                p_name = p_row[0]

                # Update personnel record
                cur.execute(
                    """
                UPDATE personnel
                SET role_type = 'CATEGORY_DIRECTOR', assigned_category = ?, facility_node_id = NULL
                WHERE id = ?;
                """,
                    (category, personnel_id),
                )

                cur.execute(
                    """
                INSERT OR REPLACE INTO team_category_directors (team_id, category, director_personnel_id)
                VALUES (?, ?, ?);
                """,
                    (team_id, category, personnel_id),
                )
                conn.commit()
                return True, f"Appointed {p_name} as {category} Director!"
            else:
                cur.execute(
                    """
                INSERT OR REPLACE INTO team_category_directors (team_id, category, director_personnel_id)
                VALUES (?, ?, NULL);
                """,
                    (team_id, category),
                )
                conn.commit()
                return True, f"{category} Director post is now vacant."

    def get_unlocked_facilities_with_capacity(self, team_id: int) -> List[Dict[str, Any]]:
        """Returns structured metadata for all unlocked facilities including current staff, head status, intern status, open slots, and specialty."""
        results = []
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            SELECT tf.node_id, tf.current_tier, fn.name, fn.department, tf.monthly_sub_budget
            FROM team_facilities tf
            JOIN facility_nodes fn ON tf.node_id = fn.id
            WHERE tf.team_id = ? AND tf.is_unlocked = 1
            ORDER BY fn.department, fn.name;
            """,
                (team_id,),
            )
            facilities = cur.fetchall()

            for f in facilities:
                node_id = f[0]
                cur_tier = int(f[1] or 1)
                fac_name = f[2]
                dept = f[3]
                p_data = self.get_facility_personnel(team_id, node_id, cur_tier)
                fin = self.db.get_department_financial_status(team_id, node_id, conn=conn)

                results.append(
                    {
                        "node_id": node_id,
                        "name": fac_name,
                        "department": dept,
                        "current_tier": cur_tier,
                        "target_specialty": p_data["target_specialty"],
                        "head": p_data["head"],
                        "has_head": p_data["head"] is not None,
                        "staff": p_data["staff"],
                        "staff_count": len(p_data["staff"]),
                        "max_staff_slots": p_data["max_staff_slots"],
                        "vacant_staff_slots": p_data["vacant_staff_slots"],
                        "intern": p_data["intern"],
                        "has_intern": p_data["intern"] is not None,
                        "surplus_budget": fin.get("surplus_or_deficit", 0.0),
                        "min_operational_cost": fin.get("min_operational_cost", 0.0),
                        "monthly_budget": fin.get("monthly_budget", 0.0),
                    }
                )
        return results

    def reassign_personnel(
        self, team_id: int, personnel_id: int, new_node_id: Optional[str], new_role: str = "STAFF"
    ) -> Tuple[bool, str]:
        """Reassigns an employee to a new department or promotes them."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT name, role_type, facility_node_id, specialty FROM personnel WHERE id = ? AND team_id = ?;",
                (personnel_id, team_id),
            )
            p_row = cur.fetchone()
            if not p_row:
                return False, "Personnel not found."
            p_name = p_row[0]
            old_node = p_row[2]

            if new_node_id is None:
                # Unassign from department
                cur.execute(
                    "UPDATE personnel SET facility_node_id = NULL, role_type = 'STAFF' WHERE id = ?;", (personnel_id,)
                )
                conn.commit()
                return True, f"Unassigned {p_name} from active department."

            # Verify target facility is unlocked
            cur.execute(
                "SELECT current_tier, is_unlocked FROM team_facilities WHERE team_id = ? AND node_id = ?;",
                (team_id, new_node_id),
            )
            tf = cur.fetchone()
            if not tf or not tf[1]:
                return False, "Target department is not unlocked."
            t_tier = int(tf[0] or 1)

            if new_role == "DEPARTMENT_HEAD":
                # Demote existing head in target node if different person
                cur.execute(
                    """
                UPDATE personnel
                SET role_type = 'STAFF'
                WHERE team_id = ? AND facility_node_id = ? AND role_type = 'DEPARTMENT_HEAD' AND id != ?;
                """,
                    (team_id, new_node_id, personnel_id),
                )

                cur.execute(
                    """
                UPDATE personnel
                SET facility_node_id = ?, role_type = 'DEPARTMENT_HEAD'
                WHERE id = ?;
                """,
                    (new_node_id, personnel_id),
                )
                conn.commit()
                return True, f"Assigned {p_name} as Department Head of {new_node_id}!"
            else:
                # Check vacant staff slots
                p_data = self.get_facility_personnel(team_id, new_node_id, t_tier)
                if old_node != new_node_id and p_data["vacant_staff_slots"] <= 0:
                    return (
                        False,
                        f"Target department has no open desk slots (Capacity: {p_data['max_staff_slots']}). Upgrade facility tier or reassign another specialist first.",
                    )

                cur.execute(
                    """
                UPDATE personnel
                SET facility_node_id = ?, role_type = 'STAFF'
                WHERE id = ?;
                """,
                    (new_node_id, personnel_id),
                )
                conn.commit()
                return True, f"Reassigned {p_name} to {new_node_id}!"

    def fire_personnel(self, team_id: int, personnel_id: int) -> Tuple[bool, str]:
        """Dismisses an employee, clearing their desk and removing them from team payroll."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT name, role_type, facility_node_id FROM personnel WHERE id = ? AND team_id = ?;",
                (personnel_id, team_id),
            )
            p_row = cur.fetchone()
            if not p_row:
                return False, "Employee not found."
            p_name = p_row[0]

            # Clear category director record if applicable
            cur.execute(
                "UPDATE team_category_directors SET director_personnel_id = NULL WHERE team_id = ? AND director_personnel_id = ?;",
                (team_id, personnel_id),
            )
            # Delete personnel
            cur.execute("DELETE FROM personnel WHERE id = ? AND team_id = ?;", (personnel_id, team_id))
            conn.commit()
            return True, f"Released {p_name} from team contract. Desk slot is now open."

    def promote_to_department_head(self, team_id: int, personnel_id: int, node_id: str) -> Tuple[bool, str]:
        """Promotes a staff specialist to Department Head of a facility node."""
        return self.reassign_personnel(team_id, personnel_id, node_id, new_role="DEPARTMENT_HEAD")

    def offer_raise(self, personnel_id: int, new_salary: float) -> Tuple[bool, str]:
        """Offers a salary increase to instantly boost morale and loyalty."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            UPDATE personnel
            SET salary_monthly = ?, morale = 98.0
            WHERE id = ?;
            """,
                (new_salary, personnel_id),
            )
            conn.commit()
            return True, f"Salary updated to ${new_salary:,.0f}/mo. Morale boosted to 98%!"

    def headhunt_rival_personnel(
        self, player_team_id: int, target_personnel_id: int, signing_bonus: float, salary_offered: float
    ) -> Tuple[bool, str]:
        """Attempts to poach a staff member or director from a rival team."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM personnel WHERE id = ?;", (target_personnel_id,))
            row = cur.fetchone()
            if not row:
                return False, "Target employee not found."
            target = dict(row)

            cur.execute("SELECT cash FROM teams WHERE id = ?;", (player_team_id,))
            cash = float(cur.fetchone()[0])
            total_upfront = signing_bonus * 1.50  # 1.5x includes buyout fee to rival team
            if cash < total_upfront:
                return False, f"Insufficient funds. Need ${total_upfront:,.0f} for buyout fee and signing bonus."

            # Success check: salary increase vs current + signing bonus
            cur_sal = float(target.get("salary_monthly", 8000.0))
            sal_increase_pct = (salary_offered - cur_sal) / max(1.0, cur_sal)

            if sal_increase_pct < 0.25 and signing_bonus < cur_sal * 3.0:
                return (
                    False,
                    f"{target['name']} rejected the offer! Demands at least +25% salary hike or larger signing bonus.",
                )

            # Deduct cash
            cur.execute("UPDATE teams SET cash = cash - ? WHERE id = ?;", (total_upfront, player_team_id))

            # Transfer employee
            cur.execute(
                """
            UPDATE personnel
            SET team_id = ?, salary_monthly = ?, morale = 95.0, facility_node_id = NULL
            WHERE id = ?;
            """,
                (player_team_id, salary_offered, target_personnel_id),
            )

            cur.execute(
                """
            INSERT INTO ledger (team_id, week, category, description, amount)
            VALUES (?, 1, 'HEADHUNTING', ?, ?);
            """,
                (player_team_id, f"Poached {target['name']} from rival team", -total_upfront),
            )

            conn.commit()
            return True, f"Successfully poached {target['name']} for ${salary_offered:,.0f}/mo!"
