#!/usr/bin/env python3
"""
tools/transcribe_ref_voices.py — ASR tất cả reference voice clips → transcript review file
Output: data/eval/ref_voice_transcripts.json + ref_voice_transcripts_review.txt

Usage:
    python -X utf8 tools/transcribe_ref_voices.py
"""
import sys, json, time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REF_DIR = ROOT / "data" / "audio" / "reference_voices"
OUT_JSON = ROOT / "data" / "eval" / "ref_voice_transcripts.json"
OUT_TXT  = ROOT / "data" / "eval" / "ref_voice_transcripts_review.txt"
OUT_JSON.parent.mkdir(parents=True, exist_ok=True)

BS_DIRS = [
    ("HN", REF_DIR / "BS_hanoi"),
    ("DN", REF_DIR / "BS_danang"),
    ("SG", REF_DIR / "BS_saigon"),
]


def transcribe_wav(wav_path: Path) -> str:
    import numpy as np
    import soundfile as sf
    from core.l1a_asr import transcribe
    audio, sr = sf.read(str(wav_path), dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    return transcribe(audio, sr)


def get_duration(wav_path: Path) -> float:
    import soundfile as sf
    info = sf.info(str(wav_path))
    return info.frames / info.samplerate


def main():
    print("=" * 65)
    print("  transcribe_ref_voices.py — ASR tất cả 57 clips")
    print("  Output → data/eval/ref_voice_transcripts_review.txt")
    print("=" * 65)

    results = []
    total = sum(len(list(d.glob("*.wav"))) for _, d in BS_DIRS)
    done = 0
    t_start = time.time()

    for bs_id, bs_dir in BS_DIRS:
        wavs = sorted(bs_dir.glob("*.wav"))
        print(f"\n[{bs_id}] {len(wavs)} clips")

        for wav in wavs:
            dur = get_duration(wav)
            done += 1
            print(f"  [{done}/{total}] {wav.name} ({dur:.1f}s) ...", end="", flush=True)
            t0 = time.time()
            try:
                hyp = transcribe_wav(wav)
                elapsed = time.time() - t0
                rtf = elapsed / max(dur, 0.1)
                print(f" {elapsed:.1f}s (RTF={rtf:.1f}x)")
                print(f"    → {hyp[:90]}{'...' if len(hyp)>90 else ''}")
                results.append({
                    "bs": bs_id,
                    "file": wav.name,
                    "duration_s": round(dur, 1),
                    "transcript_asr": hyp,
                    "transcript_gt": "",  # Andy điền vào
                    "wer": None,
                    "notes": "",
                })
            except Exception as e:
                print(f" ERROR: {e}")
                results.append({
                    "bs": bs_id,
                    "file": wav.name,
                    "duration_s": round(dur, 1),
                    "transcript_asr": f"ERROR: {e}",
                    "transcript_gt": "",
                    "wer": None,
                    "notes": "ASR_ERROR",
                })

    # Save JSON
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Saved: {OUT_JSON}")

    # Save human-readable review file
    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write("REF VOICE TRANSCRIPT REVIEW\n")
        f.write("MediVoice VN — Andy điền cột TRANSCRIPT_THẬT\n")
        f.write("=" * 70 + "\n\n")
        f.write("HƯỚNG DẪN:\n")
        f.write("  - Nghe lại từng clip\n")
        f.write("  - Điền TRANSCRIPT THẬT vào dòng 'GT:'\n")
        f.write("  - Nếu ASR đúng hoàn toàn → ghi 'OK'\n")
        f.write("  - Nếu sai → ghi lại đúng\n")
        f.write("  - Nếu có PII thật (tên BN thật) → ghi 'PII'\n\n")
        f.write("=" * 70 + "\n\n")

        current_bs = None
        for r in results:
            if r["bs"] != current_bs:
                current_bs = r["bs"]
                f.write(f"\n{'─'*70}\n")
                f.write(f"BS: {current_bs}\n")
                f.write(f"{'─'*70}\n\n")

            f.write(f"FILE: {r['file']} ({r['duration_s']}s)\n")
            f.write(f"ASR:  {r['transcript_asr']}\n")
            f.write(f"GT:   \n")
            f.write(f"NOTE: \n\n")

    print(f"✅ Saved: {OUT_TXT}")

    elapsed_total = time.time() - t_start
    print(f"\n{'='*65}")
    print(f"  Tổng: {len(results)} clips | {elapsed_total/60:.1f} phút")
    print(f"  Andy review: {OUT_TXT}")
    print(f"  JSON data:   {OUT_JSON}")
    print("=" * 65)


if __name__ == "__main__":
    main()
