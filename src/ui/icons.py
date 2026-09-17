import io
import os
import re
from typing import Dict, Optional, Tuple, Union

import pygame


class UIIcons:
    """High-performance Lucide vector icon loader, rasterizer, and surface cache for Motorsport UI."""

    _raw_svg_cache: Dict[str, str] = {}
    _surface_cache: Dict[Tuple[str, int, Tuple[int, int, int]], pygame.Surface] = {}
    _icons_dir: Optional[str] = None

    ALIASES = {
        "dashboard": "layout-dashboard",
        "rnd": "wrench",
        "tech_tree": "network",
        "tree": "network",
        "driver": "user",
        "drivers": "user",
        "staff": "users",
        "personnel": "users",
        "cash": "circle-dollar-sign",
        "finances": "circle-dollar-sign",
        "money": "circle-dollar-sign",
        "net_up": "trending-up",
        "net_down": "trending-down",
        "standings": "trophy",
        "podium": "trophy",
        "clock": "timer",
        "time": "timer",
        "weather_rain": "cloud-rain",
        "rain": "cloud-rain",
        "weather_sun": "sun",
        "sun": "sun",
        "incident": "triangle-alert",
        "warning": "triangle-alert",
        "box": "octagon",
        "pit": "wrench",
        "tutorial": "help-circle",
        "editor": "wrench",
        "scout": "search",
        "objective": "target",
        "market": "briefcase",
        "academy": "graduation-cap",
        "options": "sliders",
        "brakes": "disc",
        "brake": "disc",
        "front_wing": "wind",
        "rear_wing": "flag",
        "floor": "layers",
        "suspension": "sliders",
        "engine": "cpu",
        "ers": "battery-charging",
        "battery": "battery-charging",
    }

    @classmethod
    def get_icons_dir(cls) -> str:
        if cls._icons_dir is None:
            # Locate data/icons relative to this file: ../../data/icons
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "icons"))
            if not os.path.exists(base_dir):
                # Fallback to current working directory
                base_dir = os.path.abspath(os.path.join("data", "icons"))
            cls._icons_dir = base_dir
        return cls._icons_dir

    @classmethod
    def resolve_name(cls, name: str) -> str:
        clean_name = name.lower().strip().replace(" ", "_")
        return cls.ALIASES.get(clean_name, clean_name.replace("_", "-"))

    @classmethod
    def load_svg_string(cls, icon_name: str) -> Optional[str]:
        icon_key = cls.resolve_name(icon_name)
        if icon_key in cls._raw_svg_cache:
            return cls._raw_svg_cache[icon_key]

        icons_dir = cls.get_icons_dir()
        file_path = os.path.join(icons_dir, f"{icon_key}.svg")

        if not os.path.exists(file_path):
            # Check without hyphen replacement
            file_path = os.path.join(icons_dir, f"{icon_name}.svg")
            if not os.path.exists(file_path):
                return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            cls._raw_svg_cache[icon_key] = content
            return content
        except Exception:
            return None

    @classmethod
    def get_icon(cls, name: str, size: int = 16, color: Tuple[int, int, int] = (255, 255, 255)) -> pygame.Surface:
        """
        Loads, rasterizes sharply at target DPI size, tints to theme color, and returns cached Surface.
        """
        resolved = cls.resolve_name(name)
        size = max(8, int(size))
        cache_key = (resolved, size, (color[0], color[1], color[2]))

        if cache_key in cls._surface_cache:
            return cls._surface_cache[cache_key]

        svg_text = cls.load_svg_string(resolved)
        if not svg_text:
            # Fallback surface
            fallback = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(fallback, color, (size // 2, size // 2), size // 2 - 1, width=1)
            cls._surface_cache[cache_key] = fallback
            return fallback

        try:
            # Vector-sharp resolution injection: update root <svg ...> tag dimensions without corrupting inner elements
            def _replace_root_svg(match):
                tag = match.group(0)
                tag = re.sub(r'(?<![-\w])width="[^"]*"', f'width="{size}"', tag)
                tag = re.sub(r'(?<![-\w])height="[^"]*"', f'height="{size}"', tag)
                tag = re.sub(r'(?<![-\w])stroke="[^"]*"', 'stroke="white"', tag)
                return tag

            modified = re.sub(r"<svg\b[^>]*>", _replace_root_svg, svg_text, count=1)

            surf = pygame.image.load(io.BytesIO(modified.encode("utf-8")), "icon.svg")
            if pygame.display.get_surface() is not None:
                surf = surf.convert_alpha()

            # Dynamic color tinting
            color_surf = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
            color_surf.fill((color[0], color[1], color[2], 255))
            surf.blit(color_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            cls._surface_cache[cache_key] = surf
            return surf
        except Exception:
            # Procedural fallback on unexpected format
            fallback = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(fallback, color, (size // 2, size // 2), size // 2 - 1, width=1)
            cls._surface_cache[cache_key] = fallback
            return fallback

    @classmethod
    def draw_icon(
        cls,
        surface: pygame.Surface,
        name: str,
        rect_or_pos: Union[pygame.Rect, Tuple[int, int]],
        color: Tuple[int, int, int] = (255, 255, 255),
        size: Optional[int] = None,
    ) -> pygame.Rect:
        """
        Draws an icon either centered in a pygame.Rect or positioned at (x, y).
        Returns the bounding Rect where the icon was drawn.
        """
        if isinstance(rect_or_pos, pygame.Rect):
            icon_size = size or min(rect_or_pos.width, rect_or_pos.height)
            icon_surf = cls.get_icon(name, size=icon_size, color=color)
            ix = rect_or_pos.x + (rect_or_pos.width - icon_surf.get_width()) // 2
            iy = rect_or_pos.y + (rect_or_pos.height - icon_surf.get_height()) // 2
            surface.blit(icon_surf, (ix, iy))
            return pygame.Rect(ix, iy, icon_surf.get_width(), icon_surf.get_height())
        else:
            icon_size = size or 16
            icon_surf = cls.get_icon(name, size=icon_size, color=color)
            surface.blit(icon_surf, rect_or_pos)
            return pygame.Rect(rect_or_pos[0], rect_or_pos[1], icon_surf.get_width(), icon_surf.get_height())

    @classmethod
    def draw_tyre(
        cls,
        surface: pygame.Surface,
        pos_or_rect: Union[pygame.Rect, Tuple[int, int]],
        compound_color: Tuple[int, int, int],
        size: int = 16,
    ) -> pygame.Rect:
        """Draws a sharp F1 tyre wheel with outer rubber and compound-colored tread ring."""
        if isinstance(pos_or_rect, pygame.Rect):
            cx = pos_or_rect.x + pos_or_rect.width // 2
            cy = pos_or_rect.y + pos_or_rect.height // 2
            r = min(pos_or_rect.width, pos_or_rect.height) // 2
        else:
            r = size // 2
            cx = pos_or_rect[0] + r
            cy = pos_or_rect[1] + r

        # Outer rubber
        pygame.draw.circle(surface, (45, 50, 60), (cx, cy), r)
        # Compound color ring
        pygame.draw.circle(surface, compound_color, (cx, cy), max(2, int(r * 0.8)), width=max(1, int(r * 0.3)))
        # Hub
        pygame.draw.circle(surface, (18, 22, 28), (cx, cy), max(1, int(r * 0.4)))
        return pygame.Rect(cx - r, cy - r, r * 2, r * 2)

    @classmethod
    def draw_icon_badge(
        cls,
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
        """Draws a modern telemetry pill badge: [Icon] Value."""
        if bg_color:
            pygame.draw.rect(surface, bg_color, rect, border_radius=border_radius)
        if border_color:
            pygame.draw.rect(surface, border_color, rect, width=1, border_radius=border_radius)

        i_size = icon_size or (rect.height - 8)
        i_col = icon_color or text_color
        icon_surf = cls.get_icon(icon_name, size=i_size, color=i_col)

        txt_surf = font.render(text, True, text_color)

        gap = 6
        total_content_w = icon_surf.get_width() + gap + txt_surf.get_width()
        start_x = rect.x + max(4, (rect.width - total_content_w) // 2)
        iy = rect.y + (rect.height - icon_surf.get_height()) // 2
        ty = rect.y + (rect.height - txt_surf.get_height()) // 2

        surface.blit(icon_surf, (start_x, iy))
        surface.blit(txt_surf, (start_x + icon_surf.get_width() + gap, ty))

    @classmethod
    def clear_cache(cls):
        """Clears cached surfaces on scale/resolution changes."""
        cls._surface_cache.clear()
