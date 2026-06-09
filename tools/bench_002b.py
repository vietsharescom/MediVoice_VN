#!/usr/bin/env python3
"""
tools/bench_002b.py — BENCH-002b: WER + CEER trên 57 real-voice clips BS thật (HN/DN/SG)
GT source: data/eval/ref_voice_transcripts_review.txt (Andy điền xong PA-009)

Workflow:
  1. Parse TXT → merge GT vào JSON
  2. Compute WER per clip (jiwer)
  3. Run NER pipeline trên ASR transcript + NOTE text → entities
  4. Compute CEER: Drug Recall, Diag, Vitals, Followup
  5. Aggregate by region (HN/DN/SG) + clip type (Clip1/2/3)
  6. Save data/eval/bench_002b_results.json + print summary

Usage:
    python -X utf8 tools/bench_002b.py
    python -X utf8 tools/bench_002b.py --save-json
"""

import sys, re, json, argparse
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from tools.bench_ceer import extract_entities, ceer_drugs, ceer_diagnosis, ceer_vitals, ceer_followup

REVIEW_TXT = ROOT / "data/eval/ref_voice_transcripts_review.txt"
JSON_FILE  = ROOT / "data/eval/ref_voice_transcripts.json"
OUT_FILE   = ROOT / "data/eval/bench_002b_results.json"


# ─── Parse review TXT ────────────────────────────────────────────────────────

def parse_review_txt(path: Path) -> dict[str, dict]:
    """
    Returns {filename: {asr, gt, note}} from review TXT.
    NOTE field is Andy's clean structured annotation — used as GT for NER.
    """
    text = path.read_text(encoding="utf-8")
    records = {}
    # Split by FILE: blocks
    blocks = re.split(r"\n(?=FILE:)", text)
    for block in blocks:
        fm = re.match(r"FILE:\s*(\S+\.wav)", block)
        if not fm:
            continue
        fname = fm.group(1)
        asr_m  = re.search(r"ASR:\s*(.+?)(?=\nGT:|\nNOTE:|\Z)", block, re.S)
        gt_m   = re.search(r"GT:\s*(.+?)(?=\nNOTE:|\Z)", block, re.S)
        note_m = re.search(r"NOTE:\s*(.+?)(?=\Z)", block, re.S)
        records[fname] = {
            "asr":  asr_m.group(1).strip()  if asr_m  else "",
            "gt":   gt_m.group(1).strip()   if gt_m   else "",
            "note": note_m.group(1).strip() if note_m else "",
        }
    return records


# ─── WER helpers ─────────────────────────────────────────────────────────────

def compute_wer(hyp: str, ref: str) -> float | None:
    """Word Error Rate using jiwer. Returns None if ref empty."""
    if not ref.strip():
        return None
    try:
        import jiwer
        return round(jiwer.wer(ref, hyp), 4)
    except Exception:
        return None


def _norm_for_wer(text: str) -> str:
    """Lowercase + remove punctuation for WER."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


# ─── Clip type classification ─────────────────────────────────────────────────

def clip_type(filename: str) -> int:
    """1=intro, 2=vitals/symptoms, 3=diagnosis/drugs."""
    m = re.search(r"Clip(\d+)", filename, re.I)
    return int(m.group(1)) if m else 0


# ─── Run benchmark ───────────────────────────────────────────────────────────

def run(save_json: bool = False) -> dict:
    print("=" * 70)
    print("BENCH-002b — WER + CEER trên 57 real-voice clips (HN/DN/SG)")
    print("=" * 70)

    # 1. Parse GT
    review = parse_review_txt(REVIEW_TXT)
    print(f"  Parsed GT: {len(review)} clips from TXT")

    # 2. Load + update JSON
    with open(JSON_FILE, encoding="utf-8") as f:
        records = json.load(f)

    for r in records:
        fname = r["file"]
        if fname in review:
            r["transcript_gt"]   = review[fname]["gt"]
            r["transcript_note"] = review[fname]["note"]

    print(f"  Merged GT into {len(records)} JSON records")

    # 3. Process each clip
    results = []
    agg_wer = defaultdict(list)          # region → [wer]
    agg_ceer = defaultdict(lambda: defaultdict(list))  # region → metric → [ceer]
    agg_clip = defaultdict(lambda: defaultdict(list))  # clip_type → metric → [ceer]

    for r in records:
        fname  = r["file"]
        bs     = r["bs"]
        ctype  = clip_type(fname)
        asr    = r.get("transcript_asr", "")
        gt     = r.get("transcript_gt", "")
        note   = r.get("transcript_note", "")

        # WER
        wer_val = compute_wer(_norm_for_wer(asr), _norm_for_wer(gt))
        r["wer"] = wer_val
        if wer_val is not None:
            agg_wer[bs].append(wer_val)
            agg_wer["ALL"].append(wer_val)

        entry = {
            "file": fname, "bs": bs, "clip_type": ctype,
            "duration_s": r.get("duration_s"),
            "wer": wer_val,
        }

        # CEER trên TẤT CẢ clips (không phụ thuộc Clip type)
        # GT text: dùng NOTE nếu có (structured), fallback GT transcript (Andy corrected)
        gt_text = (note if note.strip() else gt).strip()
        if gt_text:
            gt_ents   = extract_entities(gt_text)
            pred_ents = extract_entities(asr)

            entry["pred_drugs"]    = pred_ents["drugs"]
            entry["gt_drugs"]      = gt_ents["drugs"]
            entry["pred_chan_doan"] = pred_ents["chan_doan"]
            entry["gt_chan_doan"]   = gt_ents["chan_doan"]

            # Drug CEER — chỉ tính khi GT NER tìm được drugs (tránh GT miss do spell-out)
            if gt_ents["drugs"]:
                d_res = ceer_drugs(pred_ents["drugs"], gt_ents["drugs"])
                entry["ceer_drug"] = d_res["CEER"]
                entry["drug_tp"]   = d_res["TP"]
                entry["drug_fn"]   = d_res["FN"]
                entry["drug_fp"]   = d_res["FP"]
                agg_ceer[bs]["drug"].append(d_res["CEER"])
                agg_ceer["ALL"]["drug"].append(d_res["CEER"])

            # Diag CEER — chỉ tính khi GT có diagnosis
            if gt_ents["chan_doan"]:
                diag_res = ceer_diagnosis(pred_ents["chan_doan"], gt_ents["chan_doan"])
                entry["ceer_diag"] = diag_res["CEER"]
                agg_ceer[bs]["diag"].append(diag_res["CEER"])
                agg_ceer["ALL"]["diag"].append(diag_res["CEER"])

            # Vitals CEER — chỉ tính khi GT có vitals
            v_res = ceer_vitals(pred_ents["vitals"], gt_ents["vitals"])
            if v_res["CEER"] is not None:
                entry["ceer_vitals"]   = v_res["CEER"]
                entry["vitals_stated"] = v_res["stated"]
                entry["vitals_missed"] = v_res["missed"]
                agg_ceer[bs]["vitals"].append(v_res["CEER"])
                agg_ceer["ALL"]["vitals"].append(v_res["CEER"])

            # Followup CEER
            fup_res = ceer_followup(pred_ents["tai_kham"], gt_ents["tai_kham"])
            if fup_res["CEER"] is not None:
                entry["ceer_followup"] = fup_res["CEER"]
                agg_ceer[bs]["followup"].append(fup_res["CEER"])
                agg_ceer["ALL"]["followup"].append(fup_res["CEER"])

        results.append(entry)

    # ─── Print Summary ────────────────────────────────────────────────────────

    def _avg(lst): return round(sum(lst) / len(lst), 3) if lst else None
    def _fmt(v):
        if v is None: return "  N/A  "
        bar = "✅" if v <= 0.2 else ("⚠️ " if v <= 0.5 else "🔴")
        return f"{v:.3f} {bar}"

    print()
    print("─" * 60)
    print("WER by region (ASR quality):")
    for region in ["HN", "DN", "SG", "ALL"]:
        wers = agg_wer.get(region, [])
        if wers:
            print(f"  {region:4s}: WER {_avg(wers):.3f}  (n={len(wers)})")

    print()
    print("─" * 60)
    print("CEER by region × metric:")
    print(f"  {'Region':6s} {'Drug':10s} {'Diag':10s} {'Vitals':10s} {'Followup':10s}")
    for region in ["HN", "DN", "SG", "ALL"]:
        m = agg_ceer.get(region, {})
        row = [
            _fmt(_avg(m.get("drug", []))),
            _fmt(_avg(m.get("diag", []))),
            _fmt(_avg(m.get("vitals", []))),
            _fmt(_avg(m.get("followup", []))),
        ]
        print(f"  {region:6s} {'  '.join(row)}")

    print()
    print("─" * 60)
    print("Drug detail (all clips where GT NER finds drugs):")
    all_tp = sum(r.get("drug_tp", 0) for r in results)
    all_fn = sum(r.get("drug_fn", 0) for r in results)
    all_fp = sum(r.get("drug_fp", 0) for r in results)
    clips_with_gt_drugs = sum(1 for r in results if r.get("gt_drugs"))
    clips_with_pred_drugs = sum(1 for r in results if r.get("pred_drugs"))
    print(f"  Clips where GT NER found drugs: {clips_with_gt_drugs}/57")
    print(f"  Clips where ASR pipeline found drugs: {clips_with_pred_drugs}/57")
    if all_tp + all_fn > 0:
        recall    = round(all_tp / (all_tp + all_fn), 3)
        precision = round(all_tp / max(all_tp + all_fp, 1), 3)
        print(f"  TP={all_tp}  FN={all_fn}  FP={all_fp}")
        print(f"  Drug Recall={recall}  Precision={precision}")

    # NOTE: GT drug miss analysis — drugs NER miss due to phonetic spelling
    print()
    print("  ⚠️  NOTE: BS spell drug names phonetically (MÉt PHỐT min, Tam su lÔ Xin)")
    print("       GT NER miss = undercount GT. Actual recall likely lower.")
    print("       → RAG-001 hybrid fix addresses this (see drug_rag.py)")

    # FN breakdown — which drugs were missed
    missed_drugs = []
    for r in results:
        gt_d = r.get("gt_drugs", [])
        pred_d = set(r.get("pred_drugs", []))
        for d in gt_d:
            if not any(_tok_match_simple(d, p) for p in pred_d):
                missed_drugs.append(d)
    if missed_drugs:
        from collections import Counter
        mc = Counter(missed_drugs)
        print(f"  Missed drugs (top): {dict(mc.most_common(8))}")

    print()
    print("─" * 60)
    print(f"  Total clips: {len(results)}")
    print(f"  Clip1 (intro): {sum(1 for r in results if r['clip_type']==1)}")
    print(f"  Clip2 (vitals): {sum(1 for r in results if r['clip_type']==2)}")
    print(f"  Clip3 (drugs/diag): {sum(1 for r in results if r['clip_type']==3)}")

    # Save
    output = {
        "version": "BENCH-002b-v1",
        "total_clips": len(results),
        "wer_by_region": {r: _avg(v) for r, v in agg_wer.items()},
        "ceer_by_region": {
            region: {m: _avg(vals) for m, vals in metrics.items()}
            for region, metrics in agg_ceer.items()
        },
        "drug_aggregate": {
            "tp": all_tp, "fn": all_fn, "fp": all_fp,
            "recall": round(all_tp / max(all_tp + all_fn, 1), 3),
            "precision": round(all_tp / max(all_tp + all_fp, 1), 3),
        },
        "per_clip": results,
    }

    if save_json:
        OUT_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        JSON_FILE.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n  Saved: {OUT_FILE}")
        print(f"  Updated: {JSON_FILE}")

    return output


def _tok_match_simple(a: str, b: str, threshold: float = 0.5) -> bool:
    import unicodedata
    def norm(s):
        s = s.lower()
        s = unicodedata.normalize("NFD", s)
        s = re.sub(r"[̀-ͯ]", "", s)
        return set(s.split())
    a_toks, b_toks = norm(a), norm(b)
    if not a_toks: return False
    return len(a_toks & b_toks) / len(a_toks) >= threshold


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--save-json", action="store_true", help="Save results to JSON files")
    args = parser.parse_args()
    run(save_json=args.save_json)
