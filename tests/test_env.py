import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from sf6_env.rl.env import SF6Env
from sf6_env.rl.obs import OBS_SIZE


def test_env_reset():
    env = SF6Env()
    obs, info = env.reset()
    assert obs.shape == (OBS_SIZE,)
    assert all(0.0 <= v <= 1.0 for v in obs)


def test_env_step_idle():
    env = SF6Env()
    env.reset()
    obs, reward, terminated, truncated, info = env.step(0)
    assert obs.shape == (OBS_SIZE,)
    assert isinstance(reward, float)
    assert not terminated


def test_env_runs_full_round():
    env = SF6Env()
    env.reset()
    done = False
    steps = 0
    while not done and steps < 10000:
        obs, reward, terminated, truncated, info = env.step(0)
        done = terminated or truncated
        steps += 1
    assert done, "Round should end within 10000 steps"


def test_env_action_space():
    env = SF6Env()
    assert env.action_space.n > 0
    env.reset()
    for _ in range(10):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        if terminated:
            env.reset()
