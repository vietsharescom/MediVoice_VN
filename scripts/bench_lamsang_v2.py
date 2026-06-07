#!/usr/bin/env python
# scripts/bench_lamsang_v2.py
# BENCH-002 re-run: DrugCorrectionEngine v2 vs v1 trên cùng ASR transcripts
#
# Dùng cached transcripts từ data/audio/BENCH002_ceer_results.json
# (không cần re-run PhoWhisper)
#
# Usage:
#   python -X utf8 scripts/bench_lamsang_v2.py

import json
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.l1b_drug_correct import (
    correct_drug_names,
    correct_drug_names_v2,
    extract_drug_candidates,
)

CACHE    = Path("data/audio/BENCH002_ceer_results.json")
GT_FILE  = Path("data/audio/ground_truth_lam_sang_template.json")
OUT_FILE = Path("data/audio/BENCH002_v2_results.json")


def _norm(s: str) -> str:
    if not s:
        return ""
    s = s.lower().strip()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.strip()


def _token_match(pred: str, ref: str, threshold: float = 0.6) -> bool:
    if not ref:
        return False
    ref_tok  = set(_norm(ref).split())
    pred_tok = set(_norm(pred).split())
    if not ref_tok:
        return False
    return len(ref_tok & pred_tok) / len(ref_tok) >= threshold


def ceer_drugs(pred_drugs: list[str], ref_drugs: list) -> dict:
    ref  = [r["name"] if isinstance(r, dict) else r for r in ref_drugs]
    tp = fn = fp = 0
    matched = set()
    for r in ref:
        found = False
        for i, p in enumerate(pred_drugs):
            if i not in matched and _token_match(p, r):
                tp += 1; matched.add(i); found = True; break
        if not found:
            fn += 1
    fp = len(pred_drugs) - len(matched)
    total = max(len(ref), 1)
    return {"TP": tp, "FN": fn, "FP": fp, "CEER": round((fn + fp) / total, 3)}


def main() -> None:
    if not CACHE.exists():
        print(f"[ERROR] Cache not found: {CACHE}")
        print("Run: python -X utf8 tools/bench_ceer.py --full --gt data/audio/ground_truth_lam_sang_template.json")
        sys.exit(1)

    with open(CACHE, encoding="utf-8") as f:
        cached = json.load(f)

    gt_map: dict[str, dict] = {}
    if GT_FILE.exists():
        with open(GT_FILE, encoding="utf-8") as f:
            for row in json.load(f):
                gt_map[row["file"]] = row.get("ground_truth", {})

    rows = []
    v1_ceers: list[float] = []
    v2_ceers: list[float] = []

    print("=" * 70)
    print("BENCH-002 — DrugCorrectionEngine v1 vs v2 (cached ASR transcripts)")
    print("=" * 70)
    print(f"{'File':<30} {'v1 CEER':>8} {'v2 CEER':>8}  {'v1 drugs':<25} {'v2 drugs'}")

    for item in cached:
        fname    = item["file"]
        raw_t    = item.get("transcript_corrected", "")
        gt_drugs = gt_map.get(fname, {}).get("drugs", [])

        if not raw_t or not gt_drugs:
            continue

        # v1 (exact only, backward compat)
        corr_v1   = correct_drug_names(raw_t)
        cands_v1  = extract_drug_candidates(corr_v1)
        drugs_v1  = [c["inn"] for c in cands_v1]
        ceer_v1   = ceer_drugs(drugs_v1, gt_drugs)

        # v2 (4-layer fuzzy + phonetic_variants)
        # AUTO: non-flagged → go to prescription directly (CEER metric)
        # FLAGGED: LOW_CONFIDENCE/AMBIGUOUS → BS sees, usually rejects (not in CEER)
        corr_v2, matches_v2 = correct_drug_names_v2(raw_t)
        drugs_v2_auto    = [m.inn for m in matches_v2 if not m.flagged_for_review]
        drugs_v2_flagged = [m.inn for m in matches_v2 if m.flagged_for_review]
        drugs_v2_all     = [m.inn for m in matches_v2]
        ceer_v2   = ceer_drugs(drugs_v2_auto, gt_drugs)   # CEER on AUTO only

        v1_ceers.append(ceer_v1["CEER"])
        v2_ceers.append(ceer_v2["CEER"])

        delta = "✅" if ceer_v2["CEER"] < ceer_v1["CEER"] else ("=" if ceer_v2["CEER"] == ceer_v1["CEER"] else "❌")
        gt_names = [r["name"] if isinstance(r, dict) else r for r in gt_drugs]
        print(f"{fname:<30} {ceer_v1['CEER']:>8.3f} {ceer_v2['CEER']:>8.3f}  {delta}")
        print(f"  GT:      {gt_names}")
        print(f"  v1 AUTO: {drugs_v1}")
        print(f"  v2 AUTO: {drugs_v2_auto}  + flagged(BS review)={drugs_v2_flagged[:3]}{'...' if len(drugs_v2_flagged)>3 else ''}")

        rows.append({
            "file": fname,
            "gt_drugs": gt_names,
            "v1_drugs": drugs_v1,
            "v2_auto": drugs_v2_auto,
            "v2_flagged": drugs_v2_flagged,
            "v1_ceer": ceer_v1,
            "v2_ceer": ceer_v2,
            "v2_matches": [
                {"inn": m.inn, "orig": m.original_text, "conf": round(m.confidence, 3),
                 "layer": m.match_layer, "flagged": m.flagged_for_review, "reason": m.flag_reason}
                for m in matches_v2
            ],
        })

    avg_v1 = sum(v1_ceers) / len(v1_ceers) if v1_ceers else 0.0
    avg_v2 = sum(v2_ceers) / len(v2_ceers) if v2_ceers else 0.0

    print("=" * 70)
    print(f"{'AVERAGE':<30} {avg_v1:>8.3f} {avg_v2:>8.3f}")
    print("=" * 70)
    print(f"\n  v1 Drug CEER avg: {avg_v1:.3f} ({'✅' if avg_v1 <= 0.10 else '🔴'})")
    print(f"  v2 Drug CEER avg: {avg_v2:.3f} ({'✅' if avg_v2 <= 0.10 else ('⚠️' if avg_v2 <= 0.20 else '🔴')})")
    print(f"\n  Improvement: {avg_v1 - avg_v2:+.3f} CEER points ({(avg_v1-avg_v2)/max(avg_v1,0.001)*100:.0f}% reduction)")

    if avg_v2 <= 0.10:
        print("\n  → Drug CEER ≤ 10% ✅  Pilot thật có thể bắt đầu.")
    elif avg_v2 <= 0.20:
        print("\n  → Drug CEER 10-20% ⚠️  Acceptable với BS review — cần BENCH-002b thật.")
    else:
        print("\n  → Drug CEER > 20% 🔴  Cần thêm phonetic_variants hoặc TRAIN-001.")

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump({"avg_v1": avg_v1, "avg_v2": avg_v2, "files": rows}, f,
                  ensure_ascii=False, indent=2)
    print(f"\n  Report → {OUT_FILE}")


if __name__ == "__main__":
    main()
