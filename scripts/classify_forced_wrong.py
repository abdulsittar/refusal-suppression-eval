#!/usr/bin/env python3
import argparse
import json

def extract_values(obj):
    vals = set()
    if isinstance(obj, dict):
        for v in obj.values():
            vals |= extract_values(v)
    elif isinstance(obj, list):
        for v in obj:
            vals |= extract_values(v)
    else:
        s = str(obj).strip()
        if s and len(s) > 1:
            vals.add(s)
    return vals

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("forced_jsonl")
    ap.add_argument("original_results_json")
    args = ap.parse_args()

    d = json.load(open(args.original_results_json))
    items = d if isinstance(d, list) else list(d.values())
    mock_by_id = {i["task"]["task_id"]: i["task"].get("mock_tool_return", {}) for i in items}

    counts = {"result_ignore": 0, "output_fabrication": 0, "ambiguous": 0}
    examples = {"result_ignore": [], "output_fabrication": [], "ambiguous": []}

    with open(args.forced_jsonl) as f:
        for line in f:
            r = json.loads(line)
            if r["status"] != "forced_wrong":
                continue
            task_id = r["task_id"]
            answer = r.get("answer", "") or ""
            mock = mock_by_id.get(task_id, {})
            tool_values = extract_values(mock)
            uses_real_data = any(val in answer for val in tool_values if len(val) > 2)
            category = "output_fabrication" if uses_real_data else "result_ignore"
            counts[category] += 1
            if len(examples[category]) < 3:
                examples[category].append((task_id, answer[:150]))

    total = sum(counts.values())
    print(f"Classified {total} forced_wrong items:\n")
    for cat, n in counts.items():
        pct = n / total * 100 if total else 0
        print(f"  {cat}: {n} ({pct:.1f}%)")
        for tid, ans in examples[cat]:
            print(f"    [{tid}] {ans}")
        print()

if __name__ == "__main__":
    main()
