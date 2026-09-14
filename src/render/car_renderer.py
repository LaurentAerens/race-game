import math
from typing import Any, List, Optional

import pygame

from ..core.car import Car
from .camera import Camera


class CarRenderer:
    """
    Renders cars in the minimalist, uncluttered Motorsport Manager Mobile style:
    Clean solid-filled colored balls with sharp outlines, directional pips,
    clear player indicators, crashed car hazard markers, and physical Safety Car.
    """

    def __init__(self):
        self.font_num = pygame.font.SysFont("Arial", 9, bold=True)
        self.font_sc = pygame.font.SysFont("Arial", 9, bold=True)

    def render_cars(
        self,
        surface: pygame.Surface,
        cars: List[Car],
        camera: Camera,
        view_rect: pygame.Rect,
        safety_car: Optional[Any] = None,
    ):
        # Draw non-player cars first, then player cars on top
        sorted_cars = sorted(cars, key=lambda c: 1 if c.driver.is_player else 0)

        for car in sorted_cars:
            if getattr(car, "wreckage_cleared", False):
                continue
            self._render_single_dot_car(surface, car, camera, view_rect)

        # Draw physical Safety Car if active
        if safety_car and getattr(safety_car, "is_active", False):
            self._render_safety_car(surface, safety_car, camera, view_rect)

    def _render_single_dot_car(self, surface: pygame.Surface, car: Car, camera: Camera, view_rect: pygame.Rect):
        sx, sy = camera.world_to_screen(car.world_x, car.world_y, view_rect)

        # Frustum culling
        if not (view_rect.x - 15 <= sx <= view_rect.right + 15 and view_rect.y - 15 <= sy <= view_rect.bottom + 15):
            return

        # Compact, clean ball radius: ~5px in overview, ~7.5px in zoom
        radius = max(4, int(5.5 * min(1.4, max(0.8, camera.zoom))))
        heading = car.heading

        # 1. Aerodynamic Slipstream Wake Trails when drafting (only in Follow-cam or strong tow to avoid clutter)
        if car.slipstream_active and camera.zoom >= 1.2:
            tow = max(0.2, car.slipstream_intensity)
            trail_len = radius * (1.8 + 2.5 * tow)
            perp_h = heading + math.pi / 2.0
            spread = max(1.5, radius * 0.6)

            # Left and Right subtle streamlines
            for side in [-1.0, 1.0]:
                base_x = sx + math.cos(perp_h) * (spread * side)
                base_y = sy + math.sin(perp_h) * (spread * side)
                tail_x = base_x - math.cos(heading) * trail_len
                tail_y = base_y - math.sin(heading) * trail_len

                # Subtle faint stream color
                stream_col = (160, 210, 240) if tow > 0.6 else (120, 160, 190)
                pygame.draw.line(surface, stream_col, (int(base_x), int(base_y)), (int(tail_x), int(tail_y)), 1)

        # 2. Tire Smoke Puffs on Lockups / Aggressive Dive Bombs (Subtle and compact)
        if car.smoke_timer > 0:
            smoke_alpha = min(0.6, car.smoke_timer * 0.5)
            smoke_rad = int(radius * (0.8 + 0.5 * min(1.0, car.smoke_timer)))
            smoke_x = sx - math.cos(heading) * (radius * 1.1)
            smoke_y = sy - math.sin(heading) * (radius * 1.1)

            smoke_surf = pygame.Surface((smoke_rad * 2 + 4, smoke_rad * 2 + 4), pygame.SRCALPHA)
            smoke_color = (210, 215, 220, int(90 * (smoke_alpha / 0.6)))
            pygame.draw.circle(smoke_surf, smoke_color, (smoke_rad + 2, smoke_rad + 2), smoke_rad)
            surface.blit(smoke_surf, (int(smoke_x - smoke_rad - 2), int(smoke_y - smoke_rad - 2)))

        # Broken / Crashed Car Marker
        if getattr(car, "is_broken", False):
            r, g, b = car.driver.color_rgb
            dim_col = (r // 3, g // 3, b // 3)
            pygame.draw.circle(surface, dim_col, (sx, sy), radius)
            pygame.draw.circle(surface, (230, 45, 45), (sx, sy), radius + 1, 1)
            h_len = max(2, radius - 2)
            pygame.draw.line(surface, (255, 60, 60), (sx - h_len, sy - h_len), (sx + h_len, sy + h_len), 2)
            pygame.draw.line(surface, (255, 60, 60), (sx - h_len, sy + h_len), (sx + h_len, sy - h_len), 2)
            return

        # Off-track excursion warning halo
        if getattr(car, "off_track", False):
            pygame.draw.circle(surface, (255, 200, 0), (sx, sy), radius + 3, 1)

        # 3. Defending Stance Subtle Indicator (Amber shield pip on rear)
        if car.is_defending:
            def_x = sx - math.cos(heading) * (radius + 2)
            def_y = sy - math.sin(heading) * (radius + 2)
            pygame.draw.circle(surface, (255, 175, 40), (int(def_x), int(def_y)), max(2, radius // 2))

        # 4. Blue Flag Courtesy Yield Indicator
        if car.is_yielding_blue_flag:
            bf_x = sx + math.sin(heading) * (radius + 3)
            bf_y = sy - math.cos(heading) * (radius + 3)
            pygame.draw.circle(surface, (60, 130, 255), (int(bf_x), int(bf_y)), max(2, radius // 2))

        # 5. Player car clean indicator ring
        if car.driver.is_player:
            pygame.draw.circle(surface, (0, 255, 255), (sx, sy), radius + 3, 1)

        # 6. Solid Filled Team Color Ball
        pygame.draw.circle(surface, car.driver.color_rgb, (sx, sy), radius)
        # Sharp 1px dark border
        pygame.draw.circle(surface, (12, 14, 18), (sx, sy), radius, 1)

        # 7. Small Directional Nose Pip on front of ball
        nose_x = sx + math.cos(heading) * (radius - 1)
        nose_y = sy + math.sin(heading) * (radius - 1)
        nose_col = (0, 255, 120) if car.drs_active else (255, 255, 255)
        pygame.draw.circle(surface, nose_col, (int(nose_x), int(nose_y)), max(1, radius // 3))

        # 8. Tire Compound Pip in Center (Small colored dot)
        comp_col = car.tires.compound.color_rgb
        pip_rad = max(1, radius // 3)
        pygame.draw.circle(surface, comp_col, (sx, sy), pip_rad)

        # 9. Driver Number only when zoomed in (Follow-cam)
        if camera.zoom >= 1.5:
            num_str = str(car.driver.number)
            r, g, b = car.driver.color_rgb
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            txt_col = (10, 10, 10) if lum > 140 else (255, 255, 255)
            txt_surf = self.font_num.render(num_str, True, txt_col)
            surface.blit(txt_surf, (sx - txt_surf.get_width() // 2, sy - radius * 2.2))

    def _render_safety_car(self, surface: pygame.Surface, sc: Any, camera: Camera, view_rect: pygame.Rect):
        sx, sy = camera.world_to_screen(sc.world_x, sc.world_y, view_rect)
        if not (view_rect.x - 25 <= sx <= view_rect.right + 25 and view_rect.y - 25 <= sy <= view_rect.bottom + 25):
            return

        radius = max(5, int(6.5 * min(1.4, max(0.8, camera.zoom))))
        heading = sc.heading

        # High-visibility amber body
        pygame.draw.circle(surface, (255, 204, 0), (sx, sy), radius)
        pygame.draw.circle(surface, (10, 10, 10), (sx, sy), radius, 1)

        # Directional nose pip
        nose_x = sx + math.cos(heading) * (radius - 1)
        nose_y = sy + math.sin(heading) * (radius - 1)
        pygame.draw.circle(surface, (255, 255, 255), (int(nose_x), int(nose_y)), max(1, radius // 3))

        # Flashing emergency roof strobe
        strobe_col = (255, 60, 0) if getattr(sc, "strobe_on", False) else (255, 240, 60)
        roof_x = sx - math.cos(heading) * 1.0
        roof_y = sy - math.sin(heading) * 1.0
        pygame.draw.circle(surface, strobe_col, (int(roof_x), int(roof_y)), max(2, radius // 2))

        # "SC" text badge above
        sc_lbl = self.font_sc.render("SC", True, (255, 220, 50))
        surface.blit(sc_lbl, (sx - sc_lbl.get_width() // 2, sy - radius * 2.2))
