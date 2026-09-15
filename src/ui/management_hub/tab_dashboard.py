from typing import Any, Callable, Dict, List, Optional, Tuple

import pygame

from ...management.game_manager import GameManager
from ...management.innovation_manager import InnovationManager
from ..theme import UITheme


class DashboardTab:
    """Home Dashboard Tab providing Next GP overview, Sponsor Objectives, and Innovation Pipeline."""

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        on_start_race: Callable[[], None],
        on_advance_week: Optional[Callable[[], None]] = None,
        on_open_roundup: Optional[Callable[[], None]] = None,
    ):
        self.width = screen_width
        self.height = screen_height
        self.on_start_race = on_start_race
        self.on_advance_week = on_advance_week
        self.on_open_roundup = on_open_roundup

        self._init_fonts()
        self.action_message: str = "Ready for the upcoming Grand Prix weekend."

    def _init_fonts(self):
        self.font_title = UITheme.get_font(13, bold=True)
        self.font_card_title = UITheme.get_font(12, bold=True)
        self.font_body = UITheme.get_font(11, bold=False)
        self.font_badge = UITheme.get_font(10, bold=True)
        self.font_race_btn = UITheme.get_font(13, bold=True)

    def resize(self, width: int, height: int):
        self.width = width
        self.height = height
        self._init_fonts()

    def get_pipeline_layout(
        self, active_pitches: List[Dict[str, Any]], pending_pitches: List[Dict[str, Any]]
    ) -> Tuple[Optional[pygame.Rect], List[Tuple[pygame.Rect, pygame.Rect, pygame.Rect]]]:
        """Calculates precise, non-overlapping rectangles for active project and pending proposals."""
        pipe_x = 24
        pipe_y = 280
        pipe_w = 460

        cur_y = pipe_y + 34
        act_rect = None
        if active_pitches:
            act_rect = pygame.Rect(pipe_x + 10, cur_y, pipe_w - 20, 52)
            cur_y += 58

        card_h = 100 if active_pitches else 114
        cards = []
        for idx in range(min(2, len(pending_pitches))):
            cy = cur_y + idx * (card_h + 8)
            c_rect = pygame.Rect(pipe_x + 10, cy, pipe_w - 20, card_h)
            greenlight_btn = pygame.Rect(c_rect.x + c_rect.width - 165, c_rect.y + c_rect.height - 24, 98, 20)
            discard_btn = pygame.Rect(c_rect.x + c_rect.width - 60, c_rect.y + c_rect.height - 24, 54, 20)
            cards.append((c_rect, greenlight_btn, discard_btn))

        return act_rect, cards

    def handle_click(self, mx: int, my: int, gm: GameManager, im: InnovationManager) -> bool:
        # 1. Main Action Button: Start Race Weekend OR Advance Week
        race_btn_rect = pygame.Rect(self.width - 320, self.height - 65, 300, 48)
        if race_btn_rect.collidepoint(mx, my):
            if gm.is_race_week_for_player():
                self.on_start_race()
            else:
                if self.on_advance_week:
                    self.on_advance_week()
            return True

        # View Weekly Roundup Button
        roundup_btn_rect = pygame.Rect(self.width - 530, self.height - 65, 195, 48)
        if roundup_btn_rect.collidepoint(mx, my) and self.on_open_roundup:
            self.on_open_roundup()
            return True

        # 2. Innovation Pitches Actions
        active_pitches = im.get_team_pitches(gm.team_id, status="ACTIVE")
        pending_pitches = im.get_team_pitches(gm.team_id, status="PENDING")
        _, cards = self.get_pipeline_layout(active_pitches, pending_pitches)

        for idx, (c_rect, greenlight_btn, discard_btn) in enumerate(cards):
            if idx >= len(pending_pitches):
                break
            p = pending_pitches[idx]

            if greenlight_btn.collidepoint(mx, my):
                success, msg = im.greenlight_pitch(gm.team_id, p["id"])
                self.action_message = msg
                return True
            elif discard_btn.collidepoint(mx, my):
                with im.db.get_connection() as conn:
                    conn.cursor().execute(
                        "UPDATE innovation_pitches SET status = 'DISCARDED' WHERE id = ?;", (p["id"],)
                    )
                    conn.commit()
                self.action_message = f"Discarded proposal: {p['title']}"
                return True

        return False

    def render(self, surface: pygame.Surface, gm: GameManager, im: InnovationManager, rnd_cost_mult: float = 1.0):
        from ..icons import UIIcons

        # 1. Upcoming Grand Prix / Bye Week Card (Top Left)
        is_race_week = gm.is_race_week_for_player()
        race_event = gm.get_current_race_event()
        gp_rect = pygame.Rect(24, 70, 460, 200)
        UITheme.draw_panel(surface, gp_rect)

        # Header
        hdr_rect = pygame.Rect(gp_rect.x, gp_rect.y, gp_rect.width, 28)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, hdr_rect, border_top_left_radius=4, border_top_right_radius=4)

        if is_race_week:
            gp_ic = UIIcons.get_icon("flag", size=14, color=UITheme.ACCENT_CYAN)
            surface.blit(gp_ic, (gp_rect.x + 12, gp_rect.y + 7))
            t_name = race_event.get("track_name", "Grand Prix")
            t_txt = self.font_title.render(
                f"NEXT EVENT: {t_name.upper()}",
                True,
                UITheme.ACCENT_CYAN,
            )
            surface.blit(t_txt, (gp_rect.x + 32, gp_rect.y + 6))

            round_badge = self.font_badge.render(
                f"[ RND {gm.current_round}/{gm.total_rounds} • WK {gm.current_week}/{gm.total_season_weeks} ]",
                True,
                (0, 220, 255),
            )
            surface.blit(round_badge, (gp_rect.right - 10 - round_badge.get_width(), gp_rect.y + 8))

            # Event details
            tr_ic = UIIcons.get_icon("trophy", size=13, color=(255, 215, 0))
            surface.blit(tr_ic, (gp_rect.x + 14, gp_rect.y + 35))
            circ_name = race_event.get("circuit_file", "emerald_ring.json")
            total_laps = race_event.get("total_laps", 15)
            surface.blit(
                self.font_body.render(
                    f"Circuit Layout: {circ_name} ({total_laps} Laps)",
                    True,
                    UITheme.TEXT_WHITE,
                ),
                (gp_rect.x + 32, gp_rect.y + 34),
            )

            char_demands = {
                "SPEED": ("Straight-Line Top Speed & Low Drag", (255, 120, 90)),
                "BRAKES": ("Heavy Braking Stability & Deceleration", (255, 210, 60)),
                "AERO": ("High-Speed Aero Downforce & Wing Grip", (80, 220, 255)),
                "BALANCED": ("Balanced Chassis Equilibrium & Corner Roll", (80, 230, 140)),
            }
            track_char = race_event.get("characteristic", "BALANCED")
            demand_text, demand_col = char_demands.get(track_char, char_demands["BALANCED"])

            w_prof = race_event.get("weather_profile", "DYNAMIC")
            w_ic_name = "cloud-rain" if "WET" in w_prof or "RAIN" in w_prof else "sun"
            w_ic = UIIcons.get_icon(w_ic_name, size=13, color=(60, 160, 240) if "WET" in w_prof else (255, 205, 30))
            surface.blit(w_ic, (gp_rect.x + 14, gp_rect.y + 55))

            surface.blit(
                self.font_body.render(
                    f"Forecast: {w_prof} | Character: {track_char}",
                    True,
                    UITheme.TEXT_MUTED,
                ),
                (gp_rect.x + 32, gp_rect.y + 54),
            )

            g_ic = UIIcons.get_icon("gauge", size=12, color=demand_col)
            surface.blit(g_ic, (gp_rect.x + 14, gp_rect.y + 74))
            surface.blit(
                self.font_badge.render(f"KEY DEMAND: {demand_text.upper()}", True, demand_col),
                (gp_rect.x + 30, gp_rect.y + 73),
            )

            # Car Setup Readiness
            readiness_rect = pygame.Rect(gp_rect.x + 14, gp_rect.y + 100, gp_rect.width - 28, 84)
            pygame.draw.rect(surface, (18, 22, 28), readiness_rect, border_radius=3)
            pygame.draw.rect(surface, UITheme.PANEL_BORDER, readiness_rect, width=1, border_radius=3)

            drivers = gm.db.get_team_drivers(gm.team_id)
            d1_name = drivers[0]["name"] if len(drivers) > 0 else "Driver 1"
            d2_name = drivers[1]["name"] if len(drivers) > 1 else "Driver 2"

            u_mini = UIIcons.get_icon("user", size=12, color=UITheme.TEXT_MUTED)
            surface.blit(u_mini, (readiness_rect.x + 10, readiness_rect.y + 7))
            surface.blit(
                self.font_badge.render("CAR READINESS & DRIVER LINEUP:", True, UITheme.TEXT_MUTED),
                (readiness_rect.x + 26, readiness_rect.y + 6),
            )

            surface.blit(
                self.font_body.render(
                    f"• Car #1: {d1_name} (Focus: {drivers[0]['training_focus'] if drivers else 'BALANCED'})",
                    True,
                    UITheme.TEXT_WHITE,
                ),
                (readiness_rect.x + 10, readiness_rect.y + 26),
            )
            surface.blit(
                self.font_body.render(
                    f"• Car #2: {d2_name} (Focus: {drivers[1]['training_focus'] if len(drivers) > 1 else 'BALANCED'})",
                    True,
                    UITheme.TEXT_WHITE,
                ),
                (readiness_rect.x + 10, readiness_rect.y + 44),
            )

            chk_mini = UIIcons.get_icon("check", size=12, color=(0, 240, 140))
            surface.blit(chk_mini, (readiness_rect.x + 10, readiness_rect.y + 63))
            surface.blit(
                self.font_badge.render("Full race simulation ready with live pit wall strategy.", True, (0, 240, 140)),
                (readiness_rect.x + 26, readiness_rect.y + 62),
            )
        else:
            by_ic = UIIcons.get_icon("wrench", size=14, color=(255, 215, 0))
            surface.blit(by_ic, (gp_rect.x + 12, gp_rect.y + 7))
            t_txt = self.font_title.render("HQ DEVELOPMENT (BYE WEEK)", True, (255, 215, 0))
            surface.blit(t_txt, (gp_rect.x + 32, gp_rect.y + 6))

            wk_badge = self.font_badge.render(
                f"[ WEEK {gm.current_week}/{gm.total_season_weeks} ]", True, (255, 215, 0)
            )
            surface.blit(wk_badge, (gp_rect.right - 10 - wk_badge.get_width(), gp_rect.y + 8))

            up_name = race_event.get("track_name", "Upcoming GP") if race_event else "Grand Prix"
            up_rnd = race_event.get("round", gm.current_round) if race_event else gm.current_round
            up_wk = race_event.get("week", gm.current_week + 1) if race_event else gm.current_week + 1

            tr_ic = UIIcons.get_icon("flag", size=13, color=(0, 240, 140))
            surface.blit(tr_ic, (gp_rect.x + 14, gp_rect.y + 35))
            surface.blit(
                self.font_body.render(
                    f"Next Scheduled Race: Round {up_rnd} at {up_name} (Week {up_wk})", True, (0, 240, 140)
                ),
                (gp_rect.x + 32, gp_rect.y + 34),
            )

            # Active series racing this week
            other_series = gm.get_other_series_racing_this_week()
            tier_short = {1: "Tier 1 WSF", 2: "Tier 2 Continental", 4: "Tier 4 JTS Junior", 5: "Tier 5 Karting"}
            racing_names = []
            for s in other_series:
                t_label = tier_short.get(s["tier"], f"Tier {s['tier']}")
                racing_names.append(f"{t_label}: {s['track_name']}")
            racing_str = " | ".join(racing_names[:2]) if racing_names else "Testing & Development Only"
            surface.blit(
                self.font_badge.render(f"ACTIVE ON TRACK THIS WEEK: {racing_str.upper()}", True, (0, 220, 255)),
                (gp_rect.x + 14, gp_rect.y + 76),
            )

            # HQ Status
            hq_box = pygame.Rect(gp_rect.x + 14, gp_rect.y + 104, gp_rect.width - 28, 80)
            pygame.draw.rect(surface, (18, 24, 32), hq_box, border_radius=3)
            pygame.draw.rect(surface, UITheme.PANEL_BORDER, hq_box, width=1, border_radius=3)
            surface.blit(
                self.font_badge.render("HQ FOCUS & JUNIOR ACADEMY TRACKSIDE:", True, UITheme.TEXT_MUTED),
                (hq_box.x + 10, hq_box.y + 6),
            )
            surface.blit(
                self.font_body.render(
                    "• Factory running wind tunnel R&D and component manufacturing.", True, UITheme.TEXT_WHITE
                ),
                (hq_box.x + 10, hq_box.y + 24),
            )
            surface.blit(
                self.font_body.render(
                    "• Young academy drivers in lower tiers will race under simulation.", True, (0, 220, 255)
                ),
                (hq_box.x + 10, hq_box.y + 42),
            )
            surface.blit(
                self.font_badge.render(
                    "Advance calendar week to simulate active series and review results.", True, (0, 240, 140)
                ),
                (hq_box.x + 10, hq_box.y + 60),
            )

        # 2. Sponsor Objectives & Bonuses (Top Right)
        sp_rect = pygame.Rect(504, 70, self.width - 528, 200)
        UITheme.draw_panel(surface, sp_rect)

        sp_hdr = pygame.Rect(sp_rect.x, sp_rect.y, sp_rect.width, 28)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, sp_hdr, border_top_left_radius=4, border_top_right_radius=4)
        sp_ic = UIIcons.get_icon("target", size=14, color=(255, 215, 0))
        surface.blit(sp_ic, (sp_rect.x + 12, sp_rect.y + 7))
        sp_txt = self.font_title.render("ACTIVE SPONSOR TARGETS & FINANCES", True, (255, 215, 0))
        surface.blit(sp_txt, (sp_rect.x + 12, sp_rect.y + 6))
        surface.blit(sp_txt, (sp_rect.x + 32, sp_rect.y + 6))

        # Query real active sponsors from database
        active_sponsors_list = []
        try:
            with gm.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT * FROM active_sponsors WHERE team_id = ? ORDER BY slot_tier ASC, slot_index ASC;",
                    (gm.team_id,),
                )
                active_sponsors_list = [dict(r) for r in cur.fetchall()]
        except Exception:
            active_sponsors_list = []

        # Sponsor Goal 1 (Primary / Title)
        s1_rect = pygame.Rect(sp_rect.x + 14, sp_rect.y + 38, sp_rect.width - 28, 68)
        pygame.draw.rect(surface, (18, 24, 30), s1_rect, border_radius=3)
        if len(active_sponsors_list) > 0:
            sp1 = active_sponsors_list[0]
            pygame.draw.rect(surface, (0, 180, 120), s1_rect, width=1, border_radius=3)
            aw_ic = UIIcons.get_icon("award", size=13, color=(255, 215, 0))
            surface.blit(aw_ic, (s1_rect.x + 10, s1_rect.y + 8))
            surface.blit(
                self.font_card_title.render(
                    f"{sp1.get('slot_tier', 'TITLE')} PARTNER: {sp1.get('brand_name', 'Sponsor')}", True, (255, 215, 0)
                ),
                (s1_rect.x + 10, s1_rect.y + 8),
                (s1_rect.x + 28, s1_rect.y + 8),
            )
            tgt_pos = sp1.get("target_position")
            tgt_str = (
                f"Target: Finish P{tgt_pos} or better in the Grand Prix"
                if tgt_pos
                else "Target: Clean running with maximum media exposure"
            )
            surface.blit(self.font_body.render(tgt_str, True, UITheme.TEXT_WHITE), (s1_rect.x + 10, s1_rect.y + 28))
            tg_ic = UIIcons.get_icon("target", size=12, color=UITheme.TEXT_MUTED)
            surface.blit(tg_ic, (s1_rect.x + 10, s1_rect.y + 29))
            surface.blit(self.font_body.render(tgt_str, True, UITheme.TEXT_WHITE), (s1_rect.x + 26, s1_rect.y + 28))

            tgt_bonus = sp1.get("target_bonus", 0.0)
            per_race = sp1.get("per_race_payment", 0.0)
            r_left = sp1.get("races_remaining", 0)
            payout_str = f"Bonus: +${tgt_bonus:,.0f} | Fixed Payout: +${per_race:,.0f}/race ({r_left} races left)"
            surface.blit(self.font_badge.render(payout_str, True, (0, 240, 140)), (s1_rect.x + 10, s1_rect.y + 48))
            c_ic = UIIcons.get_icon("circle-dollar-sign", size=12, color=(0, 240, 140))
            surface.blit(c_ic, (s1_rect.x + 10, s1_rect.y + 49))
            surface.blit(self.font_badge.render(payout_str, True, (0, 240, 140)), (s1_rect.x + 26, s1_rect.y + 48))
        else:
            pygame.draw.rect(surface, (60, 50, 40), s1_rect, width=1, border_radius=3)
            surface.blit(
                self.font_card_title.render("PRIMARY SPONSOR: VACANT SLOT", True, (255, 180, 60)),
                (s1_rect.x + 10, s1_rect.y + 8),
            )
            surface.blit(
                self.font_body.render("No primary sponsor contract signed.", True, UITheme.TEXT_MUTED),
                (s1_rect.x + 10, s1_rect.y + 28),
            )
            surface.blit(
                self.font_badge.render(
                    "Visit 'SPONSORS & FINANCES' tab to accept incoming corporate offers.", True, (0, 220, 255)
                ),
                (s1_rect.x + 10, s1_rect.y + 48),
            )

        # Sponsor Goal 2 (Secondary / Middle)
        s2_rect = pygame.Rect(sp_rect.x + 14, sp_rect.y + 114, sp_rect.width - 28, 68)
        pygame.draw.rect(surface, (18, 24, 30), s2_rect, border_radius=3)
        if len(active_sponsors_list) > 1:
            sp2 = active_sponsors_list[1]
            pygame.draw.rect(surface, (40, 80, 120), s2_rect, width=1, border_radius=3)
            aw2_ic = UIIcons.get_icon("award", size=13, color=(0, 200, 255))
            surface.blit(aw2_ic, (s2_rect.x + 10, s2_rect.y + 8))
            surface.blit(
                self.font_card_title.render(
                    f"{sp2.get('slot_tier', 'SECONDARY')} PARTNER: {sp2.get('brand_name', 'Sponsor')}",
                    True,
                    (0, 200, 255),
                ),
                (s2_rect.x + 10, s2_rect.y + 8),
                (s2_rect.x + 28, s2_rect.y + 8),
            )
            tgt_pos = sp2.get("target_position")
            tgt_str = (
                f"Target: Finish P{tgt_pos} or better in the Grand Prix"
                if tgt_pos
                else "Target: Reliable race completion with zero DNF"
            )
            surface.blit(self.font_body.render(tgt_str, True, UITheme.TEXT_WHITE), (s2_rect.x + 10, s2_rect.y + 28))
            tg2_ic = UIIcons.get_icon("target", size=12, color=UITheme.TEXT_MUTED)
            surface.blit(tg2_ic, (s2_rect.x + 10, s2_rect.y + 29))
            surface.blit(self.font_body.render(tgt_str, True, UITheme.TEXT_WHITE), (s2_rect.x + 26, s2_rect.y + 28))

            tgt_bonus = sp2.get("target_bonus", 0.0)
            per_race = sp2.get("per_race_payment", 0.0)
            r_left = sp2.get("races_remaining", 0)
            payout_str = f"Bonus: +${tgt_bonus:,.0f} | Fixed Payout: +${per_race:,.0f}/race ({r_left} races left)"
            surface.blit(self.font_badge.render(payout_str, True, (255, 215, 0)), (s2_rect.x + 10, s2_rect.y + 48))
            c2_ic = UIIcons.get_icon("circle-dollar-sign", size=12, color=(255, 215, 0))
            surface.blit(c2_ic, (s2_rect.x + 10, s2_rect.y + 49))
            surface.blit(self.font_badge.render(payout_str, True, (255, 215, 0)), (s2_rect.x + 26, s2_rect.y + 48))
        else:
            pygame.draw.rect(surface, (45, 50, 60), s2_rect, width=1, border_radius=3)
            surface.blit(
                self.font_card_title.render("SECONDARY SPONSOR: VACANT SLOT", True, UITheme.TEXT_MUTED),
                (s2_rect.x + 10, s2_rect.y + 8),
            )
            surface.blit(
                self.font_body.render("Additional commercial sponsorship slot available.", True, UITheme.TEXT_MUTED),
                (s2_rect.x + 10, s2_rect.y + 28),
            )
            surface.blit(
                self.font_badge.render(
                    "Sign middle or minor commercial partnerships to boost monthly cash flow.", True, (0, 220, 255)
                ),
                (s2_rect.x + 10, s2_rect.y + 48),
            )

        # 3. Innovation Proposals & Breakthrough Pipeline (Bottom Left)
        pitches = im.get_team_pitches(gm.team_id, status="PENDING")
        active_pitches = im.get_team_pitches(gm.team_id, status="ACTIVE")

        pipe_rect = pygame.Rect(24, 280, 460, self.height - 300)
        UITheme.draw_panel(surface, pipe_rect)

        pipe_hdr = pygame.Rect(pipe_rect.x, pipe_rect.y, pipe_rect.width, 28)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, pipe_hdr, border_top_left_radius=4, border_top_right_radius=4)
        spk_ic = UIIcons.get_icon("sparkles", size=14, color=(255, 180, 40))
        surface.blit(spk_ic, (pipe_rect.x + 12, pipe_rect.y + 7))
        p_txt = self.font_title.render(f"R&D INNOVATION PIPELINE ({len(pitches)} Pending)", True, (255, 180, 40))
        surface.blit(p_txt, (pipe_rect.x + 32, pipe_rect.y + 6))

        if not active_pitches and not pitches:
            emp_box = pygame.Rect(pipe_rect.x + 10, pipe_rect.y + 40, pipe_rect.width - 20, 90)
            pygame.draw.rect(surface, (18, 22, 28), emp_box, border_radius=3)
            pygame.draw.rect(surface, UITheme.PANEL_BORDER, emp_box, width=1, border_radius=3)
            surface.blit(
                self.font_card_title.render("NO ACTIVE PROPOSALS", True, UITheme.TEXT_MUTED),
                (emp_box.x + 10, emp_box.y + 16),
            )
            surface.blit(
                self.font_body.render(
                    "Chief Engineers pitch high-risk breakthroughs on race weeks.", True, UITheme.TEXT_MUTED
                ),
                (emp_box.x + 10, emp_box.y + 36),
            )

        act_rect, cards = self.get_pipeline_layout(active_pitches, pending_pitches=pitches)

        # Draw Active Project if present
        if act_rect and active_pitches:
            ap = active_pitches[0]
            pygame.draw.rect(surface, (35, 45, 20), act_rect, border_radius=3)
            pygame.draw.rect(surface, (180, 200, 40), act_rect, width=1, border_radius=3)
            ap_type = ap.get("idea_type", "CREATIVE")
            tag_col = (230, 120, 255) if ap_type == "CREATIVE" else (0, 220, 255)
            surface.blit(
                self.font_card_title.render(f"ACTIVE [{ap_type}]: {ap['title']}", True, (255, 220, 50)),
                (act_rect.x + 8, act_rect.y + 4),
            )
            raw_cats = ap.get("target_categories") or ap.get("category", "R&D")
            gain = ap.get("knowledge_gain", 20.0)
            surface.blit(
                self.font_body.render(
                    f"Targets: {raw_cats} (+{gain:.0f} Flat Knowledge) | {ap.get('weeks_remaining', 1)} wks left",
                    True,
                    UITheme.TEXT_WHITE,
                ),
                (act_rect.x + 8, act_rect.y + 20),
            )
            surface.blit(
                self.font_badge.render(
                    f"Lockout: {ap.get('locked_subnode', 'N/A')} | Estimated Success: {ap.get('est_success_min', 0)}%–{ap.get('est_success_max', 100)}%",
                    True,
                    tag_col,
                ),
                (act_rect.x + 8, act_rect.y + 36),
            )

        # Render Pending Proposals Cards
        for idx, (c_rect, greenlight_btn, discard_btn) in enumerate(cards):
            if idx >= len(pitches):
                break
            p = pitches[idx]

            pygame.draw.rect(surface, (20, 26, 34), c_rect, border_radius=3)
            pygame.draw.rect(surface, UITheme.PANEL_BORDER, c_rect, width=1, border_radius=3)

            p_type = p.get("idea_type", "CREATIVE")
            is_creative = p_type == "CREATIVE"
            badge_icon = "sparkles" if is_creative else "search"
            badge_lbl = "CREATIVE INVENTION" if is_creative else f"COMPETITOR INTEL ({p.get('observed_from', 'Rival')})"
            badge_col = (240, 110, 255) if is_creative else (0, 220, 255)

            UITheme.draw_icon(surface, badge_icon, (c_rect.x + 8, c_rect.y + 5), color=badge_col, size=13)
            surface.blit(self.font_badge.render(badge_lbl, True, badge_col), (c_rect.x + 25, c_rect.y + 4))
            surface.blit(self.font_card_title.render(p["title"], True, (255, 225, 60)), (c_rect.x + 8, c_rect.y + 18))

            raw_cats = p.get("target_categories") or p["category"]
            gain = p.get("knowledge_gain", 20.0)
            impact_str = f"Impact: +{gain:.0f} Flat Knowledge to [{raw_cats}]"
            surface.blit(self.font_body.render(impact_str, True, (0, 255, 160)), (c_rect.x + 8, c_rect.y + 36))

            est_str = f"Success: {p['est_success_min']}%–{p['est_success_max']}% | Lockout: {p['lockout_weeks']} wks"
            surface.blit(self.font_body.render(est_str, True, (180, 210, 240)), (c_rect.x + 8, c_rect.y + 54))

            cost_str = f"Cost: ${p['hard_cost']:,.0f}"
            surface.blit(self.font_badge.render(cost_str, True, (255, 140, 140)), (c_rect.x + 8, c_rect.y + 72))

            # Action Buttons
            UITheme.draw_button(surface, greenlight_btn, "APPROVE", self.font_badge, icon="check", icon_size=11)
            UITheme.draw_button(surface, discard_btn, "DISCARD", self.font_badge, icon="x", icon_size=11)

        # 4. Status Bar & Big Start Race Weekend Button (Bottom Right)
        stat_rect = pygame.Rect(504, 280, self.width - 528, self.height - 380)
        UITheme.draw_panel(surface, stat_rect)

        stat_hdr = pygame.Rect(stat_rect.x, stat_rect.y, stat_rect.width, 28)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, stat_hdr, border_top_left_radius=4, border_top_right_radius=4)
        s_title = self.font_title.render("PIT WALL TELEMETRY & INBOX", True, UITheme.ACCENT_CYAN)
        surface.blit(s_title, (stat_rect.x + 12, stat_rect.y + 6))

        surface.blit(
            self.font_body.render(f"Status: {self.action_message}", True, UITheme.TEXT_WHITE),
            (stat_rect.x + 14, stat_rect.y + 42),
        )
        surface.blit(
            self.font_body.render("• Factory running baseline telemetry analysis.", True, UITheme.TEXT_MUTED),
            (stat_rect.x + 14, stat_rect.y + 66),
        )
        surface.blit(
            self.font_body.render("• Pit crew drills completed with zero fatigue penalties.", True, UITheme.TEXT_MUTED),
            (stat_rect.x + 14, stat_rect.y + 86),
        )

        # Big Action Button: START RACE WEEKEND vs ADVANCE CALENDAR WEEK
        race_btn_rect = pygame.Rect(self.width - 320, self.height - 65, 300, 48)
        action_btn_text = "START RACE WEEKEND" if is_race_week else "ADVANCE WEEK"
        action_btn_icon = "flag" if is_race_week else "fast-forward"
        UITheme.draw_button(
            surface,
            race_btn_rect,
            action_btn_text,
            self.font_race_btn,
            icon=action_btn_icon,
            icon_size=16,
            is_active=True,
        )

        # View Weekly Roundup Button
        roundup_btn = pygame.Rect(self.width - 530, self.height - 65, 195, 48)
        UITheme.draw_button(
            surface,
            roundup_btn,
            "WEEKLY ROUNDUP",
            self.font_card_title,
            icon="calendar",
            icon_size=15,
        )
