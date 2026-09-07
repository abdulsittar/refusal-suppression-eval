#!/bin/bash
# run_all_canary_gates.sh
#
# Runs the ToolFailBench canary gate across all 6 VANTAGE checkpoints,
# one at a time: starts vLLM with tool-calling enabled, waits for readiness,
# runs the gate, saves output, tears down, moves to next.

set -uo pipefail

VANTAGE_ENV="$HOME/vantage-env"
EVAL_ENV="$HOME/vantage-eval-env"
CHECKPOINTS_DIR="${VANTAGE_ROOT:-$HOME/vantage}/checkpoints"
RESULTS_DIR="$HOME/vantage/results/canary_gates"
mkdir -p "$RESULTS_DIR"

declare -A CHECKPOINTS=(
  ["Qwen_Qwen3-4B-Instruct-2507"]="hermes"
  ["huihui-ai_Huihui-Qwen3-4B-Instruct-2507-abliterated"]="hermes"
  ["p-e-w_Qwen3-4B-Instruct-2507-heretic-v2"]="hermes"
  ["google_gemma-3-12b-it"]="hermes"
  ["huihui-ai_gemma-3-12b-it-abliterated"]="hermes"
  ["p-e-w_gemma-3-12b-it-heretic-v2"]="hermes"
)

ORDER=(
  "Qwen_Qwen3-4B-Instruct-2507"
  "huihui-ai_Huihui-Qwen3-4B-Instruct-2507-abliterated"
  "p-e-w_Qwen3-4B-Instruct-2507-heretic-v2"
  "google_gemma-3-12b-it"
  "huihui-ai_gemma-3-12b-it-abliterated"
  "p-e-w_gemma-3-12b-it-heretic-v2"
)

wait_for_server() {
  local expected_model="$1"
  local max_wait=300
  local waited=0
  echo "Waiting for vLLM server to serve: $expected_model"
  while [ "$waited" -lt "$max_wait" ]; do
    if curl -s http://localhost:${VLLM_PORT:-8000}/v1/models 2>/dev/null | grep -q "$expected_model"; then
      echo "Server ready, serving correct model."
      return 0
    fi
    sleep 5
    waited=$((waited + 5))
    echo "  ...still waiting (${waited}s elapsed)"
  done
  echo "TIMEOUT: server did not come up serving $expected_model within ${max_wait}s"
  return 1
}

kill_vllm() {
  pkill -9 -f "vllm.entrypoints.openai.api_server" 2>/dev/null || true
  sleep 3
}

SUMMARY_FILE="$RESULTS_DIR/all_gates_summary.txt"
echo "ToolFailBench Canary Gate Results - $(date)" > "$SUMMARY_FILE"
echo "==============================================" >> "$SUMMARY_FILE"

for ckpt_name in "${ORDER[@]}"; do
  tool_parser="${CHECKPOINTS[$ckpt_name]}"
  ckpt_path="$CHECKPOINTS_DIR/$ckpt_name"

  echo ""
  echo "=================================================================="
  echo "STARTING: $ckpt_name"
  echo "=================================================================="

  if [ ! -d "$ckpt_path" ]; then
    echo "SKIP: checkpoint directory not found: $ckpt_path"
    echo "$ckpt_name: SKIPPED (checkpoint dir not found)" >> "$SUMMARY_FILE"
    continue
  fi

  kill_vllm

  echo "Launching vLLM for $ckpt_name (tool_parser=$tool_parser)..."
  source "$VANTAGE_ENV/bin/activate"
  nohup python -m vllm.entrypoints.openai.api_server \
    --model "$ckpt_path" \
    --dtype bfloat16 \
    --max-model-len 32768 \
    --gpu-memory-utilization 0.90 \
    --enable-auto-tool-choice \
    --tool-call-parser "$tool_parser" \
    --port ${VLLM_PORT:-8000} \
    > "$RESULTS_DIR/${ckpt_name}_server.log" 2>&1 &

  SERVER_PID=$!
  deactivate

  if ! wait_for_server "$ckpt_path"; then
    echo "$ckpt_name: FAILED (server did not start - check $RESULTS_DIR/${ckpt_name}_server.log)" >> "$SUMMARY_FILE"
    kill_vllm
    continue
  fi

  echo "Running canary gate for $ckpt_name..."
  source "$EVAL_ENV/bin/activate"
  GATE_OUTPUT="$RESULTS_DIR/${ckpt_name}_gate_output.txt"
  python3 "$HOME/vantage/canary_gate.py" "$ckpt_path" -v > "$GATE_OUTPUT" 2>&1
  deactivate

  OVERALL_LINE=$(grep "OVERALL:" "$GATE_OUTPUT" || echo "OVERALL: UNKNOWN (check $GATE_OUTPUT)")
  STRUCT_LINE=$(grep "Structured tool calls:" "$GATE_OUTPUT" || echo "")
  RT_LINE=$(grep "Round-trip evidence" "$GATE_OUTPUT" || echo "")
  CTRL_LINE=$(grep "No-tool controls:" "$GATE_OUTPUT" || echo "")

  echo "$ckpt_name:" >> "$SUMMARY_FILE"
  echo "  $STRUCT_LINE" >> "$SUMMARY_FILE"
  echo "  $RT_LINE" >> "$SUMMARY_FILE"
  echo "  $CTRL_LINE" >> "$SUMMARY_FILE"
  echo "  $OVERALL_LINE" >> "$SUMMARY_FILE"
  echo "" >> "$SUMMARY_FILE"

  echo "Result for $ckpt_name:"
  echo "  $OVERALL_LINE"
  echo "Full output saved to: $GATE_OUTPUT"

  kill_vllm
done

echo ""
echo "=================================================================="
echo "ALL CHECKPOINTS PROCESSED"
echo "=================================================================="
echo ""
echo "Summary:"
cat "$SUMMARY_FILE"
echo ""
echo "Full summary saved to: $SUMMARY_FILE"
