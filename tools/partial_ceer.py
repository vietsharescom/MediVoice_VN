#!/usr/bin/env python3
"""
tools/partial_ceer.py
Partial CEER — chạy L1b+L1c+L1d trên transcripts từ T007_eval_results.json
Đo entity extraction coverage (không có ground truth → không phải CEER thật)
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import l1b_drug_correct, l1c_ner, l1d_icd_lookup

RESULTS_FILE = os.path.join("data", "audio", "T007_eval_results.json")
OUT_FILE     = os.path.join("data", "audio", "partial_ceer_results.json")


def run_pipeline(transcript: str) -> dict:
    corrected     = l1b_drug_correct.correct_drug_names(transcript)
    drug_cands    = l1b_drug_correct.extract_drug_candidates(corrected)
    entities      = l1c_ner.extract_entities(corrected, drug_cands)
    icd_code, icd_display = l1d_icd_lookup.auto_lookup(entities.chan_doan)
    return {
        "transcript_raw":       transcript,
        "transcript_corrected": corrected,
        "drugs_found":          [d["inn"] for d in drug_cands],
        "drug_details":         drug_cands,
        "chan_doan":             entities.chan_doan,
        "icd_code":             icd_code,
        "icd_display":          icd_display,
        "sinh_hieu": {
            "nhiet_do":            entities.nhiet_do,
            "huyet_ap":            f"{entities.huyet_ap_tam_thu}/{entities.huyet_ap_tam_truong}"
                                   if entities.huyet_ap_tam_thu else None,
            "mach":                entities.mach,
            "spo2":                entities.spo2,
            "can_nang":            entities.can_nang,
        },
        "tai_kham":             entities.tai_kham,
        "don_thuoc":            entities.don_thuoc,
        "chi_dinh":             entities.chi_dinh,
    }


def safe(s): return s.encode("ascii","replace").decode() if s else ""


def main():
    with open(RESULTS_FILE, encoding="utf-8") as f:
        t007 = json.load(f)

    print("=" * 70)
    print("PARTIAL CEER — L1b + L1c + L1d trên T007 transcripts")
    print(f"Files: {len(t007)}")
    print("=" * 70)

    results = []
    drug_hits = 0
    icd_hits  = 0
    vital_hits = 0

    for row in t007:
        fname      = row["file"]
        transcript = row["phowhisper"]["text"]
        wer        = row["phowhisper"]["wer"]

        r = run_pipeline(transcript)
        r["file"] = fname
        r["wer"]  = wer
        results.append(r)

        has_drug  = len(r["drugs_found"]) > 0
        has_icd   = bool(r["icd_code"])
        sh        = r["sinh_hieu"]
        has_vital = any(v is not None for v in sh.values())

        if has_drug:  drug_hits  += 1
        if has_icd:   icd_hits   += 1
        if has_vital: vital_hits += 1

        print(f"\n[{fname}] WER={wer:.0%}")
        print(f"  Transcript : {safe(transcript[:80])}")
        if r["transcript_corrected"] != transcript:
            print(f"  Corrected  : {safe(r['transcript_corrected'][:80])}")
        print(f"  Drugs      : {r['drugs_found'] or 'none'}")
        print(f"  Chan doan  : {safe(r['chan_doan']) or 'none'}")
        print(f"  ICD        : {r['icd_code']} {safe(r['icd_display'])}" if r["icd_code"] else "  ICD        : none")
        print(f"  Sinh hieu  : {sh}")
        print(f"  Tai kham   : {safe(r['tai_kham']) or 'none'}")

    n = len(t007)
    print("\n" + "=" * 70)
    print("SUMMARY — Partial CEER")
    print("=" * 70)
    print(f"  Drug extraction  : {drug_hits}/{n} files ({drug_hits/n:.0%})")
    print(f"  ICD match        : {icd_hits}/{n} files ({icd_hits/n:.0%})")
    print(f"  Vital signs      : {vital_hits}/{n} files ({vital_hits/n:.0%})")
    print(f"\n  NOTE: Không có ground truth — đây là coverage, không phải accuracy.")
    print(f"  CEER thật cần pilot audio + ground truth labels.")

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nDetailed: {OUT_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()
