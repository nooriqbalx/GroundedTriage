"""
taxonomy_coding.py

GroundedTriage extension - Phase 1.3: Failure-mode taxonomy (descriptive).

Walks you through each of the 45 reviewed responses one at a time, shows
the justification text, and lets you assign one of three failure-mode
categories (only for PARTIAL/GROUNDED-with-issues cases - fully GROUNDED
cases get auto-tagged as N/A since there's no failure to categorize).

Categories (drafted from your actual PARTIAL justifications):
  1 = signature_misattribution   - real static artifact (imphash, file type)
                                    treated as definitive proof of a specific
                                    family without behavioral confirmation
  2 = generic_technique_fingerprint - real but common ATT&CK techniques/behaviors
                                    written as if uniquely diagnostic of one family
  3 = compound_narrative         - several individually generic real observations
                                    strung into a specific attribution that no
                                    single piece (or their combination) establishes
  0 = other / doesn't fit        - use sparingly, note why in the comment prompt
  s = skip for now (comes back at the end)

Progress is saved after every response, so you can stop and resume anytime -
just re-run the script and it picks up where you left off.

Run:
    python3 taxonomy_coding.py

Requires: no extra installs beyond the standard library.
"""

import json
from pathlib import Path

SAMPLE_PATH = Path("data/grounding_sample.json")   # 45 items, has justification text
STATS_PATH = Path("data/grounding_stats.json")     # 45 items, has verdict (GROUNDED/PARTIAL)
OUTPUT_PATH = Path("data/failure_mode_taxonomy.json")

CATEGORIES = {
    "1": "signature_misattribution",
    "2": "generic_technique_fingerprint",
    "3": "compound_narrative",
    "0": "other",
}


def load_data():
    with open(SAMPLE_PATH) as f:
        sample = json.load(f)
    with open(STATS_PATH) as f:
        stats = json.load(f)
    if len(sample) != len(stats):
        raise ValueError("sample and stats files have different lengths - can't align by index")
    merged = []
    for s, st in zip(sample, stats):
        merged.append({
            "sha256_hash": s["sha256_hash"],
            "true_family": s["true_family"],
            "predicted_family": s["predicted_family"],
            "condition": s["condition"],
            "model": s["model"],
            "justification": s["justification"],
            "verdict": st["verdict"],  # GROUNDED or PARTIAL
        })
    return merged


def load_existing_codes():
    if OUTPUT_PATH.exists():
        with open(OUTPUT_PATH) as f:
            return json.load(f)
    return {}


def save_codes(codes):
    with open(OUTPUT_PATH, "w") as f:
        json.dump(codes, f, indent=2)


def item_key(item, idx):
    # stable key: index + hash, since hash alone could repeat across conditions
    return f"{idx}_{item['sha256_hash'][:12]}_{item['condition']}"


def print_menu():
    print("\n  Categories:")
    for k, v in CATEGORIES.items():
        print(f"    {k} = {v}")
    print("    s = skip for now")
    print("    q = save and quit")


def main():
    items = load_data()
    codes = load_existing_codes()

    print(f"Loaded {len(items)} reviewed responses.")
    print(f"Already coded: {sum(1 for k in codes if codes[k].get('category'))}")

    for idx, item in enumerate(items):
        key = item_key(item, idx)

        if item["verdict"] == "GROUNDED":
            # Fully grounded responses have no failure to categorize - auto-tag and skip display
            if key not in codes:
                codes[key] = {"category": "n/a_grounded", "note": ""}
                save_codes(codes)
            continue

        if key in codes and codes[key].get("category") and codes[key]["category"] != "SKIPPED":
            continue  # already coded, don't re-ask

        print("\n" + "=" * 70)
        print(f"Item {idx + 1}/{len(items)}  |  verdict: {item['verdict']}")
        print(f"model: {item['model']}  |  condition: {item['condition']}")
        print(f"true_family: {item['true_family']}  |  predicted_family: {item['predicted_family']}")
        print("-" * 70)
        print(item["justification"])
        print_menu()

        choice = input("\n  Your category: ").strip().lower()

        if choice == "q":
            save_codes(codes)
            print(f"\nSaved. Progress: {sum(1 for c in codes.values() if c['category'] not in ('SKIPPED',))}/{len(items)} coded.")
            print(f"Re-run the script anytime to continue.")
            return

        if choice == "s":
            codes[key] = {"category": "SKIPPED", "note": ""}
            save_codes(codes)
            continue

        if choice not in CATEGORIES:
            print("  Not a valid option - marking as skipped, you can fix it later in the JSON.")
            codes[key] = {"category": "SKIPPED", "note": ""}
            save_codes(codes)
            continue

        note = input("  Optional short note (why this category, or press enter to skip): ").strip()
        codes[key] = {
            "category": CATEGORIES[choice],
            "note": note,
            "true_family": item["true_family"],
            "predicted_family": item["predicted_family"],
            "condition": item["condition"],
            "model": item["model"],
        }
        save_codes(codes)

    save_codes(codes)
    print("\nAll items reviewed. Run summarize_taxonomy.py next to see the counts by condition.")


if __name__ == "__main__":
    main()