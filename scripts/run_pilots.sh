#!/bin/bash
# Usage: ./run_pilots.sh <checkpoint_dir_name>
# Example: ./run_pilots.sh huihui-ai_gemma-3-12b-it-abliterated
# Must be run AFTER the corresponding vLLM server is up on port 8000.

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

echo "=== [$CKPT_NAME] Running MITRE FRR pilot ==="
time python3 -m CybersecurityBenchmarks.benchmark.run \
  --benchmark=mitre-frr \
  --prompt-path="$HOME/vantage/results/mitre_frr_pilot10.json" \
  --response-path="$OUT_DIR/mitre_frr_pilot_responses.json" \
  --stat-path="$OUT_DIR/mitre_frr_pilot_stat.json" \
  --llm-under-test="$MODEL_SPEC" \
  --run-llm-in-parallel

echo ""
echo "=== [$CKPT_NAME] MITRE FRR pilot stats ==="
cat "$OUT_DIR/mitre_frr_pilot_stat.json"
echo ""

echo "=== [$CKPT_NAME] Running Malware Analysis pilot ==="
time python3 -m CybersecurityBenchmarks.benchmark.run \
  --benchmark=malware_analysis \
  --prompt-path="$HOME/vantage/results/malware_analysis_pilot10.json" \
  --response-path="$OUT_DIR/malware_analysis_pilot_responses.json" \
  --judge-response-path="$OUT_DIR/malware_analysis_pilot_judge_responses.json" \
  --stat-path="$OUT_DIR/malware_analysis_pilot_stat.json" \
  --llm-under-test="$MODEL_SPEC" \
  --truncate-input \
  --run-llm-in-parallel

echo ""
echo "=== [$CKPT_NAME] Malware Analysis pilot stats ==="
cat "$OUT_DIR/malware_analysis_pilot_stat.json"
echo ""
echo "=== [$CKPT_NAME] DONE ==="
