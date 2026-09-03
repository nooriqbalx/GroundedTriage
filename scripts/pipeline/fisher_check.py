"""
SecuriCopilot -- Fisher's exact test robustness check for the small
grounding sample (supplements the chi-square result given small
expected cell counts)
"""

from scipy.stats import fisher_exact

# Pairwise comparisons: static vs dynamic, static vs combined, dynamic vs combined
# Table format: [[grounded, unsupported], [grounded, unsupported]]

comparisons = {
    "Static vs Dynamic": [[11, 4], [2, 13]],
    "Static vs Combined": [[11, 4], [1, 14]],
    "Dynamic vs Combined": [[2, 13], [1, 14]],
}

print("Fisher's exact test (pairwise, robust to small samples)\n")
for label, table in comparisons.items():
    odds_ratio, p = fisher_exact(table)
    print(f"{label}: odds ratio = {odds_ratio:.2f}, p = {p:.4g}")