import os
import sys
from typing import Any, Dict, List, Optional

import pygame

from src.core.car import Car
from src.core.circuit import Circuit
from src.core.race_weekend import RaceWeekendManager, RaceWeekendSession
from src.core.simulation import Simulation
from src.data.default_tracks import create_emerald_ring, initialize_default_tracks_folder
from src.data.teams import load_career_teams_and_drivers, load_teams_and_drivers_from_db
from src.editor.admin_hub import AdminHub
from src.management.tutorial_manager import TutorialManager
from src.render.camera import Camera
from src.render.car_renderer import CarRenderer
from src.render.track_renderer import TrackRenderer
from src.ui.broadcast_header import BroadcastHeader
from src.ui.driver_panel import DriverStrategyPanel
from src.ui.event_feed import EventFeed
from src.ui.management_hub.management_hub import ManagementHub
from src.ui.pit_modal import PitStrategyModal
from src.ui.race_weekend.race_weekend_screen import RaceWeekendScreen
from src.ui.radio_banner import RadioBannerWidget
from src.ui.start_screen import StartScreen
from src.ui.theme import UITheme
from src.ui.timing_tower import TimingTower
from src.ui.tutorial_overlay import TutorialOverlay

if getattr(sys, "frozen", False):
    # PyInstaller bundle: ensure working directory is the application executable directory
    os.chdir(os.path.dirname(sys.executable))

if sys.platform == "win32":
    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            # DPI awareness calls may fail on older Windows versions or headless environments
            pass


class RaceGameApp:
    """Main Desktop Game Application with Full Motorsport Management Tycoon System."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Open-Wheel Motorsport Management Tycoon & Race Simulator")

        self.width = 1280
        self.height = 720
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.is_running = True

        # Auto-detect display scale for high-DPI and 5K ultrawide screens
        UITheme.auto_detect_scale(self.width, self.height)

        # 1. Instant Startup Splash Screen (User sees progress bar immediately)
        self._render_splash_screen("Initializing Race Control Engine...", 0.20)

        self.zoom_toast_timer: float = 0.0
        self.zoom_toast_msg: str = ""

        initialize_default_tracks_folder("tracks")
        self.available_tracks: List[str] = self._scan_tracks()

        # Application Modes: "START", "MANAGEMENT", "RACE", "ADMIN", "WEEKEND"
        self.mode = "START"
        self.weekend_manager: Optional[RaceWeekendManager] = None
        self.weekend_screen: Optional[RaceWeekendScreen] = None
        self.live_session_type: str = "RACE"

        # 2. Splash progress: Loading Management Hub
        self._render_splash_screen("Loading Management Career Databases...", 0.55)
        self.management_hub = ManagementHub(
            self.width, self.height, on_start_race_weekend=self.start_race_weekend, on_switch_mode=self.set_mode
        )

        # Guided Tutorial System
        self.tutorial_manager = TutorialManager(
            self.management_hub.db, team_id=self.management_hub.gm.team_id, on_switch_tab=self.management_hub.switch_tab
        )
        self.tutorial_manager.is_active = False
        self.management_hub.tutorial_manager = self.tutorial_manager
        self.tutorial_overlay = TutorialOverlay(
            self.width, self.height, self.tutorial_manager, management_hub=self.management_hub
        )

        # 3. Start Screen
        self.start_screen = StartScreen(
            self.width,
            self.height,
            on_start_career=self.start_new_career,
            on_continue=self.continue_career,
            on_open_admin=lambda: self.set_mode("ADMIN"),
        )

        # 4. Splash progress: Admin & CAD Tools
        self._render_splash_screen("Preparing Circuit Designer & Database Editor...", 0.85)
        self.admin_hub = AdminHub(
            self.width, self.height, on_back_to_menu=self._on_admin_back, on_test_race=self.start_race_on_circuit
        )

        # Viewports & UI components
        self._init_layout()

        # Renderers & Camera
        self.camera = Camera(self.width, self.height)
        self.track_renderer = TrackRenderer()
        self.car_renderer = CarRenderer()

        # Circuit & Lazy Simulation Initialization (ready on demand)
        default_circuit = create_emerald_ring()
        self.circuit = default_circuit
        self.driver_car_pairs = load_teams_and_drivers_from_db("race_game.db")
        self.sim: Optional[Simulation] = None

        # Camera fit
        self.camera.fit_circuit(self.circuit, self.view_rect)

        # 5. Splash completion
        self._render_splash_screen("Ready!", 1.0)

    def _render_splash_screen(self, status_text: str, progress: float):
        """Renders an immediate boot progress bar so the game launches with zero black-screen lag."""
        self.screen.fill((10, 14, 20))
        cx = self.width // 2
        cy = self.height // 2

        font_logo = UITheme.get_font(22, bold=True)
        font_sub = UITheme.get_font(11, bold=False)
        font_bar = UITheme.get_font(10, bold=True)

        logo = font_logo.render("OPEN-WHEEL MOTORSPORT MANAGEMENT", True, UITheme.ACCENT_CYAN)
        sub = font_sub.render("Loading simulation subsystems and race calendar...", True, UITheme.TEXT_MUTED)
        self.screen.blit(logo, (cx - logo.get_width() // 2, cy - 80))
        self.screen.blit(sub, (cx - sub.get_width() // 2, cy - 45))

        # Progress bar
        bar_w = 420
        bar_h = 18
        bar_rect = pygame.Rect(cx - bar_w // 2, cy, bar_w, bar_h)
        pygame.draw.rect(self.screen, (20, 26, 36), bar_rect, border_radius=4)
        fill_w = int(bar_w * max(0.0, min(1.0, progress)))
        if fill_w > 0:
            pygame.draw.rect(
                self.screen, (0, 220, 240), pygame.Rect(bar_rect.x, bar_rect.y, fill_w, bar_h), border_radius=4
            )
        pygame.draw.rect(self.screen, (40, 50, 68), bar_rect, width=1, border_radius=4)

        # Status text & percentage
        stat_lbl = font_bar.render(f"{status_text} ({int(progress * 100)}%)", True, UITheme.TEXT_WHITE)
        self.screen.blit(stat_lbl, (cx - stat_lbl.get_width() // 2, cy + 28))

        pygame.display.flip()
        # Pump event queue so OS knows window is responsive
        pygame.event.pump()

    def _scan_tracks(self) -> List[str]:
        if not os.path.exists("tracks"):
            return []
        return [f for f in os.listdir("tracks") if f.endswith(".json")]

    def _init_layout(self):
        self.timing_tower = TimingTower(10, 56, 290, self.height - 200)
        self.driver_panel = DriverStrategyPanel(
            10, self.height - 138, self.width - 20, 130, on_box_click=self.on_box_button_clicked
        )
        self.broadcast_header = BroadcastHeader(self.width, 48)
        self.event_feed = EventFeed(self.width - 360, self.height - 290, 350, 140)
        self.pit_modal = PitStrategyModal(self.width, self.height)
        self.radio_banner = RadioBannerWidget(self.width)

        # 2D Race Viewport
        self.view_rect = pygame.Rect(310, 56, self.width - 320, self.height - 200)

    def on_box_button_clicked(self, car: Car):
        if car.box_this_lap:
            car.cancel_pit_stop()
        else:
            team_id = getattr(self.management_hub.gm, "team_id", None) if hasattr(self, "management_hub") else None
            db = getattr(self.management_hub, "db", None) if hasattr(self, "management_hub") else None
            self.pit_modal.open(car, self.circuit.get_dry_compounds(), db_manager=db, team_id=team_id)

    def start_new_career(
        self,
        team_name: str,
        principal_name: str,
        color_hex: str,
        difficulty: str,
        engine_supplier: str = "Vortex EcoTech",
        enable_tutorial: bool = True,
    ):
        """Creates a fresh career with custom player team name, CEO / Team Principal name, livery color, difficulty, and Season 1 Engine Supplier."""
        self.management_hub.db.create_new_career(
            team_name,
            color_hex,
            difficulty,
            engine_supplier,
            principal_name=principal_name,
            enable_tutorial=enable_tutorial,
        )
        self.management_hub.difficulty_mgr.set_difficulty(difficulty)
        self.management_hub.gm.refresh_player_team()
        self.tutorial_manager.team_id = self.management_hub.gm.team_id
        if enable_tutorial:
            self.tutorial_manager.restart_tutorial()
        else:
            self.tutorial_manager.skip_tutorial()
        self.start_screen.has_existing_career = True
        self.mode = "MANAGEMENT"

    def continue_career(self):
        """Continues existing saved career with persisted difficulty settings."""
        self.management_hub.gm.refresh_player_team()
        saved_diff = self.management_hub.gm.player_team.get("difficulty", "NORMAL")
        self.management_hub.difficulty_mgr.set_difficulty(saved_diff)
        self.tutorial_manager.team_id = self.management_hub.gm.team_id
        self.tutorial_manager.load_state()
        self.mode = "MANAGEMENT"

    def start_race_weekend(self, race_event: Dict[str, Any]):
        """Transitions from Management Hub into the interactive Race Weekend Hub."""
        circuit_file = race_event.get("circuit_file", "emerald_ring.json")
        track_path = os.path.join("tracks", circuit_file)

        if os.path.exists(track_path):
            self.circuit = Circuit.load_json(track_path)
        else:
            self.circuit = create_emerald_ring()

        tier = self.management_hub.gm.player_team.get("tier", 3)
        total_laps = race_event.get("total_laps", 22)
        if hasattr(self, "management_hub") and self.management_hub.db:
            self.driver_car_pairs = load_career_teams_and_drivers(self.management_hub.db, tier=tier)

        # Query facility tiers and active equipment levels for player team
        team_id = self.management_hub.gm.team_id
        fac_tiers = {}
        eq_lvls = {}
        if hasattr(self, "management_hub") and self.management_hub.db:
            with self.management_hub.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT node_id, current_tier FROM team_facilities WHERE team_id = ? AND is_unlocked = 1;",
                    (team_id,),
                )
                fac_tiers = {r[0]: r[1] for r in cur.fetchall()}
                cur.execute(
                    "SELECT equipment_id, current_level FROM team_equipment WHERE team_id = ? AND is_active = 1;",
                    (team_id,),
                )
                eq_lvls = {r[0]: r[1] for r in cur.fetchall()}

        self.weekend_manager = RaceWeekendManager(
            league_tier=tier,
            track_metadata=race_event,
            total_laps_base=total_laps,
            facility_tiers=fac_tiers,
            equipment_levels=eq_lvls,
        )

        drivers = self.management_hub.db.get_team_drivers(self.management_hub.gm.team_id)

        self.weekend_screen = RaceWeekendScreen(
            self.width,
            self.height,
            manager=self.weekend_manager,
            drivers=drivers,
            on_start_live_session=self.start_live_session_from_weekend,
            on_finish_weekend=self.on_weekend_completed,
            driver_car_pairs=self.driver_car_pairs,
            career_db=self.management_hub.db,
            team_id=self.management_hub.gm.team_id,
        )

        self.tutorial_manager.sync_game_state("WEEKEND")
        self.mode = "WEEKEND"

    def start_live_session_from_weekend(
        self, session_type: str, laps: int, grid: Optional[List[Dict[str, Any]]] = None
    ):
        """Starts a live 2D track simulation for a specific weekend session (Sprint or Grand Prix)."""
        active_pairs = self.driver_car_pairs
        if grid:
            ordered = []
            pair_map = {p[0].name: p for p in self.driver_car_pairs}
            for g in grid:
                d_name = g.get("driver_name")
                if d_name in pair_map:
                    ordered.append(pair_map[d_name])
            if len(ordered) == len(self.driver_car_pairs):
                active_pairs = ordered

        current_tier = getattr(self.weekend_manager, "tier", 3)

        # Load persisted car part durabilities from db for player cars
        car_durs = {}
        fac_tiers = getattr(self.weekend_manager, "facility_tiers", {})
        eq_lvls = getattr(self.weekend_manager, "equipment_levels", {})

        if hasattr(self, "management_hub") and self.management_hub.db:
            team_id = self.management_hub.gm.team_id
            all_comps = self.management_hub.db.get_team_components(team_id)
            for slot in (1, 2):
                car_durs[slot] = {
                    c["category"]: c.get("current_durability", 100.0 - c.get("wear_pct", 0.0))
                    for c in all_comps
                    if c["car_slot"] == slot
                }

        track_meta = getattr(self.weekend_manager, "track_metadata", {})
        weather_prof = track_meta.get("weather_profile", "DYNAMIC")

        self.sim = Simulation(
            self.circuit,
            active_pairs,
            total_laps=laps,
            session_type=session_type,
            car_setups=self.weekend_manager.car_setups,
            setup_confidences=self.weekend_manager.setup_confidence,
            practice_bonuses=self.weekend_manager.practice_bonuses,
            league_tier=current_tier,
            car_durabilities=car_durs,
            weather_profile=weather_prof,
            car_setup_scores={
                1: self.weekend_manager.evaluate_car_setup_scores(1),
                2: self.weekend_manager.evaluate_car_setup_scores(2),
            },
        )
        self.sim.team_facilities = fac_tiers
        self.sim.team_equipment = eq_lvls

        # Apply trackside pit crew and repair modifiers to player cars
        jack_tier = fac_tiers.get("track_jack_release", 0)
        jack_eq = eq_lvls.get("eq_jck_sub02_pivot", 0)
        repair_tier = fac_tiers.get("track_fast_repair", 0)
        repair_jig_eq = eq_lvls.get("eq_rep_quick_latch_jig", 0)
        repair_rivet_eq = eq_lvls.get("eq_rep_pneumatic_riveter", 0)
        repair_resin_eq = eq_lvls.get("eq_rep_rapid_curing_resin", 0)
        wheelgun_tier = fac_tiers.get("track_wheelguns", 0)

        for car in self.sim.cars:
            if getattr(car.driver, "is_player", False):
                car.pit_modifiers = {
                    "base_stop_reduction": 0.15 * wheelgun_tier + 0.15 * jack_tier + 0.05 * jack_eq,
                    "error_rate_mult": max(0.2, 1.0 - 0.25 * jack_tier),
                    "wing_change_time": max(2.0, 4.0 - 0.6 * repair_tier - 0.15 * repair_jig_eq),
                    "repair_time": max(7.0, 14.0 - 2.0 * repair_tier - 0.4 * repair_rivet_eq),
                    "repair_durability_min": min(75.0, 55.0 + 7.0 * repair_tier + 1.5 * repair_resin_eq),
                    "repair_durability_max": min(80.0, 60.0 + 7.0 * repair_tier + 1.5 * repair_resin_eq),
                }

        self.live_session_type = session_type
        self.mode = "RACE"
        self.camera.mode = "TRACK_OVERVIEW"
        self.camera.fit_circuit(self.circuit, self.view_rect)
        self.tutorial_manager.sync_game_state("RACE")
        if self.tutorial_manager.is_active:
            cur_s = self.tutorial_manager.get_current_step()
            if cur_s and cur_s.step_id == "LIVE_RACE_PITWALL":
                self.sim.is_paused = True

    def start_race_on_circuit(self, circuit: Circuit, total_laps: int = 15):
        self.circuit = circuit
        self.sim = Simulation(self.circuit, self.driver_car_pairs, total_laps=total_laps, league_tier=3)
        self.mode = "RACE"
        self.camera.mode = "TRACK_OVERVIEW"
        self.camera.fit_circuit(self.circuit, self.view_rect)

    def on_weekend_completed(self, weekend_summary: Dict[str, Any]):
        """Passes full weekend results to Management Hub and returns to HQ."""
        final_results = weekend_summary.get("race_results") or weekend_summary.get("sprint_results") or []
        self.management_hub.on_race_completed(final_results)
        self.tutorial_manager.sync_game_state("MANAGEMENT")
        self.mode = "MANAGEMENT"

    def return_to_management_hub(self):
        """Processes race results, persists end-of-race component durabilities, and returns to Dashboard/Weekend."""
        # Persist post-race part durabilities back to database for player cars
        if hasattr(self, "management_hub") and self.management_hub.db:
            team_id = self.management_hub.gm.team_id
            player_cars = [c for c in self.sim.cars if c.driver.is_player]
            for p_car in player_cars:
                slot = 1 if getattr(p_car.driver, "number", 1) % 2 != 0 else 2
                self.management_hub.db.save_car_part_durabilities(team_id, slot, p_car.part_durability)

        sorted_cars = sorted(self.sim.cars, key=lambda c: c.position)
        results = []
        for pos, car in enumerate(sorted_cars, 1):
            results.append(
                {
                    "position": pos,
                    "driver_name": car.driver.name,
                    "team_name": car.driver.team_name,
                    "is_player": car.driver.is_player,
                }
            )

        if hasattr(self, "weekend_manager") and self.weekend_manager and not self.weekend_manager.is_weekend_completed:
            if self.live_session_type == "SPRINT":
                self.weekend_manager.record_session_completion(RaceWeekendSession.SPRINT, results)
            elif self.live_session_type == "RACE":
                self.weekend_manager.record_session_completion(RaceWeekendSession.RACE, results)
            self.mode = "WEEKEND"
        else:
            self.management_hub.on_race_completed(results)
            self.mode = "MANAGEMENT"

        self.tutorial_manager.sync_game_state(self.mode)

    def show_zoom_toast(self):

        self.zoom_toast_msg = f"UI ZOOM: {int(round(UITheme.UI_SCALE * 100))}%  (Press F9 / F8 to adjust)"
        self.zoom_toast_timer = 2.2

    def _on_admin_back(self):
        """Returns to Management Hub if career is active, otherwise to Start Screen."""
        if (
            hasattr(self, "management_hub")
            and getattr(self.management_hub, "gm", None)
            and getattr(self.management_hub.gm, "team_id", None)
        ):
            self.set_mode("MANAGEMENT")
        else:
            self.set_mode("START")

    def set_mode(self, mode: str):
        if mode == "EDITOR":
            mode = "ADMIN"
        self.previous_mode = getattr(self, "mode", "START")
        self.mode = mode
        if mode == "RACE":
            self.camera.fit_circuit(self.circuit, self.view_rect)

    def run(self):
        while self.is_running:
            dt = self.clock.tick(60) / 1000.0
            dt = min(0.1, dt)

            self.handle_events()
            self.update(dt)
            self.render()

        pygame.quit()
        sys.exit()

    def resize_all_components(self):
        """Re-initializes layout rects and propagates UI scaling to all sub-components and screens."""
        self._init_layout()
        self.start_screen.resize(self.width, self.height)
        self.management_hub.resize(self.width, self.height)
        self.admin_hub.resize(self.width, self.height)
        if self.weekend_screen:
            self.weekend_screen.resize(self.width, self.height)
        self.tutorial_overlay.resize(self.width, self.height)
        self.camera.fit_circuit(self.circuit, self.view_rect)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
                return

            if event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.w, event.h
                self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                UITheme.auto_detect_scale(self.width, self.height)
                self.resize_all_components()
                continue

            if event.type == pygame.KEYDOWN:
                # F9 or Ctrl +: Zoom In / Increase UI Scale for 4K/5K Ultrawide or Laptop Screens
                if event.key == pygame.K_F9 or (
                    (event.mod & pygame.KMOD_CTRL) and event.key in [pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS]
                ):
                    UITheme.adjust_scale(+0.10)
                    self.resize_all_components()
                    self.show_zoom_toast()
                    continue
                # F8 or Ctrl -: Zoom Out / Decrease UI Scale
                elif event.key == pygame.K_F8 or (
                    (event.mod & pygame.KMOD_CTRL) and event.key in [pygame.K_MINUS, pygame.K_KP_MINUS]
                ):
                    UITheme.adjust_scale(-0.10)
                    self.resize_all_components()
                    self.show_zoom_toast()
                    continue
                # F10: Reset to Auto-Detected Screen Scale
                elif event.key == pygame.K_F10:
                    UITheme.auto_detect_scale(self.width, self.height)
                    self.resize_all_components()
                    self.show_zoom_toast()
                    continue

            # Tutorial Overlay Event Interception (Only active in career modes: MANAGEMENT, WEEKEND, RACE)
            if self.mode in ["MANAGEMENT", "WEEKEND", "RACE"] and self.tutorial_overlay.handle_event(
                event, current_mode=self.mode
            ):
                if self.mode == "RACE" and self.sim:
                    cur_s = self.tutorial_manager.get_current_step()
                    if not self.tutorial_manager.is_active or not cur_s or cur_s.step_id != "LIVE_RACE_PITWALL":
                        self.sim.is_paused = False
                continue

            # Global Mode Switcher Tabs in top-right (Only active in RACE mode)
            if self.mode in ["RACE"] and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                tab_mgmt = pygame.Rect(self.width - 345, 10, 115, 26)
                tab_race = pygame.Rect(self.width - 225, 10, 105, 26)
                tab_admin = pygame.Rect(self.width - 115, 10, 105, 26)

                if tab_mgmt.collidepoint(mx, my):
                    self.mode = "MANAGEMENT"
                    continue
                elif tab_race.collidepoint(mx, my):
                    self.mode = "RACE"
                    self.camera.fit_circuit(self.circuit, self.view_rect)
                    continue
                elif tab_admin.collidepoint(mx, my):
                    self.mode = "ADMIN"
                    continue

                # Return to HQ button inside Race Mode (placed cleanly to the left of CAM button at width - 615)
                ret_btn = pygame.Rect(self.width - 775, 10, 145, 28)
                if ret_btn.collidepoint(mx, my):
                    self.return_to_management_hub()
                    continue

            # Route events to active mode
            if self.mode == "START":
                self.start_screen.handle_event(event)

            elif self.mode == "MANAGEMENT":
                self.management_hub.handle_event(event)

            elif self.mode == "ADMIN":
                self.admin_hub.handle_event(event)

            elif self.mode == "RACE":
                if not self.sim:
                    self.sim = Simulation(self.circuit, self.driver_car_pairs, total_laps=15)

                # Hotkeys for race simulation controls
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.sim.is_paused = not self.sim.is_paused
                        continue
                    elif event.key == pygame.K_1:
                        self.sim.is_paused = False
                        self.sim.sim_speed = 1.0
                        continue
                    elif event.key == pygame.K_2:
                        self.sim.is_paused = False
                        self.sim.sim_speed = 2.0
                        continue
                    elif event.key == pygame.K_3:
                        self.sim.is_paused = False
                        self.sim.sim_speed = 4.0
                        continue
                    elif event.key == pygame.K_4:
                        self.sim.is_paused = False
                        self.sim.sim_speed = 8.0
                        continue
                    elif event.key in (pygame.K_c, pygame.K_TAB):
                        if self.camera.mode == "TRACK_OVERVIEW":
                            player_cars = [c for c in self.sim.cars if c.driver.is_player]
                            target_car = player_cars[0] if player_cars else self.sim.cars[0]
                            self.camera.set_follow_car(target_car)
                        else:
                            self.camera.set_overview_mode(self.circuit)
                        continue
                    elif event.key == pygame.K_ESCAPE:
                        if self.pit_modal.is_open:
                            self.pit_modal.close()
                            continue

                # If race finished, handle finish banner button click
                if self.sim.race_finished and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    fin_btn_rect = pygame.Rect(self.width // 2 - 160, self.height // 2 + 20, 320, 42)
                    if fin_btn_rect.collidepoint(event.pos):
                        self.return_to_management_hub()
                        continue

                if self.pit_modal.is_open:
                    if self.pit_modal.handle_event(event):
                        continue

                if self.broadcast_header.handle_event(event, self.sim, self.camera):
                    continue

                if self.timing_tower.handle_event(event, self.sim, self.camera):
                    continue

                player_cars = [c for c in self.sim.cars if c.driver.is_player]
                self.driver_panel.handle_event(event, player_cars, league_tier=getattr(self.sim, "league_tier", 3))

            elif self.mode == "WEEKEND":
                if self.weekend_screen:
                    self.weekend_screen.handle_event(event)

    def update(self, dt: float):
        if self.zoom_toast_timer > 0:
            self.zoom_toast_timer -= dt

        if self.mode in ["MANAGEMENT", "WEEKEND", "RACE"]:
            self.tutorial_overlay.update(dt)

        if self.mode == "ADMIN":
            self.admin_hub.update(dt)

        elif self.mode == "RACE" and self.sim:
            self.sim.update(dt)
            self.camera.update(dt, self.view_rect)
            self.radio_banner.update(dt, self.width)

    def render(self):
        self.screen.fill(UITheme.BG_DARK)

        if self.mode == "START":
            self.start_screen.render(self.screen)

        elif self.mode == "MANAGEMENT":
            self.management_hub.render(self.screen)

        elif self.mode == "ADMIN":
            self.admin_hub.render(self.screen)

        elif self.mode == "WEEKEND":
            if self.weekend_screen:
                self.weekend_screen.render(self.screen)

        elif self.mode == "RACE":
            if not self.sim:
                self.sim = Simulation(self.circuit, self.driver_car_pairs, total_laps=15)

            # 1. Draw 2D Race Track & Open-Wheel Cars
            self.track_renderer.render(self.screen, self.circuit, self.camera, self.view_rect, self.sim.weather)
            self.car_renderer.render_cars(
                self.screen, self.sim.cars, self.camera, self.view_rect, safety_car=self.sim.race_control.safety_car
            )

            # 2. Draw Timing Tower & Leaderboard
            self.timing_tower.render(self.screen, self.sim, self.camera)

            # 3. Draw Broadcast Header
            self.broadcast_header.render(self.screen, self.sim, self.camera)

            # 4. Draw Driver Strategy Panel
            player_cars = [c for c in self.sim.cars if c.driver.is_player]
            self.driver_panel.render(self.screen, player_cars, league_tier=getattr(self.sim, "league_tier", 3))

            # 5. Draw Event Commentary Feed
            self.event_feed.render(self.screen, self.sim)

            # 6. Draw Team Radio / Pit Wall Message Banner Popup
            self.radio_banner.render(self.screen, self.sim.radio_system)

            # 7. Draw Pit Strategy Modal if open
            if self.pit_modal.is_open:
                self.pit_modal.render(self.screen)

            # Return to HQ button (positioned to left of CAM button at width - 615, completely clear of weather radar)
            ret_btn = pygame.Rect(self.width - 775, 10, 145, 28)
            font_b = UITheme.get_font(10, bold=True)
            UITheme.draw_button(self.screen, ret_btn, "< RETURN TO HQ", font_b, is_active=False)

            # 8. Prominent Chequered Flag Finish Overlay when session completes
            if self.sim and self.sim.race_finished:
                dim_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                dim_surf.fill((0, 0, 0, 120))
                self.screen.blit(dim_surf, (0, 0))

                banner_w = 480
                banner_h = 140
                bx = (self.width - banner_w) // 2
                by = (self.height - banner_h) // 2 - 20
                b_rect = pygame.Rect(bx, by, banner_w, banner_h)
                pygame.draw.rect(self.screen, (16, 22, 32), b_rect, border_radius=8)
                pygame.draw.rect(self.screen, (255, 215, 0), b_rect, width=2, border_radius=8)

                font_flag_title = UITheme.get_font(14, bold=True)
                font_winner = UITheme.get_font(11, bold=True)
                font_sub = UITheme.get_font(10, bold=False)
                font_btn_fin = UITheme.get_font(11, bold=True)

                lbl_flag = font_flag_title.render("🏁 CHEQUERED FLAG — RACE FINISHED! 🏁", True, (255, 215, 0))
                self.screen.blit(lbl_flag, (bx + (banner_w - lbl_flag.get_width()) // 2, by + 14))

                leader = self.sim.cars[0] if self.sim.cars else None
                win_text = (
                    f"Winner: {leader.driver.name} ({leader.driver.team_name})" if leader else "Session Completed"
                )
                lbl_win = font_winner.render(win_text, True, UITheme.TEXT_WHITE)
                self.screen.blit(lbl_win, (bx + (banner_w - lbl_win.get_width()) // 2, by + 42))

                fl_holder = getattr(self.sim, "fastest_lap_holder", None)
                fl_time = getattr(self.sim, "fastest_lap_time", 0.0)
                fl_str = (
                    f"Fastest Lap: {fl_holder.driver.name} ({self.sim.format_time(fl_time)})"
                    if fl_holder and fl_time < float("inf")
                    else "All laps completed."
                )
                lbl_fl = font_sub.render(fl_str, True, (180, 120, 255))
                self.screen.blit(lbl_fl, (bx + (banner_w - lbl_fl.get_width()) // 2, by + 62))

                fin_btn_rect = pygame.Rect(self.width // 2 - 160, self.height // 2 + 20, 320, 42)
                pygame.draw.rect(self.screen, (0, 180, 100), fin_btn_rect, border_radius=4)
                pygame.draw.rect(self.screen, (0, 255, 140), fin_btn_rect, width=2, border_radius=4)
                lbl_ret = font_btn_fin.render("< RETURN TO HQ & VIEW DEBRIEF", True, (10, 25, 15))
                self.screen.blit(
                    lbl_ret, (fin_btn_rect.x + (fin_btn_rect.width - lbl_ret.get_width()) // 2, fin_btn_rect.y + 12)
                )

        # Global Top Nav Mode Tabs (Only shown in Race Sim mode)
        if self.mode == "RACE":
            self._render_mode_tabs()

        # Render On-Screen Zoom Toast Notification if active
        if self.zoom_toast_timer > 0 and self.zoom_toast_msg:
            t_font = UITheme.get_font(11, bold=True)
            t_surf = t_font.render(self.zoom_toast_msg, True, (0, 240, 140))
            pill_w = t_surf.get_width() + 28
            pill_h = 26
            pill_rect = pygame.Rect((self.width - pill_w) // 2, 8, pill_w, pill_h)
            pygame.draw.rect(self.screen, (16, 24, 34), pill_rect, border_radius=13)
            pygame.draw.rect(self.screen, (0, 220, 255), pill_rect, width=1, border_radius=13)
            self.screen.blit(t_surf, (pill_rect.x + 14, pill_rect.y + 4))

        # Render Guided Tutorial Overlay topmost (Only in active career modes)
        if self.mode in ["MANAGEMENT", "WEEKEND", "RACE"]:
            self.tutorial_overlay.render(self.screen, current_mode=self.mode)

        pygame.display.flip()

    def _render_mode_tabs(self):
        tab_mgmt = pygame.Rect(self.width - 345, 10, 115, 26)
        tab_race = pygame.Rect(self.width - 225, 10, 105, 26)
        tab_admin = pygame.Rect(self.width - 115, 10, 105, 26)

        font_tab = UITheme.get_font(10, bold=True)

        UITheme.draw_button(self.screen, tab_mgmt, "HQ DASHBOARD", font_tab, is_active=(self.mode == "MANAGEMENT"))
        UITheme.draw_button(self.screen, tab_race, "RACE SIM", font_tab, is_active=(self.mode == "RACE"))
        UITheme.draw_button(self.screen, tab_admin, "ADMIN TOOLS", font_tab, is_active=(self.mode == "ADMIN"))


if __name__ == "__main__":
    app = RaceGameApp()
    app.run()
