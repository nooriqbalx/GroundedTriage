"""
SecuriCopilot -- Diagnostic: inspect actual wrong predictions
to check whether low accuracy is real or a matching bug
"""

import json

with open("scored_results.json", "r") as f:
    scored = json.load(f)

# Look specifically at WannaCry, since it should be highly distinctive
print("=" * 70)
print("WannaCry samples -- true_family vs predicted_family")
print("=" * 70)
count = 0
for s in scored:
    if s["true_family"] == "WannaCry" and count < 10:
        print(f"Model: {s['model']:<25} Condition: {s['condition']:<20} "
              f"Predicted: {s['predicted_family']!r:<40} Correct: {s['correct']}")
        count += 1

print("\n" + "=" * 70)
print("A few more wrong predictions across other families, for context")
print("=" * 70)
count = 0
for s in scored:
    if not s["correct"] and not s["abstained"] and s["parse_ok"] and count < 10:
        print(f"True: {s['true_family']:<15} Predicted: {s['predicted_family']!r:<40} "
              f"Model: {s['model']:<25} Condition: {s['condition']}")
        count += 1