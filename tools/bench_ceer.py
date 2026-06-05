#!/usr/bin/env python3
"""
tools/bench_ceer.py — BENCH-002: Clinical Entity Error Rate
Đo CEER thật trên audio pilot BS nói.

Chạy partial (không cần ground truth — coverage only):
    python tools/bench_ceer.py --partial

Chạy full CEER (cần data/audio/ground_truth.json):
    python tools/bench_ceer.py --full

Chỉ 1 file cụ thể:
    python tools/bench_ceer.py --partial --file test_medivoice_04.wav
"""

import os, sys, json, argparse, unicodedata, re
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from src.core import l1b_drug_correct, l1c_ner, l1d_icd_lookup

AUDIO_DIR   = os.path.join("data", "audio")
GT_FILE     = os.path.join("data", "audio", "ground_truth.json")
REPORT_FILE = os.path.join("data", "audio", "BENCH002_ceer_results.json")

# ─── Normalise helpers ────────────────────────────────────────────────────────

def _norm(s: str) -> str:
    """Lowercase, strip diacritics for fuzzy match."""
    if not s:
        return ""
    s = s.lower().strip()
    s = unicodedata.normalize("NFD", s)
    s = re.sub(r"[̀-ͯ]", "", s)
    return s.strip()


def _token_match(pred: str, ref: str, threshold: float = 0.6) -> bool:
    """True if >=threshold fraction of ref tokens appear in pred."""
    if not ref:
        return False
    ref_tokens  = set(_norm(ref).split())
    pred_tokens = set(_norm(pred).split())
    if not ref_tokens:
        return False
    overlap = len(ref_tokens & pred_tokens) / len(ref_tokens)
    return overlap >= threshold


# ─── Entity extraction from transcript ───────────────────────────────────────

def extract_entities(transcript: str) -> dict:
    corrected  = l1b_drug_correct.correct_drug_names(transcript)
    drug_cands = l1b_drug_correct.extract_drug_candidates(corrected)
    ents       = l1c_ner.extract_entities(corrected, drug_cands)
    icd_code, icd_display = l1d_icd_lookup.auto_lookup(ents.chan_doan)
    return {
        "transcript_corrected": corrected,
        "drugs":    [d["inn"] for d in drug_cands],
        "chan_doan": ents.chan_doan or "",
        "icd_code": icd_code or "",
        "vitals": {
            "huyet_ap":  f"{ents.huyet_ap_tam_thu}/{ents.huyet_ap_tam_truong}"
                         if ents.huyet_ap_tam_thu else None,
            "nhiet_do":  ents.nhiet_do,
            "mach":      ents.mach,
            "spo2":      ents.spo2,
            "can_nang":  ents.can_nang,
        },
        "tai_kham": ents.tai_kham or "",
    }


# ─── CEER calculation ─────────────────────────────────────────────────────────

def ceer_drugs(pred_drugs: list, ref_drugs: list) -> dict:
    """
    Drug CEER: entity-level.
    TP = ref drug found in pred (fuzzy), FN = missed, FP = spurious.
    CEER = (FP + FN) / max(len(ref), 1)
    """
    ref  = [r["name"] if isinstance(r, dict) else r for r in ref_drugs]
    pred = pred_drugs[:]
    tp = fn = fp = 0
    matched_pred = set()
    for r in ref:
        found = False
        for i, p in enumerate(pred):
            if i not in matched_pred and _token_match(p, r):
                tp += 1
                matched_pred.add(i)
                found = True
                break
        if not found:
            fn += 1
    fp = len(pred) - len(matched_pred)
    total = max(len(ref), 1)
    return {"TP": tp, "FN": fn, "FP": fp, "CEER": round((fn + fp) / total, 3)}


def ceer_diagnosis(pred_chan_doan: str, ref_chan_doan: str) -> dict:
    """Diagnosis CEER: 0.0 = correct, 1.0 = wrong."""
    match = _token_match(pred_chan_doan, ref_chan_doan)
    return {"match": match, "CEER": 0.0 if match else 1.0}


def ceer_vitals(pred_vitals: dict, ref_vitals: dict) -> dict:
    """Vital signs CEER: fraction of stated vitals that were missed."""
    if not ref_vitals:
        return {"stated": 0, "missed": 0, "CEER": None}
    stated = sum(1 for v in ref_vitals.values() if v is not None)
    if stated == 0:
        return {"stated": 0, "missed": 0, "CEER": None}
    missed = 0
    for k, ref_val in ref_vitals.items():
        if ref_val is None:
            continue
        pred_val = pred_vitals.get(k)
        if pred_val is None:
            missed += 1
    return {"stated": stated, "missed": missed, "CEER": round(missed / stated, 3)}


def ceer_followup(pred: str, ref: str) -> dict:
    if not ref:
        return {"CEER": None}
    match = bool(ref) and _token_match(pred, ref)
    return {"match": match, "CEER": 0.0 if match else 1.0}


# ─── Per-file runners ─────────────────────────────────────────────────────────

def run_partial(transcript: str, filename: str) -> dict:
    """Coverage only — no ground truth needed."""
    ents = extract_entities(transcript)
    has_drug   = len(ents["drugs"]) > 0
    has_icd    = bool(ents["icd_code"])
    has_vital  = any(v is not None for v in ents["vitals"].values())
    has_follow = bool(ents["tai_kham"])
    return {
        "file": filename, "mode": "partial",
        "transcript_corrected": ents["transcript_corrected"],
        "entities": ents,
        "coverage": {
            "drug":     has_drug,
            "icd":      has_icd,
            "vital":    has_vital,
            "followup": has_follow,
        },
    }


def run_full(transcript: str, filename: str, gt: dict) -> dict:
    """Full CEER against ground truth."""
    ents = extract_entities(transcript)
    ref  = gt.get("ground_truth", {})
    drug_r  = ceer_drugs(ents["drugs"], ref.get("drugs", []))
    diag_r  = ceer_diagnosis(ents["chan_doan"], ref.get("chan_doan", ""))
    vital_r = ceer_vitals(ents["vitals"], ref.get("vitals", {}))
    fup_r   = ceer_followup(ents["tai_kham"], ref.get("tai_kham", ""))
    return {
        "file": filename, "mode": "full",
        "transcript_corrected": ents["transcript_corrected"],
        "entities": ents,
        "ceer": {
            "drug":      drug_r,
            "diagnosis": diag_r,
            "vitals":    vital_r,
            "followup":  fup_r,
        },
    }


# ─── Transcription (reuse existing T007 results if available) ─────────────────

def _ensure_db_key():
    if not os.environ.get("MEDIVOICE_DB_KEY"):
        from cryptography.fernet import Fernet
        os.environ["MEDIVOICE_DB_KEY"] = Fernet.generate_key().decode()


def _live_transcribe(wav_path: str) -> str:
    """Run L0 → L1 ASR on a WAV file. Returns transcript text or ''."""
    _ensure_db_key()
    try:
        from src.pipeline.p0_ingestion.l0_input import handle as l0
        from src.pipeline.p1_processing.l1_semantic import handle as l1
        payload = {
            "source": "audio_file",
            "audio_path": wav_path,
            "session_id": "bench002",
            "doctor_id": "bench",
            "consent_given": True,
            "purpose": "medical_documentation",
        }
        r0 = l0(payload)
        if not r0.get("ok"):
            print(f"    [WARN] L0 failed: {r0.get('error')} — {r0.get('message','')}")
            return ""
        r1 = l1(r0["data"])
        if not r1.get("ok"):
            print(f"    [WARN] L1 failed: {r1.get('error')} — {r1.get('message','')}")
            return ""
        # L1 returns 'transcript' (str) or 'original_text' — not 'original_transcript'
        return r1["data"].get("transcript") or r1["data"].get("original_text", "")
    except Exception as e:
        print(f"    [WARN] Transcription exception: {e}")
        return ""


def load_transcripts(target_file: str = None, whitelist: set = None) -> dict:
    """
    Returns {filename: transcript_text}.
    Tries T007_eval_results.json cache first (fast), then live PhoWhisper ASR.
    whitelist: if set, only process files in this set (used with --gt flag).
    """
    t007_path = os.path.join(AUDIO_DIR, "T007_eval_results.json")
    cache = {}
    if os.path.exists(t007_path):
        with open(t007_path, encoding="utf-8") as f:
            for row in json.load(f):
                cache[row["file"]] = row["phowhisper"]["text"]

    wavs = sorted([
        f for f in os.listdir(AUDIO_DIR)
        if f.endswith(".wav")
        and (f == target_file if target_file else True)
        and (f in whitelist if whitelist else True)
    ])

    result = {}
    for fname in wavs:
        if fname in cache:
            result[fname] = cache[fname]
        else:
            wav_path = os.path.join(AUDIO_DIR, fname)
            print(f"    Transcribing {fname} (PhoWhisper, lần đầu ~30s)...")
            text = _live_transcribe(wav_path)
            if text:
                result[fname] = text
                print(f"    → {text[:80].encode('ascii','replace').decode()}")
            else:
                print(f"    [SKIP] Transcription trả về rỗng")
    return result


# ─── Summary stats ────────────────────────────────────────────────────────────

def print_summary_partial(results: list):
    n = len(results)
    if n == 0:
        return
    cov = defaultdict(int)
    for r in results:
        for k, v in r["coverage"].items():
            if v:
                cov[k] += 1
    print("\n" + "=" * 65)
    print("BENCH-002 — PARTIAL CEER (Coverage, không có ground truth)")
    print("=" * 65)
    print(f"  Files analysed : {n}")
    print(f"  Drug detected  : {cov['drug']}/{n}  ({cov['drug']/n:.0%})")
    print(f"  ICD matched    : {cov['icd']}/{n}   ({cov['icd']/n:.0%})")
    print(f"  Vitals found   : {cov['vital']}/{n}  ({cov['vital']/n:.0%})")
    print(f"  Follow-up found: {cov['followup']}/{n}  ({cov['followup']/n:.0%})")
    print()
    print("  NOTE: Coverage ≠ Accuracy. Cần ground_truth.json cho CEER thật.")
    print(f"  Template: data/audio/ground_truth_template.json")
    print("=" * 65)


def print_summary_full(results: list):
    n = len(results)
    if n == 0:
        return
    drug_ceer  = [r["ceer"]["drug"]["CEER"]  for r in results]
    diag_ceer  = [r["ceer"]["diagnosis"]["CEER"] for r in results]
    vital_ceer = [r["ceer"]["vitals"]["CEER"] for r in results if r["ceer"]["vitals"]["CEER"] is not None]
    fup_ceer   = [r["ceer"]["followup"]["CEER"] for r in results if r["ceer"]["followup"]["CEER"] is not None]

    def avg(lst): return round(sum(lst)/len(lst), 3) if lst else None

    drug_avg  = avg(drug_ceer)
    diag_avg  = avg(diag_ceer)
    vital_avg = avg(vital_ceer)
    fup_avg   = avg(fup_ceer)

    vitals_stated = any(r["ceer"]["vitals"]["stated"] > 0 for r in results)

    print("\n" + "=" * 65)
    print("BENCH-002 — FULL CEER (vs. ground truth)")
    print("=" * 65)
    print(f"  Files          : {n}")
    print(f"  Drug CEER      : {drug_avg}  (0=perfect, 1=all wrong)")
    print(f"  Diagnosis CEER : {diag_avg}")
    if vital_avg is not None:
        print(f"  Vitals CEER    : {vital_avg}")
    elif not vitals_stated:
        print(f"  Vitals CEER    : N/A (không có vitals trong ground truth)")
    if fup_avg is not None:
        print(f"  Follow-up CEER : {fup_avg}")

    # Decision logic per BENCH-002 spec
    max_ceer = max(c for c in [drug_avg, diag_avg] if c is not None)
    print()
    if max_ceer is not None:
        if max_ceer <= 0.05:
            print("  → CEER ≤ 5% ✅  Launch pilot trả tiền ngay.")
        elif max_ceer <= 0.10:
            print("  → CEER 5–10% ⚠️  Launch với cảnh báo BS review kỹ.")
        else:
            print("  → CEER > 10% 🔴  Cần TRAIN-001 (fine-tune PhoWhisper) trước.")
    print("=" * 65)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="BENCH-002: Clinical Entity Error Rate")
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--partial", action="store_true", help="Coverage only (không cần ground truth)")
    grp.add_argument("--full",    action="store_true", help="Full CEER vs. ground truth JSON")
    parser.add_argument("--file", default=None, help="Chỉ chạy 1 file (vd: test_medivoice_04.wav)")
    parser.add_argument("--gt",   default=None,
                        help="Custom ground truth JSON (default: data/audio/ground_truth.json)")
    args = parser.parse_args()

    gt_file = args.gt if args.gt else GT_FILE
    if args.full and not os.path.exists(gt_file):
        print(f"[ERROR] Ground truth không tìm thấy: {gt_file}")
        print(f"        Dùng --gt để chỉ file khác, hoặc chạy:")
        print(f"        python tools/gen_test_audio.py --input data/audio/ground_truth_lam_sang_template.json")
        sys.exit(1)

    print("=" * 65)
    print("BENCH-002 — Clinical Entity Error Rate | MediVoice VN")
    mode = "PARTIAL (coverage)" if args.partial else "FULL CEER"
    print(f"Mode: {mode}  |  File: {args.file or 'all'}")
    print("=" * 65)

    # Build whitelist from GT template when --gt is used
    gt_whitelist = None
    if args.gt and args.full:
        with open(gt_file, encoding="utf-8") as f:
            gt_whitelist = {row["file"] for row in json.load(f)}

    # Load transcripts
    transcripts = load_transcripts(args.file, whitelist=gt_whitelist)
    if not transcripts:
        print(f"[ERROR] Không tìm thấy file WAV trong {AUDIO_DIR}/")
        sys.exit(1)

    # Load ground truth if full mode
    gt_map = {}
    if args.full:
        with open(gt_file, encoding="utf-8") as f:
            for row in json.load(f):
                gt_map[row["file"]] = row

    results = []
    for fname, transcript in transcripts.items():
        print(f"\n  [{fname}]")
        if not transcript:
            print("    [SKIP] Không có transcript")
            continue
        safe_t = transcript[:80].encode("ascii", "replace").decode()
        print(f"    Transcript: {safe_t}...")

        if args.partial:
            r = run_partial(transcript, fname)
            cov = r["coverage"]
            print(f"    Drug:{cov['drug']}  ICD:{cov['icd']}  Vital:{cov['vital']}  Follow:{cov['followup']}")
        else:
            if fname not in gt_map:
                print(f"    [SKIP] Không có ground truth cho file này")
                continue
            r = run_full(transcript, fname, gt_map[fname])
            c = r["ceer"]
            print(f"    Drug CEER:{c['drug']['CEER']}  Diag CEER:{c['diagnosis']['CEER']}")
        results.append(r)

    # Summary
    if args.partial:
        print_summary_partial(results)
    else:
        print_summary_full(results)

    # Save report
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n  Report: {REPORT_FILE}")


if __name__ == "__main__":
    main()
