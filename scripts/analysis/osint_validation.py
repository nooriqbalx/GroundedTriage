"""
osint_validation.py (v2)

GroundedTriage extension - Phase 1.5: OSINT validation.

Checks the 15 checkable misattribution claims (signature_misattribution +
compound_narrative categories) against MalwareBazaar's public API: does the
cited artifact (imphash or contacted domain) actually have any independent
association with the model's PREDICTED family, per MalwareBazaar's own
tagging? This is deliberately independent of your human grounding judgment -
it's an external, falsifiable check.

Loads MALWAREBAZAAR_API_KEY from .env, consistent with the rest of the
project's scripts (build_dataset.py, run_evaluation.py, etc.).

Run:
    python3 osint_validation.py
"""

import json
import time
import re
import os
from pathlib import Path
from collections import Counter

import requests
from dotenv import load_dotenv

load_dotenv()

TAXONOMY_PATH = Path("data/failure_mode_taxonomy.json")
SAMPLE_PATH = Path("data/grounding_sample.json")
OUTPUT_PATH = Path("data/osint_validation_results.json")

MALWAREBAZAAR_API = "https://mb-api.abuse.ch/api/v1/"
CHECKABLE_CATEGORIES = {"signature_misattribution", "compound_narrative"}

AUTH_KEY = os.getenv("MALWAREBAZAAR_API_KEY", "")


def load_taxonomy_and_sample():
    with open(TAXONOMY_PATH) as f:
        taxonomy = json.load(f)
    with open(SAMPLE_PATH) as f:
        sample = json.load(f)
    return taxonomy, sample


def query_imphash(imphash):
    if not AUTH_KEY:
        print("    [ERROR: no key found - check MALWAREBAZAAR_API_KEY in .env]")
        return None
    try:
        resp = requests.post(
            MALWAREBAZAAR_API,
            headers={"Auth-Key": AUTH_KEY},
            data={"query": "get_imphash", "imphash": imphash},
            timeout=15,
        )
        data = resp.json()
        status = data.get("query_status")
        if status == "no_results":
            return []
        if status != "ok":
            print(f"    [API returned status: {status} - NOT the same as 'no results', treating as error]")
            return None
        families = set()
        for entry in data.get("data", []):
            sig = entry.get("signature")
            if sig:
                families.add(sig)
        return list(families)
    except Exception as e:
        print(f"    [error querying imphash {imphash}: {e}]")
        return None


def manual_review_prompt(entry):
    print("\n  MANUAL CHECK NEEDED (domain/cert-based claim, not imphash):")
    print(f"    True family: {entry.get('true_family')}  Predicted: {entry.get('predicted_family')}")
    print(f"    Note: {entry.get('note')}")
    print("    -> Search the cited domain/cert on VirusTotal or MalwareBazaar's web UI.")
    print("    -> Does it show ANY independent association with the predicted family?")
    return input("    Independently supported? (y/n/unclear): ").strip().lower()


def find_real_imphash(justification):
    for match in re.finditer(r"\b[a-f0-9]{32}\b", justification.lower()):
        start, end = match.span()
        window_after = justification[end:end + 6].lower()
        window_before = justification[max(0, start - 20):start].lower()
        if window_after.startswith((".exe", ".dll")):
            continue
        if "filename" in window_before or "named" in window_before:
            continue
        return match.group(0)
    return None


def has_domain_or_cert_claim(justification):
    domain_pattern = re.search(r"\b[a-z0-9-]+\.(com|io|pub|me|net|org)\b", justification.lower())
    cert_pattern = re.search(r"(certificate|signed by|signing)", justification.lower())
    return bool(domain_pattern or cert_pattern)


def main():
    if not AUTH_KEY:
        print("WARNING: MALWAREBAZAAR_API_KEY not found in .env.")
        print("Add it to your .env file as: MALWAREBAZAAR_API_KEY=your-key-here")
        return

    taxonomy, sample = load_taxonomy_and_sample()

    sample_lookup = {}
    for i, s in enumerate(sample):
        key_prefix = f"{i}_{s['sha256_hash'][:12]}_{s['condition']}"
        sample_lookup[key_prefix] = s

    results = {}
    if OUTPUT_PATH.exists():
        with open(OUTPUT_PATH) as f:
            results = json.load(f)

    checkable_items = {
        k: v for k, v in taxonomy.items()
        if v.get("category") in CHECKABLE_CATEGORIES
    }
    print(f"Found {len(checkable_items)} checkable claims.\n")

    for key, entry in checkable_items.items():
        if key in results:
            continue

        full_item = sample_lookup.get(key)
        justification = full_item["justification"] if full_item else entry.get("note", "")
        predicted = entry.get("predicted_family")

        print("=" * 70)
        print(f"[{key}] True: {entry.get('true_family')} -> Predicted: {predicted}")
        print(f"Category: {entry.get('category')}")

        imphash = find_real_imphash(justification)

        if imphash:
            print(f"  Found imphash: {imphash}")
            print("  Querying MalwareBazaar (authenticated)...")
            families = query_imphash(imphash)
            time.sleep(1)

            if families is None:
                verdict = "api_error"
            elif not families:
                verdict = "no_independent_support"
                print(f"  -> No families found for this imphash. No independent support for '{predicted}'.")
            elif predicted.lower() in [f.lower() for f in families]:
                verdict = "independently_supported"
                print(f"  -> Confirmed: '{predicted}' associated with this imphash.")
            else:
                verdict = "contradicted"
                print(f"  -> Contradicted: imphash associated with {families}, not '{predicted}'.")

            results[key] = {
                "true_family": entry.get("true_family"), "predicted_family": predicted,
                "category": entry.get("category"), "check_type": "imphash",
                "imphash": imphash, "mb_families_found": families, "verdict": verdict,
            }
        elif has_domain_or_cert_claim(justification):
            manual_result = manual_review_prompt(entry)
            results[key] = {
                "true_family": entry.get("true_family"), "predicted_family": predicted,
                "category": entry.get("category"), "check_type": "manual_domain_or_cert",
                "verdict": manual_result,
            }
        else:
            print("  No checkable artifact (no imphash, no domain, no cert) - skipping.")
            results[key] = {
                "true_family": entry.get("true_family"), "predicted_family": predicted,
                "category": entry.get("category"), "check_type": "none",
                "verdict": "no_checkable_artifact",
            }

        with open(OUTPUT_PATH, "w") as f:
            json.dump(results, f, indent=2)

    print("\n" + "=" * 70)
    print("OSINT VALIDATION SUMMARY")
    print("=" * 70)
    verdicts = Counter(r["verdict"] for r in results.values())
    for v, n in verdicts.items():
        print(f"  {v}: {n}")

    checkable_total = sum(n for v, n in verdicts.items() if v != "no_checkable_artifact")
    supported = verdicts.get("independently_supported", 0) + verdicts.get("y", 0)
    if checkable_total:
        print(f"\n  Precision estimate (excluding non-checkable items): "
              f"{supported}/{checkable_total} ({supported/checkable_total:.1%})")
    print(f"\n  Results saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()