from typing import Any, List, Optional

import pygame

from ..core.car import Car
from ..core.tires import TIRE_COMPOUNDS
from .theme import UITheme


class PitStrategyModal:
    """Popup modal dialog for choosing pit stop tire compounds, front wing replacement, and on-the-fly emergency repairs."""

    def __init__(self, screen_width: int, screen_height: int):
        self.width = 460
        self.height = 360
        self.rect = pygame.Rect(
            (screen_width - self.width) // 2, (screen_height - self.height) // 2, self.width, self.height
        )

        self.is_open = False
        self.target_car: Optional[Car] = None
        self.selected_compound = "SOFT"
        self.available_compounds: List[str] = ["HARD", "MEDIUM", "SOFT", "INTER", "WET"]
        self.replace_front_wing = False
        self.emergency_repairs = False
        self.spare_wing_available = True
        self.spare_wing_durability = 100.0
        self.db_manager: Optional[Any] = None

        self._init_fonts()

    def _init_fonts(self):
        self.font_title = UITheme.get_font(13, bold=True)
        self.font_btn = UITheme.get_font(12, bold=True)
        self.font_badge = UITheme.get_font(11, bold=True)
        self.font_desc = UITheme.get_font(12, bold=False)

    def resize(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.rect = pygame.Rect(
            (screen_width - self.width) // 2, (screen_height - self.height) // 2, self.width, self.height
        )
        self._init_fonts()

    def open(
        self,
        car: Car,
        dry_compounds: Optional[List[str]] = None,
        db_manager: Optional[Any] = None,
        team_id: Optional[int] = None,
    ):
        self.target_car = car
        self.db_manager = db_manager
        dry = dry_compounds or ["HARD", "MEDIUM", "SOFT"]
        self.available_compounds = dry + ["INTER", "WET"]
        self.selected_compound = (
            car.pit_queued_compound
            if car.pit_queued_compound in self.available_compounds
            else self.available_compounds[1]
        )
        self.replace_front_wing = getattr(car, "pit_replace_front_wing", False)
        self.emergency_repairs = getattr(car, "pit_emergency_repairs", False)

        # Check spare stock from warehouse if db available
        self.spare_wing_available = True
        self.spare_wing_durability = 100.0
        if db_manager and team_id:
            spares = db_manager.get_team_warehouse_components(team_id, "FRONT_WING")
            if spares:
                self.spare_wing_available = True
                self.spare_wing_durability = spares[0].get("current_durability", 100.0)
            else:
                self.spare_wing_available = False

        self.is_open = True

    def close(self):
        self.is_open = False
        self.target_car = None

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.is_open:
            return False

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # Clicked outside modal -> close
            if not self.rect.collidepoint(mx, my):
                self.close()
                return True

            # Compound buttons
            for idx, c_name in enumerate(self.available_compounds):
                b_rect = pygame.Rect(self.rect.x + 18 + idx * 84, self.rect.y + 66, 76, 58)
                if b_rect.collidepoint(mx, my):
                    self.selected_compound = c_name
                    return True

            # Front Wing Replacement toggle button
            fw_rect = pygame.Rect(self.rect.x + 18, self.rect.y + 194, 205, 42)
            if fw_rect.collidepoint(mx, my) and self.spare_wing_available:
                self.replace_front_wing = not self.replace_front_wing
                return True

            # Emergency Repairs toggle button
            er_rect = pygame.Rect(self.rect.x + 237, self.rect.y + 194, 205, 42)
            if er_rect.collidepoint(mx, my):
                self.emergency_repairs = not self.emergency_repairs
                return True

            # Confirm "CALL PIT STOP" button
            confirm_btn = pygame.Rect(self.rect.x + 24, self.rect.y + 306, 195, 36)
            if confirm_btn.collidepoint(mx, my):
                if self.target_car:
                    self.target_car.order_pit_stop(
                        self.selected_compound,
                        replace_front_wing=self.replace_front_wing,
                        front_wing_durability=self.spare_wing_durability,
                        emergency_repairs=self.emergency_repairs,
                    )
                self.close()
                return True

            # "CANCEL" button
            cancel_btn = pygame.Rect(self.rect.x + 241, self.rect.y + 306, 195, 36)
            if cancel_btn.collidepoint(mx, my):
                if self.target_car:
                    self.target_car.cancel_pit_stop()
                self.close()
                return True

        return True

    def render(self, surface: pygame.Surface):
        if not self.is_open or not self.target_car:
            return

        # Dim background overlay
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        # Main Modal Box
        UITheme.draw_panel(surface, self.rect, border_radius=6)

        # Title bar
        hdr_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, 34)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, hdr_rect, border_top_left_radius=6, border_top_right_radius=6)

        title_text = f"PIT STRATEGY - {self.target_car.driver.name} (#{self.target_car.driver.number})"
        t_surf = self.font_title.render(title_text, True, UITheme.ACCENT_CYAN)
        surface.blit(t_surf, (self.rect.x + 14, self.rect.y + 8))

        sub_text = "Select weekend tire compound to fit on in-lap:"
        s_surf = self.font_desc.render(sub_text, True, UITheme.TEXT_MUTED)
        surface.blit(s_surf, (self.rect.x + 18, self.rect.y + 44))

        from .icons import UIIcons

        # Compound cards
        for idx, c_name in enumerate(self.available_compounds):
            comp = TIRE_COMPOUNDS[c_name]
            b_rect = pygame.Rect(self.rect.x + 18 + idx * 84, self.rect.y + 66, 76, 58)
            is_sel = self.selected_compound == c_name

            bg_col = (45, 55, 75) if is_sel else (26, 30, 38)
            border_col = comp.color_rgb if is_sel else UITheme.PANEL_BORDER

            pygame.draw.rect(surface, bg_col, b_rect, border_radius=4)
            pygame.draw.rect(surface, border_col, b_rect, width=2 if is_sel else 1, border_radius=4)

            # Pip color
            pygame.draw.circle(surface, comp.color_rgb, (b_rect.x + 14, b_rect.y + 14), 6)
            # Tyre wheel graphic
            UIIcons.draw_tyre(surface, (b_rect.x + 8, b_rect.y + 8), comp.color_rgb, size=16)

            # Name & Code
            c_lbl = self.font_btn.render(comp.code, True, UITheme.TEXT_WHITE)
            surface.blit(c_lbl, (b_rect.x + 28, b_rect.y + 7))

            name_lbl = self.font_badge.render(comp.name[:7], True, (210, 215, 220))
            surface.blit(name_lbl, (b_rect.x + 8, b_rect.y + 27))

            tier_lbl = self.font_badge.render(f"[{comp.tier}]", True, UITheme.TEXT_MUTED)
            surface.blit(tier_lbl, (b_rect.x + 8, b_rect.y + 40))

        # Selected Compound Summary Line
        sel_comp = TIRE_COMPOUNDS[self.selected_compound]
        info_rect = pygame.Rect(self.rect.x + 18, self.rect.y + 132, self.rect.width - 36, 54)
        pygame.draw.rect(surface, (18, 22, 28), info_rect, border_radius=4)
        pygame.draw.rect(surface, UITheme.PANEL_BORDER, info_rect, width=1, border_radius=4)

        info1 = f"Selected: {sel_comp.name} [{sel_comp.tier}] | Grip: {int(sel_comp.base_grip * 100)}% | Cliff: {int(sel_comp.cliff_wear_pct)}%"
        cur_fw = self.target_car.part_durability.get("FRONT_WING", 65.0)
        info2 = f"Current Front Wing Durability: {cur_fw:.0f}%"

        surface.blit(self.font_btn.render(info1, True, sel_comp.color_rgb), (info_rect.x + 10, info_rect.y + 8))
        surface.blit(self.font_desc.render(info2, True, UITheme.TEXT_MUTED), (info_rect.x + 10, info_rect.y + 28))

        # 2. Repair & Replacement Options
        fw_rect = pygame.Rect(self.rect.x + 18, self.rect.y + 194, 205, 42)
        fw_bg = (30, 60, 50) if self.replace_front_wing else (22, 26, 32)
        fw_border = (0, 220, 140) if self.replace_front_wing else UITheme.PANEL_BORDER
        pygame.draw.rect(surface, fw_bg, fw_rect, border_radius=4)
        pygame.draw.rect(surface, fw_border, fw_rect, width=2 if self.replace_front_wing else 1, border_radius=4)

        chk_name = "check" if self.replace_front_wing else "wrench"
        chk_col = (0, 230, 110) if self.replace_front_wing else UITheme.TEXT_MUTED
        chk_ic = UIIcons.get_icon(chk_name, size=13, color=chk_col)
        surface.blit(chk_ic, (fw_rect.x + 8, fw_rect.y + 8))

        stock_txt = "SWAP FRONT WING (+4.0s)"
        stock_col = UITheme.TEXT_WHITE if self.spare_wing_available else (120, 120, 120)
        surface.blit(self.font_btn.render(stock_txt, True, stock_col), (fw_rect.x + 25, fw_rect.y + 6))
        avail_txt = (
            f"Spare in Stock ({self.spare_wing_durability:.0f}%)" if self.spare_wing_available else "NO SPARE IN STOCK"
        )
        surface.blit(
            self.font_badge.render(avail_txt, True, (0, 200, 220) if self.spare_wing_available else (220, 60, 60)),
            (fw_rect.x + 25, fw_rect.y + 24),
        )

        er_rect = pygame.Rect(self.rect.x + 237, self.rect.y + 194, 205, 42)
        er_bg = (65, 40, 30) if self.emergency_repairs else (22, 26, 32)
        er_border = (255, 140, 40) if self.emergency_repairs else UITheme.PANEL_BORDER
        pygame.draw.rect(surface, er_bg, er_rect, border_radius=4)
        pygame.draw.rect(surface, er_border, er_rect, width=2 if self.emergency_repairs else 1, border_radius=4)

        er_ic_name = "check" if self.emergency_repairs else "shield"
        er_ic_col = (255, 140, 40) if self.emergency_repairs else UITheme.TEXT_MUTED
        er_ic = UIIcons.get_icon(er_ic_name, size=13, color=er_ic_col)
        surface.blit(er_ic, (er_rect.x + 8, er_rect.y + 8))

        er_txt = "EMERGENCY REPAIRS (+14.0s)"
        surface.blit(self.font_btn.render(er_txt, True, UITheme.TEXT_WHITE), (er_rect.x + 25, er_rect.y + 6))
        er_sub = "Patches worn parts back to 55-60%"
        surface.blit(self.font_badge.render(er_sub, True, (255, 180, 80)), (er_rect.x + 25, er_rect.y + 24))

        # 3. Pit Duration Forecast
        est_stop = 2.4
        if self.replace_front_wing:
            est_stop += 4.0
        if self.emergency_repairs:
            est_stop += 14.0

        t_ic = UIIcons.get_icon("timer", size=13, color=(255, 215, 0))
        surface.blit(t_ic, (self.rect.x + 22, self.rect.y + 252))

        forecast_str = f"Estimated Stationary Stop: ~{est_stop:.1f}s (Tire: ~2.4s"
        if self.replace_front_wing:
            forecast_str += " + 4.0s Wing"
        if self.emergency_repairs:
            forecast_str += " + 14.0s Repairs"
        forecast_str += ")"
        f_surf = self.font_badge.render(forecast_str, True, (255, 215, 0))
        surface.blit(f_surf, (self.rect.x + 39, self.rect.y + 252))

        # Part health overview line
        parts_summary = " | ".join([f"{k[:2]}: {v:.0f}%" for k, v in self.target_car.part_durability.items()][:4])
        sh_mini = UIIcons.get_icon("shield", size=12, color=UITheme.TEXT_MUTED)
        surface.blit(sh_mini, (self.rect.x + 22, self.rect.y + 276))
        p_surf = self.font_badge.render(f"Health: {parts_summary}", True, UITheme.TEXT_MUTED)
        surface.blit(p_surf, (self.rect.x + 22, self.rect.y + 276))
        surface.blit(p_surf, (self.rect.x + 38, self.rect.y + 276))

        # Confirm & Cancel buttons
        confirm_btn = pygame.Rect(self.rect.x + 24, self.rect.y + 306, 195, 36)
        pygame.draw.rect(surface, (0, 180, 100), confirm_btn, border_radius=4)
        c_txt = self.font_btn.render("CONFIRM PIT STOP", True, (10, 20, 20))
        surface.blit(c_txt, (confirm_btn.x + (confirm_btn.width - c_txt.get_width()) // 2, confirm_btn.y + 10))
        UITheme.draw_button(surface, confirm_btn, "CONFIRM PIT STOP", self.font_btn, icon="check", icon_size=15)

        cancel_btn = pygame.Rect(self.rect.x + 241, self.rect.y + 306, 195, 36)
        pygame.draw.rect(surface, (160, 40, 40), cancel_btn, border_radius=4)
        can_txt = self.font_btn.render("ABORT / CLOSE", True, (255, 255, 255))
        surface.blit(can_txt, (cancel_btn.x + (cancel_btn.width - can_txt.get_width()) // 2, cancel_btn.y + 10))
        UITheme.draw_button(surface, cancel_btn, "ABORT / CLOSE", self.font_btn, icon="x", icon_size=15)
