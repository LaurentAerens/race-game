from typing import Any, Dict, List, Tuple

import pygame

from ...management.engineering_manager import FACTORY_PART_SPECS, EngineeringManager
from ...management.game_manager import GameManager
from ..theme import UITheme


class CarEngineeringTab:
    """
    Car Engineering & Blueprint Inspector:
    - Interactive 2D top-down chassis wireframe with component hotspots
    - Circular & linear wear/reliability health indicators
    - Selected component R&D knowledge evolution bar & generation builders
    - Filtered Warehouse Spares drawer with 1-click mounting
    - Power Unit supplier contracts and Next-Gen Regulation R&D
    """

    CATEGORIES = ["FRONT_WING", "BRAKES", "SUSPENSION", "FLOOR", "ENGINE", "ERS", "REAR_WING"]

    CATEGORY_ICONS = {
        "FRONT_WING": "wind",
        "REAR_WING": "flag",
        "FLOOR": "layers",
        "SUSPENSION": "sliders",
        "BRAKES": "disc",
        "ENGINE": "cpu",
        "ERS": "battery-charging",
    }

    CATEGORY_NAMES = {
        "FRONT_WING": "Front Wing",
        "REAR_WING": "Rear Wing",
        "FLOOR": "Floor & Venturi",
        "SUSPENSION": "Suspension",
        "BRAKES": "Carbon Brakes",
        "ENGINE": "Power Unit",
        "ERS": "ERS Hybrid",
    }

    def __init__(self, screen_width: int, screen_height: int):
        self.width = screen_width
        self.height = screen_height

        self.selected_car_slot: int = 1  # Car 1 or Car 2
        self.selected_part_category: str = "FRONT_WING"
        self._init_fonts()
        self.status_message: str = (
            "Select any component on the chassis blueprint to inspect R&D progress or mount warehouse spares."
        )

    def _init_fonts(self):
        self.font_title = UITheme.get_font(13, bold=True)
        self.font_card_title = UITheme.get_font(11, bold=True)
        self.font_body = UITheme.get_font(10, bold=False)
        self.font_badge = UITheme.get_font(9, bold=True)
        self.font_btn = UITheme.get_font(10, bold=True)

    def resize(self, width: int, height: int):
        self.width = width
        self.height = height
        self._init_fonts()

    def get_layout(
        self,
        gm: GameManager,
        em: EngineeringManager,
        tier: int,
        allowed_parts: List[str],
    ) -> Dict[str, Any]:
        """Calculates precise, non-overlapping bounding rects for rendering and click routing."""
        components = [c for c in em.get_team_components(gm.team_id) if c["car_slot"] == self.selected_car_slot]
        comp_by_cat = {c["category"]: c for c in components}

        # 1. Top Car Selector Buttons
        c1_rect = pygame.Rect(24, 70, 140, 28)
        c2_rect = pygame.Rect(170, 70, 140, 28)

        # 2. Main Columns: Left (Blueprint & R&D) vs Right (Spares & Engine & Next-Gen)
        bp_x = 24
        bp_y = 106
        gap_col = 16
        bp_w = max(520, int(self.width * 0.58))
        right_x = bp_x + bp_w + gap_col
        right_w = self.width - right_x - 24
        total_h = self.height - bp_y - 44

        bp_panel_rect = pygame.Rect(bp_x, bp_y, bp_w, total_h)
        right_panel_rect = pygame.Rect(right_x, bp_y, right_w, total_h)

        # Blueprint Canvas Area inside bp_panel
        canvas_h = max(240, int(total_h * 0.58))
        canvas_rect = pygame.Rect(bp_x + 8, bp_y + 36, bp_w - 16, canvas_h)

        # 7 Component Hotspot Cards around the car
        cx = canvas_rect.centerx
        cy = canvas_rect.centery
        card_w = min(150, (bp_w - 32) // 3)
        card_h = 48

        hotspot_rects: Dict[str, pygame.Rect] = {
            "FRONT_WING": pygame.Rect(canvas_rect.x + 8, canvas_rect.y + 8, card_w, card_h),
            "BRAKES": pygame.Rect(canvas_rect.x + 8, canvas_rect.bottom - card_h - 8, card_w, card_h),
            "SUSPENSION": pygame.Rect(cx - card_w // 2, canvas_rect.y + 8, card_w, card_h),
            "FLOOR": pygame.Rect(cx - card_w // 2, canvas_rect.bottom - card_h - 8, card_w, card_h),
            "ENGINE": pygame.Rect(canvas_rect.right - card_w - 8, canvas_rect.y + 8, card_w, card_h),
            "ERS": pygame.Rect(canvas_rect.right - card_w - 8, canvas_rect.bottom - card_h - 8, card_w, card_h),
            "REAR_WING": pygame.Rect(canvas_rect.right - card_w - 8, cy - card_h // 2, card_w, card_h),
        }

        # Selected Part R&D Detail Card (below canvas inside bp_panel)
        rd_card_y = canvas_rect.bottom + 8
        rd_card_h = bp_panel_rect.bottom - rd_card_y - 8
        rd_card_rect = pygame.Rect(bp_x + 8, rd_card_y, bp_w - 16, rd_card_h)

        build_btn = pygame.Rect(rd_card_rect.right - 145, rd_card_rect.y + 12, 135, 26)
        buy_btn = pygame.Rect(rd_card_rect.right - 145, rd_card_rect.y + 44, 135, 26)

        # Right Panel Sections:
        # A. Warehouse Spares Drawer (Top section of right panel)
        spares_drawer_h = max(130, int(total_h * 0.32))
        spares_drawer_rect = pygame.Rect(right_x, bp_y, right_w, spares_drawer_h)

        # Spares items within drawer
        spares = [
            sp
            for sp in em.get_spare_parts_in_warehouse(gm.team_id)
            if sp.get("category") == self.selected_part_category
        ]
        if not spares:
            # Show all spares if no category-specific spares found
            spares = em.get_spare_parts_in_warehouse(gm.team_id)

        spare_buttons = []
        for s_idx, sp in enumerate(spares[:3]):
            sy = spares_drawer_rect.y + 32 + s_idx * 30
            s_box = pygame.Rect(spares_drawer_rect.x + 8, sy, spares_drawer_rect.width - 16, 26)
            m_btn = pygame.Rect(s_box.right - 92, s_box.y + 1, 90, 24)
            spare_buttons.append((sp["id"], s_box, m_btn, sp))

        # B. Power Unit Suppliers (Middle section)
        suppliers = em.get_available_engine_suppliers(gm.team_id)
        supp_y = spares_drawer_rect.bottom + 10
        supp_card_h = 58
        supplier_cards = []
        for idx, supp in enumerate(suppliers[:3]):
            sy = supp_y + idx * (supp_card_h + 6)
            s_rect = pygame.Rect(right_x, sy, right_w, supp_card_h)
            sign_btn = pygame.Rect(s_rect.right - 105, s_rect.y + 16, 95, 26)
            supplier_cards.append((supp["name"], s_rect, sign_btn, supp))

        # C. Next-Gen R&D Chassis & Port-Back (Bottom section)
        ng_y = supp_y + 3 * (supp_card_h + 6) + 6
        ng_h = right_panel_rect.bottom - ng_y
        ng_rect = pygame.Rect(right_x, ng_y, right_w, max(120, ng_h))

        btn_w = 54
        btn_h = 22
        btn_y = ng_rect.y + 34
        alloc_rects = {}
        for b_idx, target_pct in enumerate([0.0, 25.0, 50.0, 75.0]):
            b_x = ng_rect.x + 10 + b_idx * (btn_w + 6)
            alloc_rects[target_pct] = pygame.Rect(b_x, btn_y, btn_w, btn_h)

        pb_btn = pygame.Rect(ng_rect.x + 10, ng_rect.bottom - 32, ng_rect.width - 20, 24)

        # Status Bar
        stat_bar = pygame.Rect(24, self.height - 34, self.width - 48, 26)

        return {
            "c1_rect": c1_rect,
            "c2_rect": c2_rect,
            "bp_panel_rect": bp_panel_rect,
            "canvas_rect": canvas_rect,
            "hotspot_rects": hotspot_rects,
            "rd_card_rect": rd_card_rect,
            "build_btn": build_btn,
            "buy_btn": buy_btn,
            "spares_drawer_rect": spares_drawer_rect,
            "spare_buttons": spare_buttons,
            "supplier_cards": supplier_cards,
            "ng_rect": ng_rect,
            "alloc_rects": alloc_rects,
            "pb_btn": pb_btn,
            "stat_bar": stat_bar,
            "components_by_cat": comp_by_cat,
        }

    def handle_click(self, mx: int, my: int, gm: GameManager, em: EngineeringManager, cost_mult: float = 1.0) -> bool:
        tier, l_name, allowed_parts = em.get_team_allowed_parts(gm.team_id)
        layout = self.get_layout(gm, em, tier, allowed_parts)

        # 1. Car Selector Tabs
        if layout["c1_rect"].collidepoint(mx, my):
            self.selected_car_slot = 1
            return True
        elif layout["c2_rect"].collidepoint(mx, my):
            self.selected_car_slot = 2
            return True

        # 2. Component Hotspots on Chassis
        for cat, h_rect in layout["hotspot_rects"].items():
            if h_rect.collidepoint(mx, my):
                self.selected_part_category = cat
                self.status_message = f"Selected {self.CATEGORY_NAMES.get(cat, cat)} for inspection and maintenance."
                return True

        # 3. Selected Component R&D Action Buttons
        comp_by_cat = layout["components_by_cat"]
        selected_comp = comp_by_cat.get(self.selected_part_category)
        if selected_comp:
            # Build Next Generation
            if layout["build_btn"].collidepoint(mx, my):
                if selected_comp["category"] not in allowed_parts or "SPEC" in allowed_parts:
                    self.status_message = (
                        f"{selected_comp['category']} is SPEC REGULATED in Tier {tier} ({l_name}). "
                        f"Earn promotion or purchase a Factory replacement!"
                    )
                    return True
                success, msg, gain = em.build_next_generation_part(gm.team_id, selected_comp["id"], cost_mult=cost_mult)
                self.status_message = msg
                return True

            # Buy Factory Replacement
            if layout["buy_btn"].collidepoint(mx, my):
                success, msg = em.buy_factory_part(
                    gm.team_id, selected_comp["category"], target_car_slot=self.selected_car_slot
                )
                self.status_message = msg
                return True

        # 4. Warehouse Spares Mount Buttons
        for sp_id, _, m_btn, sp in layout["spare_buttons"]:
            if m_btn.collidepoint(mx, my):
                success, msg = em.mount_part_from_inventory(gm.team_id, sp_id, self.selected_car_slot)
                self.status_message = msg
                return True

        # 5. Engine Suppliers Sign Contract
        for supp_name, _, sign_btn, _ in layout["supplier_cards"]:
            if sign_btn.collidepoint(mx, my):
                success, msg = em.set_engine_supplier(gm.team_id, supp_name)
                self.status_message = msg
                return True

        # 6. Next-Gen Allocation Buttons
        for target_pct, b_rect in layout["alloc_rects"].items():
            if b_rect.collidepoint(mx, my):
                success, msg = em.set_next_gen_allocation(gm.team_id, target_pct)
                self.status_message = msg
                return True

        # 7. Port-Back Upgrade Button
        if layout["pb_btn"].collidepoint(mx, my):
            success, msg = em.execute_port_back_upgrade(gm.team_id, gm.current_week)
            self.status_message = msg
            return True

        return False

    def _draw_chassis_wireframe(
        self,
        surface: pygame.Surface,
        canvas: pygame.Rect,
        comp_by_cat: Dict[str, Any],
        hotspots: Dict[str, pygame.Rect],
    ):
        """Draws technical top-down formula car wireframe with glowing component hotspots and leader lines."""
        # Technical grid background
        pygame.draw.rect(surface, (11, 14, 20), canvas, border_radius=4)
        pygame.draw.rect(surface, (24, 32, 44), canvas, width=1, border_radius=4)

        # Subtle dotted grid lines
        for gx in range(canvas.x + 20, canvas.right, 40):
            pygame.draw.line(surface, (16, 22, 30), (gx, canvas.y), (gx, canvas.bottom), 1)
        for gy in range(canvas.y + 20, canvas.bottom, 40):
            pygame.draw.line(surface, (16, 22, 30), (canvas.x, gy), (canvas.right, gy), 1)

        # Car center & dimensions
        cx = canvas.centerx
        cy = canvas.centery
        car_len = min(360, int(canvas.width * 0.58))
        half_l = car_len // 2

        # Anchor points along formula car centerline (Left = Front Nose, Right = Rear Exhaust)
        front_x = cx - half_l
        rear_x = cx + half_l

        # Component colors & highlight state
        sel = self.selected_part_category

        def get_comp_col(cat_key: str, default_col: Tuple[int, int, int]) -> Tuple[int, int, int]:
            if sel == cat_key:
                return UITheme.ACCENT_CYAN
            comp = comp_by_cat.get(cat_key)
            if not comp:
                return default_col
            wear = comp.get("wear_pct", 0.0)
            if wear > 60.0:
                return UITheme.ACCENT_RED
            elif wear > 35.0:
                return UITheme.ACCENT_YELLOW
            return default_col

        col_fw = get_comp_col("FRONT_WING", (0, 200, 240))
        col_brk = get_comp_col("BRAKES", (255, 180, 50))
        col_sus = get_comp_col("SUSPENSION", (80, 160, 255))
        col_flr = get_comp_col("FLOOR", (160, 90, 240))
        col_eng = get_comp_col("ENGINE", (255, 120, 50))
        col_ers = get_comp_col("ERS", (0, 230, 140))
        col_rw = get_comp_col("REAR_WING", (180, 100, 255))

        # --- A. FRONT WING ---
        # Swept multielement front wing
        fw_pts = [
            (front_x - 12, cy - 58),
            (front_x + 12, cy - 54),
            (front_x + 22, cy - 18),
            (front_x + 16, cy),
            (front_x + 22, cy + 18),
            (front_x + 12, cy + 54),
            (front_x - 12, cy + 58),
            (front_x - 16, cy + 44),
            (front_x - 6, cy),
            (front_x - 16, cy - 44),
        ]
        pygame.draw.polygon(surface, (18, 26, 36), fw_pts)
        pygame.draw.polygon(surface, col_fw, fw_pts, width=2 if sel == "FRONT_WING" else 1)

        # --- B. NOSE CONE & COCKPIT CHASSIS ---
        nose_pts = [
            (front_x + 16, cy),
            (front_x + 75, cy - 14),
            (cx - 30, cy - 18),
            (cx + 25, cy - 24),
            (cx + 70, cy - 22),
            (rear_x - 20, cy - 12),
            (rear_x - 10, cy),
            (rear_x - 20, cy + 12),
            (cx + 70, cy + 22),
            (cx + 25, cy + 24),
            (cx - 30, cy + 18),
            (front_x + 75, cy + 14),
        ]
        pygame.draw.polygon(surface, (14, 20, 28), nose_pts)
        pygame.draw.polygon(surface, (40, 54, 72), nose_pts, width=1)

        # --- C. FLOOR & SIDEPODS ---
        side_l = [
            (cx - 30, cy - 18),
            (cx - 20, cy - 44),
            (cx + 45, cy - 42),
            (cx + 70, cy - 22),
        ]
        side_r = [
            (cx - 30, cy + 18),
            (cx - 20, cy + 44),
            (cx + 45, cy + 42),
            (cx + 70, cy + 22),
        ]
        pygame.draw.polygon(surface, (20, 28, 38), side_l)
        pygame.draw.polygon(surface, col_flr, side_l, width=2 if sel == "FLOOR" else 1)
        pygame.draw.polygon(surface, (20, 28, 38), side_r)
        pygame.draw.polygon(surface, col_flr, side_r, width=2 if sel == "FLOOR" else 1)

        # Cockpit Opening & Halo
        pygame.draw.ellipse(surface, (8, 11, 16), (cx - 28, cy - 9, 36, 18))
        pygame.draw.ellipse(
            surface, (0, 220, 240) if sel == "FLOOR" else (50, 65, 85), (cx - 28, cy - 9, 36, 18), width=1
        )
        pygame.draw.line(surface, (60, 80, 105), (cx - 28, cy), (cx + 8, cy), 2)

        # --- D. ENGINE & ERS BAY ---
        engine_rect = pygame.Rect(cx + 15, cy - 12, 45, 24)
        pygame.draw.rect(surface, (24, 30, 22) if sel == "ENGINE" else (16, 22, 30), engine_rect, border_radius=2)
        pygame.draw.rect(surface, col_eng, engine_rect, width=2 if sel == "ENGINE" else 1, border_radius=2)

        # ERS Hybrid Battery pack icon/strip
        ers_rect = pygame.Rect(cx + 22, cy - 6, 30, 12)
        pygame.draw.rect(surface, (14, 28, 20) if sel == "ERS" else (12, 18, 24), ers_rect, border_radius=2)
        pygame.draw.rect(surface, col_ers, ers_rect, width=2 if sel == "ERS" else 1, border_radius=2)

        # --- E. WHEELS & SUSPENSION ---
        # Wheel dimensions
        fw_w, fw_h = 36, 18
        rw_w, rw_h = 42, 22
        front_axle_x = front_x + 65
        rear_axle_x = rear_x - 35

        # Suspension Wishbone Arms
        # Front Left
        pygame.draw.line(
            surface, col_sus, (front_axle_x + fw_w // 2, cy - 42), (cx - 40, cy - 14), 2 if sel == "SUSPENSION" else 1
        )
        pygame.draw.line(surface, col_sus, (front_axle_x + fw_w // 2, cy - 42), (cx - 15, cy - 15), 1)
        # Front Right
        pygame.draw.line(
            surface, col_sus, (front_axle_x + fw_w // 2, cy + 42), (cx - 40, cy + 14), 2 if sel == "SUSPENSION" else 1
        )
        pygame.draw.line(surface, col_sus, (front_axle_x + fw_w // 2, cy + 42), (cx - 15, cy + 15), 1)
        # Rear Left
        pygame.draw.line(surface, col_sus, (rear_axle_x + rw_w // 2, cy - 46), (cx + 60, cy - 18), 1)
        pygame.draw.line(surface, col_sus, (rear_axle_x + rw_w // 2, cy - 46), (rear_x - 15, cy - 10), 1)
        # Rear Right
        pygame.draw.line(surface, col_sus, (rear_axle_x + rw_w // 2, cy + 46), (cx + 60, cy + 18), 1)
        pygame.draw.line(surface, col_sus, (rear_axle_x + rw_w // 2, cy + 46), (rear_x - 15, cy + 10), 1)

        # Wheels (Rubber Outer + Carbon Rim + Brake Caliper)
        for wx, wy, ww, wh in [
            (front_axle_x, cy - 54, fw_w, fw_h),
            (front_axle_x, cy + 36, fw_w, fw_h),
            (rear_axle_x, cy - 60, rw_w, rw_h),
            (rear_axle_x, cy + 38, rw_w, rw_h),
        ]:
            w_rect = pygame.Rect(wx, wy, ww, wh)
            pygame.draw.rect(surface, (12, 14, 18), w_rect, border_radius=3)
            pygame.draw.rect(surface, (36, 46, 58), w_rect, width=1, border_radius=3)
            # Brake disc glowing core
            pygame.draw.ellipse(surface, col_brk, (wx + 6, wy + 3, ww - 12, wh - 6), width=2 if sel == "BRAKES" else 1)

        # --- F. REAR WING & DRS ---
        rw_pts = [
            (rear_x - 10, cy - 50),
            (rear_x + 15, cy - 50),
            (rear_x + 15, cy + 50),
            (rear_x - 10, cy + 50),
        ]
        pygame.draw.polygon(surface, (18, 24, 34), rw_pts)
        pygame.draw.polygon(surface, col_rw, rw_pts, width=2 if sel == "REAR_WING" else 1)
        # DRS Flap line
        pygame.draw.line(
            surface,
            (255, 255, 255) if sel == "REAR_WING" else (60, 75, 95),
            (rear_x + 8, cy - 42),
            (rear_x + 8, cy + 42),
            2,
        )

        # --- G. LEADER LINES CONNECTING HOTSPOT BADGES TO CHASSIS ---
        def draw_leader(card_rect: pygame.Rect, target_pt: Tuple[int, int], color: Tuple[int, int, int]):
            start_pt = card_rect.center
            pygame.draw.line(surface, (color[0], color[1], color[2]), start_pt, target_pt, 1)
            pygame.draw.circle(surface, color, target_pt, 3)

        draw_leader(hotspots["FRONT_WING"], (front_x, cy - 25), col_fw)
        draw_leader(hotspots["BRAKES"], (front_axle_x + 18, cy + 36), col_brk)
        draw_leader(hotspots["SUSPENSION"], (front_axle_x + 18, cy - 28), col_sus)
        draw_leader(hotspots["FLOOR"], (cx, cy + 36), col_flr)
        draw_leader(hotspots["ENGINE"], (cx + 38, cy - 12), col_eng)
        draw_leader(hotspots["ERS"], (cx + 38, cy + 12), col_ers)
        draw_leader(hotspots["REAR_WING"], (rear_x + 8, cy), col_rw)

        # --- H. HOTSPOT CARDS RENDER ---
        for cat_key, h_rect in hotspots.items():
            comp = comp_by_cat.get(cat_key, {})
            is_active = sel == cat_key
            bg = (24, 34, 48) if is_active else (14, 18, 26)
            b_col = UITheme.ACCENT_CYAN if is_active else (38, 48, 62)

            pygame.draw.rect(surface, bg, h_rect, border_radius=3)
            pygame.draw.rect(surface, b_col, h_rect, width=2 if is_active else 1, border_radius=3)

            # Icon + Name
            ic_name = self.CATEGORY_ICONS.get(cat_key, "wrench")
            UITheme.draw_icon(surface, ic_name, (h_rect.x + 6, h_rect.y + 6), color=b_col, size=13)

            cat_title = self.CATEGORY_NAMES.get(cat_key, cat_key)
            surface.blit(
                self.font_card_title.render(cat_title, True, UITheme.TEXT_WHITE), (h_rect.x + 23, h_rect.y + 5)
            )

            # Generation badge & Reliability
            gen = comp.get("generation", 1)
            wear = comp.get("wear_pct", 0.0)
            rel = max(0.0, 100.0 - wear)
            rel_col = (0, 240, 140) if rel > 70 else ((255, 190, 40) if rel > 40 else (255, 70, 70))

            surface.blit(self.font_badge.render(f"Mk {gen}", True, UITheme.ACCENT_CYAN), (h_rect.x + 6, h_rect.y + 26))

            UITheme.draw_stat_item(
                surface,
                h_rect.x + 46,
                h_rect.y + 26,
                "shield",
                f"{rel:.0f}%",
                self.font_badge,
                text_color=rel_col,
                icon_color=rel_col,
                icon_size=10,
            )

    def render(self, surface: pygame.Surface, gm: GameManager, em: EngineeringManager, cost_mult: float = 1.0):
        tier, l_name, allowed_parts = em.get_team_allowed_parts(gm.team_id)
        layout = self.get_layout(gm, em, tier, allowed_parts)
        comp_by_cat = layout["components_by_cat"]

        # 1. Car Selector Tabs
        UITheme.draw_button(
            surface,
            layout["c1_rect"],
            "CAR #1 (PRIMARY)",
            self.font_btn,
            is_active=self.selected_car_slot == 1,
            icon="user",
            icon_size=13,
        )
        UITheme.draw_button(
            surface,
            layout["c2_rect"],
            "CAR #2 (SECONDARY)",
            self.font_btn,
            is_active=self.selected_car_slot == 2,
            icon="user",
            icon_size=13,
        )

        # Regulations Badge
        reg_txt = f"TIER {tier} ({l_name}) R&D REGULATIONS: Custom R&D for [{', '.join(allowed_parts)}]"
        surface.blit(self.font_badge.render(reg_txt, True, (255, 215, 0)), (320, 78))

        # 2. Left Column: Chassis Blueprint Panel
        bp_panel = layout["bp_panel_rect"]
        UITheme.draw_panel(surface, bp_panel)

        # Header inside Blueprint Panel
        hdr_rect = pygame.Rect(bp_panel.x, bp_panel.y, bp_panel.width, 28)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, hdr_rect, border_top_left_radius=4, border_top_right_radius=4)
        UITheme.draw_icon(surface, "network", (hdr_rect.x + 10, hdr_rect.y + 6), color=UITheme.ACCENT_CYAN, size=15)
        title_str = f"CHASSIS BLUEPRINT & SENSORS • CAR #{self.selected_car_slot}"
        surface.blit(self.font_title.render(title_str, True, UITheme.ACCENT_CYAN), (hdr_rect.x + 30, hdr_rect.y + 6))

        # Render Visual Blueprint Wireframe & Hotspots
        self._draw_chassis_wireframe(surface, layout["canvas_rect"], comp_by_cat, layout["hotspot_rects"])

        # 3. Selected Component R&D Deck (Bottom of Left Panel)
        rd_card = layout["rd_card_rect"]
        pygame.draw.rect(surface, (16, 22, 30), rd_card, border_radius=3)
        pygame.draw.rect(surface, UITheme.PANEL_BORDER, rd_card, width=1, border_radius=3)

        selected_comp = comp_by_cat.get(self.selected_part_category)
        if selected_comp:
            cat = selected_comp["category"]
            # Engine Tier Rules
            if cat == "ENGINE":
                is_allowed = tier <= 2
                is_fine_tune = tier == 2
            else:
                is_allowed = cat in allowed_parts and "SPEC" not in allowed_parts
                is_fine_tune = False

            fac_unlocked, fac_tier, fac_name = em.get_facility_status_for_component(gm.team_id, cat)
            is_fac_ready = fac_unlocked and fac_tier >= 1
            can_develop = is_allowed and is_fac_ready

            # Title & Badge
            ic_name = self.CATEGORY_ICONS.get(cat, "wrench")
            UITheme.draw_icon(surface, ic_name, (rd_card.x + 10, rd_card.y + 10), color=UITheme.ACCENT_CYAN, size=18)
            cat_title = f"{self.CATEGORY_NAMES.get(cat, cat)} (Generation Mk {selected_comp['generation']})"
            surface.blit(
                self.font_card_title.render(cat_title, True, (255, 255, 255)), (rd_card.x + 34, rd_card.y + 10)
            )

            # Performance & Durability Stats
            cur_dur = selected_comp.get("current_durability", 100.0 - selected_comp.get("wear_pct", 0.0))
            max_dur = selected_comp.get("max_durability", 100.0)
            sx = rd_card.x + 10
            sy = rd_card.y + 32
            sx += (
                UITheme.draw_stat_item(
                    surface,
                    sx,
                    sy,
                    "zap",
                    f"Perf: {selected_comp['performance']:.1f}",
                    self.font_body,
                    text_color=UITheme.ACCENT_CYAN,
                    icon_color=(255, 215, 0),
                    icon_size=12,
                )
                + 14
            )
            dur_col = (0, 240, 140) if cur_dur > 50 else (255, 140, 40)
            sx += (
                UITheme.draw_stat_item(
                    surface,
                    sx,
                    sy,
                    "shield",
                    f"Durability: {cur_dur:.0f}%/{max_dur:.0f}%",
                    self.font_body,
                    text_color=dur_col,
                    icon_color=dur_col,
                    icon_size=12,
                )
                + 14
            )
            UITheme.draw_stat_item(
                surface,
                sx,
                sy,
                "triangle-alert",
                f"Wear: {selected_comp['wear_pct']:.0f}%",
                self.font_body,
                text_color=UITheme.TEXT_MUTED,
                icon_color=(255, 140, 40) if selected_comp["wear_pct"] > 50 else UITheme.TEXT_MUTED,
                icon_size=11,
            )

            # Knowledge Evolution Bar
            k_min = selected_comp["knowledge_min"]
            k_max = selected_comp["knowledge_max"]
            rk_min = selected_comp.get("rel_knowledge_min", 0.0) or 0.0
            rk_max = selected_comp.get("rel_knowledge_max", 0.0) or 0.0
            races = selected_comp["races_on_concept"]

            bar_w = rd_card.width - 170
            bar_rect = pygame.Rect(rd_card.x + 10, rd_card.y + 54, bar_w, 28)
            pygame.draw.rect(surface, (10, 14, 20), bar_rect, border_radius=3)
            fill_pct = min(1.0, races / 6.0) if can_develop else 0.0
            if fill_pct > 0:
                pygame.draw.rect(
                    surface, (0, 140, 80), (bar_rect.x, bar_rect.y, int(bar_w * fill_pct), 28), border_radius=3
                )
            pygame.draw.rect(surface, (40, 48, 60), bar_rect, width=1, border_radius=3)

            if not is_allowed:
                surface.blit(
                    self.font_badge.render("SPEC COMPONENT • Regulated by Tier Rules", True, (160, 160, 160)),
                    (bar_rect.x + 8, bar_rect.y + 8),
                )
            elif not is_fac_ready:
                surface.blit(
                    self.font_badge.render(f"FACILITY LOCKED • Requires {fac_name} Level 1", True, (255, 140, 60)),
                    (bar_rect.x + 8, bar_rect.y + 8),
                )
            else:
                surface.blit(
                    self.font_badge.render(f"KNOWLEDGE ({races} races tested):", True, (255, 255, 255)),
                    (bar_rect.x + 8, bar_rect.y + 3),
                )
                kx = bar_rect.x + 8
                ky = bar_rect.y + 14
                kx += (
                    UITheme.draw_stat_item(
                        surface,
                        kx,
                        ky,
                        "zap",
                        f"+{k_min:.1f}–{k_max:.1f} Perf",
                        self.font_badge,
                        text_color=(0, 230, 245),
                        icon_color=(255, 200, 40),
                        icon_size=11,
                    )
                    + 8
                )
                UITheme.draw_stat_item(
                    surface,
                    kx,
                    ky,
                    "shield",
                    f"+{rk_min:.1f}–{rk_max:.1f}% Rel",
                    self.font_badge,
                    text_color=(0, 230, 245),
                    icon_color=(0, 240, 140),
                    icon_size=11,
                )

            # Build Button
            base_category_costs = {
                "BRAKES": 180000.0,
                "REAR_WING": 280000.0,
                "FRONT_WING": 340000.0,
                "SUSPENSION": 380000.0,
                "ENGINE": 220000.0 if tier == 2 else 1500000.0,
                "FLOOR": 450000.0,
                "ERS": 650000.0,
            }
            if can_develop:
                b_cost = base_category_costs.get(cat, 250000.0) * cost_mult
                btn_lbl = (
                    f"TUNE (${b_cost / 1000:.0f}k)"
                    if is_fine_tune
                    else f"BUILD Mk {selected_comp['generation'] + 1} (${b_cost / 1000:.0f}k)"
                )
                UITheme.draw_button(surface, layout["build_btn"], btn_lbl, self.font_btn, icon="wrench", icon_size=12)
            elif is_allowed and not is_fac_ready:
                UITheme.draw_button(
                    surface,
                    layout["build_btn"],
                    "FACILITY L1",
                    self.font_btn,
                    icon="lock",
                    icon_size=12,
                    is_disabled=True,
                )
            else:
                UITheme.draw_button(
                    surface,
                    layout["build_btn"],
                    "SPEC LOCKED",
                    self.font_btn,
                    icon="lock",
                    icon_size=12,
                    is_disabled=True,
                )

            # Buy Factory Part Button
            f_spec = FACTORY_PART_SPECS.get(tier, FACTORY_PART_SPECS.get(3, {})).get(cat, {})
            f_cost = f_spec.get("cost", 25000.0)
            UITheme.draw_button(
                surface,
                layout["buy_btn"],
                f"BUY FACTORY (${f_cost / 1000:.0f}k)",
                self.font_badge,
                icon="shopping-cart",
                icon_size=11,
            )

        # 4. Right Column: Spares Drawer & Suppliers & Next-Gen
        sp_drawer = layout["spares_drawer_rect"]
        pygame.draw.rect(surface, (16, 20, 26), sp_drawer, border_radius=4)
        pygame.draw.rect(surface, UITheme.PANEL_BORDER, sp_drawer, width=1, border_radius=4)

        cat_label = self.CATEGORY_NAMES.get(self.selected_part_category, self.selected_part_category)
        UITheme.draw_icon(surface, "factory", (sp_drawer.x + 8, sp_drawer.y + 7), color=UITheme.ACCENT_CYAN, size=15)
        surface.blit(
            self.font_card_title.render(f"WAREHOUSE SPARES: {cat_label.upper()}", True, UITheme.ACCENT_CYAN),
            (sp_drawer.x + 28, sp_drawer.y + 6),
        )

        if not layout["spare_buttons"]:
            surface.blit(
                self.font_body.render(
                    f"No {cat_label} spares in inventory. Manufacture backups in R&D.", True, UITheme.TEXT_MUTED
                ),
                (sp_drawer.x + 10, sp_drawer.y + 34),
            )
        else:
            for _, s_box, m_btn, sp in layout["spare_buttons"]:
                pygame.draw.rect(surface, (22, 28, 36), s_box, border_radius=3)
                sp_name = f"{sp['category'].replace('_', ' ')} (Mk {sp['generation']})"
                surface.blit(self.font_btn.render(sp_name, True, UITheme.TEXT_WHITE), (s_box.x + 8, s_box.y + 5))

                sp_x = s_box.x + 130
                sp_y = s_box.y + 5
                sp_x += (
                    UITheme.draw_stat_item(
                        surface,
                        sp_x,
                        sp_y,
                        "zap",
                        f"{sp['performance']:.0f}",
                        self.font_badge,
                        text_color=(0, 220, 200),
                        icon_color=(255, 200, 40),
                        icon_size=11,
                    )
                    + 8
                )
                UITheme.draw_stat_item(
                    surface,
                    sp_x,
                    sp_y,
                    "shield",
                    f"{sp.get('current_durability', 100.0):.0f}%",
                    self.font_badge,
                    text_color=(0, 220, 200),
                    icon_color=(0, 240, 140),
                    icon_size=11,
                )

                UITheme.draw_button(
                    surface, m_btn, f"MOUNT C#{self.selected_car_slot}", self.font_badge, icon="wrench", icon_size=11
                )

        # 5. Engine Suppliers Cards
        curr_supplier = gm.player_team.get("engine_supplier", "Vortex EcoTech")
        for supp_name, s_rect, sign_btn, supp in layout["supplier_cards"]:
            is_current = supp_name == curr_supplier
            pygame.draw.rect(surface, (26, 38, 52) if is_current else (18, 24, 32), s_rect, border_radius=3)
            pygame.draw.rect(
                surface,
                UITheme.ACCENT_CYAN if is_current else UITheme.PANEL_BORDER,
                s_rect,
                width=2 if is_current else 1,
                border_radius=3,
            )

            surface.blit(
                self.font_card_title.render(supp_name, True, (255, 215, 0) if is_current else UITheme.TEXT_WHITE),
                (s_rect.x + 10, s_rect.y + 5),
            )
            active_badge = "[ACTIVE SUPPLIER]" if is_current else "[SEASON CONTRACT]"
            surface.blit(
                self.font_badge.render(active_badge, True, (0, 240, 140) if is_current else UITheme.TEXT_MUTED),
                (s_rect.x + 160, s_rect.y + 7),
            )

            cost_txt = (
                f"${supp['cost_season'] / 1000000:.1f}M/yr"
                if supp["cost_season"] >= 1000000
                else f"${supp['cost_season'] / 1000:.0f}k/yr"
            )
            sx_supp = s_rect.x + 10
            sy_supp = s_rect.y + 24
            sx_supp += (
                UITheme.draw_stat_item(
                    surface,
                    sx_supp,
                    sy_supp,
                    "zap",
                    f"{supp['base_power']:.0f} HP",
                    self.font_body,
                    text_color=UITheme.TEXT_WHITE,
                    icon_color=(255, 215, 0),
                    icon_size=11,
                )
                + 8
            )
            sx_supp += (
                UITheme.draw_stat_item(
                    surface,
                    sx_supp,
                    sy_supp,
                    "shield",
                    f"{supp['reliability']:.0f}%",
                    self.font_body,
                    text_color=UITheme.TEXT_WHITE,
                    icon_color=(0, 240, 140),
                    icon_size=11,
                )
                + 8
            )
            UITheme.draw_stat_item(
                surface,
                sx_supp,
                sy_supp,
                "circle-dollar-sign",
                cost_txt,
                self.font_body,
                text_color=(0, 220, 255),
                icon_color=(0, 220, 255),
                icon_size=11,
            )

            if not is_current:
                UITheme.draw_button(surface, sign_btn, "CONTRACT", self.font_btn, icon="check", icon_size=11)

        # 6. Next-Gen Chassis R&D Card
        ng_status = em.get_team_next_gen_status(gm.team_id)
        ng_rect = layout["ng_rect"]
        pygame.draw.rect(surface, (16, 20, 28), ng_rect, border_radius=4)
        pygame.draw.rect(surface, UITheme.ACCENT_CYAN, ng_rect, width=1, border_radius=4)
        surface.blit(
            self.font_card_title.render("NEXT-YEAR CHASSIS R&D & REGULATIONS", True, (255, 215, 0)),
            (ng_rect.x + 10, ng_rect.y + 6),
        )

        regs = ng_status.get("regulations", {})
        pkg = regs.get("upcoming_package", "STATUS_QUO")
        if gm.current_week < 9:
            reg_line = "WSF STATUS: Parity & safety monitoring active (Announcement at Week 9)"
            reg_col = (200, 200, 100)
        elif pkg == "STATUS_QUO":
            reg_line = "WSF CONFIRMATION: Status Quo (Stable Rules). Chassis boosts accumulate!"
            reg_col = (0, 220, 180)
        else:
            reg_line = f"WSF DIRECTIVE: {pkg.replace('_', ' ')}! Affected parts reset to base spec."
            reg_col = (255, 130, 50)
        surface.blit(self.font_badge.render(reg_line, True, reg_col), (ng_rect.x + 10, ng_rect.y + 21))

        # Allocation buttons
        cur_alloc = ng_status.get("allocation_pct", 0.0)
        for target_pct, b_box in layout["alloc_rects"].items():
            is_sel = abs(cur_alloc - target_pct) < 1.0
            pygame.draw.rect(surface, (40, 70, 100) if is_sel else (24, 30, 40), b_box, border_radius=3)
            pygame.draw.rect(
                surface, (0, 240, 255) if is_sel else (60, 70, 85), b_box, width=2 if is_sel else 1, border_radius=3
            )
            b_lbl = self.font_badge.render(
                f"{target_pct:.0f}% R&D", True, (255, 255, 255) if is_sel else UITheme.TEXT_MUTED
            )
            surface.blit(b_lbl, (b_box.x + (b_box.width - b_lbl.get_width()) // 2, b_box.y + 4))

        # Port-Back Upgrade Button
        pb_box = layout["pb_btn"]
        cooldown = ng_status.get("port_back_cooldown_weeks", 0)
        bonus_wks = ng_status.get("port_back_bonus_weeks", 0)
        bonus_rel = ng_status.get("port_back_bonus_rel", 0.0)
        perf_b = ng_status.get("projected_perf_boost", 0.0)

        if cooldown > 0:
            pygame.draw.rect(surface, (45, 30, 15), pb_box, border_radius=3)
            pygame.draw.rect(surface, (200, 120, 40), pb_box, width=1, border_radius=3)
            pb_txt = self.font_badge.render(
                f"FACTORY RETOOLING: Port-Back in progress ({cooldown} wks remaining)", True, (255, 170, 70)
            )
            surface.blit(pb_txt, (pb_box.x + (pb_box.width - pb_txt.get_width()) // 2, pb_box.y + 5))
        elif bonus_wks > 0:
            pygame.draw.rect(surface, (20, 45, 25), pb_box, border_radius=3)
            pygame.draw.rect(surface, (40, 180, 80), pb_box, width=1, border_radius=3)
            pb_txt = self.font_badge.render(
                f"PORT-BACK ACTIVE: +{bonus_rel:.1f}% Rel telemetry ({bonus_wks} wks left)", True, (100, 255, 150)
            )
            surface.blit(pb_txt, (pb_box.x + (pb_box.width - pb_txt.get_width()) // 2, pb_box.y + 5))
        elif gm.current_week >= 13 and gm.current_week <= 16 and pkg == "STATUS_QUO" and not regs.get("port_back_used"):
            current_add = round((2.0 / 3.0) * perf_b, 1)
            UITheme.draw_button(
                surface,
                pb_box,
                f"PORT-BACK UPGRADE (+{current_add:.1f} Boost)",
                self.font_badge,
                icon="zap",
                icon_size=11,
            )
        else:
            pygame.draw.rect(surface, (18, 22, 28), pb_box, border_radius=3)
            pb_txt = self.font_badge.render(
                "Port-Back Upgrades unlock between Weeks 13–16 under Status Quo regulations.", True, UITheme.TEXT_MUTED
            )
            surface.blit(pb_txt, (pb_box.x + (pb_box.width - pb_txt.get_width()) // 2, pb_box.y + 5))

        # Bottom Status Bar
        stat_bar = layout["stat_bar"]
        pygame.draw.rect(surface, (16, 20, 26), stat_bar, border_radius=3)
        msg_surf = self.font_body.render(self.status_message, True, UITheme.TEXT_WHITE)
        surface.blit(msg_surf, (stat_bar.x + 10, stat_bar.y + 6))
