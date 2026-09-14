from typing import Any, Callable, Dict, Optional, Tuple

import pygame

from ..database.career_db import CareerDatabase
from ..management.difficulty import DIFFICULTY_CONFIG, DIFFICULTY_LEVELS
from .theme import UITheme

COLOR_PALETTE = [
    ("#00d2be", "Teal / Cyan"),
    ("#dc0000", "Scuderia Red"),
    ("#1e41ff", "Apex Blue"),
    ("#ff8700", "Papaya Orange"),
    ("#00aa66", "Emerald Green"),
    ("#8844aa", "Royal Purple"),
    ("#ffd700", "Championship Gold"),
    ("#b4ff00", "Neon Lime"),
    ("#ff3366", "Crimson Rose"),
    ("#dddddd", "Silver Arrow"),
]

STARTING_ENGINE_SUPPLIERS = [
    {
        "name": "Vortex EcoTech",
        "philosophy": "Entry Budget & Fuel Efficiency",
        "cost_season": 250000,
        "base_power": 70.0,
        "reliability": 88.0,
        "desc": "Ultra-cheap entry engine to conserve cash for early upgrades.",
    },
    {
        "name": "Titan Velocity",
        "philosophy": "Maximum Peak Horsepower",
        "cost_season": 1200000,
        "base_power": 82.0,
        "reliability": 72.0,
        "desc": "High top-speed straight-line speed at moderate reliability risk.",
    },
    {
        "name": "AeroStar Endurance",
        "philosophy": "Bulletproof Reliability & Safe Points",
        "cost_season": 1500000,
        "base_power": 80.0,
        "reliability": 95.0,
        "desc": "High mechanical finish consistency to maximize race points.",
    },
]


class StartScreen:
    """
    First-time Startup and Career Setup Screen.
    Allows entering custom Team Name, Team Principal / CEO Name, choosing Team Color,
    selecting Starting Difficulty, picking initial Season 1 Engine Supplier, and viewing live financials.
    Also provides Load Career menu and Admin Mode access.
    """

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        on_start_career: Callable[..., None],
        on_continue: Callable[[], None],
        on_open_admin: Callable[[], None],
    ):
        self.width = screen_width
        self.height = screen_height
        self.on_start_career = on_start_career
        self.on_continue = on_continue
        self.on_open_admin = on_open_admin

        # State
        self.team_name: str = "Clarck Racing"
        self.principal_name: str = "Alex Mercer"
        self.selected_color_idx: int = 2
        self.selected_difficulty: str = "NORMAL"
        self.selected_engine_supplier: str = "Vortex EcoTech"
        self.enable_tutorial: bool = True
        self.active_input: Optional[str] = None  # 'TEAM', 'PRINCIPAL', or None
        self.is_new_game_mode: bool = False
        self.show_load_career_modal: bool = False

        # Enable Key Repeat
        pygame.key.set_repeat(350, 35)

        self._init_fonts()

        self.db = CareerDatabase("career.db")
        self.player_team: Optional[Dict[str, Any]] = None
        self.career_summary: Optional[Dict[str, Any]] = None
        self.refresh_saved_career()

    def refresh_saved_career(self):
        """Caches player team and career summary to eliminate per-frame SQL queries."""
        self.player_team = self.db.get_player_team()
        self.career_summary = self.db.get_career_summary()
        self.has_existing_career = bool(self.player_team)

    def _init_fonts(self):
        self.font_logo = UITheme.get_font(24, bold=True)
        self.font_sub = UITheme.get_font(11, bold=False)
        self.font_section = UITheme.get_font(11, bold=True)
        self.font_card_title = UITheme.get_font(12, bold=True)
        self.font_body = UITheme.get_font(10, bold=False)
        self.font_bold = UITheme.get_font(10, bold=True)
        self.font_badge = UITheme.get_font(9, bold=True)
        self.font_btn = UITheme.get_font(11, bold=True)

    def resize(self, width: int, height: int):
        """Updates dimensions on window resize while preserving current user inputs and state."""
        self.width = width
        self.height = height
        self._init_fonts()

    def _get_form_layout(self) -> Tuple[int, int, int]:
        total_w = min(1020, max(780, self.width - 60))
        col_w = (total_w - 36) // 2
        left_x = (self.width - total_w) // 2
        right_x = left_x + col_w + 36
        return left_x, right_x, col_w

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # Handle Load Career Modal clicks if open
            if self.show_load_career_modal:
                modal_w = min(540, self.width - 60)
                modal_h = 320
                modal_rect = pygame.Rect((self.width - modal_w) // 2, (self.height - modal_h) // 2, modal_w, modal_h)

                # Close button or outside click
                btn_close = pygame.Rect(modal_rect.right - 34, modal_rect.y + 10, 24, 24)
                if btn_close.collidepoint(mx, my) or not modal_rect.collidepoint(mx, my):
                    self.show_load_career_modal = False
                    return

                # Load Selected / Resume button
                btn_load = pygame.Rect(modal_rect.x + 30, modal_rect.bottom - 54, (modal_w - 75) // 2, 38)
                if btn_load.collidepoint(mx, my):
                    self.show_load_career_modal = False
                    self.on_continue()
                    return

                # Start New Save button
                btn_modal_new = pygame.Rect(
                    modal_rect.x + 45 + (modal_w - 75) // 2, modal_rect.bottom - 54, (modal_w - 75) // 2, 38
                )
                if btn_modal_new.collidepoint(mx, my):
                    self.show_load_career_modal = False
                    self.is_new_game_mode = True
                    return

                return

            # Main Menu Buttons (if existing career saved)
            if self.has_existing_career and not self.is_new_game_mode:
                btn_cont = pygame.Rect(self.width // 2 - 180, self.height // 2 - 20, 360, 42)
                btn_load = pygame.Rect(self.width // 2 - 180, self.height // 2 + 30, 360, 42)
                btn_new = pygame.Rect(self.width // 2 - 180, self.height // 2 + 80, 360, 42)
                btn_admin = pygame.Rect(self.width // 2 - 180, self.height // 2 + 130, 360, 42)

                if btn_cont.collidepoint(mx, my):
                    self.on_continue()
                    return
                elif btn_load.collidepoint(mx, my):
                    self.refresh_saved_career()
                    self.show_load_career_modal = True
                    return
                elif btn_new.collidepoint(mx, my):
                    self.is_new_game_mode = True
                    return
                elif btn_admin.collidepoint(mx, my):
                    self.on_open_admin()
                    return

            # In New Game Setup Form
            if not self.has_existing_career or self.is_new_game_mode:
                left_x, right_x, col_w = self._get_form_layout()

                # 1. Team Name Input Box click
                team_rect = pygame.Rect(left_x, 134, col_w, 28)
                # 2. Principal / CEO Name Input Box click
                princ_rect = pygame.Rect(left_x, 186, col_w, 28)

                if team_rect.collidepoint(mx, my):
                    self.active_input = "TEAM"
                elif princ_rect.collidepoint(mx, my):
                    self.active_input = "PRINCIPAL"
                else:
                    self.active_input = None

                # 3. Color Palette Chips
                chip_gap = 6
                chip_w = (col_w - (len(COLOR_PALETTE) - 1) * chip_gap) // len(COLOR_PALETTE)
                for c_idx in range(len(COLOR_PALETTE)):
                    c_rect = pygame.Rect(left_x + c_idx * (chip_w + chip_gap), 238, chip_w, 24)
                    if c_rect.collidepoint(mx, my):
                        self.selected_color_idx = c_idx
                        return

                # 4. Difficulty Level Chips
                diff_gap = 6
                diff_w = (col_w - 4 * diff_gap) // 5
                for d_idx, d_key in enumerate(DIFFICULTY_LEVELS):
                    d_rect = pygame.Rect(left_x + d_idx * (diff_w + diff_gap), 288, diff_w, 24)
                    if d_rect.collidepoint(mx, my):
                        self.selected_difficulty = d_key
                        return

                # Right Column: Engine Supplier Selection
                for s_idx, supp in enumerate(STARTING_ENGINE_SUPPLIERS):
                    sc_rect = pygame.Rect(right_x, 134 + s_idx * 104, col_w, 96)
                    if sc_rect.collidepoint(mx, my):
                        self.selected_engine_supplier = supp["name"]
                        return

                # Tutorial Checkbox Click
                tut_box = pygame.Rect(self.width // 2 - 200, self.height - 102, 400, 24)
                if tut_box.collidepoint(mx, my):
                    self.enable_tutorial = not self.enable_tutorial
                    return

                # Start Career Button (Bottom Center)
                btn_start = pygame.Rect(self.width // 2 - 220, self.height - 66, 440, 46)
                if btn_start.collidepoint(mx, my):
                    color_hex = COLOR_PALETTE[self.selected_color_idx][0]
                    self.on_start_career(
                        self.team_name.strip() or "Horizon Racing",
                        self.principal_name.strip() or "Alex Mercer",
                        color_hex,
                        self.selected_difficulty,
                        self.selected_engine_supplier,
                        self.enable_tutorial,
                    )
                    return

                # Back Button if existing career
                if self.has_existing_career:
                    btn_back = pygame.Rect(24, 24, 100, 28)
                    if btn_back.collidepoint(mx, my):
                        self.is_new_game_mode = False
                        return
                else:
                    btn_admin_top = pygame.Rect(24, 24, 180, 28)
                    if btn_admin_top.collidepoint(mx, my):
                        self.on_open_admin()
                        return

        elif event.type == pygame.KEYDOWN and self.active_input:
            if event.key == pygame.K_BACKSPACE:
                if self.active_input == "TEAM":
                    self.team_name = self.team_name[:-1]
                elif self.active_input == "PRINCIPAL":
                    self.principal_name = self.principal_name[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_TAB):
                if self.active_input == "TEAM" and event.key == pygame.K_TAB:
                    self.active_input = "PRINCIPAL"
                else:
                    self.active_input = None
            else:
                if event.unicode.isprintable():
                    if self.active_input == "TEAM" and len(self.team_name) < 24:
                        self.team_name += event.unicode
                    elif self.active_input == "PRINCIPAL" and len(self.principal_name) < 24:
                        self.principal_name += event.unicode

    def render(self, surface: pygame.Surface):
        surface.fill((10, 14, 20))

        # Title Header
        logo_txt = self.font_logo.render("OPEN-WHEEL MOTORSPORT MANAGEMENT", True, UITheme.ACCENT_CYAN)
        surface.blit(logo_txt, (self.width // 2 - logo_txt.get_width() // 2, 28))

        sub_txt = self.font_sub.render(
            "Build your racing dynasty from grassroots Tier 3 National Cup to World Super Formula Champion",
            True,
            UITheme.TEXT_MUTED,
        )
        surface.blit(sub_txt, (self.width // 2 - sub_txt.get_width() // 2, 60))

        # Main Menu View (if existing career saved and not in setup)
        if self.has_existing_career and not self.is_new_game_mode:
            p_team = self.player_team or {}
            t_name = p_team.get("name", "Player Team")
            tier_names = {
                1: "Tier 1: World Super Formula",
                2: "Tier 2: Continental Championship",
                3: "Tier 3: National Open Cup",
            }
            t_tier = tier_names.get(p_team.get("tier", 3), "Tier 3")
            cash = p_team.get("cash", 0.0)
            cur_eng = p_team.get("engine_supplier", "Vortex EcoTech")

            # Saved Career Overview Box
            box_rect = pygame.Rect(self.width // 2 - 180, self.height // 2 - 150, 360, 105)
            pygame.draw.rect(surface, (18, 24, 32), box_rect, border_radius=4)
            pygame.draw.rect(surface, UITheme.PANEL_BORDER, box_rect, width=1, border_radius=4)

            surface.blit(
                self.font_badge.render("CURRENT ACTIVE CAREER:", True, UITheme.TEXT_MUTED),
                (box_rect.x + 12, box_rect.y + 10),
            )
            surface.blit(self.font_card_title.render(t_name, True, (255, 215, 0)), (box_rect.x + 12, box_rect.y + 30))
            surface.blit(
                self.font_body.render(f"Division: {t_tier} | Cash: ${cash:,.0f}", True, UITheme.TEXT_WHITE),
                (box_rect.x + 12, box_rect.y + 54),
            )
            surface.blit(
                self.font_badge.render(f"Power Unit: {cur_eng} (Signed Full Season)", True, (0, 240, 140)),
                (box_rect.x + 12, box_rect.y + 78),
            )

            # 1. Continue Button
            btn_cont = pygame.Rect(self.width // 2 - 180, self.height // 2 - 20, 360, 42)
            pygame.draw.rect(surface, (0, 180, 100), btn_cont, border_radius=4)
            c_lbl = self.font_btn.render("CONTINUE CAREER >>", True, (10, 20, 15))
            surface.blit(c_lbl, (btn_cont.x + (btn_cont.width - c_lbl.get_width()) // 2, btn_cont.y + 12))

            # 2. Load Career Button
            btn_load = pygame.Rect(self.width // 2 - 180, self.height // 2 + 30, 360, 42)
            pygame.draw.rect(surface, (26, 38, 54), btn_load, border_radius=4)
            pygame.draw.rect(surface, (60, 90, 130), btn_load, width=1, border_radius=4)
            l_lbl = self.font_btn.render("LOAD / SWITCH CAREER", True, (0, 220, 255))
            surface.blit(l_lbl, (btn_load.x + (btn_load.width - l_lbl.get_width()) // 2, btn_load.y + 12))

            # 3. Start New Career Button
            btn_new = pygame.Rect(self.width // 2 - 180, self.height // 2 + 80, 360, 42)
            pygame.draw.rect(surface, (35, 50, 70), btn_new, border_radius=4)
            pygame.draw.rect(surface, UITheme.ACCENT_CYAN, btn_new, width=1, border_radius=4)
            n_lbl = self.font_btn.render("START NEW CAREER", True, UITheme.TEXT_WHITE)
            surface.blit(n_lbl, (btn_new.x + (btn_new.width - n_lbl.get_width()) // 2, btn_new.y + 12))

            # 4. Admin Mode (Track & Database Editor) Button
            btn_admin = pygame.Rect(self.width // 2 - 180, self.height // 2 + 130, 360, 42)
            pygame.draw.rect(surface, (28, 22, 38), btn_admin, border_radius=4)
            pygame.draw.rect(surface, (180, 80, 240), btn_admin, width=1, border_radius=4)
            a_lbl = self.font_btn.render("ADMIN MODE (TRACK & DB EDITOR)", True, (210, 140, 255))
            surface.blit(a_lbl, (btn_admin.x + (btn_admin.width - a_lbl.get_width()) // 2, btn_admin.y + 12))

            # Render Load Career Modal if open
            if self.show_load_career_modal:
                # Dim background
                dim_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                dim_surf.fill((0, 0, 0, 180))
                surface.blit(dim_surf, (0, 0))

                modal_w = min(540, self.width - 60)
                modal_h = 320
                modal_rect = pygame.Rect((self.width - modal_w) // 2, (self.height - modal_h) // 2, modal_w, modal_h)
                pygame.draw.rect(surface, (18, 24, 34), modal_rect, border_radius=6)
                pygame.draw.rect(surface, (0, 220, 240), modal_rect, width=2, border_radius=6)

                # Modal Header
                m_hdr = pygame.Rect(modal_rect.x, modal_rect.y, modal_rect.width, 40)
                pygame.draw.rect(surface, (26, 34, 48), m_hdr, border_top_left_radius=6, border_top_right_radius=6)
                surface.blit(
                    self.font_card_title.render("LOAD CAREER PROFILE", True, UITheme.ACCENT_CYAN),
                    (m_hdr.x + 16, m_hdr.y + 10),
                )

                # Close button
                btn_close = pygame.Rect(modal_rect.right - 34, modal_rect.y + 10, 24, 24)
                pygame.draw.rect(surface, (180, 40, 40), btn_close, border_radius=3)
                surface.blit(self.font_bold.render("X", True, (255, 255, 255)), (btn_close.x + 7, btn_close.y + 4))

                # Profile Card
                info_card = pygame.Rect(modal_rect.x + 20, modal_rect.y + 54, modal_w - 40, 185)
                pygame.draw.rect(surface, (12, 16, 22), info_card, border_radius=4)
                pygame.draw.rect(surface, UITheme.PANEL_BORDER, info_card, width=1, border_radius=4)

                cs = self.career_summary or {}
                surface.blit(
                    self.font_badge.render("ACTIVE SAVE SLOT #1 (career.db)", True, (0, 240, 140)),
                    (info_card.x + 14, info_card.y + 12),
                )
                surface.blit(
                    self.font_logo.render(cs.get("team_name", t_name), True, (255, 215, 0)),
                    (info_card.x + 14, info_card.y + 32),
                )

                p_str = (
                    f"Team Principal: {cs.get('principal_name', 'Alex Mercer')}  |  Division: Tier {cs.get('tier', 3)}"
                )
                surface.blit(
                    self.font_body.render(p_str, True, UITheme.TEXT_WHITE), (info_card.x + 14, info_card.y + 68)
                )

                fin_str = (
                    f"Treasury Cash: ${cs.get('cash', cash):,.0f}  |  Championship Points: {cs.get('points', 0)} pts"
                )
                surface.blit(self.font_body.render(fin_str, True, (0, 220, 255)), (info_card.x + 14, info_card.y + 92))

                drv_str = f"Race Drivers: {', '.join(cs.get('drivers', ['Driver 1', 'Driver 2']))}"
                surface.blit(
                    self.font_body.render(drv_str, True, UITheme.TEXT_MUTED), (info_card.x + 14, info_card.y + 116)
                )

                cal_str = f"Season Progress: {cs.get('completed_races', 0)} / {cs.get('total_races', 12)} Grands Prix Complete  |  Engine: {cs.get('engine_supplier', cur_eng)}"
                surface.blit(
                    self.font_badge.render(cal_str, True, (255, 200, 40)), (info_card.x + 14, info_card.y + 145)
                )

                # Modal Action Buttons
                btn_load_modal = pygame.Rect(modal_rect.x + 30, modal_rect.bottom - 54, (modal_w - 75) // 2, 38)
                pygame.draw.rect(surface, (0, 180, 100), btn_load_modal, border_radius=4)
                ld_lbl = self.font_btn.render("LOAD THIS CAREER", True, (10, 25, 20))
                surface.blit(
                    ld_lbl, (btn_load_modal.x + (btn_load_modal.width - ld_lbl.get_width()) // 2, btn_load_modal.y + 10)
                )

                btn_modal_new = pygame.Rect(
                    modal_rect.x + 45 + (modal_w - 75) // 2, modal_rect.bottom - 54, (modal_w - 75) // 2, 38
                )
                pygame.draw.rect(surface, (35, 50, 70), btn_modal_new, border_radius=4)
                pygame.draw.rect(surface, UITheme.ACCENT_CYAN, btn_modal_new, width=1, border_radius=4)
                nw_lbl = self.font_btn.render("+ START FRESH CAREER", True, UITheme.TEXT_WHITE)
                surface.blit(
                    nw_lbl, (btn_modal_new.x + (btn_modal_new.width - nw_lbl.get_width()) // 2, btn_modal_new.y + 10)
                )

        # New Game Setup Form (2-Column Layout)
        else:
            # Back Button or Admin Suite Button
            if self.has_existing_career:
                btn_back = pygame.Rect(24, 24, 100, 28)
                pygame.draw.rect(surface, (30, 40, 52), btn_back, border_radius=3)
                b_txt = self.font_badge.render("< BACK", True, UITheme.TEXT_WHITE)
                surface.blit(b_txt, (btn_back.x + (btn_back.width - b_txt.get_width()) // 2, btn_back.y + 7))
            else:
                btn_admin_top = pygame.Rect(24, 24, 180, 28)
                pygame.draw.rect(surface, (28, 22, 38), btn_admin_top, border_radius=3)
                pygame.draw.rect(surface, (180, 80, 240), btn_admin_top, width=1, border_radius=3)
                a_txt = self.font_badge.render("ADMIN & MODDING SUITE", True, (210, 140, 255))
                surface.blit(
                    a_txt, (btn_admin_top.x + (btn_admin_top.width - a_txt.get_width()) // 2, btn_admin_top.y + 7)
                )

            left_x, right_x, col_w = self._get_form_layout()

            # =================================================================
            # Left Column: Team Details, Livery, Difficulty, Live Financials
            # =================================================================
            # 1. Team Name Input
            surface.blit(
                self.font_section.render("1. ENTER CONSTRUCTOR NAME:", True, UITheme.TEXT_WHITE), (left_x, 116)
            )
            team_rect = pygame.Rect(left_x, 134, col_w, 28)
            is_team_act = self.active_input == "TEAM"
            pygame.draw.rect(surface, (18, 24, 32), team_rect, border_radius=3)
            pygame.draw.rect(
                surface,
                UITheme.ACCENT_CYAN if is_team_act else (60, 75, 95),
                team_rect,
                width=2 if is_team_act else 1,
                border_radius=3,
            )

            team_display = self.team_name + ("|" if is_team_act and (pygame.time.get_ticks() // 500) % 2 == 0 else "")
            surface.blit(
                self.font_section.render(team_display, True, UITheme.TEXT_WHITE), (team_rect.x + 8, team_rect.y + 6)
            )

            # 2. Team Principal / CEO Name Input
            surface.blit(
                self.font_section.render("2. ENTER TEAM PRINCIPAL / CEO NAME:", True, (255, 215, 0)), (left_x, 168)
            )
            princ_rect = pygame.Rect(left_x, 186, col_w, 28)
            is_princ_act = self.active_input == "PRINCIPAL"
            pygame.draw.rect(surface, (18, 24, 32), princ_rect, border_radius=3)
            pygame.draw.rect(
                surface,
                (255, 215, 0) if is_princ_act else (60, 75, 95),
                princ_rect,
                width=2 if is_princ_act else 1,
                border_radius=3,
            )

            princ_display = self.principal_name + (
                "|" if is_princ_act and (pygame.time.get_ticks() // 500) % 2 == 0 else ""
            )
            surface.blit(
                self.font_section.render(princ_display, True, (255, 215, 0)), (princ_rect.x + 8, princ_rect.y + 6)
            )

            # 3. Team Color Picker
            surface.blit(
                self.font_section.render("3. SELECT PRIMARY LIVERY COLOR:", True, UITheme.TEXT_WHITE), (left_x, 220)
            )
            chip_gap = 6
            chip_w = (col_w - (len(COLOR_PALETTE) - 1) * chip_gap) // len(COLOR_PALETTE)
            for c_idx, (col_hex, _) in enumerate(COLOR_PALETTE):
                c_rect = pygame.Rect(left_x + c_idx * (chip_w + chip_gap), 238, chip_w, 24)
                col_rgb = pygame.Color(col_hex)
                pygame.draw.rect(surface, col_rgb, c_rect, border_radius=3)
                if c_idx == self.selected_color_idx:
                    pygame.draw.rect(surface, (255, 255, 255), c_rect, width=2, border_radius=3)

            # 4. Difficulty Level Selection
            surface.blit(
                self.font_section.render("4. SELECT CAREER DIFFICULTY:", True, UITheme.TEXT_WHITE), (left_x, 270)
            )
            diff_gap = 6
            diff_w = (col_w - 4 * diff_gap) // 5
            for d_idx, d_key in enumerate(DIFFICULTY_LEVELS):
                d_rect = pygame.Rect(left_x + d_idx * (diff_w + diff_gap), 288, diff_w, 24)
                is_sel = d_key == self.selected_difficulty

                diff_cols = {
                    "VERY_EASY": (0, 240, 140),
                    "EASY": (0, 200, 255),
                    "NORMAL": (255, 215, 0),
                    "HARD": (255, 140, 40),
                    "VERY_HARD": (255, 60, 60),
                }
                d_col = diff_cols.get(d_key, (255, 215, 0))

                pygame.draw.rect(surface, (30, 40, 52) if is_sel else (18, 22, 28), d_rect, border_radius=3)
                pygame.draw.rect(
                    surface, d_col if is_sel else (45, 55, 65), d_rect, width=2 if is_sel else 1, border_radius=3
                )

                d_name = d_key.replace("_", " ")
                lbl = self.font_badge.render(d_name, True, d_col if is_sel else UITheme.TEXT_MUTED)
                surface.blit(lbl, (d_rect.x + (d_rect.width - lbl.get_width()) // 2, d_rect.y + 5))

            # 5. LIVE FINANCIAL RUNWAY & FACILITY UPKEEP OVERVIEW
            base_cash = 15000000.0  # Tier 3 baseline budget
            diff_bonuses = {
                "VERY_EASY": 5000000.0,
                "EASY": 2500000.0,
                "NORMAL": 0.0,
                "HARD": -2000000.0,
                "VERY_HARD": -4000000.0,
            }
            diff_cash = diff_bonuses.get(self.selected_difficulty, 0.0)

            selected_supp = next(
                (s for s in STARTING_ENGINE_SUPPLIERS if s["name"] == self.selected_engine_supplier),
                STARTING_ENGINE_SUPPLIERS[0],
            )
            engine_fee = selected_supp["cost_season"]
            net_starting_cash = base_cash + diff_cash - engine_fee

            diff_cfg = DIFFICULTY_CONFIG[self.selected_difficulty]
            upkeep_mult = diff_cfg.get("upkeep_mult", 1.0)
            base_monthly_upkeep = 185000.0 * upkeep_mult
            runway_months = net_starting_cash / max(1.0, base_monthly_upkeep)

            fin_rect = pygame.Rect(left_x, 324, col_w, 178)
            pygame.draw.rect(surface, (16, 22, 32), fin_rect, border_radius=4)
            pygame.draw.rect(surface, (0, 220, 255), fin_rect, width=1, border_radius=4)

            surface.blit(
                self.font_card_title.render("STARTING TREASURY & FINANCIAL RUNWAY:", True, (255, 215, 0)),
                (fin_rect.x + 10, fin_rect.y + 8),
            )

            cash_str = f"• Baseline Budget: ${base_cash / 1000000:.1f}M | Difficulty Mod: {diff_cash / 1000000:+.1f}M"
            surface.blit(self.font_body.render(cash_str, True, UITheme.TEXT_WHITE), (fin_rect.x + 10, fin_rect.y + 30))

            fee_str = f"• Engine Seasonal Fee ({selected_supp['name']}): -${engine_fee / 1000000:.2f}M"
            surface.blit(self.font_body.render(fee_str, True, (255, 120, 120)), (fin_rect.x + 10, fin_rect.y + 50))

            net_str = f"• NET STARTING CAPITAL: ${net_starting_cash / 1000000:.2f}M"
            surface.blit(self.font_card_title.render(net_str, True, (0, 240, 140)), (fin_rect.x + 10, fin_rect.y + 72))

            upk_str = f"• Base Facility Upkeep: ~${base_monthly_upkeep / 1000:.0f}k / month"
            surface.blit(self.font_body.render(upk_str, True, (255, 200, 40)), (fin_rect.x + 10, fin_rect.y + 96))

            upk_detail = "  (Includes 7 starter facility branches & active specialized tooling rigs)"
            surface.blit(
                self.font_badge.render(upk_detail, True, UITheme.TEXT_MUTED), (fin_rect.x + 10, fin_rect.y + 118)
            )

            runway_str = f"• Initial Operating Runway: ~{runway_months:.0f} Months (Pre-Prize & Sponsor Cash)"
            surface.blit(self.font_badge.render(runway_str, True, (0, 220, 255)), (fin_rect.x + 10, fin_rect.y + 140))

            # =================================================================
            # Right Column: Initial Season 1 Engine Supplier Contract
            # =================================================================
            surface.blit(
                self.font_section.render("5. SELECT SEASON 1 ENGINE SUPPLIER (FULL SEASON):", True, (255, 180, 40)),
                (right_x, 116),
            )

            for s_idx, supp in enumerate(STARTING_ENGINE_SUPPLIERS):
                sc_rect = pygame.Rect(right_x, 134 + s_idx * 104, col_w, 96)
                is_sel = supp["name"] == self.selected_engine_supplier

                bg_col = (28, 38, 52) if is_sel else (18, 22, 28)
                border_col = (0, 240, 140) if is_sel else (45, 55, 65)
                pygame.draw.rect(surface, bg_col, sc_rect, border_radius=4)
                pygame.draw.rect(surface, border_col, sc_rect, width=2 if is_sel else 1, border_radius=4)

                # Title & Selected Badge
                surface.blit(
                    self.font_card_title.render(supp["name"], True, (255, 215, 0) if is_sel else UITheme.TEXT_WHITE),
                    (sc_rect.x + 10, sc_rect.y + 8),
                )
                if is_sel:
                    surface.blit(
                        self.font_badge.render("[ CONTRACT SELECTED ]", True, (0, 240, 140)),
                        (sc_rect.x + sc_rect.width - 140, sc_rect.y + 8),
                    )

                # Philosophy & Description
                surface.blit(
                    self.font_body.render(f"Philosophy: {supp['philosophy']}", True, UITheme.TEXT_MUTED),
                    (sc_rect.x + 10, sc_rect.y + 30),
                )
                surface.blit(
                    self.font_body.render(supp["desc"], True, (160, 175, 190)), (sc_rect.x + 10, sc_rect.y + 50)
                )

                # Stats & Cost
                stat_str = f"Power: {supp['base_power']:.0f} HP | Reliability: {supp['reliability']:.0f}% | Cost: ${supp['cost_season']:,.0f}/yr"
                surface.blit(self.font_badge.render(stat_str, True, (0, 220, 255)), (sc_rect.x + 10, sc_rect.y + 72))

            # Strategic Tip Banner
            tip_rect = pygame.Rect(right_x, 460, col_w, 42)
            pygame.draw.rect(surface, (20, 26, 36), tip_rect, border_radius=3)
            pygame.draw.rect(surface, (45, 60, 80), tip_rect, width=1, border_radius=3)
            surface.blit(
                self.font_badge.render("STRATEGIC TIP:", True, (255, 215, 0)), (tip_rect.x + 8, tip_rect.y + 6)
            )
            surface.blit(
                self.font_body.render(
                    "Vortex saves early cash for facility expansion. Titan adds top speed.", True, UITheme.TEXT_WHITE
                ),
                (tip_rect.x + 8, tip_rect.y + 22),
            )

            # =================================================================
            # Interactive Tutorial Toggle Checkbox
            # =================================================================
            tut_box = pygame.Rect(self.width // 2 - 220, self.height - 102, 440, 24)
            chk_rect = pygame.Rect(tut_box.x, tut_box.y + 2, 18, 18)
            pygame.draw.rect(surface, (20, 28, 38), chk_rect, border_radius=3)
            pygame.draw.rect(
                surface, (0, 220, 255) if self.enable_tutorial else (70, 80, 95), chk_rect, width=1, border_radius=3
            )
            if self.enable_tutorial:
                pygame.draw.rect(
                    surface, (0, 200, 120), pygame.Rect(chk_rect.x + 3, chk_rect.y + 3, 12, 12), border_radius=2
                )
            chk_lbl = self.font_body.render(
                "Enable Interactive Guided Tutorial (Recommended for new principals)",
                True,
                (220, 230, 245) if self.enable_tutorial else UITheme.TEXT_MUTED,
            )
            surface.blit(chk_lbl, (tut_box.x + 28, tut_box.y + 3))

            # =================================================================
            # Start Career Button (Bottom Center)
            # =================================================================
            btn_start = pygame.Rect(self.width // 2 - 220, self.height - 66, 440, 46)
            pygame.draw.rect(surface, (0, 180, 100), btn_start, border_radius=4)
            s_lbl = self.font_btn.render("INITIALIZE CONSTRUCTOR & START CAREER >>", True, (10, 25, 20))
            surface.blit(s_lbl, (btn_start.x + (btn_start.width - s_lbl.get_width()) // 2, btn_start.y + 14))
