from typing import Any, Dict, Optional

import pygame

from ...management.game_manager import GameManager
from ..theme import UITheme


class StandingsTab:
    """Championship Standings & Calendar Tab for all 5 league tiers."""

    def __init__(self, screen_width: int, screen_height: int):
        self.width = screen_width
        self.height = screen_height

        self.selected_tier: int = 3
        self.standings_mode: str = "CONSTRUCTORS"  # "CONSTRUCTORS" or "DRIVERS"
        self.selected_round_results: Optional[Dict[str, Any]] = None

        self._init_fonts()

    def _init_fonts(self):
        self.font_title = UITheme.get_font(13, bold=True)
        self.font_card_title = UITheme.get_font(12, bold=True)
        self.font_body = UITheme.get_font(11, bold=False)
        self.font_badge = UITheme.get_font(10, bold=True)
        self.font_btn = UITheme.get_font(11, bold=True)

    def resize(self, width: int, height: int):
        self.width = width
        self.height = height
        self._init_fonts()

    def _truncate_text(self, font: pygame.font.Font, text: str, max_w: int) -> str:
        """Safely truncates text to fit within max_w pixels with an ellipsis, preventing column overlap."""
        if font.size(text)[0] <= max_w:
            return text
        ellipsis = "..."
        while text and font.size(text + ellipsis)[0] > max_w:
            text = text[:-1]
        return text.strip() + ellipsis if text else ellipsis

    def handle_click(self, mx: int, my: int, gm: GameManager) -> bool:
        # Close Round Results Modal if open
        if self.selected_round_results:
            modal_rect = pygame.Rect(self.width // 2 - 260, self.height // 2 - 210, 520, 420)
            close_btn = pygame.Rect(modal_rect.x + modal_rect.width - 80, modal_rect.y + 7, 70, 22)
            if close_btn.collidepoint(mx, my):
                self.selected_round_results = None
                return True
            if not modal_rect.collidepoint(mx, my):
                self.selected_round_results = None
                return True
            return True

        # Tier Switcher Buttons
        for t in range(1, 6):
            t_rect = pygame.Rect(24 + (t - 1) * 168, 70, 162, 28)
            if t_rect.collidepoint(mx, my):
                self.selected_tier = t
                self.selected_round_results = None
                return True

        # Standings Mode Switcher (Constructors vs Drivers)
        st_w = min(580, int(self.width * 0.46))
        cal_x = 24 + st_w + 16
        cal_w = self.width - cal_x - 24

        c_btn = pygame.Rect(24 + st_w - 246, 115, 115, 22)
        d_btn = pygame.Rect(24 + st_w - 124, 115, 115, 22)
        if c_btn.collidepoint(mx, my):
            self.standings_mode = "CONSTRUCTORS"
            return True
        elif d_btn.collidepoint(mx, my):
            self.standings_mode = "DRIVERS"
            return True

        # Calendar Round Results Click
        cal_rect = pygame.Rect(cal_x, 110, cal_w, self.height - 150)
        with gm.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM calendar WHERE tier = ? ORDER BY round ASC;", (self.selected_tier,))
            rounds = [dict(r) for r in cur.fetchall()]

        box_h = 24 if len(rounds) > 12 else 26
        gap = 4 if len(rounds) > 12 else 6
        for idx, rnd in enumerate(rounds):
            ry = cal_rect.y + 34 + idx * (box_h + gap)
            c_box = pygame.Rect(cal_rect.x + 10, ry, cal_rect.width - 20, box_h)
            if c_box.collidepoint(mx, my) and rnd.get("is_completed"):
                res = gm.db.get_series_race_results(self.selected_tier, rnd["round"])
                self.selected_round_results = {
                    "tier": self.selected_tier,
                    "round": rnd["round"],
                    "track_name": rnd["track_name"],
                    "results": res,
                }
                return True

        return False

    def render(self, surface: pygame.Surface, gm: GameManager):
        # 1. 5 Tier Switcher Buttons
        tier_names = [
            (1, "TIER 1: WSF"),
            (2, "TIER 2: CONTINENTAL"),
            (3, "TIER 3: NATIONAL"),
            (4, "TIER 4: JTS JUNIOR"),
            (5, "TIER 5: KARTING"),
        ]

        for idx, (t_num, t_label) in enumerate(tier_names):
            t_rect = pygame.Rect(24 + idx * 168, 70, 162, 28)
            is_sel = t_num == self.selected_tier
            pygame.draw.rect(surface, (35, 55, 75) if is_sel else (20, 26, 34), t_rect, border_radius=3)
            pygame.draw.rect(
                surface, UITheme.ACCENT_CYAN if is_sel else UITheme.PANEL_BORDER, t_rect, width=1, border_radius=3
            )

            lbl = self.font_btn.render(t_label, True, UITheme.TEXT_WHITE if is_sel else UITheme.TEXT_MUTED)
            surface.blit(lbl, (t_rect.x + (t_rect.width - lbl.get_width()) // 2, t_rect.y + 7))

        # 2. Championship Table (Left Column)
        st_w = min(580, int(self.width * 0.46))
        cal_x = 24 + st_w + 16
        cal_w = self.width - cal_x - 24

        st_rect = pygame.Rect(24, 110, st_w, self.height - 150)
        UITheme.draw_panel(surface, st_rect)

        st_hdr = pygame.Rect(st_rect.x, st_rect.y, st_rect.width, 32)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, st_hdr, border_top_left_radius=4, border_top_right_radius=4)
        UITheme.draw_icon(surface, "trophy", (st_rect.x + 12, st_rect.y + 8), color=(255, 215, 0), size=16)
        surface.blit(
            self.font_title.render("CHAMPIONSHIP STANDINGS", True, (255, 215, 0)), (st_rect.x + 12, st_rect.y + 8)
            self.font_title.render("CHAMPIONSHIP STANDINGS", True, (255, 215, 0)), (st_rect.x + 34, st_rect.y + 8)
        )

        # Mode Toggle Buttons: Constructors vs Drivers (anchored right)
        c_btn = pygame.Rect(st_rect.x + st_rect.width - 246, 115, 115, 22)
        d_btn = pygame.Rect(st_rect.x + st_rect.width - 124, 115, 115, 22)

        is_c = self.standings_mode == "CONSTRUCTORS"
        pygame.draw.rect(surface, (36, 56, 78) if is_c else (20, 26, 34), c_btn, border_radius=2)
        pygame.draw.rect(
            surface, UITheme.ACCENT_CYAN if is_c else UITheme.PANEL_BORDER, c_btn, width=1, border_radius=2
        UITheme.draw_button(
            surface, c_btn, "CONSTRUCTORS", self.font_badge, is_active=is_c, icon="wrench", icon_size=12
        )
        lbl_c = self.font_badge.render("CONSTRUCTORS", True, UITheme.TEXT_WHITE if is_c else UITheme.TEXT_MUTED)
        surface.blit(lbl_c, (c_btn.x + (c_btn.width - lbl_c.get_width()) // 2, c_btn.y + 4))

        is_d = self.standings_mode == "DRIVERS"
        pygame.draw.rect(surface, (36, 56, 78) if is_d else (20, 26, 34), d_btn, border_radius=2)
        pygame.draw.rect(
            surface, UITheme.ACCENT_CYAN if is_d else UITheme.PANEL_BORDER, d_btn, width=1, border_radius=2
        )
        lbl_d = self.font_badge.render("DRIVERS", True, UITheme.TEXT_WHITE if is_d else UITheme.TEXT_MUTED)
        surface.blit(lbl_d, (d_btn.x + (d_btn.width - lbl_d.get_width()) // 2, d_btn.y + 4))
        UITheme.draw_button(surface, d_btn, "DRIVERS", self.font_badge, is_active=is_d, icon="user", icon_size=12)

        # Table Header
        th_rect = pygame.Rect(st_rect.x + 10, 146, st_rect.width - 20, 22)
        pygame.draw.rect(surface, (14, 18, 24), th_rect)
        surface.blit(self.font_badge.render("POS", True, UITheme.TEXT_MUTED), (th_rect.x + 10, th_rect.y + 4))
        if is_c:
            surface.blit(
                self.font_badge.render("CONSTRUCTOR", True, UITheme.TEXT_MUTED), (th_rect.x + 56, th_rect.y + 4)
            )
            surface.blit(
                self.font_badge.render("REPUTATION", True, UITheme.TEXT_MUTED),
                (th_rect.x + th_rect.width - 150, th_rect.y + 4),
            )
            surface.blit(
                self.font_badge.render("POINTS", True, UITheme.TEXT_MUTED),
                (th_rect.x + th_rect.width - 70, th_rect.y + 4),
            )
        else:
            surface.blit(self.font_badge.render("DRIVER", True, UITheme.TEXT_MUTED), (th_rect.x + 56, th_rect.y + 4))
            surface.blit(self.font_badge.render("TEAM", True, UITheme.TEXT_MUTED), (th_rect.x + 240, th_rect.y + 4))
            surface.blit(
                self.font_badge.render("POINTS", True, UITheme.TEXT_MUTED),
                (th_rect.x + th_rect.width - 70, th_rect.y + 4),
            )

        if is_c:
            teams = gm.db.get_teams(tier=self.selected_tier)
            for idx, t in enumerate(teams):
                row_y = 172 + idx * 32
                if row_y + 30 > st_rect.y + st_rect.height:
                    break
                r_box = pygame.Rect(st_rect.x + 10, row_y, st_rect.width - 20, 28)
                is_player = bool(t["is_player"])

                pygame.draw.rect(
                    surface,
                    (28, 42, 54) if is_player else ((22, 28, 36) if idx % 2 == 0 else (16, 20, 26)),
                    r_box,
                    border_radius=2,
                )
                if is_player:
                    pygame.draw.rect(surface, UITheme.ACCENT_CYAN, r_box, width=1, border_radius=2)

                pos_str = f"P{idx + 1}"
                pos_col = (
                    (0, 240, 140) if idx == 0 else ((240, 80, 80) if idx == len(teams) - 1 else UITheme.TEXT_WHITE)
                    (255, 215, 0)
                    if idx == 0
                    else (
                        (0, 240, 140) if idx <= 2 else ((240, 80, 80) if idx == len(teams) - 1 else UITheme.TEXT_WHITE)
                    )
                )
                surface.blit(self.font_card_title.render(pos_str, True, pos_col), (r_box.x + 10, r_box.y + 6))
                if idx == 0:
                    UITheme.draw_icon(surface, "trophy", (r_box.x + 6, r_box.y + 7), color=(255, 215, 0), size=14)
                    surface.blit(self.font_card_title.render(pos_str, True, pos_col), (r_box.x + 22, r_box.y + 6))
                elif idx in (1, 2):
                    UITheme.draw_icon(surface, "medal", (r_box.x + 6, r_box.y + 7), color=(0, 240, 140), size=14)
                    surface.blit(self.font_card_title.render(pos_str, True, pos_col), (r_box.x + 22, r_box.y + 6))
                else:
                    surface.blit(self.font_card_title.render(pos_str, True, pos_col), (r_box.x + 10, r_box.y + 6))

                col_rgb = pygame.Color(t["color_hex"])
                pygame.draw.rect(surface, col_rgb, (r_box.x + 44, r_box.y + 6, 6, 16), border_radius=1)

                max_name_w = r_box.width - 215  # Up to ~345px available for team name
                t_name = t["name"]
                if is_player:
                    you_tag = " [YOU]"
                    tag_surf = self.font_badge.render(you_tag, True, (255, 215, 0))
                    tag_w = tag_surf.get_width()
                    name_trunc = self._truncate_text(self.font_card_title, t_name, max_name_w - tag_w)
                    name_surf = self.font_card_title.render(name_trunc, True, (255, 215, 0))
                    surface.blit(name_surf, (r_box.x + 56, r_box.y + 6))
                    surface.blit(tag_surf, (r_box.x + 56 + name_surf.get_width(), r_box.y + 7))
                else:
                    name_trunc = self._truncate_text(self.font_card_title, t_name, max_name_w)
                    surface.blit(
                        self.font_card_title.render(name_trunc, True, UITheme.TEXT_WHITE), (r_box.x + 56, r_box.y + 6)
                    )

                surface.blit(
                    self.font_body.render(f"{t['reputation']}/100", True, UITheme.TEXT_MUTED),
                    (r_box.x + r_box.width - 150, r_box.y + 7),
                )
                surface.blit(
                    self.font_card_title.render(f"{t['points']} PTS", True, (0, 220, 255)),
                    (r_box.x + r_box.width - 70, r_box.y + 6),
                )
        else:
            drivers = gm.db.get_driver_standings(self.selected_tier)
            for idx, d in enumerate(drivers[:15]):
                row_y = 172 + idx * 27
                if row_y + 25 > st_rect.y + st_rect.height:
                    break
                r_box = pygame.Rect(st_rect.x + 10, row_y, st_rect.width - 20, 25)
                is_acad = bool(d.get("is_academy_driver", 0))
                is_ply = bool(d.get("is_player_driver", 0))

                bg_col = (28, 46, 58) if (is_acad or is_ply) else ((22, 28, 36) if idx % 2 == 0 else (16, 20, 26))
                pygame.draw.rect(surface, bg_col, r_box, border_radius=2)
                if is_acad:
                    pygame.draw.rect(surface, (0, 240, 140), r_box, width=1, border_radius=2)
                elif is_ply:
                    pygame.draw.rect(surface, UITheme.ACCENT_CYAN, r_box, width=1, border_radius=2)

                pos_str = f"P{idx + 1}"
                pos_col = (255, 215, 0) if idx == 0 else ((0, 240, 140) if idx <= 2 else UITheme.TEXT_WHITE)
                surface.blit(self.font_badge.render(pos_str, True, pos_col), (r_box.x + 10, r_box.y + 5))
                if idx == 0:
                    UITheme.draw_icon(surface, "trophy", (r_box.x + 6, r_box.y + 6), color=(255, 215, 0), size=13)
                    surface.blit(self.font_badge.render(pos_str, True, pos_col), (r_box.x + 22, r_box.y + 5))
                elif idx in (1, 2):
                    UITheme.draw_icon(surface, "medal", (r_box.x + 6, r_box.y + 6), color=(0, 240, 140), size=13)
                    surface.blit(self.font_badge.render(pos_str, True, pos_col), (r_box.x + 22, r_box.y + 5))
                else:
                    surface.blit(self.font_badge.render(pos_str, True, pos_col), (r_box.x + 10, r_box.y + 5))

                max_driver_w = 175
                tag = " [ACADEMY]" if is_acad else (" [YOU]" if is_ply else "")
                tag_surf = self.font_badge.render(
                    tag, True, (0, 240, 140) if is_acad else ((255, 215, 0) if is_ply else UITheme.TEXT_WHITE)
                )
                tag_w = tag_surf.get_width() if tag else 0

                d_trunc = self._truncate_text(self.font_body, d["name"], max_driver_w - tag_w)
                d_col = (0, 240, 140) if is_acad else ((255, 215, 0) if is_ply else UITheme.TEXT_WHITE)
                name_surf = self.font_body.render(d_trunc, True, d_col)
                surface.blit(name_surf, (r_box.x + 56, r_box.y + 4))
                if tag:
                    surface.blit(tag_surf, (r_box.x + 56 + name_surf.get_width(), r_box.y + 5))

                max_team_w = r_box.width - 240 - 80  # Up to ~240px available for team name
                team_name = d.get("team_name", "")
                team_trunc = self._truncate_text(self.font_body, team_name, max_team_w)
                surface.blit(self.font_body.render(team_trunc, True, UITheme.TEXT_MUTED), (r_box.x + 240, r_box.y + 4))
                surface.blit(
                    self.font_card_title.render(f"{d.get('points', 0)} PTS", True, (0, 220, 255)),
                    (r_box.x + r_box.width - 70, r_box.y + 4),
                )

        # 3. Dynamic Tier Season Calendar (Right Column)
        cal_rect = pygame.Rect(cal_x, 110, cal_w, self.height - 150)
        UITheme.draw_panel(surface, cal_rect)

        with gm.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM calendar WHERE tier = ? ORDER BY round ASC;", (self.selected_tier,))
            rounds = [dict(r) for r in cur.fetchall()]

        tier_names_short = {
            1: "TIER 1 (WSF)",
            2: "TIER 2 (CONTINENTAL)",
            3: "TIER 3 (NATIONAL)",
            4: "TIER 4 (JUNIOR)",
            5: "TIER 5 (KARTING)",
        }
        t_label = tier_names_short.get(self.selected_tier, f"TIER {self.selected_tier}")
        c_hdr = pygame.Rect(cal_rect.x, cal_rect.y, cal_rect.width, 32)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, c_hdr, border_top_left_radius=4, border_top_right_radius=4)
        UITheme.draw_icon(surface, "calendar", (cal_rect.x + 12, cal_rect.y + 8), color=UITheme.ACCENT_CYAN, size=16)
        surface.blit(
            self.font_title.render(f"📅 {len(rounds)}-ROUND CALENDAR - {t_label}", True, UITheme.ACCENT_CYAN),
            (cal_rect.x + 12, cal_rect.y + 8),
            self.font_title.render(f"{len(rounds)}-ROUND CALENDAR - {t_label}", True, UITheme.ACCENT_CYAN),
            (cal_rect.x + 34, cal_rect.y + 8),
        )

        is_player_tier = self.selected_tier == gm.player_team.get("tier", 3)
        box_h = 24 if len(rounds) > 12 else 26
        gap = 4 if len(rounds) > 12 else 6

        char_colors = {
            "SPEED": {"bg": (55, 25, 20), "border": (255, 90, 60), "text": (255, 120, 90), "lbl": "SPEED"},
            "BRAKES": {"bg": (55, 45, 15), "border": (255, 190, 40), "text": (255, 210, 60), "lbl": "BRAKES"},
            "AERO": {"bg": (15, 45, 55), "border": (40, 190, 255), "text": (80, 220, 255), "lbl": "AERO"},
            "BALANCED": {"bg": (20, 45, 30), "border": (50, 200, 120), "text": (80, 230, 140), "lbl": "BALANCED"},
        }

        for idx, rnd in enumerate(rounds):
            ry = cal_rect.y + 36 + idx * (box_h + gap)
            if ry + box_h > cal_rect.y + cal_rect.height - 6:
                break
            c_box = pygame.Rect(cal_rect.x + 10, ry, cal_rect.width - 20, box_h)
            is_cur = is_player_tier and (rnd["round"] == gm.current_round) and (rnd.get("week") == gm.current_week)
            is_comp = bool(rnd["is_completed"])

            pygame.draw.rect(surface, (35, 45, 60) if is_cur else (18, 22, 28), c_box, border_radius=2)
            if is_cur:
                pygame.draw.rect(surface, (0, 240, 140), c_box, width=1, border_radius=2)

            r_num_str = f"R{rnd['round']} (Wk {rnd.get('week', 1)})"
            surface.blit(
                self.font_badge.render(r_num_str, True, (0, 240, 140) if is_cur else UITheme.TEXT_MUTED),
                (c_box.x + 8, c_box.y + 5),
            )

            # Track Name
            t_name_surf = self.font_body.render(rnd["track_name"], True, UITheme.TEXT_WHITE)
            surface.blit(t_name_surf, (c_box.x + 95, c_box.y + 5))

            # Characteristic Badge
            c_type = rnd.get("characteristic", "BALANCED")
            c_theme = char_colors.get(c_type, char_colors["BALANCED"])
            badge_lbl = self.font_badge.render(c_theme["lbl"], True, c_theme["text"])
            badge_w = max(76, badge_lbl.get_width() + 14)
            badge_h = 18
            badge_rect = pygame.Rect(c_box.x + c_box.width - 205, c_box.y + (box_h - badge_h) // 2, badge_w, badge_h)
            pygame.draw.rect(surface, c_theme["bg"], badge_rect, border_radius=3)
            pygame.draw.rect(surface, c_theme["border"], badge_rect, width=1, border_radius=3)
            surface.blit(
                badge_lbl,
                (
                    badge_rect.x + (badge_w - badge_lbl.get_width()) // 2,
                    badge_rect.y + (badge_h - badge_lbl.get_height()) // 2,
                ),
            )

            # Status / Click to View Results
            if is_comp:
                view_txt = "RESULTS 🔍"
                stat_surf = self.font_badge.render(view_txt, True, (0, 220, 120))
                UITheme.draw_icon(
                    surface, "search", (c_box.x + c_box.width - 78, c_box.y + 6), color=(0, 220, 120), size=12
                )
                stat_surf = self.font_badge.render("RESULTS", True, (0, 220, 120))
                surface.blit(stat_surf, (c_box.x + c_box.width - 62, c_box.y + 5))
            elif is_cur:
                stat_surf = self.font_badge.render("NEXT UP", True, (255, 215, 0))
                surface.blit(stat_surf, (c_box.x + c_box.width - stat_surf.get_width() - 10, c_box.y + 5))
            else:
                stat_surf = self.font_badge.render("UPCOMING", True, UITheme.TEXT_MUTED)
                surface.blit(stat_surf, (c_box.x + c_box.width - stat_surf.get_width() - 10, c_box.y + 5))

            surface.blit(stat_surf, (c_box.x + c_box.width - stat_surf.get_width() - 10, c_box.y + 5))

        # 4. Pop-up Round Results View Modal
        if self.selected_round_results:
            self._render_round_results_modal(surface)

    def _render_round_results_modal(self, surface: pygame.Surface):
        modal_w = 520
        modal_h = 420
        modal_x = (self.width - modal_w) // 2
        modal_y = (self.height - modal_h) // 2

        # Dim overlay
        dim = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 160))
        surface.blit(dim, (0, 0))

        # Box
        m_box = pygame.Rect(modal_x, modal_y, modal_w, modal_h)
        pygame.draw.rect(surface, (15, 20, 28), m_box, border_radius=6)
        pygame.draw.rect(surface, (0, 220, 255), m_box, width=2, border_radius=6)

        # Header
        hdr = pygame.Rect(modal_x, modal_y, modal_w, 36)
        pygame.draw.rect(surface, (22, 30, 44), hdr, border_top_left_radius=6, border_top_right_radius=6)

        info = self.selected_round_results
        title = f"🏁 TIER {info['tier']} ROUND {info['round']}: {info['track_name'].upper()}"
        surface.blit(self.font_card_title.render(title, True, (255, 215, 0)), (modal_x + 12, modal_y + 9))
        title = f"TIER {info['tier']} ROUND {info['round']}: {info['track_name'].upper()}"
        UITheme.draw_icon(surface, "flag", (modal_x + 12, modal_y + 10), color=(255, 215, 0), size=16)
        surface.blit(self.font_card_title.render(title, True, (255, 215, 0)), (modal_x + 34, modal_y + 9))

        close_btn = pygame.Rect(modal_x + modal_w - 80, modal_y + 7, 70, 22)
        pygame.draw.rect(surface, (140, 40, 40), close_btn, border_radius=3)
        lbl_x = self.font_badge.render("CLOSE", True, (255, 255, 255))
        surface.blit(lbl_x, (close_btn.x + (close_btn.width - lbl_x.get_width()) // 2, close_btn.y + 4))
        UITheme.draw_button(surface, close_btn, "CLOSE", self.font_badge, icon="x", icon_size=12)

        # Results Table
        results = info.get("results", [])
        if not results:
            surface.blit(
                self.font_body.render("No classification data found for this round.", True, UITheme.TEXT_MUTED),
                (modal_x + 20, modal_y + 60),
            )
            return

        # Table Header
        th = pygame.Rect(modal_x + 12, modal_y + 44, modal_w - 24, 20)
        pygame.draw.rect(surface, (12, 16, 22), th)
        surface.blit(self.font_badge.render("POS", True, UITheme.TEXT_MUTED), (th.x + 8, th.y + 3))
        surface.blit(self.font_badge.render("DRIVER", True, UITheme.TEXT_MUTED), (th.x + 50, th.y + 3))
        surface.blit(self.font_badge.render("TEAM", True, UITheme.TEXT_MUTED), (th.x + 250, th.y + 3))
        surface.blit(self.font_badge.render("POINTS", True, UITheme.TEXT_MUTED), (th.x + 430, th.y + 3))

        for idx, r in enumerate(results[:10]):
            ry = modal_y + 68 + idx * 28
            r_box = pygame.Rect(modal_x + 12, ry, modal_w - 24, 26)
            is_acad = bool(r.get("is_academy_driver"))
            is_ply = bool(r.get("is_player"))

            bg = (28, 44, 56) if (is_acad or is_ply) else ((20, 26, 34) if idx % 2 == 0 else (16, 21, 28))
            pygame.draw.rect(surface, bg, r_box, border_radius=2)
            if is_acad:
                pygame.draw.rect(surface, (0, 240, 140), r_box, width=1, border_radius=2)

            pos = r.get("position", idx + 1)
            pos_col = (255, 215, 0) if pos == 1 else ((0, 240, 140) if pos <= 3 else UITheme.TEXT_WHITE)
            surface.blit(self.font_badge.render(f"P{pos}", True, pos_col), (r_box.x + 8, r_box.y + 5))
            if pos == 1:
                UITheme.draw_icon(surface, "trophy", (r_box.x + 6, r_box.y + 6), color=(255, 215, 0), size=13)
                surface.blit(self.font_badge.render(f"P{pos}", True, pos_col), (r_box.x + 22, r_box.y + 5))
            elif pos in (2, 3):
                UITheme.draw_icon(surface, "medal", (r_box.x + 6, r_box.y + 6), color=(0, 240, 140), size=13)
                surface.blit(self.font_badge.render(f"P{pos}", True, pos_col), (r_box.x + 22, r_box.y + 5))
            else:
                surface.blit(self.font_badge.render(f"P{pos}", True, pos_col), (r_box.x + 8, r_box.y + 5))

            tag = " [ACADEMY]" if is_acad else (" [YOU]" if is_ply else "")
            d_name = f"{r.get('driver_name', 'Driver')}{tag}"
            d_col = (0, 240, 140) if is_acad else ((255, 215, 0) if is_ply else UITheme.TEXT_WHITE)
            surface.blit(self.font_body.render(d_name, True, d_col), (r_box.x + 50, r_box.y + 5))

            surface.blit(
                self.font_body.render(r.get("team_name", ""), True, UITheme.TEXT_MUTED), (r_box.x + 250, r_box.y + 5)
            )

            pts = r.get("points", 0)
            pts_col = (0, 220, 255) if pts > 0 else UITheme.TEXT_MUTED
            surface.blit(
                self.font_badge.render(f"+{pts} PTS" if pts > 0 else "-", True, pts_col), (r_box.x + 430, r_box.y + 5)
            )
