import os
from typing import Any, Dict, List, Optional

import pygame

from ..database.career_db import CareerDatabase
from ..database.db_manager import DatabaseManager
from ..ui.theme import UITheme


class DatabaseEditor:
    """
    Admin Database Editor for inspecting and modifying:
    - Teams (Name, colors)
    - Cars (Engine Power, Aero Downforce, Braking, Tire Preservation, Fuel Efficiency, Reliability)
    - Drivers (Speed, Braking, Cornering, Overtaking, Defending, Tire Management, Consistency, Wet Skill)
    Supports both Exhibition Database ('race_game.db') and Career Database ('career.db').
    """

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        exhibition_db_path: str = "race_game.db",
        career_db_path: str = "career.db",
    ):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.db_mode: str = "EXHIBITION"
        self.exhibition_db = DatabaseManager(exhibition_db_path)
        self.career_db = CareerDatabase(career_db_path)

        self.selected_team_idx: int = 0
        self.selected_driver_idx: int = 0
        self.selected_round_idx: int = 0
        self.selected_calendar_tier: int = 3
        self.selected_facility_idx: int = 0
        self.active_subtab: str = "CAR"

        self.teams: List[Dict[str, Any]] = []
        self.drivers: List[Dict[str, Any]] = []
        self.car_attrs: Dict[str, float] = {}
        self.driver_stats: Dict[str, float] = {}
        self.calendar_rounds: List[Dict[str, Any]] = []
        self.facilities: List[Dict[str, Any]] = []
        self.all_nodes: List[Dict[str, Any]] = []
        self.available_circuit_files: List[str] = []

        # Factory Custom Node Creator / Editor State
        self.selected_node_idx: int = 0
        self.node_scroll_y: int = 0
        self.team_scroll_y: int = 0
        self.cal_scroll_y: int = 0
        self.show_node_modal: bool = False
        self.modal_mode: str = "CREATE"  # "CREATE" or "EDIT"
        self.edit_node_id: str = ""
        self.edit_node_dept: str = "ENGINEERING"
        self.edit_node_name: str = ""
        self.edit_node_desc: str = ""
        self.edit_node_parent_id: Optional[str] = None
        self.edit_node_tier: int = 1
        self.edit_node_cost_m: float = 12.0
        self.edit_node_upkeep_k: float = 300.0
        self.active_input: Optional[str] = None

        self.edit_team_name: str = ""
        self.edit_driver_name: str = ""
        self.edit_driver_number: int = 1
        self.status_msg: str = "Database & Career Modding Suite Ready."
        self.status_timer: float = 0.0

        self._init_fonts()
        self.reload_data()

    def _init_fonts(self):
        self.font_title = UITheme.get_font(13, bold=True)
        self.font_card_title = UITheme.get_font(12, bold=True)
        self.font_section = UITheme.get_font(11, bold=True)
        self.font_body = UITheme.get_font(10, bold=False)
        self.font_bold = UITheme.get_font(10, bold=True)
        self.font_badge = UITheme.get_font(9, bold=True)
        self.font_val = UITheme.get_font(11, bold=True)

    def resize(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self._init_fonts()

    def reload_data(self):
        # Scan available track JSON files
        if os.path.exists("tracks"):
            self.available_circuit_files = [f for f in os.listdir("tracks") if f.endswith(".json")]
        else:
            self.available_circuit_files = ["emerald_ring.json"]

        # Calendar rounds
        self.calendar_rounds = self.career_db.get_calendar_rounds(self.selected_calendar_tier)
        if self.selected_round_idx >= len(self.calendar_rounds):
            self.selected_round_idx = 0

        # Master Facility Node Definitions
        self.all_nodes = self.career_db.get_all_facility_nodes()
        if self.selected_node_idx >= len(self.all_nodes):
            self.selected_node_idx = 0

        if self.db_mode == "EXHIBITION":
            self.teams = self.exhibition_db.get_teams()
            if not self.teams:
                self.exhibition_db.reset_and_reseed()
                self.teams = self.exhibition_db.get_teams()
        else:
            self.teams = self.career_db.get_teams()

        if self.selected_team_idx >= len(self.teams):
            self.selected_team_idx = 0

        self._load_selected_team_data()

    def _load_selected_team_data(self):
        if not self.teams:
            return

        team = self.teams[self.selected_team_idx]
        team_id = team["id"]
        self.edit_team_name = team["name"]

        if self.db_mode == "EXHIBITION":
            raw_car = self.exhibition_db.get_car_attributes(team_id)
            if raw_car:
                self.car_attrs = {
                    "engine_power": float(raw_car["engine_power"]),
                    "aero_downforce": float(raw_car["aero_downforce"]),
                    "braking_efficiency": float(raw_car["braking_efficiency"]),
                    "tire_preservation": float(raw_car["tire_preservation"]),
                    "fuel_efficiency": float(raw_car["fuel_efficiency"]),
                    "reliability": float(raw_car["reliability"]),
                }
            self.drivers = self.exhibition_db.get_drivers(team_id)
            self.facilities = []
        else:
            self.drivers = self.career_db.get_team_drivers(team_id)
            tier_val = team.get("tier", 3)
            self.car_attrs = {
                "engine_power": 80.0 + (3 - tier_val) * 8.0,
                "aero_downforce": 80.0 + (3 - tier_val) * 8.0,
                "braking_efficiency": 80.0 + (3 - tier_val) * 7.0,
                "tire_preservation": 82.0,
                "fuel_efficiency": 82.0,
                "reliability": 88.0,
            }
            self.facilities = self.career_db.get_team_facilities(team_id)
            self.all_nodes = self.career_db.get_all_facility_nodes()
            if self.selected_facility_idx >= len(self.facilities):
                self.selected_facility_idx = 0

        if self.selected_driver_idx >= len(self.drivers):
            self.selected_driver_idx = 0

        self._load_selected_driver_data()

    def _load_selected_driver_data(self):
        if not self.drivers:
            self.driver_stats = {}
            return

        d = self.drivers[self.selected_driver_idx]
        self.edit_driver_name = d["name"]
        self.edit_driver_number = d.get("number", 1)

        if self.db_mode == "EXHIBITION":
            self.driver_stats = {
                "speed": float(d.get("speed", 85.0)),
                "braking": float(d.get("braking", 85.0)),
                "cornering": float(d.get("cornering", 85.0)),
                "overtaking": float(d.get("overtaking", 80.0)),
                "defending": float(d.get("defending", 80.0)),
                "tire_management": float(d.get("tire_management", 80.0)),
                "consistency": float(d.get("consistency", 85.0)),
                "wet_skill": float(d.get("wet_skill", 80.0)),
            }
        else:
            self.driver_stats = {
                "pace": float(d.get("pace", 75)),
                "braking": float(d.get("braking", 75)),
                "consistency": float(d.get("consistency", 75)),
                "tire_management": float(d.get("tire_management", 75)),
                "defending": float(d.get("defending", 75)),
                "fuel_efficiency": float(d.get("fuel_efficiency", 75)),
                "wet_weather": float(d.get("wet_weather", 75)),
            }

    def handle_event(self, event: pygame.event.Event):
        # 1. Handle Modal Keydown & Clicks if Modal Open
        if self.show_node_modal:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.show_node_modal = False
                    self.active_input = None
                    return
                elif event.key == pygame.K_TAB:
                    # Cycle active input
                    inputs = ["NAME", "DESC"] if self.modal_mode == "EDIT" else ["ID", "NAME", "DESC"]
                    if self.active_input in inputs:
                        idx = (inputs.index(self.active_input) + 1) % len(inputs)
                        self.active_input = inputs[idx]
                    else:
                        self.active_input = inputs[0]
                    return
                elif event.key == pygame.K_BACKSPACE and self.active_input:
                    if self.active_input == "ID":
                        self.edit_node_id = self.edit_node_id[:-1]
                    elif self.active_input == "NAME":
                        self.edit_node_name = self.edit_node_name[:-1]
                    elif self.active_input == "DESC":
                        self.edit_node_desc = self.edit_node_desc[:-1]
                    return
                elif event.unicode and event.unicode.isprintable() and self.active_input:
                    if self.active_input == "ID" and len(self.edit_node_id) < 28:
                        ch = event.unicode.lower().replace(" ", "_")
                        if ch.isalnum() or ch == "_":
                            self.edit_node_id += ch
                    elif self.active_input == "NAME" and len(self.edit_node_name) < 32:
                        self.edit_node_name += event.unicode
                    elif self.active_input == "DESC" and len(self.edit_node_desc) < 64:
                        self.edit_node_desc += event.unicode
                    return

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_node_modal_clicks(event.pos[0], event.pos[1])
                return
            return

        # 2. Mouse Wheel Scrolling
        if event.type == pygame.MOUSEWHEEL:
            if self.active_subtab == "FACTORY":
                self.node_scroll_y = max(0, min(max(0, len(self.all_nodes) - 10), self.node_scroll_y - event.y))
                return
            elif self.active_subtab in ("CAR", "DRIVER"):
                self.team_scroll_y = max(0, min(max(0, len(self.teams) - 10), self.team_scroll_y - event.y))
                return
            elif self.active_subtab == "CALENDAR":
                self.cal_scroll_y = max(0, min(max(0, len(self.calendar_rounds) - 12), self.cal_scroll_y - event.y))
                return

        # 3. Mouse Button Down Handling
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            btn_exh = pygame.Rect(20, 52, 170, 26)
            btn_car = pygame.Rect(195, 52, 170, 26)
            if btn_exh.collidepoint(mx, my) and self.db_mode != "EXHIBITION":
                self.db_mode = "EXHIBITION"
                self.selected_team_idx = 0
                self.team_scroll_y = 0
                self.reload_data()
                self.set_status("Switched to Exhibition Database (race_game.db)")
                return
            elif btn_car.collidepoint(mx, my) and self.db_mode != "CAREER":
                self.db_mode = "CAREER"
                self.selected_team_idx = 0
                self.team_scroll_y = 0
                self.reload_data()
                self.set_status("Switched to Career Database (career.db)")
                return

            tab_car = pygame.Rect(380, 52, 100, 26)
            tab_drv = pygame.Rect(485, 52, 110, 26)
            tab_cal = pygame.Rect(600, 52, 140, 26)
            tab_fac = pygame.Rect(745, 52, 135, 26)

            if tab_car.collidepoint(mx, my):
                self.active_subtab = "CAR"
                return
            elif tab_drv.collidepoint(mx, my):
                self.active_subtab = "DRIVER"
                return
            elif tab_cal.collidepoint(mx, my):
                self.active_subtab = "CALENDAR"
                self.calendar_rounds = self.career_db.get_calendar_rounds()
                return
            elif tab_fac.collidepoint(mx, my):
                self.active_subtab = "FACTORY"
                if self.db_mode != "CAREER":
                    self.db_mode = "CAREER"
                    self.reload_data()
                return

            if self.active_subtab == "CALENDAR":
                self._handle_calendar_clicks(mx, my)
                return
            elif self.active_subtab == "FACTORY":
                self._handle_factory_clicks(mx, my)
                return

            team_list_rect = pygame.Rect(20, 90, 345, self.screen_height - 150)
            if team_list_rect.collidepoint(mx, my):
                item_h = 36
                clicked_idx = self.team_scroll_y + (my - (team_list_rect.y + 30)) // item_h
                if 0 <= clicked_idx < len(self.teams):
                    self.selected_team_idx = clicked_idx
                    self._load_selected_team_data()
                    return

            if self.active_subtab == "DRIVER" and self.drivers:
                for d_idx, d in enumerate(self.drivers[:4]):
                    d_btn = pygame.Rect(390 + d_idx * 160, 90, 150, 30)
                    if d_btn.collidepoint(mx, my):
                        self.selected_driver_idx = d_idx
                        self._load_selected_driver_data()
                        return

            cur_attrs = self.car_attrs if self.active_subtab == "CAR" else self.driver_stats
            keys = list(cur_attrs.keys())
            start_y = 140
            for idx, key in enumerate(keys):
                y = start_y + idx * 42
                btn_minus = pygame.Rect(self.screen_width - 240, y, 32, 24)
                btn_plus = pygame.Rect(self.screen_width - 200, y, 32, 24)
                btn_min = pygame.Rect(self.screen_width - 160, y, 36, 24)
                btn_max = pygame.Rect(self.screen_width - 116, y, 36, 24)

                if btn_minus.collidepoint(mx, my):
                    cur_attrs[key] = max(10.0, cur_attrs[key] - 2.0)
                    return
                elif btn_plus.collidepoint(mx, my):
                    cur_attrs[key] = min(100.0, cur_attrs[key] + 2.0)
                    return
                elif btn_min.collidepoint(mx, my):
                    cur_attrs[key] = 50.0
                    return
                elif btn_max.collidepoint(mx, my):
                    cur_attrs[key] = 99.0
                    return

            btn_save = pygame.Rect(self.screen_width - 320, self.screen_height - 50, 140, 34)
            btn_reset = pygame.Rect(self.screen_width - 160, self.screen_height - 50, 140, 34)

            if btn_save.collidepoint(mx, my):
                self.save_changes()
                return
            elif btn_reset.collidepoint(mx, my):
                if self.db_mode == "EXHIBITION":
                    self.exhibition_db.reset_and_reseed()
                    self.reload_data()
                    self.set_status("Exhibition database reseeded to original defaults.")
                else:
                    self.set_status("Career database cannot be reseeded (affects ongoing career).")
                return

    def _handle_calendar_clicks(self, mx: int, my: int):
        # Tier selection chips (y = 58)
        for t in range(1, 6):
            t_rect = pygame.Rect(20 + (t - 1) * 74, 58, 68, 24)
            if t_rect.collidepoint(mx, my):
                self.selected_calendar_tier = t
                self.selected_round_idx = 0
                self.calendar_rounds = self.career_db.get_calendar_rounds(self.selected_calendar_tier)
                return

        # Round selection list
        cal_list_rect = pygame.Rect(20, 90, 360, self.screen_height - 150)
        if cal_list_rect.collidepoint(mx, my):
            item_h = 30 if len(self.calendar_rounds) > 12 else 35
            clicked_idx = self.cal_scroll_y + (my - (cal_list_rect.y + 34)) // item_h
            if 0 <= clicked_idx < len(self.calendar_rounds):
                self.selected_round_idx = clicked_idx
                return

        # Actions on selected round
        if self.calendar_rounds and self.selected_round_idx < len(self.calendar_rounds):
            sel_r = self.calendar_rounds[self.selected_round_idx]
            rnd_num = sel_r["round"]
            cur_char = sel_r.get("characteristic", "BALANCED")

            # Circuit file selector chips
            c_y = 165
            for c_idx, c_file in enumerate(self.available_circuit_files[:8]):
                c_rect = pygame.Rect(400 + (c_idx % 2) * 240, c_y + (c_idx // 2) * 34, 230, 26)
                if c_rect.collidepoint(mx, my):
                    track_title = c_file.replace(".json", "").replace("_", " ").title() + " GP"
                    self.career_db.update_calendar_round(
                        rnd_num,
                        track_title,
                        c_file,
                        sel_r["total_laps"],
                        sel_r["weather_profile"],
                        tier=self.selected_calendar_tier,
                        characteristic=cur_char,
                    )
                    self.calendar_rounds = self.career_db.get_calendar_rounds(self.selected_calendar_tier)
                    self.set_status(f"Round {rnd_num} circuit set to {c_file}!")
                    return

            # Characteristic toggle chips
            for c_idx, char_name in enumerate(["BALANCED", "SPEED", "BRAKES", "AERO"]):
                char_btn = pygame.Rect(400 + c_idx * 96, 250, 88, 26)
                if char_btn.collidepoint(mx, my):
                    self.career_db.update_calendar_round(
                        rnd_num,
                        sel_r["track_name"],
                        sel_r["circuit_file"],
                        sel_r["total_laps"],
                        sel_r["weather_profile"],
                        tier=self.selected_calendar_tier,
                        characteristic=char_name,
                    )
                    self.calendar_rounds = self.career_db.get_calendar_rounds(self.selected_calendar_tier)
                    self.set_status(f"Round {rnd_num} characteristic set to {char_name}!")
                    return

            # Weather toggle chip
            w_rect = pygame.Rect(400, 315, 150, 28)
            if w_rect.collidepoint(mx, my):
                weathers = ["DYNAMIC", "SUNNY", "RAIN"]
                cur_w = sel_r.get("weather_profile", "DYNAMIC")
                next_w = weathers[(weathers.index(cur_w) + 1) % len(weathers)] if cur_w in weathers else "DYNAMIC"
                self.career_db.update_calendar_round(
                    rnd_num,
                    sel_r["track_name"],
                    sel_r["circuit_file"],
                    sel_r["total_laps"],
                    next_w,
                    tier=self.selected_calendar_tier,
                    characteristic=cur_char,
                )
                self.calendar_rounds = self.career_db.get_calendar_rounds(self.selected_calendar_tier)
                self.set_status(f"Round {rnd_num} weather set to {next_w}!")
                return

            # Lap count adjustment
            btn_laps_minus = pygame.Rect(400, 370, 34, 26)
            btn_laps_plus = pygame.Rect(440, 370, 34, 26)
            if btn_laps_minus.collidepoint(mx, my):
                new_laps = max(5, sel_r["total_laps"] - 2)
                self.career_db.update_calendar_round(
                    rnd_num,
                    sel_r["track_name"],
                    sel_r["circuit_file"],
                    new_laps,
                    sel_r["weather_profile"],
                    tier=self.selected_calendar_tier,
                    characteristic=cur_char,
                )
                self.calendar_rounds = self.career_db.get_calendar_rounds(self.selected_calendar_tier)
                return
            elif btn_laps_plus.collidepoint(mx, my):
                new_laps = min(60, sel_r["total_laps"] + 2)
                self.career_db.update_calendar_round(
                    rnd_num,
                    sel_r["track_name"],
                    sel_r["circuit_file"],
                    new_laps,
                    sel_r["weather_profile"],
                    tier=self.selected_calendar_tier,
                    characteristic=cur_char,
                )
                self.calendar_rounds = self.career_db.get_calendar_rounds(self.selected_calendar_tier)
                return

            # Delete Round button
            btn_del = pygame.Rect(self.screen_width - 200, 96, 170, 28)
            if btn_del.collidepoint(mx, my) and len(self.calendar_rounds) > 1:
                self.career_db.delete_calendar_round(rnd_num, tier=self.selected_calendar_tier)
                self.calendar_rounds = self.career_db.get_calendar_rounds(self.selected_calendar_tier)
                if self.selected_round_idx >= len(self.calendar_rounds):
                    self.selected_round_idx = max(0, len(self.calendar_rounds) - 1)
                self.set_status(f"Deleted round #{rnd_num}. Calendar re-sequenced.")
                return

        # Add Round button
        btn_add = pygame.Rect(self.screen_width - 240, self.screen_height - 50, 220, 34)
        if btn_add.collidepoint(mx, my):
            first_track = self.available_circuit_files[0] if self.available_circuit_files else "emerald_ring.json"
            t_name = first_track.replace(".json", "").replace("_", " ").title() + " Super Prix"
            new_rnd = self.career_db.add_calendar_round(
                t_name, first_track, 15, "DYNAMIC", tier=self.selected_calendar_tier
            )
            self.calendar_rounds = self.career_db.get_calendar_rounds(self.selected_calendar_tier)
            self.selected_round_idx = len(self.calendar_rounds) - 1
            self.set_status(f"Added Round {new_rnd} ({t_name}) to Season Calendar!")

    def _handle_factory_clicks(self, mx: int, my: int):
        team = self.teams[self.selected_team_idx]
        team_id = team["id"]

        # 1. Left team selector column
        team_list_rect = pygame.Rect(20, 90, 240, self.screen_height - 150)
        if team_list_rect.collidepoint(mx, my):
            item_h = 36
            clicked_idx = (my - (team_list_rect.y + 32)) // item_h
            if 0 <= clicked_idx < min(len(self.teams), 14):
                self.selected_team_idx = clicked_idx
                self._load_selected_team_data()
                return

        # 2. Right Panel Buttons
        # Top-right "+ ADD CUSTOM NODE" button
        btn_add_node = pygame.Rect(self.screen_width - 190, 96, 170, 26)
        if btn_add_node.collidepoint(mx, my):
            self.modal_mode = "CREATE"
            self.edit_node_id = f"custom_node_{len(self.all_nodes) + 1}"
            self.edit_node_dept = "ENGINEERING"
            self.edit_node_name = "Advanced Aerodynamics Rig"
            self.edit_node_desc = "Custom modded facility testing wing profiles"
            self.edit_node_parent_id = "eng_workshop"
            self.edit_node_tier = 1
            self.edit_node_cost_m = 12.0
            self.edit_node_upkeep_k = 300.0
            self.active_input = "NAME"
            self.show_node_modal = True
            return

        # Facility rows clicks
        fac_rect = pygame.Rect(270, 90, self.screen_width - 290, self.screen_height - 150)
        if fac_rect.collidepoint(mx, my):
            item_h = 38
            visible_count = min(len(self.all_nodes) - self.node_scroll_y, 11)
            # Map team facilities by node_id
            team_fac_map = {f["id"]: f for f in self.facilities}

            for v_idx in range(visible_count):
                actual_idx = self.node_scroll_y + v_idx
                if actual_idx >= len(self.all_nodes):
                    break
                node_item = self.all_nodes[actual_idx]
                n_id = node_item["id"]
                tf = team_fac_map.get(n_id, {})

                row_y = fac_rect.y + 38 + v_idx * item_h
                btn_unlock = pygame.Rect(self.screen_width - 295, row_y + 6, 75, 24)
                btn_tier = pygame.Rect(self.screen_width - 215, row_y + 6, 75, 24)
                btn_edit = pygame.Rect(self.screen_width - 135, row_y + 6, 50, 24)
                btn_del = pygame.Rect(self.screen_width - 80, row_y + 6, 45, 24)

                if btn_unlock.collidepoint(mx, my):
                    new_unlocked = not bool(tf.get("is_unlocked", 0))
                    cur_tier = max(1, tf.get("current_tier", 1)) if new_unlocked else 0
                    self.career_db.set_team_facility_tier(team_id, n_id, cur_tier, new_unlocked)
                    self.facilities = self.career_db.get_team_facilities(team_id)
                    self.set_status(f"Toggled {node_item['name']} unlock state for {team['name']}.")
                    return

                elif btn_tier.collidepoint(mx, my):
                    max_t = node_item.get("max_tier", 3)
                    cur_t = tf.get("current_tier", 0)
                    next_t = (cur_t % max_t) + 1
                    self.career_db.set_team_facility_tier(team_id, n_id, next_t, True)
                    self.facilities = self.career_db.get_team_facilities(team_id)
                    self.set_status(f"Set {node_item['name']} to Level {next_t} for {team['name']}.")
                    return

                elif btn_edit.collidepoint(mx, my):
                    self.modal_mode = "EDIT"
                    self.edit_node_id = node_item["id"]
                    self.edit_node_dept = node_item.get("department", "ENGINEERING")
                    self.edit_node_name = node_item.get("name", "")
                    self.edit_node_desc = node_item.get("description", "")
                    self.edit_node_parent_id = node_item.get("parent_id")
                    self.edit_node_cost_m = float(node_item.get("base_cost", 10000000.0)) / 1000000.0
                    self.edit_node_upkeep_k = float(node_item.get("base_upkeep", 250000.0)) / 1000.0
                    self.active_input = "NAME"
                    self.show_node_modal = True
                    return

                elif btn_del.collidepoint(mx, my):
                    # Delete node from master tech tree
                    if len(self.all_nodes) > 1:
                        self.career_db.delete_facility_node(n_id)
                        self.all_nodes = self.career_db.get_all_facility_nodes()
                        self.facilities = self.career_db.get_team_facilities(team_id)
                        self.set_status(f"Removed facility node '{node_item['name']}' from tech tree.")
                        return

    def _handle_node_modal_clicks(self, mx: int, my: int):
        modal_w = 580
        modal_h = 420
        modal_rect = pygame.Rect(
            (self.screen_width - modal_w) // 2, (self.screen_height - modal_h) // 2, modal_w, modal_h
        )

        # Close button or click outside
        btn_close = pygame.Rect(modal_rect.right - 34, modal_rect.y + 10, 24, 24)
        if btn_close.collidepoint(mx, my) or not modal_rect.collidepoint(mx, my):
            self.show_node_modal = False
            self.active_input = None
            return

        # Input fields clicks
        f_y = modal_rect.y + 55
        if self.modal_mode == "CREATE":
            id_rect = pygame.Rect(modal_rect.x + 160, f_y, 380, 26)
            if id_rect.collidepoint(mx, my):
                self.active_input = "ID"
                return

        name_rect = pygame.Rect(modal_rect.x + 160, f_y + 36, 380, 26)
        if name_rect.collidepoint(mx, my):
            self.active_input = "NAME"
            return

        desc_rect = pygame.Rect(modal_rect.x + 160, f_y + 72, 380, 26)
        if desc_rect.collidepoint(mx, my):
            self.active_input = "DESC"
            return

        # Department Cycle
        btn_dept = pygame.Rect(modal_rect.x + 160, f_y + 108, 180, 26)
        if btn_dept.collidepoint(mx, my):
            depts = [
                "ENGINEERING",
                "MANUFACTURING",
                "TESTING",
                "POWERTRAIN",
                "COMMERCIAL",
                "HR",
                "TRACKSIDE",
                "DRIVER_PERF",
            ]
            cur_idx = depts.index(self.edit_node_dept) if self.edit_node_dept in depts else 0
            self.edit_node_dept = depts[(cur_idx + 1) % len(depts)]
            return

        # Parent Dependency Node Cycle
        btn_parent = pygame.Rect(modal_rect.x + 160, f_y + 144, 220, 26)
        if btn_parent.collidepoint(mx, my):
            candidate_parents = [None] + [n["id"] for n in self.all_nodes if n["id"] != self.edit_node_id][:15]
            cur_p_idx = (
                candidate_parents.index(self.edit_node_parent_id)
                if self.edit_node_parent_id in candidate_parents
                else 0
            )
            self.edit_node_parent_id = candidate_parents[(cur_p_idx + 1) % len(candidate_parents)]
            return

        # Cost adjustment [-] [+]
        btn_cost_m = pygame.Rect(modal_rect.x + 160, f_y + 180, 30, 24)
        btn_cost_p = pygame.Rect(modal_rect.x + 200, f_y + 180, 30, 24)
        if btn_cost_m.collidepoint(mx, my):
            self.edit_node_cost_m = max(1.0, round(self.edit_node_cost_m - 2.0, 1))
            return
        elif btn_cost_p.collidepoint(mx, my):
            self.edit_node_cost_m = min(150.0, round(self.edit_node_cost_m + 2.0, 1))
            return

        # Upkeep adjustment [-] [+]
        btn_upk_m = pygame.Rect(modal_rect.x + 160, f_y + 216, 30, 24)
        btn_upk_p = pygame.Rect(modal_rect.x + 200, f_y + 216, 30, 24)
        if btn_upk_m.collidepoint(mx, my):
            self.edit_node_upkeep_k = max(20.0, round(self.edit_node_upkeep_k - 40.0, 0))
            return
        elif btn_upk_p.collidepoint(mx, my):
            self.edit_node_upkeep_k = min(3000.0, round(self.edit_node_upkeep_k + 40.0, 0))
            return

        # Confirm Save / Create button
        btn_confirm = pygame.Rect(modal_rect.x + 160, modal_rect.bottom - 50, 260, 36)
        if btn_confirm.collidepoint(mx, my):
            clean_name = self.edit_node_name.strip() or "Custom Facility"
            clean_desc = self.edit_node_desc.strip() or "Modded team facility node"
            clean_id = self.edit_node_id.strip() or f"custom_{len(self.all_nodes) + 1}"
            cost_val = self.edit_node_cost_m * 1000000.0
            upkeep_val = self.edit_node_upkeep_k * 1000.0

            if self.modal_mode == "CREATE":
                self.career_db.create_facility_node(
                    node_id=clean_id,
                    department=self.edit_node_dept,
                    name=clean_name,
                    description=clean_desc,
                    parent_id=self.edit_node_parent_id,
                    tier=self.edit_node_tier,
                    max_tier=3,
                    base_cost=cost_val,
                    base_upkeep=upkeep_val,
                    staff_capacity=8,
                    unlock_league_tier=3,
                )
                self.set_status(f"Created custom node '{clean_name}' in {self.edit_node_dept}!")
            else:
                self.career_db.update_facility_node(
                    node_id=clean_id,
                    department=self.edit_node_dept,
                    name=clean_name,
                    description=clean_desc,
                    parent_id=self.edit_node_parent_id,
                    base_cost=cost_val,
                    base_upkeep=upkeep_val,
                )
                self.set_status(f"Updated node '{clean_name}' definitions!")

            self.all_nodes = self.career_db.get_all_facility_nodes()
            team = self.teams[self.selected_team_idx]
            self.facilities = self.career_db.get_team_facilities(team["id"])
            self.show_node_modal = False
            self.active_input = None
            return

    def save_changes(self):
        if not self.teams:
            return

        team = self.teams[self.selected_team_idx]
        team_id = team["id"]

        if self.db_mode == "EXHIBITION":
            self.exhibition_db.update_car_attributes(team_id, self.car_attrs)
            if self.drivers and self.selected_driver_idx < len(self.drivers):
                d = self.drivers[self.selected_driver_idx]
                self.exhibition_db.update_driver_attributes(
                    d["id"], d["name"], d.get("code", "DRV"), d.get("number", 1), self.driver_stats
                )
            self.set_status(f"Saved changes for {team['name']} in race_game.db!")
        else:
            if self.drivers and self.selected_driver_idx < len(self.drivers):
                d = self.drivers[self.selected_driver_idx]
                self.career_db.update_driver_stats(d["id"], d["name"], d.get("number", 1), self.driver_stats)
            self.set_status(f"Updated career driver stats for {team['name']}!")

    def set_status(self, msg: str):
        self.status_msg = msg
        self.status_timer = 4.0

    def update(self, dt: float):
        if self.status_timer > 0:
            self.status_timer -= dt

    def render(self, surface: pygame.Surface):
        btn_exh = pygame.Rect(20, 52, 170, 26)
        btn_car = pygame.Rect(195, 52, 170, 26)
        UITheme.draw_button(
            surface, btn_exh, "EXHIBITION (RACE_GAME.DB)", self.font_badge, is_active=(self.db_mode == "EXHIBITION")
        )
        UITheme.draw_button(surface, btn_car, "CAREER DATABASE", self.font_badge, is_active=(self.db_mode == "CAREER"))

        tab_car = pygame.Rect(380, 52, 100, 26)
        tab_drv = pygame.Rect(485, 52, 110, 26)
        tab_cal = pygame.Rect(600, 52, 140, 26)
        tab_fac = pygame.Rect(745, 52, 135, 26)
        UITheme.draw_button(surface, tab_car, "CAR SPECS", self.font_badge, is_active=(self.active_subtab == "CAR"))
        UITheme.draw_button(
            surface, tab_drv, "DRIVER SKILLS", self.font_badge, is_active=(self.active_subtab == "DRIVER")
        )
        UITheme.draw_button(
            surface, tab_cal, "CALENDAR / TRACKS", self.font_badge, is_active=(self.active_subtab == "CALENDAR")
        )
        UITheme.draw_button(
            surface, tab_fac, "FACTORY LAYOUT", self.font_badge, is_active=(self.active_subtab == "FACTORY")
        )

        if self.active_subtab == "CALENDAR":
            self._render_calendar_tab(surface)
            self._render_footer(surface, show_save_buttons=False)
            return
        elif self.active_subtab == "FACTORY":
            self._render_factory_tab(surface)
            self._render_footer(surface, show_save_buttons=False)
            return

        team_panel = pygame.Rect(20, 90, 345, self.screen_height - 150)
        UITheme.draw_panel(surface, team_panel)

        hdr_rect = pygame.Rect(team_panel.x, team_panel.y, team_panel.width, 26)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, hdr_rect, border_top_left_radius=4, border_top_right_radius=4)
        t_title = f"TEAMS ({len(self.teams)})"
        surface.blit(self.font_section.render(t_title, True, UITheme.ACCENT_CYAN), (hdr_rect.x + 10, hdr_rect.y + 5))

        item_y = team_panel.y + 32
        total_teams = len(self.teams)
        visible_teams = max(1, (team_panel.height - 40) // 36)
        max_t_scroll = max(0, total_teams - visible_teams)
        self.team_scroll_y = max(0, min(self.team_scroll_y, max_t_scroll))

        for rel_idx in range(min(visible_teams, total_teams)):
            idx = self.team_scroll_y + rel_idx
            if idx >= total_teams:
                break
            t = self.teams[idx]
            is_sel = idx == self.selected_team_idx
            row_w = team_panel.width - (18 if max_t_scroll > 0 else 12)
            row_rect = pygame.Rect(team_panel.x + 6, item_y, row_w, 32)
            bg_col = (30, 42, 58) if is_sel else (18, 22, 28)
            border_col = UITheme.ACCENT_CYAN if is_sel else (35, 42, 52)
            pygame.draw.rect(surface, bg_col, row_rect, border_radius=3)
            pygame.draw.rect(surface, border_col, row_rect, width=1, border_radius=3)

            if self.db_mode == "EXHIBITION":
                swatch_col = (t.get("color_r", 100), t.get("color_g", 100), t.get("color_b", 100))
            else:
                hex_c = t.get("color_hex", "#00d2be").lstrip("#")
                try:
                    swatch_col = (int(hex_c[0:2], 16), int(hex_c[2:4], 16), int(hex_c[4:6], 16))
                except Exception:
                    swatch_col = (0, 210, 190)

            pygame.draw.circle(surface, swatch_col, (row_rect.x + 16, row_rect.y + 16), 7)
            t_name = t["name"]
            surface.blit(
                self.font_bold.render(t_name, True, (255, 255, 255) if is_sel else UITheme.TEXT_MUTED),
                (row_rect.x + 32, row_rect.y + 8),
            )

            if t.get("is_player"):
                p_badge = self.font_badge.render("PLAYER", True, (0, 240, 140))
                surface.blit(p_badge, (row_rect.right - 55, row_rect.y + 9))

            item_y += 36

        if max_t_scroll > 0:
            sb_track = pygame.Rect(team_panel.x + team_panel.width - 6, team_panel.y + 32, 4, team_panel.height - 38)
            pygame.draw.rect(surface, (18, 24, 32), sb_track, border_radius=2)
            thumb_h = max(20, int(sb_track.height * (visible_teams / total_teams)))
            thumb_y = sb_track.y + int((sb_track.height - thumb_h) * (self.team_scroll_y / max_t_scroll))
            pygame.draw.rect(
                surface, (60, 80, 105), pygame.Rect(sb_track.x, thumb_y, sb_track.width, thumb_h), border_radius=2
            )

        right_panel = pygame.Rect(380, 90, self.screen_width - 400, self.screen_height - 150)
        UITheme.draw_panel(surface, right_panel)

        if self.teams and self.selected_team_idx < len(self.teams):
            sel_team = self.teams[self.selected_team_idx]

            r_hdr = pygame.Rect(right_panel.x, right_panel.y, right_panel.width, 36)
            pygame.draw.rect(surface, UITheme.PANEL_HEADER, r_hdr, border_top_left_radius=4, border_top_right_radius=4)
            surface.blit(
                self.font_title.render(f"EDITING: {sel_team['name']}", True, (255, 215, 0)), (r_hdr.x + 14, r_hdr.y + 8)
            )

            if self.active_subtab == "DRIVER":
                for d_idx, d in enumerate(self.drivers[:4]):
                    d_btn = pygame.Rect(right_panel.x + 14 + d_idx * 160, right_panel.y + 46, 150, 28)
                    is_d_sel = d_idx == self.selected_driver_idx
                    UITheme.draw_button(
                        surface, d_btn, f"#{d.get('number', 1)} {d['name'][:12]}", self.font_badge, is_active=is_d_sel
                    )

            cur_attrs = self.car_attrs if self.active_subtab == "CAR" else self.driver_stats
            keys = list(cur_attrs.keys())
            start_y = right_panel.y + (50 if self.active_subtab == "CAR" else 84)

            for idx, key in enumerate(keys):
                y = start_y + idx * 42
                val = cur_attrs[key]

                label_text = key.replace("_", " ").upper()
                surface.blit(self.font_bold.render(label_text, True, UITheme.TEXT_WHITE), (right_panel.x + 20, y + 4))

                bar_x = right_panel.x + 220
                bar_w = max(60, min(240, self.screen_width - 280 - bar_x))
                bar_rect = pygame.Rect(bar_x, y + 4, bar_w, 16)
                pygame.draw.rect(surface, (20, 26, 36), bar_rect, border_radius=3)
                fill_w = int((val / 100.0) * bar_w)
                fill_col = UITheme.ACCENT_CYAN if val > 75 else (UITheme.ACCENT_YELLOW if val > 60 else (220, 60, 60))
                pygame.draw.rect(surface, fill_col, pygame.Rect(bar_x, y + 4, fill_w, 16), border_radius=3)
                pygame.draw.rect(surface, UITheme.PANEL_BORDER, bar_rect, width=1, border_radius=3)

                val_txt = f"{val:.0f}"
                surface.blit(self.font_val.render(val_txt, True, (255, 255, 255)), (bar_x + bar_w + 12, y + 3))

                btn_minus = pygame.Rect(self.screen_width - 240, y, 32, 24)
                btn_plus = pygame.Rect(self.screen_width - 200, y, 32, 24)
                btn_min = pygame.Rect(self.screen_width - 160, y, 36, 24)
                btn_max = pygame.Rect(self.screen_width - 116, y, 36, 24)

                UITheme.draw_button(surface, btn_minus, "-", self.font_bold)
                UITheme.draw_button(surface, btn_plus, "+", self.font_bold)
                UITheme.draw_button(surface, btn_min, "50", self.font_badge)
                UITheme.draw_button(surface, btn_max, "99", self.font_badge)

        self._render_footer(surface, show_save_buttons=True)

    def _render_footer(self, surface: pygame.Surface, show_save_buttons: bool = True):
        if show_save_buttons:
            btn_save = pygame.Rect(self.screen_width - 320, self.screen_height - 50, 140, 34)
            btn_reset = pygame.Rect(self.screen_width - 160, self.screen_height - 50, 140, 34)

            pygame.draw.rect(surface, (0, 180, 100), btn_save, border_radius=4)
            s_lbl = self.font_bold.render("SAVE CHANGES", True, (10, 25, 20))
            surface.blit(s_lbl, (btn_save.x + (btn_save.width - s_lbl.get_width()) // 2, btn_save.y + 9))

            pygame.draw.rect(surface, (45, 30, 35), btn_reset, border_radius=4)
            pygame.draw.rect(surface, (180, 60, 60), btn_reset, width=1, border_radius=4)
            r_lbl = self.font_bold.render("RESET DEFAULTS", True, (255, 120, 120))
            surface.blit(r_lbl, (btn_reset.x + (btn_reset.width - r_lbl.get_width()) // 2, btn_reset.y + 9))

            stat_w = self.screen_width - 360
        else:
            stat_w = self.screen_width - 280

        stat_rect = pygame.Rect(20, self.screen_height - 50, stat_w, 34)
        pygame.draw.rect(surface, (16, 22, 30), stat_rect, border_radius=4)
        pygame.draw.rect(surface, (35, 45, 60), stat_rect, width=1, border_radius=4)
        stat_txt = self.font_body.render(
            self.status_msg, True, (0, 240, 180) if self.status_timer > 0 else UITheme.TEXT_MUTED
        )
        surface.blit(stat_txt, (stat_rect.x + 12, stat_rect.y + 9))

    def _render_calendar_tab(self, surface: pygame.Surface):
        # Tier Selector Chips (y = 58)
        for t in range(1, 6):
            t_rect = pygame.Rect(20 + (t - 1) * 74, 58, 68, 24)
            is_t_sel = t == self.selected_calendar_tier
            UITheme.draw_button(surface, t_rect, f"TIER {t}", self.font_badge, is_active=is_t_sel)

        # 1. Left panel: List of rounds
        cal_panel = pygame.Rect(20, 90, 360, self.screen_height - 150)
        UITheme.draw_panel(surface, cal_panel)

        hdr_rect = pygame.Rect(cal_panel.x, cal_panel.y, cal_panel.width, 28)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, hdr_rect, border_top_left_radius=4, border_top_right_radius=4)
        surface.blit(
            self.font_section.render(
                f"TIER {self.selected_calendar_tier} CALENDAR ({len(self.calendar_rounds)} ROUNDS)",
                True,
                UITheme.ACCENT_CYAN,
            ),
            (hdr_rect.x + 10, hdr_rect.y + 6),
        )

        total_rounds = len(self.calendar_rounds)
        row_h = 30 if total_rounds > 12 else 35
        visible_rounds = max(1, (cal_panel.height - 40) // row_h)
        max_cal_scroll = max(0, total_rounds - visible_rounds)
        self.cal_scroll_y = max(0, min(self.cal_scroll_y, max_cal_scroll))

        item_y = cal_panel.y + 34
        for rel_idx in range(min(visible_rounds, total_rounds)):
            idx = self.cal_scroll_y + rel_idx
            if idx >= total_rounds:
                break
            r = self.calendar_rounds[idx]
            is_sel = idx == self.selected_round_idx
            row_w = cal_panel.width - (18 if max_cal_scroll > 0 else 12)
            row_rect = pygame.Rect(cal_panel.x + 6, item_y, row_w, 28 if total_rounds > 12 else 32)
            bg_col = (30, 44, 62) if is_sel else (18, 22, 28)
            border_col = UITheme.ACCENT_CYAN if is_sel else (35, 42, 52)
            pygame.draw.rect(surface, bg_col, row_rect, border_radius=3)
            pygame.draw.rect(surface, border_col, row_rect, width=1, border_radius=3)

            r_num_txt = self.font_badge.render(f"R{r['round']}", True, (255, 215, 0) if is_sel else UITheme.TEXT_MUTED)
            surface.blit(r_num_txt, (row_rect.x + 6, row_rect.y + 6))

            name_display = r["track_name"][:18]
            surface.blit(
                self.font_bold.render(name_display, True, (255, 255, 255) if is_sel else UITheme.TEXT_MUTED),
                (row_rect.x + 32, row_rect.y + 6),
            )

            # Characteristic badge
            c_code = r.get("characteristic", "BAL")[:3].upper()
            c_col = (
                (255, 120, 90)
                if c_code == "SPE"
                else ((255, 210, 60) if c_code == "BRA" else ((80, 220, 255) if c_code == "AER" else (80, 230, 140)))
            )
            c_badge = self.font_badge.render(c_code, True, c_col)
            surface.blit(c_badge, (row_rect.right - 68, row_rect.y + 6))

            lap_badge = self.font_badge.render(f"{r['total_laps']}L", True, UITheme.ACCENT_CYAN)
            surface.blit(lap_badge, (row_rect.right - 34, row_rect.y + 6))

            item_y += row_h

        if max_cal_scroll > 0:
            sb_track = pygame.Rect(cal_panel.x + cal_panel.width - 6, cal_panel.y + 34, 4, cal_panel.height - 40)
            pygame.draw.rect(surface, (18, 24, 32), sb_track, border_radius=2)
            thumb_h = max(20, int(sb_track.height * (visible_rounds / total_rounds)))
            thumb_y = sb_track.y + int((sb_track.height - thumb_h) * (self.cal_scroll_y / max_cal_scroll))
            pygame.draw.rect(
                surface, (60, 80, 105), pygame.Rect(sb_track.x, thumb_y, sb_track.width, thumb_h), border_radius=2
            )

        # 2. Right panel: Round configuration & track swapper
        right_panel = pygame.Rect(395, 90, self.screen_width - 415, self.screen_height - 150)
        UITheme.draw_panel(surface, right_panel)

        if self.calendar_rounds and self.selected_round_idx < len(self.calendar_rounds):
            sel_r = self.calendar_rounds[self.selected_round_idx]
            r_num = sel_r["round"]

            r_hdr = pygame.Rect(right_panel.x, right_panel.y, right_panel.width, 36)
            pygame.draw.rect(surface, UITheme.PANEL_HEADER, r_hdr, border_top_left_radius=4, border_top_right_radius=4)
            surface.blit(
                self.font_title.render(
                    f"TIER {self.selected_calendar_tier} - ROUND {r_num}: {sel_r['track_name'].upper()}",
                    True,
                    (255, 215, 0),
                ),
                (r_hdr.x + 14, r_hdr.y + 8),
            )

            # Delete Round button (top right)
            if len(self.calendar_rounds) > 1:
                btn_del = pygame.Rect(self.screen_width - 200, 96, 170, 26)
                pygame.draw.rect(surface, (45, 20, 25), btn_del, border_radius=4)
                pygame.draw.rect(surface, (200, 60, 60), btn_del, width=1, border_radius=4)
                d_lbl = self.font_badge.render("- DELETE ROUND", True, (255, 120, 120))
                surface.blit(d_lbl, (btn_del.x + (btn_del.width - d_lbl.get_width()) // 2, btn_del.y + 6))

            # Track file picker section
            surface.blit(
                self.font_bold.render("ASSIGN CIRCUIT FILE (.JSON):", True, UITheme.TEXT_WHITE),
                (right_panel.x + 20, right_panel.y + 48),
            )

            c_y = right_panel.y + 75
            for c_idx, c_file in enumerate(self.available_circuit_files[:8]):
                col = c_idx % 2
                row = c_idx // 2
                c_rect = pygame.Rect(right_panel.x + 20 + col * 240, c_y + row * 34, 230, 26)
                is_active_circuit = c_file == sel_r.get("circuit_file")
                UITheme.draw_button(surface, c_rect, c_file, self.font_badge, is_active=is_active_circuit)

            # Characteristic selector section
            char_y = right_panel.y + 220
            surface.blit(
                self.font_bold.render("TRACK CHARACTERISTIC:", True, UITheme.TEXT_WHITE), (right_panel.x + 20, char_y)
            )
            cur_char = sel_r.get("characteristic", "BALANCED")
            for c_idx, char_name in enumerate(["BALANCED", "SPEED", "BRAKES", "AERO"]):
                char_rect = pygame.Rect(right_panel.x + 20 + c_idx * 96, char_y + 25, 88, 26)
                is_active_char = char_name == cur_char
                UITheme.draw_button(surface, char_rect, char_name, self.font_badge, is_active=is_active_char)

            # Weather selector section
            w_y = right_panel.y + 285
            surface.blit(self.font_bold.render("WEATHER PROFILE:", True, UITheme.TEXT_WHITE), (right_panel.x + 20, w_y))
            w_rect = pygame.Rect(right_panel.x + 20, w_y + 25, 150, 28)
            cur_w = sel_r.get("weather_profile", "DYNAMIC")
            w_col = (0, 220, 240) if cur_w == "DYNAMIC" else ((255, 200, 40) if cur_w == "SUNNY" else (80, 140, 255))
            pygame.draw.rect(surface, (24, 30, 40), w_rect, border_radius=4)
            pygame.draw.rect(surface, w_col, w_rect, width=1, border_radius=4)
            w_lbl = self.font_bold.render(f"🌤 {cur_w} (Click)", True, w_col)
            surface.blit(w_lbl, (w_rect.x + 12, w_rect.y + 6))

            # Lap count adjust section
            l_y = right_panel.y + 350
            surface.blit(
                self.font_bold.render("RACE DISTANCE (LAPS):", True, UITheme.TEXT_WHITE), (right_panel.x + 20, l_y)
            )
            btn_l_minus = pygame.Rect(right_panel.x + 20, l_y + 25, 34, 26)
            btn_l_plus = pygame.Rect(right_panel.x + 60, l_y + 25, 34, 26)
            UITheme.draw_button(surface, btn_l_minus, "-", self.font_bold)
            UITheme.draw_button(surface, btn_l_plus, "+", self.font_bold)
            l_val = self.font_val.render(f"{sel_r.get('total_laps', 15)} Laps", True, (255, 255, 255))
            surface.blit(l_val, (right_panel.x + 105, l_y + 28))

        # Bottom Add Grand Prix Button
        btn_add = pygame.Rect(self.screen_width - 240, self.screen_height - 50, 220, 34)
        pygame.draw.rect(surface, (0, 140, 210), btn_add, border_radius=4)
        a_lbl = self.font_bold.render("+ ADD NEW GRAND PRIX", True, (255, 255, 255))
        surface.blit(a_lbl, (btn_add.x + (btn_add.width - a_lbl.get_width()) // 2, btn_add.y + 9))

    def _render_factory_tab(self, surface: pygame.Surface):
        # 1. Left panel: Teams
        team_panel = pygame.Rect(20, 90, 240, self.screen_height - 150)
        UITheme.draw_panel(surface, team_panel)

        hdr_rect = pygame.Rect(team_panel.x, team_panel.y, team_panel.width, 28)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, hdr_rect, border_top_left_radius=4, border_top_right_radius=4)
        surface.blit(
            self.font_section.render("SELECT TEAM", True, UITheme.ACCENT_CYAN), (hdr_rect.x + 10, hdr_rect.y + 6)
        )

        item_y = team_panel.y + 34
        for idx, t in enumerate(self.teams[:14]):
            is_sel = idx == self.selected_team_idx
            row_rect = pygame.Rect(team_panel.x + 6, item_y, team_panel.width - 12, 32)
            bg_col = (30, 44, 62) if is_sel else (18, 22, 28)
            border_col = UITheme.ACCENT_CYAN if is_sel else (35, 42, 52)
            pygame.draw.rect(surface, bg_col, row_rect, border_radius=3)
            pygame.draw.rect(surface, border_col, row_rect, width=1, border_radius=3)

            hex_c = t.get("color_hex", "#00d2be").lstrip("#")
            try:
                swatch_col = (int(hex_c[0:2], 16), int(hex_c[2:4], 16), int(hex_c[4:6], 16))
            except Exception:
                swatch_col = (0, 210, 190)

            pygame.draw.circle(surface, swatch_col, (row_rect.x + 14, row_rect.y + 16), 6)
            surface.blit(
                self.font_bold.render(t["name"][:14], True, (255, 255, 255) if is_sel else UITheme.TEXT_MUTED),
                (row_rect.x + 26, row_rect.y + 8),
            )

            if t.get("is_player"):
                p_badge = self.font_badge.render("YOU", True, (0, 240, 140))
                surface.blit(p_badge, (row_rect.right - 35, row_rect.y + 9))

            item_y += 36

        # 2. Right panel: Master Tech Tree Nodes & Team Tuning
        fac_panel = pygame.Rect(270, 90, self.screen_width - 290, self.screen_height - 150)
        UITheme.draw_panel(surface, fac_panel)

        sel_team = self.teams[self.selected_team_idx] if self.teams else {"name": "Team"}
        f_hdr = pygame.Rect(fac_panel.x, fac_panel.y, fac_panel.width, 36)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, f_hdr, border_top_left_radius=4, border_top_right_radius=4)
        surface.blit(
            self.font_title.render(
                f"HQ TECH TREE & CUSTOM NODES: {sel_team['name'].upper()} ({len(self.all_nodes)} TOTAL NODES)",
                True,
                (255, 215, 0),
            ),
            (f_hdr.x + 14, f_hdr.y + 8),
        )

        # Top-right "+ ADD CUSTOM NODE" button
        btn_add_node = pygame.Rect(self.screen_width - 190, 96, 170, 26)
        pygame.draw.rect(surface, (0, 120, 180), btn_add_node, border_radius=4)
        pygame.draw.rect(surface, (0, 220, 255), btn_add_node, width=1, border_radius=4)
        add_lbl = self.font_badge.render("+ ADD CUSTOM NODE", True, (255, 255, 255))
        surface.blit(add_lbl, (btn_add_node.x + (btn_add_node.width - add_lbl.get_width()) // 2, btn_add_node.y + 6))

        # Map team facilities
        team_fac_map = {f["id"]: f for f in self.facilities}

        item_h = 38
        visible_count = min(len(self.all_nodes) - self.node_scroll_y, 11)
        for v_idx in range(visible_count):
            actual_idx = self.node_scroll_y + v_idx
            if actual_idx >= len(self.all_nodes):
                break
            n = self.all_nodes[actual_idx]
            tf = team_fac_map.get(n["id"], {})

            row_y = fac_panel.y + 40 + v_idx * item_h
            row_rect = pygame.Rect(fac_panel.x + 8, row_y, fac_panel.width - 16, 34)
            pygame.draw.rect(surface, (20, 26, 36), row_rect, border_radius=3)
            pygame.draw.rect(surface, UITheme.PANEL_BORDER, row_rect, width=1, border_radius=3)

            # Department Tag
            dept_name = n.get("department", "DEPT")
            dept_col = (
                (0, 200, 220)
                if dept_name == "ENGINEERING"
                else ((255, 180, 50) if dept_name == "MANUFACTURING" else (180, 100, 240))
            )
            dept_txt = self.font_badge.render(f"[{dept_name[:4]}]", True, dept_col)
            surface.blit(dept_txt, (row_rect.x + 8, row_rect.y + 10))

            # Node Name & Parent Dependency
            name_txt = self.font_bold.render(n["name"][:20], True, UITheme.TEXT_WHITE)
            surface.blit(name_txt, (row_rect.x + 60, row_rect.y + 9))

            parent_info = f"<- {n['parent_id']}" if n.get("parent_id") else "ROOT"
            p_txt = self.font_badge.render(parent_info[:16], True, UITheme.TEXT_MUTED)
            surface.blit(p_txt, (row_rect.x + 230, row_rect.y + 11))

            # Unlock Toggle
            is_unlocked = bool(tf.get("is_unlocked", 0))
            btn_unlock = pygame.Rect(self.screen_width - 295, row_y + 5, 75, 24)
            u_col = (0, 220, 120) if is_unlocked else (180, 60, 60)
            pygame.draw.rect(surface, (25, 35, 30) if is_unlocked else (35, 22, 24), btn_unlock, border_radius=3)
            pygame.draw.rect(surface, u_col, btn_unlock, width=1, border_radius=3)
            u_lbl = self.font_badge.render("UNLOCKED" if is_unlocked else "LOCKED", True, u_col)
            surface.blit(u_lbl, (btn_unlock.x + (btn_unlock.width - u_lbl.get_width()) // 2, btn_unlock.y + 5))

            # Tier Cycle
            cur_tier = tf.get("current_tier", 0)
            max_tier = n.get("max_tier", 3)
            btn_tier = pygame.Rect(self.screen_width - 215, row_y + 5, 75, 24)
            UITheme.draw_button(
                surface, btn_tier, f"LVL {cur_tier} / {max_tier}", self.font_badge, is_active=(cur_tier > 0)
            )

            # Edit Node Button
            btn_edit = pygame.Rect(self.screen_width - 135, row_y + 5, 50, 24)
            UITheme.draw_button(surface, btn_edit, "EDIT", self.font_badge)

            # Delete Node Button
            btn_del = pygame.Rect(self.screen_width - 80, row_y + 5, 45, 24)
            pygame.draw.rect(surface, (45, 20, 25), btn_del, border_radius=3)
            pygame.draw.rect(surface, (200, 60, 60), btn_del, width=1, border_radius=3)
            del_lbl = self.font_badge.render("DEL", True, (255, 120, 120))
            surface.blit(del_lbl, (btn_del.x + (btn_del.width - del_lbl.get_width()) // 2, btn_del.y + 5))

        # Render Scroll Indicator if more nodes exist
        if len(self.all_nodes) > 11:
            scroll_txt = self.font_badge.render(
                f"Nodes {self.node_scroll_y + 1}-{min(len(self.all_nodes), self.node_scroll_y + 11)} of {len(self.all_nodes)} (Scroll with mouse wheel)",
                True,
                UITheme.TEXT_MUTED,
            )
            surface.blit(scroll_txt, (fac_panel.x + 14, fac_panel.bottom - 22))

        # Render Custom Node Creation / Editing Modal if open
        if self.show_node_modal:
            self._render_node_modal(surface)

    def _render_node_modal(self, surface: pygame.Surface):
        dim_surf = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        dim_surf.fill((0, 0, 0, 190))
        surface.blit(dim_surf, (0, 0))

        modal_w = 580
        modal_h = 420
        modal_rect = pygame.Rect(
            (self.screen_width - modal_w) // 2, (self.screen_height - modal_h) // 2, modal_w, modal_h
        )
        pygame.draw.rect(surface, (18, 24, 34), modal_rect, border_radius=6)
        pygame.draw.rect(surface, (0, 220, 240), modal_rect, width=2, border_radius=6)

        # Header
        m_hdr = pygame.Rect(modal_rect.x, modal_rect.y, modal_rect.width, 40)
        pygame.draw.rect(surface, (26, 34, 48), m_hdr, border_top_left_radius=6, border_top_right_radius=6)
        title_text = (
            "CREATE NEW CUSTOM FACILITY NODE" if self.modal_mode == "CREATE" else f"EDIT NODE: {self.edit_node_id}"
        )
        surface.blit(self.font_card_title.render(title_text, True, (255, 215, 0)), (m_hdr.x + 16, m_hdr.y + 10))

        # Close button
        btn_close = pygame.Rect(modal_rect.right - 34, modal_rect.y + 10, 24, 24)
        pygame.draw.rect(surface, (180, 40, 40), btn_close, border_radius=3)
        surface.blit(self.font_bold.render("X", True, (255, 255, 255)), (btn_close.x + 7, btn_close.y + 4))

        f_y = modal_rect.y + 55

        cursor_pipe = " |" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""

        # 1. Node ID
        surface.blit(self.font_bold.render("NODE ID (Key):", True, UITheme.TEXT_WHITE), (modal_rect.x + 20, f_y + 4))
        id_box = pygame.Rect(modal_rect.x + 160, f_y, 380, 26)
        id_col = (0, 220, 255) if self.active_input == "ID" else (40, 50, 65)
        pygame.draw.rect(surface, (12, 16, 22), id_box, border_radius=3)
        pygame.draw.rect(surface, id_col, id_box, width=1, border_radius=3)
        id_txt = self.edit_node_id + (cursor_pipe if self.active_input == "ID" else "")
        surface.blit(self.font_body.render(id_txt, True, (255, 255, 255)), (id_box.x + 8, id_box.y + 5))

        # 2. Name
        f_y += 36
        surface.blit(self.font_bold.render("DISPLAY NAME:", True, UITheme.TEXT_WHITE), (modal_rect.x + 20, f_y + 4))
        name_box = pygame.Rect(modal_rect.x + 160, f_y, 380, 26)
        name_col = (0, 220, 255) if self.active_input == "NAME" else (40, 50, 65)
        pygame.draw.rect(surface, (12, 16, 22), name_box, border_radius=3)
        pygame.draw.rect(surface, name_col, name_box, width=1, border_radius=3)
        name_txt = self.edit_node_name + (cursor_pipe if self.active_input == "NAME" else "")
        surface.blit(self.font_body.render(name_txt, True, (255, 255, 255)), (name_box.x + 8, name_box.y + 5))

        # 3. Description
        f_y += 36
        surface.blit(self.font_bold.render("DESCRIPTION:", True, UITheme.TEXT_WHITE), (modal_rect.x + 20, f_y + 4))
        desc_box = pygame.Rect(modal_rect.x + 160, f_y, 380, 26)
        desc_col = (0, 220, 255) if self.active_input == "DESC" else (40, 50, 65)
        pygame.draw.rect(surface, (12, 16, 22), desc_box, border_radius=3)
        pygame.draw.rect(surface, desc_col, desc_box, width=1, border_radius=3)
        desc_txt = self.edit_node_desc[:45] + (cursor_pipe if self.active_input == "DESC" else "")
        surface.blit(self.font_body.render(desc_txt, True, (255, 255, 255)), (desc_box.x + 8, desc_box.y + 5))

        # 4. Department
        f_y += 36
        surface.blit(self.font_bold.render("DEPARTMENT:", True, UITheme.TEXT_WHITE), (modal_rect.x + 20, f_y + 4))
        btn_dept = pygame.Rect(modal_rect.x + 160, f_y, 180, 26)
        UITheme.draw_button(surface, btn_dept, self.edit_node_dept, self.font_bold, is_active=True)

        # 5. Parent Dependency
        f_y += 36
        surface.blit(self.font_bold.render("PARENT NODE:", True, UITheme.TEXT_WHITE), (modal_rect.x + 20, f_y + 4))
        btn_parent = pygame.Rect(modal_rect.x + 160, f_y, 220, 26)
        parent_lbl = str(self.edit_node_parent_id) if self.edit_node_parent_id else "NONE (ROOT NODE)"
        UITheme.draw_button(surface, btn_parent, parent_lbl, self.font_badge)

        # 6. Base Cost & Upkeep
        f_y += 36
        surface.blit(self.font_bold.render("BASE COST ($M):", True, UITheme.TEXT_WHITE), (modal_rect.x + 20, f_y + 4))
        btn_cost_m = pygame.Rect(modal_rect.x + 160, f_y, 30, 24)
        btn_cost_p = pygame.Rect(modal_rect.x + 200, f_y, 30, 24)
        UITheme.draw_button(surface, btn_cost_m, "-", self.font_bold)
        UITheme.draw_button(surface, btn_cost_p, "+", self.font_bold)
        surface.blit(
            self.font_bold.render(f"${self.edit_node_cost_m:.1f}M", True, (255, 215, 0)), (modal_rect.x + 245, f_y + 4)
        )

        f_y += 36
        surface.blit(self.font_bold.render("UPKEEP ($k/mo):", True, UITheme.TEXT_WHITE), (modal_rect.x + 20, f_y + 4))
        btn_upk_m = pygame.Rect(modal_rect.x + 160, f_y, 30, 24)
        btn_upk_p = pygame.Rect(modal_rect.x + 200, f_y, 30, 24)
        UITheme.draw_button(surface, btn_upk_m, "-", self.font_bold)
        UITheme.draw_button(surface, btn_upk_p, "+", self.font_bold)
        surface.blit(
            self.font_bold.render(f"${self.edit_node_upkeep_k:.0f}k", True, (0, 220, 255)),
            (modal_rect.x + 245, f_y + 4),
        )

        # Bottom Confirm Button
        btn_confirm = pygame.Rect(modal_rect.x + 160, modal_rect.bottom - 50, 260, 36)
        pygame.draw.rect(surface, (0, 180, 100), btn_confirm, border_radius=4)
        c_lbl = self.font_bold.render("CONFIRM & SAVE TO TECH TREE", True, (10, 25, 20))
        surface.blit(c_lbl, (btn_confirm.x + (btn_confirm.width - c_lbl.get_width()) // 2, btn_confirm.y + 10))
