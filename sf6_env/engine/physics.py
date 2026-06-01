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


LANDING_RECOVERY_FRAMES: int = 4  # frames of landing recovery after a jump


@dataclass
class PhysicsBody:
    x: float = 500.0
    y: float = GROUND_Y
    vel_x: float = 0.0
    vel_y: float = 0.0
    airborne: bool = False
    just_landed: bool = False  # True for one frame when touching ground after being airborne

    def apply_gravity(self) -> None:
        if self.airborne:
            self.vel_y -= GRAVITY

    def integrate(self) -> None:
        self.just_landed = False
        self.x += self.vel_x
        self.y += self.vel_y
        if self.y <= GROUND_Y and self.airborne:
            self.y = GROUND_Y
            self.vel_y = 0.0
            self.airborne = False
            self.just_landed = True
        elif self.y <= GROUND_Y:
            self.y = GROUND_Y
            self.vel_y = 0.0

    def clamp_stage(self) -> None:
        self.x = max(STAGE_LEFT + PUSH_BOX_WIDTH / 2,
                     min(STAGE_RIGHT - PUSH_BOX_WIDTH / 2, self.x))

    def jump(self) -> None:
        if not self.airborne:
            self.vel_y = JUMP_VELOCITY
            self.airborne = True


def resolve_pushboxes(p1: "Character", p2: "Character") -> None:
    """Prevent characters from overlapping via push boxes.

    Works regardless of which character is on the left or right.
    """
    half = PUSH_BOX_WIDTH / 2
    # Determine left/right character dynamically
    if p1.body.x <= p2.body.x:
        left, right = p1, p2
    else:
        left, right = p2, p1

    overlap = (left.body.x + half) - (right.body.x - half)
    if overlap <= 0:
        return

    push = overlap / 2
    left_at_wall = left.body.x - half <= STAGE_LEFT
    right_at_wall = right.body.x + half >= STAGE_RIGHT

    if left_at_wall and right_at_wall:
        # Both at walls — can't push further, do nothing
        return
    elif left_at_wall:
        # Left character is cornered: push right character away
        right.body.x += overlap
    elif right_at_wall:
        # Right character is cornered: push left character away
        left.body.x -= overlap
    else:
        left.body.x -= push
        right.body.x += push

    left.body.clamp_stage()
    right.body.clamp_stage()
