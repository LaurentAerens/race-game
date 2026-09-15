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

        # Header
        hdr_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, 22)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, hdr_rect, border_top_left_radius=4, border_top_right_radius=4)
        h_txt = self.font_title.render("RACE RADIO & EVENTS", True, UITheme.TEXT_MUTED)
        surface.blit(h_txt, (self.rect.x + 8, self.rect.y + 4))

        # Items
        old_clip = surface.get_clip()
        surface.set_clip(self.rect)
        try:
            curr_y = self.rect.y + 26
            for item in sim.event_log[:6]:
                e_type = item.get("type", "INFO")
                tag_col = {
                    "OVERTAKE": UITheme.ACCENT_CYAN,
                    "FASTEST": UITheme.ACCENT_PURPLE,
                    "START": UITheme.ACCENT_GREEN,
                    "WIN": UITheme.ACCENT_YELLOW,
                    "INCIDENT": UITheme.ACCENT_RED,
                }.get(e_type, UITheme.TEXT_WHITE)

                # Draw colored dot
                pygame.draw.circle(surface, tag_col, (self.rect.x + 12, curr_y + 8), 3)

                # Event text
                txt = f"[L{item.get('lap', 1)}] {item.get('text', '')}"
                txt_surf = self.font_item.render(txt, True, UITheme.TEXT_WHITE)
                surface.blit(txt_surf, (self.rect.x + 22, curr_y + 2))

                curr_y += 18
                if curr_y > self.rect.bottom - 16:
                    break
        finally:
            surface.set_clip(old_clip)
