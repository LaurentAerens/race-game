from typing import Any, Callable, Dict, List, Optional

import pygame

from ...database.career_db import CareerDatabase
from ...management.difficulty import DifficultyManager
from ...management.driver_manager import DriverManager
from ...management.engineering_manager import EngineeringManager
from ...management.game_manager import GameManager
from ...management.innovation_manager import InnovationManager
from ...management.league_simulator import LeagueSimulator
from ...management.sponsor_manager import SponsorManager
from ...management.workforce_manager import WorkforceManager
from .hub_header import HubHeader
from .season_finale_modal import SeasonFinaleModal
from .tab_car_engineering import CarEngineeringTab
from .tab_dashboard import DashboardTab
from .tab_database_explorer import DatabaseExplorerTab
from .tab_drivers_academy import DriversAcademyTab
from .tab_factory_tree import FactoryTreeTab
from .tab_personnel import PersonnelTab
from .tab_sponsors import SponsorsTab
from .tab_standings import StandingsTab
from .weekly_roundup_modal import WeeklyRoundupModal


class ManagementHub:
    """Master Management Hub UI Controller coordinating navigation, tabs, difficulty, and career lifecycle."""

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        on_start_race_weekend: Callable[[Dict[str, Any]], None],
        on_switch_mode: Optional[Callable[[str], None]] = None,
    ):
        self.width = screen_width
        self.height = screen_height
        self.on_start_race_weekend = on_start_race_weekend
        self.on_switch_mode = on_switch_mode

        # Managers
        self.db = CareerDatabase("career.db")
        self.gm = GameManager("career.db")
        self.em = EngineeringManager(self.db)
        self.im = InnovationManager(self.db)
        self.dm = DriverManager(self.db)
        self.wm = WorkforceManager(self.db)
        self.sm = SponsorManager(self.db)
        self.ls = LeagueSimulator(self.db)

        # Load saved difficulty from database
        player_team = self.db.get_player_team()
        saved_diff = player_team.get("difficulty", "NORMAL") if player_team else "NORMAL"
        self.difficulty_mgr = DifficultyManager(saved_diff)

        # Active tab state
        self.active_tab: str = "DASHBOARD"

        # UI Sub-components
        self.header = HubHeader(screen_width, on_cycle_difficulty=self._handle_cycle_difficulty)
        self.tab_dash = DashboardTab(
            screen_width,
            screen_height,
            on_start_race=self._handle_race_start_trigger,
            on_advance_week=self._handle_advance_week_trigger,
            on_open_roundup=self._handle_open_roundup_trigger,
        )
        self.tab_car = CarEngineeringTab(screen_width, screen_height)
        self.tab_factory = FactoryTreeTab(screen_width, screen_height)
        self.tab_drivers = DriversAcademyTab(
            screen_width, screen_height, on_view_driver_dossier=self._handle_view_driver_dossier
        )
        self.tab_sponsors = SponsorsTab(screen_width, screen_height)
        self.tab_workforce = PersonnelTab(screen_width, screen_height)
        self.tab_standings = StandingsTab(screen_width, screen_height)
        self.tab_db = DatabaseExplorerTab(screen_width, screen_height)

        # Weekly Roundup debrief modal
        self.roundup_modal = WeeklyRoundupModal(screen_width, screen_height)
        self.last_roundup_summary: Dict[str, Any] = {}

        # End of Season / Start Next Season Flow Modal
        self.season_finale_modal = SeasonFinaleModal(
            screen_width, screen_height, on_season_started=self._on_new_season_started
        )
        self.show_engine_negotiation_modal: bool = False

        # Tutorial integration reference
        self.tutorial_manager: Optional[Any] = None

    def switch_tab(self, tab_name: str):
        """Switches active hub tab programmatically."""
        valid = ["DASHBOARD", "CAR_RND", "FACTORY", "DRIVERS", "SPONSORS", "WORKFORCE", "STANDINGS", "DATABASE"]
        if tab_name in valid:
            self.active_tab = tab_name

    def _on_new_season_started(self):
        """Called when SeasonFinaleModal finalizes rollover into Season N+1."""
        self.gm.refresh_player_team()
        self.last_roundup_summary = {}
        self.active_tab = "DASHBOARD"

    def _handle_view_driver_dossier(self, driver_id: int):
        """Switches active hub view to Database Explorer and opens driver's dossier with return link."""
        self.tab_db.open_driver_profile(driver_id, return_hub_tab="DRIVERS")
        self.active_tab = "DATABASE"

    def _handle_cycle_difficulty(self) -> str:
        """Cycles difficulty level and immediately persists it to the database."""
        new_diff = self.difficulty_mgr.cycle_difficulty()
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE teams SET difficulty = ? WHERE is_player = 1;", (new_diff,))
            conn.commit()
        self.gm.refresh_player_team()
        return new_diff

    def resize(self, width: int, height: int):
        """Updates dimensions and propagates to all management tabs without resetting active state."""
        self.width = width
        self.height = height
        self.header.resize(width)
        for tab in [
            self.tab_dash,
            self.tab_car,
            self.tab_factory,
            self.tab_drivers,
            self.tab_sponsors,
            self.tab_workforce,
            self.tab_standings,
            self.tab_db,
        ]:
            tab.resize(width, height)
        self.roundup_modal.resize(width, height)
        self.season_finale_modal.resize(width, height)

    def _handle_race_start_trigger(self):
        """Called when player clicks 'START RACE WEEKEND >>'."""
        race_event = self.gm.get_current_race_event()
        self.on_start_race_weekend(race_event)

    def _handle_open_roundup_trigger(self):
        """Re-opens the weekly motorsport roundup modal."""
        if self.last_roundup_summary and self.last_roundup_summary.get("week", 0) >= 1:
            self.roundup_modal.open(self.last_roundup_summary)
            return

        prev_week = self.gm.current_week - 1
        if prev_week >= 1:
            res = self.db.get_weekly_race_results(prev_week)
            if res:
                summary = {
                    "week": prev_week,
                    "tiers_simulated": sorted(list(res.keys())),
                    "results_by_tier": res,
                    "academy_highlights": [],
                }
                self.roundup_modal.open(summary)
                return

        # Start of season / no races run yet
        summary = {
            "week": 1,
            "is_season_start": True,
            "tiers_simulated": [],
            "results_by_tier": {},
            "academy_highlights": [],
        }
        self.roundup_modal.open(summary)

    def _handle_advance_week_trigger(self):
        """Advances calendar week during non-race weeks, simulating active series and processing economics."""
        diff_cfg = self.difficulty_mgr.get_config()

        # 1. Simulate active series this week
        summary = self.ls.simulate_weekly_series(self.gm.current_week)
        self.last_roundup_summary = summary

        # 2. Advance weekly driver development (base training without race pos)
        self.dm.process_weekly_driver_development(
            self.gm.team_id, player_race_pos=None, driver_growth_mult=diff_cfg.get("driver_growth_mult", 1.0)
        )
        self.dm.simulate_feeder_market_turn(force_events=1)
        self.im.process_weekly_innovation_progress(self.gm.team_id)
        self.wm.process_weekly_workforce(self.gm.team_id)
        self.em.process_monthly_department_budgets(
            self.gm.team_id, upkeep_mult=diff_cfg["upkeep_mult"], cost_mult=diff_cfg.get("rnd_cost_mult", 1.0)
        )
        self.sm.check_and_generate_offers(self.gm.team_id, is_progression=True)

        # 3. Advance calendar week
        self.gm.advance_calendar_week()

        # 4. Check for season finale
        if self.gm.is_season_finale_ready():
            self.season_finale_modal.open(
                self.gm, self.ls, self.em, prize_cash_multiplier=diff_cfg.get("prize_cash_mult", 1.0)
            )
        else:
            # 5. Open roundup modal so player sees the action
            self.roundup_modal.open(summary)

    def handle_event(self, event: pygame.event.Event):
        # Mouse Wheel Events
        if event.type == pygame.MOUSEWHEEL:
            if self.active_tab == "WORKFORCE":
                self.tab_workforce.handle_scroll(event)
                return
            elif self.active_tab == "FACTORY" and hasattr(self.tab_factory, "handle_scroll"):
                self.tab_factory.handle_scroll(event)
                return
            elif self.active_tab == "DATABASE" and hasattr(self.tab_db, "handle_scroll"):
                self.tab_db.handle_scroll(event)
                return

        # Mouse Dragging / Scrollbar Dragging
        if self.active_tab == "FACTORY" and not self.season_finale_modal.is_open:
            self.tab_factory.handle_mouse_drag(event)
        elif self.active_tab == "WORKFORCE" and not self.season_finale_modal.is_open:
            if self.tab_workforce.handle_mouse_drag(event):
                return
            if event.type == pygame.MOUSEBUTTONDOWN and (event.button == 4 or event.button == 5):
                self.tab_workforce.handle_scroll(event)
                return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # Clicks inside Season Finale Modal
            if self.season_finale_modal.is_open:
                diff_cfg = self.difficulty_mgr.get_config()
                if self.season_finale_modal.handle_click(mx, my, self.gm, self.ls, self.em, diff_cfg):
                    return
                return

            # Clicks inside Weekly Roundup Modal
            if self.roundup_modal.is_open:
                if self.roundup_modal.handle_click(mx, my):
                    return
                return

            # Check Header Tabs & Difficulty click
            if self.header.rect.collidepoint(mx, my):
                tab_clicked = self.header.handle_click(mx, my)
                if tab_clicked == "ACTION_TUTORIAL":
                    if self.tutorial_manager:
                        if self.tutorial_manager.is_active:
                            self.tutorial_manager.skip_tutorial()
                        else:
                            self.tutorial_manager.restart_tutorial()
                    return
                elif tab_clicked == "MODE_EDITOR" and self.on_switch_mode:
                    self.on_switch_mode("EDITOR")
                    return
                elif tab_clicked and not tab_clicked.startswith("DIFF_"):
                    self.active_tab = tab_clicked
                    return

            # Route to Active Tab
            diff_cfg = self.difficulty_mgr.get_config()
            if self.active_tab == "DASHBOARD":
                self.tab_dash.handle_click(mx, my, self.gm, self.im)
            elif self.active_tab == "CAR_RND":
                msg_before = self.tab_car.status_message
                self.tab_car.handle_click(mx, my, self.gm, self.em, cost_mult=diff_cfg["parts_cost_mult"])
                if self.tutorial_manager and self.tab_car.status_message != msg_before:
                    car_msg = self.tab_car.status_message.lower()
                    if "mk" in car_msg or "built" in car_msg or "manufactured" in car_msg:
                        self.tutorial_manager.notify_action_completed("BUILD_FRONT_WING")
            elif self.active_tab == "FACTORY":
                msg_before = self.tab_factory.status_message
                self.tab_factory.handle_click(mx, my, self.gm, self.em, cost_mult=diff_cfg["factory_cost_mult"])
                if self.tutorial_manager and self.tab_factory.status_message != msg_before:
                    fac_msg = self.tab_factory.status_message.lower()
                    if "purchased" in fac_msg or "upgraded" in fac_msg or "equipped" in fac_msg or "bought" in fac_msg:
                        self.tutorial_manager.notify_action_completed("BUY_BRAKES_EQUIPMENT")
                if self.tab_factory.requested_hiring_target:
                    tgt_node, tgt_role, tgt_desc = self.tab_factory.requested_hiring_target
                    self.tab_factory.requested_hiring_target = None
                    self.tab_workforce.set_hiring_target(tgt_node, role=tgt_role, slot_desc=tgt_desc)
                    self.active_tab = "WORKFORCE"
            elif self.active_tab == "DRIVERS":
                msg_before = self.tab_drivers.status_message
                self.tab_drivers.handle_click(mx, my, self.gm, self.dm)
                if self.tutorial_manager and self.tab_drivers.status_message != msg_before:
                    d_msg = self.tab_drivers.status_message.lower()
                    if (
                        "signed" in d_msg
                        or "transferred" in d_msg
                        or "enrolled" in d_msg
                        or "contract" in d_msg
                        or "focus" in d_msg
                    ):
                        self.tutorial_manager.notify_action_completed("ENROLL_DRIVER")
            elif self.active_tab == "SPONSORS":
                msg_before = self.tab_sponsors.status_message
                self.tab_sponsors.handle_click(mx, my, self.gm, self.sm)
                if self.tutorial_manager and self.tab_sponsors.status_message != msg_before:
                    sp_msg = self.tab_sponsors.status_message.lower()
                    if "signed" in sp_msg or "contract" in sp_msg or "accepted" in sp_msg:
                        self.tutorial_manager.notify_action_completed("SIGN_SPONSOR")
            elif self.active_tab == "WORKFORCE":
                msg_before = self.tab_workforce.status_message
                self.tab_workforce.handle_click(mx, my, self.gm, self.em)
                if self.tutorial_manager and self.tab_workforce.status_message != msg_before:
                    wf_msg = self.tab_workforce.status_message.lower()
                    if "hired" in wf_msg or "signed" in wf_msg or "assigned" in wf_msg or "appointed" in wf_msg:
                        self.tutorial_manager.notify_action_completed("HIRE_STAFF")

            elif self.active_tab == "STANDINGS":
                self.tab_standings.handle_click(mx, my, self.gm)
            elif self.active_tab == "DATABASE":
                self.tab_db.handle_click(mx, my, self.gm)
                if self.tab_db.return_hub_tab_requested:
                    self.active_tab = self.tab_db.return_hub_tab_requested
                    self.tab_db.return_hub_tab_requested = None

    def on_race_completed(self, results: List[Dict[str, Any]]):
        """Processes race results returned from 2D race simulator."""
        player_res = [r for r in results if r.get("is_player", False)]
        pos = player_res[0].get("position", 10) if player_res else 10

        # Prize money
        diff_cfg = self.difficulty_mgr.get_config()
        prize_pot = {
            1: 800000,
            2: 500000,
            3: 350000,
            4: 250000,
            5: 180000,
            6: 120000,
            7: 80000,
            8: 50000,
            9: 30000,
            10: 20000,
        }.get(pos, 10000)
        prize_pot = prize_pot * diff_cfg["sponsor_cash_mult"]

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE teams SET cash = cash + ? WHERE id = ?;", (prize_pot, self.gm.team_id))
            cur.execute(
                """
            INSERT INTO ledger (team_id, week, category, description, amount)
            VALUES (?, ?, 'PRIZE_MONEY', ?, ?);
            """,
                (
                    self.gm.team_id,
                    self.gm.current_week,
                    f"Race R{self.gm.current_round} Finish P{pos} Prize Money",
                    prize_pot,
                ),
            )

            # Decrement engine contract race counter
            cur.execute(
                """
            UPDATE teams 
            SET engine_contract_races_left = MAX(0, engine_contract_races_left - 1)
            WHERE id = ?;
            """,
                (self.gm.team_id,),
            )
            conn.commit()

        # Process Sponsor per-race fixed payments and objective bonuses
        self.sm.process_post_race_sponsor_payouts(self.gm.team_id, pos)
        self.sm.check_and_generate_offers(self.gm.team_id, is_progression=True)

        # Telemetry knowledge feedback (scaled by difficulty)
        drivers = self.db.get_team_drivers(self.gm.team_id)
        d_tech = drivers[0]["technical_understanding"] if drivers else 60
        d_comm = drivers[0]["communication"] if drivers else 60
        self.em.process_post_race_telemetry(
            self.gm.team_id,
            d_tech,
            d_comm,
            dev_gain_mult=diff_cfg.get("dev_gain_mult", 1.0),
            negative_penalty_mult=diff_cfg.get("negative_penalty_mult", 1.0),
        )

        # Advance background championship sim across all active series for this week
        summary = self.ls.simulate_weekly_series(self.gm.current_week, player_race_results=player_res)
        self.last_roundup_summary = summary

        # Weekly driver development, department budgets, & innovation progress
        self.dm.process_weekly_driver_development(
            self.gm.team_id, player_race_pos=pos, driver_growth_mult=diff_cfg.get("driver_growth_mult", 1.0)
        )
        self.dm.simulate_feeder_market_turn(force_events=1)
        self.im.process_weekly_innovation_progress(self.gm.team_id)
        self.wm.process_weekly_workforce(self.gm.team_id)
        self.em.process_monthly_department_budgets(
            self.gm.team_id, upkeep_mult=diff_cfg["upkeep_mult"], cost_mult=diff_cfg.get("rnd_cost_mult", 1.0)
        )

        # Roll & generate R&D proposals post-race scaled by career difficulty
        fin = self.gm.get_financial_summary()
        self.im.check_and_generate_proposals(
            self.gm.team_id,
            workforce_count=fin["staff_count"],
            cost_mult=diff_cfg["rnd_cost_mult"],
            rate_mult=diff_cfg.get("innovation_rate_mult", 1.0),
            success_mult=diff_cfg.get("innovation_success_mult", 1.0),
            gain_mult=diff_cfg.get("innovation_gain_mult", 1.0),
        )

        # Advance calendar round & week
        self.gm.advance_to_next_race_round()
        self.gm.advance_calendar_week()

        # Check if season finished (completed all rounds or week limit reached)
        if self.gm.is_season_finale_ready():
            self.season_finale_modal.open(
                self.gm, self.ls, self.em, prize_cash_multiplier=diff_cfg.get("prize_cash_mult", 1.0)
            )
        else:
            # Open weekly roundup modal with race results across all tiers
            self.roundup_modal.open(summary)

    def render(self, surface: pygame.Surface):
        # Background fill
        surface.fill((10, 14, 18))

        # Render Header
        fin = self.gm.get_financial_summary()
        self.header.render(
            surface,
            self.active_tab,
            self.gm.player_team,
            fin,
            self.gm.current_round,
            self.gm.total_rounds,
            difficulty=self.difficulty_mgr.current_difficulty,
        )

        diff_cfg = self.difficulty_mgr.get_config()

        # Render Active Tab Content
        if self.active_tab == "DASHBOARD":
            self.tab_dash.render(surface, self.gm, self.im, rnd_cost_mult=diff_cfg["rnd_cost_mult"])
        elif self.active_tab == "CAR_RND":
            self.tab_car.render(surface, self.gm, self.em, cost_mult=diff_cfg["parts_cost_mult"])
        elif self.active_tab == "FACTORY":
            self.tab_factory.render(
                surface,
                self.gm,
                self.em,
                cost_mult=diff_cfg["factory_cost_mult"],
                upkeep_mult=diff_cfg["upkeep_mult"],
                dev_gain_mult=diff_cfg.get("dev_gain_mult", 1.0),
                negative_penalty_mult=diff_cfg.get("negative_penalty_mult", 1.0),
            )
        elif self.active_tab == "DRIVERS":
            self.tab_drivers.render(surface, self.gm, self.dm)
        elif self.active_tab == "SPONSORS":
            self.tab_sponsors.render(surface, self.gm, self.sm)
        elif self.active_tab == "WORKFORCE":
            self.tab_workforce.render(surface, self.gm, self.em, dev_gain_mult=diff_cfg.get("dev_gain_mult", 1.0))
        elif self.active_tab == "STANDINGS":
            self.tab_standings.render(surface, self.gm)
        elif self.active_tab == "DATABASE":
            self.tab_db.render(surface, self.gm)

        # =====================================================================
        # Render Season Finale / New Season Transition Modal
        # =====================================================================
        if self.season_finale_modal.is_open:
            self.season_finale_modal.render(surface, self.gm)

        # =====================================================================
        # Render Weekly Motorsport Debrief Modal
        # =====================================================================
        elif self.roundup_modal.is_open:
            self.roundup_modal.render(surface)
