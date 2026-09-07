#!/usr/bin/env python3
"""
Step 2: Extract the FULL official ToolFailBench metrics (CTUR, TSR, RIR, OFR,
UTR, CTRL-Acc) for all three Qwen checkpoints, using the benchmark's own
evaluation/metrics.py -- not a reimplementation.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from evaluation.metrics import compute_all_metrics, compute_metrics_by_domain

RESULTS_DIR = Path("results/v5")

def latest_result_file(prefix: str) -> Path:
    """Find the most recent result JSON matching '<prefix>_*.json' in RESULTS_DIR."""
    candidates = sorted(RESULTS_DIR.glob(f"{prefix}_*.json"), reverse=True)
    if not candidates:
        raise FileNotFoundError(
            f"No result file found matching '{prefix}_*.json' in {RESULTS_DIR}. "
            f"Run scripts/run_eval.py (via ToolFailBench) first."
        )
    return candidates[0]


CHECKPOINTS = {
    "Qwen-Original": latest_result_file("qwen-original"),
    "Qwen-Huihui": latest_result_file("qwen-huihui"),
    "Qwen-Heretic": latest_result_file("qwen-heretic"),
}


def load_results(path):
    d = json.load(open(path))
    return d if isinstance(d, list) else list(d.values())


def main():
    all_metrics = {}

    for label, path in CHECKPOINTS.items():
        if not path.exists():
            print(f"WARNING: missing file for {label}: {path}")
            continue
        results = load_results(path)
        metrics = compute_all_metrics(results)
        all_metrics[label] = metrics

    print("\n" + "=" * 100)
    print("STEP 2: OFFICIAL ToolFailBench METRICS (via evaluation/metrics.py)")
    print("=" * 100)

    metric_keys = list(next(iter(all_metrics.values())).keys()) if all_metrics else []

    header = f"{'Metric':<25}" + "".join(f"{label:<18}" for label in all_metrics.keys())
    print(header)
    print("-" * 100)
    for key in metric_keys:
        row = f"{key:<25}"
        for label in all_metrics.keys():
            val = all_metrics[label].get(key)
            if isinstance(val, float):
                row += f"{val:.4f}".ljust(18)
            else:
                row += f"{str(val)}".ljust(18)
        print(row)

    print("=" * 100)

    out_path = RESULTS_DIR / "step2_official_metrics.json"
    with open(out_path, "w") as f:
        json.dump(all_metrics, f, indent=2)
    print(f"\nSaved: {out_path}")

    md_path = RESULTS_DIR / "step2_official_metrics.md"
    with open(md_path, "w") as f:
        f.write("| Metric | " + " | ".join(all_metrics.keys()) + " |\n")
        f.write("|---|" + "---|" * len(all_metrics) + "\n")
        for key in metric_keys:
            row = [key]
            for label in all_metrics.keys():
                val = all_metrics[label].get(key)
                row.append(f"{val:.4f}" if isinstance(val, float) else str(val))
            f.write("| " + " | ".join(row) + " |\n")
    print(f"Saved: {md_path}")


if __name__ == "__main__":
    main()
