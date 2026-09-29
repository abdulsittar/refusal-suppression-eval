# Refusal rate on harmful MITRE prompts (CyberSecEval)

n=150 per model, seed=0, greedy decoding, max_new_tokens=200, CyberSecEval scaffold
stripped (`--strip-wrapper`). Classifier: regex-based refusal/partial/compliance,
audited against 12 flagged compliance rows and 24 sampled modified-model responses
with no mislabels found.

| Family | Original | Huihui | Heretic | Paired drop |
|---|---|---|---|---|
| Llama | 22.7% [16.7%, 30.0%] | 0.0% [0.0%, 2.5%] | 0.0% [0.0%, 2.5%] | -22.7% [-29.3%, -16.0%] |
| Gemma | 42.7% [35.0%, 50.7%] | 0.0% [0.0%, 2.5%] | 0.0% [0.0%, 2.5%] | -42.7% [-50.7%, -34.7%] |
| Qwen  | 80.0% [72.9%, 85.6%] | 0.0% [0.0%, 2.5%] | 0.0% [0.0%, 2.5%] | -80.0% [-86.0%, -73.3%] |

Prompt source: CyberSecEval MITRE benchmark (PurpleLlama), `mutated_prompt` field.

Caveat: this measures plain-chat refusal only, not tool-use behavior on the same
requests (ToolFailBench's `--tools` condition is not yet run for this eval).
