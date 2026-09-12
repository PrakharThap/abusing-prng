# PRNG Abuse 

A reinforcement learning project in trying to find patterns in different Pseudorandom Number Generator (PRNG) types in the form of a coin flipping game. 

On each "turn", the player can select a guess as to what the flip will be, and by how many iterations to advance the prng sequence. The game is won by guessing 5 times in a row correctly (by pure random guess, the expected number of guesses should be 62). 
## Features

- Various PRNG types, including Middle Square, LCG (w/ various presets), and Xorshift 
- Ability to "interpret" prng values in different ways as heads/tails, such as by setting thresholds or looking at specific bits
- Can play the game yourself (which is very boring) or train RL models on specific PRNG types and interpreters and allow it to play itself

## Usage

To run the program, simply run **src/main.py**

---

Training models works by using Recurrent PPO in a gymnasium environment. The reward function works by sending small positive signals on any correct guess, and a strong positive signal on the winning guess, with any incorrect guess being neutral. 

Training models can be done by running **src/agents/train.py**
- **--prng:** Select PRNG type to train model on ("Middle Square", "LCG", or "Xorshift")
    - *--preset:* if PRNG type is set as LCG, this parameter can be used to set preset m, a, c values ("randu", "glibc", "minstd", or "msvc")
- **--timesteps:** How many timesteps to run training for (default: 200k)
- **--max-skip:** Max value for how many iterations the model can advance the PRNG state by on each turn (default: 10)
- **--output-dir:** Where to output model after training is completed (default: models/)  
    - (When running AI play, the program will still only read models inside the default models/ directory)


