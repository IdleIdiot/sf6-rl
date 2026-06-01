from __future__ import annotations
from sf6_env.characters.base import CharacterData

WALK_SPEED_FORWARD = 5.0
WALK_SPEED_BACK = 3.5
JUMP_FORWARD_VEL = 4.0
JUMP_BACK_VEL = -3.5
DASH_FORWARD_VEL = 12.0
DASH_BACK_VEL = -10.0

# Move slugs match keys in mai_frames.json (from 4rays/sf6-move-data)
# Normals
_LP  = "mai-stand-light-punch"
_MP  = "mai-stand-medium-punch"
_HP  = "mai-stand-heavy-punch"
_LK  = "mai-stand-light-kick"
_MK  = "mai-stand-medium-kick"
_HK  = "mai-stand-heavy-kick"
_2LP = "mai-crouch-light-punch"
_2MP = "mai-crouch-medium-punch"
_2HP = "mai-crouch-heavy-punch"
_2LK = "mai-crouch-light-kick"
_2MK = "mai-crouch-medium-kick"
_2HK = "mai-crouch-heavy-kick"
_jLP = "mai-jump-light-punch"
_jMP = "mai-jump-medium-punch"
_jHP = "mai-jump-heavy-punch"
_jLK = "mai-jump-light-kick"
_jMK = "mai-jump-medium-kick"
_jHK = "mai-jump-heavy-kick"

# Unique normals
_SENKOTSU   = "mai-senkotsu-uchi"       # 6HP
_HIEN2      = "mai-hien-ren-kyaku-2"    # 2nd hit of Hien Ren Kyaku (6MK)
_HIEN3      = "mai-hien-ren-kyaku-3"    # 3rd hit
_HOSHI1     = "mai-hoshi-kujaku-1"      # 6HK 1st hit
_HOSHI2     = "mai-hoshi-kujaku-2"      # 6HK 2nd hit

# Throws
_FWD_THROW  = "mai-forward-throw"
_BACK_THROW = "mai-back-throw"
_AIR_THROW  = "mai-air-throw"

# Specials — Kachousen (projectile)
_KAC_L  = "mai-l-kachousen"
_KAC_M  = "mai-m-kachousen"
_KAC_H  = "mai-h-kachousen"
_KAC_OD = "mai-od-kachousen"
_MIDARE = "mai-midare-kachousen"        # 236PP follow-up

# Specials — Ryuuenbu (spin)
_RYU_L  = "mai-l-ryuuenbu"
_RYU_M  = "mai-m-ryuuenbu"
_RYU_H  = "mai-h-ryuuenbu"
_RYU_OD = "mai-od-ryuuenbu"

# Specials — Hissatsu Shinobi Bachi (DP)
_DP_L   = "mai-l-hissatsu-shinobi-bachi"
_DP_M   = "mai-m-hissatsu-shinobi-bachi"
_DP_H   = "mai-h-hissatsu-shinobi-bachi"
_DP_OD  = "mai-od-hissatsu-shinobi-bachi"

# Specials — Hishou Ryuuenjin (air dive)
_DIVE_L  = "mai-l-hishou-ryuuenjin"
_DIVE_M  = "mai-m-hishou-ryuuenjin"
_DIVE_H  = "mai-h-hishou-ryuuenjin"
_DIVE_OD = "mai-od-hishou-ryuuenjin"

# Specials — Musasabi no Mai (wall jump)
_MUSA_L  = "mai-l-musasabi-no-mai"
_MUSA_M  = "mai-m-musasabi-no-mai"
_MUSA_H  = "mai-h-musasabi-no-mai"
_MUSA_OD = "mai-od-musasabi-no-mai"

# Super Arts
_SA1 = "mai-kagerou-no-mai"
_SA2 = "mai-chou-hissatsu-shinobi-bachi"
_SA3 = "mai-shiranui-ryuu-enbu-ada-zakura"

# System moves (hardcoded, not in frame data file)
_DI  = "drive_impact"
_DR  = "drive_reversal"

# Maps action enum index → move slug
ACTION_MOVE_MAP = {
    # Movement
    0:  "idle",
    1:  "walk_forward",
    2:  "walk_back",
    3:  "crouch",
    4:  "jump",
    51: "dash_forward",
    52: "dash_back",
    53: "jump_forward",
    54: "jump_back",
    # Standing normals
    5:  _LP,
    6:  _MP,
    7:  _HP,
    8:  _LK,
    9:  _MK,
    10: _HK,
    # Crouching normals
    11: _2LP,
    12: _2MP,
    13: _2HP,
    14: _2LK,
    15: _2MK,
    16: _2HK,
    # Jump normals
    17: _jLP,
    18: _jMP,
    19: _jHP,
    20: _jLK,
    21: _jMK,
    22: _jHK,
    # Unique normals
    56: _SENKOTSU,
    57: _HIEN2,
    58: _HOSHI1,
    # Throws
    49: _FWD_THROW,
    50: _BACK_THROW,
    # Kachousen
    23: _KAC_L,
    24: _KAC_M,
    25: _KAC_H,
    41: _KAC_OD,
    26: _MIDARE,
    # Ryuuenbu
    29: _RYU_L,
    30: _RYU_M,
    31: _RYU_H,
    42: _RYU_OD,
    # Hissatsu Shinobi Bachi (DP)
    32: _DP_L,
    33: _DP_M,
    34: _DP_H,
    55: _DP_OD,
    # Hishou Ryuuenjin (air dive — airborne only)
    35: _DIVE_L,
    36: _DIVE_M,
    37: _DIVE_H,
    43: _DIVE_OD,
    # Musasabi no Mai (wall jump — airborne only)
    38: _MUSA_L,
    39: _MUSA_M,
    40: _MUSA_H,
    # Super Arts
    44: _SA1,
    45: _SA2,
    46: _SA3,
    # System
    47: _DI,
    48: _DR,
}

NUM_ACTIONS = len(ACTION_MOVE_MAP)

# Actions only valid while airborne
AIRBORNE_ONLY = {17, 18, 19, 20, 21, 22, 35, 36, 37, 38, 39, 40, 43}
# Actions only valid while grounded
GROUND_ONLY = {
    1, 2, 3, 4,
    5, 6, 7, 8, 9, 10,
    11, 12, 13, 14, 15, 16,
    23, 24, 25, 26, 29, 30, 31, 32, 33, 34,
    41, 42, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58,
}

# Super Arts cost (in super gauge bars)
SUPER_COSTS = {44: 1, 45: 2, 46: 3}

# Drive costs for OD specials (1 bar = 1.0)
DRIVE_COSTS = {
    41: 1.0,  # OD Kachousen
    42: 1.0,  # OD Ryuuenbu
    43: 1.0,  # OD Hishou Ryuuenjin
    55: 1.0,  # OD Hissatsu Shinobi Bachi
    47: 1.0,  # Drive Impact
    48: 1.0,  # Drive Reversal
}

# cancel_into rules: which move categories each normal can cancel into
# "specials" = special moves, "super" = SA, "normals" = target combo normals
CANCEL_RULES = {
    _LP:  ["specials", "super"],
    _MP:  ["specials", "super"],
    _HP:  ["specials", "super"],
    _LK:  ["specials", "super"],
    _MK:  ["specials", "super"],
    _HK:  ["specials", "super"],
    _2LP: ["specials", "super"],
    _2MP: ["specials", "super"],
    _2HP: ["specials", "super"],
    _2LK: ["specials", "super"],
    _2MK: ["specials", "super"],
    _2HK: ["specials", "super"],
    _SENKOTSU: ["specials", "super"],
    _HOSHI1:   ["specials", "super"],
    # Specials can cancel into super
    _KAC_L:  ["super"], _KAC_M:  ["super"], _KAC_H:  ["super"], _KAC_OD: ["super"],
    _RYU_L:  ["super"], _RYU_M:  ["super"], _RYU_H:  ["super"], _RYU_OD: ["super"],
    _DP_L:   ["super"], _DP_M:   ["super"], _DP_H:   ["super"], _DP_OD:  ["super"],
}


class MaiData(CharacterData):
    def __init__(self):
        super().__init__("characters/mai_frames.json")
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
        self.drive_costs = DRIVE_COSTS
        self.cancel_rules = CANCEL_RULES
        self.max_health = 10000
        self.name = "Mai Shiranui"
        # Inject cancel_into and drive_cost into move data after loading
        self._patch_moves()

    def _patch_moves(self) -> None:
        """Inject cancel_into lists and drive_cost into loaded move data."""
        for move_name, cancel_list in CANCEL_RULES.items():
            if move_name in self.moves:
                self.moves[move_name]["cancel_into"] = cancel_list

        for action_id, cost in DRIVE_COSTS.items():
            move_name = ACTION_MOVE_MAP.get(action_id)
            if move_name and move_name in self.moves:
                self.moves[move_name]["drive_cost"] = cost

        # Inject super_cost into SA move data
        for action_id, cost in SUPER_COSTS.items():
            move_name = ACTION_MOVE_MAP.get(action_id)
            if move_name and move_name in self.moves:
                self.moves[move_name]["super_cost"] = cost

        # Mark throws
        for slug in (_FWD_THROW, _BACK_THROW, _AIR_THROW):
            if slug in self.moves:
                props = self.moves[slug].get("properties", [])
                if "throw" not in props:
                    self.moves[slug]["properties"] = props + ["throw"]

        # Mark projectile moves
        for slug in (_KAC_L, _KAC_M, _KAC_H, _KAC_OD, _MIDARE):
            if slug in self.moves:
                props = self.moves[slug].get("properties", [])
                if "projectile" not in props:
                    self.moves[slug]["properties"] = props + ["projectile"]

        # Inject hitboxes (frame data source doesn't include actual hitbox coords)
        self._inject_hitboxes()

    def _inject_hitboxes(self) -> None:
        """
        Inject approximate hitboxes for all moves.
        Frame data from 4rays/sf6-move-data doesn't include hitbox coordinates,
        so we use reasonable defaults based on move type.
        """
        # Standing normals: mid-height, forward reach
        for slug, (x, y, w, h) in [
            (_LP,  (50, 80, 70, 40)),
            (_MP,  (60, 90, 80, 50)),
            (_HP,  (70, 85, 90, 55)),
            (_LK,  (55, 50, 70, 40)),
            (_MK,  (65, 60, 80, 45)),
            (_HK,  (75, 55, 100, 50)),
        ]:
            if slug in self.moves and not self.moves[slug].get("hitboxes"):
                self.moves[slug]["hitboxes"] = [{"x_offset": x, "y_offset": y, "w": w, "h": h}]

        # Crouching normals: low height, shorter reach
        for slug, (x, y, w, h) in [
            (_2LP, (45, 30, 65, 35)),
            (_2MP, (55, 40, 75, 40)),
            (_2HP, (60, 35, 85, 45)),
            (_2LK, (50, 15, 70, 30)),
            (_2MK, (65, 20, 85, 35)),
            (_2HK, (70, 15, 100, 30)),
        ]:
            if slug in self.moves and not self.moves[slug].get("hitboxes"):
                self.moves[slug]["hitboxes"] = [{"x_offset": x, "y_offset": y, "w": w, "h": h}]

        # Jump normals: air height, diagonal reach
        for slug, (x, y, w, h) in [
            (_jLP, (40, 60, 60, 35)),
            (_jMP, (50, 55, 75, 45)),
            (_jHP, (55, 50, 85, 55)),
            (_jLK, (45, 40, 65, 40)),
            (_jMK, (55, 35, 80, 50)),
            (_jHK, (60, 30, 95, 60)),
        ]:
            if slug in self.moves and not self.moves[slug].get("hitboxes"):
                self.moves[slug]["hitboxes"] = [{"x_offset": x, "y_offset": y, "w": w, "h": h}]

        # Unique normals
        for slug, (x, y, w, h) in [
            (_SENKOTSU, (60, 70, 80, 60)),
            (_HOSHI1,   (55, 65, 75, 55)),
            (_HOSHI2,   (55, 65, 75, 55)),
            (_HIEN2,    (50, 55, 70, 45)),
            (_HIEN3,    (50, 55, 70, 45)),
        ]:
            if slug in self.moves and not self.moves[slug].get("hitboxes"):
                self.moves[slug]["hitboxes"] = [{"x_offset": x, "y_offset": y, "w": w, "h": h}]

        # Throws: close range, grab box
        for slug in (_FWD_THROW, _BACK_THROW, _AIR_THROW):
            if slug in self.moves and not self.moves[slug].get("hitboxes"):
                self.moves[slug]["hitboxes"] = [{"x_offset": 40, "y_offset": 60, "w": 60, "h": 80}]

        # Specials — Ryuuenbu (spin): wide vertical hitbox
        for slug, (x, y, w, h) in [
            (_RYU_L,  (30, 60, 80, 100)),
            (_RYU_M,  (30, 60, 80, 100)),
            (_RYU_H,  (30, 60, 80, 100)),
            (_RYU_OD, (30, 60, 90, 110)),
        ]:
            if slug in self.moves and not self.moves[slug].get("hitboxes"):
                self.moves[slug]["hitboxes"] = [{"x_offset": x, "y_offset": y, "w": w, "h": h}]

        # Specials — Hissatsu Shinobi Bachi (DP): tall vertical hitbox
        for slug, (x, y, w, h) in [
            (_DP_L,  (60, 50, 80, 60)),
            (_DP_M,  (60, 50, 80, 60)),
            (_DP_H,  (60, 50, 80, 60)),
            (_DP_OD, (60, 50, 90, 70)),
        ]:
            if slug in self.moves and not self.moves[slug].get("hitboxes"):
                self.moves[slug]["hitboxes"] = [{"x_offset": x, "y_offset": y, "w": w, "h": h}]

        # Specials — Hishou Ryuuenjin (air dive): tall descending hitbox
        for slug, (x, y, w, h) in [
            (_DIVE_L,  (20, 40, 60, 130)),
            (_DIVE_M,  (20, 40, 60, 130)),
            (_DIVE_H,  (20, 40, 60, 130)),
            (_DIVE_OD, (20, 40, 70, 140)),
        ]:
            if slug in self.moves and not self.moves[slug].get("hitboxes"):
                self.moves[slug]["hitboxes"] = [{"x_offset": x, "y_offset": y, "w": w, "h": h}]

        # Specials — Musasabi no Mai (wall jump): diagonal hitbox
        for slug in (_MUSA_L, _MUSA_M, _MUSA_H, _MUSA_OD):
            if slug in self.moves and not self.moves[slug].get("hitboxes"):
                self.moves[slug]["hitboxes"] = [{"x_offset": 50, "y_offset": 50, "w": 70, "h": 60}]

        # Super Arts: large hitboxes
        for slug, (x, y, w, h) in [
            (_SA1, (50, 50, 80, 80)),
            (_SA2, (40, 60, 100, 100)),
            (_SA3, (0, 60, 200, 120)),
        ]:
            if slug in self.moves and not self.moves[slug].get("hitboxes"):
                self.moves[slug]["hitboxes"] = [{"x_offset": x, "y_offset": y, "w": w, "h": h}]

        # Kachousen (projectile) doesn't need hitbox — spawns projectile entity

    def action_to_move(self, action_id: int) -> str:
        return self.action_map.get(action_id, "idle")
