from __future__ import annotations
import os
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import CheckpointCallback
from sf6_env.rl.env import SF6Env


def train(
    total_timesteps: int = 10_000_000,
    n_envs: int = 8,
    save_path: str = "models/",
    log_path: str = "logs/",
):
    os.makedirs(save_path, exist_ok=True)
    os.makedirs(log_path, exist_ok=True)

    env = make_vec_env(SF6Env, n_envs=n_envs, env_kwargs={"perspective": 0})

    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        tensorboard_log=log_path,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
    )

    checkpoint_cb = CheckpointCallback(
        save_freq=100_000,
        save_path=save_path,
        name_prefix="sf6_mai",
    )

    model.learn(total_timesteps=total_timesteps, callback=checkpoint_cb)
    model.save(os.path.join(save_path, "sf6_mai_final"))
    print(f"Training complete. Model saved to {save_path}")
    return model
