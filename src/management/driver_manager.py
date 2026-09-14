import random
from typing import Any, Dict, List, Optional, Tuple

from ..data.balance_config import BALANCE_REGISTRY
from ..database.career_db import CareerDatabase

TRAINING_FOCUS_OPTIONS = [
    ("BALANCED", "Balanced All-Round Training"),
    ("STARTS", "Race Starts & Launch Traction (+25% XP)"),
    ("BRAKING", "Braking & Late Apex (+25% XP)"),
    ("PACE", "Raw Single-Lap Pace (+25% XP)"),
    ("TIRES", "Tire Management & Preservation (+25% XP)"),
    ("DEFENDING", "Overtake Defense & Positioning (+25% XP)"),
    ("TECHNICAL", "Technical Understanding (+25% XP)"),
    ("COMMUNICATION", "Communication & Setup Radio (+25% XP)"),
]

FIRST_NAMES = [
    "Leo",
    "Kai",
    "Matteo",
    "Lucas",
    "Liam",
    "Noah",
    "Oliver",
    "Arthur",
    "Gabriel",
    "Oscar",
    "Max",
    "Carlos",
    "Lando",
    "Charles",
    "Lewis",
    "George",
    "Pierre",
    "Esteban",
    "Alexander",
    "Yuki",
]
LAST_NAMES = [
    "Moreno",
    "Tanaka",
    "Vasseur",
    "Novak",
    "Lindqvist",
    "Dubois",
    "Ferrari",
    "Schneider",
    "Sato",
    "Raikkonen",
    "Norris",
    "Leclerc",
    "Russell",
    "Sainz",
    "Piastri",
    "Albon",
    "Tsunoda",
    "Gasly",
    "Ocon",
    "Verstappen",
]
NATIONALITIES = ["GBR", "FRA", "GER", "ITA", "ESP", "JPN", "NED", "AUS", "FIN", "BRA", "USA", "CAN"]

# 11 Driver Attributes Matrix: 8 Driving (Parabolic Aging Curve) + 3 Mental (Can Only Go Up)
DRIVING_STATS = [
    "pace",
    "braking",
    "tire_management",
    "race_starts",
    "consistency",
    "defending",
    "wet_weather",
    "fuel_efficiency",
]

MENTAL_STATS = ["technical_understanding", "communication", "marketability"]

ALL_STATS = DRIVING_STATS + MENTAL_STATS

# Complete 10-Team Feeder Catalog with authentic Asymmetric Team Business Models & Entry Rules
# Cost spread: A bottom team is 2x to 4.5x cheaper than a top team in the same tier!
# Expected Pos: Expected placement within tier grid (Team ranking out of 10)
FEEDER_TEAMS_CATALOG: Dict[int, List[Dict[str, Any]]] = {
    # Tier 5: Karting Masters Academy (Grassroots Feeder, Min Age 14, 3 Seats / Team, 10 Teams)
    5: [
        {
            "tier": 5,
            "team_name": "KMA Elite Alpha",
            "league_name": "Tier 5 Karting Masters",
            "rating": 5,
            "expected_pos": "P1 / 10",
            "perf": 96,
            "base_cost": 95000.0,
            "pricing_model": "PRESTIGE",
            "pricing_note": "Championship Contender (Pace 36+ Req)",
            "min_age": 14,
            "min_overall": 34,
            "min_pace": 36,
            "status": "Dominant Title Contender",
        },
        {
            "tier": 5,
            "team_name": "KMA Elite Beta",
            "league_name": "Tier 5 Karting Masters",
            "rating": 5,
            "expected_pos": "P2 / 10",
            "perf": 93,
            "base_cost": 85000.0,
            "pricing_model": "PRESTIGE",
            "pricing_note": "Title Contender (Pace 34+ Req)",
            "min_age": 14,
            "min_overall": 32,
            "min_pace": 34,
            "status": "High Podium Rate",
        },
        {
            "tier": 5,
            "team_name": "EuroKart Masters",
            "league_name": "Tier 5 Karting Masters",
            "rating": 4,
            "expected_pos": "P3 / 10",
            "perf": 88,
            "base_cost": 65000.0,
            "pricing_model": "BARGAIN",
            "pricing_note": "Bargain: Talent Discount (Pace 28+)",
            "min_age": 14,
            "min_overall": 26,
            "min_pace": 28,
            "status": "Front-Running Team",
        },
        {
            "tier": 5,
            "team_name": "Nordic Karting",
            "league_name": "Tier 5 Karting Masters",
            "rating": 4,
            "expected_pos": "P4 / 10",
            "perf": 84,
            "base_cost": 72000.0,
            "pricing_model": "STANDARD",
            "pricing_note": "Solid Upper Midfield (Pace 26+)",
            "min_age": 14,
            "min_overall": 25,
            "min_pace": 26,
            "status": "Upper Midfield",
        },
        {
            "tier": 5,
            "team_name": "Monza Kart Club",
            "league_name": "Tier 5 Karting Masters",
            "rating": 3,
            "expected_pos": "P5 / 10",
            "perf": 80,
            "base_cost": 48000.0,
            "pricing_model": "BARGAIN",
            "pricing_note": "Bargain: Point Hunters (Pace 22+)",
            "min_age": 14,
            "min_overall": 20,
            "min_pace": 22,
            "status": "Competitive Midfield",
        },
        {
            "tier": 5,
            "team_name": "Silverstone Kart Cadets",
            "league_name": "Tier 5 Karting Masters",
            "rating": 3,
            "expected_pos": "P6 / 10",
            "perf": 76,
            "base_cost": 52000.0,
            "pricing_model": "STANDARD",
            "pricing_note": "Midfield Stability (Open Entry)",
            "min_age": 14,
            "min_overall": 18,
            "min_pace": 18,
            "status": "Midfield Battles",
        },
        {
            "tier": 5,
            "team_name": "Spa Young Drivers",
            "league_name": "Tier 5 Karting Masters",
            "rating": 2,
            "expected_pos": "P7 / 10",
            "perf": 72,
            "base_cost": 42000.0,
            "pricing_model": "OVERPRICED",
            "pricing_note": "Overpriced: Open to All Pay-Drivers",
            "min_age": 14,
            "min_overall": 18,
            "min_pace": 18,
            "status": "Lower Midfield",
        },
        {
            "tier": 5,
            "team_name": "Suzuka Karting School",
            "league_name": "Tier 5 Karting Masters",
            "rating": 2,
            "expected_pos": "P8 / 10",
            "perf": 66,
            "base_cost": 32000.0,
            "pricing_model": "BUDGET",
            "pricing_note": "Developing Academy (Open Entry)",
            "min_age": 14,
            "min_overall": 18,
            "min_pace": 18,
            "status": "Developing Team",
        },
        {
            "tier": 5,
            "team_name": "Interlagos Juniors",
            "league_name": "Tier 5 Karting Masters",
            "rating": 1,
            "expected_pos": "P9 / 10",
            "perf": 60,
            "base_cost": 24000.0,
            "pricing_model": "BUDGET",
            "pricing_note": "Grassroots Entry (Open to All)",
            "min_age": 14,
            "min_overall": 18,
            "min_pace": 18,
            "status": "Backmarker Grid",
        },
        {
            "tier": 5,
            "team_name": "Apex Karting Academy",
            "league_name": "Tier 5 Karting Masters",
            "rating": 1,
            "expected_pos": "P10 / 10",
            "perf": 54,
            "base_cost": 28000.0,
            "pricing_model": "OVERPRICED",
            "pricing_note": "Pay-Driver Backmarker (Open Entry)",
            "min_age": 14,
            "min_overall": 18,
            "min_pace": 18,
            "status": "Underfunded Seat",
        },
    ],
    # Tier 4: Junior Talent Series (F4 Single-Seater Feeder, Min Age 15, 3 Seats / Team, 10 Teams)
    4: [
        {
            "tier": 4,
            "team_name": "JTS Academy Blue",
            "league_name": "Tier 4 Junior Talent Series",
            "rating": 5,
            "expected_pos": "P1 / 10",
            "perf": 96,
            "base_cost": 480000.0,
            "pricing_model": "PRESTIGE",
            "pricing_note": "Title Favorite (Age 16+ & Pace 44+)",
            "min_age": 16,
            "min_overall": 42,
            "min_pace": 44,
            "status": "Dominant Title Contender",
        },
        {
            "tier": 4,
            "team_name": "JTS Academy Red",
            "league_name": "Tier 4 Junior Talent Series",
            "rating": 5,
            "expected_pos": "P2 / 10",
            "perf": 93,
            "base_cost": 420000.0,
            "pricing_model": "PRESTIGE",
            "pricing_note": "Championship Contender (Pace 40+)",
            "min_age": 15,
            "min_overall": 38,
            "min_pace": 40,
            "status": "High Podium Contender",
        },
        {
            "tier": 4,
            "team_name": "Future Stars GP",
            "league_name": "Tier 4 Junior Talent Series",
            "rating": 4,
            "expected_pos": "P3 / 10",
            "perf": 88,
            "base_cost": 310000.0,
            "pricing_model": "BARGAIN",
            "pricing_note": "Bargain: Talent Discount (Pace 36+)",
            "min_age": 15,
            "min_overall": 34,
            "min_pace": 36,
            "status": "Podium Contender",
        },
        {
            "tier": 4,
            "team_name": "Nova Talent Cup",
            "league_name": "Tier 4 Junior Talent Series",
            "rating": 4,
            "expected_pos": "P4 / 10",
            "perf": 84,
            "base_cost": 340000.0,
            "pricing_model": "STANDARD",
            "pricing_note": "Upper Midfield (Pace 34+)",
            "min_age": 15,
            "min_overall": 32,
            "min_pace": 34,
            "status": "Front Running",
        },
        {
            "tier": 4,
            "team_name": "Pioneer Junior GP",
            "league_name": "Tier 4 Junior Talent Series",
            "rating": 3,
            "expected_pos": "P5 / 10",
            "perf": 80,
            "base_cost": 220000.0,
            "pricing_model": "BARGAIN",
            "pricing_note": "Bargain: Hungry Midfield (Pace 30+)",
            "min_age": 15,
            "min_overall": 28,
            "min_pace": 30,
            "status": "Competitive Midfield",
        },
        {
            "tier": 4,
            "team_name": "Ascent Autosport",
            "league_name": "Tier 4 Junior Talent Series",
            "rating": 3,
            "expected_pos": "P6 / 10",
            "perf": 76,
            "base_cost": 240000.0,
            "pricing_model": "STANDARD",
            "pricing_note": "Consistent Midfield (Pace 28+)",
            "min_age": 15,
            "min_overall": 26,
            "min_pace": 28,
            "status": "Top 10 Finishes",
        },
        {
            "tier": 4,
            "team_name": "Velocity Youth",
            "league_name": "Tier 4 Junior Talent Series",
            "rating": 2,
            "expected_pos": "P7 / 10",
            "perf": 72,
            "base_cost": 190000.0,
            "pricing_model": "OVERPRICED",
            "pricing_note": "Pay-Driver Midfield (Open Entry)",
            "min_age": 15,
            "min_overall": 20,
            "min_pace": 20,
            "status": "Lower Midfield",
        },
        {
            "tier": 4,
            "team_name": "Vector Pro-Junior",
            "league_name": "Tier 4 Junior Talent Series",
            "rating": 2,
            "expected_pos": "P8 / 10",
            "perf": 66,
            "base_cost": 140000.0,
            "pricing_model": "BUDGET",
            "pricing_note": "Developing Junior Team (Open Entry)",
            "min_age": 15,
            "min_overall": 20,
            "min_pace": 20,
            "status": "Developing Team",
        },
        {
            "tier": 4,
            "team_name": "Rookie Vanguard",
            "league_name": "Tier 4 Junior Talent Series",
            "rating": 1,
            "expected_pos": "P9 / 10",
            "perf": 60,
            "base_cost": 110000.0,
            "pricing_model": "BUDGET",
            "pricing_note": "Budget Grid Starter (Open Entry)",
            "min_age": 15,
            "min_overall": 18,
            "min_pace": 18,
            "status": "Backmarker Grid",
        },
        {
            "tier": 4,
            "team_name": "Zenith Junior",
            "league_name": "Tier 4 Junior Talent Series",
            "rating": 1,
            "expected_pos": "P10 / 10",
            "perf": 54,
            "base_cost": 130000.0,
            "pricing_model": "OVERPRICED",
            "pricing_note": "Backmarker Seat (Open to All)",
            "min_age": 15,
            "min_overall": 18,
            "min_pace": 18,
            "status": "Underfunded Seat",
        },
    ],
    # Tier 3: National Open Cup (Pro-Am Feeder Series, Min Age 18 by Game Rules, 2 Seats / Team, 10 Teams)
    3: [
        {
            "tier": 3,
            "team_name": "Phoenix GP",
            "league_name": "Tier 3 National Open Cup",
            "rating": 5,
            "expected_pos": "P1 / 10",
            "perf": 96,
            "base_cost": 3200000.0,
            "pricing_model": "PRESTIGE",
            "pricing_note": "Title Favorite (Age 18+ & Pace 50+)",
            "min_age": 18,
            "min_overall": 48,
            "min_pace": 50,
            "status": "Dominant Title Contender",
        },
        {
            "tier": 3,
            "team_name": "Vortex Sprint",
            "league_name": "Tier 3 National Open Cup",
            "rating": 5,
            "expected_pos": "P2 / 10",
            "perf": 93,
            "base_cost": 2700000.0,
            "pricing_model": "PRESTIGE",
            "pricing_note": "Championship Contender (Pace 46+)",
            "min_age": 18,
            "min_overall": 44,
            "min_pace": 46,
            "status": "High Podium Contender",
        },
        {
            "tier": 3,
            "team_name": "Apex Club Sport",
            "league_name": "Tier 3 National Open Cup",
            "rating": 4,
            "expected_pos": "P3 / 10",
            "perf": 88,
            "base_cost": 1800000.0,
            "pricing_model": "BARGAIN",
            "pricing_note": "Bargain: Talent Subsidy (Pace 42+)",
            "min_age": 18,
            "min_overall": 40,
            "min_pace": 42,
            "status": "Podium Contender",
        },
        {
            "tier": 3,
            "team_name": "Falcon Dynamics",
            "league_name": "Tier 3 National Open Cup",
            "rating": 4,
            "expected_pos": "P4 / 10",
            "perf": 84,
            "base_cost": 2100000.0,
            "pricing_model": "STANDARD",
            "pricing_note": "Upper Midfield (Pace 40+)",
            "min_age": 18,
            "min_overall": 38,
            "min_pace": 40,
            "status": "Front Running",
        },
        {
            "tier": 3,
            "team_name": "Mirage Motorsport",
            "league_name": "Tier 3 National Open Cup",
            "rating": 3,
            "expected_pos": "P5 / 10",
            "perf": 80,
            "base_cost": 1200000.0,
            "pricing_model": "BARGAIN",
            "pricing_note": "Bargain: Hungry Midfield (Pace 36+)",
            "min_age": 18,
            "min_overall": 34,
            "min_pace": 36,
            "status": "Competitive Midfield",
        },
        {
            "tier": 3,
            "team_name": "Pulse Racing Team",
            "league_name": "Tier 3 National Open Cup",
            "rating": 3,
            "expected_pos": "P6 / 10",
            "perf": 76,
            "base_cost": 1400000.0,
            "pricing_model": "STANDARD",
            "pricing_note": "Consistent Midfield (Pace 32+)",
            "min_age": 18,
            "min_overall": 30,
            "min_pace": 32,
            "status": "Top 10 Finishes",
        },
        {
            "tier": 3,
            "team_name": "Zephyr Cup",
            "league_name": "Tier 3 National Open Cup",
            "rating": 2,
            "expected_pos": "P7 / 10",
            "perf": 72,
            "base_cost": 1100000.0,
            "pricing_model": "OVERPRICED",
            "pricing_note": "Pay-Driver Midfield (Open Entry)",
            "min_age": 18,
            "min_overall": 24,
            "min_pace": 24,
            "status": "Lower Midfield",
        },
        {
            "tier": 3,
            "team_name": "Stratos Autosport",
            "league_name": "Tier 3 National Open Cup",
            "rating": 2,
            "expected_pos": "P8 / 10",
            "perf": 66,
            "base_cost": 750000.0,
            "pricing_model": "BUDGET",
            "pricing_note": "Developing Team (Open Entry)",
            "min_age": 18,
            "min_overall": 22,
            "min_pace": 22,
            "status": "Developing Team",
        },
        {
            "tier": 3,
            "team_name": "Obsidian GP",
            "league_name": "Tier 3 National Open Cup",
            "rating": 1,
            "expected_pos": "P9 / 10",
            "perf": 60,
            "base_cost": 550000.0,
            "pricing_model": "BUDGET",
            "pricing_note": "Budget Grid Starter (Open Entry)",
            "min_age": 18,
            "min_overall": 20,
            "min_pace": 20,
            "status": "Backmarker Grid",
        },
        {
            "tier": 3,
            "team_name": "Horizon Cup Support",
            "league_name": "Tier 3 National Open Cup",
            "rating": 1,
            "expected_pos": "P10 / 10",
            "perf": 54,
            "base_cost": 850000.0,
            "pricing_model": "OVERPRICED",
            "pricing_note": "Backmarker Seat (Open to All 18+)",
            "min_age": 18,
            "min_overall": 20,
            "min_pace": 20,
            "status": "Underfunded Seat",
        },
    ],
    # Tier 2: Continental Championship (High-Power Feeder, Min Age 18, 2 Seats / Team, 10 Teams)
    2: [
        {
            "tier": 2,
            "team_name": "Nordic Velocity",
            "league_name": "Tier 2 Continental Champ.",
            "rating": 5,
            "expected_pos": "P1 / 10",
            "perf": 96,
            "base_cost": 11500000.0,
            "pricing_model": "PRESTIGE",
            "pricing_note": "Dominant Contender (Age 18+ & Pace 58+)",
            "min_age": 18,
            "min_overall": 56,
            "min_pace": 58,
            "status": "Dominant Title Contender",
        },
        {
            "tier": 2,
            "team_name": "Bavaria Sport",
            "league_name": "Tier 2 Continental Champ.",
            "rating": 5,
            "expected_pos": "P2 / 10",
            "perf": 93,
            "base_cost": 9800000.0,
            "pricing_model": "PRESTIGE",
            "pricing_note": "Championship Contender (Pace 54+)",
            "min_age": 18,
            "min_overall": 52,
            "min_pace": 54,
            "status": "High Podium Contender",
        },
        {
            "tier": 2,
            "team_name": "Riviera Corse",
            "league_name": "Tier 2 Continental Champ.",
            "rating": 4,
            "expected_pos": "P3 / 10",
            "perf": 88,
            "base_cost": 6200000.0,
            "pricing_model": "BARGAIN",
            "pricing_note": "Bargain: Talent Discount (Pace 48+)",
            "min_age": 18,
            "min_overall": 46,
            "min_pace": 48,
            "status": "Podium Contender",
        },
        {
            "tier": 2,
            "team_name": "Silverstone Engineering",
            "league_name": "Tier 2 Continental Champ.",
            "rating": 4,
            "expected_pos": "P4 / 10",
            "perf": 84,
            "base_cost": 7500000.0,
            "pricing_model": "STANDARD",
            "pricing_note": "Upper Midfield (Pace 46+)",
            "min_age": 18,
            "min_overall": 44,
            "min_pace": 46,
            "status": "Front Running",
        },
        {
            "tier": 2,
            "team_name": "Iberia Grand Prix",
            "league_name": "Tier 2 Continental Champ.",
            "rating": 3,
            "expected_pos": "P5 / 10",
            "perf": 80,
            "base_cost": 4200000.0,
            "pricing_model": "BARGAIN",
            "pricing_note": "Bargain: Hungry Midfield (Pace 42+)",
            "min_age": 18,
            "min_overall": 40,
            "min_pace": 42,
            "status": "Competitive Midfield",
        },
        {
            "tier": 2,
            "team_name": "Alps Dynamics",
            "league_name": "Tier 2 Continental Champ.",
            "rating": 3,
            "expected_pos": "P6 / 10",
            "perf": 76,
            "base_cost": 5000000.0,
            "pricing_model": "STANDARD",
            "pricing_note": "Consistent Midfield (Pace 38+)",
            "min_age": 18,
            "min_overall": 36,
            "min_pace": 38,
            "status": "Top 10 Finishes",
        },
        {
            "tier": 2,
            "team_name": "Danube GP",
            "league_name": "Tier 2 Continental Champ.",
            "rating": 2,
            "expected_pos": "P7 / 10",
            "perf": 72,
            "base_cost": 4400000.0,
            "pricing_model": "OVERPRICED",
            "pricing_note": "Pay-Driver Midfield (Open Entry)",
            "min_age": 18,
            "min_overall": 30,
            "min_pace": 30,
            "status": "Lower Midfield",
        },
        {
            "tier": 2,
            "team_name": "Baltic Motorsport",
            "league_name": "Tier 2 Continental Champ.",
            "rating": 2,
            "expected_pos": "P8 / 10",
            "perf": 66,
            "base_cost": 2900000.0,
            "pricing_model": "BUDGET",
            "pricing_note": "Developing Team (Open Entry)",
            "min_age": 18,
            "min_overall": 28,
            "min_pace": 28,
            "status": "Developing Team",
        },
        {
            "tier": 2,
            "team_name": "Apennine Racing",
            "league_name": "Tier 2 Continental Champ.",
            "rating": 1,
            "expected_pos": "P9 / 10",
            "perf": 60,
            "base_cost": 2100000.0,
            "pricing_model": "BUDGET",
            "pricing_note": "Budget Grid Starter (Open Entry)",
            "min_age": 18,
            "min_overall": 22,
            "min_pace": 22,
            "status": "Backmarker Grid",
        },
        {
            "tier": 2,
            "team_name": "Caledonia Speed",
            "league_name": "Tier 2 Continental Champ.",
            "rating": 1,
            "expected_pos": "P10 / 10",
            "perf": 54,
            "base_cost": 3100000.0,
            "pricing_model": "OVERPRICED",
            "pricing_note": "Backmarker Seat (Open to All 18+)",
            "min_age": 18,
            "min_overall": 22,
            "min_pace": 22,
            "status": "Underfunded Seat",
        },
    ],
}


class DriverManager:
    """
    Manages 11-attribute driver development:
    - 8 Driving stats following independent parabolic curves (growing until 28, declining from 30).
    - 3 Mental stats that CAN ONLY GO UP.
    - Max potential caps per stat per driver.
    - Rate driven by Finish Result (winning boosts growth; finishing high > tier), Tier, and Facilities.
    - Living Feeder Market, Dynamic Occupancy, and Mid-Season Seat Switching.
    """

    def __init__(self, db: CareerDatabase):
        self.db = db
        self._init_feeder_market()

    def _init_feeder_market(self):
        """Populates dynamic feeder market table and updates base costs, expected_pos and requirements."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM feeder_market_seats;")
            seat_count = cur.fetchone()[0]

            if seat_count == 0:
                for tier, teams in FEEDER_TEAMS_CATALOG.items():
                    seats_per_team = 3 if tier in [4, 5] else 2
                    for team in teams:
                        for slot in range(1, seats_per_team + 1):
                            is_ai_occ = random.random() < 0.60
                            ai_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}" if is_ai_occ else ""
                            cost_var = round(team["base_cost"] * random.uniform(0.94, 1.06), 0)

                            cur.execute(
                                """
                            INSERT INTO feeder_market_seats (
                                tier, team_name, league_name, seat_slot, rating, expected_pos, perf,
                                base_cost, current_cost, min_age, min_overall, min_pace,
                                pricing_model, pricing_note, is_occupied, occupant_team_id,
                                occupant_driver_id, occupant_driver_name, status
                            ) VALUES (
                                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?
                            );
                            """,
                                (
                                    tier,
                                    team["team_name"],
                                    team["league_name"],
                                    slot,
                                    team["rating"],
                                    team.get("expected_pos", "P1 / 10"),
                                    team["perf"],
                                    team["base_cost"],
                                    cost_var,
                                    team["min_age"],
                                    team["min_overall"],
                                    team["min_pace"],
                                    team["pricing_model"],
                                    team["pricing_note"],
                                    1 if is_ai_occ else 0,
                                    ai_name,
                                    team["status"],
                                ),
                            )

            else:
                for tier, teams in FEEDER_TEAMS_CATALOG.items():
                    for team in teams:
                        cur.execute(
                            """
                        UPDATE feeder_market_seats 
                        SET base_cost = ?, pricing_model = ?, pricing_note = ?,
                            min_age = ?, min_overall = ?, min_pace = ?, expected_pos = ?,
                            current_cost = ROUND(? * (0.94 + (abs(random()) % 13) / 100.0), 0)
                        WHERE team_name = ?;
                        """,
                            (
                                team["base_cost"],
                                team["pricing_model"],
                                team["pricing_note"],
                                team["min_age"],
                                team["min_overall"],
                                team["min_pace"],
                                team.get("expected_pos", "P1 / 10"),
                                team["base_cost"],
                                team["team_name"],
                            ),
                        )

            conn.commit()

    def get_team_drivers(self, team_id: int) -> List[Dict[str, Any]]:
        return self.db.get_team_drivers(team_id)

    def get_driver_buyout_cost(self, driver: Dict[str, Any]) -> float:
        """
        Calculates the contract buyout / disband compensation cost to release or replace a driver.
        - Default Drivers: $0 (free replacement at any time)
        - Standard Drivers: remaining_races * salary_per_race * 0.50
        - Pay-Drivers: Breaching personal sponsor deal incurs 1.5x penalty on remaining race commitments
        - Sponsored Loan Drivers: Breaching parent constructor loan incurs 1.5x penalty on remaining race commitments
        """
        if not driver:
            return 0.0
        d_type = driver.get("driver_type", "STANDARD")
        if d_type == "DEFAULT_DRIVER":
            return 0.0
        races_left = int(driver.get("contract_races_left", 0) or 0)
        if races_left <= 0:
            return 0.0

        if d_type == "PAY_DRIVER":
            spon_rate = float(driver.get("sponsor_income_per_race", 0.0) or 0.0)
            if spon_rate <= 0:
                tier = driver.get("tier") or 3
                tier_defaults = {1: 300000.0, 2: 100000.0, 3: 40000.0, 4: 15000.0, 5: 8000.0}
                spon_rate = tier_defaults.get(tier, 40000.0)
            # Breaching pay-driver sponsor agreement carries a 1.5x penalty on remaining race commitments
            return round(races_left * spon_rate * 1.50, -2)

        elif d_type == "SPONSORED_DRIVER":
            loan_fee = float(driver.get("sponsor_income_per_race", 0.0) or 0.0)
            if loan_fee <= 0:
                tier = driver.get("tier") or 3
                tier_defaults = {1: 350000.0, 2: 120000.0, 3: 45000.0, 4: 18000.0, 5: 10000.0}
                loan_fee = tier_defaults.get(tier, 45000.0)
            # Terminating parent constructor academy loan carries a 1.5x penalty on remaining race commitments
            return round(races_left * loan_fee * 1.50, -2)

        else:  # STANDARD
            salary_race = float(driver.get("salary_per_race", 0.0) or 0.0)
            return round(races_left * salary_race * 0.50, -2)

    def ensure_default_drivers_filled(self, team_id: int):
        """
        Ensures that an active team always has 2 primary race drivers.
        If any slot is vacant (e.g. at new game start or after contract expiration),
        it is automatically filled with a low-stat, 30yo+ Default Driver on a 0-year contract (free to let go).
        """
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            SELECT * FROM drivers 
            WHERE team_id = ? AND is_academy_driver = 0 
            ORDER BY is_player_driver DESC, id ASC;
            """,
                (team_id,),
            )
            primary = [dict(r) for r in cur.fetchall()]

            if len(primary) >= 2:
                return

            needed = 2 - len(primary)
            default_names = ["Robin Sterling", "Morgan Cross", "Taylor Brooks", "Casey Vance", "Jordan Reed"]
            random.shuffle(default_names)

            for i in range(needed):
                slot_num = len(primary) + i + 1
                name = default_names.pop() if default_names else f"Stand-in Driver {random.randint(10, 99)}"
                age = random.randint(31, 38)
                num = random.randint(50, 99)
                base_stat = random.randint(20, 28)

                cur.execute(
                    """
                INSERT INTO drivers (
                    team_id, name, age, number, is_player_driver, is_academy_driver,
                    salary_per_race, contract_races_left, contract_seasons_left, signing_bonus,
                    role_status, contract_preference, is_homegrown, main_team_seasons,
                    driver_type, parent_team_name, parent_team_tier, parent_team_expected_pos,
                    pay_driver_sponsor_name, sponsor_income_per_race,
                    potential, morale, pace, race_starts, braking, tire_management, defending, wet_weather,
                    consistency, fuel_efficiency, technical_understanding, communication, marketability,
                    pot_pace, pot_race_starts, pot_braking, pot_tire_management, pot_defending, pot_wet_weather,
                    pot_consistency, pot_fuel_efficiency, pot_technical_understanding, pot_communication, pot_marketability
                ) VALUES (
                    ?, ?, ?, ?, ?, 0,
                    1250.0, 0, 0, 0.0,
                    'EQUAL', 'BALANCED', 0, 0,
                    'DEFAULT_DRIVER', '', 1, 'P1 / 10',
                    '', 0.0,
                    35, 75.0, ?, ?, ?, ?, ?, ?,
                    40, 40, ?, ?, ?,
                    35, 35, 35, 35, 35, 35,
                    35, 35, 40, 40, 40
                );
                """,
                    (
                        team_id,
                        name,
                        age,
                        num,
                        1 if slot_num == 1 else 0,
                        base_stat,
                        base_stat,
                        base_stat,
                        base_stat,
                        base_stat,
                        base_stat,
                        base_stat,
                        base_stat,
                        base_stat,
                    ),
                )

            conn.commit()

    def release_primary_driver(self, team_id: int, driver_id: int) -> Tuple[bool, str]:
        """
        Releases a primary race driver mid-contract. Charges a buyout severance fee if contracted,
        and automatically backfills the open car seat with a free Default Driver.
        """
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM drivers WHERE id = ? AND team_id = ? AND is_academy_driver = 0;", (driver_id, team_id)
            )
            row = cur.fetchone()
            if not row:
                return False, "Driver not found on primary race roster."
            driver = dict(row)

            buyout = self.get_driver_buyout_cost(driver)
            cur.execute("SELECT cash FROM teams WHERE id = ?;", (team_id,))
            cash = float(cur.fetchone()[0] or 0.0)

            if buyout > 0 and cash < buyout:
                return False, f"Insufficient funds to buyout contract (${buyout:,.0f} severance fee required)."

            if buyout > 0:
                cur.execute("UPDATE teams SET cash = cash - ? WHERE id = ?;", (buyout, team_id))
                cur.execute(
                    """
                INSERT INTO ledger (team_id, week, category, description, amount)
                VALUES (?, 1, 'CONTRACTS', ?, ?);
                """,
                    (team_id, f"Contract Buyout Severance for {driver['name']}", -buyout),
                )

            # Calculate driver's record with player team
            cur.execute(
                """
            SELECT COUNT(*),
                   SUM(CASE WHEN position = 1 THEN 1 ELSE 0 END),
                   SUM(CASE WHEN position <= 3 THEN 1 ELSE 0 END),
                   SUM(points)
            FROM series_race_results
            WHERE (driver_id = ? OR driver_name = ?) AND team_id = ?;
            """,
                (driver_id, driver["name"], team_id),
            )
            stat_row = cur.fetchone()
            starts = stat_row[0] if stat_row and stat_row[0] else 0
            wins = stat_row[1] if stat_row and stat_row[1] else 0
            pods = stat_row[2] if stat_row and stat_row[2] else 0
            pts = stat_row[3] if stat_row and stat_row[3] else 0

            curr_s = self.db.get_current_season_num()
            self.db.record_team_alumni(
                player_team_id=team_id,
                driver_id=driver_id,
                driver_name=driver["name"],
                departure_reason="RELEASED",
                departure_season=curr_s,
                starts_with_team=starts,
                wins_with_team=wins,
                podiums_with_team=pods,
                points_with_team=pts,
            )

            # Move driver to Free Agent status rather than deleting
            cur.execute(
                "UPDATE drivers SET team_id = NULL, is_player_driver = 0, contract_races_left = 0 WHERE id = ?;",
                (driver_id,),
            )
            conn.commit()

        # Automatically fill open seat with a free Default Driver
        self.ensure_default_drivers_filled(team_id)

        fee_msg = (
            f" Paid ${buyout:,.0f} contract buyout severance." if buyout > 0 else " Released for free ($0 buyout)."
        )
        return True, f"Released {driver['name']} from race seat.{fee_msg} Default stand-in driver assigned."

    def get_primary_drivers(self, team_id: int) -> List[Dict[str, Any]]:
        self.ensure_default_drivers_filled(team_id)
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            SELECT * FROM drivers 
            WHERE team_id = ? AND is_academy_driver = 0 
            ORDER BY is_player_driver DESC, id ASC;
            """,
                (team_id,),
            )
            return [dict(r) for r in cur.fetchall()]

    def get_academy_drivers(self, team_id: int) -> List[Dict[str, Any]]:
        drivers = self.db.get_team_drivers(team_id)
        return [d for d in drivers if d["is_academy_driver"]]

    def get_scout_prospects(self, team_id: int) -> List[Dict[str, Any]]:
        """Returns scouted youth candidates available for the team's junior academy."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM scout_prospects WHERE team_id = ? ORDER BY scout_rating DESC, potential DESC;",
                (team_id,),
            )
            rows = [dict(r) for r in cur.fetchall()]
            if not rows:
                self._generate_scout_prospects(team_id)
                cur.execute(
                    "SELECT * FROM scout_prospects WHERE team_id = ? ORDER BY scout_rating DESC, potential DESC;",
                    (team_id,),
                )
                rows = [dict(r) for r in cur.fetchall()]
            return rows

    def _generate_scout_prospects(self, team_id: int):
        """Populates dynamic youth scouting board for the team with facility & equipment boosts."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM scout_prospects WHERE team_id = ?;", (team_id,))

            # Query unlocked facility tiers
            cur.execute(
                """
            SELECT node_id, current_tier FROM team_facilities
            WHERE team_id = ? AND is_unlocked = 1;
            """,
                (team_id,),
            )
            fac_tiers = {r[0]: r[1] for r in cur.fetchall()}

            # Query active equipment levels
            cur.execute(
                """
            SELECT fe.node_id, te.current_level
            FROM facility_equipment fe
            JOIN team_equipment te ON fe.id = te.equipment_id
            WHERE te.team_id = ? AND te.is_active = 1 AND te.current_level > 0;
            """,
                (team_id,),
            )
            eq_rows = cur.fetchall()
            eq_levels = {}
            for r in eq_rows:
                eq_levels[r[0]] = eq_levels.get(r[0], 0) + r[1]

            karting_tier = fac_tiers.get("driver_karting_scholarship", 0)
            acad_tier = fac_tiers.get("driver_academy", 0)
            karting_eq = eq_levels.get("driver_karting_scholarship", 0)

            # Potential floor boost: +4 min potential per karting tier + equipment
            pot_boost = (karting_tier * 4) + (karting_eq * 1)

            prospect_pool = [
                {
                    "name": "Leo Rossi",
                    "age": 15,
                    "nat": "ITA",
                    "pot": 94,
                    "scout_rating": 5,
                    "notes": "Sensational karting champion. Blistering raw pace and laser focus.",
                    "pace": 38,
                    "starts": 32,
                    "braking": 34,
                    "tires": 30,
                    "def": 28,
                    "wet": 35,
                    "tech": 40,
                    "comm": 45,
                    "mkt": 75,
                    "pref_tier": 5,
                },
                {
                    "name": "Kai Tanaka",
                    "age": 16,
                    "nat": "JPN",
                    "pot": 91,
                    "scout_rating": 5,
                    "notes": "Super-composed junior prodigy. Exceptional braking stability and tire feel.",
                    "pace": 42,
                    "starts": 38,
                    "braking": 44,
                    "tires": 40,
                    "def": 36,
                    "wet": 38,
                    "tech": 45,
                    "comm": 42,
                    "mkt": 70,
                    "pref_tier": 4,
                },
                {
                    "name": "Arthur Lindqvist",
                    "age": 14,
                    "nat": "FIN",
                    "pot": 88,
                    "scout_rating": 4,
                    "notes": "Master of wet-weather conditions and defensive racecraft.",
                    "pace": 32,
                    "starts": 28,
                    "braking": 30,
                    "tires": 34,
                    "def": 36,
                    "wet": 48,
                    "tech": 35,
                    "comm": 32,
                    "mkt": 58,
                    "pref_tier": 5,
                },
                {
                    "name": "Matteo Vasseur",
                    "age": 17,
                    "nat": "FRA",
                    "pot": 86,
                    "scout_rating": 4,
                    "notes": "Consistent, aggressive overtaker with sharp starts.",
                    "pace": 44,
                    "starts": 46,
                    "braking": 40,
                    "tires": 36,
                    "def": 42,
                    "wet": 32,
                    "tech": 38,
                    "comm": 48,
                    "mkt": 65,
                    "pref_tier": 4,
                },
                {
                    "name": "Lucas Novak",
                    "age": 18,
                    "nat": "GER",
                    "pot": 82,
                    "scout_rating": 3,
                    "notes": "Dependable and disciplined. High technical feedback capability.",
                    "pace": 46,
                    "starts": 42,
                    "braking": 44,
                    "tires": 45,
                    "def": 40,
                    "wet": 36,
                    "tech": 52,
                    "comm": 50,
                    "mkt": 60,
                    "pref_tier": 4,
                },
                {
                    "name": "Gabriel Santos",
                    "age": 15,
                    "nat": "BRA",
                    "pot": 80,
                    "scout_rating": 3,
                    "notes": "High stamina and attacking spirit from South American karting.",
                    "pace": 34,
                    "starts": 36,
                    "braking": 32,
                    "tires": 28,
                    "def": 34,
                    "wet": 30,
                    "tech": 30,
                    "comm": 38,
                    "mkt": 62,
                    "pref_tier": 5,
                },
            ]

            # If Karting Scholarship foundation is unlocked, add an exclusive world-class prodigy
            if karting_tier > 0:
                prospect_pool.insert(
                    0,
                    {
                        "name": "Valerio De Luca",
                        "age": 14,
                        "nat": "ITA",
                        "pot": min(99, 93 + karting_tier * 2),
                        "scout_rating": 5,
                        "notes": "Grassroots Karting Foundation Scholarship Discovery: Unprecedented telemetric karting corner speeds.",
                        "pace": 42,
                        "starts": 38,
                        "braking": 38,
                        "tires": 36,
                        "def": 35,
                        "wet": 42,
                        "tech": 45,
                        "comm": 48,
                        "mkt": 78,
                        "pref_tier": 5,
                    },
                )

            for p in prospect_pool:
                pot = min(99, p["pot"] + (pot_boost if p["pot"] < 90 else pot_boost // 2))
                cur.execute(
                    """
                INSERT INTO scout_prospects (
                    team_id, name, age, nationality, potential, scout_rating, scouting_notes,
                    pace, race_starts, braking, tire_management, defending, wet_weather,
                    technical_understanding, communication, marketability, preferred_tier, placement_fee_season,
                    pot_pace, pot_race_starts, pot_braking, pot_tire_management, pot_defending, pot_wet_weather,
                    pot_consistency, pot_fuel_efficiency, pot_technical_understanding, pot_communication, pot_marketability
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?
                );
                """,
                    (
                        team_id,
                        p["name"],
                        p["age"],
                        p["nat"],
                        pot,
                        p["scout_rating"],
                        p["notes"],
                        p["pace"],
                        p["starts"],
                        p["braking"],
                        p["tires"],
                        p["def"],
                        p["wet"],
                        p["tech"],
                        p["comm"],
                        p["mkt"],
                        p["pref_tier"],
                        80000.0,
                        min(99, pot + 2),
                        min(99, pot + 2),
                        min(99, pot + 2),
                        min(99, pot + 2),
                        min(99, pot + 2),
                        min(99, pot + 2),
                        min(99, pot + 2),
                        min(99, pot + 2),
                        min(99, pot + 4),
                        min(99, pot + 4),
                        min(99, pot + 4),
                    ),
                )
            conn.commit()

    def get_available_feeder_seats(self, team_tier: int) -> List[Dict[str, Any]]:
        """
        Returns all currently OPEN (unoccupied) sponsored feeder seats in leagues strictly below team's tier.
        Applies Dynamic Supply-and-Demand Scarcity Pricing:
        The fewer seats remaining open in a tier, the higher the demand fee on remaining seats.
        """
        eligible_tiers = [t for t in [5, 4, 3, 2] if t > team_tier]
        available_seats = []

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            for t in eligible_tiers:
                cur.execute("SELECT COUNT(*) FROM feeder_market_seats WHERE tier = ?;", (t,))
                total_seats = max(1, cur.fetchone()[0])

                cur.execute("SELECT COUNT(*) FROM feeder_market_seats WHERE tier = ? AND is_occupied = 0;", (t,))
                open_seats_cnt = cur.fetchone()[0]

                # Scarcity Multiplier: If only 20% seats left open, price inflates up to +40%
                scarcity_factor = 1.0 + max(0.0, (1.0 - (open_seats_cnt / total_seats))) * 0.40

                cur.execute(
                    """
                SELECT * FROM feeder_market_seats 
                WHERE tier = ? AND is_occupied = 0 
                ORDER BY rating DESC, current_cost ASC;
                """,
                    (t,),
                )
                rows = cur.fetchall()

                for r in rows:
                    s_dict = dict(r)
                    # Effective cost with live scarcity
                    s_dict["cost"] = round(s_dict["current_cost"] * scarcity_factor, 0)
                    s_dict["scarcity_pct"] = int((scarcity_factor - 1.0) * 100)
                    s_dict["open_seats_in_tier"] = open_seats_cnt
                    s_dict["total_seats_in_tier"] = total_seats
                    available_seats.append(s_dict)

        return available_seats

    def can_driver_sign_seat(self, prospect: Dict[str, Any], seat: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validates driver eligibility against championship regulations and team performance standards.
        Top teams demand high age and proven pace; lower teams are open to all pay-drivers.
        """
        if seat.get("is_occupied", 0) == 1:
            return False, f"Seat at {seat['team_name']} is currently occupied."

        # 1. Minimum Age Rule (Tier 3 Super-Licence rule = 18+, Tier 4 = 15+, Tier 5 = 14+)
        min_age = seat.get("min_age", 14)
        p_age = prospect.get("age", 15)
        if p_age < min_age:
            return (
                False,
                f"Driver is {p_age}yo. {seat['team_name']} ({seat['league_name']}) requires minimum age of {min_age}.",
            )

        # 2. Performance / Pace Requirement for competitive teams
        min_pace = seat.get("min_pace", 18)
        p_pace = prospect.get("pace", 20)
        if p_pace < min_pace:
            return (
                False,
                f"{seat['team_name']} ({'⭐' * seat.get('rating', 1)}) demands Pace {min_pace}+ (Driver has {p_pace}).",
            )

        # 3. Overall skill estimate requirement for prestige title teams
        min_ovr = seat.get("min_overall", 18)
        d_ovr = (prospect.get("pace", 30) + prospect.get("braking", 30) + prospect.get("tire_management", 30)) // 3
        if d_ovr < min_ovr:
            return False, f"{seat['team_name']} demands Overall {min_ovr}+ (Driver has {d_ovr})."

        return True, "Eligible"

    def set_training_focus(self, driver_id: int, focus: str):
        """Sets the player-directed training focus for a driver."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE drivers SET training_focus = ? WHERE id = ?;", (focus.upper(), driver_id))
            conn.commit()

    # =========================================================================
    # DRIVER MARKET & CONTRACT NEGOTIATIONS
    # =========================================================================
    def get_car_performance_rank(self, team_id: int) -> int:
        """Returns relative performance rank (1-10) of team's car in current tier based on car components/ratings."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            # 1. Query car_components table
            cur.execute("SELECT AVG(performance) FROM car_components WHERE team_id = ?;", (team_id,))
            res = cur.fetchone()
            if res and res[0] is not None:
                avg_perf = float(res[0])
                # Component performance ranges from ~20 to ~90
                rank = max(1, min(10, int(round(10 - (avg_perf / 90.0) * 9))))
                return rank

            # 2. Fallback to team reputation
            cur.execute("SELECT reputation FROM teams WHERE id = ?;", (team_id,))
            row = cur.fetchone()
            if row and row[0] is not None:
                rep = float(row[0])
                rank = max(1, min(10, int(round(10 - (rep / 100.0) * 9))))
                return rank

            return 5

    def get_feeder_seat_market_value(self, tier: int, car_rank: int = 5) -> float:
        """
        Returns the authentic annual market value for a youth feeder seat in a given championship tier
        and expected grid finish rank (1 = P1 title team, 10 = P10 backmarker).
        Matches the exact pricing scale of the feeder seats catalog that players pay for academy placements!
        """
        if tier == 1:
            if car_rank <= 2:
                base = random.uniform(85000000.0, 115000000.0)
            elif car_rank <= 4:
                base = random.uniform(55000000.0, 75000000.0)
            elif car_rank <= 6:
                base = random.uniform(40000000.0, 52000000.0)
            elif car_rank <= 8:
                base = random.uniform(30000000.0, 38000000.0)
            else:
                base = random.uniform(22000000.0, 28000000.0)
        elif tier == 2:
            if car_rank <= 2:
                base = random.uniform(36000000.0, 44000000.0)
            elif car_rank <= 4:
                base = random.uniform(17500000.0, 26000000.0)
            elif car_rank <= 6:
                base = random.uniform(11000000.0, 15000000.0)
            elif car_rank <= 8:
                base = random.uniform(8500000.0, 13500000.0)
            else:
                base = random.uniform(6200000.0, 9500000.0)
        elif tier == 3:
            if car_rank <= 2:
                base = random.uniform(12000000.0, 14500000.0)
            elif car_rank <= 4:
                base = random.uniform(5600000.0, 8200000.0)
            elif car_rank <= 6:
                base = random.uniform(3400000.0, 4800000.0)
            elif car_rank <= 8:
                base = random.uniform(2600000.0, 4200000.0)
            else:
                base = random.uniform(1750000.0, 3000000.0)
        elif tier == 4:
            if car_rank <= 2:
                base = random.uniform(3100000.0, 3800000.0)
            elif car_rank <= 4:
                base = random.uniform(1450000.0, 2100000.0)
            elif car_rank <= 6:
                base = random.uniform(850000.0, 1200000.0)
            elif car_rank <= 8:
                base = random.uniform(680000.0, 1100000.0)
            else:
                base = random.uniform(420000.0, 750000.0)
        else:
            if car_rank <= 2:
                base = random.uniform(245000.0, 290000.0)
            elif car_rank <= 4:
                base = random.uniform(135000.0, 170000.0)
            elif car_rank <= 6:
                base = random.uniform(80000.0, 110000.0)
            elif car_rank <= 8:
                base = random.uniform(62000.0, 95000.0)
        return round(base, -2)

    def get_market_drivers(self, team_tier: int, car_rank: int = 5) -> List[Dict[str, Any]]:
        """Returns available free agents, pay-drivers, and sponsored loan talents on the driver market."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM driver_market WHERE tier = ?;", (team_tier,))
            total_cnt = cur.fetchone()[0]
            cur.execute(
                "SELECT COUNT(*) FROM driver_market WHERE tier = ? AND driver_type = 'PAY_DRIVER';", (team_tier,)
            )
            pay_cnt = cur.fetchone()[0]

            if total_cnt < 8 or pay_cnt < 3:
                self._generate_market_drivers(team_tier, car_rank=car_rank)

            cur.execute(
                """
            SELECT * FROM driver_market 
            WHERE tier = ? 
            ORDER BY 
                CASE 
                    WHEN driver_type = 'PAY_DRIVER' THEN 1 
                    WHEN driver_type = 'SPONSORED_DRIVER' THEN 2 
                    ELSE 3 
                END, 
                potential DESC, 
                pace DESC;
            """,
                (team_tier,),
            )
            rows = [dict(r) for r in cur.fetchall()]
            return rows

    def _generate_market_drivers(self, tier: int, car_rank: int = 5):
        """
        Populates dynamic driver market pool for a championship tier:
        1. 6 Pay-Drivers (Common, variable skill, brings Free 2x-3x Title Sponsor)
        2. 4 Standard Pro Drivers (Balanced skill & wage demands)
        3. 3 Sponsored Loan Talents (Parent constructor junior loan, 1-year contract)
        """
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM driver_market WHERE tier = ?;", (tier,))

            # Base salary scales by tier
            base_sal_per_race = {1: 220000.0, 2: 95000.0, 3: 38000.0, 4: 12000.0, 5: 3500.0}.get(tier, 38000.0)
            base_skill = {1: 78, 2: 66, 3: 52, 4: 38, 5: 25}.get(tier, 52)

            sponsor_brands = [
                "PetroVanguard Energy",
                "CryptoMax Global",
                "Nexus Mobile 5G",
                "Volt Hyper-Drink",
                "Titanium Swiss Bank",
                "AeroDynamics Logix",
                "Quantum AI Cloud",
                "Solaria Solar Systems",
            ]

            parent_constructor_catalogs = [
                {"name": "Scuderia Apex WSF Junior Program", "tier": 1, "pos": "P1 / 10"},
                {"name": "Titan Grand Prix Development", "tier": 1, "pos": "P2 / 10"},
                {"name": "Vortex Works Academy", "tier": 1, "pos": "P3 / 10"},
                {"name": "Bavaria Continental Junior Cup", "tier": 2, "pos": "P1 / 10"},
                {"name": "Nordic Velocity Driver Academy", "tier": 2, "pos": "P2 / 10"},
                {"name": "Phoenix NOC Pro-Am Talent", "tier": 3, "pos": "P1 / 10"},
            ]

            # 1. Generate 4 Standard Market Drivers
            for _ in range(4):
                name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
                age = random.randint(21, 33)
                nat = random.choice(NATIONALITIES)
                pot = max(45, min(96, base_skill + random.randint(4, 18)))
                cur_skill = max(20, min(pot, base_skill + random.randint(-6, 8)))

                patience = random.randint(2, 5)
                pref = random.choice(
                    ["BALANCED", "SHORT_TERM", "LONG_TERM", "SALARY_SEEKER", "BONUS_SEEKER", "PRESTIGE_LEADER"]
                )

                exp_sal = round(base_sal_per_race * (cur_skill / float(base_skill)) * random.uniform(0.9, 1.15), -2)
                exp_bon = round(exp_sal * random.uniform(2.5, 4.5), -2)
                exp_role = "#1" if pref == "PRESTIGE_LEADER" or cur_skill >= base_skill + 5 else "EQUAL"
                exp_seasons = 1 if pref == "SHORT_TERM" else (4 if pref == "LONG_TERM" else random.randint(2, 3))

                pace = max(18, min(95, cur_skill + random.randint(-3, 5)))
                starts = max(18, min(95, cur_skill + random.randint(-3, 5)))
                braking = max(18, min(95, cur_skill + random.randint(-3, 5)))
                tires = max(18, min(95, cur_skill + random.randint(-3, 5)))
                defending = max(18, min(95, cur_skill + random.randint(-3, 5)))
                wet = max(18, min(95, cur_skill + random.randint(-3, 5)))
                tech = max(18, min(95, cur_skill + random.randint(-4, 6)))
                comm = max(18, min(95, cur_skill + random.randint(-4, 6)))
                mkt = random.randint(40, 85)

                cur.execute(
                    """
                INSERT INTO driver_market (
                    name, age, nationality, tier, driver_type, patience, current_patience,
                    contract_preference, expected_salary_race, expected_signing_bonus, expected_role, expected_seasons,
                    parent_team_name, parent_team_tier, parent_team_expected_pos, pay_driver_sponsor_name, sponsor_income_per_race,
                    potential, morale, pace, race_starts, braking, tire_management, defending, wet_weather,
                    consistency, fuel_efficiency, technical_understanding, communication, marketability,
                    pot_pace, pot_race_starts, pot_braking, pot_tire_management, pot_defending, pot_wet_weather,
                    pot_consistency, pot_fuel_efficiency, pot_technical_understanding, pot_communication, pot_marketability
                ) VALUES (
                    ?, ?, ?, ?, 'STANDARD', ?, ?,
                    ?, ?, ?, ?, ?,
                    '', 1, 'P1 / 10', '', 0.0,
                    ?, 80.0, ?, ?, ?, ?, ?, ?,
                    50, 50, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?
                );
                """,
                    (
                        name,
                        age,
                        nat,
                        tier,
                        patience,
                        patience,
                        pref,
                        exp_sal,
                        exp_bon,
                        exp_role,
                        exp_seasons,
                        pot,
                        pace,
                        starts,
                        braking,
                        tires,
                        defending,
                        wet,
                        tech,
                        comm,
                        mkt,
                        min(99, pot + 2),
                        min(99, pot + 2),
                        min(99, pot + 2),
                        min(99, pot + 2),
                        min(99, pot + 2),
                        min(99, pot + 2),
                        min(99, pot + 2),
                        min(99, pot + 2),
                        min(99, pot + 4),
                        min(99, pot + 4),
                        min(99, pot + 4),
                    ),
                )

            # 2. Generate 6 Pay-Drivers (PAY_DRIVER) - Very Common!
            # Rule: Worse driver/potential -> Bigger sponsor deal! (2x to 3x multiplier scaled by tier)
            for _ in range(6):
                name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
                age = random.randint(19, 29)
                nat = random.choice(NATIONALITIES)

                # Random skill variance: some okay, some awful
                skill_offset = random.randint(-18, 2)

                pot = max(38, min(80, base_skill + skill_offset + random.randint(4, 10)))
                cur_skill = max(18, min(pot, base_skill + skill_offset))

                patience = random.randint(3, 5)
                pref = "BALANCED"

                # Pay-Driver Title Sponsor calculation (2.0x to 3.0x standard sponsor payout)
                tier_spon_base = BALANCE_REGISTRY.get_pay_driver_base_income(tier)
                # Inverse correlation: Lower skill = Richer billionaire backer
                deficiency_boost = max(1.0, 1.0 + ((base_skill - cur_skill) / float(max(1, base_skill))) * 1.5)
                sponsor_per_race = round(tier_spon_base * deficiency_boost * random.uniform(0.9, 1.25), -2)
                sponsor_name = random.choice(sponsor_brands)

                # Pay-driver expects almost $0 salary or minimal token fee
                exp_sal = 0.0
                exp_bon = 0.0
                exp_role = "EQUAL"
                exp_seasons = random.randint(1, 3)

                pace = max(15, min(80, cur_skill + random.randint(-4, 4)))
                starts = max(15, min(80, cur_skill + random.randint(-4, 4)))
                braking = max(15, min(80, cur_skill + random.randint(-4, 4)))
                tires = max(15, min(80, cur_skill + random.randint(-4, 4)))
                defending = max(15, min(80, cur_skill + random.randint(-4, 4)))
                wet = max(15, min(80, cur_skill + random.randint(-4, 4)))
                tech = max(15, min(80, cur_skill + random.randint(-4, 4)))
                comm = max(15, min(80, cur_skill + random.randint(-4, 4)))
                mkt = random.randint(55, 95)  # High pay-driver marketability / PR backing

                cur.execute(
                    """
                INSERT INTO driver_market (
                    name, age, nationality, tier, driver_type, patience, current_patience,
                    contract_preference, expected_salary_race, expected_signing_bonus, expected_role, expected_seasons,
                    parent_team_name, parent_team_tier, parent_team_expected_pos, pay_driver_sponsor_name, sponsor_income_per_race,
                    potential, morale, pace, race_starts, braking, tire_management, defending, wet_weather,
                    consistency, fuel_efficiency, technical_understanding, communication, marketability,
                    pot_pace, pot_race_starts, pot_braking, pot_tire_management, pot_defending, pot_wet_weather,
                    pot_consistency, pot_fuel_efficiency, pot_technical_understanding, pot_communication, pot_marketability
                ) VALUES (
                    ?, ?, ?, ?, 'PAY_DRIVER', ?, ?,
                    ?, ?, ?, ?, ?,
                    '', 1, 'P1 / 10', ?, ?,
                    ?, 80.0, ?, ?, ?, ?, ?, ?,
                    50, 50, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?
                );
                """,
                    (
                        name,
                        age,
                        nat,
                        tier,
                        patience,
                        patience,
                        pref,
                        exp_sal,
                        exp_bon,
                        exp_role,
                        exp_seasons,
                        sponsor_name,
                        sponsor_per_race,
                        pot,
                        pace,
                        starts,
                        braking,
                        tires,
                        defending,
                        wet,
                        tech,
                        comm,
                        mkt,
                        min(99, pot + 2),
                        min(99, pot + 2),
                        min(99, pot + 2),
                        min(99, pot + 2),
                        min(99, pot + 2),
                        min(99, pot + 2),
                        min(99, pot + 2),
                        min(99, pot + 2),
                        min(99, pot + 4),
                        min(99, pot + 4),
                        min(99, pot + 4),
                    ),
                )

            # 3. Generate 3 Sponsored Loan Drivers (SPONSORED_DRIVER)
            # Youth talents from other constructors; pays you fee; 1-year contract; accelerated growth from parent team facilities
            for _ in range(3):
                name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
                age = random.randint(18, 22)
                nat = random.choice(NATIONALITIES)

                parent_info = random.choice(parent_constructor_catalogs)
                pot = max(65, min(95, base_skill + random.randint(12, 26)))  # High ceiling talent
                cur_skill = max(20, min(pot - 15, base_skill + random.randint(-10, -2)))  # Starts low

                patience = random.randint(3, 4)
                pref = "SHORT_TERM"

                # Youth seat payment: Exactly what player would pay for a seat in this tier & expected position!
                annual_seat_fee = self.get_feeder_seat_market_value(tier, car_rank=car_rank)
                loan_fee_per_race = round((annual_seat_fee / 10.0) * random.uniform(0.92, 1.08), -2)

                exp_sal = 0.0  # Parent team pays their wage

                exp_bon = 0.0
                exp_role = "EQUAL"
                exp_seasons = 1  # Always 1 season loan

                pace = max(18, min(90, cur_skill + random.randint(-3, 3)))
                starts = max(18, min(90, cur_skill + random.randint(-3, 3)))
                braking = max(18, min(90, cur_skill + random.randint(-3, 3)))
                tires = max(18, min(90, cur_skill + random.randint(-3, 3)))
                defending = max(18, min(90, cur_skill + random.randint(-3, 3)))
                wet = max(18, min(90, cur_skill + random.randint(-3, 3)))
                tech = max(18, min(90, cur_skill + random.randint(-3, 3)))
                comm = max(18, min(90, cur_skill + random.randint(-3, 3)))
                mkt = random.randint(35, 75)

                cur.execute(
                    """
                INSERT INTO driver_market (
                    name, age, nationality, tier, driver_type, patience, current_patience,
                    contract_preference, expected_salary_race, expected_signing_bonus, expected_role, expected_seasons,
                    parent_team_name, parent_team_tier, parent_team_expected_pos, pay_driver_sponsor_name, sponsor_income_per_race,
                    potential, morale, pace, race_starts, braking, tire_management, defending, wet_weather,
                    consistency, fuel_efficiency, technical_understanding, communication, marketability,
                    pot_pace, pot_race_starts, pot_braking, pot_tire_management, pot_defending, pot_wet_weather,
                    pot_consistency, pot_fuel_efficiency, pot_technical_understanding, pot_communication, pot_marketability
                ) VALUES (
                    ?, ?, ?, ?, 'SPONSORED_DRIVER', ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, '', ?,
                    ?, 85.0, ?, ?, ?, ?, ?, ?,
                    50, 50, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?
                );
                """,
                    (
                        name,
                        age,
                        nat,
                        tier,
                        patience,
                        patience,
                        pref,
                        exp_sal,
                        exp_bon,
                        exp_role,
                        exp_seasons,
                        parent_info["name"],
                        parent_info["tier"],
                        parent_info["pos"],
                        loan_fee_per_race,
                        pot,
                        pace,
                        starts,
                        braking,
                        tires,
                        defending,
                        wet,
                        tech,
                        comm,
                        mkt,
                        min(99, pot + 2),
                        min(99, pot + 2),
                        min(99, pot + 2),
                        min(99, pot + 2),
                        min(99, pot + 2),
                        min(99, pot + 2),
                        min(99, pot + 2),
                        min(99, pot + 2),
                        min(99, pot + 4),
                        min(99, pot + 4),
                        min(99, pot + 4),
                    ),
                )

            conn.commit()

    def evaluate_contract_offer(
        self,
        driver: Dict[str, Any],
        offer: Dict[str, Any],
        team_tier: int,
        car_rank: int = 5,
        is_homegrown: bool = False,
        main_team_seasons: int = 0,
    ) -> Dict[str, Any]:
        """
        Evaluates a contract proposal against driver preferences, patience, skill vs car performance delta,
        and decaying homegrown academy loyalty discounts.
        """
        current_patience = driver.get("current_patience", driver.get("patience", 3))
        d_type = driver.get("driver_type", "STANDARD")
        pref = driver.get("contract_preference", "BALANCED")

        offered_seasons = int(offer.get("seasons", 1))
        offered_sal = float(offer.get("salary_per_race", 0.0))
        offered_bon = float(offer.get("signing_bonus", 0.0))
        offered_role = offer.get("role_status", "EQUAL")

        # 1. Base Expectations
        base_sal = float(driver.get("expected_salary_race", 25000.0) or 25000.0)
        base_bon = float(driver.get("expected_signing_bonus", 80000.0) or 80000.0)
        expected_role = driver.get("expected_role", "EQUAL")

        # 2. Homegrown Academy Loyalty Discount (80% base discount -> decays to 0% over 6 seasons)
        loyalty_discount = 0.0
        if is_homegrown:
            loyalty_discount = max(0.0, 0.80 - min(6, main_team_seasons) * 0.16)
            base_sal = max(1000.0, base_sal * (1.0 - loyalty_discount))
            base_bon = max(0.0, base_bon * (1.0 - loyalty_discount))

        # 3. Car Performance & Standing Delta (Top car = discounts; Bottom car = heavy markup)
        # car_rank 1-3 -> -20% demands, car_rank 7-10 -> +35% demands
        perf_factor = 1.0 + (car_rank - 5) * 0.08
        req_sal = base_sal * perf_factor
        req_bon = base_bon * perf_factor

        # 4. Special Case: SPONSORED_DRIVER (Fixed 1 season, $0 salary)
        if d_type == "SPONSORED_DRIVER":
            if offered_seasons != 1:
                return {
                    "accepted": False,
                    "walked_away": False,
                    "patience_left": current_patience,
                    "quote": "Our parent academy only authorizes a strict 1-Season Loan contract.",
                    "satisfaction_score": 0.5,
                }
            return {
                "accepted": True,
                "walked_away": False,
                "patience_left": current_patience,
                "quote": f"Deal accepted! {driver['name']} is ready for a 1-season loan from {driver.get('parent_team_name', 'Parent Academy')}.",
                "satisfaction_score": 1.5,
            }

        # 5. Special Case: PAY_DRIVER (Salary ~0, focused on getting the drive)
        if d_type == "PAY_DRIVER":
            if offered_sal >= 0:
                return {
                    "accepted": True,
                    "walked_away": False,
                    "patience_left": current_patience,
                    "quote": f"Deal sealed! Backers at {driver.get('pay_driver_sponsor_name', 'Title Sponsor')} will transfer sponsorship funds immediately.",
                    "satisfaction_score": 1.5,
                }

        # 6. Standard Driver Evaluation Score
        sal_ratio = offered_sal / max(1.0, req_sal)
        bon_ratio = (offered_bon / max(1.0, req_bon)) if req_bon > 0 else 1.0

        role_mult = 1.0
        if expected_role == "#1" and offered_role == "#2":
            role_mult = 0.55
        elif expected_role == "#1" and offered_role == "EQUAL":
            role_mult = 0.88
        elif offered_role == "#1":
            role_mult = 1.18

        seasons_mult = 1.0
        if pref == "SHORT_TERM" and offered_seasons > 2:
            seasons_mult = 0.80
        elif pref == "LONG_TERM" and offered_seasons < 3:
            seasons_mult = 0.80
        elif pref == "BONUS_SEEKER":
            sal_ratio *= 0.85
            bon_ratio *= 1.30

        total_score = (sal_ratio * 0.60 + bon_ratio * 0.40) * role_mult * seasons_mult

        if total_score >= 0.95:
            # Accepted
            return {
                "accepted": True,
                "walked_away": False,
                "patience_left": current_patience,
                "quote": "Terms look fantastic. Let's get out on track and win races!",
                "satisfaction_score": total_score,
            }
        else:
            # Rejection - Decrement Patience
            new_patience = current_patience - 1
            if driver.get("id"):
                with self.db.get_connection() as conn:
                    conn.cursor().execute(
                        "UPDATE driver_market SET current_patience = ? WHERE id = ?;", (new_patience, driver["id"])
                    )
                    conn.commit()

            if new_patience <= 0:
                return {
                    "accepted": False,
                    "walked_away": True,
                    "patience_left": 0,
                    "quote": "My patience is exhausted with these lowball offers. Negotiations are over.",
                    "satisfaction_score": total_score,
                }

            # Detailed Feedback Quotes
            if role_mult < 0.80:
                quote = "I consider myself a team leader. I expect #1 Driver priority to race for this team."
            elif sal_ratio < 0.80:
                quote = (
                    f"The per-race salary is below my market rate (${req_sal:,.0f}/race expected for this machinery)."
                )
            elif bon_ratio < 0.70:
                quote = f"The signing bonus is lacking. I need at least ${req_bon:,.0f} upfront."
            elif seasons_mult < 0.90:
                quote = f"Contract duration doesn't match my career plan ({'1-2 years' if pref == 'SHORT_TERM' else '3+ years'} preferred)."
            else:
                quote = "We're close, but the overall package needs a slight financial bump."

            return {
                "accepted": False,
                "walked_away": False,
                "patience_left": new_patience,
                "quote": quote,
                "satisfaction_score": total_score,
            }

    def finalize_driver_contract(
        self,
        team_id: int,
        car_slot: int,
        driver: Dict[str, Any],
        contract: Dict[str, Any],
        is_homegrown: bool = False,
        main_team_seasons: int = 0,
    ) -> Tuple[bool, str]:
        """
        Signs or renews a driver contract, assigns them to Car #1 or Car #2,
        deducts signing bonus, applies special driver sponsor bindings, and removes from market.
        """
        bonus = float(contract.get("signing_bonus", 0.0))
        salary = float(contract.get("salary_per_race", 25000.0))
        seasons = int(contract.get("seasons", 1))
        role = contract.get("role_status", "EQUAL")

        with self.db.get_connection() as conn:
            cur = conn.cursor()

            # Check for existing driver in car slot and calculate buyout cost
            cur.execute(
                "SELECT * FROM drivers WHERE team_id = ? AND is_academy_driver = 0 ORDER BY is_player_driver DESC, id ASC;",
                (team_id,),
            )
            primary_drivers = [dict(r) for r in cur.fetchall()]
            target_idx = car_slot - 1
            displaced = primary_drivers[target_idx] if target_idx < len(primary_drivers) else None

            buyout_cost = self.get_driver_buyout_cost(displaced) if displaced else 0.0
            total_upfront = bonus + buyout_cost

            # Check team cash for total upfront costs
            cur.execute("SELECT cash FROM teams WHERE id = ?;", (team_id,))
            team_cash = float(cur.fetchone()[0] or 0.0)

            if total_upfront > 0 and team_cash < total_upfront:
                buyout_note = (
                    f" (including ${buyout_cost:,.0f} contract buyout for {displaced['name']})"
                    if buyout_cost > 0
                    else ""
                )
                return False, f"Insufficient funds to pay ${total_upfront:,.0f} upfront{buyout_note}."

            # Deduct signing bonus
            if bonus > 0:
                cur.execute("UPDATE teams SET cash = cash - ? WHERE id = ?;", (bonus, team_id))
                cur.execute(
                    """
                INSERT INTO ledger (team_id, week, category, description, amount)
                VALUES (?, 1, 'CONTRACTS', ?, ?);
                """,
                    (team_id, f"Signed {driver['name']} Signing Bonus", -bonus),
                )

            # Deduct buyout severance if replacing a contracted driver
            if buyout_cost > 0 and displaced:
                cur.execute("UPDATE teams SET cash = cash - ? WHERE id = ?;", (buyout_cost, team_id))
                cur.execute(
                    """
                INSERT INTO ledger (team_id, week, category, description, amount)
                VALUES (?, 1, 'CONTRACTS', ?, ?);
                """,
                    (team_id, f"Contract Buyout Severance for {displaced['name']}", -buyout_cost),
                )

            # Displace existing driver in car slot
            if displaced:
                cur.execute(
                    """
                SELECT COUNT(*),
                       SUM(CASE WHEN position = 1 THEN 1 ELSE 0 END),
                       SUM(CASE WHEN position <= 3 THEN 1 ELSE 0 END),
                       SUM(points)
                FROM series_race_results
                WHERE (driver_id = ? OR driver_name = ?) AND team_id = ?;
                """,
                    (displaced["id"], displaced["name"], team_id),
                )
                stat_row = cur.fetchone()
                starts = stat_row[0] if stat_row and stat_row[0] else 0
                wins = stat_row[1] if stat_row and stat_row[1] else 0
                pods = stat_row[2] if stat_row and stat_row[2] else 0
                pts = stat_row[3] if stat_row and stat_row[3] else 0

                curr_s = self.db.get_current_season_num()
                self.db.record_team_alumni(
                    player_team_id=team_id,
                    driver_id=displaced["id"],
                    driver_name=displaced["name"],
                    departure_reason="REPLACED",
                    departure_season=curr_s,
                    starts_with_team=starts,
                    wins_with_team=wins,
                    podiums_with_team=pods,
                    points_with_team=pts,
                )
                cur.execute(
                    "UPDATE drivers SET team_id = NULL, is_player_driver = 0, contract_races_left = 0 WHERE id = ?;",
                    (displaced["id"],),
                )

            # Free feeder market seat if driver was academy graduate
            if driver.get("is_academy_driver"):
                cur.execute(
                    """
                UPDATE feeder_market_seats 
                SET is_occupied = 0, occupant_team_id = NULL, occupant_driver_id = NULL, occupant_driver_name = ''
                WHERE occupant_driver_id = ?;
                """,
                    (driver["id"],),
                )
                cur.execute("DELETE FROM drivers WHERE id = ?;", (driver["id"],))

            # Insert newly contracted driver
            d_num = driver.get("number") or random.randint(10, 99)
            cur.execute(
                """
            INSERT INTO drivers (
                team_id, name, age, number, is_player_driver, is_academy_driver,
                salary_per_race, contract_races_left, contract_seasons_left, signing_bonus,
                role_status, contract_preference, is_homegrown, main_team_seasons,
                driver_type, parent_team_name, parent_team_tier, parent_team_expected_pos,
                pay_driver_sponsor_name, sponsor_income_per_race,
                potential, morale, pace, race_starts, braking, tire_management, defending, wet_weather,
                consistency, fuel_efficiency, technical_understanding, communication, marketability,
                pot_pace, pot_race_starts, pot_braking, pot_tire_management, pot_defending, pot_wet_weather,
                pot_consistency, pot_fuel_efficiency, pot_technical_understanding, pot_communication, pot_marketability
            ) VALUES (
                ?, ?, ?, ?, ?, 0,
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?
            );
            """,
                (
                    team_id,
                    driver["name"],
                    driver["age"],
                    d_num,
                    1 if car_slot == 1 else 0,
                    salary,
                    seasons * 10,
                    seasons,
                    bonus,
                    role,
                    driver.get("contract_preference", "BALANCED"),
                    1 if is_homegrown else 0,
                    main_team_seasons,
                    driver.get("driver_type", "STANDARD"),
                    driver.get("parent_team_name", ""),
                    driver.get("parent_team_tier", 1),
                    driver.get("parent_team_expected_pos", "P1 / 10"),
                    driver.get("pay_driver_sponsor_name", ""),
                    driver.get("sponsor_income_per_race", 0.0),
                    driver["potential"],
                    driver.get("morale", 85.0),
                    driver["pace"],
                    driver["race_starts"],
                    driver["braking"],
                    driver["tire_management"],
                    driver["defending"],
                    driver["wet_weather"],
                    driver.get("consistency", 50),
                    driver.get("fuel_efficiency", 50),
                    driver["technical_understanding"],
                    driver["communication"],
                    driver["marketability"],
                    driver.get("pot_pace") or min(99, driver["potential"] + 2),
                    driver.get("pot_race_starts") or min(99, driver["potential"] + 2),
                    driver.get("pot_braking") or min(99, driver["potential"] + 2),
                    driver.get("pot_tire_management") or min(99, driver["potential"] + 2),
                    driver.get("pot_defending") or min(99, driver["potential"] + 2),
                    driver.get("pot_wet_weather") or min(99, driver["potential"] + 2),
                    driver.get("pot_consistency") or min(99, driver["potential"] + 2),
                    driver.get("pot_fuel_efficiency") or min(99, driver["potential"] + 2),
                    driver.get("pot_technical_understanding") or min(99, driver["potential"] + 4),
                    driver.get("pot_communication") or min(99, driver["potential"] + 4),
                    driver.get("pot_marketability") or min(99, driver["potential"] + 4),
                ),
            )

            # Remove from driver_market if it came from market pool
            if driver.get("id") and not driver.get("is_academy_driver"):
                cur.execute("DELETE FROM driver_market WHERE id = ?;", (driver["id"],))

            conn.commit()

        return True, f"Successfully signed {driver['name']} to Car #{car_slot} on a {seasons}-Season Contract!"

    def refresh_scout_search(self, team_id: int, scout_cost: float = 15000.0) -> Tuple[bool, str]:
        """Deducts scouting search fee, regenerates candidate prospects, and triggers dynamic feeder seat market turnover."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT cash FROM teams WHERE id = ?;", (team_id,))
            cash = float(cur.fetchone()[0])
            if cash < scout_cost:
                return False, f"Insufficient funds for scout mission (${scout_cost:,.0f} needed)."

            # Deduct scouting fee
            cur.execute("UPDATE teams SET cash = cash - ? WHERE id = ?;", (scout_cost, team_id))
            cur.execute(
                """
            INSERT INTO ledger (team_id, week, category, description, amount)
            VALUES (?, 1, 'SCOUTING', 'Dispatched Global Talent Scout Search', ?);
            """,
                (team_id, -scout_cost),
            )
            conn.commit()

        # Simulate feeder market turnover
        self.simulate_feeder_market_turn(force_events=2)
        self._generate_scout_prospects(team_id, count=4)
        return True, "Scout search completed! New young prospects & updated feeder market seats available."

    def simulate_feeder_market_turn(self, force_events: int = 1):
        """
        Simulates weekly/monthly dynamic living feeder market events:
        - Rival constructor academies take seats or release drivers.
        - Occasional bargain opportunities or prestige seats open up at random.
        """
        with self.db.get_connection() as conn:
            cur = conn.cursor()

            for _ in range(force_events):
                # 1. 50% chance an open seat gets signed by rival academy
                cur.execute(
                    "SELECT id, team_name, tier FROM feeder_market_seats WHERE is_occupied = 0 AND occupant_team_id IS NULL;"
                )
                open_seats = cur.fetchall()
                if open_seats and random.random() < 0.50:
                    target_seat = random.choice(open_seats)
                    ai_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
                    cur.execute(
                        """
                    UPDATE feeder_market_seats 
                    SET is_occupied = 1, occupant_driver_name = ? 
                    WHERE id = ?;
                    """,
                        (ai_name, target_seat["id"]),
                    )

            # Dynamic Team Policy & Admission Shifts (Randomness: Generous top teams, demanding backmarkers)
            if random.random() < 0.35:
                cur.execute("SELECT id, tier, rating, team_name, base_cost FROM feeder_market_seats;")
                all_s = cur.fetchall()
                if all_s:
                    shuffled_seat = random.choice(all_s)
                    s_id, s_tier, s_rating, s_tname, s_cost = (
                        shuffled_seat["id"],
                        shuffled_seat["tier"],
                        shuffled_seat["rating"],
                        shuffled_seat["team_name"],
                        shuffled_seat["base_cost"],
                    )

                    policy_roll = random.random()
                    if s_rating >= 4 and policy_roll < 0.30:
                        # Generous / Free Top Team (Surprise Opportunity!)
                        new_note = "Open Admission: Free Entry Academy"
                        cur.execute(
                            """
                        UPDATE feeder_market_seats 
                        SET min_pace = 18, min_overall = 18, pricing_note = ? 
                        WHERE id = ?;
                        """,
                            (new_note, s_id),
                        )
                    elif s_rating <= 2 and policy_roll < 0.30:
                        # Demanding / Pretentious Backmarker (Quirky Team Boss!)
                        demanded_pace = 38 if s_tier == 4 else (45 if s_tier == 3 else 30)
                        new_note = f"Pretentious Boss: Demands Pace {demanded_pace}+"
                        cur.execute(
                            """
                        UPDATE feeder_market_seats 
                        SET min_pace = ?, min_overall = ?, pricing_note = ? 
                        WHERE id = ?;
                        """,
                            (demanded_pace, demanded_pace - 2, new_note, s_id),
                        )

            # Slight market price fluctuations (+-4%)
            cur.execute("""
            UPDATE feeder_market_seats 
            SET current_cost = ROUND(base_cost * (0.94 + (abs(random()) % 13) / 100.0), 0);
            """)
            conn.commit()

    def _lookup_seat_by_id_or_name(self, seat_identifier: Any) -> Optional[Dict[str, Any]]:
        """Looks up a feeder seat from the database by ID or team name."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            if isinstance(seat_identifier, int) or (isinstance(seat_identifier, str) and seat_identifier.isdigit()):
                cur.execute("SELECT * FROM feeder_market_seats WHERE id = ?;", (int(seat_identifier),))
                row = cur.fetchone()
            else:
                cur.execute(
                    "SELECT * FROM feeder_market_seats WHERE team_name = ? AND is_occupied = 0 LIMIT 1;",
                    (str(seat_identifier),),
                )
                row = cur.fetchone()
                if not row:
                    cur.execute(
                        "SELECT * FROM feeder_market_seats WHERE team_name = ? LIMIT 1;", (str(seat_identifier),)
                    )
                    row = cur.fetchone()

            return dict(row) if row else None

    def sign_young_driver(
        self, team_id: int, prospect_id: int, target_seat_id_or_name: Any = "JTS Academy Blue"
    ) -> Tuple[bool, str]:
        """
        Signs a scouted candidate into the Junior Academy and purchases a specific open sponsored seat in a feeder team.
        Locks the seat so no other driver can occupy it.
        """
        seat = self._lookup_seat_by_id_or_name(target_seat_id_or_name)
        if not seat:
            # Fallback to first open seat
            available = self.get_available_feeder_seats(3)
            seat = available[0] if available else None
            if not seat:
                return False, "No open feeder seats available in lower divisions."

        with self.db.get_connection() as conn:
            cur = conn.cursor()

            # Check constructor tier vs feeder tier
            cur.execute("SELECT tier, cash FROM teams WHERE id = ?;", (team_id,))
            team_row = cur.fetchone()
            team_tier = int(team_row[0]) if team_row else 3
            cash = float(team_row[1]) if team_row else 0.0

            if seat["tier"] <= team_tier:
                return (
                    False,
                    f"Academy drivers can only race in feeder tiers below your constructor tier (Tier {team_tier + 1} to Tier 5).",
                )

            cur.execute("SELECT * FROM scout_prospects WHERE id = ? AND team_id = ?;", (prospect_id, team_id))
            p = cur.fetchone()
            if not p:
                return False, "Candidate prospect not found."
            p = dict(p)

            # Check eligibility
            ok, reason = self.can_driver_sign_seat(p, seat)
            if not ok:
                return False, reason

            # Calculate live seat cost
            fee = seat.get("cost", seat["current_cost"])
            if cash < fee:
                return (
                    False,
                    f"Insufficient funds to fund this feeder seat (${fee:,.0f} needed, available: ${cash:,.0f}).",
                )

            # Deduct annual seat fee & record ledger
            cur.execute("UPDATE teams SET cash = cash - ? WHERE id = ?;", (fee, team_id))
            cur.execute(
                """
            INSERT INTO ledger (team_id, week, category, description, amount)
            VALUES (?, 1, 'ACADEMY', ?, ?);
            """,
                (team_id, f"Purchased 1-Year Feeder Seat at {seat['team_name']} for {p['name']}", -fee),
            )

            # Determine initial morale
            init_morale = 95.0 if seat["rating"] >= 4 else (82.0 if seat["rating"] == 3 else 68.0)

            # Assign driver number
            d_num = random.randint(30, 99)

            # Extract individual potentials
            pot = p["potential"]
            pot_pace = p.get("pot_pace") or max(p["pace"], min(99, pot + 2))
            pot_starts = p.get("pot_race_starts") or max(p["race_starts"], min(99, pot + 2))
            pot_braking = p.get("pot_braking") or max(p["braking"], min(99, pot + 2))
            pot_tires = p.get("pot_tire_management") or max(p["tire_management"], min(99, pot + 2))
            pot_defending = p.get("pot_defending") or max(p["defending"], min(99, pot + 2))
            pot_wet = p.get("pot_wet_weather") or max(p["wet_weather"], min(99, pot + 2))
            pot_cons = p.get("pot_consistency") or min(99, pot + 2)
            pot_fuel = p.get("pot_fuel_efficiency") or min(99, pot + 2)
            pot_tech = p.get("pot_technical_understanding") or max(p["technical_understanding"], min(99, pot + 4))
            pot_comm = p.get("pot_communication") or max(p["communication"], min(99, pot + 4))
            pot_mkt = p.get("pot_marketability") or max(p["marketability"], min(99, pot + 4))

            # Insert driver into junior academy
            cur.execute(
                """
            INSERT INTO drivers (
                team_id, name, age, number, is_player_driver, is_academy_driver,
                academy_tier_placement, academy_team_name, academy_seat_rating, academy_seat_expected_pos, academy_seat_cost,
                training_focus, salary_per_race, contract_races_left, potential, morale,
                race_starts, braking, pace, consistency, tire_management, defending,
                fuel_efficiency, wet_weather, technical_understanding, communication, marketability,
                pot_pace, pot_race_starts, pot_braking, pot_tire_management, pot_defending, pot_wet_weather,
                pot_consistency, pot_fuel_efficiency, pot_technical_understanding, pot_communication, pot_marketability
            ) VALUES (
                ?, ?, ?, ?, 0, 1,
                ?, ?, ?, ?, ?,
                'BALANCED', 0, 12, ?, ?,
                ?, ?, ?, 50, ?, ?,
                50, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?
            );
            """,
                (
                    team_id,
                    p["name"],
                    p["age"],
                    d_num,
                    seat["tier"],
                    seat["team_name"],
                    seat["rating"],
                    seat.get("expected_pos", "P1 / 10"),
                    fee,
                    p["potential"],
                    init_morale,
                    p["race_starts"],
                    p["braking"],
                    p["pace"],
                    p["tire_management"],
                    p["defending"],
                    p["wet_weather"],
                    p["technical_understanding"],
                    p["communication"],
                    p["marketability"],
                    pot_pace,
                    pot_starts,
                    pot_braking,
                    pot_tires,
                    pot_defending,
                    pot_wet,
                    pot_cons,
                    pot_fuel,
                    pot_tech,
                    pot_comm,
                    pot_mkt,
                ),
            )
            new_driver_id = cur.lastrowid

            # LOCK SEAT IN FEEDER MARKET
            cur.execute(
                """
            UPDATE feeder_market_seats 
            SET is_occupied = 1, occupant_team_id = ?, occupant_driver_id = ?, occupant_driver_name = ?
            WHERE id = ?;
            """,
                (team_id, new_driver_id, p["name"], seat["id"]),
            )

            # Remove prospect from scouting board
            cur.execute("DELETE FROM scout_prospects WHERE id = ?;", (prospect_id,))
            conn.commit()

            return (
                True,
                f"Signed {p['name']} to {seat['team_name']} (Exp: {seat.get('expected_pos', 'P1 / 10')} | {seat['status']}) for ${fee:,.0f}/yr!",
            )

    def transfer_academy_driver_seat(
        self, team_id: int, driver_id: int, target_seat_id_or_name: Any
    ) -> Tuple[bool, str]:
        """
        Transfers a signed academy driver to a different open feeder team seat.
        Frees up old seat and occupies the new seat.
        """
        new_seat = self._lookup_seat_by_id_or_name(target_seat_id_or_name)
        if not new_seat:
            return False, "Target feeder team seat not found."

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT tier, cash FROM teams WHERE id = ?;", (team_id,))
            team_row = cur.fetchone()
            team_tier = int(team_row[0]) if team_row else 3
            cash = float(team_row[1]) if team_row else 0.0

            if new_seat["tier"] <= team_tier:
                return False, f"Feeder seat must be in a tier below your constructor (Tier {team_tier + 1} to Tier 5)."

            # Get driver details
            cur.execute(
                "SELECT * FROM drivers WHERE id = ? AND team_id = ? AND is_academy_driver = 1;", (driver_id, team_id)
            )
            d_row = cur.fetchone()
            if not d_row:
                return False, "Academy driver not found."
            driver = dict(d_row)

            # Check eligibility
            ok, reason = self.can_driver_sign_seat(driver, new_seat)
            if not ok:
                return False, reason

            # Calculate price difference
            old_cost = float(driver.get("academy_seat_cost", 0.0) or 0.0)
            new_cost = float(new_seat.get("cost", new_seat["current_cost"]))
            cost_diff = new_cost - old_cost

            if cost_diff > 0 and cash < cost_diff:
                return False, f"Insufficient funds to upgrade seat (${cost_diff:,.0f} upgrade fee required)."

            if cost_diff > 0:
                cur.execute("UPDATE teams SET cash = cash - ? WHERE id = ?;", (cost_diff, team_id))
                cur.execute(
                    """
                INSERT INTO ledger (team_id, week, category, description, amount)
                VALUES (?, 1, 'ACADEMY', ?, ?);
                """,
                    (team_id, f"Upgraded {driver['name']} Feeder Seat to {new_seat['team_name']}", -cost_diff),
                )

            # 1. FREE OLD SEAT
            cur.execute(
                """
            UPDATE feeder_market_seats 
            SET is_occupied = 0, occupant_team_id = NULL, occupant_driver_id = NULL, occupant_driver_name = ''
            WHERE occupant_driver_id = ?;
            """,
                (driver_id,),
            )

            # 2. OCCUPY NEW SEAT
            cur.execute(
                """
            UPDATE feeder_market_seats 
            SET is_occupied = 1, occupant_team_id = ?, occupant_driver_id = ?, occupant_driver_name = ?
            WHERE id = ?;
            """,
                (team_id, driver_id, driver["name"], new_seat["id"]),
            )

            # 3. Update driver placement
            new_morale = 95.0 if new_seat["rating"] >= 4 else (82.0 if new_seat["rating"] == 3 else 68.0)
            cur.execute(
                """
            UPDATE drivers 
            SET academy_tier_placement = ?, academy_team_name = ?, academy_seat_rating = ?,
                academy_seat_expected_pos = ?, academy_seat_cost = ?, morale = ?
            WHERE id = ?;
            """,
                (
                    new_seat["tier"],
                    new_seat["team_name"],
                    new_seat["rating"],
                    new_seat.get("expected_pos", "P1 / 10"),
                    new_cost,
                    new_morale,
                    driver_id,
                ),
            )
            conn.commit()

            return (
                True,
                f"Successfully transferred {driver['name']} to {new_seat['team_name']} (Exp: {new_seat.get('expected_pos', 'P1 / 10')})!",
            )

    def promote_young_driver_to_race_seat(
        self, team_id: int, academy_driver_id: int, car_slot: int = 1
    ) -> Tuple[bool, str]:
        """
        Promotes a young academy driver directly into a primary race seat (Car #1 or Car #2).
        Frees their feeder team seat.
        """
        with self.db.get_connection() as conn:
            cur = conn.cursor()

            cur.execute(
                "SELECT * FROM drivers WHERE id = ? AND team_id = ? AND is_academy_driver = 1;",
                (academy_driver_id, team_id),
            )
            young_d = cur.fetchone()
            if not young_d:
                return False, "Young academy driver not found."

            cur.execute(
                "SELECT * FROM drivers WHERE team_id = ? AND is_academy_driver = 0 ORDER BY is_player_driver DESC, id ASC;",
                (team_id,),
            )
            primary_drivers = cur.fetchall()

            target_idx = car_slot - 1
            if target_idx < len(primary_drivers):
                displaced = primary_drivers[target_idx]
                cur.execute("DELETE FROM drivers WHERE id = ?;", (displaced["id"],))

            # Free their feeder seat
            cur.execute(
                """
            UPDATE feeder_market_seats 
            SET is_occupied = 0, occupant_team_id = NULL, occupant_driver_id = NULL, occupant_driver_name = ''
            WHERE occupant_driver_id = ?;
            """,
                (academy_driver_id,),
            )

            cur.execute(
                """
            UPDATE drivers 
            SET is_academy_driver = 0, academy_tier_placement = NULL, academy_team_name = '',
                is_player_driver = ?, salary_per_race = 5000, contract_races_left = 10
            WHERE id = ?;
            """,
                (1 if car_slot == 1 else 0, academy_driver_id),
            )
            conn.commit()

            return True, f"Successfully promoted {young_d['name']} to Car #{car_slot} Primary Race Seat!"

    def release_young_driver(self, team_id: int, driver_id: int) -> Tuple[bool, str]:
        """Releases an academy driver from the team and frees their feeder seat."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM drivers WHERE id = ? AND team_id = ?;", (driver_id, team_id))
            row = cur.fetchone()
            if not row:
                return False, "Driver not found."

            # Free occupied feeder seat
            cur.execute(
                """
            UPDATE feeder_market_seats 
            SET is_occupied = 0, occupant_team_id = NULL, occupant_driver_id = NULL, occupant_driver_name = ''
            WHERE occupant_driver_id = ?;
            """,
                (driver_id,),
            )

            cur.execute("DELETE FROM drivers WHERE id = ?;", (driver_id,))
            conn.commit()

            return True, f"Released young driver {row['name']} from Junior Academy."

    def process_weekly_driver_development(
        self, team_id: int, player_race_pos: Optional[int] = None, driver_growth_mult: float = 1.0
    ):
        """
        Advances driver attribute development across 8 driving stats & 3 mental stats:
        - Each of the 8 driving stats follows an independent parabolic curve:
          - Ages <= 28: Grows towards individual max potential.
            - Rate depends heavily on finish result (winning gives high boost, finishing high > tier),
              championship tier, facility quality, and age (younger = faster).
            - Even if you always lose, drivers still develop naturally until 28 (positive base floor).
          - Ages 28-30: Peak prime plateau (stable).
          - Ages > 30: Starts declining gradually from 30 onwards.
        - 3 Mental stats (technical_understanding, communication, marketability):
          - CAN ONLY GO UP! Never decline with age.
        """
        with self.db.get_connection() as conn:
            cur = conn.cursor()

            # Fetch team tier
            cur.execute("SELECT tier FROM teams WHERE id = ?;", (team_id,))
            t_row = cur.fetchone()
            team_tier = t_row[0] if t_row else 3

            tier_mults = {1: 1.35, 2: 1.20, 3: 1.10, 4: 1.00, 5: 0.90}

            # Query unlocked facility tiers
            cur.execute(
                """
            SELECT node_id, current_tier FROM team_facilities
            WHERE team_id = ? AND is_unlocked = 1;
            """,
                (team_id,),
            )
            fac_tiers = {r[0]: r[1] for r in cur.fetchall()}

            # Query active equipment levels
            cur.execute(
                """
            SELECT fe.node_id, te.current_level
            FROM facility_equipment fe
            JOIN team_equipment te ON fe.id = te.equipment_id
            WHERE te.team_id = ? AND te.is_active = 1 AND te.current_level > 0;
            """,
                (team_id,),
            )
            eq_rows = cur.fetchall()
            eq_levels = {}
            for r in eq_rows:
                eq_levels[r[0]] = eq_levels.get(r[0], 0) + r[1]

            sim_tier = fac_tiers.get("driver_sim", 0)
            motion_tier = fac_tiers.get("driver_motion_sim", 0)
            vr_tier = fac_tiers.get("driver_vr_cognitive", 0)
            gym_tier = fac_tiers.get("driver_gym_conditioning", 0)
            physio_tier = fac_tiers.get("driver_physio_recovery", 0)
            media_tier = fac_tiers.get("driver_media_pr_coach", 0)
            radio_tier = fac_tiers.get("driver_radio_comms_lab", 0)
            comm_suite_tier = fac_tiers.get("driver_commercial_suite", 0)
            bootcamp_tier = fac_tiers.get("driver_f4_bootcamp", 0)

            # Equipment bonuses
            motion_eq = eq_levels.get("driver_motion_sim", 0)
            vr_eq = eq_levels.get("driver_vr_cognitive", 0)
            gym_eq = eq_levels.get("driver_gym_conditioning", 0)
            physio_eq = eq_levels.get("driver_physio_recovery", 0)
            media_eq = eq_levels.get("driver_media_pr_coach", 0)
            radio_eq = eq_levels.get("driver_radio_comms_lab", 0)
            comm_suite_eq = eq_levels.get("driver_commercial_suite", 0)
            bootcamp_eq = eq_levels.get("driver_f4_bootcamp", 0)

            # Global driver XP multiplier from Motion Sim
            motion_xp_mult = 1.0 + (motion_tier * 0.25) + (motion_eq * 0.04)

            # 1. Primary Race Drivers
            cur.execute("SELECT * FROM drivers WHERE team_id = ? AND is_academy_driver = 0;", (team_id,))
            primary = cur.fetchall()
            for d_row in primary:
                d = dict(d_row)
                d_id = d["id"]
                age = d.get("age", 24)
                base_pot = d.get("potential", 75)

                # Determine finish pos multiplier
                pos = player_race_pos if player_race_pos is not None else random.randint(4, 10)
                if pos == 1:
                    pos_mult = 3.0
                elif pos <= 3:
                    pos_mult = 2.2
                elif pos <= 6:
                    pos_mult = 1.6
                elif pos <= 10:
                    pos_mult = 1.2
                elif pos <= 16:
                    pos_mult = 0.85
                else:
                    pos_mult = 0.55

                tier_mult = tier_mults.get(team_tier, 1.0)
                fac_mult = 1.15 * motion_xp_mult

                # Sponsored Driver Parent Constructor Facility Development Boost
                sponsored_mult = 1.0
                if d.get("driver_type") == "SPONSORED_DRIVER":
                    p_tier = d.get("parent_team_tier", 1) or 1
                    p_exp = d.get("parent_team_expected_pos", "P1 / 10") or "P1 / 10"
                    p_rank = 1
                    if "P" in p_exp:
                        try:
                            p_rank = int(p_exp.split("/")[0].replace("P", "").strip())
                        except Exception:
                            p_rank = 1
                    t_score = {1: 1.6, 2: 1.35, 3: 1.15, 4: 1.0, 5: 0.9}.get(p_tier, 1.3)
                    r_score = max(1.0, 1.6 - (p_rank - 1) * 0.08)
                    sponsored_mult = t_score * r_score

                updates = {}

                # 8 Driving Stats Progression
                for s in DRIVING_STATS:
                    cur_val = float(d.get(s, 50) or 50)
                    max_pot = d.get(f"pot_{s}") or min(99, base_pot + 2)

                    # Specialized facility stat multipliers
                    stat_mult = 1.0
                    if s in ["race_starts", "defending", "consistency"]:
                        # Boosted by Neuro-Cognitive Reflex Lab
                        stat_mult += (vr_tier * 0.30) + (vr_eq * 0.05)
                    elif s in ["tire_management", "wet_weather"]:
                        # Boosted by Biometric Gym & Conditioning
                        stat_mult += (gym_tier * 0.25) + (gym_eq * 0.04)

                    if age <= 28:
                        age_factor = max(0.18, 1.0 - ((age - 15) / 14.0) * 0.55)
                        growth = (
                            0.38
                            * age_factor
                            * pos_mult
                            * tier_mult
                            * fac_mult
                            * driver_growth_mult
                            * sponsored_mult
                            * stat_mult
                        )
                        new_val = min(float(max_pot), cur_val + growth)
                        updates[s] = round(new_val, 2)
                    elif age <= 30:
                        # Peak prime plateau
                        updates[s] = cur_val
                    else:
                        # Gradual decline from 30 onwards, heavily buffered by Physio & Longevity Clinic
                        decay_buffer = max(0.15, 1.0 - (physio_tier * 0.35) - (physio_eq * 0.06))
                        decay = 0.18 * ((age - 30) ** 0.80) * decay_buffer
                        new_val = max(20.0, cur_val - decay)
                        updates[s] = round(new_val, 2)

                # 3 Mental Stats (Technical, Communication, Marketability) - CAN ONLY GO UP!
                for s in MENTAL_STATS:
                    cur_val = float(d.get(s, 50) or 50)
                    max_pot = d.get(f"pot_{s}") or min(99, base_pot + 4)

                    m_stat_mult = 1.0
                    if s == "marketability":
                        # Boosted by Media PR Studio & Commercial Suite
                        m_stat_mult += (
                            (media_tier * 0.35) + (media_eq * 0.05) + (comm_suite_tier * 0.25) + (comm_suite_eq * 0.04)
                        )
                    elif s in ["communication", "technical_understanding"]:
                        # Boosted by Radio Comms Lab
                        m_stat_mult += (radio_tier * 0.35) + (radio_eq * 0.05)

                    mental_growth = 0.25 * pos_mult * tier_mult * driver_growth_mult * sponsored_mult * m_stat_mult
                    new_val = min(float(max_pot), cur_val + mental_growth)
                    updates[s] = round(new_val, 2)

                # Update driver in database
                set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
                params = list(updates.values()) + [d_id]
                cur.execute(f"UPDATE drivers SET {set_clause} WHERE id = ?;", params)

            # 2. Academy Drivers in Feeder Teams
            cur.execute("SELECT * FROM drivers WHERE team_id = ? AND is_academy_driver = 1;", (team_id,))
            academy = cur.fetchall()
            for d_row in academy:
                d = dict(d_row)
                d_id = d["id"]
                age = d.get("age", 16)
                base_pot = d.get("potential", 75)
                f_tier = d.get("academy_tier_placement", 5) or 5

                # Rule: Auto-release if older than 25
                if age > 25:
                    self.release_young_driver(team_id, d_id)
                    continue

                # Query driver's actual finish position from simulated race results
                cur.execute(
                    """
                SELECT position FROM series_race_results 
                WHERE (driver_id = ? OR driver_name = ?)
                ORDER BY id DESC LIMIT 1;
                """,
                    (d_id, d.get("name", "")),
                )
                last_res = cur.fetchone()

                if last_res:
                    finish_pos = last_res[0]
                    if finish_pos == 1:
                        feeder_pos_mult = 3.2  # Sensational race victory!
                    elif finish_pos <= 3:
                        feeder_pos_mult = 2.4  # Podium finish!
                    elif finish_pos <= 6:
                        feeder_pos_mult = 1.8  # Strong points finish
                    elif finish_pos <= 10:
                        feeder_pos_mult = 1.3  # Top 10 finish
                    elif finish_pos <= 16:
                        feeder_pos_mult = 0.9  # Midfield
                    else:
                        feeder_pos_mult = 0.65  # Backmarker
                else:
                    exp_pos_str = d.get("academy_seat_expected_pos", "P5 / 10")
                    exp_rank = 5
                    if exp_pos_str and "P" in exp_pos_str:
                        try:
                            exp_rank = int(exp_pos_str.split("/")[0].replace("P", "").strip())
                        except Exception:
                            exp_rank = 5

                    if exp_rank == 1:
                        feeder_pos_mult = 2.4
                    elif exp_rank <= 3:
                        feeder_pos_mult = 1.8
                    elif exp_rank <= 6:
                        feeder_pos_mult = 1.2
                    else:
                        feeder_pos_mult = 0.85

                feeder_tier_mult = tier_mults.get(f_tier, 0.95)
                bootcamp_mult = 1.0 + (bootcamp_tier * 0.35) + (bootcamp_eq * 0.05)

                # Every Driver Hub facility provides young driver boosts:
                # - Sim & Motion Sim: Baseline track & cockpit skills
                # - Reflex Lab: Reaction speeds & racecraft
                # - Biometric Gym: Stamina & physical conditioning
                # - Physio Clinic: Injury resilience & athletic foundation
                # - Media Studio: Media poise & public speaking
                # - Radio Lab: Tactical comms & race engineer protocol
                # - Commercial Suite: Early sponsor & partner presentation training
                # - Junior Boot Camp: Feeder Driver XP & single-seater telemetry
                # When facilities are invested in, young drivers become truly overpowered!
                young_sim_boost = 1.0 + (sim_tier * 0.12) + (motion_tier * 0.18) + (motion_eq * 0.03)
                young_gym_boost = 1.0 + (gym_tier * 0.12) + (gym_eq * 0.02)
                young_vr_boost = 1.0 + (vr_tier * 0.15) + (vr_eq * 0.03)
                young_physio_boost = 1.0 + (physio_tier * 0.10) + (physio_eq * 0.02)

                # Prodigy accelerator: young drivers (age <= 20) with high potential (>= 85)
                # gain massive growth velocity once the team invests in driver facilities!
                yd_cfg = BALANCE_REGISTRY.young_driver
                is_prodigy = age <= yd_cfg.prodigy_max_age and base_pot >= yd_cfg.prodigy_potential_threshold
                facility_count = sum([sim_tier, motion_tier, vr_tier, gym_tier, bootcamp_tier])
                # Prodigy boost activates significantly with facility investment:
                # With 0-1 starter facility: modest 1.1x boost (so raw unrefined prodigies don't max out without training)
                # With 4+ facility levels: massive 2.5x+ boost turning them into overpowered aces!
                if is_prodigy:
                    prodigy_mult = 1.05 + (facility_count * yd_cfg.facility_synergy_boost_rate * 1.5)
                else:
                    prodigy_mult = 1.0

                updates = {}
                # 8 Driving Stats Progression for Academy Drivers (boosted by all training facilities)
                for s in DRIVING_STATS:
                    cur_val = float(d.get(s, 40) or 40)
                    max_pot = d.get(f"pot_{s}") or min(99, base_pot + 2)
                    age_factor = max(0.20, 1.0 - ((age - 14) / 14.0) * 0.45)

                    # Dynamic category young driver boosts
                    stat_training_mult = young_sim_boost * young_physio_boost
                    if s in ["race_starts", "defending", "consistency"]:
                        stat_training_mult *= young_vr_boost
                    elif s in ["tire_management", "wet_weather"]:
                        stat_training_mult *= young_gym_boost

                    growth = (
                        0.52
                        * age_factor
                        * feeder_pos_mult
                        * feeder_tier_mult
                        * driver_growth_mult
                        * bootcamp_mult
                        * stat_training_mult
                        * prodigy_mult
                    )
                    new_val = min(float(max_pot), cur_val + growth)
                    updates[s] = round(new_val, 2)

                # 3 Mental Stats Progression (boosted by commercial, radio & media facilities)
                for s in MENTAL_STATS:
                    cur_val = float(d.get(s, 35) or 35)
                    max_pot = d.get(f"pot_{s}") or min(99, base_pot + 4)
                    m_stat_mult = 1.0
                    if s == "marketability":
                        m_stat_mult += (media_tier * 0.25) + (comm_suite_tier * 0.15)
                    elif s in ["communication", "technical_understanding"]:
                        m_stat_mult += (radio_tier * 0.25) + (sim_tier * 0.08)

                    mental_growth = (
                        0.22 * feeder_pos_mult * feeder_tier_mult * driver_growth_mult * bootcamp_mult * m_stat_mult
                    )
                    new_val = min(float(max_pot), cur_val + mental_growth)
                    updates[s] = round(new_val, 2)

                set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
                params = list(updates.values()) + [d_id]
                cur.execute(f"UPDATE drivers SET {set_clause} WHERE id = ?;", params)

            conn.commit()
