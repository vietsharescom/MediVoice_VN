#!/usr/bin/env python3
"""
tools/eval_ref_voices.py — WER + CEER trên 9 reference voice clips (BS thật HN/DN/SG)
Ground truth từ docs/dev/REFERENCE_VOICE_GUIDE.md

Usage:
    python -X utf8 tools/eval_ref_voices.py
"""
import sys, re
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REF_DIR = ROOT / "data" / "audio" / "reference_voices"

# Ground truth (Clip1 bỏ vì có tên BS biến đổi)
GT = {
    "Clip2": (
        "bệnh nhân vào khám với triệu chứng đau họng ba ngày nay sốt nhẹ không có ho "
        "huyết áp một trăm hai mươi trên tám mươi mạch tám mươi "
        "nhiệt độ ba mươi bảy phẩy tám độ"
    ),
    "Clip3": (
        "kê amoxicillin năm trăm miligam uống ba lần một ngày trong năm ngày "
        "paracetamol năm trăm miligam uống khi sốt trên ba mươi tám độ "
        "tái khám sau năm ngày hoặc sớm hơn nếu sốt cao không hạ"
    ),
}

# Expected NER output cho CEER
GT_ENTITIES = {
    "Clip2": {
        "huyet_ap": "120/80",
        "mach": "80",
        "nhiet_do": "37.8",
        "trieu_chung": ["đau họng", "sốt nhẹ"],
    },
    "Clip3": {
        "thuoc": [
            {"ten": "Amoxicillin", "lieu": "500mg", "tan_suat": "3 lần/ngày", "thoi_gian": "5 ngày"},
            {"ten": "Paracetamol", "lieu": "500mg", "dieu_kien": "khi sốt >38°C"},
        ],
        "tai_kham": "5 ngày",
    },
}

SPEAKERS = [
    ("HN", REF_DIR / "BS_hanoi"),
    ("DN", REF_DIR / "BS_danang"),
    ("SG", REF_DIR / "BS_saigon"),
]


def normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[,\.\!\?;:\-\—\–\"\'\"\"']", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def wer(ref: str, hyp: str) -> float:
    """Word Error Rate: (S+D+I) / N"""
    r = normalize(ref).split()
    h = normalize(hyp).split()
    n = len(r)
    if n == 0:
        return 0.0
    # DP edit distance
    d = [[0] * (len(h) + 1) for _ in range(len(r) + 1)]
    for i in range(len(r) + 1):
        d[i][0] = i
    for j in range(len(h) + 1):
        d[0][j] = j
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            if r[i - 1] == h[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                d[i][j] = 1 + min(d[i - 1][j], d[i][j - 1], d[i - 1][j - 1])
    return d[len(r)][len(h)] / n


def transcribe_wav(wav_path: Path) -> str:
    import numpy as np
    import soundfile as sf
    from core.l1a_asr import transcribe
    audio, sr = sf.read(str(wav_path), dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    return transcribe(audio, sr)


def eval_ner(hyp_text: str, clip_id: str) -> dict:
    """Run NER pipeline on hypothesis transcript, compare to GT entities."""
    from core.l1b_drug_correct import correct_drug_names
    from core.l1c_ner import extract_entities

    corrected = correct_drug_names(hyp_text)
    entities = extract_entities(corrected)

    gt = GT_ENTITIES.get(clip_id, {})
    results = {}

    if clip_id == "Clip2":
        # Vital check
        results["huyet_ap_ok"] = bool(entities.get("huyet_ap")) and entities.get("huyet_ap") == gt["huyet_ap"]
        results["mach_ok"] = bool(entities.get("mach")) and str(entities.get("mach", "")) == gt["mach"]
        results["nhiet_do_ok"] = bool(entities.get("nhiet_do"))
        results["trieu_chung_found"] = len(entities.get("trieu_chung", [])) > 0
        results["huyet_ap_val"] = entities.get("huyet_ap", "❌")
        results["mach_val"] = entities.get("mach", "❌")
        results["nhiet_do_val"] = entities.get("nhiet_do", "❌")
        results["trieu_chung_val"] = entities.get("trieu_chung", [])

    elif clip_id == "Clip3":
        # Drug + followup check
        drugs = entities.get("thuoc", [])
        drug_names = [d.get("ten", "").lower() for d in drugs]
        results["amox_found"] = any("amoxicillin" in n or "amox" in n for n in drug_names)
        results["para_found"] = any("paracetamol" in n or "para" in n for n in drug_names)
        results["tai_kham_found"] = bool(entities.get("tai_kham"))
        results["n_drugs"] = len(drugs)
        results["drugs_val"] = [(d.get("ten", "?"), d.get("lieu_dung", "?")) for d in drugs]
        results["tai_kham_val"] = entities.get("tai_kham", "❌")

    return results


def main():
    print("=" * 65)
    print("  eval_ref_voices.py — WER + NER trên Audio Thật BS")
    print("  MediVoice VN | 9 clips: HN / DN / SG × Clip1-3")
    print("=" * 65)

    all_wer = []
    clip2_results = []
    clip3_results = []

    for spk_id, spk_dir in SPEAKERS:
        print(f"\n{'─'*50}")
        print(f"  [{spk_id}] {spk_dir.name}")
        print(f"{'─'*50}")

        for clip_num in [1, 2, 3]:
            clip_id = f"Clip{clip_num}"
            wav = spk_dir / f"REF_{spk_id}_{clip_id}.wav"

            if not wav.exists():
                print(f"  [{clip_id}] ❌ File không tồn tại: {wav.name}")
                continue

            import soundfile as sf
            info = sf.info(str(wav))
            dur = info.frames / info.samplerate
            print(f"\n  [{clip_id}] {wav.name} ({dur:.1f}s)")

            print(f"    Transcribing...", end="", flush=True)
            try:
                hyp = transcribe_wav(wav)
                print(f" done")
            except Exception as e:
                print(f"\n    ❌ ASR error: {e}")
                continue

            print(f"    HYP: {hyp[:80]}{'...' if len(hyp) > 80 else ''}")

            if clip_id in GT:
                ref = GT[clip_id]
                w = wer(ref, hyp)
                all_wer.append((spk_id, clip_id, w))
                status = "✅" if w < 0.15 else ("⚠️" if w < 0.30 else "🔴")
                print(f"    WER: {w:.1%} {status}  (ref: {len(ref.split())} words)")

                # NER eval
                try:
                    ner_res = eval_ner(hyp, clip_id)
                    if clip_id == "Clip2":
                        print(f"    Vital → HA:{ner_res['huyet_ap_val']} | Mạch:{ner_res['mach_val']} | T°:{ner_res['nhiet_do_val']}")
                        print(f"    Triệu chứng: {ner_res['trieu_chung_val']}")
                        clip2_results.append((spk_id, ner_res))
                    elif clip_id == "Clip3":
                        print(f"    Thuốc ({ner_res['n_drugs']} tìm được): {ner_res['drugs_val']}")
                        print(f"    Tái khám: {ner_res['tai_kham_val']}")
                        a = "✅" if ner_res["amox_found"] else "❌"
                        p = "✅" if ner_res["para_found"] else "❌"
                        t = "✅" if ner_res["tai_kham_found"] else "❌"
                        print(f"    Amoxicillin:{a} Paracetamol:{p} Tái khám:{t}")
                        clip3_results.append((spk_id, ner_res))
                except Exception as e:
                    print(f"    NER error: {e}")
            else:
                print(f"    WER: N/A (Clip1 — tên BS biến đổi)")

    # Tổng kết
    print(f"\n{'=' * 65}")
    print("  TỔNG KẾT — WER AUDIO THẬT BS")
    print(f"{'=' * 65}")
    if all_wer:
        print(f"\n  {'BS':<6} {'Clip':<7} {'WER':<10} {'Status'}")
        print(f"  {'─'*40}")
        for spk, clip, w in all_wer:
            s = "✅ <15%" if w < 0.15 else ("⚠️ <30%" if w < 0.30 else "🔴 ≥30%")
            print(f"  {spk:<6} {clip:<7} {w:.1%}{'':5} {s}")
        avg = sum(w for _, _, w in all_wer) / len(all_wer)
        print(f"\n  Average WER: {avg:.1%}")
        print(f"  Target WER < 15% (sau fine-tune): {'✅ đạt' if avg < 0.15 else '🔴 chưa đạt (pre fine-tune)'}")

    print(f"\n  {'=' * 63}")
    print("  CEER DRUG CLIP3 — AUDIO THẬT BS")
    print(f"  {'=' * 63}")
    if clip3_results:
        amox_ok = sum(1 for _, r in clip3_results if r["amox_found"])
        para_ok = sum(1 for _, r in clip3_results if r["para_found"])
        tk_ok = sum(1 for _, r in clip3_results if r["tai_kham_found"])
        n = len(clip3_results)
        print(f"  Amoxicillin detected: {amox_ok}/{n} BS")
        print(f"  Paracetamol detected: {para_ok}/{n} BS")
        print(f"  Tái khám detected:    {tk_ok}/{n} BS")

    print(f"\n  {'=' * 63}")
    print("  CEER VITAL CLIP2 — AUDIO THẬT BS")
    print(f"  {'=' * 63}")
    if clip2_results:
        ha_ok = sum(1 for _, r in clip2_results if r["huyet_ap_ok"])
        mach_ok = sum(1 for _, r in clip2_results if r["mach_ok"])
        nhiet_ok = sum(1 for _, r in clip2_results if r["nhiet_do_ok"])
        tc_ok = sum(1 for _, r in clip2_results if r["trieu_chung_found"])
        n = len(clip2_results)
        print(f"  Huyết áp chính xác: {ha_ok}/{n} BS")
        print(f"  Mạch chính xác:     {mach_ok}/{n} BS")
        print(f"  Nhiệt độ found:     {nhiet_ok}/{n} BS")
        print(f"  Triệu chứng found:  {tc_ok}/{n} BS")

    print("=" * 65)


if __name__ == "__main__":
    main()
