#!/usr/bin/env python3
import argparse
import json
import random

def load_correctness(path):
    out = {}
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            if r["status"] == "forced_correct":
                out[r["task_id"]] = 1
            elif r["status"] == "forced_wrong":
                out[r["task_id"]] = 0
    return out

def paired_bootstrap(baseline, treatment, ids, n_boot=10000, seed=42):
    rng = random.Random(seed)
    n = len(ids)

    def acc(source, sample_ids):
        return sum(source[i] for i in sample_ids) / len(sample_ids)

    diffs = []
    for _ in range(n_boot):
        sample = [ids[rng.randrange(n)] for _ in range(n)]
        diffs.append(acc(treatment, sample) - acc(baseline, sample))
    diffs.sort()
    lo, hi = diffs[int(0.025 * n_boot)], diffs[int(0.975 * n_boot)]
    point = acc(treatment, ids) - acc(baseline, ids)
    return point, lo, hi

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("original_jsonl")
    ap.add_argument("huihui_jsonl")
    ap.add_argument("--label", default="")
    args = ap.parse_args()

    orig = load_correctness(args.original_jsonl)
    hui = load_correctness(args.huihui_jsonl)

    common_ids = sorted(set(orig.keys()) & set(hui.keys()))
    print(f"Matched task_ids (both have determinate correct/wrong): {len(common_ids)}")
    print(f"  (Original had {len(orig)} determinate, Huihui had {len(hui)} determinate)")

    point, lo, hi = paired_bootstrap(orig, hui, common_ids)

    print(f"\n{'='*70}")
    print(f"PAIRED BOOTSTRAP: Forced Accuracy, Original vs Huihui ({args.label})")
    print(f"{'='*70}")
    print(f"Original forced accuracy: {sum(orig[i] for i in common_ids)/len(common_ids):.4f}")
    print(f"Huihui   forced accuracy: {sum(hui[i] for i in common_ids)/len(common_ids):.4f}")
    print(f"Paired difference (Huihui - Original): {point:+.4f}  (95% CI: [{lo:+.4f}, {hi:+.4f}])")
    sig = "SIGNIFICANT" if (lo > 0 or hi < 0) else "not significant"
    print(f"-> {sig}")

if __name__ == "__main__":
    main()
