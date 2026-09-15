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


def test_ui_modules_import_and_components():
    from src.ui.broadcast_header import BroadcastHeader
    from src.ui.driver_panel import DriverStrategyPanel
    from src.ui.management_hub.management_hub import ManagementHub
    from src.ui.start_screen import StartScreen
    from src.ui.theme import UITheme
    from src.ui.timing_tower import TimingTower

    assert ManagementHub is not None

    surface = pygame.Surface((1280, 720))
    btn_rect = pygame.Rect(10, 10, 120, 30)
    font = UITheme.get_font(12)

    # Test button drawing with icon
    r = UITheme.draw_button(surface, btn_rect, "TEST BTN", font, icon="wrench", icon_size=14)
    assert isinstance(r, bool)

    # Test icon drawing with UITheme
    r_ic = UITheme.draw_icon(surface, "trophy", (50, 50), color=(255, 215, 0), size=16)
    assert r_ic.width == 16

    # Test stat item drawing with UITheme
    stat_w = UITheme.draw_stat_item(surface, 10, 50, "zap", "850 HP", font, text_color=(255, 255, 255))
    assert stat_w > 0

    # Test initializing UI components
    b_header = BroadcastHeader(1280, 48)
    assert b_header.rect.width == 1280

    t_tower = TimingTower(0, 48, 280, 620)
    assert t_tower.rect.height == 620

    d_panel = DriverStrategyPanel(280, 600, 720, 120, lambda car: None)
    assert d_panel.rect.width == 720

    start_screen = StartScreen(1280, 720, lambda: None, lambda: None, lambda: None)
    assert start_screen.width == 1280
    start_screen.render(surface)
    start_screen.is_new_game_mode = True
    start_screen.render(surface)
