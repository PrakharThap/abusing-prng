import random

from prng import *


def flip_until(prng: PRNG, num: int):
    n = 0
    count = 0

    while count < num:
        newVal = prng.next_value
        side = Flip((newVal >> 31) & 1)
        guess = random.choice((Flip.HEADS, Flip.TAILS))

        if guess == side:
            count += 1
        else:
            count = 0
        n += 1

    return n


def avg_flip_until(prng, num, iters=1000):
    avg = 0
    for _ in range(iters):
        avg += flip_until(prng, num)
    avg /= iters

    print(f"Avg # flips for {num} correct guesses in a row: {avg}")

    return avg
