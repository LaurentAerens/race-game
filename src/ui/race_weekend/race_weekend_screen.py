import random
from typing import Any, Callable, Dict, List, Optional, Tuple

import pygame

from ...core.race_weekend import CarSetup, RaceWeekendManager, RaceWeekendSession
from ...ui.theme import UITheme


class RaceWeekendScreen:
    """
    Comprehensive Interactive Race Weekend UI:
    - Tier-specific session sequence progress stepper
    - Practice Setup Tuning with 5 responsive sliders
    - 4 Practice Programs: BALANCED, FAST_LAP, SPRINT_STINTS, LONG_RUNS
    - Driver Telemetry Quotes & Setup Confidence Gauge
    - Live & Quick-Sim Qualifying Leaderboard
    - Sprint Grid (with Tier 1 Top 10 Reverse Grid) & Grand Prix Strategy
    """

    def __init__(
        self,
        width: int,
        height: int,
        manager: RaceWeekendManager,
        drivers: List[Dict[str, Any]],
        on_start_live_session: Callable[[str, int, Optional[List[Dict[str, Any]]]], None],
        on_finish_weekend: Callable[[Dict[str, Any]], None],
        driver_car_pairs: Optional[List[Tuple[Any, Any]]] = None,
        career_db: Optional[Any] = None,
        team_id: int = 1,
    ):
        self.width = width
        self.height = height
        self.manager = manager
        self.drivers = drivers
        self.on_start_live_session = on_start_live_session
        self.on_finish_weekend = on_finish_weekend
        self.driver_car_pairs = driver_car_pairs
        self.career_db = career_db
        self.team_id = team_id

        # Active player car slot in practice: 1 or 2
        self.active_car_slot: int = 1

        # Dragging slider state: None or parameter name
        self.dragging_param: Optional[str] = None

        # Fonts
        self._init_fonts()

        # Feedback notification message
        self.status_message: str = "Welcome to the Race Weekend. Optimize setup in Practice."

    def _init_fonts(self):
        self.font_title = UITheme.get_font(15, bold=True)
        self.font_header = UITheme.get_font(12, bold=True)
        self.font_card = UITheme.get_font(11, bold=True)
        self.font_body = UITheme.get_font(10, bold=False)
        self.font_badge = UITheme.get_font(9, bold=True)
        self.font_btn = UITheme.get_font(11, bold=True)
        self.font_big_btn = UITheme.get_font(13, bold=True)
        self.font_mini = UITheme.get_font(9, bold=True)

    def resize(self, width: int, height: int):
        self.width = width
        self.height = height
        self._init_fonts()

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging_param = None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            return self._handle_click(mx, my)

        elif event.type == pygame.MOUSEMOTION and self.dragging_param:
            mx, my = event.pos
            self._handle_slider_drag(mx, my)
            return True

        return False

    def _handle_slider_drag(self, mx: int, my: int):
        """Updates slider value while dragging."""
        setup_rect = pygame.Rect(24, 150, 480, 260)
        param_names = [
            ("front_wing", 0.0, 100.0),
            ("rear_wing", 0.0, 100.0),
            ("suspension", 0.0, 100.0),
            ("gear_ratio", 0.0, 100.0),
            ("brake_bias", 50.0, 65.0),
        ]

        for p_name, min_v, max_v in param_names:
            if self.dragging_param == p_name:
                track_x = setup_rect.x + 185
                track_w = 170
                rel_x = max(0, min(track_w, mx - track_x))
                pct = rel_x / float(track_w)
                val = min_v + pct * (max_v - min_v)
                self.manager.set_car_setup_parameter(self.active_car_slot, p_name, round(val, 1))
                break

    def _handle_click(self, mx: int, my: int) -> bool:
        mgr = self.manager

        # 1. Car Slot Toggle (Car #1 / Car #2 in practice)
        if mgr.is_practice:
            tab_c1 = pygame.Rect(24, 110, 120, 28)
            tab_c2 = pygame.Rect(150, 110, 120, 28)
            if tab_c1.collidepoint(mx, my):
                self.active_car_slot = 1
                return True
            elif tab_c2.collidepoint(mx, my):
                self.active_car_slot = 2
                return True

            # Setup Tuning Sliders
            setup_rect = pygame.Rect(24, 150, 480, 260)
            param_names = [
                ("front_wing", 0.0, 100.0, 2.0),
                ("rear_wing", 0.0, 100.0, 2.0),
                ("suspension", 0.0, 100.0, 2.0),
                ("gear_ratio", 0.0, 100.0, 2.0),
                ("brake_bias", 50.0, 65.0, 0.5),
            ]
            for idx, (p_name, min_v, max_v, step) in enumerate(param_names):
                row_y = setup_rect.y + 36 + idx * 36
                btn_minus = pygame.Rect(setup_rect.x + 150, row_y + 2, 26, 22)
                track_r = pygame.Rect(setup_rect.x + 185, row_y + 2, 170, 22)
                btn_plus = pygame.Rect(setup_rect.x + 365, row_y + 2, 26, 22)

                cur_setup = mgr.car_setups[self.active_car_slot]
                cur_val = getattr(cur_setup, p_name)

                if btn_minus.collidepoint(mx, my):
                    mgr.set_car_setup_parameter(self.active_car_slot, p_name, max(min_v, cur_val - step))
                    return True
                elif btn_plus.collidepoint(mx, my):
                    mgr.set_car_setup_parameter(self.active_car_slot, p_name, min(max_v, cur_val + step))
                    return True
                elif track_r.collidepoint(mx, my):
                    self.dragging_param = p_name
                    self._handle_slider_drag(mx, my)
                    return True

            # Setup Management Buttons (Save, Load, Factory, Copy)
            btn_save = pygame.Rect(setup_rect.x + 10, setup_rect.y + 222, 105, 28)
            btn_load = pygame.Rect(setup_rect.x + 122, setup_rect.y + 222, 105, 28)
            btn_factory = pygame.Rect(setup_rect.x + 234, setup_rect.y + 222, 115, 28)
            btn_copy = pygame.Rect(setup_rect.x + 356, setup_rect.y + 222, 114, 28)

            if btn_save.collidepoint(mx, my):
                cur_setup = mgr.car_setups[self.active_car_slot]
                if self.career_db:
                    self.career_db.save_track_setup_preset(
                        self.team_id,
                        mgr.track_name,
                        self.active_car_slot,
                        cur_setup.front_wing,
                        cur_setup.rear_wing,
                        cur_setup.suspension,
                        cur_setup.gear_ratio,
                        cur_setup.brake_bias,
                    )
                self.status_message = f"💾 Saved Car #{self.active_car_slot} setup preset for {mgr.track_name}."
                return True
            elif btn_load.collidepoint(mx, my):
                loaded = None
                if self.career_db:
                    loaded = self.career_db.load_track_setup_preset(self.team_id, mgr.track_name, self.active_car_slot)
                if loaded:
                    mgr.car_setups[self.active_car_slot] = CarSetup(
                        front_wing=loaded["front_wing"],
                        rear_wing=loaded["rear_wing"],
                        suspension=loaded["suspension"],
                        gear_ratio=loaded["gear_ratio"],
                        brake_bias=loaded["brake_bias"],
                    )
                    self.status_message = f"📂 Loaded saved setup preset for Car #{self.active_car_slot}."
                else:
                    self.status_message = f"No saved preset found for {mgr.track_name}."
                return True
            elif btn_factory.collidepoint(mx, my):
                fac_setup = mgr.get_factory_preset(self.active_car_slot)
                mgr.car_setups[self.active_car_slot] = fac_setup
                self.status_message = f"🏭 Applied Factory Baseline preset to Car #{self.active_car_slot}."
                return True
            elif btn_copy.collidepoint(mx, my):
                other_slot = 2 if self.active_car_slot == 1 else 1
                mgr.car_setups[other_slot] = mgr.car_setups[self.active_car_slot].copy()
                self.status_message = f"📋 Copied Car #{self.active_car_slot} setup to Car #{other_slot} as baseline."
                return True

            # Practice Stint Buttons (Short, Sprint, Race Sim) & Time Hop
            btn_short = pygame.Rect(24, self.height - 75, 150, 48)
            btn_sprint = pygame.Rect(182, self.height - 75, 155, 48)
            btn_long = pygame.Rect(345, self.height - 75, 160, 48)
            btn_fast_forward = pygame.Rect(520, self.height - 75, 330, 48)
            next_btn = pygame.Rect(865, self.height - 75, self.width - 889, 48)

            d_name = (
                self.drivers[self.active_car_slot - 1]["name"]
                if len(self.drivers) >= self.active_car_slot
                else f"Driver {self.active_car_slot}"
            )

            if btn_short.collidepoint(mx, my):
                if mgr.is_chequered_flag():
                    self.status_message = "Session time expired! Chequered flag is out."
                elif mgr.is_car_on_track(self.active_car_slot):
                    self.status_message = f"Car #{self.active_car_slot} is currently out on track."
                else:
                    res = mgr.start_practice_stint(self.active_car_slot, d_name, stint_type="SHORT")
                    if res.get("success"):
                        self.status_message = f"🏎️ Car #{self.active_car_slot} sent out on Short Stint ({res['laps_target']} laps, ~{res['time_cost_min']:.0f}m). Debrief available upon return."
                    else:
                        self.status_message = res.get("message", "Unable to start stint.")
                return True

            elif btn_sprint.collidepoint(mx, my):
                if mgr.is_chequered_flag():
                    self.status_message = "Session time expired! Chequered flag is out."
                elif mgr.is_car_on_track(self.active_car_slot):
                    self.status_message = f"Car #{self.active_car_slot} is currently out on track."
                else:
                    res = mgr.start_practice_stint(self.active_car_slot, d_name, stint_type="SPRINT")
                    if res.get("success"):
                        self.status_message = f"🛡️ Car #{self.active_car_slot} sent out on Sprint Stint ({res['laps_target']} laps, ~{res['time_cost_min']:.0f}m). Debrief available upon return."
                    else:
                        self.status_message = res.get("message", "Unable to start stint.")
                return True

            elif btn_long.collidepoint(mx, my):
                if mgr.tier >= 3:
                    self.status_message = "Race Simulation is available in Tier 1 & Tier 2 Grand Prix."
                    return True
                if mgr.is_chequered_flag():
                    self.status_message = "Session time expired! Chequered flag is out."
                elif mgr.is_car_on_track(self.active_car_slot):
                    self.status_message = f"Car #{self.active_car_slot} is currently out on track."
                else:
                    res = mgr.start_practice_stint(self.active_car_slot, d_name, stint_type="LONG")
                    if res.get("success"):
                        self.status_message = f"🏁 Car #{self.active_car_slot} sent out on Race Sim stint ({res['laps_target']} laps, ~{res['time_cost_min']:.0f}m). Debrief available upon return."
                    else:
                        self.status_message = res.get("message", "Unable to start stint.")
                return True

            elif btn_fast_forward.collidepoint(mx, my):
                if mgr.is_chequered_flag():
                    self.status_message = "Free Practice session time is up! Proceed to the next session."
                else:
                    prev_completed = len(mgr.driver_feedback[1]) + len(mgr.driver_feedback[2])
                    delta = mgr.fast_forward_to_next_completion()
                    now_completed = len(mgr.driver_feedback[1]) + len(mgr.driver_feedback[2])
                    if now_completed > prev_completed:
                        self.status_message = f"⏩ Advanced session time by {delta:.0f}m! Car returned to garage. Driver debrief is ready."
                    else:
                        self.status_message = f"⏩ Advanced session time by {delta:.0f}m. Time remaining: {float(mgr.session_time_remaining):.0f}m."
                return True

            elif next_btn.collidepoint(mx, my):
                has_next = mgr.advance_to_next_session()
                if has_next:
                    self.status_message = f"Moved to {mgr.current_session.value}."
                return True

        # 2. Qualifying Clicks
        elif mgr.is_qualifying:
            if not mgr.qualifying_results:
                sim_q_btn = pygame.Rect(self.width // 2 - 220, self.height // 2 - 30, 440, 60)
                if sim_q_btn.collidepoint(mx, my):
                    # Prepare driver car pairs from career
                    all_pairs = self._build_driver_car_pairs()
                    q_res = mgr.simulate_qualifying_session(all_pairs)
                    mgr.record_session_completion(RaceWeekendSession.QUALIFYING, q_res)
                    self.status_message = (
                        f"Qualifying complete! Pole: {q_res[0]['driver_name']} ({q_res[0]['lap_time_str']})"
                    )
                    return True
            else:
                next_btn = pygame.Rect(self.width // 2 - 140, self.height - 75, 280, 48)
                if next_btn.collidepoint(mx, my):
                    has_next = mgr.advance_to_next_session()
                    if has_next:
                        self.status_message = f"Proceeding to {mgr.current_session.value}."
                    return True

        # 3. Sprint Race Clicks
        elif mgr.is_sprint:
            live_btn = pygame.Rect(self.width // 2 - 250, self.height - 75, 230, 48)
            quick_btn = pygame.Rect(self.width // 2 + 20, self.height - 75, 230, 48)

            if not mgr.sprint_results:
                if live_btn.collidepoint(mx, my):
                    # Launch Live 2D Track Sprint Simulation
                    grid = mgr.get_starting_grid_for_sprint()
                    self.on_start_live_session("SPRINT", mgr.sprint_laps, grid)
                    return True
                elif quick_btn.collidepoint(mx, my):
                    # Quick Simulate Sprint Race
                    grid = mgr.get_starting_grid_for_sprint()
                    res = self._quick_simulate_race_finish(grid, laps=mgr.sprint_laps)
                    mgr.record_session_completion(RaceWeekendSession.SPRINT, res)
                    self.status_message = f"Sprint Race Complete! Winner: {res[0]['driver_name']}."
                    return True
            else:
                next_btn = pygame.Rect(self.width // 2 - 160, self.height - 75, 320, 48)
                if next_btn.collidepoint(mx, my):
                    has_next = mgr.advance_to_next_session()
                    if not has_next and mgr.tier == 3:
                        # Tier 3 ends after Sprint
                        self._trigger_finish_weekend()
                    return True

        # 4. Main Race Clicks
        elif mgr.is_race:
            live_btn = pygame.Rect(self.width // 2 - 250, self.height - 75, 230, 48)
            quick_btn = pygame.Rect(self.width // 2 + 20, self.height - 75, 230, 48)

            if not mgr.race_results:
                if live_btn.collidepoint(mx, my):
                    # Launch Live 2D Track Main Race Simulation
                    grid = mgr.get_starting_grid_for_main_race()
                    self.on_start_live_session("RACE", mgr.race_laps, grid)
                    return True
                elif quick_btn.collidepoint(mx, my):
                    # Quick Simulate Main Race
                    grid = mgr.get_starting_grid_for_main_race()
                    res = self._quick_simulate_race_finish(grid, laps=mgr.race_laps)
                    mgr.record_session_completion(RaceWeekendSession.RACE, res)
                    self.status_message = f"Grand Prix Complete! Winner: {res[0]['driver_name']}."
                    return True
            else:
                fin_btn = pygame.Rect(self.width // 2 - 160, self.height - 75, 320, 48)
                if fin_btn.collidepoint(mx, my):
                    self._trigger_finish_weekend()
                    return True

        # 5. Weekend Finished View
        elif mgr.is_weekend_completed:
            fin_btn = pygame.Rect(self.width // 2 - 160, self.height - 75, 320, 48)
            if fin_btn.collidepoint(mx, my):
                self._trigger_finish_weekend()
                return True

        return False

    def _trigger_finish_weekend(self):
        """Compiles final weekend points and prize data, returning to HQ."""
        mgr = self.manager
        summary = {
            "weekend_driver_points": mgr.weekend_driver_points,
            "weekend_team_points": mgr.weekend_team_points,
            "sprint_results": mgr.sprint_results,
            "race_results": mgr.race_results,
            "qualifying_results": mgr.qualifying_results,
        }
        self.on_finish_weekend(summary)

    def _build_driver_car_pairs(self) -> List[Tuple[Any, Any]]:
        """Returns active driver/car pairs for qualifying simulation."""
        if self.driver_car_pairs:
            return self.driver_car_pairs
        from ...database.db_manager import DatabaseManager

        return DatabaseManager("race_game.db").get_all_drivers_and_cars()

    def _quick_simulate_race_finish(self, starting_grid: List[Dict[str, Any]], laps: int) -> List[Dict[str, Any]]:
        """Quickly resolves race finishing order with slight overtaking variance."""
        ranked = []
        for g in starting_grid:
            # Score based on starting position + driver pace
            base_score = 100.0 - g.get("sprint_grid_pos", g.get("race_grid_pos", 10)) * 3.5
            if g.get("is_player"):
                # Apply long runs or sprint wear bonus and setup curves
                c_slot = 1 if g.get("number", 1) % 2 != 0 else 2
                bonuses = self.manager.practice_bonuses[c_slot]
                conf = self.manager.setup_confidence[c_slot]
                perf_score, wear_score = self.manager.evaluate_car_setup_scores(c_slot)
                score_bonus = (perf_score - 0.50) * 8.0 + (wear_score - 0.50) * 6.0
                base_score += (conf / 100.0) * 8.0 + score_bonus + bonuses.get("race_wear_bonus", 0.0) * 15.0

            # Variance
            score = base_score + random.uniform(-6.0, 6.0)
            ranked.append((score, g))

        ranked.sort(key=lambda x: x[0], reverse=True)
        results = []
        for pos, (sc, item) in enumerate(ranked, 1):
            r = dict(item)
            r["position"] = pos
            results.append(r)
        return results

    def render(self, surface: pygame.Surface):
        now = pygame.time.get_ticks()
        dt = (now - getattr(self, "last_frame_ticks", now)) / 1000.0
        self.last_frame_ticks = now
        if self.manager.is_practice:
            self.manager.update_fp_traffic(dt)

        surface.fill(UITheme.BG_DARK)
        mgr = self.manager

        # 1. Top Header & Circuit Metadata
        hdr_rect = pygame.Rect(0, 0, self.width, 52)
        pygame.draw.rect(surface, (18, 24, 34), hdr_rect)
        pygame.draw.line(surface, UITheme.PANEL_BORDER, (0, 52), (self.width, 52), 1)

        t_title = f"🏁 {mgr.track_name.upper()} — GRAND PRIX WEEKEND"
        surface.blit(self.font_title.render(t_title, True, UITheme.TEXT_WHITE), (24, 14))

        tier_str = {1: "TIER 1 (WORLD SUPER FORMULA)", 2: "TIER 2 (CONTINENTAL)", 3: "TIER 3 (NATIONAL CUP)"}.get(
            mgr.tier, "TIER 3"
        )
        t_badge = self.font_badge.render(f"[{tier_str}]", True, UITheme.ACCENT_YELLOW)
        surface.blit(t_badge, (self.width - 24 - t_badge.get_width(), 16))

        # 2. Session Stepper Bar
        self._render_session_stepper(surface, 24, 60, self.width - 48, 38)

        # 3. Active Session Specific Content
        if mgr.is_weekend_completed:
            self._render_weekend_summary(surface)
        elif mgr.is_practice:
            self._render_practice_session(surface)
        elif mgr.is_qualifying:
            self._render_qualifying_session(surface)
        elif mgr.is_sprint:
            self._render_sprint_session(surface)
        elif mgr.is_race:
            self._render_race_session(surface)

        # 4. Status Bar
        stat_bar = pygame.Rect(24, self.height - 24, self.width - 48, 20)
        surface.blit(
            self.font_badge.render(f"PIT WALL: {self.status_message}", True, UITheme.ACCENT_CYAN),
            (stat_bar.x, stat_bar.y),
        )

    def _render_session_stepper(self, surface: pygame.Surface, x: int, y: int, w: int, h: int):
        mgr = self.manager
        num_sessions = len(mgr.sessions)
        step_w = (w - (num_sessions - 1) * 8) // num_sessions

        session_labels = {
            RaceWeekendSession.FP1: "1. PRACTICE 1",
            RaceWeekendSession.FP2: "2. PRACTICE 2",
            RaceWeekendSession.QUALIFYING: "3. QUALIFYING" if mgr.tier == 1 else "QUALIFYING",
            RaceWeekendSession.SPRINT: "4. SPRINT (REV-10)" if mgr.tier == 1 else "SPRINT RACE",
            RaceWeekendSession.FP3: "5. RACE FP3",
            RaceWeekendSession.RACE: "6. GRAND PRIX" if mgr.tier == 1 else "GRAND PRIX",
        }

        for idx, sess in enumerate(mgr.sessions):
            sx = x + idx * (step_w + 8)
            s_rect = pygame.Rect(sx, y, step_w, h)
            is_active = idx == mgr.current_session_index and not mgr.is_weekend_completed
            is_done = idx < mgr.current_session_index or mgr.is_weekend_completed

            if is_active:
                pygame.draw.rect(surface, (25, 45, 65), s_rect, border_radius=4)
                pygame.draw.rect(surface, (0, 220, 255), s_rect, width=2, border_radius=4)
                txt_col = (0, 240, 255)
            elif is_done:
                pygame.draw.rect(surface, (18, 30, 24), s_rect, border_radius=4)
                pygame.draw.rect(surface, (0, 180, 100), s_rect, width=1, border_radius=4)
                txt_col = (0, 230, 120)
            else:
                pygame.draw.rect(surface, (18, 22, 28), s_rect, border_radius=4)
                pygame.draw.rect(surface, (35, 42, 52), s_rect, width=1, border_radius=4)
                txt_col = UITheme.TEXT_MUTED

            lbl = session_labels.get(sess, sess.value)
            if is_done:
                lbl = f"✓ {lbl}"
            txt = self.font_card.render(lbl, True, txt_col)
            surface.blit(
                txt,
                (s_rect.x + (s_rect.width - txt.get_width()) // 2, s_rect.y + (s_rect.height - txt.get_height()) // 2),
            )

    def _render_mini_track(self, surface: pygame.Surface, rect: pygame.Rect):
        """Renders prominent live circuit radar with sector splits (S1/S2/S3), speed trap, and active cars."""
        mgr = self.manager
        UITheme.draw_panel(surface, rect)
        p_hdr = pygame.Rect(rect.x, rect.y, rect.width, 24)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, p_hdr, border_top_left_radius=4, border_top_right_radius=4)
        surface.blit(
            self.font_header.render("LIVE CIRCUIT TELEMETRY RADAR — SECTOR ANALYSIS", True, (0, 240, 255)),
            (rect.x + 10, rect.y + 4),
        )

        circuit = mgr.get_circuit()
        if circuit is None or len(circuit.points) < 3:
            surface.blit(
                self.font_body.render("Circuit radar telemetry offline.", True, UITheme.TEXT_MUTED),
                (rect.x + 16, rect.y + 40),
            )
            return

        view_r = pygame.Rect(rect.x + 12, rect.y + 26, rect.width - 24, rect.height - 50)
        pts = circuit.points[:: max(1, len(circuit.points) // 120)]
        min_x = min(p[0] for p in pts)
        max_x = max(p[0] for p in pts)
        min_y = min(p[1] for p in pts)
        max_y = max(p[1] for p in pts)

        bb_w = max(1.0, max_x - min_x)
        bb_h = max(1.0, max_y - min_y)
        scale = min(view_r.width / bb_w, view_r.height / bb_h) * 0.90
        mid_x = (min_x + max_x) / 2.0
        mid_y = (min_y + max_y) / 2.0
        cx = view_r.x + view_r.width / 2.0
        cy = view_r.y + view_r.height / 2.0

        def _to_screen(px: float, py: float) -> Tuple[int, int]:
            return (int(cx + (px - mid_x) * scale), int(cy + (py - mid_y) * scale))

        # Circuit outline with glow underlay
        screen_pts = [_to_screen(p[0], p[1]) for p in pts]
        if len(screen_pts) > 2:
            pygame.draw.lines(surface, (28, 38, 54), True, screen_pts, width=7)

            # 3-Sector colored segments: S1 (Yellow), S2 (Cyan), S3 (Purple)
            n_pts = len(screen_pts)
            s1_end = int(n_pts * 0.35)
            s2_end = int(n_pts * 0.70)

            s1_pts = screen_pts[0 : s1_end + 1]
            s2_pts = screen_pts[s1_end : s2_end + 1]
            s3_pts = screen_pts[s2_end:] + [screen_pts[0]]

            if len(s1_pts) > 1:
                pygame.draw.lines(surface, (255, 205, 30), False, s1_pts, width=3)
            if len(s2_pts) > 1:
                pygame.draw.lines(surface, (0, 220, 240), False, s2_pts, width=3)
            if len(s3_pts) > 1:
                pygame.draw.lines(surface, (190, 85, 255), False, s3_pts, width=3)

        # Pit lane
        if circuit.pit_lane_enabled and len(circuit.pit_points) > 2:
            pit_pts = [_to_screen(p[0], p[1]) for p in circuit.pit_points[:: max(1, len(circuit.pit_points) // 25)]]
            if len(pit_pts) > 1:
                pygame.draw.lines(surface, (140, 120, 40), False, pit_pts, width=2)

        # Start / Finish line
        sf_pos = circuit.get_position(0.0)
        sf_sx, sf_sy = _to_screen(sf_pos[0], sf_pos[1])
        pygame.draw.circle(surface, (255, 255, 255), (sf_sx, sf_sy), 5)
        pygame.draw.circle(surface, (0, 240, 140), (sf_sx, sf_sy), 3)

        # Speed trap marker at 75% track length
        st_pos = circuit.get_position(circuit.length * 0.75)
        st_sx, st_sy = _to_screen(st_pos[0], st_pos[1])
        pygame.draw.circle(surface, (255, 120, 60), (st_sx, st_sy), 3)
        surface.blit(self.font_mini.render("ST", True, (255, 120, 60)), (st_sx + 5, st_sy - 5))

        # Ambient AI traffic
        active_ai = 0
        for car in mgr.fp_cars:
            if not car["in_pit"]:
                active_ai += 1
                c_pos = circuit.get_position(car["dist_m"])
                sx, sy = _to_screen(c_pos[0], c_pos[1])
                pygame.draw.circle(surface, car["color"], (sx, sy), 3)

        # Player Car 1
        st1 = mgr.active_stints.get(1)
        if st1 is not None:
            c1_pos = circuit.get_position(st1.get("dist_m", 0.0))
            sx1, sy1 = _to_screen(c1_pos[0], c1_pos[1])
            pygame.draw.circle(surface, (0, 240, 255), (sx1, sy1), 6)
            pygame.draw.circle(surface, (255, 255, 255), (sx1, sy1), 6, width=1)
            surface.blit(self.font_mini.render("C1", True, (0, 240, 255)), (sx1 + 7, sy1 - 6))

        # Player Car 2
        st2 = mgr.active_stints.get(2)
        if st2 is not None:
            c2_pos = circuit.get_position(st2.get("dist_m", 0.0))
            sx2, sy2 = _to_screen(c2_pos[0], c2_pos[1])
            pygame.draw.circle(surface, (255, 170, 0), (sx2, sy2), 6)
            pygame.draw.circle(surface, (255, 255, 255), (sx2, sy2), 6, width=1)
            surface.blit(self.font_mini.render("C2", True, (255, 170, 0)), (sx2 + 7, sy2 - 6))

        # Traffic & Sector Status Footer
        p1_tag = "🟢 C1 ON TRACK" if st1 else "🅿️ C1 GARAGE"
        p2_tag = "🟠 C2 ON TRACK" if st2 else "🅿️ C2 GARAGE"
        f_txt = f"{p1_tag}  |  {p2_tag}  |  🏎️ {active_ai} AI CARS  |  S1: 28.4s • S2: 32.1s • S3: 24.6s"
        surface.blit(self.font_badge.render(f_txt, True, UITheme.TEXT_MUTED), (rect.x + 10, rect.y + rect.height - 18))

    def _render_tyre_strategy_curves(self, surface: pygame.Surface, rect: pygame.Rect, total_laps: int):
        """Renders multi-compound tyre wear degradation forecast curves with optimal pit window."""
        pygame.draw.rect(surface, (18, 24, 32), rect, border_radius=3)
        pygame.draw.rect(surface, UITheme.PANEL_BORDER, rect, width=1, border_radius=3)

        hdr = pygame.Rect(rect.x, rect.y, rect.width, 24)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, hdr, border_top_left_radius=3, border_top_right_radius=3)
        UITheme.draw_icon(surface, "layers", (hdr.x + 8, hdr.y + 5), color=(0, 220, 255), size=13)
        surface.blit(
            self.font_badge.render("TYRE DEGRADATION FORECAST & OPTIMAL PIT WINDOW", True, (0, 220, 255)),
            (hdr.x + 26, hdr.y + 5),
        )

        chart_r = pygame.Rect(rect.x + 40, rect.y + 32, rect.width - 55, rect.height - 60)
        # Grid lines
        for pct_y in [0.0, 0.25, 0.50, 0.75, 1.0]:
            gy = int(chart_r.bottom - chart_r.height * pct_y)
            pygame.draw.line(surface, (30, 38, 50), (chart_r.x, gy), (chart_r.right, gy), 1)
            lbl = self.font_mini.render(f"{int(pct_y * 100)}%", True, UITheme.TEXT_MUTED)
            surface.blit(lbl, (rect.x + 8, gy - 6))

        # Shaded optimal pit window band (e.g. 38% to 62% of race distance)
        pit_start_lap = max(3, int(total_laps * 0.38))
        pit_end_lap = max(pit_start_lap + 2, int(total_laps * 0.62))
        px1 = chart_r.x + int(chart_r.width * (pit_start_lap / float(total_laps)))
        px2 = chart_r.x + int(chart_r.width * (pit_end_lap / float(total_laps)))
        pit_band = pygame.Rect(px1, chart_r.y, px2 - px1, chart_r.height)

        # Transparent overlay for pit window
        overlay = pygame.Surface((pit_band.width, pit_band.height), pygame.SRCALPHA)
        overlay.fill((0, 240, 140, 35))
        surface.blit(overlay, (pit_band.x, pit_band.y))
        pygame.draw.rect(surface, (0, 240, 140), pit_band, width=1)
        surface.blit(
            self.font_mini.render(f"PIT WINDOW (LAPS {pit_start_lap}-{pit_end_lap})", True, (0, 240, 140)),
            (pit_band.x + 4, chart_r.y + 4),
        )

        # Plot curves for Soft, Medium, Hard
        compounds = [
            ("SOFT", (255, 65, 65), max(8, int(total_laps * 0.55))),
            ("MEDIUM", (255, 205, 30), max(12, int(total_laps * 0.80))),
            ("HARD", (235, 240, 250), max(16, int(total_laps * 1.15))),
        ]

        for _, col, max_laps in compounds:
            pts = []
            for lap in range(total_laps + 1):
                lx = chart_r.x + int(chart_r.width * (lap / float(total_laps)))
                wear_pct = max(0.0, 1.0 - (lap / float(max_laps)) ** 1.3)
                ly = chart_r.bottom - int(chart_r.height * wear_pct)
                pts.append((lx, ly))
            if len(pts) > 1:
                pygame.draw.lines(surface, col, False, pts, width=2)

        # Legend at bottom
        leg_y = rect.bottom - 20
        lx = rect.x + 16
        for name, col, _ in compounds:
            UITheme.draw_tyre(surface, (lx, leg_y), col, size=12)
            surface.blit(self.font_mini.render(name, True, col), (lx + 16, leg_y))
            lx += 75
        rec_str = f"STRATEGY: {'M -> H (1-STOP)' if total_laps >= 18 else 'S -> M (1-STOP)'}"
        surface.blit(self.font_mini.render(rec_str, True, (0, 220, 255)), (rect.right - 180, leg_y))

    def _render_practice_session(self, surface: pygame.Surface):
        mgr = self.manager
        slot = self.active_car_slot

        # A. Car Selector Tabs (Car #1 / Car #2)
        c1_rect = pygame.Rect(24, 110, 120, 28)
        c2_rect = pygame.Rect(150, 110, 120, 28)

        d1_name = self.drivers[0]["name"] if len(self.drivers) > 0 else "Car 1"
        d2_name = self.drivers[1]["name"] if len(self.drivers) > 1 else "Car 2"

        c1_status = "🏎️" if mgr.is_car_on_track(1) else "🅿️"
        c2_status = "🏎️" if mgr.is_car_on_track(2) else "🅿️"

        pygame.draw.rect(surface, (30, 48, 70) if slot == 1 else (18, 24, 32), c1_rect, border_radius=3)
        pygame.draw.rect(surface, (0, 220, 255) if slot == 1 else (40, 50, 65), c1_rect, width=1, border_radius=3)
        t1 = self.font_card.render(
            f"CAR #1 {c1_status}: {d1_name[:7]}", True, (0, 220, 255) if slot == 1 else UITheme.TEXT_MUTED
        )
        surface.blit(t1, (c1_rect.x + (c1_rect.width - t1.get_width()) // 2, c1_rect.y + 6))

        pygame.draw.rect(surface, (30, 48, 70) if slot == 2 else (18, 24, 32), c2_rect, border_radius=3)
        pygame.draw.rect(surface, (0, 220, 255) if slot == 2 else (40, 50, 65), c2_rect, width=1, border_radius=3)
        t2 = self.font_card.render(
            f"CAR #2 {c2_status}: {d2_name[:7]}", True, (0, 220, 255) if slot == 2 else UITheme.TEXT_MUTED
        )
        surface.blit(t2, (c2_rect.x + (c2_rect.width - t2.get_width()) // 2, c2_rect.y + 6))

        # Session Clock Badge
        rem_m = float(mgr.session_time_remaining)
        total_laps = mgr.session_laps_completed.get(1, 0) + mgr.session_laps_completed.get(2, 0)
        timer_rect = pygame.Rect(280, 110, 224, 28)
        if rem_m <= 0.0:
            pygame.draw.rect(surface, (50, 20, 20), timer_rect, border_radius=3)
            pygame.draw.rect(surface, (255, 70, 70), timer_rect, width=1, border_radius=3)
            txt_t = self.font_badge.render("🏁 CHEQUERED FLAG (0:00)", True, (255, 100, 100))
        else:
            t_col = (0, 240, 140) if rem_m > 25.0 else ((255, 205, 30) if rem_m > 10.0 else (255, 100, 50))
            pygame.draw.rect(surface, (20, 28, 38), timer_rect, border_radius=3)
            pygame.draw.rect(surface, (40, 55, 75), timer_rect, width=1, border_radius=3)
            txt_t = self.font_badge.render(f"⏱️ SESSION: {int(rem_m)}m LEFT | {total_laps} LAPS", True, t_col)
        surface.blit(txt_t, (timer_rect.x + (timer_rect.width - txt_t.get_width()) // 2, timer_rect.y + 7))

        # B. Setup Tuning Panel (Left)
        setup_rect = pygame.Rect(24, 150, 480, 260)
        UITheme.draw_panel(surface, setup_rect)
        is_fp3_race_prep = mgr.current_session == RaceWeekendSession.FP3
        h_title = (
            f"CAR #{slot} FP3 RACE FINE-TUNING (POST-SPRINT SETUP)"
            if is_fp3_race_prep
            else f"CAR #{slot} MECHANICAL & AERO SETUP"
        )
        h_col = (255, 215, 0) if is_fp3_race_prep else UITheme.ACCENT_CYAN
        surface.blit(self.font_header.render(h_title, True, h_col), (setup_rect.x + 12, setup_rect.y + 6))

        cur_setup = mgr.car_setups[slot]
        guidance_ranges = mgr.get_setup_guidance_ranges(slot)

        param_configs = [
            ("Front Wing Angle", "front_wing", cur_setup.front_wing, 0.0, 100.0, ""),
            ("Rear Wing Angle", "rear_wing", cur_setup.rear_wing, 0.0, 100.0, ""),
            ("Suspension Stiffness", "suspension", cur_setup.suspension, 0.0, 100.0, ""),
            ("Gear Ratio Spread", "gear_ratio", cur_setup.gear_ratio, 0.0, 100.0, ""),
            ("Brake Bias", "brake_bias", cur_setup.brake_bias, 50.0, 65.0, "%"),
        ]

        for idx, (label, p_key, val, min_v, max_v, unit) in enumerate(param_configs):
            row_y = setup_rect.y + 36 + idx * 36
            surface.blit(self.font_body.render(label, True, UITheme.TEXT_WHITE), (setup_rect.x + 14, row_y + 4))

            # Minus Button
            btn_minus = pygame.Rect(setup_rect.x + 150, row_y + 2, 26, 22)
            pygame.draw.rect(surface, (28, 36, 48), btn_minus, border_radius=2)
            surface.blit(self.font_btn.render("-", True, UITheme.TEXT_WHITE), (btn_minus.x + 8, btn_minus.y + 2))

            # Track
            track_r = pygame.Rect(setup_rect.x + 185, row_y + 8, 170, 10)
            pygame.draw.rect(surface, (16, 20, 28), track_r, border_radius=3)

            # Setup Analytics guidance target range overlay
            if guidance_ranges and p_key in guidance_ranges:
                g_min, g_max = guidance_ranges[p_key]
                g_pct_min = max(0.0, min(1.0, (g_min - min_v) / (max_v - min_v)))
                g_pct_max = max(0.0, min(1.0, (g_max - min_v) / (max_v - min_v)))
                g_x = track_r.x + int(track_r.width * g_pct_min)
                g_w = max(4, int(track_r.width * (g_pct_max - g_pct_min)))
                target_rect = pygame.Rect(g_x, track_r.y - 2, g_w, track_r.height + 4)
                pygame.draw.rect(surface, (30, 80, 50), target_rect, border_radius=2)
                pygame.draw.rect(surface, (0, 255, 150), target_rect, width=1, border_radius=2)

            fill_pct = max(0.0, min(1.0, (val - min_v) / (max_v - min_v)))
            fill_r = pygame.Rect(track_r.x, track_r.y, int(track_r.width * fill_pct), track_r.height)
            pygame.draw.rect(surface, (0, 220, 255), fill_r, border_radius=3)

            # Plus Button
            btn_plus = pygame.Rect(setup_rect.x + 365, row_y + 2, 26, 22)
            pygame.draw.rect(surface, (28, 36, 48), btn_plus, border_radius=2)
            surface.blit(self.font_btn.render("+", True, UITheme.TEXT_WHITE), (btn_plus.x + 8, btn_plus.y + 2))

            # Value Label & Target guidance badge
            val_txt = f"{val:.1f}{unit}"
            surface.blit(self.font_badge.render(val_txt, True, (255, 215, 0)), (setup_rect.x + 396, row_y + 4))

            if guidance_ranges and p_key in guidance_ranges:
                g_min, g_max = guidance_ranges[p_key]
                target_str = f"[{g_min:.0f}-{g_max:.0f}]"
                surface.blit(self.font_mini.render(target_str, True, (0, 255, 150)), (setup_rect.x + 438, row_y + 5))

        # Setup Preset Utility Buttons inside Setup Panel
        btn_save = pygame.Rect(setup_rect.x + 10, setup_rect.y + 222, 105, 28)
        btn_load = pygame.Rect(setup_rect.x + 122, setup_rect.y + 222, 105, 28)
        btn_factory = pygame.Rect(setup_rect.x + 234, setup_rect.y + 222, 115, 28)
        btn_copy = pygame.Rect(setup_rect.x + 356, setup_rect.y + 222, 114, 28)
        other_slot = 2 if slot == 1 else 1

        for b_r, b_txt, b_col in [
            (btn_save, "💾 SAVE SETUP", UITheme.ACCENT_CYAN),
            (btn_load, "📂 LOAD SETUP", (255, 215, 0)),
            (btn_factory, "🏭 FACTORY", (0, 240, 140)),
            (btn_copy, f"📋 TO CAR {other_slot}", UITheme.TEXT_WHITE),
        ]:
            pygame.draw.rect(surface, (24, 32, 44), b_r, border_radius=3)
            pygame.draw.rect(surface, (45, 58, 75), b_r, width=1, border_radius=3)
            surface.blit(
                self.font_badge.render(b_txt, True, b_col),
                (b_r.x + (b_r.width - self.font_badge.size(b_txt)[0]) // 2, b_r.y + 7),
            )

        # C. Live Circuit Mini-Track Radar (Bottom Left - replaces old plan selector)
        track_panel = pygame.Rect(24, 425, 480, 175)
        self._render_mini_track(surface, track_panel)

        # D. Driver Feedback & Confidence Gauge (Right)
        fb_rect = pygame.Rect(520, 150, self.width - 544, 450)
        UITheme.draw_panel(surface, fb_rect)
        fb_hdr = pygame.Rect(fb_rect.x, fb_rect.y, fb_rect.width, 28)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, fb_hdr, border_top_left_radius=4, border_top_right_radius=4)

        active_stint = mgr.active_stints.get(slot)
        if active_stint is not None:
            surface.blit(
                self.font_header.render(f"CAR #{slot} — STINT IN PROGRESS ON CIRCUIT", True, (0, 240, 255)),
                (fb_rect.x + 12, fb_rect.y + 6),
            )

            # Active Stint Info Card
            st_type = active_stint["stint_type"]
            t_rem = active_stint["time_remaining_min"]
            t_tot = max(0.1, active_stint["total_duration_min"])
            l_tgt = active_stint["laps_target"]
            prog = max(0.0, min(1.0, 1.0 - (t_rem / t_tot)))

            surface.blit(
                self.font_card.render(f"ACTIVE RUN PROGRAM: {st_type} STINT", True, (255, 215, 0)),
                (fb_rect.x + 16, fb_rect.y + 42),
            )
            surface.blit(
                self.font_body.render(
                    f"Target Laps: {l_tgt} Laps | Expected Duration: ~{t_tot:.0f} Minutes", True, UITheme.TEXT_WHITE
                ),
                (fb_rect.x + 16, fb_rect.y + 66),
            )

            # Progress Bar
            surface.blit(
                self.font_badge.render(
                    f"STINT PROGRESS: {int(prog * 100)}% ({t_rem:.1f}m remaining)", True, (0, 240, 140)
                ),
                (fb_rect.x + 16, fb_rect.y + 96),
            )
            prog_bar = pygame.Rect(fb_rect.x + 16, fb_rect.y + 116, fb_rect.width - 32, 16)
            pygame.draw.rect(surface, (16, 22, 30), prog_bar, border_radius=3)
            fill_w = int(prog_bar.width * prog)
            pygame.draw.rect(surface, (0, 220, 255), (prog_bar.x, prog_bar.y, fill_w, prog_bar.height), border_radius=3)

            # Live Notice Box
            notice_rect = pygame.Rect(fb_rect.x + 16, fb_rect.y + 152, fb_rect.width - 32, 140)
            pygame.draw.rect(surface, (16, 24, 34), notice_rect, border_radius=4)
            pygame.draw.rect(surface, (35, 52, 75), notice_rect, width=1, border_radius=4)

            surface.blit(
                self.font_card.render("📡 LIVE PIT WALL TELEMETRY STREAM", True, (0, 240, 255)),
                (notice_rect.x + 14, notice_rect.y + 12),
            )
            notice_lines = [
                "• Car is completing scheduled laps out on circuit.",
                "• Driver radio debrief is deferred until the car returns to garage.",
                "• Mechanical feel, tire degradation rate (%/lap), and wear balance",
                "  will be compiled and unlocked once the stint concludes.",
                "",
                "💡 Tip: Click '⏩ FAST FORWARD' below to advance directly to stint completion!",
            ]
            for idx, n_line in enumerate(notice_lines):
                col = (0, 240, 140) if "Tip:" in n_line else UITheme.TEXT_MUTED
                surface.blit(
                    self.font_body.render(n_line, True, col), (notice_rect.x + 14, notice_rect.y + 36 + idx * 18)
                )

        else:
            # In Garage: Show Full Telemetry & Completed Debrief
            surface.blit(
                self.font_header.render(f"CAR #{slot} TELEMETRY & DRIVER RADIO FEEDBACK", True, UITheme.ACCENT_CYAN),
                (fb_rect.x + 12, fb_rect.y + 6),
            )

            # Confidence Gauge
            conf = mgr.setup_confidence[slot]
            surface.blit(
                self.font_card.render(f"SETUP CONFIDENCE: {conf:.1f}%", True, (255, 215, 0)),
                (fb_rect.x + 16, fb_rect.y + 36),
            )
            gauge_bar = pygame.Rect(fb_rect.x + 16, fb_rect.y + 56, fb_rect.width - 32, 14)
            pygame.draw.rect(surface, (16, 20, 26), gauge_bar, border_radius=3)
            fill_w = int(gauge_bar.width * (conf / 100.0))
            g_col = (0, 240, 140) if conf > 75 else ((255, 200, 40) if conf > 45 else (240, 70, 70))
            pygame.draw.rect(surface, g_col, (gauge_bar.x, gauge_bar.y, fill_w, gauge_bar.height), border_radius=3)

            # Setup Curve Potential Ratings
            perf_score, wear_score = mgr.evaluate_car_setup_scores(slot)
            p_pct = int(perf_score * 100)
            w_pct = int(wear_score * 100)
            p_col = (0, 240, 255) if p_pct > 80 else ((255, 205, 30) if p_pct > 60 else (240, 70, 70))
            w_col = (0, 240, 140) if w_pct > 80 else ((255, 205, 30) if w_pct > 60 else (240, 70, 70))
            surface.blit(
                self.font_badge.render(f"⚡ FLYING PACE POTENTIAL: {p_pct}%", True, p_col),
                (fb_rect.x + 16, fb_rect.y + 76),
            )
            surface.blit(
                self.font_badge.render(f"🛡️ TIRE PRESERVATION: {w_pct}%", True, w_col),
                (fb_rect.x + 230, fb_rect.y + 76),
            )

            # Plan bonuses list
            bonuses = mgr.practice_bonuses[slot]
            b_txt = f"Accumulated Bonuses: Qualy Pace: +{bonuses['qualy_pace_bonus']:.2f}s | Sprint Wear: -{bonuses['sprint_wear_bonus'] * 100:.0f}% | Race Wear: -{bonuses['race_wear_bonus'] * 100:.0f}% | Fuel: -{bonuses['fuel_saving_bonus'] * 100:.0f}%"
            surface.blit(self.font_badge.render(b_txt, True, UITheme.TEXT_MUTED), (fb_rect.x + 16, fb_rect.y + 98))

            # Recent Feedback items
            fb_list = mgr.driver_feedback[slot]
            surface.blit(
                self.font_header.render("RADIO DEBRIEF & COMMENTS:", True, UITheme.TEXT_WHITE),
                (fb_rect.x + 16, fb_rect.y + 120),
            )

            y_cursor = fb_rect.y + 142
            if not fb_list:
                surface.blit(
                    self.font_body.render(
                        "Car is currently in pit garage. Choose a stint below to dispatch the driver on track.",
                        True,
                        UITheme.TEXT_MUTED,
                    ),
                    (fb_rect.x + 16, y_cursor),
                )
            else:
                latest = fb_list[-1]
                surface.blit(
                    self.font_card.render(
                        f'Latest Stint ({latest.get("stint_type", "RUN")}): "{latest["summary_quote"]}"',
                        True,
                        (0, 240, 140),
                    ),
                    (fb_rect.x + 16, y_cursor),
                )
                y_cursor += 24
                for pt in latest["feedback_points"][:6]:
                    surface.blit(self.font_body.render(f"• {pt}", True, UITheme.TEXT_WHITE), (fb_rect.x + 20, y_cursor))
                    y_cursor += 20

        # E. Practice Stint Action Buttons & Time Hop (Bottom Bar)
        mx, my = pygame.mouse.get_pos()
        btn_short = pygame.Rect(24, self.height - 75, 150, 48)
        btn_sprint = pygame.Rect(182, self.height - 75, 155, 48)
        btn_long = pygame.Rect(345, self.height - 75, 160, 48)
        btn_fast_forward = pygame.Rect(520, self.height - 75, 330, 48)
        next_btn = pygame.Rect(865, self.height - 75, max(210, self.width - 889), 48)

        can_run = rem_m > 0.0
        car_on_track = mgr.is_car_on_track(slot)
        can_start_stint = can_run and not car_on_track

        short_laps = mgr.stint_laps.get("SHORT", 5)
        sprint_laps = mgr.stint_laps.get("SPRINT", 12)
        long_laps = mgr.stint_laps.get("LONG", 22)

        # 1. Short Stint button
        is_sh_hov = can_start_stint and btn_short.collidepoint(mx, my)
        bg_sh = (0, 180, 100) if is_sh_hov else ((0, 150, 85) if can_start_stint else (24, 30, 28))
        pygame.draw.rect(surface, bg_sh, btn_short, border_radius=4)
        pygame.draw.rect(
            surface, (0, 240, 140) if can_start_stint else (45, 55, 50), btn_short, width=1, border_radius=4
        )
        s_lbl = "CAR ON TRACK" if car_on_track else f"🏎️ SHORT ({short_laps}L)"
        t_s1 = self.font_btn.render(s_lbl, True, (10, 25, 15) if can_start_stint else UITheme.TEXT_MUTED)
        t_s2 = self.font_badge.render("~10 MIN STINT", True, (10, 35, 20) if can_start_stint else (60, 70, 65))
        surface.blit(t_s1, (btn_short.x + (btn_short.width - t_s1.get_width()) // 2, btn_short.y + 8))
        surface.blit(t_s2, (btn_short.x + (btn_short.width - t_s2.get_width()) // 2, btn_short.y + 28))

        # 2. Sprint Stint button
        pygame.draw.rect(surface, (20, 95, 140) if can_start_stint else (24, 28, 34), btn_sprint, border_radius=4)
        pygame.draw.rect(
            surface, (0, 220, 255) if can_start_stint else (45, 50, 60), btn_sprint, width=1, border_radius=4
        )
        m_lbl = "CAR ON TRACK" if car_on_track else f"🛡️ SPRINT ({sprint_laps}L)"
        t_m1 = self.font_btn.render(m_lbl, True, (10, 20, 30) if can_start_stint else UITheme.TEXT_MUTED)
        t_m2 = self.font_badge.render("~20 MIN STINT", True, (10, 30, 45) if can_start_stint else (60, 65, 75))
        surface.blit(t_m1, (btn_sprint.x + (btn_sprint.width - t_m1.get_width()) // 2, btn_sprint.y + 8))
        surface.blit(t_m2, (btn_sprint.x + (btn_sprint.width - t_m2.get_width()) // 2, btn_sprint.y + 28))

        # 3. Race Sim Long Stint button (Tier 1 & 2 only)
        can_race_sim = can_start_stint and mgr.tier < 3
        pygame.draw.rect(surface, (110, 50, 130) if can_race_sim else (24, 22, 28), btn_long, border_radius=4)
        pygame.draw.rect(surface, (210, 110, 255) if can_race_sim else (45, 40, 52), btn_long, width=1, border_radius=4)
        l_lbl = "CAR ON TRACK" if car_on_track else f"🏁 RACE SIM ({long_laps}L)"
        t_l1 = self.font_btn.render(l_lbl, True, (25, 10, 30) if can_race_sim else (90, 80, 100))
        sub_txt = "~32 MIN STINT" if mgr.tier < 3 else "[TIER 1/2 GP ONLY]"
        t_l2 = self.font_badge.render(sub_txt, True, (35, 15, 45) if can_race_sim else (90, 80, 100))
        surface.blit(t_l1, (btn_long.x + (btn_long.width - t_l1.get_width()) // 2, btn_long.y + 8))
        surface.blit(t_l2, (btn_long.x + (btn_long.width - t_l2.get_width()) // 2, btn_long.y + 28))

        # 4. Fast Forward / Hop in Time button
        running_stints = [s for s in mgr.active_stints.values() if s is not None]
        if running_stints:
            earliest = min(running_stints, key=lambda s: s["time_remaining_min"])
            e_slot = earliest["car_slot"]
            e_rem = earliest["time_remaining_min"]
            ff_title = f"⏩ FAST FORWARD (CAR #{e_slot} FINISH)"
            ff_sub = f"Advance {e_rem:.0f}m forward to next stint completion"
            pygame.draw.rect(surface, (35, 75, 105), btn_fast_forward, border_radius=4)
            pygame.draw.rect(surface, (0, 240, 255), btn_fast_forward, width=2, border_radius=4)
            t_ff1 = self.font_btn.render(ff_title, True, (0, 240, 255))
            t_ff2 = self.font_badge.render(ff_sub, True, (160, 220, 255))
        elif can_run:
            ff_title = "⏩ ADVANCE TIME (+5 MIN)"
            ff_sub = "Simulate 5 minutes of Free Practice session"
            pygame.draw.rect(surface, (25, 35, 48), btn_fast_forward, border_radius=4)
            pygame.draw.rect(surface, (50, 70, 95), btn_fast_forward, width=1, border_radius=4)
            t_ff1 = self.font_btn.render(ff_title, True, UITheme.TEXT_WHITE)
            t_ff2 = self.font_badge.render(ff_sub, True, UITheme.TEXT_MUTED)
        else:
            ff_title = "🏁 FREE PRACTICE EXPIRED"
            ff_sub = "Chequered flag dropped — proceed to Qualifying"
            pygame.draw.rect(surface, (35, 20, 20), btn_fast_forward, border_radius=4)
            pygame.draw.rect(surface, (80, 40, 40), btn_fast_forward, width=1, border_radius=4)
            t_ff1 = self.font_btn.render(ff_title, True, (255, 100, 100))
            t_ff2 = self.font_badge.render(ff_sub, True, (180, 80, 80))

        surface.blit(
            t_ff1, (btn_fast_forward.x + (btn_fast_forward.width - t_ff1.get_width()) // 2, btn_fast_forward.y + 8)
        )
        surface.blit(
            t_ff2, (btn_fast_forward.x + (btn_fast_forward.width - t_ff2.get_width()) // 2, btn_fast_forward.y + 28)
        )

        # 5. Next Session button
        pygame.draw.rect(surface, (30, 55, 80), next_btn, border_radius=4)
        pygame.draw.rect(surface, (0, 220, 255), next_btn, width=1, border_radius=4)
        next_lbl = (
            "PROCEED TO GRAND PRIX >>"
            if mgr.current_session == RaceWeekendSession.FP3
            else "PROCEED TO NEXT SESSION >>"
        )
        t_next = self.font_big_btn.render(next_lbl, True, UITheme.TEXT_WHITE)
        surface.blit(t_next, (next_btn.x + (next_btn.width - t_next.get_width()) // 2, next_btn.y + 14))

    def _render_qualifying_session(self, surface: pygame.Surface):
        mgr = self.manager
        q_results = mgr.qualifying_results

        # Header Info Card
        info_rect = pygame.Rect(24, 110, self.width - 48, 55)
        UITheme.draw_panel(surface, info_rect)
        surface.blit(
            self.font_header.render("⏱️ OFFICIAL QUALIFYING SHOOTOUT (SINGLE-LAP FLYING HOT LAP)", True, (255, 215, 0)),
            (info_rect.x + 14, info_rect.y + 10),
        )
        surface.blit(
            self.font_body.render(
                "All 20 cars take to the track on low fuel and soft tires. Flying lap times establish the grid.",
                True,
                UITheme.TEXT_MUTED,
            ),
            (info_rect.x + 14, info_rect.y + 30),
        )

        if not q_results:
            # Action to run qualifying
            sim_q_btn = pygame.Rect(self.width // 2 - 220, self.height // 2 - 30, 440, 60)
            pygame.draw.rect(surface, (0, 180, 100), sim_q_btn, border_radius=6)
            pygame.draw.rect(surface, (0, 255, 140), sim_q_btn, width=2, border_radius=6)
            q_txt = self.font_big_btn.render("⏱️ SIMULATE QUALIFYING SHOOTOUT >>", True, (10, 25, 15))
            surface.blit(q_txt, (sim_q_btn.x + (sim_q_btn.width - q_txt.get_width()) // 2, sim_q_btn.y + 18))
        else:
            # Leaderboard Table
            board_rect = pygame.Rect(24, 175, self.width - 48, self.height - 270)
            UITheme.draw_panel(surface, board_rect)
            b_hdr = pygame.Rect(board_rect.x, board_rect.y, board_rect.width, 28)
            pygame.draw.rect(surface, UITheme.PANEL_HEADER, b_hdr, border_top_left_radius=4, border_top_right_radius=4)
            surface.blit(
                self.font_header.render("QUALIFYING CLASSIFICATION (POLE TO P20)", True, (0, 220, 255)),
                (board_rect.x + 14, board_rect.y + 6),
            )

            y_pos = board_rect.y + 34
            col_w = (board_rect.width - 28) // 2

            for idx, entry in enumerate(q_results[:20]):
                col_x = board_rect.x + 14 if idx < 10 else board_rect.x + 14 + col_w + 10
                row_y = y_pos + (idx % 10) * 28

                row_r = pygame.Rect(col_x, row_y, col_w - 10, 24)
                is_p = entry.get("is_player", False)
                pygame.draw.rect(surface, (30, 48, 65) if is_p else (18, 24, 30), row_r, border_radius=2)
                if is_p:
                    pygame.draw.rect(surface, (0, 220, 255), row_r, width=1, border_radius=2)

                pos_str = f"P{entry['position']:02d}"
                surface.blit(
                    self.font_card.render(
                        pos_str, True, (255, 215, 0) if entry["position"] <= 3 else UITheme.TEXT_WHITE
                    ),
                    (row_r.x + 6, row_r.y + 4),
                )

                d_str = f"{entry['driver_name']} ({entry['team_name'][:12]})"
                surface.blit(
                    self.font_body.render(d_str, True, (0, 240, 255) if is_p else UITheme.TEXT_WHITE),
                    (row_r.x + 46, row_r.y + 4),
                )

                time_str = entry["lap_time_str"]
                gap_str = "POLE" if entry["position"] == 1 else f"+{entry['gap_to_pole']:.3f}s"
                surface.blit(
                    self.font_badge.render(
                        f"{time_str}  [{gap_str}]",
                        True,
                        (0, 240, 140) if entry["position"] == 1 else UITheme.TEXT_MUTED,
                    ),
                    (row_r.x + row_r.width - 130, row_r.y + 4),
                )

            # Proceed Button
            next_btn = pygame.Rect(self.width // 2 - 140, self.height - 75, 280, 48)
            pygame.draw.rect(surface, (0, 180, 100), next_btn, border_radius=4)
            pygame.draw.rect(surface, (0, 255, 140), next_btn, width=2, border_radius=4)
            q_next_lbl = "PROCEED TO SPRINT RACE >>" if mgr.tier in [1, 3] else "PROCEED TO GRAND PRIX >>"
            t_next = self.font_big_btn.render(q_next_lbl, True, (10, 25, 15))
            surface.blit(t_next, (next_btn.x + (next_btn.width - t_next.get_width()) // 2, next_btn.y + 14))

    def _render_sprint_session(self, surface: pygame.Surface):
        mgr = self.manager
        # Starting Grid Preview
        grid = mgr.get_starting_grid_for_sprint()

        info_rect = pygame.Rect(24, 110, self.width - 48, 55)
        UITheme.draw_panel(surface, info_rect)
        rev_tag = " [TOP 10 IN REVERSE GRID!]" if mgr.tier == 1 else ""
        surface.blit(
            self.font_header.render(f"🏎️ SPRINT RACE — {mgr.sprint_laps} LAPS{rev_tag}", True, (255, 215, 0)),
            (info_rect.x + 14, info_rect.y + 10),
        )
        surface.blit(
            self.font_body.render(
                "Short sprint distance. Feasible on 0 stops with Hard tires, or an aggressive 1-stop with Softs.",
                True,
                UITheme.TEXT_MUTED,
            ),
            (info_rect.x + 14, info_rect.y + 30),
        )

        if not mgr.sprint_results:
            # Show Starting Grid
            self._render_grid_table(surface, grid, is_sprint=True)

            # Start Live & Quick Sim Buttons
            live_btn = pygame.Rect(self.width // 2 - 250, self.height - 75, 230, 48)
            pygame.draw.rect(surface, (0, 180, 100), live_btn, border_radius=4)
            pygame.draw.rect(surface, (0, 255, 140), live_btn, width=2, border_radius=4)
            t_live = self.font_big_btn.render("🏁 START LIVE SPRINT", True, (10, 25, 15))
            surface.blit(t_live, (live_btn.x + (live_btn.width - t_live.get_width()) // 2, live_btn.y + 14))

            quick_btn = pygame.Rect(self.width // 2 + 20, self.height - 75, 230, 48)
            pygame.draw.rect(surface, (35, 55, 80), quick_btn, border_radius=4)
            pygame.draw.rect(surface, (0, 220, 255), quick_btn, width=1, border_radius=4)
            t_quick = self.font_btn.render("⚡ QUICK SIMULATE", True, UITheme.TEXT_WHITE)
            surface.blit(t_quick, (quick_btn.x + (quick_btn.width - t_quick.get_width()) // 2, quick_btn.y + 16))
        else:
            # Show sprint classification
            self._render_classification_table(surface, mgr.sprint_results, is_sprint=True)
            next_btn = pygame.Rect(self.width // 2 - 160, self.height - 75, 320, 48)
            pygame.draw.rect(surface, (0, 180, 100), next_btn, border_radius=4)
            lbl = "COMPLETE WEEKEND >>" if mgr.tier == 3 else "PROCEED TO FP3 (RACE TUNING) >>"
            t_next = self.font_big_btn.render(lbl, True, (10, 25, 15))
            surface.blit(t_next, (next_btn.x + (next_btn.width - t_next.get_width()) // 2, next_btn.y + 14))

    def _render_race_session(self, surface: pygame.Surface):
        mgr = self.manager
        grid = mgr.get_starting_grid_for_main_race()

        info_rect = pygame.Rect(24, 110, self.width - 48, 55)
        UITheme.draw_panel(surface, info_rect)
        surface.blit(
            self.font_header.render(f"🏆 GRAND PRIX — {mgr.race_laps} LAPS (2-3 PIT STOPS)", True, (255, 215, 0)),
            (info_rect.x + 14, info_rect.y + 10),
        )
        surface.blit(
            self.font_body.render(
                "Full Grand Prix distance requiring multi-stop pit strategy, tire degradation management, and undercut timing.",
                True,
                UITheme.TEXT_MUTED,
            ),
            (info_rect.x + 14, info_rect.y + 30),
        )

        if not mgr.race_results:
            # Show Starting Grid
            self._render_grid_table(surface, grid, is_sprint=False)

            # Buttons
            live_btn = pygame.Rect(self.width // 2 - 250, self.height - 75, 230, 48)
            pygame.draw.rect(surface, (0, 180, 100), live_btn, border_radius=4)
            pygame.draw.rect(surface, (0, 255, 140), live_btn, width=2, border_radius=4)
            t_live = self.font_big_btn.render("🏁 START GRAND PRIX", True, (10, 25, 15))
            surface.blit(t_live, (live_btn.x + (live_btn.width - t_live.get_width()) // 2, live_btn.y + 14))

            quick_btn = pygame.Rect(self.width // 2 + 20, self.height - 75, 230, 48)
            pygame.draw.rect(surface, (35, 55, 80), quick_btn, border_radius=4)
            pygame.draw.rect(surface, (0, 220, 255), quick_btn, width=1, border_radius=4)
            t_quick = self.font_btn.render("⚡ QUICK SIMULATE", True, UITheme.TEXT_WHITE)
            surface.blit(t_quick, (quick_btn.x + (quick_btn.width - t_quick.get_width()) // 2, quick_btn.y + 16))
        else:
            self._render_classification_table(surface, mgr.race_results, is_sprint=False)
            fin_btn = pygame.Rect(self.width // 2 - 160, self.height - 75, 320, 48)
            pygame.draw.rect(surface, (0, 180, 100), fin_btn, border_radius=4)
            t_fin = self.font_big_btn.render("COMPLETE WEEKEND >>", True, (10, 25, 15))
            surface.blit(t_fin, (fin_btn.x + (fin_btn.width - t_fin.get_width()) // 2, fin_btn.y + 14))

    def _render_grid_table(self, surface: pygame.Surface, grid: List[Dict[str, Any]], is_sprint: bool):
        col_w = min(480, (self.width - 64) // 2)
        grid_rect = pygame.Rect(24, 175, col_w, self.height - 265)
        UITheme.draw_panel(surface, grid_rect)
        b_hdr = pygame.Rect(grid_rect.x, grid_rect.y, grid_rect.width, 28)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, b_hdr, border_top_left_radius=4, border_top_right_radius=4)
        title = "OFFICIAL SPRINT STARTING GRID" if is_sprint else "OFFICIAL GRAND PRIX STARTING GRID"
        surface.blit(self.font_header.render(title, True, (0, 220, 255)), (grid_rect.x + 14, grid_rect.y + 6))

        y_pos = grid_rect.y + 34
        sub_col_w = (grid_rect.width - 24) // 2

        for idx, entry in enumerate(grid[:20]):
            col_x = grid_rect.x + 8 if idx < 10 else grid_rect.x + 8 + sub_col_w + 8
            row_y = y_pos + (idx % 10) * 28

            row_r = pygame.Rect(col_x, row_y, sub_col_w, 24)
            is_p = entry.get("is_player", False)
            pygame.draw.rect(surface, (30, 48, 65) if is_p else (18, 24, 30), row_r, border_radius=2)
            if is_p:
                pygame.draw.rect(surface, (0, 220, 255), row_r, width=1, border_radius=2)

            pos_key = "sprint_grid_pos" if is_sprint else "race_grid_pos"
            pos_num = entry.get(pos_key, idx + 1)
            pos_str = f"P{pos_num:02d}"
            surface.blit(
                self.font_card.render(pos_str, True, (255, 215, 0) if pos_num <= 3 else UITheme.TEXT_WHITE),
                (row_r.x + 4, row_r.y + 4),
            )

            d_name = entry.get("driver_name", "Driver")[:10]
            d_str = f"{d_name} ({entry.get('team_name', 'Team')[:7]})"
            surface.blit(
                self.font_body.render(d_str, True, (0, 240, 255) if is_p else UITheme.TEXT_WHITE),
                (row_r.x + 36, row_r.y + 4),
            )

            if is_sprint and entry.get("is_reversed_grid", False):
                surface.blit(
                    self.font_mini.render("[REV]", True, (255, 180, 40)),
                    (row_r.right - 35, row_r.y + 5),
                )

        # Right Column: Large Prominent Circuit Map & Tyre Strategy Curves
        right_x = grid_rect.right + 16
        right_w = self.width - right_x - 24
        right_h = grid_rect.height

        map_h = max(180, (right_h - 12) // 2)
        big_map_rect = pygame.Rect(right_x, 175, right_w, map_h)
        self._render_mini_track(surface, big_map_rect)

        tyre_rect = pygame.Rect(right_x, 175 + map_h + 12, right_w, right_h - map_h - 12)
        total_laps = self.manager.sprint_laps if is_sprint else self.manager.race_laps
        self._render_tyre_strategy_curves(surface, tyre_rect, total_laps)

    def _render_classification_table(self, surface: pygame.Surface, results: List[Dict[str, Any]], is_sprint: bool):
        board_rect = pygame.Rect(24, 175, self.width - 48, self.height - 270)
        UITheme.draw_panel(surface, board_rect)
        b_hdr = pygame.Rect(board_rect.x, board_rect.y, board_rect.width, 28)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, b_hdr, border_top_left_radius=4, border_top_right_radius=4)
        t_lbl = "SPRINT RACE CLASSIFICATION & POINTS" if is_sprint else "GRAND PRIX CLASSIFICATION & POINTS"
        surface.blit(self.font_header.render(t_lbl, True, (0, 240, 140)), (board_rect.x + 14, board_rect.y + 6))

        y_pos = board_rect.y + 34
        col_w = (board_rect.width - 28) // 2

        pts_table = self.manager.SPRINT_POINTS if is_sprint else self.manager.RACE_POINTS

        for idx, entry in enumerate(results[:20]):
            col_x = board_rect.x + 14 if idx < 10 else board_rect.x + 14 + col_w + 10
            row_y = y_pos + (idx % 10) * 28

            row_r = pygame.Rect(col_x, row_y, col_w - 10, 24)
            is_p = entry.get("is_player", False)
            pygame.draw.rect(surface, (30, 48, 65) if is_p else (18, 24, 30), row_r, border_radius=2)
            if is_p:
                pygame.draw.rect(surface, (0, 220, 255), row_r, width=1, border_radius=2)

            pos_num = entry.get("position", idx + 1)
            surface.blit(
                self.font_card.render(f"P{pos_num:02d}", True, (255, 215, 0) if pos_num <= 3 else UITheme.TEXT_WHITE),
                (row_r.x + 6, row_r.y + 4),
            )

            d_str = f"{entry.get('driver_name', 'Driver')} ({entry.get('team_name', 'Team')[:12]})"
            surface.blit(
                self.font_body.render(d_str, True, (0, 240, 255) if is_p else UITheme.TEXT_WHITE),
                (row_r.x + 46, row_r.y + 4),
            )

            pts = pts_table[pos_num - 1] if pos_num - 1 < len(pts_table) else 0
            if pts > 0:
                surface.blit(
                    self.font_badge.render(f"+{pts} PTS", True, (0, 240, 140)),
                    (row_r.x + row_r.width - 65, row_r.y + 4),
                )

    def _render_weekend_summary(self, surface: pygame.Surface):
        sum_rect = pygame.Rect(self.width // 2 - 320, 130, 640, 420)
        UITheme.draw_panel(surface, sum_rect)
        hdr = pygame.Rect(sum_rect.x, sum_rect.y, sum_rect.width, 32)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, hdr, border_top_left_radius=4, border_top_right_radius=4)
        surface.blit(
            self.font_header.render("🏆 RACE WEEKEND COMPLETED — SUMMARY", True, (255, 215, 0)),
            (sum_rect.x + 14, sum_rect.y + 8),
        )

        # Points
        surface.blit(
            self.font_card.render("WEEKEND CHAMPIONSHIP POINTS AWARDED:", True, UITheme.TEXT_WHITE),
            (sum_rect.x + 20, sum_rect.y + 50),
        )
        y_c = sum_rect.y + 75
        for d_name, pts in list(self.manager.weekend_driver_points.items())[:8]:
            surface.blit(
                self.font_body.render(f"• {d_name}: +{pts} Points", True, (0, 240, 140)), (sum_rect.x + 24, y_c)
            )
            y_c += 22

        fin_btn = pygame.Rect(self.width // 2 - 160, self.height - 80, 320, 48)
        pygame.draw.rect(surface, (0, 180, 100), fin_btn, border_radius=4)
        t_fin = self.font_big_btn.render("RETURN TO HQ DASHBOARD >>", True, (10, 25, 15))
        surface.blit(t_fin, (fin_btn.x + (fin_btn.width - t_fin.get_width()) // 2, fin_btn.y + 14))
