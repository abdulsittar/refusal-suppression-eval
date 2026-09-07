import matplotlib
matplotlib.use("Agg")  # remove this line if you want it to pop up a window instead of saving to file
import matplotlib.pyplot as plt
import numpy as np

# Corrected pilot data (post guided-decoding fix), n=10 per benchmark
data = [
    {"family": "Gemma", "variant": "Original", "frr_refusal": 0.00, "mal_avg": 0.492, "mal_mc_pct": 0.10, "parse_err": 0},
    {"family": "Gemma", "variant": "Huihui",   "frr_refusal": 0.00, "mal_avg": 0.421, "mal_mc_pct": 0.00, "parse_err": 0},
    {"family": "Gemma", "variant": "Heretic",  "frr_refusal": 0.00, "mal_avg": 0.488, "mal_mc_pct": 0.10, "parse_err": 0},
    {"family": "Qwen",  "variant": "Original", "frr_refusal": 0.00, "mal_avg": 0.581, "mal_mc_pct": 0.20, "parse_err": 0},
    {"family": "Qwen",  "variant": "Huihui",   "frr_refusal": 0.00, "mal_avg": 0.393, "mal_mc_pct": 0.00, "parse_err": 0},
    {"family": "Qwen",  "variant": "Heretic",  "frr_refusal": 0.00, "mal_avg": 0.606, "mal_mc_pct": 0.20, "parse_err": 0},
]

variants = ["Original", "Huihui", "Heretic"]
gemma = [d for d in data if d["family"] == "Gemma"]
qwen = [d for d in data if d["family"] == "Qwen"]

x = np.arange(len(variants))
width = 0.35

fig, axes = plt.subplots(2, 2, figsize=(13, 10))
fig.suptitle("VANTAGE Pilot Results — Post Guided-Decoding Fix (n=10)", fontsize=14, fontweight="bold")

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
        ax.text(i - width/2, v + ylim[1]*0.02, fmt.format(v), ha="center", fontsize=9)
    for i, v in enumerate(qwen_vals):
        ax.text(i + width/2, v + ylim[1]*0.02, fmt.format(v), ha="center", fontsize=9)

# Panel 1: Malware Analysis avg_score
bar_panel(axes[0, 0],
          [d["mal_avg"] for d in gemma], [d["mal_avg"] for d in qwen],
          "Malware Analysis: Average Score (Jaccard)", "Avg Score", (0, 0.7))

# Panel 2: Exact match %
bar_panel(axes[0, 1],
          [d["mal_mc_pct"] for d in gemma], [d["mal_mc_pct"] for d in qwen],
          "Malware Analysis: Exact Match Rate", "Exact Match Rate", (0, 0.3),
          fmt="{:.0%}")

# Panel 3: Parsing errors
bar_panel(axes[1, 0],
          [d["parse_err"] for d in gemma], [d["parse_err"] for d in qwen],
          "Malware Analysis: Response Parsing Failures", "Parsing Errors (of 10)", (0, 11),
          fmt="{:.0f}/10")

# Panel 4: FRR refusal rate
bar_panel(axes[1, 1],
          [d["frr_refusal"] for d in gemma], [d["frr_refusal"] for d in qwen],
          "MITRE FRR: False Refusal Rate", "Refusal Rate", (0, 1.0),
          fmt="{:.0%}")

plt.tight_layout()
plt.savefig("vantage_pilot_comparison_v2.png", dpi=150, bbox_inches="tight")
print("Saved: vantage_pilot_comparison_v2.png")

# --- Second chart: within-family deltas (the key H2 finding) ---
fig2, ax2 = plt.subplots(figsize=(9, 6))
families = ["Gemma", "Qwen"]
huihui_deltas = [-0.072, -0.187]
heretic_deltas = [-0.005, 0.025]

x2 = np.arange(len(families))
width2 = 0.35
ax2.bar(x2 - width2/2, huihui_deltas, width2, label="Huihui", color="#DD8452")
ax2.bar(x2 + width2/2, heretic_deltas, width2, label="Heretic", color="#C44E52")
ax2.axhline(0, color="black", linewidth=0.8)
ax2.set_xticks(x2)
ax2.set_xticklabels(families)
ax2.set_ylabel("Δ avg_score vs Original")
ax2.set_title("Malware Analysis Score Change vs Original\n(Huihui consistently costs correctness; Heretic does not)",
               fontsize=12, fontweight="bold")
ax2.legend()
ax2.grid(axis="y", alpha=0.3)
for i, v in enumerate(huihui_deltas):
    ax2.text(i - width2/2, v - 0.015 if v < 0 else v + 0.005, f"{v:+.3f}", ha="center", fontsize=10)
for i, v in enumerate(heretic_deltas):
    ax2.text(i + width2/2, v - 0.015 if v < 0 else v + 0.005, f"{v:+.3f}", ha="center", fontsize=10)

plt.tight_layout()
plt.savefig("vantage_delta_comparison.png", dpi=150, bbox_inches="tight")
print("Saved: vantage_delta_comparison.png")

plt.show()  # comment this out if using the Agg backend / running headless