#!/usr/bin/env python3
"""
Step 3: Item-level transition analysis.

For each task_id, compare classification under Original vs. a treatment
(Huihui or Heretic), and build a full transition matrix.
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def load_by_task_id(path):
    d = json.load(open(path))
    items = d if isinstance(d, list) else list(d.values())
    by_id = {}
    for item in items:
        task = item.get("task", {})
        tid = task.get("task_id", task.get("id"))
        by_id[tid] = item
    return by_id


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline")
    parser.add_argument("treatment")
    parser.add_argument("--label", default="Treatment")
    parser.add_argument("--out-prefix", default=None)
    args = parser.parse_args()

    baseline = load_by_task_id(args.baseline)
    treatment = load_by_task_id(args.treatment)

    common_ids = sorted(set(baseline.keys()) & set(treatment.keys()))
    print(f"Common task_ids: {len(common_ids)} (baseline={len(baseline)}, treatment={len(treatment)})")

    transition_counts = Counter()
    transition_examples = defaultdict(list)

    for tid in common_ids:
        b_cls = baseline[tid].get("classification", "UNKNOWN")
        t_cls = treatment[tid].get("classification", "UNKNOWN")
        key = (b_cls, t_cls)
        transition_counts[key] += 1
        transition_examples[key].append(tid)

    all_classes = sorted(set([k[0] for k in transition_counts] + [k[1] for k in transition_counts]))

    print(f"\n{'=' * 90}")
    print(f"FULL TRANSITION MATRIX: Original -> {args.label}")
    print(f"{'=' * 90}")
    print(f"{'FROM \\ TO':<18}" + "".join(f"{c:<15}" for c in all_classes))
    for from_cls in all_classes:
        row = f"{from_cls:<18}"
        for to_cls in all_classes:
            count = transition_counts.get((from_cls, to_cls), 0)
            row += f"{count:<15}"
        print(row)

    print(f"\n{'=' * 90}")
    print("KEY TRANSITIONS OF INTEREST")
    print(f"{'=' * 90}")

    key_pairs = [
        ("correct", "tool_skip", "Correct -> Tool-Skip (net harm from suppression)"),
        ("tool_skip", "correct", "Tool-Skip -> Correct (net benefit/unlock)"),
        ("correct", "result_ignore", "Correct -> Result-Ignore"),
        ("correct", "wrong_answer", "Correct -> Wrong-Answer"),
        ("tool_skip", "tool_skip", "Tool-Skip -> Tool-Skip (no change, still skipping)"),
        ("correct", "correct", "Correct -> Correct (no change, stayed correct)"),
    ]

    for from_cls, to_cls, description in key_pairs:
        count = transition_counts.get((from_cls, to_cls), 0)
        print(f"  {description}: {count}")

    net_skip_harm = transition_counts.get(("correct", "tool_skip"), 0) - transition_counts.get(("tool_skip", "correct"), 0)
    print(f"\n  NET Correct<->Tool-Skip movement: {net_skip_harm:+d} "
          f"({'more harm than benefit' if net_skip_harm > 0 else 'more benefit than harm' if net_skip_harm < 0 else 'balanced'})")

    out_prefix = args.out_prefix or f"step3_transitions_{args.label.lower()}"
    out_path = Path(args.baseline).parent / f"{out_prefix}.json"
    with open(out_path, "w") as f:
        json.dump(
            {
                "baseline_file": args.baseline,
                "treatment_file": args.treatment,
                "label": args.label,
                "common_task_count": len(common_ids),
                "transition_matrix": {f"{k[0]}->{k[1]}": v for k, v in transition_counts.items()},
                "transition_examples": {f"{k[0]}->{k[1]}": v for k, v in transition_examples.items()},
            },
            f,
            indent=2,
        )
    print(f"\nFull details saved to: {out_path}")


if __name__ == "__main__":
    main()

