#!/usr/bin/env python3
"""
Step 5: Combine FRR + Malware Analysis + ToolFailBench into one final comparison.
"""

import json
from pathlib import Path

HOME = Path.home()
FRR_MALWARE_PATH = HOME / "vantage" / "results" / "full_summary.json"
TOOLFAILBENCH_PATH = HOME / "vantage" / "ToolFailBench" / "results" / "v5" / "step2_official_metrics.json"
OUT_PATH = HOME / "vantage" / "results" / "step5_unified_comparison.json"
OUT_MD_PATH = HOME / "vantage" / "results" / "step5_unified_comparison.md"

CHECKPOINT_LABELS = {
    "google_gemma-3-12b-it": ("Gemma", "Original"),
    "huihui-ai_gemma-3-12b-it-abliterated": ("Gemma", "Huihui"),
    "p-e-w_gemma-3-12b-it-heretic-v2": ("Gemma", "Heretic"),
    "Qwen_Qwen3-4B-Instruct-2507": ("Qwen", "Original"),
    "huihui-ai_Huihui-Qwen3-4B-Instruct-2507-abliterated": ("Qwen", "Huihui"),
    "p-e-w_Qwen3-4B-Instruct-2507-heretic-v2": ("Qwen", "Heretic"),
}

TFB_LABELS = {
    "Qwen-Original": ("Qwen", "Original"),
    "Qwen-Huihui": ("Qwen", "Huihui"),
    "Qwen-Heretic": ("Qwen", "Heretic"),
}


def main():
    frr_malware = json.loads(FRR_MALWARE_PATH.read_text())
    tfb = json.loads(TOOLFAILBENCH_PATH.read_text()) if TOOLFAILBENCH_PATH.exists() else {}

    tfb_by_variant = {}
    for label, metrics in tfb.items():
        key = TFB_LABELS.get(label)
        if key:
            tfb_by_variant[key] = metrics

    rows = []
    for row in frr_malware:
        family = row["family"]
        variant = row["variant"]
        key = (family, variant)

        unified = {
            "family": family,
            "variant": variant,
            "frr_refusal_rate": row.get("frr_refusal_rate"),
            "mal_avg_score": row.get("mal_avg_score"),
            "mal_correct_mc_pct": row.get("mal_correct_mc_pct"),
            "tfb_tsr": None,
            "tfb_ctur": None,
            "tfb_ctrl_accuracy": None,
        }

        tfb_metrics = tfb_by_variant.get(key)
        if tfb_metrics:
            unified["tfb_tsr"] = tfb_metrics.get("tsr")
            unified["tfb_ctur"] = tfb_metrics.get("ctur")
            unified["tfb_ctrl_accuracy"] = tfb_metrics.get("ctrl_accuracy")

        rows.append(unified)

    print("\n" + "=" * 130)
    print("STEP 5: UNIFIED COMPARISON -- FRR + Malware Analysis + ToolFailBench")
    print("=" * 130)
    header = (f"{'Family':<8} {'Variant':<10} {'FRR':<8} {'MalAn avg':<11} "
              f"{'MalAn mc%':<11} {'TFB TSR':<10} {'TFB CTUR':<10} {'TFB CTRL-Acc':<12}")
    print(header)
    print("-" * 130)
    for r in rows:
        frr = f"{r['frr_refusal_rate']:.2%}" if r["frr_refusal_rate"] is not None else "N/A"
        avg = f"{r['mal_avg_score']:.4f}" if r["mal_avg_score"] is not None else "N/A"
        pct = f"{r['mal_correct_mc_pct']:.2%}" if r["mal_correct_mc_pct"] is not None else "N/A"
        tsr = f"{r['tfb_tsr']:.2%}" if r["tfb_tsr"] is not None else "N/A (Gemma excl.)"
        ctur = f"{r['tfb_ctur']:.2%}" if r["tfb_ctur"] is not None else "N/A"
        ctrl = f"{r['tfb_ctrl_accuracy']:.2%}" if r["tfb_ctrl_accuracy"] is not None else "N/A"
        print(f"{r['family']:<8} {r['variant']:<10} {frr:<8} {avg:<11} {pct:<11} {tsr:<10} {ctur:<10} {ctrl:<12}")

    print("\n" + "=" * 130)
    print("NARRATIVE SUMMARY PER CHECKPOINT (relative to own Original)")
    print("=" * 130)

    by_family = {}
    for r in rows:
        by_family.setdefault(r["family"], {})[r["variant"]] = r

    for family, variants in by_family.items():
        orig = variants.get("Original")
        if not orig:
            continue
        print(f"\n{family}:")
        for variant_name in ("Huihui", "Heretic"):
            v = variants.get(variant_name)
            if not v:
                continue

            def delta(key):
                a, b = v.get(key), orig.get(key)
                if a is None or b is None:
                    return None
                return a - b

            frr_d = delta("frr_refusal_rate")
            mal_d = delta("mal_avg_score")
            tsr_d = delta("tfb_tsr")

            frr_word = "reduces refusal" if (frr_d is not None and frr_d < -0.001) else "no change in refusal"
            mal_word = "preserves Malware Analysis" if (mal_d is not None and abs(mal_d) < 0.03) else \
                       ("degrades Malware Analysis" if (mal_d is not None and mal_d < 0) else "improves Malware Analysis")
            if tsr_d is None:
                tool_word = "ToolFailBench N/A (excluded)"
            elif tsr_d > 0.05:
                tool_word = f"DEGRADES tool-use reliability (TSR +{tsr_d:.1%})"
            else:
                tool_word = f"preserves tool-use reliability (TSR {tsr_d:+.1%})"

            print(f"  {variant_name}: {frr_word}; {mal_word} (avg_score delta={mal_d:+.4f}); {tool_word}")

    print("\n" + "=" * 130)

    OUT_PATH.write_text(json.dumps(rows, indent=2))
    print(f"\nSaved: {OUT_PATH}")

    with open(OUT_MD_PATH, "w") as f:
        f.write("| Family | Variant | FRR | MalAn avg | MalAn mc% | TFB TSR | TFB CTUR | TFB CTRL-Acc |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for r in rows:
            frr = f"{r['frr_refusal_rate']:.2%}" if r["frr_refusal_rate"] is not None else "N/A"
            avg = f"{r['mal_avg_score']:.4f}" if r["mal_avg_score"] is not None else "N/A"
            pct = f"{r['mal_correct_mc_pct']:.2%}" if r["mal_correct_mc_pct"] is not None else "N/A"
            tsr = f"{r['tfb_tsr']:.2%}" if r["tfb_tsr"] is not None else "N/A"
            ctur = f"{r['tfb_ctur']:.2%}" if r["tfb_ctur"] is not None else "N/A"
            ctrl = f"{r['tfb_ctrl_accuracy']:.2%}" if r["tfb_ctrl_accuracy"] is not None else "N/A"
            f.write(f"| {r['family']} | {r['variant']} | {frr} | {avg} | {pct} | {tsr} | {ctur} | {ctrl} |\n")
    print(f"Saved: {OUT_MD_PATH}")


if __name__ == "__main__":
    main()

