from typing import Any, Optional, Tuple

import pygame

from ..core.circuit import Circuit
from .camera import Camera


class TrackRenderer:
    """Renders the racing circuit with variable section widths, kerbs, DRS zones, and pit lane."""

    # Palette
    COLOR_GRASS = (24, 32, 28)
    COLOR_ASPHALT = (45, 48, 54)
    COLOR_ASPHALT_WET = (30, 32, 38)
    COLOR_EDGE_LINE = (180, 185, 190)
    COLOR_RACING_LINE = (60, 65, 75)
    COLOR_KERB_RED = (220, 40, 40)
    COLOR_KERB_WHITE = (245, 245, 245)
    COLOR_DRS = (0, 230, 110)
    COLOR_PIT_LANE = (40, 42, 48)
    COLOR_SECTOR_LINE = (240, 200, 20)

    def render(
        self,
        surface: pygame.Surface,
        circuit: Circuit,
        camera: Camera,
        view_rect: pygame.Rect,
        track_wetness: Any = 0.0,
    ):
        """Draws the complete circuit geometry."""
        if len(circuit.points) < 3:
            return

        # Handle WeatherSystem or numeric float wetness
        weather_obj = track_wetness if hasattr(track_wetness, "get_sector_wetness") else None
        overall_wet = getattr(
            track_wetness, "track_wetness", float(track_wetness) if isinstance(track_wetness, (int, float)) else 0.0
        )

        # 1. Fill background / grass
        pygame.draw.rect(surface, self.COLOR_GRASS, view_rect)

        # 2. Draw Pit Lane if available
        if circuit.pit_lane_enabled and len(circuit.pit_points) > 2:
            self._render_pit_lane(surface, circuit, camera, view_rect)

        # 3. Draw Main Circuit Asphalt Ribbon with Variable Width and Per-Sector Wetness
        self._render_asphalt_ribbon(surface, circuit, camera, view_rect, overall_wet, weather_obj)

        # 4. Draw Apex Kerbs (Rumble Strips)
        self._render_kerbs(surface, circuit, camera, view_rect)

        # 5. Draw DRS Zones
        self._render_drs_zones(surface, circuit, camera, view_rect)

        # 6. Draw Sector Lines
        self._render_sector_lines(surface, circuit, camera, view_rect)

        # 7. Draw Start / Finish Line
        self._render_start_finish(surface, circuit, camera, view_rect)

    def _render_asphalt_ribbon(
        self,
        surface: pygame.Surface,
        circuit: Circuit,
        camera: Camera,
        view_rect: pygame.Rect,
        overall_wet: float,
        weather_obj: Optional[Any] = None,
    ):
        n_pts = len(circuit.points)
        has_widths = len(circuit.widths_sample) == n_pts
        default_color = self._blend_color(self.COLOR_ASPHALT, self.COLOR_ASPHALT_WET, overall_wet)

        # Build left and right boundary screen points
        poly_left = []
        poly_right = []
        for i in range(n_pts):
            px, py = circuit.points[i]
            nx, ny = circuit.normals[i]
            half_w = (circuit.widths_sample[i] / 2.0) if has_widths else (circuit.width / 2.0)

            # Left edge
            lx = px + nx * half_w
            ly = py + ny * half_w
            poly_left.append(camera.world_to_screen(lx, ly, view_rect))

            # Right edge
            rx = px - nx * half_w
            ry = py - ny * half_w
            poly_right.append(camera.world_to_screen(rx, ry, view_rect))

        # Draw connecting quad polygons around the loop with per-sector wetness
        for i in range(n_pts):
            next_i = (i + 1) % n_pts
            quad = [poly_left[i], poly_left[next_i], poly_right[next_i], poly_right[i]]
            if weather_obj and len(circuit.s_samples) == n_pts:
                s_dist = circuit.s_samples[i]
                sec = circuit.get_sector(s_dist)
                sec_wet = weather_obj.get_sector_wetness(sec)
                quad_color = self._blend_color(self.COLOR_ASPHALT, self.COLOR_ASPHALT_WET, sec_wet)
            else:
                quad_color = default_color
            pygame.draw.polygon(surface, quad_color, quad)

        # Draw outer white edge boundary lines
        for i in range(n_pts):
            next_i = (i + 1) % n_pts
            pygame.draw.line(
                surface, self.COLOR_EDGE_LINE, poly_left[i], poly_left[next_i], max(1, int(1.5 * camera.zoom))
            )
            pygame.draw.line(
                surface, self.COLOR_EDGE_LINE, poly_right[i], poly_right[next_i], max(1, int(1.5 * camera.zoom))
            )

    def _render_kerbs(self, surface: pygame.Surface, circuit: Circuit, camera: Camera, view_rect: pygame.Rect):
        """Draws red-and-white alternating kerbs on tight corners."""
        kerb_w = 2.2
        n_pts = len(circuit.points)
        has_widths = len(circuit.widths_sample) == n_pts

        for i in range(n_pts):
            curv = circuit.curvatures[i]
            if curv > 0.008:
                px, py = circuit.points[i]
                nx, ny = circuit.normals[i]
                next_i = (i + 1) % n_pts
                npx, npy = circuit.points[next_i]
                nnx, nny = circuit.normals[next_i]

                half_w1 = (circuit.widths_sample[i] / 2.0) if has_widths else (circuit.width / 2.0)
                half_w2 = (circuit.widths_sample[next_i] / 2.0) if has_widths else (circuit.width / 2.0)

                k_color = self.COLOR_KERB_RED if (i // 3) % 2 == 0 else self.COLOR_KERB_WHITE

                k_p1 = camera.world_to_screen(px + nx * half_w1, py + ny * half_w1, view_rect)
                k_p2 = camera.world_to_screen(px + nx * (half_w1 + kerb_w), py + ny * (half_w1 + kerb_w), view_rect)
                k_p3 = camera.world_to_screen(npx + nnx * (half_w2 + kerb_w), npy + nny * (half_w2 + kerb_w), view_rect)
                k_p4 = camera.world_to_screen(npx + nnx * half_w2, npy + nny * half_w2, view_rect)

                pygame.draw.polygon(surface, k_color, [k_p1, k_p2, k_p3, k_p4])

    def _render_pit_lane(self, surface: pygame.Surface, circuit: Circuit, camera: Camera, view_rect: pygame.Rect):
        pit_w = 6.0
        half_w = pit_w / 2.0
        n_pts = len(circuit.pit_points)
        if n_pts < 2:
            return

        poly_left = []
        poly_right = []
        for i in range(n_pts):
            px, py = circuit.pit_points[i]
            tx, ty = circuit.pit_tangents[i]
            nx, ny = -ty, tx
            poly_left.append(camera.world_to_screen(px + nx * half_w, py + ny * half_w, view_rect))
            poly_right.append(camera.world_to_screen(px - nx * half_w, py - ny * half_w, view_rect))

        for i in range(n_pts - 1):
            quad = [poly_left[i], poly_left[i + 1], poly_right[i + 1], poly_right[i]]
            pygame.draw.polygon(surface, self.COLOR_PIT_LANE, quad)
            pygame.draw.line(
                surface, self.COLOR_EDGE_LINE, poly_left[i], poly_left[i + 1], max(1, int(1.2 * camera.zoom))
            )
            pygame.draw.line(
                surface, self.COLOR_EDGE_LINE, poly_right[i], poly_right[i + 1], max(1, int(1.2 * camera.zoom))
            )

        # Pit Entry Line (Yellow)
        pygame.draw.line(surface, (240, 210, 40), poly_left[0], poly_right[0], max(2, int(2.5 * camera.zoom)))

        # Pit Exit Line (Green)
        pygame.draw.line(surface, (40, 230, 100), poly_left[-1], poly_right[-1], max(2, int(2.5 * camera.zoom)))

        # Draw Pit Box marker
        box_px, box_py, _ = circuit.get_pit_position(circuit.pit_length * circuit.pit_box_s)
        s_box = camera.world_to_screen(box_px, box_py, view_rect)
        box_rad = max(4, int(5.5 * camera.zoom))
        pygame.draw.circle(surface, (230, 200, 40), s_box, box_rad, max(1, int(2.0 * camera.zoom)))
        pygame.draw.circle(surface, (255, 255, 255), s_box, max(2, int(3.0 * camera.zoom)))

    def _render_drs_zones(self, surface: pygame.Surface, circuit: Circuit, camera: Camera, view_rect: pygame.Rect):
        for zone in circuit.drs_zones:
            start_s = zone.get("start_s", 0.0)
            end_s = zone.get("end_s", 0.0)

            dist = (end_s - start_s) % circuit.length
            if dist <= 10.0:
                continue
            num_steps = max(5, int(dist / 6.0))

            pts_left = []
            pts_right = []
            for step in range(num_steps + 1):
                s_eval = (start_s + (dist * (step / num_steps))) % circuit.length
                w_eval = circuit.get_width(s_eval)
                lx, ly = circuit.get_position(s_eval, lateral_offset=w_eval / 2.0 - 0.5)
                rx, ry = circuit.get_position(s_eval, lateral_offset=-w_eval / 2.0 + 0.5)
                pts_left.append(camera.world_to_screen(lx, ly, view_rect))
                pts_right.append(camera.world_to_screen(rx, ry, view_rect))

            if len(pts_left) > 1:
                pygame.draw.lines(surface, self.COLOR_DRS, False, pts_left, max(2, int(3.0 * camera.zoom)))
                pygame.draw.lines(surface, self.COLOR_DRS, False, pts_right, max(2, int(3.0 * camera.zoom)))

            # Start line across track (DRS Activation)
            w_start = circuit.get_width(start_s)
            p1_start = circuit.get_position(start_s, lateral_offset=w_start / 2.0)
            p2_start = circuit.get_position(start_s, lateral_offset=-w_start / 2.0)
            s_p1 = camera.world_to_screen(p1_start[0], p1_start[1], view_rect)
            s_p2 = camera.world_to_screen(p2_start[0], p2_start[1], view_rect)
            pygame.draw.line(surface, self.COLOR_DRS, s_p1, s_p2, max(3, int(4.0 * camera.zoom)))

            # End line across track (DRS Deactivation / Braking Point)
            w_end = circuit.get_width(end_s)
            p1_end = circuit.get_position(end_s, lateral_offset=w_end / 2.0)
            p2_end = circuit.get_position(end_s, lateral_offset=-w_end / 2.0)
            e_p1 = camera.world_to_screen(p1_end[0], p1_end[1], view_rect)
            e_p2 = camera.world_to_screen(p2_end[0], p2_end[1], view_rect)
            pygame.draw.line(surface, (255, 90, 90), e_p1, e_p2, max(3, int(4.0 * camera.zoom)))

            # Render "DRS ZONE" on-track text marker midway through
            mid_s = (start_s + dist * 0.5) % circuit.length
            mid_px, mid_py = circuit.get_position(mid_s, lateral_offset=0.0)
            s_mid = camera.world_to_screen(mid_px, mid_py, view_rect)
            if view_rect.collidepoint(s_mid):
                font_sz = max(9, int(11 * camera.zoom))
                font_drs = pygame.font.SysFont("Segoe UI", font_sz, bold=True)
                drs_lbl = font_drs.render(zone.get("name", "DRS ZONE"), True, (0, 255, 140))
                lbl_rect = drs_lbl.get_rect(center=s_mid)
                pygame.draw.rect(surface, (14, 20, 16), lbl_rect.inflate(6, 4), border_radius=3)
                pygame.draw.rect(surface, (0, 220, 100), lbl_rect.inflate(6, 4), width=1, border_radius=3)
                surface.blit(drs_lbl, lbl_rect)

    def _render_sector_lines(self, surface: pygame.Surface, circuit: Circuit, camera: Camera, view_rect: pygame.Rect):
        for prop in circuit.sectors[:2]:
            s_dist = prop * circuit.length
            half_w = circuit.get_width(s_dist) / 2.0
            p_left = camera.world_to_screen(*circuit.get_position(s_dist, half_w), view_rect)
            p_right = camera.world_to_screen(*circuit.get_position(s_dist, -half_w), view_rect)
            pygame.draw.line(surface, self.COLOR_SECTOR_LINE, p_left, p_right, max(2, int(2.0 * camera.zoom)))

    def _render_start_finish(self, surface: pygame.Surface, circuit: Circuit, camera: Camera, view_rect: pygame.Rect):
        half_w = circuit.get_width(0.0) / 2.0
        p_left = camera.world_to_screen(*circuit.get_position(0.0, half_w), view_rect)
        p_right = camera.world_to_screen(*circuit.get_position(0.0, -half_w), view_rect)
        pygame.draw.line(surface, (255, 255, 255), p_left, p_right, max(3, int(4.0 * camera.zoom)))

    @staticmethod
    def _blend_color(c1: Tuple[int, int, int], c2: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
        factor = max(0.0, min(1.0, factor))
        return (
            int(c1[0] + (c2[0] - c1[0]) * factor),
            int(c1[1] + (c2[1] - c1[1]) * factor),
            int(c1[2] + (c2[2] - c1[2]) * factor),
        )
