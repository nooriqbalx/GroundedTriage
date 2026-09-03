"""
SecuriCopilot -- One-time dataset rebalancer
Trims any family that exceeds PER_FAMILY_CAP down to that cap, keeping
the dataset balanced before we move to evaluation.
"""

import json

DATASET_FILE = "dataset.json"
PER_FAMILY_CAP = 12

with open(DATASET_FILE, "r") as f:
    dataset = json.load(f)

family_counts = {}
trimmed_dataset = []

for entry in dataset:
    fam = entry["family_label"]
    family_counts[fam] = family_counts.get(fam, 0)
    if family_counts[fam] < PER_FAMILY_CAP:
        trimmed_dataset.append(entry)
        family_counts[fam] += 1

with open(DATASET_FILE, "w") as f:
    json.dump(trimmed_dataset, f, indent=2)

print(f"Trimmed dataset from {len(dataset)} to {len(trimmed_dataset)} samples.")
print("Final per-family breakdown:")
for fam, count in sorted(family_counts.items(), key=lambda x: -x[1]):
    print(f"  {fam}: {count}")