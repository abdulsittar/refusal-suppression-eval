"""
Central configuration for the VANTAGE refusal-suppression study scripts.
Reads paths from environment variables (with sensible defaults) so the
repo works on any machine without hardcoded paths.

Set these in your shell or in a .env file (see .env.example):
  VANTAGE_ROOT              - root directory for checkpoints/results (default: ~/vantage)
  VLLM_BASE_URL             - base URL of the running vLLM server (default: http://localhost:8000/v1)
"""

import os
from pathlib import Path

VANTAGE_ROOT = Path(os.environ.get("VANTAGE_ROOT", Path.home() / "vantage"))
CHECKPOINTS_DIR = VANTAGE_ROOT / "checkpoints"
RESULTS_DIR = VANTAGE_ROOT / "results"
VLLM_BASE_URL = os.environ.get("VLLM_BASE_URL", "http://localhost:8000/v1")

# The six checkpoints used in this study.
# Update these to match your own local checkpoint directory names.
CHECKPOINTS = {
    "gemma-original": "google_gemma-3-12b-it",
    "gemma-huihui": "huihui-ai_gemma-3-12b-it-abliterated",
    "gemma-heretic": "p-e-w_gemma-3-12b-it-heretic-v2",
    "qwen-original": "Qwen_Qwen3-4B-Instruct-2507",
    "qwen-huihui": "huihui-ai_Huihui-Qwen3-4B-Instruct-2507-abliterated",
    "qwen-heretic": "p-e-w_Qwen3-4B-Instruct-2507-heretic-v2",
}


def checkpoint_path(key: str) -> Path:
    """Resolve a short checkpoint key (e.g. 'qwen-original') to its full local path."""
    if key not in CHECKPOINTS:
        raise ValueError(f"Unknown checkpoint key: {key}. Valid keys: {list(CHECKPOINTS.keys())}")
    return CHECKPOINTS_DIR / CHECKPOINTS[key]
