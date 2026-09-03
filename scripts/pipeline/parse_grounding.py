"""
SecuriCopilot -- Parse the completed grounding review and compute
hallucination/fabrication statistics by model and by evidence condition.
"""

import re
import json
from collections import defaultdict

REVIEW_FILE = "grounding_review.md"  # make sure your completed file has this name
OUTPUT_FILE = "grounding_stats.json"

with open(REVIEW_FILE, "r", encoding="utf-8") as f:
    content = f.read()

# Split into individual items
items = content.split("## Item ")[1:]  # skip the header block before Item 1

parsed = []
for item in items:
    model_match = re.search(r"\*\*Model:\*\*\s*(.+?)\s{2,}", item)
    condition_match = re.search(r"\*\*Condition:\*\*\s*(.+?)\s{2,}", item)
    true_family_match = re.search(r"\*\*True family:\*\*\s*(.+?)\s{2,}", item)
    predicted_match = re.search(r"\*\*Model's guess:\*\*\s*(.+?)\s{2,}", item)
    correct_match = re.search(r"\*\*Marked correct:\*\*\s*(\w+)", item)
    verdict_match = re.search(r"\*\*VERDICT:\*\*\s*(\w+)", item)

    if not (model_match and condition_match and verdict_match):
        print(f"WARNING: couldn't fully parse an item, skipping. Snippet: {item[:100]}")
        continue

    parsed.append({
        "model": model_match.group(1).strip(),
        "condition": condition_match.group(1).strip(),
        "true_family": true_family_match.group(1).strip() if true_family_match else None,
        "predicted_family": predicted_match.group(1).strip() if predicted_match else None,
        "marked_correct": correct_match.group(1).strip() if correct_match else None,
        "verdict": verdict_match.group(1).strip().upper(),
    })

print(f"Parsed {len(parsed)} items out of 45 expected.\n")

with open(OUTPUT_FILE, "w") as f:
    json.dump(parsed, f, indent=2)

# --- Aggregate stats ---

def pct(part, whole):
    return 100 * part / whole if whole else 0.0

print("=" * 70)
print("OVERALL VERDICT DISTRIBUTION")
print("=" * 70)
overall = defaultdict(int)
for p in parsed:
    overall[p["verdict"]] += 1
for verdict in ["GROUNDED", "PARTIAL", "FABRICATED"]:
    count = overall.get(verdict, 0)
    print(f"  {verdict:<12}: {count:>3} ({pct(count, len(parsed)):.1f}%)")

print("\n" + "=" * 70)
print("VERDICT BY MODEL")
print("=" * 70)
by_model = defaultdict(lambda: defaultdict(int))
totals_by_model = defaultdict(int)
for p in parsed:
    by_model[p["model"]][p["verdict"]] += 1
    totals_by_model[p["model"]] += 1

for model in sorted(by_model.keys()):
    total = totals_by_model[model]
    print(f"\n  {model} (n={total})")
    for verdict in ["GROUNDED", "PARTIAL", "FABRICATED"]:
        count = by_model[model].get(verdict, 0)
        print(f"    {verdict:<12}: {count:>3} ({pct(count, total):.1f}%)")

print("\n" + "=" * 70)
print("VERDICT BY EVIDENCE CONDITION")
print("=" * 70)
by_condition = defaultdict(lambda: defaultdict(int))
totals_by_condition = defaultdict(int)
for p in parsed:
    by_condition[p["condition"]][p["verdict"]] += 1
    totals_by_condition[p["condition"]] += 1

for condition in ["static_evidence", "dynamic_evidence", "combined_evidence"]:
    total = totals_by_condition.get(condition, 0)
    if total == 0:
        continue
    print(f"\n  {condition} (n={total})")
    for verdict in ["GROUNDED", "PARTIAL", "FABRICATED"]:
        count = by_condition[condition].get(verdict, 0)
        print(f"    {verdict:<12}: {count:>3} ({pct(count, total):.1f}%)")

print("\n" + "=" * 70)
print("KEY STAT: 'Unsupported attribution' rate (PARTIAL + FABRICATED combined)")
print("This is your headline number -- how often a model's justification")
print("included at least one claim not backed by the shown evidence.")
print("=" * 70)
unsupported = overall.get("PARTIAL", 0) + overall.get("FABRICATED", 0)
print(f"\n  Overall: {unsupported}/{len(parsed)} ({pct(unsupported, len(parsed)):.1f}%)")

for model in sorted(by_model.keys()):
    total = totals_by_model[model]
    m_unsupported = by_model[model].get("PARTIAL", 0) + by_model[model].get("FABRICATED", 0)
    print(f"  {model}: {m_unsupported}/{total} ({pct(m_unsupported, total):.1f}%)")

print(f"\nRaw parsed data saved to {OUTPUT_FILE}")