from __future__ import annotations
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from sf6_env.engine.game import Game
from sf6_env.characters.mai import MaiData, NUM_ACTIONS
from sf6_env.rl.obs import build_obs, OBS_SIZE
from sf6_env.rl.reward import compute_reward


class SF6Env(gym.Env):
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 60}

    def __init__(self, render_mode=None, perspective: int = 0):
        super().__init__()
        self.render_mode = render_mode
        self.perspective = perspective

        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(OBS_SIZE,), dtype=np.float32
        )
        self.action_space = spaces.Discrete(NUM_ACTIONS)

        self._game: Game = None
        self._prev_state: dict = None
        self._renderer = None

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        mai_p1 = MaiData()
        mai_p2 = MaiData()
        self._game = Game(mai_p1, mai_p2)
        self._prev_state = self._game.get_state()
        obs = build_obs(self._game, self.perspective)
        return obs, {}

    def step(self, action):
        p1_action = int(action) if self.perspective == 0 else 0
        p2_action = int(action) if self.perspective == 1 else 0

        round_over, winner = self._game.step(p1_action, p2_action)
        curr_state = self._game.get_state()

        reward = compute_reward(self._prev_state, curr_state, self.perspective)
        self._prev_state = curr_state

        obs = build_obs(self._game, self.perspective)
        terminated = round_over
        truncated = False
        info = {"winner": winner, "frame": self._game.frame_count}

        if self.render_mode == "human":
            self.render()

        return obs, reward, terminated, truncated, info

    def render(self):
        if self._renderer is None:
            from sf6_env.render.pygame_renderer import PygameRenderer
            self._renderer = PygameRenderer()
        return self._renderer.render(self._game)

    def close(self):
        if self._renderer is not None:
            self._renderer.close()
            self._renderer = None


class SF6EnvSelfPlay(SF6Env):
    """Both players are controlled by the same policy (self-play)."""

    def step(self, action):
        p1_action = int(action[0]) if hasattr(action, "__len__") else int(action)
        p2_action = int(action[1]) if hasattr(action, "__len__") and len(action) > 1 else 0

        round_over, winner = self._game.step(p1_action, p2_action)
        curr_state = self._game.get_state()

        r1 = compute_reward(self._prev_state, curr_state, 0)
        r2 = compute_reward(self._prev_state, curr_state, 1)
        self._prev_state = curr_state

        obs1 = build_obs(self._game, 0)
        obs2 = build_obs(self._game, 1)
        terminated = round_over
        truncated = False
        info = {"winner": winner}

        if self.render_mode == "human":
            self.render()

        return (obs1, obs2), (r1, r2), terminated, truncated, info
