"""
Guided Tutorial Manager coordinating state machine, interactive objectives,
rewards, database persistence, and cross-screen synchronization.
"""

from dataclasses import dataclass
from typing import Any, Callable, List, Optional


@dataclass
class TutorialStep:
    step_id: str
    phase: str  # 'FACTORY' or 'RACE_WEEKEND'
    required_mode: str  # 'MANAGEMENT', 'WEEKEND', 'RACE'
    required_tab: Optional[str]  # 'DASHBOARD', 'FACTORY', 'CAR_RND', 'WORKFORCE', 'DRIVERS', 'SPONSORS'
    speaker_name: str
    speaker_role: str
    title: str
    body: str
    target_element_key: str
    action_label: str = "Next >>"
    reward_note: str = ""
    bonus_amount: float = 0.0
    interactive_action: Optional[str] = (
        None  # 'BUY_BRAKES_EQUIPMENT', 'HIRE_STAFF', 'BUILD_FRONT_WING', 'ENROLL_DRIVER', 'SIGN_SPONSOR'
    )
    objective: str = ""
    lore_briefing: str = ""

    def get_objective(self) -> str:
        if self.objective:
            return self.objective
        lines = [s.strip() for s in self.body.split("\n") if s.strip()]
        return lines[-1] if lines else self.title

    def get_lore(self) -> str:
        return self.lore_briefing or self.body


TUTORIAL_STEPS: List[TutorialStep] = [
    # -------------------------------------------------------------------------
    # 1. Welcome to Factory / HQ Dashboard
    # -------------------------------------------------------------------------
    TutorialStep(
        step_id="WELCOME_DASHBOARD",
        phase="FACTORY",
        required_mode="MANAGEMENT",
        required_tab="DASHBOARD",
        speaker_name="Maya Torres",
        speaker_role="SPORTING DIRECTOR",
        title="Welcome to Headquarters, Boss!",
        body=(
            "Welcome to the team! As our new Team Principal, you are in charge of steering our operations "
            "in the National Open Cup (Tier 3). On this Dashboard, you can track upcoming Grand Prix events, "
            "active sponsor targets, monthly cash flow, and innovation proposals.\n\n"
            "Let's take a hands-on tour of your factory and prepare our cars for Round 1!"
        ),
        objective="Inspect upcoming Round 1 at Emerald Ring on your Grand Prix calendar.",
        lore_briefing=(
            "Welcome to the team! As our new Team Principal, you are in charge of steering our operations "
            "in the National Open Cup (Tier 3). On this Dashboard, you can track upcoming Grand Prix events, "
            "active sponsor targets, monthly cash flow, and innovation proposals."
        ),
        target_element_key="tab_dashboard_gp",
        action_label="Tour Factory >>",
    ),
    # -------------------------------------------------------------------------
    # 2. Factory Facilities & Equipment (Brakes Facility)
    # -------------------------------------------------------------------------
    TutorialStep(
        step_id="FACTORY_BRAKES_EQUIPMENT",
        phase="FACTORY",
        required_mode="MANAGEMENT",
        required_tab="FACTORY",
        speaker_name="Marcus Vance",
        speaker_role="CHIEF OPERATIONS OFFICER",
        title="Factory Facilities: Upgrading Brakes",
        body=(
            "This is your industrial Tech Tree. Facilities upgrade your team's R&D output, manufacturing tolerances, "
            "and pit stop efficiency. In particular, notice our Brakes Workshop ('eng_brakes').\n\n"
            "Click into the Brakes node, inspect its specialized equipment, and purchase or upgrade an item. "
            "The Board will subsidize the purchase as an initial equipment grant!"
        ),
        objective="Open the Brakes node ('eng_brakes') and purchase any specialized equipment.",
        lore_briefing=(
            "Facilities upgrade team R&D output, manufacturing tolerances, and pit stop speed. "
            "The Brakes Workshop specializes in high decel bite and stability for heavy braking circuits."
        ),
        target_element_key="tab_factory_node",
        action_label="Next: Personnel >>",
        reward_note="🎁 Reward: +$800,000 Board Grant (Equipment Subsidy)",
        bonus_amount=800000.0,
        interactive_action="BUY_BRAKES_EQUIPMENT",
    ),
    # -------------------------------------------------------------------------
    # 3. Personnel & Inbound Recruitment
    # -------------------------------------------------------------------------
    TutorialStep(
        step_id="PERSONNEL_HIRING",
        phase="FACTORY",
        required_mode="MANAGEMENT",
        required_tab="WORKFORCE",
        speaker_name="Rachel Adams",
        speaker_role="HEAD OF HUMAN RESOURCES",
        title="Personnel: Recruiting Staff",
        body=(
            "A world-class racing team is powered by elite engineers and craftsmen! In the Personnel tab, "
            "you appoint Category Directors, Department Heads, and assign staff to desks.\n\n"
            "Switch to the Recruitment sub-tab to inspect inbound applicants. Hire a candidate to "
            "strengthen our department roster. The Board has authorized an onboarding stipend!"
        ),
        objective="Switch to Recruitment and hire a qualified candidate for our open department desk.",
        lore_briefing=(
            "A world-class racing team is powered by elite engineers and craftsmen! "
            "Appoint Category Directors, Department Heads, and assign specialist engineers to desks to boost development."
        ),
        target_element_key="tab_personnel_recruitment",
        action_label="Next: Car R&D >>",
        reward_note="🎁 Reward: +$15,000 Board Grant (Recruitment Allowance)",
        bonus_amount=15000.0,
        interactive_action="HIRE_STAFF",
    ),
    # -------------------------------------------------------------------------
    # 4. Car Engineering & Front Wing Mk II Build
    # -------------------------------------------------------------------------
    TutorialStep(
        step_id="CAR_RND_FRONT_WING",
        phase="FACTORY",
        required_mode="MANAGEMENT",
        required_tab="CAR_RND",
        speaker_name="Dr. Aris Thorne",
        speaker_role="CHIEF TECHNICAL OFFICER",
        title="Car R&D: Build Front Wing Mk II",
        body=(
            "In Tier 3, engines and suspensions are spec-regulated, but BRAKES and FRONT WINGS are open "
            "for custom constructor development! As your cars complete laps, Continuous Evolution Knowledge builds up.\n\n"
            "We've seeded initial aero data for Car #1. Click 'BUILD NEXT GEN' on the Front Wing to manufacture "
            "our Mk II specification. The Board will sponsor this prototype build!"
        ),
        objective="Select Front Wing on the chassis and click 'BUILD NEXT GEN' to produce Mk II.",
        lore_briefing=(
            "In Tier 3, engines and suspensions are spec-regulated, but BRAKES and FRONT WINGS are open "
            "for custom constructor development! As your cars complete laps, Continuous Evolution Knowledge builds up."
        ),
        target_element_key="car_rnd_front_wing",
        action_label="Next: Drivers >>",
        reward_note="🎁 Reward: +$125,000 Board Grant (Aero Prototype Subsidy)",
        bonus_amount=125000.0,
        interactive_action="BUILD_FRONT_WING",
    ),
    # -------------------------------------------------------------------------
    # 5. Drivers & Junior Academy Feeder Seat
    # -------------------------------------------------------------------------
    TutorialStep(
        step_id="DRIVERS_ACADEMY",
        phase="FACTORY",
        required_mode="MANAGEMENT",
        required_tab="DRIVERS",
        speaker_name="Elena Rostova",
        speaker_role="DRIVER ACADEMY DIRECTOR",
        title="Drivers & Young Driver Academy",
        body=(
            "Your drivers possess distinct driving styles ('Late Braker', 'Tire Whisperer') and attributes "
            "(Pace, Braking, Consistency, Tire Management, Wet Weather). Set their Training Focus to shape their growth.\n\n"
            "In the Academy / Scouts sub-tab, you can sign promising youth talents into Tier 5 Karting feeder seats "
            "to develop tomorrow's champions. The Board will fund a youth scholarship!"
        ),
        objective="Open the Scouts sub-tab and enroll a youth talent into a Tier 5 Karting seat.",
        lore_briefing=(
            "Drivers possess distinct driving styles and attribute matrices. Setting Training Focus shapes their growth. "
            "Young drivers placed into feeder seats develop skills weekly and sign with an 80% homegrown salary discount."
        ),
        target_element_key="drivers_academy_scouts",
        action_label="Next: Sponsors >>",
        reward_note="🎁 Reward: +$30,000 Board Grant (Youth Scholarship)",
        bonus_amount=30000.0,
        interactive_action="ENROLL_DRIVER",
    ),
    # -------------------------------------------------------------------------
    # 6. Commercial Sponsors & Retainers
    # -------------------------------------------------------------------------
    TutorialStep(
        step_id="SPONSORS_COMMERCIAL",
        phase="FACTORY",
        required_mode="MANAGEMENT",
        required_tab="SPONSORS",
        speaker_name="Julian Cole",
        speaker_role="COMMERCIAL DIRECTOR",
        title="Commercial: Sponsors & Retainers",
        body=(
            "Motorsport is expensive — facility upkeeps, engine leases, and wages require positive cash flow! "
            "In the Sponsors tab, you manage Title, Secondary, and Minor sponsor slots.\n\n"
            "Review incoming offers and sign a corporate contract to secure guaranteed weekly retainers "
            "and race-day performance bonuses. High finishes elevate your team's Sponsor Appeal!"
        ),
        objective="Review incoming commercial offers and sign a contract to secure weekly cash flow.",
        lore_briefing=(
            "Motorsport is expensive — facility upkeeps, engine leases, and wages require positive cash flow! "
            "Sign corporate contracts to secure guaranteed weekly retainers and race-day finish bonuses."
        ),
        target_element_key="sponsors_offers",
        action_label="Next: Race Weekend >>",
        reward_note="🎁 Reward: +$25,000 Board Grant (Commercial Signing Bonus)",
        bonus_amount=25000.0,
        interactive_action="SIGN_SPONSOR",
    ),
    # -------------------------------------------------------------------------
    # 7. Launch Race Weekend Round 1
    # -------------------------------------------------------------------------
    TutorialStep(
        step_id="LAUNCH_WEEKEND",
        phase="FACTORY",
        required_mode="MANAGEMENT",
        required_tab="DASHBOARD",
        speaker_name="Maya Torres",
        speaker_role="SPORTING DIRECTOR",
        title="Ready for Round 1!",
        body=(
            "Our factory is humming, the Mk II front wing is installed, and the haulers are loaded for Round 1! "
            "When you're ready to head trackside, click 'START RACE WEEKEND >>' to travel to the circuit.\n\n"
            "We'll see you on the pit wall!"
        ),
        objective="Click 'START RACE WEEKEND >>' on the dashboard to travel to the circuit.",
        lore_briefing=(
            "Our factory is humming, the Mk II front wing is installed, and the haulers are loaded for Round 1! "
            "Heading trackside initiates the interactive Free Practice, Qualifying, and Sprint race sessions."
        ),
        target_element_key="btn_start_race",
        action_label="Go Trackside >>",
    ),
    # -------------------------------------------------------------------------
    # 8. Race Weekend: Free Practice & Setup Tuning
    # -------------------------------------------------------------------------
    TutorialStep(
        step_id="WEEKEND_PRACTICE",
        phase="RACE_WEEKEND",
        required_mode="WEEKEND",
        required_tab=None,
        speaker_name="Declan Ward",
        speaker_role="SENIOR RACE ENGINEER",
        title="Free Practice & Setup Tuning",
        body=(
            "Welcome trackside! Tier 3 race weekends run: FP1 -> FP2 -> Qualifying -> Sprint.\n\n"
            "Use the sliders to dial in Front/Rear Wings, Suspension, Gear Ratios, and Brake Bias. "
            "Choose a Practice Plan (Balanced, Fast Lap, Sprint Stints, Long Runs) and click 'RUN PRACTICE RUN' "
            "to complete 5 laps. Driver feedback builds Setup Confidence, boosting pace across the weekend!"
        ),
        objective="Adjust setup sliders, pick a Practice Plan, and click 'RUN PRACTICE RUN' for telemetry.",
        lore_briefing=(
            "Tier 3 race weekends run: FP1 -> FP2 -> Qualifying -> Sprint. "
            "Dialing in setup sliders and running practice stints builds Setup Confidence, boosting lap pace across the weekend."
        ),
        target_element_key="weekend_practice_sliders",
        action_label="Next: Qualifying >>",
    ),
    # -------------------------------------------------------------------------
    # 9. Race Weekend: Qualifying Shootout
    # -------------------------------------------------------------------------
    TutorialStep(
        step_id="WEEKEND_QUALIFYING",
        phase="RACE_WEEKEND",
        required_mode="WEEKEND",
        required_tab=None,
        speaker_name="Declan Ward",
        speaker_role="SENIOR RACE ENGINEER",
        title="Qualifying: Setting the Grid",
        body=(
            "Practice is done! Qualifying is a 3-lap shootout where single-lap speed, driver bravery, and "
            "setup confidence determine the starting grid for the Sprint race.\n\n"
            "Click 'SIMULATE QUALIFYING' to run the shootout and see where our cars start on the grid!"
        ),
        objective="Click 'SIMULATE QUALIFYING' to run the shootout and lock in grid positions.",
        lore_briefing=(
            "Qualifying is a 3-lap shootout where single-lap speed, driver bravery, and "
            "setup confidence determine starting grid positions for the Sprint race."
        ),
        target_element_key="weekend_qualifying_btn",
        action_label="Next: Sprint Strategy >>",
    ),
    # -------------------------------------------------------------------------
    # 10. Live Sprint Race & Pit Wall Strategy
    # -------------------------------------------------------------------------
    TutorialStep(
        step_id="LIVE_RACE_PITWALL",
        phase="RACE_WEEKEND",
        required_mode="RACE",
        required_tab=None,
        speaker_name="Maya Torres",
        speaker_role="CHIEF STRATEGIST",
        title="Live Pit Wall Command",
        body=(
            "The simulation is currently PAUSED so you can get your bearings:\n\n"
            "• Driver Strategy Panel (Bottom): Toggle PACE between NORMAL and PUSH. Watch tyre deg and "
            "component health (FW/RW/BRK/ENG — reaching 0% causes instant retirement!).\n"
            "• Fuel: Starts at 50 kg. There is NO refueling during pit stops!\n"
            "• Pit Stops: Click 'BOX' to queue fresh tyres or emergency repairs.\n"
            "• Controls: Space = Pause, 1-4 = Sim Speed, Tab/C = Follow Car.\n\n"
            "Click 'Start Racing! >>' to unleash the cars and guide them to the chequered flag!"
        ),
        objective="Manage driver pace (Normal/Push), monitor tyre wear, and click 'Start Racing!'.",
        lore_briefing=(
            "Live Pit Wall Command:\n"
            "• Strategy Panel: Toggle PACE between NORMAL and PUSH. Watch tyre deg and component health.\n"
            "• Fuel: Starts at 50 kg. No refueling during pit stops!\n"
            "• Pit Stops: Click 'BOX' to queue fresh tyres or emergency repairs."
        ),
        target_element_key="race_driver_panel",
        action_label="Start Racing! >>",
    ),
    # -------------------------------------------------------------------------
    # 11. Race Debrief & Tutorial Finale
    # -------------------------------------------------------------------------
    TutorialStep(
        step_id="RACE_DEBRIEF",
        phase="RACE_WEEKEND",
        required_mode="MANAGEMENT",
        required_tab="DASHBOARD",
        speaker_name="Maya Torres",
        speaker_role="SPORTING DIRECTOR",
        title="Tutorial Complete: You're Ready to Lead!",
        body=(
            "Outstanding drive! You have completed your first race weekend as Team Principal.\n\n"
            "Championship points have been awarded, prize money distributed, and driver experience earned. "
            "Continue upgrading facilities, engineering new parts, balancing cash flow, and chase the "
            "Tier 3 Championship for promotion to Tier 2!\n\n"
            "You can reopen this tutorial at any time by clicking '? TUTORIAL' in the top header bar."
        ),
        objective="Review race classifications, driver points, and prize payouts, then complete tutorial.",
        lore_briefing=(
            "Outstanding drive! You have completed your maiden race weekend as Team Principal. "
            "Championship points have been awarded, prize money distributed, and driver experience earned. "
            "Reopen this tutorial at any time by clicking '? TUTORIAL' in the top header bar."
        ),
        target_element_key="hub_header_tutorial_btn",
        action_label="Complete Tutorial & Continue Career",
        reward_note="🎁 Reward: +$100,000 Board Grant (Maiden GP Completion Award)",
        bonus_amount=100000.0,
    ),
]


class TutorialManager:
    """
    Manages the tutorial progression, step state, user actions, cash rewards,
    and coordination between UI screens and database persistence.
    """

    def __init__(
        self,
        db: Any,
        team_id: int = 21,
        on_switch_tab: Optional[Callable[[str], None]] = None,
        on_step_changed: Optional[Callable[[TutorialStep], None]] = None,
    ):
        self.db = db
        self.team_id = team_id
        self.on_switch_tab = on_switch_tab
        self.on_step_changed = on_step_changed

        self.current_step_index: int = 0
        self.is_active: bool = False
        self.is_completed: bool = False
        self.is_skipped: bool = False

        self.claimed_rewards: set = set()
        self.load_state()

    def load_state(self):
        """Loads tutorial progress from database if present."""
        if not self.db:
            return
        try:
            prog = self.db.get_tutorial_progress(self.team_id)
            if prog:
                step_id = prog.get("current_step_id", "WELCOME_DASHBOARD")
                self.current_step_index = self._get_step_index_by_id(step_id)
                self.is_active = bool(prog.get("is_active", 1))
                self.is_completed = bool(prog.get("is_completed", 0))
                self.is_skipped = bool(prog.get("is_skipped", 0))
            else:
                self.current_step_index = 0
                self.is_active = False
                self.is_completed = False
                self.is_skipped = False
        except Exception:
            self.current_step_index = 0
            self.is_active = False
            self.is_completed = False
            self.is_skipped = False

    def save_state(self):
        """Persists current state to database."""
        if not self.db:
            return
        step = self.get_current_step()
        step_id = step.step_id if step else "WELCOME_DASHBOARD"
        try:
            self.db.save_tutorial_progress(self.team_id, step_id, self.is_active, self.is_completed, self.is_skipped)
        except Exception:
            # Fallback if DB saving fails (e.g. table not migrated or closed connection)
            pass

    def _get_step_index_by_id(self, step_id: str) -> int:
        for idx, s in enumerate(TUTORIAL_STEPS):
            if s.step_id == step_id:
                return idx
        return 0

    def get_current_step(self) -> Optional[TutorialStep]:
        if 0 <= self.current_step_index < len(TUTORIAL_STEPS):
            return TUTORIAL_STEPS[self.current_step_index]
        return None

    def get_total_steps(self) -> int:
        return len(TUTORIAL_STEPS)

    def next_step(self):
        """Advances to the next tutorial step and awards any step reward."""
        curr_step = self.get_current_step()
        if curr_step and curr_step.bonus_amount > 0 and curr_step.step_id not in self.claimed_rewards:
            self._award_step_reward(curr_step)

        if self.current_step_index < len(TUTORIAL_STEPS) - 1:
            self.current_step_index += 1
            new_step = self.get_current_step()
            # If new step specifies a tab, auto-switch to it
            if new_step and new_step.required_tab and self.on_switch_tab:
                self.on_switch_tab(new_step.required_tab)
            if new_step and self.on_step_changed:
                self.on_step_changed(new_step)
            self.save_state()
        else:
            # Reached the end!
            self.is_active = False
            self.is_completed = True
            self.save_state()

    def prev_step(self):
        """Returns to the previous tutorial step."""
        if self.current_step_index > 0:
            self.current_step_index -= 1
            prev_step = self.get_current_step()
            if prev_step and prev_step.required_tab and self.on_switch_tab:
                self.on_switch_tab(prev_step.required_tab)
            if prev_step and self.on_step_changed:
                self.on_step_changed(prev_step)
            self.save_state()

    def skip_tutorial(self):
        """Instantly dismisses the tutorial without penalizing the player."""
        self.is_active = False
        self.is_skipped = True
        self.save_state()

    def restart_tutorial(self):
        """Restarts the tutorial from Step 1."""
        self.current_step_index = 0
        self.is_active = True
        self.is_completed = False
        self.is_skipped = False
        self.claimed_rewards.clear()
        if self.db:
            try:
                self.db.reset_tutorial_progress(self.team_id)
            except Exception:
                # Silently ignore DB reset errors in transient or uninitialized test environments
                pass
        first_step = self.get_current_step()
        if first_step and first_step.required_tab and self.on_switch_tab:
            self.on_switch_tab(first_step.required_tab)
        if first_step and self.on_step_changed:
            self.on_step_changed(first_step)
        self.save_state()

    def notify_action_completed(self, action_type: str):
        """Called when an interactive player action (e.g. buying equipment, building wing) occurs."""
        curr_step = self.get_current_step()
        if not curr_step or not self.is_active:
            return

        if curr_step.interactive_action == action_type:
            # Award bonus and advance step
            self._award_step_reward(curr_step)
            self.next_step()

    def _award_step_reward(self, step: TutorialStep):
        """Credits cash grant to team and marks reward as claimed."""
        if step.step_id in self.claimed_rewards or step.bonus_amount <= 0:
            return
        self.claimed_rewards.add(step.step_id)
        if self.db:
            try:
                self.db.add_team_cash(
                    self.team_id,
                    step.bonus_amount,
                    category="BOARD_GRANT",
                    description=f"Tutorial Incentive: {step.title}",
                )
            except Exception:
                # Silently ignore failure to credit reward if DB transaction fails
                pass

    def sync_game_state(self, current_mode: str, current_tab: Optional[str] = None):
        """
        Synchronizes tutorial with game mode transitions.
        For instance, when entering WEEKEND or RACE, ensures relevant step is shown.
        """
        if not self.is_active:
            return

        curr_step = self.get_current_step()
        if not curr_step:
            return

        # If we entered WEEKEND mode and we were on any factory step, advance to WEEKEND_PRACTICE
        if current_mode == "WEEKEND":
            if curr_step.phase == "FACTORY" or curr_step.step_id in ["LAUNCH_WEEKEND", "WELCOME_DASHBOARD"]:
                self.current_step_index = self._get_step_index_by_id("WEEKEND_PRACTICE")
                self.save_state()

        # If we entered RACE mode, advance to LIVE_RACE_PITWALL
        elif current_mode == "RACE":
            if curr_step.step_id != "LIVE_RACE_PITWALL":
                self.current_step_index = self._get_step_index_by_id("LIVE_RACE_PITWALL")
                self.save_state()

        # If in MANAGEMENT mode after race completion, show debrief
        elif current_mode == "MANAGEMENT":
            if curr_step.step_id in ["LIVE_RACE_PITWALL", "WEEKEND_QUALIFYING", "WEEKEND_PRACTICE"]:
                self.current_step_index = self._get_step_index_by_id("RACE_DEBRIEF")
                self.save_state()
