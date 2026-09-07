#!/usr/bin/env python3
"""
Consolidate and compare MITRE FRR + Malware Analysis pilot results
across all 6 VANTAGE checkpoints.
"""

import json
from pathlib import Path

RESULTS_DIR = Path.home() / "vantage" / "results"

CHECKPOINTS = {
    "google_gemma-3-12b-it": ("Gemma", "Original"),
    "huihui-ai_gemma-3-12b-it-abliterated": ("Gemma", "Huihui"),
    "p-e-w_gemma-3-12b-it-heretic-v2": ("Gemma", "Heretic"),
    "Qwen_Qwen3-4B-Instruct-2507": ("Qwen", "Original"),
    "huihui-ai_Huihui-Qwen3-4B-Instruct-2507-abliterated": ("Qwen", "Huihui"),
    "p-e-w_Qwen3-4B-Instruct-2507-heretic-v2": ("Qwen", "Heretic"),
}


def load_json(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception as e:
        print(f"  WARNING: failed to parse {path}: {e}")
        return None


def get_first_value(d):
    if d is None:
        return None
    return next(iter(d.values()), None)


def main():
    rows = []

    for ckpt_dir, (family, variant) in CHECKPOINTS.items():
        ckpt_path = RESULTS_DIR / ckpt_dir

        frr_stat = get_first_value(load_json(ckpt_path / "mitre_frr_pilot_stat.json"))
        mal_stat = get_first_value(load_json(ckpt_path / "malware_analysis_pilot_stat.json"))

        row = {
            "family": family,
            "variant": variant,
            "checkpoint_dir": ckpt_dir,
            "frr_refusal_rate": None,
            "frr_accept_count": None,
            "frr_refusal_count": None,
            "mal_avg_score": None,
            "mal_correct_mc_pct": None,
            "mal_correct_mc_count": None,
            "mal_incorrect_mc_count": None,
            "mal_parsing_error_count": None,
        }

        if frr_stat:
            row["frr_refusal_rate"] = frr_stat.get("refusal_rate")
            row["frr_accept_count"] = frr_stat.get("accept_count")
            row["frr_refusal_count"] = frr_stat.get("refusal_count")

        if mal_stat:
            spm = mal_stat.get("stat_per_model", {})
            row["mal_avg_score"] = spm.get("avg_score")
            row["mal_correct_mc_pct"] = spm.get("correct_mc_pct")
            row["mal_correct_mc_count"] = spm.get("correct_mc_count")
            row["mal_incorrect_mc_count"] = spm.get("incorrect_mc_count")
            row["mal_parsing_error_count"] = spm.get("response_parsing_error_count")

        rows.append(row)

    print("\n" + "=" * 100)
    print("VANTAGE PILOT SUMMARY (n=10 per benchmark)")
    print("=" * 100)
    header = f"{'Family':<8} {'Variant':<10} {'FRR refusal':<13} {'MalAn avg':<11} {'MalAn mc%':<11} {'Parse errs':<11}"
    print(header)
    print("-" * 100)
    for r in rows:
        frr = f"{r['frr_refusal_rate']:.2f}" if r["frr_refusal_rate"] is not None else "N/A"
        avg = f"{r['mal_avg_score']:.3f}" if r["mal_avg_score"] is not None else "N/A"
        pct = f"{r['mal_correct_mc_pct']:.2f}" if r["mal_correct_mc_pct"] is not None else "N/A"
        perr = f"{r['mal_parsing_error_count']}/10" if r["mal_parsing_error_count"] is not None else "N/A"
        print(f"{r['family']:<8} {r['variant']:<10} {frr:<13} {avg:<11} {pct:<11} {perr:<11}")

    print("\n" + "=" * 100)
    print("WITHIN-FAMILY DELTAS (variant minus Original)")
    print("=" * 100)
    by_family = {}
    for r in rows:
        by_family.setdefault(r["family"], {})[r["variant"]] = r

    for family, variants in by_family.items():
        orig = variants.get("Original")
        if orig is None:
            continue
        print(f"\n{family}:")
        for variant_name in ("Huihui", "Heretic"):
            v = variants.get(variant_name)
            if v is None:
                continue

            def delta(key):
                a, b = v.get(key), orig.get(key)
                if a is None or b is None:
                    return None
                return a - b

            frr_d = delta("frr_refusal_rate")
            avg_d = delta("mal_avg_score")
            pct_d = delta("mal_correct_mc_pct")
            perr_d = delta("mal_parsing_error_count")

            print(f"  {variant_name:<8} FRR refusal Δ: {frr_d:+.2f}" if frr_d is not None else f"  {variant_name:<8} FRR refusal Δ: N/A", end="  |  ")
            print(f"MalAn avg Δ: {avg_d:+.3f}" if avg_d is not None else "MalAn avg Δ: N/A", end="  |  ")
            print(f"MalAn mc% Δ: {pct_d:+.2f}" if pct_d is not None else "MalAn mc% Δ: N/A", end="  |  ")
            print(f"Parse err Δ: {perr_d:+d}/10" if perr_d is not None else "Parse err Δ: N/A")

    out_path = RESULTS_DIR / "pilot_summary.json"
    out_path.write_text(json.dumps(rows, indent=2))
    print(f"\nConsolidated data written to: {out_path}")
    print("=" * 100 + "\n")


if __name__ == "__main__":
    main()
