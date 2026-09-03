"""
SecuriCopilot -- Grounding/hallucination check sample builder
Selects a stratified sample across all condition x model cells, pairs each
justification with its real underlying evidence, and outputs a markdown
review sheet for manual human validation (same spirit as UrduSafeBench's
Table 3 human-judge validation).
"""

import json
import random

SCORED_FILE = "scored_results.json"
EVIDENCE_FILE = "evidence_bundles.json"
OUTPUT_MD = "grounding_review.md"
OUTPUT_JSON = "grounding_sample.json"

SAMPLES_PER_CELL = 5  # 5 x 3 conditions x 3 models = 45 total to review
RANDOM_SEED = 42  # fixed seed so this is reproducible if we rerun it

random.seed(RANDOM_SEED)

with open(SCORED_FILE, "r") as f:
    scored = json.load(f)

with open(EVIDENCE_FILE, "r") as f:
    evidence_bundles = json.load(f)

evidence_by_hash = {b["sha256_hash"]: b for b in evidence_bundles}

CONDITIONS = ["static_evidence", "dynamic_evidence", "combined_evidence"]
MODELS = sorted({s["model"] for s in scored})

sample = []
for condition in CONDITIONS:
    for model in MODELS:
        cell_results = [
            s for s in scored
            if s["condition"] == condition and s["model"] == model
            and s["parse_ok"] and s.get("justification")
        ]
        chosen = random.sample(cell_results, min(SAMPLES_PER_CELL, len(cell_results)))
        sample.extend(chosen)

print(f"Selected {len(sample)} results for manual grounding review "
      f"({SAMPLES_PER_CELL} per cell x {len(CONDITIONS)} conditions x {len(MODELS)} models).")

# Save the raw sample for later programmatic scoring once verdicts are filled in
with open(OUTPUT_JSON, "w") as f:
    json.dump(sample, f, indent=2)

# Build the human-readable review sheet
lines = []
lines.append("# Grounding / Hallucination Review Sheet\n")
lines.append(f"Total items to review: {len(sample)}\n")
lines.append("For each item: read the EVIDENCE, then read the model's JUSTIFICATION. ")
lines.append("Fill in VERDICT with one of: GROUNDED (claims trace to real evidence), ")
lines.append("FABRICATED (claims cite things not actually in the evidence), or ")
lines.append("PARTIAL (mix of both). Add a one-line NOTE if useful.\n")
lines.append("---\n")

for i, item in enumerate(sample, 1):
    bundle = evidence_by_hash.get(item["sha256_hash"], {})
    evidence_text = bundle.get(item["condition"], "(evidence not found)")

    lines.append(f"## Item {i}")
    lines.append(f"**Model:** {item['model']}  ")
    lines.append(f"**Condition:** {item['condition']}  ")
    lines.append(f"**True family:** {item['true_family']}  ")
    lines.append(f"**Model's guess:** {item['predicted_family']}  ")
    lines.append(f"**Marked correct:** {item['correct']}\n")

    lines.append("**EVIDENCE SHOWN TO MODEL:**")
    lines.append("```")
    lines.append(evidence_text[:1500])  # trimmed for readability
    lines.append("```\n")

    lines.append("**MODEL'S JUSTIFICATION:**")
    lines.append("```")
    lines.append(item["justification"])
    lines.append("```\n")

    lines.append("**VERDICT:** _______________  (GROUNDED / FABRICATED / PARTIAL)")
    lines.append("**NOTE:** _______________________________________________\n")
    lines.append("---\n")

with open(OUTPUT_MD, "w") as f:
    f.write("\n".join(lines))

print(f"Review sheet written to {OUTPUT_MD}")
print(f"Raw sample data saved to {OUTPUT_JSON}")