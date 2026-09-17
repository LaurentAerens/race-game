import pygame

from ..core.simulation import Simulation
from .theme import UITheme


class EventFeed:
    """Bottom-right live commentary and team radio ticker."""

    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self._init_fonts()

    def _init_fonts(self):
        self.font_title = UITheme.get_font(12, bold=True)
        self.font_item = UITheme.get_font(11, bold=False)

    def resize(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self._init_fonts()

    def render(self, surface: pygame.Surface, sim: Simulation):
        UITheme.draw_panel(surface, self.rect)

        # Standardized Header
        hdr_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, 24)
        UITheme.draw_card_header(
            surface,
            hdr_rect,
            "RACE RADIO & EVENTS",
            icon="radio",
            icon_color=UITheme.ACCENT_CYAN,
            title_color=UITheme.TEXT_WHITE,
            border_radius=4,
        )

        from .icons import UIIcons

        # Items
        old_clip = surface.get_clip()
        surface.set_clip(self.rect)
        try:
            line_h = max(20, int(round(20 * UITheme.UI_SCALE)))
            curr_y = self.rect.y + 28
            for item in sim.event_log[:6]:
                e_type = item.get("type", "INFO")
                tag_col = {
                    "OVERTAKE": UITheme.ACCENT_CYAN,
                    "FASTEST": UITheme.ACCENT_PURPLE,
                    "START": UITheme.ACCENT_GREEN,
                    "WIN": UITheme.ACCENT_YELLOW,
                    "INCIDENT": UITheme.ACCENT_RED,
                }.get(e_type, UITheme.TEXT_WHITE)

                icon_name = {
                    "OVERTAKE": "swords",
                    "FASTEST": "zap",
                    "START": "flag",
                    "WIN": "trophy",
                    "INCIDENT": "triangle-alert",
                }.get(e_type, "radio")

                # Clean standalone Lucide icon
                ic_surf = UIIcons.get_icon(icon_name, size=12, color=tag_col)
                surface.blit(ic_surf, (self.rect.x + 8, curr_y + (line_h - ic_surf.get_height()) // 2))

                # Event text (clean single-pass blit)
                txt = f"[L{item.get('lap', 1)}] {item.get('text', '')}"
                txt_surf = self.font_item.render(txt, True, UITheme.TEXT_WHITE)
                surface.blit(txt_surf, (self.rect.x + 26, curr_y + (line_h - txt_surf.get_height()) // 2))

                curr_y += line_h
                if curr_y > self.rect.bottom - 16:
                    break
        finally:
            surface.set_clip(old_clip)
