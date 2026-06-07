#!/usr/bin/env python
# scripts/eval_drug_correction.py
# Evaluate DrugCorrectionEngine v2 against drug_correction_eval.json
# CONS-002-EVAL | MediVoice VN
#
# Usage:
#   python -X utf8 scripts/eval_drug_correction.py
#   python -X utf8 scripts/eval_drug_correction.py --json   # output JSON report
#   python -X utf8 scripts/eval_drug_correction.py --category noisy

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.l1b_drug_correct import correct_drug_names_v2

DATASET = Path("data/eval/drug_correction_eval.json")


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _norm_inn(inn: str) -> str:
    return inn.lower().strip()


def _inn_match(predicted_inn: str, expected_inn: str) -> bool:
    return _norm_inn(predicted_inn) == _norm_inn(expected_inn)


def _predicted_contains(matches, expected_inn: str) -> bool:
    return any(_inn_match(m.inn, expected_inn) for m in matches)


def _matches_have_flag(matches, flag: str) -> bool:
    return any(m.flag_reason == flag and m.flagged_for_review for m in matches)


def _any_flagged(matches) -> bool:
    return any(m.flagged_for_review for m in matches)


# ─── Evaluation ──────────────────────────────────────────────────────────────

def evaluate(cases: list[dict], category_filter: str | None = None) -> dict:
    """
    Compute 4 metrics:
    1. Drug Recall      — TP_drugs / (TP_drugs + FN_drugs)
    2. FP Rate          — false positives in negative test cases
    3. Safety Catch     — correct flags in dangerous cases
    4. Phonetic Recall  — Drug Recall restricted to noisy category
    """
    if category_filter:
        cases = [c for c in cases if c["category"] == category_filter]

    # Counters
    tp_drugs = 0
    fn_drugs = 0
    fp_count = 0
    tn_neg = 0   # negative cases with zero predictions
    fn_neg = 0   # negative cases where drugs were predicted (FP events)

    safety_caught = 0
    safety_total = 0

    phonetic_tp = 0
    phonetic_fn = 0

    errors: list[dict] = []

    for case in cases:
        transcript = case["transcript"]
        expected_drugs = case["expected_drugs"]
        expected_flags = case["expected_flags"]
        is_negative = case["is_negative"]
        cat = case["category"]
        sub = case["subcategory"]

        try:
            _, matches = correct_drug_names_v2(transcript)
        except Exception as e:
            errors.append({"id": case["id"], "error": str(e)})
            continue

        # 1. Drug Recall (non-negative cases with expected_drugs)
        if expected_drugs and not is_negative:
            for exp in expected_drugs:
                expected_inn = exp["inn"]
                if _predicted_contains(matches, expected_inn):
                    tp_drugs += 1
                else:
                    fn_drugs += 1
                    errors.append({
                        "id": case["id"],
                        "category": cat,
                        "subcategory": sub,
                        "type": "FN_drug",
                        "expected": expected_inn,
                        "predicted": [m.inn for m in matches],
                        "transcript": transcript[:80],
                    })
            # Also check Phonetic Recall for noisy category
            if cat == "noisy":
                for exp in expected_drugs:
                    if _predicted_contains(matches, exp["inn"]):
                        phonetic_tp += 1
                    else:
                        phonetic_fn += 1

        # 2. False Positive Rate (negative tests = no expected drugs)
        # Split: "silent FP" (unflagged, clinically dangerous) vs "warned FP" (LOW_CONFIDENCE flagged)
        if is_negative or (not expected_drugs and "AMBIGUOUS" not in expected_flags):
            silent = [m for m in matches if not m.flagged_for_review]
            warned = [m for m in matches if m.flagged_for_review]
            if silent:
                fp_count += 1
                fn_neg += 1
                errors.append({
                    "id": case["id"],
                    "category": cat,
                    "type": "FP_silent",  # dangerous: enters prescription without review
                    "predicted": [m.inn for m in silent],
                    "transcript": transcript[:80],
                })
            elif warned:
                # Warned FP: BS sees flag, won't blindly accept → acceptable
                errors.append({
                    "id": case["id"],
                    "category": cat,
                    "type": "FP_warned",  # expected: BS reviews + rejects
                    "predicted": [f"{m.inn}[{m.flag_reason}]" for m in warned],
                    "transcript": transcript[:80],
                })
            else:
                tn_neg += 1

        # 3. Safety Catch Rate (dangerous cases with expected_flags)
        if expected_flags:
            for flag in expected_flags:
                safety_total += 1
                if flag == "AMBIGUOUS":
                    # Expect any match to be flagged as AMBIGUOUS or no confident match
                    caught = (
                        _matches_have_flag(matches, "AMBIGUOUS")
                        or (matches and all(m.confidence < 0.8 for m in matches))
                        or not matches  # no match at all = safe
                    )
                else:
                    # DOSE_OUT_OF_RANGE: expect flagged_for_review=True with correct reason
                    caught = _matches_have_flag(matches, flag)

                if caught:
                    safety_caught += 1
                else:
                    errors.append({
                        "id": case["id"],
                        "category": cat,
                        "type": f"SAFETY_MISS_{flag}",
                        "expected_flag": flag,
                        "matches": [
                            {"inn": m.inn, "flag": m.flag_reason, "flagged": m.flagged_for_review}
                            for m in matches
                        ],
                        "transcript": transcript[:80],
                    })

    # Compute rates
    drug_recall = tp_drugs / (tp_drugs + fn_drugs) if (tp_drugs + fn_drugs) > 0 else 1.0
    fp_total_neg = fn_neg + tn_neg
    fp_rate = fn_neg / fp_total_neg if fp_total_neg > 0 else 0.0  # silent FP rate only
    safety_rate = safety_caught / safety_total if safety_total > 0 else 1.0
    phonetic_recall = phonetic_tp / (phonetic_tp + phonetic_fn) if (phonetic_tp + phonetic_fn) > 0 else 1.0

    return {
        "total_cases": len(cases),
        "category_filter": category_filter,
        "metrics": {
            "drug_recall": round(drug_recall, 4),
            "fp_rate": round(fp_rate, 4),
            "safety_catch_rate": round(safety_rate, 4),
            "phonetic_recall": round(phonetic_recall, 4),
        },
        "counts": {
            "tp_drugs": tp_drugs,
            "fn_drugs": fn_drugs,
            "fp_drug_events": fp_count,
            "tn_negative": tn_neg,
            "safety_caught": safety_caught,
            "safety_total": safety_total,
            "phonetic_tp": phonetic_tp,
            "phonetic_fn": phonetic_fn,
        },
        "errors": errors[:30],  # cap at 30 for readability
        "error_count": len(errors),
    }


def print_report(result: dict) -> None:
    m = result["metrics"]
    c = result["counts"]
    cat = result.get("category_filter") or "ALL"
    total = result["total_cases"]

    print(f"\n{'='*60}")
    print(f"DRUG CORRECTION EVAL — CONS-002-EVAL [{cat.upper()}]")
    print(f"{'='*60}")
    print(f"Cases:  {total}")
    print(f"Errors: {result['error_count']}")
    print(f"{'─'*60}")
    print(f"Drug Recall       {m['drug_recall']*100:6.1f}%  "
          f"(TP={c['tp_drugs']} FN={c['fn_drugs']})")
    print(f"Silent FP Rate    {m['fp_rate']*100:6.1f}%  "
          f"(silentFP={c['fp_drug_events']} TN={c['tn_negative']})")
    print(f"  ↳ Warned FP (LOW_CONFIDENCE flagged) = not counted — BS rejects at review")
    print(f"Safety Catch      {m['safety_catch_rate']*100:6.1f}%  "
          f"({c['safety_caught']}/{c['safety_total']})")
    print(f"Phonetic Recall   {m['phonetic_recall']*100:6.1f}%  "
          f"(TP={c['phonetic_tp']} FN={c['phonetic_fn']})")
    print(f"{'─'*60}")

    # GO/NO-GO assessment (CONS-20260610-003 GO criteria adapted for drug eval)
    go_criteria = {
        "Drug Recall ≥ 88%":       m["drug_recall"] >= 0.88,
        "FP Rate ≤ 10%":           m["fp_rate"] <= 0.10,
        "Safety Catch ≥ 80%":      m["safety_catch_rate"] >= 0.80,
        "Phonetic Recall ≥ 85%":   m["phonetic_recall"] >= 0.85,
    }
    all_pass = all(go_criteria.values())
    print(f"GO/NO-GO Assessment:")
    for criterion, passed in go_criteria.items():
        mark = "✅" if passed else "❌"
        print(f"  {mark} {criterion}")
    print(f"{'─'*60}")
    print(f"  → {'✅ GO — all criteria met' if all_pass else '❌ NO-GO — fix failing criteria'}")

    if result["errors"]:
        print(f"\nTop errors (first 10):")
        for e in result["errors"][:10]:
            etype = e.get("type", "ERR")
            print(f"  [{e.get('id','?')}] {etype}: {e.get('transcript','')[:60]}")
            if "expected" in e:
                print(f"    expected={e['expected']} got={e.get('predicted', [])}")
    print()


# ─── Per-category breakdown ───────────────────────────────────────────────────

def run_full_report(cases: list[dict], output_json: bool = False) -> None:
    overall = evaluate(cases)
    print_report(overall)

    for cat in ("clean", "noisy", "dangerous"):
        cat_cases = [c for c in cases if c["category"] == cat]
        if cat_cases:
            r = evaluate(cat_cases, category_filter=cat)
            print_report(r)

    if output_json:
        out = Path("data/eval/drug_correction_eval_report.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(overall, f, ensure_ascii=False, indent=2)
        print(f"JSON report saved → {out}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate DrugCorrectionEngine v2")
    parser.add_argument("--json", action="store_true", help="Save JSON report")
    parser.add_argument("--category", choices=["clean", "noisy", "dangerous"],
                        help="Filter by category")
    args = parser.parse_args()

    if not DATASET.exists():
        print(f"Dataset not found: {DATASET}")
        print("Run: python -X utf8 scripts/generate_drug_eval_dataset.py")
        sys.exit(1)

    with open(DATASET, encoding="utf-8") as f:
        data = json.load(f)
    cases = data["cases"]

    if args.category:
        result = evaluate(cases, category_filter=args.category)
        print_report(result)
    else:
        run_full_report(cases, output_json=args.json)


if __name__ == "__main__":
    main()
