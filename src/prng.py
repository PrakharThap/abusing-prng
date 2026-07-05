from abc import abstractmethod
from functools import partial
from enum import Enum


class Flip(Enum):
    HEADS = 0
    TAILS = 1

    @classmethod
    def BIT_INTERPRETER(cls, val: int, bit: int) -> "Flip":
        return cls.HEADS if (val >> bit) & 1 else cls.TAILS

    @classmethod
    def THRESHOLD_INTERPRETER(cls, val: int, threshold: int) -> "Flip":
        return cls.HEADS if val >= threshold else cls.TAILS


class PRNG:
    def __init__(self, seed: int) -> None:
        self.initial_seed = seed
        self.seed = seed
        self.interpreter = None

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
    @abstractmethod
    def current_flip(self) -> Flip:
        return self.interpreter(val=self.seed)

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

        self.interpreter = partial(
            Flip.THRESHOLD_INTERPRETER, threshold=(10**self.digits) // 2
        )

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

        self.interpreter = partial(Flip.BIT_INTERPRETER, bit=m.bit_count() - 1)

    @property
    def next_value(self) -> int:
        return self.set_seed((self.a * self.seed + self.c) % self.m)


# Xorshift (Shift Register Generator)
class SRG(PRNG):
    MASK = 0xFFFFFFFF

    def __init__(self, seed: int, a: int = 13, b: int = 7, c: int = 17) -> None:
        super().__init__(seed)
        self.a = a
        self.b = b
        self.c = c

        self.interpreter = partial(Flip.BIT_INTERPRETER, bit=0)

    @property
    def next_value(self) -> int:
        newSeed = self.seed
        newSeed ^= (newSeed << self.a) & SRG.MASK
        newSeed ^= (newSeed >> self.b) & SRG.MASK
        newSeed ^= (newSeed << self.c) & SRG.MASK

        return self.set_seed(newSeed)
