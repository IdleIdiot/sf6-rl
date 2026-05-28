from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from sf6_env.engine.character import Character

THROW_RANGE = 80.0

# Hit type constants
HIT_NORMAL = 0
HIT_COUNTER = 1    # hit during attacker startup frames
HIT_PUNISH = 2     # hit during attacker recovery frames


@dataclass
class Box:
    x_offset: float
    y_offset: float
    w: float
    h: float

    def to_world(self, char_x: float, char_y: float, facing: int) -> Tuple[float, float, float, float]:
        ox = self.x_offset * facing
        wx = char_x + ox - self.w / 2
        wy = char_y + self.y_offset
        return wx, wy, wx + self.w, wy + self.h


def boxes_overlap(a: Tuple[float, float, float, float],
                  b: Tuple[float, float, float, float]) -> bool:
    al, ab, ar, at = a
    bl, bb, br, bt = b
    return ar > bl and al < br and at > bb and ab < bt


@dataclass
class HitEvent:
    attacker_id: int
    defender_id: int
    damage: int
    chip_damage: int
    on_hit_adv: int
    on_block_adv: int
    drive_gain_hit: float
    drive_gain_block: float
    properties: List[str]
    move_name: str
    hit_type: int = HIT_NORMAL
    attacker_drive_rush: bool = False


def _get_hit_type(defender: "Character") -> int:
    """Determine hit type based on defender's current state."""
    move = defender.current_move_data
    if move is None:
        return HIT_NORMAL
    frame = defender.action_frame
    startup = move.get("startup", 1)
    active = move.get("active", 1)
    total = startup + active + move.get("recovery", 1)
    # Punish Counter: hit during recovery
    if frame >= startup + active:
        return HIT_PUNISH
    # Counter Hit: hit during startup (before active frames)
    if frame < startup:
        return HIT_COUNTER
    return HIT_NORMAL


def check_hit(attacker: "Character", defender: "Character") -> Optional[HitEvent]:
    move = attacker.current_move_data
    if move is None:
        return None

    frame = attacker.action_frame
    startup = move.get("startup", 1)
    active = move.get("active", 1)

    if not (startup <= frame < startup + active):
        return None

    # multi-hit: allow up to hit_count hits per action
    max_hits = move.get("hit_count", 1)
    if attacker.hits_this_action >= max_hits:
        return None

    props = move.get("properties", [])

    if "throw" in props:
        return _check_throw(attacker, defender, move)

    hitboxes: List[Box] = [Box(**b) for b in move.get("hitboxes", [])]
    hurtboxes: List[Box] = [Box(**b) for b in defender.current_hurtboxes()]

    for hb in hitboxes:
        hw = hb.to_world(attacker.body.x, attacker.body.y, attacker.facing)
        for hurtb in hurtboxes:
            hurtw = hurtb.to_world(defender.body.x, defender.body.y, defender.facing)
            if boxes_overlap(hw, hurtw):
                hit_type = _get_hit_type(defender)
                return HitEvent(
                    attacker_id=attacker.player_id,
                    defender_id=defender.player_id,
                    damage=move.get("damage", 0),
                    chip_damage=move.get("chip_damage", 0),
                    on_hit_adv=move.get("on_hit", 0),
                    on_block_adv=move.get("on_block", 0),
                    drive_gain_hit=move.get("drive_gain_hit", 0.0),
                    drive_gain_block=move.get("drive_gain_block", 0.0),
                    properties=props,
                    move_name=attacker.current_action,
                    hit_type=hit_type,
                    attacker_drive_rush=attacker.drive_rushing,
                )
    return None


def _check_throw(attacker: "Character", defender: "Character", move: dict) -> Optional[HitEvent]:
    if defender.body.airborne:
        return None
    # 投技无法命中处于硬直/倒地状态的对手
    if defender.current_action in ("hitstun", "blockstun", "knockdown", "crumple"):
        return None
    dist = abs(attacker.body.x - defender.body.x)
    if dist > THROW_RANGE:
        return None
    direction = defender.body.x - attacker.body.x
    if direction * attacker.facing <= 0:
        return None
    props = move.get("properties", [])
    return HitEvent(
        attacker_id=attacker.player_id,
        defender_id=defender.player_id,
        damage=move.get("damage", 0),
        chip_damage=0,
        on_hit_adv=move.get("on_hit", 0),
        on_block_adv=0,
        drive_gain_hit=move.get("drive_gain_hit", 0.3),
        drive_gain_block=0.0,
        properties=props,
        move_name=attacker.current_action,
        hit_type=HIT_NORMAL,
        attacker_drive_rush=False,
    )


def check_projectile_hits(projectiles: list, defender: "Character") -> Optional[HitEvent]:
    hurtboxes: List[Box] = [Box(**b) for b in defender.current_hurtboxes()]
    for proj in projectiles:
        if proj.owner_id == defender.player_id:
            continue
        pb = (proj.x - proj.w / 2, proj.y, proj.x + proj.w / 2, proj.y + proj.h)
        for hurtb in hurtboxes:
            hurtw = hurtb.to_world(defender.body.x, defender.body.y, defender.facing)
            if boxes_overlap(pb, hurtw):
                proj.active = False
                return HitEvent(
                    attacker_id=proj.owner_id,
                    defender_id=defender.player_id,
                    damage=proj.damage,
                    chip_damage=proj.chip_damage,
                    on_hit_adv=proj.on_hit_adv,
                    on_block_adv=proj.on_block_adv,
                    drive_gain_hit=proj.drive_gain_hit,
                    drive_gain_block=proj.drive_gain_block,
                    properties=proj.properties,
                    move_name=proj.move_name,
                    hit_type=HIT_NORMAL,
                    attacker_drive_rush=False,
                )
    return None


