import pygame

from ...management.engineering_manager import FACTORY_PART_SPECS, EngineeringManager
from ...management.game_manager import GameManager
from ..theme import UITheme


class CarEngineeringTab:
    """Car Engineering Tab featuring continuous evolution knowledge bars, Build Mk II buttons, and engine contracts."""

    def __init__(self, screen_width: int, screen_height: int):
        self.width = screen_width
        self.height = screen_height

        self.selected_car_slot: int = 1  # Car 1 or Car 2
        self._init_fonts()
        self.status_message: str = "Select a component to inspect knowledge pool or build next generation."

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

    def handle_click(self, mx: int, my: int, gm: GameManager, em: EngineeringManager, cost_mult: float = 1.0) -> bool:
        # Car selector tabs
        c1_rect = pygame.Rect(24, 70, 140, 28)
        c2_rect = pygame.Rect(170, 70, 140, 28)
        if c1_rect.collidepoint(mx, my):
            self.selected_car_slot = 1
            return True
        elif c2_rect.collidepoint(mx, my):
            self.selected_car_slot = 2
            return True

        tier, l_name, allowed_parts = em.get_team_allowed_parts(gm.team_id)

        # Build Next Gen Component Buttons
        components = [c for c in em.get_team_components(gm.team_id) if c["car_slot"] == self.selected_car_slot]
        start_x = 24
        start_y = 110
        card_w = min(480, int(self.width * 0.38))
        card_h = 76

        for idx, comp in enumerate(components):
            cy = start_y + idx * (card_h + 8)
            build_btn = pygame.Rect(start_x + card_w - 145, cy + 10, 135, 26)
            buy_btn = pygame.Rect(start_x + card_w - 145, cy + 40, 135, 26)

            # Click BUILD button
            if build_btn.collidepoint(mx, my):
                if comp["category"] not in allowed_parts or "SPEC" in allowed_parts:
                    self.status_message = f"{comp['category']} is SPEC REGULATED in Tier {tier} ({l_name}). Earn promotion or buy Factory replacement!"
                    return True
                success, msg, gain = em.build_next_generation_part(gm.team_id, comp["id"], cost_mult=cost_mult)
                self.status_message = msg
                return True

            # Click BUY FACTORY button
            if buy_btn.collidepoint(mx, my):
                success, msg = em.buy_factory_part(gm.team_id, comp["category"], target_car_slot=self.selected_car_slot)
                self.status_message = msg
                return True

        # Right side layout dimensions
        suppliers = em.get_available_engine_suppliers(gm.team_id)
        s_start_x = start_x + card_w + 16
        s_start_y = 110
        s_card_w = self.width - s_start_x - 24
        s_card_h = 70

        # Engine Supplier Cards Click (Right side)
        for idx, supp in enumerate(suppliers[:3]):
            sy = s_start_y + idx * (s_card_h + 6)
            sign_btn = pygame.Rect(s_start_x + s_card_w - 120, sy + 20, 110, 26)
            if sign_btn.collidepoint(mx, my):
                success, msg = em.set_engine_supplier(gm.team_id, supp["name"])
                self.status_message = msg
                return True

        # Warehouse Spares Quick-Mount (under engine suppliers)
        spares = em.get_spare_parts_in_warehouse(gm.team_id)
        w_rect_x = s_start_x
        w_rect_y = 345
        w_rect_w = s_card_w
        for s_idx, sp in enumerate(spares[:2]):
            sy = w_rect_y + 28 + s_idx * 34
            sp_box_x = w_rect_x + 8
            sp_box_w = w_rect_w - 16
            mount_btn = pygame.Rect(sp_box_x + sp_box_w - 95, sy + 4, 85, 24)
            if mount_btn.collidepoint(mx, my):
                success, msg = em.mount_part_from_inventory(gm.team_id, sp["id"], self.selected_car_slot)
                self.status_message = msg
                return True

        # 5. Next-Gen R&D Card Click (under warehouse)
        ng_status = em.get_team_next_gen_status(gm.team_id)
        ng_rect_y = 450
        btn_w = 58
        btn_h = 24
        btn_y = ng_rect_y + 44
        for b_idx, target_pct in enumerate([0.0, 25.0, 50.0, 75.0]):
            b_x = s_start_x + 10 + b_idx * (btn_w + 6)
            alloc_btn = pygame.Rect(b_x, btn_y, btn_w, btn_h)
            if alloc_btn.collidepoint(mx, my):
                success, msg = em.set_next_gen_allocation(gm.team_id, target_pct)
                self.status_message = msg
                return True

        # Port-Back Button Click
        pb_btn = pygame.Rect(s_start_x + 10, ng_rect_y + 138, s_card_w - 20, 26)
        if pb_btn.collidepoint(mx, my):
            success, msg = em.execute_port_back_upgrade(gm.team_id, gm.current_week)
            self.status_message = msg
            return True

        return False

    def render(self, surface: pygame.Surface, gm: GameManager, em: EngineeringManager, cost_mult: float = 1.0):
        tier, l_name, allowed_parts = em.get_team_allowed_parts(gm.team_id)

        # 1. Car Selector Buttons
        c1_rect = pygame.Rect(24, 70, 140, 28)
        c2_rect = pygame.Rect(170, 70, 140, 28)

        UITheme.draw_button(
            surface,
            c1_rect,
            "CAR #1 (PRIMARY)",
            self.font_btn,
            is_active=self.selected_car_slot == 1,
            icon="user",
            icon_size=13,
        )

        UITheme.draw_button(
            surface,
            c2_rect,
            "CAR #2 (SECONDARY)",
            self.font_btn,
            is_active=self.selected_car_slot == 2,
            icon="user",
            icon_size=13,
        )

        # Regulations Badge
        reg_txt = f"TIER {tier} ({l_name}) R&D REGULATIONS: Custom R&D for [{', '.join(allowed_parts)}]"
        surface.blit(self.font_badge.render(reg_txt, True, (255, 215, 0)), (320, 78))

        # 2. Car Components List (Left Column)
        components = [c for c in em.get_team_components(gm.team_id) if c["car_slot"] == self.selected_car_slot]
        start_x = 24
        start_y = 110
        card_w = min(480, int(self.width * 0.38))
        card_h = 76

        base_category_costs = {
            "BRAKES": 180000.0,
            "REAR_WING": 280000.0,
            "FRONT_WING": 340000.0,
            "SUSPENSION": 380000.0,
            "ENGINE": 220000.0 if tier == 2 else 1500000.0,
            "FLOOR": 450000.0,
            "ERS": 650000.0,
        }

        for idx, comp in enumerate(components):
            cy = start_y + idx * (card_h + 8)
            c_rect = pygame.Rect(start_x, cy, card_w, card_h)

            # Engine Tier Rules: Prohibited in Tier 3, Fine-tune in Tier 2, Full build in Tier 1
            if comp["category"] == "ENGINE":
                is_allowed = tier <= 2
                is_fine_tune = tier == 2
            else:
                is_allowed = comp["category"] in allowed_parts and "SPEC" not in allowed_parts
                is_fine_tune = False

            # Dedicated facility unlock status
            fac_unlocked, fac_tier, fac_name = em.get_facility_status_for_component(gm.team_id, comp["category"])
            is_fac_ready = fac_unlocked and fac_tier >= 1
            can_develop = is_allowed and is_fac_ready

            # Card BG
            pygame.draw.rect(surface, (18, 24, 32) if can_develop else (14, 16, 20), c_rect, border_radius=3)
            pygame.draw.rect(
                surface, UITheme.PANEL_BORDER if can_develop else (35, 40, 48), c_rect, width=1, border_radius=3
            )

            # Component Title & Generation Badge
            # Component Title & Generation Badge with Icon
            cat_icon = {
                "BRAKES": "octagon",
                "REAR_WING": "flag",
                "FRONT_WING": "shield",
                "SUSPENSION": "network",
                "ENGINE": "wrench",
                "FLOOR": "shield",
                "ERS": "zap",
            }.get(comp["category"], "wrench")

            title_col = (255, 255, 255) if can_develop else UITheme.TEXT_MUTED
            UITheme.draw_icon(surface, cat_icon, (c_rect.x + 8, c_rect.y + 7), color=title_col, size=13)

            cat_name = comp["category"].replace("_", " ")
            surface.blit(
                self.font_card_title.render(
                    f"{cat_name} (Mk {comp['generation']})",
                    True,
                    title_col,
                ),
                (c_rect.x + 25, c_rect.y + 6),
            )

            # Current Performance & Durability with Icons
            cur_dur = comp.get("current_durability", 100.0 - comp.get("wear_pct", 0.0))
            max_dur = comp.get("max_durability", 100.0)
            cx_stat = c_rect.x + 10
            cy_stat = c_rect.y + 21
            stat_col = (0, 220, 240) if can_develop else UITheme.TEXT_MUTED
            cx_stat += (
                UITheme.draw_stat_item(
                    surface,
                    cx_stat,
                    cy_stat,
                    "zap",
                    f"{comp['performance']:.1f}",
                    self.font_body,
                    text_color=stat_col,
                    icon_color=(255, 200, 40) if can_develop else UITheme.TEXT_MUTED,
                    icon_size=12,
                )
                + 12
            )
            dur_col = (0, 240, 140) if cur_dur > 50 else (255, 140, 40)
            cx_stat += (
                UITheme.draw_stat_item(
                    surface,
                    cx_stat,
                    cy_stat,
                    "shield",
                    f"{cur_dur:.0f}%/{max_dur:.0f}%",
                    self.font_body,
                    text_color=dur_col if can_develop else UITheme.TEXT_MUTED,
                    icon_color=dur_col if can_develop else UITheme.TEXT_MUTED,
                    icon_size=12,
                )
                + 12
            )
            UITheme.draw_stat_item(
                surface,
                cx_stat,
                cy_stat,
                "triangle-alert",
                f"Wear {comp['wear_pct']:.0f}%",
                self.font_body,
                text_color=UITheme.TEXT_MUTED,
                icon_color=(255, 140, 40) if comp["wear_pct"] > 50 else UITheme.TEXT_MUTED,
                icon_size=11,
            )

            # Continuous Knowledge Evolution Pool Bar (2 lines for clean readability)
            k_min = comp["knowledge_min"]
            k_max = comp["knowledge_max"]
            rk_min = comp.get("rel_knowledge_min", 0.0) or 0.0
            rk_max = comp.get("rel_knowledge_max", 0.0) or 0.0
            races = comp["races_on_concept"]

            bar_w = card_w - 170
            bar_rect = pygame.Rect(c_rect.x + 10, c_rect.y + 38, bar_w, 30)
            pygame.draw.rect(surface, (10, 14, 20), bar_rect, border_radius=3)

            # Fill bar based on races on concept (max 6 races to full knowledge)
            fill_pct = min(1.0, races / 6.0) if can_develop else 0.0
            if fill_pct > 0:
                fill_w = int(bar_w * fill_pct)
                f_rect = pygame.Rect(c_rect.x + 10, c_rect.y + 38, fill_w, 30)
                pygame.draw.rect(surface, (0, 140, 80), f_rect, border_radius=3)
            pygame.draw.rect(surface, (40, 48, 60), bar_rect, width=1, border_radius=3)

            if not is_allowed:
                line1 = "SPEC COMPONENT"
                line2 = "No R&D Permitted"
                col1 = (160, 160, 160)
                col2 = (120, 120, 120)
            elif not is_fac_ready:
                line1 = "FACILITY LOCKED"
                line2 = f"Build {fac_name} (Lvl 1)"
                col1 = (255, 140, 60)
                col2 = (220, 160, 100)
            else:
                line1 = f"KNOWLEDGE: ({races} races)"
                line2 = f"+{k_min:.1f}–{k_max:.1f} Perf | +{rk_min:.1f}–{rk_max:.1f}% Rel"
                col1 = (255, 255, 255)
                col2 = (0, 230, 245)

            surface.blit(self.font_badge.render(line1, True, col1), (bar_rect.x + 6, bar_rect.y + 2))
            surface.blit(self.font_badge.render(line2, True, col2), (bar_rect.x + 6, bar_rect.y + 15))

            # Build Button / Spec Lock
            build_btn = pygame.Rect(c_rect.x + card_w - 145, cy + 10, 135, 26)
            buy_btn = pygame.Rect(c_rect.x + card_w - 145, cy + 40, 135, 26)

            if can_develop:
                b_cost = base_category_costs.get(comp["category"], 250000.0) * cost_mult
                if is_fine_tune:
                    btn_text = f"TUNE (${b_cost / 1000:.0f}k)"
                else:
                    btn_text = f"BUILD Mk {comp['generation'] + 1} (${b_cost / 1000:.0f}k)"
                UITheme.draw_button(surface, build_btn, btn_text, self.font_btn, icon="wrench", icon_size=12)
            elif is_allowed and not is_fac_ready:
                UITheme.draw_button(
                    surface, build_btn, "FACILITY L1", self.font_btn, icon="lock", icon_size=12, is_disabled=True
                )
            else:
                UITheme.draw_button(
                    surface, build_btn, "SPEC LOCKED", self.font_btn, icon="lock", icon_size=12, is_disabled=True
                )

            # Buy Factory Part Button
            f_spec = FACTORY_PART_SPECS.get(tier, FACTORY_PART_SPECS.get(3, {})).get(comp["category"], {})
            f_cost = f_spec.get("cost", 25000.0)
            UITheme.draw_button(
                surface,
                buy_btn,
                f"BUY FACTORY (${f_cost / 1000:.0f}k)",
                self.font_badge,
                icon="shopping-cart",
                icon_size=11,
            )

        # 3. Engine Suppliers (Right Column)
        s_start_x = start_x + card_w + 16
        s_start_y = 110
        s_card_w = self.width - s_start_x - 24
        s_card_h = 70

        suppliers = em.get_available_engine_suppliers(gm.team_id)
        curr_supplier = gm.player_team.get("engine_supplier", "Vortex EcoTech")

        for idx, supp in enumerate(suppliers[:3]):
            sy = s_start_y + idx * (s_card_h + 6)
            sc_rect = pygame.Rect(s_start_x, sy, s_card_w, s_card_h)

            is_current = supp["name"] == curr_supplier
            pygame.draw.rect(surface, (26, 38, 52) if is_current else (18, 24, 32), sc_rect, border_radius=3)
            pygame.draw.rect(
                surface,
                UITheme.ACCENT_CYAN if is_current else UITheme.PANEL_BORDER,
                sc_rect,
                width=2 if is_current else 1,
                border_radius=3,
            )

            # Supplier Name & Badge
            surface.blit(
                self.font_card_title.render(supp["name"], True, (255, 215, 0) if is_current else UITheme.TEXT_WHITE),
                (sc_rect.x + 10, sc_rect.y + 6),
            )

            active_badge = "[ACTIVE SUPPLIER]" if is_current else "[SEASON CONTRACT]"
            surface.blit(
                self.font_badge.render(active_badge, True, (0, 240, 140) if is_current else UITheme.TEXT_MUTED),
                (sc_rect.x + 180, sc_rect.y + 8),
            )

            # Stats with Icons
            cost_txt = (
                f"${supp['cost_season'] / 1000000:.1f}M/yr"
                if supp["cost_season"] >= 1000000
                else f"${supp['cost_season'] / 1000:.0f}k/yr"
            )
            sx_supp = sc_rect.x + 10
            sy_supp = sc_rect.y + 26
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
                    icon_size=12,
                )
                + 10
            )
            sx_supp += (
                UITheme.draw_stat_item(
                    surface,
                    sx_supp,
                    sy_supp,
                    "fuel",
                    f"{supp['fuel_efficiency']:.0f}%",
                    self.font_body,
                    text_color=UITheme.TEXT_WHITE,
                    icon_color=(140, 200, 255),
                    icon_size=12,
                )
                + 10
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
                    icon_size=12,
                )
                + 10
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
                icon_size=12,
            )

            phil = supp.get("philosophy", "")
            surface.blit(
                self.font_badge.render(f"Philosophy: {phil}", True, UITheme.TEXT_MUTED),
                (sc_rect.x + 10, sc_rect.y + 46),
            )

            # Sign Contract Button
            if not is_current:
                sign_btn = pygame.Rect(s_start_x + s_card_w - 120, sy + 20, 110, 26)
                UITheme.draw_button(surface, sign_btn, "CONTRACT", self.font_btn, icon="check", icon_size=12)

        # 4. Warehouse Spare Inventory (Right Column Mid)
        w_rect = pygame.Rect(s_start_x, 340, s_card_w, 102)
        pygame.draw.rect(surface, (16, 20, 26), w_rect, border_radius=4)
        pygame.draw.rect(surface, UITheme.PANEL_BORDER, w_rect, width=1, border_radius=4)
        UITheme.draw_icon(
            surface,
            "factory",
            (w_rect.x + 10, w_rect.y + 7),
            color=UITheme.ACCENT_CYAN,
            size=15,
        )
        surface.blit(
            self.font_card_title.render("TEAM WAREHOUSE & SPARE PARTS INVENTORY", True, UITheme.ACCENT_CYAN),
            (w_rect.x + 30, w_rect.y + 6),
        )

        spares = em.get_spare_parts_in_warehouse(gm.team_id)
        if not spares:
            surface.blit(
                self.font_body.render(
                    "No spare parts in warehouse. Buy factory parts to keep backup inventory.", True, UITheme.TEXT_MUTED
                ),
                (w_rect.x + 10, w_rect.y + 32),
            )
        else:
            for s_idx, sp in enumerate(spares[:2]):
                sy = w_rect.y + 26 + s_idx * 34
                sp_box = pygame.Rect(w_rect.x + 8, sy, w_rect.width - 16, 30)
                pygame.draw.rect(surface, (22, 28, 36), sp_box, border_radius=3)

                sp_name = f"{sp['category'].replace('_', ' ')} (Mk {sp['generation']})"
                surface.blit(self.font_btn.render(sp_name, True, UITheme.TEXT_WHITE), (sp_box.x + 8, sp_box.y + 7))

                sp_x = sp_box.x + 160
                sp_y = sp_box.y + 7
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
                    + 12
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

                m_btn = pygame.Rect(sp_box.x + sp_box.width - 100, sp_box.y + 3, 92, 24)
                UITheme.draw_button(
                    surface, m_btn, f"MOUNT C#{self.selected_car_slot}", self.font_badge, icon="wrench", icon_size=11
                )

        # 5. Next-Year Chassis R&D & Dynamic Regulations (Right Column Bottom)
        ng_status = em.get_team_next_gen_status(gm.team_id)
        ng_rect = pygame.Rect(s_start_x, 448, s_card_w, 172)
        pygame.draw.rect(surface, (16, 20, 28), ng_rect, border_radius=4)
        pygame.draw.rect(surface, UITheme.ACCENT_CYAN, ng_rect, width=1, border_radius=4)
        surface.blit(
            self.font_card_title.render("NEXT-YEAR CHASSIS R&D & REGULATIONS", True, (255, 215, 0)),
            (ng_rect.x + 10, ng_rect.y + 6),
        )

        regs = ng_status.get("regulations", {})
        pkg = regs.get("upcoming_package", "STATUS_QUO")
        if gm.current_week < 9:
            reg_line = "FIA STATUS: Parity & safety monitoring active (Announcement at Week 9)"
            reg_col = (200, 200, 100)
        elif pkg == "STATUS_QUO":
            reg_line = "FIA CONFIRMATION: Status Quo (Stable Rules). Chassis boosts accumulate!"
            reg_col = (0, 220, 180)
        else:
            reg_line = f"FIA DIRECTIVE: {pkg.replace('_', ' ')}! Affected parts reset to base spec."
            reg_col = (255, 130, 50)
        surface.blit(self.font_badge.render(reg_line, True, reg_col), (ng_rect.x + 10, ng_rect.y + 25))

        # Allocation step buttons
        cur_alloc = ng_status.get("allocation_pct", 0.0)
        btn_w = 58
        btn_h = 24
        btn_y = ng_rect.y + 44
        for b_idx, target_pct in enumerate([0.0, 25.0, 50.0, 75.0]):
            b_x = s_start_x + 10 + b_idx * (btn_w + 6)
            is_sel = abs(cur_alloc - target_pct) < 1.0
            b_box = pygame.Rect(b_x, btn_y, btn_w, btn_h)
            pygame.draw.rect(surface, (40, 70, 100) if is_sel else (24, 30, 40), b_box, border_radius=3)
            pygame.draw.rect(
                surface, (0, 240, 255) if is_sel else (60, 70, 85), b_box, width=2 if is_sel else 1, border_radius=3
            )
            b_lbl = self.font_badge.render(
                f"{target_pct:.0f}% R&D", True, (255, 255, 255) if is_sel else UITheme.TEXT_MUTED
            )
            surface.blit(b_lbl, (b_box.x + (b_box.width - b_lbl.get_width()) // 2, b_box.y + 5))

        alloc_info = f"Chassis Split: {cur_alloc:.0f}% (Current Car Dev Speed: {100 - cur_alloc:.0f}%)"
        surface.blit(self.font_body.render(alloc_info, True, UITheme.TEXT_WHITE), (s_start_x + 270, btn_y + 4))

        # Stats lines
        pts = ng_status.get("points", 0.0)
        perf_b = ng_status.get("projected_perf_boost", 0.0)
        rel_b = ng_status.get("projected_rel_boost", 0.0)
        tire_b = ng_status.get("projected_tire_pres_bonus", 0.0)
        fuel_b = ng_status.get("projected_fuel_eff_bonus", 0.0)
        stat1 = f"Accumulated: {pts:,.0f} pts | Next-Year Base Boost: +{perf_b:.1f} Perf, +{rel_b:.1f}% Rel"
        stat2 = f"Chassis Perks: +{tire_b:.1f}% Tyre Life, +{fuel_b:.1f}% Fuel Mileage (Applies to all parts!)"
        surface.blit(self.font_body.render(stat1, True, (0, 220, 255)), (ng_rect.x + 10, ng_rect.y + 74))
        surface.blit(self.font_badge.render(stat2, True, (150, 240, 150)), (ng_rect.x + 10, ng_rect.y + 92))

        # Active chassis base rating display
        act_p = ng_status.get("active_chassis_perf_boost", 0.0)
        act_r = ng_status.get("active_chassis_rel_boost", 0.0)
        cur_chassis_str = f"Active Chassis: +{act_p:.1f} Perf, +{act_r:.1f}% Rel"
        surface.blit(
            self.font_badge.render(cur_chassis_str, True, UITheme.TEXT_MUTED), (ng_rect.x + 10, ng_rect.y + 110)
        )

        # Port-Back Row
        pb_box = pygame.Rect(s_start_x + 10, ng_rect.y + 132, s_card_w - 20, 30)
        cooldown = ng_status.get("port_back_cooldown_weeks", 0)
        bonus_wks = ng_status.get("port_back_bonus_weeks", 0)
        bonus_rel = ng_status.get("port_back_bonus_rel", 0.0)

        if cooldown > 0:
            pygame.draw.rect(surface, (45, 30, 15), pb_box, border_radius=3)
            pygame.draw.rect(surface, (200, 120, 40), pb_box, width=1, border_radius=3)
            pb_txt = self.font_body.render(
                f"FACTORY RETOOLING: Port-Back Upgrade in progress ({cooldown} wks remaining)", True, (255, 170, 70)
            )
            surface.blit(pb_txt, (pb_box.x + (pb_box.width - pb_txt.get_width()) // 2, pb_box.y + 7))
        elif bonus_wks > 0:
            pygame.draw.rect(surface, (20, 45, 25), pb_box, border_radius=3)
            pygame.draw.rect(surface, (40, 180, 80), pb_box, width=1, border_radius=3)
            pb_txt = self.font_body.render(
                f"PORT-BACK TRACK TESTING: +{bonus_rel:.2f}% Rel telemetry active ({bonus_wks} wks left)",
                True,
                (100, 255, 150),
            )
            surface.blit(pb_txt, (pb_box.x + (pb_box.width - pb_txt.get_width()) // 2, pb_box.y + 7))
        elif gm.current_week >= 13 and gm.current_week <= 16 and pkg == "STATUS_QUO" and not regs.get("port_back_used"):
            pygame.draw.rect(surface, (30, 60, 85), pb_box, border_radius=3)
            pygame.draw.rect(surface, (0, 240, 255), pb_box, width=1, border_radius=3)
            current_add = round((2.0 / 3.0) * perf_b, 1)
            pb_txt = self.font_btn.render(
                f"PORT-BACK UPGRADES (Apply +{current_add:.1f} Boost to Current Car, 2-Wk Retool)",
                True,
                UITheme.TEXT_WHITE,
            )
            surface.blit(pb_txt, (pb_box.x + (pb_box.width - pb_txt.get_width()) // 2, pb_box.y + 7))
        elif regs.get("port_back_used"):
            pygame.draw.rect(surface, (20, 24, 30), pb_box, border_radius=3)
            pb_txt = self.font_badge.render(
                "In-Season Port-Back Upgrade already utilized this season.", True, UITheme.TEXT_MUTED
            )
            surface.blit(pb_txt, (pb_box.x + (pb_box.width - pb_txt.get_width()) // 2, pb_box.y + 8))
        elif pkg != "STATUS_QUO":
            pygame.draw.rect(surface, (24, 20, 20), pb_box, border_radius=3)
            pb_txt = self.font_badge.render(
                "Port-Back prohibited: upcoming rule change prevents backward compatibility.", True, (160, 120, 120)
            )
            surface.blit(pb_txt, (pb_box.x + (pb_box.width - pb_txt.get_width()) // 2, pb_box.y + 8))
        else:
            pygame.draw.rect(surface, (18, 22, 28), pb_box, border_radius=3)
            pb_txt = self.font_badge.render(
                "Port-Back Upgrades unlock between Weeks 13–16 under Status Quo regulations.", True, UITheme.TEXT_MUTED
            )
            surface.blit(pb_txt, (pb_box.x + (pb_box.width - pb_txt.get_width()) // 2, pb_box.y + 8))

        # Bottom Status Message Bar
        stat_bar = pygame.Rect(24, self.height - 36, self.width - 48, 26)
        pygame.draw.rect(surface, (16, 20, 26), stat_bar, border_radius=3)
        msg_surf = self.font_body.render(self.status_message, True, UITheme.TEXT_WHITE)
        surface.blit(msg_surf, (stat_bar.x + 10, stat_bar.y + 6))
