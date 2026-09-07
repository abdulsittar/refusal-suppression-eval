#!/usr/bin/env python3
"""
Step 4: Paired statistics for ToolFailBench comparisons.
Bootstrap 95% CI on paired TSR/CTUR differences, plus McNemar's exact test
on Correct<->Tool-Skip discordant pairs.
"""

import argparse
import json
import random
from pathlib import Path

try:
    from scipy.stats import binomtest
    HAVE_SCIPY = True
except ImportError:
    HAVE_SCIPY = False


def load_by_task_id(path):
    d = json.load(open(path))
    items = d if isinstance(d, list) else list(d.values())
    by_id = {}
    for item in items:
        task = item.get("task", {})
        tid = task.get("task_id", task.get("id"))
        by_id[tid] = item
    return by_id


def is_tool_required(item):
    return item.get("task", {}).get("evaluation_criteria", {}).get("tool_must_be_called", False)


def tsr_for_subset(baseline, treatment, task_ids, use_treatment=True):
    source = treatment if use_treatment else baseline
    required = [tid for tid in task_ids if is_tool_required(baseline[tid])]
    if not required:
        return 0.0
    skips = sum(1 for tid in required if source[tid].get("classification") == "tool_skip")
    return skips / len(required)


def ctur_for_subset(baseline, treatment, task_ids, use_treatment=True):
    source = treatment if use_treatment else baseline
    required = [tid for tid in task_ids if is_tool_required(baseline[tid])]
    if not required:
        return 0.0
    clean = sum(1 for tid in required if source[tid].get("classification") == "correct")
    return clean / len(required)


def bootstrap_paired_diff(baseline, treatment, task_ids, metric_fn, n_boot=10000, seed=42):
    rng = random.Random(seed)
    n = len(task_ids)
    diffs = []
    for _ in range(n_boot):
        sample = [task_ids[rng.randrange(n)] for _ in range(n)]
        treat_val = metric_fn(baseline, treatment, sample, use_treatment=True)
        base_val = metric_fn(baseline, treatment, sample, use_treatment=False)
        diffs.append(treat_val - base_val)
    diffs.sort()
    lo = diffs[int(0.025 * n_boot)]
    hi = diffs[int(0.975 * n_boot)]
    point = metric_fn(baseline, treatment, task_ids, use_treatment=True) - metric_fn(baseline, treatment, task_ids, use_treatment=False)
    return point, lo, hi


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    if HAVE_SCIPY:
        result = binomtest(min(b, c), n, 0.5, alternative="two-sided")
        return result.pvalue
    else:
        import math
        stat = (abs(b - c) - 1) ** 2 / n
        p = math.erfc(math.sqrt(stat / 2))
        return p


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline")
    parser.add_argument("treatment")
    parser.add_argument("--label", default="Treatment")
    parser.add_argument("--n-boot", type=int, default=10000)
    args = parser.parse_args()

    baseline = load_by_task_id(args.baseline)
    treatment = load_by_task_id(args.treatment)
    common_ids = sorted(set(baseline.keys()) & set(treatment.keys()))

    print(f"\n{'=' * 90}")
    print(f"STEP 4: PAIRED STATISTICS -- Original vs {args.label}  (n={len(common_ids)} paired tasks)")
    print(f"{'=' * 90}")

    tsr_point, tsr_lo, tsr_hi = bootstrap_paired_diff(baseline, treatment, common_ids, tsr_for_subset, n_boot=args.n_boot)
    print(f"\nTool-Skip Rate (TSR):")
    print(f"  Paired difference: {tsr_point:+.4f}  (95% bootstrap CI: [{tsr_lo:+.4f}, {tsr_hi:+.4f}])")
    if tsr_lo > 0 or tsr_hi < 0:
        print(f"  -> CI excludes zero: statistically significant difference")
    else:
        print(f"  -> CI includes zero: not statistically significant at 95% level")

    ctur_point, ctur_lo, ctur_hi = bootstrap_paired_diff(baseline, treatment, common_ids, ctur_for_subset, n_boot=args.n_boot)
    print(f"\nClean Tool-Use Rate (CTUR):")
    print(f"  Paired difference: {ctur_point:+.4f}  (95% bootstrap CI: [{ctur_lo:+.4f}, {ctur_hi:+.4f}])")
    if ctur_lo > 0 or ctur_hi < 0:
        print(f"  -> CI excludes zero: statistically significant difference")
    else:
        print(f"  -> CI includes zero: not statistically significant at 95% level")

    b = sum(1 for tid in common_ids
            if baseline[tid].get("classification") == "correct"
            and treatment[tid].get("classification") == "tool_skip")
    c = sum(1 for tid in common_ids
            if baseline[tid].get("classification") == "tool_skip"
            and treatment[tid].get("classification") == "correct")

    p_value = mcnemar_exact(b, c)
    print(f"\nMcNemar's exact test (Correct <-> Tool-Skip discordant pairs):")
    print(f"  Correct->Tool-Skip (b): {b}")
    print(f"  Tool-Skip->Correct (c): {c}")
    print(f"  p-value: {p_value:.6f}")
    if p_value < 0.05:
        print(f"  -> SIGNIFICANT at p<0.05: the direction of change (b vs c) is unlikely due to chance")
    else:
        print(f"  -> NOT significant at p<0.05")

    print(f"\n{'=' * 90}\n")

    out_path = Path(args.baseline).parent / f"step4_paired_stats_{args.label.lower()}.json"
    with open(out_path, "w") as f:
        json.dump(
            {
                "label": args.label,
                "n_paired_tasks": len(common_ids),
                "tsr_diff": tsr_point,
                "tsr_ci_95": [tsr_lo, tsr_hi],
                "ctur_diff": ctur_point,
                "ctur_ci_95": [ctur_lo, ctur_hi],
                "mcnemar_b_correct_to_skip": b,
                "mcnemar_c_skip_to_correct": c,
                "mcnemar_p_value": p_value,
            },
            f,
            indent=2,
        )
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
