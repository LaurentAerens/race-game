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
        self.height = 52
        self.x = (screen_width - self.width) // 2
        self.y = 56  # Just below the top broadcast header

        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self._init_fonts()
        self.pulse_timer: float = 0.0

    def _init_fonts(self):
        self.font_speaker = UITheme.get_font(11, bold=True)
        self.font_text = UITheme.get_font(12, bold=True)

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

        from .icons import UIIcons

        # Category colors
        border_col = {
            "WEATHER": UITheme.ACCENT_CYAN,
            "TIRES": UITheme.ACCENT_YELLOW,
            "INCIDENT": UITheme.ACCENT_RED,
            "STRATEGY": UITheme.ACCENT_GREEN,
        }.get(msg.category, UITheme.ACCENT_CYAN)

        # Background card
        pygame.draw.rect(surface, UITheme.BG_DARK, self.rect, border_radius=6)
        pygame.draw.rect(surface, border_col, self.rect, width=2, border_radius=6)

        # Pulsing Radio Wave Indicator on left
        icon_x = self.rect.x + 18
        icon_y = self.rect.y + self.rect.height // 2
        pulse_r = 6 + int(math.sin(self.pulse_timer) * 2)
        pygame.draw.circle(surface, border_col, (icon_x, icon_y), max(4, pulse_r))
        pygame.draw.circle(surface, (255, 255, 255), (icon_x, icon_y), 3)

        # Vector Radio Icon & Speaker Tag
        rad_ic = UIIcons.get_icon("radio", size=13, color=border_col)
        surface.blit(rad_ic, (self.rect.x + 36, self.rect.y + 8))

        spk_surf = self.font_speaker.render(f"{msg.speaker.upper()}:", True, border_col)
        surface.blit(spk_surf, (self.rect.x + 54, self.rect.y + 7))

        # Message Text
        txt_surf = self.font_text.render(msg.text, True, UITheme.TEXT_WHITE)
        surface.blit(txt_surf, (self.rect.x + 36, self.rect.y + 27))
