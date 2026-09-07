#!/usr/bin/env python3
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

RESULTS_DIR = Path.home() / "vantage" / "results"

CHECKPOINTS = [
    ("google_gemma-3-12b-it", "Gemma", "Original"),
    ("huihui-ai_gemma-3-12b-it-abliterated", "Gemma", "Huihui"),
    ("p-e-w_gemma-3-12b-it-heretic-v2", "Gemma", "Heretic"),
    ("Qwen_Qwen3-4B-Instruct-2507", "Qwen", "Original"),
    ("huihui-ai_Huihui-Qwen3-4B-Instruct-2507-abliterated", "Qwen", "Huihui"),
    ("p-e-w_Qwen3-4B-Instruct-2507-heretic-v2", "Qwen", "Heretic"),
]

rows = []
for ckpt_dir, family, variant in CHECKPOINTS:
    mal_path = RESULTS_DIR / ckpt_dir / "malware_analysis_full_stat.json"
    frr_path = RESULTS_DIR / ckpt_dir / "mitre_frr_full_stat.json"

    mal = json.loads(mal_path.read_text()) if mal_path.exists() else {}
    frr = json.loads(frr_path.read_text()) if frr_path.exists() else {}

    mal_stats = next(iter(mal.values()), {}).get("stat_per_model", {}) if mal else {}
    frr_stats = next(iter(frr.values()), {}) if frr else {}

    rows.append({
        "family": family,
        "variant": variant,
        "correct": mal_stats.get("correct_mc_count", 0),
        "incorrect": mal_stats.get("incorrect_mc_count", 0),
        "parse_err": mal_stats.get("response_parsing_error_count", 0),
        "accept": frr_stats.get("accept_count", 0),
        "refuse": frr_stats.get("refusal_count", 0),
    })

variants = ["Original", "Huihui", "Heretic"]
gemma = sorted([r for r in rows if r["family"] == "Gemma"], key=lambda r: variants.index(r["variant"]))
qwen = sorted([r for r in rows if r["family"] == "Qwen"], key=lambda r: variants.index(r["variant"]))

x = np.arange(len(variants))
width = 0.35

fig, axes = plt.subplots(2, 2, figsize=(13, 10))
fig.suptitle("VANTAGE Full Results — Raw Counts (not percentages)\nMITRE FRR n=750, Malware Analysis n=609",
             fontsize=14, fontweight="bold")

def bar_panel(ax, gemma_vals, qwen_vals, title, ylabel, ylim):
    ax.bar(x - width/2, gemma_vals, width, label="Gemma", color="#55A868")
    ax.bar(x + width/2, qwen_vals, width, label="Qwen", color="#8172B2")
    ax.set_xticks(x)
    ax.set_xticklabels(variants)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.set_ylim(*ylim)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    for i, v in enumerate(gemma_vals):
        ax.text(i - width/2, v + ylim[1]*0.02, f"{v}", ha="center", fontsize=9, fontweight="bold")
    for i, v in enumerate(qwen_vals):
        ax.text(i + width/2, v + ylim[1]*0.02, f"{v}", ha="center", fontsize=9, fontweight="bold")

# Panel 1: Correct count (out of 609)
bar_panel(axes[0, 0],
          [r["correct"] for r in gemma], [r["correct"] for r in qwen],
          "Malware Analysis: Exact-Correct Count (out of 609)", "Correct answers", (0, 150))

# Panel 2: Incorrect count (out of 609)
bar_panel(axes[0, 1],
          [r["incorrect"] for r in gemma], [r["incorrect"] for r in qwen],
          "Malware Analysis: Incorrect Count (out of 609)", "Incorrect answers", (0, 609))

# Panel 3: Parsing error count (out of 609)
bar_panel(axes[1, 0],
          [r["parse_err"] for r in gemma], [r["parse_err"] for r in qwen],
          "Malware Analysis: Parsing Error Count (out of 609)", "Parsing errors", (0, 50))

# Panel 4: FRR refusal count (out of 750)
bar_panel(axes[1, 1],
          [r["refuse"] for r in gemma], [r["refuse"] for r in qwen],
          "MITRE FRR: Refusal Count (out of 750)", "Refusals", (0, 50))

plt.tight_layout()
out_path = RESULTS_DIR / "vantage_raw_counts.png"
plt.savefig(out_path, dpi=150, bbox_inches="tight")
print(f"Saved: {out_path}")
