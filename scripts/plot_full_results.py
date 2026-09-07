#!/usr/bin/env python3
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

RESULTS_DIR = Path.home() / "vantage" / "results"
summary_path = RESULTS_DIR / "full_summary.json"

with open(summary_path) as f:
    rows = json.load(f)

variants = ["Original", "Huihui", "Heretic"]
gemma = [r for r in rows if r["family"] == "Gemma"]
qwen = [r for r in rows if r["family"] == "Qwen"]
# ensure consistent order
gemma = sorted(gemma, key=lambda r: variants.index(r["variant"]))
qwen = sorted(qwen, key=lambda r: variants.index(r["variant"]))

x = np.arange(len(variants))
width = 0.35

fig, axes = plt.subplots(2, 2, figsize=(13, 10))
fig.suptitle("VANTAGE Full Results — Gemma-3-12B vs Qwen3-4B\n(MITRE FRR n=750, Malware Analysis n=609)",
             fontsize=14, fontweight="bold")

def bar_panel(ax, gemma_vals, qwen_vals, title, ylabel, ylim, fmt="{:.3f}"):
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
        if v is not None:
            ax.text(i - width/2, v + ylim[1]*0.02, fmt.format(v), ha="center", fontsize=9)
    for i, v in enumerate(qwen_vals):
        if v is not None:
            ax.text(i + width/2, v + ylim[1]*0.02, fmt.format(v), ha="center", fontsize=9)

# Panel 1: Malware Analysis avg_score
bar_panel(axes[0, 0],
          [r["mal_avg_score"] for r in gemma], [r["mal_avg_score"] for r in qwen],
          "Malware Analysis: Average Score (Jaccard)", "Avg Score", (0, 0.7))

# Panel 2: Exact match %
bar_panel(axes[0, 1],
          [r["mal_correct_mc_pct"] for r in gemma], [r["mal_correct_mc_pct"] for r in qwen],
          "Malware Analysis: Exact Match Rate", "Exact Match Rate", (0, 0.5),
          fmt="{:.1%}")

# Panel 3: Parsing errors (as % of 609, easier to read than raw counts)
gemma_perr_pct = [(r["mal_parsing_error_count"] / 609) if r["mal_parsing_error_count"] is not None else None for r in gemma]
qwen_perr_pct = [(r["mal_parsing_error_count"] / 609) if r["mal_parsing_error_count"] is not None else None for r in qwen]
bar_panel(axes[1, 0],
          gemma_perr_pct, qwen_perr_pct,
          "Malware Analysis: Response Parsing Failure Rate", "Parsing Error Rate", (0, 1.0),
          fmt="{:.1%}")

# Panel 4: FRR refusal rate
bar_panel(axes[1, 1],
          [r["frr_refusal_rate"] for r in gemma], [r["frr_refusal_rate"] for r in qwen],
          "MITRE FRR: False Refusal Rate", "Refusal Rate", (0, 1.0),
          fmt="{:.1%}")

plt.tight_layout()
out1 = RESULTS_DIR / "vantage_full_comparison.png"
plt.savefig(out1, dpi=150, bbox_inches="tight")
print(f"Saved: {out1}")

# --- Delta chart ---
fig2, ax2 = plt.subplots(figsize=(9, 6))
families_list = ["Gemma", "Qwen"]
by_family = {}
for r in rows:
    by_family.setdefault(r["family"], {})[r["variant"]] = r

huihui_deltas = []
heretic_deltas = []
for fam in families_list:
    orig = by_family[fam]["Original"]["mal_avg_score"]
    huihui_deltas.append(by_family[fam]["Huihui"]["mal_avg_score"] - orig)
    heretic_deltas.append(by_family[fam]["Heretic"]["mal_avg_score"] - orig)

x2 = np.arange(len(families_list))
width2 = 0.35
ax2.bar(x2 - width2/2, huihui_deltas, width2, label="Huihui", color="#DD8452")
ax2.bar(x2 + width2/2, heretic_deltas, width2, label="Heretic", color="#C44E52")
ax2.axhline(0, color="black", linewidth=0.8)
ax2.set_xticks(x2)
ax2.set_xticklabels(families_list)
ax2.set_ylabel("Δ avg_score vs Original")
ax2.set_title("Malware Analysis Score Change vs Original (Full Run)", fontsize=12, fontweight="bold")
ax2.legend()
ax2.grid(axis="y", alpha=0.3)
for i, v in enumerate(huihui_deltas):
    ax2.text(i - width2/2, v - 0.015 if v < 0 else v + 0.005, f"{v:+.4f}", ha="center", fontsize=10)
for i, v in enumerate(heretic_deltas):
    ax2.text(i + width2/2, v - 0.015 if v < 0 else v + 0.005, f"{v:+.4f}", ha="center", fontsize=10)

plt.tight_layout()
out2 = RESULTS_DIR / "vantage_full_delta.png"
plt.savefig(out2, dpi=150, bbox_inches="tight")
print(f"Saved: {out2}")
