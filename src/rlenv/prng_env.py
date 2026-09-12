import sys
import os
from typing import Optional
import numpy as np
import gymnasium as gym
from gymnasium import spaces

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from prng import Flip, make_prng, PRNG


class PRNGEnv(gym.Env):
    def __init__(
        self,
        prng_type: str = "LCG",
        seed: int = 42,
        params: Optional[dict] = None,
        max_skip: int = 50,
        max_streak: int = 5,
        history_len: int = 10,
        max_steps: int = 100,
    ):
        super().__init__()

        self.prng_type = prng_type
        self.params = params
        self.max_skip = max_skip
        self.max_streak = max_streak
        self.history_len = history_len
        self.max_steps = max_steps

        self.action_space = spaces.MultiDiscrete([max_skip, 2])

        obs_dim = history_len * 3 + 3
        self.observation_space = spaces.Box(
            low=-1.0, high=1.0, shape=(obs_dim,), dtype=np.float32
        )

        self._setup_prng_seed = seed
        self.results_history = None
        self.guesses_history = None
        self.skips_history = None
        self.streak = None
        self.step_count = None
        self.last_correct = None
        self.prng = None

    def _make_prng(self, seed: int) -> PRNG:
        return make_prng(self.prng_type, seed, self.params)

    def _get_obs(self):
        return np.array(
            self.results_history
            + self.guesses_history
            + self.skips_history
            + [
                self.streak / self.max_streak,
                self.step_count / self.max_steps,
                self.last_correct,
            ],
            dtype=np.float32,
        )

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        prng_seed = (
            seed if seed is not None else int(self.np_random.integers(1, 2**31 - 1))
        )
        self.prng = self._make_prng(prng_seed)

        self.results_history = [-1.0] * self.history_len
        self.guesses_history = [-1.0] * self.history_len
        self.skips_history = [0.0] * self.history_len
        self.streak = 0
        self.step_count = 0
        self.last_correct = 0.0

        return self._get_obs(), {}

    def step(self, action):
        skip = int(action[0]) + 1
        pred = int(action[1])

        for _ in range(skip):
            self.prng.next_value

        actual_flip = self.prng.current_flip.value
        correct = int(pred == actual_flip)

        if correct:
            self.streak += 1
        else:
            self.streak = 0

        self.results_history = self.results_history[1:] + [float(actual_flip)]
        self.guesses_history = self.guesses_history[1:] + [float(pred)]
        self.skips_history = self.skips_history[1:] + [skip / self.max_skip]
        self.last_correct = float(correct)
        self.step_count += 1

        if not correct:
            reward = 0
        elif self.streak < 5:
            reward = 0.1  # tiny, just enough to guide early learning
        else:
            reward = 1 / self.step_count  # dominant signal

        terminated = bool(self.streak >= self.max_streak)
        truncated = bool(self.step_count >= self.max_steps)

        return self._get_obs(), reward, terminated, truncated, {}

    def render(self, mode="human"):
        pass
