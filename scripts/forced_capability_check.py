#!/usr/bin/env python3
import argparse
import json
import time
from openai import OpenAI

def check_match(answer, ground_truth):
    must_contain = ground_truth.get("answer_must_contain", [])
    mode = ground_truth.get("match_mode", "all")
    if not must_contain:
        return None
    matches = [m in (answer or "") for m in must_contain]
    return all(matches) if mode == "all" else any(matches)

def build_tool_def(expected_call):
    args = expected_call.get("arguments", {})
    props = {k: {"type": "string"} for k in args.keys()}
    return {
        "type": "function",
        "function": {
            "name": expected_call["name"],
            "description": f"Retrieve data via {expected_call['name']}",
            "parameters": {"type": "object", "properties": props, "required": list(props.keys())},
        },
    }

def run_one(client, model_id, item, retries=1, debug=False):
    t = item["task"]
    expected_call = t.get("expected_tool_call")
    mock_return = t.get("mock_tool_return")
    gt = t.get("ground_truth", {})
    user_msg = t["user_message"]

    if not expected_call or not mock_return:
        return {"status": "skip", "task_id": t["task_id"]}

    tool = build_tool_def(expected_call)
    messages = [{"role": "user", "content": user_msg}]

    last_err = None
    for attempt in range(retries + 1):
        try:
            resp1 = client.chat.completions.create(
                model=model_id, messages=messages, tools=[tool],
                tool_choice="required", temperature=0.0, timeout=90,
            )
            msg = resp1.choices[0].message
            if not msg.tool_calls:
                return {"status": "forced_call_failed", "task_id": t["task_id"]}
            tc = msg.tool_calls[0]

            if debug and msg.content:
                print(f"    [DEBUG] resp1.content was NOT empty: {msg.content[:150]!r}")

            msgs2 = messages + [
                {"role": "assistant", "content": None,
                 "tool_calls": [{"id": tc.id, "type": "function",
                                  "function": {"name": tc.function.name, "arguments": tc.function.arguments}}]},
                {"role": "tool", "tool_call_id": tc.id, "content": json.dumps(mock_return)},
            ]
            resp2 = client.chat.completions.create(
                model=model_id, messages=msgs2,
                temperature=0.0, timeout=90,
            )
            msg2 = resp2.choices[0].message
            if debug and msg2.tool_calls:
                print(f"    [DEBUG] resp2 STILL emitted tool_calls despite tool_choice='none': {msg2.tool_calls}")
            final_answer = msg2.content or ""
            match = check_match(final_answer, gt)
            status = "no_criteria" if match is None else ("forced_correct" if match else "forced_wrong")
            return {"status": status, "task_id": t["task_id"], "domain": t["domain"], "answer": final_answer[:200]}
        except Exception as e:
            last_err = str(e)
            time.sleep(3)
            continue
    return {"status": "api_error", "task_id": t["task_id"], "error": last_err}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results_path")
    ap.add_argument("model_id")
    ap.add_argument("--base-url", default="http://localhost:8000/v1")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--output", default="forced_capability_results.jsonl")
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()

    client = OpenAI(base_url=args.base_url, api_key="dummy-key")

    d = json.load(open(args.results_path))
    items = d if isinstance(d, list) else list(d.values())
    tool_required = [i for i in items
                      if i.get("task", {}).get("evaluation_criteria", {}).get("tool_must_be_called")]
    if args.limit:
        tool_required = tool_required[:args.limit]

    print(f"Running forced tool_choice='required' on {len(tool_required)} items", flush=True)
    print(f"Model: {args.model_id}", flush=True)
    print(f"Saving incrementally to: {args.output}\n", flush=True)

    results = {"forced_correct": 0, "forced_wrong": 0, "no_criteria": 0,
               "forced_call_failed": 0, "api_error": 0, "skip": 0}

    with open(args.output, "w") as outf:
        for idx, item in enumerate(tool_required):
            t = item["task"]
            print(f"[{idx+1}/{len(tool_required)}] {t['task_id']} ({t['domain']}) ...", end=" ", flush=True)
            r = run_one(client, args.model_id, item, retries=1, debug=args.debug)
            results[r["status"]] += 1
            print(r["status"].upper(), flush=True)
            outf.write(json.dumps(r) + "\n")
            outf.flush()

    print("\n" + "=" * 70)
    print("FORCED CAPABILITY-CEILING RESULTS")
    print("=" * 70)
    total = len(tool_required)
    for k, v in results.items():
        print(f"  {k}: {v} / {total} ({v/total:.1%})")

if __name__ == "__main__":
    main()
