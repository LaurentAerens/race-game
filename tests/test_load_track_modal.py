import os
import unittest
import pygame
from src.core.circuit import Circuit
from src.editor.load_track_modal import LoadTrackModal
from src.editor.track_editor import TrackEditor


class TestLoadTrackModal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1280, 720), pygame.HIDDEN)

    def test_scan_and_refresh_tracks(self):
        loaded_circuits = []
        modal = LoadTrackModal(on_track_loaded=lambda c: loaded_circuits.append(c))
        modal.open()
        self.assertTrue(modal.is_open)
        self.assertGreater(len(modal.track_items), 0)

        # Check that known tracks exist in list
        filenames = [item["filename"] for item in modal.track_items]
        self.assertIn("apex_park.json", filenames)

    def test_search_filter(self):
        modal = LoadTrackModal(on_track_loaded=lambda c: None)
        modal.open()
        
        modal.search_query = "apex"
        filtered = modal._get_filtered_items()
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0][1]["filename"], "apex_park.json")

        modal.search_query = "non_existent_circuit_name_xyz"
        self.assertEqual(len(modal._get_filtered_items()), 0)

    def test_load_track_file(self):
        loaded_circuits = []
        modal = LoadTrackModal(on_track_loaded=lambda c: loaded_circuits.append(c))
        modal.open()
        
        target_path = os.path.join("tracks", "apex_park.json")
        self.assertTrue(os.path.exists(target_path))
        modal._load_track_file(target_path)

        self.assertEqual(len(loaded_circuits), 1)
        c = loaded_circuits[0]
        self.assertEqual(c.name, "Apex Park")
        self.assertEqual(len(c.control_points), 13)
        self.assertFalse(modal.is_open) # Modal closes after loading

    def test_track_editor_integration(self):
        editor = TrackEditor(1280, 720, lambda c: None)
        btns = editor._get_panel_buttons()
        self.assertIn("load_json", btns)
        self.assertIn("save_json", btns)

        # Clicking load_json button opens load_modal
        editor._handle_panel_click(btns["load_json"].centerx, btns["load_json"].centery, 1)
        self.assertTrue(editor.load_modal.is_open)

        # Render editor while modal is open
        surf = pygame.Surface((1280, 720))
        editor.render(surf)

        # Pressing Escape closes modal
        esc_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0)
        editor.handle_event(esc_event)
        self.assertFalse(editor.load_modal.is_open)


if __name__ == "__main__":
    unittest.main()
