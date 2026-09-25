#!/usr/bin/env python3
import argparse
import json
import random

def load_classifications(path):
    d = json.load(open(path))
    items = d if isinstance(d, list) else list(d.values())
    out = {}
    for i in items:
        t = i.get("task", {})
        if t.get("evaluation_criteria", {}).get("tool_must_be_called"):
            out[t["task_id"]] = i.get("classification")
    return out

def paired_bootstrap_rate(baseline, treatment, ids, is_target_fn, n_boot=10000, seed=42):
    rng = random.Random(seed)
    n = len(ids)

    def rate(source, sample_ids):
        return sum(1 for i in sample_ids if is_target_fn(source[i])) / len(sample_ids)

    diffs = []
    for _ in range(n_boot):
        sample = [ids[rng.randrange(n)] for _ in range(n)]
        diffs.append(rate(treatment, sample) - rate(baseline, sample))
    diffs.sort()
    lo, hi = diffs[int(0.025 * n_boot)], diffs[int(0.975 * n_boot)]
    point = rate(treatment, ids) - rate(baseline, ids)
    return point, lo, hi

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("baseline_json")
    ap.add_argument("treatment_json")
    ap.add_argument("--label", default="")
    args = ap.parse_args()

    base = load_classifications(args.baseline_json)
    treat = load_classifications(args.treatment_json)
    common_ids = sorted(set(base.keys()) & set(treat.keys()))

    print(f"\n{'='*70}")
    print(f"STEP 4 (4-DOMAIN): PAIRED STATISTICS -- Original vs {args.label}")
    print(f"(n={len(common_ids)} tool-required tasks)")
    print(f"{'='*70}\n")

    tsr_point, tsr_lo, tsr_hi = paired_bootstrap_rate(
        base, treat, common_ids, lambda c: c == "tool_skip"
    )
    print("Tool-Skip Rate (TSR):")
    print(f"  Paired difference: {tsr_point:+.4f}  (95% bootstrap CI: [{tsr_lo:+.4f}, {tsr_hi:+.4f}])")
    sig = "CI excludes zero: statistically significant difference" if (tsr_lo > 0 or tsr_hi < 0) else "CI includes zero: not statistically significant"
    print(f"  -> {sig}\n")

    ctur_point, ctur_lo, ctur_hi = paired_bootstrap_rate(
        base, treat, common_ids, lambda c: c == "correct"
    )
    print("Clean Tool-Use Rate (CTUR):")
    print(f"  Paired difference: {ctur_point:+.4f}  (95% bootstrap CI: [{ctur_lo:+.4f}, {ctur_hi:+.4f}])")
    sig = "CI excludes zero: statistically significant difference" if (ctur_lo > 0 or ctur_hi < 0) else "CI includes zero: not statistically significant"
    print(f"  -> {sig}\n")

    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
