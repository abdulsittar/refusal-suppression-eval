#!/bin/bash
# Usage: ./serve_checkpoint_tools.sh <checkpoint_dir_name> <tool_parser>
# tool_parser is typically "hermes" for Qwen3

if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: $0 <checkpoint_dir_name> <tool_parser>"
  echo "Example: $0 Qwen_Qwen3-4B-Instruct-2507 hermes"
  exit 1
fi

CKPT_DIR="${VANTAGE_ROOT:-$HOME/vantage}/checkpoints/$1"
TOOL_PARSER="$2"

python -m vllm.entrypoints.openai.api_server \
  --model "$CKPT_DIR" \
  --dtype bfloat16 \
  --max-model-len 32768 \
  --gpu-memory-utilization 0.90 \
  --enable-auto-tool-choice \
  --tool-call-parser "$TOOL_PARSER" \
  --port ${VLLM_PORT:-8000}
