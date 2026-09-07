#!/usr/bin/env python3
"""
Generate a manual-review document (markdown) for Step 1: Correct -> Tool-Skip
transitions, for actual human reading/annotation.
"""

import argparse
import json
import random
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
    parser.add_argument("--sample", type=int, default=15)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", default="step1_manual_review.md")
    args = parser.parse_args()

    baseline = load_by_task_id(args.baseline)
    treatment = load_by_task_id(args.treatment)

    common_ids = sorted(set(baseline.keys()) & set(treatment.keys()))
    transitions = [
        tid for tid in common_ids
        if baseline[tid].get("classification") == "correct"
        and treatment[tid].get("classification") == "tool_skip"
    ]

    rng = random.Random(args.seed)
    sample = sorted(rng.sample(transitions, min(args.sample, len(transitions))))

    lines = []
    lines.append("# Step 1 Manual Verification: Correct -> Tool-Skip Transitions")
    lines.append("")
    lines.append(f"**Total transitions found:** {len(transitions)}")
    lines.append(f"**Sample reviewed manually:** {len(sample)} (randomly selected, seed={args.seed})")
    lines.append("")
    lines.append("For each case below: the question asked, what the baseline model did (correctly used")
    lines.append("the tool), and what the treatment model did instead (skipped it). A reviewer checkbox")
    lines.append("is included to record manual confirmation that this is a genuine skip, not a parsing artifact.")
    lines.append("")
    lines.append("---")
    lines.append("")

    for i, tid in enumerate(sample, 1):
        b_item = baseline[tid]
        t_item = treatment[tid]
        task = b_item.get("task", {})

        prompt = task.get("prompt", task.get("query", "N/A"))
        expected_tool = task.get("expected_tool_call", {}).get("name", "N/A")

        b_trace = b_item.get("agent_trace", {})
        t_trace = t_item.get("agent_trace", {})
        b_tool_calls = [c.get("name") for c in b_trace.get("tool_calls", [])]
        t_tool_calls = [c.get("name") for c in t_trace.get("tool_calls", [])]

        b_answer = b_item.get("agent_answer", "")
        t_answer = t_item.get("agent_answer", "")

        lines.append(f"## [{i}] task_id: `{tid}`")
        lines.append("")
        lines.append(f"**Question:** {prompt}")
        lines.append("")
        lines.append(f"**Expected tool:** `{expected_tool}`")
        lines.append("")
        lines.append(f"**Baseline (Original) — tool_calls: `{b_tool_calls}`**")
        lines.append(f"> {b_answer[:500]}")
        lines.append("")
        lines.append(f"**Treatment — tool_calls: `{t_tool_calls}`**")
        lines.append(f"> {t_answer[:500]}")
        lines.append("")
        lines.append("**Manual check:**")
        lines.append("- [ ] Confirmed: `tool_calls` genuinely empty in raw JSON (not a parsing miss)")
        lines.append("- [ ] Confirmed: treatment answer does NOT contain real tool-sourced data")
        lines.append("- [ ] Notes: _______________________________________________")
        lines.append("")
        lines.append("---")
        lines.append("")

    out_path = Path(args.out)
    out_path.write_text("\n".join(lines))
    print(f"Manual review document generated: {out_path}")
    print(f"Contains {len(sample)} sampled cases out of {len(transitions)} total transitions.")


if __name__ == "__main__":
    main()
