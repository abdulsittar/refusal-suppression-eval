#!/bin/bash
cd ~/vantage/ToolFailBench
for fam in llama gemma qwen; do
  for v in original huihui heretic; do
    name=$fam-$v
    f=models/configs/vantage/$name.yaml
    path=$(awk '/^hf_model_id:/{print $2}' "$f")
    if [ -z "$path" ]; then echo "SKIP $name (no path)"; continue; fi
    echo "=== $name ($path)"
    python3 refusal_eval.py run --model-name $name --model-path "$path" \
        --prompts "$MITRE" --field mutated_prompt --strip-wrapper \
        --n 150 --seed 0 --out results/refusal_${fam}_stripped/
  done
done
echo ALL DONE
