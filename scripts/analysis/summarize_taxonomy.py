"""
summarize_taxonomy.py

GroundedTriage extension - Phase 1.3: Failure-mode taxonomy summary.

Reads data/failure_mode_taxonomy.json (produced by taxonomy_coding.py) and
produces the counts-by-condition table for the write-up, plus a breakdown
by model and a few illustrative examples per category pulled automatically
from your notes.

This treats the taxonomy as DESCRIPTIVE (counts + examples), consistent
with the Phase 1.1 power analysis finding that n=15/condition cannot
support a formally tested chi-square comparison across categories.

Run:
    python3 summarize_taxonomy.py
"""

import json
from pathlib import Path
from collections import Counter, defaultdict

TAXONOMY_PATH = Path("data/failure_mode_taxonomy.json")

CATEGORY_LABELS = {
    "signature_misattribution": "Signature/hash misattribution",
    "generic_technique_fingerprint": "Generic-technique-as-fingerprint",
    "compound_narrative": "Compound narrative construction",
    "other": "Other / hedged or malformed",
    "n/a_grounded": "N/A (fully grounded)",
}

CONDITION_ORDER = ["static_evidence", "dynamic_evidence", "combined_evidence"]


def load_taxonomy():
    with open(TAXONOMY_PATH) as f:
        return json.load(f)


def main():
    if not TAXONOMY_PATH.exists():
        print(f"ERROR: {TAXONOMY_PATH} not found. Run taxonomy_coding.py first.")
        return

    codes = load_taxonomy()

    # Filter out anything not actually coded (shouldn't be any, but just in case)
    coded = {k: v for k, v in codes.items() if v.get("category") and v["category"] != "SKIPPED"}
    print(f"Total coded items: {len(coded)} / {len(codes)}\n")

    # --- Table 1: counts by category overall ---
    print("=" * 70)
    print("TABLE 1: Failure-mode counts overall (descriptive - no p-values)")
    print("=" * 70)
    overall_counts = Counter(v["category"] for v in coded.values())
    for cat, label in CATEGORY_LABELS.items():
        n = overall_counts.get(cat, 0)
        print(f"  {label:38s}: {n}")
    print()

    # --- Table 2: counts by category x condition ---
    print("=" * 70)
    print("TABLE 2: Failure-mode counts by evidence condition")
    print("=" * 70)
    by_condition = defaultdict(Counter)
    for v in coded.values():
        cond = v.get("condition", "unknown")
        by_condition[cond][v["category"]] += 1

    header = f"{'Category':38s}" + "".join(f"{c.replace('_evidence',''):>10s}" for c in CONDITION_ORDER)
    print(header)
    for cat, label in CATEGORY_LABELS.items():
        row = f"{label:38s}"
        for cond in CONDITION_ORDER:
            row += f"{by_condition[cond].get(cat, 0):>10d}"
        print(row)
    print()

    # --- Table 3: counts by category x model ---
    print("=" * 70)
    print("TABLE 3: Failure-mode counts by model")
    print("=" * 70)
    by_model = defaultdict(Counter)
    for v in coded.values():
        model = v.get("model", "unknown")
        by_model[model][v["category"]] += 1

    models = sorted(by_model.keys())
    header = f"{'Category':38s}" + "".join(f"{m[-14:]:>16s}" for m in models)
    print(header)
    for cat, label in CATEGORY_LABELS.items():
        row = f"{label:38s}"
        for m in models:
            row += f"{by_model[m].get(cat, 0):>16d}"
        print(row)
    print()

    # --- Illustrative examples: pull 1-2 notes per category for the write-up ---
    print("=" * 70)
    print("ILLUSTRATIVE EXAMPLES (for write-up - pick 1-2 per category)")
    print("=" * 70)
    examples_by_cat = defaultdict(list)
    for k, v in coded.items():
        if v["category"] in ("n/a_grounded",):
            continue
        examples_by_cat[v["category"]].append((k, v))

    for cat, label in CATEGORY_LABELS.items():
        if cat == "n/a_grounded":
            continue
        print(f"\n--- {label} ---")
        for k, v in examples_by_cat.get(cat, [])[:2]:
            print(f"  [{k}] {v.get('true_family')} -> {v.get('predicted_family')} "
                  f"({v.get('condition')}, {v.get('model')})")
            print(f"  Note: {v.get('note', '')}")

    print("\nDone. Copy Tables 1-3 and chosen examples into the extended write-up.")


if __name__ == "__main__":
    main()