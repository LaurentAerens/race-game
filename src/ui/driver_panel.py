import pygame
from typing import List, Callable, Optional
from ..core.car import Car
from .theme import UITheme

class DriverStrategyPanel:
    """Tactical command bar for player's drivers (Pace, Fuel, ERS, Box)."""
    def __init__(self, x: int, y: int, width: int, height: int, on_box_click: Callable[[Car], None]):
        self.rect = pygame.Rect(x, y, width, height)
        self.on_box_click = on_box_click
        self._init_fonts()

    def _init_fonts(self):
        self.font_title = UITheme.get_font(13, bold=True)
        self.font_sub = UITheme.get_font(11, bold=False)
        self.font_lbl = UITheme.get_font(10, bold=True)
        self.font_btn = UITheme.get_font(10, bold=True)

    def resize(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self._init_fonts()

    def handle_event(self, event: pygame.event.Event, player_cars: List[Car], league_tier: int = 3):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if not self.rect.collidepoint(mx, my):
                return

            card_w = (self.rect.width - 20) // 2
            for i, car in enumerate(player_cars[:2]):
                cx = self.rect.x + 8 + i * (card_w + 8)
                cy = self.rect.y + 6
                mode_locked = getattr(car, "is_mode_locked", False)
                
                # Column layouts
                strat_x = cx + 152
                box_w = 68
                box_x = cx + card_w - box_w - 8
                avail_strat_w = box_x - strat_x - 10
                btn_w = max(42, min(54, (avail_strat_w - 3 * 5) // 4))
                btn_gap = 5
                
                # Check Pace buttons
                pace_modes = ["CONSERVE", "NORMAL", "PUSH", "ATTACK"]
                for p_idx, p_mode in enumerate(pace_modes):
                    # Under neutralization flags or Tier 3 tier locks, buttons are locked
                    if mode_locked or (league_tier >= 3 and p_mode in ["CONSERVE", "ATTACK"]):
                        continue
                    b_rect = pygame.Rect(strat_x + p_idx * (btn_w + btn_gap), cy + 22, btn_w, 20)
                    if b_rect.collidepoint(mx, my):
                        car.pace_mode = p_mode
                        return

                # Check Engine Mix buttons
                eng_modes = ["LEAN", "STANDARD", "RICH"]
                for e_idx, e_mode in enumerate(eng_modes):
                    if mode_locked or (league_tier >= 3 and e_mode in ["LEAN", "RICH"]):
                        continue
                    b_rect = pygame.Rect(strat_x + e_idx * (btn_w + btn_gap), cy + 46, btn_w, 20)
                    if b_rect.collidepoint(mx, my):
                        car.engine_mode = e_mode
                        return

                # Check ERS mode buttons (only active in Tier 2 and Tier 1)
                if league_tier < 3 and not mode_locked:
                    ers_modes = ["AUTO", "RECHARGE", "BALANCED", "OVERTAKE"]
                    for er_idx, er_mode in enumerate(ers_modes):
                        b_rect = pygame.Rect(strat_x + er_idx * (btn_w + btn_gap), cy + 70, btn_w, 20)
                        if b_rect.collidepoint(mx, my):
                            car.ers_mode = er_mode
                            return

                # Check Box This Lap button
                box_btn = pygame.Rect(box_x, cy + 22, box_w, 68)
                if box_btn.collidepoint(mx, my):
                    self.on_box_click(car)
                    return

    def render(self, surface: pygame.Surface, player_cars: List[Car], league_tier: int = 3):
        UITheme.draw_panel(surface, self.rect)
        
        card_w = (self.rect.width - 20) // 2
        for i, car in enumerate(player_cars[:2]):
            cx = self.rect.x + 8 + i * (card_w + 8)
            cy = self.rect.y + 6
            c_rect = pygame.Rect(cx, cy, card_w, self.rect.height - 12)
            
            # Sub card background
            pygame.draw.rect(surface, (28, 33, 44), c_rect, border_radius=4)
            pygame.draw.rect(surface, UITheme.PANEL_BORDER, c_rect, width=1, border_radius=4)

            # Driver title, Position & Technique Tag
            style_label = car.driver.driving_style.replace("_", " ")
            flag_tag = " [FLAG LOCKED]" if getattr(car, "is_mode_locked", False) else ""
            title_col = (255, 204, 0) if getattr(car, "is_mode_locked", False) else UITheme.ACCENT_CYAN
            t_surf = self.font_title.render(f"P{car.position:02d} #{car.driver.number} {car.driver.name} [{style_label}]{flag_tag}", True, title_col)
            surface.blit(t_surf, (cx + 8, cy + 4))

            # Left Telemetry Data Column (cx + 8 to cx + 144)
            # Fuel
            f_lbl = self.font_lbl.render("FUEL", True, UITheme.TEXT_MUTED)
            f_val = self.font_sub.render(f"{car.fuel_kg:04.1f}kg", True, UITheme.TEXT_WHITE)
            surface.blit(f_lbl, (cx + 8, cy + 25))
            surface.blit(f_val, (cx + 46, cy + 24))

            # ERS
            if league_tier >= 3:
                ers_text = "N/A [Spec]"
                ers_col = (110, 120, 135)
            elif league_tier == 2:
                ers_text = f"{int(car.ers_pct)}% [Spec]"
                ers_col = UITheme.ACCENT_CYAN
            else:
                ers_text = f"{int(car.ers_pct)}% [{car.ers_mode[:4]}]"
                ers_col = UITheme.ACCENT_GREEN if car.ers_mode == "AUTO" else UITheme.TEXT_WHITE
            
            e_lbl = self.font_lbl.render("ERS", True, UITheme.TEXT_MUTED)
            e_val = self.font_sub.render(ers_text, True, ers_col)
            surface.blit(e_lbl, (cx + 8, cy + 49))
            surface.blit(e_val, (cx + 46, cy + 48))

            # Tyre
            t_lbl = self.font_lbl.render("TYRE", True, UITheme.TEXT_MUTED)
            t_val = self.font_sub.render(f"{int(100 - car.tires.wear_pct)}% ({car.tires.compound.name})", True, car.tires.compound.color_rgb)
            surface.blit(t_lbl, (cx + 8, cy + 73))
            surface.blit(t_val, (cx + 46, cy + 72))

            # Vertical separator line between Telemetry and Strategy Buttons
            sep_x = cx + 146
            pygame.draw.line(surface, UITheme.PANEL_BORDER, (sep_x, cy + 22), (sep_x, cy + 90), 1)

            # Center Strategy Buttons Column
            strat_x = cx + 152
            box_w = 68
            box_x = cx + card_w - box_w - 8
            avail_strat_w = box_x - strat_x - 10
            btn_w = max(42, min(54, (avail_strat_w - 3 * 5) // 4))
            btn_gap = 5

            mode_locked = getattr(car, "is_mode_locked", False)

            # Pace Mode Row
            pace_modes = ["CONSERVE", "NORMAL", "PUSH", "ATTACK"]
            for p_idx, p_mode in enumerate(pace_modes):
                b_rect = pygame.Rect(strat_x + p_idx * (btn_w + btn_gap), cy + 22, btn_w, 20)
                is_active = (car.pace_mode == p_mode)
                is_disabled = mode_locked or (league_tier >= 3 and p_mode in ["CONSERVE", "ATTACK"])
                label = {"CONSERVE": "CONS", "NORMAL": "NORM", "PUSH": "PUSH", "ATTACK": "ATK"}[p_mode]
                if is_disabled:
                    label = f"[{label[:3]}]"
                UITheme.draw_button(surface, b_rect, label, self.font_btn, is_active=is_active, is_disabled=is_disabled)

            # Engine Mix Row
            eng_modes = ["LEAN", "STANDARD", "RICH"]
            for e_idx, e_mode in enumerate(eng_modes):
                b_rect = pygame.Rect(strat_x + e_idx * (btn_w + btn_gap), cy + 46, btn_w, 20)
                is_active = (car.engine_mode == e_mode)
                is_disabled = mode_locked or (league_tier >= 3 and e_mode in ["LEAN", "RICH"])
                label = {"LEAN": "LEAN", "STANDARD": "STD", "RICH": "RICH"}[e_mode]
                if is_disabled:
                    label = f"[{label[:3]}]"
                UITheme.draw_button(surface, b_rect, label, self.font_btn, is_active=is_active, is_disabled=is_disabled)

            # ERS Mode Row (AUTO, RECHARGE, BALANCED, OVERTAKE)
            ers_modes = ["AUTO", "RECHARGE", "BALANCED", "OVERTAKE"]
            for er_idx, er_mode in enumerate(ers_modes):
                b_rect = pygame.Rect(strat_x + er_idx * (btn_w + btn_gap), cy + 70, btn_w, 20)
                is_active = (car.ers_mode == er_mode) and (league_tier < 3)
                is_disabled = mode_locked or (league_tier >= 3)
                label = {"AUTO": "AUTO", "RECHARGE": "RCHG", "BALANCED": "BAL", "OVERTAKE": "BOOST"}[er_mode]
                if is_disabled:
                    label = "----"
                UITheme.draw_button(surface, b_rect, label, self.font_btn, is_active=is_active, is_disabled=is_disabled)

            # Right BOX Button
            box_btn = pygame.Rect(box_x, cy + 22, box_w, 68)
            box_color = (200, 30, 30) if car.box_this_lap else (40, 50, 65)
            pygame.draw.rect(surface, box_color, box_btn, border_radius=4)
            pygame.draw.rect(surface, (255, 255, 255) if car.box_this_lap else UITheme.BTN_BORDER, box_btn, width=1, border_radius=4)
            
            box_txt1 = self.font_btn.render("BOX", True, UITheme.TEXT_WHITE)
            box_txt2 = self.font_btn.render("CANCEL" if car.box_this_lap else "STRATEGY", True, (240, 240, 240))
            surface.blit(box_txt1, (box_btn.x + (box_btn.width - box_txt1.get_width()) // 2, box_btn.y + 14))
            surface.blit(box_txt2, (box_btn.x + (box_btn.width - box_txt2.get_width()) // 2, box_btn.y + 36))

            # Reliability & Part Durability Health Row
            durs = getattr(car, "part_durability", {})
            fw = durs.get("FRONT_WING", 65.0)
            rw = durs.get("REAR_WING", 65.0)
            brk = durs.get("BRAKES", 65.0)
            eng = durs.get("ENGINE", 65.0)
            min_dur = min(durs.values()) if durs else 65.0
            
            # Health summary color: red if critical (<30%), orange if low (<50%), green otherwise
            h_col = (255, 70, 70) if min_dur < 30.0 else ((255, 180, 50) if min_dur < 50.0 else (0, 220, 160))
            h_text = f"PARTS: FW {fw:.0f}% | RW {rw:.0f}% | BRK {brk:.0f}% | ENG {eng:.0f}%"
            if getattr(car, "is_broken", False):
                h_text = f"RETIRED - MECHANICAL BREAKDOWN ({getattr(car, 'blunder_part_damaged', 'PART')})"
                h_col = (255, 50, 50)
            h_surf = self.font_sub.render(h_text, True, h_col)
            surface.blit(h_surf, (cx + 8, cy + 96))
