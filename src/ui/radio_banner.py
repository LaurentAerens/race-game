import math
from typing import Optional

import pygame

from ..core.radio_system import RadioMessage, RadioMessageSystem
from .theme import UITheme


class RadioBannerWidget:
    """
    Renders top-center broadcast Pit Wall Radio popups with pulsating radio icons,
    speaker labels, and high-priority alert highlights.
    """

    def __init__(self, screen_width: int):
        self.width = 540
        self.height = 46
        self.x = (screen_width - self.width) // 2
        self.y = 56  # Just below the top broadcast header

        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self._init_fonts()
        self.pulse_timer: float = 0.0

    def _init_fonts(self):
        self.font_speaker = UITheme.get_font(12, bold=True)
        self.font_text = UITheme.get_font(13, bold=True)

    def resize(self, screen_width: int):
        self.x = (screen_width - self.width) // 2
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self._init_fonts()

    def update(self, dt: float, screen_width: int):
        self.x = (screen_width - self.width) // 2
        self.rect.x = self.x
        self.pulse_timer += dt * 6.0

    def render(self, surface: pygame.Surface, radio_system: RadioMessageSystem):
        msg: Optional[RadioMessage] = radio_system.active_message
        if not msg:
            return

        # Category colors
        border_col = {
            "WEATHER": (0, 210, 255),  # Cyan for rain/weather
            "TIRES": (255, 205, 30),  # Yellow for tire alerts
            "INCIDENT": (245, 45, 45),  # Red for safety car/crashes
            "STRATEGY": (0, 240, 140),  # Green for pit strategy
        }.get(msg.category, UITheme.ACCENT_CYAN)

        # Background card with slight shadow
        pygame.draw.rect(surface, (15, 18, 24), self.rect, border_radius=6)
        pygame.draw.rect(surface, border_col, self.rect, width=2, border_radius=6)

        # Pulsing Radio Wave Icon on left
        icon_x = self.rect.x + 22
        icon_y = self.rect.y + self.rect.height // 2
        pulse_r = 5 + int(math.sin(self.pulse_timer) * 2)
        pygame.draw.circle(surface, border_col, (icon_x, icon_y), max(2, pulse_r))
        pygame.draw.circle(surface, (255, 255, 255), (icon_x, icon_y), 3)

        # Speaker Tag (e.g. "PIT WALL", "RACE ENGINEER", "DRIVER")
        spk_surf = self.font_speaker.render(f"📻 {msg.speaker.upper()}:", True, border_col)
        surface.blit(spk_surf, (self.rect.x + 40, self.rect.y + 6))

        # Message Text
        txt_surf = self.font_text.render(msg.text, True, (250, 250, 250))
        surface.blit(txt_surf, (self.rect.x + 40, self.rect.y + 22))
