#!/bin/bash
cd ~/vantage/ToolFailBench
for spec in "gemma-original:google_gemma-3-12b-it" \
            "gemma-huihui:huihui-ai_gemma-3-12b-it-abliterated" \
            "gemma-heretic:p-e-w_gemma-3-12b-it-heretic-v2"; do
  name=${spec%%:*}; dir=${spec#*:}
  python3 refusal_eval.py run --model-name $name \
      --model-path /home/abduls/vantage/checkpoints/$dir \
      --prompts "$MITRE" --field mutated_prompt --strip-wrapper \
      --n 150 --seed 0 --out results/refusal_gemma_stripped/
done
echo GEMMA DONE
