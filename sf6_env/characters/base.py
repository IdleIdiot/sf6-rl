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

    def get_move(self, move_name: str) -> Dict[str, Any]:
        return self.moves.get(move_name, {})

    def get_hurtboxes(self, action: str) -> List[Dict[str, float]]:
        move = self.get_move(action)
        return move.get("hurtboxes", [{"x_offset": 0, "y_offset": 60, "w": 40, "h": 120}])

    def get_total_frames(self, move_name: str) -> int:
        move = self.get_move(move_name)
        return move.get("startup", 1) + move.get("active", 1) + move.get("recovery", 1)

    def action_to_move(self, action_id: int) -> str:
        return self.action_map.get(action_id, "idle")
