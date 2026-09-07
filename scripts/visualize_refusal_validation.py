import os
import glob
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import RESULTS_DIR

INPUT_DIR = str(RESULTS_DIR / "all_refusal_validation")


OUTPUT_DIR = os.path.join(INPUT_DIR, "figures")

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# FIND VALIDATION CSV FILES
# ============================================================

files = glob.glob(
    os.path.join(INPUT_DIR, "**", "*refusal_validation.csv"),
    recursive=True
)

if not files:
    raise FileNotFoundError(
        f"No refusal validation CSV files found in {INPUT_DIR}"
    )

print("=" * 100)
print("REFUSAL VALIDATION VISUALIZATION")
print("=" * 100)
print()
print(f"Input directory : {INPUT_DIR}")
print(f"Files found     : {len(files)}")
print(f"Output directory: {OUTPUT_DIR}")
print()


# ============================================================
# MODEL / DATASET DETECTION
# ============================================================

def detect_model(path):
    p = path.lower()

    if "huihui-ai_gemma" in p:
        return "Gemma-3-12B-IT Abliterated"

    if "p-e-w_gemma" in p:
        return "Gemma-3-12B-IT Heretic-v2"

    if "google_gemma" in p:
        return "Gemma-3-12B-IT"

    if "huihui-ai_huihui-qwen" in p:
        return "Qwen3-4B Abliterated"

    if "p-e-w_qwen" in p:
        return "Qwen3-4B Heretic-v2"

    if "qwen_qwen" in p:
        return "Qwen3-4B-Instruct-2507"

    return "Unknown"


def detect_dataset(path, df):
    p = path.lower()

    if "mitre" in p:
        return "MITRE FRR"

    if "malware" in p:
        return "Malware Analysis"

    # Fallback based on columns
    cols = " ".join(str(c).lower() for c in df.columns)

    if "attack_type" in cols or "test_case_prompt" in cols:
        return "MITRE FRR"

    return "Malware Analysis"


# ============================================================
# LOAD DATA
# ============================================================

all_data = []

for path in files:

    try:
        df = pd.read_csv(path)

        if df.empty:
            continue

        model = detect_model(path)
        dataset = detect_dataset(path, df)

        print(
            f"{dataset:<20} | "
            f"{model:<35} | "
            f"{len(df):>6} rows"
        )

        # ----------------------------------------------------
        # Determine classification column
        # ----------------------------------------------------

        classification_col = None

        candidates = [
            "validated_classification",
            "classification",
            "refusal_classification"
        ]

        for c in candidates:
            if c in df.columns:
                classification_col = c
                break

        if classification_col is None:
            print(f"WARNING: no classification column in {path}")
            continue

        df["_model"] = model
        df["_dataset"] = dataset
        df["_classification"] = df[classification_col].astype(str)

        all_data.append(df)

    except Exception as e:
        print(f"ERROR reading {path}: {e}")


if not all_data:
    raise RuntimeError("No usable validation data found.")


data = pd.concat(all_data, ignore_index=True)


# ============================================================
# NORMALIZE CLASSIFICATIONS
# ============================================================

data["_classification"] = (
    data["_classification"]
    .str.upper()
    .str.strip()
)


# ============================================================
# SUMMARY
# ============================================================

models = sorted(data["_model"].unique())
datasets = sorted(data["_dataset"].unique())


def is_refusal(x):
    return x in [
        "REFUSAL_ONLY",
        "REFUSAL_PLUS_SAFE_REDIRECTION",
        "REFUSAL_WITH_CODE_PROVISION",
    ]


def is_redirection(x):
    return x in [
        "REFUSAL_PLUS_SAFE_REDIRECTION",
        "SAFE_REDIRECTION_WITHOUT_EXPLICIT_REFUSAL",
        "SAFE_REDIRECTION_WITHOUT_EXPLICIT_REFUSAL",
    ]


summary = []


for dataset in datasets:

    for model in models:

        subset = data[
            (data["_dataset"] == dataset) &
            (data["_model"] == model)
        ]

        if len(subset) == 0:
            continue

        total = len(subset)

        refusal = subset["_classification"].apply(is_refusal).sum()

        redirection = subset["_classification"].apply(
            is_redirection
        ).sum()

        safety_warning = (
            subset["_classification"]
            .eq("COMPLIANCE_WITH_SAFETY_WARNING")
            .sum()
        )

        full_compliance = (
            subset["_classification"]
            .eq("FULL_COMPLIANCE")
            .sum()
        )

        partial = (
            subset["_classification"]
            .eq("PARTIAL_COMPLIANCE")
            .sum()
        )

        ambiguous = (
            subset["_classification"]
            .eq("AMBIGUOUS_NEEDS_REVIEW")
            .sum()
        )

        summary.append({
            "Dataset": dataset,
            "Model": model,
            "Total": total,

            "Explicit Refusal": refusal,
            "Refusal Rate (%)":
                refusal / total * 100,

            "Safe Redirection": redirection,
            "Safe Redirection Rate (%)":
                redirection / total * 100,

            "Safety Warning": safety_warning,
            "Safety Warning Rate (%)":
                safety_warning / total * 100,

            "Full Compliance": full_compliance,
            "Full Compliance Rate (%)":
                full_compliance / total * 100,

            "Partial Compliance": partial,
            "Partial Compliance Rate (%)":
                partial / total * 100,

            "Ambiguous": ambiguous,
            "Ambiguous Rate (%)":
                ambiguous / total * 100,
        })


summary_df = pd.DataFrame(summary)


# ============================================================
# SAVE SUMMARY
# ============================================================

summary_path = os.path.join(
    OUTPUT_DIR,
    "refusal_validation_summary.csv"
)

summary_df.to_csv(
    summary_path,
    index=False
)

print()
print("=" * 100)
print("SUMMARY")
print("=" * 100)

print(
    summary_df[
        [
            "Dataset",
            "Model",
            "Total",
            "Explicit Refusal",
            "Refusal Rate (%)",
            "Safe Redirection",
            "Safety Warning"
        ]
    ].to_string(index=False)
)

print()
print(f"Summary CSV: {summary_path}")


# ============================================================
# MODEL DISPLAY NAMES
# ============================================================

display_names = {
    "Gemma-3-12B-IT":
        "Gemma-3-12B-IT",

    "Gemma-3-12B-IT Abliterated":
        "Gemma-3-12B-IT\nAbliterated",

    "Gemma-3-12B-IT Heretic-v2":
        "Gemma-3-12B-IT\nHeretic-v2",

    "Qwen3-4B-Instruct-2507":
        "Qwen3-4B\nInstruct-2507",

    "Qwen3-4B Abliterated":
        "Qwen3-4B\nAbliterated",

    "Qwen3-4B Heretic-v2":
        "Qwen3-4B\nHeretic-v2",
}


# ============================================================
# 1. FRR COMPARISON
# ============================================================

pivot = summary_df.pivot(
    index="Model",
    columns="Dataset",
    values="Refusal Rate (%)"
)

ax = pivot.plot(
    kind="bar",
    figsize=(12, 7)
)

ax.set_title(
    "Gemma and Qwen Refusal Rate (FRR) Comparison",
    fontsize=16
)

ax.set_ylabel("Refusal Rate (%)")
ax.set_xlabel("Model")
ax.legend(title="Dataset")

plt.xticks(rotation=25, ha="right")
plt.tight_layout()

plt.savefig(
    os.path.join(
        OUTPUT_DIR,
        "01_frr_comparison.png"
    ),
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 2. EXPLICIT REFUSAL RATE
# ============================================================

pivot = summary_df.pivot(
    index="Model",
    columns="Dataset",
    values="Refusal Rate (%)"
)

ax = pivot.plot(
    kind="bar",
    figsize=(12, 7)
)

ax.set_title(
    "Manual Evaluation — Explicit Refusal Rate",
    fontsize=16
)

ax.set_ylabel("Explicit Refusal Rate (%)")
ax.set_xlabel("Model")

plt.xticks(rotation=25, ha="right")
plt.tight_layout()

plt.savefig(
    os.path.join(
        OUTPUT_DIR,
        "02_explicit_refusal_rate.png"
    ),
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 3. SAFE REDIRECTION
# ============================================================

pivot = summary_df.pivot(
    index="Model",
    columns="Dataset",
    values="Safe Redirection Rate (%)"
)

ax = pivot.plot(
    kind="bar",
    figsize=(12, 7)
)

ax.set_title(
    "Safe Redirection Rate",
    fontsize=16
)

ax.set_ylabel("Safe Redirection Rate (%)")
ax.set_xlabel("Model")

plt.xticks(rotation=25, ha="right")
plt.tight_layout()

plt.savefig(
    os.path.join(
        OUTPUT_DIR,
        "03_safe_redirection_rate.png"
    ),
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 4. SAFETY WARNING
# ============================================================

pivot = summary_df.pivot(
    index="Model",
    columns="Dataset",
    values="Safety Warning Rate (%)"
)

ax = pivot.plot(
    kind="bar",
    figsize=(12, 7)
)

ax.set_title(
    "Compliance with Safety Warning",
    fontsize=16
)

ax.set_ylabel("Safety-Warning Rate (%)")
ax.set_xlabel("Model")

plt.xticks(rotation=25, ha="right")
plt.tight_layout()

plt.savefig(
    os.path.join(
        OUTPUT_DIR,
        "04_safety_warning_rate.png"
    ),
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 5. CLASSIFICATION BREAKDOWN
# ============================================================

classification_order = [
    "FULL_COMPLIANCE",
    "COMPLIANCE_WITH_SAFETY_WARNING",
    "PARTIAL_COMPLIANCE",
    "REFUSAL_ONLY",
    "REFUSAL_PLUS_SAFE_REDIRECTION",
    "REFUSAL_WITH_CODE_PROVISION",
    "SAFE_REDIRECTION_WITHOUT_EXPLICIT_REFUSAL",
    "AMBIGUOUS_NEEDS_REVIEW",
]


for dataset in datasets:

    subset = data[
        data["_dataset"] == dataset
    ]

    counts = (
        subset
        .groupby(["_model", "_classification"])
        .size()
        .unstack(fill_value=0)
    )

    counts = counts.reindex(
        columns=[
            c for c in classification_order
            if c in counts.columns
        ],
        fill_value=0
    )

    percentages = counts.div(
        counts.sum(axis=1),
        axis=0
    ) * 100

    ax = percentages.plot(
        kind="bar",
        stacked=True,
        figsize=(14, 8)
    )

    title = (
        f"Manual Evaluation — {dataset}\n"
        "Response Classification Distribution"
    )

    ax.set_title(
        title,
        fontsize=16
    )

    ax.set_ylabel("Percentage of Responses (%)")
    ax.set_xlabel("Model")

    plt.xticks(
        rotation=25,
        ha="right"
    )

    plt.legend(
        title="Classification",
        bbox_to_anchor=(1.02, 1),
        loc="upper left"
    )

    plt.tight_layout()

    filename = (
        "05_classification_breakdown_"
        + dataset.lower()
        .replace(" ", "_")
        .replace("-", "_")
        + ".png"
    )

    plt.savefig(
        os.path.join(
            OUTPUT_DIR,
            filename
        ),
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()


# ============================================================
# 6. GEMMA VS QWEN
# ============================================================

def family(model):

    if model.lower().startswith("gemma"):
        return "Gemma"

    if model.lower().startswith("qwen"):
        return "Qwen"

    return "Other"


summary_df["Family"] = summary_df["Model"].apply(family)


family_summary = (
    summary_df
    .groupby(["Dataset", "Family"])["Refusal Rate (%)"]
    .mean()
    .reset_index()
)


pivot = family_summary.pivot(
    index="Family",
    columns="Dataset",
    values="Refusal Rate (%)"
)

ax = pivot.plot(
    kind="bar",
    figsize=(9, 6)
)

ax.set_title(
    "Gemma vs Qwen — Mean Refusal Rate",
    fontsize=16
)

ax.set_ylabel("Mean Refusal Rate (%)")
ax.set_xlabel("Model Family")

plt.xticks(rotation=0)

plt.tight_layout()

plt.savefig(
    os.path.join(
        OUTPUT_DIR,
        "06_gemma_vs_qwen_frr.png"
    ),
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 7. HEATMAP-LIKE TABLE
# ============================================================

frr_table = summary_df.pivot(
    index="Model",
    columns="Dataset",
    values="Refusal Rate (%)"
)

fig, ax = plt.subplots(
    figsize=(10, 5)
)

ax.axis("off")

table = ax.table(
    cellText=[
        [
            model,
            f"{frr_table.loc[model].get('MITRE FRR', 0):.2f}",
            f"{frr_table.loc[model].get('Malware Analysis', 0):.2f}"
        ]
        for model in frr_table.index
    ],
    colLabels=[
        "Model",
        "MITRE FRR (%)",
        "Malware (%)"
    ],
    loc="center"
)

table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 2)

ax.set_title(
    "Refusal Rate Summary",
    fontsize=16,
    pad=20
)

plt.tight_layout()

plt.savefig(
    os.path.join(
        OUTPUT_DIR,
        "07_frr_summary_table.png"
    ),
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# FINAL
# ============================================================

print()
print("=" * 100)
print("VISUALIZATION COMPLETE")
print("=" * 100)
print()

for f in sorted(glob.glob(os.path.join(OUTPUT_DIR, "*.png"))):
    print(f)

print()
print(f"Summary CSV:")
print(summary_path)
