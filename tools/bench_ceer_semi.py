#!/usr/bin/env python3
"""
tools/bench_ceer_semi.py — CEER trên 30 files semi_synthetic (HN/SG/CT).
Đọc groundtruth_all.json → ASR → NER → CEER theo region và scenario.

Usage:
    python tools/bench_ceer_semi.py
"""
import sys, json, os
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from tools.bench_ceer import (
    extract_entities, ceer_drugs, ceer_diagnosis, ceer_vitals, ceer_followup
)

GT_FILE  = Path("data/audio/corpus/semi_synthetic/groundtruth_all.json")
SEMI_DIR = Path("data/audio/corpus/semi_synthetic")
REGIONS  = {"HN", "SG", "CT"}  # CA bỏ


def transcribe_wav(wav_path: Path) -> str:
    import numpy as np, soundfile as sf
    from core.l1a_asr import transcribe
    audio, sr = sf.read(str(wav_path), dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    return transcribe(audio, sr)


def normalize_gt(gt: dict) -> dict:
    """Convert groundtruth_all.json format → bench_ceer format."""
    sh = gt.get("sinh_hieu", {})
    ha = sh.get("huyet_ap")
    return {
        "drugs":    [d["ten"] for d in gt.get("thuoc", [])],
        "chan_doan": gt.get("chan_doan", ""),
        "vitals": {
            "huyet_ap": ha,
            "nhiet_do": sh.get("nhiet_do"),
            "mach":     sh.get("mach"),
            "can_nang": sh.get("can_nang"),
        },
        "tai_kham": gt.get("tai_kham", ""),
    }


def main():
    with open(GT_FILE, encoding="utf-8") as f:
        data = json.load(f)

    cases = [c for c in data["test_cases"] if c["region"] in REGIONS]

    print("=" * 68)
    print("  BENCH-002a — CEER Semi-Synthetic | MediVoice VN")
    print(f"  Cases: {len(cases)} (HN/SG/CT × 5 SC × take1)")
    print("=" * 68)
    print("  [INFO] Loading PhoWhisper-medium (~30s)...")

    by_region:   dict[str, list] = defaultdict(list)
    by_scenario: dict[str, list] = defaultdict(list)
    all_results = []

    for case in cases:
        region = case["region"]
        sc     = case["script_id"]
        wav    = SEMI_DIR / region / f"{sc.replace('-','').replace('SC','SC'[:2])}_{region}_take1.wav"

        # Build path: SC-01 → SC01_HN_take1.wav
        sc_code = sc.replace("SC-", "SC").replace("-", "")  # SC-01 → SC01
        wav = SEMI_DIR / region / f"{sc_code}_{region}_take1.wav"

        if not wav.exists():
            print(f"\n  [SKIP] {wav.name} — file không tồn tại")
            continue

        print(f"\n  [{wav.name}]")
        hyp = transcribe_wav(wav)
        if not hyp:
            print("    [SKIP] Transcript rỗng")
            continue

        ref_norm = normalize_gt(case["ground_truth"])
        ents     = extract_entities(hyp)

        drug_r  = ceer_drugs(ents["drugs"], ref_norm["drugs"])
        diag_r  = ceer_diagnosis(ents["chan_doan"], ref_norm["chan_doan"])
        vital_r = ceer_vitals(ents["vitals"], ref_norm["vitals"])
        fup_r   = ceer_followup(ents["tai_kham"], ref_norm["tai_kham"])

        print(f"    HYP: {hyp[:80]}")
        print(f"    Drug CEER:{drug_r['CEER']}  Diag CEER:{diag_r['CEER']}  "
              f"Vital CEER:{vital_r['CEER']}  Fup CEER:{fup_r['CEER']}")

        r = {"region": region, "sc": sc,
             "drug": drug_r["CEER"], "diag": diag_r["CEER"],
             "vital": vital_r["CEER"], "fup": fup_r["CEER"]}
        all_results.append(r)
        by_region[region].append(r)
        by_scenario[sc].append(r)

    if not all_results:
        print("\n  Không có kết quả.")
        return

    def avg(lst): return round(sum(x for x in lst if x is not None) /
                               max(sum(1 for x in lst if x is not None), 1), 3)

    print("\n" + "=" * 68)
    print("  TỔNG KẾT CEER")
    print("=" * 68)

    print("\n  Theo Region:")
    for r in sorted(by_region):
        rows = by_region[r]
        print(f"    {r}: Drug={avg([x['drug'] for x in rows])}  "
              f"Diag={avg([x['diag'] for x in rows])}  "
              f"Vital={avg([x['vital'] for x in rows])}  "
              f"Fup={avg([x['fup'] for x in rows])}")

    print("\n  Theo Scenario:")
    for sc in sorted(by_scenario):
        rows = by_scenario[sc]
        print(f"    {sc}: Drug={avg([x['drug'] for x in rows])}  "
              f"Diag={avg([x['diag'] for x in rows])}")

    all_drug  = avg([x["drug"] for x in all_results])
    all_diag  = avg([x["diag"] for x in all_results])
    all_vital = avg([x["vital"] for x in all_results])
    all_fup   = avg([x["fup"] for x in all_results])

    print(f"\n  OVERALL: Drug={all_drug}  Diag={all_diag}  "
          f"Vital={all_vital}  Fup={all_fup}")

    max_ceer = max(c for c in [all_drug, all_diag] if c is not None)
    print()
    if max_ceer <= 0.05:
        print("  → CEER ≤ 5% ✅  Pipeline đủ tốt cho pilot.")
    elif max_ceer <= 0.10:
        print("  → CEER 5–10% ⚠️  Dùng được, BS review kỹ.")
    else:
        print("  → CEER > 10% 🔴  Cần TRAIN-001 trước pilot.")
    print("=" * 68)


if __name__ == "__main__":
    main()
