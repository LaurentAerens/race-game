from typing import Any, Callable, Dict, List, Optional, Tuple

import pygame

from ...management.driver_manager import TRAINING_FOCUS_OPTIONS, DriverManager
from ...management.game_manager import GameManager
from ..theme import UITheme


class DriversAcademyTab:
    """
    Drivers & Young Driver Academy Management Tab.
    Features:
    - Primary Race Drivers inspection, 11-attribute matrix, training focus, and contract renewal negotiations.
    - Living Feeder Team Seat Market: Multi-tier options, dynamic occupancy, and team expectations.
    - Junior Academy with pagination, promotion with decaying 80% Homegrown Academy Loyalty Discount.
    - Driver Market: Standard Pro Drivers, Pay-Drivers (Free Title Sponsor 2x-3x payout), and Sponsored Loan Talents.
    - Interactive Contract Negotiation Modal: Patience threshold (2-5), Salary, Bonus, Role Hierarchy, and dynamic counter-offers.
    """

    def __init__(
        self, screen_width: int, screen_height: int, on_view_driver_dossier: Optional[Callable[[int], None]] = None
    ):
        self.width = screen_width
        self.height = screen_height
        self.on_view_driver_dossier = on_view_driver_dossier

        self._init_fonts()

        # Sub-tabs: 'ACADEMY', 'SCOUTS', 'MARKET'
        self.active_subtab: str = "ACADEMY"
        self.selected_feeder_seats: Dict[int, int] = {}  # prospect_id -> seat_id
        self.selected_tier_filter: str = "ALL"  # 'ALL', '4', '5', '3', '2'
        self.market_filter: str = "ALL"  # 'ALL', 'STANDARD', 'PAY_DRIVER', 'SPONSORED_DRIVER'
        self.academy_page: int = 0
        self.scout_page: int = 0
        self.market_page: int = 0

        # Negotiation Modal State
        self.show_negotiation_modal: bool = False
        self.negotiating_driver: Optional[Dict[str, Any]] = None
        self.negotiation_is_homegrown: bool = False
        self.negotiation_main_seasons: int = 0
        self.negotiation_car_slot: int = 1  # 1 or 2
        self.offer_seasons: int = 2
        self.offer_salary: float = 25000.0
        self.offer_bonus: float = 80000.0
        self.offer_role: str = "EQUAL"  # "#1", "EQUAL", "#2"
        self.negotiation_feedback: str = ""
        self.negotiation_patience: int = 3
        self.negotiation_accepted: bool = False
        self.negotiation_walked_away: bool = False

        self.status_message: str = (
            "Manage primary race drivers, recruit talent from the Driver Market, or fund academy feeder seats."
        )

    def _init_fonts(self):
        self.font_title = UITheme.get_font(13, bold=True)
        self.font_card_title = UITheme.get_font(11, bold=True)
        self.font_body = UITheme.get_font(10, bold=False)
        self.font_badge = UITheme.get_font(9, bold=True)
        self.font_btn = UITheme.get_font(10, bold=True)
        self.font_modal_title = UITheme.get_font(14, bold=True)

    def resize(self, width: int, height: int):
        self.width = width
        self.height = height
        self._init_fonts()

    def _get_layout(self) -> Tuple[pygame.Rect, pygame.Rect]:
        left_w = min(460, int(self.width * 0.35))
        left_rect = pygame.Rect(24, 70, left_w, self.height - 150)

        right_x = left_rect.x + left_rect.width + 16
        right_w = self.width - right_x - 24
        right_rect = pygame.Rect(right_x, 70, right_w, self.height - 150)
        return left_rect, right_rect

    def _get_displayed_seats(self, available_seats: List[Dict[str, Any]], team_tier: int) -> List[Dict[str, Any]]:
        """Returns diverse seats across star ratings for display across eligible feeder tiers."""
        if self.selected_tier_filter != "ALL":
            target_t = int(self.selected_tier_filter)
            t_seats = [s for s in available_seats if s["tier"] == target_t]
            top = [s for s in t_seats if s["rating"] >= 4]
            mid = [s for s in t_seats if s["rating"] == 3]
            low = [s for s in t_seats if s["rating"] <= 2]
            res = []
            if top:
                res.extend(top[:2])
            if mid:
                res.extend(mid[:2])
            if low:
                res.extend(low[:1])
            for s in t_seats:
                if s not in res and len(res) < 5:
                    res.append(s)
            return res[:5]

        eligible_tiers = sorted([t for t in [2, 3, 4, 5] if t > team_tier])
        if not eligible_tiers:
            return []

        seats_per_tier = max(1, 5 // len(eligible_tiers))
        balanced = []
        for t in eligible_tiers:
            t_seats = [s for s in available_seats if s["tier"] == t]
            top = [s for s in t_seats if s["rating"] >= 4]
            mid = [s for s in t_seats if s["rating"] == 3]
            low = [s for s in t_seats if s["rating"] <= 2]

            t_pick = []
            if top:
                t_pick.append(top[0])
            if mid and len(t_pick) < seats_per_tier:
                t_pick.append(mid[0])
            if low and len(t_pick) < seats_per_tier:
                t_pick.append(low[0])
            for s in t_seats:
                if s not in t_pick and len(t_pick) < seats_per_tier:
                    t_pick.append(s)
            balanced.extend(t_pick)

        if len(balanced) < 5:
            for s in available_seats:
                if s not in balanced and len(balanced) < 5:
                    balanced.append(s)

        return balanced[:5]

    def open_negotiation_modal(
        self, driver: Dict[str, Any], is_homegrown: bool = False, main_team_seasons: int = 0, default_car_slot: int = 1
    ):
        """Opens interactive contract negotiation modal for a market driver, academy graduate, or existing driver renewal."""
        self.negotiating_driver = driver
        self.negotiation_is_homegrown = is_homegrown
        self.negotiation_main_seasons = main_team_seasons
        self.negotiation_car_slot = default_car_slot

        # Init base offers
        d_type = driver.get("driver_type", "STANDARD")
        if d_type == "SPONSORED_DRIVER":
            self.offer_seasons = 1
            self.offer_salary = 0.0
            self.offer_bonus = 0.0
            self.negotiation_accepted = True
            self.negotiation_feedback = f"Loan authorized! Ready for a 1-season development loan from {driver.get('parent_team_name', 'Parent Academy')}."
        elif d_type == "PAY_DRIVER":
            self.offer_seasons = max(1, min(3, driver.get("expected_seasons", 2)))
            self.offer_salary = 0.0
            self.offer_bonus = 0.0
            self.negotiation_accepted = True
            self.negotiation_feedback = f"Deal agreed! Backers at '{driver.get('pay_driver_sponsor_name', 'Title Sponsor')}' will sponsor the team immediately."
        else:
            base_sal = float(driver.get("expected_salary_race", 25000.0) or 25000.0)
            base_bon = float(driver.get("expected_signing_bonus", 80000.0) or 80000.0)
            if is_homegrown:
                discount = max(0.0, 0.80 - min(6, main_team_seasons) * 0.16)
                base_sal = max(1000.0, base_sal * (1.0 - discount))
                base_bon = max(0.0, base_bon * (1.0 - discount))
            self.offer_seasons = max(1, min(4, driver.get("expected_seasons", 2)))
            self.offer_salary = round(base_sal, -2)
            self.offer_bonus = round(base_bon, -2)
            self.negotiation_accepted = False
            self.negotiation_feedback = "Greetings! Review my contract terms and propose an offer when ready."

        self.offer_role = driver.get("expected_role", "EQUAL") or "EQUAL"
        self.negotiation_patience = driver.get("current_patience", driver.get("patience", 3))
        self.negotiation_walked_away = False
        self.show_negotiation_modal = True

    def handle_click(self, mx: int, my: int, gm: GameManager, dm: DriverManager) -> bool:
        team_tier = gm.player_team.get("tier", 3)
        car_rank = dm.get_car_performance_rank(gm.team_id)
        p_rect, r_rect = self._get_layout()

        # =====================================================================
        # 1. Handle Negotiation Modal Clicks
        # =====================================================================
        if self.show_negotiation_modal and self.negotiating_driver:
            modal_rect = pygame.Rect(self.width // 2 - 340, self.height // 2 - 250, 680, 500)
            d = self.negotiating_driver
            d_type = d.get("driver_type", "STANDARD")

            # Close button
            btn_close = pygame.Rect(modal_rect.x + modal_rect.width - 36, modal_rect.y + 10, 26, 26)
            if btn_close.collidepoint(mx, my):
                self.show_negotiation_modal = False
                return True

            # Car Slot Selection (Car #1 vs Car #2)
            btn_c1 = pygame.Rect(modal_rect.x + 140, modal_rect.y + 115, 80, 24)
            btn_c2 = pygame.Rect(modal_rect.x + 230, modal_rect.y + 115, 80, 24)
            if btn_c1.collidepoint(mx, my):
                self.negotiation_car_slot = 1
                return True
            elif btn_c2.collidepoint(mx, my):
                self.negotiation_car_slot = 2
                return True

            # Contract Length Steppers (1 to 5 seasons)
            if d_type != "SPONSORED_DRIVER":
                btn_s_dec = pygame.Rect(modal_rect.x + 140, modal_rect.y + 155, 30, 24)
                btn_s_inc = pygame.Rect(modal_rect.x + 230, modal_rect.y + 155, 30, 24)
                if btn_s_dec.collidepoint(mx, my) and self.offer_seasons > 1:
                    self.offer_seasons -= 1
                    return True
                elif btn_s_inc.collidepoint(mx, my) and self.offer_seasons < 5:
                    self.offer_seasons += 1
                    return True

            # Salary Per Race Steppers
            sal_step = 5000 if team_tier >= 3 else 25000
            btn_sal_dec = pygame.Rect(modal_rect.x + 140, modal_rect.y + 195, 30, 24)
            btn_sal_inc = pygame.Rect(modal_rect.x + 270, modal_rect.y + 195, 30, 24)
            if btn_sal_dec.collidepoint(mx, my) and self.offer_salary >= sal_step:
                self.offer_salary -= sal_step
                return True
            elif btn_sal_inc.collidepoint(mx, my):
                self.offer_salary += sal_step
                return True

            # Signing Bonus Steppers
            bon_step = 10000 if team_tier >= 3 else 50000
            btn_bon_dec = pygame.Rect(modal_rect.x + 140, modal_rect.y + 235, 30, 24)
            btn_bon_inc = pygame.Rect(modal_rect.x + 270, modal_rect.y + 235, 30, 24)
            if btn_bon_dec.collidepoint(mx, my) and self.offer_bonus >= bon_step:
                self.offer_bonus -= bon_step
                return True
            elif btn_bon_inc.collidepoint(mx, my):
                self.offer_bonus += bon_step
                return True

            # Role Status Buttons (#1, EQUAL, #2)
            btn_r1 = pygame.Rect(modal_rect.x + 140, modal_rect.y + 275, 75, 24)
            btn_req = pygame.Rect(modal_rect.x + 220, modal_rect.y + 275, 75, 24)
            btn_r2 = pygame.Rect(modal_rect.x + 300, modal_rect.y + 275, 75, 24)
            if btn_r1.collidepoint(mx, my):
                self.offer_role = "#1"
                return True
            elif btn_req.collidepoint(mx, my):
                self.offer_role = "EQUAL"
                return True
            elif btn_r2.collidepoint(mx, my):
                self.offer_role = "#2"
                return True

            # Submit Offer / Finalize Contract Button
            btn_act = pygame.Rect(modal_rect.x + 20, modal_rect.y + 435, modal_rect.width - 40, 44)
            if btn_act.collidepoint(mx, my):
                if self.negotiation_walked_away:
                    self.show_negotiation_modal = False
                    return True
                elif not self.negotiation_accepted:
                    # Evaluate Offer
                    offer_pkg = {
                        "seasons": self.offer_seasons,
                        "salary_per_race": self.offer_salary,
                        "signing_bonus": self.offer_bonus,
                        "role_status": self.offer_role,
                    }
                    eval_res = dm.evaluate_contract_offer(
                        d,
                        offer_pkg,
                        team_tier,
                        car_rank,
                        is_homegrown=self.negotiation_is_homegrown,
                        main_team_seasons=self.negotiation_main_seasons,
                    )
                    self.negotiation_accepted = eval_res["accepted"]
                    self.negotiation_walked_away = eval_res["walked_away"]
                    self.negotiation_patience = eval_res["patience_left"]
                    self.negotiation_feedback = eval_res["quote"]
                    return True
                else:
                    # Finalize Contract
                    agreed = {
                        "seasons": self.offer_seasons,
                        "salary_per_race": self.offer_salary,
                        "signing_bonus": self.offer_bonus,
                        "role_status": self.offer_role,
                    }
                    success, msg = dm.finalize_driver_contract(
                        gm.team_id,
                        self.negotiation_car_slot,
                        d,
                        agreed,
                        is_homegrown=self.negotiation_is_homegrown,
                        main_team_seasons=self.negotiation_main_seasons,
                    )
                    self.status_message = msg
                    if success:
                        gm.refresh_player_team()
                        self.show_negotiation_modal = False
                    else:
                        self.negotiation_feedback = f"Signing Failed: {msg}"
                    return True

            return True

        # =====================================================================
        # 2. Left Column: Primary Race Drivers Training Focus, Renew & Release
        # =====================================================================
        primary_drivers = dm.get_primary_drivers(gm.team_id)
        for idx, d in enumerate(primary_drivers[:2]):
            cy = 108 + idx * 175

            # Dossier button click or header click
            dossier_btn = pygame.Rect(p_rect.x + p_rect.width - 92, cy + 6, 84, 20)
            header_rect = pygame.Rect(p_rect.x + 10, cy + 4, p_rect.width - 110, 36)
            if (dossier_btn.collidepoint(mx, my) or header_rect.collidepoint(mx, my)) and self.on_view_driver_dossier:
                self.on_view_driver_dossier(d["id"])
                return True

            # Training focus
            focus_btn = pygame.Rect(p_rect.x + 65, cy + 116, p_rect.width - 240, 24)
            if focus_btn.collidepoint(mx, my):
                curr_focus = d["training_focus"]
                focus_keys = [f[0] for f in TRAINING_FOCUS_OPTIONS]
                next_idx = (focus_keys.index(curr_focus) + 1) % len(focus_keys) if curr_focus in focus_keys else 0
                new_focus = focus_keys[next_idx]
                dm.set_training_focus(d["id"], new_focus)
                self.status_message = f"{d['name']} training focus set to {new_focus}."
                return True

            # Action button: Default Stand-in -> [SIGN PRO] goes to MARKET; Contracted -> [RENEW]
            if d.get("driver_type") == "DEFAULT_DRIVER":
                sign_pro_btn = pygame.Rect(p_rect.x + p_rect.width - 165, cy + 116, 95, 24)
                if sign_pro_btn.collidepoint(mx, my):
                    self.active_subtab = "MARKET"
                    return True
            else:
                renew_btn = pygame.Rect(p_rect.x + p_rect.width - 165, cy + 116, 95, 24)
                if renew_btn.collidepoint(mx, my):
                    is_hg = bool(d.get("is_homegrown", 0))
                    m_seasons = int(d.get("main_team_seasons", 0))
                    self.open_negotiation_modal(
                        d, is_homegrown=is_hg, main_team_seasons=m_seasons, default_car_slot=idx + 1
                    )
                    return True

            # Release Driver Button (Charges buyout severance if contracted, $0 if default)
            rel_btn = pygame.Rect(p_rect.x + p_rect.width - 65, cy + 116, 55, 24)
            if rel_btn.collidepoint(mx, my):
                success, msg = dm.release_primary_driver(gm.team_id, d["id"])
                self.status_message = msg
                return True

        # =====================================================================
        # 3. Sub-Tab Switcher (ACADEMY, SCOUTS, MARKET)
        # =====================================================================
        tab_acad_rect = pygame.Rect(r_rect.x, 68, 145, 28)
        tab_scout_rect = pygame.Rect(r_rect.x + 150, 68, 160, 28)
        tab_market_rect = pygame.Rect(r_rect.x + 315, 68, 135, 28)

        if tab_acad_rect.collidepoint(mx, my):
            self.active_subtab = "ACADEMY"
            return True
        elif tab_scout_rect.collidepoint(mx, my):
            self.active_subtab = "SCOUTS"
            return True
        elif tab_market_rect.collidepoint(mx, my):
            self.active_subtab = "MARKET"
            return True

        # =====================================================================
        # 4. Junior Academy Sub-Tab Clicks
        # =====================================================================
        academy_drivers = dm.get_academy_drivers(gm.team_id)
        if self.active_subtab == "ACADEMY":
            drivers_per_page = 4
            max_pages = max(1, (len(academy_drivers) + drivers_per_page - 1) // drivers_per_page)

            if len(academy_drivers) > drivers_per_page:
                prev_btn = pygame.Rect(r_rect.x + r_rect.width - 150, 70, 65, 24)
                next_btn = pygame.Rect(r_rect.x + r_rect.width - 80, 70, 65, 24)
                if prev_btn.collidepoint(mx, my) and self.academy_page > 0:
                    self.academy_page -= 1
                    return True
                elif next_btn.collidepoint(mx, my) and self.academy_page < max_pages - 1:
                    self.academy_page += 1
                    return True

            start_y = 108
            card_w = r_rect.width - 20
            card_h = 120
            page_drivers = academy_drivers[
                self.academy_page * drivers_per_page : (self.academy_page + 1) * drivers_per_page
            ]

            for idx, d in enumerate(page_drivers):
                cy = start_y + idx * (card_h + 10)
                card_rect = pygame.Rect(r_rect.x + 10, cy, card_w, card_h)

                # Promote to Car #1 Button (Opens negotiation with 80% Homegrown loyalty discount!)
                btn_p1 = pygame.Rect(card_rect.x + card_w - 230, cy + 10, 105, 24)
                if btn_p1.collidepoint(mx, my):
                    self.open_negotiation_modal(d, is_homegrown=True, main_team_seasons=0, default_car_slot=1)
                    return True

                # Promote to Car #2 Button
                btn_p2 = pygame.Rect(card_rect.x + card_w - 115, cy + 10, 105, 24)
                if btn_p2.collidepoint(mx, my):
                    self.open_negotiation_modal(d, is_homegrown=True, main_team_seasons=0, default_car_slot=2)
                    return True

                # Seat Transfer / Mid-Season Switch Button
                btn_trans = pygame.Rect(card_rect.x + card_w - 230, cy + 42, 220, 24)
                if btn_trans.collidepoint(mx, my):
                    available_seats = dm.get_available_feeder_seats(team_tier)
                    if not available_seats:
                        self.status_message = "No open feeder seats available in lower leagues."
                        return True
                    target = available_seats[0]
                    success, msg = dm.transfer_academy_driver_seat(gm.team_id, d["id"], target["id"])
                    self.status_message = msg
                    return True

                # Dossier Button / Header Click
                btn_dos = pygame.Rect(card_rect.x + card_w - 230, cy + 76, 130, 22)
                hdr_rect = pygame.Rect(card_rect.x + 10, cy + 6, 250, 22)
                if (btn_dos.collidepoint(mx, my) or hdr_rect.collidepoint(mx, my)) and self.on_view_driver_dossier:
                    self.on_view_driver_dossier(d["id"])
                    return True

                # Release Button
                btn_rel = pygame.Rect(card_rect.x + card_w - 90, cy + 76, 80, 22)
                if btn_rel.collidepoint(mx, my):
                    success, msg = dm.release_young_driver(gm.team_id, d["id"])
                    self.status_message = msg
                    return True

        # =====================================================================
        # 5. Scout Candidates Sub-Tab Clicks
        # =====================================================================
        elif self.active_subtab == "SCOUTS":
            btn_scout = pygame.Rect(r_rect.x + r_rect.width - 190, 70, 180, 24)
            if btn_scout.collidepoint(mx, my):
                success, msg = dm.refresh_scout_search(gm.team_id, scout_cost=15000.0)
                self.status_message = msg
                return True

            scout_prospects = dm.get_scout_prospects(gm.team_id)
            prospects_per_page = 3
            max_scout_pages = max(1, (len(scout_prospects) + prospects_per_page - 1) // prospects_per_page)
            if len(scout_prospects) > prospects_per_page:
                prev_btn = pygame.Rect(r_rect.x + r_rect.width - 340, 70, 65, 24)
                next_btn = pygame.Rect(r_rect.x + r_rect.width - 270, 70, 65, 24)
                if prev_btn.collidepoint(mx, my) and self.scout_page > 0:
                    self.scout_page -= 1
                    return True
                elif next_btn.collidepoint(mx, my) and self.scout_page < max_scout_pages - 1:
                    self.scout_page += 1
                    return True

            eligible_tiers = sorted([t for t in [2, 3, 4, 5] if t > team_tier])
            tier_tabs = ["ALL"] + [str(t) for t in eligible_tiers]
            curr_tab_x = r_rect.x + 460
            for t_idx, t_val in enumerate(tier_tabs):
                pill_w = 75 if t_val == "ALL" else 60
                t_rect = pygame.Rect(curr_tab_x, 70, pill_w, 24)
                curr_tab_x += pill_w + 6
                if t_rect.collidepoint(mx, my):
                    self.selected_tier_filter = t_val
                    return True

            available_seats = dm.get_available_feeder_seats(team_tier)
            displayed_seats = self._get_displayed_seats(available_seats, team_tier)

            start_y = 108
            card_w = r_rect.width - 20
            card_h = 136

            page_scouts = scout_prospects[
                self.scout_page * prospects_per_page : (self.scout_page + 1) * prospects_per_page
            ]
            for idx, p in enumerate(page_scouts):
                cy = start_y + idx * (card_h + 10)
                card_rect = pygame.Rect(r_rect.x + 10, cy, card_w, card_h)

                # Dossier button click or header click
                btn_dos = pygame.Rect(card_rect.x + card_w - 100, cy + 6, 90, 20)
                hdr_rect = pygame.Rect(card_rect.x + 10, cy + 6, 300, 22)
                if (btn_dos.collidepoint(mx, my) or hdr_rect.collidepoint(mx, my)) and self.on_view_driver_dossier:
                    self.on_view_driver_dossier(f"scout_{p['id']}")
                    return True

                max_chips = min(5, len(displayed_seats))
                chip_w = min(128, max(100, (card_w - 180) // max(1, max_chips) - 6))

                for s_idx, seat in enumerate(displayed_seats[:5]):
                    t_btn = pygame.Rect(card_rect.x + 10 + s_idx * (chip_w + 6), cy + 78, chip_w, 48)
                    if t_btn.collidepoint(mx, my):
                        self.selected_feeder_seats[p["id"]] = seat["id"]
                        return True

                btn_sign = pygame.Rect(card_rect.x + card_w - 155, cy + 78, 145, 48)
                if btn_sign.collidepoint(mx, my):
                    sel_seat_id = self.selected_feeder_seats.get(p["id"])
                    if not sel_seat_id and displayed_seats:
                        sel_seat_id = displayed_seats[0]["id"]
                    if sel_seat_id:
                        success, msg = dm.sign_young_driver(gm.team_id, p["id"], sel_seat_id)
                        self.status_message = msg
                        return True

        # =====================================================================
        # 6. Driver Market Sub-Tab Clicks
        # =====================================================================
        elif self.active_subtab == "MARKET":
            # Market Filter Tabs
            m_filters = [("ALL", 45), ("STANDARD", 75), ("PAY_DRIVER", 95), ("SPONSORED_DRIVER", 75)]
            curr_m_x = r_rect.x + 460
            for m_val, m_w in m_filters:
                m_rect = pygame.Rect(curr_m_x, 70, m_w, 24)
                curr_m_x += m_w + 6
                if m_rect.collidepoint(mx, my):
                    self.market_filter = m_val
                    self.market_page = 0
                    return True

            car_rank = dm.get_car_performance_rank(gm.team_id)
            market_drivers = dm.get_market_drivers(team_tier, car_rank=car_rank)
            if self.market_filter != "ALL":
                market_drivers = [d for d in market_drivers if d.get("driver_type") == self.market_filter]

            drivers_per_page = 5
            max_pages = max(1, (len(market_drivers) + drivers_per_page - 1) // drivers_per_page)
            if len(market_drivers) > drivers_per_page:
                prev_btn = pygame.Rect(r_rect.x + r_rect.width - 150, 70, 65, 24)
                next_btn = pygame.Rect(r_rect.x + r_rect.width - 80, 70, 65, 24)
                if prev_btn.collidepoint(mx, my) and self.market_page > 0:
                    self.market_page -= 1
                    return True
                elif next_btn.collidepoint(mx, my) and self.market_page < max_pages - 1:
                    self.market_page += 1
                    return True

            start_y = 108
            card_w = r_rect.width - 20
            card_h = 92
            page_drivers = market_drivers[
                self.market_page * drivers_per_page : (self.market_page + 1) * drivers_per_page
            ]

            for idx, d in enumerate(page_drivers):
                cy = start_y + idx * (card_h + 8)
                card_rect = pygame.Rect(r_rect.x + 10, cy, card_w, card_h)

                # Dossier button click or header click
                btn_dos = pygame.Rect(card_rect.x + card_w - 110, cy + 3, 100, 18)
                hdr_rect = pygame.Rect(card_rect.x + 10, cy + 3, 260, 22)
                if (btn_dos.collidepoint(mx, my) or hdr_rect.collidepoint(mx, my)) and self.on_view_driver_dossier:
                    self.on_view_driver_dossier(f"market_{d['id']}")
                    return True

                btn_neg = pygame.Rect(card_rect.x + card_w - 170, cy + 24, 160, 42)
                if btn_neg.collidepoint(mx, my):
                    self.open_negotiation_modal(d, is_homegrown=False, main_team_seasons=0, default_car_slot=1)
                    return True

        return False

    def render(self, surface: pygame.Surface, gm: GameManager, dm: DriverManager):
        primary_drivers = dm.get_primary_drivers(gm.team_id)
        academy_drivers = dm.get_academy_drivers(gm.team_id)
        scout_prospects = dm.get_scout_prospects(gm.team_id)
        team_tier = gm.player_team.get("tier", 3)
        available_seats = dm.get_available_feeder_seats(team_tier)
        p_rect, r_rect = self._get_layout()

        # =====================================================================
        # 1. Left Column: Primary Race Drivers (Car #1 and Car #2)
        # =====================================================================
        UITheme.draw_panel(surface, p_rect)
        surface.blit(
            self.font_title.render("PRIMARY RACE DRIVERS", True, UITheme.TEXT_WHITE), (p_rect.x + 14, p_rect.y + 10)
        )

        for idx, d in enumerate(primary_drivers[:2]):
            cy = 108 + idx * 175
            d_rect = pygame.Rect(p_rect.x + 10, cy, p_rect.width - 20, 165)

            d_type = d.get("driver_type", "STANDARD")
            car_col = (255, 215, 0) if idx == 0 else (0, 220, 255)
            border_col = car_col

            if d_type == "DEFAULT_DRIVER":
                border_col = (130, 140, 150)
                type_tag = "STAND-IN (Free Replacement)"
                tag_col = (150, 160, 170)
            elif d_type == "PAY_DRIVER":
                border_col = (0, 240, 140)
                spon = d.get("pay_driver_sponsor_name", "")
                type_tag = f"PAY-DRIVER: {spon}" if spon else "PAY-DRIVER"
                tag_col = (0, 240, 140)
            elif d_type == "SPONSORED_DRIVER":
                border_col = (255, 140, 0)
                p_team = d.get("parent_team_name", "")
                type_tag = f"LOAN: {p_team}" if p_team else "LOAN TALENT"
                tag_col = (255, 140, 0)
            else:
                type_tag = "PRO CONTRACT"
                tag_col = car_col

            pygame.draw.rect(surface, (18, 24, 32), d_rect, border_radius=4)
            pygame.draw.rect(surface, border_col, d_rect, width=1, border_radius=4)

            # Line 1: [CAR #X] Driver Name on the left, DOSSIER button on the right
            car_lbl = f"[CAR #{idx + 1}]"
            car_surf = self.font_badge.render(car_lbl, True, car_col)
            surface.blit(car_surf, (d_rect.x + 10, d_rect.y + 7))

            name_col = (255, 215, 0) if d_type != "DEFAULT_DRIVER" else (180, 190, 200)
            name_surf = self.font_card_title.render(d["name"], True, name_col)
            surface.blit(name_surf, (d_rect.x + 10 + car_surf.get_width() + 6, d_rect.y + 6))

            # Dossier button (Right aligned)
            dossier_btn = pygame.Rect(d_rect.x + d_rect.width - 92, d_rect.y + 6, 84, 20)
            UITheme.draw_button(surface, dossier_btn, "DOSSIER", self.font_badge, icon="user", icon_size=11)

            # Line 2: Driver Demographics & Contract Type Badge (dedicated row)
            demo_str = f"{d['age']}yo | #{d['number']}"
            demo_surf = self.font_body.render(demo_str, True, UITheme.TEXT_MUTED)
            surface.blit(demo_surf, (d_rect.x + 10, d_rect.y + 24))

            tag_surf = self.font_badge.render(f"[{type_tag}]", True, tag_col)
            surface.blit(tag_surf, (d_rect.x + 10 + demo_surf.get_width() + 8, d_rect.y + 24))

            # Driver Trait Emblem Badge
            trait_name = None
            trait_icon = None
            trait_col = (0, 240, 140)
            if d.get("wet_weather", 0) >= 75:
                trait_name = "RAIN MASTER"
                trait_icon = "cloud-rain"
                trait_col = (100, 190, 255)
            elif d.get("tire_management", 0) >= 75:
                trait_name = "SMOOTH OPERATOR"
                trait_icon = "layers"
                trait_col = (255, 180, 50)
            elif d.get("defending", 0) >= 75:
                trait_name = "DEFENSIVE TANK"
                trait_icon = "shield"
                trait_col = (140, 220, 255)
            elif d.get("consistency", 0) >= 75:
                trait_name = "METRONOME"
                trait_icon = "target"
                trait_col = (0, 240, 140)
            elif d.get("pace", 0) >= 75:
                trait_name = "RAW SPEED"
                trait_icon = "zap"
                trait_col = (255, 215, 0)
            elif d.get("marketability", 0) >= 75:
                trait_name = "MEDIA STAR"
                trait_icon = "award"
                trait_col = (240, 130, 255)

            if trait_name:
                tr_x = d_rect.x + 10 + demo_surf.get_width() + 8 + tag_surf.get_width() + 8
                if tr_x + 90 < d_rect.right - 10:
                    UITheme.draw_icon(surface, trait_icon, (tr_x, d_rect.y + 25), color=trait_col, size=11)
                    surface.blit(self.font_badge.render(trait_name, True, trait_col), (tr_x + 14, d_rect.y + 24))

            # 8 Driving Stats with Icons
            sx1 = d_rect.x + 10
            sy1 = d_rect.y + 42
            gap = 12
            sx1 += (
                UITheme.draw_stat_item(
                    surface,
                    sx1,
                    sy1,
                    "zap",
                    f"Pace: {d['pace']}",
                    self.font_body,
                    UITheme.TEXT_WHITE,
                    (255, 215, 0),
                    icon_size=12,
                    gap=3,
                )
                + gap
            )
            sx1 += (
                UITheme.draw_stat_item(
                    surface,
                    sx1,
                    sy1,
                    "disc",
                    f"Braking: {d['braking']}",
                    self.font_body,
                    UITheme.TEXT_WHITE,
                    (0, 220, 255),
                    icon_size=12,
                    gap=3,
                )
                + gap
            )
            sx1 += (
                UITheme.draw_stat_item(
                    surface,
                    sx1,
                    sy1,
                    "flag",
                    f"Starts: {d['race_starts']}",
                    self.font_body,
                    UITheme.TEXT_WHITE,
                    (200, 215, 230),
                    icon_size=12,
                    gap=3,
                )
                + gap
            )
            UITheme.draw_stat_item(
                surface,
                sx1,
                sy1,
                "target",
                f"Consistency: {d['consistency']}",
                self.font_body,
                UITheme.TEXT_WHITE,
                (0, 240, 140),
                icon_size=12,
                gap=3,
            )

            # Row 2: Tires, Defending, Fuel, Wet
            sx2 = d_rect.x + 10
            sy2 = d_rect.y + 58
            sx2 += (
                UITheme.draw_stat_item(
                    surface,
                    sx2,
                    sy2,
                    "layers",
                    f"Tires: {d['tire_management']}",
                    self.font_body,
                    UITheme.TEXT_WHITE,
                    (255, 170, 50),
                    icon_size=12,
                    gap=3,
                )
                + gap
            )
            sx2 += (
                UITheme.draw_stat_item(
                    surface,
                    sx2,
                    sy2,
                    "shield",
                    f"Defending: {d['defending']}",
                    self.font_body,
                    UITheme.TEXT_WHITE,
                    (100, 200, 255),
                    icon_size=12,
                    gap=3,
                )
                + gap
            )
            sx2 += (
                UITheme.draw_stat_item(
                    surface,
                    sx2,
                    sy2,
                    "fuel",
                    f"Fuel: {d['fuel_efficiency']}",
                    self.font_body,
                    UITheme.TEXT_WHITE,
                    (140, 230, 140),
                    icon_size=12,
                    gap=3,
                )
                + gap
            )
            UITheme.draw_stat_item(
                surface,
                sx2,
                sy2,
                "cloud-rain",
                f"Wet: {d['wet_weather']}",
                self.font_body,
                UITheme.TEXT_WHITE,
                (120, 190, 255),
                icon_size=12,
                gap=3,
            )

            # 3 Off-Track Stats with Icons
            sx3 = d_rect.x + 10
            sy3 = d_rect.y + 74
            sx3 += (
                UITheme.draw_stat_item(
                    surface,
                    sx3,
                    sy3,
                    "wrench",
                    f"Technical: {d['technical_understanding']}",
                    self.font_body,
                    (0, 200, 255),
                    (0, 200, 255),
                    icon_size=12,
                    gap=3,
                )
                + gap
            )
            sx3 += (
                UITheme.draw_stat_item(
                    surface,
                    sx3,
                    sy3,
                    "radio",
                    f"Communication: {d['communication']}",
                    self.font_body,
                    (0, 200, 255),
                    (140, 200, 255),
                    icon_size=12,
                    gap=3,
                )
                + gap
            )
            UITheme.draw_stat_item(
                surface,
                sx3,
                sy3,
                "trending-up",
                f"Commercial: {d['marketability']}",
                self.font_body,
                (0, 200, 255),
                (255, 215, 0),
                icon_size=12,
                gap=3,
            )

            # Career Stage & Contract Buyout info
            age = d.get("age", 25)
            buyout_val = dm.get_driver_buyout_cost(d)
            buyout_str = f"Severance: ${buyout_val:,.0f}" if buyout_val > 0 else "Severance: $0 (Free)"

            if d_type == "DEFAULT_DRIVER":
                dev_text = f"EMERGENCY STAND-IN ($2.5k/mo | 0-Yr Contract | {buyout_str})"
                dev_color = (150, 160, 170)
            elif age <= 28:
                dev_text = f"DEVELOPING (Age {age} - Peak at 28 | {buyout_str})"
                dev_color = (0, 240, 140)
            elif age <= 30:
                dev_text = f"PEAK PRIME (Age {age} - Optimal Window | {buyout_str})"
                dev_color = (255, 215, 0)
            else:
                dev_text = f"VETERAN (Age {age} - Physical Decline Active | {buyout_str})"
                dev_color = (255, 140, 40)

            dev_bar = pygame.Rect(d_rect.x + 10, d_rect.y + 94, d_rect.width - 20, 16)
            pygame.draw.rect(surface, (14, 20, 28), dev_bar, border_radius=2)
            pygame.draw.rect(surface, dev_color, dev_bar, width=1, border_radius=2)
            surface.blit(self.font_badge.render(dev_text, True, dev_color), (dev_bar.x + 6, dev_bar.y + 2))

            # Focus Button
            surface.blit(self.font_badge.render("FOCUS:", True, UITheme.TEXT_MUTED), (d_rect.x + 10, d_rect.y + 120))
            focus_btn = pygame.Rect(d_rect.x + 65, d_rect.y + 116, d_rect.width - 240, 24)
            pygame.draw.rect(surface, (35, 50, 70), focus_btn, border_radius=3)
            btn_txt = self.font_btn.render(f"[{d['training_focus']}]", True, UITheme.TEXT_WHITE)
            surface.blit(btn_txt, (focus_btn.x + (focus_btn.width - btn_txt.get_width()) // 2, focus_btn.y + 4))

            # Action Button: [SIGN PRO] or [RENEW]
            if d_type == "DEFAULT_DRIVER":
                sign_pro_btn = pygame.Rect(d_rect.x + d_rect.width - 165, cy + 116, 95, 24)
                pygame.draw.rect(surface, (0, 180, 120), sign_pro_btn, border_radius=3)
                s_txt = self.font_btn.render("+ SIGN PRO", True, (10, 25, 20))
                surface.blit(
                    s_txt, (sign_pro_btn.x + (sign_pro_btn.width - s_txt.get_width()) // 2, sign_pro_btn.y + 4)
                )
            else:
                renew_btn = pygame.Rect(d_rect.x + d_rect.width - 165, cy + 116, 95, 24)
                pygame.draw.rect(surface, (30, 65, 95), renew_btn, border_radius=3)
                r_txt = self.font_btn.render("RENEW", True, (0, 220, 255))
                surface.blit(r_txt, (renew_btn.x + (renew_btn.width - r_txt.get_width()) // 2, renew_btn.y + 4))

            # Release Button
            rel_btn = pygame.Rect(d_rect.x + d_rect.width - 65, cy + 116, 55, 24)
            pygame.draw.rect(surface, (140, 40, 40), rel_btn, border_radius=3)
            rel_txt = self.font_btn.render("FIRE", True, (255, 220, 220))
            surface.blit(rel_txt, (rel_btn.x + (rel_btn.width - rel_txt.get_width()) // 2, rel_btn.y + 4))

        # Driver Talent Radar Comparison (Car #1 vs Car #2)
        radar_y = 460
        radar_bottom = p_rect.y + p_rect.height - 48
        radar_h = radar_bottom - radar_y
        if radar_h >= 75 and len(primary_drivers) > 0:
            radar_panel = pygame.Rect(p_rect.x + 10, radar_y, p_rect.width - 20, radar_h)
            pygame.draw.rect(surface, (18, 24, 32), radar_panel, border_radius=3)
            pygame.draw.rect(surface, UITheme.PANEL_BORDER, radar_panel, width=1, border_radius=3)

            r_hdr = pygame.Rect(radar_panel.x, radar_panel.y, radar_panel.width, 22)
            pygame.draw.rect(surface, UITheme.PANEL_HEADER, r_hdr, border_top_left_radius=3, border_top_right_radius=3)
            UITheme.draw_icon(surface, "sparkles", (r_hdr.x + 8, r_hdr.y + 4), color=(0, 220, 255), size=12)
            surface.blit(
                self.font_badge.render("TALENT RADAR — CAR #1 vs CAR #2 COMPARISON", True, (0, 220, 255)),
                (r_hdr.x + 24, r_hdr.y + 4),
            )

            d1 = primary_drivers[0]
            d2 = primary_drivers[1] if len(primary_drivers) > 1 else None

            radar_attrs = ["Pace", "Brake", "Defend", "Consist", "Tires", "Wet"]
            v1 = [
                float(d1.get("pace", 60)),
                float(d1.get("braking", 60)),
                float(d1.get("defending", 60)),
                float(d1.get("consistency", 60)),
                float(d1.get("tire_management", 60)),
                float(d1.get("wet_weather", 60)),
            ]
            v2 = (
                [
                    float(d2.get("pace", 60)),
                    float(d2.get("braking", 60)),
                    float(d2.get("defending", 60)),
                    float(d2.get("consistency", 60)),
                    float(d2.get("tire_management", 60)),
                    float(d2.get("wet_weather", 60)),
                ]
                if d2
                else None
            )

            rc_cx = radar_panel.x + radar_panel.width // 2
            available_h = radar_panel.height - 24
            rad = max(18, min(40, (available_h - 22) // 2))
            rc_cy = radar_panel.y + 24 + available_h // 2 - 4

            UITheme.draw_radar_chart(
                surface,
                center=(rc_cx, rc_cy),
                radius=rad,
                attributes=radar_attrs,
                values_1=v1,
                values_2=v2,
                label_1=f"C1: {d1['name'][:7]}",
                label_2=f"C2: {d2['name'][:7]}" if d2 else None,
                color_1=(255, 215, 0),
                color_2=(0, 220, 255),
                show_labels=True,
            )

        # Bottom Left Info Note
        l_note = pygame.Rect(p_rect.x + 10, p_rect.y + p_rect.height - 42, p_rect.width - 20, 32)
        pygame.draw.rect(surface, (16, 22, 30), l_note, border_radius=3)
        surface.blit(
            self.font_badge.render(
                "Negotiate contracts or recruit Pay/Sponsored talents from Market.", True, (255, 215, 0)
            ),
            (l_note.x + 8, l_note.y + 8),
        )

        # =====================================================================
        # 2. Right Column Sub-Tabs (ACADEMY, SCOUTS, MARKET)
        # =====================================================================
        UITheme.draw_panel(surface, r_rect)

        tab_acad_rect = pygame.Rect(r_rect.x, 68, 145, 28)
        tab_scout_rect = pygame.Rect(r_rect.x + 150, 68, 160, 28)
        tab_market_rect = pygame.Rect(r_rect.x + 315, 68, 135, 28)

        is_acad = self.active_subtab == "ACADEMY"
        UITheme.draw_button(
            surface,
            tab_acad_rect,
            f"ACADEMY ({len(academy_drivers)})",
            self.font_btn,
            is_active=is_acad,
            icon="graduation-cap",
            icon_size=13,
        )

        is_scout = self.active_subtab == "SCOUTS"
        UITheme.draw_button(
            surface,
            tab_scout_rect,
            f"SCOUTS ({len(scout_prospects)})",
            self.font_btn,
            is_active=is_scout,
            icon="search",
            icon_size=13,
        )

        is_market = self.active_subtab == "MARKET"
        UITheme.draw_button(
            surface,
            tab_market_rect,
            "MARKET",
            self.font_btn,
            is_active=is_market,
            icon="briefcase",
            icon_size=13,
        )

        # =====================================================================
        # View 1: JUNIOR ACADEMY
        # =====================================================================
        if is_acad:
            drivers_per_page = 4
            max_pages = max(1, (len(academy_drivers) + drivers_per_page - 1) // drivers_per_page)

            if len(academy_drivers) > drivers_per_page:
                prev_btn = pygame.Rect(r_rect.x + r_rect.width - 150, 70, 65, 24)
                next_btn = pygame.Rect(r_rect.x + r_rect.width - 80, 70, 65, 24)
                pygame.draw.rect(surface, (30, 45, 60), prev_btn, border_radius=3)
                pygame.draw.rect(
                    surface,
                    (0, 220, 255) if self.academy_page > 0 else (40, 50, 60),
                    prev_btn,
                    width=1,
                    border_radius=3,
                )
                surface.blit(
                    self.font_btn.render(
                        "< PREV", True, UITheme.TEXT_WHITE if self.academy_page > 0 else UITheme.TEXT_MUTED
                    ),
                    (prev_btn.x + 8, prev_btn.y + 4),
                )

                pygame.draw.rect(surface, (30, 45, 60), next_btn, border_radius=3)
                pygame.draw.rect(
                    surface,
                    (0, 220, 255) if self.academy_page < max_pages - 1 else (40, 50, 60),
                    next_btn,
                    width=1,
                    border_radius=3,
                )
                surface.blit(
                    self.font_btn.render(
                        "NEXT >", True, UITheme.TEXT_WHITE if self.academy_page < max_pages - 1 else UITheme.TEXT_MUTED
                    ),
                    (next_btn.x + 8, next_btn.y + 4),
                )

            if not academy_drivers:
                empty_rect = pygame.Rect(r_rect.x + 16, 120, r_rect.width - 32, 160)
                pygame.draw.rect(surface, (16, 22, 30), empty_rect, border_radius=4)
                pygame.draw.rect(surface, (45, 60, 80), empty_rect, width=1, border_radius=4)
                surface.blit(
                    self.font_card_title.render("NO YOUNG DRIVERS CURRENTLY IN ACADEMY", True, (255, 215, 0)),
                    (empty_rect.x + 20, empty_rect.y + 20),
                )
                surface.blit(
                    self.font_body.render(
                        "Click [SCOUT CANDIDATES] above to discover young talents or [DRIVER MARKET] to hire pros.",
                        True,
                        UITheme.TEXT_WHITE,
                    ),
                    (empty_rect.x + 20, empty_rect.y + 48),
                )
                surface.blit(
                    self.font_badge.render(
                        "• Homegrown Stars: Graduating academy drivers ask for 80% lower salary in Year 1!",
                        True,
                        (0, 240, 140),
                    ),
                    (empty_rect.x + 20, empty_rect.y + 80),
                )
            else:
                start_y = 108
                card_w = r_rect.width - 20
                card_h = 120
                page_drivers = academy_drivers[
                    self.academy_page * drivers_per_page : (self.academy_page + 1) * drivers_per_page
                ]

                for idx, d in enumerate(page_drivers):
                    cy = start_y + idx * (card_h + 10)
                    card_rect = pygame.Rect(r_rect.x + 10, cy, card_w, card_h)

                    pygame.draw.rect(surface, (18, 24, 32), card_rect, border_radius=3)
                    s_rating = d.get("academy_seat_rating", 3) or 3
                    b_color = (0, 240, 140) if s_rating >= 4 else ((255, 200, 0) if s_rating == 3 else (255, 100, 100))
                    pygame.draw.rect(surface, b_color, card_rect, width=1, border_radius=3)

                    t_name = d.get("academy_team_name") or "Feeder Seat"
                    t_cost = d.get("academy_seat_cost", 0.0) or 0.0
                    cost_fmt = f"${t_cost / 1000000:.1f}M" if t_cost >= 1000000 else f"${t_cost / 1000:.0f}k"
                    exp_rank = d.get("academy_seat_expected_pos") or "P1 / 10"

                    surface.blit(
                        self.font_card_title.render(
                            f"#{d['number']} {d['name']} ({d['age']}yo | Pot: {d['potential']})", True, (255, 215, 0)
                        ),
                        (card_rect.x + 10, card_rect.y + 8),
                    )
                    surface.blit(
                        self.font_badge.render(
                            f"RACING AT: {t_name} (Tier {d['academy_tier_placement']} Feeder | Expected Rank: {exp_rank} | {cost_fmt}/yr)",
                            True,
                            (0, 220, 255),
                        ),
                        (card_rect.x + 10, card_rect.y + 28),
                    )

                    mor = d["morale"]
                    mental_status = (
                        "Peak Mental Form" if mor >= 90 else ("Solid Confidence" if mor >= 75 else "Mental Fatigue")
                    )
                    mor_col = (0, 240, 140) if mor >= 85 else ((255, 200, 0) if mor >= 70 else (255, 90, 90))
                    UITheme.draw_stat_item(
                        surface,
                        card_rect.x + 10,
                        card_rect.y + 48,
                        "heart",
                        f"Mental Morale: {mor:.0f}% — {mental_status}",
                        self.font_badge,
                        text_color=mor_col,
                        icon_color=mor_col,
                        icon_size=12,
                        gap=4,
                    )

                    st_x = card_rect.x + 10
                    st_y = card_rect.y + 68
                    gap = 10
                    st_x += (
                        UITheme.draw_stat_item(
                            surface,
                            st_x,
                            st_y,
                            "zap",
                            f"Pace: {d['pace']}",
                            self.font_body,
                            UITheme.TEXT_WHITE,
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
                            "disc",
                            f"Braking: {d['braking']}",
                            self.font_body,
                            UITheme.TEXT_WHITE,
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
                            "flag",
                            f"Starts: {d['race_starts']}",
                            self.font_body,
                            UITheme.TEXT_WHITE,
                            (200, 215, 230),
                            icon_size=12,
                            gap=3,
                        )
                        + gap
                    )
                    UITheme.draw_stat_item(
                        surface,
                        st_x,
                        st_y,
                        "layers",
                        f"Tires: {d['tire_management']}",
                        self.font_body,
                        UITheme.TEXT_WHITE,
                        (255, 170, 50),
                        icon_size=12,
                        gap=3,
                    )

                    # Promote Buttons (Opens Negotiation Modal with 80% Homegrown loyalty discount)
                    btn_p1 = pygame.Rect(card_rect.x + card_w - 230, cy + 10, 105, 24)
                    pygame.draw.rect(surface, (0, 160, 90), btn_p1, border_radius=3)
                    p1_lbl = self.font_btn.render("PROMOTE CAR #1", True, (10, 20, 15))
                    surface.blit(p1_lbl, (btn_p1.x + (btn_p1.width - p1_lbl.get_width()) // 2, btn_p1.y + 4))

                    btn_p2 = pygame.Rect(card_rect.x + card_w - 115, cy + 10, 105, 24)
                    pygame.draw.rect(surface, (0, 160, 90), btn_p2, border_radius=3)
                    p2_lbl = self.font_btn.render("PROMOTE CAR #2", True, (10, 20, 15))
                    surface.blit(p2_lbl, (btn_p2.x + (btn_p2.width - p2_lbl.get_width()) // 2, btn_p2.y + 4))

                    # Switch Feeder Seat
                    btn_trans = pygame.Rect(card_rect.x + card_w - 230, cy + 42, 220, 24)
                    pygame.draw.rect(surface, (35, 75, 110), btn_trans, border_radius=3)
                    trans_lbl = self.font_btn.render("SWITCH FEEDER SEAT", True, (255, 255, 255))
                    surface.blit(
                        trans_lbl, (btn_trans.x + (btn_trans.width - trans_lbl.get_width()) // 2, btn_trans.y + 4)
                    )

                    # Dossier Button
                    btn_dos = pygame.Rect(card_rect.x + card_w - 230, cy + 76, 130, 22)
                    pygame.draw.rect(surface, (30, 48, 66), btn_dos, border_radius=3)
                    pygame.draw.rect(surface, UITheme.ACCENT_CYAN, btn_dos, width=1, border_radius=3)
                    dos_lbl = self.font_badge.render("DOSSIER 👤", True, UITheme.TEXT_WHITE)
                    surface.blit(dos_lbl, (btn_dos.x + (btn_dos.width - dos_lbl.get_width()) // 2, btn_dos.y + 4))
                    UITheme.draw_button(surface, btn_dos, "DOSSIER", self.font_badge, icon="user", icon_size=11)

                    # Release Button
                    btn_rel = pygame.Rect(card_rect.x + card_w - 90, cy + 76, 80, 22)
                    pygame.draw.rect(surface, (140, 40, 40), btn_rel, border_radius=3)
                    rel_lbl = self.font_btn.render("RELEASE", True, (255, 220, 220))
                    surface.blit(rel_lbl, (btn_rel.x + (btn_rel.width - rel_lbl.get_width()) // 2, btn_rel.y + 3))

        # =====================================================================
        # View 2: SCOUT CANDIDATES
        # =====================================================================
        elif is_scout:
            # Scout Search Button at top right
            btn_scout = pygame.Rect(r_rect.x + r_rect.width - 190, 70, 180, 24)
            pygame.draw.rect(surface, (0, 180, 120), btn_scout, border_radius=3)
            btn_scout_lbl = self.font_btn.render("SCOUT SEARCH ($15k)", True, (10, 30, 20))
            surface.blit(
                btn_scout_lbl, (btn_scout.x + (btn_scout.width - btn_scout_lbl.get_width()) // 2, btn_scout.y + 4)
            )

            # Pagination Controls
            prospects_per_page = 3
            max_scout_pages = max(1, (len(scout_prospects) + prospects_per_page - 1) // prospects_per_page)
            if len(scout_prospects) > prospects_per_page:
                prev_btn = pygame.Rect(r_rect.x + r_rect.width - 340, 70, 65, 24)
                next_btn = pygame.Rect(r_rect.x + r_rect.width - 270, 70, 65, 24)
                UITheme.draw_button(surface, prev_btn, "< PREV", self.font_badge, is_disabled=self.scout_page == 0)
                UITheme.draw_button(
                    surface, next_btn, "NEXT >", self.font_badge, is_disabled=self.scout_page >= max_scout_pages - 1
                )

            eligible_tiers = sorted([t for t in [2, 3, 4, 5] if t > team_tier])
            tier_tabs = ["ALL"] + [str(t) for t in eligible_tiers]
            curr_tab_x = r_rect.x + 460

            for t_idx, t_val in enumerate(tier_tabs):
                pill_w = 75 if t_val == "ALL" else 60
                t_lbl_str = f"TIER {t_val}" if t_val != "ALL" else "ALL TIERS"
                t_rect = pygame.Rect(curr_tab_x, 70, pill_w, 24)
                curr_tab_x += pill_w + 6
                is_sel = self.selected_tier_filter == t_val
                pygame.draw.rect(surface, (40, 60, 85) if is_sel else (20, 26, 34), t_rect, border_radius=3)
                pygame.draw.rect(surface, (0, 220, 255) if is_sel else (45, 55, 65), t_rect, width=1, border_radius=3)
                t_text = self.font_badge.render(t_lbl_str, True, (255, 255, 255) if is_sel else UITheme.TEXT_MUTED)
                surface.blit(t_text, (t_rect.x + (t_rect.width - t_text.get_width()) // 2, t_rect.y + 5))

            displayed_seats = self._get_displayed_seats(available_seats, team_tier)
            start_y = 108
            card_w = r_rect.width - 20
            card_h = 136

            page_scouts = scout_prospects[
                self.scout_page * prospects_per_page : (self.scout_page + 1) * prospects_per_page
            ]
            for idx, p in enumerate(page_scouts):
                cy = start_y + idx * (card_h + 10)
                card_rect = pygame.Rect(r_rect.x + 10, cy, card_w, card_h)

                pygame.draw.rect(surface, (18, 24, 32), card_rect, border_radius=3)
                pygame.draw.rect(surface, (45, 60, 80), card_rect, width=1, border_radius=3)

                star_str = "⭐" * p["scout_rating"]
                surface.blit(
                    self.font_card_title.render(
                        f"{p['name']} ({p['age']}yo | {p['nationality']}) — Pot: {p['potential']} {star_str}",
                        True,
                        (255, 215, 0),
                    ),
                    (card_rect.x + 10, card_rect.y + 8),
                )

                # Dossier Button
                btn_dos = pygame.Rect(card_rect.x + card_w - 100, cy + 6, 90, 20)
                UITheme.draw_button(surface, btn_dos, "DOSSIER", self.font_badge, icon="user", icon_size=10)

                surface.blit(
                    self.font_body.render(f'Scout Report: "{p["scouting_notes"]}"', True, (170, 185, 200)),
                    (card_rect.x + 10, card_rect.y + 26),
                )

                st_x = card_rect.x + 10
                st_y = card_rect.y + 44
                gap = 10
                st_x += (
                    UITheme.draw_stat_item(
                        surface,
                        st_x,
                        st_y,
                        "zap",
                        f"Pace: {p['pace']}",
                        self.font_badge,
                        (0, 220, 255),
                        (255, 215, 0),
                        icon_size=11,
                        gap=3,
                    )
                    + gap
                )
                st_x += (
                    UITheme.draw_stat_item(
                        surface,
                        st_x,
                        st_y,
                        "disc",
                        f"Braking: {p['braking']}",
                        self.font_badge,
                        (0, 220, 255),
                        (0, 220, 255),
                        icon_size=11,
                        gap=3,
                    )
                    + gap
                )
                st_x += (
                    UITheme.draw_stat_item(
                        surface,
                        st_x,
                        st_y,
                        "flag",
                        f"Starts: {p['race_starts']}",
                        self.font_badge,
                        (0, 220, 255),
                        (200, 215, 230),
                        icon_size=11,
                        gap=3,
                    )
                    + gap
                )
                st_x += (
                    UITheme.draw_stat_item(
                        surface,
                        st_x,
                        st_y,
                        "layers",
                        f"Tires: {p['tire_management']}",
                        self.font_badge,
                        (0, 220, 255),
                        (255, 170, 50),
                        icon_size=11,
                        gap=3,
                    )
                    + gap
                )
                UITheme.draw_stat_item(
                    surface,
                    st_x,
                    st_y,
                    "cloud-rain",
                    f"Wet: {p['wet_weather']}",
                    self.font_badge,
                    (0, 220, 255),
                    (120, 190, 255),
                    icon_size=11,
                    gap=3,
                )

                sel_seat_id = self.selected_feeder_seats.get(p["id"])
                sel_seat_obj = next((s for s in available_seats if s["id"] == sel_seat_id), None)
                if not sel_seat_obj:
                    eligible_first = next(
                        (s for s in displayed_seats if dm.can_driver_sign_seat(p, s)[0]),
                        displayed_seats[0] if displayed_seats else None,
                    )
                    sel_seat_obj = eligible_first
                    if sel_seat_obj:
                        self.selected_feeder_seats[p["id"]] = sel_seat_obj["id"]

                if sel_seat_obj:
                    sel_tier = sel_seat_obj["tier"]
                    sel_fee = sel_seat_obj["cost"]
                    sel_fee_fmt = (
                        f"${sel_fee / 1000000:.2f}M/yr" if sel_fee >= 1000000 else f"${sel_fee / 1000:.0f}k/yr"
                    )
                    p_note = sel_seat_obj.get("pricing_note", "")
                    exp_rank = sel_seat_obj.get("expected_pos", "P1 / 10")
                    scarcity_note = (
                        f"(Scarcity: +{sel_seat_obj['scarcity_pct']}%)"
                        if sel_seat_obj.get("scarcity_pct", 0) > 0
                        else ""
                    )
                    t_info_str = f"Selected: [TIER {sel_tier}] {sel_seat_obj['team_name']} (Expected Rank: {exp_rank}) — {sel_fee_fmt} {scarcity_note} | {p_note}"
                    surface.blit(
                        self.font_badge.render(t_info_str, True, (0, 240, 140)), (card_rect.x + 10, card_rect.y + 60)
                    )

                max_chips = min(5, len(displayed_seats))
                chip_w = min(128, max(100, (card_w - 180) // max(1, max_chips) - 6))
                tier_colors = {5: (0, 180, 255), 4: (255, 180, 0), 3: (180, 100, 255), 2: (0, 240, 140)}

                for s_idx, seat in enumerate(displayed_seats[:5]):
                    t_btn = pygame.Rect(card_rect.x + 10 + s_idx * (chip_w + 6), cy + 78, chip_w, 48)
                    is_t_sel = sel_seat_obj and sel_seat_obj["id"] == seat["id"]
                    is_ok, reason = dm.can_driver_sign_seat(p, seat)
                    t_badge_col = tier_colors.get(seat["tier"], (0, 220, 255))

                    if not is_ok:
                        pygame.draw.rect(surface, (16, 18, 22), t_btn, border_radius=3)
                        pygame.draw.rect(surface, (45, 45, 50), t_btn, width=1, border_radius=3)
                        surface.blit(
                            self.font_badge.render(
                                f"[T{seat['tier']}] {seat['team_name'][:11]}", True, (120, 120, 130)
                            ),
                            (t_btn.x + 5, t_btn.y + 4),
                        )
                        surface.blit(
                            self.font_badge.render("INELIGIBLE", True, (255, 90, 90)), (t_btn.x + 5, t_btn.y + 18)
                        )
                    else:
                        pygame.draw.rect(surface, (30, 50, 70) if is_t_sel else (16, 20, 26), t_btn, border_radius=3)
                        pygame.draw.rect(
                            surface,
                            (0, 240, 140) if is_t_sel else (45, 55, 65),
                            t_btn,
                            width=2 if is_t_sel else 1,
                            border_radius=3,
                        )
                        exp_pos = seat.get("expected_pos", "P1 / 10")
                        c_val = seat["cost"]
                        cost_txt = f"${c_val / 1000000:.1f}M" if c_val >= 1000000 else f"${c_val / 1000:.0f}k"
                        surface.blit(
                            self.font_badge.render(
                                f"[T{seat['tier']}] {seat['team_name'][:13]}",
                                True,
                                t_badge_col if not is_t_sel else (255, 255, 255),
                            ),
                            (t_btn.x + 5, t_btn.y + 4),
                        )
                        surface.blit(
                            self.font_badge.render(f"Exp: {exp_pos} ({cost_txt})", True, (255, 215, 0)),
                            (t_btn.x + 5, t_btn.y + 18),
                        )
                        surface.blit(
                            self.font_badge.render(f"{seat.get('status', 'Open Seat')[:14]}", True, (0, 220, 255)),
                            (t_btn.x + 5, t_btn.y + 32),
                        )

                if sel_seat_obj:
                    fee = sel_seat_obj["cost"]
                    fee_btn_txt = f"${fee / 1000000:.2f}M" if fee >= 1000000 else f"${fee / 1000:.0f}k"
                    btn_sign = pygame.Rect(card_rect.x + card_w - 155, cy + 78, 145, 48)
                    pygame.draw.rect(surface, (0, 180, 100), btn_sign, border_radius=3)
                    sign_txt = self.font_btn.render(f"BUY SEAT ({fee_btn_txt})", True, (10, 25, 20))
                    surface.blit(sign_txt, (btn_sign.x + (btn_sign.width - sign_txt.get_width()) // 2, btn_sign.y + 16))

        # =====================================================================
        # View 3: DRIVER MARKET (Standard, Pay-Drivers, and Sponsored Loans)
        # =====================================================================
        elif is_market:
            m_filters = [("ALL", 45), ("STANDARD", 75), ("PAY_DRIVER", 95), ("SPONSORED_DRIVER", 75)]
            m_labels = [
                ("ALL", "ALL"),
                ("STANDARD", "STANDARD"),
                ("PAY_DRIVER", "PAY-DRIVERS"),
                ("SPONSORED_DRIVER", "LOANS"),
            ]
            curr_m_x = r_rect.x + 460
            for (m_val, m_w), (_, m_lbl) in zip(m_filters, m_labels):
                m_rect = pygame.Rect(curr_m_x, 70, m_w, 24)
                curr_m_x += m_w + 6
                is_sel = self.market_filter == m_val
                pygame.draw.rect(surface, (40, 60, 85) if is_sel else (20, 26, 34), m_rect, border_radius=3)
                pygame.draw.rect(surface, (0, 220, 255) if is_sel else (45, 55, 65), m_rect, width=1, border_radius=3)
                m_txt = self.font_badge.render(m_lbl, True, (255, 255, 255) if is_sel else UITheme.TEXT_MUTED)
                surface.blit(m_txt, (m_rect.x + (m_rect.width - m_txt.get_width()) // 2, m_rect.y + 5))

            car_rank = dm.get_car_performance_rank(gm.team_id)
            market_drivers = dm.get_market_drivers(team_tier, car_rank=car_rank)
            if self.market_filter != "ALL":
                market_drivers = [d for d in market_drivers if d.get("driver_type") == self.market_filter]

            drivers_per_page = 5
            max_pages = max(1, (len(market_drivers) + drivers_per_page - 1) // drivers_per_page)

            if len(market_drivers) > drivers_per_page:
                prev_btn = pygame.Rect(r_rect.x + r_rect.width - 150, 70, 65, 24)
                next_btn = pygame.Rect(r_rect.x + r_rect.width - 80, 70, 65, 24)
                pygame.draw.rect(surface, (30, 45, 60), prev_btn, border_radius=3)
                pygame.draw.rect(
                    surface, (0, 220, 255) if self.market_page > 0 else (40, 50, 60), prev_btn, width=1, border_radius=3
                )
                surface.blit(
                    self.font_btn.render(
                        "< PREV", True, UITheme.TEXT_WHITE if self.market_page > 0 else UITheme.TEXT_MUTED
                    ),
                    (prev_btn.x + 8, prev_btn.y + 4),
                )

                pygame.draw.rect(surface, (30, 45, 60), next_btn, border_radius=3)
                pygame.draw.rect(
                    surface,
                    (0, 220, 255) if self.market_page < max_pages - 1 else (40, 50, 60),
                    next_btn,
                    width=1,
                    border_radius=3,
                )
                surface.blit(
                    self.font_btn.render(
                        "NEXT >", True, UITheme.TEXT_WHITE if self.market_page < max_pages - 1 else UITheme.TEXT_MUTED
                    ),
                    (next_btn.x + 8, next_btn.y + 4),
                )

            start_y = 108
            card_w = r_rect.width - 20
            card_h = 92
            page_drivers = market_drivers[
                self.market_page * drivers_per_page : (self.market_page + 1) * drivers_per_page
            ]

            for idx, d in enumerate(page_drivers):
                cy = start_y + idx * (card_h + 8)
                card_rect = pygame.Rect(r_rect.x + 10, cy, card_w, card_h)

                d_type = d.get("driver_type", "STANDARD")
                border_col = (
                    (0, 240, 140)
                    if d_type == "PAY_DRIVER"
                    else ((255, 140, 0) if d_type == "SPONSORED_DRIVER" else (45, 65, 85))
                )

                pygame.draw.rect(surface, (18, 24, 32), card_rect, border_radius=3)
                pygame.draw.rect(surface, border_col, card_rect, width=1, border_radius=3)

                # Archetype Badge & Name
                if d_type == "PAY_DRIVER":
                    arch_tag = f"[PAY-DRIVER: Brings Free Title Sponsor '{d.get('pay_driver_sponsor_name', '')}']"
                    arch_col = (0, 240, 140)
                    finance_txt = f"Sponsor Payout: +${d.get('sponsor_income_per_race', 0.0):,.0f}/race (Free 2x-3x Title Deal) | Salary: $0"
                elif d_type == "SPONSORED_DRIVER":
                    arch_tag = (
                        f"[SPONSORED LOAN: {d.get('parent_team_name', '')} ({d.get('parent_team_expected_pos', '')})]"
                    )
                    arch_col = (255, 140, 0)
                    finance_txt = f"Loan Stipend: +${d.get('sponsor_income_per_race', 0.0):,.0f}/race (Parent Constructor Pays) | 1-Year Fast Growth"
                else:
                    arch_tag = f"[STANDARD PRO: Prefers {d.get('contract_preference', 'BALANCED')}]"
                    arch_col = (0, 220, 255)
                    finance_txt = f"Expected Salary: ${d.get('expected_salary_race', 25000.0):,.0f}/race | Bonus: ${d.get('expected_signing_bonus', 80000.0):,.0f} | Role: {d.get('expected_role', 'EQUAL')}"

                surface.blit(
                    self.font_card_title.render(
                        f"{d['name']} ({d['age']}yo | {d['nationality']}) — Pot: {d['potential']}", True, (255, 215, 0)
                    ),
                    (card_rect.x + 10, card_rect.y + 8),
                )
                surface.blit(self.font_badge.render(arch_tag, True, arch_col), (card_rect.x + 280, card_rect.y + 8))

                st_x = card_rect.x + 10
                st_y = card_rect.y + 32
                gap = 10
                st_x += (
                    UITheme.draw_stat_item(
                        surface,
                        st_x,
                        st_y,
                        "zap",
                        f"Pace: {d['pace']}",
                        self.font_body,
                        UITheme.TEXT_WHITE,
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
                        "disc",
                        f"Braking: {d['braking']}",
                        self.font_body,
                        UITheme.TEXT_WHITE,
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
                        "flag",
                        f"Starts: {d['race_starts']}",
                        self.font_body,
                        UITheme.TEXT_WHITE,
                        (200, 215, 230),
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
                        "layers",
                        f"Tires: {d['tire_management']}",
                        self.font_body,
                        UITheme.TEXT_WHITE,
                        (255, 170, 50),
                        icon_size=12,
                        gap=3,
                    )
                    + gap
                )
                UITheme.draw_stat_item(
                    surface,
                    st_x,
                    st_y,
                    "shield",
                    f"Defending: {d['defending']}",
                    self.font_body,
                    UITheme.TEXT_WHITE,
                    (100, 200, 255),
                    icon_size=12,
                    gap=3,
                )
                surface.blit(
                    self.font_badge.render(finance_txt, True, (200, 220, 240)), (card_rect.x + 10, card_rect.y + 54)
                )

                # Dossier Button
                btn_dos = pygame.Rect(card_rect.x + card_w - 110, cy + 3, 100, 18)
                UITheme.draw_button(surface, btn_dos, "DOSSIER", self.font_badge, icon="user", icon_size=10)

                # Negotiate Contract Button
                btn_neg = pygame.Rect(card_rect.x + card_w - 170, cy + 24, 160, 42)
                pygame.draw.rect(surface, (0, 160, 100), btn_neg, border_radius=3)
                neg_lbl = self.font_btn.render("NEGOTIATE CONTRACT >>", True, (10, 25, 20))
                surface.blit(neg_lbl, (btn_neg.x + (btn_neg.width - neg_lbl.get_width()) // 2, btn_neg.y + 13))

        # =====================================================================
        # 4. Interactive Contract Negotiation Modal (Render Overlay)
        # =====================================================================
        if self.show_negotiation_modal and self.negotiating_driver:
            self._render_negotiation_modal(surface, gm, dm, team_tier)

        # Bottom Status Message Bar
        stat_bar = pygame.Rect(24, self.height - 36, self.width - 48, 26)
        pygame.draw.rect(surface, (16, 20, 26), stat_bar, border_radius=3)
        msg_surf = self.font_body.render(self.status_message, True, UITheme.TEXT_WHITE)
        surface.blit(msg_surf, (stat_bar.x + 10, stat_bar.y + 6))

    def _render_negotiation_modal(self, surface: pygame.Surface, gm: GameManager, dm: DriverManager, team_tier: int):
        """Renders the comprehensive contract negotiation modal dialog."""

        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        modal_rect = pygame.Rect(self.width // 2 - 340, self.height // 2 - 250, 680, 500)
        pygame.draw.rect(surface, (14, 18, 26), modal_rect, border_radius=6)
        pygame.draw.rect(surface, (0, 220, 255), modal_rect, width=2, border_radius=6)

        # Header Bar
        hdr_rect = pygame.Rect(modal_rect.x, modal_rect.y, modal_rect.width, 42)
        pygame.draw.rect(surface, (22, 32, 48), hdr_rect, border_top_left_radius=6, border_top_right_radius=6)

        d = self.negotiating_driver
        d_type = d.get("driver_type", "STANDARD")
        title_txt = f"CONTRACT NEGOTIATIONS: {d['name']} ({d['age']}yo | Pot: {d['potential']})"
        surface.blit(
            self.font_modal_title.render(title_txt, True, (255, 215, 0)), (modal_rect.x + 16, modal_rect.y + 10)
        )

        # Close X Button
        btn_close = pygame.Rect(modal_rect.x + modal_rect.width - 36, modal_rect.y + 10, 26, 26)
        pygame.draw.rect(surface, (140, 40, 40), btn_close, border_radius=3)
        surface.blit(self.font_btn.render("X", True, (255, 255, 255)), (btn_close.x + 8, btn_close.y + 4))

        # Patience Hearts Indicator
        p_hearts = "❤️ " * self.negotiation_patience
        if self.negotiation_patience == 0:
            p_hearts = "💔 (EXHAUSTED)"
        surface.blit(
            self.font_btn.render(
                f"Driver Patience: {p_hearts} ({self.negotiation_patience} offers left)", True, (255, 90, 90)
            ),
            (modal_rect.x + 20, modal_rect.y + 52),
        )

        # Special Badges (Homegrown loyalty, Pay-driver sponsor, Sponsored loan)
        if self.negotiation_is_homegrown:
            loyalty_pct = int((0.80 - min(6, self.negotiation_main_seasons) * 0.16) * 100)
            hg_txt = f"⭐ HOMEGROWN ACADEMY STAR: -{loyalty_pct}% Loyalty Wage Discount (Year {self.negotiation_main_seasons + 1} in Main Team)"
            surface.blit(self.font_badge.render(hg_txt, True, (0, 240, 140)), (modal_rect.x + 20, modal_rect.y + 74))
        elif d_type == "PAY_DRIVER":
            pd_txt = f"💰 PAY-DRIVER TITLE DEAL: Brings '{d.get('pay_driver_sponsor_name', '')}' paying +${d.get('sponsor_income_per_race', 0.0):,.0f}/race!"
            surface.blit(self.font_badge.render(pd_txt, True, (0, 240, 140)), (modal_rect.x + 20, modal_rect.y + 74))
        elif d_type == "SPONSORED_DRIVER":
            sp_txt = f"🏎️ LOANED TALENT: From {d.get('parent_team_name', '')} ({d.get('parent_team_expected_pos', '')}) paying +${d.get('sponsor_income_per_race', 0.0):,.0f}/race stipend"
            surface.blit(self.font_badge.render(sp_txt, True, (255, 140, 0)), (modal_rect.x + 20, modal_rect.y + 74))

        # Row 1: Target Car Slot (Car #1 vs Car #2)
        surface.blit(
            self.font_btn.render("Assign Seat:", True, UITheme.TEXT_WHITE), (modal_rect.x + 20, modal_rect.y + 118)
        )
        for c_idx in [1, 2]:
            c_btn = pygame.Rect(modal_rect.x + 140 + (c_idx - 1) * 90, modal_rect.y + 115, 80, 24)
            is_c_sel = self.negotiation_car_slot == c_idx
            pygame.draw.rect(surface, (0, 180, 120) if is_c_sel else (25, 35, 45), c_btn, border_radius=3)
            c_lbl = self.font_btn.render(f"Car #{c_idx}", True, (10, 25, 20) if is_c_sel else UITheme.TEXT_WHITE)
            surface.blit(c_lbl, (c_btn.x + (c_btn.width - c_lbl.get_width()) // 2, c_btn.y + 4))

        primary_drivers = dm.get_primary_drivers(gm.team_id)
        target_idx = self.negotiation_car_slot - 1
        displaced = primary_drivers[target_idx] if target_idx < len(primary_drivers) else None
        buyout_fee = dm.get_driver_buyout_cost(displaced) if displaced else 0.0
        disp_name = displaced["name"] if displaced else "Empty"
        if buyout_fee > 0:
            disp_txt = f"Replaces {disp_name} (Severance: ${buyout_fee:,.0f})"
            disp_col = (255, 160, 40)
        else:
            disp_txt = f"Replaces {disp_name} ($0 Disband / Free)"
            disp_col = (0, 240, 140)
        surface.blit(self.font_badge.render(disp_txt, True, disp_col), (modal_rect.x + 330, modal_rect.y + 118))

        # Row 2: Contract Seasons (1 to 5)
        surface.blit(
            self.font_btn.render("Contract Length:", True, UITheme.TEXT_WHITE), (modal_rect.x + 20, modal_rect.y + 158)
        )
        if d_type == "SPONSORED_DRIVER":
            surface.blit(
                self.font_btn.render("1 Season (Fixed Loan)", True, (255, 140, 0)),
                (modal_rect.x + 140, modal_rect.y + 158),
            )
        else:
            btn_s_dec = pygame.Rect(modal_rect.x + 140, modal_rect.y + 155, 30, 24)
            btn_s_inc = pygame.Rect(modal_rect.x + 230, modal_rect.y + 155, 30, 24)
            pygame.draw.rect(surface, (35, 50, 70), btn_s_dec, border_radius=3)
            pygame.draw.rect(surface, (35, 50, 70), btn_s_inc, border_radius=3)
            surface.blit(self.font_btn.render("-", True, UITheme.TEXT_WHITE), (btn_s_dec.x + 10, btn_s_dec.y + 3))
            surface.blit(self.font_btn.render("+", True, UITheme.TEXT_WHITE), (btn_s_inc.x + 10, btn_s_inc.y + 3))
            surface.blit(
                self.font_btn.render(f"{self.offer_seasons} Season(s)", True, (255, 215, 0)),
                (modal_rect.x + 175, modal_rect.y + 158),
            )

        # Row 3: Salary Per Race
        surface.blit(
            self.font_btn.render("Salary Per Race:", True, UITheme.TEXT_WHITE), (modal_rect.x + 20, modal_rect.y + 198)
        )
        if d_type in ["PAY_DRIVER", "SPONSORED_DRIVER"]:
            surface.blit(
                self.font_btn.render("$0 / race (Covered by Sponsor/Parent)", True, (0, 240, 140)),
                (modal_rect.x + 140, modal_rect.y + 198),
            )
        else:
            btn_sal_dec = pygame.Rect(modal_rect.x + 140, modal_rect.y + 195, 30, 24)
            btn_sal_inc = pygame.Rect(modal_rect.x + 270, modal_rect.y + 195, 30, 24)
            pygame.draw.rect(surface, (35, 50, 70), btn_sal_dec, border_radius=3)
            pygame.draw.rect(surface, (35, 50, 70), btn_sal_inc, border_radius=3)
            surface.blit(self.font_btn.render("-", True, UITheme.TEXT_WHITE), (btn_sal_dec.x + 10, btn_sal_dec.y + 3))
            surface.blit(self.font_btn.render("+", True, UITheme.TEXT_WHITE), (btn_sal_inc.x + 10, btn_sal_inc.y + 3))
            surface.blit(
                self.font_btn.render(f"${self.offer_salary:,.0f} / race", True, (255, 215, 0)),
                (modal_rect.x + 175, modal_rect.y + 198),
            )

        # Row 4: Signing Bonus
        surface.blit(
            self.font_btn.render("Signing Bonus:", True, UITheme.TEXT_WHITE), (modal_rect.x + 20, modal_rect.y + 238)
        )
        if d_type in ["PAY_DRIVER", "SPONSORED_DRIVER"]:
            surface.blit(
                self.font_btn.render("$0 Upfront", True, (0, 240, 140)), (modal_rect.x + 140, modal_rect.y + 238)
            )
        else:
            btn_bon_dec = pygame.Rect(modal_rect.x + 140, modal_rect.y + 235, 30, 24)
            btn_bon_inc = pygame.Rect(modal_rect.x + 270, modal_rect.y + 235, 30, 24)
            pygame.draw.rect(surface, (35, 50, 70), btn_bon_dec, border_radius=3)
            pygame.draw.rect(surface, (35, 50, 70), btn_bon_inc, border_radius=3)
            surface.blit(self.font_btn.render("-", True, UITheme.TEXT_WHITE), (btn_bon_dec.x + 10, btn_bon_dec.y + 3))
            surface.blit(self.font_btn.render("+", True, UITheme.TEXT_WHITE), (btn_bon_inc.x + 10, btn_bon_inc.y + 3))
            surface.blit(
                self.font_btn.render(f"${self.offer_bonus:,.0f}", True, (255, 215, 0)),
                (modal_rect.x + 175, modal_rect.y + 238),
            )

        # Row 5: Role Hierarchy (#1, EQUAL, #2)
        surface.blit(
            self.font_btn.render("Driver Role:", True, UITheme.TEXT_WHITE), (modal_rect.x + 20, modal_rect.y + 278)
        )
        roles = [("#1", "#1 Driver"), ("EQUAL", "Equal Status"), ("#2", "#2 Driver")]
        for r_idx, (r_val, r_lbl) in enumerate(roles):
            r_btn = pygame.Rect(modal_rect.x + 140 + r_idx * 85, modal_rect.y + 275, 80, 24)
            is_r_sel = self.offer_role == r_val
            pygame.draw.rect(surface, (0, 180, 120) if is_r_sel else (25, 35, 45), r_btn, border_radius=3)
            lbl = self.font_btn.render(r_lbl, True, (10, 25, 20) if is_r_sel else UITheme.TEXT_WHITE)
            surface.blit(lbl, (r_btn.x + (r_btn.width - lbl.get_width()) // 2, r_btn.y + 4))

        # Driver Reaction & Feedback Box
        fb_rect = pygame.Rect(modal_rect.x + 20, modal_rect.y + 320, modal_rect.width - 40, 95)
        fb_bg = (
            (20, 35, 25)
            if self.negotiation_accepted
            else ((35, 20, 20) if self.negotiation_walked_away else (18, 24, 32))
        )
        fb_border = (
            (0, 240, 140)
            if self.negotiation_accepted
            else ((255, 90, 90) if self.negotiation_walked_away else (45, 60, 80))
        )
        pygame.draw.rect(surface, fb_bg, fb_rect, border_radius=4)
        pygame.draw.rect(surface, fb_border, fb_rect, width=1, border_radius=4)

        surface.blit(
            self.font_badge.render("DRIVER REACTION & TELEMETRY RESPONSE:", True, (255, 215, 0)),
            (fb_rect.x + 10, fb_rect.y + 8),
        )
        surface.blit(
            self.font_body.render(f'"{self.negotiation_feedback}"', True, (240, 245, 250)),
            (fb_rect.x + 10, fb_rect.y + 28),
        )

        # Bottom Action Button
        btn_act = pygame.Rect(modal_rect.x + 20, modal_rect.y + 435, modal_rect.width - 40, 42)
        total_upfront = self.offer_bonus + buyout_fee
        if self.negotiation_walked_away:
            pygame.draw.rect(surface, (80, 30, 30), btn_act, border_radius=4)
            surface.blit(
                self.font_btn.render("NEGOTIATIONS FAILED (DRIVER WALKED AWAY) — CLICK TO EXIT", True, (255, 200, 200)),
                (btn_act.x + 80, btn_act.y + 14),
            )
        elif self.negotiation_accepted:
            pygame.draw.rect(surface, (0, 180, 100), btn_act, border_radius=4)
            upfront_str = f" (${total_upfront:,.0f} Total Upfront)" if total_upfront > 0 else ""
            act_txt = f"SEAL DEAL & SIGN CONTRACT (Car #{self.negotiation_car_slot}{upfront_str})"
            surface.blit(self.font_btn.render(act_txt, True, (10, 25, 20)), (btn_act.x + 60, btn_act.y + 14))
        else:
            pygame.draw.rect(surface, (35, 75, 120), btn_act, border_radius=4)
            surface.blit(
                self.font_btn.render("PROPOSE OFFER TO DRIVER >>", True, (255, 255, 255)),
                (btn_act.x + 210, btn_act.y + 14),
            )
