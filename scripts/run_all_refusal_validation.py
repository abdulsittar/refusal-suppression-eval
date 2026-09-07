import os
import csv
import json
import subprocess
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import RESULTS_DIR

BASE = str(RESULTS_DIR)
VALIDATOR = str(Path(__file__).parent / "validate_gemma_refusals.py")

MODELS = {
    "Gemma-3-12B-IT": "google_gemma-3-12b-it",
    "Gemma-3-12B-IT-Abliterated": "huihui-ai_gemma-3-12b-it-abliterated",
    "Gemma-3-12B-IT-Heretic-v2": "p-e-w_gemma-3-12b-it-heretic-v2",

    "Qwen3-4B-Instruct-2507": "Qwen_Qwen3-4B-Instruct-2507",
    "Qwen3-4B-Instruct-2507-Abliterated":
        "huihui-ai_Huihui-Qwen3-4B-Instruct-2507-abliterated",
    "Qwen3-4B-Instruct-2507-Heretic-v2":
        "p-e-w_Qwen3-4B-Instruct-2507-heretic-v2",
}

DATASETS = {
    "MITRE_FRR": "mitre_frr_full_responses.json",
    "MALWARE_ANALYSIS": "malware_analysis_full_responses.json",
}


def run_validator(model_name, model_dir, dataset_name, filename):

    input_file = os.path.join(
        BASE,
        model_dir,
        filename
    )

    output_dir = os.path.join(
        BASE,
        "all_refusal_validation",
        model_dir,
        dataset_name
    )

    os.makedirs(output_dir, exist_ok=True)

    print("\n" + "=" * 100)
    print(f"MODEL   : {model_name}")
    print(f"DATASET : {dataset_name}")
    print(f"INPUT   : {input_file}")
    print(f"OUTPUT  : {output_dir}")
    print("=" * 100)

    if not os.path.exists(input_file):
        print(f"ERROR: File does not exist: {input_file}")
        return False

    cmd = [
        "python3",
        VALIDATOR,
        "--input",
        input_file,
        "--output-dir",
        output_dir,
    ]

    result = subprocess.run(cmd)

    if result.returncode != 0:
        print(
            f"ERROR validating {model_name} / {dataset_name}"
        )
        return False

    return True


def main():

    print("=" * 100)
    print("RUNNING STRICT REFUSAL VALIDATION")
    print("=" * 100)

    total = len(MODELS) * len(DATASETS)

    print(f"Models   : {len(MODELS)}")
    print(f"Datasets : {len(DATASETS)}")
    print(f"Total runs: {total}")
    print()

    successful = 0
    failed = 0

    for model_name, model_dir in MODELS.items():

        for dataset_name, filename in DATASETS.items():

            success = run_validator(
                model_name,
                model_dir,
                dataset_name,
                filename
            )

            if success:
                successful += 1
            else:
                failed += 1

    print("\n" + "=" * 100)
    print("BATCH VALIDATION COMPLETE")
    print("=" * 100)

    print(f"Successful runs: {successful}")
    print(f"Failed runs    : {failed}")
    print(f"Total runs     : {total}")

    print()
    print(
        "Results directory:"
    )
    print(
        os.path.join(
            BASE,
            "all_refusal_validation"
        )
    )


if __name__ == "__main__":
    main()
