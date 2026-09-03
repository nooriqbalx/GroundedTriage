"""
SecuriCopilot -- Inspect one full HA report's structure to plan the
static/dynamic evidence split
"""

import json

with open("dataset.json", "r") as f:
    dataset = json.load(f)

sample = dataset[0]
report = sample["ha_full_report"]

print(f"Sample family: {sample['family_label']}")
print(f"Top-level keys in ha_full_report:\n")
for key in report.keys():
    value = report[key]
    if isinstance(value, (dict, list)):
        preview = f"({type(value).__name__}, length {len(value)})"
    else:
        preview = str(value)[:80]
    print(f"  {key}: {preview}")