import pytest
import os
import random
from src.database.career_db import CareerDatabase, ALL_FACILITY_NODES
from src.database.equipment_catalog import EQUIPMENT_CATALOG
from src.core.car import Car, CarAttributes
from src.core.driver import Driver
from src.data.default_tracks import create_emerald_ring
from src.core.race_weekend import RaceWeekendManager, RaceWeekendSession, CarSetup, OptimalTrackSetup
from src.core.weather import WeatherSystem
from src.management.innovation_manager import InnovationManager
from src.management.engineering_manager import EngineeringManager

TEST_DB_PATH = "test_trackside_suite.db"

@pytest.fixture
def clean_db(tmp_path):
    db_file = str(tmp_path / "test_trackside_suite.db")
    db = CareerDatabase(db_file)
    return db

def test_trackside_facility_nodes_seeded(clean_db):
    expected_nodes = [
        "track_pitrig", "track_wheelguns", "track_telemetry",
        "track_fast_repair", "track_jack_release", "track_rival_intel",
        "track_reverse_eng", "track_weather_station", "track_setup_telemetry",
        "track_virtual_sim", "track_comm_uplink"
    ]
    with clean_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, department FROM facility_nodes WHERE department = 'TRACKSIDE';")
        db_nodes = {r[0] for r in cur.fetchall()}
        for en in expected_nodes:
            assert en in db_nodes, f"Missing trackside node: {en}"

def test_trackside_equipment_catalog(clean_db):
    expected_equipment = [
        ("track_fast_repair", "eq_rep_quick_latch_jig"),
        ("track_fast_repair", "eq_rep_rapid_curing_resin"),
        ("track_fast_repair", "eq_rep_pneumatic_riveter"),
        ("track_jack_release", "eq_jck_sub02_pivot"),
        ("track_jack_release", "eq_jck_laser_traffic"),
        ("track_rival_intel", "eq_intel_telephoto_array"),
        ("track_rival_intel", "eq_intel_acoustic_microphones"),
        ("track_reverse_eng", "eq_rev_lidar_scanner"),
        ("track_reverse_eng", "eq_rev_photogrammetry_ai"),
        ("track_weather_station", "eq_met_xband_doppler"),
        ("track_weather_station", "eq_met_barometric_array"),
        ("track_setup_telemetry", "eq_set_laser_ride_sensors"),
        ("track_setup_telemetry", "eq_set_pushrod_strain_links"),
        ("track_virtual_sim", "eq_vsim_cloud_cluster"),
        ("track_virtual_sim", "eq_vsim_tire_degrade_sim"),
        ("track_comm_uplink", "eq_uplink_satellite_transceiver"),
        ("track_comm_uplink", "eq_uplink_edge_telemetry"),
    ]
    with clean_db.get_connection() as conn:
        cur = conn.cursor()
        for node_id, eq_id in expected_equipment:
            cur.execute("SELECT id, node_id FROM facility_equipment WHERE id = ?;", (eq_id,))
            row = cur.fetchone()
            assert row is not None, f"Missing equipment: {eq_id}"
            assert row[1] == node_id, f"Equipment {eq_id} mismatch: {row[1]}"

def test_car_pit_modifiers_and_repairs():
    driver = Driver("Test Driver", 1, "GBR", 25, 80, 80, 80, 80, 80, 80, 80)
    car = Car(1, driver)
    car.pit_modifiers = {
        "base_stop_reduction": 0.45,
        "error_rate_mult": 0.2,
        "wing_change_time": 2.2,
        "repair_time": 8.0,
        "repair_durability_min": 72.0,
        "repair_durability_max": 78.0,
    }
    car.order_pit_stop(new_compound="HARD", replace_front_wing=True, emergency_repairs=True)
    car.part_durability["FRONT_WING"] = 20.0
    car.part_durability["ENGINE"] = 40.0

    circuit = create_emerald_ring()
    car.in_pit_lane = True
    car.pit_state = "APPROACH"
    car.pit_s = circuit.pit_length * circuit.pit_box_s
    car.speed = 0.0

    car._update_pit_lane(dt=0.01, circuit=circuit)
    assert car.pit_state == "IN_BOX"
    assert car.pit_timer >= 12.0
    assert car.pit_timer <= 15.5

    car._update_pit_lane(dt=car.pit_timer + 0.1, circuit=circuit)
    assert car.pit_state == "EXITING"
    assert car.part_durability["FRONT_WING"] >= 99.0
    assert car.part_durability["ENGINE"] >= 72.0

def test_virtual_sim_fp1_seeding_and_confidence():
    track_meta = {"track_name": "Emerald Ring", "circuit_file": "emerald_ring.json"}
    mgr_no_sim = RaceWeekendManager(league_tier=3, track_metadata=track_meta, facility_tiers={}, equipment_levels={})
    assert mgr_no_sim.setup_confidence[1] == 25.0
    assert mgr_no_sim.car_setups[1].front_wing == 50.0

    mgr_with_sim = RaceWeekendManager(
        league_tier=3, track_metadata=track_meta,
        facility_tiers={"track_virtual_sim": 2},
        equipment_levels={"eq_vsim_cloud_cluster": 3, "eq_vsim_tire_degrade_sim": 2}
    )
    assert mgr_with_sim.setup_confidence[1] >= 45.0
    opt = mgr_with_sim.optimal_setup
    c1_setup = mgr_with_sim.car_setups[1]
    assert abs(c1_setup.front_wing - opt.front_wing) <= 12.0

def test_setup_guidance_ranges():
    track_meta = {"track_name": "Emerald Ring", "circuit_file": "emerald_ring.json"}
    mgr_no_analytics = RaceWeekendManager(3, track_meta, facility_tiers={})
    assert mgr_no_analytics.get_setup_guidance_ranges() is None

    mgr_t1 = RaceWeekendManager(3, track_meta, facility_tiers={"track_setup_telemetry": 1})
    ranges_t1 = mgr_t1.get_setup_guidance_ranges()
    assert ranges_t1 is not None
    span_fw_t1 = ranges_t1["front_wing"][1] - ranges_t1["front_wing"][0]

    mgr_t3 = RaceWeekendManager(3, track_meta, facility_tiers={"track_setup_telemetry": 3}, equipment_levels={"eq_set_laser_ride_sensors": 3})
    ranges_t3 = mgr_t3.get_setup_guidance_ranges()
    span_fw_t3 = ranges_t3["front_wing"][1] - ranges_t3["front_wing"][0]
    assert span_fw_t3 < span_fw_t1

def test_competitor_intelligence_scaling(clean_db):
    im = InnovationManager(clean_db)
    with clean_db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM teams LIMIT 1;")
        team_id = cur.fetchone()[0]
        cur.execute("""
        INSERT INTO team_facilities (team_id, node_id, current_tier, is_unlocked, monthly_sub_budget)
        VALUES (?, 'track_rival_intel', 3, 1, 50000),
               (?, 'track_reverse_eng', 3, 1, 50000)
        ON CONFLICT(team_id, node_id) DO UPDATE SET current_tier = 3, is_unlocked = 1;
        """, (team_id, team_id))
        cur.execute("""
        INSERT INTO team_equipment (team_id, equipment_id, current_level, is_active)
        VALUES (?, 'eq_intel_telephoto_array', 4, 1),
               (?, 'eq_rev_lidar_scanner', 4, 1)
        ON CONFLICT(team_id, equipment_id) DO UPDATE SET current_level = 4, is_active = 1;
        """, (team_id, team_id))

    random.seed(42)
    im.check_and_generate_proposals(team_id, workforce_count=50, trackside_crew_count=15)
    pitches = im.get_team_pitches(team_id, status="PENDING")
    assert len(pitches) > 0

def test_weather_radar_lookahead():
    weather = WeatherSystem()
    slice_base = weather.get_forecast_slice(current_lap=1, window=6, radar_tier=0, radar_eq_lvl=0)
    slice_boosted = weather.get_forecast_slice(current_lap=1, window=6, radar_tier=3, radar_eq_lvl=3)
    assert len(slice_boosted) > len(slice_base)
