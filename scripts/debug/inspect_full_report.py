"""
SecuriCopilot -- Fetch and inspect a FULL Hybrid Analysis report
(not just the overview) for one sample, to see real static+dynamic fields.
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
HYBRID_ANALYSIS_KEY = os.getenv("HYBRID_ANALYSIS_API_KEY")

with open("dataset.json", "r") as f:
    dataset = json.load(f)

sample = dataset[0]
sha256 = sample["sha256_hash"]
print(f"Sample family: {sample['family_label']}")
print(f"SHA256: {sha256}\n")

headers = {
    "api-key": HYBRID_ANALYSIS_KEY,
    "user-agent": "Falcon Sandbox",
}

# Step 1: search by hash to get the specific job id (includes environment info)
print("Step 1: searching for job id...")
search_url = "https://www.hybrid-analysis.com/api/v2/search/hash"
resp = requests.post(search_url, headers=headers, data={"hash": sha256}, timeout=30)
resp.raise_for_status()
results = resp.json()

if not results:
    print("No detailed job found for this hash via search/hash.")
else:
    job = results[0]
    job_id = job.get("job_id") or job.get("sha256")
    print(f"Found job id: {job_id}")
    print(f"Top-level keys in search result:\n")
    for key in job.keys():
        value_preview = str(job[key])[:100]
        print(f"  {key}: {value_preview}")

    # Step 2: fetch the full detailed report using that job id
    print(f"\nStep 2: fetching full report for job id {job_id}...")
    report_url = f"https://www.hybrid-analysis.com/api/v2/report/{job_id}/summary"
    resp2 = requests.get(report_url, headers=headers, timeout=30)
    print(f"Status: {resp2.status_code}")
    if resp2.status_code == 200:
        full_report = resp2.json()
        print(f"\nTop-level keys in FULL report:\n")
        for key in full_report.keys():
            value_preview = str(full_report[key])[:100]
            print(f"  {key}: {value_preview}")
    else:
        print(f"Response body: {resp2.text[:500]}")