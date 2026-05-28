from __future__ import annotations
import numpy as np
from sf6_env.engine.game import Game
from sf6_env.engine.drive import DRIVE_MAX
from sf6_env.engine.game import ROUND_TIME_FRAMES
from sf6_env.engine.physics import STAGE_LEFT, STAGE_RIGHT, JUMP_VELOCITY
from sf6_env.characters.mai import NUM_ACTIONS

STAGE_WIDTH = STAGE_RIGHT - STAGE_LEFT
MAX_HEALTH = 10000.0
SUPER_MAX = 3.0
MAX_STUN = 120.0
MAX_VEL_X = 15.0
MAX_COMBO = 20.0

# Per-character features (14):
#   x, y, health, drive, super, action_norm, frame_pct,
#   airborne, burnout, blocking, stun_norm, vel_x_norm, punish_window_norm, combo_norm
# Global features (2): distance, timer
# Total: 2*14 + 2 = 30
OBS_SIZE = 30


def build_obs(game: Game, perspective: int) -> np.ndarray:
    if perspective == 0:
        self_c, opp_c = game.p1, game.p2
    else:
        self_c, opp_c = game.p2, game.p1

    def char_features(c):
        x_norm = (c.body.x - STAGE_LEFT) / STAGE_WIDTH
        y_norm = min(c.body.y / 200.0, 1.0)
        health_norm = c.health / MAX_HEALTH
        drive_norm = c.drive.value / DRIVE_MAX
        super_norm = c.super_gauge / SUPER_MAX
        action_id = list(c.data.action_map.values()).index(c.current_action) \
            if c.current_action in c.data.action_map.values() else 0
        action_norm = action_id / max(NUM_ACTIONS - 1, 1)
        total_frames = max(c.data.get_total_frames(c.current_action), 1)
        frame_pct = min(c.action_frame / total_frames, 1.0)
        airborne = float(c.body.airborne)
        burnout = float(c.drive.burnout)
        blocking = float(c.is_blocking)
        stun_norm = min(c.stun_frames / MAX_STUN, 1.0)
        vel_x_norm = (c.body.vel_x / MAX_VEL_X + 1.0) / 2.0  # [-1,1] → [0,1]
        punish_norm = min(c.punish_window / 20.0, 1.0)
        combo_norm = min(c.combo_count / MAX_COMBO, 1.0)
        return [x_norm, y_norm, health_norm, drive_norm, super_norm,
                action_norm, frame_pct, airborne, burnout, blocking,
                stun_norm, vel_x_norm, punish_norm, combo_norm]

    self_feats = char_features(self_c)
    opp_feats = char_features(opp_c)
    distance = abs(self_c.body.x - opp_c.body.x) / STAGE_WIDTH
    timer = 1.0 - game.frame_count / ROUND_TIME_FRAMES

    obs = np.array(self_feats + opp_feats + [distance, timer], dtype=np.float32)
    return obs
