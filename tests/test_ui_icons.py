import pygame
import pytest

from src.ui.icons import UIIcons


@pytest.fixture(scope="session", autouse=True)
def init_pygame():
    pygame.init()
    pygame.display.set_mode((100, 100), pygame.HIDDEN)
    yield
    pygame.quit()


def test_ui_icons_get_icon():
    UIIcons.clear_cache()
    # Test common icons
    test_names = [
        "dashboard",
        "wrench",
        "user",
        "circle-dollar-sign",
        "trophy",
        "fuel",
        "zap",
        "shield",
        "flag",
        "timer",
        "cloud-rain",
        "sun",
        "camera",
        "check",
        "x",
    ]

    for name in test_names:
        surf = UIIcons.get_icon(name, size=20, color=(0, 220, 240))
        assert isinstance(surf, pygame.Surface)
        assert surf.get_width() == 20
        assert surf.get_height() == 20

    # Test alias resolution
    surf_alias = UIIcons.get_icon("cash", size=16, color=(0, 255, 0))
    assert surf_alias.get_size() == (16, 16)


def test_ui_icons_draw_methods():
    canvas = pygame.Surface((200, 100))
    font = pygame.font.Font(None, 16)

    # Draw icon directly
    r1 = UIIcons.draw_icon(canvas, "fuel", (10, 10), color=(255, 200, 0), size=18)
    assert r1.width == 18

    # Draw icon in rect
    rect_target = pygame.Rect(40, 10, 30, 30)
    r2 = UIIcons.draw_icon(canvas, "zap", rect_target, color=(0, 255, 0), size=16)
    assert r2.width == 16

    # Draw tyre
    r3 = UIIcons.draw_tyre(canvas, (10, 40), (255, 0, 0), size=16)
    assert r3.width == 16

    # Draw icon badge
    badge_rect = pygame.Rect(40, 50, 120, 24)
    UIIcons.draw_icon_badge(canvas, badge_rect, "fuel", "42.5 kg", font, text_color=(255, 255, 255))

