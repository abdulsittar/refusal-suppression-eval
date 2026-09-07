# VANTAGE: Refusal-Suppression Evaluation Study

Evaluates whether refusal-suppression ("uncensoring") techniques applied to
open-weight LLMs degrade defensive cybersecurity capability, across three axes:

1. **MITRE FRR** — False Refusal Rate on benign cybersecurity prompts
2. **Malware Analysis** (CyberSOCEval) — multiple-choice malware-analysis accuracy
3. **ToolFailBench** — agentic tool-use reliability (Qwen family only; see Limitations)

Six checkpoints tested: Gemma-3-12B-it and Qwen3-4B-Instruct-2507, each in three
variants — Original, Huihui (abliterated), and Heretic.

## Key finding

Two different refusal-suppression techniques applied to the same base model
produce very different downstream effects. **Huihui** causes a large,
statistically significant degradation in both Malware Analysis accuracy and
agentic tool-use reliability (Tool-Skip Rate +20pp on Qwen, p<0.000001).
**Heretic** does not — its effects are statistically indistinguishable from
no change (p=0.727). See `manifest/MANIFEST.md` for the full experimental log.

## Setup

```bash
git clone <this-repo-url>
cd vantage-refusal-suppression
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env: set VANTAGE_ROOT to your checkpoints/results directory
```

You will also need, cloned separately (not included in this repo):
- [vLLM](https://github.com/vllm-project/vllm) — for serving checkpoints
- [PurpleLlama/CybersecurityBenchmarks](https://github.com/meta-llama/PurpleLlama) — MITRE FRR + Malware Analysis
- [ToolFailBench](https://github.com/SoHarshh/ToolFailBench) — agentic tool-use benchmark

**Important:** `scripts/serve_checkpoint_tools.sh` and the ToolFailBench eval
require vLLM's OpenAI-compatible server. See `patches/README.md` for a required
patch to PurpleLlama's `openai.py` client (guided-decoding fix).

## Checkpoints

Download the six model checkpoints (not included in this repo — see
`config.py` for expected directory names) into `$VANTAGE_ROOT/checkpoints/`:

| Key | Hugging Face repo |
|---|---|
| gemma-original | google/gemma-3-12b-it |
| gemma-huihui | huihui-ai/gemma-3-12b-it-abliterated |
| gemma-heretic | p-e-w/gemma-3-12b-it-heretic-v2 |
| qwen-original | Qwen/Qwen3-4B-Instruct-2507 |
| qwen-huihui | huihui-ai/Huihui-Qwen3-4B-Instruct-2507-abliterated |
| qwen-heretic | p-e-w/Qwen3-4B-Instruct-2507-heretic-v2 |

## Usage

### 1. Serve a checkpoint

```bash
scripts/serve_checkpoint.sh qwen-original          # plain chat serving
scripts/serve_checkpoint_tools.sh qwen-original hermes   # with tool-calling
```

### 2. Run MITRE FRR / Malware Analysis pilots or full runs

```bash
scripts/run_pilots.sh qwen-original     # 10-item pilot, both benchmarks
scripts/run_full.sh qwen-original       # full 750/609-item runs
```

### 3. Run the tool-calling canary gate (validates a checkpoint before ToolFailBench)

```bash
python3 scripts/canary_gate.py <checkpoint_path_as_served> -v
```

### 4. ToolFailBench evaluation (run from the ToolFailBench repo, using its own `run_eval.py`)

```bash
VLLM_BASE_URL="http://localhost:8000/v1" python3 scripts/run_eval.py \
  --model qwen-original --domains cybersecurity
```

### 5. Analysis pipeline (Steps 1-5)

```bash
python3 scripts/verify_transitions.py <baseline.json> <treatment.json> --from correct --to tool_skip
python3 scripts/step2_extract_metrics.py
python3 scripts/step3_transitions.py <baseline.json> <treatment.json> --label Huihui
python3 scripts/step4_paired_stats.py <baseline.json> <treatment.json> --label Huihui
python3 scripts/step5_unified_comparison.py
```

## Repo structure
