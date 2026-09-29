# VANTAGE: Refusal-Suppression Evaluation Study

Evaluates whether refusal-suppression ("uncensoring") techniques applied to
open-weight LLMs degrade defensive cybersecurity capability, across three axes:

1. **MITRE FRR** — False Refusal Rate on benign cybersecurity prompts
2. **Malware Analysis** (CyberSOCEval) — multiple-choice malware-analysis accuracy
3. **ToolFailBench** — agentic tool-use reliability (Qwen and Llama
   families; Gemma excluded — failed preliminary tool-interface checks; see
   `manifest/MANIFEST.md`)

Nine checkpoints tested: Gemma-3-12B-it, Qwen3-4B-Instruct-2507, and
Llama-3.1-8B-Instruct, each in three variants — Original, Huihui (abliterated),
and Heretic.

## Key finding

Refusal-suppressed checkpoints (Huihui and Heretic derivatives of Qwen,
Llama, and Gemma) reduce detected refusal on harmful and benign prompts, but
do not consistently preserve malware-analysis capability or agentic tool-use
reliability — and which axis degrades, and how much, differs by model
family. See `manifest/MANIFEST.md` for the working experimental log.

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

Download the nine model checkpoints (not included in this repo — see
`config.py` for expected directory names) into `$VANTAGE_ROOT/checkpoints/`:

| Key | Hugging Face repo |
|---|---|
| gemma-original | google/gemma-3-12b-it |
| gemma-huihui | huihui-ai/gemma-3-12b-it-abliterated |
| gemma-heretic | p-e-w/gemma-3-12b-it-heretic-v2 |
| qwen-original | Qwen/Qwen3-4B-Instruct-2507 |
| qwen-huihui | huihui-ai/Huihui-Qwen3-4B-Instruct-2507-abliterated |
| qwen-heretic | p-e-w/Qwen3-4B-Instruct-2507-heretic-v2 |
| llama-original | meta-llama/Meta-Llama-3.1-8B-Instruct |
| llama-huihui | huihui-ai/Meta-Llama-3.1-8B-Instruct-abliterated |
| llama-heretic | p-e-w/Llama-3.1-8B-Instruct-heretic (via askalgore mirror — see note) |

*Llama-Heretic was obtained through the askalgore mirror after the original
p-e-w repository became unavailable. Identity with the earlier p-e-w upload
has not been verified.*

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
