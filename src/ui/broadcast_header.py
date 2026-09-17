import pygame

from ..core.race_control import FlagStatus
from ..core.simulation import Simulation
from ..render.camera import Camera
from .theme import UITheme


class BroadcastHeader:
    """Top bar for session laps, weather radar, speed controls, flags, and camera modes."""

    def __init__(self, width: int, height: int = 48):
        self.rect = pygame.Rect(0, 0, width, height)
        self._init_fonts()

    def _init_fonts(self):
        self.font_title = UITheme.get_font(13, bold=True)
        self.font_lap = UITheme.get_font(15, bold=True)
        self.font_sub = UITheme.get_font(12, bold=False)
        self.font_btn = UITheme.get_font(11, bold=True)
        self.font_flag = UITheme.get_font(11, bold=True)

    def resize(self, width: int, height: int = 48):
        self.rect = pygame.Rect(0, 0, width, height)
        self._init_fonts()

    def handle_event(self, event: pygame.event.Event, sim: Simulation, camera: Camera) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if not self.rect.collidepoint(mx, my):
                return False

            # Camera View Toggle button (Placed to the left of speed buttons, completely clear of nav tabs)
            # Nav tabs occupy: width - 345 to width - 10
            # Speed buttons occupy: width - 505 to width - 360 (5 buttons)
            # Camera button occupies: width - 615 to width - 515 (100px wide)
            cam_btn = pygame.Rect(self.rect.width - 615, 10, 100, 28)
            if cam_btn.collidepoint(mx, my):
                if camera.mode == "TRACK_OVERVIEW":
                    player_cars = [c for c in sim.cars if c.driver.is_player]
                    target_car = player_cars[0] if player_cars else sim.cars[0]
                    camera.set_follow_car(target_car)
                else:
                    camera.set_overview_mode(sim.circuit)
                return True

            # Speed buttons (||, 1x, 2x, 4x, 8x) placed from width - 505 to width - 360
            speeds = [(0.0, "||"), (1.0, "1x"), (2.0, "2x"), (4.0, "4x"), (8.0, "8x")]
            speed_start_x = self.rect.width - 505
            for idx, (spd, lbl) in enumerate(speeds):
                b_rect = pygame.Rect(speed_start_x + idx * 29, 10, 27, 28)
                if b_rect.collidepoint(mx, my):
                    if spd == 0.0:
                        sim.is_paused = not sim.is_paused
                    else:
                        sim.is_paused = False
                        sim.sim_speed = spd
                    return True

        return False

    def render(self, surface: pygame.Surface, sim: Simulation, camera: Camera):
        # Background bar
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, self.rect)
        pygame.draw.line(surface, UITheme.PANEL_BORDER, (0, self.rect.bottom - 1), (self.rect.width, self.rect.bottom - 1), 1)

        # 1. Circuit Name & Flag Status
        c_name = self.font_title.render(sim.circuit.name.upper(), True, UITheme.TEXT_WHITE)
        surface.blit(c_name, (14, 6))

        # Flag Status Badge
        flag_status = sim.race_control.flag
        if getattr(sim, "race_finished", False):
            f_str = "CHEQUERED"
            flag_col = UITheme.ACCENT_GOLD
        elif flag_status == FlagStatus.YELLOW and getattr(sim.race_control, "yellow_sector", None):
            f_str = f"SEC {sim.race_control.yellow_sector} YELLOW"
            flag_col = UITheme.ACCENT_YELLOW
        elif flag_status == FlagStatus.SAFETY_CAR:
            f_str = "SAFETY CAR"
            flag_col = UITheme.ACCENT_YELLOW
        elif flag_status == FlagStatus.VSC:
            f_str = "VSC"
            flag_col = UITheme.ACCENT_YELLOW
        elif flag_status == FlagStatus.GREEN:
            f_str = "GREEN"
            flag_col = UITheme.ACCENT_GREEN
        else:
            f_str = flag_status.value
            flag_col = UITheme.ACCENT_RED

        f_txt = self.font_flag.render(f_str, True, UITheme.TEXT_DARK)
        flag_w = max(75, f_txt.get_width() + 12)
        flag_rect = pygame.Rect(14, 26, flag_w, 16)
        pygame.draw.rect(surface, flag_col, flag_rect, border_radius=2)
        surface.blit(f_txt, (flag_rect.x + (flag_rect.width - f_txt.get_width()) // 2, flag_rect.y + 2))

        # 2. Lap Counter & Session Clock
        from .icons import UIIcons

        lap_ic = UIIcons.get_icon("flag", size=14, color=UITheme.ACCENT_YELLOW)
        surface.blit(lap_ic, (190, 8))
        lap_str = f"LAP {min(sim.total_laps, sim.current_lap)} / {sim.total_laps}"
        l_surf = self.font_lap.render(lap_str, True, UITheme.ACCENT_YELLOW)
        surface.blit(l_surf, (208, 6))

        clock_ic = UIIcons.get_icon("timer", size=12, color=UITheme.TEXT_MUTED)
        surface.blit(clock_ic, (190, 28))
        clock_str = sim.format_time(sim.race_time)
        c_surf = self.font_sub.render(clock_str, True, UITheme.TEXT_MUTED)
        surface.blit(c_surf, (206, 26))

        # Mouse position for hover states
        mx, my = pygame.mouse.get_pos()

        # 3. Weather Radar & Track Wetness (extends width without colliding into cam/speed buttons)
        radar_tier = 0
        radar_eq_lvl = 0
        if hasattr(sim, "team_facilities"):
            radar_tier = sim.team_facilities.get("track_weather_station", 0)
        if hasattr(sim, "team_equipment"):
            radar_eq_lvl = sim.team_equipment.get("eq_met_xband_doppler", 0)

        radar_bars_count = min(10, 6 + (radar_tier * 2) + radar_eq_lvl)
        max_weather_right = self.rect.width - 625
        w_x = 340
        w_width = min(max(170, max_weather_right - w_x), 20 + radar_bars_count * 28)
        w_rect = pygame.Rect(w_x, 6, w_width, 36)
        pygame.draw.rect(surface, (18, 22, 28), w_rect, border_radius=3)
        pygame.draw.rect(
            surface, UITheme.ACCENT_CYAN if radar_tier > 0 else UITheme.PANEL_BORDER, w_rect, width=1, border_radius=3
        )

        wet_pct = int(sim.weather.track_wetness * 100)
        wet_col = (60, 160, 240) if wet_pct > 15 else UITheme.TEXT_MUTED
        radar_tag = " [DOPPLER]" if radar_tier > 0 else ""

        w_icon_name = "cloud-rain" if wet_pct > 10 else "sun"
        w_icon_col = (60, 160, 240) if wet_pct > 10 else UITheme.ACCENT_YELLOW
        w_ic = UIIcons.get_icon(w_icon_name, size=13, color=w_icon_col)
        surface.blit(w_ic, (w_rect.x + 6, w_rect.y + 4))

        if getattr(sim.weather, "is_local_shower", False) and any(
            sim.weather.get_sector_wetness(s) > 0.05 for s in (1, 2, 3)
        ):
            s1 = int(sim.weather.get_sector_wetness(1) * 100)
            s2 = int(sim.weather.get_sector_wetness(2) * 100)
            s3 = int(sim.weather.get_sector_wetness(3) * 100)
            w_txt = self.font_sub.render(
                f"S1:{s1}% S2:{s2}% S3:{s3}% | {sim.weather.track_temp:04.1f}°C{radar_tag}", True, wet_col
            )
        else:
            w_txt = self.font_sub.render(f"{wet_pct}% Wet | {sim.weather.track_temp:04.1f}°C{radar_tag}", True, wet_col)
        surface.blit(w_txt, (w_rect.x + 22, w_rect.y + 4))

        # Mini forward forecast bars
        forecast_nodes = sim.weather.get_forecast_slice(
            sim.current_lap, window=radar_bars_count - 1, radar_tier=radar_tier, radar_eq_lvl=radar_eq_lvl
        )
        for f_idx, node in enumerate(forecast_nodes[:radar_bars_count]):
            bar_x = w_rect.x + 6 + f_idx * 28
            bar_y = w_rect.y + 19
            if bar_x + 26 > w_rect.right - 4:
                break
            bar_col = (
                (40, 140, 240)
                if node.rain_intensity > 0.3
                else ((100, 180, 255) if node.rain_intensity > 0.05 else (70, 75, 85))
            )
            pygame.draw.rect(surface, bar_col, (bar_x, bar_y, 25, 13), border_radius=2)
            l_num = UITheme.font_mini().render(f"L{node.lap}", True, UITheme.TEXT_WHITE)
            surface.blit(l_num, (bar_x + (25 - l_num.get_width()) // 2, bar_y + 1))

        # 4. Camera View Toggle button (Placed to the left of speed controls: width - 615)
        cam_btn = pygame.Rect(self.rect.width - 615, 10, 100, 28)
        cam_active = camera.mode == "FOLLOW_CAR"
        cam_label = "CAR" if cam_active else "TRACK"
        UITheme.draw_button(
            surface,
            cam_btn,
            cam_label,
            self.font_btn,
            is_active=cam_active,
            is_hover=cam_btn.collidepoint(mx, my),
            icon="camera",
        )

        # 5. Speed controls (Placed from width - 505 to width - 360, clear of nav tabs at width - 345)
        speeds = [
            (0.0, "", "pause"),
            (1.0, "", "play"),
            (2.0, "2x", "fast-forward"),
            (4.0, "4x", None),
            (8.0, "8x", None),
        ]
        speed_start_x = self.rect.width - 505
        for idx, (spd, lbl, ic) in enumerate(speeds):
            b_rect = pygame.Rect(speed_start_x + idx * 29, 10, 27, 28)
            is_active = sim.is_paused if spd == 0.0 else (not sim.is_paused and sim.sim_speed == spd)
            UITheme.draw_button(
                surface,
                b_rect,
                lbl,
                self.font_btn,
                is_active=is_active,
                is_hover=b_rect.collidepoint(mx, my),
                icon=ic,
                icon_size=12,
            )
