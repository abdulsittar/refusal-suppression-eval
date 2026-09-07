#!/usr/bin/env python3
"""
Show the actual pilot questions/prompts and each checkpoint's raw response,
side by side, for either benchmark.

Usage:
    python3 view_pilot_examples.py mitre_frr
    python3 view_pilot_examples.py malware_analysis
    python3 view_pilot_examples.py malware_analysis --item 3
"""

import argparse
import json
from pathlib import Path

RESULTS_DIR = Path.home() / "vantage" / "results"

CHECKPOINTS = [
    ("google_gemma-3-12b-it", "Gemma-Original"),
    ("huihui-ai_gemma-3-12b-it-abliterated", "Gemma-Huihui"),
    ("p-e-w_gemma-3-12b-it-heretic-v2", "Gemma-Heretic"),
    ("Qwen_Qwen3-4B-Instruct-2507", "Qwen-Original"),
    ("huihui-ai_Huihui-Qwen3-4B-Instruct-2507-abliterated", "Qwen-Huihui"),
    ("p-e-w_Qwen3-4B-Instruct-2507-heretic-v2", "Qwen-Heretic"),
]


def load_json(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception as e:
        print(f"  WARNING: failed to parse {path}: {e}")
        return None


def truncate(s, n=500):
    s = s if isinstance(s, str) else str(s)
    return s if len(s) <= n else s[:n] + f"... [truncated, {len(s)} chars total]"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("benchmark", choices=["mitre_frr", "malware_analysis"])
    parser.add_argument("--item", type=int, default=None, help="Only show this prompt_id")
    parser.add_argument("--max-chars", type=int, default=500, help="Truncate long fields")
    args = parser.parse_args()

    responses_file = f"{args.benchmark}_pilot_responses.json"

    all_data = {}
    for ckpt_dir, label in CHECKPOINTS:
        data = load_json(RESULTS_DIR / ckpt_dir / responses_file)
        if data is None:
            print(f"(no data for {label} — skipping)")
            continue
        by_id = {item["prompt_id"]: item for item in data}
        all_data[label] = by_id

    if not all_data:
        print("No data found for any checkpoint.")
        return

    first_label = next(iter(all_data))
    prompt_ids = sorted(all_data[first_label].keys())
    if args.item is not None:
        prompt_ids = [pid for pid in prompt_ids if pid == args.item]

    for pid in prompt_ids:
        print("\n" + "#" * 110)
        print(f"# ITEM {pid}")
        print("#" * 110)

        sample = all_data[first_label].get(pid, {})
        if args.benchmark == "mitre_frr":
            prompt_text = sample.get("test_case_prompt", sample.get("prompt", ""))
            print(f"\nPROMPT:\n{truncate(prompt_text, args.max_chars)}")
        else:
            question = sample.get("question", "")
            options = sample.get("options", [])
            correct = sample.get("correct_options", [])
            print(f"\nQUESTION:\n{truncate(question, args.max_chars)}")
            print(f"\nOPTIONS: {options}")
            print(f"CORRECT ANSWER(S): {correct}")

        print("\n" + "-" * 110)
        for _, label in CHECKPOINTS:
            if label not in all_data or pid not in all_data[label]:
                print(f"[{label}] -- no data --")
                continue
            item = all_data[label][pid]
            resp = item.get("response", "")
            print(f"\n[{label}] RESPONSE:")
            print(truncate(resp, args.max_chars))
        print()


if __name__ == "__main__":
    main()
