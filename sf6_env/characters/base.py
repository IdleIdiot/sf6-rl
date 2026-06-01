from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List


class CharacterData:
    def __init__(self, data_file: str):
        self.data_file = data_file
        self.moves: Dict[str, Any] = {}
        # Subclasses must set these
        self.name: str = "Unknown"
        self.max_health: int = 10000
        self.walk_speed_forward: float = 5.0
        self.walk_speed_back: float = 3.5
        self.action_map: Dict[int, str] = {}
        self.num_actions: int = 1
        self.airborne_only: set = set()
        self.ground_only: set = set()
        self.super_costs: Dict[int, int] = {}
        self._load_data()

    def _load_data(self) -> None:
        path = Path(__file__).parent.parent / "data" / self.data_file
        with open(path, "r", encoding="utf-8") as f:
            self.moves = json.load(f)
        # Add hardcoded system moves (not in frame data files)
        self._add_system_moves()

    def _add_system_moves(self) -> None:
        """Inject system-wide moves that are not in the per-character frame data."""
        # Drive Impact: 26f startup, 4 active, 20 recovery, armor on frames 1-25
        self.moves["drive_impact"] = {
            "name": "Drive Impact",
            "input": "HP+HK",
            "type": "normal",
            "startup": 26, "active": 4, "recovery": 20,
            "active_frames": [26, 29],
            "on_hit": 0, "on_block": -6,
            "damage": 2000, "chip_damage": 500,
            "drive_gain_hit": 0.0, "drive_gain_block": -1.0,
            "drive_cost": 1.0,
            "properties": ["armor", "knockdown"],
            "hitboxes": [{"x_offset": 40, "y_offset": 40, "w": 80, "h": 120}],
            "hurtboxes": [{"x_offset": 0, "y_offset": 60, "w": 40, "h": 120}],
            "hit_count": 1, "notes": [],
        }
        # Drive Reversal: 20f startup, fully invincible 1-20, -10 on block
        self.moves["drive_reversal"] = {
            "name": "Drive Reversal",
            "input": "6HP+HK (while blocking)",
            "type": "normal",
            "startup": 20, "active": 2, "recovery": 30,
            "active_frames": [20, 21],
            "on_hit": 0, "on_block": -10,
            "damage": 1500, "chip_damage": 0,
            "drive_gain_hit": 0.0, "drive_gain_block": 0.0,
            "drive_cost": 1.0,
            "properties": ["invincible", "knockdown"],
            "hitboxes": [{"x_offset": 40, "y_offset": 60, "w": 80, "h": 120}],
            "hurtboxes": [{"x_offset": 0, "y_offset": 60, "w": 40, "h": 120}],
            "hit_count": 1, "notes": [],
            "invuln_str": "1-20 Full",
        }
        # Dash forward/back: no hitboxes, just movement
        for slug, startup, active, recovery in [
            ("dash_forward", 3, 14, 4),
            ("dash_back",    4, 14, 6),
        ]:
            self.moves[slug] = {
                "name": slug.replace("_", " ").title(),
                "input": "",
                "type": "movement",
                "startup": startup, "active": active, "recovery": recovery,
                "active_frames": list(range(startup, startup + active)),
                "on_hit": 0, "on_block": 0,
                "damage": 0, "chip_damage": 0,
                "drive_gain_hit": 0.0, "drive_gain_block": 0.0,
                "drive_cost": 0.0,
                "properties": [],
                "hitboxes": [],
                "hurtboxes": [{"x_offset": 0, "y_offset": 60, "w": 40, "h": 120}],
                "hit_count": 1, "notes": [],
            }

    def get_move(self, move_name: str) -> Dict[str, Any]:
        return self.moves.get(move_name, {})

    # Default hurtbox written by the scraper — not posture-aware, treat as absent
    _SCRAPER_DEFAULT_HURTBOX = [{"x_offset": 0, "y_offset": 60, "w": 40, "h": 120}]

    def get_hurtboxes(self, action: str) -> List[Dict[str, float]]:
        """
        Return hurtboxes for the given action.

        Priority:
          1. Move data has explicit hurtboxes that differ from the scraper default → use them
          2. Action name implies a posture → use posture default
          3. Fallback → standing hurtbox

        Posture hurtboxes (approximate, based on SF6 conventions):
          Standing : 40×120, y_offset=0  (bottom at ground)
          Crouching: 50×80,  y_offset=0  — shorter & slightly wider
          Airborne : 40×100, y_offset=0  — slightly shorter
        """
        move = self.get_move(action)
        explicit = move.get("hurtboxes")
        if explicit and explicit != self._SCRAPER_DEFAULT_HURTBOX:
            return explicit

        # Determine posture from action name
        if ("crouch" in action or action in {"blockstun_crouch"}):
            return [{"x_offset": 0, "y_offset": 0, "w": 50, "h": 80}]
        if ("jump" in action or action.startswith("mai-j")
                or "air" in action or "musasabi" in action):
            return [{"x_offset": 0, "y_offset": 0, "w": 40, "h": 100}]
        return [{"x_offset": 0, "y_offset": 0, "w": 40, "h": 120}]

    def get_total_frames(self, move_name: str) -> int:
        move = self.get_move(move_name)
        return move.get("startup", 1) + move.get("active", 1) + move.get("recovery", 1)

    def get_cancel_into(self, move_name: str) -> List[str]:
        """Return the list of cancel categories allowed from this move."""
        # Subclasses may override via cancel_rules dict
        rules = getattr(self, "cancel_rules", {})
        if move_name in rules:
            return rules[move_name]
        # Fallback: read from move data (legacy field)
        move = self.get_move(move_name)
        return move.get("cancel_into", [])

    def action_to_move(self, action_id: int) -> str:
        return self.action_map.get(action_id, "idle")
