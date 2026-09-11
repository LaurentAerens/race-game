import pytest
import sqlite3
import os
from src.database.career_db import CareerDatabase, ALL_FACILITY_NODES
from src.database.equipment_catalog import EQUIPMENT_CATALOG
from src.management.staff_manager import StaffManager

@pytest.fixture
def temp_db(tmp_path):
    db_file = str(tmp_path / "test_mgmt_career.db")
    db = CareerDatabase(db_file)
    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
        UPDATE teams 
        SET tier = 1, cash = 50000000.0, reputation = 80.0, is_player = 1
        WHERE id = 1;
        """)
        # Clear existing personnel and team_facilities for team 1 to have isolated test state
        cur.execute("DELETE FROM personnel WHERE team_id = 1;")
        cur.execute("DELETE FROM team_facilities WHERE team_id = 1;")
        cur.execute("DELETE FROM team_equipment WHERE team_id = 1;")
        cur.execute("DELETE FROM team_category_directors WHERE team_id = 1;")
        conn.commit()
    return db

def test_management_single_node_tree_structure(temp_db):
    """Verifies that MANAGEMENT has exactly 1 single root node (Executive Boardroom)."""
    mgmt_nodes = [n for n in ALL_FACILITY_NODES if n[1] == "MANAGEMENT"]
    assert len(mgmt_nodes) == 1, f"Expected exactly 1 MANAGEMENT node, got {len(mgmt_nodes)}: {[n[0] for n in mgmt_nodes]}"
    
    boardroom = mgmt_nodes[0]
    node_id, dept, name, desc, parent_id, min_tier, max_tier, cost, upkeep, staff_cap, league = boardroom
    assert node_id == "mgmt_boardroom"
    assert dept == "MANAGEMENT"
    assert parent_id is None
    assert max_tier == 3
    assert cost > 0
    assert upkeep > 0

def test_management_equipment_catalog():
    """Verifies all equipment pieces for mgmt_boardroom are properly configured with no orphans."""
    mgmt_eq = [eq for eq in EQUIPMENT_CATALOG if eq[1] == "mgmt_boardroom"]
    assert len(mgmt_eq) == 4
    eq_ids = [eq[0] for eq in mgmt_eq]
    assert "eq_mgmt_strategy_war_room" in eq_ids
    assert "eq_mgmt_exec_telemetry" in eq_ids
    assert "eq_mgmt_mentorship_suite" in eq_ids
    assert "eq_mgmt_board_display" in eq_ids

    # Ensure no old mgmt_automation equipment remains
    auto_eq = [eq for eq in EQUIPMENT_CATALOG if eq[1] == "mgmt_automation"]
    assert len(auto_eq) == 0

def test_management_global_leadership_output_boost(temp_db):
    """Verifies calculate_facility_staff_output boosts effective head/director leadership and coordination."""
    staff_mgr = StaffManager(temp_db)

    with temp_db.get_connection() as conn:
        cur = conn.cursor()
        
        # Seed an engineering facility node and personnel
        cur.execute("INSERT INTO team_facilities (team_id, node_id, current_tier, is_unlocked) VALUES (1, 'eng_workshop', 1, 1);")
        cur.execute("INSERT INTO team_facilities (team_id, node_id, current_tier, is_unlocked) VALUES (1, 'mgmt_boardroom', 0, 0);")
        
        # Seed Category Director for ENGINEERING with baseline 40 leadership
        cur.execute("""
        INSERT INTO personnel (id, team_id, facility_node_id, assigned_category, role_type, name, age, birth_year, peak_age, retire_age, specialty, salary_monthly, market_value_monthly, morale, stat_engineering, stat_craftsmanship, stat_marketing, stat_communication, stat_leadership, stat_composure, stat_potential)
        VALUES (10, 1, NULL, 'ENGINEERING', 'CATEGORY_DIRECTOR', 'Elena Vance', 45, 1981, 50, 70, 'COMPOSITES', 10000, 10000, 90, 60, 40, 40, 50, 40, 50, 70);
        """)
        cur.execute("INSERT OR REPLACE INTO team_category_directors (team_id, category, director_personnel_id) VALUES (1, 'ENGINEERING', 10);")

        # Seed Department Head with baseline 35 leadership
        cur.execute("""
        INSERT INTO personnel (id, team_id, facility_node_id, assigned_category, role_type, name, age, birth_year, peak_age, retire_age, specialty, salary_monthly, market_value_monthly, morale, stat_engineering, stat_craftsmanship, stat_marketing, stat_communication, stat_leadership, stat_composure, stat_potential)
        VALUES (20, 1, 'eng_workshop', NULL, 'DEPARTMENT_HEAD', 'Marcus Croft', 42, 1984, 50, 70, 'COMPOSITES', 8000, 8000, 90, 55, 40, 40, 45, 35, 50, 65);
        """)

        # Seed 2 staff specialists
        cur.execute("""
        INSERT INTO personnel (id, team_id, facility_node_id, assigned_category, role_type, name, age, birth_year, peak_age, retire_age, specialty, salary_monthly, market_value_monthly, morale, stat_engineering, stat_craftsmanship, stat_marketing, stat_communication, stat_leadership, stat_composure, stat_potential)
        VALUES 
        (31, 1, 'eng_workshop', NULL, 'STAFF', 'Tech Alpha', 28, 1998, 50, 70, 'COMPOSITES', 4000, 4000, 90, 50, 40, 40, 40, 30, 50, 65),
        (32, 1, 'eng_workshop', NULL, 'STAFF', 'Tech Beta', 29, 1997, 50, 70, 'COMPOSITES', 4000, 4000, 90, 50, 40, 40, 40, 30, 50, 65);
        """)
        conn.commit()

    # 1. Baseline calculation with mgmt_boardroom Tier 0
    out_tier0 = staff_mgr.calculate_facility_staff_output(1, 'eng_workshop', 1)
    assert out_tier0["mgmt_lead_bonus"] == 0.0
    base_head_mult = out_tier0["head_mult"]
    base_dir_mult = out_tier0["dir_mult"]
    base_coord = out_tier0["coordination_rating"]
    base_total_mult = out_tier0["staff_mult"]

    # 2. Upgrade mgmt_boardroom to Tier 2 (+10.0 Global Leadership Aura)
    with temp_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE team_facilities SET current_tier = 2, is_unlocked = 1 WHERE team_id = 1 AND node_id = 'mgmt_boardroom';")
        conn.commit()

    out_tier2 = staff_mgr.calculate_facility_staff_output(1, 'eng_workshop', 1)
    assert out_tier2["mgmt_lead_bonus"] == 10.0
    assert out_tier2["head_mult"] > base_head_mult
    assert out_tier2["dir_mult"] > base_dir_mult
    assert out_tier2["coordination_rating"] > base_coord
    assert out_tier2["staff_mult"] > base_total_mult

    # 3. Add Strategic War Room equipment (level 2 -> +3.0 additional leadership)
    with temp_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO team_equipment (team_id, equipment_id, current_level, is_active) VALUES (1, 'eq_mgmt_strategy_war_room', 2, 1);")
        conn.commit()

    out_equip = staff_mgr.calculate_facility_staff_output(1, 'eng_workshop', 1)
    assert out_equip["mgmt_lead_bonus"] == 13.0 # 10.0 from tier + 3.0 from equipment
    assert out_equip["head_mult"] > out_tier2["head_mult"]
    assert out_equip["staff_mult"] > out_tier2["staff_mult"]

def test_management_weekly_personnel_turn_boost(temp_db):
    """Verifies that advance_weekly_personnel increases stat_leadership for ALL personnel in the factory."""
    staff_mgr = StaffManager(temp_db)

    with temp_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO team_facilities (team_id, node_id, current_tier, is_unlocked) VALUES (1, 'mgmt_boardroom', 2, 1);") # Tier 2 -> 0.30/wk

        # Insert 1 Director, 1 Head, 1 Staff, 1 Intern
        cur.execute("""
        INSERT INTO personnel (id, team_id, facility_node_id, assigned_category, role_type, name, age, birth_year, peak_age, retire_age, specialty, salary_monthly, market_value_monthly, morale, stat_engineering, stat_craftsmanship, stat_marketing, stat_communication, stat_leadership, stat_composure, stat_potential, is_intern)
        VALUES 
        (1, 1, NULL, 'ENGINEERING', 'CATEGORY_DIRECTOR', 'Dir One', 45, 1981, 50, 70, 'COMPOSITES', 10000, 10000, 90, 50, 50, 50, 50, 40.0, 50, 70, 0),
        (2, 1, 'eng_workshop', NULL, 'DEPARTMENT_HEAD', 'Head One', 42, 1984, 50, 70, 'COMPOSITES', 8000, 8000, 90, 50, 50, 50, 50, 35.0, 50, 70, 0),
        (3, 1, 'eng_workshop', NULL, 'STAFF', 'Staff One', 28, 1998, 50, 70, 'COMPOSITES', 4000, 4000, 90, 50, 50, 50, 50, 25.0, 50, 70, 0),
        (4, 1, 'eng_workshop', NULL, 'INTERN', 'Intern One', 21, 2005, 50, 70, 'COMPOSITES', 1000, 1000, 90, 30, 30, 30, 30, 20.0, 50, 70, 1);
        """)
        conn.commit()

    # Advance 1 week
    staff_mgr.advance_weekly_personnel(1)

    with temp_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, role_type, stat_leadership FROM personnel WHERE team_id = 1 ORDER BY id;")
        results = cur.fetchall()

    # Expected gain: 0.15 * 2 = +0.30 leadership for EVERYONE in the factory
    dir_row = results[0]
    head_row = results[1]
    staff_row = results[2]
    intern_row = results[3]

    assert dir_row[2] == pytest.approx(40.30, rel=1e-2)
    assert head_row[2] == pytest.approx(35.30, rel=1e-2)
    assert staff_row[2] == pytest.approx(25.30, rel=1e-2)
    assert intern_row[2] == pytest.approx(20.30, rel=1e-2)

def test_management_mentorship_equipment_growth_bonus(temp_db):
    """Verifies that Executive Mentorship Suite equipment further accelerates weekly leadership growth."""
    staff_mgr = StaffManager(temp_db)

    with temp_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO team_facilities (team_id, node_id, current_tier, is_unlocked) VALUES (1, 'mgmt_boardroom', 1, 1);") # Tier 1 -> 0.15/wk
        # Add Mentorship Suite level 2 (+0.10/wk) -> total 0.25/wk
        cur.execute("INSERT INTO team_equipment (team_id, equipment_id, current_level, is_active) VALUES (1, 'eq_mgmt_mentorship_suite', 2, 1);")

        cur.execute("""
        INSERT INTO personnel (id, team_id, facility_node_id, assigned_category, role_type, name, age, birth_year, peak_age, retire_age, specialty, salary_monthly, market_value_monthly, morale, stat_engineering, stat_craftsmanship, stat_marketing, stat_communication, stat_leadership, stat_composure, stat_potential)
        VALUES (5, 1, 'eng_workshop', NULL, 'STAFF', 'Specialist Jack', 30, 1996, 50, 70, 'COMPOSITES', 4000, 4000, 90, 50, 50, 50, 50, 30.0, 50, 70);
        """)
        conn.commit()

    staff_mgr.advance_weekly_personnel(1)

    with temp_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT stat_leadership FROM personnel WHERE id = 5;")
        new_lead = cur.fetchone()[0]

    assert new_lead == pytest.approx(30.25, rel=1e-2)
