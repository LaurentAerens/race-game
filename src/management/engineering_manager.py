import random
from typing import Any, Dict, List, Optional, Tuple

from ..data.balance_config import BALANCE_REGISTRY
from ..database.career_db import CareerDatabase

ENGINE_SUPPLIERS = {
    # =========================================================================
    # TIER 3: National Open Cup Engines (70 to 82 HP)
    # =========================================================================
    "Vortex EcoTech": {
        "name": "Vortex EcoTech",
        "philosophy": "Entry Budget & Fuel Efficiency",
        "cost_season": 250000,
        "base_power": 70.0,
        "fuel_efficiency": 95.0,
        "reliability": 88.0,
        "min_tier": 3,
        "is_in_house": False,
    },
    "AeroStar Endurance": {
        "name": "AeroStar Endurance",
        "philosophy": "Bulletproof Reliability & Safe Points",
        "cost_season": 800000,
        "base_power": 76.0,
        "fuel_efficiency": 88.0,
        "reliability": 95.0,
        "min_tier": 3,
        "is_in_house": False,
    },
    "Titan Velocity": {
        "name": "Titan Velocity",
        "philosophy": "Maximum Peak Horsepower",
        "cost_season": 1200000,
        "base_power": 82.0,
        "fuel_efficiency": 74.0,
        "reliability": 72.0,
        "min_tier": 3,
        "is_in_house": False,
    },
    # =========================================================================
    # TIER 2: Continental Championship Engines (300 to 400 HP)
    # =========================================================================
    "CosmoSpec Customer V6": {
        "name": "CosmoSpec Customer V6",
        "philosophy": "Post-Promotion Survival Budget Unit",
        "cost_season": 1200000,
        "base_power": 310.0,
        "fuel_efficiency": 90.0,
        "reliability": 86.0,
        "min_tier": 2,
        "is_in_house": False,
    },
    "AeroTorque Endurance V6": {
        "name": "AeroTorque Endurance V6",
        "philosophy": "High Thermal Efficiency & Extreme Reliability",
        "cost_season": 4500000,
        "base_power": 350.0,
        "fuel_efficiency": 88.0,
        "reliability": 94.0,
        "min_tier": 2,
        "is_in_house": False,
    },
    "Apex High-Rev V8": {
        "name": "Apex High-Rev V8",
        "philosophy": "High-RPM Aggressive Performance Power Unit",
        "cost_season": 8500000,
        "base_power": 395.0,
        "fuel_efficiency": 80.0,
        "reliability": 82.0,
        "min_tier": 2,
        "is_in_house": False,
    },
    # =========================================================================
    # TIER 1: World Super Formula Engines (700 to 810 HP Customer, In-House 600 -> 1000+ HP)
    # =========================================================================
    "Formula Standard Customer V6": {
        "name": "Formula Standard Customer V6",
        "philosophy": "Post-Promotion Baseline Customer Unit",
        "cost_season": 5000000,
        "base_power": 710.0,
        "fuel_efficiency": 90.0,
        "reliability": 88.0,
        "min_tier": 1,
        "is_in_house": False,
    },
    "Solaris Quantum Hybrid V6": {
        "name": "Solaris Quantum Hybrid V6",
        "philosophy": "Elite Midfield Customer Hybrid System",
        "cost_season": 35000000,
        "base_power": 765.0,
        "fuel_efficiency": 92.0,
        "reliability": 92.0,
        "min_tier": 1,
        "is_in_house": False,
    },
    "Scuderia Factory Hyper-V6": {
        "name": "Scuderia Factory Hyper-V6",
        "philosophy": "Pinnacle World Championship Factory Engine",
        "cost_season": 65000000,
        "base_power": 810.0,
        "fuel_efficiency": 94.0,
        "reliability": 94.0,
        "min_tier": 1,
        "is_in_house": False,
    },
    "Works In-House V6 Turbo": {
        "name": "Works In-House V6 Turbo",
        "philosophy": "Full Bespoke Works Power Unit ($0 Supplier Fee, Unlimited Evolution)",
        "cost_season": 0,
        "base_power": 600.0,
        "fuel_efficiency": 92.0,
        "reliability": 85.0,
        "min_tier": 1,
        "is_in_house": True,
    },
}


FACTORY_PART_SPECS = {
    # Tier 3: National Open Cup (Spec supplier parts, baseline ~65% durability)
    3: {
        "BRAKES": {"name": "Factory Spec Calipers & Discs", "cost": 75000.0, "perf": 65.0, "durability": 65.0},
        "FRONT_WING": {"name": "Factory Standard Front Wing", "cost": 95000.0, "perf": 66.0, "durability": 65.0},
        "REAR_WING": {"name": "Factory Spec Rear Wing & Gurney", "cost": 85000.0, "perf": 66.0, "durability": 65.0},
        "SUSPENSION": {"name": "Factory Spec Pushrod Dampers", "cost": 90000.0, "perf": 64.0, "durability": 65.0},
        "FLOOR": {"name": "Factory Molded Underbody Plank", "cost": 110000.0, "perf": 68.0, "durability": 65.0},
        "ENGINE": {"name": "Standard Customer Engine Refresh", "cost": 140000.0, "perf": 72.0, "durability": 65.0},
        "ERS": {"name": "Basic Alternator Unit", "cost": 45000.0, "perf": 0.0, "durability": 65.0},
    },
    # Tier 2: Continental Championship (Midfield, ~72% durability, ~3-4x Tier 3 cost)
    2: {
        "BRAKES": {"name": "Continental Carbon Calipers & Pads", "cost": 250000.0, "perf": 95.0, "durability": 72.0},
        "FRONT_WING": {"name": "Continental Aero Spec Front Wing", "cost": 320000.0, "perf": 96.0, "durability": 72.0},
        "REAR_WING": {
            "name": "Continental High-Downforce Rear Wing",
            "cost": 350000.0,
            "perf": 96.0,
            "durability": 72.0,
        },
        "SUSPENSION": {"name": "Continental Multi-Way Damper Pack", "cost": 380000.0, "perf": 94.0, "durability": 72.0},
        "FLOOR": {"name": "Continental Venturi Underfloor", "cost": 420000.0, "perf": 98.0, "durability": 72.0},
        "ENGINE": {"name": "CosmoSpec Customer V6 Refresh", "cost": 500000.0, "perf": 320.0, "durability": 72.0},
        "ERS": {"name": "Standard Hybrid Motor Generator", "cost": 280000.0, "perf": 50.0, "durability": 72.0},
    },
    # Tier 1: World Super Formula (Pinnacle, ~80% durability, ~5-8x Tier 2 cost)
    1: {
        "BRAKES": {"name": "Grand Prix Carbon-Carbon Brake Set", "cost": 1200000.0, "perf": 140.0, "durability": 80.0},
        "FRONT_WING": {"name": "Grand Prix Customer Front Wing", "cost": 1500000.0, "perf": 145.0, "durability": 80.0},
        "REAR_WING": {"name": "Grand Prix Active DRS Rear Wing", "cost": 1650000.0, "perf": 145.0, "durability": 80.0},
        "SUSPENSION": {
            "name": "Grand Prix Active Inerter Suspension",
            "cost": 1750000.0,
            "perf": 140.0,
            "durability": 80.0,
        },
        "FLOOR": {
            "name": "Grand Prix Ground-Effect Diffuser Floor",
            "cost": 2400000.0,
            "perf": 150.0,
            "durability": 80.0,
        },
        "ENGINE": {"name": "Customer Hyper-V6 Power Unit Lease", "cost": 3500000.0, "perf": 760.0, "durability": 80.0},
        "ERS": {"name": "FIA Spec MGU-K & Battery Pack", "cost": 2200000.0, "perf": 100.0, "durability": 80.0},
    },
}


COMPONENT_FACILITY_MAP = {
    "BRAKES": ("eng_brakes", "Brakes Engineering Lab"),
    "FRONT_WING": ("eng_wings_front", "Front Aero & Wing Facility"),
    "REAR_WING": ("eng_wings_rear", "Rear Aero & Wing Facility"),
    "SUSPENSION": ("eng_suspension", "Chassis & Setup Workshop"),
    "ENGINE": ("eng_tuning", "Engine Tuning Facility"),
    "FLOOR": ("eng_floor", "Floor & Diffusers Lab"),
    "ERS": ("eng_ers", "ERS & Hybrid Systems Lab"),
}

RELEVANT_COMPONENT_FACILITIES = {
    "BRAKES": [
        "eng_brakes",
        "eng_thermal_rig",
        "mfg_cnc_machining",
        "mfg_additive_metal",
        "eng_comp_materials",
        "test_qa_ndt",
        "eng_workshop",
    ],
    "FRONT_WING": [
        "eng_wings_front",
        "eng_windtunnel",
        "eng_cfd",
        "eng_aero_scanning",
        "eng_aero_model_shop",
        "mfg_cleanroom_autoclave",
        "mfg_prepreg_freezer",
        "mfg_rapid_tooling",
        "mfg_paint_bay",
        "test_qa_ndt",
        "eng_workshop",
    ],
    "REAR_WING": [
        "eng_wings_rear",
        "eng_windtunnel",
        "eng_cfd",
        "eng_aero_scanning",
        "eng_aero_model_shop",
        "mfg_cleanroom_autoclave",
        "mfg_prepreg_freezer",
        "mfg_rapid_tooling",
        "mfg_paint_bay",
        "test_qa_ndt",
        "eng_workshop",
    ],
    "FLOOR": [
        "eng_floor",
        "eng_windtunnel",
        "eng_cfd",
        "eng_aero_scanning",
        "test_shaker_rig",
        "mfg_cleanroom_autoclave",
        "mfg_prepreg_freezer",
        "eng_comp_materials",
        "test_qa_ndt",
        "eng_workshop",
    ],
    "SUSPENSION": [
        "eng_suspension",
        "eng_kinematics_lab",
        "test_shaker_rig",
        "test_torsional_rig",
        "mfg_cnc_machining",
        "mfg_additive_metal",
        "mfg_monocoque_jig",
        "eng_comp_materials",
        "test_qa_ndt",
        "eng_workshop",
    ],
    "ENGINE": [
        "eng_tuning",
        "eng_dyno",
        "eng_works_powertrain",
        "eng_thermal_rig",
        "mfg_exotic_welding",
        "mfg_electronics",
        "mfg_additive_metal",
        "test_qa_ndt",
        "eng_workshop",
    ],
    "ERS": ["eng_ers", "eng_dyno", "mfg_electronics", "test_qa_ndt", "eng_workshop"],
}


from src.management.staff_manager import StaffManager


class EngineeringManager:
    """Handles car components, manufacturing, factory tech tree, and R&D pipelines."""

    FACTORY_PART_SPECS = FACTORY_PART_SPECS
    ENGINE_SUPPLIERS = ENGINE_SUPPLIERS

    def __init__(self, db: CareerDatabase):
        self.db = db
        self.staff_manager = StaffManager(self.db)

    def get_team_components(self, team_id: int) -> List[Dict[str, Any]]:
        return self.db.get_team_components(team_id)

    def get_team_facilities(self, team_id: int) -> List[Dict[str, Any]]:
        return self.db.get_team_facilities(team_id)

    def get_facility_status_for_component(self, team_id: int, category: str) -> Tuple[bool, int, str]:
        """Checks whether the dedicated facility for this component category is unlocked and built."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            if category == "ENGINE":
                cur.execute(
                    """
                SELECT is_unlocked, current_tier, node_id FROM team_facilities 
                WHERE team_id = ? AND node_id IN ('eng_tuning', 'eng_works_powertrain');
                """,
                    (team_id,),
                )
                rows = cur.fetchall()
                tuning_built = any(r[0] and r[1] >= 1 and r[2] == "eng_tuning" for r in rows)
                works_built = any(r[0] and r[1] >= 1 and r[2] == "eng_works_powertrain" for r in rows)
                if works_built:
                    return True, 2, "Works Engine Factory"
                if tuning_built:
                    return True, 1, "Engine Tuning Facility"
                return False, 0, "Engine Tuning Facility"

            fac_info = COMPONENT_FACILITY_MAP.get(category)
            if not fac_info:
                return True, 1, ""
            fac_node, fac_name = fac_info
            cur.execute(
                "SELECT is_unlocked, current_tier FROM team_facilities WHERE team_id = ? AND node_id = ?;",
                (team_id, fac_node),
            )
            row = cur.fetchone()
            if row and row[0] and row[1] >= 1:
                return True, int(row[1]), fac_name
            return False, 0, fac_name

    def process_post_race_telemetry(
        self,
        team_id: int,
        driver_tech_skill: float,
        driver_comm_skill: float,
        telemetry_rig_level: int = 1,
        dev_gain_mult: float = 1.0,
        negative_penalty_mult: float = 1.0,
    ):
        """
        Gathers race telemetry and expands the knowledge pool for each active component on Car 1 & Car 2.
        - Knowledge growth is strictly driven by the dedicated facility tier (Tier 0 = 0.0 knowledge gain).
        - Facilities grant single-digit baseline knowledge gains per race (scaled by difficulty dev_gain_mult).
        - Installed equipment rigs grant 0.X performance and reliability bonuses per race (scaled by difficulty).
        - Negative trade-offs reverse-scale with difficulty (Easy = lower penalty, Hard = harsher penalty).
        - Both facility and equipment knowledge gains scale with concept diminishing returns (races 1–6).
        - Driver technical understanding & communication accelerate telemetry insight.
        """
        components = self.get_team_components(team_id)

        with self.db.get_connection() as conn:
            cur = conn.cursor()

            # Query Next-Gen R&D Allocation % to dampen current-season telemetry
            cur.execute("SELECT next_gen_rnd_pct FROM teams WHERE id = ?;", (team_id,))
            ng_row = cur.fetchone()
            next_gen_pct = float(ng_row[0]) if ng_row and ng_row[0] else 0.0
            telemetry_split_mult = max(0.2, 1.0 - (next_gen_pct / 100.0))

            cur.execute(
                """
            SELECT node_id, current_tier, is_unlocked FROM team_facilities 
            WHERE team_id = ?;
            """,
                (team_id,),
            )
            fac_rows = cur.fetchall()
            facility_tiers = {r["node_id"]: (r["current_tier"] if r["is_unlocked"] else 0) for r in fac_rows}

            # Fetch active equipment bonuses
            cur.execute(
                """
            SELECT fe.node_id, fe.perf_bonus_per_level, fe.rel_bonus_per_level, te.current_level
            FROM facility_equipment fe
            JOIN team_equipment te ON fe.id = te.equipment_id
            WHERE te.team_id = ? AND te.is_active = 1 AND te.current_level > 0;
            """,
                (team_id,),
            )
            eq_rows = cur.fetchall()
            equipment_by_node = {}
            for r in eq_rows:
                nid = r["node_id"]
                if nid not in equipment_by_node:
                    equipment_by_node[nid] = []
                equipment_by_node[nid].append(
                    (
                        float(r["perf_bonus_per_level"]) * int(r["current_level"]),
                        float(r["rel_bonus_per_level"]) * int(r["current_level"]),
                    )
                )

            # Driver insight multiplier (0.75x to 1.6x)
            radio_tier = facility_tiers.get("driver_radio_comms_lab", 0)
            radio_eq_level = 0
            if "driver_radio_comms_lab" in equipment_by_node:
                radio_eq_level = len(equipment_by_node["driver_radio_comms_lab"])
            radio_factor = (radio_tier * 0.15) + (radio_eq_level * 0.03)

            driver_factor = (
                0.75
                + (driver_tech_skill / 100.0) * 0.35
                + (driver_comm_skill / 100.0) * 0.25
                + 0.05 * telemetry_rig_level
                + radio_factor
            )

            wt_tier = facility_tiers.get("eng_windtunnel", 0)
            cfd_tier = facility_tiers.get("eng_cfd", 0)
            aero_scan_tier = facility_tiers.get("eng_aero_scanning", 0)
            model_tier = facility_tiers.get("eng_aero_model_shop", 0)
            cleanroom_tier = facility_tiers.get("mfg_cleanroom_autoclave", 0)
            paint_tier = facility_tiers.get("mfg_paint_bay", 0)

            comp_mat_tier = facility_tiers.get("eng_comp_materials", 0)
            cnc_tier = facility_tiers.get("mfg_cnc_machining", 0)
            kin_tier = facility_tiers.get("eng_kinematics_lab", 0)
            shaker_tier = facility_tiers.get("test_shaker_rig", 0)
            metal_3d_tier = facility_tiers.get("mfg_additive_metal", 0)
            torsion_tier = facility_tiers.get("test_torsional_rig", 0)

            dyno_tier = facility_tiers.get("eng_dyno", 0)
            thermal_tier = facility_tiers.get("eng_thermal_rig", 0)
            elec_tier = facility_tiers.get("mfg_electronics", 0)
            weld_tier = facility_tiers.get("mfg_exotic_welding", 0)

            ndt_tier = facility_tiers.get("test_qa_ndt", 0)
            tuning_tier = facility_tiers.get("eng_tuning", 0)
            works_tier = facility_tiers.get("eng_works_powertrain", 0)
            uplink_tier = facility_tiers.get("track_comm_uplink", 0)

            # Uplink facility & equipment multipliers (cross-cutting to all components)
            uplink_sat_lvl = 0
            uplink_edge_lvl = 0
            if "track_comm_uplink" in equipment_by_node:
                uplink_sat_lvl = sum(1 for p, r in equipment_by_node["track_comm_uplink"])
            uplink_perf_mult = 1.0 + (uplink_tier * 0.15) + (uplink_sat_lvl * 0.05)
            uplink_rel_mult = 1.0 + (uplink_tier * 0.12) + (uplink_edge_lvl * 0.04)

            for comp in components:
                cat = comp["category"]

                if cat == "ENGINE":
                    fac_tier = max(tuning_tier, works_tier)
                else:
                    fac_info = COMPONENT_FACILITY_MAP.get(cat)
                    if not fac_info:
                        continue
                    fac_node, _ = fac_info
                    fac_tier = facility_tiers.get(fac_node, 0)

                # If facility is unbuilt/locked (tier 0) -> NO knowledge growth from telemetry!
                if fac_tier == 0:
                    continue

                # Base facility multiplier: Tier 1: 1.0x, Tier 2: 1.65x, Tier 3: 2.3x
                fac_mult = 1.0 + (fac_tier - 1) * 0.65

                # Cross-cutting facility bonuses (Performance):
                cross_mult = 1.0

                # Wind Tunnel impacts all parts EXCEPT engine/ers (5 parts: Front Wing, Rear Wing, Floor, Suspension, Brakes)
                if cat in ["FRONT_WING", "REAR_WING", "FLOOR", "SUSPENSION", "BRAKES"]:
                    cross_mult *= 1.0 + wt_tier * 0.08

                if cat in ["FRONT_WING", "REAR_WING", "FLOOR"]:
                    cross_mult *= (1.0 + cfd_tier * 0.12) * (1.0 + aero_scan_tier * 0.10) * (1.0 + model_tier * 0.08)
                    # Torsional Rig slight weight/perf trade-off for high rigidity
                    if torsion_tier > 0:
                        cross_mult *= 1.0 - torsion_tier * 0.02

                if cat in ["FRONT_WING", "REAR_WING", "FLOOR", "SUSPENSION"]:
                    # Autoclave & Paint: Aggressive lightweighting yields high performance (+12% & +8%)
                    cross_mult *= (1.0 + cleanroom_tier * 0.12) * (1.0 + paint_tier * 0.08)

                if cat in ["SUSPENSION", "BRAKES"]:
                    cross_mult *= (1.0 + comp_mat_tier * 0.15) * (1.0 + kin_tier * 0.12) * (1.0 + shaker_tier * 0.15)

                if cat in ["SUSPENSION", "BRAKES", "ENGINE"]:
                    cross_mult *= 1.0 + cnc_tier * 0.10

                if cat in ["SUSPENSION", "BRAKES", "ERS"]:
                    cross_mult *= 1.0 + metal_3d_tier * 0.09

                if cat in ["ENGINE", "ERS"]:
                    cross_mult *= (1.0 + dyno_tier * 0.18) * (1.0 + elec_tier * 0.14) * (1.0 + weld_tier * 0.13)
                    # Engine tuning aggressive boost mapping (+15% HP)
                    if cat == "ENGINE" and tuning_tier > 0:
                        cross_mult *= 1.0 + tuning_tier * 0.15

                if cat in ["ENGINE", "ERS", "BRAKES"]:
                    cross_mult *= 1.0 + thermal_tier * 0.11

                # QA & NDT Lab conservative screening: blocks risky bleeding-edge designs (-4% perf penalty across all parts)
                if ndt_tier > 0:
                    cross_mult *= 1.0 - ndt_tier * 0.04

                fac_node_id = (
                    fac_node if cat != "ENGINE" else ("eng_works_powertrain" if works_tier > 0 else "eng_tuning")
                )
                staff_out = self.staff_manager.calculate_facility_staff_output(
                    team_id, fac_node_id, fac_tier, dev_gain_mult
                )
                staff_mult = staff_out["staff_mult"]

                eff_fac_perf = fac_mult * staff_mult
                total_insight = eff_fac_perf * cross_mult * driver_factor * dev_gain_mult * uplink_perf_mult

                # Cross-cutting facility bonuses (Reliability & Mechanical Failure Prevention):
                # QA & NDT Lab delivers a massive reliability boost (+35% per tier) across ALL components
                rel_cross_mult = 1.0 + ndt_tier * 0.35

                # Autoclave & Paint lightweighting slight reliability strain (-5% & -3% on composites)
                if cat in ["FRONT_WING", "REAR_WING", "FLOOR", "SUSPENSION"]:
                    if cleanroom_tier > 0:
                        rel_cross_mult *= 1.0 - cleanroom_tier * 0.05
                    if paint_tier > 0:
                        rel_cross_mult *= 1.0 - paint_tier * 0.03
                    if torsion_tier > 0:
                        rel_cross_mult *= 1.0 + torsion_tier * 0.14

                # Engine tuning slight thermal stress penalty on reliability (-6%)
                if cat == "ENGINE" and tuning_tier > 0:
                    rel_cross_mult *= 1.0 - tuning_tier * 0.06

                # Powertrain stress testing, welding & electronics reinforce reliability
                if cat in ["ENGINE", "ERS"]:
                    rel_cross_mult *= (1.0 + dyno_tier * 0.22) * (1.0 + elec_tier * 0.15) * (1.0 + weld_tier * 0.14)
                elif cat in ["SUSPENSION", "BRAKES"]:
                    rel_cross_mult *= (1.0 + comp_mat_tier * 0.18) * (1.0 + torsion_tier * 0.16)

                if cat in ["ENGINE", "ERS", "BRAKES"]:
                    rel_cross_mult *= 1.0 + thermal_tier * 0.12

                eff_fac_rel = fac_mult * staff_mult
                total_rel_insight = eff_fac_rel * rel_cross_mult * driver_factor * dev_gain_mult * uplink_rel_mult

                # Sum equipment 0.X bonuses from all relevant facilities with difficulty scaling
                relevant_nodes = RELEVANT_COMPONENT_FACILITIES.get(cat, ["eng_workshop"])
                eq_perf_bonus = 0.0
                eq_rel_bonus = 0.0
                for n in relevant_nodes:
                    if n in equipment_by_node:
                        for p_b, r_b in equipment_by_node[n]:
                            # Scale performance: positive with dev_gain_mult, negative with negative_penalty_mult
                            if p_b > 0:
                                eq_perf_bonus += p_b * dev_gain_mult
                            elif p_b < 0:
                                eq_perf_bonus += p_b * negative_penalty_mult

                            # Scale reliability: positive with dev_gain_mult, negative with negative_penalty_mult
                            if r_b > 0:
                                eq_rel_bonus += r_b * dev_gain_mult
                            elif r_b < 0:
                                eq_rel_bonus += r_b * negative_penalty_mult

                races = comp["races_on_concept"] + 1
                cur_min = comp["knowledge_min"]
                cur_max = comp["knowledge_max"]
                cur_rel_min = comp.get("rel_knowledge_min", 0.0) or 0.0
                cur_rel_max = comp.get("rel_knowledge_max", 0.0) or 0.0

                # Diminishing returns curve for both Facility (single-digit) and Equipment (0.X)
                if races == 1:
                    race_factor = 1.0
                    base_perf_min = random.uniform(3.5, 5.0)
                    base_perf_max = random.uniform(5.5, 7.5)
                    base_rel_min = random.uniform(2.0, 3.5)
                    base_rel_max = random.uniform(3.5, 5.0)
                elif races <= 3:
                    race_factor = 0.50
                    base_perf_min = random.uniform(2.0, 3.2)
                    base_perf_max = random.uniform(3.5, 4.8)
                    base_rel_min = random.uniform(1.0, 1.8)
                    base_rel_max = random.uniform(1.8, 2.8)
                elif races <= 5:
                    race_factor = 0.25
                    base_perf_min = random.uniform(1.0, 1.8)
                    base_perf_max = random.uniform(1.8, 2.6)
                    base_rel_min = random.uniform(0.5, 1.0)
                    base_rel_max = random.uniform(1.0, 1.6)
                else:
                    race_factor = 0.10
                    base_perf_min = 0.2
                    base_perf_max = 0.8
                    base_rel_min = 0.1
                    base_rel_max = 0.5

                eq_perf_add = eq_perf_bonus * race_factor * driver_factor
                eq_rel_add = eq_rel_bonus * race_factor * driver_factor

                add_min = round(((base_perf_min * total_insight) + (eq_perf_add * 0.8)) * telemetry_split_mult, 1)
                add_max = round(((base_perf_max * total_insight) + (eq_perf_add * 1.2)) * telemetry_split_mult, 1)
                rel_add_min = round(((base_rel_min * total_rel_insight) + (eq_rel_add * 0.8)) * telemetry_split_mult, 1)
                rel_add_max = round(((base_rel_max * total_rel_insight) + (eq_rel_add * 1.2)) * telemetry_split_mult, 1)

                if add_max < add_min:
                    add_max = add_min
                if rel_add_max < rel_add_min:
                    rel_add_max = rel_add_min

                new_min = round(cur_min + add_min, 1)
                new_max = round(cur_max + add_max, 1)
                new_rel_min = round(cur_rel_min + rel_add_min, 1)
                new_rel_max = round(cur_rel_max + rel_add_max, 1)

                cur.execute(
                    """
                UPDATE car_components 
                SET knowledge_min = ?, knowledge_max = ?, rel_knowledge_min = ?, rel_knowledge_max = ?, races_on_concept = ?
                WHERE id = ?;
                """,
                    (new_min, new_max, new_rel_min, new_rel_max, races, comp["id"]),
                )
            conn.commit()

    def get_team_allowed_parts(self, team_id: int) -> Tuple[int, str, List[str]]:
        """Returns the team's current league tier, league name, and list of allowed custom R&D parts."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            SELECT t.tier, l.name as league_name, l.custom_parts_allowed 
            FROM teams t 
            LEFT JOIN leagues l ON t.tier = l.tier 
            WHERE t.id = ?;
            """,
                (team_id,),
            )
            row = cur.fetchone()
            if not row:
                return 3, "National Open Cup", ["BRAKES", "FRONT_WING"]
            tier = row["tier"] or 3
            l_name = row["league_name"] or "National Open Cup"
            if tier >= 3:
                # In Tier 3, custom R&D is allowed for Brakes & Front Wing; Rear Wings, Suspension, Floor, Engine are bought as factory supplier parts
                return 3, l_name, ["BRAKES", "FRONT_WING"]
            elif tier == 2:
                return 2, l_name, ["BRAKES", "FRONT_WING", "REAR_WING", "SUSPENSION", "ENGINE"]
            else:
                return 1, l_name, ["BRAKES", "FRONT_WING", "REAR_WING", "SUSPENSION", "ENGINE", "FLOOR", "ERS"]

    def build_next_generation_part(
        self, team_id: int, component_id: int, cost_mult: float = 1.0
    ) -> Tuple[bool, str, float]:
        """
        Builds the next generation of a component:
        - Tier 3: Brakes and Front Wing custom builds allowed. Rear Wings, Suspension, Floor, Engine are bought factory.
        - Tier 2: Unlocks Rear Wings, Suspension, and Engine Fine-Tuning.
        - Tier 1: Full Constructor Freedom including Full Power Unit R&D and bespoke builds.
        - Durability accumulates progressively with telemetry knowledge and facility bonuses (+10% to +15% per Mk build),
          smoothly surpassing 100%+ in Tier 3 and scaling to 200%-500% with elite Tier 1 facilities!
        """
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM car_components WHERE id = ? AND team_id = ?;", (component_id, team_id))
            comp = cur.fetchone()
            if not comp:
                return False, "Component not found.", 0.0

            # 1. Check League Tier Regulations
            tier, l_name, allowed_parts = self.get_team_allowed_parts(team_id)
            if comp["category"] == "ENGINE" and tier == 3:
                return (
                    False,
                    f"Engine R&D is PROHIBITED in Tier 3 ({l_name}). Power units are customer engines contracted at season start.",
                    0.0,
                )

            if "SPEC" in allowed_parts or comp["category"] not in allowed_parts:
                return (
                    False,
                    f"{comp['category']} development is SPEC REGULATED in Tier {tier} ({l_name}). Purchase Factory Supplier parts in the warehouse or earn promotion to unlock custom R&D!",
                    0.0,
                )

            # 2. Check Dedicated Facility Unlock (Must be Level >= 1)
            if comp["category"] == "ENGINE":
                if tier == 1:
                    cur.execute(
                        "SELECT is_unlocked, current_tier FROM team_facilities WHERE team_id = ? AND node_id = 'eng_works_powertrain';",
                        (team_id,),
                    )
                    f_row = cur.fetchone()
                    if not f_row or not f_row[0] or f_row[1] < 1:
                        return (
                            False,
                            "Cannot manufacture Works ENGINE. Construct Level 1 of Works Engine Factory in the Factory first.",
                            0.0,
                        )
                else:
                    cur.execute(
                        "SELECT is_unlocked, current_tier FROM team_facilities WHERE team_id = ? AND node_id = 'eng_tuning';",
                        (team_id,),
                    )
                    f_row = cur.fetchone()
                    if not f_row or not f_row[0] or f_row[1] < 1:
                        return (
                            False,
                            "Cannot fine-tune ENGINE. Construct Level 1 of Engine Tuning Facility in the Factory first.",
                            0.0,
                        )
            else:
                fac_info = COMPONENT_FACILITY_MAP.get(comp["category"])
                if fac_info:
                    fac_node, fac_name = fac_info
                    cur.execute(
                        """
                    SELECT is_unlocked, current_tier FROM team_facilities 
                    WHERE team_id = ? AND node_id = ?;
                    """,
                        (team_id, fac_node),
                    )
                    fac_row = cur.fetchone()
                    if not fac_row or not fac_row[0] or fac_row[1] < 1:
                        return (
                            False,
                            f"Cannot manufacture {comp['category']} Mk {comp['generation'] + 1}. Construct Level 1 of {fac_name} in the Factory first.",
                            0.0,
                        )

            cur.execute("SELECT cash FROM teams WHERE id = ?;", (team_id,))
            cash = float(cur.fetchone()[0])

            # Base manufacturing costs per component type scaled by league tier from centralized balance registry
            base_cost = BALANCE_REGISTRY.get_part_build_cost(tier, comp["category"])
            build_cost = base_cost * cost_mult

            if cash < build_cost:
                return False, f"Insufficient funds. Need ${build_cost:,.0f}.", 0.0

            # Dedicated facility tier level for this component category
            fac_info = COMPONENT_FACILITY_MAP.get(comp["category"])
            fac_node_chk = (
                fac_info[0] if fac_info else ("eng_tuning" if comp["category"] == "ENGINE" else "eng_workshop")
            )
            cur.execute(
                "SELECT current_tier, is_unlocked FROM team_facilities WHERE team_id = ? AND node_id = ?;",
                (team_id, fac_node_chk),
            )
            fac_n_row = cur.fetchone()
            fac_lvl = fac_n_row[0] if (fac_n_row and fac_n_row[1]) else 1

            # 0 races on concept = 0 improvement
            rk_min = comp["rel_knowledge_min"] if "rel_knowledge_min" in comp.keys() else 0.0
            rk_max = comp["rel_knowledge_max"] if "rel_knowledge_max" in comp.keys() else 0.0
            is_breakthrough = False

            if comp["races_on_concept"] == 0 or (comp["knowledge_max"] <= 0.0 and rk_max <= 0.0):
                gain = 0.0
                rel_gain = 0.0
            else:
                # Breakthrough innovation chance: boosted by facility tier, staff output, and luck
                # Breakthrough chance: 12% base + 8% per facility tier level above 1 (max 28% at Level 3)
                breakthrough_chance = 0.12 + max(0, fac_lvl - 1) * 0.08
                is_breakthrough = random.random() < breakthrough_chance
                breakthrough_mult = random.uniform(1.30, 1.50) if is_breakthrough else 1.0

                if comp["category"] == "ENGINE" and tier == 2:
                    # Tier 2 Engine Fine-Tuning: calibration improvement (+1.5 to +4.5 HP per build, totaling up to ~20 HP over a season)
                    raw_gain = random.uniform(comp["knowledge_min"], comp["knowledge_max"])
                    gain = round(min(4.5 * breakthrough_mult, max(1.0, raw_gain * 0.35 * breakthrough_mult)), 1)
                elif comp["category"] == "ENGINE" and tier == 1:
                    # Tier 1 Engine R&D: full bespoke development gains (unconstrained, enabling progression to 1000+ HP over seasons)
                    gain = round(random.uniform(comp["knowledge_min"], comp["knowledge_max"]) * breakthrough_mult, 1)
                else:
                    gain = round(random.uniform(comp["knowledge_min"], comp["knowledge_max"]) * breakthrough_mult, 1)

                if rk_max > 0.0:
                    rel_gain = round(random.uniform(rk_min, rk_max) * (1.15 if is_breakthrough else 1.0), 1)
                else:
                    rel_gain = 0.0

            # Scale build gain by next-gen R&D allocation
            cur.execute("SELECT next_gen_rnd_pct FROM teams WHERE id = ?;", (team_id,))
            ng_res = cur.fetchone()
            next_gen_split = float(ng_res[0]) if ng_res and ng_res[0] else 0.0
            build_damp = max(0.5, 1.0 - 0.5 * (next_gen_split / 100.0))
            gain = round(gain * build_damp, 1)

            # Performance ceiling scales with dedicated facility tier level (fac_lvl):
            # Level 1: Starter workshop capability -> up to ~1.85x baseline (~120-130 pts in T3, ~175 in T2)
            # Level 2: Professional lab capability -> up to ~2.65x baseline (~172-185 pts in T3, ~250 in T2)
            # Level 3: Apex facility capability   -> full 3.0x peak potential (up to 3.0x baseline)
            # Special tuning for FLOOR & ERS: Level 1 provides entry capability (~75-80 pts); requires Level 2/3 for peak Tier 1 downforce/power
            tier_specs = FACTORY_PART_SPECS.get(tier, FACTORY_PART_SPECS[3])
            base_perf_baseline = tier_specs.get(comp["category"], {}).get("perf", 65.0)
            if comp["category"] in ["FLOOR", "ERS"] and tier == 1:
                # Level 1 in Tier 1: Entry level only (~85 perf), not enough for World Championship without Level 2/3
                fac_cap_mult = {1: 0.65, 2: 1.65, 3: 2.80}.get(fac_lvl, 1.0)
                max_allowed_perf = round(base_perf_baseline * fac_cap_mult, 1)
            else:
                fac_cap_mult = {1: 1.85, 2: 2.65, 3: 3.0}.get(fac_lvl, 2.0)
                max_allowed_perf = round(base_perf_baseline * fac_cap_mult, 1)

            new_perf = min(max_allowed_perf, round(comp["performance"] + gain, 1))
            new_gen = comp["generation"] + 1

            # Progressive uncapped Durability calculation
            cur_dur = (
                comp["max_durability"]
                if "max_durability" in comp.keys() and comp["max_durability"]
                else {1: 80.0, 2: 72.0, 3: 65.0}.get(tier, 65.0)
            )
            durability_gain = round(max(8.0, rel_gain * 1.20), 1)
            new_max_durability = round(cur_dur + durability_gain, 1)

            # Dynamic Reliability & Mechanical Strain Trade-Off:
            # Pushing components towards peak performance imposes mechanical stress.
            # Breakthrough innovations trade short-term reliability for speed leaps (-2.5% to -5.0%),
            # while established QA testing (test_qa_ndt) and Materials science shield reliability!
            cur.execute(
                "SELECT current_tier, is_unlocked FROM team_facilities WHERE team_id = ? AND node_id = 'test_qa_ndt';",
                (team_id,),
            )
            ndt_row = cur.fetchone()
            ndt_shield = (ndt_row[0] * 1.5) if (ndt_row and ndt_row[1]) else 0.0

            if is_breakthrough:
                perf_strain = random.uniform(2.5, 5.0) - (ndt_shield * 0.6)
                net_rel_change = round(rel_gain - max(0.5, perf_strain), 1)
            else:
                net_rel_change = round(rel_gain + (ndt_shield * 0.3), 1)

            # Dyno Lab extra reliability boost on engines: +1.5% per tier of eng_dyno
            dyno_extra = 0.0
            if comp["category"] == "ENGINE":
                cur.execute(
                    "SELECT current_tier, is_unlocked FROM team_facilities WHERE team_id = ? AND node_id = 'eng_dyno';",
                    (team_id,),
                )
                dyno_res = cur.fetchone()
                dyno_lvl = dyno_res[0] if dyno_res and dyno_res[1] else 0
                dyno_extra = dyno_lvl * 1.5

            new_rel = max(45.0, min(99.0, round(comp["reliability"] + net_rel_change + dyno_extra, 1)))

            # Deduct cash & reset knowledge to 0.0 for new generation, resetting wear to 0%
            cur.execute("UPDATE teams SET cash = cash - ? WHERE id = ?;", (build_cost, team_id))
            cur.execute(
                """
            UPDATE car_components 
            SET generation = ?, performance = ?, reliability = ?, 
                knowledge_min = 0.0, knowledge_max = 0.0, 
                rel_knowledge_min = 0.0, rel_knowledge_max = 0.0, 
                races_on_concept = 0, wear_pct = 0.0,
                max_durability = ?, current_durability = ?
            WHERE id = ?;
            """,
                (new_gen, new_perf, new_rel, new_max_durability, new_max_durability, component_id),
            )

            cur.execute(
                """
            INSERT INTO ledger (team_id, week, category, description, amount)
            VALUES (?, 1, 'RND_BUILD', ?, ?);
            """,
                (
                    team_id,
                    f"Manufactured {comp['category']} Mk {new_gen} (+{gain:.1f} Perf, +{durability_gain:.1f}% Durability -> {new_max_durability:.0f}%)",
                    -build_cost,
                ),
            )

            conn.commit()
            return (
                True,
                f"Successfully built {comp['category']} Mk {new_gen}! (+{gain:.1f} Perf, Durability upgraded to {new_max_durability:.0f}%).",
                gain,
            )

    def buy_factory_part(self, team_id: int, category: str, target_car_slot: int = 0) -> Tuple[bool, str]:
        """Buys a factory specification component based on the team's tier."""
        tier, _, _ = self.get_team_allowed_parts(team_id)
        tier_specs = FACTORY_PART_SPECS.get(tier, FACTORY_PART_SPECS[3])
        spec = tier_specs.get(category, tier_specs["BRAKES"])
        success, msg, _ = self.db.buy_factory_component(
            team_id=team_id,
            category=category,
            cost=spec["cost"],
            performance=spec["perf"],
            durability=spec["durability"],
            target_car_slot=target_car_slot,
        )
        return success, msg

    def mount_part_from_inventory(self, team_id: int, component_id: int, target_car_slot: int) -> Tuple[bool, str]:
        """Mounts a spare component from the warehouse to Car 1 or 2."""
        return self.db.mount_component(team_id, component_id, target_car_slot)

    def get_spare_parts_in_warehouse(self, team_id: int, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns spare components in warehouse stock."""
        return self.db.get_team_warehouse_components(team_id, category)

    def get_available_engine_suppliers(self, team_id: int) -> List[Dict[str, Any]]:
        """Returns list of engine suppliers available to the team based on current league tier and works factory unlocks."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT tier FROM teams WHERE id = ?;", (team_id,))
            row = cur.fetchone()
            tier = row[0] if row else 3

            # Check if Works Engine Factory is built
            cur.execute(
                """
            SELECT is_unlocked FROM team_facilities 
            WHERE team_id = ? AND node_id = 'eng_works_powertrain';
            """,
                (team_id,),
            )
            w_row = cur.fetchone()
            has_works_factory = bool(w_row[0]) if w_row else False

            available = []
            for name, data in ENGINE_SUPPLIERS.items():
                if data.get("is_in_house", False):
                    # In-house works power unit is only available in Tier 1 with Works Factory
                    if tier == 1 and has_works_factory:
                        available.append(data)
                else:
                    # Customer suppliers matching current league tier
                    if tier == data["min_tier"]:
                        available.append(data)
            return available

    def set_engine_supplier(self, team_id: int, supplier_name: str, force_new_season: bool = False) -> Tuple[bool, str]:
        """
        Signs engine supplier contract for a full season.
        If mid-season (and not force_new_season), engine supplier cannot be hot-swapped.
        """
        if supplier_name not in ENGINE_SUPPLIERS:
            return False, "Invalid engine supplier."

        supp = ENGINE_SUPPLIERS[supplier_name]
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT tier, cash, engine_contract_races_left, engine_locked_for_season FROM teams WHERE id = ?;",
                (team_id,),
            )
            res = cur.fetchone()
            tier, cash = res[0], res[1]
            races_left = res[2] if len(res) > 2 and res[2] is not None else 0
            is_locked = res[3] if len(res) > 3 and res[3] is not None else 1

            if not force_new_season and is_locked and races_left > 0:
                return (
                    False,
                    f"Engine contract is locked for this season ({races_left} races left). New supplier negotiations open at season end!",
                )

            if supp.get("is_in_house", False):
                if tier != 1:
                    return False, "Works In-House Engine is only permitted in Tier 1 (World Super Formula)."
                cur.execute(
                    "SELECT is_unlocked FROM team_facilities WHERE team_id = ? AND node_id = 'eng_works_powertrain';",
                    (team_id,),
                )
                w_row = cur.fetchone()
                if not w_row or not w_row[0]:
                    return False, "Requires Works Engine Factory (eng_works_powertrain) constructed first."
            else:
                if tier != supp["min_tier"]:
                    return False, f"{supplier_name} is only available for Tier {supp['min_tier']} championships."

            cost = supp["cost_season"]
            if cash < cost and not supp.get("is_in_house", False):
                return False, f"Insufficient funds. Need ${cost:,.0f} for seasonal engine contract."

            cur.execute(
                """
            UPDATE teams 
            SET engine_supplier = ?, engine_contract_cost = ?, engine_contract_races_left = 10, engine_locked_for_season = 1, cash = cash - ?
            WHERE id = ?;
            """,
                (supp["name"], cost, cost, team_id),
            )

            # Update Car 1 and Car 2 Engine components
            cur.execute(
                """
            UPDATE car_components 
            SET performance = ?, reliability = ?
            WHERE team_id = ? AND category = 'ENGINE';
            """,
                (supp["base_power"], supp["reliability"], team_id),
            )

            if cost > 0:
                cur.execute(
                    """
                INSERT INTO ledger (team_id, week, category, description, amount)
                VALUES (?, 1, 'ENGINE_SUPPLIER', ?, ?);
                """,
                    (team_id, f"Signed Engine Contract: {supp['name']} (Full Season)", -cost),
                )

            conn.commit()
            return True, f"Full Season Contract signed with {supp['name']}!"

    def set_subnode_budget(self, team_id: int, node_id: str, monthly_budget: float, upkeep_mult: float = 1.0):
        """Sets monthly operational funding for a facility sub-node, bounded by minimum operational costs (facility upkeep + equipment upkeep + staff wages)."""
        status = self.db.get_department_financial_status(team_id, node_id, upkeep_mult=upkeep_mult)
        min_cost = status.get("min_operational_cost", 0.0)
        bounded_budget = max(min_cost, monthly_budget)
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            UPDATE team_facilities 
            SET monthly_sub_budget = ?
            WHERE team_id = ? AND node_id = ?;
            """,
                (bounded_budget, team_id, node_id),
            )
            conn.commit()

    def build_facility_node(self, team_id: int, node_id: str, cost_mult: float = 1.0) -> Tuple[bool, str]:
        """Purchases and constructs a new facility sub-node from cash reserves, scaled by difficulty cost multiplier."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM facility_nodes WHERE id = ?;", (node_id,))
            node = cur.fetchone()
            if not node:
                return False, "Facility node not found."

            # Check parent prerequisites
            if node_id == "eng_windtunnel":
                # Wind Tunnel requires an OR prerequisite: Front Aero OR Rear Aero OR Aero Model Shop constructed first!
                cur.execute(
                    """
                SELECT node_id FROM team_facilities 
                WHERE team_id = ? AND node_id IN ('eng_wings_front', 'eng_wings_rear', 'eng_aero_model_shop') AND is_unlocked = 1 AND current_tier >= 1;
                """,
                    (team_id,),
                )
                unlocked_wings = cur.fetchall()
                if not unlocked_wings:
                    return False, "Wind Tunnel requires constructing Front Aero, Rear Aero, or Aero Model Shop first."

            elif node["parent_id"]:
                p_id = node["parent_id"]
                cur.execute(
                    """
                SELECT is_unlocked, current_tier FROM team_facilities 
                WHERE team_id = ? AND node_id = ?;
                """,
                    (team_id, p_id),
                )
                p_row = cur.fetchone()
                if not p_row or not p_row[0] or p_row[1] < 1:
                    cur.execute("SELECT name FROM facility_nodes WHERE id = ?;", (p_id,))
                    p_name_res = cur.fetchone()
                    p_name = p_name_res[0] if p_name_res else p_id
                    return False, f"Requires parent facility ({p_name}) constructed first."

            cur.execute("SELECT tier, cash FROM teams WHERE id = ?;", (team_id,))
            team_row = cur.fetchone()
            if not team_row:
                return False, "Team not found."
            team_tier = int(team_row[0])
            cash = float(team_row[1])

            # Check league tier unlock requirement: facility unlock_league_tier specifies min tier (1=WSF, 2=CC, 3=NOC)
            fac_req_tier = int(
                node["unlock_league_tier"]
                if "unlock_league_tier" in node.keys() and node["unlock_league_tier"] is not None
                else 3
            )
            if team_tier > fac_req_tier:
                tier_names = {
                    1: "Tier 1 (World Super Formula)",
                    2: "Tier 2 (Continental Championship)",
                    3: "Tier 3 (National Open Cup)",
                }
                req_name = tier_names.get(fac_req_tier, f"Tier {fac_req_tier}")
                return False, f"Facility requires promotion to {req_name} to construct."

            cost = node["base_cost"] * cost_mult

            if cash < cost:
                return False, f"Insufficient funds. Required: ${cost:,.0f}."

            # Deduct cash & insert or update team_facilities
            cur.execute("UPDATE teams SET cash = cash - ? WHERE id = ?;", (cost, team_id))
            base_upk = float(node["base_upkeep"])
            cur.execute(
                """
            INSERT INTO team_facilities (team_id, node_id, current_tier, is_unlocked, monthly_sub_budget)
            VALUES (?, ?, 1, 1, ?)
            ON CONFLICT(team_id, node_id) DO UPDATE SET current_tier = 1, is_unlocked = 1, monthly_sub_budget = MAX(monthly_sub_budget, ?);
            """,
                (team_id, node_id, base_upk, base_upk),
            )

            cur.execute(
                """
            INSERT INTO ledger (team_id, week, category, description, amount)
            VALUES (?, 1, 'RND_BUILD', ?, ?);
            """,
                (team_id, f"Constructed Facility: {node['name']} (Tier 1)", -cost),
            )

            conn.commit()
            return True, f"Successfully built {node['name']}!"

    def upgrade_facility_node(self, team_id: int, node_id: str, cost_mult: float = 1.0) -> Tuple[bool, str]:
        """Upgrades an existing unlocked facility to the next tier level, scaled by difficulty cost multiplier."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            SELECT fn.*, tf.current_tier, tf.is_unlocked 
            FROM facility_nodes fn
            JOIN team_facilities tf ON fn.id = tf.node_id
            WHERE tf.team_id = ? AND fn.id = ?;
            """,
                (team_id, node_id),
            )
            res = cur.fetchone()
            if not res or not res["is_unlocked"]:
                return False, "Facility is not built yet."

            cur_tier = res["current_tier"]
            if cur_tier >= res["max_tier"]:
                return False, "Facility is already at maximum tier level."

            next_tier = cur_tier + 1
            upgrade_cost = res["base_cost"] * (1.5 if next_tier == 2 else 2.5) * cost_mult

            cur.execute("SELECT cash FROM teams WHERE id = ?;", (team_id,))
            cash = float(cur.fetchone()[0])
            if cash < upgrade_cost:
                return False, f"Insufficient funds. Required: ${upgrade_cost:,.0f}."

            cur.execute("UPDATE teams SET cash = cash - ? WHERE id = ?;", (upgrade_cost, team_id))
            min_new_budget = float(res["base_upkeep"]) * next_tier
            cur.execute(
                """
            UPDATE team_facilities 
            SET current_tier = ?, monthly_sub_budget = MAX(monthly_sub_budget, ?)
            WHERE team_id = ? AND node_id = ?;
            """,
                (next_tier, min_new_budget, team_id, node_id),
            )

            cur.execute(
                """
            INSERT INTO ledger (team_id, week, category, description, amount)
            VALUES (?, 1, 'RND_BUILD', ?, ?);
            """,
                (team_id, f"Upgraded {res['name']} to Tier {next_tier}", -upgrade_cost),
            )

            conn.commit()
            return True, f"Upgraded {res['name']} to Tier {next_tier}!"

    def process_monthly_department_budgets(
        self, team_id: int, upkeep_mult: float = 1.0, cost_mult: float = 1.0
    ) -> List[Dict[str, Any]]:
        """
        Processes monthly department budget execution for all unlocked facilities:
        - Deficit (Budget < Upkeep Demand): Shuts down equipment (no upkeep but lost boost), and downsizes staff if still deficient.
        - Surplus (Budget > Upkeep Demand): Autonomous reinvestment into hiring specialists up to capacity and auto-upgrading equipment.
        - HR Recruitment level & Management Department Head quality boost decision ROI.
        """
        logs = []
        facilities = self.db.get_team_facilities(team_id)

        # Calculate HR and Dept Head Quality Index (0.6x to 1.4x efficiency)
        hr_fac = next((f for f in facilities if f["id"] == "hr_recruitment"), None)
        headhunter_fac = next((f for f in facilities if f["id"] == "hr_headhunter"), None)
        hr_lvl = (hr_fac["current_tier"] if hr_fac and hr_fac["is_unlocked"] else 0) + (
            headhunter_fac["current_tier"] if headhunter_fac and headhunter_fac["is_unlocked"] else 0
        )
        hr_quality_mult = 0.8 + 0.15 * hr_lvl

        with self.db.get_connection() as conn:
            cur = conn.cursor()

            for fac in facilities:
                if not fac["is_unlocked"]:
                    continue

                node_id = fac["id"]
                fac_name = fac["name"]
                fac_tier = fac["current_tier"]
                status = self.db.get_department_financial_status(team_id, node_id, upkeep_mult=upkeep_mult)
                budget = status["monthly_budget"]
                surplus_deficit = status["surplus_or_deficit"]
                equipment_list = self.db.get_facility_equipment(team_id, node_id, upkeep_mult=upkeep_mult)

                # =============================================================
                # Case A: DEFICIT (Budget < Minimum Upkeep Demand)
                # =============================================================
                if surplus_deficit < 0:
                    needed_cut = abs(surplus_deficit)
                    # 1. Shut down active equipment to eliminate upkeep
                    active_eq = [e for e in equipment_list if e["is_active"] and e["current_level"] > 0]
                    # Sort by lowest performance per upkeep dollar (least efficient first)
                    active_eq.sort(key=lambda e: e["perf_bonus_per_level"] / max(1.0, e["base_upkeep"]))

                    shut_down_count = 0
                    for eq in active_eq:
                        if needed_cut <= 0:
                            break
                        saved = eq["base_upkeep"] * eq["current_level"]
                        cur.execute(
                            """
                        INSERT INTO team_equipment (team_id, equipment_id, current_level, is_active)
                        VALUES (?, ?, ?, 0)
                        ON CONFLICT(team_id, equipment_id) DO UPDATE SET is_active = 0;
                        """,
                            (team_id, eq["id"], eq["current_level"]),
                        )
                        needed_cut -= saved
                        shut_down_count += 1

                    if shut_down_count > 0:
                        logs.append(
                            {
                                "type": "DEFICIT_SHUTDOWN",
                                "node_id": node_id,
                                "facility_name": fac_name,
                                "message": f"Budget Deficit in {fac_name}: Shut down {shut_down_count} equipment rigs to reduce upkeep.",
                            }
                        )

                    # 2. If still in deficit, downsize staff in this department
                    if needed_cut > 0:
                        cur.execute(
                            "SELECT id, salary_monthly FROM staff WHERE team_id = ? AND assigned_subnode = ? ORDER BY skill ASC;",
                            (team_id, node_id),
                        )
                        staff_members = cur.fetchall()
                        laid_off = 0
                        for sm in staff_members:
                            if needed_cut <= 0:
                                break
                            cur.execute("DELETE FROM staff WHERE id = ?;", (sm[0],))
                            needed_cut -= float(sm[1])
                            laid_off += 1

                        if laid_off > 0:
                            logs.append(
                                {
                                    "type": "DEFICIT_LAYOFF",
                                    "node_id": node_id,
                                    "facility_name": fac_name,
                                    "message": f"Severe Budget Deficit in {fac_name}: Downsized {laid_off} staff members to meet monthly budget.",
                                }
                            )

                # =============================================================
                # Case B: SURPLUS (Budget > Required Upkeep)
                # =============================================================
                elif surplus_deficit > 2000.0:
                    investable_surplus = surplus_deficit * hr_quality_mult

                    # 1. Autonomous Staff Hiring (if under capacity)
                    staff_cap = fac["staff_capacity"] * fac_tier
                    cur.execute(
                        "SELECT COUNT(*) FROM staff WHERE team_id = ? AND assigned_subnode = ?;", (team_id, node_id)
                    )
                    cur_staff = int(cur.fetchone()[0])

                    if cur_staff < staff_cap and investable_surplus >= 4000.0:
                        # Auto-hire 1 specialized engineer
                        FIRST_NAMES = [
                            "Alex",
                            "James",
                            "Elena",
                            "Lucas",
                            "Sophie",
                            "Marcus",
                            "Yuki",
                            "Chloe",
                            "David",
                            "Liam",
                        ]
                        LAST_NAMES = [
                            "Vance",
                            "Kovacs",
                            "Moreau",
                            "Sato",
                            "Schneider",
                            "Ricci",
                            "Novak",
                            "Berg",
                            "Dubois",
                        ]
                        new_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
                        new_skill = min(92, int(45 + 8 * fac_tier + 5 * hr_quality_mult + random.randint(-3, 6)))
                        salary = 3200.0 if new_skill < 65 else (4500.0 if new_skill < 80 else 6000.0)

                        cur.execute(
                            """
                        INSERT INTO staff (team_id, name, role, assigned_subnode, skill, salary_monthly)
                        VALUES (?, ?, 'Specialist Engineer', ?, ?, ?);
                        """,
                            (team_id, new_name, node_id, new_skill, salary),
                        )

                        investable_surplus -= salary
                        logs.append(
                            {
                                "type": "SURPLUS_HIRE",
                                "node_id": node_id,
                                "facility_name": fac_name,
                                "message": f"Autonomous Reinvestment in {fac_name}: Recruited specialist {new_name} (Skill: {new_skill}).",
                            }
                        )

                    # 2. Autonomous Equipment Upgrades (prioritizing best ROI)
                    # Filter equipment unlocked by current facility tier and not max level
                    upgradeable_eq = [
                        e for e in equipment_list if not e["is_tier_locked"] and e["current_level"] < e["max_level"]
                    ]
                    # Sort by highest ROI (perf bonus / cost)
                    upgradeable_eq.sort(
                        key=lambda e: e["perf_bonus_per_level"] / max(1.0, e["next_upgrade_cost"]), reverse=True
                    )

                    for eq in upgradeable_eq:
                        upg_cost = eq["next_upgrade_cost"] * cost_mult
                        # If department surplus can fund it or team cash allows investment
                        cur.execute("SELECT cash FROM teams WHERE id = ?;", (team_id,))
                        team_cash = float(cur.fetchone()[0])

                        if investable_surplus >= upg_cost * 0.15 and team_cash >= upg_cost * 1.5:
                            next_lvl = eq["current_level"] + 1
                            cur.execute("UPDATE teams SET cash = cash - ? WHERE id = ?;", (upg_cost, team_id))
                            cur.execute(
                                """
                            INSERT INTO team_equipment (team_id, equipment_id, current_level, is_active)
                            VALUES (?, ?, ?, 1)
                            ON CONFLICT(team_id, equipment_id) DO UPDATE SET current_level = ?, is_active = 1;
                            """,
                                (team_id, eq["id"], next_lvl, next_lvl),
                            )
                            cur.execute(
                                """
                            INSERT INTO ledger (team_id, week, category, description, amount)
                            VALUES (?, 1, 'RND_BUILD', ?, ?);
                            """,
                                (team_id, f"Auto-Upgraded Equipment: {eq['name']} to Level {next_lvl}", -upg_cost),
                            )

                            logs.append(
                                {
                                    "type": "SURPLUS_UPGRADE",
                                    "node_id": node_id,
                                    "facility_name": fac_name,
                                    "message": f"Department Head Reinvestment: Auto-upgraded {eq['name']} to Level {next_lvl}!",
                                }
                            )
                            break

            conn.commit()
        return logs

    # =========================================================================
    # NEXT-GEN CAR DEVELOPMENT & DYNAMIC REGULATIONS
    # =========================================================================

    def set_next_gen_allocation(self, team_id: int, pct: float) -> Tuple[bool, str]:
        """Sets the team's R&D allocation % toward next season's chassis (0% to 80%)."""
        pct = max(0.0, min(80.0, round(pct, 1)))
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE teams SET next_gen_rnd_pct = ? WHERE id = ?;", (pct, team_id))
            conn.commit()
        return True, f"Next-Year Chassis R&D allocation updated to {pct:.0f}%."

    def get_team_next_gen_status(self, team_id: int) -> Dict[str, Any]:
        """Returns the team's current next-gen R&D progress, projected boosts, and port-back eligibility."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            SELECT id, tier, monthly_engineering_budget, next_gen_rnd_pct, next_gen_rnd_points,
                   chassis_perf_boost, chassis_rel_boost, chassis_tire_preservation_base, chassis_fuel_efficiency_base,
                   port_back_cooldown_weeks, port_back_bonus_weeks, port_back_bonus_rel
            FROM teams WHERE id = ?;
            """,
                (team_id,),
            )
            team = cur.fetchone()
            if not team:
                return {}

            t_data = dict(team)
            pts = float(t_data.get("next_gen_rnd_points", 0.0) or 0.0)
            alloc_pct = float(t_data.get("next_gen_rnd_pct", 0.0) or 0.0)
            eng_budget = float(t_data.get("monthly_engineering_budget", 60000.0) or 60000.0)
            tier = t_data.get("tier", 3)

            # Projected gains from accumulated points
            proj_perf = round(pts / 25000.0, 1)
            proj_rel = round((pts / 30000.0) * 1.2, 1)
            proj_tire = round(min(12.0, (pts / 20000.0) * 1.0), 1)
            proj_fuel = round(min(10.0, (pts / 25000.0) * 1.0), 1)

            # Weekly accumulation rate
            weekly_investment = (eng_budget / 4.0) * (alloc_pct / 100.0)
            cooldown = t_data.get("port_back_cooldown_weeks", 0)
            bonus_wks = t_data.get("port_back_bonus_weeks", 0)
            bonus_rel = float(t_data.get("port_back_bonus_rel", 0.0) or 0.0)

            # Check regulations status for tier
            season_num = self.db.get_current_season_num()
            regs = self.db.get_season_regulations(tier, season_num)

            return {
                "team_id": team_id,
                "tier": tier,
                "season_num": season_num,
                "allocation_pct": alloc_pct,
                "points": pts,
                "weekly_investment": weekly_investment,
                "projected_perf_boost": proj_perf,
                "projected_rel_boost": proj_rel,
                "projected_tire_pres_bonus": proj_tire,
                "projected_fuel_eff_bonus": proj_fuel,
                "active_chassis_perf_boost": float(t_data.get("chassis_perf_boost", 0.0) or 0.0),
                "active_chassis_rel_boost": float(t_data.get("chassis_rel_boost", 0.0) or 0.0),
                "chassis_tire_base": float(t_data.get("chassis_tire_preservation_base", 85.0) or 85.0),
                "chassis_fuel_base": float(t_data.get("chassis_fuel_efficiency_base", 85.0) or 85.0),
                "port_back_cooldown_weeks": cooldown,
                "port_back_bonus_weeks": bonus_wks,
                "port_back_bonus_rel": bonus_rel,
                "regulations": regs,
            }

    def process_weekly_next_gen_rnd(self, team_id: int, current_week: int) -> Dict[str, Any]:
        """Advances weekly Next-Gen Chassis R&D for a team."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            SELECT monthly_engineering_budget, next_gen_rnd_pct, next_gen_rnd_points,
                   port_back_cooldown_weeks, port_back_bonus_weeks, port_back_bonus_rel
            FROM teams WHERE id = ?;
            """,
                (team_id,),
            )
            t_row = cur.fetchone()
            if not t_row:
                return {}

            alloc_pct = float(t_row["next_gen_rnd_pct"] or 0.0)
            budget = float(t_row["monthly_engineering_budget"] or 60000.0)
            cur_pts = float(t_row["next_gen_rnd_points"] or 0.0)
            cooldown = int(t_row["port_back_cooldown_weeks"] or 0)
            bonus_wks = int(t_row["port_back_bonus_weeks"] or 0)
            bonus_rel = float(t_row["port_back_bonus_rel"] or 0.0)

            # If factory is in port-back cooldown (2 weeks):
            if cooldown > 0:
                cooldown -= 1
                cur.execute("UPDATE teams SET port_back_cooldown_weeks = ? WHERE id = ?;", (cooldown, team_id))
                conn.commit()
                return {
                    "points_added": 0.0,
                    "cooldown_left": cooldown,
                    "message": f"Factory tooling port-back upgrade. Next-gen R&D paused ({cooldown} wks remaining).",
                }

            # Normal weekly point accumulation
            weekly_invest = (budget / 4.0) * (alloc_pct / 100.0)
            # Add facility multiplier if design/simulation facilities exist
            cur.execute(
                """
            SELECT SUM(current_tier) FROM team_facilities 
            WHERE team_id = ? AND is_unlocked = 1 AND node_id IN ('aero_wind_tunnel', 'aero_cfd_super', 'eng_workshop', 'test_qa_rig');
            """,
                (team_id,),
            )
            fac_sum = cur.fetchone()[0] or 0
            fac_mult = 1.0 + (fac_sum * 0.08)
            points_added = round(weekly_invest * fac_mult, 1)
            new_pts = cur_pts + points_added

            # If port-back bonus is active (3 weeks):
            bonus_applied = 0.0
            if bonus_wks > 0:
                bonus_wks -= 1
                bonus_applied = bonus_rel
                # Increase chassis_rel_boost by bonus_rel directly
                cur.execute(
                    """
                UPDATE teams 
                SET next_gen_rnd_points = ?, port_back_bonus_weeks = ?, chassis_rel_boost = chassis_rel_boost + ?
                WHERE id = ?;
                """,
                    (new_pts, bonus_wks, bonus_rel, team_id),
                )
            else:
                cur.execute("UPDATE teams SET next_gen_rnd_points = ? WHERE id = ?;", (new_pts, team_id))

            conn.commit()
            return {"points_added": points_added, "bonus_rel_applied": bonus_applied, "total_points": new_pts}

    def execute_port_back_upgrade(self, team_id: int, current_week: int) -> Tuple[bool, str]:
        """
        Ports back 2/3 of the accumulated next-year chassis boost to the current car.
        Allowed only under STATUS_QUO between weeks 13 and 16.
        Triggers a 2-week factory cooldown (+0% next-gen progress),
        followed by a 3-week reliability boost of (5% of accumulated rel / 3) per week.
        """
        if current_week < 13 or current_week > 16:
            return False, "Port-Back upgrades can only be manufactured between calendar Weeks 13 and 16."

        status = self.get_team_next_gen_status(team_id)
        if not status:
            return False, "Team not found."

        regs = status.get("regulations", {})
        if regs.get("upcoming_package") != "STATUS_QUO":
            return (
                False,
                f"Port-Back upgrades are prohibited because {regs.get('upcoming_package')} rule changes are announced for next year! Concepts cannot be adapted.",
            )

        if regs.get("port_back_used"):
            return False, "Your team has already executed an In-Season Port-Back Upgrade this season."

        pts = status["points"]
        if pts < 10000.0:
            return (
                False,
                f"Insufficient next-gen progress to port back. Current progress: {pts:,.0f} pts (minimum 10,000 pts required).",
            )

        # Calculate 2/3 boost
        proj_perf = status["projected_perf_boost"]
        proj_rel = status["projected_rel_boost"]
        current_boost_add = round((2.0 / 3.0) * proj_perf, 1)
        current_rel_add = round((2.0 / 3.0) * proj_rel, 1)

        # 5% of accumulated reliability gain spread over 3 weeks
        bonus_per_week = round((0.05 * proj_rel) / 3.0, 2)

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            # Apply to current car chassis stats immediately
            cur.execute(
                """
            UPDATE teams 
            SET chassis_perf_boost = chassis_perf_boost + ?,
                chassis_rel_boost = chassis_rel_boost + ?,
                port_back_cooldown_weeks = 2,
                port_back_bonus_weeks = 3,
                port_back_bonus_rel = ?
            WHERE id = ?;
            """,
                (current_boost_add, current_rel_add, bonus_per_week, team_id),
            )

            # Mark port back used for this season
            season_num = status["season_num"]
            tier = status["tier"]
            cur.execute(
                """
            UPDATE season_regulations SET port_back_used = 1 WHERE season_num = ? AND tier = ?;
            """,
                (season_num, tier),
            )

            cur.execute(
                """
            INSERT INTO ledger (team_id, week, category, description, amount)
            VALUES (?, ?, 'RND_BUILD', ?, 0.0);
            """,
                (
                    team_id,
                    current_week,
                    f"Ported Next-Gen Concept Back to Current Car (+{current_boost_add:.1f} Perf, +{current_rel_add:.1f}% Rel)",
                ),
            )

            conn.commit()

        return (
            True,
            f"Port-Back Upgrade Successful! Current car received +{current_boost_add:.1f} Perf and +{current_rel_add:.1f}% Rel. Factory in 2-week retooling cooldown, followed by 3-week track testing telemetry bonuses.",
        )

    def evaluate_season_regulations(
        self, tier: int, current_week: int = 9, season_num: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Evaluates competitive landscape at Week 9 and announces upcoming regulations.
        Thresholds:
        - Tier 3: Total Part Score > 3,000 OR Points Lead > 35% OR 5 consecutive stable seasons
        - Tier 2: Total Part Score > 6,500 OR Points Lead > 35% OR 4 consecutive stable seasons
        - Tier 1: Total Part Score > 15,000 OR Points Lead > 35% OR 3 consecutive stable seasons
        """
        if season_num is None:
            season_num = self.db.get_current_season_num()

        reg_record = self.db.get_season_regulations(tier, season_num)
        if reg_record.get("is_announced"):
            return reg_record

        consec_stable = reg_record.get("consecutive_stable_seasons", 0)

        # 1. Total score limit check
        total_ceiling = {1: 15000.0, 2: 6500.0, 3: 3000.0}.get(tier, 3000.0)
        mandatory_cycles = {1: 3, 2: 4, 3: 5}.get(tier, 5)

        with self.db.get_connection() as conn:
            cur = conn.cursor()

            # Find max total component performance among teams in this tier
            cur.execute(
                """
            SELECT t.id, t.name, SUM(c.performance) as total_perf
            FROM teams t
            JOIN car_components c ON t.id = c.team_id AND c.car_slot = 1
            WHERE t.tier = ?
            GROUP BY t.id, t.name
            ORDER BY total_perf DESC LIMIT 1;
            """,
                (tier,),
            )
            top_perf_row = cur.fetchone()
            max_perf = float(top_perf_row["total_perf"]) if top_perf_row and top_perf_row["total_perf"] else 0.0
            top_perf_team = top_perf_row["name"] if top_perf_row else "Top Team"

            # Check points runaway
            cur.execute("SELECT name, points FROM teams WHERE tier = ? ORDER BY points DESC LIMIT 2;", (tier,))
            top_points = cur.fetchall()
            p1_pts = top_points[0]["points"] if len(top_points) > 0 else 0
            p2_pts = top_points[1]["points"] if len(top_points) > 1 else 0

            is_ceiling_breach = max_perf >= total_ceiling
            is_monopoly_runaway = p1_pts >= 25 and (p1_pts - p2_pts) > (p1_pts * 0.35)
            is_mandatory_cycle = consec_stable >= mandatory_cycles

            # Determine package
            if is_ceiling_breach or is_mandatory_cycle or is_monopoly_runaway:
                if is_ceiling_breach:
                    upcoming_pkg = "MAJOR_OVERHAUL"
                    reason = f"Extreme speed safety thresholds breached by {top_perf_team} ({max_perf:.0f} pts > {total_ceiling:.0f} limit)."
                elif is_mandatory_cycle:
                    packages = ["MECHANICAL_TWEAKS", "AERO_SHAKEUP", "POWERTRAIN_DIRECTIVE", "MAJOR_OVERHAUL"]
                    upcoming_pkg = random.choice(packages)
                    reason = f"Mandatory {mandatory_cycles}-season FIA cycle reached for Tier {tier}."
                else:
                    packages = ["AERO_SHAKEUP", "MECHANICAL_TWEAKS", "POWERTRAIN_DIRECTIVE"]
                    upcoming_pkg = random.choice(packages)
                    reason = "Runaway championship gap detected (P1 lead over P2 > 35%)."

                announcement = f"FIA DIRECTIVE: {upcoming_pkg.replace('_', ' ')} mandated for next season! Reason: {reason} Affected parts will reset to base factory specifications at season end."
            else:
                upcoming_pkg = "STATUS_QUO"
                announcement = "FIA CONFIRMATION: Stable Technical Regulations (Status Quo) confirmed for next season! Competitive parity within acceptable safety margins."

            self.db.set_season_regulations(
                season_num, tier, upcoming_pkg, is_announced=True, announcement_text=announcement
            )
            return self.db.get_season_regulations(tier, season_num)

    def apply_season_rollover_regulations(self, tier: int, season_num: Optional[int] = None) -> Dict[str, Any]:
        """
        Applies end-of-season regulation reset and chassis rollover across all teams in the tier.
        - Under rule change:
          * Wipes ALL previous chassis base improvements back to zero!
          * Wipes custom iterations for affected parts back to Tier Base Spec (Mk 1).
          * Injects new chassis boost (perf, rel, tyre preservation, fuel efficiency) universally.
        - Under STATUS_QUO:
          * Chassis boosts accumulate year-over-year!
          * Custom parts carry forward with their accumulated performance.
        - Resets next_gen_rnd_pct and points to 0 for the upcoming season.
        """
        if season_num is None:
            season_num = self.db.get_current_season_num()

        reg_record = self.db.get_season_regulations(tier, season_num)
        pkg = reg_record.get("upcoming_package", "STATUS_QUO")
        is_rule_change = pkg != "STATUS_QUO"

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM teams WHERE tier = ?;", (tier,))
            teams = [dict(r) for r in cur.fetchall()]

            base_specs = FACTORY_PART_SPECS.get(tier, {})

            for t in teams:
                team_id = t["id"]
                pts = float(t.get("next_gen_rnd_points", 0.0) or 0.0)

                # Compute newly earned chassis boosts from next-gen R&D
                earned_perf = round(pts / 25000.0, 1)
                earned_rel = round((pts / 30000.0) * 1.2, 1)
                earned_tire = round(min(12.0, (pts / 20000.0) * 1.0), 1)
                earned_fuel = round(min(10.0, (pts / 25000.0) * 1.0), 1)

                if is_rule_change:
                    # Non-Status Quo: WIPES ALL PRIOR CHASSIS BASE IMPROVEMENTS!
                    new_chassis_perf = earned_perf
                    new_chassis_rel = earned_rel
                    new_tire_pres = 85.0 + earned_tire
                    new_fuel_eff = 85.0 + earned_fuel
                else:
                    # STATUS_QUO: Chassis boosts accumulate!
                    old_perf = float(t.get("chassis_perf_boost", 0.0) or 0.0)
                    old_rel = float(t.get("chassis_rel_boost", 0.0) or 0.0)
                    old_tire = float(t.get("chassis_tire_preservation_base", 85.0) or 85.0)
                    old_fuel = float(t.get("chassis_fuel_efficiency_base", 85.0) or 85.0)

                    new_chassis_perf = round(old_perf + earned_perf, 1)
                    new_chassis_rel = round(old_rel + earned_rel, 1)
                    new_tire_pres = min(99.0, round(old_tire + earned_tire, 1))
                    new_fuel_eff = min(99.0, round(old_fuel + earned_fuel, 1))

                # Update team chassis base stats and reset next-gen development
                cur.execute(
                    """
                UPDATE teams 
                SET chassis_perf_boost = ?,
                    chassis_rel_boost = ?,
                    chassis_tire_preservation_base = ?,
                    chassis_fuel_efficiency_base = ?,
                    next_gen_rnd_pct = 0.0,
                    next_gen_rnd_points = 0.0,
                    port_back_cooldown_weeks = 0,
                    port_back_bonus_weeks = 0,
                    port_back_bonus_rel = 0.0
                WHERE id = ?;
                """,
                    (new_chassis_perf, new_chassis_rel, new_tire_pres, new_fuel_eff, team_id),
                )

                # Part Resets for affected categories
                if is_rule_change:
                    affected_cats = []
                    if pkg == "MECHANICAL_TWEAKS":
                        affected_cats = ["BRAKES", "SUSPENSION"]
                    elif pkg == "AERO_SHAKEUP":
                        affected_cats = ["FRONT_WING", "REAR_WING", "FLOOR"]
                    elif pkg == "POWERTRAIN_DIRECTIVE":
                        affected_cats = ["ENGINE", "ERS"]
                    elif pkg == "MAJOR_OVERHAUL":
                        affected_cats = ["BRAKES", "FRONT_WING", "REAR_WING", "SUSPENSION", "FLOOR", "ENGINE", "ERS"]

                    for cat in affected_cats:
                        f_spec = base_specs.get(cat, {})
                        base_p = f_spec.get("perf", 75.0)
                        base_d = f_spec.get("durability", 65.0)

                        # Reset Car 1, Car 2, and Spares in warehouse
                        cur.execute(
                            """
                        UPDATE car_components 
                        SET generation = 1,
                            performance = ?,
                            reliability = ?,
                            wear_pct = 0.0,
                            knowledge_min = 0.0,
                            knowledge_max = 0.0,
                            rel_knowledge_min = 0.0,
                            rel_knowledge_max = 0.0,
                            races_on_concept = 0,
                            max_durability = ?,
                            current_durability = ?
                        WHERE team_id = ? AND category = ?;
                        """,
                            (base_p, base_d, base_d, base_d, team_id, cat),
                        )

            # Update season_regulations for next season
            next_season = season_num + 1
            new_stable = (reg_record.get("consecutive_stable_seasons", 0) + 1) if not is_rule_change else 0
            cur.execute(
                """
            INSERT OR REPLACE INTO season_regulations (
                season_num, tier, consecutive_stable_seasons, is_announced, announcement_week, 
                current_package, upcoming_package, port_back_used, announcement_text
            ) VALUES (?, ?, ?, 0, 9, ?, 'STATUS_QUO', 0, '');
            """,
                (next_season, tier, new_stable, pkg),
            )

            conn.commit()

        return {"tier": tier, "applied_package": pkg, "is_rule_change": is_rule_change, "next_season": season_num + 1}
