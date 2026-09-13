"""
generate_fig6.py

GroundedTriage extension - Figure 6: Failure-mode taxonomy by evidence condition.

Produces a grouped/stacked bar chart of Table 6 (condition x category counts),
matching the style of the existing fig1-fig5 outputs (same color conventions,
same output paths and formats).

Run:
    python3 generate_fig6.py

Requires: matplotlib (already in your environment)
"""

import json
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

# Match your existing figures' style - adjust if fig1-5 use a specific rcParams block
matplotlib.rcParams.update({
    "font.size": 11,
    "font.family": "serif",
    "axes.spines.top": False,
    "axes.spines.right": False,
})

CATEGORIES = [
    "Signature/hash\nmisattribution",
    "Generic-technique-\nas-fingerprint",
    "Compound narrative\nconstruction",
    "Other (hedged\nor malformed)",
    "Fully grounded",
]

CONDITIONS = ["Static", "Dynamic", "Combined"]

# Pulled directly from Table 6 in REPORT.md - keep in sync if taxonomy changes
DATA = {
    "Static":   [3, 0, 0, 1, 11],
    "Dynamic":  [2, 7, 3, 1, 2],
    "Combined": [3, 3, 4, 4, 1],
}

COLORS = ["#c44e52", "#dd8452", "#937860", "#8c8c8c", "#4c72b0"]


def make_grouped_bar():
    fig, ax = plt.subplots(figsize=(9, 5.5))

    x = np.arange(len(CONDITIONS))
    n_cats = len(CATEGORIES)
    bar_width = 0.8 / n_cats

    for i, cat in enumerate(CATEGORIES):
        values = [DATA[cond][i] for cond in CONDITIONS]
        offset = (i - n_cats / 2 + 0.5) * bar_width
        ax.bar(x + offset, values, bar_width, label=cat, color=COLORS[i], edgecolor="white", linewidth=0.5)

    ax.set_xticks(x)
    ax.set_xticklabels(CONDITIONS)
    ax.set_ylabel("Count (of 15 responses per condition)")
    ax.set_xlabel("Evidence Condition")
    ax.set_title("Failure-Mode Category by Evidence Condition (N = 45, descriptive)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize=9, frameon=False)
    ax.set_ylim(0, 13)

    plt.tight_layout()
    return fig


def make_stacked_bar():
    """Alternative view: stacked bars showing full composition per condition."""
    fig, ax = plt.subplots(figsize=(7, 5.5))

    x = np.arange(len(CONDITIONS))
    bottom = np.zeros(len(CONDITIONS))

    for i, cat in enumerate(CATEGORIES):
        values = np.array([DATA[cond][i] for cond in CONDITIONS])
        ax.bar(x, values, bottom=bottom, label=cat, color=COLORS[i], edgecolor="white", linewidth=0.5)
        bottom += values

    ax.set_xticks(x)
    ax.set_xticklabels(CONDITIONS)
    ax.set_ylabel("Count (of 15 responses per condition)")
    ax.set_xlabel("Evidence Condition")
    ax.set_title("Failure-Mode Composition by Evidence Condition (N = 45, descriptive)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=9, frameon=False)
    ax.set_ylim(0, 16)

    plt.tight_layout()
    return fig


def main():
    # Grouped bar is generally clearer for showing the condition-level shift
    # (the pattern you want to highlight: technique-fingerprint and compound
    # narrative both being ~0 under static, then rising). Stacked bar is saved
    # too as an alternative - pick whichever reads better once you see both.

    fig_grouped = make_grouped_bar()
    fig_grouped.savefig("figures/fig6_taxonomy.png", dpi=300, bbox_inches="tight")
    fig_grouped.savefig("figures/fig6_taxonomy.pdf", bbox_inches="tight")
    plt.close(fig_grouped)

    fig_stacked = make_stacked_bar()
    fig_stacked.savefig("figures/fig6_taxonomy_stacked.png", dpi=300, bbox_inches="tight")
    fig_stacked.savefig("figures/fig6_taxonomy_stacked.pdf", bbox_inches="tight")
    plt.close(fig_stacked)

    print("Saved:")
    print("  figures/fig6_taxonomy.png / .pdf (grouped bar - recommended)")
    print("  figures/fig6_taxonomy_stacked.png / .pdf (stacked bar - alternative)")
    print("\nOpen both and pick whichever communicates the condition-level shift more clearly.")
    print("Reference the chosen one in REPORT.md Section 5.4, after Table 6.")


if __name__ == "__main__":
    main()