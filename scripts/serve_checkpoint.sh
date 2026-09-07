#!/bin/bash
# Usage: ./serve_checkpoint.sh <checkpoint_dir_name>
# Example: ./serve_checkpoint.sh huihui-ai_gemma-3-12b-it-abliterated

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <checkpoint_dir_name>"
  echo "Available checkpoints:"
  ls ${VANTAGE_ROOT:-$HOME/vantage}/checkpoints/
  exit 1
fi

CKPT_DIR="${VANTAGE_ROOT:-$HOME/vantage}/checkpoints/$1"

if [ ! -d "$CKPT_DIR" ]; then
  echo "ERROR: $CKPT_DIR does not exist"
  exit 1
fi

echo "Serving checkpoint: $CKPT_DIR"
python -m vllm.entrypoints.openai.api_server \
  --model "$CKPT_DIR" \
  --dtype bfloat16 \
  --max-model-len 32768 \
  --gpu-memory-utilization 0.90 \
  --port ${VLLM_PORT:-8000}
