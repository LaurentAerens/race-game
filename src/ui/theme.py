from typing import Dict, Optional, Tuple

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
        from .icons import UIIcons

        UIIcons.clear_cache()

    @classmethod
    def set_scale(cls, scale: float):
        """Sets the UI scale factor and clears cached fonts."""
        cls.UI_SCALE = max(0.80, min(2.0, scale))
        cls._font_cache.clear()
        from .icons import UIIcons

        UIIcons.clear_cache()

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
        icon: Optional[str] = None,
        icon_size: Optional[int] = None,
        bg_color: Optional[Tuple[int, int, int]] = None,
        border_color: Optional[Tuple[int, int, int]] = None,
        text_color: Optional[Tuple[int, int, int]] = None,
    ) -> bool:
        if is_disabled:
            bg = (18, 22, 28)
            resolved_text_col = (80, 90, 105)
            resolved_border_col = (30, 36, 45)
        elif is_active:
            bg = UITheme.BTN_ACTIVE
            resolved_text_col = UITheme.TEXT_DARK
            resolved_border_col = border_color or UITheme.BTN_BORDER
        elif is_hover:
            bg = UITheme.BTN_HOVER if bg_color is None else tuple(min(255, c + 20) for c in bg_color)
            resolved_text_col = text_color or UITheme.TEXT_WHITE
            resolved_border_col = border_color or UITheme.BTN_BORDER
        else:
            bg = bg_color if bg_color is not None else UITheme.BTN_BG
            resolved_text_col = text_color or UITheme.TEXT_WHITE
            resolved_border_col = border_color or UITheme.BTN_BORDER

        pygame.draw.rect(surface, bg, rect, border_radius=3)
        pygame.draw.rect(surface, resolved_border_col, rect, width=1, border_radius=3)

        from .icons import UIIcons

        if icon:
            ic_s = icon_size or max(12, rect.height - 10)
            ic_surf = UIIcons.get_icon(icon, size=ic_s, color=resolved_text_col)
            if text:
                txt_surf = font.render(text, True, resolved_text_col)
                gap = 5
                total_w = ic_surf.get_width() + gap + txt_surf.get_width()
                start_x = rect.x + (rect.width - total_w) // 2
                surface.blit(ic_surf, (start_x, rect.y + (rect.height - ic_surf.get_height()) // 2))
                surface.blit(
                    txt_surf, (start_x + ic_surf.get_width() + gap, rect.y + (rect.height - txt_surf.get_height()) // 2)
                )
            else:
                surface.blit(
                    ic_surf,
                    (
                        rect.x + (rect.width - ic_surf.get_width()) // 2,
                        rect.y + (rect.height - ic_surf.get_height()) // 2,
                    ),
                )
        else:
            txt_surf = font.render(text, True, resolved_text_col)
            surface.blit(
                txt_surf,
                (
                    rect.x + (rect.width - txt_surf.get_width()) // 2,
                    rect.y + (rect.height - txt_surf.get_height()) // 2,
                ),
            )
        return False

    @staticmethod
    def draw_icon(
        surface: pygame.Surface,
        name: str,
        rect_or_pos,
        color: Tuple[int, int, int] = (255, 255, 255),
        size: Optional[int] = None,
    ) -> pygame.Rect:
        from .icons import UIIcons

        return UIIcons.draw_icon(surface, name, rect_or_pos, color=color, size=size)

    @staticmethod
    def draw_tyre(
        surface: pygame.Surface,
        pos_or_rect,
        compound_color: Tuple[int, int, int],
        size: int = 16,
    ) -> pygame.Rect:
        from .icons import UIIcons

        return UIIcons.draw_tyre(surface, pos_or_rect, compound_color=compound_color, size=size)

    @staticmethod
    def draw_icon_badge(
        surface: pygame.Surface,
        rect: pygame.Rect,
        icon_name: str,
        text: str,
        font: pygame.font.Font,
        text_color: Tuple[int, int, int] = (255, 255, 255),
        icon_color: Optional[Tuple[int, int, int]] = None,
        bg_color: Optional[Tuple[int, int, int]] = (18, 22, 28),
        border_color: Optional[Tuple[int, int, int]] = (40, 46, 58),
        icon_size: Optional[int] = None,
        border_radius: int = 3,
    ):
        from .icons import UIIcons

        UIIcons.draw_icon_badge(
            surface,
            rect,
            icon_name,
            text,
            font,
            text_color=text_color,
            icon_color=icon_color,
            bg_color=bg_color,
            border_color=border_color,
            icon_size=icon_size,
            border_radius=border_radius,
        )

    @staticmethod
    def draw_stat_item(
        surface: pygame.Surface,
        x: int,
        y: int,
        icon_name: str,
        text: str,
        font: pygame.font.Font,
        text_color: Tuple[int, int, int] = (255, 255, 255),
        icon_color: Optional[Tuple[int, int, int]] = None,
        icon_size: int = 14,
        gap: int = 4,
    ) -> int:
        """
        Draws an inline [Icon] Text pair at (x, y) vertically centered.
        Returns the total horizontal width consumed (icon width + gap + text width).
        """
        from .icons import UIIcons

        i_col = icon_color or text_color
        icon_surf = UIIcons.get_icon(icon_name, size=icon_size, color=i_col)
        txt_surf = font.render(text, True, text_color)

        line_h = max(icon_surf.get_height(), txt_surf.get_height())
        iy = y + (line_h - icon_surf.get_height()) // 2
        ty = y + (line_h - txt_surf.get_height()) // 2

        surface.blit(icon_surf, (x, iy))
        surface.blit(txt_surf, (x + icon_surf.get_width() + gap, ty))
        return icon_surf.get_width() + gap + txt_surf.get_width()
