import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from prng import MiddleSquare


def generate_sequence(seed, count):
    prng = MiddleSquare(seed)
    values = list(prng.generate_values(count))
    parity = [v % 2 for v in values]
    return values, parity


def plot_parity_bars(parity, ax, max_display=200):
    data = parity[:max_display]
    n = len(data)
    colors = ["#e74c3c" if p == 1 else "#3498db" for p in data]
    ax.bar(range(n), data, color=colors, width=0.8, edgecolor="none")
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Parity (1=Odd, 0=Even)")
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["Even", "Odd"])
    ax.set_xlim(-0.5, n - 0.5)
    ax.set_title(f"Odd/Even Sequence (first {n} values)")


def plot_transition_matrix(parity, ax):
    trans = np.zeros((2, 2), dtype=int)
    for i in range(len(parity) - 1):
        trans[parity[i], parity[i + 1]] += 1
    row_sums = trans.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums == 0, 1, row_sums)
    prob = trans / row_sums

    labels = [["Even→Even", "Even→Odd"], ["Odd→Even", "Odd→Odd"]]
    cmap = LinearSegmentedColormap.from_list("prob", ["#ffffff", "#2c3e50"], N=256)
    im = ax.imshow(prob, cmap=cmap, vmin=0, vmax=1)
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(["Next Even", "Next Odd"])
    ax.set_yticklabels(["Current Even", "Current Odd"])
    for i in range(2):
        for j in range(2):
            ax.text(
                j,
                i,
                f"{prob[i, j]:.3f}\n({trans[i, j]})",
                ha="center",
                va="center",
                fontsize=11,
                color="white" if prob[i, j] > 0.5 else "black",
            )
    ax.set_title("Transition Probabilities (counts)")


def plot_run_lengths(parity, ax):
    runs = []
    current = parity[0]
    length = 1
    for p in parity[1:]:
        if p == current:
            length += 1
        else:
            runs.append((current, length))
            current = p
            length = 1
    runs.append((current, length))

    odd_runs = [r[1] for r in runs if r[0] == 1]
    even_runs = [r[1] for r in runs if r[0] == 0]

    max_run = max(max(odd_runs) if odd_runs else 0, max(even_runs) if even_runs else 0)
    bins = range(1, max_run + 2)

    if odd_runs:
        ax.hist(
            odd_runs,
            bins=bins,
            alpha=0.7,
            color="#e74c3c",
            label=f"Odd (mean={np.mean(odd_runs):.2f})",
            align="left",
        )
    if even_runs:
        ax.hist(
            even_runs,
            bins=bins,
            alpha=0.7,
            color="#3498db",
            label=f"Even (mean={np.mean(even_runs):.2f})",
            align="left",
        )
    ax.set_xlabel("Run Length")
    ax.set_ylabel("Frequency")
    ax.set_title("Run-Length Distribution")
    ax.legend()


def plot_value_trace(values, ax, max_display=200):
    data = values[:max_display]
    colors = ["#e74c3c" if v % 2 else "#3498db" for v in data]
    ax.scatter(range(len(data)), data, c=colors, s=8, alpha=0.6, edgecolor="none")
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Value")
    ax.set_title(f"Raw Values (first {len(data)}) — red=odd, blue=even")


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 675248
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 500

    values, parity = generate_sequence(seed, count)

    n_odds = sum(parity)
    n_evens = count - n_odds
    total_zeros = parity.count(0)
    total_ones = parity.count(1)

    print(f"Seed: {seed}")
    print(f"Sequence length: {count}")
    print(f"  Odds:  {n_odds} ({n_odds / count * 100:.1f}%)")
    print(f"  Evens: {n_evens} ({n_evens / count * 100:.1f}%)")
    print(
        f"  Odd/Even ratio: {n_odds / n_evens:.3f}" if n_evens else "  All odd values!"
    )

    trans = np.zeros((2, 2), dtype=int)
    for i in range(len(parity) - 1):
        trans[parity[i], parity[i + 1]] += 1
    print("\nTransition counts:")
    print(f"  Even→Even: {trans[0, 0]:4d}   Even→Odd: {trans[0, 1]:4d}")
    print(f"  Odd→Even:  {trans[1, 0]:4d}   Odd→Odd:  {trans[1, 1]:4d}")

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f"Middle Square PRNG — Seed: {seed}", fontsize=14)

    plot_parity_bars(parity, axes[0, 0])
    plot_transition_matrix(parity, axes[0, 1])
    plot_run_lengths(parity, axes[1, 0])
    plot_value_trace(values, axes[1, 1])

    plt.tight_layout()

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"middlesquare_seed{seed}.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"\nSaved plot to {out_path}")


if __name__ == "__main__":
    main()
