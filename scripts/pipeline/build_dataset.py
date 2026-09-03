"""
SecuriCopilot -- Dataset builder v4
Filters for REAL usable evidence (state=SUCCESS AND non-zero processes/
network/signatures), not just "a report exists." Mirai dropped -- its
non-Windows architecture is incompatible with this sandbox. Resumes from
existing usable samples and backfills to target.
"""

import os
import time
import json
import requests
from dotenv import load_dotenv

load_dotenv()

MALWAREBAZAAR_KEY = os.getenv("MALWAREBAZAAR_API_KEY")
HYBRID_ANALYSIS_KEY = os.getenv("HYBRID_ANALYSIS_API_KEY")

TARGET_COUNT = 56           # 7 families x 8, since Mirai is dropped
OUTPUT_FILE = "dataset.json"
DELAY_BETWEEN_HA_CALLS = 1.2
REQUEST_TIMEOUT = 60
MAX_RETRIES = 3

TARGET_FAMILIES = [
    "Vidar", "njrat", "WannaCry", "NanoCore",
    "CoinMiner", "ConnectWise", "NetSupport", "AgentTesla",
]
PER_FAMILY_CAP = 8


def request_with_retry(method, url, **kwargs):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            kwargs.setdefault("timeout", REQUEST_TIMEOUT)
            return requests.request(method, url, **kwargs)
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            print(f"    (network issue, attempt {attempt}/{MAX_RETRIES}: {type(e).__name__})")
            if attempt == MAX_RETRIES:
                return None
            time.sleep(3 * attempt)
    return None


def fetch_candidates_for_family(family_name, limit=150):
    print(f"  Querying family: {family_name}...")
    url = "https://mb-api.abuse.ch/api/v1/"
    headers = {"Auth-Key": MALWAREBAZAAR_KEY}
    data = {"query": "get_siginfo", "signature": family_name, "limit": str(limit)}
    resp = request_with_retry("POST", url, headers=headers, data=data)

    if resp is None or resp.status_code != 200:
        print(f"    Failed to reach MalwareBazaar for {family_name}, skipping family.")
        return []

    result = resp.json()
    if result.get("query_status") != "ok":
        print(f"    (no results for {family_name}: {result.get('query_status')})")
        return []
    return result["data"]


def find_real_report_id(sha256_hash):
    headers = {"api-key": HYBRID_ANALYSIS_KEY, "user-agent": "Falcon Sandbox"}
    url = "https://www.hybrid-analysis.com/api/v2/search/hash"
    resp = request_with_retry("POST", url, headers=headers, params={"hash": sha256_hash})

    if resp is None or resp.status_code != 200:
        return None
    result = resp.json()
    reports = result.get("reports", [])
    if not reports:
        return None
    return reports[0].get("id")


def fetch_full_report(report_id):
    headers = {"api-key": HYBRID_ANALYSIS_KEY, "user-agent": "Falcon Sandbox"}
    url = f"https://www.hybrid-analysis.com/api/v2/report/{report_id}/summary"
    resp = request_with_retry("GET", url, headers=headers)

    if resp is None or resp.status_code != 200:
        return None
    return resp.json()


def has_real_evidence(report):
    """The key fix: check state AND actual non-zero evidence, not just existence."""
    state = report.get("state")
    total_processes = report.get("total_processes", 0)
    total_network = report.get("total_network_connections", 0)
    total_signatures = report.get("total_signatures", 0)
    return state == "SUCCESS" and (total_processes > 0 or total_network > 0 or total_signatures > 0)


def load_existing_dataset():
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            return json.load(f)
    return []


def save_dataset(dataset):
    with open(OUTPUT_FILE, "w") as f:
        json.dump(dataset, f, indent=2)


if __name__ == "__main__":
    print("=" * 60)
    print("SecuriCopilot -- building dataset (v4, real usable evidence only)")
    print("=" * 60)

    # Load existing dataset and keep ONLY the genuinely usable samples,
    # dropping Mirai and any error/empty ones.
    raw_dataset = load_existing_dataset()
    dataset = [
        s for s in raw_dataset
        if s["family_label"] != "Mirai" and has_real_evidence(s["ha_full_report"])
    ]
    already_have = {entry["sha256_hash"] for entry in dataset}
    family_counts = {}
    for entry in dataset:
        fam = entry["family_label"]
        family_counts[fam] = family_counts.get(fam, 0) + 1

    print(f"Kept {len(dataset)} genuinely usable samples from before "
          f"(dropped Mirai and any error/empty reports).\n")

    for family in TARGET_FAMILIES:
        if len(dataset) >= TARGET_COUNT:
            break
        if family_counts.get(family, 0) >= PER_FAMILY_CAP:
            print(f"Already have enough {family} samples, skipping.")
            continue

        candidates = fetch_candidates_for_family(family)

        for sample in candidates:
            if family_counts.get(family, 0) >= PER_FAMILY_CAP:
                break
            if len(dataset) >= TARGET_COUNT:
                break

            sha256 = sample["sha256_hash"]
            if sha256 in already_have:
                continue

            print(f"    Checking {sha256[:16]}...", end=" ")
            report_id = find_real_report_id(sha256)
            time.sleep(DELAY_BETWEEN_HA_CALLS)

            if report_id is None:
                print("-> no real report, skipping")
                continue

            full_report = fetch_full_report(report_id)
            time.sleep(DELAY_BETWEEN_HA_CALLS)

            if full_report is None:
                print("-> report id found but fetch failed, skipping")
                continue

            if not has_real_evidence(full_report):
                print(f"-> report exists but empty/errored "
                      f"(state={full_report.get('state')}), skipping")
                continue

            print("-> CONFIRMED with real, usable evidence, saving")
            dataset.append({
                "sha256_hash": sha256,
                "family_label": family,
                "file_type": sample.get("file_type"),
                "file_name": sample.get("file_name"),
                "report_id": report_id,
                "ha_full_report": full_report,
            })
            already_have.add(sha256)
            family_counts[family] = family_counts.get(family, 0) + 1
            save_dataset(dataset)
            print(f"    Progress: {len(dataset)}/{TARGET_COUNT} "
                  f"({family}: {family_counts[family]}/{PER_FAMILY_CAP})")

    print("\n" + "=" * 60)
    print(f"Done for this run. Dataset has {len(dataset)} samples with REAL usable evidence.")
    print("Per-family breakdown:")
    for fam, count in sorted(family_counts.items(), key=lambda x: -x[1]):
        print(f"  {fam}: {count}")
    if len(dataset) < TARGET_COUNT:
        print("\nDidn't hit target yet -- just rerun this script, it resumes automatically.")
    print("=" * 60)