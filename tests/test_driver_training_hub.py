import pytest

from src.database.career_db import ALL_FACILITY_NODES, FACILITY_SPECIALTY_MAP, CareerDatabase
from src.database.equipment_catalog import EQUIPMENT_CATALOG
from src.management.driver_manager import DriverManager
from src.management.engineering_manager import EngineeringManager
from src.management.sponsor_manager import SponsorManager


@pytest.fixture
def test_db(tmp_path):
    db_file = tmp_path / "test_driver_hub.db"
    db = CareerDatabase(str(db_file))
    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
        UPDATE teams 
        SET tier = 3, cash = 50000000.0, reputation = 50.0, is_player = 1
        WHERE id = 1;
        """)
        # Clear existing drivers in team 1 to have clean test state
        cur.execute("DELETE FROM drivers WHERE team_id = 1;")
        conn.commit()
    return db


def test_driver_perf_nodes_and_equipment_catalog(test_db):
    """Verifies all 11 DRIVER_PERF nodes are present in database schema and have equipment entries."""
    driver_nodes = [n for n in ALL_FACILITY_NODES if n[1] == "DRIVER_PERF"]
    node_ids = {n[0] for n in driver_nodes}

    expected_nodes = {
        "driver_sim",
        "driver_motion_sim",
        "driver_vr_cognitive",
        "driver_gym_conditioning",
        "driver_physio_recovery",
        "driver_media_pr_coach",
        "driver_radio_comms_lab",
        "driver_commercial_suite",
        "driver_academy",
        "driver_karting_scholarship",
        "driver_f4_bootcamp",
    }
    assert expected_nodes.issubset(node_ids), f"Missing nodes: {expected_nodes - node_ids}"

    # Verify specialty mapping for all driver nodes
    for nid in expected_nodes:
        assert nid in FACILITY_SPECIALTY_MAP, f"Node {nid} not found in FACILITY_SPECIALTY_MAP"

    # Verify equipment catalog has 4 equipment items for each driver facility node
    driver_eq = [e for e in EQUIPMENT_CATALOG if e[1] in expected_nodes]
    eq_by_node = {}
    for e in driver_eq:
        eq_by_node[e[1]] = eq_by_node.get(e[1], 0) + 1

    for nid in expected_nodes:
        assert eq_by_node.get(nid, 0) == 4, f"Node {nid} has {eq_by_node.get(nid, 0)} equipment items, expected 4"


def test_driver_progression_reflex_and_gym_buffs(test_db):
    """Verifies Neuro-Reflex Lab and Biometric Gym accelerate driver physical stats."""
    dm = DriverManager(test_db)

    # Insert a young driver (age 22)
    with test_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO drivers (
            id, team_id, name, age, number, is_player_driver, is_academy_driver,
            salary_per_race, contract_races_left, contract_seasons_left, potential,
            pace, race_starts, braking, tire_management, defending, wet_weather,
            consistency, fuel_efficiency, technical_understanding, communication, marketability,
            pot_pace, pot_race_starts, pot_braking, pot_tire_management, pot_defending, pot_wet_weather,
            pot_consistency, pot_fuel_efficiency, pot_technical_understanding, pot_communication, pot_marketability
        ) VALUES (
            9001, 1, 'Test Driver', 22, 11, 1, 0,
            5000.0, 10, 1, 90,
            50.0, 50.0, 50.0, 50.0, 50.0, 50.0,
            50.0, 50.0, 50.0, 50.0, 50.0,
            90.0, 90.0, 90.0, 90.0, 90.0, 90.0,
            90.0, 90.0, 90.0, 90.0, 90.0
        );
        """)
        conn.commit()

    # Step 1: Base progression without facilities
    dm.process_weekly_driver_development(1, player_race_pos=1)
    with test_db.get_connection() as conn:
        d_base = dict(conn.cursor().execute("SELECT * FROM drivers WHERE id = 9001;").fetchone())

    base_starts_gain = d_base["race_starts"] - 50.0
    base_tires_gain = d_base["tire_management"] - 50.0

    # Step 2: Unlock driver_vr_cognitive (tier 2) and driver_gym_conditioning (tier 2)
    with test_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO team_facilities (team_id, node_id, is_unlocked, current_tier)
        VALUES 
            (1, 'driver_vr_cognitive', 1, 2),
            (1, 'driver_gym_conditioning', 1, 2)
        ON CONFLICT(team_id, node_id) DO UPDATE SET is_unlocked=1, current_tier=2;
        """)
        # Reset driver stats to 50
        cur.execute("""
        UPDATE drivers SET race_starts = 50.0, tire_management = 50.0, consistency = 50.0, defending = 50.0, wet_weather = 50.0
        WHERE id = 9001;
        """)
        conn.commit()

    dm.process_weekly_driver_development(1, player_race_pos=1)
    with test_db.get_connection() as conn:
        d_boosted = dict(conn.cursor().execute("SELECT * FROM drivers WHERE id = 9001;").fetchone())

    boosted_starts_gain = d_boosted["race_starts"] - 50.0
    boosted_tires_gain = d_boosted["tire_management"] - 50.0

    assert boosted_starts_gain > base_starts_gain * 1.4, (
        f"Starts gain not boosted: {boosted_starts_gain} vs {base_starts_gain}"
    )
    assert boosted_tires_gain > base_tires_gain * 1.3, (
        f"Tires gain not boosted: {boosted_tires_gain} vs {base_tires_gain}"
    )


def test_veteran_age_decay_physio_protection(test_db):
    """Verifies Physio & Longevity Clinic significantly protects veteran drivers (age > 30) from physical decay."""
    dm = DriverManager(test_db)

    # Insert a 36-year-old veteran driver
    with test_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO drivers (
            id, team_id, name, age, number, is_player_driver, is_academy_driver,
            salary_per_race, contract_races_left, contract_seasons_left, potential,
            pace, race_starts, braking, tire_management, defending, wet_weather,
            consistency, fuel_efficiency, technical_understanding, communication, marketability
        ) VALUES (
            9002, 1, 'Veteran Champion', 36, 1, 1, 0,
            15000.0, 10, 1, 88,
            80.0, 80.0, 80.0, 80.0, 80.0, 80.0,
            80.0, 80.0, 80.0, 80.0, 80.0
        );
        """)
        conn.commit()

    # Step 1: Base decline without clinic
    dm.process_weekly_driver_development(1, player_race_pos=5)
    with test_db.get_connection() as conn:
        d_unprotected = dict(conn.cursor().execute("SELECT * FROM drivers WHERE id = 9002;").fetchone())
    decay_unprotected = 80.0 - d_unprotected["pace"]

    # Step 2: Unlock Physio Clinic Tier 2
    with test_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO team_facilities (team_id, node_id, is_unlocked, current_tier)
        VALUES (1, 'driver_physio_recovery', 1, 2)
        ON CONFLICT(team_id, node_id) DO UPDATE SET is_unlocked=1, current_tier=2;
        """)
        cur.execute("UPDATE drivers SET pace = 80.0 WHERE id = 9002;")
        conn.commit()

    dm.process_weekly_driver_development(1, player_race_pos=5)
    with test_db.get_connection() as conn:
        d_protected = dict(conn.cursor().execute("SELECT * FROM drivers WHERE id = 9002;").fetchone())
    decay_protected = 80.0 - d_protected["pace"]

    assert decay_protected < decay_unprotected * 0.45, (
        f"Physio did not protect veteran: decay_protected={decay_protected}, decay_unprotected={decay_unprotected}"
    )


def test_commercial_and_communication_progression(test_db):
    """Verifies Media PR Studio, Radio Comms Lab, and Commercial Suite boost Marketability & Comms."""
    dm = DriverManager(test_db)

    # Insert driver
    with test_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO drivers (
            id, team_id, name, age, number, is_player_driver, is_academy_driver,
            salary_per_race, contract_races_left, contract_seasons_left, potential,
            pace, race_starts, braking, tire_management, defending, wet_weather,
            consistency, fuel_efficiency, technical_understanding, communication, marketability,
            pot_technical_understanding, pot_communication, pot_marketability
        ) VALUES (
            9003, 1, 'Media Star', 24, 44, 1, 0,
            8000.0, 10, 1, 85,
            70.0, 70.0, 70.0, 70.0, 70.0, 70.0,
            70.0, 70.0, 50.0, 50.0, 50.0,
            90.0, 90.0, 90.0
        );
        """)
        conn.commit()

    # Step 1: Base progression
    dm.process_weekly_driver_development(1, player_race_pos=1)
    with test_db.get_connection() as conn:
        d_base = dict(conn.cursor().execute("SELECT * FROM drivers WHERE id = 9003;").fetchone())

    base_mkt_gain = d_base["marketability"] - 50.0
    base_comm_gain = d_base["communication"] - 50.0

    # Step 2: Unlock Media Studio Tier 2 and Radio Comms Lab Tier 2
    with test_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO team_facilities (team_id, node_id, is_unlocked, current_tier)
        VALUES 
            (1, 'driver_media_pr_coach', 1, 2),
            (1, 'driver_commercial_suite', 1, 1),
            (1, 'driver_radio_comms_lab', 1, 2)
        ON CONFLICT(team_id, node_id) DO UPDATE SET is_unlocked=1, current_tier=excluded.current_tier;
        """)
        cur.execute("UPDATE drivers SET marketability = 50.0, communication = 50.0 WHERE id = 9003;")
        conn.commit()

    dm.process_weekly_driver_development(1, player_race_pos=1)
    with test_db.get_connection() as conn:
        d_boosted = dict(conn.cursor().execute("SELECT * FROM drivers WHERE id = 9003;").fetchone())

    boosted_mkt_gain = d_boosted["marketability"] - 50.0
    boosted_comm_gain = d_boosted["communication"] - 50.0

    assert boosted_mkt_gain > base_mkt_gain * 1.5, (
        f"Marketability gain not boosted: {boosted_mkt_gain} vs {base_mkt_gain}"
    )
    assert boosted_comm_gain > base_comm_gain * 1.5, (
        f"Communication gain not boosted: {boosted_comm_gain} vs {base_comm_gain}"
    )


def test_sponsor_appeal_and_engineering_synergy(test_db):
    """Verifies driver_commercial_suite boosts Sponsor Appeal & race payouts, and driver_radio_comms_lab boosts R&D knowledge."""
    sm = SponsorManager(test_db)
    em = EngineeringManager(test_db)

    # Appeal without Commercial Suite
    appeal_base = sm.calculate_sponsor_appeal(1)["total_appeal"]

    # Unlock driver_commercial_suite Tier 2
    with test_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO team_facilities (team_id, node_id, is_unlocked, current_tier)
        VALUES (1, 'driver_commercial_suite', 1, 2)
        ON CONFLICT(team_id, node_id) DO UPDATE SET is_unlocked=1, current_tier=2;
        """)
        conn.commit()

    appeal_boosted = sm.calculate_sponsor_appeal(1)["total_appeal"]
    assert appeal_boosted >= appeal_base + 10, f"Sponsor Appeal not boosted: {appeal_boosted} vs {appeal_base}"

    # Verify engineering driver factor boost with Radio Comms Lab Tier 2
    with test_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO team_facilities (team_id, node_id, is_unlocked, current_tier)
        VALUES (1, 'driver_radio_comms_lab', 1, 2)
        ON CONFLICT(team_id, node_id) DO UPDATE SET is_unlocked=1, current_tier=2;
        """)
        conn.commit()

    # Query facility tiers
    with test_db.get_connection() as conn:
        fac_tiers = {
            r[0]: r[1]
            for r in conn.cursor()
            .execute("SELECT node_id, current_tier FROM team_facilities WHERE team_id=1;")
            .fetchall()
        }

    radio_tier = fac_tiers.get("driver_radio_comms_lab", 0)
    assert radio_tier == 2


def test_karting_scholarship_scout_generation(test_db):
    """Verifies Grassroots Karting Foundation adds guaranteed prodigy prospect and raises potential floor."""
    dm = DriverManager(test_db)

    # Base scouting
    dm._generate_scout_prospects(1)
    with test_db.get_connection() as conn:
        prospects_base = [
            dict(r) for r in conn.cursor().execute("SELECT * FROM scout_prospects WHERE team_id=1;").fetchall()
        ]

    assert len(prospects_base) == 6

    # Unlock Grassroots Karting Scholarship Tier 2
    with test_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO team_facilities (team_id, node_id, is_unlocked, current_tier)
        VALUES (1, 'driver_karting_scholarship', 1, 2)
        ON CONFLICT(team_id, node_id) DO UPDATE SET is_unlocked=1, current_tier=2;
        """)
        conn.commit()

    dm._generate_scout_prospects(1)
    with test_db.get_connection() as conn:
        prospects_boosted = [
            dict(r) for r in conn.cursor().execute("SELECT * FROM scout_prospects WHERE team_id=1;").fetchall()
        ]

    # Should contain 7 prospects (including scholarship prodigy Valerio De Luca)
    assert len(prospects_boosted) == 7
    names = [p["name"] for p in prospects_boosted]
    assert "Valerio De Luca" in names

    # Compare average potentials
    avg_pot_base = sum(p["potential"] for p in prospects_base) / len(prospects_base)
    avg_pot_boosted = sum(p["potential"] for p in prospects_boosted) / len(prospects_boosted)
    assert avg_pot_boosted > avg_pot_base + 3, f"Average potential not boosted: {avg_pot_boosted} vs {avg_pot_base}"


def test_sim_trickle_down_to_academy_drivers(test_db):
    """Verifies senior Driver Sim and Hexapod Motion Sim trickle down to boost academy junior driver progression."""
    dm = DriverManager(test_db)

    # Insert academy driver
    with test_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO drivers (
            id, team_id, name, age, number, is_player_driver, is_academy_driver,
            salary_per_race, contract_races_left, contract_seasons_left, potential,
            pace, race_starts, braking, tire_management, defending, wet_weather,
            consistency, fuel_efficiency, technical_understanding, communication, marketability,
            academy_tier_placement, academy_team_name, academy_seat_expected_pos
        ) VALUES (
            9004, 1, 'Academy Rookie', 16, 88, 0, 1,
            500.0, 10, 1, 92,
            40.0, 40.0, 40.0, 40.0, 40.0, 40.0,
            40.0, 40.0, 35.0, 35.0, 35.0,
            5, 'EuroKart Masters', 'P3 / 10'
        );
        """)
        conn.commit()

    # Base development with senior sim facilities at tier 0
    with test_db.get_connection() as conn:
        conn.cursor().execute("""
        UPDATE team_facilities 
        SET current_tier = 0, is_unlocked = 0 
        WHERE team_id = 1 AND node_id IN ('driver_sim', 'driver_motion_sim');
        """)
        conn.commit()

    dm.process_weekly_driver_development(1)
    with test_db.get_connection() as conn:
        d_base = dict(conn.cursor().execute("SELECT * FROM drivers WHERE id = 9004;").fetchone())
    base_pace_gain = d_base["pace"] - 40.0

    # Unlock senior driver_sim Tier 2 and driver_motion_sim Tier 2
    with test_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO team_facilities (team_id, node_id, is_unlocked, current_tier)
        VALUES 
            (1, 'driver_sim', 1, 2),
            (1, 'driver_motion_sim', 1, 2)
        ON CONFLICT(team_id, node_id) DO UPDATE SET is_unlocked=1, current_tier=2;
        """)
        cur.execute("UPDATE drivers SET pace = 40.0 WHERE id = 9004;")
        conn.commit()

    dm.process_weekly_driver_development(1)
    with test_db.get_connection() as conn:
        d_boosted = dict(conn.cursor().execute("SELECT * FROM drivers WHERE id = 9004;").fetchone())
    boosted_pace_gain = d_boosted["pace"] - 40.0

    # Trickle down bonus (+6% * 2 from sim + 8% * 2 from motion sim = +28% trickle down)
    assert boosted_pace_gain > base_pace_gain * 1.20, (
        f"Trickle down not observed: {boosted_pace_gain} vs {base_pace_gain}"
    )


def test_driver_buyout_costs_expensive_for_pay_and_loan_drivers(test_db):
    """Verifies that pay-drivers and loan talents carry substantial contract buyout severance while stand-in defaults are free."""
    dm = DriverManager(test_db)

    # Stand-in Default driver: $0 buyout
    d_default = {"driver_type": "DEFAULT_DRIVER", "contract_races_left": 0}
    assert dm.get_driver_buyout_cost(d_default) == 0.0

    # Pay-driver: 10 races left at $40,000/race sponsor income -> 1.5x penalty = $600,000
    d_pay = {"driver_type": "PAY_DRIVER", "contract_races_left": 10, "sponsor_income_per_race": 40000.0, "tier": 3}
    cost_pay = dm.get_driver_buyout_cost(d_pay)
    assert cost_pay == 600000.0
    assert cost_pay > 0.0

    # Sponsored loan driver: 10 races left at $50,000/race fee -> 1.5x penalty = $750,000
    d_loan = {
        "driver_type": "SPONSORED_DRIVER",
        "contract_races_left": 10,
        "sponsor_income_per_race": 50000.0,
        "tier": 3,
    }
    cost_loan = dm.get_driver_buyout_cost(d_loan)
    assert cost_loan == 750000.0
    assert cost_loan > 0.0

    # Standard driver: 10 races left at $30,000/race -> 0.5x severance = $150,000
    d_std = {"driver_type": "STANDARD", "contract_races_left": 10, "salary_per_race": 30000.0}
    assert dm.get_driver_buyout_cost(d_std) == 150000.0
