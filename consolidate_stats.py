"""
consolidate_stats.py

GroundedTriage extension - Phase 1.6: Full statistical consolidation.

Recomputes every finding (original + extension) with effect sizes and
confidence intervals, producing the final numbers for the write-up in
one place. Pulls from:
  - data/scored_results.json     (504 responses - accuracy/abstention)
  - data/grounding_stats.json    (45 responses - human grounding review)
  - data/failure_mode_taxonomy.json (45 responses - taxonomy coding)
  - data/osint_validation_results.json (11-15 checkable OSINT checks)

Run:
    python3 consolidate_stats.py

Requires:
    pip install scipy statsmodels --break-system-packages
"""

import json
import math
from pathlib import Path
from collections import Counter, defaultdict

from scipy import stats as sps
from statsmodels.stats.proportion import proportion_confint


def wilson_ci(successes, n):
    if n == 0:
        return (float("nan"), float("nan"))
    return proportion_confint(successes, n, alpha=0.05, method="wilson")


def cohens_h(p1, p2):
    return abs(2 * math.asin(math.sqrt(p1)) - 2 * math.asin(math.sqrt(p2)))


def cramers_v(chi2, n, min_dim):
    return math.sqrt(chi2 / (n * (min_dim - 1))) if n > 0 else float("nan")


def section_accuracy_abstention():
    print("=" * 70)
    print("SECTION 1: Accuracy and abstention by condition (original finding)")
    print("=" * 70)
    data = json.load(open("data/scored_results.json"))
    conditions = ["static_evidence", "dynamic_evidence", "combined_evidence"]

    acc_table = []
    abst_table = []
    for cond in conditions:
        sub = [r for r in data if r["condition"] == cond]
        n = len(sub)
        acc = sum(1 for r in sub if r["correct"])
        abst = sum(1 for r in sub if r["abstained"])
        acc_ci = wilson_ci(acc, n)
        abst_ci = wilson_ci(abst, n)
        acc_table.append((cond, acc, n))
        abst_table.append((cond, abst, n))
        print(f"  {cond:20s}: accuracy {acc}/{n} ({acc/n:.1%}, 95% CI [{acc_ci[0]:.1%}, {acc_ci[1]:.1%}])"
              f"  |  abstention {abst}/{n} ({abst/n:.1%}, 95% CI [{abst_ci[0]:.1%}, {abst_ci[1]:.1%}])")

    # Chi-square + Cramer's V for accuracy across conditions
    acc_contingency = [[a, n - a] for _, a, n in acc_table]
    chi2, p, dof, _ = sps.chi2_contingency(acc_contingency)
    n_total = sum(n for _, _, n in acc_table)
    v = cramers_v(chi2, n_total, min(2, 3))
    print(f"\n  Accuracy chi-square: chi2={chi2:.2f}, p={p:.4f}, Cramer's V={v:.3f}")

    abst_contingency = [[a, n - a] for _, a, n in abst_table]
    chi2b, pb, dofb, _ = sps.chi2_contingency(abst_contingency)
    vb = cramers_v(chi2b, n_total, min(2, 3))
    print(f"  Abstention chi-square: chi2={chi2b:.2f}, p={pb:.6f}, Cramer's V={vb:.3f}")
    print()


def section_grounding_collapse():
    print("=" * 70)
    print("SECTION 2: Grounding collapse (original headline finding, with CIs)")
    print("=" * 70)
    data = json.load(open("data/grounding_stats.json"))
    conditions = ["static_evidence", "dynamic_evidence", "combined_evidence"]

    rates = {}
    for cond in conditions:
        sub = [r for r in data if r["condition"] == cond]
        n = len(sub)
        grounded = sum(1 for r in sub if r["verdict"] == "GROUNDED")
        ci = wilson_ci(grounded, n)
        rates[cond] = (grounded, n)
        print(f"  {cond:20s}: {grounded}/{n} grounded ({grounded/n:.1%}, 95% CI [{ci[0]:.1%}, {ci[1]:.1%}])")

    g_static, n_static = rates["static_evidence"]
    g_combined, n_combined = rates["combined_evidence"]
    table = [[g_static, n_static - g_static], [g_combined, n_combined - g_combined]]
    odds_ratio, p = sps.fisher_exact(table)
    h = cohens_h(g_static / n_static, g_combined / n_combined)
    print(f"\n  Fisher's exact (static vs combined): p = {p:.6f}")
    print(f"  Cohen's h: {h:.3f} (large effect threshold: 0.8)")
    print()


def section_taxonomy():
    print("=" * 70)
    print("SECTION 3: Failure-mode taxonomy (descriptive - reported per Phase 1.1)")
    print("=" * 70)
    taxonomy = json.load(open("data/failure_mode_taxonomy.json"))
    coded = {k: v for k, v in taxonomy.items() if v.get("category") not in (None, "SKIPPED")}
    counts = Counter(v["category"] for v in coded.values())
    total = sum(counts.values())
    for cat, n in counts.most_common():
        print(f"  {cat:35s}: {n}/{total} ({n/total:.1%})")
    print("\n  NOTE: reported as descriptive counts only - power analysis (Phase 1.1)")
    print("  found n=15/condition insufficient for a formally tested comparison.")
    print()


def section_osint():
    print("=" * 70)
    print("SECTION 4: OSINT validation (independent precision check)")
    print("=" * 70)
    path = Path("data/osint_validation_results.json")
    if not path.exists():
        print("  No OSINT results found - run osint_validation.py first.")
        return
    results = json.load(open(path))

    checkable = {k: v for k, v in results.items() if v["verdict"] != "no_checkable_artifact"}
    supported = sum(1 for v in checkable.values() if v["verdict"] in ("independently_supported", "y"))
    contradicted = sum(1 for v in checkable.values() if v["verdict"] == "contradicted")
    unsupported = sum(1 for v in checkable.values() if v["verdict"] in ("no_independent_support", "n"))
    total = len(checkable)

    ci = wilson_ci(supported, total)
    print(f"  Checkable claims: {total}")
    print(f"    Independently supported: {supported} ({supported/total:.1%}, 95% CI [{ci[0]:.1%}, {ci[1]:.1%}])")
    print(f"    Directly contradicted:   {contradicted} ({contradicted/total:.1%})")
    print(f"    Unsupported (no confirming evidence): {unsupported} ({unsupported/total:.1%})")

    # Breakdown: imphash-based vs manual domain/cert-based
    by_type = defaultdict(list)
    for v in checkable.values():
        by_type[v["check_type"]].append(v["verdict"])
    print("\n  By check type:")
    for check_type, verdicts in by_type.items():
        n = len(verdicts)
        sup = sum(1 for v in verdicts if v in ("independently_supported", "y"))
        print(f"    {check_type:25s}: {sup}/{n} supported")
    print()


def main():
    section_accuracy_abstention()
    section_grounding_collapse()
    section_taxonomy()
    section_osint()

    print("=" * 70)
    print("ALL SECTIONS COMPLETE - copy relevant numbers into REPORT.md / manuscript")
    print("=" * 70)


if __name__ == "__main__":
    main()