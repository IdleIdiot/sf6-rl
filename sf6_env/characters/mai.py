from __future__ import annotations
from sf6_env.characters.base import CharacterData

WALK_SPEED_FORWARD = 5.0
WALK_SPEED_BACK = 3.5
JUMP_FORWARD_VEL = 4.0
JUMP_BACK_VEL = -3.5
DASH_FORWARD_VEL = 12.0
DASH_BACK_VEL = -10.0

# Maps action enum index to move name in frame data
ACTION_MOVE_MAP = {
    0:  "idle",
    1:  "walk_forward",
    2:  "walk_back",
    3:  "crouch",
    4:  "jump",
    5:  "5LP",
    6:  "5MP",
    7:  "5HP",
    8:  "5LK",
    9:  "5MK",
    10: "5HK",
    11: "2LP",
    12: "2MP",
    13: "2HP",
    14: "2LK",
    15: "2MK",
    16: "2HK",
    17: "jLP",
    18: "jMP",
    19: "jHP",
    20: "jLK",
    21: "jMK",
    22: "jHK",
    23: "kachousen_L",
    24: "kachousen_M",
    25: "kachousen_H",
    26: "idle",  # unused (midare_kachousen removed - not in SF6 Mai)
    27: "idle",  # unused
    28: "idle",  # unused
    29: "ryuuenbu_L",
    30: "ryuuenbu_M",
    31: "ryuuenbu_H",
    32: "shinobibachi_L",
    33: "shinobibachi_M",
    34: "shinobibachi_H",
    35: "hishou_ryuuenjin_L",
    36: "hishou_ryuuenjin_M",
    37: "hishou_ryuuenjin_H",
    38: "musasabi_L",
    39: "musasabi_M",
    40: "musasabi_H",
    41: "kachousen_OD",
    42: "ryuuenbu_OD",
    43: "hishou_ryuuenjin_OD",
    44: "SA1",
    45: "SA2",
    46: "SA3",
    47: "drive_impact",
    48: "drive_reversal",
    49: "forward_throw",
    50: "back_throw",
    51: "dash_forward",
    52: "dash_back",
    53: "jump_forward",
    54: "jump_back",
    55: "shinobibachi_OD",
    56: "hien_ren_kyaku",
    57: "hoshi_kujaku",
    58: "senkotsu_uchi",
}

NUM_ACTIONS = len(ACTION_MOVE_MAP)

# Actions only valid while airborne
AIRBORNE_ONLY = {17, 18, 19, 20, 21, 22, 38, 39, 40}
# Actions only valid while grounded
GROUND_ONLY = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
               23, 24, 25, 29, 30, 31, 32, 33, 34, 35, 36, 37,
               41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58}
# Actions that cost super meter
SUPER_COSTS = {44: 1, 45: 2, 46: 3}


class MaiData(CharacterData):
    def __init__(self):
        super().__init__("mai_frames.json")
        self.walk_speed_forward = WALK_SPEED_FORWARD
        self.walk_speed_back = WALK_SPEED_BACK
        self.jump_forward_vel = JUMP_FORWARD_VEL
        self.jump_back_vel = JUMP_BACK_VEL
        self.dash_forward_vel = DASH_FORWARD_VEL
        self.dash_back_vel = DASH_BACK_VEL
        self.action_map = ACTION_MOVE_MAP
        self.num_actions = NUM_ACTIONS
        self.airborne_only = AIRBORNE_ONLY
        self.ground_only = GROUND_ONLY
        self.super_costs = SUPER_COSTS
        self.max_health = 10000
        self.name = "Mai Shiranui"

    def action_to_move(self, action_id: int) -> str:
        return self.action_map.get(action_id, "idle")
