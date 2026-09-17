from typing import Any, Dict, Optional, Tuple

import pygame

from ..theme import UITheme


class WeeklyRoundupModal:
    """
    Pop-up debrief modal showing simulated race outcomes across active championship series
    for the current calendar week, with special focus on Academy Drivers and Tier 1/2 results.
    """

    def __init__(self, screen_width: int, screen_height: int):
        self.width = screen_width
        self.height = screen_height
        self.is_open = False
        self.summary_data: Dict[str, Any] = {}
        self.selected_tier_tab: str = "HIGHLIGHTS"

        self._init_fonts()

    def _init_fonts(self):
        self.font_title = UITheme.get_font(14, bold=True)
        self.font_subtitle = UITheme.get_font(10, bold=False)
        self.font_tab = UITheme.get_font(11, bold=True)
        self.font_card_title = UITheme.get_font(12, bold=True)
        self.font_body = UITheme.get_font(11, bold=False)
        self.font_badge = UITheme.get_font(10, bold=True)
        self.font_btn = UITheme.get_font(11, bold=True)

    def resize(self, width: int, height: int):
        self.width = width
        self.height = height
        self._init_fonts()

    def _truncate_text(self, font: pygame.font.Font, text: str, max_w: int) -> str:
        """Truncate text to fit within max_w pixels with an ellipsis."""
        if font.size(text)[0] <= max_w:
            return text
        ellipsis = "..."
        while text and font.size(text + ellipsis)[0] > max_w:
            text = text[:-1]
        return text.strip() + ellipsis if text else ellipsis

    def open(self, summary_data: Dict[str, Any]):
        self.summary_data = summary_data
        self.is_open = True
        # Default to HIGHLIGHTS if academy raced, else first simulated tier
        tiers = summary_data.get("tiers_simulated", [])
        if summary_data.get("academy_highlights"):
            self.selected_tier_tab = "HIGHLIGHTS"
        elif tiers:
            self.selected_tier_tab = f"TIER_{tiers[0]}"
        else:
            self.selected_tier_tab = "HIGHLIGHTS"

    def close(self):
        self.is_open = False

    def handle_click(self, mx: int, my: int) -> bool:
        if not self.is_open:
            return False

        modal_w = min(820, self.width - 60)
        modal_h = min(540, self.height - 60)
        modal_x = (self.width - modal_w) // 2
        modal_y = (self.height - modal_h) // 2

        # 1. Close / Dismiss Button
        dismiss_btn = pygame.Rect(modal_x + modal_w - 180, modal_y + modal_h - 44, 165, 34)
        if dismiss_btn.collidepoint(mx, my):
            self.close()
            return True

        # 2. Tab Switchers
        tab_x = modal_x + 16
        tab_y = modal_y + 46
        tab_w = 115
        tab_h = 26

        # Highlights tab
        h_rect = pygame.Rect(tab_x, tab_y, tab_w, tab_h)
        if h_rect.collidepoint(mx, my):
            self.selected_tier_tab = "HIGHLIGHTS"
            return True

        # Tier tabs
        tiers = self.summary_data.get("tiers_simulated", [])
        for idx, t in enumerate(tiers):
            t_rect = pygame.Rect(tab_x + (idx + 1) * (tab_w + 8), tab_y, tab_w, tab_h)
            if t_rect.collidepoint(mx, my):
                self.selected_tier_tab = f"TIER_{t}"
                return True

        # Click inside modal consumes click event so background doesn't trigger
        modal_rect = pygame.Rect(modal_x, modal_y, modal_w, modal_h)
        return modal_rect.collidepoint(mx, my)

    def render(self, surface: pygame.Surface):
        if not self.is_open:
            return

        mx, my = pygame.mouse.get_pos()
        pending_tooltip: Optional[Tuple[str, str, Tuple[int, int], str]] = None

        # Dim Background Overlay
        dim_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim_surf.fill((0, 0, 0, 195))
        surface.blit(dim_surf, (0, 0))

        modal_w = min(820, self.width - 60)
        modal_h = min(540, self.height - 60)
        modal_x = (self.width - modal_w) // 2
        modal_y = (self.height - modal_h) // 2

        # Modal Box Frame
        modal_rect = pygame.Rect(modal_x, modal_y, modal_w, modal_h)
        pygame.draw.rect(surface, (14, 18, 25), modal_rect, border_radius=6)
        pygame.draw.rect(surface, (0, 220, 255), modal_rect, width=2, border_radius=6)

        # Header Banner
        hdr_rect = pygame.Rect(modal_x, modal_y, modal_w, 44)
        pygame.draw.rect(surface, (20, 28, 42), hdr_rect, border_top_left_radius=6, border_top_right_radius=6)

        is_season_start = bool(self.summary_data.get("is_season_start", False))
        week = self.summary_data.get("week", 1)

        if is_season_start:
            title_txt = "🏁 SEASON OPENER: MOTORSPORT ROUNDUP"
            sub_txt = "Championship Season Underway • Round 1 Upcoming"
        else:
            title_txt = f"🏁 WEEK {week} / 18: WORLD MOTORSPORT ROUNDUP"
            tiers_sim = self.summary_data.get("tiers_simulated", [])
            tiers_str = ", ".join([f"Tier {t}" for t in tiers_sim]) if tiers_sim else "No series racing"
            sub_txt = f"Active Series Simulated This Week: {tiers_str}"

        surface.blit(self.font_title.render(title_txt, True, (255, 215, 0)), (modal_x + 16, modal_y + 6))
        sub_trunc = self._truncate_text(self.font_subtitle, sub_txt, modal_w - 32)
        surface.blit(self.font_subtitle.render(sub_trunc, True, UITheme.TEXT_MUTED), (modal_x + 16, modal_y + 26))

        # Tab Strip
        tab_x = modal_x + 16
        tab_y = modal_y + 48
        tab_w = 115
        tab_h = 26

        if is_season_start:
            h_rect = pygame.Rect(tab_x, tab_y, 140, tab_h)
            pygame.draw.rect(surface, (36, 56, 78), h_rect, border_radius=3)
            pygame.draw.rect(surface, UITheme.ACCENT_CYAN, h_rect, width=1, border_radius=3)
            lbl_h = self.font_tab.render("SEASON KICKOFF", True, UITheme.TEXT_WHITE)
            surface.blit(lbl_h, (h_rect.x + (140 - lbl_h.get_width()) // 2, h_rect.y + 6))
        else:
            # 1. Highlights Tab
            is_hl = self.selected_tier_tab == "HIGHLIGHTS"
            h_rect = pygame.Rect(tab_x, tab_y, tab_w, tab_h)
            pygame.draw.rect(surface, (36, 56, 78) if is_hl else (20, 26, 36), h_rect, border_radius=3)
            pygame.draw.rect(
                surface, UITheme.ACCENT_CYAN if is_hl else UITheme.PANEL_BORDER, h_rect, width=1, border_radius=3
            )
            lbl_h = self.font_tab.render("HIGHLIGHTS", True, UITheme.TEXT_WHITE if is_hl else UITheme.TEXT_MUTED)
            surface.blit(lbl_h, (h_rect.x + (tab_w - lbl_h.get_width()) // 2, h_rect.y + 6))

            # Tier Tabs
            tier_labels = {
                1: "TIER 1 (WSF)",
                2: "TIER 2 (CC)",
                3: "TIER 3 (NOC)",
                4: "TIER 4 (JTS)",
                5: "TIER 5 (KART)",
            }
            for idx, t in enumerate(tiers_sim):
                t_rect = pygame.Rect(tab_x + (idx + 1) * (tab_w + 8), tab_y, tab_w, tab_h)
                is_sel = self.selected_tier_tab == f"TIER_{t}"
                pygame.draw.rect(surface, (36, 56, 78) if is_sel else (20, 26, 36), t_rect, border_radius=3)
                pygame.draw.rect(
                    surface, UITheme.ACCENT_CYAN if is_sel else UITheme.PANEL_BORDER, t_rect, width=1, border_radius=3
                )
                t_lbl = self.font_tab.render(
                    tier_labels.get(t, f"TIER {t}"), True, UITheme.TEXT_WHITE if is_sel else UITheme.TEXT_MUTED
                )
                surface.blit(t_lbl, (t_rect.x + (tab_w - t_lbl.get_width()) // 2, t_rect.y + 6))

        # Content Box
        content_rect = pygame.Rect(modal_x + 16, modal_y + 80, modal_w - 32, modal_h - 134)
        pygame.draw.rect(surface, (18, 23, 31), content_rect, border_radius=4)
        pygame.draw.rect(surface, UITheme.PANEL_BORDER, content_rect, width=1, border_radius=4)

        if is_season_start:
            pending_tooltip = self._render_season_opener(surface, content_rect, mx, my)
        elif self.selected_tier_tab == "HIGHLIGHTS":
            self._render_highlights(surface, content_rect)
        else:
            try:
                tier_num = int(self.selected_tier_tab.replace("TIER_", ""))
                self._render_tier_table(surface, content_rect, tier_num)
            except Exception:
                self._render_highlights(surface, content_rect)

        # Dismiss Button
        dismiss_btn = pygame.Rect(modal_x + modal_w - 180, modal_y + modal_h - 44, 165, 34)
        pygame.draw.rect(surface, (0, 180, 100), dismiss_btn, border_radius=4)
        btn_label = "GOT IT >>" if is_season_start else "DISMISS & CONTINUE >>"
        d_txt = self.font_btn.render(btn_label, True, (10, 25, 20))
        surface.blit(d_txt, (dismiss_btn.x + (dismiss_btn.width - d_txt.get_width()) // 2, dismiss_btn.y + 9))

        if pending_tooltip:
            t_title, t_text, t_pos, t_icon = pending_tooltip
            UITheme.draw_tooltip(
                surface,
                t_text,
                t_pos,
                title=t_title,
                icon=t_icon,
                font=self.font_badge,
                max_width=360,
            )

    def _render_season_opener(
        self, surface: pygame.Surface, rect: pygame.Rect, mx: int, my: int
    ) -> Optional[Tuple[str, str, Tuple[int, int], str]]:
        """Renders an informative visual state explaining season kickoff and upcoming Round 1."""
        card_w = rect.width - 40
        card_h = min(280, rect.height - 30)
        card_x = rect.x + 20
        card_y = rect.y + (rect.height - card_h) // 2

        card_rect = pygame.Rect(card_x, card_y, card_w, card_h)
        pygame.draw.rect(surface, (22, 30, 42), card_rect, border_radius=6)
        pygame.draw.rect(surface, UITheme.ACCENT_CYAN, card_rect, width=1, border_radius=6)

        # Title & Info Button
        title_txt = "🚦 THE NEW MOTORSPORT SEASON IS UNDERWAY"
        t_surf = self.font_card_title.render(title_txt, True, (255, 215, 0))
        surface.blit(t_surf, (card_x + 24, card_y + 16))

        info_rect = pygame.Rect(card_x + 24 + t_surf.get_width() + 8, card_y + 15, 16, 16)
        is_info_hov = info_rect.collidepoint(mx, my)
        UITheme.draw_info_icon(surface, info_rect, is_hover=is_info_hov)

        tip = None
        if is_info_hov:
            season_lore = (
                "Championship Season Simulation Rules:\n\n"
                "• All 5 open-wheel motorsport tiers simulate active races as weeks advance.\n"
                "• Official championship standings, points, podiums, and DNFs are recorded.\n"
                "• Signed academy drivers competing in feeder series are debriefed weekly.\n"
                "• Commercial partners pay guaranteed fixed income and target finish bonuses.\n\n"
                "Click START RACE WEEKEND on the dashboard to qualify and race!"
            )
            tip = ("SEASON OPENER DEBRIEF", season_lore, (mx + 10, my + 10), "flag")

        # 3 Visual Feature Cards
        features = [
            (
                "flag",
                "5 ACTIVE MOTORSPORT TIERS",
                "Open-wheel formulas competing concurrently from Karting up to World Super Formula",
                (0, 220, 255),
            ),
            (
                "trophy",
                "POINTS & STANDINGS SYSTEM",
                "Driver & Team championships tracked across all racing divisions after each round",
                (255, 215, 0),
            ),
            (
                "graduation-cap",
                "ACADEMY DRIVER TELEMETRY",
                "Weekly debriefs spotlighting junior development driver racecraft and pace",
                (0, 240, 140),
            ),
        ]

        f_y = card_y + 44
        f_h = 50
        for icon_name, f_title, f_desc, color in features:
            f_box = pygame.Rect(card_x + 20, f_y, card_w - 40, f_h)
            pygame.draw.rect(surface, (16, 22, 32), f_box, border_radius=4)
            pygame.draw.rect(surface, (40, 52, 70), f_box, width=1, border_radius=4)

            UITheme.draw_stat_item(
                surface,
                f_box.x + 12,
                f_box.y + 8,
                icon_name,
                f_title,
                self.font_card_title,
                text_color=color,
                icon_color=color,
                icon_size=14,
            )
            surface.blit(self.font_body.render(f_desc, True, UITheme.TEXT_MUTED), (f_box.x + 12, f_box.y + 28))
            f_y += f_h + 8

        # Prompt Banner at bottom
        UITheme.draw_stat_item(
            surface,
            card_x + 24,
            card_y + card_h - 28,
            "play",
            "Click 'START RACE WEEKEND' on the dashboard to hit the track for Round 1!",
            self.font_badge,
            text_color=(0, 240, 140),
            icon_color=(0, 240, 140),
            icon_size=12,
        )

        return tip

    def _render_highlights(self, surface: pygame.Surface, rect: pygame.Rect):
        """Renders Academy Driver Spotlight & Top Series Winners."""
        academy_highlights = self.summary_data.get("academy_highlights", [])
        res_by_tier = self.summary_data.get("results_by_tier", {})

        cur_y = rect.y + 12

        # 1. Academy Driver Spotlight Card
        if academy_highlights:
            for ah in academy_highlights:
                card_h = 76
                c_box = pygame.Rect(rect.x + 12, cur_y, rect.width - 24, card_h)
                pygame.draw.rect(surface, (24, 38, 48), c_box, border_radius=4)
                pygame.draw.rect(surface, (0, 240, 140), c_box, width=1, border_radius=4)

                pos = ah["position"]
                pos_col = (255, 215, 0) if pos == 1 else ((0, 240, 140) if pos <= 3 else (0, 220, 255))
                pos_str = f"P{pos}"
                surface.blit(
                    self.font_card_title.render(
                        f"🌟 ACADEMY SPOTLIGHT: {ah['driver_name'].upper()}", True, (255, 215, 0)
                    ),
                    (c_box.x + 12, c_box.y + 8),
                )
                surface.blit(self.font_title.render(pos_str, True, pos_col), (c_box.x + c_box.width - 52, c_box.y + 10))

                surface.blit(
                    self.font_body.render(ah["message"], True, UITheme.TEXT_WHITE), (c_box.x + 12, c_box.y + 30)
                )
                stat_str = (
                    f"Championship Points Earned: +{ah['points']} PTS | Updated Driver Morale: {ah['morale']:.0f}%"
                )
                surface.blit(self.font_badge.render(stat_str, True, (0, 220, 255)), (c_box.x + 12, c_box.y + 52))

                cur_y += card_h + 10
        else:
            c_box = pygame.Rect(rect.x + 12, cur_y, rect.width - 24, 52)
            pygame.draw.rect(surface, (20, 26, 34), c_box, border_radius=4)
            surface.blit(
                self.font_card_title.render(
                    "ACADEMY WATCH: No academy drivers had a scheduled race this week.", True, UITheme.TEXT_MUTED
                ),
                (c_box.x + 12, c_box.y + 16),
            )
            cur_y += 62

        # 2. Winners Across Simulated Tiers
        sec_title = self.font_card_title.render("SERIES RACE WINNERS THIS WEEK", True, (0, 220, 255))
        surface.blit(sec_title, (rect.x + 12, cur_y))
        cur_y += 24

        tier_names = {
            1: "Tier 1 World Super Formula",
            2: "Tier 2 Continental Championship",
            3: "Tier 3 National Open Cup",
            4: "Tier 4 Junior Talent Series",
            5: "Tier 5 Karting Masters",
        }

        for t_num in [1, 2, 3, 4, 5]:
            if t_num in res_by_tier:
                results = res_by_tier[t_num]
                if not results:
                    continue
                w = results[0]  # P1 winner
                p2 = results[1] if len(results) > 1 else None
                p3 = results[2] if len(results) > 2 else None

                row_rect = pygame.Rect(rect.x + 12, cur_y, rect.width - 24, 40)
                pygame.draw.rect(surface, (22, 28, 38), row_rect, border_radius=3)
                pygame.draw.rect(surface, (40, 50, 68), row_rect, width=1, border_radius=3)

                t_lbl = self.font_card_title.render(tier_names.get(t_num, f"Tier {t_num}"), True, (255, 215, 0))
                surface.blit(t_lbl, (row_rect.x + 10, row_rect.y + 11))

                pod_col_x = max(row_rect.x + 460, row_rect.x + int(row_rect.width * 0.62))
                w_max_w = pod_col_x - (row_rect.x + 210) - 10
                w_txt = f"🏆 P1: {w['driver_name']} ({w['team_name']})"
                w_trunc = self._truncate_text(self.font_body, w_txt, w_max_w)
                surface.blit(self.font_body.render(w_trunc, True, (0, 240, 140)), (row_rect.x + 210, row_rect.y + 11))

                if p2 and p3:
                    pod_txt = f"P2: {p2['driver_name']}  |  P3: {p3['driver_name']}"
                    pod_max_w = row_rect.x + row_rect.width - pod_col_x - 10
                    pod_trunc = self._truncate_text(self.font_subtitle, pod_txt, pod_max_w)
                    surface.blit(
                        self.font_subtitle.render(pod_trunc, True, UITheme.TEXT_MUTED),
                        (pod_col_x, row_rect.y + 12),
                    )

                cur_y += 46
                if cur_y > rect.y + rect.height - 45:
                    break

    def _render_tier_table(self, surface: pygame.Surface, rect: pygame.Rect, tier: int):
        """Renders complete top 10 race classification table for a specific tier."""
        res_by_tier = self.summary_data.get("results_by_tier", {})
        results = res_by_tier.get(tier, [])

        if not results:
            surface.blit(
                self.font_body.render(f"No results recorded for Tier {tier} this week.", True, UITheme.TEXT_MUTED),
                (rect.x + 20, rect.y + 20),
            )
            return

        # Table Header
        th_rect = pygame.Rect(rect.x + 10, rect.y + 8, rect.width - 20, 22)
        pygame.draw.rect(surface, (14, 18, 24), th_rect)
        surface.blit(self.font_badge.render("POS", True, UITheme.TEXT_MUTED), (th_rect.x + 10, th_rect.y + 4))
        surface.blit(self.font_badge.render("DRIVER", True, UITheme.TEXT_MUTED), (th_rect.x + 60, th_rect.y + 4))
        surface.blit(
            self.font_badge.render("TEAM / CONSTRUCTOR", True, UITheme.TEXT_MUTED), (th_rect.x + 280, th_rect.y + 4)
        )
        surface.blit(self.font_badge.render("POINTS", True, UITheme.TEXT_MUTED), (th_rect.x + 540, th_rect.y + 4))

        for idx, r in enumerate(results[:10]):
            r_y = rect.y + 34 + idx * 27
            if r_y + 26 > rect.y + rect.height:
                break
            r_box = pygame.Rect(rect.x + 10, r_y, rect.width - 20, 25)
            is_acad = bool(r.get("is_academy_driver", False))
            is_ply = bool(r.get("is_player", False))

            bg_col = (28, 46, 58) if (is_acad or is_ply) else ((20, 26, 34) if idx % 2 == 0 else (16, 21, 28))
            pygame.draw.rect(surface, bg_col, r_box, border_radius=2)
            if is_acad:
                pygame.draw.rect(surface, (0, 240, 140), r_box, width=1, border_radius=2)
            elif is_ply:
                pygame.draw.rect(surface, UITheme.ACCENT_CYAN, r_box, width=1, border_radius=2)

            # Pos
            pos = r.get("position", idx + 1)
            pos_col = (255, 215, 0) if pos == 1 else ((0, 240, 140) if pos <= 3 else UITheme.TEXT_WHITE)
            surface.blit(self.font_badge.render(f"P{pos}", True, pos_col), (r_box.x + 10, r_box.y + 5))

            # Driver Name
            tag = " [ACADEMY]" if is_acad else (" [YOU]" if is_ply else "")
            d_name = f"{r.get('driver_name', 'Driver')}{tag}"
            d_col = (0, 240, 140) if is_acad else ((255, 215, 0) if is_ply else UITheme.TEXT_WHITE)
            surface.blit(self.font_body.render(d_name, True, d_col), (r_box.x + 60, r_box.y + 4))

            # Team Name
            surface.blit(
                self.font_body.render(r.get("team_name", ""), True, UITheme.TEXT_MUTED), (r_box.x + 280, r_box.y + 4)
            )

            # Points
            pts = r.get("points", 0)
            pts_col = (0, 220, 255) if pts > 0 else UITheme.TEXT_MUTED
            surface.blit(
                self.font_badge.render(f"+{pts} PTS" if pts > 0 else "-", True, pts_col), (r_box.x + 540, r_box.y + 5)
            )
