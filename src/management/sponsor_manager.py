import random
from typing import Dict, List, Any, Optional, Tuple
from ..database.career_db import CareerDatabase
from ..data.balance_config import BALANCE_REGISTRY

BRAND_CATALOG = {
    "TITLE": [
        {"name": "Solaris Global Telecom", "color_hex": "#00d2be", "base_sign": 1200000, "base_per_race": 320000, "min_appeal": 65, "target_pos": 4, "target_bonus": 180000},
        {"name": "Apex Hyper Energy", "color_hex": "#ff8700", "base_sign": 1500000, "base_per_race": 380000, "min_appeal": 75, "target_pos": 3, "target_bonus": 250000},
        {"name": "Titan Aerospace", "color_hex": "#dc0000", "base_sign": 1800000, "base_per_race": 450000, "min_appeal": 85, "target_pos": 2, "target_bonus": 350000},
        {"name": "Vanguard Capital", "color_hex": "#006f62", "base_sign": 1100000, "base_per_race": 290000, "min_appeal": 55, "target_pos": 5, "target_bonus": 150000},
        {"name": "Horizon Microchips", "color_hex": "#1e41ff", "base_sign": 800000, "base_per_race": 210000, "min_appeal": 40, "target_pos": 7, "target_bonus": 100000}
    ],
    "MIDDLE": [
        {"name": "Quantum Synthetics", "color_hex": "#b4ff00", "base_sign": 400000, "base_per_race": 110000, "min_appeal": 35, "target_pos": 8, "target_bonus": 60000},
        {"name": "Castillo Petroleum", "color_hex": "#ffcc00", "base_sign": 500000, "base_per_race": 130000, "min_appeal": 45, "target_pos": 7, "target_bonus": 75000},
        {"name": "Nordic Logistics", "color_hex": "#0088cc", "base_sign": 350000, "base_per_race": 95000, "min_appeal": 25, "target_pos": 9, "target_bonus": 50000},
        {"name": "Bavaria Automotive", "color_hex": "#3366cc", "base_sign": 450000, "base_per_race": 120000, "min_appeal": 50, "target_pos": 6, "target_bonus": 85000},
        {"name": "Velocity Timepieces", "color_hex": "#cc3366", "base_sign": 300000, "base_per_race": 85000, "min_appeal": 10, "target_pos": 10, "target_bonus": 40000}
    ],
    "MINOR": [
        {"name": "AeroSpark Plugs", "color_hex": "#ff4444", "base_sign": 80000, "base_per_race": 28000, "min_appeal": 14, "target_pos": None, "target_bonus": 0},
        {"name": "Kevlar Composites", "color_hex": "#888888", "base_sign": 95000, "base_per_race": 32000, "min_appeal": 20, "target_pos": None, "target_bonus": 0},
        {"name": "DynoFlow Lubricants", "color_hex": "#33aa33", "base_sign": 70000, "base_per_race": 25000, "min_appeal": 6, "target_pos": None, "target_bonus": 0},
        {"name": "Optic Telemetry", "color_hex": "#00aaff", "base_sign": 110000, "base_per_race": 38000, "min_appeal": 25, "target_pos": None, "target_bonus": 0},
        {"name": "Paddock Radio Comms", "color_hex": "#aa44bb", "base_sign": 60000, "base_per_race": 22000, "min_appeal": 8, "target_pos": None, "target_bonus": 0},
        {"name": "Apex Trackside Apparel", "color_hex": "#ff9900", "base_sign": 75000, "base_per_race": 26000, "min_appeal": 10, "target_pos": None, "target_bonus": 0},
        {"name": "Matrix Simulators", "color_hex": "#00ffcc", "base_sign": 120000, "base_per_race": 40000, "min_appeal": 28, "target_pos": None, "target_bonus": 0},
        {"name": "Pulse Energy Drink", "color_hex": "#ff3399", "base_sign": 85000, "base_per_race": 30000, "min_appeal": 16, "target_pos": None, "target_bonus": 0}
    ]
}

class SponsorManager:
    """
    Manages 3 tiers of sponsors:
    - 2 Title Sponsors (Flagship deals)
    - 4 Middle Sponsors (Secondary partnerships)
    - 10 Minor Sponsors (Technical / Supplier partners)
    Calculates Sponsor Appeal from Tier, Form, 5-Season History, Driver Marketability, and Marketing HQ.
    """
    def __init__(self, db: CareerDatabase):
        self.db = db

    def calculate_sponsor_appeal(self, team_id: int) -> Dict[str, Any]:
        """
        Calculates total sponsor appeal score (0 - 100) and component breakdown:
        1. League Tier (Max 35 pts)
        2. Last 10 Races Form (Max 25 pts)
        3. Last 5 Seasons History (Max 15 pts)
        4. Driver Marketability (Max 15 pts)
        5. Marketing Facilities (Max 40 pts)
        """
        with self.db.get_connection() as conn:
            cur = conn.cursor()

            # 1. League Tier
            cur.execute("SELECT tier FROM teams WHERE id = ?;", (team_id,))
            row = cur.fetchone()
            tier = row[0] if row else 3
            tier_pts = BALANCE_REGISTRY.sponsor.tier_appeal_points.get(tier, 4.0)

            # 2. Last 10 Races Form (0.0 for unproven team with no races)
            cur.execute("SELECT finish_position FROM race_history WHERE team_id = ? ORDER BY id DESC LIMIT 10;", (team_id,))
            recent_finishes = [r[0] for r in cur.fetchall()]
            if recent_finishes:
                avg_pos = sum(recent_finishes) / len(recent_finishes)
                # P1 -> 25pts, P10 -> 10pts, P20 -> 2pts
                form_pts = max(2.0, min(25.0, 27.0 - avg_pos * 1.25))
            else:
                form_pts = 0.0 # Baseline default for team with no race history

            # 3. Last 5 Seasons Historical Prestige (0.0 for unproven team with no history)
            cur.execute("SELECT championship_position FROM season_history WHERE team_id = ? AND season_num >= 1 ORDER BY season_num DESC LIMIT 5;", (team_id,))
            seasons = [r[0] for r in cur.fetchall()]
            weights = [0.40, 0.25, 0.18, 0.12, 0.05]
            if seasons:
                hist_score = 0.0
                for idx, pos in enumerate(seasons):
                    w = weights[idx] if idx < len(weights) else 0.05
                    hist_score += max(1.0, 16.0 - pos * 1.5) * w
                history_pts = min(15.0, hist_score)
            else:
                history_pts = 0.0 # Baseline default for team with no season history

            # 4. Driver Marketability (enhanced by Media Studio and Digital Channels)
            cur.execute("SELECT AVG(marketability) FROM drivers WHERE team_id = ? AND is_academy_driver = 0;", (team_id,))
            mkt_res = cur.fetchone()[0]
            avg_mkt = float(mkt_res) if mkt_res is not None else 50.0
            
            # 5. Marketing & Commercial Facilities (Massive Marketability Impact)
            cur.execute("""
            SELECT node_id, current_tier FROM team_facilities 
            WHERE team_id = ? AND is_unlocked = 1;
            """, (team_id,))
            fac_tiers = {r[0]: r[1] for r in cur.fetchall()}

            # Media Studio (+20% / tier) and Digital (+15% / tier) enhance driver marketability reach
            driver_reach_mult = 1.0 + fac_tiers.get("mkt_studio", 0) * 0.20 + fac_tiers.get("mkt_digital", 0) * 0.15
            driver_pts = min(15.0, (avg_mkt / 100.0) * 10.0 * driver_reach_mult)

            # Core Commercial Facilities Marketability Score
            comm_suite_tier = fac_tiers.get("driver_commercial_suite", 0)
            comm_score = (
                fac_tiers.get("mkt_press", 0) * 3.0 +
                fac_tiers.get("mkt_brand_design", 0) * 4.0 +
                fac_tiers.get("mkt_digital", 0) * 5.0 +
                fac_tiers.get("mkt_studio", 0) * 8.0 +
                fac_tiers.get("mkt_hospitality", 0) * 6.0 +
                fac_tiers.get("mkt_merch", 0) * 3.0 +
                fac_tiers.get("mkt_fan_club", 0) * 3.0 +
                fac_tiers.get("mkt_licensing", 0) * 3.0 +
                fac_tiers.get("mkt_esports", 0) * 4.0 +
                fac_tiers.get("mkt_customer_racing", 0) * 8.0 +
                comm_suite_tier * 5.0  # Driver Commercial & Sponsor Suite
            )

            # Heritage Collection & Museum Championship Multiplier
            museum_tier = fac_tiers.get("mkt_heritage", 0)
            museum_bonus = 0.0
            if museum_tier > 0:
                cur.execute("SELECT COUNT(*) FROM season_history WHERE team_id = ? AND championship_position = 1 AND season_num >= 1;", (team_id,))
                titles_won = int(cur.fetchone()[0] or 0)
                museum_bonus = min(15.0, (museum_tier * 4.0) + (titles_won * 3.0 * museum_tier))

            facility_pts = min(40.0, comm_score + museum_bonus)

            total_appeal = int(min(100.0, max(1.0, tier_pts + form_pts + history_pts + driver_pts + facility_pts)))

            return {
                "total_appeal": total_appeal,
                "tier_pts": tier_pts,
                "form_pts": form_pts,
                "history_pts": history_pts,
                "driver_pts": driver_pts,
                "facility_pts": facility_pts,
                "museum_bonus": museum_bonus,
                "commercial_suite_tier": comm_suite_tier,
                "customer_racing_unlocked": bool(fac_tiers.get("mkt_customer_racing", 0) > 0)
            }




    def get_active_sponsors(self, team_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """Returns active sponsors grouped by slot tier ('TITLE', 'MIDDLE', 'MINOR'), including Pay-Driver Free Title Deals and Youth Loan Partners."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM active_sponsors WHERE team_id = ? ORDER BY slot_tier ASC, slot_index ASC;", (team_id,))
            rows = [dict(r) for r in cur.fetchall()]

            categorized = {"TITLE": [], "MIDDLE": [], "MINOR": []}
            for r in rows:
                categorized.get(r["slot_tier"], []).append(r)

            # Check for active PAY_DRIVER in team
            cur.execute("""
            SELECT name, pay_driver_sponsor_name, sponsor_income_per_race, contract_races_left, contract_seasons_left
            FROM drivers
            WHERE team_id = ? AND is_academy_driver = 0 AND driver_type = 'PAY_DRIVER' AND pay_driver_sponsor_name != '';
            """, (team_id,))
            for d in cur.fetchall():
                d_name, spon_name, income, r_left, s_left = d[0], d[1], float(d[2] or 0.0), d[3], d[4]
                races_display = f"{r_left} RACES" if r_left > 0 else f"{s_left} SEASONS"
                categorized["TITLE"].append({
                    "id": -99,
                    "team_id": team_id,
                    "slot_tier": "TITLE",
                    "slot_index": len(categorized["TITLE"]) + 1,
                    "brand_name": spon_name,
                    "color_hex": "#00d2be",
                    "races_total": r_left,
                    "races_remaining": races_display,
                    "signing_bonus": 0.0,
                    "per_race_payment": income,
                    "target_position": None,
                    "target_bonus": 0.0,
                    "is_pay_driver_sponsor": True,
                    "driver_name": d_name,
                    "sponsor_type_tag": f"PAY-DRIVER DEAL: {d_name}"
                })

            # Check for active SPONSORED_DRIVER in team (Youth Loan Talent Stipend as Minor Partner)
            cur.execute("""
            SELECT name, parent_team_name, sponsor_income_per_race, contract_races_left, contract_seasons_left
            FROM drivers
            WHERE team_id = ? AND is_academy_driver = 0 AND driver_type = 'SPONSORED_DRIVER' AND sponsor_income_per_race > 0;
            """, (team_id,))
            for d in cur.fetchall():
                d_name, parent_team, income, r_left, s_left = d[0], d[1], float(d[2] or 0.0), d[3], d[4]
                races_display = f"{r_left} RACES" if r_left > 0 else f"{s_left} SEASONS"
                categorized["MINOR"].append({
                    "id": -98,
                    "team_id": team_id,
                    "slot_tier": "MINOR",
                    "slot_index": len(categorized["MINOR"]) + 1,
                    "brand_name": parent_team,
                    "color_hex": "#ff8700",
                    "races_total": r_left,
                    "races_remaining": races_display,
                    "signing_bonus": 0.0,
                    "per_race_payment": income,
                    "target_position": None,
                    "target_bonus": 0.0,
                    "is_sponsored_loan": True,
                    "driver_name": d_name,
                    "sponsor_type_tag": f"YOUTH LOAN: {d_name}"
                })

            return categorized



    def get_sponsor_offers(self, team_id: int) -> List[Dict[str, Any]]:
        """Returns pending sponsor offers."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM sponsor_offers WHERE team_id = ?;", (team_id,))
            return [dict(r) for r in cur.fetchall()]

    def _insert_offer(self, cur, team_id: int, slot_tier: str, template: Dict[str, Any], current_appeal: int, team_tier: int):
        """Inserts a single sponsor offer row for the given team and brand template."""
        races = random.choice([6, 12, 18])
        tier_mult = {1: 5.0, 2: 2.2, 3: 1.0, 4: 0.4, 5: 0.15}.get(team_tier, 1.0)
        mult = (0.8 + (current_appeal / 100.0) * 0.5) * tier_mult
        signing_bonus = round(template["base_sign"] * mult, -3)
        per_race = round(template["base_per_race"] * mult, -3)
        target_bonus = round(template["target_bonus"] * mult, -3)

        cur.execute("""
        INSERT INTO sponsor_offers (
            team_id, slot_tier, brand_name, color_hex, races_total,
            signing_bonus, per_race_payment, target_position, target_bonus, required_appeal
        ) VALUES (
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?
        );
        """, (
            team_id, slot_tier, template["name"], template["color_hex"], races,
            signing_bonus, per_race, template["target_pos"], target_bonus, template["min_appeal"]
        ))

    def seed_initial_sponsor_offers(self, team_id: int):
        """
        Seeds starting sponsor offers for a new career:
        - 0 Title offers (locked behind reputation/appeal >= 40)
        - 1 Secondary offer (Middle tier)
        - 2 Minor offers (or 3 Minor offers on VERY_EASY difficulty)
        Ensures no duplicate brand names are offered.
        """
        appeal_data = self.calculate_sponsor_appeal(team_id)
        current_appeal = appeal_data["total_appeal"]

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT difficulty, tier FROM teams WHERE id = ?;", (team_id,))
            t_row = cur.fetchone()
            difficulty = t_row[0] if t_row else "NORMAL"
            team_tier = t_row[1] if t_row else 3

            # Clear existing pending offers for a clean start
            cur.execute("DELETE FROM sponsor_offers WHERE team_id = ?;", (team_id,))

            active = self.get_active_sponsors(team_id)
            used_brands = {s["brand_name"] for s_list in active.values() for s in s_list}

            # 1. Secondary offer (1 Middle sponsor)
            mid_eligible = [b for b in BRAND_CATALOG["MIDDLE"] if b["min_appeal"] <= current_appeal + 8 and b["name"] not in used_brands]
            if mid_eligible:
                chosen_mid = random.choice(mid_eligible)
                self._insert_offer(cur, team_id, "MIDDLE", chosen_mid, current_appeal, team_tier)
                used_brands.add(chosen_mid["name"])

            # 2. Minor offers (2 standard, 3 on VERY_EASY)
            minor_count = 3 if difficulty == "VERY_EASY" else 2
            min_eligible = [b for b in BRAND_CATALOG["MINOR"] if b["min_appeal"] <= current_appeal + 8 and b["name"] not in used_brands]
            random.shuffle(min_eligible)
            for template in min_eligible[:minor_count]:
                self._insert_offer(cur, team_id, "MINOR", template, current_appeal, team_tier)
                used_brands.add(template["name"])

            conn.commit()

    def check_and_generate_offers(self, team_id: int, is_progression: bool = False):
        """
        Manages sponsor offer pool.
        - If team has 0 active sponsors and 0 offers, seeds starting offers.
        - Does NOT generate offers during frame renders (is_progression=False) once initialized,
          preventing immediate full-slot saturation.
        - During calendar progression or post-race (is_progression=True), allows incoming offers
          up to target pending limits without duplicate brands.
        """
        active = self.get_active_sponsors(team_id)
        offers = self.get_sponsor_offers(team_id)

        total_active = sum(len(active.get(st, [])) for st in ["TITLE", "MIDDLE", "MINOR"])
        if total_active == 0 and len(offers) == 0:
            self.seed_initial_sponsor_offers(team_id)
            return

        if not is_progression:
            return

        appeal_data = self.calculate_sponsor_appeal(team_id)
        current_appeal = appeal_data["total_appeal"]

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT difficulty, tier FROM teams WHERE id = ?;", (team_id,))
            t_row = cur.fetchone()
            difficulty = t_row[0] if t_row else "NORMAL"
            team_tier = t_row[1] if t_row else 3

            minor_limit = 3 if difficulty == "VERY_EASY" else 2
            # Target pending offers per tier
            offer_targets = {
                "TITLE": 1 if current_appeal >= 40 and len(active.get("TITLE", [])) < 2 else 0,
                "MIDDLE": 1 if len(active.get("MIDDLE", [])) < 4 else 0,
                "MINOR": minor_limit if len(active.get("MINOR", [])) < 10 else 0
            }

            used_brands = {s["brand_name"] for s_list in active.values() for s in s_list} | {o["brand_name"] for o in offers}

            for slot_tier, target in offer_targets.items():
                tier_offers = [o for o in offers if o["slot_tier"] == slot_tier]
                if len(tier_offers) < target:
                    eligible = [b for b in BRAND_CATALOG[slot_tier] if b["min_appeal"] <= current_appeal + 8 and b["name"] not in used_brands]
                    if eligible:
                        chosen = random.choice(eligible)
                        self._insert_offer(cur, team_id, slot_tier, chosen, current_appeal, team_tier)
                        used_brands.add(chosen["name"])

            conn.commit()

    def sign_sponsor_offer(self, team_id: int, offer_id: int) -> Tuple[bool, str]:
        """Signs a pending sponsor offer into an available slot and awards the signing bonus."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM sponsor_offers WHERE id = ? AND team_id = ?;", (offer_id, team_id))
            offer = cur.fetchone()
            if not offer:
                return False, "Sponsor offer not found."

            slot_tier = offer["slot_tier"]
            limit = {"TITLE": 2, "MIDDLE": 4, "MINOR": 10}[slot_tier]

            cur.execute("SELECT COUNT(*) FROM active_sponsors WHERE team_id = ? AND slot_tier = ?;", (team_id, slot_tier))
            active_count = cur.fetchone()[0]
            if active_count >= limit:
                return False, f"All {limit} {slot_tier.lower()} sponsor slots are full."

            # Sign into active sponsors
            cur.execute("""
            INSERT INTO active_sponsors (
                team_id, slot_tier, slot_index, brand_name, color_hex, races_total,
                races_remaining, signing_bonus, per_race_payment, target_position, target_bonus
            ) VALUES (
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?
            );
            """, (
                team_id, slot_tier, active_count + 1, offer["brand_name"], offer["color_hex"],
                offer["races_total"], offer["races_total"], offer["signing_bonus"],
                offer["per_race_payment"], offer["target_position"], offer["target_bonus"]
            ))

            # Deposit signing bonus
            cur.execute("UPDATE teams SET cash = cash + ? WHERE id = ?;", (offer["signing_bonus"], team_id))
            cur.execute("""
            INSERT INTO ledger (team_id, week, category, description, amount)
            VALUES (?, 1, 'SPONSOR', ?, ?);
            """, (team_id, f"Signed Sponsor: {offer['brand_name']} Upfront Bonus", offer["signing_bonus"]))

            # Remove accepted offer
            cur.execute("DELETE FROM sponsor_offers WHERE id = ?;", (offer_id,))
            conn.commit()

        # Update official broadcast team name with active title sponsor
        self.update_effective_team_name(team_id)

        return True, f"Signed {offer['brand_name']}! Received ${offer['signing_bonus']:,.0f} signing bonus."

    def update_effective_team_name(self, team_id: int):
        """Updates team.name to prepend active TITLE sponsor brand name(s) to team.base_name."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT base_name FROM teams WHERE id = ?;", (team_id,))
            row = cur.fetchone()
            if not row:
                return
            base_name = row["base_name"] or "Player Racing"

            # Get active title sponsors (including Pay-Driver Title Sponsors)
            cur.execute("SELECT brand_name FROM active_sponsors WHERE team_id = ? AND slot_tier = 'TITLE' ORDER BY id ASC;", (team_id,))
            title_sponsors = [r["brand_name"] for r in cur.fetchall()]

            cur.execute("SELECT pay_driver_sponsor_name FROM drivers WHERE team_id = ? AND is_academy_driver = 0 AND driver_type = 'PAY_DRIVER' AND pay_driver_sponsor_name != '';", (team_id,))
            pay_sponsors = [r[0] for r in cur.fetchall() if r[0]]
            title_sponsors.extend(pay_sponsors)

            if title_sponsors:
                if len(title_sponsors) >= 2:
                    # Strip corporate suffixes for clean, authentic co-title team naming (e.g. "Solaris Apex Racing")
                    suffixes = {'Global', 'Telecom', 'Hyper', 'Energy', 'Aerospace', 'Capital', 'Microchips', 'Synthetics', 'Petroleum', 'Logistics', 'Automotive', 'Timepieces', 'Corporation', 'Corp', 'Inc', 'Ltd', 'Motors', 'Racing'}
                    short_brands = []
                    for b in title_sponsors:
                        cleaned = [w for w in b.split() if w not in suffixes]
                        short_brands.append(' '.join(cleaned) if cleaned else b.split()[0])
                    prefix = " ".join(short_brands)
                else:
                    prefix = title_sponsors[0]
                effective_name = f"{prefix} {base_name}"
            else:
                effective_name = base_name

            cur.execute("UPDATE teams SET name = ? WHERE id = ?;", (effective_name, team_id))
            conn.commit()

    def process_post_race_sponsor_payouts(self, team_id: int, best_finish_position: int) -> Dict[str, Any]:
        """
        Processes per-race fixed payments, checks performance bonus clauses,
        adds Pay-Driver Free Title Sponsor income and Sponsored Driver stipends,
        decrements contract races, and removes expired sponsorships.
        """
        fixed_total = 0.0
        bonus_total = 0.0
        driver_sponsor_total = 0.0
        expired = []

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM active_sponsors WHERE team_id = ?;", (team_id,))
            active = [dict(r) for r in cur.fetchall()]

            for s in active:
                fixed_total += s["per_race_payment"]
                
                # Check bonus objective
                if s["target_position"] and best_finish_position <= s["target_position"]:
                    bonus_total += s["target_bonus"]

                remaining = s["races_remaining"] - 1
                if remaining <= 0:
                    expired.append(s["brand_name"])
                    cur.execute("DELETE FROM active_sponsors WHERE id = ?;", (s["id"],))
                else:
                    cur.execute("UPDATE active_sponsors SET races_remaining = ? WHERE id = ?;", (remaining, s["id"]))

            # Add Pay-Driver Title Sponsors & Sponsored Driver Development Stipends
            cur.execute("""
            SELECT name, driver_type, sponsor_income_per_race, pay_driver_sponsor_name, parent_team_name 
            FROM drivers 
            WHERE team_id = ? AND is_academy_driver = 0 AND sponsor_income_per_race > 0;
            """, (team_id,))
            special_drivers = cur.fetchall()
            for d in special_drivers:
                d_inc = float(d[2])
                driver_sponsor_total += d_inc

            # Driver Commercial Suite VIP appearance bonus multiplier (+6% per tier)
            cur.execute("""
            SELECT current_tier FROM team_facilities 
            WHERE team_id = ? AND node_id = 'driver_commercial_suite' AND is_unlocked = 1;
            """, (team_id,))
            cs_row = cur.fetchone()
            cs_tier = int(cs_row[0]) if cs_row else 0
            if cs_tier > 0:
                bonus_total *= (1.0 + cs_tier * 0.06)

            # Credit team bank account
            total_sponsor_payout = fixed_total + bonus_total + driver_sponsor_total
            if total_sponsor_payout > 0:
                cur.execute("UPDATE teams SET cash = cash + ? WHERE id = ?;", (total_sponsor_payout, team_id))
                cur.execute("""
                INSERT INTO ledger (team_id, week, category, description, amount)
                VALUES (?, 1, 'SPONSOR', 'Post-Race Sponsor Payouts & Driver Sponsorship Deals', ?);
                """, (team_id, total_sponsor_payout))

            # Record race history
            cur.execute("""
            INSERT INTO race_history (team_id, season_num, round_num, finish_position, points_scored)
            VALUES (?, 1, 1, ?, 0);
            """, (team_id, best_finish_position))

            conn.commit()

        # Update official broadcast team name (reverts if title sponsor expired)
        self.update_effective_team_name(team_id)

        return {
            "fixed_payments": fixed_total,
            "bonus_payments": bonus_total,
            "driver_sponsorships": driver_sponsor_total,
            "total_payout": total_sponsor_payout,
            "expired_sponsors": expired
        }


