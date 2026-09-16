import pygame

from ..core.simulation import Simulation
from ..render.camera import Camera
from .theme import UITheme


class TimingTower:
    """Live Motorsport Manager timing tower and leaderboard."""

    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self._init_fonts()
        self.row_height = 24

    def _init_fonts(self):
        self.font_header = UITheme.get_font(13, bold=True)
        self.font_row = UITheme.get_font(12, bold=False)
        self.font_bold = UITheme.get_font(12, bold=True)
        self.font_badge = UITheme.get_font(11, bold=True)

    def resize(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self._init_fonts()

    def handle_event(self, event: pygame.event.Event, sim: Simulation, camera: Camera) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.rect.collidepoint(mx, my):
                # Calculate clicked row
                offset_y = my - (self.rect.y + 28)
                if offset_y >= 0:
                    row_idx = offset_y // self.row_height
                    if 0 <= row_idx < len(sim.cars):
                        selected_car = sim.cars[row_idx]
                        camera.set_follow_car(selected_car)
                        return True

        return False

    def render(self, surface: pygame.Surface, sim: Simulation, camera: Camera):
        UITheme.draw_panel(surface, self.rect)

        # Header bar
        hdr_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, 26)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, hdr_rect, border_top_left_radius=4, border_top_right_radius=4)

        # Header columns
        from .icons import UIIcons

        # Header columns with icons
        txt_pos = self.font_header.render("POS", True, UITheme.TEXT_MUTED)
        txt_drv = self.font_header.render("DRIVER", True, UITheme.TEXT_MUTED)
        surface.blit(txt_pos, (self.rect.x + 8, self.rect.y + 6))

        ic_drv = UIIcons.get_icon("user", size=12, color=UITheme.TEXT_MUTED)
        surface.blit(ic_drv, (self.rect.x + 38, self.rect.y + 7))
        txt_drv = self.font_header.render("DRV", True, UITheme.TEXT_MUTED)
        surface.blit(txt_drv, (self.rect.x + 53, self.rect.y + 6))

        ic_gap = UIIcons.get_icon("timer", size=12, color=UITheme.TEXT_MUTED)
        surface.blit(ic_gap, (self.rect.x + 120, self.rect.y + 7))
        txt_gap = self.font_header.render("GAP", True, UITheme.TEXT_MUTED)
        surface.blit(txt_gap, (self.rect.x + 135, self.rect.y + 6))

        UIIcons.draw_tyre(surface, (self.rect.x + 188, self.rect.y + 7), (160, 170, 185), size=12)
        txt_tire = self.font_header.render("TYRE", True, UITheme.TEXT_MUTED)
        surface.blit(txt_tire, (self.rect.x + 203, self.rect.y + 6))

        ic_pit = UIIcons.get_icon("wrench", size=12, color=UITheme.TEXT_MUTED)
        surface.blit(ic_pit, (self.rect.x + 250, self.rect.y + 7))
        txt_pit = self.font_header.render("PIT", True, UITheme.TEXT_MUTED)
        surface.blit(txt_pit, (self.rect.x + 265, self.rect.y + 6))

        surface.blit(txt_pos, (self.rect.x + 8, self.rect.y + 6))
        surface.blit(txt_drv, (self.rect.x + 42, self.rect.y + 6))
        surface.blit(txt_gap, (self.rect.x + 130, self.rect.y + 6))
        surface.blit(txt_tire, (self.rect.x + 195, self.rect.y + 6))
        surface.blit(txt_pit, (self.rect.x + 252, self.rect.y + 6))

        # Rows
        start_y = self.rect.y + 28
        for i, car in enumerate(sim.cars[:20]):
            r_rect = pygame.Rect(
                self.rect.x + 2, start_y + i * self.row_height, self.rect.width - 4, self.row_height - 2
            )

            # Hover / Selected highlight
            is_selected = camera.followed_car == car and camera.mode == "FOLLOW_CAR"
            if is_selected:
                pygame.draw.rect(surface, (35, 50, 70), r_rect, border_radius=2)
            elif car.driver.is_player:
                pygame.draw.rect(surface, (20, 38, 48), r_rect, border_radius=2)

            # Team Livery color strip
            c_strip = pygame.Rect(r_rect.x + 2, r_rect.y + 2, 4, r_rect.height - 4)
            pygame.draw.rect(surface, car.driver.color_rgb, c_strip)

            # Position
            p_text = f"{car.position:02d}"
            p_surf = self.font_bold.render(p_text, True, UITheme.TEXT_WHITE)
            surface.blit(p_surf, (r_rect.x + 10, r_rect.y + 4))

            # Driver code & name
            drv_text = car.driver.code
            drv_color = UITheme.ACCENT_CYAN if car.driver.is_player else UITheme.TEXT_WHITE
            drv_surf = self.font_bold.render(drv_text, True, drv_color)
            surface.blit(drv_surf, (r_rect.x + 40, r_rect.y + 4))

            # Gap to leader / Leader status
            if getattr(car, "is_dnf", False):
                dnf_ic = UIIcons.get_icon("x", size=12, color=UITheme.ACCENT_RED)
                surface.blit(dnf_ic, (r_rect.x + 124, r_rect.y + 5))
                gap_surf = self.font_row.render("DNF", True, UITheme.ACCENT_RED)
                surface.blit(gap_surf, (r_rect.x + 138, r_rect.y + 4))
            elif getattr(car, "off_track", False):
                gap_surf = self.font_row.render("OFF", True, UITheme.ACCENT_YELLOW)
                surface.blit(gap_surf, (r_rect.x + 126, r_rect.y + 4))
            elif i == 0:
                tr_ic = UIIcons.get_icon("trophy", size=12, color=UITheme.ACCENT_YELLOW)
                surface.blit(tr_ic, (r_rect.x + 122, r_rect.y + 5))
                gap_surf = self.font_bold.render("LEADER", True, UITheme.ACCENT_YELLOW)
                surface.blit(gap_surf, (r_rect.x + 137, r_rect.y + 4))
            else:
                gap_text = f"+{car.gap_to_leader:04.1f}s"
                gap_surf = self.font_row.render(gap_text, True, UITheme.TEXT_WHITE)
                surface.blit(gap_surf, (r_rect.x + 126, r_rect.y + 4))

            # Tire compound badge + wear %
            comp = car.tires.compound
            UIIcons.draw_tyre(surface, (r_rect.x + 192, r_rect.y + 3), comp.color_rgb, size=15)
            t_code = self.font_badge.render(comp.code[:1], True, (255, 255, 255))
            surface.blit(t_code, (r_rect.x + 196, r_rect.y + 2))

            # Wear % text
            wear_int = int(100.0 - car.tires.wear_pct)
            wear_color = UITheme.TEXT_MUTED if wear_int > 40 else UITheme.ACCENT_RED
            wear_surf = self.font_row.render(f"{wear_int}%", True, wear_color)
            surface.blit(wear_surf, (r_rect.x + 212, r_rect.y + 4))

            # Pit Stop state / count
            if getattr(car, "is_dnf", False):
                pit_text = "OUT"
                pit_color = UITheme.ACCENT_RED
            elif car.in_pit_lane:
                pit_text = "PIT"
                pit_color = UITheme.ACCENT_YELLOW
                p_ic = UIIcons.get_icon("wrench", size=12, color=UITheme.ACCENT_YELLOW)
                surface.blit(p_ic, (r_rect.x + 248, r_rect.y + 5))
            elif car.box_this_lap:
                pit_text = "BOX"
                pit_color = UITheme.ACCENT_RED
                b_ic = UIIcons.get_icon("octagon", size=12, color=UITheme.ACCENT_RED)
                surface.blit(b_ic, (r_rect.x + 248, r_rect.y + 5))
            else:
                pit_text = f"{car.total_pit_stops}P"
                pit_color = UITheme.TEXT_MUTED

            pit_x = r_rect.x + 263 if (car.in_pit_lane or car.box_this_lap) else r_rect.x + 252
            pit_surf = self.font_bold.render(pit_text, True, pit_color)
            surface.blit(pit_surf, (pit_x, r_rect.y + 4))
