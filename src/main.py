import random

from guesser import *
from prng import *


def main():
    # Random 4 digit seed
    seed = random.randint(1000, 9999)
    prng = LCG(2**32, 1664525, 1013904223, seed)

    flips = flip_until(prng, 1)

    print(f"Initial seed: {seed}")
    print(f"# flips for 3 correct guesses in a row: {flips}")


if __name__ == "__main__":
    main()
