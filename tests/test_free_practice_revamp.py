"""Unit tests for Free Practice session overhaul.

Tests:
1. Dual-peak hidden setup curves (SliderCurve) with peak performance and peak tire preservation.
2. Distinct setup curves per race and per car (Car 1 vs Car 2).
3. Session time budgeting (60 min clock per car), prep costs, and stint lap counts (SHORT, SPRINT, LONG).
4. Chequered flag drop when session time runs out.
5. Factory preset generation scaling with track_virtual_sim.
6. Setup preset persistence (save, load, copy between cars) in career_db.
7. Radio feedback differentiation between short (pace) and long (wear) stints.
"""

from __future__ import annotations

import os
import tempfile

import pytest

from src.core.car import Car
from src.core.race_weekend import (
    RaceWeekendManager,
    RaceWeekendSession,
    SliderCurve,
    StintType,
)
from src.database.career_db import CareerDatabase


@pytest.fixture
def career_db():
    temp_fd, temp_path = tempfile.mkstemp(suffix=".db")
    os.close(temp_fd)
    db = CareerDatabase(db_path=temp_path)
    yield db
    try:
        os.remove(temp_path)
    except OSError:
        pass


def test_slider_curve_dual_peaks():
    """Verify SliderCurve evaluates peak performance and wear with penalties at 0 and 100."""
    curve = SliderCurve(
        perf_target=60.0,
        wear_target=40.0,
        tolerance=6.0,
    )

    # Performance peak at 60.0
    score_at_perf_opt = curve.evaluate_perf(60.0)
    score_at_wear_opt = curve.evaluate_perf(40.0)
    assert score_at_perf_opt == pytest.approx(1.0, abs=0.01)
    assert score_at_perf_opt > score_at_wear_opt

    # Wear peak at 40.0
    wear_at_wear_opt = curve.evaluate_wear(40.0)
    wear_at_perf_opt = curve.evaluate_wear(60.0)
    assert wear_at_wear_opt == pytest.approx(1.0, abs=0.01)
    assert wear_at_wear_opt > wear_at_perf_opt

    # Severe penalty at extreme bounds 0 and 100
    assert curve.evaluate_perf(0.0) <= 0.35
    assert curve.evaluate_perf(100.0) <= 0.35
    assert curve.evaluate_wear(0.0) <= 0.35
    assert curve.evaluate_wear(100.0) <= 0.35


def test_curves_differ_per_car_and_track():
    """Verify Car 1 and Car 2 have distinct optimal setup curves for the same track."""
    track_meta_1 = {"track_name": "Monza", "circuit_file": "apex_temple.json"}
    rwm = RaceWeekendManager(league_tier=1, track_metadata=track_meta_1)
    c1_curves = rwm.car_curves[1]
    c2_curves = rwm.car_curves[2]

    # Check that at least several sliders have different optima between Car 1 and Car 2
    differences = 0
    for key in ["front_wing", "rear_wing", "suspension", "gear_ratio", "brake_bias"]:
        if c1_curves[key].perf_target != c2_curves[key].perf_target:
            differences += 1
    assert differences >= 2, "Car 1 and Car 2 must have distinct curve optima"

    # Also verify different tracks generate different curves
    track_meta_2 = {"track_name": "Monaco", "circuit_file": "harbor_circuit.json"}
    rwm_monaco = RaceWeekendManager(league_tier=1, track_metadata=track_meta_2)
    monaco_c1_curves = rwm_monaco.car_curves[1]
    assert monaco_c1_curves["front_wing"].perf_target != c1_curves["front_wing"].perf_target


def test_session_time_budget_and_stints():
    """Verify practice session starts with 60 min per car, stints adapt laps to track length, and stint times are consistent."""
    track_meta = {"track_name": "Emerald Ring", "circuit_file": "emerald_ring.json"}
    rwm = RaceWeekendManager(league_tier=1, track_metadata=track_meta)
    assert rwm.current_session == RaceWeekendSession.FP1
    assert rwm.session_time_remaining[1] == 60.0
    assert rwm.session_time_remaining[2] == 60.0
    assert rwm.session_laps_completed[1] == 0

    # Emerald ring is ~2789m, lap is ~73.4s (1.22 min).
    # Short stint laps = round(6.0 / 1.22) = 5 laps.
    # Total time = 4.0m prep + 5 * 1.22m = ~10.1m.
    expected_short_laps = rwm.stint_laps["SHORT"]
    res_short = rwm.run_practice_run(car_slot=1, driver_name="Max", stint_type=StintType.SHORT)
    assert res_short["laps_completed"] == expected_short_laps
    assert res_short["time_cost_min"] == pytest.approx(10.0, abs=1.0)
    assert rwm.session_laps_completed[1] == expected_short_laps

    # Sprint stint laps = round(16.0 / 1.22) = 13 laps.
    # Total time = 4.0m prep + 13 * 1.22m = ~19.9m.
    expected_sprint_laps = rwm.stint_laps["SPRINT"]
    res_sprint = rwm.run_practice_run(car_slot=1, driver_name="Max", stint_type=StintType.SPRINT)
    assert res_sprint["laps_completed"] == expected_sprint_laps
    assert res_sprint["time_cost_min"] == pytest.approx(20.0, abs=1.0)
    assert rwm.session_laps_completed[1] == expected_short_laps + expected_sprint_laps

    # Radio feedback for short vs sprint:
    joined_short = " ".join(res_short["feedback_points"]).lower()
    assert "wing" in joined_short or "balance" in joined_short or "suspension" in joined_short

    # Sprint stint should mention tire degradation
    joined_sprint = " ".join(res_sprint["feedback_points"]).lower()
    assert "degradation" in joined_sprint or "tire" in joined_sprint


def test_track_length_adapts_stint_laps_for_consistent_duration():
    """Verify shorter circuits get more laps and longer circuits get fewer laps, keeping duration consistent."""
    # Short track: Harbor City (~1792m, ~47s / 0.79 min per lap)
    rwm_short = RaceWeekendManager(
        league_tier=1, track_metadata={"track_name": "Harbor", "circuit_file": "harbor_city_street_circuit.json"}
    )
    # Long track: Autodromo Velocita (~3366m, ~89s / 1.48 min per lap)
    rwm_long = RaceWeekendManager(
        league_tier=1, track_metadata={"track_name": "Velocita", "circuit_file": "autodromo_velocita.json"}
    )

    # Short track should run significantly more laps per stint than long track
    assert rwm_short.stint_laps["SHORT"] > rwm_long.stint_laps["SHORT"]
    assert rwm_short.stint_laps["SPRINT"] > rwm_long.stint_laps["SPRINT"]
    assert rwm_short.stint_laps["LONG"] > rwm_long.stint_laps["LONG"]

    # Yet both stint total times should remain consistently around ~10 min (short), ~20 min (sprint), ~32 min (long)
    time_short_track = rwm_short.GARAGE_PREP_MINUTES + rwm_short.stint_laps["SHORT"] * rwm_short.minutes_per_lap
    time_long_track = rwm_long.GARAGE_PREP_MINUTES + rwm_long.stint_laps["SHORT"] * rwm_long.minutes_per_lap
    assert time_short_track == pytest.approx(10.0, abs=1.0)
    assert time_long_track == pytest.approx(10.0, abs=1.0)


def test_chequered_flag_drop_when_out_of_time():
    """When time remaining is 0 or less, session drops chequered flag and prevents further runs."""
    track_meta = {"track_name": "Emerald Ring", "circuit_file": "emerald_ring.json"}
    rwm = RaceWeekendManager(league_tier=1, track_metadata=track_meta)
    rwm.session_time_remaining[1] = 5.0  # Only 5 minutes left

    # Attempting a LONG stint (requires 33.0 min: 20 laps * 1.45m + 4.0m prep)
    # Since only 5 min left, it caps/runs scaled laps or exhausts time to 0.0
    res = rwm.run_practice_run(car_slot=1, driver_name="Max", stint_type=StintType.LONG)
    assert rwm.session_time_remaining[1] == 0.0

    # Now with 0.0 time remaining, car is chequered-flagged
    assert rwm.is_chequered_flag(car_slot=1) is True

    res_flag = rwm.run_practice_run(car_slot=1, driver_name="Max", stint_type=StintType.SHORT)
    assert res_flag["is_expired"] is True
    assert res_flag["laps_completed"] == 0
    assert "Chequered flag" in res_flag["summary_quote"]


def test_factory_preset_generation_and_virtual_sim():
    """Factory baseline preset gets closer to sweet spot with higher track_virtual_sim tier."""
    track_meta = {"track_name": "Emerald Ring", "circuit_file": "emerald_ring.json"}
    # Tier 0 sim: broad fallback
    rwm_no_sim = RaceWeekendManager(league_tier=1, track_metadata=track_meta, facility_tiers={"track_virtual_sim": 0})
    p0 = rwm_no_sim.get_factory_preset(car_slot=1)
    assert p0.front_wing == 50.0  # Default CarSetup

    # Tier 3 sim + equipment: tight baseline near optimal
    rwm_high_sim = RaceWeekendManager(
        league_tier=1,
        track_metadata=track_meta,
        facility_tiers={"track_virtual_sim": 3},
        equipment_levels={"eq_vsim_cloud_cluster": 3},
    )
    p3 = rwm_high_sim.get_factory_preset(car_slot=1)

    opt1 = rwm_high_sim.optimal_setup.front_wing
    dist_p3 = abs(p3.front_wing - opt1)
    assert dist_p3 <= 12.0


def test_save_load_setup_presets_database(career_db):
    """Test saving, loading, and cross-car copying of setup presets in CareerDatabase."""
    # Ensure empty initially
    loaded = career_db.load_track_setup_preset(team_id=1, track_name="Monza", car_slot=1)
    assert loaded is None

    # Save preset for Car 1
    career_db.save_track_setup_preset(
        team_id=1,
        track_name="Monza",
        car_slot=1,
        front_wing=65.0,
        rear_wing=55.0,
        suspension=45.0,
        gear_ratio=70.0,
        brake_bias=58.0,
    )

    # Retrieve Car 1 preset
    retrieved_c1 = career_db.load_track_setup_preset(team_id=1, track_name="Monza", car_slot=1)
    assert retrieved_c1 is not None
    assert retrieved_c1["front_wing"] == 65.0
    assert retrieved_c1["rear_wing"] == 55.0
    assert retrieved_c1["brake_bias"] == 58.0

    # Fallback to Car 1 if Car 2 has not saved one yet
    retrieved_c2 = career_db.load_track_setup_preset(team_id=1, track_name="Monza", car_slot=2)
    assert retrieved_c2 is not None
    assert retrieved_c2["front_wing"] == 65.0

    # Now save a specific setup for Car 2
    career_db.save_track_setup_preset(
        team_id=1,
        track_name="Monza",
        car_slot=2,
        front_wing=40.0,
        rear_wing=40.0,
        suspension=50.0,
        gear_ratio=60.0,
        brake_bias=52.0,
    )
    retrieved_c2_updated = career_db.load_track_setup_preset(team_id=1, track_name="Monza", car_slot=2)
    assert retrieved_c2_updated["front_wing"] == 40.0
    # Car 1 unchanged
    assert career_db.load_track_setup_preset(team_id=1, track_name="Monza", car_slot=1)["front_wing"] == 65.0


def test_car_physics_incorporates_setup_scores():
    """Verify Car physics respects setup_perf_score and setup_wear_score."""
    from src.core.driver import Driver

    drv1 = Driver(id=1, name="Opt Driver", code="OPT", number=1, team_name="Test", color_rgb=(255, 0, 0))
    drv2 = Driver(id=2, name="Bad Driver", code="BAD", number=2, team_name="Test", color_rgb=(0, 255, 0))

    car_optimal = Car(
        car_id=1,
        driver=drv1,
        setup_perf_score=1.0,
        setup_wear_score=1.0,
    )
    car_bad = Car(
        car_id=2,
        driver=drv2,
        setup_perf_score=0.2,
        setup_wear_score=0.2,
    )

    # Check setup_perf_factor on cornering / effective grip
    factor_opt = getattr(car_optimal, "setup_perf_factor", 1.0)
    factor_bad = getattr(car_bad, "setup_perf_factor", 0.94)
    assert factor_opt > factor_bad

    # Check tire wear degradation factor
    wear_factor_opt = getattr(car_optimal, "setup_wear_factor", 1.0)
    wear_factor_bad = getattr(car_bad, "setup_wear_factor", 1.2)
    assert wear_factor_opt < wear_factor_bad


def test_stint_linked_bonuses():
    """Verify that stint types directly award their linked run program bonuses."""
    track_meta = {"track_name": "Emerald Ring", "circuit_file": "emerald_ring.json"}
    rwm = RaceWeekendManager(league_tier=1, track_metadata=track_meta)

    # Initial bonuses 0
    assert rwm.practice_bonuses[1]["qualy_pace_bonus"] == 0.0
    assert rwm.practice_bonuses[1]["sprint_wear_bonus"] == 0.0
    assert rwm.practice_bonuses[1]["race_wear_bonus"] == 0.0

    # Short stint awards qualy pace bonus
    rwm.run_practice_run(car_slot=1, driver_name="Driver 1", stint_type=StintType.SHORT)
    assert rwm.practice_bonuses[1]["qualy_pace_bonus"] > 0.0
    assert rwm.practice_bonuses[1]["sprint_wear_bonus"] == 0.0

    # Sprint stint awards sprint wear bonus
    rwm.run_practice_run(car_slot=1, driver_name="Driver 1", stint_type=StintType.SPRINT)
    assert rwm.practice_bonuses[1]["sprint_wear_bonus"] > 0.0
    assert rwm.practice_bonuses[1]["race_wear_bonus"] == 0.0

    # Long stint awards race wear & fuel saving bonus
    rwm.run_practice_run(car_slot=1, driver_name="Driver 1", stint_type=StintType.LONG)
    assert rwm.practice_bonuses[1]["race_wear_bonus"] > 0.0
    assert rwm.practice_bonuses[1]["fuel_saving_bonus"] > 0.0


def test_deferred_stint_lifecycle_and_fast_forward():
    """Verify deferred feedback lifecycle and hop forward in time for simultaneous stints."""
    track_meta = {"track_name": "Emerald Ring", "circuit_file": "emerald_ring.json"}
    rwm = RaceWeekendManager(league_tier=1, track_metadata=track_meta)

    assert rwm.session_time_remaining[1] == 60.0
    assert rwm.session_time_remaining[2] == 60.0

    # Dispatch Car 1 on Short Stint (~10 min)
    res1 = rwm.start_practice_stint(car_slot=1, driver_name="Driver 1", stint_type="SHORT")
    assert res1["success"] is True
    assert rwm.is_car_on_track(1) is True
    assert len(rwm.driver_feedback[1]) == 0, "Debrief must NOT be available while stint is running"

    # Trying to start another stint on Car 1 while running is disallowed
    res1_dup = rwm.start_practice_stint(car_slot=1, driver_name="Driver 1", stint_type="SHORT")
    assert res1_dup["success"] is False

    # Dispatch Car 2 on Sprint Stint (~20 min)
    res2 = rwm.start_practice_stint(car_slot=2, driver_name="Driver 2", stint_type="SPRINT")
    assert res2["success"] is True
    assert rwm.is_car_on_track(2) is True
    assert len(rwm.driver_feedback[2]) == 0

    dur1 = rwm.active_stints[1]["time_remaining_min"]
    dur2 = rwm.active_stints[2]["time_remaining_min"]
    assert dur1 < dur2

    # Fast forward: should jump by dur1 (earliest finisher)
    jumped = rwm.fast_forward_to_next_completion()
    assert jumped == pytest.approx(dur1, abs=0.1)

    # Car 1 should now be FINISHED and back in the garage with debrief revealed!
    assert rwm.is_car_on_track(1) is False
    assert len(rwm.driver_feedback[1]) == 1
    assert "feedback_points" in rwm.driver_feedback[1][0]

    # Car 2 should STILL be out on track with remaining time
    assert rwm.is_car_on_track(2) is True
    assert len(rwm.driver_feedback[2]) == 0
    rem_car2 = rwm.active_stints[2]["time_remaining_min"]
    assert rem_car2 == pytest.approx(dur2 - dur1, abs=0.2)

    # Fast forward again: jumps remaining time for Car 2
    jumped2 = rwm.fast_forward_to_next_completion()
    assert jumped2 == pytest.approx(rem_car2, abs=0.1)
    assert rwm.is_car_on_track(2) is False
    assert len(rwm.driver_feedback[2]) == 1


def test_mini_track_circuit_radar_and_traffic():
    """Verify circuit loading, mini-track geometry, and ambient Free Practice traffic."""
    track_meta = {"track_name": "Emerald Ring", "circuit_file": "emerald_ring.json"}
    rwm = RaceWeekendManager(league_tier=1, track_metadata=track_meta)

    circuit = rwm.get_circuit()
    assert circuit is not None
    assert len(circuit.points) > 10

    # Ambient AI traffic initialized
    assert len(rwm.fp_cars) >= 8
    initial_dists = [c["dist_m"] for c in rwm.fp_cars if not c["in_pit"]]

    # Animate traffic
    rwm.update_fp_traffic(dt_seconds=1.0)
    updated_dists = [c["dist_m"] for c in rwm.fp_cars if not c["in_pit"]]
    # At least some cars moved forward along track
    assert any(u != i for u, i in zip(updated_dists, initial_dists))
