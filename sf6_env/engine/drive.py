from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sf6_env.engine.character import Character

DRIVE_MAX: float = 6.0
DRIVE_REGEN_PER_FRAME: float = 0.01          # ~600 frames to full from 0
BURNOUT_RECOVERY_FRAMES: int = 180
BURNOUT_EXTRA_BLOCKSTUN: int = 4

# Drive action costs (in Drive bars)
COST_DRIVE_IMPACT: float = 1.0
COST_DRIVE_PARRY_PER_FRAME: float = 0.03     # ~200 frames max hold
COST_DRIVE_RUSH_DIRECT: float = 1.5
COST_DRIVE_RUSH_FROM_PARRY: float = 0.0
COST_DRIVE_REVERSAL: float = 2.0
COST_OVERDRIVE: float = 2.0

# Drive Impact frame data
DI_STARTUP: int = 26
DI_ACTIVE: int = 4
DI_RECOVERY: int = 20
DI_ARMOR_FRAMES_START: int = 1
DI_ARMOR_FRAMES_END: int = 25
DI_DAMAGE: int = 1000
DI_CHIP: int = 250
DI_ON_HIT: int = 0       # leads to crumple
DI_ON_BLOCK: int = -6

# Drive Rush frame data
DR_DURATION: int = 18
DR_ADDED_HITSTUN: int = 4
DR_ADDED_BLOCKSTUN: int = 4

# Drive Parry
DP_SUCCESS_ADVANTAGE: int = 6

# Drive Reversal
DREV_STARTUP: int = 20
DREV_INVINCIBLE_FRAMES: int = 20
DREV_DAMAGE: int = 500
DREV_ON_BLOCK: int = -10


class DriveAction(Enum):
    NONE = auto()
    IMPACT = auto()
    PARRY = auto()
    RUSH = auto()
    REVERSAL = auto()


@dataclass
class DriveGauge:
    value: float = DRIVE_MAX
    burnout: bool = False
    burnout_timer: int = 0
    parrying: bool = False
    rushing: bool = False
    rush_timer: int = 0
    rush_from_parry: bool = False

    def tick(self) -> None:
        if self.burnout:
            self.burnout_timer += 1
            if self.burnout_timer >= BURNOUT_RECOVERY_FRAMES:
                self._exit_burnout()
            return

        if self.parrying:
            self._drain(COST_DRIVE_PARRY_PER_FRAME)

        if self.rushing:
            self.rush_timer -= 1
            if self.rush_timer <= 0:
                self.rushing = False

        if not self.parrying:
            self._regen()

    def _regen(self) -> None:
        self.value = min(DRIVE_MAX, self.value + DRIVE_REGEN_PER_FRAME)

    def _drain(self, amount: float) -> None:
        self.value -= amount
        if self.value <= 0.0:
            self.value = 0.0
            self._enter_burnout()

    def _enter_burnout(self) -> None:
        self.value = 0.0
        self.burnout = True
        self.burnout_timer = 0
        self.parrying = False
        self.rushing = False

    def _exit_burnout(self) -> None:
        self.burnout = False
        self.burnout_timer = 0
        self.value = DRIVE_MAX

    def can_afford(self, cost: float) -> bool:
        return not self.burnout and self.value >= cost

    def spend(self, cost: float) -> bool:
        if not self.can_afford(cost):
            return False
        self._drain(cost)
        return True

    # --- Drive action initiators ---

    def start_drive_impact(self) -> bool:
        return self.spend(COST_DRIVE_IMPACT)

    def start_drive_parry(self) -> bool:
        if self.burnout:
            return False
        self.parrying = True
        return True

    def stop_drive_parry(self) -> None:
        self.parrying = False

    def start_drive_rush(self, from_parry: bool = False) -> bool:
        cost = COST_DRIVE_RUSH_FROM_PARRY if from_parry else COST_DRIVE_RUSH_DIRECT
        if not self.spend(cost):
            return False
        self.rushing = True
        self.rush_timer = DR_DURATION
        self.rush_from_parry = from_parry
        if from_parry:
            self.parrying = False
        return True

    def start_drive_reversal(self) -> bool:
        return self.spend(COST_DRIVE_REVERSAL)

    def spend_overdrive(self) -> bool:
        return self.spend(COST_OVERDRIVE)

    def gain(self, amount: float) -> None:
        if not self.burnout:
            self.value = min(DRIVE_MAX, self.value + amount)

    @property
    def normalized(self) -> float:
        return self.value / DRIVE_MAX
