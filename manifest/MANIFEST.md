
## CyberSOCEval_data submodule
Commit: ce7daa5bc7da51559ca97476d2277be02631783e
Fixed via: git submodule update --init --recursive --force

## CyberSOCEval_data submodule
Commit: ce7daa5bc7da51559ca97476d2277be02631783e
Fixed via: git submodule update --init --recursive --force

## Malware Analysis judge script patch
Original malware_analysis.py crashes with TypeError when model response's
extracted JSON lacks "correct_answers" as a list (e.g. model echoes the JSON
schema instead of answering). Patched process_judge_prompt to check
isinstance(parsed_response.get("correct_answers"), list) before scoring,
so these cases correctly fall through to "answered_correctly": "parsing error"
instead of crashing, matching the plan's requirement to count (not drop) parsing errors.

## Malware Analysis judge script patch
Original malware_analysis.py crashes with TypeError when model response's
extracted JSON lacks "correct_answers" as a list (e.g. model echoes the JSON
schema instead of answering, observed intermittently in Gemma-original pilot runs (item index varies by run due to sampling/parallel ordering)).
Patched process_judge_prompt (line ~439) to check
isinstance(parsed_response.get("correct_answers"), list) before scoring,
so these cases correctly fall through to "answered_correctly": "parsing error"
instead of crashing — matching the plan's requirement to count, not drop, parsing errors.
Backup saved as malware_analysis.py.bak.

## Observation: structured-output degradation in Huihui-Gemma pilot
Malware Analysis pilot (10 items): Gemma-original had 1/10 response_parsing_error_count,
Huihui-Gemma had 5/10. Qualitative pattern: Huihui consistently echoes the JSON schema
wrapper and inconsistently places its actual answer (sometimes correct top-level key,
sometimes nested under spurious "values" key, sometimes renames the key, sometimes
omits answer entirely). MITRE FRR refusal rate unaffected (0% for both).
Worth tracking across full 750-item runs and other checkpoints as a secondary finding —
possible capability cost of refusal-suppression distinct from the main FRR/malware-score metrics.

## Observation: Heretic-Gemma total structured-output failure on Malware Analysis
Malware Analysis pilot (10 items): Heretic-Gemma produced 10/10 response_parsing_error_count.
All 10 responses were byte-identical (133 chars): the bare JSON schema with no answer content
whatsoever, unlike Huihui which at least attempted answers (often just misplaced/mislabeled).
General inference sanity-checked as working correctly (e.g. "What is 2+2?" -> "Four").
MITRE FRR unaffected (0% refusal, matches Gemma-original and Huihui-Gemma).
Trend across family: Gemma-original 1/10 parsing errors -> Huihui 5/10 -> Heretic 10/10.
This is a strong candidate finding for H2 (Huihui vs Heretic differ in Malware Analysis
capability preservation) and should be checked for consistency across the full 750-item runs
and against the Qwen family.

## Cross-family comparison: parsing errors vs. correctness degradation
Gemma family (Malware Analysis pilot, 10 items):
  Original: 1/10 parsing errors, correct_mc_pct not yet computed for comparison
  Huihui:   5/10 parsing errors
  Heretic:  10/10 parsing errors (total structured-output failure)
  -> Pattern: increasing parsing/formatting failure with refusal-suppression strength

Qwen family (Malware Analysis pilot, 10 items):
  Original: 0/10 parsing errors, avg_score 0.554, correct_mc_pct 0.20
  Huihui:   0/10 parsing errors, avg_score 0.393, correct_mc_pct 0.00
  -> Pattern: NO parsing/formatting failure, but correctness declines
             (0.554->0.393 avg_score, 20%->0% exact-match rate)

Preliminary interpretation: the two families show DIFFERENT failure modes under
refusal-suppression. Gemma degrades via structured-output/instruction-following
collapse; Qwen degrades via answer-quality decline while maintaining format compliance.
This does not replicate cleanly across families and should be treated as a key
finding to verify at full-scale (750 items) rather than assumed from the pilot alone.

## Complete pilot summary (Malware Analysis, n=10, all 6 checkpoints)
Gemma:  Original 1/10 parse-err | Huihui 5/10 parse-err | Heretic 10/10 parse-err (total collapse)
Qwen:   Original 0/10 parse-err, avg 0.554, mc_pct 0.20
        Huihui   0/10 parse-err, avg 0.393, mc_pct 0.00  (correctness dip, no format issue)
        Heretic  0/10 parse-err, avg 0.606, mc_pct 0.20  (no degradation vs original at n=10)

Key finding: Huihui and Heretic do NOT show consistent relative behavior across families.
Gemma: Heretic >> Huihui in severity of degradation (structured-output collapse).
Qwen: Huihui shows correctness dip; Heretic shows no dip. Opposite ordering from Gemma.
All pilot n=10 — must verify at full n=750 scale before treating as robust finding,
per plan's requirement that pilot results are for pipeline validation, not conclusions.

## CRITICAL: guided-decoding fix invalidates prior parsing-error findings
Gemma-Heretic re-tested under fixed json_schema enforcement:
  Before fix: 10/10 parsing errors, avg_score 0.000
  After fix:  0/10 parsing errors, avg_score 0.480 (nearly identical to Gemma-Original's 0.482)
This means the "structured-output collapse" story from the original pilot was largely
a measurement artifact of weak client-side JSON enforcement (json_object mode), not a
genuine capability difference. ALL prior pilot results (all 6 checkpoints) must be
re-run under the fixed openai.py before drawing any conclusions. Prior Gemma-family
parsing-error progression (1/10 -> 5/10 -> 10/10) is now considered UNRELIABLE.

## ToolFailBench canary gate results
Qwen-Original: 10/10 structured, 10/10 round-trip, 5/5 controls -> GO

## ToolFailBench canary gate — FINAL GO/NO-GO DECISION
Qwen-Original:  GO
Qwen-Huihui:    GO
Qwen-Heretic:   GO
Gemma-Original: NO-GO
Gemma-Huihui:   NO-GO
Gemma-Heretic:  NO-GO

DECISION: Gemma fails the gate at the ORIGINAL checkpoint level (not just the
suppressed variants), indicating this is an architecture/interface limitation of
Gemma-3-12B-it's tool-calling support via vLLM's hermes parser, not an effect of
refusal-suppression. Per plan Section 8.1 contingency: ToolFailBench (RQ3, agentic
tool-use axis) proceeds as a QWEN-ONLY three-checkpoint study (Original/Huihui/Heretic).
Gemma remains fully in scope for RQ1 (MITRE FRR) and RQ2 (Malware Analysis), where
full 750/609-item results already exist for all six checkpoints.

## Gemma NO-GO — root cause detail
All three Gemma checkpoints scored 0/10 on structured tool calls (vs Qwen's 10/10
across all three variants). Gemma did NOT error, crash, or produce malformed tool
syntax -- it simply never emitted a tool_calls response for ANY of the 10 tool-required
canaries, answering every one in plain prose instead (5/5 no-tool controls also
answered correctly in prose, but this reflects the model defaulting to prose
universally, not correct judgment about when to use a tool).
Root cause: Gemma-3-12B-it was not trained with vLLM's supported function-calling
format (hermes parser expects a specific tool-call token/syntax Gemma-3-12B-it does
not produce). This is consistent across Original/Huihui/Heretic, confirming it is a
base-model/interface limitation, not an effect of refusal-suppression.
No prompt-engineering or custom parsing workaround was attempted, per plan's explicit
prohibition on adapters/hacks for this gate.

## Gemma NO-GO — confirmed structural, not fixable via parser change
Checked vLLM 0.27.1's full list of supported --tool-call-parser options: includes
a dedicated "functiongemma" parser, confirming tool-calling for the Gemma family
requires a separate, purpose-trained FunctionGemma checkpoint -- NOT the general
Gemma-3-12B-it chat model used throughout this study. Additionally,
google_gemma-3-12b-it/chat_template.json contains zero tool/function-related
Jinja logic or special tokens (grep returned empty), confirming the checkpoint
itself has no native mechanism to receive or emit tool-call syntax.
No parser swap or template modification can fix this without introducing a
custom adapter, which the plan explicitly prohibits (Section 8.1).
FINAL: Gemma is excluded from ToolFailBench (RQ3) on structural grounds.
Proceeding as Qwen-only 3-checkpoint agentic study, per plan's pre-registered fallback.

## ToolFailBench full results (Qwen family, cybersecurity domain, n=200: 150 tool-required + 50 CTRL)
Qwen-Original: TSR 48.00%, Result-Ignore 1.28%, Clean Tool-Use 51.33%, CTRL-Acc 78.00%
Qwen-Huihui:   TSR 68.00%, Result-Ignore 2.08%, Clean Tool-Use 31.33%, CTRL-Acc 76.00%
Qwen-Heretic:  TSR 49.33%, Result-Ignore 0.00%, Clean Tool-Use 50.67%, CTRL-Acc 80.00%

Finding: Huihui causes a large, consistent degradation in tool-use reliability
(+20pp Tool-Skip Rate, -20pp Clean Tool-Use vs Original). Heretic shows no
meaningful degradation on any metric. This REPLICATES the same relative pattern
found in Malware Analysis (Huihui costs correctness, Heretic does not) -- now
confirmed across two structurally different task types (knowledge QA vs agentic
tool-use), strengthening the overall H2 finding considerably.

## Gemma NO-GO — final confirmation with alternate parser
Also tested --tool-call-parser gemma4 (in addition to hermes) against Gemma-Original.
Result: identical failure -- 0/8+ structured tool calls observed before process completion
(matches the hermes result of 0/10 exactly). No further vLLM-supported parser exists for
this checkpoint; the only purpose-built option (functiongemma) targets an unrelated,
much smaller (270M param) specialist model not part of this study, per Google's own
documentation (not intended as a dialogue model, requires further fine-tuning to be
reliable even for its intended use case).
CONCLUSION: Gemma-3-12B-it's exclusion from ToolFailBench (RQ3) is final and
structurally grounded, confirmed across two independent parser attempts.

## Gemma family — exhaustive confirmation across variants (final)
Tested with --tool-call-parser gemma4 (in addition to earlier hermes tests):
  Gemma-Original: 0/10 structured calls, 5/5 correct no-tool controls -> NO-GO
  Gemma-Huihui:   0/10 structured calls, 5/5 correct no-tool controls -> NO-GO
Both variants behave identically to each other and to prior hermes-parser results.
Confirms tool-calling gap is a property of the base architecture, unaffected by
refusal-suppression. No further Gemma variants tested beyond this point (paused
before Heretic-Gemma at user's request); pattern is already fully consistent
across 2 of 3 variants and 2 parsers, sufficient for exclusion decision.

## Step 1 (manual verification) - COMPLETE
Confirmed 33 Correct->Tool-Skip transitions (Original->Huihui) exist with genuinely
empty agent_trace.tool_calls (not a parsing artifact).
Chat template comparison: Huihui-Qwen's chat_template.jinja retains the identical
core tool-calling logic block (tools injection + <tool_call> tag instructions) as
Qwen-Original's template. Differences are additive only (multi-step tool tracking,
<think> reasoning-content handling) -- consistent with a newer official Qwen template
version, NOT damage from the abliteration process.
CONCLUSION: Elevated Huihui Tool-Skip Rate (48%->68%) is a genuine behavioral
effect of the model, not a broken/degraded tool-calling template or harness bug.
Additionally discovered: ~61-69% of tool-skip cases across ALL THREE checkpoints
involve fabricated tool-attribution (answers formatted as "Per `tool_name`:" despite
no real tool call) -- this rate is roughly constant across checkpoints, so Huihui's
harm comes from skipping MORE OFTEN, not fabricating more aggressively per-skip.

## Step 1 - reproducibility confirmation (full independent rerun)
Re-ran ToolFailBench cybersecurity eval for qwen-original and qwen-huihui from
scratch (fresh server launch, fresh 200-item run each).
Result: 100% identical classification counts to the original run for both
checkpoints (correct/tool_skip/wrong_answer/result_ignore all matched exactly).
The 33 Correct->Tool-Skip transitions are identical between runs (same count,
confirmed via verify_transitions.py). This confirms temperature=0/seed=42 produce
fully deterministic results on this setup, and the Huihui Tool-Skip effect is not
run-to-run noise.

## Step 2 - Official ToolFailBench metrics (COMPLETE)
Computed via evaluation/metrics.py compute_all_metrics(), n=200 (150 tool-required + 50 CTRL):

Metric          Original   Huihui     Heretic
TSR             48.00%     68.00%     49.33%
RIR              1.28%      2.08%      0.00%
OFR              0.00%      0.00%      0.00%
CTUR            51.33%     31.33%     50.67%
UTR               0.00%      0.00%      0.00%
CTRL-Acc        78.00%     76.00%     80.00%

Note: OFR=0.00% across all checkpoints because detect_output_fabrication() only
evaluates cases where a tool WAS called -- it does not capture the
"fabricated tool attribution while skipping" pattern found manually in Step 1
(answers formatted as "Per `tool_name`:" despite empty tool_calls). This is a
genuine gap in the official OFR metric for this specific failure mode; our
manual fabrication analysis (detect_fabricated_attribution.py) captures it instead.

## Step 3 - Item-level transition analysis (COMPLETE)
Full transition matrices computed for Original->Huihui and Original->Heretic (n=200 each).

Key comparison:
                        Huihui    Heretic
Correct->Correct         78        108
Correct->Tool-Skip       33          5    <- main driver of TSR difference
Correct->Wrong-Answer     5          3
Tool-Skip->Correct        2          3
Tool-Skip->Tool-Skip     69         69    <- IDENTICAL in both (same 69 baseline-hard tasks)
Net Correct<->Skip       +31        +2

Finding: The Tool-Skip->Tool-Skip count (69) is identical for both treatments,
confirming both comparisons share the same baseline. The entire TSR/CTUR gap
between Huihui and Heretic is explained almost entirely by ONE transition type:
Correct->Tool-Skip regression (33 vs 5, ~6.6x difference). This isolates the
harm to a single, specific, well-defined behavioral shift rather than general
noise across many transition types.

## Step 4 - Paired statistics (COMPLETE)
Bootstrap 95% CIs (10,000 resamples) + McNemar's exact test on Correct<->Tool-Skip
discordant pairs, n=200 paired tasks (same items across all checkpoints).

Huihui:  TSR diff +20.00pp [95% CI: +13.01, +27.22]  -- SIGNIFICANT
         CTUR diff -20.00pp [95% CI: -27.34, -12.93]  -- SIGNIFICANT
         McNemar: b=33, c=2, p<0.000001               -- SIGNIFICANT

Heretic: TSR diff +1.33pp [95% CI: -2.10, +5.03]      -- NOT significant (CI includes 0)
         CTUR diff -0.67pp [95% CI: -4.58, +3.31]     -- NOT significant (CI includes 0)
         McNemar: b=5, c=3, p=0.727                    -- NOT significant

CONCLUSION: Huihui's degradation of tool-use reliability is statistically robust
and large. Heretic shows no statistically distinguishable effect from Original --
its small observed difference is consistent with chance variation alone.
This provides rigorous statistical support for H2 (the two suppression techniques
differ) with Huihui as the technique carrying a real, quantified capability cost.
