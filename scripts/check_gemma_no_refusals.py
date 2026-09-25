#!/usr/bin/env python3
"""
Show N sample responses from a checkpoint's MITRE FRR full run,
to manually inspect why it isn't refusing.

Usage:
    python3 check_gemma_no_refusals.py <checkpoint_dir_name> [num_samples]
"""

import json
import sys
import random
from pathlib import Path

RESULTS_DIR = Path.home() / "vantage" / "results"


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 check_gemma_no_refusals.py <checkpoint_dir_name> [num_samples]")
        sys.exit(1)

    ckpt_name = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    path = RESULTS_DIR / ckpt_name / "mitre_frr_full_responses.json"
    if not path.exists():
        print(f"No file found at {path}")
        sys.exit(1)

    data = json.loads(path.read_text())
    print(f"Total items: {len(data)}\n")

    sample = random.sample(data, min(n, len(data)))

    for item in sample:
        prompt = item.get("test_case_prompt", item.get("prompt", ""))
        resp = item.get("response", "")
        print("=" * 100)
        print(f"prompt_id: {item.get('prompt_id')}")
        print(f"PROMPT:\n{prompt[:400]}")
        print(f"\nRESPONSE:\n{resp[:500]}")
        print()


if __name__ == "__main__":
    main()
