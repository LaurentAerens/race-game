"""
Personnel & Organizational Hierarchy Tab.
Features the full interactive Personnel Tree (CEO, Category Directors, Department Heads, Staff Desks & Open Slots),
Targeted Spot Hiring & Inbound Tryouts, Department Destination Selector Modal, Employee Spot Reassignment,
Headhunter Paddock (rival poaching), and Employee Details Inspector.
"""

from typing import Any, Dict, Optional

import pygame

from ...database.career_db import FACILITY_SPECIALTY_MAP
from ...management.engineering_manager import EngineeringManager
from ...management.game_manager import GameManager
from ..theme import UITheme


class PersonnelTab:
    """Master Personnel Management Screen with Org Tree, Open Desks, Destination Picker, and Spot Reassignment."""

    def __init__(self, screen_width: int, screen_height: int):
        self.width = screen_width
        self.height = screen_height

        self.sub_tab: str = "TREE"  # 'TREE', 'RECRUITMENT', 'HEADHUNTER', 'POLICIES'
        self.selected_category: str = "ENGINEERING"  # Focused department on Executive Org Deck
        self.inspected_personnel_id: Optional[int] = None
        self.inspected_applicant_id: Optional[int] = None

        # Targeted Spot Assignment Context
        self.target_assignment_node: Optional[str] = None
        self.target_assignment_role: str = "STAFF"  # 'STAFF', 'INTERN', 'HEAD', 'DIRECTOR'
        self.target_assignment_slot_desc: str = ""

        # Destination Picker Modal Context (when picking where to assign an applicant or moving staff)
        self.destination_picker_data: Optional[Dict[str, Any]] = None

        self.scroll_y: float = 0.0
        self.max_scroll: float = 0.0
        self.is_dragging_scrollbar: bool = False
        self.drag_mouse_start_y: float = 0.0
        self.drag_scroll_start_y: float = 0.0
        self.scrollbar_track_rect: Optional[pygame.Rect] = None
        self.scrollbar_thumb_rect: Optional[pygame.Rect] = None

        self.status_message: str = (
            "Manage your team hierarchy, appoint Category Directors, and recruit into open desks."
        )

        self._init_fonts()

    def _init_fonts(self):
        self.font_title = UITheme.get_font(13, bold=True)
        self.font_card_title = UITheme.get_font(12, bold=True)
        self.font_body = UITheme.get_font(11, bold=False)
        self.font_badge = UITheme.get_font(10, bold=True)
        self.font_btn = UITheme.get_font(10, bold=True)
        self.font_mini = UITheme.get_font(9, bold=False)

    def resize(self, width: int, height: int):
        self.width = width
        self.height = height
        self._init_fonts()

    def set_hiring_target(self, node_id: str, role: str = "STAFF", slot_desc: str = ""):
        """Sets a targeted facility destination for hiring and switches to the Recruitment tab."""
        self.target_assignment_node = node_id
        self.target_assignment_role = role
        self.target_assignment_slot_desc = slot_desc
        self.sub_tab = "RECRUITMENT"
        self.scroll_y = 0.0
        self.status_message = f"Select an applicant to assign to {node_id} ({slot_desc or role})."

    def handle_scroll(self, event: pygame.event.Event) -> bool:
        """Handles mouse wheel scrolling across sub-tabs and modal."""
        if self.destination_picker_data is not None:
            # Scroll inside destination picker modal
            if event.type == pygame.MOUSEWHEEL:
                cur_s = self.destination_picker_data.get("scroll_y", 0.0)
                max_s = self.destination_picker_data.get("max_scroll", 0.0)
                new_s = cur_s + event.y * 36.0
                self.destination_picker_data["scroll_y"] = min(0.0, max(-max_s, new_s))
                return True
            return True

        if event.type == pygame.MOUSEWHEEL:
            self.scroll_y += event.y * 36.0
            self.scroll_y = min(0.0, max(-self.max_scroll, self.scroll_y))
            return True
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:
                self.scroll_y += 36.0
                self.scroll_y = min(0.0, max(-self.max_scroll, self.scroll_y))
                return True
            elif event.button == 5:
                self.scroll_y -= 36.0
                self.scroll_y = min(0.0, max(-self.max_scroll, self.scroll_y))
                return True
        return False

    def handle_mouse_drag(self, event: pygame.event.Event) -> bool:
        """Handles scrollbar dragging and track jumping."""
        if self.destination_picker_data is not None:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.scrollbar_thumb_rect and self.scrollbar_thumb_rect.collidepoint(mx, my):
                self.is_dragging_scrollbar = True
                self.drag_mouse_start_y = my
                self.drag_scroll_start_y = self.scroll_y
                return True
            elif self.scrollbar_track_rect and self.scrollbar_track_rect.collidepoint(mx, my):
                track_h = self.scrollbar_track_rect.height
                rel_y = my - self.scrollbar_track_rect.y
                target_ratio = max(0.0, min(1.0, rel_y / track_h))
                self.scroll_y = -target_ratio * self.max_scroll
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging_scrollbar = False
        elif event.type == pygame.MOUSEMOTION and self.is_dragging_scrollbar:
            if self.scrollbar_track_rect and self.scrollbar_thumb_rect and self.max_scroll > 0:
                dy = event.pos[1] - self.drag_mouse_start_y
                track_h = self.scrollbar_track_rect.height - self.scrollbar_thumb_rect.height
                if track_h > 0:
                    scroll_delta = (dy / track_h) * self.max_scroll
                    self.scroll_y = min(0.0, max(-self.max_scroll, self.drag_scroll_start_y - scroll_delta))
                return True
        return False

    def _draw_scrollbar(self, surface: pygame.Surface, canvas_rect: pygame.Rect):
        """Renders an interactive vertical scrollbar with track and thumb."""
        if self.max_scroll > 0:
            track_w = 6
            track_x = canvas_rect.x + canvas_rect.width - track_w - 3
            track_y = canvas_rect.y + 4
            track_h = canvas_rect.height - 8
            self.scrollbar_track_rect = pygame.Rect(track_x, track_y, track_w, track_h)
            pygame.draw.rect(surface, (20, 26, 36), self.scrollbar_track_rect, border_radius=3)

            thumb_h = max(24, int(track_h * (canvas_rect.height / (canvas_rect.height + self.max_scroll))))
            scroll_ratio = abs(self.scroll_y) / self.max_scroll if self.max_scroll > 0 else 0.0
            thumb_y = track_y + int((track_h - thumb_h) * scroll_ratio)
            self.scrollbar_thumb_rect = pygame.Rect(track_x, thumb_y, track_w, thumb_h)
            pygame.draw.rect(
                surface,
                (0, 220, 255) if self.is_dragging_scrollbar else (80, 105, 135),
                self.scrollbar_thumb_rect,
                border_radius=3,
            )
        else:
            self.scrollbar_track_rect = None
            self.scrollbar_thumb_rect = None

    def handle_click(self, mx: int, my: int, gm: GameManager, em: Optional[EngineeringManager] = None) -> bool:
        """Processes clicks across sub-tabs, org tree nodes, recruitments, destination modals, and inspector actions."""
        # 1. Clicks inside Destination Picker Modal (if open)
        if self.destination_picker_data is not None:
            modal_w = min(780, self.width - 80)
            modal_h = min(540, self.height - 100)
            modal_x = (self.width - modal_w) // 2
            modal_y = (self.height - modal_h) // 2

            close_btn = pygame.Rect(modal_x + modal_w - 75, modal_y + 12, 65, 24)
            if close_btn.collidepoint(mx, my):
                self.destination_picker_data = None
                return True

            list_canvas = pygame.Rect(modal_x + 12, modal_y + 80, modal_w - 24, modal_h - 96)
            if list_canvas.collidepoint(mx, my):
                fac_list = gm.staff_manager.get_unlocked_facilities_with_capacity(gm.team_id)
                m_scroll = self.destination_picker_data.get("scroll_y", 0.0)
                card_y = list_canvas.y + m_scroll

                for fac in fac_list:
                    card_r = pygame.Rect(list_canvas.x + 4, card_y, list_canvas.width - 8, 58)
                    assign_btn = pygame.Rect(card_r.x + card_r.width - 150, card_r.y + 14, 140, 28)

                    if assign_btn.collidepoint(mx, my):
                        d_type = self.destination_picker_data["type"]
                        target_node = fac["node_id"]

                        if d_type == "APPLICANT":
                            app_id = self.destination_picker_data["id"]
                            success, msg = gm.staff_manager.hire_applicant(gm.team_id, app_id, target_node)
                            self.status_message = msg
                        elif d_type == "EXISTING_STAFF":
                            p_id = self.destination_picker_data["id"]
                            success, msg = gm.staff_manager.reassign_personnel(
                                gm.team_id, p_id, target_node, new_role="STAFF"
                            )
                            self.status_message = msg
                        elif d_type == "PROMOTE_HEAD":
                            p_id = self.destination_picker_data["id"]
                            success, msg = gm.staff_manager.reassign_personnel(
                                gm.team_id, p_id, target_node, new_role="DEPARTMENT_HEAD"
                            )
                            self.status_message = msg
                        elif d_type == "POACH":
                            p_id = self.destination_picker_data["id"]
                            s_bonus = self.destination_picker_data["bonus"]
                            s_offered = self.destination_picker_data["salary"]
                            success, msg = gm.staff_manager.headhunt_rival_personnel(
                                gm.team_id, p_id, s_bonus, s_offered
                            )
                            if success:
                                gm.staff_manager.reassign_personnel(gm.team_id, p_id, target_node, new_role="STAFF")
                            self.status_message = msg

                        self.destination_picker_data = None
                        self.target_assignment_node = None
                        return True
                    card_y += 66
            return True

        # 2. Sub-Tab Bar
        tab_tree_rect = pygame.Rect(24, 62, 160, 26)
        tab_rec_rect = pygame.Rect(188, 62, 175, 26)
        tab_head_rect = pygame.Rect(367, 62, 175, 26)
        tab_pol_rect = pygame.Rect(546, 62, 205, 26)

        if tab_tree_rect.collidepoint(mx, my):
            self.sub_tab = "TREE"
            self.scroll_y = 0.0
            return True
        elif tab_rec_rect.collidepoint(mx, my):
            self.sub_tab = "RECRUITMENT"
            self.scroll_y = 0.0
            return True
        elif tab_head_rect.collidepoint(mx, my):
            self.sub_tab = "HEADHUNTER"
            self.scroll_y = 0.0
            return True
        elif tab_pol_rect.collidepoint(mx, my):
            self.sub_tab = "POLICIES"
            self.scroll_y = 0.0
            return True

        # 3. Employee Inspector Drawer
        if self.inspected_personnel_id is not None:
            drawer_x = self.width - 440
            drawer_rect = pygame.Rect(drawer_x, 60, 416, self.height - 75)
            if drawer_rect.collidepoint(mx, my):
                close_btn = pygame.Rect(drawer_x + 416 - 65, 66, 55, 22)
                if close_btn.collidepoint(mx, my):
                    self.inspected_personnel_id = None
                    return True

                with gm.db.get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT * FROM personnel WHERE id = ?;", (self.inspected_personnel_id,))
                    p_info = dict(cur.fetchone()) if cur.fetchone() else {}

                if p_info:
                    sy = 104 + 48 + 7 * 20 + 8
                    reassign_btn = pygame.Rect(drawer_x + 14, sy + 56, 185, 26)
                    if reassign_btn.collidepoint(mx, my):
                        self.destination_picker_data = {
                            "type": "EXISTING_STAFF",
                            "id": p_info["id"],
                            "name": p_info["name"],
                            "specialty": p_info.get("specialty"),
                            "role": p_info.get("role_type"),
                            "salary": float(p_info.get("salary_monthly", 8000)),
                            "scroll_y": 0.0,
                            "max_scroll": 0.0,
                        }
                        return True

                    if p_info.get("role_type") != "DEPARTMENT_HEAD":
                        p_head_btn = pygame.Rect(drawer_x + 210, sy + 56, 185, 26)
                        if p_head_btn.collidepoint(mx, my):
                            gm.staff_manager.promote_to_department_head(
                                gm.team_id, p_info["id"], p_info.get("facility_node_id")
                            )
                            return True

                    raise_btn = pygame.Rect(drawer_x + 14, sy + 90, 185, 26)
                    if raise_btn.collidepoint(mx, my):
                        gm.staff_manager.offer_raise(
                            p_info["id"], round(float(p_info.get("salary_monthly", 8000)) * 1.25, 0)
                        )
                        return True

                    fire_btn = pygame.Rect(drawer_x + 210, sy + 90, 185, 26)
                    if fire_btn.collidepoint(mx, my):
                        gm.staff_manager.fire_personnel(gm.team_id, p_info["id"])
                        self.inspected_personnel_id = None
                        return True
                return True

        # 4. Tree Tab Clicks
        # 4. Tree Tab Clicks (Split-Screen Executive Org Deck)
        if self.sub_tab == "TREE":
            depts = ["ENGINEERING", "MANUFACTURING", "TESTING", "POWERTRAIN", "COMMERCIAL", "HR", "TRACKSIDE"]
            content_w = self.width - (470 if self.inspected_personnel_id else 48)
            content_rect = pygame.Rect(24, 90, content_w, self.height - 132)

            left_x = content_rect.x + 8
            left_y = content_rect.y + 42
            left_w = 260
            left_h = content_rect.bottom - left_y - 6
            left_rect = pygame.Rect(left_x, left_y, left_w, left_h)

            card_h = max(42, (left_h - (len(depts) - 1) * 6 - 8) // len(depts))
            for idx, d_name in enumerate(depts):
                card_y = left_y + 4 + idx * (card_h + 6)
                card_r = pygame.Rect(left_x + 4, card_y, left_w - 8, card_h)
                if card_r.collidepoint(mx, my):
                    self.selected_category = d_name
                    self.scroll_y = 0.0
                    return True

            right_x = left_rect.right + 8
            right_w = content_rect.right - right_x - 8
            right_canvas = pygame.Rect(right_x, left_y, right_w, left_h)

            if right_canvas.collidepoint(mx, my):
                active_dept = self.selected_category if self.selected_category in depts else "ENGINEERING"
                directors = gm.staff_manager.get_category_directors(gm.team_id)
                dir_obj = directors.get(active_dept)

                curr_y = right_canvas.y + self.scroll_y + 6
                dir_box = pygame.Rect(right_canvas.x + 6, curr_y, right_canvas.width - 12, 48)

                if dir_box.collidepoint(mx, my):
                    if dir_obj:
                        self.inspected_personnel_id = dir_obj["id"]
                    else:
                        self.set_hiring_target("", role="DIRECTOR", slot_desc=f"{active_dept} Director")
                    return True

                curr_y += 56

                with gm.db.get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute(
                        "SELECT node_id, current_tier, is_unlocked FROM team_facilities WHERE team_id = ? AND is_unlocked = 1;",
                        (gm.team_id,),
                    )
                    unlocked_facs = {r[0]: r[1] for r in cur.fetchall()}
                    cur.execute("SELECT id, department, name FROM facility_nodes WHERE department = ?;", (active_dept,))
                    fac_nodes = cur.fetchall()

                for f_id, _, f_name in fac_nodes:
                    if f_id not in unlocked_facs:
                        continue
                    f_tier = unlocked_facs[f_id]
                    p_data = gm.staff_manager.get_facility_personnel(gm.team_id, f_id, f_tier)

                    grid_items = []
                    for s_idx, s in enumerate(p_data["staff"]):
                        grid_items.append(("STAFF", s_idx, s))
                    for v_idx in range(p_data["vacant_staff_slots"]):
                        grid_items.append(("VACANT", v_idx, None))
                    grid_items.append(("INTERN", 0, p_data.get("intern")))

                    num_rows = (len(grid_items) + 1) // 2
                    room_h = 32 + 30 + num_rows * 40 + 8
                    room_box = pygame.Rect(right_canvas.x + 6, curr_y, right_canvas.width - 12, room_h)

                    if room_box.collidepoint(mx, my):
                        # Head slot click
                        h_slot = pygame.Rect(room_box.x + 8, room_box.y + 28, room_box.width - 16, 24)
                        if h_slot.collidepoint(mx, my):
                            if p_data["head"]:
                                self.inspected_personnel_id = p_data["head"]["id"]
                            else:
                                self.set_hiring_target(f_id, role="HEAD", slot_desc=f"Head of {f_name}")
                            return True

                        # Grid chips click
                        grid_col_w = (room_box.width - 24) // 2
                        for g_idx, item in enumerate(grid_items):
                            row = g_idx // 2
                            col = g_idx % 2
                            chip_x = room_box.x + 8 + col * (grid_col_w + 8)
                            chip_y = room_box.y + 56 + row * 40
                            chip_r = pygame.Rect(chip_x, chip_y, grid_col_w, 36)

                            if chip_r.collidepoint(mx, my):
                                itype = item[0]
                                if itype == "STAFF":
                                    self.inspected_personnel_id = item[2]["id"]
                                elif itype == "VACANT":
                                    desk_num = len(p_data["staff"]) + item[1] + 1
                                    self.set_hiring_target(f_id, role="STAFF", slot_desc=f"Desk #{desk_num}")
                                elif itype == "INTERN":
                                    intern = item[2]
                                    if intern:
                                        self.inspected_personnel_id = intern["id"]
                                    else:
                                        self.set_hiring_target(f_id, role="INTERN", slot_desc="6-Month Intern Tryout")
                                return True

                    curr_y += room_h + 10

                return True

        # 5. Recruitment Tab Clicks
        elif self.sub_tab == "RECRUITMENT":
            rec_canvas = pygame.Rect(24, 94, self.width - 48, self.height - 135)
            if self.target_assignment_node:
                banner_cancel_btn = pygame.Rect(rec_canvas.x + rec_canvas.width - 150, rec_canvas.y + 6, 140, 24)
                if banner_cancel_btn.collidepoint(mx, my):
                    self.target_assignment_node = None
                    self.status_message = "Cleared target filter."
                    return True

            if rec_canvas.collidepoint(mx, my):
                apps = gm.staff_manager.get_inbound_applications(gm.team_id)
                item_y = rec_canvas.y + self.scroll_y + (48 if self.target_assignment_node else 36)

                for app in apps:
                    card_r = pygame.Rect(rec_canvas.x + 10, item_y, rec_canvas.width - 20, 72)
                    hire_btn = pygame.Rect(card_r.x + card_r.width - 210, card_r.y + 22, 130, 26)
                    rej_btn = pygame.Rect(card_r.x + card_r.width - 74, card_r.y + 22, 65, 26)

                    if hire_btn.collidepoint(mx, my):
                        if self.target_assignment_node:
                            success, msg = gm.staff_manager.hire_applicant(
                                gm.team_id, app["application_id"], self.target_assignment_node
                            )
                            self.status_message = msg
                            if success:
                                self.target_assignment_node = None
                            return True
                        else:
                            self.destination_picker_data = {
                                "type": "APPLICANT",
                                "id": app["application_id"],
                                "name": app["name"],
                                "specialty": app.get("specialty"),
                                "is_intern": bool(app.get("is_internship_tryout")),
                                "salary": float(app.get("salary_requested", 1000)),
                                "scroll_y": 0.0,
                                "max_scroll": 0.0,
                            }
                            return True

                    elif rej_btn.collidepoint(mx, my):
                        with gm.db.get_connection() as conn:
                            cur = conn.cursor()
                            cur.execute("DELETE FROM personnel_applications WHERE id = ?;", (app["application_id"],))
                            cur.execute("DELETE FROM personnel WHERE id = ?;", (app["id"],))
                            conn.commit()
                        self.status_message = f"Dismissed application from {app['name']}."
                        return True

                    item_y += 80
                return True

        # 6. Headhunter Tab Clicks
        elif self.sub_tab == "HEADHUNTER":
            head_canvas = pygame.Rect(24, 94, self.width - 48, self.height - 135)
            if head_canvas.collidepoint(mx, my):
                with gm.db.get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute(
                        """
                    SELECT p.*, t.name as team_name
                    FROM personnel p
                    JOIN teams t ON p.team_id = t.id
                    WHERE p.team_id != ? AND p.role_type IN ('CATEGORY_DIRECTOR', 'DEPARTMENT_HEAD', 'STAFF')
                    ORDER BY p.stat_engineering DESC LIMIT 10;
                    """,
                        (gm.team_id,),
                    )
                    rival_staff = [dict(r) for r in cur.fetchall()]

                item_y = head_canvas.y + self.scroll_y + 36
                for r_p in rival_staff:
                    r_card = pygame.Rect(head_canvas.x + 10, item_y, head_canvas.width - 20, 68)
                    poach_btn = pygame.Rect(r_card.x + r_card.width - 160, r_card.y + 18, 150, 30)

                    if poach_btn.collidepoint(mx, my):
                        cur_sal = float(r_p.get("salary_monthly", 8000.0))
                        offered_sal = round(cur_sal * 1.35, 0)
                        signing_bonus = round(cur_sal * 4.0, 0)
                        self.destination_picker_data = {
                            "type": "POACH",
                            "id": r_p["id"],
                            "name": r_p["name"],
                            "specialty": r_p.get("specialty"),
                            "salary": offered_sal,
                            "bonus": signing_bonus,
                            "scroll_y": 0.0,
                            "max_scroll": 0.0,
                        }
                        return True

                    item_y += 76
                return True

        # 7. HR Policies Tab Clicks
        elif self.sub_tab == "POLICIES":
            pol_canvas = pygame.Rect(24, 94, self.width - 48, self.height - 135)
            if pol_canvas.collidepoint(mx, my):
                policies = gm.db.get_hr_policies(gm.team_id)
                with gm.db.get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute(
                        "SELECT node_id, current_tier, is_unlocked FROM team_facilities WHERE team_id = ?;",
                        (gm.team_id,),
                    )
                    fac_tiers = {r[0]: (r[1] if r[2] else 0) for r in cur.fetchall()}

                toggle_defs = [
                    ("auto_fill_desks", "hr_recruitment", 1),
                    ("auto_intern_pipeline", "hr_recruitment", 2),
                    ("min_intern_potential", "hr_recruitment", 2),
                    ("auto_payroll", "hr_payroll", 1),
                    ("auto_equip_procure", "hr_equipment_procurement", 1),
                    ("auto_cull", "hr_performance_cull", 1),
                    ("auto_replace", "hr_workforce_optimizer", 1),
                    ("auto_headhunt", "hr_headhunting", 1),
                ]

                item_y = pol_canvas.y + self.scroll_y + 36
                for key, req_fac, req_tier in toggle_defs:
                    is_unlocked = fac_tiers.get(req_fac, 0) >= req_tier
                    card_r = pygame.Rect(pol_canvas.x + 8, item_y, pol_canvas.width - 16, 60)

                    if key == "min_intern_potential":
                        if is_unlocked:
                            btn_minus = pygame.Rect(card_r.x + card_r.width - 140, card_r.y + 16, 30, 26)
                            btn_plus = pygame.Rect(card_r.x + card_r.width - 50, card_r.y + 16, 30, 26)
                            if btn_minus.collidepoint(mx, my):
                                cur_val = policies.get("min_intern_potential", 75)
                                gm.db.update_hr_policy(gm.team_id, "min_intern_potential", max(50, cur_val - 5))
                                return True
                            elif btn_plus.collidepoint(mx, my):
                                cur_val = policies.get("min_intern_potential", 75)
                                gm.db.update_hr_policy(gm.team_id, "min_intern_potential", min(95, cur_val + 5))
                                return True
                    else:
                        toggle_btn = pygame.Rect(card_r.x + card_r.width - 130, card_r.y + 16, 110, 26)
                        if toggle_btn.collidepoint(mx, my) and is_unlocked:
                            cur_en = bool(policies.get(key, 0))
                            gm.db.update_hr_policy(gm.team_id, key, int(not cur_en))
                            return True

                    item_y += 68

                return True

        return False

    def render(
        self,
        surface: pygame.Surface,
        gm: GameManager,
        em: Optional[EngineeringManager] = None,
        dev_gain_mult: float = 1.0,
        principal_name: str = "Alex Mercer",
    ):
        """Renders the Personnel Hub with Hierarchy Tree, Recruitment, Destination Modal, and Staff Drawer."""
        content_w = self.width - (450 if self.inspected_personnel_id else 48)

        # Draw Nav
        t_x = 24
        nav_tabs = [
            ("TREE", "ORG HIERARCHY & DESKS", "network"),
            ("RECRUITMENT", "RECRUITMENT & TRYOUTS", "users"),
            ("HEADHUNTER", "HEADHUNTER PADDOCK", "target"),
            ("POLICIES", "HR DIRECTIVES & POLICIES", "wrench"),
        ]
        for tab_key, tab_label, tab_icon in nav_tabs:
            t_rect = pygame.Rect(t_x, 62, 175 if tab_key != "POLICIES" else 205, 26)
            is_active = self.sub_tab == tab_key
            pygame.draw.rect(
                surface,
                (30, 50, 75) if is_active else (18, 24, 34),
                t_rect,
                border_top_left_radius=4,
                border_top_right_radius=4,
            )
            pygame.draw.rect(
                surface,
                (0, 220, 255) if is_active else (35, 45, 60),
                t_rect,
                width=1,
                border_top_left_radius=4,
                border_top_right_radius=4,
            )
            col = (0, 220, 255) if is_active else (150, 165, 180)
            UITheme.draw_icon(surface, tab_icon, (t_rect.x + 8, t_rect.y + 5), color=col, size=15)
            t_txt = self.font_badge.render(tab_label, True, col)
            surface.blit(t_txt, (t_rect.x + 28, t_rect.y + 6))
            t_x += t_rect.width + 4

        content_rect = pygame.Rect(24, 90, content_w, self.height - 132)
        pygame.draw.rect(surface, (12, 16, 22), content_rect, border_radius=3)
        pygame.draw.rect(surface, (35, 45, 60), content_rect, width=1, border_radius=3)

        # =====================================================================
        # SUB-TAB A: PERSONNEL ORG DECK (SPLIT SCREEN)
        # =====================================================================
        if self.sub_tab == "TREE":
            depts = ["ENGINEERING", "MANUFACTURING", "TESTING", "POWERTRAIN", "COMMERCIAL", "HR", "TRACKSIDE"]
            dept_icons = {
                "ENGINEERING": "wrench",
                "MANUFACTURING": "factory",
                "TESTING": "gauge",
                "POWERTRAIN": "cpu",
                "COMMERCIAL": "circle-dollar-sign",
                "HR": "users",
                "TRACKSIDE": "flag",
            }
            if self.selected_category not in depts:
                self.selected_category = "ENGINEERING"

            directors = gm.staff_manager.get_category_directors(gm.team_id)

            with gm.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT node_id, current_tier, is_unlocked FROM team_facilities WHERE team_id = ? AND is_unlocked = 1;",
                    (gm.team_id,),
                )
                unlocked_facs = {r[0]: r[1] for r in cur.fetchall()}
                cur.execute("SELECT id, department, name FROM facility_nodes;")
                all_fac_nodes = cur.fetchall()
                cur.execute("SELECT COUNT(*), SUM(salary_monthly) FROM personnel WHERE team_id = ?;", (gm.team_id,))
                p_tot_row = cur.fetchone()
                total_staff_db = (p_tot_row[0] or 0) if p_tot_row else 0
                total_payroll_db = float(p_tot_row[1] or 0.0) if p_tot_row else 0.0

            nodes_by_dept = {}
            for f_id, f_dept, f_name in all_fac_nodes:
                nodes_by_dept.setdefault(f_dept, []).append((f_id, f_name))

            # Calculate total capacity and active directors
            total_capacity = 0
            dept_stats = {}
            total_perf_yield = 0.0
            for d_name in depts:
                d_facs = nodes_by_dept.get(d_name, [])
                d_staff = 0
                d_vacant = 0
                d_perf = 0.0
                for f_id, f_name in d_facs:
                    if f_id in unlocked_facs:
                        f_tier = unlocked_facs[f_id]
                        p_data = gm.staff_manager.get_facility_personnel(gm.team_id, f_id, f_tier)
                        d_staff += len(p_data["staff"])
                        d_vacant += p_data["vacant_staff_slots"]
                        p_out = gm.staff_manager.calculate_facility_staff_output(
                            gm.team_id, f_id, f_tier, dev_gain_mult
                        )
                        d_perf += p_out.get("final_perf", 0.0)
                d_cap = d_staff + d_vacant
                total_capacity += d_cap
                total_perf_yield += d_perf
                dept_stats[d_name] = {"staff": d_staff, "vacant": d_vacant, "cap": d_cap, "perf": d_perf}

            active_directors_count = sum(1 for d in directors.values() if d is not None)

            # 1. Top Executive Workforce Summary Bar
            exec_bar = pygame.Rect(content_rect.x + 8, content_rect.y + 6, content_rect.width - 16, 30)
            pygame.draw.rect(surface, (16, 22, 32), exec_bar, border_radius=3)
            pygame.draw.rect(surface, (35, 48, 65), exec_bar, width=1, border_radius=3)

            pct_staff = (total_staff_db / max(1, total_capacity)) * 100.0 if total_capacity > 0 else 0.0
            UITheme.draw_stat_item(
                surface,
                exec_bar.x + 12,
                exec_bar.y + 7,
                "users",
                f"STAFF: {total_staff_db}/{total_capacity} Desks ({pct_staff:.0f}%)",
                self.font_badge,
                text_color=(0, 240, 220),
                icon_color=(0, 240, 220),
                icon_size=13,
            )
            UITheme.draw_stat_item(
                surface,
                exec_bar.x + 230,
                exec_bar.y + 7,
                "circle-dollar-sign",
                f"PAYROLL: ${total_payroll_db:,.0f}/mo",
                self.font_badge,
                text_color=(255, 180, 50),
                icon_color=(255, 180, 50),
                icon_size=13,
            )
            UITheme.draw_stat_item(
                surface,
                exec_bar.x + 440,
                exec_bar.y + 7,
                "award",
                f"DIRECTORS: {active_directors_count}/7 Appointed",
                self.font_badge,
                text_color=(255, 215, 0),
                icon_color=(255, 215, 0),
                icon_size=13,
            )
            UITheme.draw_stat_item(
                surface,
                exec_bar.x + 650,
                exec_bar.y + 7,
                "zap",
                f"STAFF YIELD: +{total_perf_yield:.2f} Perf/wk",
                self.font_badge,
                text_color=(0, 255, 160),
                icon_color=(0, 255, 160),
                icon_size=13,
            )

            # 2. Left Column: Department Org Directory
            left_w = 260
            left_x = content_rect.x + 8
            left_y = exec_bar.bottom + 6
            left_h = content_rect.bottom - left_y - 6
            left_rect = pygame.Rect(left_x, left_y, left_w, left_h)
            pygame.draw.rect(surface, (14, 18, 25), left_rect, border_radius=3)
            pygame.draw.rect(surface, (32, 42, 56), left_rect, width=1, border_radius=3)

            card_h = max(42, (left_h - (len(depts) - 1) * 6 - 8) // len(depts))
            for idx, d_name in enumerate(depts):
                card_y = left_y + 4 + idx * (card_h + 6)
                card_r = pygame.Rect(left_x + 4, card_y, left_w - 8, card_h)
                is_sel = self.selected_category == d_name
                d_icon = dept_icons.get(d_name, "network")
                dir_obj = directors.get(d_name)
                st = dept_stats.get(d_name, {"staff": 0, "cap": 0, "perf": 0.0})

                bg_c = (26, 38, 54) if is_sel else (18, 24, 34)
                b_c = (0, 220, 255) if is_sel else (38, 50, 68)
                pygame.draw.rect(surface, bg_c, card_r, border_radius=3)
                pygame.draw.rect(surface, b_c, card_r, width=2 if is_sel else 1, border_radius=3)

                # Icon & Title
                UITheme.draw_icon(
                    surface,
                    d_icon,
                    (card_r.x + 6, card_r.y + 6),
                    color=(0, 220, 255) if is_sel else (150, 165, 180),
                    size=14,
                )
                surface.blit(
                    self.font_card_title.render(d_name, True, (0, 220, 255) if is_sel else UITheme.TEXT_WHITE),
                    (card_r.x + 24, card_r.y + 5),
                )

                # Director status or vacancy alert
                if dir_obj:
                    d_txt = f"Dir: {dir_obj['name']} (Lvl {dir_obj.get('stat_leadership', 50):.0f})"
                    surface.blit(self.font_mini.render(d_txt, True, (0, 255, 160)), (card_r.x + 24, card_r.y + 22))
                else:
                    surface.blit(
                        self.font_mini.render("VACANT DIRECTOR [APPOINT]", True, (255, 110, 110)),
                        (card_r.x + 24, card_r.y + 22),
                    )

                # Desks & Perf
                desk_str = f"{st['staff']}/{st['cap']} Desks"
                d_surf = self.font_mini.render(desk_str, True, (180, 200, 220))
                surface.blit(d_surf, (card_r.right - d_surf.get_width() - 6, card_r.y + 6))
                if st["perf"] > 0:
                    p_surf = self.font_mini.render(f"+{st['perf']:.1f} P", True, (0, 240, 140))
                    surface.blit(p_surf, (card_r.right - p_surf.get_width() - 6, card_r.y + 22))

            # 3. Right Column: Department Operations & Room Desks (Focused View)
            right_x = left_rect.right + 8
            right_w = content_rect.right - right_x - 8
            right_canvas = pygame.Rect(right_x, left_y, right_w, left_h)
            pygame.draw.rect(surface, (12, 16, 22), right_canvas, border_radius=3)
            pygame.draw.rect(surface, (32, 42, 56), right_canvas, width=1, border_radius=3)

            prev_clip = surface.get_clip()
            surface.set_clip(right_canvas)

            curr_y = right_canvas.y + self.scroll_y + 6
            active_dept = self.selected_category
            dir_obj = directors.get(active_dept)

            # Department Director Profile Card
            dir_box = pygame.Rect(right_canvas.x + 6, curr_y, right_canvas.width - 12, 48)
            if dir_obj:
                pygame.draw.rect(surface, (20, 28, 40), dir_box, border_radius=3)
                pygame.draw.rect(surface, (0, 220, 255), dir_box, width=1, border_radius=3)
                UITheme.draw_icon(surface, "briefcase", (dir_box.x + 8, dir_box.y + 8), color=(0, 220, 255), size=16)
                dir_title = f"{active_dept} DIRECTOR: {dir_obj['name']} (Age {dir_obj['age']}) | Spec: {dir_obj.get('specialty', 'GENERAL')}"
                surface.blit(
                    self.font_card_title.render(dir_title, True, (0, 220, 255)), (dir_box.x + 30, dir_box.y + 6)
                )
                # Stats
                ds_x = dir_box.x + 30
                ds_y = dir_box.y + 26
                ds_x += (
                    UITheme.draw_stat_item(
                        surface,
                        ds_x,
                        ds_y,
                        "award",
                        f"Leadership: {dir_obj.get('stat_leadership', 50):.0f}",
                        self.font_body,
                        text_color=(180, 200, 220),
                        icon_color=(255, 160, 200),
                        icon_size=12,
                        gap=3,
                    )
                    + 12
                )
                ds_x += (
                    UITheme.draw_stat_item(
                        surface,
                        ds_x,
                        ds_y,
                        "wrench",
                        f"Core: {dir_obj.get('stat_engineering', 50):.0f}",
                        self.font_body,
                        text_color=(180, 200, 220),
                        icon_color=(0, 220, 255),
                        icon_size=12,
                        gap=3,
                    )
                    + 12
                )
                UITheme.draw_stat_item(
                    surface,
                    ds_x,
                    ds_y,
                    "circle-dollar-sign",
                    f"${dir_obj.get('salary_monthly', 12000):,.0f}/mo",
                    self.font_body,
                    text_color=(180, 200, 220),
                    icon_color=(255, 200, 40),
                    icon_size=12,
                    gap=3,
                )
                # Action button
                dt_btn = pygame.Rect(dir_box.right - 90, dir_box.y + 12, 80, 24)
                UITheme.draw_button(surface, dt_btn, "DETAILS", self.font_btn, icon="user", icon_size=11)
            else:
                pygame.draw.rect(surface, (32, 20, 24), dir_box, border_radius=3)
                pygame.draw.rect(surface, (220, 70, 70), dir_box, width=1, border_radius=3)
                UITheme.draw_icon(
                    surface, "triangle-alert", (dir_box.x + 8, dir_box.y + 8), color=(255, 90, 90), size=16
                )
                surface.blit(
                    self.font_card_title.render(f"{active_dept} DIRECTOR: VACANT POST", True, (255, 90, 90)),
                    (dir_box.x + 30, dir_box.y + 6),
                )
                surface.blit(
                    self.font_body.render("Click [+ APPOINT] to recruit or promote a Director.", True, (190, 150, 150)),
                    (dir_box.x + 30, dir_box.y + 26),
                )
                ap_btn = pygame.Rect(dir_box.right - 105, dir_box.y + 12, 95, 24)
                UITheme.draw_button(
                    surface, ap_btn, "+ APPOINT", self.font_btn, bg_color=(180, 40, 40), icon="users", icon_size=11
                )

            curr_y += 56

            # Facility Rooms in this Department
            fac_nodes = nodes_by_dept.get(active_dept, [])
            for f_id, f_name in fac_nodes:
                if f_id not in unlocked_facs:
                    continue
                f_tier = unlocked_facs[f_id]
                p_data = gm.staff_manager.get_facility_personnel(gm.team_id, f_id, f_tier)
                p_out = gm.staff_manager.calculate_facility_staff_output(gm.team_id, f_id, f_tier, dev_gain_mult)

                # Construct grid items
                grid_items = []
                for s_idx, s in enumerate(p_data["staff"]):
                    grid_items.append(("STAFF", s_idx, s))
                for v_idx in range(p_data["vacant_staff_slots"]):
                    grid_items.append(("VACANT", v_idx, None))
                grid_items.append(("INTERN", 0, p_data.get("intern")))

                num_rows = (len(grid_items) + 1) // 2
                room_h = 32 + 30 + num_rows * 40 + 8
                room_box = pygame.Rect(right_canvas.x + 6, curr_y, right_canvas.width - 12, room_h)

                pygame.draw.rect(surface, (16, 22, 32), room_box, border_radius=3)
                pygame.draw.rect(surface, (45, 58, 75), room_box, width=1, border_radius=3)

                # Room Header
                UITheme.draw_icon(surface, "factory", (room_box.x + 8, room_box.y + 7), color=(255, 215, 0), size=15)
                r_title = f"{f_name} (Tier {f_tier})"
                surface.blit(
                    self.font_card_title.render(r_title, True, (255, 215, 0)), (room_box.x + 28, room_box.y + 6)
                )
                spec_str = f"Specialty: {p_data['target_specialty']} [+50% MATCH]"
                surface.blit(self.font_badge.render(spec_str, True, (0, 240, 220)), (room_box.x + 230, room_box.y + 7))
                out_str = f"Output: +{p_out['final_perf']:.2f} Perf"
                o_surf = self.font_badge.render(out_str, True, (0, 255, 160))
                surface.blit(o_surf, (room_box.right - o_surf.get_width() - 8, room_box.y + 7))

                # Dept Head Slot
                head = p_data["head"]
                h_slot = pygame.Rect(room_box.x + 8, room_box.y + 28, room_box.width - 16, 24)
                if head:
                    pygame.draw.rect(surface, (20, 32, 45), h_slot, border_radius=2)
                    is_match = head.get("specialty") == p_data["target_specialty"]
                    h_col = (0, 240, 140) if is_match else (220, 220, 220)
                    UITheme.draw_icon(surface, "award", (h_slot.x + 6, h_slot.y + 4), color=h_col, size=14)
                    h_txt = f"Head: {head['name']} (Age {head['age']} | {head.get('specialty')} {'[MATCH +50%]' if is_match else ''}) | {p_out['head_mult']:.2f}x Multiplier"
                    surface.blit(self.font_body.render(h_txt, True, h_col), (h_slot.x + 24, h_slot.y + 4))
                else:
                    pygame.draw.rect(surface, (36, 24, 24), h_slot, border_radius=2)
                    pygame.draw.rect(surface, (180, 70, 70), h_slot, width=1, border_radius=2)
                    UITheme.draw_icon(
                        surface, "triangle-alert", (h_slot.x + 6, h_slot.y + 4), color=(255, 120, 120), size=14
                    )
                    surface.blit(
                        self.font_body.render(
                            "Dept Head: VACANT - Click to Appoint / Recruit Head", True, (255, 120, 120)
                        ),
                        (h_slot.x + 24, h_slot.y + 4),
                    )

                # 2-Column Desk Grid
                grid_col_w = (room_box.width - 24) // 2
                for g_idx, item in enumerate(grid_items):
                    row = g_idx // 2
                    col = g_idx % 2
                    chip_x = room_box.x + 8 + col * (grid_col_w + 8)
                    chip_y = room_box.y + 56 + row * 40
                    chip_r = pygame.Rect(chip_x, chip_y, grid_col_w, 36)

                    itype = item[0]
                    if itype == "STAFF":
                        s = item[2]
                        pygame.draw.rect(surface, (18, 26, 36), chip_r, border_radius=3)
                        pygame.draw.rect(surface, (40, 52, 68), chip_r, width=1, border_radius=3)
                        is_match = s.get("specialty") == p_data["target_specialty"]
                        s_col = (0, 220, 255) if is_match else UITheme.TEXT_WHITE
                        UITheme.draw_icon(surface, "user", (chip_r.x + 6, chip_r.y + 6), color=s_col, size=13)
                        s_line1 = f"{s['name']} (Age {s['age']})"
                        surface.blit(self.font_badge.render(s_line1, True, s_col), (chip_r.x + 24, chip_r.y + 4))
                        s_line2 = f"{s.get('specialty')} | ${s.get('salary_monthly', 8000):,.0f}/mo"
                        surface.blit(
                            self.font_mini.render(s_line2, True, (150, 170, 190)), (chip_r.x + 24, chip_r.y + 19)
                        )
                    elif itype == "VACANT":
                        v_idx = item[1]
                        desk_num = len(p_data["staff"]) + v_idx + 1
                        pygame.draw.rect(surface, (14, 24, 34), chip_r, border_radius=3)
                        pygame.draw.rect(surface, (0, 160, 200), chip_r, width=1, border_radius=3)
                        UITheme.draw_icon(surface, "users", (chip_r.x + 6, chip_r.y + 10), color=(0, 220, 255), size=14)
                        surface.blit(
                            self.font_badge.render(f"OPEN DESK #{desk_num}", True, (0, 220, 255)),
                            (chip_r.x + 24, chip_r.y + 10),
                        )
                        r_btn = pygame.Rect(chip_r.right - 80, chip_r.y + 6, 74, 24)
                        UITheme.draw_button(surface, r_btn, "+ RECRUIT", self.font_mini, bg_color=(0, 120, 160))
                    elif itype == "INTERN":
                        intern = item[2]
                        if intern:
                            pygame.draw.rect(surface, (26, 20, 36), chip_r, border_radius=3)
                            pygame.draw.rect(surface, (140, 90, 200), chip_r, width=1, border_radius=3)
                            UITheme.draw_icon(
                                surface, "graduation-cap", (chip_r.x + 6, chip_r.y + 6), color=(180, 140, 255), size=14
                            )
                            i_l1 = f"Intern: {intern['name']}"
                            surface.blit(
                                self.font_badge.render(i_l1, True, (180, 140, 255)), (chip_r.x + 24, chip_r.y + 4)
                            )
                            i_l2 = f"Tryout Mo {intern.get('intern_months_completed', 0)}/6"
                            surface.blit(
                                self.font_mini.render(i_l2, True, (180, 150, 220)), (chip_r.x + 24, chip_r.y + 19)
                            )
                        else:
                            pygame.draw.rect(surface, (20, 18, 28), chip_r, border_radius=3)
                            pygame.draw.rect(surface, (100, 60, 150), chip_r, width=1, border_radius=3)
                            UITheme.draw_icon(
                                surface, "graduation-cap", (chip_r.x + 6, chip_r.y + 10), color=(180, 140, 255), size=14
                            )
                            surface.blit(
                                self.font_badge.render("OPEN INTERN DESK", True, (180, 140, 255)),
                                (chip_r.x + 24, chip_r.y + 10),
                            )
                            a_btn = pygame.Rect(chip_r.right - 75, chip_r.y + 6, 70, 24)
                            UITheme.draw_button(surface, a_btn, "+ ASSIGN", self.font_mini, bg_color=(100, 60, 150))

                curr_y += room_h + 10

            total_h = curr_y - (right_canvas.y + self.scroll_y)
            self.max_scroll = max(0.0, total_h - right_canvas.height + 20)
            surface.set_clip(prev_clip)
            self._draw_scrollbar(surface, right_canvas)

        # =====================================================================
        # SUB-TAB B: RECRUITMENT & INBOUND INTERNS
        # =====================================================================
        elif self.sub_tab == "RECRUITMENT":
            apps = gm.staff_manager.get_inbound_applications(gm.team_id)

            top_offset = 0
            if self.target_assignment_node:
                top_offset = 46
                banner_rect = pygame.Rect(content_rect.x + 8, content_rect.y + 8, content_rect.width - 16, 36)
                pygame.draw.rect(surface, (0, 48, 64), banner_rect, border_radius=3)
                pygame.draw.rect(surface, (0, 220, 255), banner_rect, width=1, border_radius=3)

                UITheme.draw_icon(
                    surface, "target", (banner_rect.x + 10, banner_rect.y + 9), color=(255, 215, 0), size=18
                )
                target_spec = FACILITY_SPECIALTY_MAP.get(self.target_assignment_node, "COMPOSITES")
                banner_txt = f"TARGET SPOT: {self.target_assignment_node.replace('_', ' ').title()} ({self.target_assignment_slot_desc or self.target_assignment_role}) | Ideal Specialty: {target_spec}"
                surface.blit(
                    self.font_card_title.render(banner_txt, True, (255, 215, 0)),
                    (banner_rect.x + 34, banner_rect.y + 8),
                )

                cancel_btn = pygame.Rect(banner_rect.x + banner_rect.width - 140, banner_rect.y + 5, 130, 26)
                UITheme.draw_button(surface, cancel_btn, "Clear Target", self.font_btn, icon="x", icon_size=12)

            UITheme.draw_icon(
                surface, "users", (content_rect.x + 14, content_rect.y + 14 + top_offset), color=(0, 220, 255), size=18
            )
            surface.blit(
                self.font_title.render(
                    f"INBOUND CANDIDATES & 6-MONTH TALENT TRYOUTS ({len(apps)} Pending):", True, (0, 220, 255)
                ),
                (content_rect.x + 38, content_rect.y + 12 + top_offset),
            )

            rec_canvas = pygame.Rect(
                content_rect.x + 4,
                content_rect.y + 36 + top_offset,
                content_rect.width - 8,
                content_rect.height - 40 - top_offset,
            )
            prev_clip = surface.get_clip()
            surface.set_clip(rec_canvas)

            item_y = rec_canvas.y + self.scroll_y
            target_spec = (
                FACILITY_SPECIALTY_MAP.get(self.target_assignment_node, "") if self.target_assignment_node else ""
            )

            for app in apps:
                card_r = pygame.Rect(rec_canvas.x + 8, item_y, rec_canvas.width - 16, 72)
                is_tryout = bool(app.get("is_internship_tryout"))
                pygame.draw.rect(surface, (18, 24, 34), card_r, border_radius=3)
                pygame.draw.rect(
                    surface, (160, 100, 240) if is_tryout else (0, 180, 220), card_r, width=1, border_radius=3
                )

                c_icon = "graduation-cap" if is_tryout else "user"
                c_icon_col = (180, 140, 255) if is_tryout else (0, 220, 255)
                UITheme.draw_icon(surface, c_icon, (card_r.x + 10, card_r.y + 8), color=c_icon_col, size=16)

                is_spec_match = target_spec and app.get("specialty") == target_spec
                match_tag = " [MATCH +50%]" if is_spec_match else ""
                role_tag = "[ 6-MO TRYOUT ]" if is_tryout else f"[ {app.get('applied_role_type', 'STAFF')} ]"
                cand_title = (
                    f"{app['name']} (Age {app['age']}) | Specialty: {app.get('specialty')}{match_tag} {role_tag}"
                )
                surface.blit(
                    self.font_card_title.render(cand_title, True, (0, 255, 160) if is_spec_match else (255, 215, 0)),
                    (card_r.x + 32, card_r.y + 8),
                )

                e_str = gm.staff_manager.get_stat_scouting_display(gm.team_id, app.get("stat_engineering", 30))
                c_str = gm.staff_manager.get_stat_scouting_display(gm.team_id, app.get("stat_craftsmanship", 30))
                m_str = gm.staff_manager.get_stat_scouting_display(gm.team_id, app.get("stat_marketing", 30))
                comm_str = gm.staff_manager.get_stat_scouting_display(gm.team_id, app.get("stat_communication", 30))
                st_x = card_r.x + 32
                st_y = card_r.y + 30
                gap = 10
                st_x += (
                    UITheme.draw_stat_item(
                        surface,
                        st_x,
                        st_y,
                        "wrench",
                        f"Eng: {e_str}",
                        self.font_body,
                        UITheme.TEXT_MUTED,
                        (0, 220, 255),
                        icon_size=12,
                        gap=3,
                    )
                    + gap
                )
                st_x += (
                    UITheme.draw_stat_item(
                        surface,
                        st_x,
                        st_y,
                        "sparkles",
                        f"Craft: {c_str}",
                        self.font_body,
                        UITheme.TEXT_MUTED,
                        (255, 180, 40),
                        icon_size=12,
                        gap=3,
                    )
                    + gap
                )
                st_x += (
                    UITheme.draw_stat_item(
                        surface,
                        st_x,
                        st_y,
                        "trending-up",
                        f"Mkt: {m_str}",
                        self.font_body,
                        UITheme.TEXT_MUTED,
                        (255, 215, 0),
                        icon_size=12,
                        gap=3,
                    )
                    + gap
                )
                st_x += (
                    UITheme.draw_stat_item(
                        surface,
                        st_x,
                        st_y,
                        "radio",
                        f"Comm: {comm_str}",
                        self.font_body,
                        UITheme.TEXT_MUTED,
                        (140, 200, 255),
                        icon_size=12,
                        gap=3,
                    )
                    + gap
                )
                UITheme.draw_stat_item(
                    surface,
                    st_x,
                    st_y,
                    "circle-dollar-sign",
                    f"${app.get('salary_requested', 1000):,.0f}/mo",
                    self.font_body,
                    UITheme.TEXT_MUTED,
                    (255, 200, 40),
                    icon_size=12,
                    gap=3,
                )

                # Buttons
                hire_btn = pygame.Rect(card_r.x + card_r.width - 210, card_r.y + 22, 130, 26)
                if self.target_assignment_node:
                    node_short = self.target_assignment_node.replace("eng_", "").replace("hr_", "").upper()
                    UITheme.draw_button(
                        surface, hire_btn, f"HIRE TO {node_short[:7]}", self.font_btn, icon="check", icon_size=14
                    )
                else:
                    UITheme.draw_button(surface, hire_btn, "CHOOSE ROOM", self.font_btn, icon="network", icon_size=14)

                rej_btn = pygame.Rect(card_r.x + card_r.width - 74, card_r.y + 22, 65, 26)
                UITheme.draw_button(surface, rej_btn, "REJECT", self.font_btn, icon="x", icon_size=12)

                item_y += 80

            total_h = item_y - (rec_canvas.y + self.scroll_y)
            self.max_scroll = max(0.0, total_h - rec_canvas.height + 20)
            surface.set_clip(prev_clip)
            self._draw_scrollbar(surface, rec_canvas)

        # =====================================================================
        # SUB-TAB C: HEADHUNTER PADDOCK
        # =====================================================================
        elif self.sub_tab == "HEADHUNTER":
            UITheme.draw_icon(
                surface, "target", (content_rect.x + 14, content_rect.y + 14), color=(255, 180, 40), size=18
            )
            surface.blit(
                self.font_title.render(
                    "RIVAL PADDOCK SCOUTING & POACHING (Buyout fees + Signing Bonuses):", True, (255, 180, 40)
                ),
                (content_rect.x + 38, content_rect.y + 12),
            )

            with gm.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                SELECT p.*, t.name as team_name
                FROM personnel p
                JOIN teams t ON p.team_id = t.id
                WHERE p.team_id != ? AND p.role_type IN ('CATEGORY_DIRECTOR', 'DEPARTMENT_HEAD', 'STAFF')
                ORDER BY p.stat_engineering DESC LIMIT 10;
                """,
                    (gm.team_id,),
                )
                rival_staff = [dict(r) for r in cur.fetchall()]

            head_canvas = pygame.Rect(
                content_rect.x + 4, content_rect.y + 36, content_rect.width - 8, content_rect.height - 40
            )
            prev_clip = surface.get_clip()
            surface.set_clip(head_canvas)

            item_y = head_canvas.y + self.scroll_y
            for r_p in rival_staff:
                r_card = pygame.Rect(head_canvas.x + 8, item_y, head_canvas.width - 16, 68)
                pygame.draw.rect(surface, (18, 22, 30), r_card, border_radius=3)
                pygame.draw.rect(surface, (50, 65, 85), r_card, width=1, border_radius=3)

                UITheme.draw_icon(surface, "award", (r_card.x + 10, r_card.y + 8), color=(255, 215, 0), size=16)
                r_title = (
                    f"{r_p['name']} ({r_p.get('team_name')}) | {r_p.get('role_type')} | Spec: {r_p.get('specialty')}"
                )
                surface.blit(
                    self.font_card_title.render(r_title, True, UITheme.TEXT_WHITE), (r_card.x + 32, r_card.y + 8)
                )

                cur_sal = float(r_p.get("salary_monthly", 8000.0))
                e_scout = gm.staff_manager.get_stat_scouting_display(gm.team_id, r_p.get("stat_engineering", 50))
                l_scout = gm.staff_manager.get_stat_scouting_display(gm.team_id, r_p.get("stat_leadership", 50))
                rt_x = r_card.x + 32
                rt_y = r_card.y + 28
                gap = 12
                rt_x += (
                    UITheme.draw_stat_item(
                        surface,
                        rt_x,
                        rt_y,
                        "wrench",
                        f"Eng: {e_scout}",
                        self.font_body,
                        (180, 200, 220),
                        (0, 220, 255),
                        icon_size=12,
                        gap=3,
                    )
                    + gap
                )
                rt_x += (
                    UITheme.draw_stat_item(
                        surface,
                        rt_x,
                        rt_y,
                        "award",
                        f"Lead: {l_scout}",
                        self.font_body,
                        (180, 200, 220),
                        (255, 160, 200),
                        icon_size=12,
                        gap=3,
                    )
                    + gap
                )
                rt_x += (
                    UITheme.draw_stat_item(
                        surface,
                        rt_x,
                        rt_y,
                        "circle-dollar-sign",
                        f"Wage: ${cur_sal:,.0f}/mo",
                        self.font_body,
                        (180, 200, 220),
                        (255, 200, 40),
                        icon_size=12,
                        gap=3,
                    )
                    + gap
                )
                UITheme.draw_stat_item(
                    surface,
                    rt_x,
                    rt_y,
                    "coins",
                    f"Buyout: ${cur_sal * 6:,.0f}",
                    self.font_body,
                    (180, 200, 220),
                    (255, 140, 40),
                    icon_size=12,
                    gap=3,
                )

                poach_btn = pygame.Rect(r_card.x + r_card.width - 160, r_card.y + 18, 150, 30)
                UITheme.draw_button(surface, poach_btn, "POACH & ASSIGN", self.font_btn, icon="briefcase", icon_size=14)

                item_y += 76

            total_h = item_y - (head_canvas.y + self.scroll_y)
            self.max_scroll = max(0.0, total_h - head_canvas.height + 20)
            surface.set_clip(prev_clip)
            self._draw_scrollbar(surface, head_canvas)

        # =====================================================================
        # SUB-TAB D: HR POLICIES & AUTONOMOUS WORKFORCE DIRECTIVES
        # =====================================================================
        elif self.sub_tab == "POLICIES":
            surface.blit(
                self.font_title.render("HR AUTONOMOUS DIRECTIVES & FACILITY WORKFORCE POLICIES:", True, (255, 215, 0)),
                (content_rect.x + 14, content_rect.y + 12),
            )

            policies = gm.db.get_hr_policies(gm.team_id)
            with gm.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT node_id, current_tier, is_unlocked FROM team_facilities WHERE team_id = ?;", (gm.team_id,)
                )
                fac_tiers = {r[0]: (r[1] if r[2] else 0) for r in cur.fetchall()}

            pol_canvas = pygame.Rect(
                content_rect.x + 4, content_rect.y + 36, content_rect.width - 8, content_rect.height - 40
            )
            prev_clip = surface.get_clip()
            surface.set_clip(pol_canvas)

            item_y = pol_canvas.y + self.scroll_y

            toggle_defs = [
                (
                    "auto_fill_desks",
                    "Automated Specialist Hiring",
                    "hr_recruitment",
                    1,
                    "Auto-fills open facility specialist desks when room budget allows.",
                ),
                (
                    "auto_intern_pipeline",
                    "Automated European Intern Pipeline",
                    "hr_recruitment",
                    2,
                    "Auto-assigns intern tryouts with $2,000/mo headroom & signs top talent.",
                ),
                (
                    "min_intern_potential",
                    "Min Intern Potential Sign Threshold",
                    "hr_recruitment",
                    2,
                    "Interns below this potential are released after 6-month tryout.",
                ),
                (
                    "auto_payroll",
                    "Automated Payroll Calibration Desk",
                    "hr_payroll",
                    1,
                    "Auto-adjusts employee wages to meet market expectations within budget.",
                ),
                (
                    "auto_equip_procure",
                    "Autonomous Equipment Procurement",
                    "hr_equipment_procurement",
                    1,
                    "Uses accumulated Department Savings Accounts to auto-buy/upgrade rigs.",
                ),
                (
                    "auto_cull",
                    "Demographic Age-Curve Performance Cull",
                    "hr_performance_cull",
                    1,
                    "Auto-releases employees falling >20 pts below demographic curve expectations.",
                ),
                (
                    "auto_replace",
                    "Workforce Succession & Replacement",
                    "hr_workforce_optimizer",
                    1,
                    "Auto-replaces specialists when strictly superior talent is found for equal/lower wage.",
                ),
                (
                    "auto_headhunt",
                    "Executive Headhunting Delegation",
                    "hr_headhunting",
                    1,
                    "Auto-poaches highest-value rival personnel when room has payroll headroom.",
                ),
            ]

            for key, title, req_fac, req_tier, desc in toggle_defs:
                is_unlocked = fac_tiers.get(req_fac, 0) >= req_tier
                card_r = pygame.Rect(pol_canvas.x + 8, item_y, pol_canvas.width - 16, 60)
                pygame.draw.rect(surface, (18, 24, 34) if is_unlocked else (12, 14, 18), card_r, border_radius=3)
                pygame.draw.rect(
                    surface, (0, 180, 220) if is_unlocked else (40, 48, 60), card_r, width=1, border_radius=3
                )

                t_color = (255, 255, 255) if is_unlocked else (100, 110, 125)
                surface.blit(self.font_card_title.render(title, True, t_color), (card_r.x + 12, card_r.y + 8))

                req_txt = (
                    f"Status: Unlocked | {desc}"
                    if is_unlocked
                    else f"🔒 LOCKED (Requires {req_fac.replace('_', ' ').title()} Tier {req_tier}) | {desc}"
                )
                surface.blit(
                    self.font_badge.render(req_txt, True, (0, 220, 255) if is_unlocked else (180, 80, 80)),
                    (card_r.x + 12, card_r.y + 32),
                )

                if key == "min_intern_potential":
                    if is_unlocked:
                        btn_minus = pygame.Rect(card_r.x + card_r.width - 140, card_r.y + 16, 30, 26)
                        btn_plus = pygame.Rect(card_r.x + card_r.width - 50, card_r.y + 16, 30, 26)
                        pygame.draw.rect(surface, (45, 55, 70), btn_minus, border_radius=2)
                        pygame.draw.rect(surface, (45, 55, 70), btn_plus, border_radius=2)
                        surface.blit(
                            self.font_btn.render("-", True, UITheme.TEXT_WHITE), (btn_minus.x + 10, btn_minus.y + 4)
                        )
                        surface.blit(
                            self.font_btn.render("+", True, UITheme.TEXT_WHITE), (btn_plus.x + 9, btn_plus.y + 4)
                        )

                        pot_val = policies.get("min_intern_potential", 75)
                        pot_lbl = self.font_card_title.render(f"{pot_val}", True, (255, 215, 0))
                        surface.blit(pot_lbl, (card_r.x + card_r.width - 98, card_r.y + 20))
                else:
                    toggle_btn = pygame.Rect(card_r.x + card_r.width - 130, card_r.y + 16, 110, 26)
                    is_enabled = bool(policies.get(key, 0)) and is_unlocked
                    if not is_unlocked:
                        pygame.draw.rect(surface, (25, 30, 40), toggle_btn, border_radius=2)
                        b_txt = self.font_btn.render("LOCKED", True, (90, 100, 115))
                    elif is_enabled:
                        pygame.draw.rect(surface, (0, 140, 80), toggle_btn, border_radius=2)
                        b_txt = self.font_btn.render("ACTIVE [ON]", True, UITheme.TEXT_WHITE)
                    else:
                        pygame.draw.rect(surface, (120, 35, 35), toggle_btn, border_radius=2)
                        b_txt = self.font_btn.render("DISABLED", True, (220, 220, 220))

                    surface.blit(b_txt, (toggle_btn.x + (toggle_btn.width - b_txt.get_width()) // 2, toggle_btn.y + 6))

                item_y += 68

            total_h = item_y - (pol_canvas.y + self.scroll_y)
            self.max_scroll = max(0.0, total_h - pol_canvas.height + 20)
            surface.set_clip(prev_clip)
            self._draw_scrollbar(surface, pol_canvas)

        # =====================================================================
        # 3. Employee Details Inspector Drawer (Right Side)
        # =====================================================================
        if self.inspected_personnel_id is not None:
            drawer_x = self.width - 440
            drawer_rect = pygame.Rect(drawer_x, 60, 416, self.height - 75)
            pygame.draw.rect(surface, (14, 18, 26), drawer_rect, border_radius=4)
            pygame.draw.rect(surface, (0, 220, 255), drawer_rect, width=2, border_radius=4)

            with gm.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM personnel WHERE id = ?;", (self.inspected_personnel_id,))
                row = cur.fetchone()
                p_info = dict(row) if row else {}

            if p_info:
                hdr_rect = pygame.Rect(drawer_x, 60, 416, 36)
                pygame.draw.rect(surface, (20, 30, 45), hdr_rect, border_top_left_radius=4, border_top_right_radius=4)
                UITheme.draw_icon(surface, "user", (drawer_x + 14, 70), color=(255, 215, 0), size=16)
                surface.blit(self.font_title.render(f"{p_info['name']}", True, (255, 215, 0)), (drawer_x + 36, 70))

                close_btn = pygame.Rect(drawer_x + 416 - 65, 66, 55, 22)
                UITheme.draw_button(surface, close_btn, "CLOSE", self.font_btn, icon="x", icon_size=12)

                dy = 104
                cur_node = p_info.get("facility_node_id") or "Unassigned"
                surface.blit(
                    self.font_card_title.render(
                        f"Role: {p_info.get('role_type')} | Room: {cur_node.replace('_', ' ').title()}",
                        True,
                        UITheme.TEXT_WHITE,
                    ),
                    (drawer_x + 14, dy),
                )
                surface.blit(
                    self.font_badge.render(
                        f"Specialty: {p_info.get('specialty')} (+50% Matching Room Output)", True, (0, 240, 140)
                    ),
                    (drawer_x + 14, dy + 22),
                )

                stats = [
                    ("Engineering", "wrench", p_info.get("stat_engineering", 40.0), (0, 220, 255)),
                    ("Craftsmanship", "sparkles", p_info.get("stat_craftsmanship", 40.0), (255, 180, 40)),
                    ("Marketing", "trending-up", p_info.get("stat_marketing", 40.0), (255, 215, 0)),
                    ("Communication", "radio", p_info.get("stat_communication", 40.0), (140, 200, 255)),
                    ("Leadership", "award", p_info.get("stat_leadership", 40.0), (255, 120, 180)),
                    ("Composure", "shield", p_info.get("stat_composure", 40.0), (160, 240, 140)),
                    ("Potential Ceiling", "zap", p_info.get("stat_potential", 70.0), (180, 140, 255)),
                ]

                sy = dy + 48
                for s_name, s_icon, s_val, s_col in stats:
                    UITheme.draw_icon(surface, s_icon, (drawer_x + 14, sy + 1), color=s_col, size=13)
                    scout_str = gm.staff_manager.get_stat_scouting_display(gm.team_id, float(s_val))
                    surface.blit(
                        self.font_body.render(f"{s_name}: {scout_str}", True, UITheme.TEXT_MUTED), (drawer_x + 32, sy)
                    )
                    bar_bg = pygame.Rect(drawer_x + 165, sy + 3, 225, 10)
                    pygame.draw.rect(surface, (25, 32, 42), bar_bg, border_radius=2)
                    fill_w = int(225 * (min(100.0, float(s_val)) / 100.0))
                    pygame.draw.rect(surface, s_col, pygame.Rect(bar_bg.x, bar_bg.y, fill_w, 10), border_radius=2)
                    sy += 20

                sy += 8
                sal = float(p_info.get("salary_monthly", 8000.0))
                mkt = float(p_info.get("market_value_monthly", 8000.0))
                mor = float(p_info.get("morale", 85.0))

                surface.blit(
                    self.font_card_title.render("CONTRACT & POSITION MANAGEMENT:", True, (255, 215, 0)),
                    (drawer_x + 14, sy),
                )
                surface.blit(
                    self.font_body.render(
                        f"Monthly Salary: ${sal:,.0f}/mo (Market Expectation: ${mkt:,.0f}/mo)", True, UITheme.TEXT_WHITE
                    ),
                    (drawer_x + 14, sy + 18),
                )
                surface.blit(
                    self.font_body.render(
                        f"Morale Satisfaction: {mor:.0f}%", True, (0, 240, 140) if mor >= 75 else (255, 140, 40)
                    ),
                    (drawer_x + 14, sy + 34),
                )

                r_btn1 = pygame.Rect(drawer_x + 14, sy + 56, 185, 26)
                UITheme.draw_button(surface, r_btn1, "REASSIGN ROOM", self.font_btn, icon="network", icon_size=14)

                cur_role = p_info.get("role_type", "STAFF")
                r_btn2 = pygame.Rect(drawer_x + 210, sy + 56, 185, 26)
                if cur_role != "DEPARTMENT_HEAD":
                    UITheme.draw_button(surface, r_btn2, "PROMOTE TO HEAD", self.font_btn, icon="award", icon_size=14)
                else:
                    pygame.draw.rect(surface, (25, 32, 42), r_btn2, border_radius=3)
                    surface.blit(
                        self.font_btn.render("[ ACTIVE HEAD ]", True, (130, 140, 150)), (r_btn2.x + 36, r_btn2.y + 6)
                    )

                raise_btn = pygame.Rect(drawer_x + 14, sy + 90, 185, 26)
                UITheme.draw_button(
                    surface, raise_btn, "+25% WAGE RAISE", self.font_btn, icon="circle-dollar-sign", icon_size=14
                )

                fire_btn = pygame.Rect(drawer_x + 210, sy + 90, 185, 26)
                UITheme.draw_button(surface, fire_btn, "RELEASE / FIRE", self.font_btn, icon="x", icon_size=14)

        # =====================================================================
        # 4. Department Destination Selector Modal
        # =====================================================================
        if self.destination_picker_data is not None:
            dim_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            dim_surf.fill((0, 0, 0, 180))
            surface.blit(dim_surf, (0, 0))

            modal_w = min(780, self.width - 80)
            modal_h = min(540, self.height - 100)
            modal_x = (self.width - modal_w) // 2
            modal_y = (self.height - modal_h) // 2
            modal_rect = pygame.Rect(modal_x, modal_y, modal_w, modal_h)

            pygame.draw.rect(surface, (14, 18, 26), modal_rect, border_radius=6)
            pygame.draw.rect(surface, (0, 220, 255), modal_rect, width=2, border_radius=6)

            p_data = self.destination_picker_data
            hdr_rect = pygame.Rect(modal_x, modal_y, modal_w, 48)
            pygame.draw.rect(surface, (20, 32, 48), hdr_rect, border_top_left_radius=6, border_top_right_radius=6)

            UITheme.draw_icon(surface, "network", (modal_x + 16, modal_y + 14), color=(255, 215, 0), size=20)
            title_txt = f"SELECT DESTINATION: {p_data['name']} (Spec: {p_data.get('specialty')})"
            surface.blit(self.font_title.render(title_txt, True, (255, 215, 0)), (modal_x + 42, modal_y + 14))

            close_btn = pygame.Rect(modal_x + modal_w - 75, modal_y + 12, 65, 24)
            UITheme.draw_button(surface, close_btn, "CANCEL", self.font_btn, icon="x", icon_size=12)

            sub_note = "Choose an unlocked department room with open capacity to assign this personnel member."
            surface.blit(self.font_body.render(sub_note, True, (180, 200, 220)), (modal_x + 16, modal_y + 54))

            list_canvas = pygame.Rect(modal_x + 12, modal_y + 80, modal_w - 24, modal_h - 96)
            prev_clip = surface.get_clip()
            surface.set_clip(list_canvas)

            fac_list = gm.staff_manager.get_unlocked_facilities_with_capacity(gm.team_id)
            m_scroll = p_data.get("scroll_y", 0.0)
            card_y = list_canvas.y + m_scroll

            cand_spec = p_data.get("specialty")

            for fac in fac_list:
                card_r = pygame.Rect(list_canvas.x + 4, card_y, list_canvas.width - 8, 58)
                is_spec_match = cand_spec and fac["target_specialty"] == cand_spec

                pygame.draw.rect(surface, (20, 28, 40), card_r, border_radius=3)
                pygame.draw.rect(
                    surface, (0, 240, 140) if is_spec_match else (40, 55, 75), card_r, width=1, border_radius=3
                )

                UITheme.draw_icon(surface, "factory", (card_r.x + 10, card_r.y + 6), color=(255, 215, 0), size=16)
                f_title = f"{fac['name']} (Tier {fac['current_tier']}) - {fac['department']}"
                surface.blit(
                    self.font_card_title.render(f_title, True, UITheme.TEXT_WHITE), (card_r.x + 32, card_r.y + 6)
                )

                spec_str = f"Room Specialty: {fac['target_specialty']}"
                if is_spec_match:
                    spec_str += "  [MATCH +50%]"
                surface.blit(
                    self.font_badge.render(spec_str, True, (0, 240, 140) if is_spec_match else (170, 185, 200)),
                    (card_r.x + 32, card_r.y + 24),
                )

                head_txt = "Head: Active" if fac["has_head"] else "Head: VACANT"
                intern_txt = "Intern: Active" if fac["has_intern"] else "Intern: Open"
                cap_str = f"Desks: {fac['staff_count']}/{fac['max_staff_slots']} Filled ({fac['vacant_staff_slots']} Open) | {head_txt} | {intern_txt}"
                surface.blit(self.font_body.render(cap_str, True, UITheme.TEXT_MUTED), (card_r.x + 10, card_r.y + 40))

                assign_btn = pygame.Rect(card_r.x + card_r.width - 150, card_r.y + 14, 140, 28)
                has_space = fac["vacant_staff_slots"] > 0 or not fac["has_head"]

                if has_space:
                    UITheme.draw_button(surface, assign_btn, "ASSIGN HERE", self.font_btn, icon="check", icon_size=14)
                else:
                    UITheme.draw_button(surface, assign_btn, "ROOM FULL", self.font_btn, is_disabled=True)

                card_y += 66

            total_h = card_y - (list_canvas.y + m_scroll)
            p_data["max_scroll"] = max(0.0, total_h - list_canvas.height + 20)
            surface.set_clip(prev_clip)

        # 5. Status Bar
        stat_bar = pygame.Rect(24, self.height - 36, self.width - 48, 26)
        pygame.draw.rect(surface, (16, 20, 26), stat_bar, border_radius=3)
        pygame.draw.rect(surface, UITheme.PANEL_BORDER, stat_bar, width=1, border_radius=3)
        surface.blit(
            self.font_badge.render(f"PERSONNEL HR: {self.status_message}", True, UITheme.ACCENT_CYAN),
            (stat_bar.x + 10, stat_bar.y + 6),
        )
