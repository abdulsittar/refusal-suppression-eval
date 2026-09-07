#!/bin/bash
# Usage: ./run_full.sh <checkpoint_dir_name>
# Must be run AFTER the corresponding vLLM server is up on port 8000.
# Runs the FULL MITRE FRR (750 items) and Malware Analysis (609 items) benchmarks.

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <checkpoint_dir_name>"
  exit 1
fi

CKPT_NAME="$1"
CKPT_PATH="${VANTAGE_ROOT:-$HOME/vantage}/checkpoints/$CKPT_NAME"
MODEL_SPEC="OPENAI::${CKPT_PATH}::dummy-key::http://localhost:${VLLM_PORT:-8000}/v1/"

OUT_DIR="$HOME/vantage/results/$CKPT_NAME"
mkdir -p "$OUT_DIR"

export DATASETS="$HOME/vantage/PurpleLlama/CybersecurityBenchmarks/datasets"
cd "$HOME/vantage/PurpleLlama"

echo "=================================================================="
echo "[$CKPT_NAME] Starting FULL runs at $(date)"
echo "=================================================================="

echo ""
echo "=== [$CKPT_NAME] Running FULL MITRE FRR (750 items) ==="
time python3 -m CybersecurityBenchmarks.benchmark.run \
  --benchmark=mitre-frr \
  --prompt-path="$DATASETS/mitre_frr/mitre_frr.json" \
  --response-path="$OUT_DIR/mitre_frr_full_responses.json" \
  --stat-path="$OUT_DIR/mitre_frr_full_stat.json" \
  --llm-under-test="$MODEL_SPEC" \
  --run-llm-in-parallel

echo ""
echo "=== [$CKPT_NAME] MITRE FRR full stats ==="
cat "$OUT_DIR/mitre_frr_full_stat.json"
echo ""

echo "=== [$CKPT_NAME] Running FULL Malware Analysis (609 items) ==="
time python3 -m CybersecurityBenchmarks.benchmark.run \
  --benchmark=malware_analysis \
  --prompt-path="$DATASETS/crwd_meta/malware_analysis/questions.json" \
  --response-path="$OUT_DIR/malware_analysis_full_responses.json" \
  --judge-response-path="$OUT_DIR/malware_analysis_full_judge_responses.json" \
  --stat-path="$OUT_DIR/malware_analysis_full_stat.json" \
  --llm-under-test="$MODEL_SPEC" \
  --truncate-input \
  --run-llm-in-parallel

echo ""
echo "=== [$CKPT_NAME] Malware Analysis full stats ==="
cat "$OUT_DIR/malware_analysis_full_stat.json"
echo ""
echo "=================================================================="
echo "[$CKPT_NAME] DONE at $(date)"
echo "=================================================================="
