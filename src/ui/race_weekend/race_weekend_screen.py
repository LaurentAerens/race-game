import random
from typing import Any, Callable, Dict, List, Optional, Tuple

import pygame

from ...core.race_weekend import PracticePlan, RaceWeekendManager, RaceWeekendSession
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
    ):
        self.width = width
        self.height = height
        self.manager = manager
        self.drivers = drivers
        self.on_start_live_session = on_start_live_session
        self.on_finish_weekend = on_finish_weekend
        self.driver_car_pairs = driver_car_pairs

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

        for idx, (p_name, min_v, max_v) in enumerate(param_names):
            if self.dragging_param == p_name:
                row_y = setup_rect.y + 42 + idx * 42
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
                row_y = setup_rect.y + 42 + idx * 42
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

            # Practice Plan Buttons
            plan_panel = pygame.Rect(24, 425, 480, 175)
            plan_buttons = [
                (PracticePlan.BALANCED, pygame.Rect(plan_panel.x + 14, plan_panel.y + 35, 215, 34)),
                (PracticePlan.FAST_LAP, pygame.Rect(plan_panel.x + 245, plan_panel.y + 35, 215, 34)),
                (PracticePlan.SPRINT_STINTS, pygame.Rect(plan_panel.x + 14, plan_panel.y + 75, 215, 34)),
                (PracticePlan.LONG_RUNS, pygame.Rect(plan_panel.x + 245, plan_panel.y + 75, 215, 34)),
            ]
            for plan_enum, btn_r in plan_buttons:
                if btn_r.collidepoint(mx, my):
                    mgr.set_practice_plan(self.active_car_slot, plan_enum)
                    self.status_message = f"Selected {plan_enum.value} program for Car #{self.active_car_slot}."
                    return True

            # Action: Run Practice Run
            run_btn = pygame.Rect(24, self.height - 75, 260, 48)
            if run_btn.collidepoint(mx, my):
                d_name = (
                    self.drivers[self.active_car_slot - 1]["name"]
                    if len(self.drivers) >= self.active_car_slot
                    else f"Driver {self.active_car_slot}"
                )
                res = mgr.run_practice_run(self.active_car_slot, d_name, laps_run=5)
                self.status_message = f"Completed 5 laps! Confidence is now {res['confidence_pct']}%."
                return True

            # Action: Next Session >>
            next_btn = pygame.Rect(300, self.height - 75, 204, 48)
            if next_btn.collidepoint(mx, my):
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
                # Apply long runs or sprint wear bonus
                c_slot = 1 if g.get("number", 1) % 2 != 0 else 2
                bonuses = self.manager.practice_bonuses[c_slot]
                conf = self.manager.setup_confidence[c_slot]
                base_score += (conf / 100.0) * 8.0 + bonuses.get("race_wear_bonus", 0.0) * 15.0

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

    def _render_practice_session(self, surface: pygame.Surface):
        mgr = self.manager
        slot = self.active_car_slot

        # A. Car Selector Tabs (Car #1 / Car #2)
        c1_rect = pygame.Rect(24, 110, 120, 28)
        c2_rect = pygame.Rect(150, 110, 120, 28)

        d1_name = self.drivers[0]["name"] if len(self.drivers) > 0 else "Car 1"
        d2_name = self.drivers[1]["name"] if len(self.drivers) > 1 else "Car 2"

        pygame.draw.rect(surface, (30, 48, 70) if slot == 1 else (18, 24, 32), c1_rect, border_radius=3)
        pygame.draw.rect(surface, (0, 220, 255) if slot == 1 else (40, 50, 65), c1_rect, width=1, border_radius=3)
        t1 = self.font_card.render(f"CAR #1: {d1_name[:8]}", True, (0, 220, 255) if slot == 1 else UITheme.TEXT_MUTED)
        surface.blit(t1, (c1_rect.x + (c1_rect.width - t1.get_width()) // 2, c1_rect.y + 6))

        pygame.draw.rect(surface, (30, 48, 70) if slot == 2 else (18, 24, 32), c2_rect, border_radius=3)
        pygame.draw.rect(surface, (0, 220, 255) if slot == 2 else (40, 50, 65), c2_rect, width=1, border_radius=3)
        t2 = self.font_card.render(f"CAR #2: {d2_name[:8]}", True, (0, 220, 255) if slot == 2 else UITheme.TEXT_MUTED)
        surface.blit(t2, (c2_rect.x + (c2_rect.width - t2.get_width()) // 2, c2_rect.y + 6))

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
        guidance_ranges = mgr.get_setup_guidance_ranges()

        param_configs = [
            ("Front Wing Angle", "front_wing", cur_setup.front_wing, 0.0, 100.0, ""),
            ("Rear Wing Angle", "rear_wing", cur_setup.rear_wing, 0.0, 100.0, ""),
            ("Suspension Stiffness", "suspension", cur_setup.suspension, 0.0, 100.0, ""),
            ("Gear Ratio Spread", "gear_ratio", cur_setup.gear_ratio, 0.0, 100.0, ""),
            ("Brake Bias", "brake_bias", cur_setup.brake_bias, 50.0, 65.0, "%"),
        ]

        for idx, (label, p_key, val, min_v, max_v, unit) in enumerate(param_configs):
            row_y = setup_rect.y + 42 + idx * 42
            surface.blit(self.font_body.render(label, True, UITheme.TEXT_WHITE), (setup_rect.x + 14, row_y + 4))

            # Minus Button
            btn_minus = pygame.Rect(setup_rect.x + 150, row_y + 2, 26, 22)
            pygame.draw.rect(surface, (28, 36, 48), btn_minus, border_radius=2)
            surface.blit(self.font_btn.render("-", True, UITheme.TEXT_WHITE), (btn_minus.x + 8, btn_minus.y + 2))

            # Track
            track_r = pygame.Rect(setup_rect.x + 185, row_y + 8, 170, 10)
            pygame.draw.rect(surface, (16, 20, 28), track_r, border_radius=3)

            # Setup Analytics guidance target range overlay (bracket / shaded zone)
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
            surface.blit(self.font_badge.render(val_txt, True, (255, 215, 0)), (setup_rect.x + 400, row_y + 4))

            if guidance_ranges and p_key in guidance_ranges:
                g_min, g_max = guidance_ranges[p_key]
                target_str = f"[{g_min:.0f}-{g_max:.0f}]"
                surface.blit(self.font_btn.render(target_str, True, (0, 255, 150)), (setup_rect.x + 440, row_y + 4))

        # C. Practice Plans Selector (Bottom Left)
        plan_panel = pygame.Rect(24, 425, 480, 175)
        UITheme.draw_panel(surface, plan_panel)
        p_hdr = pygame.Rect(plan_panel.x, plan_panel.y, plan_panel.width, 26)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, p_hdr, border_top_left_radius=4, border_top_right_radius=4)
        surface.blit(
            self.font_header.render("SELECT PRACTICE RUN PROGRAM", True, (255, 205, 30)),
            (plan_panel.x + 12, plan_panel.y + 5),
        )

        active_plan = mgr.practice_plans[slot]
        plan_buttons = [
            (PracticePlan.BALANCED, "⚖️ BALANCED PROGRAM", pygame.Rect(plan_panel.x + 14, plan_panel.y + 35, 215, 34)),
            (PracticePlan.FAST_LAP, "⚡ FAST LAP (QUALY)", pygame.Rect(plan_panel.x + 245, plan_panel.y + 35, 215, 34)),
            (PracticePlan.SPRINT_STINTS, "🏎️ SPRINT STINTS", pygame.Rect(plan_panel.x + 14, plan_panel.y + 75, 215, 34)),
            (PracticePlan.LONG_RUNS, "🛡️ LONG RUNS (RACE)", pygame.Rect(plan_panel.x + 245, plan_panel.y + 75, 215, 34)),
        ]

        for plan_enum, lbl, btn_r in plan_buttons:
            is_sel = plan_enum == active_plan
            pygame.draw.rect(surface, (30, 52, 75) if is_sel else (20, 26, 36), btn_r, border_radius=3)
            pygame.draw.rect(
                surface, (0, 220, 255) if is_sel else (45, 55, 70), btn_r, width=2 if is_sel else 1, border_radius=3
            )
            txt = self.font_card.render(lbl, True, (0, 240, 255) if is_sel else UITheme.TEXT_MUTED)
            surface.blit(txt, (btn_r.x + 10, btn_r.y + 8))

        # Description of active plan
        descs = {
            PracticePlan.BALANCED: "Balanced program: +6% extra setup confidence gain and well-rounded pace data.",
            PracticePlan.FAST_LAP: "Low-fuel hot-lap flying simulation: Awards up to +0.65s Qualifying Pace Boost.",
            PracticePlan.SPRINT_STINTS: "Medium-stint simulation: Reduces Sprint tire degradation by up to 30%.",
            PracticePlan.LONG_RUNS: "Heavy-fuel simulation: Cuts Normal Race tire wear by 35% & saves 15% fuel.",
        }
        desc_box = pygame.Rect(plan_panel.x + 14, plan_panel.y + 118, plan_panel.width - 28, 45)
        pygame.draw.rect(surface, (16, 22, 30), desc_box, border_radius=3)
        surface.blit(self.font_badge.render(descs[active_plan], True, (0, 240, 140)), (desc_box.x + 8, desc_box.y + 12))

        # D. Driver Feedback & Confidence Gauge (Right)
        fb_rect = pygame.Rect(520, 150, self.width - 544, 450)
        UITheme.draw_panel(surface, fb_rect)
        fb_hdr = pygame.Rect(fb_rect.x, fb_rect.y, fb_rect.width, 28)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, fb_hdr, border_top_left_radius=4, border_top_right_radius=4)
        surface.blit(
            self.font_header.render(f"CAR #{slot} TELEMETRY & DRIVER RADIO FEEDBACK", True, UITheme.ACCENT_CYAN),
            (fb_rect.x + 12, fb_rect.y + 6),
        )

        # Confidence Gauge
        conf = mgr.setup_confidence[slot]
        surface.blit(
            self.font_card.render(f"SETUP CONFIDENCE: {conf:.1f}%", True, (255, 215, 0)),
            (fb_rect.x + 16, fb_rect.y + 40),
        )
        gauge_bar = pygame.Rect(fb_rect.x + 16, fb_rect.y + 62, fb_rect.width - 32, 16)
        pygame.draw.rect(surface, (16, 20, 26), gauge_bar, border_radius=3)
        fill_w = int(gauge_bar.width * (conf / 100.0))
        g_col = (0, 240, 140) if conf > 75 else ((255, 200, 40) if conf > 45 else (240, 70, 70))
        pygame.draw.rect(surface, g_col, (gauge_bar.x, gauge_bar.y, fill_w, gauge_bar.height), border_radius=3)

        # Plan bonuses list
        bonuses = mgr.practice_bonuses[slot]
        b_txt = f"Accumulated Bonuses: Qualy Pace: +{bonuses['qualy_pace_bonus']:.2f}s | Sprint Wear: -{bonuses['sprint_wear_bonus'] * 100:.0f}% | Race Wear: -{bonuses['race_wear_bonus'] * 100:.0f}% | Fuel: -{bonuses['fuel_saving_bonus'] * 100:.0f}%"
        surface.blit(self.font_badge.render(b_txt, True, UITheme.ACCENT_CYAN), (fb_rect.x + 16, fb_rect.y + 86))

        # Recent Feedback items
        fb_list = mgr.driver_feedback[slot]
        surface.blit(
            self.font_header.render("RADIO DEBRIEF & COMMENTS:", True, UITheme.TEXT_WHITE),
            (fb_rect.x + 16, fb_rect.y + 112),
        )

        y_cursor = fb_rect.y + 135
        if not fb_list:
            surface.blit(
                self.font_body.render(
                    "No practice runs completed yet. Click [RUN 5 PRACTICE LAPS] to test the setup.",
                    True,
                    UITheme.TEXT_MUTED,
                ),
                (fb_rect.x + 16, y_cursor),
            )
        else:
            latest = fb_list[-1]
            surface.blit(
                self.font_card.render(f'Driver Debrief: "{latest["summary_quote"]}"', True, (0, 240, 140)),
                (fb_rect.x + 16, y_cursor),
            )
            y_cursor += 26
            for pt in latest["feedback_points"][:5]:
                surface.blit(self.font_body.render(f"• {pt}", True, UITheme.TEXT_WHITE), (fb_rect.x + 20, y_cursor))
                y_cursor += 22

        # E. Action Buttons
        run_btn = pygame.Rect(24, self.height - 75, 260, 48)
        pygame.draw.rect(surface, (0, 180, 100), run_btn, border_radius=4)
        pygame.draw.rect(surface, (0, 255, 140), run_btn, width=2, border_radius=4)
        t_run = self.font_big_btn.render("🏎️ RUN 5 PRACTICE LAPS", True, (10, 25, 15))
        surface.blit(t_run, (run_btn.x + (run_btn.width - t_run.get_width()) // 2, run_btn.y + 14))

        next_btn = pygame.Rect(300, self.height - 75, 204, 48)
        pygame.draw.rect(surface, (30, 55, 80), next_btn, border_radius=4)
        pygame.draw.rect(surface, (0, 220, 255), next_btn, width=1, border_radius=4)
        next_lbl = "PROCEED TO GRAND PRIX >>" if mgr.current_session == RaceWeekendSession.FP3 else "NEXT SESSION >>"
        t_next = self.font_btn.render(next_lbl, True, UITheme.TEXT_WHITE)
        surface.blit(t_next, (next_btn.x + (next_btn.width - t_next.get_width()) // 2, next_btn.y + 16))

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
        board_rect = pygame.Rect(24, 175, self.width - 48, self.height - 270)
        UITheme.draw_panel(surface, board_rect)
        b_hdr = pygame.Rect(board_rect.x, board_rect.y, board_rect.width, 28)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, b_hdr, border_top_left_radius=4, border_top_right_radius=4)
        title = "OFFICIAL SPRINT STARTING GRID" if is_sprint else "OFFICIAL GRAND PRIX STARTING GRID"
        surface.blit(self.font_header.render(title, True, (0, 220, 255)), (board_rect.x + 14, board_rect.y + 6))

        y_pos = board_rect.y + 34
        col_w = (board_rect.width - 28) // 2

        for idx, entry in enumerate(grid[:20]):
            col_x = board_rect.x + 14 if idx < 10 else board_rect.x + 14 + col_w + 10
            row_y = y_pos + (idx % 10) * 28

            row_r = pygame.Rect(col_x, row_y, col_w - 10, 24)
            is_p = entry.get("is_player", False)
            pygame.draw.rect(surface, (30, 48, 65) if is_p else (18, 24, 30), row_r, border_radius=2)
            if is_p:
                pygame.draw.rect(surface, (0, 220, 255), row_r, width=1, border_radius=2)

            pos_key = "sprint_grid_pos" if is_sprint else "race_grid_pos"
            pos_num = entry.get(pos_key, idx + 1)
            pos_str = f"P{pos_num:02d}"
            surface.blit(
                self.font_card.render(pos_str, True, (255, 215, 0) if pos_num <= 3 else UITheme.TEXT_WHITE),
                (row_r.x + 6, row_r.y + 4),
            )

            d_str = f"{entry.get('driver_name', 'Driver')} ({entry.get('team_name', 'Team')[:12]})"
            surface.blit(
                self.font_body.render(d_str, True, (0, 240, 255) if is_p else UITheme.TEXT_WHITE),
                (row_r.x + 46, row_r.y + 4),
            )

            if is_sprint and entry.get("is_reversed_grid", False):
                surface.blit(
                    self.font_badge.render("[REVERSED]", True, (255, 180, 40)),
                    (row_r.x + row_r.width - 90, row_r.y + 4),
                )

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
