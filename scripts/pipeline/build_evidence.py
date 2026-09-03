"""
SecuriCopilot -- Evidence extractor
Builds static-only, dynamic-only, and combined evidence bundles for each
sample, deliberately excluding any field that would leak the ground-truth
verdict or family (vx_family, av_detect, threat_score, verdict, tags).
"""

import json

INPUT_FILE = "dataset.json"
OUTPUT_FILE = "evidence_bundles.json"


def extract_static_evidence(report):
    lines = []
    lines.append(f"File type: {report.get('type', 'unknown')}")
    lines.append(f"Submitted filename: {report.get('submit_name', 'unknown')}")
    lines.append(f"File size: {report.get('size', 'unknown')} bytes")

    if report.get("imphash"):
        lines.append(f"Import hash (imphash): {report['imphash']}")
    if report.get("entrypoint"):
        lines.append(f"Entry point: {report['entrypoint']} "
                      f"(section: {report.get('entrypoint_section', 'unknown')})")
    if report.get("image_base"):
        lines.append(f"Image base: {report['image_base']}")
    if report.get("subsystem"):
        lines.append(f"Subsystem: {report['subsystem']}")

    characteristics = report.get("image_file_characteristics", [])
    if characteristics:
        lines.append(f"Image file characteristics: {', '.join(characteristics)}")

    dll_chars = report.get("dll_characteristics", [])
    if dll_chars:
        lines.append(f"DLL characteristics: {', '.join(dll_chars)}")

    certs = report.get("certificates", [])
    if certs:
        for cert in certs[:3]:  # cap to avoid huge prompts
            lines.append(f"Code signing certificate: owner={cert.get('owner', 'unknown')}, "
                          f"issuer={cert.get('issuer', 'unknown')}")

    return "\n".join(lines)


def extract_dynamic_evidence(report):
    lines = []

    processes = report.get("processes", [])
    if processes:
        lines.append(f"Processes observed ({len(processes)} total):")
        for p in processes[:10]:  # cap for prompt length
            lines.append(f"  - {p.get('name', 'unknown')} "
                          f"(path: {p.get('normalized_path', 'unknown')}, "
                          f"command line: {p.get('command_line', 'none')})")

    domains = report.get("domains", [])
    if domains:
        lines.append(f"Domains contacted: {', '.join(domains[:10])}")

    hosts = report.get("hosts", [])
    if hosts:
        lines.append(f"IP addresses contacted: {', '.join(hosts[:10])}")

    net_count = report.get("total_network_connections", 0)
    lines.append(f"Total network connections: {net_count}")

    signatures = report.get("signatures", [])
    if signatures:
        lines.append(f"\nBehavioral signatures observed ({len(signatures)} total):")
        for sig in signatures[:15]:  # cap for prompt length
            lines.append(f"  - [{sig.get('threat_level_human', 'unknown')}] "
                          f"{sig.get('category', 'unknown')}: {sig.get('name', 'unknown')}")

    attacks = report.get("mitre_attcks", [])
    if attacks:
        lines.append(f"\nMITRE ATT&CK techniques observed ({len(attacks)} total):")
        seen = set()
        for a in attacks:
            key = a.get("attck_id")
            if key and key not in seen:
                seen.add(key)
                lines.append(f"  - {a.get('attck_id')}: {a.get('technique', 'unknown')} "
                              f"(tactic: {a.get('tactic', 'unknown')})")
            if len(seen) >= 15:  # cap for prompt length
                break

    return "\n".join(lines)


if __name__ == "__main__":
    with open(INPUT_FILE, "r") as f:
        dataset = json.load(f)

    bundles = []
    for sample in dataset:
        report = sample["ha_full_report"]
        static_ev = extract_static_evidence(report)
        dynamic_ev = extract_dynamic_evidence(report)
        combined_ev = static_ev + "\n\n--- DYNAMIC BEHAVIOR ---\n\n" + dynamic_ev

        bundles.append({
            "sha256_hash": sample["sha256_hash"],
            "family_label": sample["family_label"],
            "static_evidence": static_ev,
            "dynamic_evidence": dynamic_ev,
            "combined_evidence": combined_ev,
        })

    with open(OUTPUT_FILE, "w") as f:
        json.dump(bundles, f, indent=2)

    print(f"Built evidence bundles for {len(bundles)} samples.")
    print(f"Saved to {OUTPUT_FILE}\n")

    # Show one example so we can sanity-check it looks right
    example = bundles[0]
    print("=" * 60)
    print(f"EXAMPLE -- family: {example['family_label']}")
    print("=" * 60)
    print("\n--- STATIC EVIDENCE ---")
    print(example["static_evidence"])
    print("\n--- DYNAMIC EVIDENCE ---")
    print(example["dynamic_evidence"][:1000])  # trimmed for display
    print("=" * 60)