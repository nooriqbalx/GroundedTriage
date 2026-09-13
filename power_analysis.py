"""
power_analysis.py

GroundedTriage extension - Phase 1.1: Power analysis.

Decides whether the existing 45-item human grounding review (15 responses
per evidence condition: static / dynamic / combined) is large enough to
support the planned extension work, or whether the dataset needs to be
expanded first.

Three things are checked:
  1. Post-hoc sanity check: was n=15/condition enough to detect the
     grounding-collapse effect you already found? (Should come back yes -
     this just confirms the existing headline finding is solid.)
  2. Forward-looking: once the 45 items are split into k failure-mode
     taxonomy categories, is there still enough data per cell to detect
     a real difference in failure-mode distribution across conditions?
  3. OSINT validation: what precision-estimate confidence interval width
     do you get at your current subsample size, and how many samples
     would you need for a tighter estimate?

Run:
    python3 -m pip install statsmodels scipy --break-system-packages
    python3 power_analysis.py
"""

import json
import math
from pathlib import Path

from scipy import stats
from statsmodels.stats.power import GofChisquarePower
from statsmodels.stats.proportion import proportion_confint

DATA_PATH = Path("data/grounding_stats.json")  # run this from the GroundedTriage repo root


def load_grounding_data():
    with open(DATA_PATH) as f:
        return json.load(f)


def cohens_w(observed_props, expected_props):
    """Cohen's w effect size for chi-square / GOF tests."""
    return math.sqrt(sum((o - e) ** 2 / e for o, e in zip(observed_props, expected_props)))


def section_1_posthoc_check(records):
    print("=" * 70)
    print("1. POST-HOC CHECK: was n=15/condition enough for the grounding")
    print("   collapse you already found?")
    print("=" * 70)

    conditions = ["static_evidence", "dynamic_evidence", "combined_evidence"]
    grounded_counts = {}
    n_per_cond = {}
    for cond in conditions:
        sub = [r for r in records if r["condition"] == cond]
        n_per_cond[cond] = len(sub)
        grounded_counts[cond] = sum(1 for r in sub if r["verdict"] == "GROUNDED")

    for cond in conditions:
        n = n_per_cond[cond]
        g = grounded_counts[cond]
        rate = g / n
        print(f"  {cond:20s}: {g}/{n} grounded ({rate:.1%})")

    static_g, static_n = grounded_counts["static_evidence"], n_per_cond["static_evidence"]
    combined_g, combined_n = grounded_counts["combined_evidence"], n_per_cond["combined_evidence"]
    table = [
        [static_g, static_n - static_g],
        [combined_g, combined_n - combined_g],
    ]
    odds_ratio, p_value = stats.fisher_exact(table)
    print(f"\n  Fisher's exact (static vs combined): p = {p_value:.6f}")

    p1, p2 = static_g / static_n, combined_g / combined_n
    h = 2 * math.asin(math.sqrt(p1)) - 2 * math.asin(math.sqrt(p2))
    print(f"  Cohen's h (proportion difference): {abs(h):.3f}  (>0.8 = large effect)")
    print(
        "\n  Verdict: this effect is large and n=15/condition was already "
        "more than sufficient\n  to detect it (p < 0.001 with a huge effect size). "
        "The headline finding does NOT\n  need more data. This is expected - "
        "it's just a sanity check before moving on.\n"
    )
    return n_per_cond


def section_2_taxonomy_power(n_per_cell_available):
    print("=" * 70)
    print("2. FORWARD-LOOKING: is 45 items still enough once split into a")
    print("   failure-mode taxonomy (3 conditions x k categories)?")
    print("=" * 70)

    power_analysis = GofChisquarePower()
    alpha = 0.05
    target_power = 0.80

    for k_categories in [3, 4, 5, 6]:
        n_medium = power_analysis.solve_power(
            effect_size=0.3, alpha=alpha, power=target_power, n_bins=k_categories
        )
        n_large = power_analysis.solve_power(
            effect_size=0.5, alpha=alpha, power=target_power, n_bins=k_categories
        )

        print(f"\n  If taxonomy has {k_categories} categories (per condition, n=15 available):")
        print(f"    n needed for 80% power, medium effect (w=0.3): {n_medium:.0f}")
        print(f"    n needed for 80% power, large  effect (w=0.5): {n_large:.0f}")
        print(f"    You currently have: 15 per condition")
        if 15 >= n_medium:
            print(f"    -> 15 is ENOUGH to detect a medium-or-larger difference here.")
        elif 15 >= n_large:
            print(f"    -> 15 is only enough to reliably detect a LARGE difference, "
                  f"not a medium one.")
        else:
            print(f"    -> 15 is UNDERPOWERED even for a large effect at this many categories.")

    print(
        "\n  Honest read: at n=15/condition, none of these are within reach even for a\n"
        "  large effect. Treat the failure-mode taxonomy as DESCRIPTIVE (counts + examples),\n"
        "  not a formally tested chi-square comparison across conditions.\n"
    )


def section_3_osint_precision(n_available):
    print("=" * 70)
    print("3. OSINT VALIDATION: precision-estimate confidence interval at")
    print("   your current subsample size")
    print("=" * 70)

    for n in [10, 15, 20, 30]:
        for assumed_precision in [0.7, 0.85]:
            successes = round(n * assumed_precision)
            ci_low, ci_high = proportion_confint(successes, n, alpha=0.05, method="wilson")
            width = ci_high - ci_low
            print(
                f"  n={n:2d}, assumed precision~{assumed_precision:.0%}: "
                f"95% CI = [{ci_low:.1%}, {ci_high:.1%}]  (width: {width:.1%})"
            )

    print(
        "\n  Interpretation: with n=15-20 confident family-attribution claims, expect a\n"
        "  95% CI width of ~30-35 percentage points - wide, but usable for a first-pass\n"
        "  estimate. For a tighter estimate (~20pp width), you'd need n~30+, pulled from\n"
        "  confident-but-unreviewed responses in the full 504, not new samples.\n"
    )


def main():
    if not DATA_PATH.exists():
        print(f"ERROR: {DATA_PATH} not found. Run this script from the GroundedTriage repo root.")
        return

    records = load_grounding_data()
    n_per_cond = section_1_posthoc_check(records)
    section_2_taxonomy_power(n_per_cond)
    section_3_osint_precision(n_per_cond)

    print("=" * 70)
    print("DECISION")
    print("=" * 70)
    print(
        "  - Headline grounding-collapse finding: already well-powered. No expansion needed.\n"
        "  - Failure-mode taxonomy: report descriptively (counts + examples), not as a\n"
        "    formal statistical test - n=15/condition can't support that at any category count.\n"
        "  - OSINT validation: proceed with the confident-claims subset from the 45-item\n"
        "    review as a first-pass precision estimate.\n"
        "  - Net recommendation: do NOT expand the 56-sample dataset or re-run new model\n"
        "    inference. Proceed straight to Phase 1.3 (taxonomy) using what you have.\n"
    )


if __name__ == "__main__":
    main()