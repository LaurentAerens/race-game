import sqlite3
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class CarAttributes:
    """Car performance attributes (values 1 - 100)."""

    engine_power: float = 85.0  # Straight-line speed & acceleration
    aero_downforce: float = 85.0  # High-speed cornering grip & downforce
    braking_efficiency: float = 85.0  # Deceleration power & deep braking zone overtakes
    tire_preservation: float = 85.0  # Chassis tire wear reduction & thermal control
    fuel_efficiency: float = 85.0  # Fuel consumption rate
    reliability: float = 90.0  # Mechanical failure / glitch resistance


@dataclass
class DriverAttributes:
    """Driver skill attributes (values 1 - 100)."""

    speed: float = 85.0
    braking: float = 85.0  # Late-braking & divebomb skill
    cornering: float = 85.0  # Corner apex precision
    overtaking: float = 80.0  # Passing aggression & opportunistic moves
    defending: float = 80.0  # Defensive positioning
    tire_management: float = 80.0  # Tire conservation
    consistency: float = 85.0  # Mistake avoidance & lap time variance
    wet_skill: float = 80.0  # Rain driving mastery


class DatabaseManager:
    """
    Manages SQLite database for persisting fictional team, car, and driver attributes.
    All rosters, names, liveries and statistics are 100% fictional and original.
    """

    def __init__(self, db_path: str = "race_game.db"):
        self.db_path = db_path
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Creates tables and seeds default 10 fictional teams, cars and 20 drivers if empty."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            # 1. Teams Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                color_r INTEGER NOT NULL,
                color_g INTEGER NOT NULL,
                color_b INTEGER NOT NULL,
                is_player INTEGER DEFAULT 0
            )
            """)

            # 2. Car Attributes Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS car_attributes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL UNIQUE,
                engine_power REAL NOT NULL DEFAULT 85.0,
                aero_downforce REAL NOT NULL DEFAULT 85.0,
                braking_efficiency REAL NOT NULL DEFAULT 85.0,
                tire_preservation REAL NOT NULL DEFAULT 85.0,
                fuel_efficiency REAL NOT NULL DEFAULT 85.0,
                reliability REAL NOT NULL DEFAULT 90.0,
                FOREIGN KEY (team_id) REFERENCES teams(id)
            )
            """)

            # 3. Drivers Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS drivers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                code TEXT NOT NULL,
                number INTEGER NOT NULL,
                is_player INTEGER DEFAULT 0,
                speed REAL NOT NULL DEFAULT 85.0,
                braking REAL NOT NULL DEFAULT 85.0,
                cornering REAL NOT NULL DEFAULT 85.0,
                overtaking REAL NOT NULL DEFAULT 80.0,
                defending REAL NOT NULL DEFAULT 80.0,
                tire_management REAL NOT NULL DEFAULT 80.0,
                consistency REAL NOT NULL DEFAULT 85.0,
                wet_skill REAL NOT NULL DEFAULT 80.0,
                FOREIGN KEY (team_id) REFERENCES teams(id)
            )
            """)
            conn.commit()

            cursor.execute("SELECT COUNT(*) as count FROM teams")
            if cursor.fetchone()["count"] == 0:
                self._seed_default_data(conn)
        finally:
            conn.close()

    def reset_and_reseed(self):
        """Forces database reset with fresh fictional rosters."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM drivers")
            cursor.execute("DELETE FROM car_attributes")
            cursor.execute("DELETE FROM teams")
            try:
                cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('teams', 'car_attributes', 'drivers')")
            except Exception:
                # sqlite_sequence table may not exist if no autoincrement keys exist yet
                pass
            conn.commit()
            self._seed_default_data(conn)
        finally:
            conn.close()

    def _seed_default_data(self, conn: sqlite3.Connection):
        """Populates 10 100% original fictional teams and 20 fictional drivers."""
        cursor = conn.cursor()

        teams_data = [
            # Tier 1: Storm Racing Team (Midnight Navy & Orange)
            {
                "name": "Storm Racing Team",
                "color": (20, 40, 140),
                "player": 0,
                "car": {"engine": 98.0, "aero": 98.0, "brakes": 97.0, "tire": 92.0, "fuel": 92.0, "rel": 96.0},
                "drivers": [
                    {
                        "name": "Axel Lindqvist",
                        "code": "LIN",
                        "number": 1,
                        "player": 0,
                        "speed": 99,
                        "braking": 98,
                        "cornering": 98,
                        "overtake": 98,
                        "defend": 97,
                        "tire": 93,
                        "cons": 98,
                        "wet": 98,
                    },
                    {
                        "name": "Javier Morales",
                        "code": "MOR",
                        "number": 33,
                        "player": 0,
                        "speed": 86,
                        "braking": 85,
                        "cornering": 84,
                        "overtake": 85,
                        "defend": 88,
                        "tire": 94,
                        "cons": 83,
                        "wet": 80,
                    },
                ],
            },
            # Tier 1: Scuderia Veloce (Italian Scarlet Red & Gold)
            {
                "name": "Scuderia Veloce",
                "color": (230, 25, 35),
                "player": 0,
                "car": {"engine": 97.0, "aero": 95.0, "brakes": 94.0, "tire": 82.0, "fuel": 84.0, "rel": 88.0},
                "drivers": [
                    {
                        "name": "Lorenzo De Luca",
                        "code": "DEL",
                        "number": 16,
                        "player": 0,
                        "speed": 97,
                        "braking": 96,
                        "cornering": 96,
                        "overtake": 94,
                        "defend": 89,
                        "tire": 82,
                        "cons": 91,
                        "wet": 89,
                    },
                    {
                        "name": "Gabriel Duarte",
                        "code": "DUA",
                        "number": 55,
                        "player": 0,
                        "speed": 89,
                        "braking": 90,
                        "cornering": 88,
                        "overtake": 87,
                        "defend": 91,
                        "tire": 89,
                        "cons": 92,
                        "wet": 85,
                    },
                ],
            },
            # Tier 2: Apex Dynamics (Cyan & Slate / Player Team)
            {
                "name": "Apex Dynamics",
                "color": (0, 220, 240),
                "player": 1,
                "car": {"engine": 91.0, "aero": 92.0, "brakes": 94.0, "tire": 88.0, "fuel": 87.0, "rel": 93.0},
                "drivers": [
                    {
                        "name": "Leo Vance",
                        "code": "VAN",
                        "number": 4,
                        "player": 1,
                        "speed": 93,
                        "braking": 95,
                        "cornering": 92,
                        "overtake": 92,
                        "defend": 89,
                        "tire": 87,
                        "cons": 93,
                        "wet": 90,
                    },
                    {
                        "name": "Marcus Rossi",
                        "code": "ROS",
                        "number": 23,
                        "player": 1,
                        "speed": 86,
                        "braking": 87,
                        "cornering": 85,
                        "overtake": 84,
                        "defend": 83,
                        "tire": 83,
                        "cons": 86,
                        "wet": 81,
                    },
                ],
            },
            # Tier 2: Solaris Grand Prix (Solar Papaya & Carbon)
            {
                "name": "Solaris Grand Prix",
                "color": (255, 135, 0),
                "player": 0,
                "car": {"engine": 93.0, "aero": 94.0, "brakes": 92.0, "tire": 89.0, "fuel": 88.0, "rel": 94.0},
                "drivers": [
                    {
                        "name": "Liam Gallagher",
                        "code": "GAL",
                        "number": 27,
                        "player": 0,
                        "speed": 95,
                        "braking": 94,
                        "cornering": 95,
                        "overtake": 92,
                        "defend": 89,
                        "tire": 89,
                        "cons": 94,
                        "wet": 92,
                    },
                    {
                        "name": "Flynn MacIntyre",
                        "code": "MAC",
                        "number": 81,
                        "player": 0,
                        "speed": 89,
                        "braking": 89,
                        "cornering": 89,
                        "overtake": 88,
                        "defend": 86,
                        "tire": 84,
                        "cons": 89,
                        "wet": 85,
                    },
                ],
            },
            # Tier 2: AeroStar Motorsport (Silver & Electric Teal)
            {
                "name": "AeroStar Motorsport",
                "color": (0, 165, 155),
                "player": 0,
                "car": {"engine": 92.0, "aero": 91.0, "brakes": 93.0, "tire": 96.0, "fuel": 92.0, "rel": 95.0},
                "drivers": [
                    {
                        "name": "Julian Drake",
                        "code": "DRA",
                        "number": 44,
                        "player": 0,
                        "speed": 94,
                        "braking": 96,
                        "cornering": 93,
                        "overtake": 95,
                        "defend": 94,
                        "tire": 97,
                        "cons": 96,
                        "wet": 98,
                    },
                    {
                        "name": "Tyler Bennett",
                        "code": "BEN",
                        "number": 63,
                        "player": 0,
                        "speed": 90,
                        "braking": 91,
                        "cornering": 89,
                        "overtake": 88,
                        "defend": 87,
                        "tire": 86,
                        "cons": 88,
                        "wet": 88,
                    },
                ],
            },
            # Tier 3: Vanguard Racing (British Racing Green & Lime)
            {
                "name": "Vanguard Racing",
                "color": (0, 110, 60),
                "player": 0,
                "car": {"engine": 86.0, "aero": 87.0, "brakes": 91.0, "tire": 93.0, "fuel": 89.0, "rel": 91.0},
                "drivers": [
                    {
                        "name": "Roberto Vega",
                        "code": "VEG",
                        "number": 14,
                        "player": 0,
                        "speed": 94,
                        "braking": 97,
                        "cornering": 93,
                        "overtake": 97,
                        "defend": 98,
                        "tire": 97,
                        "cons": 95,
                        "wet": 95,
                    },
                    {
                        "name": "Colin Crawford",
                        "code": "CRA",
                        "number": 18,
                        "player": 0,
                        "speed": 79,
                        "braking": 78,
                        "cornering": 77,
                        "overtake": 78,
                        "defend": 76,
                        "tire": 79,
                        "cons": 76,
                        "wet": 86,
                    },
                ],
            },
            # Tier 3: Titan Grand Prix (Deep Royal Blue & White)
            {
                "name": "Titan Grand Prix",
                "color": (30, 90, 200),
                "player": 0,
                "car": {"engine": 90.0, "aero": 81.0, "brakes": 84.0, "tire": 85.0, "fuel": 83.0, "rel": 89.0},
                "drivers": [
                    {
                        "name": "Alexander Cross",
                        "code": "CRO",
                        "number": 5,
                        "player": 0,
                        "speed": 89,
                        "braking": 90,
                        "cornering": 87,
                        "overtake": 88,
                        "defend": 90,
                        "tire": 90,
                        "cons": 91,
                        "wet": 87,
                    },
                    {
                        "name": "Lucas Ferreira",
                        "code": "FER",
                        "number": 43,
                        "player": 0,
                        "speed": 82,
                        "braking": 83,
                        "cornering": 81,
                        "overtake": 83,
                        "defend": 80,
                        "tire": 81,
                        "cons": 83,
                        "wet": 82,
                    },
                ],
            },
            # Tier 3: Nexus Performance (Cobalt Blue & Pink)
            {
                "name": "Nexus Performance",
                "color": (0, 140, 230),
                "player": 0,
                "car": {"engine": 85.0, "aero": 84.0, "brakes": 85.0, "tire": 83.0, "fuel": 83.0, "rel": 87.0},
                "drivers": [
                    {
                        "name": "Antoine Laurent",
                        "code": "LAU",
                        "number": 10,
                        "player": 0,
                        "speed": 86,
                        "braking": 87,
                        "cornering": 85,
                        "overtake": 85,
                        "defend": 84,
                        "tire": 84,
                        "cons": 86,
                        "wet": 85,
                    },
                    {
                        "name": "Hugo Vasseur",
                        "code": "VAS",
                        "number": 31,
                        "player": 0,
                        "speed": 83,
                        "braking": 84,
                        "cornering": 82,
                        "overtake": 85,
                        "defend": 89,
                        "tire": 82,
                        "cons": 83,
                        "wet": 83,
                    },
                ],
            },
            # Tier 4: Kestrel Tech (Gunmetal Grey & Scarlet)
            {
                "name": "Kestrel Tech",
                "color": (180, 40, 40),
                "player": 0,
                "car": {"engine": 87.0, "aero": 78.0, "brakes": 82.0, "tire": 76.0, "fuel": 80.0, "rel": 85.0},
                "drivers": [
                    {
                        "name": "Henrik Weber",
                        "code": "WEB",
                        "number": 8,
                        "player": 0,
                        "speed": 87,
                        "braking": 88,
                        "cornering": 84,
                        "overtake": 84,
                        "defend": 82,
                        "tire": 80,
                        "cons": 89,
                        "wet": 85,
                    },
                    {
                        "name": "Viktor Lund",
                        "code": "LUN",
                        "number": 20,
                        "player": 0,
                        "speed": 81,
                        "braking": 83,
                        "cornering": 80,
                        "overtake": 88,
                        "defend": 92,
                        "tire": 77,
                        "cons": 78,
                        "wet": 81,
                    },
                ],
            },
            # Tier 4: Neon Velocity (High-Vis Green & Black)
            {
                "name": "Neon Velocity",
                "color": (40, 210, 50),
                "player": 0,
                "car": {"engine": 81.0, "aero": 79.0, "brakes": 80.0, "tire": 84.0, "fuel": 84.0, "rel": 88.0},
                "drivers": [
                    {
                        "name": "Jarno Koskinen",
                        "code": "KOS",
                        "number": 77,
                        "player": 0,
                        "speed": 85,
                        "braking": 86,
                        "cornering": 84,
                        "overtake": 81,
                        "defend": 80,
                        "tire": 88,
                        "cons": 89,
                        "wet": 82,
                    },
                    {
                        "name": "Jin Tanaka",
                        "code": "TAN",
                        "number": 24,
                        "player": 0,
                        "speed": 79,
                        "braking": 80,
                        "cornering": 78,
                        "overtake": 77,
                        "defend": 78,
                        "tire": 80,
                        "cons": 81,
                        "wet": 79,
                    },
                ],
            },
        ]

        for t in teams_data:
            c_r, c_g, c_b = t["color"]
            cursor.execute(
                "INSERT INTO teams (name, color_r, color_g, color_b, is_player) VALUES (?, ?, ?, ?, ?)",
                (t["name"], c_r, c_g, c_b, t["player"]),
            )
            team_id = cursor.lastrowid

            car = t["car"]
            cursor.execute(
                """INSERT INTO car_attributes (team_id, engine_power, aero_downforce, braking_efficiency, tire_preservation, fuel_efficiency, reliability)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (team_id, car["engine"], car["aero"], car["brakes"], car["tire"], car["fuel"], car["rel"]),
            )

            for d in t["drivers"]:
                cursor.execute(
                    """INSERT INTO drivers (team_id, name, code, number, is_player, speed, braking, cornering, overtaking, defending, tire_management, consistency, wet_skill)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        team_id,
                        d["name"],
                        d["code"],
                        d["number"],
                        d["player"],
                        d["speed"],
                        d["braking"],
                        d["cornering"],
                        d["overtake"],
                        d["defend"],
                        d["tire"],
                        d["cons"],
                        d["wet"],
                    ),
                )
        conn.commit()

    def get_all_drivers_and_cars(self) -> List[Dict]:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT 
                d.id as driver_id, d.name, d.code, d.number, d.is_player,
                d.speed, d.braking, d.cornering, d.overtaking, d.defending, d.tire_management, d.consistency, d.wet_skill,
                t.id as team_id, t.name as team_name, t.color_r, t.color_g, t.color_b,
                c.engine_power, c.aero_downforce, c.braking_efficiency, c.tire_preservation, c.fuel_efficiency, c.reliability
            FROM drivers d
            JOIN teams t ON d.team_id = t.id
            JOIN car_attributes c ON t.id = c.team_id
            ORDER BY t.id, d.id
            """)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_teams(self) -> List[Dict]:
        """Returns all teams in race_game.db."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM teams ORDER BY id ASC")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_car_attributes(self, team_id: int) -> Optional[Dict]:
        """Returns car attributes for a given team_id."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM car_attributes WHERE team_id = ?", (team_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_drivers(self, team_id: Optional[int] = None) -> List[Dict]:
        """Returns drivers, optionally filtered by team_id."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            if team_id is not None:
                cursor.execute("SELECT * FROM drivers WHERE team_id = ? ORDER BY id ASC", (team_id,))
            else:
                cursor.execute("SELECT * FROM drivers ORDER BY team_id ASC, id ASC")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def update_team(self, team_id: int, name: str, color_r: int, color_g: int, color_b: int) -> bool:
        """Updates team name and livery colors."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE teams SET name = ?, color_r = ?, color_g = ?, color_b = ? WHERE id = ?",
                (name, color_r, color_g, color_b, team_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def update_car_attributes(self, team_id: int, attrs: Dict[str, float]) -> bool:
        """Updates performance attributes for a team's car."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
            UPDATE car_attributes
            SET engine_power = ?, aero_downforce = ?, braking_efficiency = ?,
                tire_preservation = ?, fuel_efficiency = ?, reliability = ?
            WHERE team_id = ?
            """,
                (
                    attrs.get("engine_power", 85.0),
                    attrs.get("aero_downforce", 85.0),
                    attrs.get("braking_efficiency", 85.0),
                    attrs.get("tire_preservation", 85.0),
                    attrs.get("fuel_efficiency", 85.0),
                    attrs.get("reliability", 90.0),
                    team_id,
                ),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def update_driver_attributes(
        self, driver_id: int, name: str, code: str, number: int, stats: Dict[str, float]
    ) -> bool:
        """Updates driver bio and attributes."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
            UPDATE drivers
            SET name = ?, code = ?, number = ?,
                speed = ?, braking = ?, cornering = ?, overtaking = ?,
                defending = ?, tire_management = ?, consistency = ?, wet_skill = ?
            WHERE id = ?
            """,
                (
                    name,
                    code,
                    number,
                    stats.get("speed", 85.0),
                    stats.get("braking", 85.0),
                    stats.get("cornering", 85.0),
                    stats.get("overtaking", 80.0),
                    stats.get("defending", 80.0),
                    stats.get("tire_management", 80.0),
                    stats.get("consistency", 85.0),
                    stats.get("wet_skill", 80.0),
                    driver_id,
                ),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
