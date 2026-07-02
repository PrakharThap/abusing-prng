from abc import abstractmethod
from enum import Enum

class Flip(Enum):
    HEADS = 0
    TAILS = 1


class PRNG:
    def __init__(self, seed: int) -> None:
        self.initial_seed = seed
        self.seed = seed

    @abstractmethod
    def sub_init(self) -> None:
        pass

    def reset(self, seed: int | None = None) -> None:
        if seed is not None:
            self.initial_seed = seed
        self.seed = self.initial_seed
        self.sub_init()

    def generate_values(self, numValues):
        for _ in range(numValues):
            yield self.next_value

    @property
    @abstractmethod
    def next_value(self) -> int:
        pass

    @property
    def current_seed(self) -> int:
        return self.seed

    def set_seed(self, newSeed: int) -> int:
        self.seed = newSeed
        return newSeed


# Squares seed and extracts middle n digits to find new seed
class MiddleSquare(PRNG):
    def __init__(self, seed: int) -> None:
        super().__init__(seed)
        self.digits = len(str(self.seed))
        self._cycle_detected = False

    @property
    def next_value(self) -> int:
        return self.set_seed(
            int(
                str(self.seed * self.seed).zfill(self.digits * 2)[
                    (self.digits // 2) : (self.digits * 3 // 2)
                ]
            )
        )


# Linear Congruential Generator
class LCG(PRNG):
    def __init__(self, m: int, a: int, c: int, seed: int) -> None:
        super().__init__(seed)
        self.m = m
        self.a = a
        self.c = c

    @property
    def next_value(self) -> int:
        return self.set_seed((self.a * self.seed + self.c) % self.m)
