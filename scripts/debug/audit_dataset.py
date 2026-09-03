"""
SecuriCopilot -- Audit the dataset for samples with an ERROR state or
zero actual evidence (empty processes/network/signatures)
"""

import json

with open("dataset.json", "r") as f:
    dataset = json.load(f)

usable = []
unusable = []

for sample in dataset:
    report = sample["ha_full_report"]
    state = report.get("state")
    total_processes = report.get("total_processes", 0)
    total_network = report.get("total_network_connections", 0)
    total_signatures = report.get("total_signatures", 0)

    has_real_evidence = (
        state == "SUCCESS"
        and (total_processes > 0 or total_network > 0 or total_signatures > 0)
    )

    if has_real_evidence:
        usable.append(sample)
    else:
        unusable.append(sample)
        print(f"UNUSABLE: {sample['sha256_hash'][:16]}... "
              f"({sample['family_label']}) -- state={state}, "
              f"processes={total_processes}, network={total_network}, "
              f"signatures={total_signatures}")

print("\n" + "=" * 60)
print(f"Usable (real evidence): {len(usable)}")
print(f"Unusable (empty/errored): {len(unusable)}")
print("\nUsable per-family breakdown:")
family_counts = {}
for s in usable:
    fam = s["family_label"]
    family_counts[fam] = family_counts.get(fam, 0) + 1
for fam, count in sorted(family_counts.items(), key=lambda x: -x[1]):
    print(f"  {fam}: {count}")
print("=" * 60)