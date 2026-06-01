from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from sf6_env.engine.physics import PhysicsBody, GROUND_Y, LANDING_RECOVERY_FRAMES
from sf6_env.engine.drive import (DriveGauge, BURNOUT_EXTRA_BLOCKSTUN,
                                   COST_DRIVE_RUSH_DIRECT, DR_DURATION,
                                   DP_SUCCESS_ADVANTAGE)
from sf6_env.engine.collision import HIT_NORMAL, HIT_COUNTER, HIT_PUNISH, _last_active_frame

SUPER_GAUGE_MAX = 3


def _is_invincible_at_frame(move: dict, frame: int) -> bool:
    """
    Parse invuln_str from frame data and return True if the given frame
    falls within any invincibility window.

    invuln_str examples:
      "1-8 Full"
      "1-8 Strike/Throw, 9-39 Air (Upper Body)"
      "1-11 Full"
    """
    import re
    invuln_str = move.get("invuln_str", "")
    if not invuln_str:
        return False
    for segment in invuln_str.split(","):
        m = re.match(r"\s*(\d+)-(\d+)", segment.strip())
        if m:
            start, end = int(m.group(1)), int(m.group(2))
            if start <= frame <= end:
                return True
    return False


class Projectile:
    def __init__(self, owner_id, x, y, vel_x, damage=800, chip_damage=200,
                 on_hit_adv=2, on_block_adv=-2, drive_gain_hit=0.5,
                 drive_gain_block=0.25, properties=None, move_name="projectile",
                 w=60.0, h=40.0):
        self.owner_id = owner_id
        self.x = x
        self.y = y
        self.vel_x = vel_x
        self.w = w
        self.h = h
        self.damage = damage
        self.chip_damage = chip_damage
        self.on_hit_adv = on_hit_adv
        self.on_block_adv = on_block_adv
        self.drive_gain_hit = drive_gain_hit
        self.drive_gain_block = drive_gain_block
        self.properties = properties or []
        self.move_name = move_name
        self.active = True

    def tick(self):
        self.x += self.vel_x
        if self.x < -100 or self.x > 1100:
            self.active = False

class Character:
    def __init__(self, char_data, player_id: int, start_x: float):
        self.data = char_data
        self.player_id = player_id
        self.body = PhysicsBody(x=start_x)
        self.facing: int = 1 if player_id == 0 else -1
        self.health: int = char_data.max_health
        self.drive = DriveGauge()
        self.super_gauge: float = 0.0
        self.current_action: str = "idle"
        self.action_frame: int = 0
        self.stun_frames: int = 0
        self.hit_connected_this_action: bool = False
        self.hits_this_action: int = 0  # for multi-hit tracking
        self.is_blocking: bool = False
        self.crouching: bool = False
        self.projectiles: list = []
        self.invincible: bool = False  # DR startup invincibility
        self.parrying: bool = False    # Drive Parry active
        self.drive_rushing: bool = False  # Drive Rush active (forward dash)
        self.dr_frames: int = 0        # Drive Rush remaining frames
        self.di_armor_used: bool = False  # DI armor consumed (one-hit armor)
        # combo tracking
        self.combo_count: int = 0
        self.last_hit_frame: int = 0
        # punish window: frames remaining where opponent is punishable
        self.punish_window: int = 0

    @property
    def alive(self) -> bool:
        return self.health > 0

    @property
    def in_stun(self) -> bool:
        return self.stun_frames > 0

    @property
    def current_move_data(self):
        return self.data.get_move(self.current_action) or None

    def current_hurtboxes(self):
        return self.data.get_hurtboxes(self.current_action)

    def update_facing(self, opponent_x: float) -> None:
        neutral = ("idle", "walk_forward", "walk_back", "crouch")
        if not self.in_stun and self.current_action in neutral:
            self.facing = 1 if opponent_x > self.body.x else -1

    def tick(self, action_id: int, opponent) -> None:
        self.update_facing(opponent.body.x)
        self.drive.tick()
        if self.punish_window > 0:
            self.punish_window -= 1

        # Drive Parry: stop if burnout triggered by drain
        if self.parrying and self.drive.burnout:
            self.parrying = False
            self.drive.stop_drive_parry()

        # Drive Rush: advance forward dash
        if self.drive_rushing:
            self.dr_frames -= 1
            self.body.vel_x = self.data.dash_forward_vel * self.facing * 1.5
            if self.dr_frames <= 0:
                self.drive_rushing = False
                self.body.vel_x = 0.0

        for proj in self.projectiles:
            proj.tick()
        self.projectiles = [p for p in self.projectiles if p.active]
        if self.in_stun:
            self.stun_frames -= 1
            if self.stun_frames <= 0:
                self._finish_action()
            # decay knockback velocity while grounded
            if not self.body.airborne:
                self.body.vel_x *= 0.6
            self.body.apply_gravity()
            self.body.integrate()
            self.body.clamp_stage()
            return
        move_name = self.data.action_to_move(action_id)
        self._process_action(action_id, move_name, opponent)
        self.body.apply_gravity()
        self.body.integrate()
        self.body.clamp_stage()
        # Landing recovery: enter a brief landing state after touching ground from a jump
        if self.body.just_landed and self.current_action not in ("hitstun", "blockstun", "knockdown", "crumple", "landing"):
            self.current_action = "landing"
            self.action_frame = 0
            self.body.vel_x = 0.0

    def _process_action(self, action_id: int, move_name: str, opponent) -> None:
        stun_states = ("hitstun", "blockstun", "knockdown", "crumple")
        if self.current_action in stun_states:
            self.action_frame += 1
            total = self.data.get_total_frames(self.current_action)
            if self.action_frame >= total:
                self._finish_action()
            return

        # Landing recovery: brief window after touching ground from a jump
        if self.current_action == "landing":
            self.action_frame += 1
            if self.action_frame >= LANDING_RECOVERY_FRAMES:
                self._finish_action()
            return

        # while airborne, only allow air attacks or idle (preserve vel_x)
        if self.body.airborne:
            if move_name in self.data.airborne_only or action_id in self.data.airborne_only:
                if self.current_action in ("jump", "idle"):
                    self._start_attack(action_id, move_name, opponent)
            # if already in an air attack, advance its frames
            if self.current_action not in ("jump", "idle"):
                self.action_frame += 1
                move = self.data.get_move(self.current_action)
                if move:
                    total = self.data.get_total_frames(self.current_action)
                    if self.action_frame >= total:
                        self._finish_action()
            return

        neutral = ("idle", "walk_forward", "walk_back", "crouch", "jump")
        dash_states = ("dash_forward", "dash_back")
        if self.current_action in dash_states:
            self.action_frame += 1
            move = self.data.get_move(self.current_action)
            total = self.data.get_total_frames(self.current_action) if move else 1
            if move:
                active = move.get("active", 1)
                startup = move.get("startup", 1)
                if self.action_frame >= startup + active:
                    self.body.vel_x *= 0.5
            if self.action_frame >= total:
                self.body.vel_x = 0.0
                self._finish_action()
            return

        if self.current_action not in neutral:
            self.action_frame += 1
            move = self.data.get_move(self.current_action)
            if move:
                startup = move.get("startup", 0)
                active = move.get("active", 1)
                # Invincibility: check invuln_str from frame data, or hardcoded for drive_reversal
                if self.current_action == "drive_reversal":
                    self.invincible = self.action_frame <= startup
                else:
                    self.invincible = _is_invincible_at_frame(move, self.action_frame)
                if self.action_frame == startup and "projectile" in move.get("properties", []):
                    self._spawn_projectile(self.current_action)
                # Cancel window: from first active frame through recovery's first 3 frames
                # (startup frames are NOT cancellable — attack hasn't come out yet)
                last_active = _last_active_frame(move)
                in_cancel_window = (
                    startup <= self.action_frame <= last_active + 3
                )
                if in_cancel_window and move_name not in neutral and move_name != "idle":
                    if self._try_cancel(action_id, move_name, move):
                        return
            total = self.data.get_total_frames(self.current_action)
            if self.action_frame >= total:
                self._finish_action()
            return
        # 精防状态下锁定为 idle，不处理任何攻击输入
        if self.parrying:
            self.current_action = "idle"
            self.body.vel_x = 0.0
            return
        self._handle_movement(action_id, move_name, opponent)

    def _try_cancel(self, action_id: int, new_move_name: str, current_move: dict) -> bool:
        """Attempt to cancel current action into new_move_name. Returns True if successful."""
        cancel_into = self.data.get_cancel_into(self.current_action)
        new_move = self.data.get_move(new_move_name)
        if not new_move:
            return False

        # determine cancel category of the new move
        new_props = new_move.get("properties", [])
        is_special = "special" in new_props
        is_super = new_move.get("super_cost", 0) > 0
        is_normal = not is_special and not is_super

        allowed = False
        if "specials" in cancel_into and is_special:
            allowed = True
        if "super" in cancel_into and is_super:
            allowed = True
        # normals can only cancel into normals if explicitly listed
        if "normals" in cancel_into and is_normal:
            allowed = True

        if not allowed:
            return False

        # must have hit connected for special/super cancel (hit-confirm)
        # but allow free cancel for normals
        if (is_special or is_super) and not self.hit_connected_this_action:
            # allow cancel even without hit (SF6 allows special cancel on block too)
            pass

        return self._start_attack(action_id, new_move_name, None) is not False

    def _handle_movement(self, action_id: int, move_name: str, opponent) -> None:
        airborne = self.body.airborne
        if move_name == "walk_forward":
            self.body.vel_x = self.data.walk_speed_forward * self.facing
            self.current_action = "walk_forward"
            self.is_blocking = False
            self.crouching = False
        elif move_name == "walk_back":
            self.body.vel_x = self.data.walk_speed_back * -self.facing
            self.current_action = "walk_back"
            self.is_blocking = True
            self.crouching = False
        elif move_name == "crouch":
            self.body.vel_x = 0.0
            self.current_action = "crouch"
            self.crouching = True
            # Crouch blocking: if already blocking (walk_back), keep blocking
            # Otherwise, crouch without blocking (neutral crouch)
            # is_blocking state is preserved from previous frame
        elif move_name == "jump" and not airborne:
            self.body.jump()
            self.body.vel_x = 0.0
            self.current_action = "jump"
            self.is_blocking = False
            self.crouching = False
        elif move_name == "jump_forward" and not airborne:
            self.body.jump()
            self.body.vel_x = self.data.jump_forward_vel * self.facing
            self.current_action = "jump"
            self.is_blocking = False
            self.crouching = False
        elif move_name == "jump_back" and not airborne:
            self.body.jump()
            self.body.vel_x = self.data.jump_back_vel * self.facing
            self.current_action = "jump"
            self.is_blocking = False
            self.crouching = False
        elif move_name == "dash_forward" and not airborne:
            if self.current_action not in ("dash_forward", "dash_back"):
                self.current_action = "dash_forward"
                self.action_frame = 0
                self.body.vel_x = self.data.dash_forward_vel * self.facing
            self.is_blocking = False
            self.crouching = False
        elif move_name == "dash_back" and not airborne:
            if self.current_action not in ("dash_forward", "dash_back"):
                self.current_action = "dash_back"
                self.action_frame = 0
                self.body.vel_x = self.data.dash_back_vel * self.facing
            self.is_blocking = False
            self.crouching = False
        elif move_name == "idle":
            if not airborne:
                self.body.vel_x = 0.0
            self.current_action = "idle" if not airborne else self.current_action
            self.is_blocking = False
            self.crouching = False
        else:
            self._start_attack(action_id, move_name, opponent)
    def _start_attack(self, action_id: int, move_name: str, opponent) -> bool:
        move = self.data.get_move(move_name)
        if not move:
            return False
        airborne = self.body.airborne
        if action_id in self.data.airborne_only and not airborne:
            return False
        if action_id in self.data.ground_only and airborne:
            return False
        drive_cost = move.get("drive_cost", 0.0)
        if drive_cost > 0 and not self.drive.spend(drive_cost):
            return False
        super_cost = move.get("super_cost", 0)
        if super_cost > 0 and self.super_gauge < super_cost:
            return False
        if super_cost > 0:
            self.super_gauge -= super_cost
        self.current_action = move_name
        self.action_frame = 0
        self.hit_connected_this_action = False
        self.hits_this_action = 0
        # Reset DI armor when starting a new Drive Impact
        if move_name == "drive_impact":
            self.di_armor_used = False
        # preserve vel_x while airborne so jump arc continues
        if not airborne:
            self.body.vel_x = 0.0
        # 投技：startup 期间前冲
        if "throw" in move.get("properties", []):
            self.body.vel_x = 5.0 * self.facing
        return True

    def _finish_action(self) -> None:
        if self.body.airborne:
            self.current_action = "jump"
        elif self.crouching:
            self.current_action = "crouch"
        else:
            self.current_action = "idle"
        self.action_frame = 0

    def receive_hit(self, event, combo_count: int = 0) -> bool:
        """
        Apply hit/block effects to this character.

        Returns:
            True if Drive Parry successfully absorbed the hit (attacker should be stunned)
        """
        # Drive Reversal startup is fully invincible
        if self.invincible:
            return False
        # Drive Parry: absorb the hit, gain +6F advantage, stop parrying
        if self.parrying and "throw" not in event.properties and "unblockable" not in event.properties:
            self.parrying = False
            self.drive.stop_drive_parry()
            # Parry success: defender gains drive and is free to act
            # Attacker will be stunned by game.py
            self.drive.gain(0.5)
            return True
        # Drive Impact armor: absorbs one hit during startup (frames 1 to startup-1)
        if self.current_action == "drive_impact":
            move = self.data.get_move("drive_impact")
            startup = move.get("startup", 26)
            if self.action_frame < startup and "throw" not in event.properties:
                if not self.di_armor_used:
                    self.di_armor_used = True
                    return False  # armor absorbs the hit (one-time only)
        move = self.data.get_move(event.move_name)
        is_low = "low" in event.properties
        is_overhead = "overhead" in event.properties
        is_throw = "throw" in event.properties
        if is_throw:
            self._apply_hitstun(event, combo_count)
            return False
        can_block = (self.is_blocking and not is_overhead and
                     not (is_low and not self.crouching))
        if can_block:
            self._apply_blockstun(event)
        else:
            self._apply_hitstun(event, combo_count)
        return False

    def _apply_hitstun(self, event, combo_count: int = 0) -> None:
        # SF6 damage scaling: 100% / 90% / 80% / ... / 20% minimum
        scale = max(0.2, 1.0 - combo_count * 0.1)
        actual_damage = int(event.damage * scale)
        if self.drive.burnout and "special" in event.properties:
            actual_damage = int(actual_damage * 0.25)
        self.health = max(0, self.health - actual_damage)
        self.drive.gain(event.drive_gain_hit)

        ch_bonus = 2 if event.hit_type == HIT_COUNTER else 0
        pc_bonus = 4 if event.hit_type == HIT_PUNISH else 0
        frame_bonus = ch_bonus + pc_bonus

        if "knockdown" in event.properties:
            self.stun_frames = 60
            self.current_action = "knockdown"
            self.body.vel_x = -self.facing * 3.0
        elif "throw" in event.properties:
            # 投技：抛起效果
            self.stun_frames = max(1, 14 + event.on_hit_adv)
            self.current_action = "hitstun"
            self.body.vel_x = -self.facing * 3.0
            self.body.vel_y = 10.0
            self.body.airborne = True
        elif "crumple" in event.properties or event.hit_type == HIT_PUNISH:
            self.stun_frames = 80
            self.current_action = "crumple"
            self.body.vel_x = -self.facing * 2.0
        else:
            dr_bonus = 4 if event.attacker_drive_rush else 0
            hitstun = max(1, 14 + event.on_hit_adv + dr_bonus + frame_bonus)
            self.stun_frames = hitstun
            self.current_action = "hitstun"
            self.body.vel_x = -self.facing * 4.0
        self.action_frame = 0
        self.is_blocking = False
        self.punish_window = 0

    def _apply_blockstun(self, event) -> None:
        chip = event.chip_damage
        if self.drive.burnout:
            self.health = max(0, self.health - chip)
        # drive_gain_block is negative in new frame data (attacker loses drive on block)
        # but we apply it to the defender's drive gauge (defender gains drive on block)
        # so flip the sign: defender gains abs(drive_gain_block)
        defender_drive_gain = abs(event.drive_gain_block)
        self.drive.gain(defender_drive_gain)

        dr_bonus = 4 if event.attacker_drive_rush else 0
        extra = BURNOUT_EXTRA_BLOCKSTUN if self.drive.burnout else 0
        blockstun = max(1, 11 + event.on_block_adv + dr_bonus + extra)
        self.stun_frames = blockstun
        self.current_action = "blockstun"
        self.action_frame = 0
        self.body.vel_x = -self.facing * 2.0
        if event.on_block_adv < 0:
            self.punish_window = abs(event.on_block_adv)

    def _spawn_projectile(self, move_name: str) -> None:
        move = self.data.get_move(move_name)
        if not move:
            return
        proj = Projectile(
            owner_id=self.player_id,
            x=self.body.x + 60 * self.facing,
            y=self.body.y + 80,
            vel_x=8.0 * self.facing,
            damage=move.get("damage", 800),
            chip_damage=move.get("chip_damage", 200),
            on_hit_adv=move.get("on_hit", 2),
            on_block_adv=move.get("on_block", -2),
            drive_gain_hit=move.get("drive_gain_hit", 0.5),
            drive_gain_block=move.get("drive_gain_block", 0.25),
            properties=move.get("properties", []),
            move_name=move_name,
        )
        self.projectiles.append(proj)

    def start_drive_parry(self) -> bool:
        """Start Drive Parry (hold MP+MK)."""
        if self.drive.start_drive_parry():
            self.parrying = True
            return True
        return False

    def stop_drive_parry(self) -> None:
        """Stop Drive Parry."""
        self.parrying = False
        self.drive.stop_drive_parry()

    def start_drive_rush(self, from_parry: bool = False) -> bool:
        """Start Drive Rush (forward dash with +4F bonus)."""
        if self.drive.start_drive_rush(from_parry):
            self.drive_rushing = True
            self.dr_frames = DR_DURATION
            return True
        return False

    def mark_hit_connected(self) -> None:
        self.hits_this_action += 1
        move = self.current_move_data
        max_hits = move.get("hit_count", 1) if move else 1
        if self.hits_this_action >= max_hits:
            self.hit_connected_this_action = True
        if move:
            # drive_gain_hit is positive in new frame data (attacker gains drive on hit)
            self.drive.gain(move.get("drive_gain_hit", 0.0))
            sc = move.get("super_cost", 0)
            if sc == 0:
                self.super_gauge = min(SUPER_GAUGE_MAX, self.super_gauge + 0.3)

    def increment_combo(self) -> None:
        self.combo_count += 1

    def reset_combo(self) -> None:
        self.combo_count = 0
