from typing import Dict, Tuple

import pygame


class UITheme:
    """F1 / Motorsport Manager Broadcast dark color palette & dynamic font scaling engine."""

    BG_DARK = (15, 17, 22)
    PANEL_BG = (22, 26, 34)
    PANEL_BORDER = (40, 46, 58)
    PANEL_HEADER = (30, 35, 45)

    TEXT_WHITE = (245, 248, 252)
    TEXT_MUTED = (145, 155, 170)
    TEXT_DARK = (20, 24, 30)

    ACCENT_CYAN = (0, 220, 240)
    ACCENT_PURPLE = (180, 80, 240)  # Fastest lap purple
    ACCENT_GREEN = (0, 230, 110)  # Personal best / Sector green
    ACCENT_YELLOW = (255, 205, 30)  # Caution / Sector yellow
    ACCENT_RED = (240, 45, 45)  # Warning / Soft tire

    BTN_BG = (35, 42, 54)
    BTN_HOVER = (50, 60, 78)
    BTN_ACTIVE = (0, 180, 210)
    BTN_BORDER = (60, 70, 90)

    # Global UI & Font Scale Factor
    UI_SCALE: float = 1.0
    _font_cache: Dict[Tuple[str, int, bool], pygame.font.Font] = {}

    @classmethod
    def auto_detect_scale(cls, screen_width: int, screen_height: int):
        """
        Automatically selects balanced UI scaling based on screen size.
        Guarantees clear, comfortable readability on compact laptop screens and ultrawide displays alike.
        """
        if screen_height >= 2000:
            cls.UI_SCALE = 1.35  # 4K / 5K UHD Vertical (2160p)
        elif screen_height >= 1300:
            cls.UI_SCALE = 1.15  # 1440p / 5K Ultrawide (5120x1440 / 3440x1440)
        elif screen_height >= 850:
            cls.UI_SCALE = 1.05  # 1080p FHD & Standard Laptop Screens
        else:
            cls.UI_SCALE = 1.00  # 720p / 768p Compact Laptops
        cls._font_cache.clear()

    @classmethod
    def set_scale(cls, scale: float):
        """Sets the UI scale factor and clears cached fonts."""
        cls.UI_SCALE = max(0.80, min(2.0, scale))
        cls._font_cache.clear()

    @classmethod
    def adjust_scale(cls, delta: float):
        """Adjusts the UI scale factor by delta (+0.10 / -0.10)."""
        cls.set_scale(round(cls.UI_SCALE + delta, 2))

    @classmethod
    def get_font(
        cls, base_size: int, bold: bool = False, font_name: str = "Segoe UI Emoji,Segoe UI Symbol,Segoe UI,Arial"
    ) -> pygame.font.Font:
        """
        Returns a crisply rendered, DPI-scaled font supporting full Unicode emojis (⭐, 🔍, 🏎️, etc.).
        Enforces a minimum legible font floor (11pt body / 10pt badge) so small laptop screens remain easily readable.
        """
        min_size = 11 if bold or base_size >= 11 else 10
        scaled_size = max(min_size, int(round(base_size * cls.UI_SCALE)))
        key = (font_name, scaled_size, bold)

        if key not in cls._font_cache:
            try:
                cls._font_cache[key] = pygame.font.SysFont(font_name, scaled_size, bold=bold)
            except Exception:
                try:
                    cls._font_cache[key] = pygame.font.SysFont("Arial", scaled_size, bold=bold)
                except Exception:
                    cls._font_cache[key] = pygame.font.Font(None, scaled_size)

        return cls._font_cache[key]

    # Pre-defined semantic font getters
    @classmethod
    def font_logo(cls) -> pygame.font.Font:
        return cls.get_font(24, bold=True)

    @classmethod
    def font_title(cls) -> pygame.font.Font:
        return cls.get_font(13, bold=True)

    @classmethod
    def font_card_title(cls) -> pygame.font.Font:
        return cls.get_font(12, bold=True)

    @classmethod
    def font_body(cls) -> pygame.font.Font:
        return cls.get_font(11, bold=False)

    @classmethod
    def font_badge(cls) -> pygame.font.Font:
        return cls.get_font(10, bold=True)

    @classmethod
    def font_btn(cls) -> pygame.font.Font:
        return cls.get_font(11, bold=True)

    @classmethod
    def font_sub(cls) -> pygame.font.Font:
        return cls.get_font(11, bold=False)

    @staticmethod
    def draw_panel(surface: pygame.Surface, rect: pygame.Rect, border_radius: int = 4):
        pygame.draw.rect(surface, UITheme.PANEL_BG, rect, border_radius=border_radius)
        pygame.draw.rect(surface, UITheme.PANEL_BORDER, rect, width=1, border_radius=border_radius)

    @staticmethod
    def draw_button(
        surface: pygame.Surface,
        rect: pygame.Rect,
        text: str,
        font: pygame.font.Font,
        is_active: bool = False,
        is_hover: bool = False,
        is_disabled: bool = False,
    ) -> bool:
        if is_disabled:
            bg = (18, 22, 28)
            text_color = (80, 90, 105)
            border_color = (30, 36, 45)
        else:
            bg = UITheme.BTN_ACTIVE if is_active else (UITheme.BTN_HOVER if is_hover else UITheme.BTN_BG)
            text_color = UITheme.TEXT_DARK if is_active else UITheme.TEXT_WHITE
            border_color = UITheme.BTN_BORDER

        pygame.draw.rect(surface, bg, rect, border_radius=3)
        pygame.draw.rect(surface, border_color, rect, width=1, border_radius=3)

        txt_surf = font.render(text, True, text_color)
        surface.blit(
            txt_surf,
            (rect.x + (rect.width - txt_surf.get_width()) // 2, rect.y + (rect.height - txt_surf.get_height()) // 2),
        )
