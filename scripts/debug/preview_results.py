"""
SecuriCopilot -- Preview actual model responses from the test run
"""

import json

with open("evaluation_results.json", "r") as f:
    results = json.load(f)

# Show one full example per model, for the same sample/condition, to compare
target_sha = results[0]["sha256_hash"]
target_condition = "combined_evidence"

for r in results:
    if r["sha256_hash"] == target_sha and r["condition"] == target_condition:
        print("=" * 60)
        print(f"MODEL: {r['model']}")
        print(f"TRUE FAMILY: {r['true_family']}")
        print("=" * 60)
        if "raw_response" in r["response"]:
            print(r["response"]["raw_response"])
        else:
            print(f"ERROR: {r['response']}")
        print()