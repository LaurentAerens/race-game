from typing import Any, Callable, Dict

import pygame

from ..theme import UITheme


class HubHeader:
    """Top broadcast navigation bar for the Management Hub with dynamic responsive tab expansion."""

    def __init__(self, screen_width: int, on_cycle_difficulty: Callable[[], str]):
        self.width = screen_width
        self.height = 56
        self.rect = pygame.Rect(0, 0, screen_width, self.height)
        self.on_cycle_difficulty = on_cycle_difficulty
        self._init_fonts()

        # Navigation Tabs
        # Navigation Tabs: (key, label, icon_name)
        self.tabs = [
            ("DASHBOARD", "DASHBOARD"),
            ("CAR_RND", "CAR & R&D"),
            ("FACTORY", "TECH TREE"),
            ("DRIVERS", "DRIVERS & ACADEMY"),
            ("SPONSORS", "SPONSORS & FINANCES"),
            ("WORKFORCE", "PERSONNEL"),
            ("STANDINGS", "STANDINGS"),
            ("DATABASE", "DATABASE EXPLORER"),
            ("DASHBOARD", "DASHBOARD", "layout-dashboard"),
            ("CAR_RND", "CAR R&D", "wrench"),
            ("FACTORY", "TECH TREE", "network"),
            ("DRIVERS", "DRIVERS", "user"),
            ("SPONSORS", "FINANCES", "circle-dollar-sign"),
            ("WORKFORCE", "PERSONNEL", "users"),
            ("STANDINGS", "STANDINGS", "trophy"),
            ("DATABASE", "DATABASE", "database"),
        ]

    def _init_fonts(self):
        self.font_team = UITheme.get_font(13, bold=True)
        self.font_stat = UITheme.get_font(11, bold=True)
        self.font_tab = UITheme.get_font(11, bold=True)
        self.font_diff = UITheme.get_font(10, bold=True)

    def resize(self, width: int):
        self.width = width
        self.rect = pygame.Rect(0, 0, width, self.height)
        self._init_fonts()

    def get_tab_rects(self) -> Dict[str, pygame.Rect]:
        """Dynamically scales tab widths based on screen width to ensure generous padding and zero text spill."""
        num_tabs = len(self.tabs)
        x_start = 18
        avail_w = self.width - 36
        gap = 6

        # Proportional width calculation (min 130px, max 240px)
        calculated_w = (avail_w - (num_tabs - 1) * gap) // num_tabs
        tab_w = max(130, min(240, calculated_w))
        tab_h = 26
        y = 26

        rects = {}
        for idx, (t_key, _) in enumerate(self.tabs):
        for idx, (t_key, _, _) in enumerate(self.tabs):
            rects[t_key] = pygame.Rect(x_start + idx * (tab_w + gap), y, tab_w, tab_h)
        return rects

    def handle_click(self, mx: int, my: int) -> str:
        # Check Tutorial Button Click
        tut_btn = pygame.Rect(self.width - 340, 4, 92, 18)
        if tut_btn.collidepoint(mx, my):
            return "ACTION_TUTORIAL"

        # Check Difficulty Button Click (Top right area)
        diff_btn = pygame.Rect(self.width - 240, 4, 112, 18)
        if diff_btn.collidepoint(mx, my):
            new_diff = self.on_cycle_difficulty()
            return f"DIFF_{new_diff}"

        # Check Track Editor Quick Button
        edit_btn = pygame.Rect(self.width - 120, 4, 105, 18)
        if edit_btn.collidepoint(mx, my):
            return "MODE_EDITOR"

        tab_rects = self.get_tab_rects()
        for t_key, r in tab_rects.items():
            if r.collidepoint(mx, my):
                return t_key
        return ""

    def render(
        self,
        surface: pygame.Surface,
        active_tab: str,
        team_data: Dict[str, Any],
        financial_data: Dict[str, Any],
        current_round: int,
        total_rounds: int,
        difficulty: str = "NORMAL",
    ):
        from ..icons import UIIcons

        # Header background panel
        pygame.draw.rect(surface, (14, 18, 24), self.rect)
        pygame.draw.line(surface, UITheme.PANEL_BORDER, (0, self.height), (self.width, self.height), 1)

        # Team identity badge (Left)
        t_name = team_data.get("name", "Player Team")
        tier_names = {1: "TIER 1 (WSF)", 2: "TIER 2 (CONTINENTAL)", 3: "TIER 3 (NATIONAL CUP)"}
        t_tier = tier_names.get(team_data.get("tier", 3), "TIER 3")

        col_rgb = pygame.Color(team_data.get("color_hex", "#00d2be"))
        pygame.draw.rect(surface, col_rgb, (18, 6, 8, 14), border_radius=2)
        team_surf = self.font_team.render(f"{t_name.upper()}  [{t_tier}]", True, UITheme.TEXT_WHITE)
        surface.blit(team_surf, (32, 5))

        # Financial & Round Stats (Dynamically anchored left of tutorial & difficulty button)
        # Financial & Round Stats with Icons
        cash = financial_data.get("cash", 0.0)
        net_mo = financial_data.get("net_monthly", 0.0)
        staff_cnt = financial_data.get("staff_count", 24)

        net_str = f"+${net_mo:,.0f}/mo" if net_mo >= 0 else f"-${abs(net_mo):,.0f}/mo"
        stat_txt = f"CASH: ${cash:,.0f}   |   NET: {net_str}   |   STAFF: {staff_cnt}   |   ROUND: {current_round}/{total_rounds}"
        s_surf = self.font_stat.render(stat_txt, True, UITheme.TEXT_MUTED)
        stats_x = team_surf.get_width() + 45

        stats_x = max(team_surf.get_width() + 40, self.width - 355 - s_surf.get_width())
        surface.blit(s_surf, (stats_x, 6))
        # 1. Cash Pill
        c_ic = UIIcons.get_icon("circle-dollar-sign", size=13, color=(0, 240, 140))
        c_txt = self.font_stat.render(f"${cash:,.0f}", True, (0, 240, 140))
        surface.blit(c_ic, (stats_x, 6))
        surface.blit(c_txt, (stats_x + 16, 5))
        stats_x += 16 + c_txt.get_width() + 16

        # 2. Net Monthly Pill
        is_pos = net_mo >= 0
        net_ic_name = "trending-up" if is_pos else "trending-down"
        net_col = (0, 230, 110) if is_pos else (240, 60, 60)
        n_ic = UIIcons.get_icon(net_ic_name, size=13, color=net_col)
        n_txt = self.font_stat.render(f"{'+' if is_pos else '-'}${abs(net_mo):,.0f}/mo", True, net_col)
        surface.blit(n_ic, (stats_x, 6))
        surface.blit(n_txt, (stats_x + 16, 5))
        stats_x += 16 + n_txt.get_width() + 16

        # 3. Staff Pill
        s_ic = UIIcons.get_icon("users", size=13, color=UITheme.TEXT_MUTED)
        s_txt = self.font_stat.render(f"{staff_cnt}", True, UITheme.TEXT_MUTED)
        surface.blit(s_ic, (stats_x, 6))
        surface.blit(s_txt, (stats_x + 16, 5))
        stats_x += 16 + s_txt.get_width() + 16

        # 4. Round Pill
        r_ic = UIIcons.get_icon("flag", size=13, color=UITheme.ACCENT_YELLOW)
        r_txt = self.font_stat.render(f"{current_round}/{total_rounds}", True, UITheme.ACCENT_YELLOW)
        surface.blit(r_ic, (stats_x, 6))
        surface.blit(r_txt, (stats_x + 16, 5))

        # Tutorial Button (x = width - 340)
        tut_btn = pygame.Rect(self.width - 340, 4, 92, 18)
        pygame.draw.rect(surface, (18, 26, 38), tut_btn, border_radius=3)
        pygame.draw.rect(surface, (0, 200, 240), tut_btn, width=1, border_radius=3)
        tut_lbl = self.font_diff.render("? TUTORIAL", True, (0, 220, 255))
        surface.blit(tut_lbl, (tut_btn.x + (tut_btn.width - tut_lbl.get_width()) // 2, tut_btn.y + 3))
        tut_ic = UIIcons.get_icon("help-circle", size=11, color=(0, 220, 255))
        tut_lbl = self.font_diff.render("TUTORIAL", True, (0, 220, 255))
        tut_w = tut_ic.get_width() + 4 + tut_lbl.get_width()
        tut_start = tut_btn.x + (tut_btn.width - tut_w) // 2
        surface.blit(tut_ic, (tut_start, tut_btn.y + 3))
        surface.blit(tut_lbl, (tut_start + tut_ic.get_width() + 4, tut_btn.y + 3))

        # Difficulty Selector Button (Top right: x = width - 240)
        diff_btn = pygame.Rect(self.width - 240, 4, 112, 18)
        diff_cols = {
            "VERY_EASY": (0, 240, 140),
            "EASY": (0, 200, 255),
            "NORMAL": (255, 215, 0),
            "HARD": (255, 140, 40),
            "VERY_HARD": (255, 60, 60),
        }
        d_col = diff_cols.get(difficulty, (255, 215, 0))
        pygame.draw.rect(surface, (22, 28, 36), diff_btn, border_radius=2)
        pygame.draw.rect(surface, d_col, diff_btn, width=1, border_radius=2)

        diff_label = f"DIFF: {difficulty.replace('_', ' ')}"
        d_ic = UIIcons.get_icon("zap", size=11, color=d_col)
        diff_label = difficulty.replace("_", " ")
        d_surf = self.font_diff.render(diff_label, True, d_col)
        surface.blit(d_surf, (diff_btn.x + (diff_btn.width - d_surf.get_width()) // 2, diff_btn.y + 2))
        d_w = d_ic.get_width() + 4 + d_surf.get_width()
        d_start = diff_btn.x + (diff_btn.width - d_w) // 2
        surface.blit(d_ic, (d_start, diff_btn.y + 3))
        surface.blit(d_surf, (d_start + d_ic.get_width() + 4, diff_btn.y + 2))

        # Track Editor Mode Button (Top right: x = width - 120)
        edit_btn = pygame.Rect(self.width - 120, 4, 105, 18)
        pygame.draw.rect(surface, (26, 34, 46), edit_btn, border_radius=2)
        pygame.draw.rect(surface, UITheme.PANEL_BORDER, edit_btn, width=1, border_radius=2)
        ed_ic = UIIcons.get_icon("wrench", size=11, color=UITheme.TEXT_WHITE)
        e_surf = self.font_diff.render("TRACK EDITOR", True, UITheme.TEXT_WHITE)
        surface.blit(e_surf, (edit_btn.x + (edit_btn.width - e_surf.get_width()) // 2, edit_btn.y + 2))
        ed_w = ed_ic.get_width() + 4 + e_surf.get_width()
        ed_start = edit_btn.x + (edit_btn.width - ed_w) // 2
        surface.blit(ed_ic, (ed_start, edit_btn.y + 3))
        surface.blit(e_surf, (ed_start + ed_ic.get_width() + 4, edit_btn.y + 2))

        # Navigation Tabs (Bottom Row)
        tab_rects = self.get_tab_rects()
        for t_key, label in self.tabs:
        for t_key, label, icon_name in self.tabs:
            r = tab_rects[t_key]
            is_active = t_key == active_tab
            bg_col = (35, 45, 60) if is_active else (20, 24, 32)
            border_col = UITheme.ACCENT_CYAN if is_active else (45, 55, 70)

            pygame.draw.rect(surface, bg_col, r, border_radius=3)
            pygame.draw.rect(surface, border_col, r, width=1, border_radius=3)

            txt_col = UITheme.TEXT_WHITE if is_active else UITheme.TEXT_MUTED
            t_lbl = self.font_tab.render(label, True, txt_col)
            surface.blit(t_lbl, (r.x + (r.width - t_lbl.get_width()) // 2, r.y + (r.height - t_lbl.get_height()) // 2))
            ic_surf = UIIcons.get_icon(icon_name, size=14, color=txt_col)

            gap = 5
            total_content_w = ic_surf.get_width() + gap + t_lbl.get_width()
            start_content_x = r.x + (r.width - total_content_w) // 2

            surface.blit(ic_surf, (start_content_x, r.y + (r.height - ic_surf.get_height()) // 2))
            surface.blit(
                t_lbl, (start_content_x + ic_surf.get_width() + gap, r.y + (r.height - t_lbl.get_height()) // 2)
            )
