#!/usr/bin/env python3
"""
Step 1: Manually-inspectable Correct -> Tool-Skip transitions,
Original vs Huihui (or any two result files).

Usage:
    python3 verify_transitions.py <baseline_result.json> <treatment_result.json> \
        --from correct --to tool_skip [--limit 30] [--full]
"""

import argparse
import json
from pathlib import Path


def load_by_task_id(path):
    d = json.load(open(path))
    items = d if isinstance(d, list) else list(d.values())
    by_id = {}
    for item in items:
        task = item.get("task", {})
        tid = (
            item.get("task_id")
            or task.get("task_id")
            or task.get("id")
            or item.get("id")
        )
        by_id[tid] = item
    return by_id


def get_classification(item):
    return item.get("classification", "UNKNOWN")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline")
    parser.add_argument("treatment")
    parser.add_argument("--from", dest="from_cls", default="correct")
    parser.add_argument("--to", dest="to_cls", default="tool_skip")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--full", action="store_true", help="Show full agent_trace/answer, not truncated")
    args = parser.parse_args()

    baseline = load_by_task_id(args.baseline)
    treatment = load_by_task_id(args.treatment)

    common_ids = set(baseline.keys()) & set(treatment.keys())
    print(f"Baseline items: {len(baseline)}, Treatment items: {len(treatment)}, Common: {len(common_ids)}")

    transitions = []
    for tid in common_ids:
        b_cls = get_classification(baseline[tid])
        t_cls = get_classification(treatment[tid])
        if b_cls == args.from_cls and t_cls == args.to_cls:
            transitions.append(tid)

    print(f"\nFound {len(transitions)} transitions: {args.from_cls} -> {args.to_cls}")
    print(f"Showing up to {args.limit}\n")
    print("=" * 100)

    for i, tid in enumerate(sorted(transitions)[: args.limit]):
        b_item = baseline[tid]
        t_item = treatment[tid]

        b_trace = b_item.get("agent_trace", {})
        t_trace = t_item.get("agent_trace", {})

        b_tool_calls = [c.get("name") for c in b_trace.get("tool_calls", [])]
        t_tool_calls = [c.get("name") for c in t_trace.get("tool_calls", [])]

        b_answer = b_item.get("agent_answer", "")
        t_answer = t_item.get("agent_answer", "")

        task = b_item.get("task", {})
        prompt = task.get("prompt", task.get("query", task.get("user_message", "N/A")))
        expected_tool = task.get("expected_tool_call", {}).get("name", "N/A")

        n = 400 if not args.full else 100000

        print(f"[{i+1}] task_id={tid}")
        print(f"  PROMPT: {str(prompt)[:n]}")
        print(f"  EXPECTED TOOL: {expected_tool}")
        print(f"  BASELINE  -> tool_calls={b_tool_calls}  classification={get_classification(b_item)}")
        print(f"    answer: {str(b_answer)[:n]}")
        print(f"  TREATMENT -> tool_calls={t_tool_calls}  classification={get_classification(t_item)}")
        print(f"    answer: {str(t_answer)[:n]}")
        print("-" * 100)


if __name__ == "__main__":
    main()
