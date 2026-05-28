from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sf6_env.engine.character import Character

STAGE_LEFT: float = 0.0
STAGE_RIGHT: float = 1000.0
GROUND_Y: float = 0.0
GRAVITY: float = 0.8
JUMP_VELOCITY: float = 18.0
PUSH_BOX_WIDTH: float = 60.0


@dataclass
class PhysicsBody:
    x: float = 500.0
    y: float = GROUND_Y
    vel_x: float = 0.0
    vel_y: float = 0.0
    airborne: bool = False

    def apply_gravity(self) -> None:
        if self.airborne:
            self.vel_y -= GRAVITY

    def integrate(self) -> None:
        self.x += self.vel_x
        self.y += self.vel_y
        if self.y <= GROUND_Y:
            self.y = GROUND_Y
            self.vel_y = 0.0
            self.airborne = False

    def clamp_stage(self) -> None:
        self.x = max(STAGE_LEFT + PUSH_BOX_WIDTH / 2,
                     min(STAGE_RIGHT - PUSH_BOX_WIDTH / 2, self.x))

    def jump(self) -> None:
        if not self.airborne:
            self.vel_y = JUMP_VELOCITY
            self.airborne = True


def resolve_pushboxes(p1: "Character", p2: "Character") -> None:
    """Prevent characters from overlapping via push boxes."""
    half = PUSH_BOX_WIDTH / 2
    overlap = (p1.body.x + half) - (p2.body.x - half)
    if overlap <= 0:
        return

    push = overlap / 2
    p1_at_wall = p1.body.x - half <= STAGE_LEFT
    p2_at_wall = p2.body.x + half >= STAGE_RIGHT

    if p1_at_wall and p2_at_wall:
        return
    elif p1_at_wall:
        p2.body.x += overlap
    elif p2_at_wall:
        p1.body.x -= overlap
    else:
        p1.body.x -= push
        p2.body.x += push

    p1.body.clamp_stage()
    p2.body.clamp_stage()
