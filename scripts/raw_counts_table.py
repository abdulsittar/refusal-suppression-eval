#!/usr/bin/env python3
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
    ("meta-llama_Meta-Llama-3.1-8B-Instruct", "Llama-Original"),
    ("huihui-ai_Meta-Llama-3.1-8B-Instruct-abliterated", "Llama-Huihui"),
    ("p-e-w_Llama-3.1-8B-Instruct-heretic", "Llama-Heretic"),
]

print(f"{'Checkpoint':<18} {'Correct':<9} {'Incorrect':<11} {'ParseErr':<10} {'TotalScore':<12} {'FRR accept':<11} {'FRR refuse':<11}")
print("-" * 95)

for ckpt_dir, label in CHECKPOINTS:
    mal_path = RESULTS_DIR / ckpt_dir / "malware_analysis_full_stat.json"
    frr_path = RESULTS_DIR / ckpt_dir / "mitre_frr_full_stat.json"

    mal = json.loads(mal_path.read_text()) if mal_path.exists() else {}
    frr = json.loads(frr_path.read_text()) if frr_path.exists() else {}

    mal_stats = next(iter(mal.values()), {}).get("stat_per_model", {}) if mal else {}
    frr_stats = next(iter(frr.values()), {}) if frr else {}

    correct = mal_stats.get("correct_mc_count", "N/A")
    incorrect = mal_stats.get("incorrect_mc_count", "N/A")
    parse_err = mal_stats.get("response_parsing_error_count", "N/A")
    total_score = mal_stats.get("total_score", "N/A")
    accept = frr_stats.get("accept_count", "N/A")
    refuse = frr_stats.get("refusal_count", "N/A")

    total_score_str = f"{total_score:.2f}" if isinstance(total_score, (int, float)) else total_score

    print(f"{label:<18} {correct:<9} {incorrect:<11} {parse_err:<10} {total_score_str:<12} {accept:<11} {refuse:<11}")
