"""
SecuriCopilot -- Publication-quality figure generation
Mirrors the visual language of UrduSafeBench (Fig 1: heatmap + ranked bar
pair; Fig 4: row-normalized confusion-style heatmap), applied to this
project's accuracy, abstention, and grounding results.

Outputs high-res PNG + PDF for each figure, ready for a paper/report.
"""

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# ---------------------------------------------------------------
# Style setup -- consistent, paper-ready look across all figures
# ---------------------------------------------------------------
sns.set_theme(style="whitegrid", context="paper", font_scale=1.15)
plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "font.family": "sans-serif",
    "axes.edgecolor": "#333333",
    "axes.linewidth": 0.8,
    "figure.facecolor": "white",
})

MODEL_LABELS = {
    "openai/gpt-oss-120b": "GPT-OSS-120B",
    "openai/gpt-oss-20b": "GPT-OSS-20B",
    "qwen/qwen3.6-27b": "Qwen3.6-27B",
}
CONDITION_LABELS = {
    "static_evidence": "Static",
    "dynamic_evidence": "Dynamic",
    "combined_evidence": "Combined",
}
CONDITION_ORDER = ["static_evidence", "dynamic_evidence", "combined_evidence"]
MODEL_ORDER = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.6-27b"]

OUT_DIR = "figures"
import os
os.makedirs(OUT_DIR, exist_ok=True)


def save_fig(fig, name):
    fig.savefig(f"{OUT_DIR}/{name}.png", bbox_inches="tight")
    fig.savefig(f"{OUT_DIR}/{name}.pdf", bbox_inches="tight")
    print(f"Saved {OUT_DIR}/{name}.png and .pdf")


# =================================================================
# Load data
# =================================================================
with open("scored_results.json", "r") as f:
    scored = json.load(f)

with open("grounding_stats.json", "r") as f:
    grounding = json.load(f)

df = pd.DataFrame(scored)
gdf = pd.DataFrame(grounding)


# =================================================================
# FIGURE 1 -- Accuracy heatmap (model x condition) + ranked bar
# Mirrors UrduSafeBench Fig 1 structure exactly.
# =================================================================
def build_heatmap_bar_pair(metric_col, agg_func, cbar_label, bar_label,
                            title, filename, cmap="RdYlGn_r", bar_color="#C0392B"):
    pivot = (
        df.pivot_table(index="model", columns="condition", values=metric_col,
                        aggfunc=agg_func, observed=True)
        .reindex(index=MODEL_ORDER, columns=CONDITION_ORDER) * 100
    )
    pivot.index = [MODEL_LABELS[m] for m in pivot.index]
    pivot.columns = [CONDITION_LABELS[c] for c in pivot.columns]

    mean_by_condition = pivot.mean(axis=0).sort_values(ascending=False)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw={"width_ratios": [1.15, 1]})

    sns.heatmap(pivot, annot=True, fmt=".1f", cmap=cmap, cbar_kws={"label": cbar_label},
                linewidths=0.6, linecolor="white", ax=axes[0], vmin=0,
                vmax=max(pivot.values.max(), 5))
    axes[0].set_title(f"{title} by Model × Condition", fontsize=11, fontweight="bold")
    axes[0].set_xlabel("Evidence Condition")
    axes[0].set_ylabel("")

    axes[1].barh(mean_by_condition.index, mean_by_condition.values, color=bar_color, alpha=0.85)
    axes[1].invert_yaxis()
    axes[1].set_title(f"Mean {bar_label} Across Models", fontsize=11, fontweight="bold")
    axes[1].set_xlabel(bar_label)
    for i, v in enumerate(mean_by_condition.values):
        axes[1].text(v + max(mean_by_condition.values) * 0.02, i, f"{v:.1f}%",
                     va="center", fontsize=9)

    fig.suptitle(f"Fig. — {title} Across Evidence Conditions (N=504)",
                  fontsize=12, fontweight="bold", y=1.03)
    fig.tight_layout()
    save_fig(fig, filename)
    plt.close(fig)


build_heatmap_bar_pair(
    metric_col="correct", agg_func="mean",
    cbar_label="Accuracy (%)", bar_label="Accuracy (%)",
    title="Classification Accuracy", filename="fig1_accuracy",
    cmap="RdYlGn", bar_color="#2E7D32",
)

build_heatmap_bar_pair(
    metric_col="abstained", agg_func="mean",
    cbar_label="Abstention Rate (%)", bar_label="Abstention Rate (%)",
    title="Abstention Rate", filename="fig2_abstention",
    cmap="YlOrRd", bar_color="#C0392B",
)


# =================================================================
# FIGURE 3 -- Grounding rate: heatmap + ranked bar (from N=45 sample)
# =================================================================
gdf["grounded_num"] = (gdf["verdict"] == "GROUNDED").astype(int)

pivot_g = (
    gdf.pivot_table(index="model", columns="condition", values="grounded_num",
                     aggfunc="mean", observed=True)
    .reindex(index=MODEL_ORDER, columns=CONDITION_ORDER) * 100
)
pivot_g.index = [MODEL_LABELS[m] for m in pivot_g.index]
pivot_g.columns = [CONDITION_LABELS[c] for c in pivot_g.columns]

mean_ground_by_condition = pivot_g.mean(axis=0).sort_values(ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw={"width_ratios": [1.15, 1]})

sns.heatmap(pivot_g, annot=True, fmt=".1f", cmap="RdYlGn", cbar_kws={"label": "Grounded (%)"},
            linewidths=0.6, linecolor="white", ax=axes[0], vmin=0, vmax=100)
axes[0].set_title("Grounding Rate by Model × Condition", fontsize=11, fontweight="bold")
axes[0].set_xlabel("Evidence Condition")
axes[0].set_ylabel("")

axes[1].barh(mean_ground_by_condition.index, mean_ground_by_condition.values,
             color="#2E7D32", alpha=0.85)
axes[1].invert_yaxis()
axes[1].set_title("Mean Grounding Rate", fontsize=11, fontweight="bold")
axes[1].set_xlabel("Grounded (%)")
for i, v in enumerate(mean_ground_by_condition.values):
    axes[1].text(v + 2, i, f"{v:.1f}%", va="center", fontsize=9)

fig.suptitle("Fig. — Grounding Rate Across Evidence Conditions\n"
             "(Human-Reviewed Stratified Sample, N=45)",
             fontsize=12, fontweight="bold", y=1.06)
fig.tight_layout()
save_fig(fig, "fig3_grounding")
plt.close(fig)


# =================================================================
# FIGURE 4 -- Confusion-matrix-style heatmap:
# Abstention Behavior x Outcome, row-normalized (mirrors paper's
# Refusal x Safety Judgment confusion matrix, Fig. 4)
# =================================================================
def outcome_label(row):
    if row["correct"]:
        return "Correct"
    elif row["abstained"]:
        return "Abstained"
    else:
        return "Wrong (Committed)"

df["outcome"] = df.apply(outcome_label, axis=1)

confusion = pd.crosstab(
    df["condition"].map(CONDITION_LABELS),
    df["outcome"],
    normalize="index",
) * 100
confusion = confusion.reindex(index=[CONDITION_LABELS[c] for c in CONDITION_ORDER])
# Reorder columns for a sensible reading order
col_order = [c for c in ["Correct", "Wrong (Committed)", "Abstained"] if c in confusion.columns]
confusion = confusion[col_order]

fig, ax = plt.subplots(figsize=(6.5, 4.2))
sns.heatmap(confusion, annot=True, fmt=".1f", cmap="RdPu", cbar_kws={"label": "Row %"},
            linewidths=0.6, linecolor="white", ax=ax, vmin=0, vmax=100)
ax.set_title("Fig. — Response Outcome by Evidence Condition\n(Row-Normalized, N=504)",
              fontsize=12, fontweight="bold")
ax.set_xlabel("Outcome")
ax.set_ylabel("Evidence Condition")
fig.tight_layout()
save_fig(fig, "fig4_outcome_confusion")
plt.close(fig)


# =================================================================
# FIGURE 5 -- Per-family accuracy heatmap (model x family)
# =================================================================
pivot_family = (
    df.pivot_table(index="model", columns="true_family", values="correct",
                    aggfunc="mean", observed=True)
    .reindex(index=MODEL_ORDER) * 100
)
pivot_family.index = [MODEL_LABELS[m] for m in pivot_family.index]
# Sort families by mean accuracy for readability
family_order = pivot_family.mean(axis=0).sort_values(ascending=False).index
pivot_family = pivot_family[family_order]

fig, ax = plt.subplots(figsize=(10, 3.8))
sns.heatmap(pivot_family, annot=True, fmt=".0f", cmap="RdYlGn", cbar_kws={"label": "Accuracy (%)"},
            linewidths=0.6, linecolor="white", ax=ax, vmin=0,
            vmax=max(pivot_family.values.max(), 5))
ax.set_title("Fig. — Classification Accuracy by Malware Family × Model (N=504)",
              fontsize=12, fontweight="bold")
ax.set_xlabel("True Malware Family")
ax.set_ylabel("")
plt.xticks(rotation=30, ha="right")
fig.tight_layout()
save_fig(fig, "fig5_family_accuracy")
plt.close(fig)

print("\nAll figures generated in the 'figures/' folder.")