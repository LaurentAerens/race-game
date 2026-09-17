from typing import Any, Dict, List, Optional

import pygame

from ...management.game_manager import GameManager
from ..theme import UITheme


class DatabaseExplorerTab:
    """
    Interactive Motorsport Almanac & Database Explorer:
    - Multi-year season archive across all 5 tiers (rankings, points, race results)
    - Fully clickable navigation: click any driver or team anywhere to jump straight to their overview!
    - Comprehensive Driver Dossier & Alumni Tracker (ex-player drivers, what they do after leaving)
    - Comprehensive Constructor Dossier & Team Directory (drivers, stats, historic finishes)
    - All-Time Hall of Fame records
    - AI Career Trajectory Intelligence
    """

    def __init__(self, screen_width: int, screen_height: int):
        self.width = screen_width
        self.height = screen_height

        self.active_subtab: str = "SEASON_ARCHIVE"  # "SEASON_ARCHIVE", "DRIVERS", "CONSTRUCTORS", "HALL_OF_FAME"
        self.previous_subtab: Optional[str] = None

        # Season Archive state
        self.selected_season_idx: int = 0
        self.seasons_list: List[Dict[str, Any]] = []
        self.selected_tier: int = 3
        self.archive_mode: str = "CONSTRUCTORS"  # "CONSTRUCTORS", "DRIVERS", "RACES"
        self.selected_round_results: Optional[Dict[str, Any]] = None

        # Driver Dossier state
        self.driver_filter: str = "ALUMNI"  # "ALUMNI", "ALL", "T1", "T2", "T3", "T4_5", "FREE_AGENT"
        self.selected_driver_id: Optional[int] = None
        self.driver_list_scroll: int = 0
        self.driver_search_query: str = ""

        # Constructor Dossier state
        self.team_selected_tier: int = 1
        self.selected_team_id: Optional[int] = None
        self.team_list_scroll: int = 0

        self.return_hub_tab: Optional[str] = None
        self.return_hub_tab_requested: Optional[str] = None

        self._init_fonts()

    def open_driver_profile(
        self, driver_id: int, return_subtab: Optional[str] = None, return_hub_tab: Optional[str] = None
    ):
        """Programmatically switches active view to Driver Dossier and opens the given driver profile."""
        self.selected_driver_id = driver_id
        if return_subtab:
            self.previous_subtab = return_subtab
        if return_hub_tab:
            self.return_hub_tab = return_hub_tab
        self.active_subtab = "DRIVERS"
        self.selected_round_results = None

    def open_team_profile(
        self, team_id: int, team_tier: Optional[int] = None, return_subtab: Optional[str] = "DRIVERS"
    ):
        """Programmatically switches active view to Constructor Dossier and opens the given team profile."""
        self.selected_team_id = team_id
        if team_tier:
            self.team_selected_tier = team_tier
        if return_subtab:
            self.previous_subtab = return_subtab
        self.active_subtab = "CONSTRUCTORS"
        self.selected_round_results = None

    def _init_fonts(self):
        self.font_header = UITheme.get_font(13, bold=True)
        self.font_title = UITheme.get_font(12, bold=True)
        self.font_btn = UITheme.get_font(11, bold=True)
        self.font_body = UITheme.get_font(10, bold=False)
        self.font_body_bold = UITheme.get_font(10, bold=True)
        self.font_badge = UITheme.get_font(9, bold=True)
        self.font_stat = UITheme.get_font(13, bold=True)
        self.font_huge = UITheme.get_font(16, bold=True)

    def resize(self, width: int, height: int):
        self.width = width
        self.height = height
        self._init_fonts()

    def handle_scroll(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEWHEEL:
            if self.active_subtab == "DRIVERS":
                self.driver_list_scroll = max(0, self.driver_list_scroll - event.y * 30)
            elif self.active_subtab == "CONSTRUCTORS":
                self.team_list_scroll = max(0, self.team_list_scroll - event.y * 30)

    def handle_click(self, mx: int, my: int, gm: GameManager) -> bool:
        # 1. Round Results Modal clicks
        if self.selected_round_results:
            modal_w = 560
            modal_h = 440
            modal_x = (self.width - modal_w) // 2
            modal_y = (self.height - modal_h) // 2
            modal_rect = pygame.Rect(modal_x, modal_y, modal_w, modal_h)

            close_btn = pygame.Rect(modal_x + modal_w - 75, modal_y + 7, 65, 22)
            if close_btn.collidepoint(mx, my) or not modal_rect.collidepoint(mx, my):
                self.selected_round_results = None
                return True

            # Click driver or team inside results modal
            results = self.selected_round_results.get("results", [])
            for idx, r in enumerate(results[:12]):
                ry = modal_y + 68 + idx * 28
                drv_rect = pygame.Rect(modal_x + 60, ry, 190, 24)
                team_rect = pygame.Rect(modal_x + 250, ry, 170, 24)

                if drv_rect.collidepoint(mx, my) and r.get("driver_id"):
                    self.selected_driver_id = r["driver_id"]
                    self.previous_subtab = self.active_subtab
                    self.active_subtab = "DRIVERS"
                    self.selected_round_results = None
                    return True
                elif team_rect.collidepoint(mx, my) and r.get("team_id"):
                    self.selected_team_id = r["team_id"]
                    self.team_selected_tier = r.get("tier", self.selected_tier)
                    self.previous_subtab = self.active_subtab
                    self.active_subtab = "CONSTRUCTORS"
                    self.selected_round_results = None
                    return True
            return True

        # 2. Subtab switcher (Top row at y = 68)
        subtabs = [
            ("SEASON_ARCHIVE", "SEASON ARCHIVE", "calendar"),
            ("DRIVERS", "DRIVER DOSSIER & ALUMNI", "user"),
            ("CONSTRUCTORS", "CONSTRUCTORS", "wrench"),
            ("HALL_OF_FAME", "HALL OF FAME", "trophy"),
        ]
        subtab_w = 200
        for idx, (st_id, _, _) in enumerate(subtabs):
            st_rect = pygame.Rect(24 + idx * (subtab_w + 10), 68, subtab_w, 28)
            if st_rect.collidepoint(mx, my):
                self.previous_subtab = self.active_subtab
                self.active_subtab = st_id
                self.selected_round_results = None
                return True

        # 3. Route click to active subtab
        if self.active_subtab == "SEASON_ARCHIVE":
            return self._handle_click_season_archive(mx, my, gm)
        elif self.active_subtab == "DRIVERS":
            return self._handle_click_drivers(mx, my, gm)
        elif self.active_subtab == "CONSTRUCTORS":
            return self._handle_click_constructors(mx, my, gm)
        elif self.active_subtab == "HALL_OF_FAME":
            return self._handle_click_hall_of_fame(mx, my, gm)

        return False

    def _handle_click_season_archive(self, mx: int, my: int, gm: GameManager) -> bool:
        seasons = gm.db.get_available_seasons()
        if not seasons:
            return False

        # Season navigation arrows
        prev_s_btn = pygame.Rect(24, 108, 30, 26)
        next_s_btn = pygame.Rect(324, 108, 30, 26)
        if prev_s_btn.collidepoint(mx, my):
            self.selected_season_idx = min(len(seasons) - 1, self.selected_season_idx + 1)
            self.selected_round_results = None
            return True
        elif next_s_btn.collidepoint(mx, my):
            self.selected_season_idx = max(0, self.selected_season_idx - 1)
            self.selected_round_results = None
            return True

        # Tier buttons (1 to 5)
        for t in range(1, 6):
            t_btn = pygame.Rect(370 + (t - 1) * 115, 108, 108, 26)
            if t_btn.collidepoint(mx, my):
                self.selected_tier = t
                self.selected_round_results = None
                return True

        # Mode toggles: Constructors, Drivers, Calendar Races
        c_btn = pygame.Rect(24, 146, 140, 24)
        d_btn = pygame.Rect(170, 146, 140, 24)
        r_btn = pygame.Rect(316, 146, 150, 24)

        if c_btn.collidepoint(mx, my):
            self.archive_mode = "CONSTRUCTORS"
            return True
        elif d_btn.collidepoint(mx, my):
            self.archive_mode = "DRIVERS"
            return True
        elif r_btn.collidepoint(mx, my):
            self.archive_mode = "RACES"
            return True

        sel_season = seasons[self.selected_season_idx]["season_num"]
        box_x, box_y = 24, 178
        box_w = self.width - 48
        box_h = self.height - 198

        # Clickable rows in CONSTRUCTORS mode -> jump to team overview
        if self.archive_mode == "CONSTRUCTORS":
            teams = gm.db.get_historical_constructor_standings(sel_season, self.selected_tier)
            for idx, t in enumerate(teams):
                row_y = box_y + 36 + idx * 30
                if row_y + 28 > box_y + box_h:
                    break
                row_rect = pygame.Rect(box_x + 8, row_y, box_w - 16, 28)
                if row_rect.collidepoint(mx, my):
                    self.selected_team_id = t["id"]
                    self.team_selected_tier = t.get("tier", self.selected_tier)
                    self.previous_subtab = "SEASON_ARCHIVE"
                    self.active_subtab = "CONSTRUCTORS"
                    return True

        # Clickable rows in DRIVERS mode -> click driver or team to jump
        elif self.archive_mode == "DRIVERS":
            drivers = gm.db.get_historical_driver_standings(sel_season, self.selected_tier)
            for idx, d in enumerate(drivers[:18]):
                row_y = box_y + 36 + idx * 28
                if row_y + 26 > box_y + box_h:
                    break
                drv_rect = pygame.Rect(box_x + 80, row_y, 270, 26)
                team_rect = pygame.Rect(box_x + 360, row_y, 250, 26)

                if drv_rect.collidepoint(mx, my):
                    self.selected_driver_id = d.get("driver_id") or d.get("id")
                    self.previous_subtab = "SEASON_ARCHIVE"
                    self.active_subtab = "DRIVERS"
                    return True
                elif team_rect.collidepoint(mx, my) and d.get("team_id"):
                    self.selected_team_id = d["team_id"]
                    self.team_selected_tier = d.get("tier", self.selected_tier)
                    self.previous_subtab = "SEASON_ARCHIVE"
                    self.active_subtab = "CONSTRUCTORS"
                    return True

        # Clickable rows in RACES mode -> click winner driver/team or results button
        elif self.archive_mode == "RACES":
            races = gm.db.get_historical_season_races(sel_season, self.selected_tier)
            for idx, r in enumerate(races):
                row_y = box_y + 36 + idx * 30
                if row_y + 28 > box_y + box_h:
                    break
                btn_view = pygame.Rect(self.width - 240, row_y + 3, 100, 22)
                if btn_view.collidepoint(mx, my):
                    res = gm.db.get_race_classification(sel_season, self.selected_tier, r["round_num"])
                    self.selected_round_results = {
                        "tier": self.selected_tier,
                        "season_num": sel_season,
                        "round": r["round_num"],
                        "track_name": r["track_name"],
                        "results": res,
                    }
                    return True

        return False

    def _handle_click_drivers(self, mx: int, my: int, gm: GameManager) -> bool:
        # Back button
        if self.previous_subtab or self.return_hub_tab:
            back_btn = pygame.Rect(self.width - 120, 108, 96, 24)
            if back_btn.collidepoint(mx, my):
                if self.return_hub_tab:
                    target_hub = self.return_hub_tab
                    self.return_hub_tab = None
                    self.return_hub_tab_requested = target_hub
                    return True
                target = self.previous_subtab
                self.previous_subtab = None
                self.active_subtab = target
                return True

        # Filter buttons
        filters = [
            ("ALUMNI", "★ ALUMNI"),
            ("ALL", "ALL DRIVERS"),
            ("T1", "TIER 1 (WSF)"),
            ("T2", "TIER 2 (CC)"),
            ("T3", "TIER 3 (NOC)"),
            ("T4_5", "FEEDERS"),
            ("FREE_AGENT", "FREE AGENTS"),
        ]
        fx = 24
        for f_key, f_lbl in filters:
            btn_w = 120 if f_key == "ALUMNI" else 96
            f_rect = pygame.Rect(fx, 108, btn_w, 24)
            if f_rect.collidepoint(mx, my):
                self.driver_filter = f_key
                self.driver_list_scroll = 0
                return True
            fx += btn_w + 6

        # Driver list selection click
        drivers = self._get_filtered_drivers(gm)
        panel_y = 144
        panel_h = self.height - 165
        for idx, d in enumerate(drivers):
            item_y = panel_y + 4 + idx * 46 - self.driver_list_scroll
            if item_y < panel_y or item_y + 42 > panel_y + panel_h:
                continue
            item_rect = pygame.Rect(24, item_y, 360, 42)
            if item_rect.collidepoint(mx, my):
                self.selected_driver_id = d["id"]
                return True

        # Clickable constructor links inside Driver Dossier (Right Panel)
        if self.selected_driver_id:
            profile = gm.db.get_driver_profile(self.selected_driver_id)
            if profile:
                detail_box = pygame.Rect(400, 144, self.width - 424, self.height - 165)

                # 1. Header constructor button/link
                team_id = profile.get("team_id")
                t_name = profile.get("team_name", "")
                if not team_id and t_name and t_name not in ("Free Agent", "Youth Academy Prospect", "Youth Prospect"):
                    t_obj = gm.db.get_team_by_name(t_name)
                    if t_obj:
                        team_id = t_obj["id"]

                if team_id:
                    team_btn_rect = pygame.Rect(detail_box.x + 60, detail_box.y + 24, 240, 24)
                    if team_btn_rect.collidepoint(mx, my):
                        self.open_team_profile(team_id, team_tier=profile.get("team_tier", 1), return_subtab="DRIVERS")
                        return True

                # 2. Historical Season Breakdown Constructor links
                cur_y = detail_box.y + 58
                if profile.get("is_team_alumni", False):
                    cur_y += 46
                cur_y += 48 + 66 + 18

                seasons_hist = profile.get("season_history", [])
                for s_idx, sh in enumerate(seasons_hist):
                    row_y = cur_y + 24 + s_idx * 24
                    if row_y + 22 > detail_box.y + detail_box.height:
                        break
                    team_cell_rect = pygame.Rect(detail_box.x + 12 + 215, row_y, 195, 22)
                    if team_cell_rect.collidepoint(mx, my):
                        sh_team_id = sh.get("team_id")
                        sh_team_name = sh.get("team_name", "")
                        if not sh_team_id and sh_team_name and sh_team_name not in ("Free Agent", "None"):
                            t_obj = gm.db.get_team_by_name(sh_team_name)
                            if t_obj:
                                sh_team_id = t_obj["id"]

                        if sh_team_id:
                            self.open_team_profile(sh_team_id, team_tier=sh.get("tier", 1), return_subtab="DRIVERS")
                            return True

        return False

    def _handle_click_constructors(self, mx: int, my: int, gm: GameManager) -> bool:
        # Back button
        if self.previous_subtab:
            back_btn = pygame.Rect(self.width - 120, 108, 96, 24)
            if back_btn.collidepoint(mx, my):
                target = self.previous_subtab
                self.previous_subtab = None
                self.active_subtab = target
                return True

        # Tier switcher buttons
        for t in range(1, 6):
            t_btn = pygame.Rect(24 + (t - 1) * 125, 108, 118, 26)
            if t_btn.collidepoint(mx, my):
                self.team_selected_tier = t
                teams = gm.db.get_teams(tier=t)
                if teams:
                    self.selected_team_id = teams[0]["id"]
                return True

        # Team list click on left panel
        teams = gm.db.get_teams(tier=self.team_selected_tier)
        panel_y = 144
        panel_h = self.height - 165
        for idx, t in enumerate(teams):
            item_y = panel_y + 32 + idx * 48 - self.team_list_scroll
            if item_y < panel_y + 30 or item_y + 44 > panel_y + panel_h:
                continue
            item_rect = pygame.Rect(30, item_y, 310, 44)
            if item_rect.collidepoint(mx, my):
                self.selected_team_id = t["id"]
                return True

        # Clicks inside Constructor Dossier (Right Panel)
        if self.selected_team_id:
            team_prof = gm.db.get_team_profile(self.selected_team_id)
            if team_prof:
                detail_box = pygame.Rect(370, 144, self.width - 394, self.height - 165)
                # Driver cards click
                drivers = team_prof.get("drivers", [])
                card_w = (detail_box.width - 34) // 2
                card_y = detail_box.y + 60
                for d_idx, d in enumerate(drivers[:2]):
                    d_rect = pygame.Rect(detail_box.x + 12 + d_idx * (card_w + 10), card_y, card_w, 64)
                    if d_rect.collidepoint(mx, my) and d.get("id"):
                        self.selected_driver_id = d["id"]
                        self.previous_subtab = "CONSTRUCTORS"
                        self.active_subtab = "DRIVERS"
                        return True

        return False

    def _handle_click_hall_of_fame(self, mx: int, my: int, gm: GameManager) -> bool:
        records = gm.db.get_all_time_records()
        box = pygame.Rect(24, 108, self.width - 48, self.height - 128)
        half_w = (box.width - 36) // 2
        half_h = (box.height - 36) // 2

        # 1. Top champions (Top-Left) -> jump to driver
        for idx, d in enumerate(records.get("top_champions", [])[:5]):
            ry = box.y + 12 + 34 + idx * 26
            row_rect = pygame.Rect(box.x + 12, ry, half_w, 24)
            if row_rect.collidepoint(mx, my):
                with gm.db.get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT id FROM drivers WHERE name = ? LIMIT 1;", (d["driver_name"],))
                    r = cur.fetchone()
                    if r:
                        self.selected_driver_id = r[0]
                        self.previous_subtab = "HALL_OF_FAME"
                        self.active_subtab = "DRIVERS"
                        return True

        # 2. Top constructors (Top-Right) -> jump to team
        for idx, t in enumerate(records.get("top_constructors", [])[:5]):
            ry = box.y + 12 + 34 + idx * 26
            row_rect = pygame.Rect(box.x + 24 + half_w, ry, half_w, 24)
            if row_rect.collidepoint(mx, my):
                with gm.db.get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT id, tier FROM teams WHERE name = ? LIMIT 1;", (t["name"],))
                    r = cur.fetchone()
                    if r:
                        self.selected_team_id = r[0]
                        self.team_selected_tier = r[1]
                        self.previous_subtab = "HALL_OF_FAME"
                        self.active_subtab = "CONSTRUCTORS"
                        return True

        # 3. Top wins (Bottom-Left) -> jump to driver
        for idx, d in enumerate(records.get("top_wins_drivers", [])[:5]):
            ry = box.y + 24 + half_h + 34 + idx * 26
            row_rect = pygame.Rect(box.x + 12, ry, half_w, 24)
            if row_rect.collidepoint(mx, my):
                with gm.db.get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT id FROM drivers WHERE name = ? LIMIT 1;", (d["driver_name"],))
                    r = cur.fetchone()
                    if r:
                        self.selected_driver_id = r[0]
                        self.previous_subtab = "HALL_OF_FAME"
                        self.active_subtab = "DRIVERS"
                        return True

        # 4. Top points (Bottom-Right) -> jump to driver
        for idx, d in enumerate(records.get("top_pts_drivers", [])[:5]):
            ry = box.y + 24 + half_h + 34 + idx * 26
            row_rect = pygame.Rect(box.x + 24 + half_w, ry, half_w, 24)
            if row_rect.collidepoint(mx, my):
                with gm.db.get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT id FROM drivers WHERE name = ? LIMIT 1;", (d["driver_name"],))
                    r = cur.fetchone()
                    if r:
                        self.selected_driver_id = r[0]
                        self.previous_subtab = "HALL_OF_FAME"
                        self.active_subtab = "DRIVERS"
                        return True

        return False

    def _get_filtered_drivers(self, gm: GameManager) -> List[Dict[str, Any]]:
        tier_arg = None
        only_alumni = False
        if self.driver_filter == "ALUMNI":
            only_alumni = True
        elif self.driver_filter == "T1":
            tier_arg = 1
        elif self.driver_filter == "T2":
            tier_arg = 2
        elif self.driver_filter == "T3":
            tier_arg = 3
        elif self.driver_filter == "T4_5":
            return [
                d
                for d in gm.db.get_all_drivers_directory(player_team_id=gm.team_id)
                if (d.get("team_tier") in [4, 5] or d.get("is_academy_driver"))
            ]
        elif self.driver_filter == "FREE_AGENT":
            return [d for d in gm.db.get_all_drivers_directory(player_team_id=gm.team_id) if not d.get("team_id")]

        return gm.db.get_all_drivers_directory(tier=tier_arg, only_alumni=only_alumni, player_team_id=gm.team_id)

    def render(self, surface: pygame.Surface, gm: GameManager):
        # 1. Top Subtab Bar
        subtabs = [
            ("SEASON_ARCHIVE", "SEASON ARCHIVE", "calendar"),
            ("DRIVERS", "DRIVER DOSSIER & ALUMNI", "user"),
            ("CONSTRUCTORS", "CONSTRUCTORS", "wrench"),
            ("HALL_OF_FAME", "HALL OF FAME", "trophy"),
        ]
        subtab_w = 200
        for idx, (st_id, st_lbl, st_icon) in enumerate(subtabs):
            st_rect = pygame.Rect(24 + idx * (subtab_w + 10), 68, subtab_w, 28)
            is_sel = self.active_subtab == st_id
            UITheme.draw_button(surface, st_rect, st_lbl, self.font_btn, is_active=is_sel, icon=st_icon, icon_size=14)

        # 2. Render Active Subtab Content
        if self.active_subtab == "SEASON_ARCHIVE":
            self._render_season_archive(surface, gm)
        elif self.active_subtab == "DRIVERS":
            self._render_drivers(surface, gm)
        elif self.active_subtab == "CONSTRUCTORS":
            self._render_constructors(surface, gm)
        elif self.active_subtab == "HALL_OF_FAME":
            self._render_hall_of_fame(surface, gm)

        # 3. Round Results Modal
        if self.selected_round_results:
            self._render_round_results_modal(surface)

    def _render_season_archive(self, surface: pygame.Surface, gm: GameManager):
        seasons = gm.db.get_available_seasons()
        if not seasons:
            return

        if self.selected_season_idx >= len(seasons):
            self.selected_season_idx = 0

        curr_s_info = seasons[self.selected_season_idx]
        sel_season_num = curr_s_info["season_num"]

        # Season Selector Bar
        s_box = pygame.Rect(24, 108, 330, 26)
        pygame.draw.rect(surface, (20, 26, 36), s_box, border_radius=3)
        pygame.draw.rect(surface, UITheme.PANEL_BORDER, s_box, width=1, border_radius=3)

        # Arrows
        prev_s_btn = pygame.Rect(24, 108, 30, 26)
        next_s_btn = pygame.Rect(324, 108, 30, 26)
        pygame.draw.rect(surface, (28, 38, 52), prev_s_btn, border_top_left_radius=3, border_bottom_left_radius=3)
        pygame.draw.rect(surface, (28, 38, 52), next_s_btn, border_top_right_radius=3, border_bottom_right_radius=3)
        surface.blit(self.font_btn.render("◄", True, UITheme.ACCENT_CYAN), (prev_s_btn.x + 9, prev_s_btn.y + 5))
        surface.blit(self.font_btn.render("►", True, UITheme.ACCENT_CYAN), (next_s_btn.x + 10, next_s_btn.y + 5))

        # Label
        s_txt = curr_s_info["label"]
        txt_surf = self.font_btn.render(s_txt, True, (255, 215, 0) if curr_s_info["is_current"] else UITheme.TEXT_WHITE)
        surface.blit(txt_surf, (s_box.x + (s_box.width - txt_surf.get_width()) // 2, s_box.y + 5))

        # Tier Buttons (1 to 5)
        tier_names = {1: "T1: WSF", 2: "T2: CONTINENTAL", 3: "T3: NATIONAL", 4: "T4: JUNIOR", 5: "T5: KARTING"}
        for t in range(1, 6):
            t_btn = pygame.Rect(370 + (t - 1) * 115, 108, 108, 26)
            is_sel = t == self.selected_tier
            pygame.draw.rect(surface, (34, 52, 70) if is_sel else (18, 24, 32), t_btn, border_radius=2)
            pygame.draw.rect(
                surface, UITheme.ACCENT_CYAN if is_sel else UITheme.PANEL_BORDER, t_btn, width=1, border_radius=2
            )
            t_lbl = self.font_badge.render(tier_names[t], True, UITheme.TEXT_WHITE if is_sel else UITheme.TEXT_MUTED)
            surface.blit(t_lbl, (t_btn.x + (t_btn.width - t_lbl.get_width()) // 2, t_btn.y + 6))

        # Mode toggles: Constructors, Drivers, Races
        c_btn = pygame.Rect(24, 146, 140, 24)
        d_btn = pygame.Rect(170, 146, 140, 24)
        r_btn = pygame.Rect(316, 146, 150, 24)

        is_c = self.archive_mode == "CONSTRUCTORS"
        is_d = self.archive_mode == "DRIVERS"
        is_r = self.archive_mode == "RACES"

        UITheme.draw_button(
            surface, c_btn, "CONSTRUCTORS", self.font_badge, is_active=is_c, icon="wrench", icon_size=12
        )
        UITheme.draw_button(surface, d_btn, "DRIVERS TABLE", self.font_badge, is_active=is_d, icon="user", icon_size=12)
        UITheme.draw_button(
            surface, r_btn, "RACES & RESULTS", self.font_badge, is_active=is_r, icon="flag", icon_size=12
        )

        # Main Table Area
        main_box = pygame.Rect(24, 178, self.width - 48, self.height - 198)
        UITheme.draw_panel(surface, main_box)

        if is_c:
            self._render_archive_constructors_table(surface, gm, main_box, sel_season_num)
        elif is_d:
            self._render_archive_drivers_table(surface, gm, main_box, sel_season_num)
        elif is_r:
            self._render_archive_races_table(surface, gm, main_box, sel_season_num)

    def _render_archive_constructors_table(
        self, surface: pygame.Surface, gm: GameManager, box: pygame.Rect, season_num: int
    ):
        teams = gm.db.get_historical_constructor_standings(season_num, self.selected_tier)

        th = pygame.Rect(box.x + 8, box.y + 8, box.width - 16, 24)
        pygame.draw.rect(surface, (14, 18, 24), th)
        surface.blit(self.font_badge.render("POS", True, UITheme.TEXT_MUTED), (th.x + 12, th.y + 5))
        surface.blit(
            self.font_badge.render("CONSTRUCTOR (CLICK FOR OVERVIEW)", True, UITheme.TEXT_MUTED), (th.x + 80, th.y + 5)
        )
        surface.blit(self.font_badge.render("ENGINE SUPPLIER", True, UITheme.TEXT_MUTED), (th.x + 420, th.y + 5))
        surface.blit(self.font_badge.render("REPUTATION", True, UITheme.TEXT_MUTED), (th.x + 650, th.y + 5))
        surface.blit(
            self.font_badge.render("CHAMPIONSHIP POINTS", True, UITheme.TEXT_MUTED), (th.x + box.width - 210, th.y + 5)
        )

        if not teams:
            surface.blit(
                self.font_body.render("No constructor records found for this season & tier.", True, UITheme.TEXT_MUTED),
                (box.x + 20, box.y + 45),
            )
            return

        leader_pts = teams[0].get("points", 0) if teams else 0
        for idx, t in enumerate(teams):
            row_y = box.y + 36 + idx * 30
            if row_y + 28 > box.y + box.height:
                break
            r_box = pygame.Rect(box.x + 8, row_y, box.width - 16, 28)
            is_ply = bool(t.get("is_player"))

            bg = (28, 44, 58) if is_ply else ((20, 26, 34) if idx % 2 == 0 else (16, 20, 26))
            pygame.draw.rect(surface, bg, r_box, border_radius=2)
            if is_ply:
                pygame.draw.rect(surface, UITheme.ACCENT_CYAN, r_box, width=1, border_radius=2)

            pos = t.get("championship_position", idx + 1)
            pos_col = (255, 215, 0) if pos == 1 else ((0, 240, 140) if pos <= 3 else UITheme.TEXT_WHITE)
            surface.blit(self.font_btn.render(f"P{pos}", True, pos_col), (r_box.x + 12, r_box.y + 5))

            col_hex = t.get("color_hex", "#00d2be")
            pygame.draw.rect(surface, pygame.Color(col_hex), (r_box.x + 60, r_box.y + 6, 6, 16), border_radius=1)

            t_name = f"{t.get('name', 'Constructor')} {'[YOU]' if is_ply else ''}"
            surface.blit(
                self.font_btn.render(t_name, True, (255, 215, 0) if is_ply else UITheme.TEXT_WHITE),
                (r_box.x + 80, r_box.y + 5),
            )

            surface.blit(
                self.font_body.render(t.get("engine_supplier", "Standard"), True, UITheme.TEXT_MUTED),
                (r_box.x + 420, r_box.y + 6),
            )
            surface.blit(
                self.font_body.render(f"{t.get('reputation', 50)} / 100", True, UITheme.TEXT_MUTED),
                (r_box.x + 650, r_box.y + 6),
            )

            pts = t.get("points", 0)
            pts_str = f"{pts} PTS"
            if pos > 1 and leader_pts > 0:
                pts_str += f"  (-{leader_pts - pts})"
            surface.blit(self.font_btn.render(pts_str, True, (0, 220, 255)), (r_box.x + box.width - 210, r_box.y + 5))

    def _render_archive_drivers_table(
        self, surface: pygame.Surface, gm: GameManager, box: pygame.Rect, season_num: int
    ):
        drivers = gm.db.get_historical_driver_standings(season_num, self.selected_tier)

        th = pygame.Rect(box.x + 8, box.y + 8, box.width - 16, 24)
        pygame.draw.rect(surface, (14, 18, 24), th)
        surface.blit(self.font_badge.render("POS", True, UITheme.TEXT_MUTED), (th.x + 12, th.y + 5))
        surface.blit(
            self.font_badge.render("DRIVER (CLICK FOR DOSSIER)", True, UITheme.TEXT_MUTED), (th.x + 80, th.y + 5)
        )
        surface.blit(
            self.font_badge.render("CONSTRUCTOR (CLICK FOR OVERVIEW)", True, UITheme.TEXT_MUTED), (th.x + 360, th.y + 5)
        )
        surface.blit(self.font_badge.render("STARTS", True, UITheme.TEXT_MUTED), (th.x + 620, th.y + 5))
        surface.blit(self.font_badge.render("WINS", True, UITheme.TEXT_MUTED), (th.x + 720, th.y + 5))
        surface.blit(self.font_badge.render("PODIUMS", True, UITheme.TEXT_MUTED), (th.x + 820, th.y + 5))
        surface.blit(self.font_badge.render("POINTS", True, UITheme.TEXT_MUTED), (th.x + box.width - 180, th.y + 5))

        if not drivers:
            surface.blit(
                self.font_body.render("No driver records found for this season & tier.", True, UITheme.TEXT_MUTED),
                (box.x + 20, box.y + 45),
            )
            return

        for idx, d in enumerate(drivers[:18]):
            row_y = box.y + 36 + idx * 28
            if row_y + 26 > box.y + box.height:
                break
            r_box = pygame.Rect(box.x + 8, row_y, box.width - 16, 26)
            is_ply = bool(d.get("is_player_driver"))
            is_acad = bool(d.get("is_academy_driver"))

            bg = (28, 46, 60) if (is_ply or is_acad) else ((20, 26, 34) if idx % 2 == 0 else (16, 20, 26))
            pygame.draw.rect(surface, bg, r_box, border_radius=2)
            if is_ply:
                pygame.draw.rect(surface, UITheme.ACCENT_CYAN, r_box, width=1, border_radius=2)
            elif is_acad:
                pygame.draw.rect(surface, (0, 240, 140), r_box, width=1, border_radius=2)

            pos = d.get("championship_position", idx + 1)
            pos_col = (255, 215, 0) if pos == 1 else ((0, 240, 140) if pos <= 3 else UITheme.TEXT_WHITE)
            surface.blit(self.font_badge.render(f"P{pos}", True, pos_col), (r_box.x + 12, r_box.y + 5))

            tag = " [YOU]" if is_ply else (" [ACADEMY]" if is_acad else "")
            d_name = f"{d.get('driver_name', d.get('name', 'Driver'))}{tag}"
            d_col = (255, 215, 0) if is_ply else ((0, 240, 140) if is_acad else UITheme.TEXT_WHITE)
            surface.blit(self.font_body_bold.render(d_name, True, d_col), (r_box.x + 80, r_box.y + 5))

            t_name = d.get("team_name", "Constructor")
            surface.blit(self.font_body.render(t_name, True, (0, 220, 255)), (r_box.x + 360, r_box.y + 5))

            starts = d.get("race_starts", 0)
            wins = d.get("wins", 0)
            pods = d.get("podiums", 0)
            surface.blit(self.font_body.render(str(starts), True, UITheme.TEXT_MUTED), (r_box.x + 630, r_box.y + 5))
            surface.blit(
                self.font_body.render(str(wins), True, (255, 215, 0) if wins > 0 else UITheme.TEXT_MUTED),
                (r_box.x + 730, r_box.y + 5),
            )
            surface.blit(
                self.font_body.render(str(pods), True, (0, 240, 140) if pods > 0 else UITheme.TEXT_MUTED),
                (r_box.x + 835, r_box.y + 5),
            )

            pts = d.get("points", 0)
            surface.blit(
                self.font_btn.render(f"{pts} PTS", True, (0, 220, 255)), (r_box.x + box.width - 180, r_box.y + 4)
            )

    def _render_archive_races_table(self, surface: pygame.Surface, gm: GameManager, box: pygame.Rect, season_num: int):
        races = gm.db.get_historical_season_races(season_num, self.selected_tier)

        th = pygame.Rect(box.x + 8, box.y + 8, box.width - 16, 24)
        pygame.draw.rect(surface, (14, 18, 24), th)
        surface.blit(self.font_badge.render("ROUND", True, UITheme.TEXT_MUTED), (th.x + 12, th.y + 5))
        surface.blit(self.font_badge.render("GRAND PRIX CIRCUIT", True, UITheme.TEXT_MUTED), (th.x + 90, th.y + 5))
        surface.blit(self.font_badge.render("RACE WINNER", True, UITheme.TEXT_MUTED), (th.x + 420, th.y + 5))
        surface.blit(self.font_badge.render("WINNING CONSTRUCTOR", True, UITheme.TEXT_MUTED), (th.x + 680, th.y + 5))
        surface.blit(
            self.font_badge.render("CLASSIFICATION", True, UITheme.TEXT_MUTED), (th.x + box.width - 220, th.y + 5)
        )

        if not races:
            surface.blit(
                self.font_body.render("No race weekend logs found for this season & tier.", True, UITheme.TEXT_MUTED),
                (box.x + 20, box.y + 45),
            )
            return

        for idx, r in enumerate(races):
            row_y = box.y + 36 + idx * 30
            if row_y + 28 > box.y + box.height:
                break
            r_box = pygame.Rect(box.x + 8, row_y, box.width - 16, 28)
            pygame.draw.rect(surface, (20, 26, 34) if idx % 2 == 0 else (16, 20, 26), r_box, border_radius=2)

            r_num = r.get("round_num", idx + 1)
            surface.blit(self.font_btn.render(f"R{r_num}", True, UITheme.ACCENT_CYAN), (r_box.x + 12, r_box.y + 5))
            surface.blit(
                self.font_body_bold.render(r.get("track_name", "Circuit"), True, UITheme.TEXT_WHITE),
                (r_box.x + 90, r_box.y + 6),
            )

            w_drv = r.get("winner_driver")
            w_team = r.get("winner_team")
            if w_drv:
                UITheme.draw_icon(surface, "trophy", (r_box.x + 420, r_box.y + 6), color=(255, 215, 0), size=14)
                surface.blit(self.font_btn.render(f"{w_drv}", True, (255, 215, 0)), (r_box.x + 438, r_box.y + 5))
                surface.blit(
                    self.font_body.render(w_team or "", True, UITheme.TEXT_MUTED), (r_box.x + 680, r_box.y + 6)
                )

                btn_view = pygame.Rect(self.width - 240, row_y + 3, 100, 22)
                UITheme.draw_button(surface, btn_view, "RESULTS", self.font_badge, icon="search", icon_size=12)
            else:
                surface.blit(
                    self.font_body.render("Upcoming Event / In Progress", True, UITheme.TEXT_MUTED),
                    (r_box.x + 420, r_box.y + 6),
                )

    def _render_drivers(self, surface: pygame.Surface, gm: GameManager):
        # 1. Back button if jumped from another view
        if self.previous_subtab or self.return_hub_tab:
            back_btn = pygame.Rect(self.width - 120, 108, 96, 24)
            UITheme.draw_button(surface, back_btn, "BACK", self.font_badge, icon="fast-forward", icon_size=12)

        # 2. Filter Bar (y = 108)
        filters = [
            ("ALUMNI", "★ ALUMNI"),
            ("ALL", "ALL DRIVERS"),
            ("T1", "TIER 1 (WSF)"),
            ("T2", "TIER 2 (CC)"),
            ("T3", "TIER 3 (NOC)"),
            ("T4_5", "FEEDERS"),
            ("FREE_AGENT", "FREE AGENTS"),
        ]
        fx = 24
        for f_key, f_lbl in filters:
            btn_w = 120 if f_key == "ALUMNI" else 96
            f_rect = pygame.Rect(fx, 108, btn_w, 24)
            is_sel = self.driver_filter == f_key
            icon = "award" if f_key == "ALUMNI" else None
            UITheme.draw_button(surface, f_rect, f_lbl, self.font_badge, is_active=is_sel, icon=icon, icon_size=12)
            fx += btn_w + 6

        # 3. Driver List (Left Panel)
        drivers = self._get_filtered_drivers(gm)
        list_box = pygame.Rect(24, 144, 360, self.height - 165)
        UITheme.draw_panel(surface, list_box)

        total_driver_h = len(drivers) * 46
        visible_driver_h = max(1, list_box.height - 36)
        max_driver_scroll = max(0, total_driver_h - visible_driver_h)
        self.driver_list_scroll = max(0, min(self.driver_list_scroll, max_driver_scroll))

        l_hdr = pygame.Rect(list_box.x, list_box.y, list_box.width, 28)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, l_hdr, border_top_left_radius=4, border_top_right_radius=4)
        cnt_lbl = self.font_badge.render(f"DRIVERS DIRECTORY ({len(drivers)})", True, UITheme.TEXT_MUTED)
        surface.blit(cnt_lbl, (l_hdr.x + 10, l_hdr.y + 7))

        if not drivers:
            surface.blit(
                self.font_body.render("No drivers found matching this filter.", True, UITheme.TEXT_MUTED),
                (list_box.x + 16, list_box.y + 40),
            )
        else:
            if self.selected_driver_id is None and drivers:
                self.selected_driver_id = drivers[0]["id"]

            for idx, d in enumerate(drivers):
                row_y = list_box.y + 32 + idx * 46 - self.driver_list_scroll
                if row_y < list_box.y + 30 or row_y + 42 > list_box.y + list_box.height:
                    continue
                r_box = pygame.Rect(list_box.x + 6, row_y, list_box.width - (16 if max_driver_scroll > 0 else 12), 42)
                is_sel = d["id"] == self.selected_driver_id
                is_alumni = bool(d.get("alumni_id"))

                bg = (32, 50, 68) if is_sel else ((22, 28, 38) if idx % 2 == 0 else (17, 22, 30))
                pygame.draw.rect(surface, bg, r_box, border_radius=3)
                if is_sel:
                    pygame.draw.rect(surface, UITheme.ACCENT_CYAN, r_box, width=1, border_radius=3)
                elif is_alumni:
                    pygame.draw.rect(surface, (255, 215, 0), r_box, width=1, border_radius=3)

                surface.blit(
                    self.font_btn.render(d["name"], True, (255, 215, 0) if is_alumni else UITheme.TEXT_WHITE),
                    (r_box.x + 10, r_box.y + 4),
                )

                t_tier = d.get("team_tier")
                t_name = d.get("team_name") or "Free Agent"
                tier_str = f"Tier {t_tier}" if t_tier else "Free Agent"
                surface.blit(
                    self.font_body.render(f"{t_name} ({tier_str})", True, UITheme.TEXT_MUTED),
                    (r_box.x + 10, r_box.y + 22),
                )

                if is_alumni:
                    alumni_badge = pygame.Rect(r_box.x + r_box.width - 86, r_box.y + 11, 80, 20)
                    pygame.draw.rect(surface, (50, 42, 10), alumni_badge, border_radius=2)
                    pygame.draw.rect(surface, (255, 215, 0), alumni_badge, width=1, border_radius=2)
                    UITheme.draw_icon(
                        surface, "award", (alumni_badge.x + 6, alumni_badge.y + 4), color=(255, 215, 0), size=12
                    )
                    surface.blit(
                        self.font_badge.render("ALUMNI", True, (255, 215, 0)),
                        (alumni_badge.x + 22, alumni_badge.y + 3),
                    )
                else:
                    pts = d.get("points", 0)
                    surface.blit(
                        self.font_btn.render(f"{pts} PTS", True, (0, 220, 255)),
                        (r_box.x + r_box.width - 65, r_box.y + 12),
                    )

            if max_driver_scroll > 0:
                sb_track = pygame.Rect(list_box.x + list_box.width - 6, list_box.y + 32, 4, list_box.height - 36)
                pygame.draw.rect(surface, (18, 24, 32), sb_track, border_radius=2)
                thumb_ratio = visible_driver_h / (total_driver_h + visible_driver_h)
                thumb_h = max(20, int(sb_track.height * thumb_ratio))
                scroll_frac = self.driver_list_scroll / max_driver_scroll
                thumb_y = sb_track.y + int((sb_track.height - thumb_h) * scroll_frac)
                pygame.draw.rect(
                    surface, (60, 80, 105), pygame.Rect(sb_track.x, thumb_y, sb_track.width, thumb_h), border_radius=2
                )

        # 4. Selected Driver Dossier (Right Panel)
        detail_box = pygame.Rect(400, 144, self.width - 424, self.height - 165)
        UITheme.draw_panel(surface, detail_box)

        if self.selected_driver_id:
            profile = gm.db.get_driver_profile(self.selected_driver_id)
            if profile:
                self._render_driver_dossier_content(surface, gm, detail_box, profile)
        else:
            surface.blit(
                self.font_body.render(
                    "Select a driver from the left directory to view full career dossier.", True, UITheme.TEXT_MUTED
                ),
                (detail_box.x + 24, detail_box.y + 40),
            )

    def _render_driver_dossier_content(
        self, surface: pygame.Surface, gm: GameManager, box: pygame.Rect, p: Dict[str, Any]
    ):
        hdr_rect = pygame.Rect(box.x, box.y, box.width, 50)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, hdr_rect, border_top_left_radius=4, border_top_right_radius=4)

        num = p.get("number", 7)
        surface.blit(self.font_huge.render(f"#{num}", True, (255, 215, 0)), (hdr_rect.x + 14, hdr_rect.y + 12))

        d_name = p.get("name", "Driver")
        surface.blit(
            self.font_header.render(d_name.upper(), True, UITheme.TEXT_WHITE), (hdr_rect.x + 60, hdr_rect.y + 8)
        )

        t_name = p.get("team_name", "Free Agent")
        t_tier = p.get("team_tier")
        tier_lbl = f"TIER {t_tier}" if t_tier else "FREE AGENT"
        team_id = p.get("team_id")
        if not team_id and t_name and t_name not in ("Free Agent", "Youth Academy Prospect", "Youth Prospect"):
            t_obj = gm.db.get_team_by_name(t_name)
            if t_obj:
                team_id = t_obj["id"]
                if not t_tier:
                    t_tier = t_obj.get("tier", 1)
                    tier_lbl = f"TIER {t_tier}"

        if team_id:
            team_btn_rect = pygame.Rect(hdr_rect.x + 60, hdr_rect.y + 25, 230, 20)
            UITheme.draw_button(
                surface, team_btn_rect, f"{t_name.upper()} ({tier_lbl})", self.font_badge, icon="wrench", icon_size=12
            )

            meta_str = f"Age: {p.get('age', 25)}  |  Morale: {p.get('morale', 80):.0f}%"
            surface.blit(
                self.font_body.render(meta_str, True, UITheme.TEXT_MUTED),
                (team_btn_rect.x + team_btn_rect.width + 12, hdr_rect.y + 28),
            )
        else:
            team_str = f"{t_name} ({tier_lbl})  |  Age: {p.get('age', 25)}  |  Morale: {p.get('morale', 80):.0f}%"
            UITheme.draw_icon(surface, "user", (hdr_rect.x + 60, hdr_rect.y + 28), color=UITheme.TEXT_MUTED, size=13)
            surface.blit(self.font_body.render(team_str, True, UITheme.TEXT_MUTED), (hdr_rect.x + 78, hdr_rect.y + 28))

        cur_y = box.y + 58
        is_alumni = p.get("is_team_alumni", False)
        if is_alumni:
            alumni = p.get("alumni_data", {})
            a_banner = pygame.Rect(box.x + 12, cur_y, box.width - 24, 38)
            pygame.draw.rect(surface, (36, 32, 12), a_banner, border_radius=3)
            pygame.draw.rect(surface, (255, 215, 0), a_banner, width=1, border_radius=3)

            UITheme.draw_icon(surface, "award", (a_banner.x + 10, a_banner.y + 4), color=(255, 215, 0), size=14)
            surface.blit(
                self.font_body_bold.render("OFFICIAL TEAM ALUMNI", True, (255, 215, 0)),
                (a_banner.x + 28, a_banner.y + 4),
            )

            dep_str = {
                "RELEASED": "Departed via Buyout",
                "REPLACED": "Displaced by New Signing",
                "PROMOTED_TIER2": "Earned Promotion to Tier 2",
                "CONTRACT_EXPIRY": "Contract Expired",
            }.get(alumni.get("departure_reason"), "Ex-Driver")

            a_info = f"Tenure: {alumni.get('seasons_active', 'Past Season')}  |  {alumni.get('starts_with_team', 0)} Starts, {alumni.get('wins_with_team', 0)} Wins, {alumni.get('podiums_with_team', 0)} Podiums  |  Departure: {dep_str}"
            surface.blit(self.font_body.render(a_info, True, UITheme.TEXT_WHITE), (a_banner.x + 10, a_banner.y + 20))
            cur_y += 46

        # Career Grand Totals Grid
        totals = p.get("career_totals", {})
        stat_cards = [
            ("CAREER STARTS", str(totals.get("starts", 0)), "flag"),
            ("GRAND PRIX WINS", str(totals.get("wins", 0)), "trophy"),
            ("PODIUM FINISHES", str(totals.get("podiums", 0)), "medal"),
            ("TOTAL POINTS", str(totals.get("points", 0)), "circle-dollar-sign"),
            ("CHAMPIONSHIPS", str(totals.get("titles", 0)), "award"),
            ("BEST FINISH", totals.get("best_finish", "P1"), "award"),
        ]
        cols = 3 if box.width < 700 else 6
        card_w = (box.width - 24 - (cols - 1) * 4) // cols
        for idx, (stat_title, stat_val, stat_icon) in enumerate(stat_cards):
            row = idx // cols
            col = idx % cols
            c_rect = pygame.Rect(box.x + 12 + col * (card_w + 4), cur_y + row * 46, card_w, 42)
            pygame.draw.rect(surface, (18, 24, 32), c_rect, border_radius=2)
            pygame.draw.rect(surface, UITheme.PANEL_BORDER, c_rect, width=1, border_radius=2)

            val_col = (
                (255, 215, 0)
                if "WIN" in stat_title or "CHAMPION" in stat_title
                else ((0, 220, 255) if "POINTS" in stat_title else UITheme.TEXT_WHITE)
            )
            UITheme.draw_icon(surface, stat_icon, (c_rect.x + 6, c_rect.y + 4), color=val_col, size=11)
            t_surf = self.font_badge.render(stat_title, True, UITheme.TEXT_MUTED)
            surface.blit(t_surf, (c_rect.x + 20, c_rect.y + 4))

            v_surf = self.font_stat.render(stat_val, True, val_col)
            surface.blit(v_surf, (c_rect.x + (card_w - v_surf.get_width()) // 2, c_rect.y + 19))

        cur_y += 48 if cols == 6 else 96

        # AI Career Report & Driver Talent Radar Spider Chart
        ai_data = p.get("ai_analysis", {})
        radar_w = 210
        ai_box_w = box.width - 24 - radar_w - 12
        ai_box = pygame.Rect(box.x + 12, cur_y, ai_box_w, 88)
        pygame.draw.rect(surface, (16, 26, 36), ai_box, border_radius=3)
        pygame.draw.rect(surface, (0, 180, 220), ai_box, width=1, border_radius=3)

        arc_label = ai_data.get("trajectory_arc", "MIDFIELD STALWART")
        UITheme.draw_icon(surface, "brain", (ai_box.x + 10, ai_box.y + 5), color=(0, 220, 255), size=16)
        surface.blit(
            self.font_btn.render(f"AI PERFORMANCE REPORT  [{arc_label}]", True, (0, 220, 255)),
            (ai_box.x + 32, ai_box.y + 5),
        )
        surface.blit(
            self.font_body.render(ai_data.get("scout_assessment", ""), True, UITheme.TEXT_WHITE),
            (ai_box.x + 10, ai_box.y + 26),
        )

        alumni_note = ai_data.get("alumni_insight", "")
        if alumni_note:
            surface.blit(
                self.font_body.render(alumni_note, True, (255, 215, 0) if is_alumni else UITheme.TEXT_MUTED),
                (ai_box.x + 10, ai_box.y + 46),
            )

        # Driver Talent Radar Spider Chart
        radar_rect = pygame.Rect(box.x + 12 + ai_box_w + 12, cur_y, radar_w, 88)
        pygame.draw.rect(surface, (16, 22, 30), radar_rect, border_radius=3)
        pygame.draw.rect(surface, UITheme.PANEL_BORDER, radar_rect, width=1, border_radius=3)

        radar_attrs = ["Pace", "Brake", "Defend", "Consist", "Tires", "Wet"]
        radar_vals = [
            float(p.get("pace", 65)),
            float(p.get("braking", 65)),
            float(p.get("defending", 65)),
            float(p.get("consistency", 65)),
            float(p.get("tire_management", 65)),
            float(p.get("wet_weather", 65)),
        ]
        rc_x = radar_rect.x + radar_rect.width // 2
        rc_y = radar_rect.y + radar_rect.height // 2 - 8
        UITheme.draw_radar_chart(
            surface,
            center=(rc_x, rc_y),
            radius=26,
            attributes=radar_attrs,
            values_1=radar_vals,
            label_1=p.get("name", "Driver")[:10],
            color_1=(0, 220, 240),
            show_labels=True,
        )

        cur_y += 96

        # Season-by-Season Career History Table
        surface.blit(self.font_btn.render("HISTORICAL SEASON BREAKDOWN", True, UITheme.TEXT_WHITE), (box.x + 12, cur_y))
        cur_y += 18

        sh_rect = pygame.Rect(box.x + 12, cur_y, box.width - 24, 20)
        pygame.draw.rect(surface, (14, 18, 24), sh_rect)
        surface.blit(self.font_badge.render("YEAR / SEASON", True, UITheme.TEXT_MUTED), (sh_rect.x + 8, sh_rect.y + 3))
        surface.blit(self.font_badge.render("TIER", True, UITheme.TEXT_MUTED), (sh_rect.x + 130, sh_rect.y + 3))
        surface.blit(self.font_badge.render("CONSTRUCTOR", True, (0, 220, 255)), (sh_rect.x + 220, sh_rect.y + 3))
        surface.blit(self.font_badge.render("FINAL POS", True, UITheme.TEXT_MUTED), (sh_rect.x + 420, sh_rect.y + 3))
        surface.blit(self.font_badge.render("STARTS", True, UITheme.TEXT_MUTED), (sh_rect.x + 510, sh_rect.y + 3))
        surface.blit(self.font_badge.render("WINS", True, UITheme.TEXT_MUTED), (sh_rect.x + 590, sh_rect.y + 3))
        surface.blit(self.font_badge.render("PODIUMS", True, UITheme.TEXT_MUTED), (sh_rect.x + 660, sh_rect.y + 3))
        surface.blit(
            self.font_badge.render("POINTS", True, UITheme.TEXT_MUTED), (sh_rect.x + box.width - 110, sh_rect.y + 3)
        )

        seasons_hist = p.get("season_history", [])
        if not seasons_hist:
            surface.blit(
                self.font_body.render("No historical season records on file.", True, UITheme.TEXT_MUTED),
                (box.x + 20, cur_y + 26),
            )
        else:
            for s_idx, sh in enumerate(seasons_hist):
                row_y = cur_y + 24 + s_idx * 24
                if row_y + 22 > box.y + box.height:
                    break
                row_box = pygame.Rect(box.x + 12, row_y, box.width - 24, 22)
                pygame.draw.rect(surface, (20, 26, 34) if s_idx % 2 == 0 else (16, 20, 26), row_box, border_radius=2)

                s_num = sh.get("season_num", 1)
                s_yr = 2025 + s_num
                surface.blit(
                    self.font_body_bold.render(f"Season {s_num} ({s_yr})", True, UITheme.TEXT_WHITE),
                    (row_box.x + 8, row_box.y + 3),
                )
                surface.blit(
                    self.font_body.render(f"Tier {sh.get('tier', 3)}", True, UITheme.TEXT_MUTED),
                    (row_box.x + 130, row_box.y + 3),
                )

                sh_team = sh.get("team_name", "Constructor")
                sh_team_id = sh.get("team_id")
                can_click_team = bool(sh_team_id or (sh_team and sh_team not in ("Free Agent", "None")))
                if can_click_team:
                    UITheme.draw_icon(surface, "wrench", (row_box.x + 220, row_box.y + 4), color=(0, 220, 255), size=12)
                    t_surf = self.font_body_bold.render(f"{sh_team}", True, (0, 220, 255))
                    surface.blit(t_surf, (row_box.x + 236, row_box.y + 3))
                else:
                    t_surf = self.font_body.render(sh_team, True, UITheme.TEXT_WHITE)
                    surface.blit(t_surf, (row_box.x + 220, row_box.y + 3))

                pos = sh.get("championship_position", 10)
                pos_col = (255, 215, 0) if pos == 1 else ((0, 240, 140) if pos <= 3 else UITheme.TEXT_WHITE)
                surface.blit(self.font_badge.render(f"P{pos}", True, pos_col), (row_box.x + 420, row_box.y + 4))

                surface.blit(
                    self.font_body.render(str(sh.get("race_starts", 0)), True, UITheme.TEXT_MUTED),
                    (row_box.x + 510, row_box.y + 3),
                )
                surface.blit(
                    self.font_body.render(
                        str(sh.get("wins", 0)), True, (255, 215, 0) if sh.get("wins", 0) > 0 else UITheme.TEXT_MUTED
                    ),
                    (row_box.x + 590, row_box.y + 3),
                )
                surface.blit(
                    self.font_body.render(
                        str(sh.get("podiums", 0)),
                        True,
                        (0, 240, 140) if sh.get("podiums", 0) > 0 else UITheme.TEXT_MUTED,
                    ),
                    (row_box.x + 660, row_box.y + 3),
                )
                surface.blit(
                    self.font_body_bold.render(f"{sh.get('points', 0)} PTS", True, (0, 220, 255)),
                    (row_box.x + box.width - 110, row_box.y + 3),
                )

    def _render_constructors(self, surface: pygame.Surface, gm: GameManager):
        # 1. Back button if jumped from another view
        if self.previous_subtab:
            back_btn = pygame.Rect(self.width - 120, 108, 96, 24)
            UITheme.draw_button(surface, back_btn, "BACK", self.font_badge, icon="fast-forward", icon_size=12)

        # 2. Tier Buttons (1 to 5)
        tier_names = {
            1: "TIER 1 (WSF)",
            2: "TIER 2 (CONTINENTAL)",
            3: "TIER 3 (NATIONAL)",
            4: "TIER 4 (JUNIOR)",
            5: "TIER 5 (KARTING)",
        }
        for t in range(1, 6):
            t_btn = pygame.Rect(24 + (t - 1) * 125, 108, 118, 26)
            is_sel = t == self.team_selected_tier
            pygame.draw.rect(surface, (34, 52, 70) if is_sel else (18, 24, 32), t_btn, border_radius=2)
            pygame.draw.rect(
                surface, UITheme.ACCENT_CYAN if is_sel else UITheme.PANEL_BORDER, t_btn, width=1, border_radius=2
            )
            t_lbl = self.font_badge.render(tier_names[t], True, UITheme.TEXT_WHITE if is_sel else UITheme.TEXT_MUTED)
            surface.blit(t_lbl, (t_btn.x + (t_btn.width - t_lbl.get_width()) // 2, t_btn.y + 6))

        # 3. Left Panel: Constructor Directory List
        teams = gm.db.get_teams(tier=self.team_selected_tier)
        list_box = pygame.Rect(24, 144, 330, self.height - 165)
        UITheme.draw_panel(surface, list_box)

        total_team_h = len(teams) * 48
        visible_team_h = max(1, list_box.height - 36)
        max_team_scroll = max(0, total_team_h - visible_team_h)
        self.team_list_scroll = max(0, min(self.team_list_scroll, max_team_scroll))

        l_hdr = pygame.Rect(list_box.x, list_box.y, list_box.width, 28)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, l_hdr, border_top_left_radius=4, border_top_right_radius=4)
        cnt_lbl = self.font_badge.render(f"CONSTRUCTORS ({len(teams)})", True, UITheme.TEXT_MUTED)
        surface.blit(cnt_lbl, (l_hdr.x + 10, l_hdr.y + 7))

        if not teams:
            surface.blit(
                self.font_body.render("No teams found in this tier.", True, UITheme.TEXT_MUTED),
                (list_box.x + 14, list_box.y + 40),
            )
        else:
            if self.selected_team_id is None:
                self.selected_team_id = teams[0]["id"]

            for idx, t in enumerate(teams):
                row_y = list_box.y + 32 + idx * 48 - self.team_list_scroll
                if row_y < list_box.y + 30 or row_y + 44 > list_box.y + list_box.height:
                    continue
                r_box = pygame.Rect(list_box.x + 6, row_y, list_box.width - (16 if max_team_scroll > 0 else 12), 44)
                is_sel = t["id"] == self.selected_team_id
                is_ply = bool(t.get("is_player"))

                bg = (32, 50, 68) if is_sel else ((22, 28, 38) if idx % 2 == 0 else (17, 22, 30))
                pygame.draw.rect(surface, bg, r_box, border_radius=3)
                if is_sel:
                    pygame.draw.rect(surface, UITheme.ACCENT_CYAN, r_box, width=1, border_radius=3)
                elif is_ply:
                    pygame.draw.rect(surface, (255, 215, 0), r_box, width=1, border_radius=3)

                col_hex = t.get("color_hex", "#00d2be")
                pygame.draw.rect(surface, pygame.Color(col_hex), (r_box.x + 8, r_box.y + 10, 6, 24), border_radius=1)

                t_name = f"{t.get('name', 'Constructor')} {'[YOU]' if is_ply else ''}"
                surface.blit(
                    self.font_btn.render(t_name, True, (255, 215, 0) if is_ply else UITheme.TEXT_WHITE),
                    (r_box.x + 20, r_box.y + 4),
                )

                eng = t.get("engine_supplier", "Standard")
                surface.blit(
                    self.font_body.render(f"{eng}  |  Rep: {t.get('reputation', 50)}", True, UITheme.TEXT_MUTED),
                    (r_box.x + 20, r_box.y + 24),
                )

                pts = t.get("points", 0)
                surface.blit(
                    self.font_btn.render(f"{pts} PTS", True, (0, 220, 255)), (r_box.x + r_box.width - 65, r_box.y + 12)
                )

            if max_team_scroll > 0:
                sb_track = pygame.Rect(list_box.x + list_box.width - 6, list_box.y + 32, 4, list_box.height - 36)
                pygame.draw.rect(surface, (18, 24, 32), sb_track, border_radius=2)
                thumb_ratio = visible_team_h / (total_team_h + visible_team_h)
                thumb_h = max(20, int(sb_track.height * thumb_ratio))
                scroll_frac = self.team_list_scroll / max_team_scroll
                thumb_y = sb_track.y + int((sb_track.height - thumb_h) * scroll_frac)
                pygame.draw.rect(
                    surface, (60, 80, 105), pygame.Rect(sb_track.x, thumb_y, sb_track.width, thumb_h), border_radius=2
                )

        # 4. Right Panel: Selected Constructor Dossier
        detail_box = pygame.Rect(370, 144, self.width - 394, self.height - 165)
        UITheme.draw_panel(surface, detail_box)

        if self.selected_team_id:
            team_prof = gm.db.get_team_profile(self.selected_team_id)
            if team_prof:
                self._render_constructor_dossier_content(surface, gm, detail_box, team_prof)
        else:
            surface.blit(
                self.font_body.render(
                    "Select a constructor from the left directory to view full overview.", True, UITheme.TEXT_MUTED
                ),
                (detail_box.x + 24, detail_box.y + 40),
            )

    def _render_constructor_dossier_content(
        self, surface: pygame.Surface, gm: GameManager, box: pygame.Rect, t: Dict[str, Any]
    ):
        # Header Box
        hdr_rect = pygame.Rect(box.x, box.y, box.width, 50)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, hdr_rect, border_top_left_radius=4, border_top_right_radius=4)

        col_hex = t.get("color_hex", "#00d2be")
        pygame.draw.rect(surface, pygame.Color(col_hex), (hdr_rect.x + 14, hdr_rect.y + 12, 10, 26), border_radius=2)

        t_name = t.get("name", "Constructor")
        is_ply = bool(t.get("is_player"))
        surface.blit(
            self.font_header.render(
                f"{t_name.upper()} {'[YOUR TEAM]' if is_ply else ''}",
                True,
                (255, 215, 0) if is_ply else UITheme.TEXT_WHITE,
            ),
            (hdr_rect.x + 32, hdr_rect.y + 8),
        )

        sub_info = f"Tier {t.get('tier', 3)}   |   Engine: {t.get('engine_supplier', 'Standard')}   |   Reputation: {t.get('reputation', 50)}/100   |   Budget: ${t.get('cash', 0):,.0f}"
        surface.blit(self.font_body.render(sub_info, True, UITheme.TEXT_MUTED), (hdr_rect.x + 32, hdr_rect.y + 28))

        cur_y = box.y + 58

        # Current Driver Lineup Cards (Car #1, Car #2)
        surface.blit(
            self.font_btn.render("CURRENT ACTIVE DRIVER LINEUP (CLICK DRIVER FOR DOSSIER)", True, UITheme.TEXT_WHITE),
            (box.x + 12, cur_y),
        )
        cur_y += 20

        drivers = t.get("drivers", [])
        card_w = (box.width - 34) // 2
        for d_idx in range(2):
            c_rect = pygame.Rect(box.x + 12 + d_idx * (card_w + 10), cur_y, card_w, 58)
            pygame.draw.rect(surface, (18, 24, 34), c_rect, border_radius=3)
            pygame.draw.rect(surface, UITheme.PANEL_BORDER, c_rect, width=1, border_radius=3)

            if d_idx < len(drivers):
                d = drivers[d_idx]
                surface.blit(
                    self.font_badge.render(f"CAR #{d_idx + 1}", True, UITheme.ACCENT_CYAN),
                    (c_rect.x + 10, c_rect.y + 6),
                )
                surface.blit(
                    self.font_btn.render(
                        f"#{d.get('number', 0)}  {d.get('name', 'Driver')}",
                        True,
                        (255, 215, 0) if d.get("is_player_driver") else UITheme.TEXT_WHITE,
                    ),
                    (c_rect.x + 10, c_rect.y + 20),
                )
                ds_x = c_rect.x + 10
                ds_y = c_rect.y + 38
                gap = 12
                ds_x += (
                    UITheme.draw_stat_item(
                        surface,
                        ds_x,
                        ds_y,
                        "zap",
                        f"Pace: {d.get('pace', 50)}",
                        self.font_body,
                        text_color=UITheme.TEXT_MUTED,
                        icon_color=(255, 215, 0),
                        icon_size=11,
                        gap=3,
                    )
                    + gap
                )
                ds_x += (
                    UITheme.draw_stat_item(
                        surface,
                        ds_x,
                        ds_y,
                        "user",
                        f"Age: {d.get('age', 25)}",
                        self.font_body,
                        text_color=UITheme.TEXT_MUTED,
                        icon_color=UITheme.TEXT_MUTED,
                        icon_size=11,
                        gap=3,
                    )
                    + gap
                )
                UITheme.draw_stat_item(
                    surface,
                    ds_x,
                    ds_y,
                    "trophy",
                    f"{d.get('points', 0)} PTS",
                    self.font_body,
                    text_color=UITheme.TEXT_MUTED,
                    icon_color=(0, 220, 255),
                    icon_size=11,
                    gap=3,
                )

                view_btn = pygame.Rect(c_rect.x + c_rect.width - 92, c_rect.y + 16, 84, 24)
                UITheme.draw_button(surface, view_btn, "DOSSIER", self.font_badge, icon="user", icon_size=12)
            else:
                surface.blit(
                    self.font_badge.render(f"CAR #{d_idx + 1} [SEAT VACANT]", True, UITheme.TEXT_MUTED),
                    (c_rect.x + 10, c_rect.y + 20),
                )

        cur_y += 68

        # Team Career Totals Cards
        stat_cards = [
            ("TOTAL RACES", str(t.get("total_starts", 0)), "flag"),
            ("RACE WINS", str(t.get("total_wins", 0)), "trophy"),
            ("PODIUM FINISHES", str(t.get("total_podiums", 0)), "medal"),
            ("LIFETIME POINTS", str(t.get("all_time_points", 0)), "circle-dollar-sign"),
            ("WORLD TITLES", str(t.get("tier1_titles", 0)), "award"),
        ]
        card_w5 = (box.width - 32) // 5
        for idx, (stat_title, stat_val, stat_icon) in enumerate(stat_cards):
            c_rect = pygame.Rect(box.x + 12 + idx * (card_w5 + 2), cur_y, card_w5, 42)
            pygame.draw.rect(surface, (18, 24, 32), c_rect, border_radius=2)
            pygame.draw.rect(surface, UITheme.PANEL_BORDER, c_rect, width=1, border_radius=2)

            val_col = (
                (255, 215, 0)
                if "WIN" in stat_title or "TITLE" in stat_title
                else ((0, 220, 255) if "POINTS" in stat_title else UITheme.TEXT_WHITE)
            )
            UITheme.draw_icon(surface, stat_icon, (c_rect.x + 6, c_rect.y + 4), color=val_col, size=11)
            t_surf = self.font_badge.render(stat_title, True, UITheme.TEXT_MUTED)
            surface.blit(t_surf, (c_rect.x + 20, c_rect.y + 4))

            v_surf = self.font_stat.render(stat_val, True, val_col)
            surface.blit(v_surf, (c_rect.x + (card_w5 - v_surf.get_width()) // 2, c_rect.y + 19))

        cur_y += 50

        # Season-by-Season History Table
        surface.blit(
            self.font_btn.render("HISTORICAL CHAMPIONSHIP RECORD", True, UITheme.TEXT_WHITE), (box.x + 12, cur_y)
        )
        cur_y += 18

        sh_rect = pygame.Rect(box.x + 12, cur_y, box.width - 24, 20)
        pygame.draw.rect(surface, (14, 18, 24), sh_rect)
        surface.blit(self.font_badge.render("SEASON / YEAR", True, UITheme.TEXT_MUTED), (sh_rect.x + 8, sh_rect.y + 3))
        surface.blit(self.font_badge.render("TIER", True, UITheme.TEXT_MUTED), (sh_rect.x + 160, sh_rect.y + 3))
        surface.blit(
            self.font_badge.render("CHAMPIONSHIP FINISH", True, UITheme.TEXT_MUTED), (sh_rect.x + 300, sh_rect.y + 3)
        )
        surface.blit(
            self.font_badge.render("TOTAL POINTS", True, UITheme.TEXT_MUTED),
            (sh_rect.x + box.width - 150, sh_rect.y + 3),
        )

        hist = t.get("season_history", [])
        if not hist:
            surface.blit(
                self.font_body.render("No completed season records on file for this team.", True, UITheme.TEXT_MUTED),
                (box.x + 20, cur_y + 26),
            )
        else:
            for s_idx, sh in enumerate(hist):
                row_y = cur_y + 24 + s_idx * 24
                if row_y + 22 > box.y + box.height:
                    break
                row_box = pygame.Rect(box.x + 12, row_y, box.width - 24, 22)
                pygame.draw.rect(surface, (20, 26, 34) if s_idx % 2 == 0 else (16, 20, 26), row_box, border_radius=2)

                s_num = sh.get("season_num", 1)
                s_yr = 2025 + s_num
                surface.blit(
                    self.font_body_bold.render(f"Season {s_num} ({s_yr})", True, UITheme.TEXT_WHITE),
                    (row_box.x + 8, row_box.y + 3),
                )
                surface.blit(
                    self.font_body.render(f"Tier {sh.get('tier', 3)}", True, UITheme.TEXT_MUTED),
                    (row_box.x + 160, row_box.y + 3),
                )

                pos = sh.get("championship_position", 10)
                pos_col = (255, 215, 0) if pos == 1 else ((0, 240, 140) if pos <= 3 else UITheme.TEXT_WHITE)
                surface.blit(self.font_badge.render(f"P{pos}", True, pos_col), (row_box.x + 300, row_box.y + 4))

                surface.blit(
                    self.font_body_bold.render(f"{sh.get('points_total', 0)} PTS", True, (0, 220, 255)),
                    (row_box.x + box.width - 150, row_box.y + 3),
                )

    def _render_hall_of_fame(self, surface: pygame.Surface, gm: GameManager):
        records = gm.db.get_all_time_records()

        box = pygame.Rect(24, 108, self.width - 48, self.height - 128)
        UITheme.draw_panel(surface, box)

        half_w = (box.width - 36) // 2
        half_h = (box.height - 36) // 2

        quadrants = [
            (
                "ALL-TIME DRIVERS' CHAMPIONSHIPS",
                "trophy",
                records.get("top_champions", []),
                "titles",
                "TITLES",
                box.x + 12,
                box.y + 12,
            ),
            (
                "ALL-TIME CONSTRUCTORS' TITLES",
                "award",
                records.get("top_constructors", []),
                "titles",
                "TITLES",
                box.x + 24 + half_w,
                box.y + 12,
            ),
            (
                "MOST GRAND PRIX WINS",
                "flag",
                records.get("top_wins_drivers", []),
                "total_wins",
                "WINS",
                box.x + 12,
                box.y + 24 + half_h,
            ),
            (
                "ALL-TIME CAREER POINTS",
                "zap",
                records.get("top_pts_drivers", []),
                "total_points",
                "POINTS",
                box.x + 24 + half_w,
                box.y + 24 + half_h,
            ),
        ]

        for q_title, q_icon, q_list, val_key, val_unit, qx, qy in quadrants:
            q_box = pygame.Rect(qx, qy, half_w, half_h)
            pygame.draw.rect(surface, (18, 24, 32), q_box, border_radius=3)
            pygame.draw.rect(surface, UITheme.PANEL_BORDER, q_box, width=1, border_radius=3)

            q_hdr = pygame.Rect(q_box.x, q_box.y, q_box.width, 28)
            pygame.draw.rect(surface, UITheme.PANEL_HEADER, q_hdr, border_top_left_radius=3, border_top_right_radius=3)
            UITheme.draw_icon(surface, q_icon, (q_hdr.x + 10, q_hdr.y + 6), color=(255, 215, 0), size=16)
            surface.blit(
                self.font_btn.render(f"{q_title} (CLICK TO VIEW)", True, (255, 215, 0)), (q_hdr.x + 32, q_hdr.y + 6)
            )

            if not q_list:
                surface.blit(
                    self.font_body.render("No historical record entries on file.", True, UITheme.TEXT_MUTED),
                    (q_box.x + 14, q_box.y + 40),
                )
            else:
                for idx, entry in enumerate(q_list[:5]):
                    ry = q_box.y + 34 + idx * 26
                    name = entry.get("driver_name", entry.get("name", "Driver / Team"))
                    val = entry.get(val_key, 0)
                    pos_col = (255, 215, 0) if idx == 0 else ((0, 240, 140) if idx <= 2 else UITheme.TEXT_WHITE)

                    surface.blit(self.font_badge.render(f"#{idx + 1}", True, pos_col), (q_box.x + 10, ry + 4))
                    surface.blit(self.font_body_bold.render(name, True, (0, 220, 255)), (q_box.x + 36, ry + 4))
                    surface.blit(
                        self.font_btn.render(f"{val} {val_unit}", True, (255, 215, 0)),
                        (q_box.x + q_box.width - 100, ry + 3),
                    )

    def _render_round_results_modal(self, surface: pygame.Surface):
        modal_w = 560
        modal_h = 440
        modal_x = (self.width - modal_w) // 2
        modal_y = (self.height - modal_h) // 2

        dim = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 160))
        surface.blit(dim, (0, 0))

        m_box = pygame.Rect(modal_x, modal_y, modal_w, modal_h)
        pygame.draw.rect(surface, (15, 20, 28), m_box, border_radius=6)
        pygame.draw.rect(surface, (0, 220, 255), m_box, width=2, border_radius=6)

        hdr = pygame.Rect(modal_x, modal_y, modal_w, 36)
        pygame.draw.rect(surface, (22, 30, 44), hdr, border_top_left_radius=6, border_top_right_radius=6)

        info = self.selected_round_results
        s_num = info.get("season_num", 1)
        title = f"S{s_num} TIER {info['tier']} R{info['round']}: {info['track_name'].upper()}"
        UITheme.draw_icon(surface, "flag", (modal_x + 12, modal_y + 10), color=(255, 215, 0), size=16)
        surface.blit(self.font_btn.render(title, True, (255, 215, 0)), (modal_x + 34, modal_y + 9))

        close_btn = pygame.Rect(modal_x + modal_w - 75, modal_y + 7, 65, 22)
        UITheme.draw_button(surface, close_btn, "CLOSE", self.font_badge, icon="x", icon_size=12)

        results = info.get("results", [])
        if not results:
            surface.blit(
                self.font_body.render("No classification records found for this race.", True, UITheme.TEXT_MUTED),
                (modal_x + 20, modal_y + 60),
            )
            return

        th = pygame.Rect(modal_x + 12, modal_y + 44, modal_w - 24, 20)
        pygame.draw.rect(surface, (12, 16, 22), th)
        surface.blit(self.font_badge.render("POS", True, UITheme.TEXT_MUTED), (th.x + 8, th.y + 3))
        surface.blit(self.font_badge.render("DRIVER (CLICK TO VIEW)", True, UITheme.TEXT_MUTED), (th.x + 50, th.y + 3))
        surface.blit(
            self.font_badge.render("CONSTRUCTOR (CLICK TO VIEW)", True, UITheme.TEXT_MUTED), (th.x + 250, th.y + 3)
        )
        surface.blit(self.font_badge.render("POINTS", True, UITheme.TEXT_MUTED), (th.x + 440, th.y + 3))

        for idx, r in enumerate(results[:12]):
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
            surface.blit(self.font_body_bold.render(d_name, True, d_col), (r_box.x + 50, r_box.y + 5))

            surface.blit(
                self.font_body.render(r.get("team_name", ""), True, (0, 220, 255)), (r_box.x + 250, r_box.y + 5)
            )

            pts = r.get("points", 0)
            pts_col = (0, 220, 255) if pts > 0 else UITheme.TEXT_MUTED
            surface.blit(
                self.font_badge.render(f"+{pts} PTS" if pts > 0 else "-", True, pts_col), (r_box.x + 440, r_box.y + 5)
            )
