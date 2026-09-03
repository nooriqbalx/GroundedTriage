"""
SecuriCopilot -- Inspect a REAL successful report's structure to plan
the static/dynamic evidence split properly
"""

import json

with open("dataset.json", "r") as f:
    dataset = json.load(f)

sample = dataset[0]
report = sample["ha_full_report"]

print(f"Sample family: {sample['family_label']}")
print(f"State: {report.get('state')}\n")
print("Full structpython3 inspect_real_structure.pyure:\n")

for key in report.keys():
    value = report[key]
    if isinstance(value, list):
        print(f"  {key}: (list, {len(value)} items)")
        if len(value) > 0:
            print(f"      first item preview: {str(value[0])[:200]}")
    elif isinstance(value, dict):
        print(f"  {key}: (dict, keys: {list(value.keys())[:10]})")
    else:
        print(f"  {key}: {str(value)[:150]}")