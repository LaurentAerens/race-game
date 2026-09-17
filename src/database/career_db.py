import json
import random
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from ..data.balance_config import BALANCE_REGISTRY
from .equipment_catalog import EQUIPMENT_CATALOG

# Fictional Team Names across 5 tiers (10 teams per tier = 50 teams)
TIER_TEAMS = {
    1: [  # Tier 1: World Super Formula (WSF) - Elite Titans
        {"name": "Storm Racing", "color_hex": "#00d2be", "budget": 45000000, "reputation": 95},
        {"name": "Scuderia Veloce", "color_hex": "#dc0000", "budget": 48000000, "reputation": 98},
        {"name": "Apex Dynamics", "color_hex": "#1e41ff", "budget": 42000000, "reputation": 93},
        {"name": "Solaris GP", "color_hex": "#ff8700", "budget": 36000000, "reputation": 88},
        {"name": "AeroStar GP", "color_hex": "#00a0de", "budget": 34000000, "reputation": 85},
        {"name": "Vanguard Motorsport", "color_hex": "#006f62", "budget": 32000000, "reputation": 82},
        {"name": "Titan GP", "color_hex": "#900000", "budget": 30000000, "reputation": 80},
        {"name": "Nexus Racing", "color_hex": "#5e2d79", "budget": 28000000, "reputation": 78},
        {"name": "Kestrel F1", "color_hex": "#ffffff", "budget": 26000000, "reputation": 75},
        {"name": "Neon Velocity", "color_hex": "#b4ff00", "budget": 25000000, "reputation": 74},
    ],
    2: [  # Tier 2: Continental Championship (CC)
        {"name": "Nordic Velocity", "color_hex": "#0088cc", "budget": 18000000, "reputation": 68},
        {"name": "Bavaria Sport", "color_hex": "#3366cc", "budget": 16500000, "reputation": 65},
        {"name": "Riviera Corse", "color_hex": "#cc3333", "budget": 15000000, "reputation": 63},
        {"name": "Silverstone Engineering", "color_hex": "#228844", "budget": 14500000, "reputation": 62},
        {"name": "Iberia Grand Prix", "color_hex": "#e69900", "budget": 13000000, "reputation": 59},
        {"name": "Alps Dynamics", "color_hex": "#8844aa", "budget": 12500000, "reputation": 58},
        {"name": "Danube GP", "color_hex": "#009999", "budget": 11500000, "reputation": 55},
        {"name": "Baltic Motorsport", "color_hex": "#556677", "budget": 11000000, "reputation": 54},
        {"name": "Apennine Racing", "color_hex": "#993355", "budget": 10500000, "reputation": 52},
        {"name": "Caledonia Speed", "color_hex": "#114488", "budget": 10000000, "reputation": 50},
    ],
    3: [  # Tier 3: National Open Cup (NOC) - Starter Playable Tier
        {"name": "Horizon Racing", "color_hex": "#ff6600", "budget": 6500000, "reputation": 45},
        {"name": "Vortex Sprint", "color_hex": "#00aa66", "budget": 6000000, "reputation": 42},
        {"name": "Apex Club Sport", "color_hex": "#336699", "budget": 5800000, "reputation": 40},
        {"name": "Phoenix GP", "color_hex": "#cc4422", "budget": 5500000, "reputation": 38},
        {"name": "Falcon Dynamics", "color_hex": "#778899", "budget": 5200000, "reputation": 36},
        {"name": "Mirage Motorsport", "color_hex": "#9966cc", "budget": 4800000, "reputation": 34},
        {"name": "Pulse Racing Team", "color_hex": "#cc3366", "budget": 4500000, "reputation": 32},
        {"name": "Zephyr Cup", "color_hex": "#0099bb", "budget": 4200000, "reputation": 30},
        {"name": "Stratos Autosport", "color_hex": "#667744", "budget": 4000000, "reputation": 28},
        {"name": "Obsidian GP", "color_hex": "#333333", "budget": 3800000, "reputation": 26},
    ],
    4: [  # Tier 4: Junior Talent Series (JTS) - Feeder League
        {"name": "JTS Academy Blue", "color_hex": "#2255aa", "budget": 1500000, "reputation": 20},
        {"name": "JTS Academy Red", "color_hex": "#aa2222", "budget": 1500000, "reputation": 20},
        {"name": "Future Stars GP", "color_hex": "#22aa55", "budget": 1400000, "reputation": 19},
        {"name": "Nova Talent Cup", "color_hex": "#aa8822", "budget": 1350000, "reputation": 18},
        {"name": "Pioneer Junior GP", "color_hex": "#6633aa", "budget": 1300000, "reputation": 17},
        {"name": "Ascent Autosport", "color_hex": "#2288aa", "budget": 1250000, "reputation": 16},
        {"name": "Velocity Youth", "color_hex": "#aa4466", "budget": 1200000, "reputation": 15},
        {"name": "Vector Pro-Junior", "color_hex": "#55aa22", "budget": 1150000, "reputation": 14},
        {"name": "Rookie Vanguard", "color_hex": "#445566", "budget": 1100000, "reputation": 13},
        {"name": "Zenith Junior", "color_hex": "#775533", "budget": 1000000, "reputation": 12},
    ],
    5: [  # Tier 5: Karting Masters Academy (KMA) - Grassroots Feeder
        {"name": "KMA Elite Alpha", "color_hex": "#114499", "budget": 400000, "reputation": 10},
        {"name": "KMA Elite Beta", "color_hex": "#991111", "budget": 400000, "reputation": 10},
        {"name": "EuroKart Masters", "color_hex": "#119944", "budget": 350000, "reputation": 9},
        {"name": "Nordic Karting", "color_hex": "#997711", "budget": 350000, "reputation": 9},
        {"name": "Monza Kart Club", "color_hex": "#661199", "budget": 300000, "reputation": 8},
        {"name": "Silverstone Kart Cadets", "color_hex": "#117799", "budget": 300000, "reputation": 8},
        {"name": "Spa Young Drivers", "color_hex": "#993355", "budget": 280000, "reputation": 7},
        {"name": "Suzuka Karting School", "color_hex": "#449911", "budget": 260000, "reputation": 6},
        {"name": "Interlagos Juniors", "color_hex": "#334455", "budget": 250000, "reputation": 5},
        {"name": "Apex Karting Academy", "color_hex": "#664422", "budget": 240000, "reputation": 5},
    ],
}

# Fictional Driver Names Pool
CORE_SPECIALTIES = [
    "BRAKES",
    "AERO_SURFACES",
    "FLOOR_UNDERBODY",
    "SUSPENSION",
    "POWERTRAIN_ICE",
    "ERS_HYBRID",
    "COMPOSITES",
    "CNC_MACHINING",
    "QA_DEFECT_SCREENING",
    "PIT_CREW_WHEELGUNS",
    "PIT_CREW_OPERATIONS",
    "RIVAL_INTELLIGENCE",
    "METEOROLOGY",
    "TELEMETRY_ANALYTICS",
    "MERCHANDISE",
    "PRESS_PR",
    "DIGITAL_MEDIA",
    "VIP_HOSPITALITY",
    "STAFF_HR",
    "DRIVER_COGNITIVE",
    "DRIVER_PHYSICAL",
    "DRIVER_PHYSIO",
    "RADIO_COMMS",
    "SCOUTING_YOUTH",
    "JUNIOR_DEVELOPMENT",
]

FACILITY_SPECIALTY_MAP = {
    "eng_workshop": "COMPOSITES",
    "eng_brakes": "BRAKES",
    "eng_wings_front": "AERO_SURFACES",
    "eng_wings_rear": "AERO_SURFACES",
    "eng_floor": "FLOOR_UNDERBODY",
    "eng_suspension": "SUSPENSION",
    "eng_tuning": "POWERTRAIN_ICE",
    "eng_cad_office": "AERO_SURFACES",
    "eng_cfd": "AERO_SURFACES",
    "eng_comp_materials": "COMPOSITES",
    "eng_thermal_rig": "POWERTRAIN_ICE",
    "eng_aero_model_shop": "AERO_SURFACES",
    "eng_kinematics_lab": "SUSPENSION",
    "eng_dyno": "POWERTRAIN_ICE",
    "eng_windtunnel": "AERO_SURFACES",
    "eng_aero_scanning": "AERO_SURFACES",
    "eng_ers": "ERS_HYBRID",
    "eng_works_powertrain": "POWERTRAIN_ICE",
    "mfg_cleanroom_autoclave": "COMPOSITES",
    "mfg_cnc_machining": "CNC_MACHINING",
    "mfg_prepreg_freezer": "COMPOSITES",
    "mfg_rapid_tooling": "COMPOSITES",
    "mfg_electronics": "ERS_HYBRID",
    "mfg_additive_metal": "CNC_MACHINING",
    "mfg_rapid_proto": "COMPOSITES",
    "mfg_monocoque_jig": "COMPOSITES",
    "mfg_exotic_welding": "POWERTRAIN_ICE",
    "mfg_paint_bay": "COMPOSITES",
    "test_shaker_rig": "SUSPENSION",
    "test_qa_ndt": "QA_DEFECT_SCREENING",
    "test_torsional_rig": "COMPOSITES",
    "track_telemetry": "TELEMETRY_ANALYTICS",
    "track_sim_rig": "SUSPENSION",
    "track_pitrig": "PIT_CREW_WHEELGUNS",
    "track_wheelguns": "PIT_CREW_WHEELGUNS",
    "track_fast_repair": "PIT_CREW_OPERATIONS",
    "track_jack_release": "PIT_CREW_OPERATIONS",
    "track_rival_intel": "RIVAL_INTELLIGENCE",
    "track_reverse_eng": "RIVAL_INTELLIGENCE",
    "track_weather_station": "METEOROLOGY",
    "track_setup_telemetry": "TELEMETRY_ANALYTICS",
    "track_virtual_sim": "TELEMETRY_ANALYTICS",
    "track_comm_uplink": "TELEMETRY_ANALYTICS",
    "mkt_press": "PRESS_PR",
    "mkt_broadcast": "DIGITAL_MEDIA",
    "mkt_merch": "MERCHANDISE",
    "mkt_fan_zone": "MERCHANDISE",
    "mkt_vip": "VIP_HOSPITALITY",
    "mkt_museum": "PRESS_PR",
    "hr_recruitment": "STAFF_HR",
    "hr_headhunting": "STAFF_HR",
    "hr_payroll": "STAFF_HR",
    "hr_teambuilding": "STAFF_HR",
    "hr_leadership_institute": "STAFF_HR",
    "hr_performance_review": "STAFF_HR",
    "hr_performance_cull": "STAFF_HR",
    "hr_tech_academy": "STAFF_HR",
    "hr_craft_workshop": "STAFF_HR",
    "hr_workforce_optimizer": "STAFF_HR",
    "hr_wellness_center": "STAFF_HR",
    "hr_equipment_procurement": "STAFF_HR",
    "driver_sim": "SUSPENSION",
    "driver_motion_sim": "SUSPENSION",
    "driver_vr_cognitive": "DRIVER_COGNITIVE",
    "driver_gym_conditioning": "DRIVER_PHYSICAL",
    "driver_physio_recovery": "DRIVER_PHYSIO",
    "driver_media_pr_coach": "PRESS_PR",
    "driver_radio_comms_lab": "RADIO_COMMS",
    "driver_commercial_suite": "VIP_HOSPITALITY",
    "driver_academy": "STAFF_HR",
    "driver_karting_scholarship": "SCOUTING_YOUTH",
    "driver_f4_bootcamp": "JUNIOR_DEVELOPMENT",
    "mgmt_boardroom": "STAFF_HR",
    "mgmt_ops_center": "STAFF_HR",
}


def seed_team_personnel(cur, team_id: int, tier: int, is_player: bool, unlocked_nodes: List[str]):
    """Populates initial personnel, category directors, and inbound applicant queues."""
    categories = ["ENGINEERING", "COMMERCIAL", "TRACKSIDE", "POWERTRAIN", "MANUFACTURING", "TESTING", "HR"]

    if is_player:
        # Player starts with:
        # 1. Apex CEO / Team Principal
        # 2. 7 Category Directors start as VACANT
        for cat in categories:
            cur.execute(
                """
            INSERT OR REPLACE INTO team_category_directors (team_id, category, director_personnel_id)
            VALUES (?, ?, NULL);
            """,
                (team_id, cat),
            )

        # 3. Department Head for every unlocked facility at start (Aged 30-50, mid/low stats, lower leadership)
        for node_id in unlocked_nodes:
            fac_spec = FACILITY_SPECIALTY_MAP.get(node_id, "COMPOSITES")
            h_age = random.randint(30, 50)
            h_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            h_skill = random.randint(35, 52)
            h_lead = random.randint(18, 38)  # Especially lower leadership as requested
            h_comp = random.randint(35, 52)
            h_pot = random.randint(48, 68)
            h_salary = round(h_skill * 75.0, 0)  # ~$2,600 to $3,900 / mo

            cur.execute(
                """
            INSERT INTO personnel (
                team_id, facility_node_id, assigned_category, role_type, name, age, birth_year,
                peak_age, retire_age, specialty, salary_monthly, market_value_monthly, morale,
                stat_engineering, stat_craftsmanship, stat_marketing, stat_communication,
                stat_leadership, stat_composure, stat_potential
            ) VALUES (
                ?, ?, NULL, 'DEPARTMENT_HEAD', ?, ?, 2026 - ?,
                ?, ?, ?, ?, ?, 85.0,
                ?, ?, ?, ?,
                ?, ?, ?
            );
            """,
                (
                    team_id,
                    node_id,
                    h_name,
                    h_age,
                    h_age,
                    random.randint(48, 54),
                    random.randint(67, 75),
                    fac_spec,
                    h_salary,
                    h_salary,
                    h_skill
                    if fac_spec
                    in ["BRAKES", "AERO_SURFACES", "FLOOR_UNDERBODY", "SUSPENSION", "POWERTRAIN_ICE", "ERS_HYBRID"]
                    else random.randint(25, 45),
                    h_skill
                    if fac_spec in ["COMPOSITES", "CNC_MACHINING", "QA_DEFECT_SCREENING", "PIT_CREW_WHEELGUNS"]
                    else random.randint(25, 45),
                    h_skill if fac_spec in ["MERCHANDISE", "VIP_HOSPITALITY"] else random.randint(25, 45),
                    h_skill if fac_spec in ["PRESS_PR", "DIGITAL_MEDIA", "STAFF_HR"] else random.randint(25, 45),
                    h_lead,
                    h_comp,
                    h_pot,
                ),
            )

        # 4. Seed 4 Inbound Applicants / European Intern candidates ready in recruitment queue
        for _ in range(4):
            i_age = random.randint(19, 28)
            i_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            i_spec = random.choice(CORE_SPECIALTIES)
            is_intern = random.random() < 0.50
            is_prodigy = random.random() < 0.28
            i_potential = random.randint(90, 98) if is_prodigy else random.randint(62, 85)
            i_base = random.randint(22, 38) if is_intern else random.randint(42, 65)
            salary = 1000.0 if is_intern else (i_base * 140.0)
            role = "INTERN" if is_intern else "STAFF"

            cur.execute(
                """
            INSERT INTO personnel (
                team_id, facility_node_id, assigned_category, role_type, name, age, birth_year,
                peak_age, retire_age, specialty, salary_monthly, market_value_monthly, morale,
                stat_engineering, stat_craftsmanship, stat_marketing, stat_communication,
                stat_leadership, stat_composure, stat_potential, is_intern, intern_months_completed, intern_months_total, is_potential_revealed
            ) VALUES (
                ?, NULL, NULL, ?, ?, ?, 2026 - ?,
                ?, 67, ?, ?, ?, 95.0,
                ?, ?, ?, ?,
                ?, ?, ?, ?, 0, 6, 0
            );
            """,
                (
                    team_id,
                    role,
                    i_name,
                    i_age,
                    i_age,
                    random.randint(48, 54),
                    i_spec,
                    salary,
                    salary,
                    i_base,
                    i_base,
                    i_base,
                    i_base,
                    random.randint(25, 60),
                    random.randint(25, 60),
                    i_potential,
                    1 if is_intern else 0,
                ),
            )
            new_app_id = cur.lastrowid
            cur.execute(
                """
            INSERT INTO personnel_applications (
                team_id, applicant_personnel_id, applied_role_type, target_facility_node_id, salary_requested, application_week, is_internship_tryout
            ) VALUES (?, ?, ?, NULL, ?, 1, ?);
            """,
                (team_id, new_app_id, role, salary, 1 if is_intern else 0),
            )
        return

    # AI Teams: Seed according to league tier
    tier_base_dir_skill = {1: 82, 2: 72, 3: 58, 4: 45, 5: 35}[tier]
    vacant_chance = 0.0 if tier == 1 else (0.15 if tier <= 3 else 0.40)

    for cat in categories:
        is_vacant = random.random() < vacant_chance
        if is_vacant:
            cur.execute(
                """
            INSERT OR REPLACE INTO team_category_directors (team_id, category, director_personnel_id)
            VALUES (?, ?, NULL);
            """,
                (team_id, cat),
            )
        else:
            age = random.randint(45, 62)
            peak_age = random.randint(48, 54)
            retire_age = random.randint(67, 76)
            name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            skill_base = max(20, min(98, tier_base_dir_skill + random.randint(-6, 6)))
            spec = random.choice(CORE_SPECIALTIES)
            salary = skill_base * 400.0

            cur.execute(
                """
            INSERT INTO personnel (
                team_id, facility_node_id, assigned_category, role_type, name, age, birth_year,
                peak_age, retire_age, specialty, salary_monthly, market_value_monthly, morale,
                stat_engineering, stat_craftsmanship, stat_marketing, stat_communication,
                stat_leadership, stat_composure, stat_potential
            ) VALUES (
                ?, NULL, ?, 'CATEGORY_DIRECTOR', ?, ?, 2026 - ?,
                ?, ?, ?, ?, ?, 90.0,
                ?, ?, ?, ?,
                ?, ?, ?
            );
            """,
                (
                    team_id,
                    cat,
                    name,
                    age,
                    age,
                    peak_age,
                    retire_age,
                    spec,
                    salary,
                    salary,
                    skill_base if cat in ["ENGINEERING", "POWERTRAIN"] else random.randint(30, 60),
                    skill_base if cat in ["MANUFACTURING", "TESTING"] else random.randint(30, 60),
                    skill_base if cat == "COMMERCIAL" else random.randint(30, 60),
                    skill_base if cat in ["COMMERCIAL", "HR"] else random.randint(30, 60),
                    min(99, skill_base + random.randint(2, 10)),
                    min(99, skill_base + random.randint(0, 8)),
                    min(99, skill_base + random.randint(2, 12)),
                ),
            )
            dir_id = cur.lastrowid
            cur.execute(
                """
            INSERT OR REPLACE INTO team_category_directors (team_id, category, director_personnel_id)
            VALUES (?, ?, ?);
            """,
                (team_id, cat, dir_id),
            )

    # AI Facility Department Heads & Staff for unlocked nodes
    tier_base_staff_skill = {1: 78, 2: 68, 3: 52, 4: 40, 5: 30}[tier]
    for node_id in unlocked_nodes:
        fac_spec = FACILITY_SPECIALTY_MAP.get(node_id, "COMPOSITES")

        # Department Head (1 per unlocked facility)
        head_age = random.randint(38, 58)
        head_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        head_skill = max(20, min(96, tier_base_staff_skill + random.randint(-4, 8)))
        head_salary = head_skill * 250.0

        cur.execute(
            """
        INSERT INTO personnel (
            team_id, facility_node_id, assigned_category, role_type, name, age, birth_year,
            peak_age, retire_age, specialty, salary_monthly, market_value_monthly, morale,
            stat_engineering, stat_craftsmanship, stat_marketing, stat_communication,
            stat_leadership, stat_composure, stat_potential
        ) VALUES (
            ?, ?, NULL, 'DEPARTMENT_HEAD', ?, ?, 2026 - ?,
            ?, ?, ?, ?, ?, 88.0,
            ?, ?, ?, ?,
            ?, ?, ?
        );
        """,
            (
                team_id,
                node_id,
                head_name,
                head_age,
                head_age,
                random.randint(48, 54),
                random.randint(67, 75),
                fac_spec,
                head_salary,
                head_salary,
                head_skill
                if fac_spec
                in ["BRAKES", "AERO_SURFACES", "FLOOR_UNDERBODY", "SUSPENSION", "POWERTRAIN_ICE", "ERS_HYBRID"]
                else random.randint(30, 55),
                head_skill
                if fac_spec in ["COMPOSITES", "CNC_MACHINING", "QA_DEFECT_SCREENING", "PIT_CREW_WHEELGUNS"]
                else random.randint(30, 55),
                head_skill if fac_spec in ["MERCHANDISE", "VIP_HOSPITALITY"] else random.randint(30, 55),
                head_skill if fac_spec in ["PRESS_PR", "DIGITAL_MEDIA", "STAFF_HR"] else random.randint(30, 55),
                min(98, head_skill + random.randint(4, 12)),
                min(98, head_skill + random.randint(0, 8)),
                min(99, head_skill + random.randint(2, 10)),
            ),
        )

        # Specialist Staff
        num_staff = 2 if tier >= 4 else 3
        for _ in range(num_staff):
            s_age = random.randint(22, 48)
            s_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            s_skill = max(18, min(95, tier_base_staff_skill + random.randint(-8, 6)))
            s_spec = fac_spec if random.random() < 0.70 else random.choice(CORE_SPECIALTIES)
            s_salary = s_skill * 150.0

            cur.execute(
                """
            INSERT INTO personnel (
                team_id, facility_node_id, assigned_category, role_type, name, age, birth_year,
                peak_age, retire_age, specialty, salary_monthly, market_value_monthly, morale,
                stat_engineering, stat_craftsmanship, stat_marketing, stat_communication,
                stat_leadership, stat_composure, stat_potential
            ) VALUES (
                ?, ?, NULL, 'STAFF', ?, ?, 2026 - ?,
                ?, ?, ?, ?, ?, 85.0,
                ?, ?, ?, ?,
                ?, ?, ?
            );
            """,
                (
                    team_id,
                    node_id,
                    s_name,
                    s_age,
                    s_age,
                    random.randint(47, 53),
                    random.randint(67, 72),
                    s_spec,
                    s_salary,
                    s_salary,
                    s_skill
                    if s_spec
                    in ["BRAKES", "AERO_SURFACES", "FLOOR_UNDERBODY", "SUSPENSION", "POWERTRAIN_ICE", "ERS_HYBRID"]
                    else random.randint(25, 50),
                    s_skill
                    if s_spec in ["COMPOSITES", "CNC_MACHINING", "QA_DEFECT_SCREENING", "PIT_CREW_WHEELGUNS"]
                    else random.randint(25, 50),
                    s_skill if s_spec in ["MERCHANDISE", "VIP_HOSPITALITY"] else random.randint(25, 50),
                    s_skill if s_spec in ["PRESS_PR", "DIGITAL_MEDIA", "STAFF_HR"] else random.randint(25, 50),
                    random.randint(25, 65),
                    random.randint(30, 75),
                    min(99, s_skill + random.randint(5, 20) if s_age < 28 else s_skill + 4),
                ),
            )


FIRST_NAMES = [
    "Lucas",
    "Marco",
    "Julian",
    "Alex",
    "Liam",
    "Carlos",
    "Nikita",
    "Arthur",
    "Oliver",
    "Felix",
    "Sebastian",
    "Gabriel",
    "Mateo",
    "Henrik",
    "Soren",
    "David",
    "Max",
    "Daniel",
    "Oscar",
    "Lando",
    "George",
    "Pierre",
    "Esteban",
    "Yuki",
    "Valtteri",
    "Fernando",
    "Sergio",
    "Lance",
    "Charles",
    "Lewis",
    "Kimi",
    "Kai",
    "Hugo",
    "Leo",
    "Theo",
    "Nico",
    "Jenson",
    "Mika",
    "Ayrton",
]
LAST_NAMES = [
    "Sterling",
    "Vance",
    "Moreno",
    "Tanaka",
    "Lindqvist",
    "Kovacs",
    "Rousseau",
    "Castillo",
    "De Vries",
    "Novak",
    "Sato",
    "Bergstrom",
    "Dupont",
    "Alvarez",
    "Fischer",
    "Nakamura",
    "Bianchi",
    "Kowalski",
    "Schneider",
    "Larsson",
    "Rossi",
    "Muller",
    "Webber",
    "Barrichello",
    "Hakkinen",
    "Prost",
    "Mansell",
    "Villeneuve",
    "Hill",
    "Coulthard",
    "Montoya",
    "Kubica",
    "Glock",
    "Trulli",
]

ALL_FACILITY_NODES = [
    # LAYER 0 (ROOT - TIER 3 STARTER GATEWAY)
    (
        "eng_workshop",
        "ENGINEERING",
        "R&D Workshop",
        "Base manufacturing shop for brakes & chassis",
        None,
        1,
        3,
        2200000,
        75000,
        12,
        1,
    ),
    # LAYER 1 (PRIMARY GATEWAYS & CORE DEPARTMENTS)
    # Tier 3 Gateways (~$1.8M - $2.2M):
    (
        "eng_brakes",
        "ENGINEERING",
        "Brakes Lab",
        "Caliper bite, cooling discs & lockup resistance",
        "eng_workshop",
        1,
        3,
        1800000,
        55000,
        8,
        1,
    ),
    (
        "eng_wings_front",
        "ENGINEERING",
        "Front Aero Lab",
        "Front wing cascade elements & ground clearance",
        "eng_workshop",
        1,
        3,
        2200000,
        65000,
        10,
        1,
    ),
    # Tier 2 Gateways (~$7M - $10M):
    (
        "eng_wings_rear",
        "ENGINEERING",
        "Rear Aero Lab",
        "Rear wing profiles, endplates & DRS flap channels",
        "eng_workshop",
        1,
        3,
        7500000,
        220000,
        10,
        1,
    ),
    (
        "eng_suspension",
        "ENGINEERING",
        "Suspension Shop",
        "Mechanical grip, curb ride & tire wear reduction",
        "eng_workshop",
        1,
        3,
        8500000,
        240000,
        12,
        1,
    ),
    (
        "eng_tuning",
        "ENGINEERING",
        "Engine Tuning",
        "ECU mapping & high-boost tuning calibration (+3.8 Perf, -0.5% Rel)",
        "eng_workshop",
        1,
        3,
        9500000,
        260000,
        10,
        1,
    ),
    (
        "eng_cad_office",
        "ENGINEERING",
        "CAD Design Office",
        "Structural stress FEA modeling & chassis packaging (+5% R&D Success)",
        "eng_workshop",
        1,
        3,
        7000000,
        200000,
        10,
        1,
    ),
    (
        "mfg_cleanroom_autoclave",
        "MANUFACTURING",
        "Autoclave Suite",
        "Carbon pre-preg layup & lightweight chassis (+1.5 Perf/part, -0.3% Rel)",
        "eng_workshop",
        1,
        3,
        10500000,
        300000,
        14,
        1,
    ),
    # LAYER 2 (SPECIALIZED LABS & SECONDARY GATEWAYS - TIER 2 TO TIER 1 JUMPS)
    (
        "eng_cfd",
        "ENGINEERING",
        "CFD Supercluster",
        "Virtual airflow simulation & aerodynamic flow analysis",
        "eng_cad_office",
        1,
        3,
        14000000,
        420000,
        12,
        1,
    ),
    (
        "eng_comp_materials",
        "ENGINEERING",
        "Materials Lab",
        "Microstructures, custom carbon weaves & exotic alloys (+1.5 Perf, +0.8% Rel)",
        "eng_cad_office",
        1,
        3,
        11000000,
        320000,
        10,
        1,
    ),
    (
        "eng_thermal_rig",
        "ENGINEERING",
        "Thermal Flow Rig",
        "Internal radiator airflow & brake duct thermal dissipation",
        "eng_brakes",
        1,
        3,
        10000000,
        290000,
        10,
        1,
    ),
    (
        "eng_aero_model_shop",
        "ENGINEERING",
        "Aero Model Shop",
        "Precision scale model workshop for wind tunnel verification",
        "eng_wings_rear",
        1,
        3,
        9500000,
        280000,
        10,
        1,
    ),
    (
        "eng_kinematics_lab",
        "TESTING",
        "Kinematics Rig",
        "Roll centers, camber gain & anti-dive motion simulation (-6% Tyre Deg)",
        "eng_suspension",
        1,
        3,
        12500000,
        360000,
        12,
        1,
    ),
    (
        "mfg_cnc_machining",
        "MANUFACTURING",
        "5-Axis CNC Shop",
        "Milling suspension uprights, wishbones & solid alloy parts",
        "eng_suspension",
        1,
        3,
        11500000,
        330000,
        14,
        1,
    ),
    (
        "mfg_prepreg_freezer",
        "MANUFACTURING",
        "Pre-Preg Freezers",
        "Sub-zero climate carbon roll storage & CNC ultrasonic ply cutting",
        "mfg_cleanroom_autoclave",
        1,
        3,
        8500000,
        240000,
        10,
        1,
    ),
    (
        "mfg_rapid_tooling",
        "MANUFACTURING",
        "Rapid Tooling",
        "High-speed dense foam routers creating master composite molds",
        "mfg_cleanroom_autoclave",
        1,
        3,
        10000000,
        280000,
        12,
        1,
    ),
    (
        "eng_dyno",
        "POWERTRAIN",
        "Engine Dyno Cells",
        "Transient dynamometers & stress testing (+1.8 Perf, +1.8% Rel)",
        "eng_tuning",
        1,
        3,
        24000000,
        650000,
        16,
        1,
    ),
    (
        "mfg_electronics",
        "MANUFACTURING",
        "Electronics Lab",
        "MIL-SPEC sealed looms, ECUs, sensor arrays & telemetry hardware",
        "eng_tuning",
        1,
        3,
        9500000,
        270000,
        10,
        1,
    ),
    # LAYER 3 (ADVANCED TESTING RIGS & ADDITIVE FABRICATION - TIER 1 PRE-APEX)
    (
        "eng_windtunnel",
        "ENGINEERING",
        "Wind Tunnel",
        "Advanced overarching aerodynamic testing for all aero surfaces (5 Parts)",
        "eng_aero_model_shop",
        1,
        3,
        38000000,
        950000,
        18,
        1,
    ),
    (
        "eng_aero_scanning",
        "ENGINEERING",
        "Aero PIV Scanner",
        "Particle Image Velocimetry & laser boundary layer mapping",
        "eng_cfd",
        1,
        3,
        20000000,
        550000,
        12,
        1,
    ),
    (
        "test_shaker_rig",
        "TESTING",
        "7-Post Shaker Rig",
        "Replicates track surface bumps, kerb strikes & aero heave (+15% Kerb Grip)",
        "eng_kinematics_lab",
        1,
        3,
        22000000,
        600000,
        14,
        1,
    ),
    (
        "mfg_additive_metal",
        "MANUFACTURING",
        "Metal 3D Printing",
        "Direct metal laser sintering of hollow titanium/Inconel components",
        "mfg_cnc_machining",
        1,
        3,
        18000000,
        500000,
        12,
        1,
    ),
    (
        "mfg_rapid_proto",
        "MANUFACTURING",
        "Rapid Prototyping",
        "Additive manufacturing of scale test parts (+8% Innovation Speed)",
        "mfg_cnc_machining",
        1,
        3,
        11000000,
        310000,
        10,
        1,
    ),
    (
        "mfg_monocoque_jig",
        "MANUFACTURING",
        "Monocoque Jig",
        "Ground-anchored steel alignment jigs for carbon safety cell bonding",
        "mfg_prepreg_freezer",
        1,
        3,
        21000000,
        580000,
        14,
        1,
    ),
    (
        "test_qa_ndt",
        "TESTING",
        "QA & NDT Lab",
        "Ultrasonic defect detection & failure prevention (+2.0% Rel, -0.4 Perf | 7 Parts)",
        "mfg_electronics",
        1,
        3,
        9000000,
        260000,
        10,
        1,
    ),
    (
        "mfg_exotic_welding",
        "MANUFACTURING",
        "Exotic Welding",
        "Argon-purged cleanrooms for paper-thin Inconel exhausts",
        "eng_dyno",
        1,
        3,
        12000000,
        340000,
        10,
        1,
    ),
    (
        "eng_ers",
        "POWERTRAIN",
        "ERS Hybrid Lab",
        "High-voltage battery pack assembly, MGU-K/MGU-H maps (Accessible entry-level)",
        "eng_workshop",
        1,
        3,
        9500000,
        260000,
        12,
        1,
    ),
    # LAYER 4 (APEX FACILITIES & POLISH - TIER 1 WORKSHOPS)
    # Accessible entry Level 1 cost between Tier 3 & Tier 2 budget ($8M), but requires Level 2/3 for competitive Tier 1 downforce
    (
        "eng_floor",
        "ENGINEERING",
        "Underbody Lab",
        "Underbody Venturi tunnels & ground effect downforce (Level 1 Starter)",
        "eng_workshop",
        1,
        3,
        8000000,
        220000,
        12,
        1,
    ),
    (
        "mfg_paint_bay",
        "MANUFACTURING",
        "Paint & Livery Bay",
        "Specialized boundary-layer topcoats & lightweight liveries (+0.5 Perf, -0.2% Rel)",
        "eng_workshop",
        1,
        3,
        7500000,
        210000,
        8,
        1,
    ),
    (
        "test_torsional_rig",
        "TESTING",
        "Torsional Rig",
        "Hydraulic load frames twisting bare tubs for structural stiffness",
        "mfg_monocoque_jig",
        1,
        3,
        16000000,
        440000,
        12,
        1,
    ),
    (
        "eng_works_powertrain",
        "POWERTRAIN",
        "Works Engine Lab",
        "Full bespoke V6 Turbo & Works Power Unit builder ($0 Supplier Fee)",
        "eng_tuning",
        1,
        3,
        85000000,
        2400000,
        35,
        1,
    ),
    # HR & WORKFORCE AUTOMATION SUITE
    (
        "hr_recruitment",
        "HR",
        "Recruitment Bureau",
        "T1: Auto-Fill Desks | T2: Auto-Intern Pipeline with Min-Wage Budget Check",
        None,
        1,
        2,
        4500000,
        130000,
        6,
        1,
    ),
    (
        "hr_headhunting",
        "HR",
        "Executive Headhunting",
        "Autonomous rival paddock scouting & best-value talent poaching",
        "hr_recruitment",
        1,
        3,
        8500000,
        240000,
        8,
        1,
    ),
    (
        "hr_payroll",
        "HR",
        "Payroll Calibration",
        "Automated market wage adjustments within budget to prevent discontent",
        "hr_recruitment",
        1,
        3,
        6000000,
        170000,
        6,
        1,
    ),
    (
        "hr_teambuilding",
        "HR",
        "Culture & Welfare",
        "Buffers underpaid wage discontent (25-35%) & accelerates morale recovery",
        "hr_recruitment",
        1,
        3,
        9000000,
        260000,
        8,
        1,
    ),
    (
        "hr_leadership_institute",
        "HR",
        "Leadership Institute",
        "Accelerates weekly Leadership & Communication growth for Heads & Directors",
        "hr_recruitment",
        1,
        3,
        12000000,
        340000,
        10,
        1,
    ),
    (
        "hr_performance_review",
        "HR",
        "Performance Analytics",
        "Fog-of-War Stat Clarity: Narrows stat uncertainty range to exact numbers",
        "hr_recruitment",
        1,
        3,
        10500000,
        300000,
        10,
        1,
    ),
    (
        "hr_performance_cull",
        "HR",
        "Talent Exit Review",
        "Demographic age-curve review: auto-dismisses severe underperformers",
        "hr_performance_review",
        1,
        3,
        7500000,
        210000,
        8,
        1,
    ),
    (
        "hr_tech_academy",
        "HR",
        "Tech R&D Academy",
        "Weekly training gains for Engineering stat & potential conversion",
        "hr_performance_review",
        1,
        3,
        16000000,
        440000,
        12,
        1,
    ),
    (
        "hr_craft_workshop",
        "HR",
        "Craft Guild",
        "Weekly training gains for Craftsmanship & Composure for mfg/testing techs",
        "hr_performance_review",
        1,
        3,
        14000000,
        390000,
        10,
        1,
    ),
    (
        "hr_workforce_optimizer",
        "HR",
        "Succession Optimizer",
        "Auto-replaces staff when strictly superior talent is available for same/lower wage",
        "hr_performance_cull",
        1,
        3,
        19000000,
        520000,
        12,
        1,
    ),
    (
        "hr_wellness_center",
        "HR",
        "Longevity Center",
        "Extends peak age to 54 & reduces post-50 stat degradation by 60%",
        "hr_teambuilding",
        1,
        3,
        13500000,
        380000,
        10,
        1,
    ),
    (
        "hr_equipment_procurement",
        "HR",
        "Rig Procurement",
        "Uses accumulated Department Savings to auto-buy/upgrade equipment rigs",
        "hr_payroll",
        1,
        3,
        11000000,
        310000,
        10,
        1,
    ),
    # COMMERCIAL & MARKETING
    (
        "mkt_press",
        "COMMERCIAL",
        "Press & PR Office",
        "Media access, press releases & sentiment protection (+4 Marketability)",
        None,
        1,
        3,
        2400000,
        70000,
        6,
        1,
    ),
    (
        "mkt_brand_design",
        "COMMERCIAL",
        "Brand & Livery",
        "Livery styling & decal placement (+6 Marketability, +5% Sponsor Value)",
        "mkt_press",
        1,
        3,
        8500000,
        240000,
        8,
        1,
    ),
    (
        "mkt_digital",
        "COMMERCIAL",
        "Digital & Social",
        "Real-time coverage & viral fan channels (+8 Marketability)",
        "mkt_press",
        1,
        3,
        7800000,
        220000,
        8,
        1,
    ),
    (
        "mkt_merch",
        "COMMERCIAL",
        "Merchandise",
        "Official apparel & fan gear (+5 Marketability & performance-scaled retail sales)",
        "mkt_brand_design",
        1,
        3,
        11500000,
        320000,
        10,
        1,
    ),
    (
        "mkt_fan_club",
        "COMMERCIAL",
        "Fan Club",
        "Fan community & loyalty voting (+5 Marketability & performance-scaled dues)",
        "mkt_digital",
        1,
        3,
        9500000,
        270000,
        8,
        1,
    ),
    (
        "mkt_studio",
        "COMMERCIAL",
        "Media Studio",
        "Soundstage, car launches & docuseries (+12 Marketability)",
        "mkt_digital",
        1,
        3,
        21000000,
        580000,
        12,
        1,
    ),
    (
        "mkt_hospitality",
        "COMMERCIAL",
        "VIP Hospitality",
        "Paddock Club suites & executive lounges (+10 Sponsor Appeal)",
        "mkt_brand_design",
        1,
        3,
        29000000,
        780000,
        14,
        1,
    ),
    (
        "mkt_licensing",
        "COMMERCIAL",
        "Brand Licensing",
        "Gaming CAD & diecast partnerships (+6 Marketability & licensing royalties)",
        "mkt_merch",
        1,
        3,
        16500000,
        450000,
        10,
        1,
    ),
    (
        "mkt_esports",
        "COMMERCIAL",
        "Esports Rig",
        "Factory sim racing team & streaming rigs (+6 Marketability)",
        "mkt_studio",
        1,
        3,
        13500000,
        380000,
        10,
        1,
    ),
    (
        "mkt_heritage",
        "COMMERCIAL",
        "Heritage Museum",
        "Championship trophy showroom (+8 Marketability + 4 pts/Title & museum income)",
        "mkt_licensing",
        1,
        3,
        25000000,
        680000,
        12,
        1,
    ),
    (
        "mkt_customer_racing",
        "COMMERCIAL",
        "Customer Racing",
        "Retired F1 chassis sales & VIP client track days (+15 Sponsor Appeal & sales)",
        "mkt_hospitality",
        1,
        3,
        65000000,
        1750000,
        18,
        1,
    ),
    # TRACKSIDE & PIT CREW
    (
        "track_pitrig",
        "TRACKSIDE",
        "Pit Practice Rig",
        "Basic 12-man pit crew reaction training",
        None,
        1,
        3,
        2200000,
        68000,
        14,
        1,
    ),
    (
        "track_wheelguns",
        "TRACKSIDE",
        "Carbon Guns",
        "2.1s pit stops & laser wheel-nut alignment",
        "track_pitrig",
        1,
        3,
        12500000,
        360000,
        18,
        1,
    ),
    (
        "track_telemetry",
        "TRACKSIDE",
        "Track Telemetry",
        "High-accuracy live weather & race telemetry",
        "track_pitrig",
        1,
        3,
        9800000,
        280000,
        8,
        1,
    ),
    (
        "track_fast_repair",
        "TRACKSIDE",
        "Rapid Repair Gantry",
        "Sub-2.5s wing swaps & rapid composite bonding (-50% repair box time)",
        "track_wheelguns",
        1,
        3,
        13500000,
        390000,
        12,
        1,
    ),
    (
        "track_jack_release",
        "TRACKSIDE",
        "Active Jack & Release",
        "Sub-0.2s pneumatic lifting & automated green-light traffic gantry (Sub-2.0s stops)",
        "track_fast_repair",
        1,
        3,
        21000000,
        580000,
        14,
        1,
    ),
    (
        "track_rival_intel",
        "TRACKSIDE",
        "Paddock Recon Unit",
        "Trackside rival intelligence, acoustic listening & +40% competitor pitch roll rate",
        "track_telemetry",
        1,
        3,
        11500000,
        330000,
        10,
        1,
    ),
    (
        "track_reverse_eng",
        "TRACKSIDE",
        "Optical Telemetry Intercept",
        "Pit-straight dynamic LIDAR ride height profiling & +35% reverse-engineering knowledge",
        "track_rival_intel",
        1,
        3,
        19000000,
        520000,
        12,
        1,
    ),
    (
        "track_weather_station",
        "TRACKSIDE",
        "Doppler Weather Radar",
        "Dual-polarization mobile radar extending race rain forecast to 16 laps",
        "track_telemetry",
        1,
        3,
        12000000,
        350000,
        8,
        1,
    ),
    (
        "track_setup_telemetry",
        "TRACKSIDE",
        "Setup Analytics",
        "Dynamic ride height & damper telemetry providing recommended setup ranges in FP",
        "track_telemetry",
        1,
        3,
        15000000,
        420000,
        10,
        1,
    ),
    (
        "track_virtual_sim",
        "TRACKSIDE",
        "Virtual FP Solver",
        "10,000 synthetic pre-weekend laps ensuring FP1 starts significantly closer to optimal",
        "track_setup_telemetry",
        1,
        3,
        26000000,
        720000,
        12,
        1,
    ),
    (
        "track_comm_uplink",
        "TRACKSIDE",
        "Factory Mission Control",
        "10,000Hz satellite telemetry uplink boosting post-race knowledge & reliability on all parts",
        "track_telemetry",
        1,
        3,
        22000000,
        600000,
        12,
        1,
    ),
    # DRIVER PERFORMANCE & ACADEMY
    (
        "driver_sim",
        "DRIVER_PERF",
        "Driver Sim Rig",
        "Driver track familiarity & baseline training",
        None,
        1,
        3,
        2300000,
        72000,
        6,
        1,
    ),
    (
        "driver_motion_sim",
        "DRIVER_PERF",
        "Hexapod Sim",
        "Driver-in-the-Loop Hexapod Sim (+50% driver XP)",
        "driver_sim",
        1,
        3,
        26000000,
        720000,
        10,
        1,
    ),
    (
        "driver_vr_cognitive",
        "DRIVER_PERF",
        "Neuro-Reflex Lab",
        "Batak reaction matrix & saccade tracking (+30% Race Starts, Defending & Consistency)",
        "driver_motion_sim",
        1,
        3,
        13500000,
        390000,
        8,
        1,
    ),
    (
        "driver_gym_conditioning",
        "DRIVER_PERF",
        "Biometric Gym",
        "G-force neck harnesses & sauna heat chambers (+25% Tire Management & Wet Weather)",
        "driver_sim",
        1,
        3,
        9500000,
        275000,
        8,
        1,
    ),
    (
        "driver_physio_recovery",
        "DRIVER_PERF",
        "Physio Clinic",
        "Cryotherapy & hyperbaric recovery (-35% Age 30+ physical decline decay)",
        "driver_gym_conditioning",
        1,
        3,
        17000000,
        480000,
        10,
        1,
    ),
    (
        "driver_media_pr_coach",
        "DRIVER_PERF",
        "Media & PR Studio",
        "Paddock press simulation & crisis coaching (+35% Marketability & morale shield)",
        "driver_sim",
        1,
        3,
        10500000,
        300000,
        8,
        1,
    ),
    (
        "driver_radio_comms_lab",
        "DRIVER_PERF",
        "Radio Comms Lab",
        "115dB cockpit acoustic simulation & telemetry debrief (+35% Comms & +15% R&D insight)",
        "driver_media_pr_coach",
        1,
        3,
        14000000,
        400000,
        10,
        1,
    ),
    (
        "driver_commercial_suite",
        "DRIVER_PERF",
        "Sponsor Suite",
        "Brand ambassador stage & VIP lounges (+5 Sponsor Appeal & +6% race bonus)",
        "driver_media_pr_coach",
        1,
        3,
        18500000,
        520000,
        12,
        1,
    ),
    (
        "driver_academy",
        "DRIVER_PERF",
        "Driver Academy",
        "Scout, sign & fund junior drivers in feeder leagues",
        "driver_sim",
        1,
        3,
        16000000,
        460000,
        12,
        1,
    ),
    (
        "driver_karting_scholarship",
        "DRIVER_PERF",
        "Karting Foundation",
        "Grassroots talent radar in Tier 5 KMA (Guaranteed prodigy & +4 min potential floor)",
        "driver_academy",
        1,
        3,
        19000000,
        540000,
        12,
        1,
    ),
    (
        "driver_f4_bootcamp",
        "DRIVER_PERF",
        "Junior Boot Camp",
        "Single-seater test fleet & telemetry track camp (+35% Feeder Driver XP & smooth promotion)",
        "driver_karting_scholarship",
        1,
        3,
        24000000,
        680000,
        14,
        1,
    ),
    # MANAGEMENT (SINGLE-NODE FACTORY LEADERSHIP ENGINE)
    (
        "mgmt_boardroom",
        "MANAGEMENT",
        "Executive Boardroom",
        "Executive leadership command center improving overall leadership, coordination, and synergy for all factory personnel (+5 to +15 Global Leadership)",
        None,
        1,
        3,
        2600000,
        78000,
        8,
        1,
    ),
]


class CareerDatabase:
    """Master SQLite Database Manager for the Motorsport Management Career."""

    def __init__(self, db_path: str = "career.db"):
        self.db_path = db_path
        self._open_connections: List[sqlite3.Connection] = []
        self.init_schema()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA busy_timeout = 30000;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.row_factory = sqlite3.Row
        self._open_connections.append(conn)
        return conn

    def close(self):
        """Closes all open connections created by this database instance."""
        for conn in list(self._open_connections):
            try:
                conn.close()
            except sqlite3.Error as e:
                print(f"[CareerDatabase] Warning closing SQLite connection: {e}")
            except Exception as e:
                print(f"[CareerDatabase] Unexpected error closing SQLite connection: {e}")
        self._open_connections.clear()

    def init_schema(self):
        """Creates all 5-tier league tables, staff, driver matrix, and node tree facilities."""
        with self.get_connection() as conn:
            cur = conn.cursor()

            # 1. Leagues (5 Tiers)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS leagues (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                code TEXT NOT NULL,
                tier INTEGER NOT NULL,
                is_playable BOOLEAN NOT NULL,
                base_prize_pool REAL NOT NULL,
                sponsor_multiplier REAL NOT NULL,
                custom_parts_allowed TEXT NOT NULL
            );
            """)

            # 2. Teams (50 Teams)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                base_name TEXT NOT NULL DEFAULT '',
                color_hex TEXT NOT NULL,
                tier INTEGER NOT NULL,
                is_player BOOLEAN NOT NULL DEFAULT 0,
                cash REAL NOT NULL,
                reputation INTEGER NOT NULL,
                points INTEGER NOT NULL DEFAULT 0,
                engine_supplier TEXT NOT NULL DEFAULT 'Vortex EcoTech',
                engine_contract_cost REAL NOT NULL DEFAULT 350000,
                engine_contract_races_left INTEGER NOT NULL DEFAULT 10,
                engine_locked_for_season BOOLEAN NOT NULL DEFAULT 1,
                monthly_engineering_budget REAL NOT NULL DEFAULT 60000,
                monthly_hr_budget REAL NOT NULL DEFAULT 15000,
                monthly_marketing_budget REAL NOT NULL DEFAULT 20000,
                monthly_trackside_budget REAL NOT NULL DEFAULT 25000,
                auto_hire_enabled BOOLEAN NOT NULL DEFAULT 1,
                difficulty TEXT NOT NULL DEFAULT 'NORMAL'
            );


            """)

            # 3. Drivers (11-Attribute Matrix & Junior Academy)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS drivers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                number INTEGER NOT NULL,
                is_player_driver BOOLEAN NOT NULL DEFAULT 0,
                is_academy_driver BOOLEAN NOT NULL DEFAULT 0,
                academy_tier_placement INTEGER DEFAULT NULL,
                academy_team_name TEXT DEFAULT '',
                academy_seat_rating INTEGER DEFAULT 3,
                academy_seat_expected_pos TEXT DEFAULT 'P1 / 10',
                academy_seat_cost REAL DEFAULT 0.0,
                training_focus TEXT NOT NULL DEFAULT 'BALANCED',
                has_out_of_league_trait BOOLEAN NOT NULL DEFAULT 0,
                salary_per_race REAL NOT NULL,
                contract_races_left INTEGER NOT NULL,
                potential INTEGER NOT NULL,
                morale REAL NOT NULL DEFAULT 80.0,

                -- 8 On-Track Driving Attributes
                race_starts INTEGER NOT NULL,

                braking INTEGER NOT NULL,
                pace INTEGER NOT NULL,
                consistency INTEGER NOT NULL,
                tire_management INTEGER NOT NULL,
                defending INTEGER NOT NULL,
                fuel_efficiency INTEGER NOT NULL,
                wet_weather INTEGER NOT NULL,
                -- 3 Off-Track & Setup Attributes
                technical_understanding INTEGER NOT NULL,
                communication INTEGER NOT NULL,
                marketability INTEGER NOT NULL,
                xp_progress REAL NOT NULL DEFAULT 0.0,
                FOREIGN KEY (team_id) REFERENCES teams(id)
            );
            """)

            # 4. Facility Nodes & Tech Tree (Root Departments & Granular Sub-Nodes)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS facility_nodes (
                id TEXT PRIMARY KEY,
                department TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                parent_id TEXT,
                tier INTEGER NOT NULL DEFAULT 1,
                max_tier INTEGER NOT NULL DEFAULT 3,
                base_cost REAL NOT NULL,
                base_upkeep REAL NOT NULL,
                staff_capacity INTEGER NOT NULL DEFAULT 5,
                unlock_league_tier INTEGER NOT NULL DEFAULT 3
            );
            """)

            # 5. Team Facilities, Sub-Node Monthly Budgets & Department Savings Accounts
            cur.execute("""
            CREATE TABLE IF NOT EXISTS team_facilities (
                team_id INTEGER NOT NULL,
                node_id TEXT NOT NULL,
                current_tier INTEGER NOT NULL DEFAULT 0,
                is_unlocked BOOLEAN NOT NULL DEFAULT 0,
                monthly_sub_budget REAL NOT NULL DEFAULT 10000,
                savings_balance REAL NOT NULL DEFAULT 0.0,
                PRIMARY KEY (team_id, node_id),
                FOREIGN KEY (team_id) REFERENCES teams(id),
                FOREIGN KEY (node_id) REFERENCES facility_nodes(id)
            );
            """)

            try:
                cur.execute("ALTER TABLE team_facilities ADD COLUMN savings_balance REAL DEFAULT 0.0;")
            except Exception:
                # Column may already exist in upgraded schemas
                pass

            # 5b. HR Department Automation Policies & Thresholds
            cur.execute("""
            CREATE TABLE IF NOT EXISTS team_hr_policies (
                team_id INTEGER PRIMARY KEY,
                auto_fill_desks BOOLEAN NOT NULL DEFAULT 1,
                auto_intern_pipeline BOOLEAN NOT NULL DEFAULT 1,
                auto_headhunt BOOLEAN NOT NULL DEFAULT 0,
                auto_payroll BOOLEAN NOT NULL DEFAULT 1,
                auto_cull BOOLEAN NOT NULL DEFAULT 0,
                auto_replace BOOLEAN NOT NULL DEFAULT 0,
                auto_equip_procure BOOLEAN NOT NULL DEFAULT 1,
                min_intern_potential INTEGER NOT NULL DEFAULT 75,
                max_cull_underperform_deficit REAL NOT NULL DEFAULT 20.0,
                FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
            );
            """)

            # 6. Workforce Staff (Specialists 20 to 1,000 Scaling)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                assigned_subnode TEXT NOT NULL,
                skill INTEGER NOT NULL,
                salary_monthly REAL NOT NULL,
                morale REAL NOT NULL DEFAULT 80.0,
                FOREIGN KEY (team_id) REFERENCES teams(id)
            );
            """)

            # 7. Car Components & Continuous Evolution Knowledge Pool
            cur.execute("""
            CREATE TABLE IF NOT EXISTS car_components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                car_slot INTEGER NOT NULL, -- 1 or 2, 0 for warehouse spare inventory
                category TEXT NOT NULL,    -- 'BRAKES', 'REAR_WING', 'FRONT_WING', 'SUSPENSION', 'ENGINE', 'FLOOR', 'ERS'
                generation INTEGER NOT NULL DEFAULT 1, -- Mk 1, Mk 2, etc.
                performance REAL NOT NULL,
                reliability REAL NOT NULL,
                wear_pct REAL NOT NULL DEFAULT 0.0,
                -- Continuous Knowledge Evolution Pool (0.0 when 0 races on concept)
                knowledge_min REAL NOT NULL DEFAULT 0.0,
                knowledge_max REAL NOT NULL DEFAULT 0.0,
                rel_knowledge_min REAL NOT NULL DEFAULT 0.0,
                rel_knowledge_max REAL NOT NULL DEFAULT 0.0,
                races_on_concept INTEGER NOT NULL DEFAULT 0,
                max_durability REAL NOT NULL DEFAULT 100.0,
                current_durability REAL NOT NULL DEFAULT 100.0,
                FOREIGN KEY (team_id) REFERENCES teams(id)
            );
            """)

            # Safe migrations for existing databases
            for col_name, col_type in [
                ("max_durability", "REAL NOT NULL DEFAULT 100.0"),
                ("current_durability", "REAL NOT NULL DEFAULT 100.0"),
            ]:
                try:
                    cur.execute(f"ALTER TABLE car_components ADD COLUMN {col_name} {col_type};")
                except Exception:
                    # Column may already exist in upgraded schemas
                    pass

            # 8. Innovation Pipeline (Breakthrough Ideas & Fog-of-War Ranges)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS innovation_pitches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                proposer_name TEXT NOT NULL,
                category TEXT NOT NULL,
                locked_subnode TEXT NOT NULL,
                lockout_weeks INTEGER NOT NULL,
                hard_cost REAL NOT NULL,
                -- Fog-of-war estimated ranges
                est_success_min INTEGER NOT NULL,
                est_success_max INTEGER NOT NULL,
                actual_success_rate INTEGER NOT NULL,
                est_perf_min REAL NOT NULL,
                est_perf_max REAL NOT NULL,
                actual_perf_gain REAL NOT NULL,
                est_rel_min REAL NOT NULL,
                est_rel_max REAL NOT NULL,
                actual_rel_gain REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING', -- 'PENDING', 'ACTIVE', 'COMPLETED', 'DISCARDED'
                weeks_remaining INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (team_id) REFERENCES teams(id)
            );
            """)

            # 9. Specialized Facility Equipment Rigs & Autonomous Department Assets
            cur.execute("""
            CREATE TABLE IF NOT EXISTS facility_equipment (
                id TEXT PRIMARY KEY,
                node_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                base_cost REAL NOT NULL,
                base_upkeep REAL NOT NULL,
                perf_bonus_per_level REAL NOT NULL DEFAULT 0.3,
                rel_bonus_per_level REAL NOT NULL DEFAULT 0.2,
                unlocked_at_facility_tier INTEGER NOT NULL DEFAULT 1,
                max_level INTEGER NOT NULL DEFAULT 5,
                FOREIGN KEY (node_id) REFERENCES facility_nodes(id)
            );
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS team_equipment (
                team_id INTEGER NOT NULL,
                equipment_id TEXT NOT NULL,
                current_level INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY (team_id, equipment_id),
                FOREIGN KEY (team_id) REFERENCES teams(id),
                FOREIGN KEY (equipment_id) REFERENCES facility_equipment(id)
            );
            """)

            # 9. Championship Calendar & Standings (Multi-Tier with Track Characteristics & 18-Week Season)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS calendar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tier INTEGER NOT NULL DEFAULT 3,
                round INTEGER NOT NULL,
                week INTEGER NOT NULL DEFAULT 1,
                track_name TEXT NOT NULL,
                circuit_file TEXT NOT NULL,
                total_laps INTEGER NOT NULL DEFAULT 15,
                weather_profile TEXT NOT NULL DEFAULT 'DYNAMIC',
                is_completed BOOLEAN NOT NULL DEFAULT 0,
                characteristic TEXT NOT NULL DEFAULT 'BALANCED',
                UNIQUE(tier, round)
            );
            """)

            # Migration check: ensure week column exists in calendar
            cur.execute("PRAGMA table_info(calendar);")
            cal_cols = [r[1] for r in cur.fetchall()]
            if "week" not in cal_cols:
                cur.execute("ALTER TABLE calendar ADD COLUMN week INTEGER NOT NULL DEFAULT 1;")

            # Migration check: ensure points, champion columns exist in drivers
            cur.execute("PRAGMA table_info(drivers);")
            d_cols = [r[1] for r in cur.fetchall()]
            if "points" not in d_cols:
                cur.execute("ALTER TABLE drivers ADD COLUMN points INTEGER NOT NULL DEFAULT 0;")
            if "is_champion" not in d_cols:
                cur.execute("ALTER TABLE drivers ADD COLUMN is_champion INTEGER NOT NULL DEFAULT 0;")
            if "champion_titles" not in d_cols:
                cur.execute("ALTER TABLE drivers ADD COLUMN champion_titles INTEGER NOT NULL DEFAULT 0;")
            if "champion_mood" not in d_cols:
                cur.execute("ALTER TABLE drivers ADD COLUMN champion_mood TEXT NOT NULL DEFAULT '';")

            # Migration check: ensure relegated titan tracking in teams
            cur.execute("PRAGMA table_info(teams);")
            t_cols = [r[1] for r in cur.fetchall()]
            if "is_relegated_titan" not in t_cols:
                cur.execute("ALTER TABLE teams ADD COLUMN is_relegated_titan INTEGER NOT NULL DEFAULT 0;")
            if "relegated_rnd_boost" not in t_cols:
                cur.execute("ALTER TABLE teams ADD COLUMN relegated_rnd_boost REAL NOT NULL DEFAULT 1.0;")

            # Ensure calendar is seeded for all 5 tiers
            cur.execute("SELECT COUNT(*) FROM calendar;")
            if cur.fetchone()[0] == 0:
                self._seed_calendar(cur)
            else:
                self._migrate_calendar_weeks(cur)

            # 9b. Historical & Current Season Series Race Results
            cur.execute("""
            CREATE TABLE IF NOT EXISTS series_race_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tier INTEGER NOT NULL,
                round_num INTEGER NOT NULL,
                week INTEGER NOT NULL,
                track_name TEXT NOT NULL,
                position INTEGER NOT NULL,
                driver_name TEXT NOT NULL,
                team_name TEXT NOT NULL,
                team_id INTEGER,
                driver_id INTEGER,
                is_academy_driver BOOLEAN NOT NULL DEFAULT 0,
                is_player BOOLEAN NOT NULL DEFAULT 0,
                points INTEGER NOT NULL DEFAULT 0
            );
            """)

            # Migration check: ensure season_num column exists in series_race_results
            cur.execute("PRAGMA table_info(series_race_results);")
            srr_cols = [r[1] for r in cur.fetchall()]
            if "season_num" not in srr_cols:
                cur.execute("ALTER TABLE series_race_results ADD COLUMN season_num INTEGER NOT NULL DEFAULT 1;")

            # 9c. Historical Driver Season Standings
            cur.execute("""
            CREATE TABLE IF NOT EXISTS driver_season_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver_id INTEGER,
                driver_name TEXT NOT NULL,
                team_id INTEGER,
                team_name TEXT NOT NULL,
                tier INTEGER NOT NULL,
                season_num INTEGER NOT NULL,
                championship_position INTEGER NOT NULL,
                points INTEGER NOT NULL DEFAULT 0,
                race_starts INTEGER NOT NULL DEFAULT 0,
                wins INTEGER NOT NULL DEFAULT 0,
                podiums INTEGER NOT NULL DEFAULT 0,
                is_player_driver BOOLEAN NOT NULL DEFAULT 0,
                is_academy_driver BOOLEAN NOT NULL DEFAULT 0
            );
            """)

            # 9d. Team Alumni & Former Drivers Tracker
            cur.execute("""
            CREATE TABLE IF NOT EXISTS team_alumni (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_team_id INTEGER NOT NULL,
                driver_id INTEGER NOT NULL,
                driver_name TEXT NOT NULL,
                seasons_active TEXT NOT NULL DEFAULT '',
                starts_with_team INTEGER NOT NULL DEFAULT 0,
                wins_with_team INTEGER NOT NULL DEFAULT 0,
                podiums_with_team INTEGER NOT NULL DEFAULT 0,
                points_with_team INTEGER NOT NULL DEFAULT 0,
                departure_reason TEXT NOT NULL DEFAULT 'RELEASED',
                departure_season INTEGER NOT NULL DEFAULT 1,
                current_team_id INTEGER,
                current_team_name TEXT DEFAULT '',
                current_tier INTEGER DEFAULT NULL
            );
            """)

            # 10. Financial Transactions Ledger
            cur.execute("""
            CREATE TABLE IF NOT EXISTS ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                week INTEGER NOT NULL,
                category TEXT NOT NULL, -- 'PRIZE_MONEY', 'SPONSOR', 'PAYROLL', 'SUB_BUDGET', 'RND_BUILD', 'INNOVATION'
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                FOREIGN KEY (team_id) REFERENCES teams(id)
            );
            """)

            # 11. Active Team Sponsors & Contract Slots (2 Title, 4 Middle, 10 Minor)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS active_sponsors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                slot_tier TEXT NOT NULL, -- 'TITLE', 'MIDDLE', 'MINOR'
                slot_index INTEGER NOT NULL,
                brand_name TEXT NOT NULL,
                color_hex TEXT NOT NULL DEFAULT '#00d2be',
                races_total INTEGER NOT NULL,
                races_remaining INTEGER NOT NULL,
                signing_bonus REAL NOT NULL DEFAULT 0.0,
                per_race_payment REAL NOT NULL,
                target_position INTEGER DEFAULT NULL,
                target_bonus REAL NOT NULL DEFAULT 0.0,
                FOREIGN KEY (team_id) REFERENCES teams(id)
            );
            """)

            # 12. Incoming Sponsor Offers
            cur.execute("""
            CREATE TABLE IF NOT EXISTS sponsor_offers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                slot_tier TEXT NOT NULL, -- 'TITLE', 'MIDDLE', 'MINOR'
                brand_name TEXT NOT NULL,
                color_hex TEXT NOT NULL DEFAULT '#00d2be',
                races_total INTEGER NOT NULL,
                signing_bonus REAL NOT NULL,
                per_race_payment REAL NOT NULL,
                target_position INTEGER DEFAULT NULL,
                target_bonus REAL NOT NULL DEFAULT 0.0,
                required_appeal INTEGER NOT NULL,
                FOREIGN KEY (team_id) REFERENCES teams(id)
            );
            """)

            # 13. Historical Race Results (Last 10 Races Form Tracker)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS race_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                season_num INTEGER NOT NULL,
                round_num INTEGER NOT NULL,
                finish_position INTEGER NOT NULL,
                points_scored INTEGER NOT NULL,
                FOREIGN KEY (team_id) REFERENCES teams(id)
            );
            """)

            # 14. Historical Season Standings (Prestige Tracker)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS season_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                season_num INTEGER NOT NULL,
                tier INTEGER NOT NULL,
                championship_position INTEGER NOT NULL,
                points_total INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (team_id) REFERENCES teams(id)
            );
            """)

            # 14b. Technical Regulations and Next-Gen Season Rules
            cur.execute("""
            CREATE TABLE IF NOT EXISTS season_regulations (
                season_num INTEGER NOT NULL,
                tier INTEGER NOT NULL,
                consecutive_stable_seasons INTEGER NOT NULL DEFAULT 0,
                is_announced BOOLEAN NOT NULL DEFAULT 0,
                announcement_week INTEGER NOT NULL DEFAULT 9,
                current_package TEXT NOT NULL DEFAULT 'STATUS_QUO',
                upcoming_package TEXT NOT NULL DEFAULT 'STATUS_QUO',
                port_back_used BOOLEAN NOT NULL DEFAULT 0,
                announcement_text TEXT DEFAULT '',
                PRIMARY KEY (season_num, tier)
            );
            """)

            # 15. Scouted Young Driver Candidates & Prospect Pool
            cur.execute("""
            CREATE TABLE IF NOT EXISTS scout_prospects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                nationality TEXT NOT NULL,
                potential INTEGER NOT NULL,
                scout_rating INTEGER NOT NULL,
                scouting_notes TEXT NOT NULL,
                pace INTEGER NOT NULL,
                race_starts INTEGER NOT NULL,
                braking INTEGER NOT NULL,
                tire_management INTEGER NOT NULL,
                defending INTEGER NOT NULL,
                wet_weather INTEGER NOT NULL,
                technical_understanding INTEGER NOT NULL,
                communication INTEGER NOT NULL,
                marketability INTEGER NOT NULL,
                preferred_tier INTEGER NOT NULL DEFAULT 4,
                placement_fee_season REAL NOT NULL DEFAULT 80000.0,
                FOREIGN KEY (team_id) REFERENCES teams(id)
            );
            """)

            # 16. Living Feeder Market Seats (Occupancy, Requirements, Asymmetric Pricing, Scarcity & Mid-Season Transfers)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS feeder_market_seats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tier INTEGER NOT NULL,
                team_name TEXT NOT NULL,
                league_name TEXT NOT NULL,
                seat_slot INTEGER NOT NULL, -- 1, 2, or 3
                rating INTEGER NOT NULL,
                expected_pos TEXT NOT NULL DEFAULT 'P1 - P3',
                perf INTEGER NOT NULL,
                base_cost REAL NOT NULL,
                current_cost REAL NOT NULL,
                min_age INTEGER NOT NULL DEFAULT 15,
                min_overall INTEGER NOT NULL DEFAULT 30,
                min_pace INTEGER NOT NULL DEFAULT 30,
                pricing_model TEXT NOT NULL DEFAULT 'STANDARD', -- 'BARGAIN', 'OVERPRICED', 'PRESTIGE', 'BUDGET', 'STANDARD'
                pricing_note TEXT NOT NULL DEFAULT '',
                is_occupied BOOLEAN NOT NULL DEFAULT 0,
                occupant_team_id INTEGER DEFAULT NULL,
                occupant_driver_id INTEGER DEFAULT NULL,
                occupant_driver_name TEXT DEFAULT '',
                status TEXT NOT NULL,
                xp_rate TEXT DEFAULT '',
                xp_mult REAL DEFAULT 1.0
            );
            """)

            # 17. Driver Market Pool (Standard, Pay-Drivers, and Sponsored Loan Talents)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS driver_market (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                nationality TEXT NOT NULL,
                tier INTEGER NOT NULL DEFAULT 3,
                driver_type TEXT NOT NULL DEFAULT 'STANDARD', -- 'STANDARD', 'PAY_DRIVER', 'SPONSORED_DRIVER'
                patience INTEGER NOT NULL DEFAULT 3,
                current_patience INTEGER NOT NULL DEFAULT 3,
                contract_preference TEXT NOT NULL DEFAULT 'BALANCED',
                expected_salary_race REAL NOT NULL,
                expected_signing_bonus REAL NOT NULL,
                expected_role TEXT NOT NULL DEFAULT 'EQUAL',
                expected_seasons INTEGER NOT NULL DEFAULT 2,
                parent_team_name TEXT DEFAULT '',
                parent_team_tier INTEGER DEFAULT 1,
                parent_team_expected_pos TEXT DEFAULT 'P1 / 10',
                pay_driver_sponsor_name TEXT DEFAULT '',
                sponsor_income_per_race REAL DEFAULT 0.0,
                potential INTEGER NOT NULL,
                morale REAL NOT NULL DEFAULT 80.0,
                pace INTEGER NOT NULL,
                race_starts INTEGER NOT NULL,
                braking INTEGER NOT NULL,
                tire_management INTEGER NOT NULL,
                defending INTEGER NOT NULL,
                wet_weather INTEGER NOT NULL,
                consistency INTEGER NOT NULL DEFAULT 50,
                fuel_efficiency INTEGER NOT NULL DEFAULT 50,
                technical_understanding INTEGER NOT NULL,
                communication INTEGER NOT NULL,
                marketability INTEGER NOT NULL,
                pot_pace INTEGER,
                pot_race_starts INTEGER,
                pot_braking INTEGER,
                pot_tire_management INTEGER,
                pot_defending INTEGER,
                pot_wet_weather INTEGER,
                pot_consistency INTEGER,
                pot_fuel_efficiency INTEGER,
                pot_technical_understanding INTEGER,
                pot_communication INTEGER,
                pot_marketability INTEGER
            );
            """)

            # Automatic SQLite column migrations for new feature fields
            cur.execute("PRAGMA table_info(feeder_market_seats);")
            fm_cols = [c[1] for c in cur.fetchall()]
            if "expected_pos" not in fm_cols:
                cur.execute("ALTER TABLE feeder_market_seats ADD COLUMN expected_pos TEXT NOT NULL DEFAULT 'P1 / 10';")

            cur.execute("PRAGMA table_info(drivers);")
            d_cols = [c[1] for c in cur.fetchall()]
            if "academy_seat_expected_pos" not in d_cols:
                cur.execute("ALTER TABLE drivers ADD COLUMN academy_seat_expected_pos TEXT DEFAULT 'P1 / 10';")

            # Contract Negotiation Columns
            contract_cols = [
                ("patience", "INTEGER DEFAULT 3"),
                ("contract_seasons_left", "INTEGER DEFAULT 1"),
                ("signing_bonus", "REAL DEFAULT 0.0"),
                ("role_status", "TEXT DEFAULT 'EQUAL'"),
                ("contract_preference", "TEXT DEFAULT 'BALANCED'"),
                ("is_homegrown", "BOOLEAN DEFAULT 0"),
                ("main_team_seasons", "INTEGER DEFAULT 0"),
                ("driver_type", "TEXT DEFAULT 'STANDARD'"),
                ("parent_team_name", "TEXT DEFAULT ''"),
                ("parent_team_tier", "INTEGER DEFAULT 1"),
                ("parent_team_expected_pos", "TEXT DEFAULT 'P1 / 10'"),
                ("sponsor_income_per_race", "REAL DEFAULT 0.0"),
                ("pay_driver_sponsor_name", "TEXT DEFAULT ''"),
            ]
            for col_name, col_def in contract_cols:
                if col_name not in d_cols:
                    cur.execute(f"ALTER TABLE drivers ADD COLUMN {col_name} {col_def};")

            # 11 Individual Stat Potential Caps
            stat_names = [
                "pace",
                "braking",
                "tire_management",
                "race_starts",
                "consistency",
                "defending",
                "wet_weather",
                "fuel_efficiency",
                "technical_understanding",
                "communication",
                "marketability",
            ]
            for s in stat_names:
                p_col = f"pot_{s}"
                if p_col not in d_cols:
                    cur.execute(f"ALTER TABLE drivers ADD COLUMN {p_col} INTEGER DEFAULT NULL;")

            # Also for scout_prospects
            cur.execute("PRAGMA table_info(scout_prospects);")
            sp_cols = [c[1] for c in cur.fetchall()]
            for s in stat_names:
                p_col = f"pot_{s}"
                if p_col not in sp_cols:
                    cur.execute(f"ALTER TABLE scout_prospects ADD COLUMN {p_col} INTEGER DEFAULT NULL;")

            # Innovation Pitches Pipeline Columns (Creative Inventions vs Competitor Intel)
            cur.execute("PRAGMA table_info(innovation_pitches);")
            ip_cols = [c[1] for c in cur.fetchall()]
            innovation_cols = [
                ("idea_type", "TEXT NOT NULL DEFAULT 'CREATIVE'"),
                ("target_categories", "TEXT NOT NULL DEFAULT ''"),
                ("knowledge_gain", "REAL NOT NULL DEFAULT 0.0"),
                ("observed_from", "TEXT NOT NULL DEFAULT ''"),
            ]
            for col_name, col_def in innovation_cols:
                if col_name not in ip_cols:
                    cur.execute(f"ALTER TABLE innovation_pitches ADD COLUMN {col_name} {col_def};")

            # Car Components Reliability Knowledge Migration
            cur.execute("PRAGMA table_info(car_components);")
            cc_cols = [c[1] for c in cur.fetchall()]
            if "rel_knowledge_min" not in cc_cols:
                cur.execute("ALTER TABLE car_components ADD COLUMN rel_knowledge_min REAL NOT NULL DEFAULT 0.0;")
            if "rel_knowledge_max" not in cc_cols:
                cur.execute("ALTER TABLE car_components ADD COLUMN rel_knowledge_max REAL NOT NULL DEFAULT 0.0;")

            # Teams Principal Name & Difficulty Column Migration
            cur.execute("PRAGMA table_info(teams);")
            t_cols = [c[1] for c in cur.fetchall()]
            if "difficulty" not in t_cols:
                cur.execute("ALTER TABLE teams ADD COLUMN difficulty TEXT NOT NULL DEFAULT 'NORMAL';")
            if "principal_name" not in t_cols:
                cur.execute("ALTER TABLE teams ADD COLUMN principal_name TEXT NOT NULL DEFAULT 'Alex Mercer';")

            # Next-Gen Car R&D and Chassis Base Attributes Migration
            new_team_cols = [
                ("next_gen_rnd_pct", "REAL NOT NULL DEFAULT 0.0"),
                ("next_gen_rnd_points", "REAL NOT NULL DEFAULT 0.0"),
                ("chassis_perf_boost", "REAL NOT NULL DEFAULT 0.0"),
                ("chassis_rel_boost", "REAL NOT NULL DEFAULT 0.0"),
                ("chassis_tire_preservation_base", "REAL NOT NULL DEFAULT 85.0"),
                ("chassis_fuel_efficiency_base", "REAL NOT NULL DEFAULT 85.0"),
                ("port_back_cooldown_weeks", "INTEGER NOT NULL DEFAULT 0"),
                ("port_back_bonus_weeks", "INTEGER NOT NULL DEFAULT 0"),
                ("port_back_bonus_rel", "REAL NOT NULL DEFAULT 0.0"),
            ]
            for col_name, col_def in new_team_cols:
                if col_name not in t_cols:
                    cur.execute(f"ALTER TABLE teams ADD COLUMN {col_name} {col_def};")

            # Facility Equipment Reliability Bonus Migration
            cur.execute("PRAGMA table_info(facility_equipment);")
            fe_cols = [c[1] for c in cur.fetchall()]
            if "rel_bonus_per_level" not in fe_cols:
                cur.execute("ALTER TABLE facility_equipment ADD COLUMN rel_bonus_per_level REAL NOT NULL DEFAULT 0.2;")

            # 18. Personnel & Organizational Hierarchy System Tables
            cur.execute("""
            CREATE TABLE IF NOT EXISTS personnel (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                facility_node_id TEXT, -- Hard 1-to-1 link to team_facilities.node_id (NULL for Category Directors or free agents)
                assigned_category TEXT, -- For Category Directors (e.g. 'ENGINEERING', 'COMMERCIAL', etc.)
                role_type TEXT NOT NULL CHECK(role_type IN ('CATEGORY_DIRECTOR', 'DEPARTMENT_HEAD', 'STAFF', 'INTERN')),
                name TEXT NOT NULL,
                age INTEGER NOT NULL CHECK(age >= 18 AND age <= 85),
                birth_year INTEGER NOT NULL,
                peak_age INTEGER NOT NULL DEFAULT 50,
                retire_age INTEGER NOT NULL DEFAULT 67,
                is_retiring_soon INTEGER NOT NULL DEFAULT 0,
                
                -- Specialty & Financials
                specialty TEXT NOT NULL, -- e.g. 'BRAKES', 'AERO_SURFACES', 'POWERTRAIN_ICE', 'PRESS_PR', etc.
                salary_monthly REAL NOT NULL DEFAULT 8000.0,
                market_value_monthly REAL NOT NULL DEFAULT 8000.0,
                morale REAL NOT NULL DEFAULT 85.0 CHECK(morale >= 0.0 AND morale <= 100.0),
                contract_months_served INTEGER NOT NULL DEFAULT 0,
                
                -- 7 Streamlined Core Universal Stats (0.0 - 100.0)
                stat_engineering REAL NOT NULL DEFAULT 35.0,
                stat_craftsmanship REAL NOT NULL DEFAULT 35.0,
                stat_marketing REAL NOT NULL DEFAULT 35.0,
                stat_communication REAL NOT NULL DEFAULT 35.0,
                stat_leadership REAL NOT NULL DEFAULT 35.0,
                stat_composure REAL NOT NULL DEFAULT 35.0,
                stat_potential REAL NOT NULL DEFAULT 60.0,
                
                -- European 6-Month Internship Tryout
                is_intern INTEGER NOT NULL DEFAULT 0,
                intern_months_completed INTEGER NOT NULL DEFAULT 0,
                intern_months_total INTEGER NOT NULL DEFAULT 6,
                intern_mentor_id INTEGER REFERENCES personnel(id) ON DELETE SET NULL,
                is_potential_revealed INTEGER NOT NULL DEFAULT 0,
                
                FOREIGN KEY(team_id) REFERENCES teams(id) ON DELETE CASCADE,
                FOREIGN KEY(facility_node_id) REFERENCES team_facilities(node_id) ON DELETE SET NULL
            );
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS team_category_directors (
                team_id INTEGER NOT NULL,
                category TEXT NOT NULL CHECK(category IN ('ENGINEERING', 'COMMERCIAL', 'TRACKSIDE', 'POWERTRAIN', 'MANUFACTURING', 'TESTING', 'HR', 'DRIVER_PERF', 'MANAGEMENT')),
                director_personnel_id INTEGER REFERENCES personnel(id) ON DELETE SET NULL,
                PRIMARY KEY(team_id, category),
                FOREIGN KEY(team_id) REFERENCES teams(id) ON DELETE CASCADE
            );
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS personnel_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                applicant_personnel_id INTEGER NOT NULL REFERENCES personnel(id) ON DELETE CASCADE,
                applied_role_type TEXT NOT NULL,
                target_facility_node_id TEXT,
                salary_requested REAL NOT NULL,
                application_week INTEGER NOT NULL,
                is_internship_tryout INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(team_id) REFERENCES teams(id) ON DELETE CASCADE
            );
            """)

            cur.execute("CREATE INDEX IF NOT EXISTS idx_personnel_facility ON personnel(team_id, facility_node_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_personnel_role ON personnel(team_id, role_type);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_calendar_tier_week ON calendar(tier, week, is_completed);")
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_series_race_results_season ON series_race_results(season_num, tier, driver_id);"
            )
            cur.execute("CREATE INDEX IF NOT EXISTS idx_season_history_team ON season_history(team_id, season_num);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_drivers_team ON drivers(team_id, is_academy_driver);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_car_components_team ON car_components(team_id, car_slot);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_active_sponsors_team ON active_sponsors(team_id, slot_tier);")

            # 19. Central Balance Settings / AppSettings Table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS balance_settings (
                key TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                value_json TEXT NOT NULL,
                description TEXT
            );
            """)

            # 20. Tutorial Progress Table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS tutorial_progress (
                team_id INTEGER PRIMARY KEY,
                current_step_id TEXT NOT NULL DEFAULT 'WELCOME_DASHBOARD',
                is_active BOOLEAN NOT NULL DEFAULT 1,
                is_completed BOOLEAN NOT NULL DEFAULT 0,
                is_skipped BOOLEAN NOT NULL DEFAULT 0,
                brakes_equipment_bought BOOLEAN NOT NULL DEFAULT 0,
                personnel_hired BOOLEAN NOT NULL DEFAULT 0,
                front_wing_built BOOLEAN NOT NULL DEFAULT 0,
                driver_placed BOOLEAN NOT NULL DEFAULT 0,
                sponsor_signed BOOLEAN NOT NULL DEFAULT 0
            );
            """)

            # 21. Personal Track Setup Presets
            cur.execute("""
            CREATE TABLE IF NOT EXISTS track_setup_presets (
                team_id INTEGER NOT NULL,
                track_name TEXT NOT NULL,
                car_slot INTEGER NOT NULL DEFAULT 1,
                front_wing REAL NOT NULL,
                rear_wing REAL NOT NULL,
                suspension REAL NOT NULL,
                gear_ratio REAL NOT NULL,
                brake_bias REAL NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (team_id, track_name, car_slot)
            );
            """)

            cur.execute("SELECT COUNT(*) FROM balance_settings;")
            if cur.fetchone()[0] == 0:
                for cat, settings in BALANCE_REGISTRY.to_dict().items():
                    cur.execute(
                        """
                    INSERT OR REPLACE INTO balance_settings (key, category, value_json, description)
                    VALUES (?, ?, ?, ?);
                    """,
                        (cat, "BALANCE", json.dumps(settings), f"Configuration parameters for {cat}"),
                    )

            # Ensure all dedicated facility nodes exist in facility_nodes
            for n in ALL_FACILITY_NODES:
                cur.execute("INSERT OR REPLACE INTO facility_nodes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", n)

            # Ensure all equipment catalog entries exist
            cur.executemany(
                "INSERT OR REPLACE INTO facility_equipment VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", EQUIPMENT_CATALOG
            )

            # Safety Personnel Migration for Existing Saves
            cur.execute("SELECT id, tier, is_player FROM teams;")
            existing_teams = cur.fetchall()
            for t_row in existing_teams:
                t_id = t_row[0]
                t_tier = t_row[1]
                t_is_player = bool(t_row[2])
                cur.execute("SELECT COUNT(*) FROM personnel WHERE team_id = ?;", (t_id,))
                p_cnt = cur.fetchone()[0]
                if p_cnt == 0:
                    cur.execute("SELECT node_id FROM team_facilities WHERE team_id = ? AND is_unlocked = 1;", (t_id,))
                    u_nodes = [r[0] for r in cur.fetchall()]
                    if not u_nodes:
                        u_nodes = [
                            "eng_workshop",
                            "eng_brakes",
                            "eng_wings_front",
                            "mkt_press",
                            "track_pitrig",
                            "driver_sim",
                            "mgmt_boardroom",
                        ]
                    seed_team_personnel(cur, t_id, t_tier, t_is_player, u_nodes)

            conn.commit()

        self._seed_default_data()
        self._seed_historical_seasons()

        # Purge orphaned series_race_results for current season if no championship races are completed yet
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM calendar WHERE is_completed = 1;")
            completed_races = cur.fetchone()[0]
            if completed_races == 0:
                cur.execute("SELECT COALESCE(MAX(season_num), 0) + 1 FROM season_history WHERE season_num >= 1;")
                curr_s_row = cur.fetchone()
                curr_s = int(curr_s_row[0]) if curr_s_row and curr_s_row[0] is not None else 1
                cur.execute("DELETE FROM series_race_results WHERE season_num = ?;", (curr_s,))
                conn.commit()

    def _seed_default_data(self):
        """Populates the 5 tiers, teams, facility node definitions, initial staff and parts."""
        with self.get_connection() as conn:
            cur = conn.cursor()

            # Check if already seeded
            cur.execute("SELECT COUNT(*) FROM leagues;")
            if cur.fetchone()[0] > 0:
                return

            # Seed 5 Leagues
            leagues_data = [
                (
                    1,
                    "World Super Formula",
                    "WSF",
                    1,
                    1,
                    200000000,
                    3.5,
                    "BRAKES,REAR_WING,FRONT_WING,SUSPENSION,ENGINE,FLOOR,ERS",
                ),
                (
                    2,
                    "Continental Championship",
                    "CC",
                    2,
                    1,
                    60000000,
                    2.0,
                    "BRAKES,REAR_WING,FRONT_WING,SUSPENSION,ENGINE",
                ),
                (3, "National Open Cup", "NOC", 3, 1, 15000000, 1.0, "BRAKES,FRONT_WING"),
                (4, "Junior Talent Series", "JTS", 4, 0, 3000000, 0.4, "SPEC"),
                (5, "Karting Masters Academy", "KMA", 5, 0, 800000, 0.15, "SPEC"),
            ]
            cur.executemany("INSERT INTO leagues VALUES (?, ?, ?, ?, ?, ?, ?, ?);", leagues_data)

            # Seed Facility Tech Tree Nodes ($5M–$10M Early Upgrades up to $250M Late Upgrades)
            # Already seeded in init_schema from ALL_FACILITY_NODES

            # Seed Specialized Facility Equipment Rigs (135+ Pieces)
            cur.executemany(
                "INSERT OR REPLACE INTO facility_equipment VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", EQUIPMENT_CATALOG
            )

            # Seed 50 Teams & Initial Drivers across the 5 Tiers
            driver_number_pool = list(range(2, 99))
            random.shuffle(driver_number_pool)

            for tier, teams_list in TIER_TEAMS.items():
                for t_idx, t_data in enumerate(teams_list):
                    is_player = tier == 3 and t_idx == 0  # Horizon Racing in Tier 3 is the default Player Team!

                    cur.execute(
                        """
                    INSERT INTO teams (name, base_name, color_hex, tier, is_player, cash, reputation)
                    VALUES (?, ?, ?, ?, ?, ?, ?);
                    """,
                        (
                            t_data["name"],
                            t_data["name"],
                            t_data["color_hex"],
                            tier,
                            1 if is_player else 0,
                            t_data["budget"],
                            t_data["reputation"],
                        ),
                    )

                    team_id = cur.lastrowid

                    # Unlock base facilities for this team (No HR unlocked at start)
                    base_nodes = [
                        "eng_workshop",
                        "eng_brakes",
                        "eng_wings_front",
                        "mkt_press",
                        "track_pitrig",
                        "driver_sim",
                        "mgmt_boardroom",
                    ]
                    if tier <= 2:
                        base_nodes.extend(
                            [
                                "eng_wings_rear",
                                "eng_windtunnel",
                                "eng_suspension",
                                "eng_tuning",
                                "eng_cfd",
                                "eng_cad_office",
                                "track_wheelguns",
                                "track_telemetry",
                                "driver_motion_sim",
                            ]
                        )
                    if tier == 1:
                        base_nodes.extend(
                            [
                                "eng_floor",
                                "eng_ers",
                                "eng_dyno",
                                "eng_works_powertrain",
                                "mfg_cleanroom_autoclave",
                                "mfg_cnc_machining",
                                "test_shaker_rig",
                                "test_qa_ndt",
                                "mkt_hospitality",
                                "driver_academy",
                                "hr_recruitment",
                                "track_fast_repair",
                                "track_setup_telemetry",
                            ]
                        )

                    for node_id in base_nodes:
                        cur.execute("SELECT base_upkeep FROM facility_nodes WHERE id = ?;", (node_id,))
                        bu_row = cur.fetchone()
                        base_upk = float(bu_row[0]) if bu_row else 20000.0
                        cur.execute(
                            """
                        INSERT INTO team_facilities (team_id, node_id, current_tier, is_unlocked, monthly_sub_budget)
                        VALUES (?, ?, 1, 1, ?);
                        """,
                            (team_id, node_id, base_upk),
                        )

                    # Seed 1-to-1 Personnel (Directors, Department Heads, Staff Specialists, and rare Interns)
                    seed_team_personnel(cur, team_id, tier, is_player, base_nodes)

                    # Update starter facility budgets so they always cover starter head & staff salaries
                    for node_id in base_nodes:
                        cur.execute(
                            "SELECT SUM(salary_monthly) FROM personnel WHERE team_id = ? AND facility_node_id = ?;",
                            (team_id, node_id),
                        )
                        staff_sal = float(cur.fetchone()[0] or 0.0)
                        cur.execute("SELECT base_upkeep FROM facility_nodes WHERE id = ?;", (node_id,))
                        base_upk = float(cur.fetchone()[0] or 0.0)
                        min_init_budget = base_upk + staff_sal
                        cur.execute(
                            "UPDATE team_facilities SET monthly_sub_budget = MAX(monthly_sub_budget, ?) WHERE team_id = ? AND node_id = ?;",
                            (min_init_budget, team_id, node_id),
                        )

                    # Seed initial team equipment levels (all equipment starts at Level 0 with 0 impact)
                    for eq in EQUIPMENT_CATALOG:
                        eq_id = eq[0]
                        cur.execute(
                            """
                        INSERT INTO team_equipment (team_id, equipment_id, current_level, is_active)
                        VALUES (?, ?, 0, 0);
                        """,
                            (team_id, eq_id),
                        )

                    # Generate Drivers: 3 drivers for Tiers 4 & 5, 2 drivers for Tiers 1, 2, 3
                    # Player team always starts with Default Drivers (30yo+, bad stats, 0-yr contract, free to replace)
                    driver_slots = [1, 2, 3] if tier in [4, 5] else [1, 2]
                    for d_slot in driver_slots:
                        d_num = driver_number_pool.pop() if driver_number_pool else random.randint(2, 99)
                        if is_player:
                            age = random.randint(32, 38)
                            d_name = "Robin Sterling" if d_slot == 1 else "Morgan Cross"
                            base_val = random.randint(22, 28)
                            cur.execute(
                                """
                            INSERT INTO drivers (
                                team_id, name, age, number, is_player_driver, is_academy_driver,
                                training_focus, salary_per_race, contract_races_left, contract_seasons_left,
                                driver_type, role_status, potential, morale,
                                race_starts, braking, pace, consistency, tire_management, defending,
                                fuel_efficiency, wet_weather, technical_understanding, communication, marketability,
                                pot_pace, pot_race_starts, pot_braking, pot_tire_management, pot_defending, pot_wet_weather,
                                pot_consistency, pot_fuel_efficiency, pot_technical_understanding, pot_communication, pot_marketability
                            ) VALUES (
                                ?, ?, ?, ?, ?, 0,
                                'BALANCED', 1250.0, 0, 0,
                                'DEFAULT_DRIVER', 'EQUAL', 35, 75.0,
                                ?, ?, ?, ?, ?, ?,
                                ?, ?, ?, ?, ?,
                                35, 35, 35, 35, 35, 35,
                                35, 35, 40, 40, 40
                            );
                            """,
                                (
                                    team_id,
                                    d_name,
                                    age,
                                    d_num,
                                    1 if d_slot == 1 else 0,
                                    base_val,
                                    base_val,
                                    base_val,
                                    base_val,
                                    base_val,
                                    base_val,
                                    base_val,
                                    base_val,
                                    base_val,
                                    base_val,
                                    base_val,
                                ),
                            )
                        else:
                            age = random.randint(18, 34)
                            # Base skill scales with tier
                            tier_base_skill = {1: 85, 2: 72, 3: 58, 4: 42, 5: 30}[tier]
                            skill_var = random.randint(-5, 6)
                            base_val = max(15, min(98, tier_base_skill + skill_var))
                            d_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

                            cur.execute(
                                """
                            INSERT INTO drivers (
                                team_id, name, age, number, is_player_driver, is_academy_driver,
                                training_focus, salary_per_race, contract_races_left, contract_seasons_left,
                                driver_type, role_status, potential, morale,
                                race_starts, braking, pace, consistency, tire_management, defending,
                                fuel_efficiency, wet_weather, technical_understanding, communication, marketability,
                                pot_pace, pot_race_starts, pot_braking, pot_tire_management, pot_defending, pot_wet_weather,
                                pot_consistency, pot_fuel_efficiency, pot_technical_understanding, pot_communication, pot_marketability
                            ) VALUES (
                                ?, ?, ?, ?, 0, 0,
                                'BALANCED', ?, 12, 1,
                                'STANDARD', 'EQUAL', ?, 85.0,
                                ?, ?, ?, ?, ?, ?,
                                ?, ?, ?, ?, ?,
                                ?, ?, ?, ?, ?, ?,
                                ?, ?, ?, ?, ?
                            );
                            """,
                                (
                                    team_id,
                                    d_name,
                                    age,
                                    d_num,
                                    (base_val * 1200) if tier <= 3 else 1000,
                                    min(99, base_val + random.randint(3, 16) if age < 24 else base_val + 2),
                                    base_val + random.randint(-3, 3),
                                    base_val + random.randint(-3, 3),
                                    base_val + random.randint(-2, 4),
                                    base_val + random.randint(-4, 3),
                                    base_val + random.randint(-3, 3),
                                    base_val + random.randint(-3, 3),
                                    base_val + random.randint(-4, 4),
                                    base_val + random.randint(-5, 5),
                                    base_val + random.randint(-4, 4),
                                    base_val + random.randint(-3, 3),
                                    base_val + random.randint(-5, 5),
                                    min(99, base_val + 6),
                                    min(99, base_val + 6),
                                    min(99, base_val + 6),
                                    min(99, base_val + 6),
                                    min(99, base_val + 6),
                                    min(99, base_val + 6),
                                    min(99, base_val + 6),
                                    min(99, base_val + 6),
                                    min(99, base_val + 8),
                                    min(99, base_val + 8),
                                    min(99, base_val + 8),
                                ),
                            )

                    # Generate Initial Staff workforce (20 to 1,000 scaling)
                    staff_counts = {1: 450, 2: 120, 3: 24, 4: 10, 5: 5}[tier]
                    for s_i in range(staff_counts):
                        s_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
                        cur.execute(
                            """
                        INSERT INTO staff (team_id, name, role, assigned_subnode, skill, salary_monthly)
                        VALUES (?, ?, 'Engineer', 'eng_workshop', ?, ?);
                        """,
                            (team_id, s_name, random.randint(40, 85), 3500 if tier <= 3 else 1500),
                        )

                    # Generate Car Components for Car #1 and Car #2 (0.0 knowledge for 0 races on concept)
                    tier_part_perf = {1: 150.0, 2: 110.0, 3: 75.0, 4: 45.0, 5: 25.0}[tier]
                    tier_durability = {1: 80.0, 2: 72.0, 3: 65.0, 4: 55.0, 5: 45.0}.get(tier, 65.0)
                    for c_slot in [1, 2]:
                        for cat in ["BRAKES", "REAR_WING", "FRONT_WING", "SUSPENSION", "ENGINE", "FLOOR", "ERS"]:
                            if cat == "ENGINE":
                                base_eng_perf = {1: 760.0, 2: 350.0, 3: 75.0, 4: 45.0, 5: 25.0}[tier]
                                p_val = round(base_eng_perf + random.uniform(-5.0, 5.0), 1)
                            else:
                                p_val = round(tier_part_perf + random.uniform(-4.0, 4.0), 1)
                            cur.execute(
                                """
                            INSERT INTO car_components (team_id, car_slot, category, generation, performance, reliability, wear_pct, knowledge_min, knowledge_max, races_on_concept, max_durability, current_durability)
                            VALUES (?, ?, ?, 1, ?, ?, 0.0, 0.0, 0.0, 0, ?, ?);
                            """,
                                (team_id, c_slot, cat, p_val, tier_durability, tier_durability, tier_durability),
                            )

                    # Seed initial spares in warehouse (car_slot = 0) for player team
                    if is_player:
                        for sp_cat, sp_perf in [("FRONT_WING", tier_part_perf), ("BRAKES", tier_part_perf)]:
                            cur.execute(
                                """
                            INSERT INTO car_components (team_id, car_slot, category, generation, performance, reliability, wear_pct, knowledge_min, knowledge_max, races_on_concept, max_durability, current_durability)
                            VALUES (?, 0, ?, 1, ?, ?, 0.0, 0.0, 0.0, 0, ?, ?);
                            """,
                                (team_id, sp_cat, sp_perf, tier_durability, tier_durability, tier_durability),
                            )

            # Seed Championship Calendar Rounds for all 5 Tiers
            self._seed_calendar(cur)
            conn.commit()

    def _migrate_calendar_weeks(self, cur: sqlite3.Cursor):
        """Ensures all calendar rounds have their canonical 18-week schedule assigned."""
        week_mappings = {
            (1, 1): 1,
            (1, 2): 2,
            (1, 3): 3,
            (1, 4): 4,
            (1, 5): 5,
            (1, 6): 6,
            (1, 7): 7,
            (1, 8): 8,
            (1, 9): 10,
            (1, 10): 11,
            (1, 11): 12,
            (1, 12): 13,
            (1, 13): 14,
            (1, 14): 15,
            (1, 15): 16,
            (1, 16): 18,
            (2, 1): 1,
            (2, 2): 2,
            (2, 3): 4,
            (2, 4): 5,
            (2, 5): 7,
            (2, 6): 8,
            (2, 7): 10,
            (2, 8): 11,
            (2, 9): 13,
            (2, 10): 14,
            (2, 11): 16,
            (2, 12): 18,
            (3, 1): 1,
            (3, 2): 3,
            (3, 3): 6,
            (3, 4): 9,
            (3, 5): 12,
            (3, 6): 15,
            (3, 7): 18,
            (4, 1): 2,
            (4, 2): 5,
            (4, 3): 8,
            (4, 4): 11,
            (4, 5): 14,
            (4, 6): 17,
            (5, 1): 1,
            (5, 2): 4,
            (5, 3): 7,
            (5, 4): 10,
            (5, 5): 13,
            (5, 6): 16,
        }
        for (t, r), w in week_mappings.items():
            cur.execute("UPDATE calendar SET week = ? WHERE tier = ? AND round = ?;", (w, t, r))

    def _seed_calendar(self, cur: sqlite3.Cursor):
        """Seeds the championship calendar schedule across all 5 tiers across 18 weeks if table is empty."""
        cur.execute("SELECT COUNT(*) FROM calendar;")
        if cur.fetchone()[0] > 0:
            return

        calendar_schedule = [
            # Tier 1 (16 race weekends) - Pinnacle World Series (Weeks 1-8, 10-16, 18)
            (1, 1, 1, "Emerald Ring Grand Prix", "emerald_ring.json", 16, "DYNAMIC", "BALANCED"),
            (1, 2, 2, "Autodromo Velocita", "autodromo_velocita.json", 18, "SUNNY", "SPEED"),
            (1, 3, 3, "Oasis Grand Prix", "oasis_grand_prix.json", 15, "DYNAMIC", "BRAKES"),
            (1, 4, 4, "Vortex Aero Ring", "vortex_aero_ring.json", 16, "SUNNY", "AERO"),
            (1, 5, 5, "Riviera Speedway", "riviera_speedway.json", 15, "DYNAMIC", "BALANCED"),
            (1, 6, 6, "Ardennes Forest Circuit", "ardennes_forest_circuit.json", 14, "RAIN", "SPEED"),
            (1, 7, 7, "Harbor City Street GP", "harbor_city_street_circuit.json", 18, "SUNNY", "BRAKES"),
            (1, 8, 8, "Apex Park International", "apex_park.json", 16, "DYNAMIC", "BRAKES"),
            (1, 9, 10, "Autodromo Velocita Sprint", "autodromo_velocita.json", 16, "SUNNY", "SPEED"),
            (1, 10, 11, "Vortex Aero Trophy", "vortex_aero_ring.json", 17, "DYNAMIC", "AERO"),
            (1, 11, 12, "Emerald Ring Summer GP", "emerald_ring.json", 16, "SUNNY", "BALANCED"),
            (1, 12, 13, "Oasis Desert Classic", "oasis_grand_prix.json", 15, "SUNNY", "BRAKES"),
            (1, 13, 14, "Ardennes Forest Challenge", "ardennes_forest_circuit.json", 15, "DYNAMIC", "SPEED"),
            (1, 14, 15, "Riviera Super Prix", "riviera_speedway.json", 16, "SUNNY", "BALANCED"),
            (1, 15, 16, "Apex Park Super Trophy", "apex_park.json", 15, "RAIN", "BRAKES"),
            (1, 16, 18, "World Championship Finale GP", "emerald_ring.json", 20, "DYNAMIC", "BALANCED"),
            # Tier 2 (12 race weekends) - Continental Series (Weeks 1, 2, 4, 5, 7, 8, 10, 11, 13, 14, 16, 18)
            (2, 1, 1, "Emerald Ring Grand Prix", "emerald_ring.json", 15, "SUNNY", "BALANCED"),
            (2, 2, 2, "Oasis Grand Prix", "oasis_grand_prix.json", 14, "DYNAMIC", "BRAKES"),
            (2, 3, 4, "Autodromo Velocita", "autodromo_velocita.json", 16, "SUNNY", "SPEED"),
            (2, 4, 5, "Vortex Aero Ring", "vortex_aero_ring.json", 15, "DYNAMIC", "AERO"),
            (2, 5, 7, "Apex Park International", "apex_park.json", 14, "SUNNY", "BRAKES"),
            (2, 6, 8, "Riviera Speedway", "riviera_speedway.json", 15, "DYNAMIC", "BALANCED"),
            (2, 7, 10, "Harbor City Street GP", "harbor_city_street_circuit.json", 16, "SUNNY", "BRAKES"),
            (2, 8, 11, "Ardennes Forest Circuit", "ardennes_forest_circuit.json", 14, "RAIN", "SPEED"),
            (2, 9, 13, "Oasis Night GP", "oasis_grand_prix.json", 14, "DYNAMIC", "BRAKES"),
            (2, 10, 14, "Vortex Sweeper Challenge", "vortex_aero_ring.json", 15, "SUNNY", "AERO"),
            (2, 11, 16, "Autodromo Velocita Super Sprint", "autodromo_velocita.json", 16, "DYNAMIC", "SPEED"),
            (2, 12, 18, "Continental Championship Finale", "emerald_ring.json", 18, "DYNAMIC", "BALANCED"),
            # Tier 3 (7 race weekends) - National Cup (Player Starts Here: Weeks 1, 3, 6, 9, 12, 15, 18)
            (3, 1, 1, "Emerald Ring National GP", "emerald_ring.json", 14, "SUNNY", "BALANCED"),
            (3, 2, 3, "Autodromo Velocita Speed Trophy", "autodromo_velocita.json", 15, "SUNNY", "SPEED"),
            (3, 3, 6, "Apex Park Challenge", "apex_park.json", 14, "DYNAMIC", "BRAKES"),
            (3, 4, 9, "Vortex Aero Classic", "vortex_aero_ring.json", 14, "SUNNY", "AERO"),
            (3, 5, 12, "Harbor City Street GP", "harbor_city_street_circuit.json", 15, "SUNNY", "BRAKES"),
            (3, 6, 15, "Ardennes Forest Cup", "ardennes_forest_circuit.json", 13, "RAIN", "SPEED"),
            (3, 7, 18, "National Championship Finale", "riviera_speedway.json", 16, "DYNAMIC", "BALANCED"),
            # Tier 4 (6 race weekends) - Junior Series (F4 Feeder: Weeks 2, 5, 8, 11, 14, 17)
            (4, 1, 2, "Silverstone National", "silverstone_national", 12, "SUNNY", "AERO"),
            (4, 2, 5, "Oulton Park International", "oulton_park", 12, "DYNAMIC", "BALANCED"),
            (4, 3, 8, "Donington Park National", "donington_park", 12, "SUNNY", "SPEED"),
            (4, 4, 11, "Brands Hatch Indy", "brands_hatch", 14, "DYNAMIC", "BRAKES"),
            (4, 5, 14, "Snetterton 300 Circuit", "snetterton_300", 12, "SUNNY", "SPEED"),
            (4, 6, 17, "Knockhill Junior Finale", "knockhill_circuit", 14, "RAIN", "BRAKES"),
            # Tier 5 (6 race weekends) - Karting Feeder (Weeks 1, 4, 7, 10, 13, 16)
            (5, 1, 1, "Genk International Trophy", "genk_kart", 10, "SUNNY", "BALANCED"),
            (5, 2, 4, "South Garda Winter Cup", "south_garda", 10, "DYNAMIC", "BRAKES"),
            (5, 3, 7, "Wackersdorf Pro Trophy", "wackersdorf", 10, "SUNNY", "SPEED"),
            (5, 4, 10, "Zuera Karting Classic", "zuera_karting", 10, "SUNNY", "AERO"),
            (5, 5, 13, "Lonato Autumn Cup", "lonato_karting", 10, "DYNAMIC", "BRAKES"),
            (5, 6, 16, "Campillos Super Finale", "campillos_karting", 12, "SUNNY", "BALANCED"),
        ]
        cur.executemany(
            """
        INSERT INTO calendar (tier, round, week, track_name, circuit_file, total_laps, weather_profile, characteristic, is_completed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0);
        """,
            calendar_schedule,
        )

    def get_calendar_for_week(self, week: int) -> List[Dict[str, Any]]:
        """Returns all scheduled championship rounds across all 5 tiers for the given season week."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM calendar WHERE week = ? ORDER BY tier ASC;", (week,))
            return [dict(r) for r in cur.fetchall()]

    def get_series_race_results(
        self, tier: int, round_num: int, season_num: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Returns race classification for a specific tier round and season."""
        if season_num is None:
            season_num = self.get_current_season_num()
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            SELECT * FROM series_race_results 
            WHERE tier = ? AND round_num = ? AND season_num = ?
            ORDER BY position ASC;
            """,
                (tier, round_num, season_num),
            )
            return [dict(r) for r in cur.fetchall()]

    def get_weekly_race_results(self, week: int, season_num: Optional[int] = None) -> Dict[int, List[Dict[str, Any]]]:
        """Returns all race results recorded for a given calendar week, keyed by tier."""
        if season_num is None:
            season_num = self.get_current_season_num()
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            SELECT * FROM series_race_results 
            WHERE week = ? AND season_num = ?
            ORDER BY tier ASC, position ASC;
            """,
                (week, season_num),
            )
            rows = [dict(r) for r in cur.fetchall()]
            results_by_tier: Dict[int, List[Dict[str, Any]]] = {}
            for r in rows:
                t = r["tier"]
                if t not in results_by_tier:
                    results_by_tier[t] = []
                results_by_tier[t].append(r)
            return results_by_tier

    def get_driver_standings(self, tier: int) -> List[Dict[str, Any]]:
        """Returns drivers ranked by championship points for the given tier."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            if tier in [4, 5]:
                cur.execute(
                    """
                SELECT d.*, 
                       CASE WHEN d.is_academy_driver = 1 AND d.academy_team_name != '' 
                            THEN d.academy_team_name 
                            ELSE COALESCE(t.name, 'Feeder Team') 
                       END as team_name,
                       COALESCE(t.color_hex, '#4488cc') as team_color_hex
                FROM drivers d
                LEFT JOIN teams t ON d.team_id = t.id
                WHERE (t.tier = ? AND d.is_academy_driver = 0)
                   OR (d.is_academy_driver = 1 AND d.academy_tier_placement = ?)
                ORDER BY d.points DESC, d.pace DESC;
                """,
                    (tier, tier),
                )
            else:
                cur.execute(
                    """
                SELECT d.*, t.name as team_name, t.color_hex as team_color_hex
                FROM drivers d
                JOIN teams t ON d.team_id = t.id
                WHERE t.tier = ? AND d.is_academy_driver = 0
                ORDER BY d.points DESC, d.pace DESC;
                """,
                    (tier,),
                )
            return [dict(r) for r in cur.fetchall()]

    def award_driver_champion(self, driver_id: int) -> Dict[str, Any]:
        """
        Crowns driver as Drivers' Champion:
        - Sets morale = 100.0
        - Marks is_champion = 1, champion_titles += 1, champion_mood = 'WORLD_CHAMPION'
        - Gives permanent champion stat buffs: +2 Pace, +2 Consistency, +2 Defending
        - Boosts marketability by +12 (cap 99)
        - If player's driver: awards $2,500,000 royalty bonus to player team cash and increases team reputation by +8
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            SELECT d.*, t.id as team_id, t.name as team_name, t.is_player as team_is_player
            FROM drivers d
            LEFT JOIN teams t ON d.team_id = t.id
            WHERE d.id = ?;
            """,
                (driver_id,),
            )
            row = cur.fetchone()
            if not row:
                return {}
            driver = dict(row)

            new_pace = min(99, int(driver.get("pace", 75)) + 2)
            new_cons = min(99, int(driver.get("consistency", 75)) + 2)
            new_def = min(99, int(driver.get("defending", 75)) + 2)
            new_mkt = min(99, int(driver.get("marketability", 75)) + 12)
            titles = int(driver.get("champion_titles", 0)) + 1

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
                (titles, new_pace, new_cons, new_def, new_mkt, driver_id),
            )

            royalty_awarded = 0.0
            if driver.get("team_is_player") or driver.get("is_player_driver"):
                royalty_awarded = 2500000.0
                cur.execute(
                    "UPDATE teams SET cash = cash + ?, reputation = MIN(100, reputation + 8) WHERE id = ?;",
                    (royalty_awarded, driver["team_id"]),
                )
                cur.execute(
                    """
                INSERT INTO ledger (team_id, week, category, description, amount)
                VALUES (?, 18, 'SPONSOR', ?, ?);
                """,
                    (
                        driver["team_id"],
                        f"Driver Championship Merchandising Royalty ({driver['name']})",
                        royalty_awarded,
                    ),
                )

            conn.commit()

            driver["new_pace"] = new_pace
            driver["new_consistency"] = new_cons
            driver["new_defending"] = new_def
            driver["new_marketability"] = new_mkt
            driver["champion_titles"] = titles
            driver["royalty_awarded"] = royalty_awarded
            return driver

    def get_player_team(self) -> Dict[str, Any]:
        """Returns the player's managed team."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM teams WHERE is_player = 1 LIMIT 1;")
            row = cur.fetchone()
            return dict(row) if row else {}

    def get_teams(self, tier: Optional[int] = None) -> List[Dict[str, Any]]:
        """Returns teams, optionally filtered by league tier."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            if tier:
                cur.execute("SELECT * FROM teams WHERE tier = ? ORDER BY points DESC, reputation DESC;", (tier,))
            else:
                cur.execute("SELECT * FROM teams ORDER BY tier ASC, points DESC;")
            return [dict(r) for r in cur.fetchall()]

    def get_current_season_num(self) -> int:
        """Returns current season number based on active/completed seasons in season_history."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COALESCE(MAX(season_num), 0) + 1 FROM season_history WHERE season_num >= 1;")
            row = cur.fetchone()
            val = int(row[0]) if row and row[0] is not None else 1
            return max(1, val)

    def get_season_regulations(self, tier: int, season_num: Optional[int] = None) -> Dict[str, Any]:
        """Returns regulations record for the tier and season."""
        if season_num is None:
            season_num = self.get_current_season_num()
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM season_regulations WHERE season_num = ? AND tier = ?;", (season_num, tier))
            row = cur.fetchone()
            if row:
                return dict(row)
            # Fetch previous season's consecutive stable seasons if any
            cur.execute(
                "SELECT consecutive_stable_seasons FROM season_regulations WHERE season_num = ? AND tier = ?;",
                (season_num - 1, tier),
            )
            prev = cur.fetchone()
            prev_stable = prev[0] if prev else 0
            cur.execute(
                """
            INSERT OR IGNORE INTO season_regulations (season_num, tier, consecutive_stable_seasons, is_announced, announcement_week, current_package, upcoming_package, port_back_used, announcement_text)
            VALUES (?, ?, ?, 0, 9, 'STATUS_QUO', 'STATUS_QUO', 0, '');
            """,
                (season_num, tier, prev_stable),
            )
            conn.commit()
            cur.execute("SELECT * FROM season_regulations WHERE season_num = ? AND tier = ?;", (season_num, tier))
            row = cur.fetchone()
            return dict(row) if row else {}

    def set_season_regulations(
        self, season_num: int, tier: int, upcoming_package: str, is_announced: bool = True, announcement_text: str = ""
    ):
        """Updates the announced regulations for next season."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            UPDATE season_regulations
            SET upcoming_package = ?, is_announced = ?, announcement_text = ?
            WHERE season_num = ? AND tier = ?;
            """,
                (upcoming_package, 1 if is_announced else 0, announcement_text, season_num, tier),
            )
            conn.commit()

    def get_team_drivers(self, team_id: int) -> List[Dict[str, Any]]:
        """Returns all primary and academy drivers for a team."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM drivers WHERE team_id = ? ORDER BY is_academy_driver ASC, id ASC;", (team_id,))
            return [dict(r) for r in cur.fetchall()]

    def get_career_summary(self) -> Optional[Dict[str, Any]]:
        """Returns structured metadata summary of the active saved career."""
        p_team = self.get_player_team()
        if not p_team:
            return None
        with self.get_connection() as conn:
            cur = conn.cursor()
            p_tier = p_team.get("tier", 3)
            cur.execute("SELECT COUNT(*) FROM calendar WHERE tier = ? AND is_completed = 1;", (p_tier,))
            completed_races = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM calendar WHERE tier = ?;", (p_tier,))
            total_races = cur.fetchone()[0]

            cur.execute(
                "SELECT name, number FROM drivers WHERE team_id = ? AND is_academy_driver = 0 LIMIT 2;", (p_team["id"],)
            )
            drivers = [f"#{r[1]} {r[0]}" for r in cur.fetchall()]

            return {
                "team_id": p_team["id"],
                "team_name": p_team.get("name", "Player Team"),
                "principal_name": p_team.get("principal_name", "Team Principal"),
                "tier": p_team.get("tier", 3),
                "cash": p_team.get("cash", 0.0),
                "points": p_team.get("points", 0),
                "color_hex": p_team.get("color_hex", "#00d2be"),
                "engine_supplier": p_team.get("engine_supplier", "Vortex EcoTech"),
                "difficulty": p_team.get("difficulty", "NORMAL"),
                "completed_races": completed_races,
                "total_races": total_races,
                "drivers": drivers,
            }

    def update_team_info(self, team_id: int, name: str, color_hex: str) -> bool:
        """Updates team name and livery color in career mode."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE teams SET name = ?, color_hex = ? WHERE id = ?;", (name, color_hex, team_id))
            conn.commit()
            return cur.rowcount > 0

    def update_driver_stats(self, driver_id: int, name: str, number: int, stats: Dict[str, Any]) -> bool:
        """Updates career driver bio and 8 on-track skill attributes."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            UPDATE drivers
            SET name = ?, number = ?,
                pace = ?, braking = ?, consistency = ?, tire_management = ?,
                defending = ?, fuel_efficiency = ?, wet_weather = ?
            WHERE id = ?;
            """,
                (
                    name,
                    number,
                    int(stats.get("pace", 75)),
                    int(stats.get("braking", 75)),
                    int(stats.get("consistency", 75)),
                    int(stats.get("tire_management", 75)),
                    int(stats.get("defending", 75)),
                    int(stats.get("fuel_efficiency", 75)),
                    int(stats.get("wet_weather", 75)),
                    driver_id,
                ),
            )
            conn.commit()
            return cur.rowcount > 0

    def get_team_facilities(self, team_id: int) -> List[Dict[str, Any]]:
        """Returns all unlocked and available facility nodes for a team with joined definitions."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            SELECT fn.*, 
                   COALESCE(tf.current_tier, 0) as current_tier, 
                   COALESCE(tf.is_unlocked, 0) as is_unlocked, 
                   COALESCE(tf.monthly_sub_budget, 0.0) as monthly_sub_budget,
                   COALESCE(tf.savings_balance, 0.0) as savings_balance
            FROM facility_nodes fn
            LEFT JOIN team_facilities tf ON fn.id = tf.node_id AND tf.team_id = ?
            ORDER BY fn.department ASC, fn.tier ASC;
            """,
                (team_id,),
            )
            return [dict(r) for r in cur.fetchall()]

    def get_team_components(self, team_id: int) -> List[Dict[str, Any]]:
        """Returns all active car components for a team."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM car_components WHERE team_id = ? ORDER BY car_slot ASC, category ASC;", (team_id,)
            )
            return [dict(r) for r in cur.fetchall()]

    def get_team_warehouse_components(self, team_id: int, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns all unmounted spare components in the warehouse (car_slot = 0)."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            if category:
                cur.execute(
                    "SELECT * FROM car_components WHERE team_id = ? AND car_slot = 0 AND category = ? ORDER BY generation DESC, performance DESC;",
                    (team_id, category),
                )
            else:
                cur.execute(
                    "SELECT * FROM car_components WHERE team_id = ? AND car_slot = 0 ORDER BY category ASC, generation DESC;",
                    (team_id,),
                )
            return [dict(r) for r in cur.fetchall()]

    def buy_factory_component(
        self, team_id: int, category: str, cost: float, performance: float, durability: float, target_car_slot: int = 0
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Purchases a factory specification component, charging team budget, and mounts or places in warehouse."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT cash, tier FROM teams WHERE id = ?;", (team_id,))
            team = cur.fetchone()
            if not team:
                return False, "Team not found.", None
            if team["cash"] < cost:
                return False, f"Insufficient funds (${team['cash']:,.0f} available, ${cost:,.0f} required).", None

            new_cash = team["cash"] - cost
            cur.execute("UPDATE teams SET cash = ? WHERE id = ?;", (new_cash, team_id))

            # If mounting directly to Car 1 or 2, demote existing part to warehouse (slot 0)
            if target_car_slot in (1, 2):
                cur.execute(
                    "UPDATE car_components SET car_slot = 0 WHERE team_id = ? AND car_slot = ? AND category = ?;",
                    (team_id, target_car_slot, category),
                )

            cur.execute(
                """
            INSERT INTO car_components (team_id, car_slot, category, generation, performance, reliability, wear_pct, knowledge_min, knowledge_max, races_on_concept, max_durability, current_durability)
            VALUES (?, ?, ?, 1, ?, ?, 0.0, 0.0, 0.0, 0, ?, ?);
            """,
                (team_id, target_car_slot, category, performance, durability, durability, durability),
            )
            new_id = cur.lastrowid
            conn.commit()

            cur.execute("SELECT * FROM car_components WHERE id = ?;", (new_id,))
            row = dict(cur.fetchone())
            dest = f"Car #{target_car_slot}" if target_car_slot in (1, 2) else "Warehouse Stock"
            return (
                True,
                f"Factory {category} purchased for ${cost:,.0f} and placed into {dest} ({durability:.0f}% Durability).",
                row,
            )

    def mount_component(self, team_id: int, component_id: int, target_car_slot: int) -> Tuple[bool, str]:
        """Mounts a component from the warehouse to Car 1 or 2, sending previously mounted component to warehouse."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM car_components WHERE id = ? AND team_id = ?;", (component_id, team_id))
            comp = cur.fetchone()
            if not comp:
                return False, "Component not found."
            category = comp["category"]

            # Move current mounted part to warehouse
            cur.execute(
                "UPDATE car_components SET car_slot = 0 WHERE team_id = ? AND car_slot = ? AND category = ?;",
                (team_id, target_car_slot, category),
            )
            # Mount selected part
            cur.execute("UPDATE car_components SET car_slot = ? WHERE id = ?;", (target_car_slot, component_id))
            conn.commit()
            return True, f"{category} (Mk {comp['generation']}) successfully mounted on Car #{target_car_slot}."

    def consume_spare_component(self, team_id: int, category: str) -> Optional[Dict[str, Any]]:
        """Finds and consumes the best spare part in the warehouse (used for in-race front wing replacement)."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM car_components WHERE team_id = ? AND car_slot = 0 AND category = ? ORDER BY current_durability DESC, generation DESC LIMIT 1;",
                (team_id, category),
            )
            row = cur.fetchone()
            if not row:
                return None
            comp = dict(row)
            cur.execute("DELETE FROM car_components WHERE id = ?;", (comp["id"],))
            conn.commit()
            return comp

    def save_car_part_durabilities(self, team_id: int, car_slot: int, durabilities: Dict[str, float]):
        """Persists end-of-race part durabilities into car_components."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            for cat, dur in durabilities.items():
                dur_clamped = max(0.0, float(dur))
                wear = max(0.0, min(100.0, 100.0 - dur_clamped))
                cur.execute(
                    """
                UPDATE car_components 
                SET current_durability = ?, wear_pct = ?
                WHERE team_id = ? AND car_slot = ? AND category = ?;
                """,
                    (dur_clamped, wear, team_id, car_slot, cat),
                )
            conn.commit()

    def get_team_staff_count(self, team_id: int) -> int:
        """Returns total workforce count for a team."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM staff WHERE team_id = ?;", (team_id,))
            return int(cur.fetchone()[0])

    def get_facility_equipment(self, team_id: int, node_id: str, upkeep_mult: float = 1.0) -> List[Dict[str, Any]]:
        """Returns all specialized equipment for a facility node with unlock status and active level."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            SELECT fe.*, 
                   COALESCE(te.current_level, 0) as current_level,
                   COALESCE(te.is_active, 1) as is_active,
                   tf.current_tier as parent_facility_tier,
                   tf.is_unlocked as parent_is_unlocked
            FROM facility_equipment fe
            LEFT JOIN team_facilities tf ON fe.node_id = tf.node_id AND tf.team_id = ?
            LEFT JOIN team_equipment te ON fe.id = te.equipment_id AND te.team_id = ?
            WHERE fe.node_id = ?
            ORDER BY fe.unlocked_at_facility_tier ASC, fe.id ASC;
            """,
                (team_id, team_id, node_id),
            )
            items = []
            for r in cur.fetchall():
                d = dict(r)
                fac_tier = d["parent_facility_tier"] or 0
                is_unlocked = bool(d["parent_is_unlocked"])
                # Tier locking check: e.g. Tier 1 unlocks up to equipment unlocked_at <= 1
                d["is_tier_locked"] = not is_unlocked or (d["unlocked_at_facility_tier"] > fac_tier)
                d["current_upkeep"] = (
                    (d["base_upkeep"] * d["current_level"] * upkeep_mult)
                    if (d["is_active"] and d["current_level"] > 0)
                    else 0.0
                )
                next_lvl = d["current_level"] + 1
                d["next_upgrade_cost"] = d["base_cost"] * (1.2 ** (next_lvl - 1)) if next_lvl <= d["max_level"] else 0.0
                items.append(d)
            return items

    def set_equipment_active(self, team_id: int, equipment_id: str, is_active: bool):
        """Toggles active/shutdown state of a facility equipment piece."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            INSERT INTO team_equipment (team_id, equipment_id, current_level, is_active)
            VALUES (?, ?, 1, ?)
            ON CONFLICT(team_id, equipment_id) DO UPDATE SET is_active = ?;
            """,
                (team_id, equipment_id, 1 if is_active else 0, 1 if is_active else 0),
            )
            conn.commit()

    def upgrade_equipment(self, team_id: int, equipment_id: str, cost_mult: float = 1.0) -> Tuple[bool, str]:
        """Manually upgrades an equipment piece to the next level."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            SELECT fe.*, 
                   COALESCE(te.current_level, 0) as current_level,
                   tf.current_tier as parent_facility_tier,
                   tf.is_unlocked as parent_is_unlocked
            FROM facility_equipment fe
            LEFT JOIN team_facilities tf ON fe.node_id = tf.node_id AND tf.team_id = ?
            LEFT JOIN team_equipment te ON fe.id = te.equipment_id AND te.team_id = ?
            WHERE fe.id = ?;
            """,
                (team_id, team_id, equipment_id),
            )
            row = cur.fetchone()
            if not row:
                return False, "Equipment not found."

            if not row["parent_is_unlocked"]:
                return False, "Parent facility is not constructed yet."

            fac_tier = row["parent_facility_tier"] or 0
            if row["unlocked_at_facility_tier"] > fac_tier:
                return False, f"Requires {row['node_id']} Facility Tier {row['unlocked_at_facility_tier']}."

            cur_lvl = row["current_level"]
            if cur_lvl >= row["max_level"]:
                return False, "Equipment is already at maximum level."

            next_lvl = cur_lvl + 1
            cost = (row["base_cost"] * (1.2 ** (next_lvl - 1))) * cost_mult

            cur.execute("SELECT cash FROM teams WHERE id = ?;", (team_id,))
            cash = float(cur.fetchone()[0])
            if cash < cost:
                return False, f"Insufficient funds. Need ${cost:,.0f}."

            cur.execute("UPDATE teams SET cash = cash - ? WHERE id = ?;", (cost, team_id))
            cur.execute(
                """
            INSERT INTO team_equipment (team_id, equipment_id, current_level, is_active)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(team_id, equipment_id) DO UPDATE SET current_level = ?, is_active = 1;
            """,
                (team_id, equipment_id, next_lvl, next_lvl),
            )

            cur.execute(
                """
            INSERT INTO ledger (team_id, week, category, description, amount)
            VALUES (?, 1, 'RND_BUILD', ?, ?);
            """,
                (team_id, f"Upgraded Equipment: {row['name']} to Level {next_lvl}", -cost),
            )

            conn.commit()
            return True, f"Upgraded {row['name']} to Level {next_lvl}!"

    def get_department_financial_status(
        self, team_id: int, node_id: str, upkeep_mult: float = 1.0, conn: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Calculates monthly budget vs minimum operational costs (facility upkeep + active equipment upkeep + staff salaries) for a node, scaled by difficulty upkeep multiplier."""

        def _compute(active_conn):
            cur = active_conn.cursor()
            cur.execute(
                """
            SELECT tf.monthly_sub_budget, tf.savings_balance, tf.current_tier, tf.is_unlocked, fn.base_upkeep
            FROM facility_nodes fn
            LEFT JOIN team_facilities tf ON fn.id = tf.node_id AND tf.team_id = ?
            WHERE fn.id = ?;
            """,
                (team_id, node_id),
            )
            tf = cur.fetchone()
            monthly_budget = float(tf["monthly_sub_budget"]) if tf and tf["monthly_sub_budget"] is not None else 0.0
            savings_bal = float(tf["savings_balance"]) if tf and tf["savings_balance"] is not None else 0.0
            cur_tier = int(tf["current_tier"]) if tf and tf["current_tier"] is not None else 0
            is_unlocked = bool(tf["is_unlocked"]) if tf and tf["is_unlocked"] is not None else False
            base_upkeep = float(tf["base_upkeep"]) if tf and tf["base_upkeep"] is not None else 0.0

            # 1. Facility Tier Base Maintenance Upkeep
            fac_upkeep = (base_upkeep * cur_tier * upkeep_mult) if (is_unlocked and cur_tier > 0) else 0.0

            # 2. Sum active equipment upkeep scaled by difficulty upkeep multiplier
            cur.execute(
                """
            SELECT SUM(fe.base_upkeep * te.current_level)
            FROM facility_equipment fe
            JOIN team_equipment te ON fe.id = te.equipment_id
            WHERE te.team_id = ? AND fe.node_id = ? AND te.is_active = 1;
            """,
                (team_id, node_id),
            )
            res = cur.fetchone()[0]
            eq_upkeep = (float(res) if res else 0.0) * upkeep_mult

            # 3. Sum personnel salaries assigned to this facility
            cur.execute(
                """
            SELECT COUNT(*), SUM(salary_monthly)
            FROM personnel
            WHERE team_id = ? AND facility_node_id = ?;
            """,
                (team_id, node_id),
            )
            s_row = cur.fetchone()
            staff_count = int(s_row[0]) if s_row and s_row[0] else 0
            staff_salaries = float(s_row[1]) if s_row and s_row[1] else 0.0

            min_operational_cost = fac_upkeep + eq_upkeep + staff_salaries
            total_demand = min_operational_cost

            # Effective budget is bounded to at least minimum operational costs
            effective_budget = max(min_operational_cost, monthly_budget)
            surplus_deficit = effective_budget - min_operational_cost

            return {
                "monthly_budget": effective_budget,
                "facility_upkeep": fac_upkeep,
                "equipment_upkeep": eq_upkeep,
                "staff_salaries": staff_salaries,
                "min_operational_cost": min_operational_cost,
                "total_demand": total_demand,
                "surplus_or_deficit": surplus_deficit,
                "is_deficit": False,
                "staff_count": staff_count,
                "savings_balance": savings_bal,
            }

        if conn is not None:
            return _compute(conn)
        else:
            with self.get_connection() as c:
                return _compute(c)

    def get_facility_savings(self, team_id: int, node_id: str) -> float:
        """Returns the accumulated department savings account balance."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT savings_balance FROM team_facilities WHERE team_id = ? AND node_id = ?;", (team_id, node_id)
            )
            row = cur.fetchone()
            return float(row[0]) if row and row[0] is not None else 0.0

    def deposit_facility_savings(self, team_id: int, node_id: str, amount: float):
        """Deposits unspent monthly budget surplus into department savings."""
        if amount <= 0:
            return
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE team_facilities SET savings_balance = savings_balance + ? WHERE team_id = ? AND node_id = ?;",
                (amount, team_id, node_id),
            )
            conn.commit()

    def sweep_facility_savings_to_treasury(
        self, team_id: int, node_id: str, amount: Optional[float] = None
    ) -> Tuple[bool, str, float]:
        """Transfers accumulated department savings back into central team bank treasury."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT savings_balance FROM team_facilities WHERE team_id = ? AND node_id = ?;", (team_id, node_id)
            )
            row = cur.fetchone()
            cur_bal = float(row[0]) if row and row[0] is not None else 0.0
            if cur_bal <= 0:
                return False, "Department savings account has no funds to transfer.", 0.0
            sweep_amt = cur_bal if amount is None else min(cur_bal, float(amount))
            cur.execute(
                "UPDATE team_facilities SET savings_balance = savings_balance - ? WHERE team_id = ? AND node_id = ?;",
                (sweep_amt, team_id, node_id),
            )
            cur.execute("UPDATE teams SET cash = cash + ? WHERE id = ?;", (sweep_amt, team_id))
            cur.execute(
                """
            INSERT INTO ledger (team_id, week, category, description, amount)
            VALUES (?, 1, 'FACILITY_SWEEP', ?, ?);
            """,
                (team_id, f"Swept ${sweep_amt:,.0f} from {node_id} Savings to Team Treasury", sweep_amt),
            )
            conn.commit()
            return True, f"Swept ${sweep_amt:,.0f} into main team bank treasury!", sweep_amt

    def get_hr_policies(self, team_id: int) -> Dict[str, Any]:
        """Returns all HR workforce automation toggle states and thresholds."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM team_hr_policies WHERE team_id = ?;", (team_id,))
            row = cur.fetchone()
            if row:
                return dict(row)
            # Default policies if not yet initialized
            cur.execute("INSERT OR REPLACE INTO team_hr_policies (team_id) VALUES (?);", (team_id,))
            conn.commit()
            cur.execute("SELECT * FROM team_hr_policies WHERE team_id = ?;", (team_id,))
            return dict(cur.fetchone())

    def update_hr_policy(self, team_id: int, policy_key: str, value: Any):
        """Updates a specific HR workforce automation policy toggle or threshold."""
        allowed_keys = [
            "auto_fill_desks",
            "auto_intern_pipeline",
            "auto_headhunt",
            "auto_payroll",
            "auto_cull",
            "auto_replace",
            "auto_equip_procure",
            "min_intern_potential",
            "max_cull_underperform_deficit",
        ]
        if policy_key not in allowed_keys:
            return
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(f"UPDATE team_hr_policies SET {policy_key} = ? WHERE team_id = ?;", (value, team_id))
            if cur.rowcount == 0:
                cur.execute("INSERT OR REPLACE INTO team_hr_policies (team_id) VALUES (?);", (team_id,))
                cur.execute(f"UPDATE team_hr_policies SET {policy_key} = ? WHERE team_id = ?;", (value, team_id))
            conn.commit()

    def process_monthly_department_savings(self, team_id: int, upkeep_mult: float = 1.0):
        """Computes unspent monthly surplus for each unlocked facility and deposits it into the department savings account."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT node_id FROM team_facilities WHERE team_id = ? AND is_unlocked = 1;", (team_id,))
            unlocked = [r[0] for r in cur.fetchall()]
            for n in unlocked:
                fin = self.get_department_financial_status(team_id, n, upkeep_mult)
                surplus = fin["surplus_or_deficit"]
                if surplus > 0:
                    cur.execute(
                        "UPDATE team_facilities SET savings_balance = savings_balance + ? WHERE team_id = ? AND node_id = ?;",
                        (surplus, team_id, n),
                    )
            conn.commit()

    def get_team_total_equipment_upkeep(self, team_id: int, upkeep_mult: float = 1.0) -> float:
        """Returns total active equipment upkeep across all departments for a team scaled by difficulty upkeep multiplier."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            SELECT SUM(fe.base_upkeep * te.current_level)
            FROM facility_equipment fe
            JOIN team_equipment te ON fe.id = te.equipment_id
            WHERE te.team_id = ? AND te.is_active = 1;
            """,
                (team_id,),
            )
            res = cur.fetchone()[0]
            return (float(res) if res else 0.0) * upkeep_mult

    def create_new_career(
        self,
        player_team_name: str,
        color_hex: str,
        difficulty: str = "NORMAL",
        engine_supplier: str = "Vortex EcoTech",
        principal_name: str = "Alex Mercer",
        enable_tutorial: bool = True,
    ):
        """Resets career database and seeds a fresh career with custom player team name, livery color, difficulty, and Season 1 Engine Supplier."""
        tables = [
            "teams",
            "drivers",
            "staff",
            "personnel",
            "team_category_directors",
            "personnel_applications",
            "team_hr_policies",
            "car_components",
            "team_facilities",
            "facility_nodes",
            "facility_equipment",
            "team_equipment",
            "leagues",
            "active_sponsors",
            "sponsor_offers",
            "race_history",
            "season_history",
            "calendar",
            "ledger",
            "innovation_pitches",
            "scout_prospects",
            "series_race_results",
            "driver_season_history",
            "season_regulations",
            "driver_market",
            "feeder_market_seats",
            "team_alumni",
            "balance_settings",
            "tutorial_progress",
        ]

        with self.get_connection() as conn:
            cur = conn.cursor()
            for t in tables:
                cur.execute(f"DROP TABLE IF EXISTS {t};")
            conn.commit()

        # Rebuild fresh schema
        self.init_schema()

        # Apply player custom team name, color, difficulty cash bonus, and engine supplier
        diff_cash_bonuses = {
            "VERY_EASY": 5000000.0,
            "EASY": 2500000.0,
            "NORMAL": 0.0,
            "HARD": -2000000.0,
            "VERY_HARD": -4000000.0,
        }
        cash_bonus = diff_cash_bonuses.get(difficulty, 0.0)

        supplier_costs = {
            "Vortex EcoTech": 250000.0,
            "Titan Velocity": 1200000.0,
            "AeroStar Endurance": 1500000.0,
            "CosmoSpec Customer V6": 600000.0,
            "Apex High-Rev V8": 8500000.0,
            "Vanguard Twin-Turbo": 14000000.0,
            "Formula Standard Customer V6": 1500000.0,
            "Solaris Quantum Hybrid V6": 35000000.0,
            "Scuderia Factory Hyper-V6": 65000000.0,
            "Works In-House V6 Turbo": 0.0,
        }
        contract_cost = supplier_costs.get(engine_supplier, 250000.0)

        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            UPDATE teams 
            SET name = ?, base_name = ?, color_hex = ?, cash = cash + ? - ?,
                engine_supplier = ?, engine_contract_cost = ?, engine_contract_races_left = 10, engine_locked_for_season = 1,
                difficulty = ?, principal_name = ?
            WHERE is_player = 1;
            """,
                (
                    player_team_name,
                    player_team_name,
                    color_hex,
                    cash_bonus,
                    contract_cost,
                    engine_supplier,
                    contract_cost,
                    difficulty,
                    principal_name,
                ),
            )

            cur.execute(
                """
            INSERT INTO ledger (team_id, week, category, description, amount)
            SELECT id, 1, 'ENGINE_SUPPLIER', ?, ? FROM teams WHERE is_player = 1;
            """,
                (f"Signed Engine Contract: {engine_supplier} (Full Season)", -contract_cost),
            )

            # Initialize tutorial state
            cur.execute(
                """
            INSERT OR REPLACE INTO tutorial_progress (
                team_id, current_step_id, is_active, is_completed, is_skipped
            )
            SELECT id, 'WELCOME_DASHBOARD', ?, 0, ? FROM teams WHERE is_player = 1;
            """,
                (1 if enable_tutorial else 0, 0 if enable_tutorial else 1),
            )

            # Provide starting Continuous Evolution Knowledge on FRONT_WING for player cars
            # so the player can immediately experience manufacturing an upgraded Mk II part!
            cur.execute("""
            UPDATE car_components 
            SET knowledge_min = 28.0, knowledge_max = 42.0, rel_knowledge_min = 12.0, rel_knowledge_max = 24.0
            WHERE category = 'FRONT_WING' AND team_id IN (SELECT id FROM teams WHERE is_player = 1);
            """)

            conn.commit()

        # Seed initial sponsor offers (1 secondary, 2 minors / 3 on very easy)
        from ..management.sponsor_manager import SponsorManager

        p_team = self.get_player_team()
        if p_team:
            sm = SponsorManager(self)
            sm.seed_initial_sponsor_offers(p_team["id"])

    # =========================================================================
    # Guided Tutorial Persistence API
    # =========================================================================
    def get_tutorial_progress(self, team_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves tutorial progress record for the specified team."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM tutorial_progress WHERE team_id = ?;", (team_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def save_tutorial_progress(
        self, team_id: int, step_id: str, is_active: bool, is_completed: bool, is_skipped: bool, **kwargs
    ):
        """Updates or inserts tutorial progress with optional feature completion flags."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            INSERT INTO tutorial_progress (team_id, current_step_id, is_active, is_completed, is_skipped)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(team_id) DO UPDATE SET
                current_step_id = excluded.current_step_id,
                is_active = excluded.is_active,
                is_completed = excluded.is_completed,
                is_skipped = excluded.is_skipped;
            """,
                (team_id, step_id, 1 if is_active else 0, 1 if is_completed else 0, 1 if is_skipped else 0),
            )

            for key in [
                "brakes_equipment_bought",
                "personnel_hired",
                "front_wing_built",
                "driver_placed",
                "sponsor_signed",
            ]:
                if key in kwargs:
                    cur.execute(
                        f"UPDATE tutorial_progress SET {key} = ? WHERE team_id = ?;", (1 if kwargs[key] else 0, team_id)
                    )
            conn.commit()

    def reset_tutorial_progress(self, team_id: int):
        """Resets tutorial to the starting step and reactivates it."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            INSERT INTO tutorial_progress (team_id, current_step_id, is_active, is_completed, is_skipped, brakes_equipment_bought, personnel_hired, front_wing_built, driver_placed, sponsor_signed)
            VALUES (?, 'WELCOME_DASHBOARD', 1, 0, 0, 0, 0, 0, 0, 0)
            ON CONFLICT(team_id) DO UPDATE SET
                current_step_id = 'WELCOME_DASHBOARD',
                is_active = 1,
                is_completed = 0,
                is_skipped = 0,
                brakes_equipment_bought = 0,
                personnel_hired = 0,
                front_wing_built = 0,
                driver_placed = 0,
                sponsor_signed = 0;
            """,
                (team_id,),
            )

            # Ensure FRONT_WING has knowledge for the build step
            cur.execute(
                """
            UPDATE car_components 
            SET knowledge_min = 28.0, knowledge_max = 42.0, rel_knowledge_min = 12.0, rel_knowledge_max = 24.0
            WHERE category = 'FRONT_WING' AND team_id = ?;
            """,
                (team_id,),
            )
            conn.commit()

    def add_team_cash(
        self, team_id: int, amount: float, category: str = "BOARD_GRANT", description: str = "Tutorial Bonus"
    ):
        """Directly credits team cash and appends an entry in the ledger."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE teams SET cash = cash + ? WHERE id = ?;", (amount, team_id))
            cur.execute(
                """
            INSERT INTO ledger (team_id, week, category, description, amount)
            VALUES (?, 1, ?, ?, ?);
            """,
                (team_id, category, description, amount),
            )
            conn.commit()

    # =========================================================================
    # Career Modding & Customization API (Calendar & Factory Layout)
    # =========================================================================
    def get_calendar_rounds(self, tier: Optional[int] = None) -> List[Dict[str, Any]]:
        """Returns all championship rounds for the given tier (defaults to player team's tier or 3)."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            eff_tier = tier
            if eff_tier is None:
                cur.execute("SELECT tier FROM teams WHERE is_player = 1 LIMIT 1;")
                r = cur.fetchone()
                eff_tier = r[0] if r else 3
            cur.execute("SELECT * FROM calendar WHERE tier = ? ORDER BY round ASC;", (eff_tier,))
            return [dict(r) for r in cur.fetchall()]

    def get_total_rounds_for_tier(self, tier: int) -> int:
        """Returns total calendar rounds scheduled for the given tier."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM calendar WHERE tier = ?;", (tier,))
            return cur.fetchone()[0] or 0

    def get_calendar_round(self, tier: int, round_num: int) -> Optional[Dict[str, Any]]:
        """Returns metadata for a specific round in a tier."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM calendar WHERE tier = ? AND round = ?;", (tier, round_num))
            r = cur.fetchone()
            return dict(r) if r else None

    def update_calendar_round(
        self,
        round_num: int,
        track_name: str,
        circuit_file: str,
        total_laps: int,
        weather_profile: str,
        tier: Optional[int] = None,
        characteristic: str = "BALANCED",
    ) -> bool:
        """Updates an existing calendar round with custom track or race conditions."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            eff_tier = tier
            if eff_tier is None:
                cur.execute("SELECT tier FROM teams WHERE is_player = 1 LIMIT 1;")
                r = cur.fetchone()
                eff_tier = r[0] if r else 3
            cur.execute(
                """
            UPDATE calendar 
            SET track_name = ?, circuit_file = ?, total_laps = ?, weather_profile = ?, characteristic = ?
            WHERE tier = ? AND round = ?;
            """,
                (track_name, circuit_file, total_laps, weather_profile, characteristic, eff_tier, round_num),
            )
            conn.commit()
            return cur.rowcount > 0

    def add_calendar_round(
        self,
        track_name: str,
        circuit_file: str,
        total_laps: int = 15,
        weather_profile: str = "DYNAMIC",
        tier: Optional[int] = None,
        characteristic: str = "BALANCED",
    ) -> int:
        """Adds a new Grand Prix round to the season calendar for a tier."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            eff_tier = tier
            if eff_tier is None:
                cur.execute("SELECT tier FROM teams WHERE is_player = 1 LIMIT 1;")
                r = cur.fetchone()
                eff_tier = r[0] if r else 3
            cur.execute("SELECT MAX(round) FROM calendar WHERE tier = ?;", (eff_tier,))
            max_rnd = cur.fetchone()[0] or 0
            new_rnd = max_rnd + 1
            cur.execute(
                """
            INSERT INTO calendar (tier, round, track_name, circuit_file, total_laps, weather_profile, is_completed, characteristic)
            VALUES (?, ?, ?, ?, ?, ?, 0, ?);
            """,
                (eff_tier, new_rnd, track_name, circuit_file, total_laps, weather_profile, characteristic),
            )
            conn.commit()
            return new_rnd

    def delete_calendar_round(self, round_num: int, tier: Optional[int] = None) -> bool:
        """Deletes a calendar round and re-sequences subsequent round numbers for a tier."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            eff_tier = tier
            if eff_tier is None:
                cur.execute("SELECT tier FROM teams WHERE is_player = 1 LIMIT 1;")
                r = cur.fetchone()
                eff_tier = r[0] if r else 3
            cur.execute("DELETE FROM calendar WHERE tier = ? AND round = ?;", (eff_tier, round_num))
            cur.execute("SELECT round FROM calendar WHERE tier = ? ORDER BY round ASC;", (eff_tier,))
            rows = cur.fetchall()
            for idx, r in enumerate(rows, 1):
                old_r = r[0]
                if old_r != idx:
                    cur.execute("UPDATE calendar SET round = ? WHERE tier = ? AND round = ?;", (idx, eff_tier, old_r))
            conn.commit()
            return True

    def set_team_facility_tier(self, team_id: int, node_id: str, tier: int, is_unlocked: bool = True) -> bool:
        """Modifies a team's facility node level and unlock state directly (Custom Factory Layout)."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            INSERT INTO team_facilities (team_id, node_id, current_tier, is_unlocked, monthly_sub_budget, savings_balance)
            VALUES (?, ?, ?, ?, 15000.0, 0.0)
            ON CONFLICT(team_id, node_id) DO UPDATE SET 
                current_tier = excluded.current_tier,
                is_unlocked = excluded.is_unlocked;
            """,
                (team_id, node_id, tier, 1 if is_unlocked else 0),
            )
            conn.commit()
            return True

    def get_all_facility_nodes(self) -> List[Dict[str, Any]]:
        """Returns all master facility node definitions in the career database."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM facility_nodes ORDER BY department ASC, tier ASC, name ASC;")
            return [dict(r) for r in cur.fetchall()]

    def create_facility_node(
        self,
        node_id: str,
        department: str,
        name: str,
        description: str,
        parent_id: Optional[str] = None,
        tier: int = 1,
        max_tier: int = 3,
        base_cost: float = 10000000.0,
        base_upkeep: float = 250000.0,
        staff_capacity: int = 6,
        unlock_league_tier: int = 3,
    ) -> bool:
        """Creates a brand new custom facility node in the master tech tree, initializing it for all existing teams."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            INSERT INTO facility_nodes (
                id, department, name, description, parent_id, tier, max_tier,
                base_cost, base_upkeep, staff_capacity, unlock_league_tier
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
                (
                    node_id,
                    department,
                    name,
                    description,
                    parent_id,
                    tier,
                    max_tier,
                    base_cost,
                    base_upkeep,
                    staff_capacity,
                    unlock_league_tier,
                ),
            )

            # Initialize entry in team_facilities for all teams
            cur.execute(
                """
            INSERT OR IGNORE INTO team_facilities (team_id, node_id, current_tier, is_unlocked, monthly_sub_budget, savings_balance)
            SELECT id, ?, 0, 0, 10000.0, 0.0 FROM teams;
            """,
                (node_id,),
            )

            conn.commit()
            return True

    def update_facility_node(
        self,
        node_id: str,
        department: str,
        name: str,
        description: str,
        parent_id: Optional[str] = None,
        base_cost: float = 10000000.0,
        base_upkeep: float = 250000.0,
    ) -> bool:
        """Updates definition parameters of an existing facility node."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            UPDATE facility_nodes
            SET department = ?, name = ?, description = ?, parent_id = ?, base_cost = ?, base_upkeep = ?
            WHERE id = ?;
            """,
                (department, name, description, parent_id, base_cost, base_upkeep, node_id),
            )
            conn.commit()
            return cur.rowcount > 0

    def delete_facility_node(self, node_id: str) -> bool:
        """Removes a custom facility node, re-linking child dependencies and deleting team associations."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            # 1. Clear parent_id for any child nodes pointing to this node
            cur.execute("UPDATE facility_nodes SET parent_id = NULL WHERE parent_id = ?;", (node_id,))
            # 2. Delete from team_facilities
            cur.execute("DELETE FROM team_facilities WHERE node_id = ?;", (node_id,))
            # 3. Delete from facility_equipment and team_equipment if any
            cur.execute(
                "DELETE FROM team_equipment WHERE equipment_id IN (SELECT id FROM facility_equipment WHERE node_id = ?);",
                (node_id,),
            )
            cur.execute("DELETE FROM facility_equipment WHERE node_id = ?;", (node_id,))
            # 4. Nullify personnel facility_node_id references
            cur.execute("UPDATE personnel SET facility_node_id = NULL WHERE facility_node_id = ?;", (node_id,))
            # 5. Delete from facility_nodes
            cur.execute("DELETE FROM facility_nodes WHERE id = ?;", (node_id,))
            conn.commit()
            return True

    def _seed_historical_seasons(self, cur: Optional[sqlite3.Cursor] = None):
        """Seeds 2 prior historical seasons (-1 and 0, corresponding to 2024 and 2025) across all 5 tiers."""
        conn: Optional[sqlite3.Connection] = None
        if cur is None:
            conn = self.get_connection()
            cur = conn.cursor()

        try:
            # Check if already seeded
            cur.execute("SELECT COUNT(*) FROM driver_season_history;")
            if cur.fetchone()[0] > 0:
                if conn is not None:
                    conn.close()
                return

            points_map = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]

            # We seed Season -1 (2024) and Season 0 (2025)
            for s_num in [-1, 0]:
                for tier in range(1, 6):
                    cur.execute(
                        "SELECT id, name, color_hex, is_player FROM teams WHERE tier = ? ORDER BY reputation DESC, id ASC;",
                        (tier,),
                    )
                    teams = [dict(r) for r in cur.fetchall()]
                    if not teams:
                        continue

                    # Deterministic pseudo-random seed per tier and season
                    rnd_state = random.Random(tier * 100 + (s_num + 5) * 17)
                    shuffled_teams = list(teams)
                    shuffled_teams.sort(key=lambda t: (t["id"] * 7) % 23 + rnd_state.randint(0, 15))

                    base_pts_curve = {
                        1: [340, 295, 250, 205, 160, 120, 85, 55, 30, 14],
                        2: [240, 205, 175, 140, 105, 80, 55, 36, 20, 8],
                        3: [145, 120, 98, 78, 58, 42, 28, 18, 10, 4],
                        4: [125, 100, 80, 62, 46, 32, 22, 14, 8, 2],
                        5: [120, 96, 76, 58, 44, 30, 20, 12, 6, 2],
                    }[tier]

                    # Record Team Season History
                    for pos_idx, team in enumerate(shuffled_teams):
                        t_pts = base_pts_curve[pos_idx] if pos_idx < len(base_pts_curve) else 0
                        cur.execute(
                            """
                        INSERT INTO season_history (team_id, season_num, championship_position, points_total, tier)
                        VALUES (?, ?, ?, ?, ?);
                        """,
                            (team["id"], s_num, pos_idx + 1, t_pts, tier),
                        )

                        # Fetch drivers for this team
                        cur.execute(
                            "SELECT id, name, is_player_driver, is_academy_driver FROM drivers WHERE team_id = ? ORDER BY id ASC;",
                            (team["id"],),
                        )
                        team_drivers = [dict(r) for r in cur.fetchall()]
                        if not team_drivers:
                            team_drivers = [
                                {
                                    "id": None,
                                    "name": f"Driver {team['name'][:4]}",
                                    "is_player_driver": 0,
                                    "is_academy_driver": 0,
                                }
                            ]

                        d1_pts = int(round(t_pts * 0.60))
                        d2_pts = max(0, t_pts - d1_pts)
                        tier_rounds = {1: 16, 2: 12, 3: 7, 4: 6, 5: 6}[tier]

                        for d_idx, d in enumerate(team_drivers[:2]):
                            pts = d1_pts if d_idx == 0 else d2_pts
                            wins = (
                                max(0, min(tier_rounds // 2, (pts // 35) + rnd_state.randint(0, 1)))
                                if pos_idx < 3
                                else 0
                            )
                            podiums = (
                                max(wins, min(tier_rounds, (pts // 18) + rnd_state.randint(0, 2))) if pos_idx < 6 else 0
                            )

                            cur.execute(
                                """
                            INSERT INTO driver_season_history (
                                driver_id, driver_name, team_id, team_name, tier, season_num,
                                championship_position, points, race_starts, wins, podiums,
                                is_player_driver, is_academy_driver
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                            """,
                                (
                                    d["id"],
                                    d["name"],
                                    team["id"],
                                    team["name"],
                                    tier,
                                    s_num,
                                    (pos_idx * 2 + d_idx + 1),
                                    pts,
                                    tier_rounds,
                                    wins,
                                    podiums,
                                    d.get("is_player_driver", 0),
                                    d.get("is_academy_driver", 0),
                                ),
                            )

                    # Seed series_race_results for this tier and season
                    cur.execute(
                        "SELECT round, week, track_name FROM calendar WHERE tier = ? ORDER BY round ASC;", (tier,)
                    )
                    cal_rounds = [dict(r) for r in cur.fetchall()]

                    cur.execute(
                        """
                    SELECT d.id, d.name, t.id as team_id, t.name as team_name, d.is_player_driver, d.is_academy_driver
                    FROM drivers d
                    JOIN teams t ON d.team_id = t.id
                    WHERE t.tier = ?
                    ORDER BY t.reputation DESC, d.id ASC;
                    """,
                        (tier,),
                    )
                    tier_driver_pool = [dict(r) for r in cur.fetchall()]

                    for rnd in cal_rounds:
                        r_num = rnd["round"]
                        r_week = rnd.get("week", r_num)
                        r_track = rnd["track_name"]

                        classified = list(tier_driver_pool)
                        classified.sort(key=lambda x: tier_driver_pool.index(x) + rnd_state.uniform(-3.5, 4.5))

                        for finish_pos, drv in enumerate(classified[:10], 1):
                            pts_award = points_map[finish_pos - 1] if finish_pos <= len(points_map) else 0
                            cur.execute(
                                """
                            INSERT INTO series_race_results (
                                tier, round_num, week, track_name, position, driver_name,
                                team_name, team_id, driver_id, is_academy_driver, is_player, points, season_num
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                            """,
                                (
                                    tier,
                                    r_num,
                                    r_week,
                                    r_track,
                                    finish_pos,
                                    drv["name"],
                                    drv["team_name"],
                                    drv["team_id"],
                                    drv["id"],
                                    drv.get("is_academy_driver", 0),
                                    drv.get("is_player_driver", 0),
                                    pts_award,
                                    s_num,
                                ),
                            )

            # Seed an Alumni Driver for player team
            cur.execute("SELECT id, name FROM teams WHERE is_player = 1;")
            player_team_row = cur.fetchone()
            if player_team_row:
                p_id = player_team_row[0]
                cur.execute("SELECT COUNT(*) FROM team_alumni WHERE player_team_id = ?;", (p_id,))
                if cur.fetchone()[0] == 0:
                    cur.execute("""
                    SELECT d.id, d.name, t.id as team_id, t.name as team_name, t.tier
                    FROM drivers d
                    JOIN teams t ON d.team_id = t.id
                    WHERE t.tier = 2 AND t.is_player = 0
                    LIMIT 1;
                    """)
                    alumni_candidate = cur.fetchone()
                    if alumni_candidate:
                        a_did, a_dname, a_tid, a_tname, a_tier = alumni_candidate
                        cur.execute(
                            """
                        INSERT INTO team_alumni (
                            player_team_id, driver_id, driver_name, seasons_active,
                            starts_with_team, wins_with_team, podiums_with_team, points_with_team,
                            departure_reason, departure_season, current_team_id, current_team_name, current_tier
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                            (
                                p_id,
                                a_did,
                                a_dname,
                                "Season 0 (2025)",
                                7,
                                1,
                                3,
                                42,
                                "PROMOTED_TIER2",
                                0,
                                a_tid,
                                a_tname,
                                a_tier,
                            ),
                        )

            if conn is not None:
                conn.commit()
                conn.close()
        except Exception as e:
            print(f"[CareerDatabase] Historical seasons seeding error: {e}")
            if conn is not None:
                conn.close()

    def get_available_seasons(self) -> List[Dict[str, Any]]:
        """Returns all seasons (historical + current) sorted from newest to oldest."""
        curr = self.get_current_season_num()
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT DISTINCT season_num FROM season_history UNION SELECT DISTINCT season_num FROM driver_season_history ORDER BY season_num DESC;"
            )
            nums = [r[0] for r in cur.fetchall()]

        if curr not in nums:
            nums.append(curr)
        nums = sorted(list(set(nums)), reverse=True)

        result = []
        for s in nums:
            year = 2025 + s
            is_cur = s == curr
            lbl = f"SEASON {s} ({year})" + (" [CURRENT]" if is_cur else " [ARCHIVED]")
            result.append({"season_num": s, "year": year, "label": lbl, "is_current": is_cur})
        return result

    def get_historical_constructor_standings(self, season_num: int, tier: int) -> List[Dict[str, Any]]:
        """Returns team championship standings for a given season and tier."""
        curr = self.get_current_season_num()
        if season_num == curr:
            teams = self.get_teams(tier=tier)
            for idx, t in enumerate(teams):
                t["championship_position"] = idx + 1
            return teams

        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            SELECT sh.championship_position, sh.points_total as points, sh.tier, sh.season_num,
                   t.id, t.name, t.color_hex, t.is_player, t.reputation, t.engine_supplier
            FROM season_history sh
            JOIN teams t ON sh.team_id = t.id
            WHERE sh.season_num = ? AND sh.tier = ?
            ORDER BY sh.championship_position ASC;
            """,
                (season_num, tier),
            )
            return [dict(r) for r in cur.fetchall()]

    def get_historical_driver_standings(self, season_num: int, tier: int) -> List[Dict[str, Any]]:
        """Returns driver championship standings for a given season and tier."""
        curr = self.get_current_season_num()
        if season_num == curr:
            drivers = self.get_driver_standings(tier=tier)
            for idx, d in enumerate(drivers):
                d["championship_position"] = idx + 1
            return drivers

        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            SELECT dsh.*, t.color_hex as team_color_hex
            FROM driver_season_history dsh
            LEFT JOIN teams t ON dsh.team_id = t.id
            WHERE dsh.season_num = ? AND dsh.tier = ?
            ORDER BY dsh.championship_position ASC;
            """,
                (season_num, tier),
            )
            return [dict(r) for r in cur.fetchall()]

    def get_historical_season_races(self, season_num: int, tier: int) -> List[Dict[str, Any]]:
        """Returns list of races and winners for a specific season and tier."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            SELECT round_num, week, track_name, 
                   MAX(CASE WHEN position = 1 THEN driver_name ELSE NULL END) as winner_driver,
                   MAX(CASE WHEN position = 1 THEN team_name ELSE NULL END) as winner_team,
                   COUNT(*) as finisher_count
            FROM series_race_results
            WHERE season_num = ? AND tier = ?
            GROUP BY round_num, week, track_name
            ORDER BY round_num ASC;
            """,
                (season_num, tier),
            )
            rows = [dict(r) for r in cur.fetchall()]
            if not rows and season_num == self.get_current_season_num():
                cur.execute(
                    "SELECT round as round_num, week, track_name, characteristic, is_completed FROM calendar WHERE tier = ? ORDER BY round ASC;",
                    (tier,),
                )
                cal = [dict(r) for r in cur.fetchall()]
                for c in cal:
                    if c["is_completed"]:
                        cur.execute(
                            "SELECT driver_name, team_name FROM series_race_results WHERE tier = ? AND round_num = ? AND season_num = ? AND position = 1;",
                            (tier, c["round_num"], season_num),
                        )
                        w = cur.fetchone()
                        c["winner_driver"] = w[0] if w else "N/A"
                        c["winner_team"] = w[1] if w else ""
                    else:
                        c["winner_driver"] = None
                        c["winner_team"] = None
                return cal
            return rows

    def get_race_classification(self, season_num: int, tier: int, round_num: int) -> List[Dict[str, Any]]:
        """Returns full finishing classification for a specific race round and season."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            SELECT * FROM series_race_results
            WHERE season_num = ? AND tier = ? AND round_num = ?
            ORDER BY position ASC;
            """,
                (season_num, tier, round_num),
            )
            return [dict(r) for r in cur.fetchall()]

    def get_all_drivers_directory(
        self,
        tier: Optional[int] = None,
        only_alumni: bool = False,
        player_team_id: Optional[int] = None,
        search_query: str = "",
    ) -> List[Dict[str, Any]]:
        """Returns directory of drivers with team details and alumni badges for browsing."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            query = """
            SELECT d.id, d.name, d.age, d.number, d.pace, d.consistency, d.potential,
                   d.morale, d.points, d.is_player_driver, d.is_academy_driver,
                   d.team_id, t.name as team_name, t.tier as team_tier, t.color_hex as team_color,
                   a.id as alumni_id, a.departure_reason, a.seasons_active
            FROM drivers d
            LEFT JOIN teams t ON d.team_id = t.id
            LEFT JOIN team_alumni a ON (d.id = a.driver_id AND a.player_team_id = ?)
            WHERE 1=1
            """
            params: List[Any] = [player_team_id or 0]

            if tier is not None:
                query += " AND t.tier = ? "
                params.append(tier)

            if only_alumni:
                query += " AND a.id IS NOT NULL "

            if search_query:
                query += " AND (d.name LIKE ? OR t.name LIKE ?) "
                sq = f"%{search_query}%"
                params.extend([sq, sq])

            query += " ORDER BY t.tier ASC NULLS LAST, d.points DESC, d.pace DESC;"
            cur.execute(query, params)
            return [dict(r) for r in cur.fetchall()]

    def get_driver_profile(self, driver_id: Any, driver_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Returns comprehensive driver dossier including bio, stats, alumni status, season history, and AI analysis."""
        with self.get_connection() as conn:
            cur = conn.cursor()

            # Normalize driver_id and driver_type if prefixed
            if isinstance(driver_id, str):
                if driver_id.startswith("market_"):
                    driver_type = "MARKET"
                    driver_id = int(driver_id.split("_")[1])
                elif driver_id.startswith("scout_"):
                    driver_type = "SCOUT"
                    driver_id = int(driver_id.split("_")[1])
                elif driver_id.isdigit():
                    driver_id = int(driver_id)

            row = None
            m_row = None
            sp_row = None
            h_row = None

            if driver_type == "MARKET":
                cur.execute(
                    """
                SELECT dm.*, t.id as team_id, t.name as team_name, t.color_hex as team_color, t.tier as team_tier, 0 as team_is_player
                FROM driver_market dm
                LEFT JOIN teams t ON dm.parent_team_name = t.name
                WHERE dm.id = ?;
                """,
                    (driver_id,),
                )
                m_row = cur.fetchone()
            elif driver_type == "SCOUT":
                cur.execute(
                    """
                SELECT sp.*, 'Youth Prospect' as team_name, '#888888' as team_color, sp.preferred_tier as team_tier, 0 as team_is_player
                FROM scout_prospects sp
                WHERE sp.id = ?;
                """,
                    (driver_id,),
                )
                sp_row = cur.fetchone()
            else:
                cur.execute(
                    """
                SELECT d.*, t.name as team_name, t.color_hex as team_color, t.tier as team_tier, t.is_player as team_is_player
                FROM drivers d
                LEFT JOIN teams t ON d.team_id = t.id
                WHERE d.id = ?;
                """,
                    (driver_id,),
                )
                row = cur.fetchone()
                if not row:
                    # 1. Try driver_market
                    cur.execute(
                        """
                    SELECT dm.*, t.id as team_id, t.name as team_name, t.color_hex as team_color, t.tier as team_tier, 0 as team_is_player
                    FROM driver_market dm
                    LEFT JOIN teams t ON dm.parent_team_name = t.name
                    WHERE dm.id = ?;
                    """,
                        (driver_id,),
                    )
                    m_row = cur.fetchone()

                    # 2. Try scout_prospects
                    if not m_row:
                        cur.execute(
                            """
                        SELECT sp.*, 'Youth Prospect' as team_name, '#888888' as team_color, sp.preferred_tier as team_tier, 0 as team_is_player
                        FROM scout_prospects sp
                        WHERE sp.id = ?;
                        """,
                            (driver_id,),
                        )
                        sp_row = cur.fetchone()

                    # 3. Try driver_season_history
                    if not m_row and not sp_row:
                        cur.execute(
                            "SELECT * FROM driver_season_history WHERE driver_id = ? ORDER BY season_num DESC LIMIT 1;",
                            (driver_id,),
                        )
                        h_row = cur.fetchone()

            if row:
                d_dict = dict(row)
                if not d_dict.get("team_name"):
                    d_dict["team_name"] = "Free Agent"
                    d_dict["team_color"] = "#888888"
                    d_dict["team_tier"] = None
            elif m_row:
                d_dict = dict(m_row)
                d_dict["morale"] = d_dict.get("morale", 80.0)
                if not d_dict.get("team_name"):
                    d_dict["team_name"] = "Free Agent"
                    d_dict["team_tier"] = d_dict.get("tier", 3)
                    d_dict["team_color"] = "#00d2be"
                d_dict["number"] = d_dict.get("number", 99)
            elif sp_row:
                d_dict = dict(sp_row)
                d_dict["morale"] = 85.0
                d_dict["team_name"] = "Youth Academy Prospect"
                d_dict["team_tier"] = d_dict.get("preferred_tier", 4)
                d_dict["team_color"] = "#22c55e"
                d_dict["number"] = 0
            elif h_row:
                d_dict = dict(h_row)
                d_dict["name"] = d_dict["driver_name"]
                d_dict["age"] = 26
                d_dict["number"] = 44
                d_dict["morale"] = 80.0
                d_dict["pace"] = 75
                d_dict["consistency"] = 75
                d_dict["braking"] = 75
                d_dict["defending"] = 75
                d_dict["tire_management"] = 75
                d_dict["wet_weather"] = 75
                d_dict["marketability"] = 70
                d_dict["team_name"] = d_dict.get("team_name", "Free Agent")
                d_dict["team_tier"] = d_dict.get("tier", 3)
                d_dict["team_color"] = "#00d2be"
            else:
                return None

            # For MARKET or SCOUT pool prospects, driver_id is from a separate table
            if driver_type == "SCOUT":
                seasons = []
            elif driver_type == "MARKET":
                cur.execute(
                    """
                SELECT * FROM driver_season_history
                WHERE driver_name = ?
                ORDER BY season_num DESC;
                """,
                    (d_dict["name"],),
                )
                seasons = [dict(r) for r in cur.fetchall()]
            else:
                cur.execute(
                    """
                SELECT * FROM driver_season_history
                WHERE driver_id = ? OR driver_name = ?
                ORDER BY season_num DESC;
                """,
                    (driver_id, d_dict["name"]),
                )
                seasons = [dict(r) for r in cur.fetchall()]
            d_dict["season_history"] = seasons

            total_starts = sum(s.get("race_starts", 0) for s in seasons)
            total_wins = sum(s.get("wins", 0) for s in seasons)
            total_podiums = sum(s.get("podiums", 0) for s in seasons)
            total_points = sum(s.get("points", 0) for s in seasons) + int(d_dict.get("points", 0))

            if driver_type == "SCOUT":
                pass
            elif driver_type == "MARKET":
                cur.execute(
                    """
                SELECT COUNT(*), 
                       SUM(CASE WHEN position = 1 THEN 1 ELSE 0 END),
                       SUM(CASE WHEN position <= 3 THEN 1 ELSE 0 END)
                FROM series_race_results 
                WHERE driver_name = ? AND season_num = ?;
                """,
                    (d_dict["name"], self.get_current_season_num()),
                )
                cur_r = cur.fetchone()
                if cur_r and cur_r[0]:
                    total_starts += cur_r[0]
                    total_wins += cur_r[1] or 0
                    total_podiums += cur_r[2] or 0
            else:
                cur.execute(
                    """
                SELECT COUNT(*), 
                       SUM(CASE WHEN position = 1 THEN 1 ELSE 0 END),
                       SUM(CASE WHEN position <= 3 THEN 1 ELSE 0 END)
                FROM series_race_results 
                WHERE (driver_id = ? OR driver_name = ?) AND season_num = ?;
                """,
                    (driver_id, d_dict["name"], self.get_current_season_num()),
                )
                cur_r = cur.fetchone()
                if cur_r and cur_r[0]:
                    total_starts += cur_r[0]
                    total_wins += cur_r[1] or 0
                    total_podiums += cur_r[2] or 0

            if driver_type == "SCOUT":
                best_fin = "N/A"
            elif driver_type == "MARKET":
                cur.execute("SELECT MIN(position) FROM series_race_results WHERE driver_name = ?;", (d_dict["name"],))
                bf_row = cur.fetchone()
                if bf_row and bf_row[0] is not None:
                    best_fin = f"P{bf_row[0]}"
                elif total_wins > 0:
                    best_fin = "P1"
                elif total_podiums > 0:
                    best_fin = "P2"
                elif total_starts > 0:
                    best_fin = "P5"
                else:
                    best_fin = "N/A"
            else:
                cur.execute(
                    "SELECT MIN(position) FROM series_race_results WHERE driver_id = ? OR driver_name = ?;",
                    (driver_id, d_dict["name"]),
                )
                bf_row = cur.fetchone()
                if bf_row and bf_row[0] is not None:
                    best_fin = f"P{bf_row[0]}"
                elif total_wins > 0:
                    best_fin = "P1"
                elif total_podiums > 0:
                    best_fin = "P2"
                elif total_starts > 0:
                    best_fin = "P5"
                else:
                    best_fin = "N/A"

            d_dict["career_totals"] = {
                "starts": total_starts,
                "wins": total_wins,
                "podiums": total_podiums,
                "points": total_points,
                "titles": int(d_dict.get("champion_titles", 0)),
                "best_finish": best_fin,
            }

            if driver_type in ("MARKET", "SCOUT"):
                cur.execute("SELECT * FROM team_alumni WHERE driver_name = ?;", (d_dict["name"],))
            else:
                cur.execute(
                    "SELECT * FROM team_alumni WHERE driver_id = ? OR driver_name = ?;", (driver_id, d_dict["name"])
                )
            alumni_row = cur.fetchone()
            d_dict["is_team_alumni"] = bool(alumni_row)
            d_dict["alumni_data"] = dict(alumni_row) if alumni_row else None
            d_dict["ai_analysis"] = self._generate_driver_ai_analysis(d_dict)

            return d_dict

    def _generate_driver_ai_analysis(self, p: Dict[str, Any]) -> Dict[str, str]:
        """Generates AI Chief Scout / Career Trajectory intelligence report."""
        age = p.get("age", 25)
        pot = p.get("potential", 70)
        pace = p.get("pace", 65)
        wins = p.get("career_totals", {}).get("wins", 0)
        is_alumni = p.get("is_team_alumni", False)
        alumni = p.get("alumni_data")
        team = p.get("team_name", "Free Agent")
        tier = p.get("team_tier", 3)

        starts = p.get("career_totals", {}).get("starts", 0)

        if starts == 0 and pot >= 80:
            arc = "UNTESTED PRODIGY"
            outlook = f"Unraced junior talent possessing immense ceiling ({pot} Potential). Eager for professional race starts."
        elif starts == 0:
            arc = "ROOKIE PROSPECT"
            outlook = (
                "Has not yet contested an official championship season. Untested in open-wheel wheel-to-wheel combat."
            )
        elif age <= 22 and pot >= 85:
            arc = "GENERATIONAL PRODIGY"
            outlook = (
                f"Rapidly climbing the ranks. Projected to reach elite Tier 1 form within {max(1, 25 - age)} seasons."
            )
        elif age <= 24 and pot >= 75:
            arc = "RISING TALENT"
            outlook = f"High growth potential. Driver pace ({pace}/99) demonstrates steady upward trajectory."
        elif age >= 33:
            arc = "VETERAN CAMPAIGNER"
            outlook = "Brings invaluable experience and calm racecraft, though developmental peak has stabilized."
        elif wins >= 4 or p.get("career_totals", {}).get("titles", 0) >= 1:
            arc = "PROVEN RACE WINNER"
            outlook = "Proven front-runner under high-pressure scenarios. Decisive overtaker and race leader."
        else:
            arc = "MIDFIELD STALWART"
            outlook = "Consistent points gatherer with balanced technical discipline and defensive grit."

        if is_alumni and alumni:
            dep_reason = alumni.get("departure_reason", "DEPARTED")
            reason_str = {
                "RELEASED": "Departed your squad via contract buyout",
                "REPLACED": "Replaced on primary roster by new signing",
                "PROMOTED_TIER2": "Earned graduation promotion to Tier 2",
                "CONTRACT_EXPIRY": "Left your organization upon contract expiry",
            }.get(dep_reason, "Former player team driver")

            alumni_verdict = f"{reason_str}. Now piloting for {team} (Tier {tier or 'FA'}). Lifetime career points: {p.get('career_totals', {}).get('points', 0)} PTS."
        else:
            alumni_verdict = "No previous contract tenure with your organization."

        return {"trajectory_arc": arc, "scout_assessment": outlook, "alumni_insight": alumni_verdict}

    def get_team_alumni(self, player_team_id: int) -> List[Dict[str, Any]]:
        """Returns all former drivers of the player team with live status updates."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            SELECT a.*, d.age, d.pace, d.consistency, d.morale, d.points as cur_points,
                   t.name as live_team_name, t.tier as live_tier, t.color_hex as live_color
            FROM team_alumni a
            LEFT JOIN drivers d ON a.driver_id = d.id
            LEFT JOIN teams t ON d.team_id = t.id
            WHERE a.player_team_id = ?
            ORDER BY a.departure_season DESC, a.id DESC;
            """,
                (player_team_id,),
            )
            rows = [dict(r) for r in cur.fetchall()]
            for r in rows:
                if r.get("live_team_name"):
                    r["current_team_name"] = r["live_team_name"]
                    r["current_tier"] = r["live_tier"]
                elif not r.get("current_team_name"):
                    r["current_team_name"] = "Free Agent"
            return rows

    def record_team_alumni(
        self,
        player_team_id: int,
        driver_id: int,
        driver_name: str,
        departure_reason: str = "RELEASED",
        departure_season: int = 1,
        starts_with_team: int = 0,
        wins_with_team: int = 0,
        podiums_with_team: int = 0,
        points_with_team: int = 0,
        current_team_id: Optional[int] = None,
        current_team_name: str = "Free Agent",
        current_tier: Optional[int] = None,
    ):
        """Records or updates a former driver's alumni dossier."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id FROM team_alumni WHERE player_team_id = ? AND driver_id = ?;", (player_team_id, driver_id)
            )
            row = cur.fetchone()
            if row:
                cur.execute(
                    """
                UPDATE team_alumni
                SET departure_reason = ?, departure_season = ?, starts_with_team = ?,
                    wins_with_team = ?, podiums_with_team = ?, points_with_team = ?,
                    current_team_id = ?, current_team_name = ?, current_tier = ?
                WHERE id = ?;
                """,
                    (
                        departure_reason,
                        departure_season,
                        starts_with_team,
                        wins_with_team,
                        podiums_with_team,
                        points_with_team,
                        current_team_id,
                        current_team_name,
                        current_tier,
                        row[0],
                    ),
                )
            else:
                seasons_active = f"Season {departure_season}"
                cur.execute(
                    """
                INSERT INTO team_alumni (
                    player_team_id, driver_id, driver_name, seasons_active,
                    starts_with_team, wins_with_team, podiums_with_team, points_with_team,
                    departure_reason, departure_season, current_team_id, current_team_name, current_tier
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                    (
                        player_team_id,
                        driver_id,
                        driver_name,
                        seasons_active,
                        starts_with_team,
                        wins_with_team,
                        podiums_with_team,
                        points_with_team,
                        departure_reason,
                        departure_season,
                        current_team_id,
                        current_team_name,
                        current_tier,
                    ),
                )
            conn.commit()

    def get_all_time_records(self) -> Dict[str, Any]:
        """Returns all-time Hall of Fame rankings for drivers and constructors."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            SELECT driver_name, team_name, SUM(wins) as total_wins, SUM(podiums) as total_podiums, SUM(points) as total_points
            FROM driver_season_history
            GROUP BY driver_name
            ORDER BY total_wins DESC, total_podiums DESC, total_points DESC
            LIMIT 5;
            """)
            top_wins_drivers = [dict(r) for r in cur.fetchall()]

            cur.execute("""
            SELECT driver_name, team_name, COUNT(*) as titles
            FROM driver_season_history
            WHERE championship_position = 1 AND tier = 1
            GROUP BY driver_name
            ORDER BY titles DESC
            LIMIT 5;
            """)
            top_champions = [dict(r) for r in cur.fetchall()]

            cur.execute("""
            SELECT t.name, t.color_hex, COUNT(*) as titles
            FROM season_history sh
            JOIN teams t ON sh.team_id = t.id
            WHERE sh.championship_position = 1 AND sh.tier = 1
            GROUP BY t.id
            ORDER BY titles DESC
            LIMIT 5;
            """)
            top_constructors = [dict(r) for r in cur.fetchall()]

            cur.execute("""
            SELECT driver_name, team_name, SUM(points) as total_points
            FROM driver_season_history
            GROUP BY driver_name
            ORDER BY total_points DESC
            LIMIT 5;
            """)
            top_pts_drivers = [dict(r) for r in cur.fetchall()]

            return {
                "top_wins_drivers": top_wins_drivers,
                "top_champions": top_champions,
                "top_constructors": top_constructors,
                "top_pts_drivers": top_pts_drivers,
            }

    def get_balance_setting(self, key: str) -> Optional[Any]:
        """Retrieves a balance setting by key, parsing JSON."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT value_json FROM balance_settings WHERE key = ?;", (key,))
            row = cur.fetchone()
            if row:
                try:
                    return json.loads(row[0])
                except Exception:
                    return row[0]
            return None

    def set_balance_setting(self, key: str, value: Any, category: str = "BALANCE", description: str = "") -> bool:
        """Stores or updates a balance setting."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            val_json = json.dumps(value) if not isinstance(value, str) else value
            cur.execute(
                """
            INSERT INTO balance_settings (key, category, value_json, description)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value_json = excluded.value_json;
            """,
                (key, category, val_json, description),
            )
            conn.commit()
            return True

    def get_all_balance_settings(self) -> Dict[str, Any]:
        """Returns all balance settings as a dictionary."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT key, value_json FROM balance_settings;")
            out = {}
            for r in cur.fetchall():
                try:
                    out[r[0]] = json.loads(r[1])
                except Exception:
                    out[r[0]] = r[1]
            return out

    def get_team_profile(self, team_id: int) -> Optional[Dict[str, Any]]:
        """Returns comprehensive constructor profile including roster, stats, and historical seasons."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM teams WHERE id = ?;", (team_id,))
            row = cur.fetchone()
            if not row:
                return None
            t_dict = dict(row)

            # Current active drivers
            cur.execute(
                """
            SELECT d.* FROM drivers d
            WHERE d.team_id = ? AND d.is_academy_driver = 0
            ORDER BY d.is_player_driver DESC, d.id ASC;
            """,
                (team_id,),
            )
            t_dict["drivers"] = [dict(r) for r in cur.fetchall()]

            # Academy drivers assigned
            cur.execute(
                """
            SELECT d.* FROM drivers d
            WHERE d.team_id = ? AND d.is_academy_driver = 1
            ORDER BY d.id ASC;
            """,
                (team_id,),
            )
            t_dict["academy_drivers"] = [dict(r) for r in cur.fetchall()]

            # Season history
            cur.execute(
                """
            SELECT * FROM season_history
            WHERE team_id = ?
            ORDER BY season_num DESC;
            """,
                (team_id,),
            )
            t_dict["season_history"] = [dict(r) for r in cur.fetchall()]

            # Career race stats
            cur.execute(
                """
            SELECT COUNT(*),
                   SUM(CASE WHEN position = 1 THEN 1 ELSE 0 END),
                   SUM(CASE WHEN position <= 3 THEN 1 ELSE 0 END),
                   SUM(points)
            FROM series_race_results
            WHERE team_id = ?;
            """,
                (team_id,),
            )
            stat_row = cur.fetchone()
            t_dict["total_starts"] = stat_row[0] if stat_row and stat_row[0] else 0
            t_dict["total_wins"] = stat_row[1] if stat_row and stat_row[1] else 0
            t_dict["total_podiums"] = stat_row[2] if stat_row and stat_row[2] else 0
            t_dict["all_time_points"] = stat_row[3] if stat_row and stat_row[3] else 0

            # Titles
            cur.execute(
                "SELECT COUNT(*) FROM season_history WHERE team_id = ? AND championship_position = 1 AND tier = 1;",
                (team_id,),
            )
            t_dict["tier1_titles"] = cur.fetchone()[0]

            return t_dict

    def get_team_by_name(self, team_name: str) -> Optional[Dict[str, Any]]:
        """Finds a constructor/team by name (case-insensitive)."""
        if not team_name:
            return None
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM teams WHERE name = ? COLLATE NOCASE;", (team_name,))
            row = cur.fetchone()
            return dict(row) if row else None

    def save_track_setup_preset(
        self,
        team_id: int,
        track_name: str,
        car_slot: int,
        front_wing: float,
        rear_wing: float,
        suspension: float,
        gear_ratio: float,
        brake_bias: float,
    ) -> bool:
        """Persists a personal setup configuration for a specific track and car slot."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO track_setup_presets (
                    team_id, track_name, car_slot, front_wing, rear_wing, suspension, gear_ratio, brake_bias, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(team_id, track_name, car_slot) DO UPDATE SET
                    front_wing = excluded.front_wing,
                    rear_wing = excluded.rear_wing,
                    suspension = excluded.suspension,
                    gear_ratio = excluded.gear_ratio,
                    brake_bias = excluded.brake_bias,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                (team_id, track_name, car_slot, front_wing, rear_wing, suspension, gear_ratio, brake_bias),
            )
            conn.commit()
            return True

    def load_track_setup_preset(self, team_id: int, track_name: str, car_slot: int = 1) -> Optional[Dict[str, float]]:
        """Retrieves a saved personal setup for a track and car slot, falling back to car_slot 1 if needed."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT front_wing, rear_wing, suspension, gear_ratio, brake_bias
                FROM track_setup_presets
                WHERE team_id = ? AND track_name = ? AND car_slot = ?;
                """,
                (team_id, track_name, car_slot),
            )
            row = cur.fetchone()
            if not row and car_slot != 1:
                # Fallback to car 1 preset if car 2 specific preset not found
                cur.execute(
                    """
                    SELECT front_wing, rear_wing, suspension, gear_ratio, brake_bias
                    FROM track_setup_presets
                    WHERE team_id = ? AND track_name = ? AND car_slot = 1;
                    """,
                    (team_id, track_name),
                )
                row = cur.fetchone()

            if row:
                return {
                    "front_wing": float(row[0]),
                    "rear_wing": float(row[1]),
                    "suspension": float(row[2]),
                    "gear_ratio": float(row[3]),
                    "brake_bias": float(row[4]),
                }
            return None
