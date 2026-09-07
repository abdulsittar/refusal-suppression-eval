# Patches to third-party dependencies

## openai_json_schema_fix.diff

**Applies to:** `PurpleLlama/CybersecurityBenchmarks/benchmark/llms/openai.py`
(not included in this repo — clone PurpleLlama separately, then apply this patch)

**Problem:** The stock `openai.py` client uses OpenAI's loose
`response_format={"type": "json_object"}` mode when `guided_decode_json_schema`
is set. This mode only guarantees syntactically valid JSON, not that it matches
the required schema — it does not use vLLM's actual schema-constrained decoding.
This allowed models (especially refusal-suppressed variants) to return JSON that
echoed the schema itself instead of answering, causing spurious
`response_parsing_error_count` spikes unrelated to real model capability
(observed: Gemma-Heretic went from 10/10 parsing errors to 0/10 after this fix).

**Fix:** Replaces `{"type": "json_object"}` with proper
`{"type": "json_schema", "json_schema": {...}}`, which vLLM enforces via real
constrained decoding.

**To apply:**
```bash
cd PurpleLlama/CybersecurityBenchmarks/benchmark/llms/
cp openai.py openai.py.bak   # backup first
patch < /path/to/this/repo/patches/openai_json_schema_fix.diff
```

**Reference backup:** `openai_original.py.bak` is the pre-patch version, kept
here for reference/diffing.
