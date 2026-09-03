"""
SecuriCopilot -- Check how many of our confirmed samples actually have
real behavioral reports (not just multiscan/verdict data)
"""

import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()
HYBRID_ANALYSIS_KEY = os.getenv("HYBRID_ANALYSIS_API_KEY")

headers = {
    "api-key": HYBRID_ANALYSIS_KEY,
    "user-agent": "Falcon Sandbox",
}

with open("dataset.json", "r") as f:
    dataset = json.load(f)

url = "https://www.hybrid-analysis.com/api/v2/search/hash"

has_real_report = 0
no_real_report = 0

for i, sample in enumerate(dataset):
    sha256 = sample["sha256_hash"]
    resp = requests.post(url, headers=headers, params={"hash": sha256}, timeout=30)
    time.sleep(1.2)

    if resp.status_code != 200:
        print(f"[{i+1}] {sha256[:16]}... -> ERROR {resp.status_code}")
        continue

    result = resp.json()
    reports = result.get("reports", [])

    if reports:
        has_real_report += 1
        print(f"[{i+1}] {sha256[:16]}... ({sample['family_label']}) -> "
              f"HAS real report ({len(reports)} job(s))")
    else:
        no_real_report += 1
        print(f"[{i+1}] {sha256[:16]}... ({sample['family_label']}) -> "
              f"no behavioral report, verdict-only")

print("\n" + "=" * 60)
print(f"Samples with real behavioral reports: {has_real_report}")
print(f"Samples with verdict-only data: {no_real_report}")
print("=" * 60)