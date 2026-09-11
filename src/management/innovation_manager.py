import random
import math
from typing import Dict, List, Any, Optional, Tuple
from ..database.career_db import CareerDatabase

CREATIVE_TEMPLATES = [
    {
        "title": "Inverted Venturi Tunnel Strakes",
        "description": "Radical sculpted underbody vortex generators accelerating floor underpressure.",
        "target_categories": ["REAR_WING", "FLOOR"],
        "subnode": "eng_windtunnel",
        "base_cost": 320000.0,
        "lockout_weeks": 3,
        "gain_range": (60, 160)
    },
    {
        "title": "Asymmetric Kinetic Inerter System",
        "description": "High-frequency hydraulic heave dampers eliminating high-speed aerodynamic pitch.",
        "target_categories": ["SUSPENSION", "BRAKES"],
        "subnode": "eng_suspension",
        "base_cost": 280000.0,
        "lockout_weeks": 3,
        "gain_range": (45, 120)
    },
    {
        "title": "Pulsed Boundary-Layer Flap Bleed",
        "description": "Micro-perforated carbon wing elements maintaining attached laminar airflow.",
        "target_categories": ["FRONT_WING", "REAR_WING"],
        "subnode": "eng_wings",
        "base_cost": 390000.0,
        "lockout_weeks": 4,
        "gain_range": (80, 210)
    },
    {
        "title": "Cryogenic Intercooler Bypass Manifold",
        "description": "Sub-zero charge-air thermal loop delivering instantaneous low-end combustion boost.",
        "target_categories": ["ENGINE"],
        "subnode": "eng_dyno",
        "base_cost": 460000.0,
        "lockout_weeks": 4,
        "gain_range": (90, 250)
    },
    {
        "title": "Carbon-Nanotube Matrix Bulkhead",
        "description": "Ultra-rigid woven nanotube structural weave redistributing cornering lateral loads.",
        "target_categories": ["SUSPENSION", "BRAKES"],
        "subnode": "eng_materials",
        "base_cost": 240000.0,
        "lockout_weeks": 2,
        "gain_range": (35, 95)
    },
    {
        "title": "Flexible Aeroelastic Wing Profiles",
        "description": "Passive aerodynamic deformation flexing flat on straights for maximum top speed.",
        "target_categories": ["FRONT_WING"],
        "subnode": "eng_cfd",
        "base_cost": 350000.0,
        "lockout_weeks": 3,
        "gain_range": (55, 175)
    },
    {
        "title": "Direct Neural Telemetry Linkage",
        "description": "High-bandwidth predictive algorithm optimizing brake bias and differential locks.",
        "target_categories": ["BRAKES", "SUSPENSION", "REAR_WING"],
        "subnode": "eng_reliability",
        "base_cost": 520000.0,
        "lockout_weeks": 5,
        "gain_range": (110, 250)
    },
    {
        "title": "Active Fluidic Vortex Generators",
        "description": "Compressed air jets energizing turbulent wake over the rear diffuser strakes.",
        "target_categories": ["REAR_WING", "FLOOR"],
        "subnode": "eng_windtunnel",
        "base_cost": 410000.0,
        "lockout_weeks": 4,
        "gain_range": (70, 190)
    }
]

COMPETITOR_TEMPLATES = [
    {
        "title": "Slotted Cascade Endplates",
        "description": "Reverse-engineered multi-element endplate vents creating low-pressure outwash.",
        "target_categories": ["FRONT_WING"],
        "subnode": "eng_wings",
        "base_cost": 120000.0,
        "lockout_weeks": 2,
        "gain_range": (12, 26)
    },
    {
        "title": "Brake Caliper Thermal Shrouding",
        "description": "Observed radial ducting geometry redirecting airflow through carbon disc core.",
        "target_categories": ["BRAKES"],
        "subnode": "eng_brakes",
        "base_cost": 95000.0,
        "lockout_weeks": 2,
        "gain_range": (10, 22)
    },
    {
        "title": "Third-Spring Heave Rocker Geometry",
        "description": "Competitor progressive rocker linkage stabilizing high-speed ride height.",
        "target_categories": ["SUSPENSION"],
        "subnode": "eng_suspension",
        "base_cost": 135000.0,
        "lockout_weeks": 2,
        "gain_range": (14, 28)
    },
    {
        "title": "Low-Drag Stepped Diffuser Floor",
        "description": "Photographed floor edge strakes sealing ground effect airflow.",
        "target_categories": ["FLOOR"],
        "subnode": "eng_windtunnel",
        "base_cost": 160000.0,
        "lockout_weeks": 3,
        "gain_range": (15, 30)
    },
    {
        "title": "Wastegate Pre-Spool Calibration",
        "description": "Rival ECU anti-lag throttle mapping minimizing turbo boost threshold delay.",
        "target_categories": ["ENGINE"],
        "subnode": "eng_dyno",
        "base_cost": 180000.0,
        "lockout_weeks": 3,
        "gain_range": (16, 30)
    },
    {
        "title": "Curved Trailing-Edge Gurney Flap",
        "description": "Competitor serrated trailing edge generating high downforce with minimal drag.",
        "target_categories": ["REAR_WING"],
        "subnode": "eng_workshop",
        "base_cost": 85000.0,
        "lockout_weeks": 1,
        "gain_range": (10, 20)
    },
    {
        "title": "Titanium Caliper Piston Insulators",
        "description": "Observed lightweight heat shields preventing brake fluid boil over race distance.",
        "target_categories": ["BRAKES"],
        "subnode": "eng_brakes",
        "base_cost": 90000.0,
        "lockout_weeks": 2,
        "gain_range": (10, 24)
    },
    {
        "title": "High-Camber Front Wing Flap Profile",
        "description": "Photographed aggressive front wing angle generating extra low-speed turn-in grip.",
        "target_categories": ["FRONT_WING"],
        "subnode": "eng_cfd",
        "base_cost": 125000.0,
        "lockout_weeks": 2,
        "gain_range": (12, 26)
    },
    {
        "title": "Dual-Element Beam Wing Extension",
        "description": "Rival low-drag rear beam wing coupling with diffuser upwash.",
        "target_categories": ["REAR_WING"],
        "subnode": "eng_wings",
        "base_cost": 110000.0,
        "lockout_weeks": 2,
        "gain_range": (11, 25)
    },
    {
        "title": "Progressive Anti-Roll Bar Droplinks",
        "description": "Competitor asymmetric droplink mounts improving kerb ride compliance.",
        "target_categories": ["SUSPENSION"],
        "subnode": "eng_materials",
        "base_cost": 115000.0,
        "lockout_weeks": 2,
        "gain_range": (12, 25)
    }
]


RIVAL_TEAMS = [
    "Scuderia Apex WSF", "Titan Grand Prix", "Vortex Works",
    "Bavaria Continental", "Nordic Velocity", "Phoenix Racing", "Solaris Team"
]

CREATIVE_PROPOSERS = [
    "Dr. Aris Thorne (Chief Aerodynamicist)",
    "Elena Rostova (Lead Systems Engineer)",
    "Mark Jensen (Materials Scientist)",
    "Dr. Hiroshi Sato (Vehicle Dynamics Lead)",
    "Claire Dupont (Senior Powertrain Specialist)",
    "Victor Vance (Experimental R&D Tech)"
]

class InnovationManager:
    """
    Manages the R&D Innovation Pipeline:
    1. Creative Inventions:
       - Rare spontaneous staff ideas ($P = 1/240$ per staff per week).
       - Default success 3% to 12% (boosted by factory CFD/Wind Tunnel/Materials upgrades).
       - Massive flat knowledge boost (+35 to +250) across 1 to 3 parts.
    2. Competitor Intelligence:
       - Observed from rival teams scaled by trackside crew count.
       - High default success rate (45% to 65%).
       - Targeted flat knowledge boost (+10 to +30) on 1 to 2 parts.
    3. Flat Knowledge Application:
       - On success, increases knowledge_min and knowledge_max by the exact flat gain on all target parts.
    """
    def __init__(self, db: CareerDatabase):
        self.db = db

    def get_team_pitches(self, team_id: int, status: str = "PENDING") -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            SELECT * FROM innovation_pitches 
            WHERE team_id = ? AND status = ? 
            ORDER BY id DESC;
            """, (team_id, status))
            return [dict(r) for r in cur.fetchall()]

    def check_and_generate_proposals(
        self,
        team_id: int,
        workforce_count: int = 24,
        trackside_crew_count: Optional[int] = None,
        cost_mult: float = 1.0,
        rate_mult: float = 1.0,
        success_mult: float = 1.0,
        gain_mult: float = 1.0
    ):
        """
        Dynamically generates breakthrough design proposals:
        1. Creative Inventions: Rolled per staff ($1/240$ chance per staff/week * rate_mult).
        2. Competitor Intelligence: Rolled based on trackside crew count * rate_mult.
        """
        existing_pending = self.get_team_pitches(team_id, status="PENDING")
        if len(existing_pending) >= 4:
            return

        # Determine trackside crew if not provided
        if trackside_crew_count is None:
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                SELECT COUNT(*) FROM staff 
                WHERE team_id = ? AND assigned_subnode IN ('track_pitrig', 'track_wheelguns', 'track_telemetry');
                """, (team_id,))
                t_res = cur.fetchone()[0]
                trackside_crew_count = int(t_res) if t_res > 0 else max(3, int(workforce_count * 0.18))

        # Query unlocked factory upgrade levels for success bonuses
        factory_bonus = 0.0
        trackside_bonus = 0.0
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            SELECT node_id, current_tier FROM team_facilities 
            WHERE team_id = ? AND is_unlocked = 1;
            """, (team_id,))
            fac_tiers = {r[0]: r[1] for r in cur.fetchall()}
            
            # CAD Office (+5%/tier), Rapid Proto (+8%/tier), QA/NDT (+6%/tier), CFD (+4%/tier), Wind Tunnel (+4%/tier)
            factory_bonus = (
                fac_tiers.get("eng_cad_office", 0) * 5.0 +
                fac_tiers.get("mfg_rapid_proto", 0) * 8.0 +
                fac_tiers.get("test_qa_ndt", 0) * 6.0 +
                fac_tiers.get("eng_cfd", 0) * 4.0 +
                fac_tiers.get("eng_windtunnel", 0) * 4.0
            )

            # Query equipment levels for trackside recon rigs
            cur.execute("""
            SELECT te.equipment_id, te.current_level 
            FROM team_equipment te
            WHERE te.team_id = ? AND te.is_active = 1;
            """, (team_id,))
            eq_lvls = {r[0]: r[1] for r in cur.fetchall()}

            # Trackside bonus including Recon Unit, Reverse Engineering, and Telemetry
            trackside_bonus = (
                fac_tiers.get("track_telemetry", 0) * 3.0 +
                fac_tiers.get("track_pitrig", 0) * 2.0 +
                fac_tiers.get("track_wheelguns", 0) * 1.5 +
                fac_tiers.get("track_rival_intel", 0) * 6.0 +
                fac_tiers.get("track_reverse_eng", 0) * 5.0 +
                eq_lvls.get("eq_intel_acoustic_microphones", 0) * 2.0
            )


        # =====================================================================
        # 1. Roll for Creative Inventions (P = 1/240 per staff per week * rate_mult)
        # =====================================================================
        p_staff = (1.0 / 240.0) * rate_mult
        p_any_creative = 1.0 - math.pow(max(0.0, 1.0 - p_staff), max(1, workforce_count))
        
        # Large teams (e.g. 500-2000 staff) can generate multiple ideas
        expected_ideas = workforce_count * p_staff
        num_creative_to_generate = 0
        if expected_ideas >= 1.0:
            num_creative_to_generate = min(2, int(round(expected_ideas * random.uniform(0.5, 1.2))))
            if num_creative_to_generate == 0 and random.random() < p_any_creative:
                num_creative_to_generate = 1
        elif random.random() < p_any_creative:
            num_creative_to_generate = 1

        for _ in range(num_creative_to_generate):
            if len(self.get_team_pitches(team_id, status="PENDING")) >= 4:
                break
            self._create_pitch(team_id, "CREATIVE", factory_bonus, cost_mult, success_mult=success_mult, gain_mult=gain_mult)

        # =====================================================================
        # 2. Roll for Competitor Intelligence Ideas (Based on Trackside Crew * rate_mult)
        # =====================================================================
        # Boosted by Paddock Recon Unit (track_rival_intel) and Telephoto Array equipment
        recon_tier = fac_tiers.get("track_rival_intel", 0)
        telephoto_lvl = eq_lvls.get("eq_intel_telephoto_array", 0)
        intel_roll_mult = 1.0 + (recon_tier * 0.40) + (telephoto_lvl * 0.10)
        
        p_competitor = min(0.95, (0.15 + (trackside_crew_count / 20.0) * 0.35) * rate_mult * intel_roll_mult)
        if random.random() < p_competitor:
            if len(self.get_team_pitches(team_id, status="PENDING")) < 4:
                rev_tier = fac_tiers.get("track_reverse_eng", 0)
                lidar_lvl = eq_lvls.get("eq_rev_lidar_scanner", 0)
                photogram_lvl = eq_lvls.get("eq_rev_photogrammetry_ai", 0)
                copy_gain_mult = gain_mult * (1.0 + rev_tier * 0.25 + lidar_lvl * 0.08)
                lockout_reduction = 1 if (rev_tier >= 2 or photogram_lvl >= 2) else 0

                self._create_pitch(
                    team_id, "COMPETITOR", trackside_bonus, cost_mult, 
                    success_mult=success_mult, gain_mult=copy_gain_mult,
                    lockout_delta=-lockout_reduction
                )

    def _create_pitch(
        self,
        team_id: int,
        idea_type: str,
        facility_bonus: float,
        cost_mult: float,
        success_mult: float = 1.0,
        gain_mult: float = 1.0,
        lockout_delta: int = 0
    ):
        """Constructs and inserts a single Innovation Pitch into the database."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()

            if idea_type == "CREATIVE":
                tmpl = random.choice(CREATIVE_TEMPLATES)
                proposer = random.choice(CREATIVE_PROPOSERS)
                observed_from = "In-House R&D Breakthrough"
                target_cats = ",".join(tmpl["target_categories"])
                
                # Knowledge gain between 35 and 250 scaled by difficulty gain_mult
                g_min, g_max = tmpl["gain_range"]
                raw_gain = float(random.randint(g_min, g_max))
                knowledge_gain = round(raw_gain * gain_mult, 1)

                # Inverse success chance: +35 gain -> ~12% success; +250 gain -> ~3% success (with randomness)
                gain_fraction = (raw_gain - 35.0) / (250.0 - 35.0)
                base_success = (12.0 - gain_fraction * 9.0 + random.uniform(-2.5, 3.5)) * success_mult
                base_success = max(2.0, min(16.0, base_success)) # 2% to 16% clamp with difficulty

                actual_success = min(75.0, round(base_success + facility_bonus, 1))

                hard_cost = round(tmpl["base_cost"] * (knowledge_gain / 100.0) * cost_mult, -3)
                lockout_weeks = max(1, tmpl["lockout_weeks"] + lockout_delta)
                primary_cat = tmpl["target_categories"][0]
                subnode = tmpl["subnode"]

            else:
                tmpl = random.choice(COMPETITOR_TEMPLATES)
                rival = random.choice(RIVAL_TEAMS)
                proposer = f"Trackside Reconnaissance ({rival})"
                observed_from = rival
                target_cats = ",".join(tmpl["target_categories"])

                # Knowledge gain between 10 and 30 scaled by difficulty gain_mult and reverse engineering bonuses
                g_min, g_max = tmpl["gain_range"]
                raw_gain = float(random.randint(g_min, g_max))
                knowledge_gain = round(raw_gain * gain_mult, 1)

                # Competitor ideas have high baseline success (45% to 65%) scaled by difficulty success_mult
                base_success = random.uniform(46.0, 62.0) * success_mult
                actual_success = min(95.0, round(base_success + facility_bonus, 1))

                hard_cost = round(tmpl["base_cost"] * cost_mult, -3)
                lockout_weeks = max(1, tmpl["lockout_weeks"] + lockout_delta)
                primary_cat = tmpl["target_categories"][0]
                subnode = tmpl["subnode"]


            # Fog-of-war estimated ranges for UI display (+-3% to +-6%)
            fuzz = random.randint(3, 6)
            est_min = max(2, int(actual_success - fuzz))
            est_max = min(99, int(actual_success + fuzz))

            cur.execute("""
            INSERT INTO innovation_pitches (
                team_id, title, description, proposer_name, category, locked_subnode,
                lockout_weeks, hard_cost, est_success_min, est_success_max, actual_success_rate,
                est_perf_min, est_perf_max, actual_perf_gain, est_rel_min, est_rel_max,
                actual_rel_gain, status, weeks_remaining,
                idea_type, target_categories, knowledge_gain, observed_from
            ) VALUES (
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, 'PENDING', ?,
                ?, ?, ?, ?
            );
            """, (
                team_id, tmpl["title"], tmpl["description"], proposer, primary_cat, subnode,
                lockout_weeks, hard_cost, est_min, est_max, actual_success,
                knowledge_gain, knowledge_gain, knowledge_gain, 0.0, 0.0,
                0.0, lockout_weeks,
                idea_type, target_cats, knowledge_gain, observed_from
            ))
            conn.commit()

    def greenlight_pitch(self, team_id: int, pitch_id: int) -> Tuple[bool, str]:
        """Funds and activates an innovation pitch, deducting hard cost and locking sub-department."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM innovation_pitches WHERE id = ? AND team_id = ? AND status = 'PENDING';", (pitch_id, team_id))
            pitch = cur.fetchone()
            if not pitch:
                return False, "Innovation proposal not found."

            cur.execute("SELECT cash FROM teams WHERE id = ?;", (team_id,))
            cash = float(cur.fetchone()[0])
            if cash < pitch["hard_cost"]:
                return False, f"Insufficient funds. Required: ${pitch['hard_cost']:,.0f}"

            # Deduct cash & set active
            cur.execute("UPDATE teams SET cash = cash - ? WHERE id = ?;", (pitch["hard_cost"], team_id))
            cur.execute("""
            UPDATE innovation_pitches 
            SET status = 'ACTIVE', weeks_remaining = lockout_weeks 
            WHERE id = ?;
            """, (pitch_id,))
            
            cur.execute("""
            INSERT INTO ledger (team_id, week, category, description, amount)
            VALUES (?, 1, 'INNOVATION', ?, ?);
            """, (team_id, f"Funded R&D Project: {pitch['title']}", -pitch["hard_cost"]))
            
            conn.commit()
            return True, f"Project '{pitch['title']}' greenlit! {pitch['locked_subnode']} locked for {pitch['lockout_weeks']} weeks."

    def process_weekly_innovation_progress(self, team_id: int) -> List[Dict[str, Any]]:
        """
        Advances active innovation projects by 1 week.
        Upon completion, evaluates success and applies flat knowledge pool increases
        directly to knowledge_min and knowledge_max on car_components for all target parts!
        """
        results = []
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM innovation_pitches WHERE team_id = ? AND status = 'ACTIVE';", (team_id,))
            active_pitches = [dict(r) for r in cur.fetchall()]

            for p in active_pitches:
                remaining = p["weeks_remaining"] - 1
                if remaining <= 0:
                    # Roll success against actual_success_rate
                    roll = random.uniform(0.0, 100.0)
                    is_success = (roll <= p["actual_success_rate"])

                    gain = float(p.get("knowledge_gain", 20.0) or 20.0)
                    raw_cats = p.get("target_categories") or p["category"]
                    categories = [c.strip() for c in raw_cats.split(",") if c.strip()]
                    cat_names = ", ".join(categories)

                    if is_success:
                        # Apply flat knowledge gain to all targeted components on Car 1 & Car 2
                        for cat in categories:
                            cur.execute("""
                            UPDATE car_components 
                            SET knowledge_min = round(knowledge_min + ?, 1),
                                knowledge_max = round(knowledge_max + ?, 1)
                            WHERE team_id = ? AND category = ?;
                            """, (gain, gain, team_id, cat))

                        idea_lbl = "Creative Breakthrough" if p.get("idea_type") == "CREATIVE" else "Competitor Intel"
                        outcome_msg = f"🎉 BREAKTHROUGH ({idea_lbl})! '{p['title']}' succeeded! Added +{gain:.0f} Flat Knowledge to {cat_names}!"
                    else:
                        outcome_msg = f"❌ Concept Failure: '{p['title']}' failed validation testing. Zero knowledge gained."

                    cur.execute("UPDATE innovation_pitches SET status = 'COMPLETED', weeks_remaining = 0 WHERE id = ?;", (p["id"],))
                    results.append({"title": p["title"], "is_success": is_success, "message": outcome_msg})
                else:
                    cur.execute("UPDATE innovation_pitches SET weeks_remaining = ? WHERE id = ?;", (remaining, p["id"]))

            conn.commit()
        return results

