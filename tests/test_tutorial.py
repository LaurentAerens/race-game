import os
import tempfile
import unittest

import pygame

from src.database.career_db import CareerDatabase
from src.management.tutorial_manager import TUTORIAL_STEPS, TutorialManager
from src.ui.tutorial_overlay import TutorialOverlay


class TestTutorialSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1280, 720), pygame.NOFRAME)

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_tutorial_career.db")
        self.db = CareerDatabase(self.db_path)
        self.db.create_new_career(
            "Tutorial Racing", "#00d2be", "NORMAL", "Vortex EcoTech", "Alex Mercer", enable_tutorial=True
        )
        player_team = self.db.get_player_team()
        self.team_id = player_team["id"]

    def tearDown(self):
        self.db.close()
        self.temp_dir.cleanup()

    def test_tutorial_steps_definition(self):
        """Validates all 11 tutorial steps are well-defined with proper text, roles, and targets."""
        self.assertEqual(len(TUTORIAL_STEPS), 11)
        step_ids = [s.step_id for s in TUTORIAL_STEPS]
        self.assertIn("WELCOME_DASHBOARD", step_ids)
        self.assertIn("FACTORY_BRAKES_EQUIPMENT", step_ids)
        self.assertIn("PERSONNEL_HIRING", step_ids)
        self.assertIn("CAR_RND_FRONT_WING", step_ids)
        self.assertIn("DRIVERS_ACADEMY", step_ids)
        self.assertIn("SPONSORS_COMMERCIAL", step_ids)
        self.assertIn("LAUNCH_WEEKEND", step_ids)
        self.assertIn("WEEKEND_PRACTICE", step_ids)
        self.assertIn("WEEKEND_QUALIFYING", step_ids)
        self.assertIn("LIVE_RACE_PITWALL", step_ids)
        self.assertIn("RACE_DEBRIEF", step_ids)

        for step in TUTORIAL_STEPS:
            self.assertTrue(len(step.title) > 0)
            self.assertTrue(len(step.body) > 0)
            self.assertTrue(len(step.speaker_role) > 0)
            self.assertTrue(len(step.speaker_name) > 0)
            self.assertIn(step.required_mode, ["MANAGEMENT", "WEEKEND", "RACE"])

    def test_manager_initialization_and_first_step(self):
        """Manager loads tutorial progress and starts at Step 1."""
        tm = TutorialManager(self.db, self.team_id)
        self.assertTrue(tm.is_active)
        self.assertFalse(tm.is_completed)
        self.assertFalse(tm.is_skipped)
        self.assertEqual(tm.current_step_index, 0)
        curr = tm.get_current_step()
        self.assertIsNotNone(curr)
        self.assertEqual(curr.step_id, "WELCOME_DASHBOARD")

    def test_step_progression_and_tab_switching(self):
        """Iterates through steps with tab callback notification."""
        switched_tabs = []

        def on_tab(tab):
            switched_tabs.append(tab)

        tm = TutorialManager(self.db, self.team_id, on_switch_tab=on_tab)

        # Advance from Step 0 to Step 1 (FACTORY)
        tm.next_step()
        self.assertEqual(tm.current_step_index, 1)
        self.assertEqual(tm.get_current_step().step_id, "FACTORY_BRAKES_EQUIPMENT")
        self.assertIn("FACTORY", switched_tabs)

        # Go back to Step 0
        tm.prev_step()
        self.assertEqual(tm.current_step_index, 0)
        self.assertEqual(tm.get_current_step().step_id, "WELCOME_DASHBOARD")

    def test_interactive_action_completion_and_cash_rewards(self):
        """Interactive actions trigger bonuses and advance steps."""
        tm = TutorialManager(self.db, self.team_id)

        # Advance to step 1 (FACTORY_BRAKES_EQUIPMENT)
        tm.next_step()
        self.assertEqual(tm.get_current_step().step_id, "FACTORY_BRAKES_EQUIPMENT")

        initial_cash = self.db.get_player_team()["cash"]

        # Notify interactive action
        tm.notify_action_completed("BUY_BRAKES_EQUIPMENT")

        # Step should advance to PERSONNEL_HIRING and award $800,000 subsidy
        self.assertEqual(tm.get_current_step().step_id, "PERSONNEL_HIRING")
        updated_cash = self.db.get_player_team()["cash"]
        self.assertAlmostEqual(updated_cash - initial_cash, 800000.0, delta=1.0)

    def test_skip_tutorial(self):
        """Skipping immediately disables the tutorial and persists skipped status."""
        tm = TutorialManager(self.db, self.team_id)
        self.assertTrue(tm.is_active)

        tm.skip_tutorial()
        self.assertFalse(tm.is_active)
        self.assertTrue(tm.is_skipped)

        # Reload from DB
        tm2 = TutorialManager(self.db, self.team_id)
        self.assertFalse(tm2.is_active)
        self.assertTrue(tm2.is_skipped)

    def test_restart_tutorial(self):
        """Restarting re-enables tutorial at step 0."""
        tm = TutorialManager(self.db, self.team_id)
        tm.skip_tutorial()
        self.assertFalse(tm.is_active)

        tm.restart_tutorial()
        self.assertTrue(tm.is_active)
        self.assertFalse(tm.is_skipped)
        self.assertEqual(tm.current_step_index, 0)

    def test_mode_synchronization(self):
        """Entering WEEKEND and RACE modes auto-syncs the tutorial step."""
        tm = TutorialManager(self.db, self.team_id)

        # When entering WEEKEND mode
        tm.sync_game_state("WEEKEND")
        self.assertEqual(tm.get_current_step().step_id, "WEEKEND_PRACTICE")

        # When entering RACE mode
        tm.sync_game_state("RACE")
        self.assertEqual(tm.get_current_step().step_id, "LIVE_RACE_PITWALL")

        # When finishing race and returning to MANAGEMENT
        tm.sync_game_state("MANAGEMENT")
        self.assertEqual(tm.get_current_step().step_id, "RACE_DEBRIEF")

    def test_tutorial_overlay_rendering_and_events(self):
        """Overlay renders without error and handles keyboard/mouse navigation."""
        tm = TutorialManager(self.db, self.team_id)
        overlay = TutorialOverlay(1280, 720, tm)

        # Render test surface
        surf = pygame.Surface((1280, 720))
        overlay.render(surf)

        # Test ESC to skip
        esc_event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
        consumed = overlay.handle_event(esc_event)
        self.assertTrue(consumed)
        self.assertFalse(tm.is_active)
        self.assertTrue(tm.is_skipped)

        # Restart and test Enter to advance
        tm.restart_tutorial()
        enter_event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN})
        consumed = overlay.handle_event(enter_event)
        self.assertTrue(consumed)
        self.assertEqual(tm.current_step_index, 1)

    def test_front_wing_starting_knowledge(self):
        """Verifies player starts with enough knowledge on FRONT_WING to build Mk II during tutorial."""
        comps = self.db.get_team_components(self.team_id)
        fw = [c for c in comps if c["category"] == "FRONT_WING"]
        self.assertTrue(len(fw) > 0)
        self.assertTrue(fw[0]["knowledge_min"] >= 25.0)

    def test_no_db_progress_defaults_inactive(self):
        """When no tutorial row exists in DB for a team, is_active must default to False."""
        tm = TutorialManager(self.db, team_id=999999)
        self.assertFalse(tm.is_active)
        self.assertFalse(tm.is_completed)
        self.assertFalse(tm.is_skipped)

    def test_start_and_admin_mode_guards(self):
        """Overlay must not consume events or render on START or ADMIN screens even if manager is active."""
        tm = TutorialManager(self.db, self.team_id)
        self.assertTrue(tm.is_active)
        overlay = TutorialOverlay(1280, 720, tm)

        # On START mode, events must be ignored and not consumed
        enter_event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN})
        self.assertFalse(overlay.handle_event(enter_event, current_mode="START"))
        self.assertEqual(tm.current_step_index, 0)

        # On ADMIN mode, events must also be ignored
        self.assertFalse(overlay.handle_event(enter_event, current_mode="ADMIN"))
        self.assertEqual(tm.current_step_index, 0)

        # On MANAGEMENT mode, events should be consumed and advance
        self.assertTrue(overlay.handle_event(enter_event, current_mode="MANAGEMENT"))
        self.assertEqual(tm.current_step_index, 1)

        # Render guard
        surf = pygame.Surface((1280, 720))
        # Should execute cleanly with current_mode without drawing over START or ADMIN
        overlay.render(surf, current_mode="START")
        overlay.render(surf, current_mode="ADMIN")
        overlay.render(surf, current_mode="MANAGEMENT")

    def test_card_adjacent_docking_and_target_badge(self):
        """Card for Step 1 (top-left target) must dock beside target (not in bottom-right corner)."""
        tm = TutorialManager(self.db, self.team_id)
        overlay = TutorialOverlay(1280, 720, tm)
        step1 = tm.get_current_step()
        self.assertEqual(step1.step_id, "WELCOME_DASHBOARD")

        target = overlay.get_target_rect(step1)
        self.assertIsNotNone(target)
        self.assertEqual(target.x, 24)
        self.assertEqual(target.y, 70)

        card = overlay.get_card_rect(step1)
        # Card must be adjacent to the right of the target (x >= target.right)
        self.assertGreaterEqual(card.x, target.right)
        # Card must be in the top portion of the screen (not bottom-right > 400y)
        self.assertLess(card.y, 200)

        # Ensure render with callout pointer and badge executes cleanly
        surf = pygame.Surface((1280, 720))
        overlay.render(surf, current_mode="MANAGEMENT")

    def test_step2_brakes_target_and_drawer_transition(self):
        """Step 2 must accurately highlight Brakes Lab node, and switch to equipment item when drawer opens."""
        tm = TutorialManager(self.db, self.team_id)
        tm.next_step()  # Advance to step 1 (FACTORY_BRAKES_EQUIPMENT)
        step2 = tm.get_current_step()
        self.assertEqual(step2.step_id, "FACTORY_BRAKES_EQUIPMENT")

        overlay = TutorialOverlay(1280, 720, tm)

        # 1. Without drawer open: Target must cleanly encompass Brakes Lab node (x=370, y=130, w=210, h=105)
        target_closed = overlay.get_target_rect(step2)
        self.assertIsNotNone(target_closed)
        self.assertEqual(target_closed.x, 370)
        self.assertEqual(target_closed.y, 130)
        self.assertEqual(target_closed.width, 210)
        self.assertEqual(target_closed.height, 105)

        # Card must dock to the right of Brakes Lab (x >= 580)
        card_closed = overlay.get_card_rect(step2)
        self.assertGreaterEqual(card_closed.x, target_closed.right)

        # 2. Simulate drawer open with a mock management hub
        class MockFactoryTab:
            inspected_node_id = "eng_brakes"
            pan_x = 40.0
            pan_y = 130.0
            zoom = 1.0
            node_positions = {"eng_brakes": (330.0, 0.0)}

        class MockHub:
            tab_factory = MockFactoryTab()

        overlay.management_hub = MockHub()

        # When drawer is open, target must switch to equipment list inside drawer (x >= 730)
        target_open = overlay.get_target_rect(step2)
        self.assertIsNotNone(target_open)
        self.assertGreaterEqual(target_open.x, 700)

        # Card must dock to the left of the drawer without overlapping it
        card_open = overlay.get_card_rect(step2)
        self.assertLessEqual(card_open.right, target_open.x)

        # Render must succeed cleanly in both states
        surf = pygame.Surface((1280, 720))
        overlay.render(surf, current_mode="MANAGEMENT")

    def test_step3_personnel_targeting_and_modal_state(self):
        """Step 3 must target recruitment tab, candidate card, and modal assign button when destination picker opens."""
        tm = TutorialManager(self.db, self.team_id)
        tm.current_step_index = 2  # PERSONNEL_HIRING
        step3 = tm.get_current_step()
        self.assertEqual(step3.step_id, "PERSONNEL_HIRING")

        overlay = TutorialOverlay(1280, 720, tm)

        class MockWorkforceTab:
            width = 1280
            sub_tab = "TREE"
            inspected_personnel_id = None
            destination_picker_data = None
            target_assignment_node = None
            scroll_y = 0.0

        class MockHub:
            tab_workforce = MockWorkforceTab()

        overlay.management_hub = MockHub()

        # 1. On TREE sub-tab: highlights Recruitment subtab button at x=203, y=62
        t1 = overlay.get_target_rect(step3)
        self.assertEqual(t1.x, 203)
        self.assertEqual(t1.y, 62)

        # 2. On RECRUITMENT sub-tab: highlights first applicant card at y=126
        MockHub.tab_workforce.sub_tab = "RECRUITMENT"
        t2 = overlay.get_target_rect(step3)
        self.assertEqual(t2.x, 36)
        self.assertEqual(t2.y, 126)

        # 3. When destination picker modal is open: highlights ASSIGN HERE button
        MockHub.tab_workforce.destination_picker_data = {"type": "APPLICANT", "id": 1}
        t3 = overlay.get_target_rect(step3)
        self.assertIsNotNone(t3)
        self.assertGreater(t3.x, 500)

    def test_step4_car_blueprint_and_build_btn_targeting(self):
        """Step 4 must target front wing blueprint hotspot, then switch to BUILD NEXT GEN button when selected."""
        tm = TutorialManager(self.db, self.team_id)
        tm.current_step_index = 3  # CAR_RND_FRONT_WING
        step4 = tm.get_current_step()
        self.assertEqual(step4.step_id, "CAR_RND_FRONT_WING")

        overlay = TutorialOverlay(1280, 720, tm)

        class MockCarTab:
            selected_part_category = "SUSPENSION"  # Not front wing initially

            def get_layout(self, gm, em, tier, allowed_parts):
                return {
                    "hotspot_rects": {
                        "FRONT_WING": pygame.Rect(560, 130, 80, 40),
                        "SUSPENSION": pygame.Rect(560, 240, 80, 40),
                    },
                    "build_btn": pygame.Rect(520, 490, 160, 36),
                }

        class MockGM:
            team_id = 1

        class MockEM:
            def get_team_allowed_parts(self, tid):
                return 3, "National Open Cup", ["FRONT_WING", "BRAKES"]

        class MockHub:
            tab_car = MockCarTab()
            gm = MockGM()
            em = MockEM()

        overlay.management_hub = MockHub()

        # 1. When Front Wing not selected: targets blueprint hotspot
        t1 = overlay.get_target_rect(step4)
        self.assertEqual(t1.x, 560)
        self.assertEqual(t1.y, 130)

        # 2. When Front Wing is selected: targets BUILD NEXT GEN button
        MockHub.tab_car.selected_part_category = "FRONT_WING"
        t2 = overlay.get_target_rect(step4)
        self.assertEqual(t2.x, 520)
        self.assertEqual(t2.y, 490)


if __name__ == "__main__":
    unittest.main()
