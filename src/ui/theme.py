import math
from typing import Dict, List, Optional, Tuple

import pygame


class UITheme:
    """F1 / Motorsport Manager Broadcast dark color palette & dynamic font scaling engine."""

    # Surfaces & Backgrounds
    BG_DARK = (15, 17, 22)
    PANEL_BG = (22, 26, 34)
    PANEL_BORDER = (40, 46, 58)
    PANEL_HEADER = (30, 35, 45)
    SURFACE_CARD = (20, 25, 34)
    SURFACE_ELEVATED = (28, 35, 48)
    SURFACE_INPUT = (16, 20, 28)
    SURFACE_HOVER = (35, 45, 60)
    BORDER_SUBTLE = (38, 46, 60)

    # Typography / Texts
    TEXT_WHITE = (245, 248, 252)
    TEXT_MUTED = (145, 155, 170)
    TEXT_DARK = (20, 24, 30)

    # Motorsport Accents & Badges
    ACCENT_CYAN = (0, 220, 240)
    ACCENT_PURPLE = (180, 80, 240)  # Fastest lap purple / Sector 3
    ACCENT_GREEN = (0, 230, 110)  # Personal best / Sector green
    ACCENT_YELLOW = (255, 205, 30)  # Caution / Sector yellow
    ACCENT_RED = (240, 45, 45)  # Warning / Soft tire
    ACCENT_GOLD = (255, 215, 0)  # Championship / Title partner

    # Semantic Status
    SUCCESS_GREEN = (0, 230, 120)
    WARNING_AMBER = (255, 195, 30)
    DANGER_RED = (245, 55, 55)

    # Buttons
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
        if base_size <= 9:
            min_size = 9
        elif base_size == 10:
            min_size = 10
        else:
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
    def font_mini(cls) -> pygame.font.Font:
        return cls.get_font(9, bold=True)

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
    def draw_card_header(
        surface: pygame.Surface,
        rect: pygame.Rect,
        title: str,
        font: Optional[pygame.font.Font] = None,
        icon: Optional[str] = None,
        icon_color: Optional[Tuple[int, int, int]] = None,
        title_color: Optional[Tuple[int, int, int]] = None,
        bg_color: Optional[Tuple[int, int, int]] = None,
        border_radius: int = 4,
    ) -> pygame.Rect:
        """Standardized card/panel header bar with top rounded corners, Lucide icon, and title."""
        hdr_bg = bg_color or UITheme.PANEL_HEADER
        pygame.draw.rect(
            surface,
            hdr_bg,
            rect,
            border_top_left_radius=border_radius,
            border_top_right_radius=border_radius,
        )
        t_col = title_color or UITheme.ACCENT_CYAN
        f = font or UITheme.font_title()

        from .icons import UIIcons

        text_x = rect.x + 12
        if icon:
            i_col = icon_color or t_col
            ic_size = max(12, rect.height - 14)
            ic_surf = UIIcons.get_icon(icon, size=ic_size, color=i_col)
            surface.blit(ic_surf, (text_x, rect.y + (rect.height - ic_surf.get_height()) // 2))
            text_x += ic_surf.get_width() + 7

        txt_surf = f.render(title, True, t_col)
        surface.blit(txt_surf, (text_x, rect.y + (rect.height - txt_surf.get_height()) // 2))
        return rect

    @staticmethod
    def draw_pill_badge(
        surface: pygame.Surface,
        rect: pygame.Rect,
        text: str,
        font: Optional[pygame.font.Font] = None,
        icon: Optional[str] = None,
        fg_color: Tuple[int, int, int] = (245, 248, 252),
        bg_color: Tuple[int, int, int] = (20, 26, 36),
        border_color: Optional[Tuple[int, int, int]] = None,
        border_radius: int = 3,
    ) -> pygame.Rect:
        """Standardized pill badge with optional Lucide icon."""
        brd_col = border_color or fg_color
        pygame.draw.rect(surface, bg_color, rect, border_radius=border_radius)
        pygame.draw.rect(surface, brd_col, rect, width=1, border_radius=border_radius)

        f = font or UITheme.font_badge()
        from .icons import UIIcons

        if icon:
            ic_s = max(10, rect.height - 8)
            ic_surf = UIIcons.get_icon(icon, size=ic_s, color=fg_color)
            txt_surf = f.render(text, True, fg_color)
            total_w = ic_surf.get_width() + 4 + txt_surf.get_width()
            start_x = rect.x + (rect.width - total_w) // 2
            surface.blit(ic_surf, (start_x, rect.y + (rect.height - ic_surf.get_height()) // 2))
            surface.blit(
                txt_surf, (start_x + ic_surf.get_width() + 4, rect.y + (rect.height - txt_surf.get_height()) // 2)
            )
        else:
            txt_surf = f.render(text, True, fg_color)
            surface.blit(
                txt_surf,
                (
                    rect.x + (rect.width - txt_surf.get_width()) // 2,
                    rect.y + (rect.height - txt_surf.get_height()) // 2,
                ),
            )
        return rect

    @staticmethod
    def draw_progress_bar(
        surface: pygame.Surface,
        rect: pygame.Rect,
        pct: float,
        fill_color: Tuple[int, int, int],
        bg_color: Tuple[int, int, int] = (14, 18, 24),
        border_color: Tuple[int, int, int] = (38, 48, 62),
        border_radius: int = 3,
        ticks: Optional[int] = None,
    ):
        """Standardized progress meter with track, filled portion, border, and optional milestone ticks."""
        pygame.draw.rect(surface, bg_color, rect, border_radius=border_radius)
        clamped_pct = max(0.0, min(1.0, pct))
        fill_w = int((rect.width - 2) * clamped_pct)
        if fill_w > 0:
            fill_rect = pygame.Rect(rect.x + 1, rect.y + 1, fill_w, rect.height - 2)
            pygame.draw.rect(surface, fill_color, fill_rect, border_radius=max(1, border_radius - 1))

        if ticks and ticks > 1:
            for i in range(1, ticks):
                tx = rect.x + int(rect.width * (i / ticks))
                pygame.draw.line(surface, (50, 62, 80), (tx, rect.y), (tx, rect.bottom - 1), 1)

        pygame.draw.rect(surface, border_color, rect, width=1, border_radius=border_radius)

    @staticmethod
    def draw_modal_backdrop(surface: pygame.Surface, alpha: int = 190):
        """Standardized dimmed modal backdrop."""
        w, h = surface.get_size()
        dim_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        dim_surf.fill((0, 0, 0, alpha))
        surface.blit(dim_surf, (0, 0))

    @staticmethod
    def draw_info_icon(
        surface: pygame.Surface,
        rect: pygame.Rect,
        is_hover: bool = False,
        icon: str = "help-circle",
        color: Optional[Tuple[int, int, int]] = None,
        bg_color: Optional[Tuple[int, int, int]] = None,
        border_color: Optional[Tuple[int, int, int]] = None,
    ):
        """Draws an interactive info/help button with hover glow feedback."""
        resolved_col = color or (UITheme.ACCENT_CYAN if is_hover else (140, 160, 185))
        resolved_bg = bg_color or ((30, 45, 65) if is_hover else (20, 26, 36))
        resolved_border = border_color or (UITheme.ACCENT_CYAN if is_hover else (45, 55, 72))

        pygame.draw.rect(surface, resolved_bg, rect, border_radius=3)
        pygame.draw.rect(surface, resolved_border, rect, width=1, border_radius=3)
        ic_size = max(10, min(rect.width, rect.height) - 6)
        ix = rect.x + (rect.width - ic_size) // 2
        iy = rect.y + (rect.height - ic_size) // 2
        UITheme.draw_icon(surface, icon, (ix, iy), color=resolved_col, size=ic_size)

    @staticmethod
    def draw_tooltip(
        surface: pygame.Surface,
        text: str,
        pos: Tuple[int, int],
        font: Optional[pygame.font.Font] = None,
        title: Optional[str] = None,
        icon: Optional[str] = None,
        fg_color: Tuple[int, int, int] = (245, 248, 252),
        bg_color: Tuple[int, int, int] = (20, 26, 36),
        border_color: Tuple[int, int, int] = (0, 220, 255),
        title_color: Tuple[int, int, int] = (0, 220, 255),
        max_width: int = 340,
    ):
        """Draws floating multiline tooltip with optional header, icon, and boundary clamping."""
        f_body = font or UITheme.font_badge()
        f_title = UITheme.font_card_title()
        pad_x, pad_y = 10, 8

        # 1. Word-wrap body text
        wrapped_lines: List[str] = []
        raw_lines = text.split("\n")
        avail_body_w = max(120, max_width - pad_x * 2)

        for r_line in raw_lines:
            words = r_line.split(" ")
            if not words or not r_line.strip():
                wrapped_lines.append("")
                continue
            cur_line = ""
            for w in words:
                test_line = f"{cur_line} {w}".strip() if cur_line else w
                if f_body.size(test_line)[0] <= avail_body_w:
                    cur_line = test_line
                else:
                    if cur_line:
                        wrapped_lines.append(cur_line)
                    cur_line = w
            if cur_line:
                wrapped_lines.append(cur_line)

        # 2. Compute bounding size
        line_h = f_body.get_linesize()
        body_w = max([f_body.size(l)[0] for l in wrapped_lines] + [80]) if wrapped_lines else 80
        body_h = len(wrapped_lines) * line_h

        header_h = 0
        header_w = 0
        if title:
            t_surf_w = f_title.size(title)[0]
            header_w = t_surf_w + (20 if icon else 0)
            header_h = f_title.get_linesize() + 6

        tip_w = max(body_w, header_w) + pad_x * 2
        tip_h = header_h + body_h + pad_y * 2

        mx, my = pos
        tx = max(4, min(surface.get_width() - tip_w - 4, mx + 12))
        ty = max(4, min(surface.get_height() - tip_h - 4, my - tip_h - 4 if my > tip_h + 8 else my + 20))

        # Drop shadow
        shadow_rect = pygame.Rect(tx + 2, ty + 2, tip_w, tip_h)
        shadow_surf = pygame.Surface((tip_w, tip_h), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 90))
        surface.blit(shadow_surf, (tx + 2, ty + 2))

        # Tooltip body box
        tip_rect = pygame.Rect(tx, ty, tip_w, tip_h)
        pygame.draw.rect(surface, bg_color, tip_rect, border_radius=4)
        pygame.draw.rect(surface, border_color, tip_rect, width=1, border_radius=4)

        cur_y = ty + pad_y
        if title:
            hx = tx + pad_x
            if icon:
                UITheme.draw_icon(surface, icon, (hx, cur_y + 1), color=title_color, size=13)
                hx += 18
            surface.blit(f_title.render(title, True, title_color), (hx, cur_y))
            cur_y += f_title.get_linesize() + 4
            pygame.draw.line(surface, (45, 58, 75), (tx + pad_x, cur_y - 2), (tx + tip_w - pad_x, cur_y - 2), 1)
            cur_y += 2

        for l in wrapped_lines:
            if l:
                surface.blit(f_body.render(l, True, fg_color), (tx + pad_x, cur_y))
            cur_y += line_h

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

    @staticmethod
    def draw_radar_chart(
        surface: pygame.Surface,
        center: Tuple[int, int],
        radius: int,
        attributes: List[str],
        values_1: List[float],
        values_2: Optional[List[float]] = None,
        label_1: str = "Driver 1",
        label_2: Optional[str] = None,
        color_1: Tuple[int, int, int] = (0, 220, 240),
        color_2: Tuple[int, int, int] = (255, 205, 30),
        font: Optional[pygame.font.Font] = None,
        show_labels: bool = True,
        max_value: float = 100.0,
    ):
        """
        Renders a radar (spider) chart for driver talent comparison.
        Draws concentric webs, attribute radial axes, semi-transparent filled polygons,
        vertex indicator pips, and legend.
        """
        cx, cy = center
        n = len(attributes)
        if n < 3:
            return

        lbl_font = font or UITheme.get_font(9, bold=True)
        angles = [(-math.pi / 2) + (2 * math.pi * i / n) for i in range(n)]

        # 1. Concentric Grid Webs (25%, 50%, 75%, 100%)
        for ring_pct in [0.25, 0.50, 0.75, 1.0]:
            ring_r = radius * ring_pct
            ring_pts = [(int(cx + ring_r * math.cos(ang)), int(cy + ring_r * math.sin(ang))) for ang in angles]
            ring_col = (45, 55, 70) if ring_pct == 1.0 else (30, 36, 48)
            pygame.draw.polygon(surface, ring_col, ring_pts, width=1)

        # 2. Radial Spoke Lines from Center to Web Perimeters
        for ang in angles:
            ox = int(cx + radius * math.cos(ang))
            oy = int(cy + radius * math.sin(ang))
            pygame.draw.line(surface, (38, 46, 60), (cx, cy), (ox, oy), 1)

        # 3. Attribute Labels on Outer Web
        if show_labels:
            for label, ang in zip(attributes, angles):
                lx = cx + (radius + 14) * math.cos(ang)
                ly = cy + (radius + 14) * math.sin(ang)
                txt = lbl_font.render(label, True, UITheme.TEXT_MUTED)
                surface.blit(txt, (int(lx - txt.get_width() / 2), int(ly - txt.get_height() / 2)))

        # Bounding box for alpha polygon rendering
        pad = radius + 30
        poly_surf = pygame.Surface((pad * 2, pad * 2), pygame.SRCALPHA)
        local_cx, local_cy = pad, pad

        # 4. Driver 1 Polygon
        norm_v1 = [max(0.05, min(1.0, v / max_value)) for v in values_1]
        pts_1 = [
            (int(cx + radius * nv * math.cos(ang)), int(cy + radius * nv * math.sin(ang)))
            for nv, ang in zip(norm_v1, angles)
        ]
        local_pts_1 = [
            (int(local_cx + radius * nv * math.cos(ang)), int(local_cy + radius * nv * math.sin(ang)))
            for nv, ang in zip(norm_v1, angles)
        ]
        pygame.draw.polygon(poly_surf, (color_1[0], color_1[1], color_1[2], 75), local_pts_1)
        pygame.draw.polygon(surface, color_1, pts_1, width=2)
        for p in pts_1:
            pygame.draw.circle(surface, color_1, p, 3)

        # 5. Driver 2 Polygon (Optional Comparison Overlay)
        if values_2:
            norm_v2 = [max(0.05, min(1.0, v / max_value)) for v in values_2]
            pts_2 = [
                (int(cx + radius * nv * math.cos(ang)), int(cy + radius * nv * math.sin(ang)))
                for nv, ang in zip(norm_v2, angles)
            ]
            local_pts_2 = [
                (int(local_cx + radius * nv * math.cos(ang)), int(local_cy + radius * nv * math.sin(ang)))
                for nv, ang in zip(norm_v2, angles)
            ]
            pygame.draw.polygon(poly_surf, (color_2[0], color_2[1], color_2[2], 75), local_pts_2)
            pygame.draw.polygon(surface, color_2, pts_2, width=2)
            for p in pts_2:
                pygame.draw.circle(surface, color_2, p, 3)

        # Blit alpha polygons onto main surface
        surface.blit(poly_surf, (cx - pad, cy - pad))

        # 6. Mini Legend
        leg_y = cy + radius + 22
        leg_font = UITheme.get_font(9, bold=True)
        if label_1:
            t1 = leg_font.render(f"■ {label_1}", True, color_1)
            if values_2 and label_2:
                t2 = leg_font.render(f"■ {label_2}", True, color_2)
                total_w = t1.get_width() + 16 + t2.get_width()
                start_x = int(cx - total_w / 2)
                surface.blit(t1, (start_x, leg_y))
                surface.blit(t2, (start_x + t1.get_width() + 16, leg_y))
            else:
                surface.blit(t1, (int(cx - t1.get_width() / 2), leg_y))
