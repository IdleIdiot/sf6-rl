from __future__ import annotations
from typing import Tuple, Optional
from sf6_env.engine.character import Character
from sf6_env.engine.physics import resolve_pushboxes
from sf6_env.engine.collision import check_hit, check_projectile_hits

ROUND_TIME_FRAMES = 5400  # 90 seconds at 60 FPS


class Game:
    def __init__(self, p1_data, p2_data):
        self.p1 = Character(p1_data, player_id=0, start_x=300.0)
        self.p2 = Character(p2_data, player_id=1, start_x=700.0)
        self.frame_count = 0
        self.round_over = False
        self.winner: Optional[int] = None

    def step(self, p1_action: int, p2_action: int) -> Tuple[bool, Optional[int]]:
        self.frame_count += 1
        self.p1.tick(p1_action, self.p2)
        self.p2.tick(p2_action, self.p1)
        resolve_pushboxes(self.p1, self.p2)
        self._check_collisions()
        self._check_round_end()
        return self.round_over, self.winner

    def _check_collisions(self) -> None:
        hit_event = check_hit(self.p1, self.p2)
        if hit_event:
            self.p2.receive_hit(hit_event, self.p1.combo_count)
            self.p1.mark_hit_connected()
            self.p1.increment_combo()
            self.p1.drive.gain(hit_event.drive_gain_hit * 0.5)
            self.p2.reset_combo()
        else:
            if self.p1.current_action in ("idle", "walk_forward", "walk_back", "crouch"):
                self.p1.reset_combo()

        hit_event = check_hit(self.p2, self.p1)
        if hit_event:
            self.p1.receive_hit(hit_event, self.p2.combo_count)
            self.p2.mark_hit_connected()
            self.p2.increment_combo()
            self.p2.drive.gain(hit_event.drive_gain_hit * 0.5)
            self.p1.reset_combo()
        else:
            if self.p2.current_action in ("idle", "walk_forward", "walk_back", "crouch"):
                self.p2.reset_combo()

        proj_hit = check_projectile_hits(self.p1.projectiles, self.p2)
        if proj_hit:
            self.p2.receive_hit(proj_hit, self.p1.combo_count)
            self.p1.increment_combo()
            self.p1.drive.gain(proj_hit.drive_gain_hit * 0.5)
            self.p2.reset_combo()
        proj_hit = check_projectile_hits(self.p2.projectiles, self.p1)
        if proj_hit:
            self.p1.receive_hit(proj_hit, self.p2.combo_count)
            self.p2.increment_combo()
            self.p2.drive.gain(proj_hit.drive_gain_hit * 0.5)
            self.p1.reset_combo()

    def _check_round_end(self) -> None:
        if self.round_over:
            return
        if not self.p1.alive:
            self.round_over = True
            self.winner = 1
        elif not self.p2.alive:
            self.round_over = True
            self.winner = 0
        elif self.frame_count >= ROUND_TIME_FRAMES:
            self.round_over = True
            if self.p1.health > self.p2.health:
                self.winner = 0
            elif self.p2.health > self.p1.health:
                self.winner = 1
            else:
                self.winner = None

    def reset(self) -> None:
        self.p1 = Character(self.p1.data, player_id=0, start_x=300.0)
        self.p2 = Character(self.p2.data, player_id=1, start_x=700.0)
        self.frame_count = 0
        self.round_over = False
        self.winner = None

    def get_state(self) -> dict:
        return {
            "p1": {
                "x": self.p1.body.x,
                "y": self.p1.body.y,
                "health": self.p1.health,
                "drive": self.p1.drive.value,
                "super": self.p1.super_gauge,
                "action": self.p1.current_action,
                "frame": self.p1.action_frame,
                "facing": self.p1.facing,
                "burnout": self.p1.drive.burnout,
                "combo_count": self.p1.combo_count,
                "punish_window": self.p1.punish_window,
            },
            "p2": {
                "x": self.p2.body.x,
                "y": self.p2.body.y,
                "health": self.p2.health,
                "drive": self.p2.drive.value,
                "super": self.p2.super_gauge,
                "action": self.p2.current_action,
                "frame": self.p2.action_frame,
                "facing": self.p2.facing,
                "burnout": self.p2.drive.burnout,
                "combo_count": self.p2.combo_count,
                "punish_window": self.p2.punish_window,
            },
            "frame": self.frame_count,
            "round_over": self.round_over,
            "winner": self.winner,
        }
