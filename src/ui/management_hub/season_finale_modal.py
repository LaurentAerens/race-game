import pygame
from typing import Dict, List, Any, Optional, Callable
from ..theme import UITheme
from ...management.game_manager import GameManager
from ...management.league_simulator import LeagueSimulator
from ...management.engineering_manager import EngineeringManager

class SeasonFinaleModal:
    """
    Comprehensive End of Season & New Season Transition Modal.
    Guides the player through:
    1. Constructors' Championship Standings & Scaled Prize Money (Big HQ Upgrade tier scaling)
    2. Drivers' Championship Rating, Champion Spotlight & Champion Mood/Bonuses
    3. Promotion & Relegation Choice (Player P1 option to promote/decline, P10 Tier 3 protection, relegated titans)
    4. Next Season Engine Supplier Selection
    5. Season Kickoff Overview & Start Season Rollover
    """
    def __init__(self, screen_width: int, screen_height: int, on_season_started: Optional[Callable[[], None]] = None):
        self.width = screen_width
        self.height = screen_height
        self.is_open: bool = False
        self.on_season_started = on_season_started

        self.stage: int = 1  # 1 to 5
        self.finale_data: Dict[str, Any] = {}
        self.player_choice_promote: bool = True
        self.selected_engine_name: Optional[str] = None
        self.available_engines: List[Dict[str, Any]] = []

        self._init_fonts()

    def _init_fonts(self):
        self.font_title = UITheme.get_font(14, bold=True)
        self.font_subtitle = UITheme.get_font(10, bold=False)
        self.font_tab = UITheme.get_font(10, bold=True)
        self.font_card_title = UITheme.get_font(12, bold=True)
        self.font_body = UITheme.get_font(11, bold=False)
        self.font_badge = UITheme.get_font(10, bold=True)
        self.font_btn = UITheme.get_font(11, bold=True)
        self.font_giant = UITheme.get_font(18, bold=True)

    def resize(self, width: int, height: int):
        self.width = width
        self.height = height
        self._init_fonts()

    def open(self, gm: GameManager, ls: LeagueSimulator, em: EngineeringManager, prize_cash_multiplier: float = 1.0):
        """Prepares season finale data, sets up preview, and opens the modal."""
        self.finale_data = ls.calculate_season_finale_data(gm.team_id, prize_cash_multiplier=prize_cash_multiplier)
        self.stage = 1
        self.player_choice_promote = True
        self.is_open = True

        # Pre-select player's current engine or first tier engine
        self._refresh_available_engines(gm, em)

    def _get_effective_tier(self) -> int:
        """Determines player tier taking promotion/relegation choice into account."""
        base_tier = self.finale_data.get("player_tier", 3)
        can_choose = self.finale_data.get("can_player_choose_promotion", False)

        if can_choose and self.player_choice_promote:
            return max(1, base_tier - 1)
        return base_tier

    def _refresh_available_engines(self, gm: GameManager, em: EngineeringManager):
        """Loads engine suppliers based on effective tier."""
        eff_tier = self._get_effective_tier()
        
        # Query if Works Engine Factory is built
        has_works_factory = False
        with gm.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            SELECT is_unlocked FROM team_facilities 
            WHERE team_id = ? AND node_id = 'eng_works_powertrain';
            """, (gm.team_id,))
            w_row = cur.fetchone()
            has_works_factory = bool(w_row[0]) if w_row else False

        from ...management.engineering_manager import ENGINE_SUPPLIERS
        available = []
        for name, data in ENGINE_SUPPLIERS.items():
            if data.get("is_in_house", False):
                if eff_tier == 1 and has_works_factory:
                    available.append(data)
            else:
                if eff_tier == data["min_tier"]:
                    available.append(data)

        self.available_engines = available
        if not self.selected_engine_name or not any(e["name"] == self.selected_engine_name for e in available):
            if available:
                self.selected_engine_name = available[0]["name"]

    def close(self):
        self.is_open = False

    def handle_click(self, mx: int, my: int, gm: GameManager, ls: LeagueSimulator, em: EngineeringManager, diff_cfg: Dict[str, Any]) -> bool:
        if not self.is_open:
            return False

        modal_w = min(1000, self.width - 40)
        modal_h = min(620, self.height - 40)
        modal_x = (self.width - modal_w) // 2
        modal_y = (self.height - modal_h) // 2

        # 1. Top Stage Tabs clicking
        tab_names = ["1. PRIZES", "2. DRIVERS", "3. PROMOTION", "4. ENGINE", "5. KICKOFF"]
        tab_w = 120
        tab_gap = 8
        tab_total_w = len(tab_names) * tab_w + (len(tab_names) - 1) * tab_gap
        tab_start_x = modal_x + (modal_w - tab_total_w) // 2
        tab_y = modal_y + 44

        for idx in range(len(tab_names)):
            t_rect = pygame.Rect(tab_start_x + idx * (tab_w + tab_gap), tab_y, tab_w, 26)
            if t_rect.collidepoint(mx, my):
                self.stage = idx + 1
                self._refresh_available_engines(gm, em)
                return True

        # 2. Bottom Navigation Buttons
        prev_btn = pygame.Rect(modal_x + 20, modal_y + modal_h - 44, 130, 32)
        next_btn = pygame.Rect(modal_x + modal_w - 190, modal_y + modal_h - 44, 170, 32)

        # Previous
        if self.stage > 1 and prev_btn.collidepoint(mx, my):
            self.stage -= 1
            self._refresh_available_engines(gm, em)
            return True

        # Next
        if self.stage < 5 and next_btn.collidepoint(mx, my):
            self.stage += 1
            self._refresh_available_engines(gm, em)
            return True

        # START NEW SEASON Button (Stage 5)
        if self.stage == 5 and next_btn.collidepoint(mx, my):
            prize_mult = diff_cfg.get("prize_cash_mult", 1.0)
            ls.commit_season_finale(
                player_team_id=gm.team_id,
                player_choice_promote=self.player_choice_promote,
                selected_engine=self.selected_engine_name,
                prize_cash_multiplier=prize_mult
            )
            gm.reset_for_new_season()
            self.close()
            if self.on_season_started:
                self.on_season_started()
            return True

        # 3. Stage-Specific Interactive Clicks
        content_rect = pygame.Rect(modal_x + 16, modal_y + 78, modal_w - 32, modal_h - 132)

        if self.stage == 3:
            # Promotion Toggle Clicks if player finished P1
            can_choose = self.finale_data.get("can_player_choose_promotion", False)
            if can_choose:
                card_w = 340
                card_h = 110
                opt1_rect = pygame.Rect(content_rect.x + 14, content_rect.y + 56, card_w, card_h)
                opt2_rect = pygame.Rect(content_rect.x + card_w + 34, content_rect.y + 56, card_w, card_h)

                if opt1_rect.collidepoint(mx, my):
                    self.player_choice_promote = True
                    self._refresh_available_engines(gm, em)
                    return True
                elif opt2_rect.collidepoint(mx, my):
                    self.player_choice_promote = False
                    self._refresh_available_engines(gm, em)
                    return True

        elif self.stage == 4:
            # Engine Selection Clicks
            start_y = content_rect.y + 54
            for idx, supp in enumerate(self.available_engines):
                sy = start_y + idx * 72
                card_rect = pygame.Rect(content_rect.x + 14, sy, content_rect.width - 28, 64)
                if card_rect.collidepoint(mx, my):
                    self.selected_engine_name = supp["name"]
                    return True

        return True

    def render(self, surface: pygame.Surface, gm: GameManager):
        if not self.is_open:
            return

        # 1. Dim Background
        dim_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim_surf.fill((0, 0, 0, 205))
        surface.blit(dim_surf, (0, 0))

        # 2. Modal Frame
        modal_w = min(1000, self.width - 40)
        modal_h = min(620, self.height - 40)
        modal_x = (self.width - modal_w) // 2
        modal_y = (self.height - modal_h) // 2

        modal_rect = pygame.Rect(modal_x, modal_y, modal_w, modal_h)
        pygame.draw.rect(surface, (14, 18, 26), modal_rect, border_radius=6)
        pygame.draw.rect(surface, (0, 220, 255), modal_rect, width=2, border_radius=6)

        # 3. Header Banner
        hdr_rect = pygame.Rect(modal_x, modal_y, modal_w, 38)
        pygame.draw.rect(surface, (20, 30, 46), hdr_rect, border_top_left_radius=6, border_top_right_radius=6)
        
        season_num = self.finale_data.get("season_num", 1)
        surface.blit(self.font_title.render(f"🏆 SEASON {season_num} CHAMPIONSHIP FINALE & NEXT SEASON LAUNCH", True, (255, 215, 0)), (modal_x + 16, modal_y + 10))

        # 4. Top Stage Tabs
        tab_names = ["1. PRIZES", "2. DRIVERS", "3. PROMOTION", "4. ENGINE", "5. KICKOFF"]
        tab_w = 120
        tab_gap = 8
        tab_total_w = len(tab_names) * tab_w + (len(tab_names) - 1) * tab_gap
        tab_start_x = modal_x + (modal_w - tab_total_w) // 2
        tab_y = modal_y + 44

        for idx, t_name in enumerate(tab_names):
            t_num = idx + 1
            is_active = (self.stage == t_num)
            is_done = (self.stage > t_num)

            t_rect = pygame.Rect(tab_start_x + idx * (tab_w + tab_gap), tab_y, tab_w, 26)
            bg_col = (35, 60, 85) if is_active else ((22, 38, 30) if is_done else (18, 22, 30))
            border_col = (255, 215, 0) if is_active else ((0, 240, 140) if is_done else (40, 52, 68))

            pygame.draw.rect(surface, bg_col, t_rect, border_radius=3)
            pygame.draw.rect(surface, border_col, t_rect, width=1, border_radius=3)

            lbl_txt = f"✓ {t_name}" if is_done else t_name
            lbl_col = (255, 215, 0) if is_active else ((0, 240, 140) if is_done else UITheme.TEXT_MUTED)
            lbl = self.font_tab.render(lbl_txt, True, lbl_col)
            surface.blit(lbl, (t_rect.x + (tab_w - lbl.get_width()) // 2, t_rect.y + 6))

        # 5. Content Container Box
        content_rect = pygame.Rect(modal_x + 16, modal_y + 78, modal_w - 32, modal_h - 132)
        pygame.draw.rect(surface, (18, 23, 31), content_rect, border_radius=4)
        pygame.draw.rect(surface, (35, 46, 62), content_rect, width=1, border_radius=4)

        # Render Active Stage
        if self.stage == 1:
            self._render_stage_prizes(surface, content_rect)
        elif self.stage == 2:
            self._render_stage_drivers(surface, content_rect)
        elif self.stage == 3:
            self._render_stage_promotion(surface, content_rect)
        elif self.stage == 4:
            self._render_stage_engine(surface, content_rect)
        elif self.stage == 5:
            self._render_stage_kickoff(surface, content_rect, gm)

        # 6. Bottom Navigation Bar
        prev_btn = pygame.Rect(modal_x + 20, modal_y + modal_h - 44, 130, 32)
        next_btn = pygame.Rect(modal_x + modal_w - 190, modal_y + modal_h - 44, 170, 32)

        if self.stage > 1:
            pygame.draw.rect(surface, (28, 38, 52), prev_btn, border_radius=3)
            pygame.draw.rect(surface, UITheme.PANEL_BORDER, prev_btn, width=1, border_radius=3)
            p_txt = self.font_btn.render("< PREVIOUS", True, UITheme.TEXT_WHITE)
            surface.blit(p_txt, (prev_btn.x + (prev_btn.width - p_txt.get_width()) // 2, prev_btn.y + 8))

        if self.stage < 5:
            pygame.draw.rect(surface, (0, 180, 100), next_btn, border_radius=3)
            n_txt = self.font_btn.render("NEXT STAGE >>", True, (10, 25, 20))
            surface.blit(n_txt, (next_btn.x + (next_btn.width - n_txt.get_width()) // 2, next_btn.y + 8))
        else:
            pygame.draw.rect(surface, (255, 215, 0), next_btn, border_radius=3)
            s_txt = self.font_btn.render("START NEW SEASON >>", True, (10, 20, 15))
            surface.blit(s_txt, (next_btn.x + (next_btn.width - s_txt.get_width()) // 2, next_btn.y + 8))

    # =========================================================================
    # STAGE 1: CONSTRUCTORS' CHAMPIONSHIP & SCALED PRIZE MONEY
    # =========================================================================
    def _render_stage_prizes(self, surface: pygame.Surface, rect: pygame.Rect):
        p_tier = self.finale_data.get("player_tier", 3)
        teams = self.finale_data.get("constructor_standings", {}).get(p_tier, [])
        p_finish = self.finale_data.get("player_constructor_finish", {})

        pos = p_finish.get("position", 1)
        payout = p_finish.get("prize_money", 45000000.0)

        # Top Celebratory Banner
        banner_rect = pygame.Rect(rect.x + 14, rect.y + 10, rect.width - 28, 56)
        is_champ = (pos == 1)
        bg_col = (38, 52, 28) if is_champ else (24, 34, 48)
        border_col = (255, 215, 0) if is_champ else (0, 220, 255)
        pygame.draw.rect(surface, bg_col, banner_rect, border_radius=4)
        pygame.draw.rect(surface, border_col, banner_rect, width=1, border_radius=4)

        if is_champ:
            title_str = "🏆 CONSTRUCTORS' WORLD CHAMPIONS! 🏆"
            desc_str = f"Incredible achievement! You secured 1st Place. Payout: ${payout:,.0f} (Massive HQ Upgrade scale)"
        else:
            title_str = f"CHAMPIONSHIP CONCLUDED - FINISHED P{pos}"
            desc_str = f"Official Constructors' Prize Payout: ${payout:,.0f} has been deposited into your treasury."

        surface.blit(self.font_card_title.render(title_str, True, (255, 215, 0) if is_champ else UITheme.TEXT_WHITE), (banner_rect.x + 14, banner_rect.y + 8))
        surface.blit(self.font_body.render(desc_str, True, (0, 240, 140) if is_champ else UITheme.TEXT_MUTED), (banner_rect.x + 14, banner_rect.y + 30))

        # Standings Table (Left Side)
        table_rect = pygame.Rect(rect.x + 14, rect.y + 74, 580, rect.height - 84)
        pygame.draw.rect(surface, (14, 18, 24), table_rect, border_radius=3)
        pygame.draw.rect(surface, UITheme.PANEL_BORDER, table_rect, width=1, border_radius=3)

        # Header
        th_rect = pygame.Rect(table_rect.x, table_rect.y, table_rect.width, 24)
        pygame.draw.rect(surface, (20, 26, 36), th_rect)
        surface.blit(self.font_badge.render("POS", True, UITheme.TEXT_MUTED), (th_rect.x + 8, th_rect.y + 5))
        surface.blit(self.font_badge.render("CONSTRUCTOR", True, UITheme.TEXT_MUTED), (th_rect.x + 54, th_rect.y + 5))
        surface.blit(self.font_badge.render("POINTS", True, UITheme.TEXT_MUTED), (th_rect.x + 320, th_rect.y + 5))
        surface.blit(self.font_badge.render("SEASON PRIZE MONEY", True, UITheme.TEXT_MUTED), (th_rect.x + 420, th_rect.y + 5))

        for idx, t in enumerate(teams[:10]):
            ry = th_rect.y + 26 + idx * 30
            r_box = pygame.Rect(table_rect.x + 4, ry, table_rect.width - 8, 26)
            is_player = bool(t.get("is_player"))

            r_bg = (34, 48, 64) if is_player else ((22, 28, 38) if idx % 2 == 0 else (16, 20, 28))
            pygame.draw.rect(surface, r_bg, r_box, border_radius=2)
            if is_player:
                pygame.draw.rect(surface, UITheme.ACCENT_CYAN, r_box, width=1, border_radius=2)

            pos_txt = f"P{idx+1}"
            pos_col = (255, 215, 0) if idx == 0 else ((240, 90, 90) if idx == 9 else UITheme.TEXT_WHITE)
            surface.blit(self.font_badge.render(pos_txt, True, pos_col), (r_box.x + 8, r_box.y + 6))

            col_rgb = pygame.Color(t.get("color_hex", "#4080ff"))
            pygame.draw.rect(surface, col_rgb, (r_box.x + 40, r_box.y + 6, 6, 14), border_radius=1)

            t_name = f"{t['name']} {'[YOU]' if is_player else ''}"
            surface.blit(self.font_badge.render(t_name, True, (255, 215, 0) if is_player else UITheme.TEXT_WHITE), (r_box.x + 54, r_box.y + 6))

            surface.blit(self.font_badge.render(f"{t['points']} PTS", True, (0, 220, 255)), (r_box.x + 320, r_box.y + 6))

            pz_txt = f"${t.get('prize_money', 0):,.0f}"
            surface.blit(self.font_badge.render(pz_txt, True, (0, 240, 140) if is_player else UITheme.TEXT_WHITE), (r_box.x + 420, r_box.y + 6))

        # Right Side: Financial Impact Card
        info_rect = pygame.Rect(rect.x + 606, rect.y + 74, rect.width - 620, rect.height - 84)
        pygame.draw.rect(surface, (14, 18, 24), info_rect, border_radius=3)
        pygame.draw.rect(surface, UITheme.PANEL_BORDER, info_rect, width=1, border_radius=3)

        surface.blit(self.font_card_title.render("TREASURY UPGRADE POWER", True, (255, 215, 0)), (info_rect.x + 14, info_rect.y + 12))
        lines = [
            f"Your Payout: ${payout:,.0f}",
            "",
            "Why this prize is transformative:",
            "• Difference between P1 and P10 is >10x!",
            "• P1 provides multiple major HQ facility unlocks:",
            "  - Construct Autoclave Suite ($26M)",
            "  - Build CFD Supercluster ($28M)",
            "  - Expand CAD Offices & Dyno cells",
            "",
            "Funds are already deposited into your cash balance",
            "ready to invest into next season's championship car!"
        ]
        for l_idx, line in enumerate(lines):
            col = (0, 240, 140) if l_idx == 0 else (UITheme.TEXT_WHITE if line.startswith("•") else UITheme.TEXT_MUTED)
            surface.blit(self.font_body.render(line, True, col), (info_rect.x + 14, info_rect.y + 36 + l_idx * 18))

    # =========================================================================
    # STAGE 2: DRIVERS' CHAMPIONSHIP & CHAMPION SPOTLIGHT
    # =========================================================================
    def _render_stage_drivers(self, surface: pygame.Surface, rect: pygame.Rect):
        p_tier = self.finale_data.get("player_tier", 3)
        drivers = self.finale_data.get("driver_standings", {}).get(p_tier, [])
        champ = self.finale_data.get("player_driver_champion", {})

        # Standings Table (Left Side)
        table_rect = pygame.Rect(rect.x + 14, rect.y + 10, 520, rect.height - 20)
        pygame.draw.rect(surface, (14, 18, 24), table_rect, border_radius=3)
        pygame.draw.rect(surface, UITheme.PANEL_BORDER, table_rect, width=1, border_radius=3)

        th_rect = pygame.Rect(table_rect.x, table_rect.y, table_rect.width, 24)
        pygame.draw.rect(surface, (20, 26, 36), th_rect)
        surface.blit(self.font_badge.render("POS", True, UITheme.TEXT_MUTED), (th_rect.x + 8, th_rect.y + 5))
        surface.blit(self.font_badge.render("DRIVER", True, UITheme.TEXT_MUTED), (th_rect.x + 50, th_rect.y + 5))
        surface.blit(self.font_badge.render("TEAM", True, UITheme.TEXT_MUTED), (th_rect.x + 240, th_rect.y + 5))
        surface.blit(self.font_badge.render("PTS", True, UITheme.TEXT_MUTED), (th_rect.x + 440, th_rect.y + 5))

        for idx, d in enumerate(drivers[:12]):
            ry = th_rect.y + 26 + idx * 30
            r_box = pygame.Rect(table_rect.x + 4, ry, table_rect.width - 8, 26)
            is_ply = bool(d.get("is_player_driver")) or (d.get("team_id") == self.finale_data.get("player_team_id"))

            r_bg = (34, 48, 64) if is_ply else ((22, 28, 38) if idx % 2 == 0 else (16, 20, 28))
            pygame.draw.rect(surface, r_bg, r_box, border_radius=2)
            if idx == 0:
                pygame.draw.rect(surface, (255, 215, 0), r_box, width=1, border_radius=2)

            pos_txt = "👑 P1" if idx == 0 else f"P{idx+1}"
            pos_col = (255, 215, 0) if idx == 0 else UITheme.TEXT_WHITE
            surface.blit(self.font_badge.render(pos_txt, True, pos_col), (r_box.x + 6, r_box.y + 6))

            d_name = d.get("name", "Driver")
            surface.blit(self.font_badge.render(d_name, True, (255, 215, 0) if idx == 0 else UITheme.TEXT_WHITE), (r_box.x + 50, r_box.y + 6))

            t_name = d.get("team_name", "Team")
            surface.blit(self.font_body.render(t_name, True, UITheme.TEXT_MUTED), (r_box.x + 240, r_box.y + 6))

            surface.blit(self.font_badge.render(f"{d.get('points', 0)} PTS", True, (0, 220, 255)), (r_box.x + 440, r_box.y + 6))

        # Right Side: Champion Spotlight Card
        spot_rect = pygame.Rect(rect.x + 546, rect.y + 10, rect.width - 560, rect.height - 20)
        pygame.draw.rect(surface, (18, 26, 38), spot_rect, border_radius=4)
        pygame.draw.rect(surface, (255, 215, 0), spot_rect, width=2, border_radius=4)

        if champ:
            c_name = champ.get("name", "World Champion")
            c_team = champ.get("team_name", "Championship Team")
            is_ply_champ = champ.get("is_player_champion", False)

            surface.blit(self.font_card_title.render("👑 DRIVERS' WORLD CHAMPION SPOTLIGHT", True, (255, 215, 0)), (spot_rect.x + 14, spot_rect.y + 12))
            surface.blit(self.font_giant.render(c_name.upper(), True, UITheme.TEXT_WHITE), (spot_rect.x + 14, spot_rect.y + 36))
            surface.blit(self.font_body.render(f"Constructor: {c_team} | {champ.get('points', 0)} Championship Points", True, UITheme.TEXT_MUTED), (spot_rect.x + 14, spot_rect.y + 62))

            # Champion Mood Pill
            pill_rect = pygame.Rect(spot_rect.x + 14, spot_rect.y + 92, spot_rect.width - 28, 44)
            pygame.draw.rect(surface, (36, 48, 30), pill_rect, border_radius=4)
            pygame.draw.rect(surface, (0, 240, 140), pill_rect, width=1, border_radius=4)
            surface.blit(self.font_card_title.render("CHAMPION MOOD: 'WORLD CHAMPION' (Active for Season)", True, (0, 240, 140)), (pill_rect.x + 10, pill_rect.y + 6))
            surface.blit(self.font_body.render("100% Morale, Immune to low morale drops, +35% Composure under pressure", True, UITheme.TEXT_WHITE), (pill_rect.x + 10, pill_rect.y + 24))

            # Stat Buffs
            surface.blit(self.font_card_title.render("CHAMPION PERMANENT ATTRIBUTE GAINS:", True, (0, 220, 255)), (spot_rect.x + 14, spot_rect.y + 152))
            buff_lines = [
                "• Pace: +2 Permanent Rating Gain",
                "• Consistency: +2 Mistake Reduction Gain",
                "• Defending: +2 Wheel-to-Wheel Defense",
                "• Marketability: +12 Fan & Sponsor Magnet Surge"
            ]
            for b_idx, bl in enumerate(buff_lines):
                surface.blit(self.font_body.render(bl, True, UITheme.TEXT_WHITE), (spot_rect.x + 14, spot_rect.y + 176 + b_idx * 18))

            # Player Team Royalty Bonus or Academy Champion Banner
            if is_ply_champ:
                roy_rect = pygame.Rect(spot_rect.x + 14, spot_rect.y + 258, spot_rect.width - 28, 52)
                pygame.draw.rect(surface, (38, 50, 28), roy_rect, border_radius=4)
                pygame.draw.rect(surface, (255, 215, 0), roy_rect, width=1, border_radius=4)
                surface.blit(self.font_card_title.render("💰 TEAM COMMERCIAL ROYALTY BONUS", True, (255, 215, 0)), (roy_rect.x + 10, roy_rect.y + 6))
                surface.blit(self.font_body.render("+$2,500,000 Merchandising Bonus + 8 Global Team Reputation!", True, (0, 240, 140)), (roy_rect.x + 10, roy_rect.y + 26))

        # Academy Champion Spotlight (if player's junior driver won Tier 4 or 5)
        acad_champs = self.finale_data.get("player_academy_champions", [])
        if acad_champs:
            ac_rect = pygame.Rect(spot_rect.x + 14, spot_rect.y + 318, spot_rect.width - 28, 126)
            pygame.draw.rect(surface, (20, 36, 45), ac_rect, border_radius=4)
            pygame.draw.rect(surface, (0, 220, 255), ac_rect, width=1, border_radius=4)

            ac = acad_champs[0]
            ac_name = ac.get("name", "Young Driver")
            ac_tier = ac.get("academy_tier_placement") or 4
            ac_tier_name = "Tier 4 Junior Series" if ac_tier == 4 else "Tier 5 Karting Series"
            ac_pz = ac.get("prize_money", 25000.0 if ac_tier == 4 else 10000.0)
            ac_rep = ac.get("reputation_boost", 5 if ac_tier == 4 else 3)
            is_grad = ac.get("forced_graduation", False)

            surface.blit(self.font_card_title.render(f"🌟 ACADEMY CHAMPION: {ac_name.upper()} ({ac_tier_name})", True, (0, 220, 255)), (ac_rect.x + 10, ac_rect.y + 6))
            surface.blit(self.font_body.render(f"Driver Prize Bonus: ${ac_pz:,.0f} (Pure Driver Bonus) | Team Marketing: +{ac_rep} Reputation", True, (0, 240, 140)), (ac_rect.x + 10, ac_rect.y + 26))
            surface.blit(self.font_body.render("Driver Stat Surge: +5 Pace, +4 Braking, +4 Consistency, +15 Marketability!", True, UITheme.TEXT_WHITE), (ac_rect.x + 10, ac_rect.y + 46))
            
            if is_grad:
                target_t = ac.get("next_tier", ac_tier - 1)
                grad_str = f"🚀 MANDATORY PROMOTION: Age requirement met! Promoted to Tier {target_t} seat!"
                surface.blit(self.font_body.render(grad_str, True, (255, 215, 0)), (ac_rect.x + 10, ac_rect.y + 68))
            else:
                surface.blit(self.font_body.render("Driver will continue skill development in feeder category.", True, UITheme.TEXT_MUTED), (ac_rect.x + 10, ac_rect.y + 68))

    # =========================================================================
    # STAGE 3: PROMOTION & RELEGATION
    # =========================================================================
    def _render_stage_promotion(self, surface: pygame.Surface, rect: pygame.Rect):
        p_tier = self.finale_data.get("player_tier", 3)
        can_choose = self.finale_data.get("can_player_choose_promotion", False)
        is_p10_t3 = self.finale_data.get("is_player_p10_tier3", False)

        cands = self.finale_data.get("candidates", {})
        t2_relegated = cands.get("t2_p10") if p_tier == 3 else cands.get("t1_p10")

        surface.blit(self.font_card_title.render("SEASON TRANSITION: PROMOTION & RELEGATION", True, (255, 215, 0)), (rect.x + 14, rect.y + 12))

        # Promotion Section
        if can_choose:
            sub = "You finished 1st! You have earned the right to upgrade to the next tier, or remain to consolidate."
            surface.blit(self.font_body.render(sub, True, UITheme.TEXT_WHITE), (rect.x + 14, rect.y + 32))

            card_w = 340
            card_h = 110

            # Card 1: Accept Promotion
            opt1_rect = pygame.Rect(rect.x + 14, rect.y + 56, card_w, card_h)
            is_sel1 = self.player_choice_promote
            pygame.draw.rect(surface, (28, 48, 38) if is_sel1 else (18, 24, 32), opt1_rect, border_radius=4)
            pygame.draw.rect(surface, (0, 240, 140) if is_sel1 else (40, 52, 68), opt1_rect, width=2 if is_sel1 else 1, border_radius=4)

            surface.blit(self.font_card_title.render("OPTION A: ACCEPT PROMOTION ↗", True, (0, 240, 140) if is_sel1 else UITheme.TEXT_WHITE), (opt1_rect.x + 12, opt1_rect.y + 10))
            surface.blit(self.font_body.render(f"Promote team to Tier {p_tier - 1}!", True, UITheme.TEXT_WHITE), (opt1_rect.x + 12, opt1_rect.y + 32))
            surface.blit(self.font_badge.render("• Bigger prize money & lucrative sponsors", True, UITheme.TEXT_MUTED), (opt1_rect.x + 12, opt1_rect.y + 54))
            status1 = "[ SELECTED ]" if is_sel1 else "[ CLICK TO SELECT ]"
            surface.blit(self.font_badge.render(status1, True, (0, 240, 140) if is_sel1 else UITheme.TEXT_MUTED), (opt1_rect.x + 12, opt1_rect.y + 82))

            # Card 2: Decline Promotion
            opt2_rect = pygame.Rect(rect.x + card_w + 34, rect.y + 56, card_w, card_h)
            is_sel2 = not self.player_choice_promote
            pygame.draw.rect(surface, (38, 42, 28) if is_sel2 else (18, 24, 32), opt2_rect, border_radius=4)
            pygame.draw.rect(surface, (255, 215, 0) if is_sel2 else (40, 52, 68), opt2_rect, width=2 if is_sel2 else 1, border_radius=4)

            surface.blit(self.font_card_title.render("OPTION B: DECLINE & REMAIN HERE", True, (255, 215, 0) if is_sel2 else UITheme.TEXT_WHITE), (opt2_rect.x + 12, opt2_rect.y + 10))
            p2_team = cands.get("t3_p2", {}).get("name", "2nd Place Team") if p_tier == 3 else cands.get("t2_p2", {}).get("name", "2nd Place Team")
            surface.blit(self.font_body.render(f"Remain in Tier {p_tier}. 2nd team ({p2_team}) promotes instead.", True, UITheme.TEXT_WHITE), (opt2_rect.x + 12, opt2_rect.y + 32))
            surface.blit(self.font_badge.render("• Keep dominating & stockpiling HQ facilities", True, UITheme.TEXT_MUTED), (opt2_rect.x + 12, opt2_rect.y + 54))
            status2 = "[ SELECTED ]" if is_sel2 else "[ CLICK TO SELECT ]"
            surface.blit(self.font_badge.render(status2, True, (255, 215, 0) if is_sel2 else UITheme.TEXT_MUTED), (opt2_rect.x + 12, opt2_rect.y + 82))

        elif is_p10_t3:
            life_rect = pygame.Rect(rect.x + 14, rect.y + 56, rect.width - 28, 70)
            pygame.draw.rect(surface, (38, 48, 30), life_rect, border_radius=4)
            pygame.draw.rect(surface, (0, 240, 140), life_rect, width=1, border_radius=4)
            surface.blit(self.font_card_title.render("🛡️ TIER 3 RELEGATION PROTECTION LIFELINE", True, (0, 240, 140)), (life_rect.x + 12, life_rect.y + 12))
            surface.blit(self.font_body.render("You finished 10th in Tier 3. Promotion from Tier 4 is canceled and you remain safely in Tier 3 to rebuild!", True, UITheme.TEXT_WHITE), (life_rect.x + 12, life_rect.y + 36))

        else:
            std_rect = pygame.Rect(rect.x + 14, rect.y + 56, rect.width - 28, 70)
            pygame.draw.rect(surface, (20, 26, 36), std_rect, border_radius=4)
            p1_name = cands.get(f"t{p_tier}_p1", {}).get("name", "Champion Team")
            surface.blit(self.font_card_title.render(f"TIER {p_tier} PROMOTION: {p1_name} Promoted", True, (0, 220, 255)), (std_rect.x + 12, std_rect.y + 12))
            surface.blit(self.font_body.render(f"{p1_name} finished 1st and advances to Tier {max(1, p_tier - 1)}.", True, UITheme.TEXT_WHITE), (std_rect.x + 12, std_rect.y + 36))

        # Relegation Section (Relegated Titan Warning)
        cur_y = rect.y + 186
        if t2_relegated:
            rel_rect = pygame.Rect(rect.x + 14, cur_y, rect.width - 28, 140)
            pygame.draw.rect(surface, (34, 24, 26), rel_rect, border_radius=4)
            pygame.draw.rect(surface, (240, 90, 90), rel_rect, width=1, border_radius=4)

            rel_team = t2_relegated.get("name", "Relegated Team")
            from_t = p_tier - 1 if p_tier > 1 else 1
            to_t = p_tier

            surface.blit(self.font_card_title.render(f"⚠️ RELEGATED TITAN: {rel_team.upper()} (Tier {from_t} ➔ Tier {to_t})", True, (240, 90, 90)), (rel_rect.x + 12, rel_rect.y + 12))
            surface.blit(self.font_body.render(f"{rel_team} has dropped down from Tier {from_t} and will compete in your tier this upcoming season.", True, UITheme.TEXT_WHITE), (rel_rect.x + 12, rel_rect.y + 36))

            desc_lines = [
                "• Starting Position: They did not plan to be relegated, so they adapt their car to this tier's baseline",
                "  and start slightly behind on initial setup readiness.",
                "• Season Development: They possess massive factory resources and will improve AGGRESSIVELY during",
                "  the season! Expect a ferocious championship battle against this former titan."
            ]
            for idx, dl in enumerate(desc_lines):
                surface.blit(self.font_badge.render(dl, True, (255, 200, 200) if "AGGRESSIVELY" in dl else UITheme.TEXT_MUTED), (rel_rect.x + 12, rel_rect.y + 60 + idx * 17))

    # =========================================================================
    # STAGE 4: ENGINE SUPPLIER SELECTION
    # =========================================================================
    def _render_stage_engine(self, surface: pygame.Surface, rect: pygame.Rect):
        eff_tier = self._get_effective_tier()
        surface.blit(self.font_card_title.render(f"POWER UNIT CONTRACT NEGOTIATIONS (Tier {eff_tier})", True, (255, 215, 0)), (rect.x + 14, rect.y + 12))
        surface.blit(self.font_body.render("Pick your engine supplier for the upcoming championship season. Contracts last for all rounds.", True, UITheme.TEXT_MUTED), (rect.x + 14, rect.y + 30))

        start_y = rect.y + 54
        for idx, supp in enumerate(self.available_engines):
            sy = start_y + idx * 72
            card_rect = pygame.Rect(rect.x + 14, sy, rect.width - 28, 64)

            is_sel = (self.selected_engine_name == supp["name"])
            is_works = supp.get("is_in_house", False)

            bg_col = (28, 48, 64) if is_sel else ((24, 32, 42) if is_works else (18, 22, 30))
            border_col = (255, 215, 0) if is_sel else ((0, 240, 140) if is_works else (40, 52, 68))

            pygame.draw.rect(surface, bg_col, card_rect, border_radius=4)
            pygame.draw.rect(surface, border_col, card_rect, width=2 if is_sel else 1, border_radius=4)

            # Name & Badge
            surface.blit(self.font_card_title.render(supp["name"], True, (255, 215, 0) if is_sel else UITheme.TEXT_WHITE), (card_rect.x + 12, card_rect.y + 8))
            if is_works:
                surface.blit(self.font_badge.render("[ BESPOKE IN-HOUSE WORKS UNIT ]", True, (0, 240, 140)), (card_rect.x + 240, card_rect.y + 8))

            # Philosophy
            surface.blit(self.font_body.render(f"Philosophy: {supp['philosophy']}", True, UITheme.TEXT_MUTED), (card_rect.x + 12, card_rect.y + 26))

            # Stats
            cost_str = "$0/yr" if is_works else f"${supp['cost_season']:,.0f}/yr"
            stat_str = f"Power: {supp['base_power']:.0f} HP | Reliability: {supp['reliability']:.0f}% | Cost: {cost_str}"
            surface.blit(self.font_badge.render(stat_str, True, (0, 220, 255)), (card_rect.x + 12, card_rect.y + 44))

            # Selection Pill
            pill_rect = pygame.Rect(card_rect.x + card_rect.width - 130, card_rect.y + 18, 118, 28)
            p_col = (0, 240, 140) if is_sel else (36, 48, 62)
            pygame.draw.rect(surface, p_col, pill_rect, border_radius=3)
            p_lbl = self.font_btn.render("SELECTED ✓" if is_sel else "SELECT", True, (10, 25, 20) if is_sel else UITheme.TEXT_WHITE)
            surface.blit(p_lbl, (pill_rect.x + (pill_rect.width - p_lbl.get_width()) // 2, pill_rect.y + 6))

    # =========================================================================
    # STAGE 5: SEASON KICKOFF OVERVIEW & CONFIRMATION
    # =========================================================================
    def _render_stage_kickoff(self, surface: pygame.Surface, rect: pygame.Rect, gm: GameManager):
        season_num = self.finale_data.get("season_num", 1)
        next_season = season_num + 1
        eff_tier = self._get_effective_tier()
        tier_names = {1: "Tier 1: World Super Formula (WSF)", 2: "Tier 2: Continental Championship (CC)", 3: "Tier 3: National Open Cup (NOC)"}

        surface.blit(self.font_card_title.render(f"READY TO COMMENCE SEASON {next_season}!", True, (255, 215, 0)), (rect.x + 14, rect.y + 12))
        surface.blit(self.font_body.render("Review your confirmed championship parameters below before taking the green flag:", True, UITheme.TEXT_MUTED), (rect.x + 14, rect.y + 32))

        # Overview Grid Card
        grid_rect = pygame.Rect(rect.x + 14, rect.y + 56, rect.width - 28, 240)
        pygame.draw.rect(surface, (14, 18, 26), grid_rect, border_radius=4)
        pygame.draw.rect(surface, UITheme.PANEL_BORDER, grid_rect, width=1, border_radius=4)

        rows = [
            ("Championship League:", tier_names.get(eff_tier, f"Tier {eff_tier}")),
            ("Championship Status:", f"Season {next_season} (Week 1 / 18, Round 1)"),
            ("Signed Power Unit:", f"{self.selected_engine_name or 'Default'}"),
            ("Championship Points:", "All teams and drivers reset to 0 PTS"),
            ("Driver Development:", "Drivers age +1 year | Morale & skills updated"),
            ("Chassis & Components:", "Wear reset to 0% | Full durability restored"),
            ("Opening Race Venue:", "Round 1 / Grand Prix (Emerald Ring)")
        ]

        for idx, (label, val) in enumerate(rows):
            ry = grid_rect.y + 14 + idx * 30
            surface.blit(self.font_card_title.render(label, True, UITheme.TEXT_MUTED), (grid_rect.x + 16, ry))
            surface.blit(self.font_card_title.render(val, True, (0, 220, 255) if idx == 0 else UITheme.TEXT_WHITE), (grid_rect.x + 240, ry))

        # Instruction Pill
        ins_rect = pygame.Rect(rect.x + 14, rect.y + 308, rect.width - 28, 38)
        pygame.draw.rect(surface, (24, 38, 28), ins_rect, border_radius=4)
        pygame.draw.rect(surface, (0, 240, 140), ins_rect, width=1, border_radius=4)
        surface.blit(self.font_badge.render("Click 'START NEW SEASON >>' below to apply rewards, roll over regulations, and launch into Season " + str(next_season) + "!", True, (0, 240, 140)), (ins_rect.x + 14, ins_rect.y + 11))
