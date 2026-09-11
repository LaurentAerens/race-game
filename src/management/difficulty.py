from typing import Dict, Any, List

DIFFICULTY_LEVELS = ["VERY_EASY", "EASY", "NORMAL", "HARD", "VERY_HARD"]

DIFFICULTY_CONFIG: Dict[str, Dict[str, Any]] = {
    "VERY_EASY": {
        "name": "Very Easy",
        "description": "Generous sponsor budgets, -30% facility upkeep, rapid breakthroughs, and forgiving AI rivals.",
        "dev_gain_mult": 1.40,
        "driver_growth_mult": 1.50,
        "sponsor_cash_mult": 1.50,
        "upkeep_mult": 0.70,
        "factory_cost_mult": 1.00,
        "parts_cost_mult": 1.00,
        "rnd_cost_mult": 1.00,
        "ai_pace_mult": 0.93,
        "innovation_rate_mult": 1.50,
        "innovation_success_mult": 1.30,
        "innovation_gain_mult": 1.30,
        "negative_penalty_mult": 0.60,
        "starting_cash_bonus": 5000000.0
    },
    "EASY": {
        "name": "Easy",
        "description": "-15% facility upkeep, boosted research efficiency, faster driver growth, and strong sponsor funding.",
        "dev_gain_mult": 1.20,
        "driver_growth_mult": 1.25,
        "sponsor_cash_mult": 1.25,
        "upkeep_mult": 0.85,
        "factory_cost_mult": 1.00,
        "parts_cost_mult": 1.00,
        "rnd_cost_mult": 1.00,
        "ai_pace_mult": 0.97,
        "innovation_rate_mult": 1.25,
        "innovation_success_mult": 1.15,
        "innovation_gain_mult": 1.15,
        "negative_penalty_mult": 0.80,
        "starting_cash_bonus": 2500000.0
    },
    "NORMAL": {
        "name": "Normal",
        "description": "Balanced and authentic motorsport management tycoon experience.",
        "dev_gain_mult": 1.00,
        "driver_growth_mult": 1.00,
        "sponsor_cash_mult": 1.00,
        "upkeep_mult": 1.00,
        "factory_cost_mult": 1.00,
        "parts_cost_mult": 1.00,
        "rnd_cost_mult": 1.00,
        "ai_pace_mult": 1.00,
        "innovation_rate_mult": 1.00,
        "innovation_success_mult": 1.00,
        "innovation_gain_mult": 1.00,
        "negative_penalty_mult": 1.00,
        "starting_cash_bonus": 0.0
    },
    "HARD": {
        "name": "Hard",
        "description": "+25% facility upkeep, tighter financial margins, aggressive AI competition, and demanding development.",
        "dev_gain_mult": 0.85,
        "driver_growth_mult": 0.80,
        "sponsor_cash_mult": 0.80,
        "upkeep_mult": 1.25,
        "factory_cost_mult": 1.00,
        "parts_cost_mult": 1.00,
        "rnd_cost_mult": 1.00,
        "ai_pace_mult": 1.03,
        "innovation_rate_mult": 0.75,
        "innovation_success_mult": 0.85,
        "innovation_gain_mult": 0.85,
        "negative_penalty_mult": 1.30,
        "starting_cash_bonus": -2000000.0
    },
    "VERY_HARD": {
        "name": "Very Hard",
        "description": "Punishing hardcore mode: +50% upkeep, ruthless AI, minimal prize margins, and tough driver progression.",
        "dev_gain_mult": 0.70,
        "driver_growth_mult": 0.65,
        "sponsor_cash_mult": 0.65,
        "upkeep_mult": 1.50,
        "factory_cost_mult": 1.00,
        "parts_cost_mult": 1.00,
        "rnd_cost_mult": 1.00,
        "ai_pace_mult": 1.06,
        "innovation_rate_mult": 0.50,
        "innovation_success_mult": 0.70,
        "innovation_gain_mult": 0.70,
        "negative_penalty_mult": 1.60,
        "starting_cash_bonus": -4000000.0
    }
}



class DifficultyManager:
    """Manages career difficulty level and applies dynamic modifiers across all game systems."""
    def __init__(self, current_difficulty: str = "NORMAL"):
        if current_difficulty not in DIFFICULTY_CONFIG:
            current_difficulty = "NORMAL"
        self.current_difficulty = current_difficulty

    def set_difficulty(self, difficulty: str):
        if difficulty in DIFFICULTY_CONFIG:
            self.current_difficulty = difficulty

    def cycle_difficulty(self) -> str:
        idx = DIFFICULTY_LEVELS.index(self.current_difficulty)
        next_idx = (idx + 1) % len(DIFFICULTY_LEVELS)
        self.current_difficulty = DIFFICULTY_LEVELS[next_idx]
        return self.current_difficulty

    def get_config(self) -> Dict[str, Any]:
        return DIFFICULTY_CONFIG[self.current_difficulty]

    def get_modifier(self, key: str, default: float = 1.0) -> float:
        return self.get_config().get(key, default)

    def scale_gain_or_penalty(self, value: float) -> float:
        """
        Scales a performance or reliability change based on difficulty:
        - Positive (> 0): scaled by dev_gain_mult (Easy = larger gain, Hard = smaller gain).
        - Negative (< 0): scaled by negative_penalty_mult (Easy = milder penalty, Hard = harsher penalty).
        """
        if value > 0:
            return value * self.get_modifier("dev_gain_mult", 1.0)
        elif value < 0:
            return value * self.get_modifier("negative_penalty_mult", 1.0)
        return 0.0

