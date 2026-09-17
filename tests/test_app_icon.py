import os
import unittest
from unittest.mock import patch

import pygame
from PIL import Image

from main import RaceGameApp


class TestAppIcon(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.data_dir = os.path.join(cls.project_root, "data")
        cls.png_path = os.path.join(cls.data_dir, "app_icon.png")
        cls.ico_path = os.path.join(cls.data_dir, "app_icon.ico")
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_icon_files_exist(self):
        """Verify that both PNG and ICO icon assets exist on disk and are non-empty."""
        self.assertTrue(os.path.exists(self.png_path), f"Missing {self.png_path}")
        self.assertTrue(os.path.exists(self.ico_path), f"Missing {self.ico_path}")
        self.assertGreater(os.path.getsize(self.png_path), 1000)
        self.assertGreater(os.path.getsize(self.ico_path), 1000)

    def test_png_icon_properties(self):
        """Verify the PNG icon is high-res RGBA and has transparent squircle corners."""
        with Image.open(self.png_path) as img:
            self.assertEqual(img.size, (512, 512))
            self.assertEqual(img.mode, "RGBA")
            # The corner pixel at (0, 0) should be transparent (alpha == 0)
            corner_pixel = img.getpixel((0, 0))
            self.assertEqual(corner_pixel[3], 0, "Outer corner pixel must be transparent")
            # The center of the image should be fully opaque
            center_pixel = img.getpixel((256, 256))
            self.assertEqual(center_pixel[3], 255, "Center of icon badge must be opaque")

    def test_ico_icon_resolutions(self):
        """Verify that the ICO contains standard multi-resolution layers."""
        with Image.open(self.ico_path) as ico:
            # Pillow exposes icon sizes via ico.info['sizes'] or frame inspection
            sizes = ico.info.get("sizes", set())
            expected_sizes = {(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)}
            for expected in expected_sizes:
                self.assertIn(expected, sizes, f"Expected size {expected} not found in ICO layers: {sizes}")

    def test_pygame_can_load_png_icon(self):
        """Verify that pygame.image.load loads the icon into a valid Pygame surface."""
        surf = pygame.image.load(self.png_path)
        self.assertIsInstance(surf, pygame.Surface)
        self.assertEqual(surf.get_size(), (512, 512))

    def test_race_game_app_set_app_icon(self):
        """Verify that RaceGameApp._set_app_icon executes cleanly without exception."""
        app = RaceGameApp.__new__(RaceGameApp)
        # Should not raise any error
        app._set_app_icon()

    def test_race_game_app_set_windows_taskbar_icon(self):
        """Verify that RaceGameApp._set_windows_taskbar_icon executes safely across platforms."""
        app = RaceGameApp.__new__(RaceGameApp)
        # Headless call without hwnd should exit gracefully
        app._set_windows_taskbar_icon()

    def test_race_game_app_windows_taskbar_icon_with_mock_hwnd(self):
        """Verify that Win32 API calls are dispatched when a valid window handle exists."""
        app = RaceGameApp.__new__(RaceGameApp)
        with (
            patch("pygame.display.get_wm_info", return_value={"window": 12345}),
            patch("ctypes.windll.user32.LoadImageW", return_value=9999),
            patch("ctypes.windll.user32.SendMessageW") as mock_send,
            patch("sys.platform", "win32"),
        ):
            app._set_windows_taskbar_icon()
            self.assertEqual(mock_send.call_count, 2)


if __name__ == "__main__":
    unittest.main()
