from typing import List, Tuple
from ..core.driver import Driver
from ..database.db_manager import DatabaseManager, CarAttributes

def load_teams_and_drivers_from_db(db_path: str = "race_game.db") -> List[Tuple[Driver, CarAttributes]]:
    """Loads all 20 drivers and their corresponding CarAttributes from SQLite database."""
    db = DatabaseManager(db_path)
    records = db.get_all_drivers_and_cars()
    
    results: List[Tuple[Driver, CarAttributes]] = []
    for r in records:
        driver = Driver(
            id=r["driver_id"],
            name=r["name"],
            code=r["code"],
            number=r["number"],
            team_name=r["team_name"],
            color_rgb=(r["color_r"], r["color_g"], r["color_b"]),
            is_player=bool(r["is_player"]),
            speed=r["speed"] / 100.0,
            braking=r["braking"] / 100.0,
            cornering=r["cornering"] / 100.0,
            overtaking=r["overtaking"] / 100.0,
            defending=r["defending"] / 100.0,
            tire_management=r["tire_management"] / 100.0,
            consistency=r["consistency"] / 100.0,
            wet_skill=r["wet_skill"] / 100.0
        )
        car_attrs = CarAttributes(
            engine_power=r["engine_power"],
            aero_downforce=r["aero_downforce"],
            braking_efficiency=r["braking_efficiency"],
            tire_preservation=r["tire_preservation"],
            fuel_efficiency=r["fuel_efficiency"],
            reliability=r["reliability"]
        )
        results.append((driver, car_attrs))
    return results

def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    try:
        hex_str = hex_str.lstrip("#")
        if len(hex_str) == 6:
            return (int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))
    except Exception:
        pass
    return (70, 140, 240)

def load_career_teams_and_drivers(career_db, tier: int = 3) -> List[Tuple[Driver, CarAttributes]]:
    """Loads all drivers and car components for the given championship tier from career database."""
    try:
        teams = career_db.get_teams(tier=tier)
        if not teams:
            return load_teams_and_drivers_from_db()
        
        results: List[Tuple[Driver, CarAttributes]] = []
        for team in teams:
            team_id = team["id"]
            team_name = team["name"]
            is_player = bool(team.get("is_player", 0))
            color_rgb = hex_to_rgb(team.get("color_hex", "#4080ff"))
            
            drivers = career_db.get_team_drivers(team_id)
            primary_drivers = [d for d in drivers if not d.get("is_academy_driver", 0)]
            if len(primary_drivers) < 2:
                primary_drivers = drivers[:2]
            
            # Components for car 1 and car 2
            components = career_db.get_team_components(team_id)
            slot_comps = {1: {}, 2: {}}
            for c in components:
                slot = c.get("car_slot", 1)
                cat = c.get("category")
                if slot in slot_comps and cat:
                    slot_comps[slot][cat] = c.get("performance", 85.0)
            
            for slot_idx, drv_row in enumerate(primary_drivers[:2]):
                c_slot = slot_idx + 1
                comps = slot_comps.get(c_slot, {})
                
                # Raw component performance ratings
                brakes_perf = comps.get("BRAKES", 85.0)
                engine_perf = comps.get("ENGINE", 85.0)
                fw_perf = comps.get("FRONT_WING", 85.0)
                rw_perf = comps.get("REAR_WING", 85.0)
                fl_perf = comps.get("FLOOR", 85.0)
                aero_perf = (fw_perf * 0.35 + rw_perf * 0.35 + fl_perf * 0.30)
                susp_perf = comps.get("SUSPENSION", 85.0)
                ers_perf = comps.get("ERS", 85.0)
                
                # Driver skills
                d_code = drv_row["name"][:3].upper() if drv_row.get("name") else f"D{drv_row['id']}"
                pace_val = float(drv_row.get("pace", 75)) / 100.0
                defend_val = float(drv_row.get("defending", 75)) / 100.0
                braking_val = float(drv_row.get("braking", 75)) / 100.0
                tire_val = float(drv_row.get("tire_management", 75)) / 100.0
                cons_val = float(drv_row.get("consistency", 75)) / 100.0
                wet_val = float(drv_row.get("wet_weather", 75)) / 100.0
                # Overtaking skill is driven by pace, defending and aggression
                overtake_val = min(0.99, pace_val * 0.60 + braking_val * 0.40)
                aggr_val = max(0.40, min(0.95, 0.50 + (overtake_val - defend_val) * 0.5 + (braking_val - 0.75) * 0.4))
                
                driver = Driver(
                    id=drv_row["id"],
                    name=drv_row["name"],
                    code=d_code,
                    number=drv_row.get("number", 10 + drv_row["id"]),
                    team_name=team_name,
                    color_rgb=color_rgb,
                    is_player=is_player,
                    speed=pace_val,
                    braking=braking_val,
                    cornering=pace_val,
                    overtaking=overtake_val,
                    defending=defend_val,
                    tire_management=tire_val,
                    consistency=cons_val,
                    wet_skill=wet_val,
                    aggression=aggr_val,
                    is_champion=bool(drv_row.get("is_champion", 0))
                )
                
                # Universal Chassis Boosts (applies to all parts, including spec/locked parts)
                chassis_boost = float(team.get("chassis_perf_boost", 0.0) or 0.0)
                chassis_rel = float(team.get("chassis_rel_boost", 0.0) or 0.0)
                chassis_tire = float(team.get("chassis_tire_preservation_base", 85.0) or 85.0)
                chassis_fuel = float(team.get("chassis_fuel_efficiency_base", 85.0) or 85.0)

                tire_pres = float(susp_perf * 0.5 + chassis_tire * 0.5)
                fuel_eff = float(ers_perf * 0.5 + chassis_fuel * 0.5)

                car_attrs = CarAttributes(
                    engine_power=float(engine_perf + chassis_boost),
                    aero_downforce=float(aero_perf + chassis_boost),
                    braking_efficiency=float(brakes_perf + chassis_boost),
                    tire_preservation=tire_pres,
                    fuel_efficiency=fuel_eff,
                    reliability=min(99.0, 90.0 + chassis_rel)
                )
                results.append((driver, car_attrs))
                
        if len(results) >= 2:
            return results
        return load_teams_and_drivers_from_db()
    except Exception as e:
        print(f"Error loading career teams and drivers: {e}")
        return load_teams_and_drivers_from_db()

def get_default_teams_and_drivers() -> List[Driver]:
    """Fallback helper returning drivers list."""
    pairs = load_teams_and_drivers_from_db()
    return [p[0] for p in pairs]
