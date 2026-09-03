"""
SecuriCopilot -- Statistical significance testing
Chi-square tests of independence + Cramer's V effect size, run on:
1. Full 504-response dataset: Accuracy x Condition, Accuracy x Model,
   Abstention x Condition, Abstention x Model
2. 45-item human-reviewed sample: Grounding verdict x Condition,
   Grounding verdict x Model
"""

import json
import numpy as np
from scipy.stats import chi2_contingency

SCORED_FILE = "scored_results.json"
GROUNDING_FILE = "grounding_stats.json"


def cramers_v(chi2, n, table_shape):
    """Cramer's V effect size, same measure used in the UrduSafeBench paper."""
    r, k = table_shape
    return np.sqrt(chi2 / (n * (min(r - 1, k - 1))))


def run_chi_square(table, label, row_labels, col_labels):
    table = np.array(table)
    chi2, p, dof, expected = chi2_contingency(table)
    n = table.sum()
    v = cramers_v(chi2, n, table.shape)

    print(f"\n{label}")
    print(f"  chi2 = {chi2:.2f}, df = {dof}, p = {p:.4g}, Cramer's V = {v:.3f}, N = {n}")

    min_expected = expected.min()
    if min_expected < 5:
        print(f"  CAUTION: smallest expected cell count is {min_expected:.1f} "
              f"(below 5) -- chi-square approximation may be unreliable here.")

    print(f"  Rows: {row_labels}")
    print(f"  Cols: {col_labels}")
    print(f"  Observed table:\n{table}")
    return chi2, p, v


if __name__ == "__main__":
    with open(SCORED_FILE, "r") as f:
        scored = json.load(f)

    conditions = ["static_evidence", "dynamic_evidence", "combined_evidence"]
    models = sorted({s["model"] for s in scored})

    print("=" * 70)
    print("PART 1: FULL DATASET (N=504) -- Accuracy and Abstention")
    print("=" * 70)

    # --- Accuracy x Condition ---
    acc_by_condition = []
    for condition in conditions:
        subset = [s for s in scored if s["condition"] == condition]
        correct = sum(1 for s in subset if s["correct"])
        not_correct = len(subset) - correct
        acc_by_condition.append([correct, not_correct])

    run_chi_square(acc_by_condition, "Accuracy x Condition",
                    conditions, ["Correct", "Not Correct"])

    # --- Accuracy x Model ---
    acc_by_model = []
    for model in models:
        subset = [s for s in scored if s["model"] == model]
        correct = sum(1 for s in subset if s["correct"])
        not_correct = len(subset) - correct
        acc_by_model.append([correct, not_correct])

    run_chi_square(acc_by_model, "Accuracy x Model",
                    models, ["Correct", "Not Correct"])

    # --- Abstention x Condition ---
    abstain_by_condition = []
    for condition in conditions:
        subset = [s for s in scored if s["condition"] == condition]
        abstained = sum(1 for s in subset if s["abstained"])
        not_abstained = len(subset) - abstained
        abstain_by_condition.append([abstained, not_abstained])

    run_chi_square(abstain_by_condition, "Abstention x Condition",
                    conditions, ["Abstained", "Not Abstained"])

    # --- Abstention x Model ---
    abstain_by_model = []
    for model in models:
        subset = [s for s in scored if s["model"] == model]
        abstained = sum(1 for s in subset if s["abstained"])
        not_abstained = len(subset) - abstained
        abstain_by_model.append([abstained, not_abstained])

    run_chi_square(abstain_by_model, "Abstention x Model",
                    models, ["Abstained", "Not Abstained"])

    # --- Part 2: Grounding sample (N=45) ---
    print("\n\n" + "=" * 70)
    print("PART 2: HUMAN-REVIEWED SAMPLE (N=45) -- Grounding Verdict")
    print("=" * 70)

    with open(GROUNDING_FILE, "r") as f:
        grounding = json.load(f)

    g_conditions = sorted({g["condition"] for g in grounding})
    g_models = sorted({g["model"] for g in grounding})

    # --- Grounded/Unsupported x Condition ---
    ground_by_condition = []
    for condition in g_conditions:
        subset = [g for g in grounding if g["condition"] == condition]
        grounded = sum(1 for g in subset if g["verdict"] == "GROUNDED")
        unsupported = len(subset) - grounded  # PARTIAL + FABRICATED
        ground_by_condition.append([grounded, unsupported])

    run_chi_square(ground_by_condition, "Grounding x Condition (small sample -- caution advised)",
                    g_conditions, ["Grounded", "Unsupported"])

    # --- Grounded/Unsupported x Model ---
    ground_by_model = []
    for model in g_models:
        subset = [g for g in grounding if g["model"] == model]
        grounded = sum(1 for g in subset if g["verdict"] == "GROUNDED")
        unsupported = len(subset) - grounded
        ground_by_model.append([grounded, unsupported])

    run_chi_square(ground_by_model, "Grounding x Model (small sample -- caution advised)",
                    g_models, ["Grounded", "Unsupported"])

    print("\n" + "=" * 70)
    print("Done. All tests reported above.")
    print("=" * 70)