import pygame

from ...management.game_manager import GameManager
from ...management.sponsor_manager import SponsorManager
from ..theme import UITheme


class SponsorsTab:
    """Sponsors & Commercial Hub featuring 3-tier slots (2 Title, 4 Middle, 10 Minor) and incoming contract offers."""

    def __init__(self, screen_width: int, screen_height: int):
        self.width = screen_width
        self.height = screen_height

        self._init_fonts()
        self.status_message: str = "Review active sponsor partnerships or negotiate incoming commercial contracts."

    def _init_fonts(self):
        self.font_title = UITheme.get_font(13, bold=True)
        self.font_card_title = UITheme.get_font(12, bold=True)
        self.font_body = UITheme.get_font(11, bold=False)
        self.font_badge = UITheme.get_font(10, bold=True)
        self.font_btn = UITheme.get_font(11, bold=True)

    def resize(self, width: int, height: int):
        self.width = width
        self.height = height
        self._init_fonts()

    def handle_click(self, mx: int, my: int, gm: GameManager, sm: SponsorManager) -> bool:
        offers = sm.get_sponsor_offers(gm.team_id)

        # Check click on Sign Offer Buttons (Right Column)
        off_rect = pygame.Rect(560, 126, self.width - 584, self.height - 170)

        for idx, o in enumerate(offers[:4]):
            oy = 158 + idx * 88
            oc_box = pygame.Rect(off_rect.x + 10, oy, off_rect.width - 20, 80)
            sign_btn = pygame.Rect(oc_box.x + oc_box.width - 105, oc_box.y + 26, 95, 28)
            if sign_btn.collidepoint(mx, my):
                success, msg = sm.sign_sponsor_offer(gm.team_id, o["id"])
                if success:
                    gm.refresh_player_team()
                self.status_message = msg
                return True

        return False

    def render(self, surface: pygame.Surface, gm: GameManager, sm: SponsorManager):
        sm.check_and_generate_offers(gm.team_id, is_progression=False)
        appeal_data = sm.calculate_sponsor_appeal(gm.team_id)
        active = sm.get_active_sponsors(gm.team_id)
        offers = sm.get_sponsor_offers(gm.team_id)

        # 1. Sponsor Appeal Meter Banner (Top)
        app_rect = pygame.Rect(24, 70, self.width - 48, 48)
        pygame.draw.rect(surface, (16, 22, 30), app_rect, border_radius=4)
        pygame.draw.rect(surface, UITheme.PANEL_BORDER, app_rect, width=1, border_radius=4)

        # Title & Breakdown on Left
        surface.blit(
            self.font_card_title.render("GLOBAL SPONSOR APPEAL", True, (255, 215, 0)), (app_rect.x + 12, app_rect.y + 6)
        )
        breakdown_str = f"Tier: +{appeal_data['tier_pts']:.0f}pts  |  10-Race Form: +{appeal_data['form_pts']:.0f}pts  |  5-Season History: +{appeal_data['history_pts']:.0f}pts  |  Driver Marketability: +{appeal_data['driver_pts']:.0f}pts  |  Marketing HQ: +{appeal_data['facility_pts']:.0f}pts"
        surface.blit(self.font_body.render(breakdown_str, True, UITheme.TEXT_MUTED), (app_rect.x + 12, app_rect.y + 26))

        # Score & Visual Progress Bar on Top Right
        score_val = appeal_data["total_appeal"]
        score_txt = f"{score_val} / 100"
        score_surf = self.font_title.render(score_txt, True, (0, 240, 140))
        lbl_surf = self.font_badge.render("APPEAL SCORE:", True, (255, 215, 0))

        total_score_w = lbl_surf.get_width() + 8 + score_surf.get_width()
        right_x = app_rect.x + app_rect.width - 16 - total_score_w
        surface.blit(lbl_surf, (right_x, app_rect.y + 8))
        surface.blit(score_surf, (right_x + lbl_surf.get_width() + 8, app_rect.y + 6))

        bar_w = total_score_w
        bar_rect = pygame.Rect(right_x, app_rect.y + 28, bar_w, 8)
        pygame.draw.rect(surface, (10, 14, 20), bar_rect, border_radius=3)
        fill_pct = min(1.0, max(0.0, score_val / 100.0))
        if fill_pct > 0:
            fill_w = max(4, int(bar_w * fill_pct))
            fill_rect = pygame.Rect(right_x, app_rect.y + 28, fill_w, 8)
            pygame.draw.rect(surface, (0, 220, 140), fill_rect, border_radius=3)
        pygame.draw.rect(surface, (40, 50, 65), bar_rect, width=1, border_radius=3)

        # 2. Active Sponsor Slots (Left Column)
        act_rect = pygame.Rect(24, 126, 520, self.height - 170)
        UITheme.draw_panel(surface, act_rect)

        act_hdr = pygame.Rect(act_rect.x, act_rect.y, act_rect.width, 26)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, act_hdr, border_top_left_radius=4, border_top_right_radius=4)
        surface.blit(
            self.font_title.render("ACTIVE SPONSOR CONTRACTS (3 TIERS)", True, (0, 220, 255)),
            (act_rect.x + 12, act_rect.y + 5),
        )

        cur_y = 158

        # --- A. TITLE SPONSORS (2 Max) ---
        surface.blit(
            self.font_card_title.render("1. TITLE SPONSORS (2 Slots Max)", True, (255, 215, 0)),
            (act_rect.x + 10, cur_y),
        )
        cur_y += 20
        title_slots = active.get("TITLE", [])
        num_title_display = max(2, len(title_slots))
        for s_idx in range(num_title_display):
            s_box = pygame.Rect(act_rect.x + 10, cur_y, act_rect.width - 20, 52)
            if s_idx < len(title_slots):
                s = title_slots[s_idx]
                pygame.draw.rect(surface, (28, 36, 46), s_box, border_radius=3)

                is_pay_driver = s.get("is_pay_driver_sponsor", False)
                b_color = (0, 240, 140) if is_pay_driver else (255, 215, 0)
                pygame.draw.rect(surface, b_color, s_box, width=1, border_radius=3)

                col_rgb = pygame.Color(s.get("color_hex", "#00d2be"))
                pygame.draw.rect(surface, col_rgb, (s_box.x + 8, s_box.y + 8, 8, 36), border_radius=2)

                if is_pay_driver:
                    surface.blit(
                        self.font_card_title.render(f"{s['brand_name']}", True, (0, 240, 140)),
                        (s_box.x + 22, s_box.y + 7),
                    )
                    sub_txt = (
                        f"+${s['per_race_payment']:,.0f} / race  •  Free Title Sponsor ({s.get('driver_name', '')})"
                    )
                    surface.blit(self.font_body.render(sub_txt, True, UITheme.TEXT_WHITE), (s_box.x + 22, s_box.y + 27))
                    surface.blit(
                        self.font_badge.render(f"{s['races_remaining']}", True, (0, 240, 140)),
                        (s_box.x + s_box.width - 110, s_box.y + 8),
                    )
                else:
                    surface.blit(
                        self.font_card_title.render(s["brand_name"], True, UITheme.TEXT_WHITE),
                        (s_box.x + 22, s_box.y + 7),
                    )
                    t_str = (
                        f"Target: Top P{s['target_position']} (+${s['target_bonus']:,.0f})"
                        if s["target_position"]
                        else "Standard Partnership"
                    )
                    surface.blit(
                        self.font_body.render(f"+${s['per_race_payment']:,.0f} / race | {t_str}", True, (0, 240, 140)),
                        (s_box.x + 22, s_box.y + 27),
                    )
                    r_rem = (
                        f"{s['races_remaining']} RACES LEFT"
                        if isinstance(s["races_remaining"], int)
                        else str(s["races_remaining"])
                    )
                    surface.blit(
                        self.font_badge.render(r_rem, True, UITheme.TEXT_MUTED),
                        (s_box.x + s_box.width - 110, s_box.y + 8),
                    )
            else:
                pygame.draw.rect(surface, (16, 20, 26), s_box, border_radius=3)
                pygame.draw.rect(surface, (45, 55, 65), s_box, width=1, border_radius=3)
                surface.blit(
                    self.font_body.render(
                        f"[ EMPTY TITLE SLOT #{s_idx + 1} - AWAITING OFFER ]", True, UITheme.TEXT_MUTED
                    ),
                    (s_box.x + 14, s_box.y + 18),
                )
            cur_y += 58

        # --- B. MIDDLE SPONSORS (4 Max) ---
        surface.blit(
            self.font_card_title.render("2. SECONDARY SPONSORS (4 Slots Max)", True, (0, 200, 255)),
            (act_rect.x + 10, cur_y),
        )
        cur_y += 20
        mid_slots = active.get("MIDDLE", [])
        for s_idx in range(4):
            s_box = pygame.Rect(act_rect.x + 10, cur_y, act_rect.width - 20, 42)
            if s_idx < len(mid_slots):
                s = mid_slots[s_idx]
                pygame.draw.rect(surface, (20, 28, 36), s_box, border_radius=3)
                pygame.draw.rect(surface, (0, 180, 220), s_box, width=1, border_radius=3)
                surface.blit(
                    self.font_card_title.render(s["brand_name"], True, UITheme.TEXT_WHITE), (s_box.x + 10, s_box.y + 6)
                )
                surface.blit(
                    self.font_body.render(f"+${s['per_race_payment']:,.0f} / race", True, (0, 240, 140)),
                    (s_box.x + 10, s_box.y + 24),
                )
                surface.blit(
                    self.font_badge.render(f"{s['races_remaining']} RACES LEFT", True, UITheme.TEXT_MUTED),
                    (s_box.x + s_box.width - 100, s_box.y + 6),
                )
            else:
                pygame.draw.rect(surface, (14, 18, 22), s_box, border_radius=3)
                pygame.draw.rect(surface, (35, 45, 55), s_box, width=1, border_radius=3)
                surface.blit(
                    self.font_body.render(f"[ Empty Secondary Slot #{s_idx + 1} ]", True, (80, 95, 110)),
                    (s_box.x + 10, s_box.y + 14),
                )
            cur_y += 46

        # --- C. MINOR & ACADEMY PARTNERS (10 Max) ---
        minor_slots = active.get("MINOR", [])
        surface.blit(
            self.font_card_title.render(
                f"3. MINOR & ACADEMY PARTNERS ({len(minor_slots)}/10 Active)", True, UITheme.TEXT_WHITE
            ),
            (act_rect.x + 10, cur_y),
        )
        cur_y += 18
        min_box = pygame.Rect(act_rect.x + 10, cur_y, act_rect.width - 20, 56)
        pygame.draw.rect(surface, (16, 20, 26), min_box, border_radius=3)
        pygame.draw.rect(surface, UITheme.PANEL_BORDER, min_box, width=1, border_radius=3)

        if minor_slots:
            m_items = []
            for m in minor_slots[:5]:
                if m.get("is_sponsored_loan"):
                    m_items.append(
                        f"{m['brand_name']} (+${m['per_race_payment'] / 1000:.0f}k [Loan: {m.get('driver_name', '')}])"
                    )
                else:
                    m_items.append(f"{m['brand_name']} (+${m['per_race_payment'] / 1000:.0f}k)")
            m_txt = " • ".join(m_items)
            surface.blit(self.font_badge.render(m_txt, True, (0, 220, 255)), (min_box.x + 8, min_box.y + 8))

            if len(minor_slots) > 5:
                m_items2 = []
                for m in minor_slots[5:10]:
                    if m.get("is_sponsored_loan"):
                        m_items2.append(
                            f"{m['brand_name']} (+${m['per_race_payment'] / 1000:.0f}k [Loan: {m.get('driver_name', '')}])"
                        )
                    else:
                        m_items2.append(f"{m['brand_name']} (+${m['per_race_payment'] / 1000:.0f}k)")
                m_txt2 = " • ".join(m_items2)
                surface.blit(self.font_badge.render(m_txt2, True, (0, 220, 255)), (min_box.x + 8, min_box.y + 28))
        else:
            surface.blit(
                self.font_body.render(
                    "No minor suppliers or youth academy loans currently active.", True, UITheme.TEXT_MUTED
                ),
                (min_box.x + 10, min_box.y + 18),
            )

        # 3. Incoming Sponsor Offers Portal (Right Column)

        off_rect = pygame.Rect(560, 126, self.width - 584, self.height - 170)
        UITheme.draw_panel(surface, off_rect)

        off_hdr = pygame.Rect(off_rect.x, off_rect.y, off_rect.width, 26)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, off_hdr, border_top_left_radius=4, border_top_right_radius=4)
        surface.blit(
            self.font_title.render(f"INCOMING SPONSOR OFFERS ({len(offers)} Available)", True, (255, 180, 40)),
            (off_rect.x + 12, off_rect.y + 5),
        )

        for idx, o in enumerate(offers[:4]):
            oy = 158 + idx * 88
            oc_box = pygame.Rect(off_rect.x + 10, oy, off_rect.width - 20, 80)
            pygame.draw.rect(surface, (20, 26, 34), oc_box, border_radius=3)
            pygame.draw.rect(surface, UITheme.PANEL_BORDER, oc_box, width=1, border_radius=3)

            tier_col = (
                (255, 215, 0)
                if o["slot_tier"] == "TITLE"
                else ((0, 200, 255) if o["slot_tier"] == "MIDDLE" else UITheme.TEXT_WHITE)
            )
            surface.blit(
                self.font_card_title.render(f"{o['brand_name']} [{o['slot_tier']}]", True, tier_col),
                (oc_box.x + 10, oc_box.y + 8),
            )
            surface.blit(
                self.font_body.render(
                    f"Signing Bonus: +${o['signing_bonus']:,.0f} (Instant Cash) | Contract: {o['races_total']} Races",
                    True,
                    (0, 240, 140),
                ),
                (oc_box.x + 10, oc_box.y + 28),
            )

            t_str = (
                f"Target: P{o['target_position']} (+${o['target_bonus']:,.0f}/race)"
                if o["target_position"]
                else "Fixed Payout"
            )
            surface.blit(
                self.font_body.render(
                    f"Payment: ${o['per_race_payment']:,.0f} / race | {t_str}", True, UITheme.TEXT_WHITE
                ),
                (oc_box.x + 10, oc_box.y + 48),
            )

            # Sign Offer Button
            sign_btn = pygame.Rect(oc_box.x + oc_box.width - 105, oc_box.y + 26, 95, 28)
            pygame.draw.rect(surface, (0, 180, 100), sign_btn, border_radius=3)
            s_txt = self.font_btn.render("SIGN DEAL", True, (10, 20, 15))
            surface.blit(s_txt, (sign_btn.x + (sign_btn.width - s_txt.get_width()) // 2, sign_btn.y + 6))

        # Bottom Status Bar
        stat_bar = pygame.Rect(24, self.height - 36, self.width - 48, 26)
        pygame.draw.rect(surface, (16, 20, 26), stat_bar, border_radius=3)
        msg_surf = self.font_body.render(self.status_message, True, UITheme.TEXT_WHITE)
        surface.blit(msg_surf, (stat_bar.x + 10, stat_bar.y + 6))
