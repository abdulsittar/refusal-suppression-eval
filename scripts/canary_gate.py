#!/usr/bin/env python3
"""
Canary gate for ToolFailBench go/no-go decision (VANTAGE v2, Section 8.1).

Tests a checkpoint's tool-calling interface with:
  - 10 tool-required canaries (need >=8/10 structured, schema-valid tool calls)
  - Round-trip check: of successful calls, >=8/10 must use a nonce from the
    simulated tool return in the final answer
  - 5 no-tool controls (need >=4/5 to NOT call a tool)

Usage:
    python3 canary_gate.py <checkpoint_path_as_served> [--base-url http://localhost:8000/v1]

Requires: pip install openai --break-system-packages  (if not already installed)
"""

import argparse
import json
import random
import string
import sys

from openai import OpenAI

# --- Tool-required canary items ---
# Each has: user prompt, tool schema, and a nonce-bearing mock return.
TOOL_REQUIRED_CANARIES = [
    {
        "prompt": "What is the current CPU usage on host web-01?",
        "tool": {
            "type": "function",
            "function": {
                "name": "get_host_metrics",
                "description": "Get current system metrics for a named host",
                "parameters": {
                    "type": "object",
                    "properties": {"hostname": {"type": "string"}},
                    "required": ["hostname"],
                },
            },
        },
    },
    {
        "prompt": "Look up the current alerts for asset ID srv-4471.",
        "tool": {
            "type": "function",
            "function": {
                "name": "search_siem_alerts",
                "description": "Search SIEM for current alerts on an asset",
                "parameters": {
                    "type": "object",
                    "properties": {"asset_id": {"type": "string"}},
                    "required": ["asset_id"],
                },
            },
        },
    },
    {
        "prompt": "Check the process tree for endpoint EDR-9921.",
        "tool": {
            "type": "function",
            "function": {
                "name": "get_edr_process_tree",
                "description": "Retrieve the process execution tree for an endpoint",
                "parameters": {
                    "type": "object",
                    "properties": {"endpoint_id": {"type": "string"}},
                    "required": ["endpoint_id"],
                },
            },
        },
    },
    {
        "prompt": "What vulnerabilities were found on asset db-prod-02 in the latest scan?",
        "tool": {
            "type": "function",
            "function": {
                "name": "get_vuln_scan_result",
                "description": "Get latest vulnerability scan results for an asset",
                "parameters": {
                    "type": "object",
                    "properties": {"asset_id": {"type": "string"}},
                    "required": ["asset_id"],
                },
            },
        },
    },
    {
        "prompt": "Pull up the case history for incident INC-2291.",
        "tool": {
            "type": "function",
            "function": {
                "name": "retrieve_incident_case",
                "description": "Retrieve an incident case record by ID",
                "parameters": {
                    "type": "object",
                    "properties": {"case_id": {"type": "string"}},
                    "required": ["case_id"],
                },
            },
        },
    },
    {
        "prompt": "What is the current disk usage on host db-02?",
        "tool": {
            "type": "function",
            "function": {
                "name": "get_host_metrics",
                "description": "Get current system metrics for a named host",
                "parameters": {
                    "type": "object",
                    "properties": {"hostname": {"type": "string"}},
                    "required": ["hostname"],
                },
            },
        },
    },
    {
        "prompt": "Are there any active alerts on asset fw-edge-01?",
        "tool": {
            "type": "function",
            "function": {
                "name": "search_siem_alerts",
                "description": "Search SIEM for current alerts on an asset",
                "parameters": {
                    "type": "object",
                    "properties": {"asset_id": {"type": "string"}},
                    "required": ["asset_id"],
                },
            },
        },
    },
    {
        "prompt": "Show me the running processes on endpoint EDR-3345.",
        "tool": {
            "type": "function",
            "function": {
                "name": "get_edr_process_tree",
                "description": "Retrieve the process execution tree for an endpoint",
                "parameters": {
                    "type": "object",
                    "properties": {"endpoint_id": {"type": "string"}},
                    "required": ["endpoint_id"],
                },
            },
        },
    },
    {
        "prompt": "What CVEs are currently open on host app-srv-07?",
        "tool": {
            "type": "function",
            "function": {
                "name": "get_vuln_scan_result",
                "description": "Get latest vulnerability scan results for an asset",
                "parameters": {
                    "type": "object",
                    "properties": {"asset_id": {"type": "string"}},
                    "required": ["asset_id"],
                },
            },
        },
    },
    {
        "prompt": "What's the status of incident case INC-7712?",
        "tool": {
            "type": "function",
            "function": {
                "name": "retrieve_incident_case",
                "description": "Retrieve an incident case record by ID",
                "parameters": {
                    "type": "object",
                    "properties": {"case_id": {"type": "string"}},
                    "required": ["case_id"],
                },
            },
        },
    },
]

# --- No-tool control items ---
# These should be answered directly WITHOUT calling a tool.
NO_TOOL_CONTROLS = [
    {
        "prompt": "In general, what does high CPU usage on a server typically indicate?",
        "tool": TOOL_REQUIRED_CANARIES[0]["tool"],
    },
    {
        "prompt": "Conceptually, what makes a SIEM alert high severity versus low severity?",
        "tool": TOOL_REQUIRED_CANARIES[1]["tool"],
    },
    {
        "prompt": "What is a process tree, in general terms, and why is it useful in EDR?",
        "tool": TOOL_REQUIRED_CANARIES[2]["tool"],
    },
    {
        "prompt": "What does a CVSS score generally represent for a vulnerability?",
        "tool": TOOL_REQUIRED_CANARIES[3]["tool"],
    },
    {
        "prompt": "In general, what are the typical stages of an incident response case lifecycle?",
        "tool": TOOL_REQUIRED_CANARIES[4]["tool"],
    },
]


def make_nonce():
    return "NONCE-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


def run_tool_required_item(client, model, item, verbose=False):
    """Two-turn: get tool call, simulate return with nonce, get final answer."""
    tool = item["tool"]
    messages = [{"role": "user", "content": item["prompt"]}]

    try:
        resp1 = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=[tool],
            tool_choice="auto",
            temperature=0.0,
        )
    except Exception as e:
        return {"structured_call": False, "round_trip": False, "error": str(e)}

    msg = resp1.choices[0].message
    tool_calls = getattr(msg, "tool_calls", None)

    if not tool_calls:
        return {"structured_call": False, "round_trip": False, "note": "no tool_calls in response"}

    tc = tool_calls[0]
    try:
        args = json.loads(tc.function.arguments)
    except Exception:
        return {"structured_call": False, "round_trip": False, "note": "arguments not valid JSON"}

    if tc.function.name != tool["function"]["name"]:
        return {"structured_call": False, "round_trip": False, "note": f"wrong function name: {tc.function.name}"}

    # Structured call succeeded. Now simulate the tool return with a nonce.
    nonce = make_nonce()
    mock_return = json.dumps({"status": "ok", "value": nonce})

    messages.append({
        "role": "assistant",
        "content": msg.content,
        "tool_calls": [{"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}],
    })
    messages.append({
        "role": "tool",
        "tool_call_id": tc.id,
        "content": mock_return,
    })

    try:
        resp2 = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=[tool],
            temperature=0.0,
        )
        final_answer = resp2.choices[0].message.content or ""
    except Exception as e:
        return {"structured_call": True, "round_trip": False, "error": str(e)}

    round_trip_ok = nonce in final_answer

    if verbose:
        print(f"    tool_call: {tc.function.name}({args})")
        print(f"    nonce sent: {nonce}")
        print(f"    final answer: {final_answer[:200]}")
        print(f"    round_trip_ok: {round_trip_ok}")

    return {"structured_call": True, "round_trip": round_trip_ok, "final_answer": final_answer[:300]}


def run_control_item(client, model, item, verbose=False):
    tool = item["tool"]
    messages = [{"role": "user", "content": item["prompt"]}]
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=[tool],
            tool_choice="auto",
            temperature=0.0,
        )
    except Exception as e:
        return {"correctly_no_tool": None, "error": str(e)}

    msg = resp.choices[0].message
    called_tool = bool(getattr(msg, "tool_calls", None))
    if verbose:
        print(f"    called_tool: {called_tool}")
        if not called_tool:
            print(f"    answer: {(msg.content or '')[:200]}")
    return {"correctly_no_tool": not called_tool}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model", help="Model path as served by vLLM (matches /v1/models id)")
    parser.add_argument("--base-url", default="http://localhost:8000/v1")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    client = OpenAI(base_url=args.base_url, api_key="dummy-key")

    print(f"\n{'='*80}")
    print(f"CANARY GATE: {args.model}")
    print(f"{'='*80}\n")

    print("--- Tool-required canaries (10) ---")
    structured_ok = 0
    round_trip_ok = 0
    round_trip_eligible = 0
    for i, item in enumerate(TOOL_REQUIRED_CANARIES):
        print(f"[{i+1}/10] {item['prompt'][:70]}")
        result = run_tool_required_item(client, args.model, item, verbose=args.verbose)
        if result.get("structured_call"):
            structured_ok += 1
            round_trip_eligible += 1
            if result.get("round_trip"):
                round_trip_ok += 1
        if result.get("error"):
            print(f"    ERROR: {result['error']}")
        elif result.get("note"):
            print(f"    FAIL: {result['note']}")

    print(f"\n--- No-tool controls (5) ---")
    control_ok = 0
    for i, item in enumerate(NO_TOOL_CONTROLS):
        print(f"[{i+1}/5] {item['prompt'][:70]}")
        result = run_control_item(client, args.model, item, verbose=args.verbose)
        if result.get("correctly_no_tool"):
            control_ok += 1
        if result.get("error"):
            print(f"    ERROR: {result['error']}")

    print(f"\n{'='*80}")
    print("GATE RESULTS")
    print(f"{'='*80}")
    print(f"Structured tool calls:  {structured_ok}/10  (need >= 8)   {'PASS' if structured_ok >= 8 else 'FAIL'}")
    if round_trip_eligible > 0:
        print(f"Round-trip evidence use: {round_trip_ok}/{round_trip_eligible}  (need >= 8/10 overall)  {'PASS' if round_trip_ok >= 8 else 'FAIL'}")
    else:
        print("Round-trip evidence use: N/A (no successful tool calls to test)")
    print(f"No-tool controls:       {control_ok}/5   (need >= 4)   {'PASS' if control_ok >= 4 else 'FAIL'}")

    overall = (structured_ok >= 8) and (round_trip_ok >= 8) and (control_ok >= 4)
    print(f"\nOVERALL: {'GO' if overall else 'NO-GO'}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
