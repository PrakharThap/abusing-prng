import sys
import os
import argparse
from sb3_contrib import RecurrentPPO
from stable_baselines3.common.vec_env import DummyVecEnv
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from env.prng_env import PRNGEnv

LCG_PRESETS = {
    "randu": {"m": 2**31, "a": 65539, "c": 0},
    "glibc": {"m": 2**31, "a": 1103515245, "c": 12345},
    "minstd": {"m": 2**31 - 1, "a": 16807, "c": 0},
    "msvc": {"m": 2**31, "a": 214013, "c": 2531011},
}


def _params_for(prng_type, preset):
    if prng_type == "LCG":
        if preset:
            p = LCG_PRESETS[preset]
            return {"m": p["m"], "a": p["a"], "c": p["c"], "interpreter": {"type": "bit", "value": 30}}
        return {"m": 2**31, "a": 1103515245, "c": 12345, "interpreter": {"type": "bit", "value": 30}}
    if prng_type == "Xorshift":
        return {"a": 13, "b": 7, "c": 17, "interpreter": {"type": "bit", "value": 0}}
    return {"interpreter": {"type": "threshold", "value": 500000}}


def _model_name_for(prng_type, preset):
    if prng_type == "LCG" and preset:
        return f"LCG_{preset}"
    return prng_type.replace(" ", "_")


def make_env(prng_type, params, max_skip=50):
    def _init():
        return PRNGEnv(prng_type=prng_type, seed=0, params=params, max_skip=max_skip)
    return _init


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prng", choices=["Middle Square", "LCG", "Xorshift"], default="LCG")
    parser.add_argument("--preset", choices=list(LCG_PRESETS.keys()), default=None)
    parser.add_argument("--timesteps", type=int, default=200_000)
    parser.add_argument("--max-skip", type=int, default=50)
    parser.add_argument("--output-dir", default="models")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    params = _params_for(args.prng, args.preset)
    model_name = _model_name_for(args.prng, args.preset)

    env = PRNGEnv(
        prng_type=args.prng,
        seed=0,
        params=params,
        max_skip=args.max_skip,
    )

    print(f"Training PPO-LSTM for {args.prng} (preset={args.preset})")
    print(f"  Observation space: {env.observation_space}")
    print(f"  Action space: {env.action_space}")

    vec_env = DummyVecEnv([lambda: env])

    model = RecurrentPPO(
        "MlpLstmPolicy",
        vec_env,
        verbose=1,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        learning_rate=3e-4,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        policy_kwargs={"lstm_hidden_size": 128, "n_lstm_layers": 1},
    )

    model.learn(total_timesteps=args.timesteps)

    path = os.path.join(args.output_dir, f"{model_name}.zip")
    model.save(path)
    print(f"Model saved to {path}")

    obs, _ = env.reset(seed=42)
    lstm_states = None
    episode_starts = True
    total_reward = 0.0
    steps = 0

    while True:
        action, lstm_states = model.predict(
            obs, state=lstm_states, episode_start=episode_starts, deterministic=False
        )
        obs, reward, terminated, truncated, _ = env.step(action)
        total_reward += reward
        steps += 1
        episode_starts = terminated or truncated
        if terminated or truncated:
            break

    print(f"Evaluation: {steps} steps, total reward {total_reward:.2f}")
    env.close()


if __name__ == "__main__":
    main()
