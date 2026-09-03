"""
SecuriCopilot -- Inspect one HA report's structure
"""

import json

with open("dataset.json", "r") as f:
    dataset = json.load(f)

sample = dataset[0]
print(f"Sample family: {sample['family_label']}")
print(f"Top-level keys in ha_report:\n")
for key in sample["ha_report"].keys():
    value = sample["ha_report"][key]
    value_preview = str(value)[:100]
    print(f"  {key}: {value_preview}")