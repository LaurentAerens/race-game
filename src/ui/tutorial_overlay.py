"""
Interactive Guided Tutorial Overlay.
Renders glowing target highlights, animated spotlight pulse,
and a floating, draggable Advisor Dialog Card with step navigation and rewards.
"""

import math
from typing import Any, Optional, Tuple

import pygame

from ..management.tutorial_manager import TutorialManager, TutorialStep
from .theme import UITheme


class TutorialOverlay:
    """
    Renders high-tech floating tutorial cards and element highlights
    on top of the active game mode.
    """

    def __init__(
        self, screen_width: int, screen_height: int, manager: TutorialManager, management_hub: Optional[Any] = None
    ):
        self.width = screen_width
        self.height = screen_height
        self.manager = manager
        self.management_hub = management_hub

        self._init_fonts()

        # Animation timers
        self.pulse_timer: float = 0.0

        # Card dragging state
        self.custom_card_pos: Optional[Tuple[int, int]] = None
        self.is_dragging: bool = False
        self.drag_offset: Tuple[int, int] = (0, 0)

        # Card dimensions
        self.card_w: int = 480
        self.card_h: int = 280
        self._last_step_id: Optional[str] = None
        self._last_drawer_open: bool = False

    def _init_fonts(self):
        self.font_role = UITheme.get_font(10, bold=True)
        self.font_name = UITheme.get_font(11, bold=True)
        self.font_step = UITheme.get_font(9, bold=True)
        self.font_title = UITheme.get_font(13, bold=True)
        self.font_body = UITheme.get_font(10, bold=False)
        self.font_reward = UITheme.get_font(10, bold=True)
        self.font_badge = UITheme.get_font(9, bold=True)
        self.font_btn = UITheme.get_font(10, bold=True)

    def resize(self, width: int, height: int):
        self.width = width
        self.height = height
        self._init_fonts()
        self.card_w = min(490, max(420, int(width * 0.38)))
        self.card_h = 280

    def update(self, dt: float):
        self.pulse_timer += dt * 3.5

    def get_target_rect(self, step: TutorialStep) -> Optional[pygame.Rect]:
        """Returns the screen bounding box of the highlighted element."""
        key = step.target_element_key
        w, h = self.width, self.height

        if key == "tab_dashboard_gp":
            col_w = min(540, (w - 64) // 2)
            return pygame.Rect(24, 70, col_w, 215)
        elif key == "tab_factory_node":
            if self.management_hub and hasattr(self.management_hub, "tab_factory"):
                tf = self.management_hub.tab_factory
                # If equipment drawer is open for Brakes Lab, highlight the first equipment item & its buy button
                if getattr(tf, "inspected_node_id", None) == "eng_brakes":
                    drawer_x = self.width - 550
                    return pygame.Rect(drawer_x + 18, 304, 490, 82)
                # If drawer is closed, highlight the Brakes Lab node on the canvas with exact coordinates
                if hasattr(tf, "node_positions") and "eng_brakes" in tf.node_positions:
                    gx, gy = tf.node_positions["eng_brakes"]
                    sx = int(tf.pan_x + gx * tf.zoom)
                    sy = int(tf.pan_y + gy * tf.zoom)
                    sw = int(210 * tf.zoom)
                    sh = int(105 * tf.zoom)
                    return pygame.Rect(sx, sy, sw, sh)
            return pygame.Rect(370, 130, 210, 105)
        elif key == "tab_personnel_recruitment":
            if self.management_hub and hasattr(self.management_hub, "tab_workforce"):
                tw = self.management_hub.tab_workforce
                # 1. If Destination Picker Modal is open, highlight the first room's "ASSIGN HERE" button
                if getattr(tw, "destination_picker_data", None) is not None:
                    modal_w = min(780, self.width - 80)
                    modal_x = (self.width - modal_w) // 2
                    modal_y = (self.height - min(540, self.height - 100)) // 2
                    list_x = modal_x + 12
                    card_w = modal_w - 24
                    return pygame.Rect(list_x + card_w - 158, modal_y + 94, 140, 28)
                # 2. If on RECRUITMENT sub-tab, highlight the first applicant card and its hire button
                if getattr(tw, "sub_tab", "") == "RECRUITMENT":
                    content_w = tw.width - (450 if getattr(tw, "inspected_personnel_id", None) else 48)
                    card_w = content_w - 24
                    top_offset = 46 if getattr(tw, "target_assignment_node", None) else 0
                    scroll_y = int(getattr(tw, "scroll_y", 0.0))
                    card_y = 126 + top_offset + scroll_y
                    card_x = 36
                    return pygame.Rect(card_x, card_y, card_w, 72)
                # 3. If on TREE sub-tab, highlight the Recruitment sub-tab button
                return pygame.Rect(203, 62, 175, 26)
            return pygame.Rect(203, 62, 175, 26)
        elif key == "car_rnd_front_wing":
            if self.management_hub and hasattr(self.management_hub, "tab_car"):
                tc = self.management_hub.tab_car
                gm = self.management_hub.gm
                em = self.management_hub.em
                tier, _, allowed_parts = em.get_team_allowed_parts(gm.team_id)
                layout = tc.get_layout(gm, em, tier, allowed_parts)
                # If FRONT_WING is already selected, highlight the "BUILD NEXT GEN" button in the R&D Evolution deck
                if getattr(tc, "selected_part_category", "") == "FRONT_WING":
                    b_btn = layout.get("build_btn")
                    if b_btn:
                        return b_btn
                # Otherwise, highlight the Front Wing hotspot on the chassis blueprint
                hotspots = layout.get("hotspot_rects", {})
                if "FRONT_WING" in hotspots:
                    return hotspots["FRONT_WING"]
            return pygame.Rect(self.width // 2 - 160, 480, 160, 36)
        elif key == "drivers_academy_scouts":
            if self.management_hub and hasattr(self.management_hub, "tab_drivers"):
                td = self.management_hub.tab_drivers
                right_x = min(460, int(self.width * 0.35)) + 40
                right_w = self.width - right_x - 24
                # If on SCOUTS sub-tab, highlight the first scout prospect card and its sign button
                if getattr(td, "active_subtab", "") == "SCOUTS":
                    return pygame.Rect(right_x + 10, 108, right_w - 20, 134)
                # Otherwise highlight the SCOUTS sub-tab button
                return pygame.Rect(right_x + 150, 68, 160, 28)
            right_x = min(460, int(w * 0.35)) + 40
            return pygame.Rect(right_x + 150, 68, 160, 28)
        elif key == "sponsors_offers":
            off_rect_x = 560
            off_rect_w = self.width - 584
            return pygame.Rect(off_rect_x + 10, 158, off_rect_w - 20, 80)
        elif key == "btn_start_race":
            return pygame.Rect(self.width - 320, self.height - 65, 300, 48)
        elif key == "weekend_practice_sliders":
            return pygame.Rect(24, 150, 480, 260)
        elif key == "weekend_qualifying_btn":
            return pygame.Rect(self.width // 2 - 220, self.height // 2 - 30, 440, 60)
        elif key == "race_driver_panel":
            return pygame.Rect(10, self.height - 138, self.width - 20, 130)
        elif key == "hub_header_tutorial_btn":
            return pygame.Rect(self.width - 340, 4, 92, 18)

        return None

    def get_card_rect(self, step: TutorialStep) -> pygame.Rect:
        """Calculates smart positioning directly adjacent to the target element."""
        # Auto-reset custom drag if step changed, or if interactive screen state changed
        is_drawer_open = bool(
            self.management_hub
            and hasattr(self.management_hub, "tab_factory")
            and getattr(self.management_hub.tab_factory, "inspected_node_id", None) == "eng_brakes"
        )
        wf_sub_tab = (
            getattr(self.management_hub.tab_workforce, "sub_tab", "")
            if (self.management_hub and hasattr(self.management_hub, "tab_workforce"))
            else ""
        )
        has_dest_picker = bool(
            self.management_hub
            and hasattr(self.management_hub, "tab_workforce")
            and getattr(self.management_hub.tab_workforce, "destination_picker_data", None) is not None
        )
        car_part = (
            getattr(self.management_hub.tab_car, "selected_part_category", "")
            if (self.management_hub and hasattr(self.management_hub, "tab_car"))
            else ""
        )
        drivers_sub_tab = (
            getattr(self.management_hub.tab_drivers, "active_subtab", "")
            if (self.management_hub and hasattr(self.management_hub, "tab_drivers"))
            else ""
        )
        if (
            getattr(self, "_last_step_id", None) != step.step_id
            or getattr(self, "_last_drawer_open", None) != is_drawer_open
            or getattr(self, "_last_wf_sub_tab", None) != wf_sub_tab
            or getattr(self, "_last_dest_picker", None) != has_dest_picker
            or getattr(self, "_last_car_part", None) != car_part
            or getattr(self, "_last_drivers_sub_tab", None) != drivers_sub_tab
        ):
            self._last_step_id = step.step_id
            self._last_drawer_open = is_drawer_open
            self._last_wf_sub_tab = wf_sub_tab
            self._last_dest_picker = has_dest_picker
            self._last_car_part = car_part
            self._last_drivers_sub_tab = drivers_sub_tab
            self.custom_card_pos = None

        if self.custom_card_pos:
            cx, cy = self.custom_card_pos
            # Clamp inside screen
            cx = max(10, min(self.width - self.card_w - 10, cx))
            cy = max(10, min(self.height - self.card_h - 10, cy))
            return pygame.Rect(cx, cy, self.card_w, self.card_h)

        target = self.get_target_rect(step)
        if not target:
            # Top-right by default
            return pygame.Rect(self.width - self.card_w - 24, 75, self.card_w, self.card_h)

        # 1. Wide targets (e.g. recruitment candidate card, race bottom panel)
        if target.width > self.width * 0.65:
            # If target is in top half of screen (like recruitment candidate card at y=126), dock card below it
            if target.centery < self.height // 2:
                card_x = max(24, min(self.width - self.card_w - 24, target.centerx - self.card_w // 2))
                card_y = target.bottom + 24
                # If fitting below would exceed screen, clamp to bottom
                card_y = min(self.height - self.card_h - 16, card_y)
                return pygame.Rect(card_x, card_y, self.card_w, self.card_h)
            else:
                card_x = self.width - self.card_w - 24
                card_y = 75
                return pygame.Rect(card_x, card_y, self.card_w, self.card_h)

        # 2. Target is on left side of screen -> dock horizontally to its RIGHT
        if target.centerx < self.width // 2:
            card_x = target.right + 20
            if card_x + self.card_w <= self.width - 16:
                card_y = max(60, min(self.height - self.card_h - 20, target.y))
                return pygame.Rect(card_x, card_y, self.card_w, self.card_h)
            else:
                return pygame.Rect(
                    self.width - self.card_w - 24,
                    max(60, min(self.height - self.card_h - 20, target.y)),
                    self.card_w,
                    self.card_h,
                )

        # 3. Target is on right side of screen -> dock horizontally to its LEFT
        else:
            card_x = target.x - 20 - self.card_w
            if card_x >= 16:
                card_y = max(60, min(self.height - self.card_h - 20, target.y))
                return pygame.Rect(card_x, card_y, self.card_w, self.card_h)
            else:
                return pygame.Rect(24, max(60, min(self.height - self.card_h - 20, target.y)), self.card_w, self.card_h)

    def _get_card_buttons(self, card_rect: pygame.Rect) -> Tuple[pygame.Rect, pygame.Rect, pygame.Rect]:
        """Returns unified button rectangles (skip, back, next) to prevent hitbox desync."""
        btn_y = card_rect.bottom - 44
        btn_h = 32
        btn_skip = pygame.Rect(card_rect.x + 16, btn_y, 100, btn_h)
        btn_back = pygame.Rect(card_rect.right - 232, btn_y, 76, btn_h)
        btn_next = pygame.Rect(card_rect.right - 146, btn_y, 132, btn_h)
        return btn_skip, btn_back, btn_next

    def handle_event(self, event: pygame.event.Event, current_mode: Optional[str] = None) -> bool:
        """Handles clicks and shortcuts on the tutorial card."""
        if current_mode in ["START", "ADMIN"]:
            return False
        if not self.manager.is_active:
            return False

        step = self.manager.get_current_step()
        if not step:
            return False

        card_rect = self.get_card_rect(step)

        # Keyboard shortcuts: ESC to skip, ENTER/SPACE/RIGHT to next, LEFT to prev
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.manager.skip_tutorial()
                return True
            elif event.key in (pygame.K_RETURN, pygame.K_RIGHT):
                self.manager.next_step()
                return True
            elif event.key == pygame.K_LEFT:
                self.manager.prev_step()
                return True

        # Mouse Dragging
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            hdr_rect = pygame.Rect(card_rect.x, card_rect.y, card_rect.width, 36)

            # Unified button rects at bottom of card
            btn_skip, btn_back, btn_next = self._get_card_buttons(card_rect)

            if btn_skip.collidepoint(mx, my):
                self.manager.skip_tutorial()
                return True

            if btn_back.collidepoint(mx, my) and self.manager.current_step_index > 0:
                self.manager.prev_step()
                return True

            if btn_next.collidepoint(mx, my):
                self.manager.next_step()
                return True

            # Drag card by clicking header
            if hdr_rect.collidepoint(mx, my):
                self.is_dragging = True
                self.drag_offset = (mx - card_rect.x, my - card_rect.y)
                return True

            # Absorb clicks inside card so they don't accidentally trigger background buttons
            if card_rect.collidepoint(mx, my):
                return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging = False

        elif event.type == pygame.MOUSEMOTION and self.is_dragging:
            mx, my = event.pos
            self.custom_card_pos = (mx - self.drag_offset[0], my - self.drag_offset[1])
            return True

        return False

    def render(self, surface: pygame.Surface, current_mode: Optional[str] = None):
        """Draws glowing target highlight and floating advisor card."""
        if current_mode in ["START", "ADMIN"]:
            return
        if not self.manager.is_active:
            return

        step = self.manager.get_current_step()
        if not step:
            return

        # 1. Glowing Target Spotlight
        # Guard: Only render target highlight if active screen mode matches step requirement
        if current_mode and step.required_mode != current_mode:
            target = None
        elif (
            current_mode == "MANAGEMENT"
            and step.required_tab
            and self.management_hub
            and getattr(self.management_hub, "active_tab", None) != step.required_tab
        ):
            target = None
        else:
            target = self.get_target_rect(step)

        if target:
            # Pulsing alpha border
            pulse = (math.sin(self.pulse_timer) + 1.0) * 0.5  # 0.0 to 1.0
            cyan_val = int(180 + pulse * 75)
            glow_color = (0, cyan_val, 255)

            # Draw outer highlight border with padding
            pad = 4
            highlight_rect = pygame.Rect(
                target.x - pad, target.y - pad, target.width + pad * 2, target.height + pad * 2
            )
            pygame.draw.rect(surface, glow_color, highlight_rect, width=2, border_radius=5)

            # Draw subtle semi-transparent corner accents
            corner_len = 14
            # Top-left
            pygame.draw.line(
                surface,
                (255, 255, 255),
                (highlight_rect.x, highlight_rect.y),
                (highlight_rect.x + corner_len, highlight_rect.y),
                3,
            )
            pygame.draw.line(
                surface,
                (255, 255, 255),
                (highlight_rect.x, highlight_rect.y),
                (highlight_rect.x, highlight_rect.y + corner_len),
                3,
            )
            # Bottom-right
            pygame.draw.line(
                surface,
                (255, 255, 255),
                (highlight_rect.right, highlight_rect.bottom),
                (highlight_rect.right - corner_len, highlight_rect.bottom),
                3,
            )
            pygame.draw.line(
                surface,
                (255, 255, 255),
                (highlight_rect.right, highlight_rect.bottom),
                (highlight_rect.right, highlight_rect.bottom - corner_len),
                3,
            )

            # Step Focus Badge attached to the highlighted target
            badge_txt = f"🎯 TUTORIAL FOCUS: STEP {self.manager.current_step_index + 1}"
            if step.step_id == "WELCOME_DASHBOARD":
                badge_txt = "🎯 STEP 1: REVIEW CALENDAR & CIRCUIT DEMANDS"
            elif step.step_id == "FACTORY_BRAKES_EQUIPMENT":
                if (
                    self.management_hub
                    and hasattr(self.management_hub, "tab_factory")
                    and getattr(self.management_hub.tab_factory, "inspected_node_id", None) == "eng_brakes"
                ):
                    badge_txt = "🎯 STEP 2: CLICK 'BUY' OR 'UPGRADE' (FREE BOARD GRANT)"
                else:
                    badge_txt = "🎯 STEP 2: CLICK 'BRAKES WORKSHOP' TO OPEN EQUIPMENT"
            elif step.step_id == "PERSONNEL_HIRING":
                if self.management_hub and hasattr(self.management_hub, "tab_workforce"):
                    tw = self.management_hub.tab_workforce
                    if getattr(tw, "destination_picker_data", None) is not None:
                        badge_txt = "🎯 STEP 3: CLICK 'ASSIGN HERE' TO COMPLETE HIRING"
                    elif getattr(tw, "sub_tab", "") == "RECRUITMENT":
                        badge_txt = "🎯 STEP 3: CLICK 'INBOUND / CHOOSE ROOM' TO HIRE"
                    else:
                        badge_txt = "🎯 STEP 3: CLICK 'RECRUITMENT & TRYOUTS' SUB-TAB"
            elif step.step_id == "CAR_RND_FRONT_WING":
                if (
                    self.management_hub
                    and hasattr(self.management_hub, "tab_car")
                    and getattr(self.management_hub.tab_car, "selected_part_category", "") == "FRONT_WING"
                ):
                    badge_txt = "🎯 STEP 4: CLICK 'BUILD NEXT GEN' (BOARD PROTO SUBSIDY)"
                else:
                    badge_txt = "🎯 STEP 4: CLICK FRONT WING ON BLUEPRINT"
            elif step.step_id == "DRIVERS_ACADEMY":
                if (
                    self.management_hub
                    and hasattr(self.management_hub, "tab_drivers")
                    and getattr(self.management_hub.tab_drivers, "active_subtab", "") == "SCOUTS"
                ):
                    badge_txt = "🎯 STEP 5: SIGN YOUNG TALENT OR ASSIGN FEEDER SEAT"
                else:
                    badge_txt = "🎯 STEP 5: CLICK 'SCOUTS' SUB-TAB TO FIND YOUTH TALENT"
            elif step.step_id == "SPONSORS_COMMERCIAL":
                badge_txt = "🎯 STEP 6: SIGN CORPORATE SPONSOR CONTRACT"
            elif step.step_id == "LAUNCH_WEEKEND":
                badge_txt = "🎯 STEP 7: CLICK 'START RACE WEEKEND' TO TRAVEL TO TRACK"
            elif step.step_id == "WEEKEND_PRACTICE":
                badge_txt = "🎯 STEP 8: TUNE WING/BRAKE SLIDERS & RUN PRACTICE STINT"
            elif step.step_id == "WEEKEND_QUALIFYING":
                badge_txt = "🎯 STEP 9: CLICK 'SIMULATE QUALIFYING SHOOTOUT'"
            elif step.step_id == "LIVE_RACE_PITWALL":
                badge_txt = "🎯 STEP 10: MANAGE DRIVER PACE & TYRE LIFE ON PIT WALL"
            elif step.step_id == "RACE_DEBRIEF":
                badge_txt = "🎯 TUTORIAL COMPLETE: CONGRATULATIONS TEAM PRINCIPAL!"

            badge_surf = self.font_step.render(badge_txt, True, (0, 240, 255))
            bw, bh = badge_surf.get_width() + 16, 20
            by = highlight_rect.y - 22 if highlight_rect.y >= 26 else highlight_rect.bottom + 4
            b_rect = pygame.Rect(highlight_rect.x + 8, by, bw, bh)
            pygame.draw.rect(surface, (12, 18, 26), b_rect, border_radius=3)
            pygame.draw.rect(surface, (0, 200, 240), b_rect, width=1, border_radius=3)
            surface.blit(badge_surf, (b_rect.x + 8, b_rect.y + 4))

        # 2. Floating Advisor Card
        card = self.get_card_rect(step)

        # Callout Pointer / Beacon Arrow connecting Card and Target
        if target and not self.custom_card_pos:
            # Card is to the right of target
            if card.x >= target.right - 8:
                ptr_y = max(card.y + 24, min(card.bottom - 24, target.centery))
                ptr_pts = [(card.x + 1, ptr_y - 9), (card.x - 12, ptr_y), (card.x + 1, ptr_y + 9)]
                pygame.draw.polygon(surface, (15, 20, 28), ptr_pts)
                pygame.draw.polygon(surface, (0, 200, 240), ptr_pts, width=2)
                if card.x - 12 > target.right:
                    pygame.draw.line(surface, (0, 180, 220), (target.right, ptr_y), (card.x - 12, ptr_y), 1)

            # Card is to the left of target
            elif card.right <= target.x + 8:
                ptr_y = max(card.y + 24, min(card.bottom - 24, target.centery))
                ptr_pts = [(card.right - 1, ptr_y - 9), (card.right + 12, ptr_y), (card.right - 1, ptr_y + 9)]
                pygame.draw.polygon(surface, (15, 20, 28), ptr_pts)
                pygame.draw.polygon(surface, (0, 200, 240), ptr_pts, width=2)
                if target.x > card.right + 12:
                    pygame.draw.line(surface, (0, 180, 220), (card.right + 12, ptr_y), (target.x, ptr_y), 1)

            # Card is below target
            elif card.y >= target.bottom - 8:
                ptr_x = max(card.x + 24, min(card.right - 24, target.centerx))
                ptr_pts = [(ptr_x - 9, card.y + 1), (ptr_x, card.y - 12), (ptr_x + 9, card.y + 1)]
                pygame.draw.polygon(surface, (15, 20, 28), ptr_pts)
                pygame.draw.polygon(surface, (0, 200, 240), ptr_pts, width=2)

            # Card is above target
            elif card.bottom <= target.y + 8:
                ptr_x = max(card.x + 24, min(card.right - 24, target.centerx))
                ptr_pts = [(ptr_x - 9, card.bottom - 1), (ptr_x, card.bottom + 12), (ptr_x + 9, card.bottom - 1)]
                pygame.draw.polygon(surface, (15, 20, 28), ptr_pts)
                pygame.draw.polygon(surface, (0, 200, 240), ptr_pts, width=2)

        # Drop shadow
        shadow_rect = pygame.Rect(card.x + 4, card.y + 6, card.width, card.height)
        shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 140))
        surface.blit(shadow_surf, (shadow_rect.x, shadow_rect.y))

        # Card body
        pygame.draw.rect(surface, (15, 20, 28), card, border_radius=6)
        pygame.draw.rect(surface, (0, 200, 240), card, width=2, border_radius=6)

        # Card Header Bar
        hdr_rect = pygame.Rect(card.x, card.y, card.width, 36)
        pygame.draw.rect(surface, (22, 28, 40), hdr_rect, border_top_left_radius=6, border_top_right_radius=6)
        pygame.draw.line(surface, (35, 45, 65), (hdr_rect.x, hdr_rect.bottom), (hdr_rect.right, hdr_rect.bottom), 1)

        # Advisor Badge & Name
        # Advisor Badge & Name
        role_surf = self.font_role.render(f"[{step.speaker_role}]", True, (0, 230, 255))
        surface.blit(role_surf, (card.x + 14, card.y + 10))

        name_surf = self.font_name.render(step.speaker_name, True, UITheme.TEXT_WHITE)
        surface.blit(name_surf, (card.x + 20 + role_surf.get_width(), card.y + 9))

        # [i] Info Hover Button (Briefing & Lore)
        mx, my = pygame.mouse.get_pos()
        info_btn = pygame.Rect(card.x + 24 + role_surf.get_width() + name_surf.get_width(), card.y + 8, 20, 20)
        is_info_hover = info_btn.collidepoint(mx, my)
        UITheme.draw_info_icon(surface, info_btn, is_hover=is_info_hover)

        # Step Meter (e.g. "Step 3 / 11")
        step_txt = f"Step {self.manager.current_step_index + 1} of {self.manager.get_total_steps()}"
        step_surf = self.font_step.render(step_txt, True, (255, 215, 0))
        surface.blit(step_surf, (card.right - step_surf.get_width() - 14, card.y + 11))

        # Title
        title_surf = self.font_title.render(step.title, True, (255, 215, 0))
        surface.blit(title_surf, (card.x + 16, card.y + 44))

        # Dynamic Context-Aware Objective
        obj_text = step.get_objective()
        if (
            step.step_id == "FACTORY_BRAKES_EQUIPMENT"
            and self.management_hub
            and hasattr(self.management_hub, "tab_factory")
        ):
            if getattr(self.management_hub.tab_factory, "inspected_node_id", None) == "eng_brakes":
                obj_text = "Click 'BUY' or 'UPGRADE' on any equipment item in the drawer (100% Board grant subsidy)."
        elif (
            step.step_id == "PERSONNEL_HIRING" and self.management_hub and hasattr(self.management_hub, "tab_workforce")
        ):
            tw = self.management_hub.tab_workforce
            if getattr(tw, "destination_picker_data", None) is not None:
                obj_text = "Choose an unlocked facility room with an open desk and click 'ASSIGN HERE'."
            elif getattr(tw, "sub_tab", "") == "RECRUITMENT":
                obj_text = "Click 'INBOUND / CHOOSE ROOM' (or 'HIRE') on a candidate to onboard them."
        elif step.step_id == "CAR_RND_FRONT_WING" and self.management_hub and hasattr(self.management_hub, "tab_car"):
            tc = self.management_hub.tab_car
            if getattr(tc, "selected_part_category", "") == "FRONT_WING":
                obj_text = "Click 'BUILD NEXT GEN' to manufacture our Mk II specification (+ $125k Board subsidy)."
            else:
                obj_text = "Click the FRONT WING hotspot on the chassis blueprint to inspect its R&D development."
        elif step.step_id == "DRIVERS_ACADEMY" and self.management_hub and hasattr(self.management_hub, "tab_drivers"):
            td = self.management_hub.tab_drivers
            if getattr(td, "active_subtab", "") == "SCOUTS":
                obj_text = "Select a feeder seat tier (e.g. Tier 5 Karting) and click 'SIGN PROSPECT'."

        # Objective Box
        obj_box = pygame.Rect(card.x + 14, card.y + 68, card.width - 28, 52)
        pygame.draw.rect(surface, (20, 28, 40), obj_box, border_radius=4)
        pygame.draw.rect(surface, (0, 220, 255), obj_box, width=1, border_radius=4)
        UITheme.draw_icon(surface, "target", (obj_box.x + 10, obj_box.y + 14), color=(0, 240, 255), size=18)
        surface.blit(self.font_title.render("DIRECTIVE:", True, (0, 240, 255)), (obj_box.x + 34, obj_box.y + 6))
        self._render_wrapped_text(
            surface,
            obj_text,
            obj_box.x + 34,
            obj_box.y + 24,
            obj_box.width - 40,
            self.font_body,
            UITheme.TEXT_WHITE,
            line_spacing=14,
        )

        # Quick Context Chips Row
        step_chips = {
            "WELCOME_DASHBOARD": [
                ("calendar", "Calendar Planning", (0, 220, 255)),
                ("award", "Tier 3 Cup", (255, 215, 0)),
                ("flag", "Round 1 Prep", (0, 240, 140)),
            ],
            "FACTORY_BRAKES_EQUIPMENT": [
                ("disc", "Carbon Brakes", (255, 180, 50)),
                ("wrench", "Precision Dynos", (0, 220, 255)),
                ("coins", "+$800k Subsidy", (0, 240, 140)),
            ],
            "PERSONNEL_HIRING": [
                ("users", "Specialist Staff", (0, 220, 255)),
                ("award", "Dept Heads", (255, 215, 0)),
                ("circle-dollar-sign", "+$15k Stipend", (0, 240, 140)),
            ],
            "CAR_RND_FRONT_WING": [
                ("wind", "Front Wing Mk II", (0, 220, 255)),
                ("zap", "+Perf & Rel", (255, 215, 0)),
                ("coins", "+$125k Subsidy", (0, 240, 140)),
            ],
            "DRIVERS_ACADEMY": [
                ("graduation-cap", "Youth Academy", (0, 220, 255)),
                ("award", "Feeder Seats", (255, 215, 0)),
                ("coins", "+$30k Scholarship", (0, 240, 140)),
            ],
            "SPONSORS_COMMERCIAL": [
                ("circle-dollar-sign", "Weekly Retainers", (0, 240, 140)),
                ("target", "Finish Bonuses", (255, 215, 0)),
                ("award", "+$25k Signing", (0, 220, 255)),
            ],
            "LAUNCH_WEEKEND": [
                ("flag", "Trackside Haulers", (0, 240, 140)),
                ("gauge", "Free Practice", (0, 220, 255)),
                ("zap", "Sprint Race", (255, 215, 0)),
            ],
            "WEEKEND_PRACTICE": [
                ("sliders", "Setup Sliders", (0, 220, 255)),
                ("timer", "5-Lap Stints", (255, 215, 0)),
                ("award", "Setup Confidence", (0, 240, 140)),
            ],
            "WEEKEND_QUALIFYING": [
                ("timer", "3-Lap Shootout", (0, 220, 255)),
                ("flag", "Starting Grid", (255, 215, 0)),
                ("zap", "Single-Lap Bravery", (0, 240, 140)),
            ],
            "LIVE_RACE_PITWALL": [
                ("gauge", "Pace Control", (0, 240, 140)),
                ("disc", "Tire Management", (255, 180, 50)),
                ("wrench", "Box Strategy", (0, 220, 255)),
            ],
            "RACE_DEBRIEF": [
                ("award", "Championship Pts", (255, 215, 0)),
                ("circle-dollar-sign", "Prize Money", (0, 240, 140)),
                ("network", "Factory R&D", (0, 220, 255)),
            ],
        }
        chips = step_chips.get(
            step.step_id, [("zap", "Key Milestone", (0, 220, 255)), ("award", "Progression", (255, 215, 0))]
        )
        chip_w = (card.width - 28 - (len(chips) - 1) * 6) // len(chips)
        for c_idx, (c_ic, c_lbl, c_col) in enumerate(chips):
            cx = card.x + 14 + c_idx * (chip_w + 6)
            c_rect = pygame.Rect(cx, card.y + 126, chip_w, 24)
            pygame.draw.rect(surface, (18, 24, 34), c_rect, border_radius=3)
            pygame.draw.rect(surface, (38, 48, 62), c_rect, width=1, border_radius=3)
            UITheme.draw_icon(surface, c_ic, (c_rect.x + 6, c_rect.y + 5), color=c_col, size=12)
            disp_lbl = self.font_badge.render(c_lbl, True, c_col)
            surface.blit(disp_lbl, (c_rect.x + 22, c_rect.y + 5))

        # Reward Banner (if any)
        if step.reward_note:
            reward_rect = pygame.Rect(card.x + 14, card.bottom - 74, card.width - 28, 26)
            pygame.draw.rect(surface, (18, 38, 28), reward_rect, border_radius=3)
            pygame.draw.rect(surface, (0, 220, 120), reward_rect, width=1, border_radius=3)
            UITheme.draw_icon(surface, "award", (reward_rect.x + 8, reward_rect.y + 6), color=(0, 240, 140), size=14)
            rew_surf = self.font_reward.render(step.reward_note, True, (0, 255, 140))
            surface.blit(rew_surf, (reward_rect.x + 26, reward_rect.y + 5))

        # Bottom Button Row (Synchronized with handle_event)
        btn_skip, btn_back, btn_next = self._get_card_buttons(card)

        # Skip Tutorial Button (Always available!)
        pygame.draw.rect(surface, (30, 36, 48), btn_skip, border_radius=3)
        pygame.draw.rect(surface, (70, 80, 95), btn_skip, width=1, border_radius=3)
        sk_lbl = self.font_btn.render("Skip Tutorial", True, (170, 180, 195))
        surface.blit(sk_lbl, (btn_skip.x + (btn_skip.width - sk_lbl.get_width()) // 2, btn_skip.y + 8))

        # Back Button (if past Step 1)
        if self.manager.current_step_index > 0:
            pygame.draw.rect(surface, (25, 32, 44), btn_back, border_radius=3)
            pygame.draw.rect(surface, (50, 65, 85), btn_back, width=1, border_radius=3)
            bk_lbl = self.font_btn.render("< Back", True, UITheme.TEXT_WHITE)
            surface.blit(bk_lbl, (btn_back.x + (btn_back.width - bk_lbl.get_width()) // 2, btn_back.y + 8))

        # Primary Action / Next Button
        pygame.draw.rect(surface, (0, 180, 110), btn_next, border_radius=3)
        pygame.draw.rect(surface, (0, 240, 150), btn_next, width=1, border_radius=3)
        nx_lbl = self.font_btn.render(step.action_label, True, (10, 24, 18))
        surface.blit(nx_lbl, (btn_next.x + (btn_next.width - nx_lbl.get_width()) // 2, btn_next.y + 8))

        # Floating Info Tooltip if info button is hovered
        if is_info_hover:
            UITheme.draw_tooltip(
                surface,
                step.get_lore(),
                (info_btn.centerx, info_btn.bottom + 4),
                title="ADVISOR BRIEFING & LORE",
                icon="help-circle",
                max_width=360,
            )

    def _render_wrapped_text(
        self,
        surface: pygame.Surface,
        text: str,
        x: int,
        y: int,
        max_width: int,
        font: pygame.font.Font,
        color: Tuple[int, int, int],
        line_spacing: int = 15,
    ):
        """Helper to render multi-line and paragraph-wrapped text cleanly."""
        paragraphs = text.split("\n")
        cur_y = y

        for p in paragraphs:
            if not p.strip():
                cur_y += line_spacing // 2
                continue

            words = p.split(" ")
            cur_line = ""

            for w in words:
                test_line = f"{cur_line} {w}".strip()
                if font.size(test_line)[0] <= max_width:
                    cur_line = test_line
                else:
                    if cur_line:
                        surface.blit(font.render(cur_line, True, color), (x, cur_y))
                        cur_y += line_spacing
                    cur_line = w

            if cur_line:
                surface.blit(font.render(cur_line, True, color), (x, cur_y))
                cur_y += line_spacing
