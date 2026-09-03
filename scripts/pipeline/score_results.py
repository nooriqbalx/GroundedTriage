"""
SecuriCopilot -- Scoring script
Parses each model's FAMILY/CONFIDENCE/JUSTIFICATION from its response,
compares FAMILY against ground truth, and aggregates accuracy by
condition (static/dynamic/combined) and by model.
"""

import json
import re
from collections import defaultdict

RESULTS_FILE = "evaluation_results.json"
SCORED_FILE = "scored_results.json"


def parse_response(text):
    """Extract FAMILY, CONFIDENCE, JUSTIFICATION from a model's final answer."""
    family_match = re.search(r"FAMILY:\s*(.+)", text)
    confidence_match = re.search(r"CONFIDENCE:\s*(low|medium|high)", text, re.IGNORECASE)
    justification_match = re.search(r"JUSTIFICATION:\s*(.+)", text, re.DOTALL)

    family = family_match.group(1).strip() if family_match else None
    confidence = confidence_match.group(1).lower() if confidence_match else None
    justification = justification_match.group(1).strip() if justification_match else None

    # Clean trailing markdown artifacts sometimes left by models
    if family:
        family = family.strip("*").strip()

    return family, confidence, justification


def is_correct(predicted_family, true_family):
    """Simple, honest matching: does the true family name appear in the
    model's stated guess (case-insensitive)? This deliberately does NOT
    try to be clever about aliases -- a stricter, more defensible choice
    for a first pass."""
    if not predicted_family:
        return False
    return true_family.lower() in predicted_family.lower()


def is_abstained(predicted_family):
    """Did the model explicitly decline to guess (say 'unknown' etc.)
    rather than commit to a wrong answer? Worth tracking separately."""
    if not predicted_family:
        return False
    abstain_markers = ["unknown", "insufficient", "unable to determine", "cannot confidently"]
    return any(marker in predicted_family.lower() for marker in abstain_markers)


if __name__ == "__main__":
    with open(RESULTS_FILE, "r") as f:
        results = json.load(f)

    scored = []
    parse_failures = 0

    for r in results:
        response = r["response"]
        if "error" in response:
            scored.append({**r, "predicted_family": None, "confidence": None,
                            "correct": False, "abstained": False, "parse_ok": False,
                            "note": "api_error"})
            continue

        text = response.get("final_answer") or response.get("raw_response", "")
        family, confidence, justification = parse_response(text)

        if family is None:
            parse_failures += 1
            scored.append({**r, "predicted_family": None, "confidence": None,
                            "correct": False, "abstained": False, "parse_ok": False,
                            "note": "parse_failure"})
            continue

        correct = is_correct(family, r["true_family"])
        abstained = is_abstained(family)

        scored.append({
            **r,
            "predicted_family": family,
            "confidence": confidence,
            "justification": justification,
            "correct": correct,
            "abstained": abstained,
            "parse_ok": True,
        })

    with open(SCORED_FILE, "w") as f:
        json.dump(scored, f, indent=2)

    print("=" * 70)
    print(f"Scored {len(scored)} results. Parse failures: {parse_failures}")
    print("=" * 70)

    # Accuracy by condition x model
    breakdown = defaultdict(lambda: {"correct": 0, "abstained": 0, "wrong": 0, "total": 0})

    for s in scored:
        key = (s["condition"], s["model"])
        breakdown[key]["total"] += 1
        if s["correct"]:
            breakdown[key]["correct"] += 1
        elif s["abstained"]:
            breakdown[key]["abstained"] += 1
        else:
            breakdown[key]["wrong"] += 1

    print(f"\n{'Condition':<20} {'Model':<25} {'Acc%':>7} {'Abstain%':>10} {'Wrong%':>8} {'N':>5}")
    print("-" * 80)
    for condition in ["static_evidence", "dynamic_evidence", "combined_evidence"]:
        for model in sorted({s["model"] for s in scored}):
            key = (condition, model)
            if key not in breakdown:
                continue
            d = breakdown[key]
            acc_pct = 100 * d["correct"] / d["total"]
            abstain_pct = 100 * d["abstained"] / d["total"]
            wrong_pct = 100 * d["wrong"] / d["total"]
            print(f"{condition:<20} {model:<25} {acc_pct:>6.1f}% {abstain_pct:>9.1f}% "
                  f"{wrong_pct:>7.1f}% {d['total']:>5}")

    # Overall accuracy by condition (pooled across models) -- the core research question
    print("\n" + "=" * 70)
    print("CORE RESULT: Accuracy by evidence condition (pooled across all models)")
    print("=" * 70)
    condition_totals = defaultdict(lambda: {"correct": 0, "total": 0})
    for s in scored:
        condition_totals[s["condition"]]["total"] += 1
        if s["correct"]:
            condition_totals[s["condition"]]["correct"] += 1

    for condition in ["static_evidence", "dynamic_evidence", "combined_evidence"]:
        d = condition_totals[condition]
        acc = 100 * d["correct"] / d["total"]
        print(f"  {condition:<20}: {acc:.1f}% accuracy ({d['correct']}/{d['total']})")