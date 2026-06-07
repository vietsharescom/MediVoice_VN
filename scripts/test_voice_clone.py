#!/usr/bin/env python
# scripts/test_voice_clone.py
# CONS-002-SPRINT6 — Test F5-TTS voice cloning từ reference voices 3 BS
#
# Usage:
#   python -X utf8 scripts/test_voice_clone.py
#
# Output: data/audio/reference_voices/test_output/TEST_*.wav

import sys
import time
from pathlib import Path

import soundfile as sf

sys.path.insert(0, str(Path(__file__).parent.parent))

REF_DIR = Path("data/audio/reference_voices")
OUT_DIR = Path("data/audio/reference_voices/test_output")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Reference voice: Clip 3 (kê đơn) — phù hợp nhất với nội dung y tế
SPEAKERS = [
    {
        "id": "HN",
        "ref_file": REF_DIR / "BS_hanoi" / "REF_HN_Clip3.wav",
        "ref_text": (
            "Kê Amoxicillin năm trăm miligam, uống ba lần một ngày trong năm ngày. "
            "Paracetamol năm trăm miligam uống khi sốt trên ba mươi tám độ. "
            "Tái khám sau năm ngày, hoặc sớm hơn nếu sốt cao không hạ."
        ),
    },
    {
        "id": "DN",
        "ref_file": REF_DIR / "BS_danang" / "REF_DN_Clip3.wav",
        "ref_text": (
            "Kê Amoxicillin năm trăm miligam, uống ba lần một ngày trong năm ngày. "
            "Paracetamol năm trăm miligam uống khi sốt trên ba mươi tám độ. "
            "Tái khám sau năm ngày, hoặc sớm hơn nếu sốt cao không hạ."
        ),
    },
    {
        "id": "SG",
        "ref_file": REF_DIR / "BS_saigon" / "REF_SG_Clip3.wav",
        "ref_text": (
            "Kê Amoxicillin năm trăm miligam, uống ba lần một ngày trong năm ngày. "
            "Paracetamol năm trăm miligam uống khi sốt trên ba mươi tám độ. "
            "Tái khám sau năm ngày, hoặc sớm hơn nếu sốt cao không hạ."
        ),
    },
]

# Câu test generate — ngắn để chạy nhanh trên CPU
TEST_SENTENCES = [
    {
        "id": "drug_simple",
        "text": "Kê Metformin năm trăm miligam, uống hai lần một ngày sau ăn.",
    },
    {
        "id": "drug_complex",
        "text": (
            "Amlodipine năm miligam, uống một viên mỗi sáng. "
            "Losartan năm mươi miligam, uống một lần một ngày."
        ),
    },
]


def main():
    print("=" * 60)
    print("  CONS-002-SPRINT6 — F5-TTS Voice Clone Test")
    print("  MediVoice VN | 3 BS: HN / DN / SG")
    print("=" * 60)

    print("\n  [INFO] Loading F5-TTS model (download ~1.2GB nếu lần đầu)...")
    t0 = time.time()
    try:
        from f5_tts.api import F5TTS
        tts = F5TTS(device="cpu")
    except Exception as e:
        print(f"  [ERROR] F5TTS init failed: {e}")
        sys.exit(1)
    print(f"  [OK] Model loaded in {time.time()-t0:.1f}s")

    results = []

    for spk in SPEAKERS:
        if not spk["ref_file"].exists():
            print(f"\n  [SKIP] {spk['id']}: {spk['ref_file'].name} not found")
            continue

        ref_info = sf.info(str(spk["ref_file"]))
        ref_dur = ref_info.frames / ref_info.samplerate
        print(f"\n  [{spk['id']}] ref={spk['ref_file'].name} ({ref_dur:.1f}s)")

        for sent in TEST_SENTENCES:
            out_name = f"TEST_{spk['id']}_{sent['id']}.wav"
            out_path = OUT_DIR / out_name

            print(f"    Generating: {sent['text'][:50]}...")
            t1 = time.time()
            try:
                wav, sr, _ = tts.infer(
                    ref_file=str(spk["ref_file"]),
                    ref_text=spk["ref_text"],
                    gen_text=sent["text"],
                    speed=1.0,
                    remove_silence=True,
                )
                sf.write(str(out_path), wav, sr)
                elapsed = time.time() - t1
                gen_dur = len(wav) / sr
                rtf = elapsed / max(gen_dur, 0.001)
                print(f"    → {out_name} | {gen_dur:.1f}s audio | {elapsed:.0f}s elapsed | RTF={rtf:.1f}x")
                results.append({
                    "speaker": spk["id"], "sentence": sent["id"],
                    "output": str(out_path), "duration": gen_dur,
                    "elapsed": elapsed, "rtf": rtf, "ok": True,
                })
            except Exception as e:
                print(f"    [ERROR] {e}")
                results.append({"speaker": spk["id"], "sentence": sent["id"], "ok": False, "error": str(e)})

    print("\n" + "=" * 60)
    print("  TỔNG KẾT")
    print("=" * 60)
    ok = [r for r in results if r.get("ok")]
    fail = [r for r in results if not r.get("ok")]
    print(f"  Generated: {len(ok)}/{len(results)} clips ✅")
    if fail:
        print(f"  Failed: {len(fail)} — {[f['error'] for f in fail]}")
    if ok:
        avg_rtf = sum(r["rtf"] for r in ok) / len(ok)
        total_audio = sum(r["duration"] for r in ok)
        est_1100 = avg_rtf * 20 * 1100 / 3600  # avg 20s per clip
        print(f"  Avg RTF: {avg_rtf:.1f}x (CPU) — {avg_rtf:.0f}s generate per 1s audio")
        print(f"  Total generated: {total_audio:.1f}s audio")
        print(f"  Est. 1,100 clips (avg 20s): ~{est_1100:.0f} giờ CPU")
        print(f"\n  Output → {OUT_DIR}")
        if avg_rtf <= 50:
            print("  → RTF OK ✅  Có thể generate overnight")
        else:
            print("  → RTF cao ⚠️  Cân nhắc chia batch hoặc dùng Vbee API")
    print("=" * 60)


if __name__ == "__main__":
    main()
