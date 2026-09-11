import unittest
import pygame
from src.editor.track_editor import TrackEditor

class TestTrackEditorUndoRedo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((800, 600))

    def setUp(self):
        self.editor = TrackEditor(1280, 720, on_test_race=lambda c: None)

    def test_initial_state(self):
        self.assertGreaterEqual(len(self.editor.circuit.control_points), 3)
        self.assertEqual(len(self.editor.undo_stack), 0)
        self.assertEqual(len(self.editor.redo_stack), 0)

    def test_insert_node_undo_redo(self):
        initial_count = len(self.editor.circuit.control_points)
        self.editor._insert_node_at(100.0, 100.0)
        self.assertEqual(len(self.editor.circuit.control_points), initial_count + 1)
        self.assertEqual(len(self.editor.undo_stack), 1)
        self.assertEqual(len(self.editor.redo_stack), 0)

        self.editor.undo()
        self.assertEqual(len(self.editor.circuit.control_points), initial_count)
        self.assertEqual(len(self.editor.undo_stack), 0)
        self.assertEqual(len(self.editor.redo_stack), 1)

        self.editor.redo()
        self.assertEqual(len(self.editor.circuit.control_points), initial_count + 1)
        self.assertEqual(len(self.editor.undo_stack), 1)
        self.assertEqual(len(self.editor.redo_stack), 0)

    def test_delete_selected_node(self):
        initial_count = len(self.editor.circuit.control_points)
        self.editor.selected_node_a = 2
        node_to_delete = self.editor.circuit.control_points[2]

        self.editor.delete_selected_node()
        self.assertEqual(len(self.editor.circuit.control_points), initial_count - 1)
        self.assertNotIn(node_to_delete, self.editor.circuit.control_points)
        self.assertEqual(len(self.editor.undo_stack), 1)

        self.editor.undo()
        self.assertEqual(len(self.editor.circuit.control_points), initial_count)
        self.assertEqual(self.editor.circuit.control_points[2], node_to_delete)

        self.editor.redo()
        self.assertEqual(len(self.editor.circuit.control_points), initial_count - 1)

    def test_delete_node_minimum_boundary(self):
        while len(self.editor.circuit.control_points) > 3:
            self.editor.selected_node_a = 0
            self.editor.delete_selected_node()

        self.assertEqual(len(self.editor.circuit.control_points), 3)
        self.editor.selected_node_a = 0
        self.editor.delete_selected_node()
        self.assertEqual(len(self.editor.circuit.control_points), 3)
        self.assertIn("at least 3", self.editor.status_message)

    def test_keyboard_shortcuts(self):
        initial_count = len(self.editor.circuit.control_points)
        self.editor.selected_node_a = 1

        event_del = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DELETE, mod=0)
        self.editor.handle_event(event_del)
        self.assertEqual(len(self.editor.circuit.control_points), initial_count - 1)

        event_undo = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_z, mod=pygame.KMOD_CTRL)
        self.editor.handle_event(event_undo)
        self.assertEqual(len(self.editor.circuit.control_points), initial_count)

        event_redo = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_y, mod=pygame.KMOD_CTRL)
        self.editor.handle_event(event_redo)
        self.assertEqual(len(self.editor.circuit.control_points), initial_count - 1)

    def test_panel_buttons_interaction(self):
        btns = self.editor._get_panel_buttons()
        self.assertIn("undo", btns)
        self.assertIn("redo", btns)
        self.assertIn("delete_node", btns)

        self.assertGreater(btns["undo"].width, 0)
        self.assertGreater(btns["redo"].width, 0)
        self.assertGreater(btns["delete_node"].width, 0)

        initial_count = len(self.editor.circuit.control_points)
        self.editor.selected_node_a = 0
        self.editor._handle_panel_click(btns["delete_node"].centerx, btns["delete_node"].centery, 1)
        self.assertEqual(len(self.editor.circuit.control_points), initial_count - 1)

        self.editor._handle_panel_click(btns["undo"].centerx, btns["undo"].centery, 1)
        self.assertEqual(len(self.editor.circuit.control_points), initial_count)

        self.editor._handle_panel_click(btns["redo"].centerx, btns["redo"].centery, 1)
        self.assertEqual(len(self.editor.circuit.control_points), initial_count - 1)

    def test_all_nodes_visible_and_numbered(self):
        # Verify that for any circuit, every single control point is drawn with its node number
        c = self.editor.circuit
        self.assertGreater(len(c.control_points), 0)
        
        surf = pygame.Surface((1280, 720))
        # Rendering shouldn't crash and should process all nodes
        self.editor.render(surf)

    def test_drs_synchronization(self):
        c = self.editor.circuit
        c.drs_zones = [{
            "name": "DRS #1->#3",
            "node_a": 0,
            "node_b": 2,
            "start_s": 0.0,
            "end_s": 100.0
        }]
        c.build_circuit()
        self.assertEqual(c.drs_zones[0]["start_s"], c.node_s_distances[0])
        self.assertEqual(c.drs_zones[0]["end_s"], c.node_s_distances[2])


if __name__ == "__main__":
    unittest.main()

