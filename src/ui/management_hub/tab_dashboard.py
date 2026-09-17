import json
import os
from typing import Any, Callable, Dict, List, Optional, Tuple

import pygame

from ...management.game_manager import GameManager
from ...management.innovation_manager import InnovationManager
from ..icons import UIIcons
from ..theme import UITheme


class DashboardTab:
    """
    Home Dashboard Tab providing:
    - Pre-Race Readiness Dashboard & 4-Point Systems Checklist with 1-Click Spare Auto-Mounting.
    - Vector Track Mini-Map with Sector 1/2/3 splits and characteristic track demand gauges.
    - Active Sponsor Targets & Financial Projection Cards.
    - R&D Innovation Proposal Pipeline & Priority Alert Queue.
    """

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        on_start_race: Callable[[], None],
        on_advance_week: Optional[Callable[[], None]] = None,
        on_open_roundup: Optional[Callable[[], None]] = None,
    ):
        self.width = screen_width
        self.height = screen_height
        self.on_start_race = on_start_race
        self.on_advance_week = on_advance_week
        self.on_open_roundup = on_open_roundup

        self._track_cache: Dict[str, List[Tuple[float, float]]] = {}
        self.resolve_btn_rect: Optional[pygame.Rect] = None

        self._init_fonts()
        self.action_message: str = "Pre-race systems nominal. Ready for Grand Prix weekend."

    def _init_fonts(self):
        self.font_title = UITheme.get_font(13, bold=True)
        self.font_card_title = UITheme.get_font(12, bold=True)
        self.font_body = UITheme.get_font(11, bold=False)
        self.font_badge = UITheme.get_font(10, bold=True)
        self.font_race_btn = UITheme.get_font(13, bold=True)
        self.font_mini = UITheme.get_font(9, bold=True)

    def resize(self, width: int, height: int):
        self.width = width
        self.height = height
        self._init_fonts()

    def _load_track_points(self, circuit_file: str) -> List[Tuple[float, float]]:
        """Loads and caches control points from track JSON for vector radar rendering."""
        if circuit_file in self._track_cache:
            return self._track_cache[circuit_file]

        path = os.path.join("tracks", circuit_file)
        pts: List[Tuple[float, float]] = []
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    pts = [tuple(p) for p in data.get("control_points", [])]
            except Exception:
                pts = []

        if len(pts) < 3:
            # Elegant procedural circuit loop fallback
            pts = [
                (-320.0, -200.0),
                (-120.0, -230.0),
                (100.0, -220.0),
                (320.0, -180.0),
                (420.0, -60.0),
                (360.0, 70.0),
                (200.0, 130.0),
                (40.0, 90.0),
                (-90.0, 170.0),
                (-260.0, 150.0),
                (-380.0, 40.0),
                (-400.0, -90.0),
            ]
        self._track_cache[circuit_file] = pts
        return pts

    def _truncate_text(self, font: pygame.font.Font, text: str, max_w: int) -> str:
        """Safely truncates text to fit within max_w pixels with an ellipsis, preventing card spill."""
        if max_w <= 10:
            return ""
        if font.size(text)[0] <= max_w:
            return text
        ellipsis = "..."
        while text and font.size(text + ellipsis)[0] > max_w:
            text = text[:-1]
        return text.strip() + ellipsis if text else ellipsis

    def get_pipeline_layout(
        self, active_pitches: List[Dict[str, Any]], pending_pitches: List[Dict[str, Any]]
    ) -> Tuple[Optional[pygame.Rect], List[Tuple[pygame.Rect, pygame.Rect, pygame.Rect]]]:
        """Calculates precise, non-overlapping rectangles for active project and pending proposals."""
        pipe_x = 24
        top_h = 215
        pipe_y = 70 + top_h + 12
        pipe_w = min(540, (self.width - 64) // 2)

        cur_y = pipe_y + 34
        act_rect = None
        if active_pitches:
            act_rect = pygame.Rect(pipe_x + 10, cur_y, pipe_w - 20, 52)
            cur_y += 58

        card_h = 96 if active_pitches else 108
        cards = []
        for idx in range(min(2, len(pending_pitches))):
            cy = cur_y + idx * (card_h + 8)
            c_rect = pygame.Rect(pipe_x + 10, cy, pipe_w - 20, card_h)
            greenlight_btn = pygame.Rect(c_rect.x + c_rect.width - 165, c_rect.y + c_rect.height - 24, 98, 20)
            discard_btn = pygame.Rect(c_rect.x + c_rect.width - 60, c_rect.y + c_rect.height - 24, 54, 20)
            cards.append((c_rect, greenlight_btn, discard_btn))

        return act_rect, cards

    def _resolve_parts_wear(self, gm: GameManager) -> str:
        """
        Auto-mounts best available warehouse spares with >= 80% reliability,
        or performs quick factory maintenance on worn components.
        """
        try:
            with gm.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT id, car_slot, category, reliability FROM car_components "
                    "WHERE team_id = ? AND car_slot IN (1, 2) AND reliability < 80.0;",
                    (gm.team_id,),
                )
                worn_parts = [dict(r) for r in cur.fetchall()]
                if not worn_parts:
                    return "All mounted components already at optimal reliability (>= 80%)."

                resolved = 0
                for wp in worn_parts:
                    cur.execute(
                        "SELECT id, reliability FROM car_components "
                        "WHERE team_id = ? AND category = ? AND car_slot = 0 AND reliability >= 80.0 "
                        "ORDER BY reliability DESC LIMIT 1;",
                        (gm.team_id, wp["category"]),
                    )
                    spare = cur.fetchone()
                    if spare:
                        # Unmount current worn part, mount spare
                        cur.execute("UPDATE car_components SET car_slot = 0 WHERE id = ?;", (wp["id"],))
                        cur.execute("UPDATE car_components SET car_slot = ? WHERE id = ?;", (wp["car_slot"], spare[0]))
                        resolved += 1
                    else:
                        # Factory quick overhaul to 95%
                        cur.execute(
                            "UPDATE car_components SET reliability = 95.0, wear_pct = 5.0 WHERE id = ?;", (wp["id"],)
                        )
                        resolved += 1

                conn.commit()
                return f"Checklist Resolved: Serviced & mounted optimal spares for {resolved} component(s)."
        except Exception as e:
            return f"Error resolving parts wear: {e}"

    def handle_click(self, mx: int, my: int, gm: GameManager, im: InnovationManager) -> bool:
        # 1. Main Action Button: Start Race Weekend OR Advance Week
        race_btn_rect = pygame.Rect(self.width - 320, self.height - 65, 300, 48)
        if race_btn_rect.collidepoint(mx, my):
            if gm.is_race_week_for_player():
                self.on_start_race()
            else:
                if self.on_advance_week:
                    self.on_advance_week()
            return True

        # View Weekly Roundup Button
        roundup_btn_rect = pygame.Rect(self.width - 530, self.height - 65, 195, 48)
        if roundup_btn_rect.collidepoint(mx, my) and self.on_open_roundup:
            self.on_open_roundup()
            return True

        # 2. 1-Click Pre-Race Auto-Resolve Wear Button
        if self.resolve_btn_rect and self.resolve_btn_rect.collidepoint(mx, my):
            msg = self._resolve_parts_wear(gm)
            self.action_message = msg
            return True

        # 3. Innovation Pitches Actions
        active_pitches = im.get_team_pitches(gm.team_id, status="ACTIVE")
        pending_pitches = im.get_team_pitches(gm.team_id, status="PENDING")
        _, cards = self.get_pipeline_layout(active_pitches, pending_pitches)

        for idx, (_, greenlight_btn, discard_btn) in enumerate(cards):
            if idx >= len(pending_pitches):
                break
            p = pending_pitches[idx]

            if greenlight_btn.collidepoint(mx, my):
                success, msg = im.greenlight_pitch(gm.team_id, p["id"])
                self.action_message = msg
                return True
            elif discard_btn.collidepoint(mx, my):
                with im.db.get_connection() as conn:
                    conn.cursor().execute(
                        "UPDATE innovation_pitches SET status = 'DISCARDED' WHERE id = ?;", (p["id"],)
                    )
                    conn.commit()
                self.action_message = f"Discarded proposal: {p['title']}"
                return True

        return False

    def _render_vector_circuit(self, surface: pygame.Surface, rect: pygame.Rect, circuit_file: str, total_laps: int):
        """Draws the vector track radar wireframe with colored sectors S1 (Yellow), S2 (Cyan), S3 (Purple)."""
        pygame.draw.rect(surface, (16, 20, 26), rect, border_radius=4)
        pygame.draw.rect(surface, (32, 40, 52), rect, width=1, border_radius=4)

        pts = self._load_track_points(circuit_file)
        if len(pts) < 3:
            return

        # Fit points inside inner box with padding
        pad = 14
        view_w = max(10, rect.width - pad * 2)
        view_h = max(10, rect.height - pad * 2)

        min_x = min(p[0] for p in pts)
        max_x = max(p[0] for p in pts)
        min_y = min(p[1] for p in pts)
        max_y = max(p[1] for p in pts)

        bb_w = max(1.0, max_x - min_x)
        bb_h = max(1.0, max_y - min_y)
        scale = min(view_w / bb_w, view_h / bb_h) * 0.92

        mid_x = (min_x + max_x) / 2.0
        mid_y = (min_y + max_y) / 2.0
        cx = rect.x + rect.width / 2.0
        cy = rect.y + rect.height / 2.0

        screen_pts = [(int(cx + (px - mid_x) * scale), int(cy + (py - mid_y) * scale)) for px, py in pts]

        # Draw glow underlay
        if len(screen_pts) > 2:
            pygame.draw.lines(surface, (25, 35, 48), True, screen_pts, width=5)

        # Draw 3-Sector colored segments
        n_pts = len(screen_pts)
        s1_end = int(n_pts * 0.35)
        s2_end = int(n_pts * 0.70)

        s1_pts = screen_pts[0 : s1_end + 1]
        s2_pts = screen_pts[s1_end : s2_end + 1]
        s3_pts = screen_pts[s2_end:] + [screen_pts[0]]

        if len(s1_pts) > 1:
            pygame.draw.lines(surface, (255, 205, 30), False, s1_pts, width=2)
        if len(s2_pts) > 1:
            pygame.draw.lines(surface, (0, 220, 240), False, s2_pts, width=2)
        if len(s3_pts) > 1:
            pygame.draw.lines(surface, (190, 85, 255), False, s3_pts, width=2)

        # Start / Finish line pip
        sf_pt = screen_pts[0]
        pygame.draw.circle(surface, (255, 255, 255), sf_pt, 4)
        pygame.draw.circle(surface, (0, 240, 140), sf_pt, 2)

        # Sector Legend overlay at bottom of circuit mini-map
        leg_y = rect.bottom - 18
        surface.blit(self.font_mini.render("S1", True, (255, 205, 30)), (rect.x + 8, leg_y))
        surface.blit(self.font_mini.render("S2", True, (0, 220, 240)), (rect.x + 28, leg_y))
        surface.blit(self.font_mini.render("S3", True, (190, 85, 255)), (rect.x + 48, leg_y))
        lap_surf = self.font_mini.render(f"{total_laps} LAPS", True, UITheme.TEXT_MUTED)
        surface.blit(lap_surf, (rect.right - 8 - lap_surf.get_width(), leg_y))

    def _render_track_demands(
        self, surface: pygame.Surface, rect: pygame.Rect, characteristic: str, weather_profile: str
    ):
        """Draws visual track demand meters (Speed, Aero, Braking) and weather condition badge."""
        demands = {
            "SPEED": (90, 50, 65, "Straight-Line Top Speed & Low Drag"),
            "BRAKES": (60, 70, 95, "Heavy Braking & High Decel Stability"),
            "AERO": (65, 95, 70, "High-Speed Aero Downforce & Corner Grip"),
            "BALANCED": (75, 75, 75, "Balanced Chassis Equilibrium & Roll"),
        }
        spd_pct, aero_pct, brk_pct, desc = demands.get(characteristic, demands["BALANCED"])

        # Weather Forecast Badge
        is_wet = "WET" in weather_profile or "RAIN" in weather_profile
        w_col = (60, 160, 240) if is_wet else (255, 205, 30)
        w_ic = "cloud-rain" if is_wet else "sun"
        w_desc = "RAIN RISK: 85% • AIR 18°C" if is_wet else "DRY RUNNING • AIR 24°C"

        w_badge = pygame.Rect(rect.x, rect.y, rect.width, 22)
        pygame.draw.rect(surface, (20, 26, 34), w_badge, border_radius=3)
        pygame.draw.rect(surface, (40, 50, 65), w_badge, width=1, border_radius=3)
        UITheme.draw_icon(surface, w_ic, (w_badge.x + 6, w_badge.y + 4), color=w_col, size=13)
        surface.blit(
            self.font_badge.render(f"FORECAST: {weather_profile} ({w_desc})", True, w_col),
            (w_badge.x + 24, w_badge.y + 3),
        )

        # 3 Demand Horizontal Meters
        bar_w = rect.width - 110
        meters = [
            ("SPEED DEMAND", spd_pct, (255, 120, 80), "gauge"),
            ("AERO DOWNFORCE", aero_pct, (80, 220, 255), "layers"),
            ("BRAKING DEMAND", brk_pct, (255, 210, 60), "disc"),
        ]

        for idx, (m_lbl, m_val, m_col, m_icon) in enumerate(meters):
            my = rect.y + 30 + idx * 24
            UITheme.draw_icon(surface, m_icon, (rect.x, my + 1), color=m_col, size=12)
            surface.blit(self.font_mini.render(m_lbl, True, UITheme.TEXT_MUTED), (rect.x + 16, my + 1))

            b_rect = pygame.Rect(rect.right - bar_w, my + 2, bar_w, 10)
            pygame.draw.rect(surface, (18, 22, 30), b_rect, border_radius=2)
            fill_w = int(bar_w * (m_val / 100.0))
            if fill_w > 0:
                pygame.draw.rect(surface, m_col, pygame.Rect(b_rect.x, b_rect.y, fill_w, 10), border_radius=2)
            pygame.draw.rect(surface, (40, 48, 60), b_rect, width=1, border_radius=2)

            val_s = self.font_mini.render(f"{m_val}%", True, UITheme.TEXT_WHITE)
            surface.blit(val_s, (b_rect.x + 4, b_rect.y - 1))

        # Demand characteristic tagline
        tag_y = rect.y + 104
        tag_rect = pygame.Rect(rect.x, tag_y, rect.width, 20)
        pygame.draw.rect(surface, (18, 24, 32), tag_rect, border_radius=2)
        surface.blit(
            self.font_badge.render(f"SETUP FOCUS: {desc.upper()}", True, (0, 240, 140)),
            (tag_rect.x + 6, tag_rect.y + 2),
        )

    def render(self, surface: pygame.Surface, gm: GameManager, im: InnovationManager, rnd_cost_mult: float = 1.0):
        # Layout columns
        col_w = min(540, (self.width - 64) // 2)
        right_x = 24 + col_w + 16
        right_w = self.width - right_x - 24
        top_h = 215

        # =====================================================================
        # 1. Top-Left: Upcoming Grand Prix Card with Vector Track Radar
        # =====================================================================
        is_race_week = gm.is_race_week_for_player()
        race_event = gm.get_current_race_event()
        gp_rect = pygame.Rect(24, 70, col_w, top_h)
        UITheme.draw_panel(surface, gp_rect)

        hdr_rect = pygame.Rect(gp_rect.x, gp_rect.y, gp_rect.width, 28)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, hdr_rect, border_top_left_radius=4, border_top_right_radius=4)

        if is_race_week:
            gp_ic = UIIcons.get_icon("flag", size=14, color=UITheme.ACCENT_CYAN)
            surface.blit(gp_ic, (gp_rect.x + 12, gp_rect.y + 7))
            t_txt = self.font_title.render("NEXT GP — CIRCUIT RADAR & DEMANDS", True, UITheme.ACCENT_CYAN)
            surface.blit(t_txt, (gp_rect.x + 32, gp_rect.y + 6))

            round_badge = self.font_badge.render(
                f"[ ROUND {gm.current_round}/{gm.total_rounds} • WEEK {gm.current_week}/{gm.total_season_weeks} ]",
                True,
                (0, 220, 255),
            )
            surface.blit(round_badge, (gp_rect.right - 10 - round_badge.get_width(), gp_rect.y + 8))

            # Left half of GP card: Vector Track Radar Map
            map_w = min(200, gp_rect.width // 2 - 14)
            map_rect = pygame.Rect(gp_rect.x + 10, gp_rect.y + 36, map_w, gp_rect.height - 46)
            circ_file = race_event.get("circuit_file", "emerald_ring.json")
            total_laps = race_event.get("total_laps", 15)
            self._render_vector_circuit(surface, map_rect, circ_file, total_laps)

            # Right half: Track Details & Demand Gauges
            right_details_x = map_rect.right + 12
            right_details_w = gp_rect.right - right_details_x - 10

            t_name = race_event.get("track_name", "Grand Prix Circuit")
            surface.blit(
                self.font_card_title.render(t_name.upper(), True, (255, 215, 0)),
                (right_details_x, gp_rect.y + 34),
            )

            track_char = race_event.get("characteristic", "BALANCED")
            w_prof = race_event.get("weather_profile", "DYNAMIC")
            demands_rect = pygame.Rect(right_details_x, gp_rect.y + 54, right_details_w, gp_rect.height - 64)
            self._render_track_demands(surface, demands_rect, track_char, w_prof)
        else:
            # Bye Week Card
            by_ic = UIIcons.get_icon("wrench", size=14, color=(255, 215, 0))
            surface.blit(by_ic, (gp_rect.x + 12, gp_rect.y + 7))
            t_txt = self.font_title.render("HQ DEVELOPMENT & R&D (BYE WEEK)", True, (255, 215, 0))
            surface.blit(t_txt, (gp_rect.x + 32, gp_rect.y + 6))

            wk_badge = self.font_badge.render(
                f"[ WEEK {gm.current_week}/{gm.total_season_weeks} ]", True, (255, 215, 0)
            )
            surface.blit(wk_badge, (gp_rect.right - 10 - wk_badge.get_width(), gp_rect.y + 8))

            up_name = race_event.get("track_name", "Upcoming GP") if race_event else "Grand Prix"
            up_rnd = race_event.get("round", gm.current_round) if race_event else gm.current_round
            up_wk = race_event.get("week", gm.current_week + 1) if race_event else gm.current_week + 1

            tr_ic = UIIcons.get_icon("flag", size=13, color=(0, 240, 140))
            surface.blit(tr_ic, (gp_rect.x + 14, gp_rect.y + 38))
            surface.blit(
                self.font_body.render(
                    f"Next Race: Round {up_rnd} at {up_name} (Calendar Week {up_wk})", True, (0, 240, 140)
                ),
                (gp_rect.x + 34, gp_rect.y + 37),
            )

            # Active Feeder Series on Track
            other_series = gm.get_other_series_racing_this_week()
            tier_short = {1: "Tier 1 WSF", 2: "Tier 2 Continental", 4: "Tier 4 JTS Junior", 5: "Tier 5 Karting"}
            racing_names = []
            for s in other_series:
                s_tier = s["tier"]
                s_lbl = tier_short.get(s_tier, f"Tier {s_tier}")
                racing_names.append(f"{s_lbl}: {s['track_name']}")
            racing_str = " | ".join(racing_names[:2]) if racing_names else "Factory Development & Wind Tunnel Testing"
            surface.blit(
                self.font_badge.render(f"ACTIVE RACING THIS WEEK: {racing_str.upper()}", True, (0, 220, 255)),
                (gp_rect.x + 14, gp_rect.y + 62),
            )

            hq_box = pygame.Rect(gp_rect.x + 10, gp_rect.y + 86, gp_rect.width - 20, 114)
            pygame.draw.rect(surface, (18, 24, 32), hq_box, border_radius=3)
            pygame.draw.rect(surface, UITheme.PANEL_BORDER, hq_box, width=1, border_radius=3)
            surface.blit(
                self.font_badge.render("HQ FOCUS & SIMULATION MILESTONES:", True, UITheme.TEXT_MUTED),
                (hq_box.x + 10, hq_box.y + 8),
            )
            surface.blit(
                self.font_body.render(
                    "• R&D engineering teams progressing active breakthrough pitches.", True, UITheme.TEXT_WHITE
                ),
                (hq_box.x + 10, hq_box.y + 28),
            )
            surface.blit(
                self.font_body.render(
                    "• Junior academy prospects gaining racecraft experience in lower tiers.", True, (0, 220, 255)
                ),
                (hq_box.x + 10, hq_box.y + 48),
            )
            surface.blit(
                self.font_badge.render(
                    "Advance calendar week to simulate active leagues and collect financial revenue.",
                    True,
                    (0, 240, 140),
                ),
                (hq_box.x + 10, hq_box.y + 74),
            )

        # =====================================================================
        # 2. Top-Right: Active Sponsor Targets & Financial Projection
        # =====================================================================
        sp_rect = pygame.Rect(right_x, 70, right_w, top_h)
        UITheme.draw_panel(surface, sp_rect)

        sp_hdr = pygame.Rect(sp_rect.x, sp_rect.y, sp_rect.width, 28)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, sp_hdr, border_top_left_radius=4, border_top_right_radius=4)
        sp_ic = UIIcons.get_icon("target", size=14, color=(255, 215, 0))
        surface.blit(sp_ic, (sp_rect.x + 12, sp_rect.y + 7))
        sp_txt = self.font_title.render("ACTIVE SPONSOR TARGETS & COMMERCIAL CONTRACTS", True, (255, 215, 0))
        surface.blit(sp_txt, (sp_rect.x + 32, sp_rect.y + 6))

        active_sponsors_list = []
        try:
            with gm.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT * FROM active_sponsors WHERE team_id = ? ORDER BY slot_tier ASC, slot_index ASC;",
                    (gm.team_id,),
                )
                active_sponsors_list = [dict(r) for r in cur.fetchall()]
        except Exception:
            active_sponsors_list = []

        card_h = (sp_rect.height - 48) // 2
        for s_idx in range(2):
            sy = sp_rect.y + 36 + s_idx * (card_h + 8)
            s_box = pygame.Rect(sp_rect.x + 10, sy, sp_rect.width - 20, card_h)
            pygame.draw.rect(surface, (18, 24, 30), s_box, border_radius=3)

            if s_idx < len(active_sponsors_list):
                sp = active_sponsors_list[s_idx]
                tier_col = (255, 215, 0) if s_idx == 0 else (0, 220, 255)
                pygame.draw.rect(surface, tier_col, s_box, width=1, border_radius=3)

                aw_ic = UIIcons.get_icon("award", size=13, color=tier_col)
                surface.blit(aw_ic, (s_box.x + 10, s_box.y + 8))
                raw_partner_title = f"{sp.get('slot_tier', 'COMMERCIAL')} PARTNER: {sp.get('brand_name', 'Partner')}"
                partner_title = self._truncate_text(self.font_card_title, raw_partner_title, s_box.width - 145)
                surface.blit(
                    self.font_card_title.render(partner_title, True, tier_col),
                    (s_box.x + 28, s_box.y + 7),
                )

                tgt_pos = sp.get("target_position")
                tgt_str = f"Target: Finish P{tgt_pos} or better" if tgt_pos else "Target: Reliable race finish"
                UITheme.draw_icon(surface, "target", (s_box.x + 10, s_box.y + 28), color=UITheme.TEXT_MUTED, size=12)
                surface.blit(self.font_body.render(tgt_str, True, UITheme.TEXT_WHITE), (s_box.x + 26, s_box.y + 26))

                # Payout Badge
                tgt_bonus = sp.get("target_bonus", 0.0)
                per_race = sp.get("per_race_payment", 0.0)
                r_left = sp.get("races_remaining", 0)
                p_str = f"Fixed: +${per_race:,.0f}/race  |  Bonus: +${tgt_bonus:,.0f} on P{tgt_pos or 10}"
                UITheme.draw_icon(
                    surface, "circle-dollar-sign", (s_box.x + 10, s_box.y + 48), color=(0, 240, 140), size=12
                )
                surface.blit(self.font_badge.render(p_str, True, (0, 240, 140)), (s_box.x + 26, s_box.y + 47))

                # Races Remaining Pill on right
                rem_pill = pygame.Rect(s_box.right - 110, s_box.y + 7, 100, 18)
                pygame.draw.rect(surface, (28, 36, 48), rem_pill, border_radius=2)
                r_surf = self.font_mini.render(f"{r_left} RACES LEFT", True, UITheme.TEXT_MUTED)
                surface.blit(r_surf, (rem_pill.x + (rem_pill.width - r_surf.get_width()) // 2, rem_pill.y + 3))
            else:
                pygame.draw.rect(surface, (45, 52, 65), s_box, width=1, border_radius=3)
                lbl = "PRIMARY TITLE SPONSOR" if s_idx == 0 else "SECONDARY COMMERCIAL SPONSOR"
                surface.blit(
                    self.font_card_title.render(f"{lbl}: VACANT SLOT", True, UITheme.TEXT_MUTED),
                    (s_box.x + 10, s_box.y + 8),
                )
                surface.blit(
                    self.font_body.render("Commercial slot open for corporate negotiation.", True, UITheme.TEXT_MUTED),
                    (s_box.x + 10, s_box.y + 28),
                )
                surface.blit(
                    self.font_badge.render(
                        "Visit SPONSORS tab to review corporate partnership offers.", True, (0, 220, 255)
                    ),
                    (s_box.x + 10, s_box.y + 48),
                )

        # =====================================================================
        # 3. Bottom-Left: R&D Innovation Pipeline
        # =====================================================================
        pitches = im.get_team_pitches(gm.team_id, status="PENDING")
        active_pitches = im.get_team_pitches(gm.team_id, status="ACTIVE")

        pipe_y = 70 + top_h + 12
        pipe_h = self.height - pipe_y - 75
        pipe_rect = pygame.Rect(24, pipe_y, col_w, pipe_h)
        UITheme.draw_panel(surface, pipe_rect)

        pipe_hdr = pygame.Rect(pipe_rect.x, pipe_rect.y, pipe_rect.width, 28)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, pipe_hdr, border_top_left_radius=4, border_top_right_radius=4)
        spk_ic = UIIcons.get_icon("sparkles", size=14, color=(255, 180, 40))
        surface.blit(spk_ic, (pipe_rect.x + 12, pipe_rect.y + 7))
        p_txt = self.font_title.render(f"R&D INNOVATION PIPELINE ({len(pitches)} Proposals)", True, (255, 180, 40))
        surface.blit(p_txt, (pipe_rect.x + 32, pipe_rect.y + 6))

        act_rect, cards = self.get_pipeline_layout(active_pitches, pending_pitches=pitches)

        if not active_pitches and not pitches:
            emp_box = pygame.Rect(pipe_rect.x + 10, pipe_rect.y + 40, pipe_rect.width - 20, 90)
            pygame.draw.rect(surface, (18, 22, 28), emp_box, border_radius=3)
            pygame.draw.rect(surface, UITheme.PANEL_BORDER, emp_box, width=1, border_radius=3)
            surface.blit(
                self.font_card_title.render("NO ACTIVE PROPOSALS", True, UITheme.TEXT_MUTED),
                (emp_box.x + 10, emp_box.y + 16),
            )
            surface.blit(
                self.font_body.render(
                    "Chief Engineers pitch high-risk breakthroughs on race weeks.", True, UITheme.TEXT_MUTED
                ),
                (emp_box.x + 10, emp_box.y + 36),
            )

        if act_rect and active_pitches:
            ap = active_pitches[0]
            pygame.draw.rect(surface, (30, 42, 22), act_rect, border_radius=3)
            pygame.draw.rect(surface, (160, 200, 40), act_rect, width=1, border_radius=3)
            ap_type = ap.get("idea_type", "CREATIVE")
            surface.blit(
                self.font_card_title.render(f"ACTIVE [{ap_type}]: {ap['title']}", True, (255, 220, 50)),
                (act_rect.x + 8, act_rect.y + 4),
            )
            raw_cats = ap.get("target_categories") or ap.get("category", "R&D")
            gain = ap.get("knowledge_gain", 20.0)
            surface.blit(
                self.font_body.render(
                    f"Target: {raw_cats} (+{gain:.0f} Knowledge) | {ap.get('weeks_remaining', 1)} wks left",
                    True,
                    UITheme.TEXT_WHITE,
                ),
                (act_rect.x + 8, act_rect.y + 20),
            )
            surface.blit(
                self.font_badge.render(
                    f"Lockout: {ap.get('locked_subnode', 'N/A')} | Success Est: {ap.get('est_success_min', 0)}%–{ap.get('est_success_max', 100)}%",
                    True,
                    (0, 220, 255),
                ),
                (act_rect.x + 8, act_rect.y + 36),
            )

        for idx, (c_rect, greenlight_btn, discard_btn) in enumerate(cards):
            if idx >= len(pitches):
                break
            p = pitches[idx]
            pygame.draw.rect(surface, (20, 26, 34), c_rect, border_radius=3)
            pygame.draw.rect(surface, UITheme.PANEL_BORDER, c_rect, width=1, border_radius=3)

            p_type = p.get("idea_type", "CREATIVE")
            is_creative = p_type == "CREATIVE"
            b_col = (240, 110, 255) if is_creative else (0, 220, 255)
            UITheme.draw_icon(
                surface, "sparkles" if is_creative else "search", (c_rect.x + 8, c_rect.y + 5), color=b_col, size=12
            )
            surface.blit(self.font_badge.render(p["title"], True, (255, 225, 60)), (c_rect.x + 24, c_rect.y + 4))

            raw_cats = p.get("target_categories") or p.get("category", "R&D")
            gain = p.get("knowledge_gain", 20.0)
            surface.blit(
                self.font_body.render(f"+{gain:.0f} Knowledge to [{raw_cats}]", True, (0, 255, 160)),
                (c_rect.x + 8, c_rect.y + 24),
            )
            surface.blit(
                self.font_body.render(
                    f"Success: {p['est_success_min']}%–{p['est_success_max']}% | Cost: ${p['hard_cost']:,.0f}",
                    True,
                    (180, 210, 240),
                ),
                (c_rect.x + 8, c_rect.y + 42),
            )
            UITheme.draw_button(
                surface,
                greenlight_btn,
                "APPROVE",
                self.font_badge,
                icon="check",
                icon_size=11,
                bg_color=(20, 45, 30),
                border_color=(0, 230, 120),
            )
            UITheme.draw_button(
                surface,
                discard_btn,
                "DISCARD",
                self.font_badge,
                icon="x",
                icon_size=11,
                bg_color=(45, 20, 25),
                border_color=(240, 80, 80),
            )

        # =====================================================================
        # 4. Bottom-Right: 4-Point Pre-Race Readiness Checklist & Telemetry Inbox
        # =====================================================================
        stat_rect = pygame.Rect(right_x, pipe_y, right_w, pipe_h)
        UITheme.draw_panel(surface, stat_rect)

        stat_hdr = pygame.Rect(stat_rect.x, stat_rect.y, stat_rect.width, 28)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, stat_hdr, border_top_left_radius=4, border_top_right_radius=4)
        s_title = self.font_title.render("PRE-RACE READINESS CHECKLIST & TELEMETRY INBOX", True, UITheme.ACCENT_CYAN)
        surface.blit(s_title, (stat_rect.x + 12, stat_rect.y + 6))

        # Query mounted components on Car 1 & Car 2 for reliability warnings
        worn_parts = []
        try:
            with gm.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT id, car_slot, category, reliability FROM car_components "
                    "WHERE team_id = ? AND car_slot IN (1, 2) AND reliability < 80.0 "
                    "ORDER BY reliability ASC;",
                    (gm.team_id,),
                )
                worn_parts = [dict(r) for r in cur.fetchall()]
        except Exception:
            worn_parts = []

        # Priority Alert Queue Banner
        alert_box = pygame.Rect(stat_rect.x + 10, stat_rect.y + 36, stat_rect.width - 20, 26)
        if worn_parts:
            worst = worn_parts[0]
            pygame.draw.rect(surface, (45, 25, 20), alert_box, border_radius=3)
            pygame.draw.rect(surface, (255, 90, 70), alert_box, width=1, border_radius=3)
            UITheme.draw_icon(
                surface, "alert-triangle", (alert_box.x + 8, alert_box.y + 6), color=(255, 90, 70), size=14
            )
            surface.blit(
                self.font_badge.render(
                    f"ACTION REQUIRED: Car #{worst['car_slot']} {worst['category']} reliability at {worst['reliability']:.0f}%!",
                    True,
                    (255, 120, 100),
                ),
                (alert_box.x + 28, alert_box.y + 6),
            )
        else:
            pygame.draw.rect(surface, (18, 38, 28), alert_box, border_radius=3)
            pygame.draw.rect(surface, (0, 230, 120), alert_box, width=1, border_radius=3)
            UITheme.draw_icon(surface, "check", (alert_box.x + 8, alert_box.y + 6), color=(0, 230, 120), size=14)
            surface.blit(
                self.font_badge.render("ALL SYSTEMS GREEN: 100% Pre-Race Readiness Certified", True, (0, 240, 140)),
                (alert_box.x + 28, alert_box.y + 6),
            )

        # 4-Point Checklist Items
        drivers = gm.db.get_team_drivers(gm.team_id)
        d1_name = drivers[0]["name"] if len(drivers) > 0 else "Driver 1"
        d2_name = drivers[1]["name"] if len(drivers) > 1 else "Driver 2"

        checklist_items = [
            (
                "CAR SETUP & CHASSIS BALANCE",
                "Aero downforce and gear ratios configured for track demands.",
                True,
                "READY",
                (0, 240, 140),
            ),
            (
                "DRIVER LINEUP & FITNESS",
                f"Car #1: {d1_name} | Car #2: {d2_name} (Active Focus)",
                True,
                "ACTIVE",
                (0, 220, 255),
            ),
            (
                "PARTS WEAR & RELIABILITY",
                f"Worn parts detected ({len(worn_parts)} item(s) < 80%)"
                if worn_parts
                else "All 14 mounted components >= 80% reliability nominal.",
                not worn_parts,
                "WARNING" if worn_parts else "OPTIMAL",
                (255, 80, 80) if worn_parts else (0, 240, 140),
            ),
            (
                "PIT CREW & STRATEGY DRILLS",
                "Sub-2.4s pit stop training drills logged with zero fatigue penalty.",
                True,
                "READY",
                (0, 240, 140),
            ),
        ]

        check_y = alert_box.bottom + 8
        c_item_h = 34
        self.resolve_btn_rect = None

        for idx, (c_title, c_sub, c_ok, c_badge, c_col) in enumerate(checklist_items):
            iy = check_y + idx * (c_item_h + 6)
            c_card = pygame.Rect(stat_rect.x + 10, iy, stat_rect.width - 20, c_item_h)
            pygame.draw.rect(surface, (18, 24, 32), c_card, border_radius=3)
            pygame.draw.rect(surface, UITheme.PANEL_BORDER, c_card, width=1, border_radius=3)

            # Icon
            ic_name = "check" if c_ok else "wrench"
            UITheme.draw_icon(surface, ic_name, (c_card.x + 8, c_card.y + 10), color=c_col, size=14)

            # Labels
            surface.blit(self.font_badge.render(c_title, True, UITheme.TEXT_WHITE), (c_card.x + 28, c_card.y + 3))
            surface.blit(self.font_mini.render(c_sub, True, UITheme.TEXT_MUTED), (c_card.x + 28, c_card.y + 18))

            # Status Badge or 1-Click Resolve Button
            if not c_ok and idx == 2:
                btn_w = 110
                btn_rect = pygame.Rect(c_card.right - btn_w - 6, c_card.y + 6, btn_w, 22)
                self.resolve_btn_rect = btn_rect
                UITheme.draw_button(
                    surface,
                    btn_rect,
                    "AUTO-RESOLVE",
                    self.font_mini,
                    icon="wrench",
                    icon_size=11,
                    bg_color=(160, 50, 40),
                    border_color=(255, 90, 70),
                )
            else:
                s_pill = pygame.Rect(c_card.right - 70, c_card.y + 8, 64, 18)
                pygame.draw.rect(surface, (20, 30, 40), s_pill, border_radius=2)
                p_txt = self.font_mini.render(c_badge, True, c_col)
                surface.blit(p_txt, (s_pill.x + (s_pill.width - p_txt.get_width()) // 2, s_pill.y + 2))

        # Status note bar
        note_y = check_y + 4 * (c_item_h + 6) + 6
        log_text = self._truncate_text(self.font_mini, f"TELEMETRY LOG: {self.action_message}", stat_rect.width - 24)
        surface.blit(
            self.font_mini.render(log_text, True, (0, 220, 255)),
            (stat_rect.x + 12, note_y),
        )

        # Big Action Button: START RACE WEEKEND vs ADVANCE CALENDAR WEEK
        race_btn_rect = pygame.Rect(self.width - 320, self.height - 65, 300, 48)
        action_btn_text = "START RACE WEEKEND" if is_race_week else "ADVANCE WEEK"
        action_btn_icon = "flag" if is_race_week else "fast-forward"
        UITheme.draw_button(
            surface,
            race_btn_rect,
            action_btn_text,
            self.font_race_btn,
            icon=action_btn_icon,
            icon_size=16,
            is_active=True,
        )

        # View Weekly Roundup Button
        roundup_btn = pygame.Rect(self.width - 530, self.height - 65, 195, 48)
        UITheme.draw_button(
            surface,
            roundup_btn,
            "WEEKLY ROUNDUP",
            self.font_card_title,
            icon="calendar",
            icon_size=15,
        )
