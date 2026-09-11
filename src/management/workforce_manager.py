import random
from typing import Dict, List, Any, Optional, Tuple
from ..database.career_db import CareerDatabase

class WorkforceManager:
    """
    Manages workforce scaling from 20 to 1,000 employees,
    sub-node staff capacity limits, hiring/firing,
    and HR automated recruitment delegation.
    """
    def __init__(self, db: CareerDatabase):
        self.db = db

    def get_workforce_summary(self, team_id: int) -> Dict[str, Any]:
        """Calculates total staff count, total capacity across unlocked sub-nodes, and monthly payroll."""
        facilities = self.db.get_team_facilities(team_id)
        total_capacity = sum(f["staff_capacity"] * f["current_tier"] for f in facilities if f["is_unlocked"])
        
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*), SUM(salary_monthly), AVG(skill) FROM staff WHERE team_id = ?;", (team_id,))
            res = cur.fetchone()
            count = int(res[0] or 0)
            payroll = float(res[1] or 0.0)
            avg_skill = float(res[2] or 50.0)

            cur.execute("SELECT auto_hire_enabled FROM teams WHERE id = ?;", (team_id,))
            auto_hire = bool(cur.fetchone()[0])

            return {
                "staff_count": count,
                "total_capacity": total_capacity,
                "monthly_payroll": payroll,
                "average_skill": avg_skill,
                "auto_hire_enabled": auto_hire
            }

    def set_auto_hire(self, team_id: int, enabled: bool):
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE teams SET auto_hire_enabled = ? WHERE id = ?;", (1 if enabled else 0, team_id))
            conn.commit()

    def process_weekly_workforce(self, team_id: int):
        """If HR auto-hire is enabled, automatically recruits specialists up to facility capacity."""
        summary = self.get_workforce_summary(team_id)
        if not summary["auto_hire_enabled"]:
            return

        needed = summary["total_capacity"] - summary["staff_count"]
        if needed <= 0:
            return

        # Hire up to 5 specialists per week until capacity reached
        to_hire = min(5, needed)
        first_names = ["Alex", "Julian", "Marcus", "Elena", "Sophie", "Lucas", "David", "Chloe", "Henrik"]
        last_names = ["Vance", "Sterling", "Kovacs", "Rousseau", "Lindqvist", "Novak", "Sato", "Fischer"]

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            for _ in range(to_hire):
                name = f"{random.choice(first_names)} {random.choice(last_names)}"
                skill = random.randint(55, 80)
                salary = skill * 45.0
                cur.execute("""
                INSERT INTO staff (team_id, name, role, assigned_subnode, skill, salary_monthly)
                VALUES (?, ?, 'Specialist', 'eng_workshop', ?, ?);
                """, (team_id, name, skill, salary))
            conn.commit()
