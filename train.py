#!/usr/bin/env python3
import argparse
from sf6_env.rl.train import train

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train SF6 RL agent")
    parser.add_argument("--steps", type=int, default=10_000_000)
    parser.add_argument("--envs", type=int, default=8)
    parser.add_argument("--save", type=str, default="models/")
    parser.add_argument("--log", type=str, default="logs/")
    args = parser.parse_args()
    train(total_timesteps=args.steps, n_envs=args.envs,
          save_path=args.save, log_path=args.log)
