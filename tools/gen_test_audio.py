#!/usr/bin/env python3
"""
tools/gen_test_audio.py — Tạo audio WAV từ ground_truth JSON template (gTTS)

Dùng cho bench CEER lâm sàng vùng miền:
    python tools/gen_test_audio.py --input data/audio/ground_truth_lam_sang_template.json

Tuỳ chọn:
    --out-dir   DIR    Thư mục lưu WAV (default: data/audio/)
    --force            Ghi đè WAV đã tồn tại
    --dry-run          Chỉ hiện transcript, không tạo audio

Sau khi xong:
    python -X utf8 tools/bench_ceer.py --full --gt data/audio/ground_truth_lam_sang_template.json
"""

import os, sys, json, argparse, tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SAMPLE_RATE = 16000


def text_to_wav(text: str, out_path: str) -> bool:
    """gTTS Vietnamese → MP3 → WAV 16kHz mono."""
    try:
        from gtts import gTTS
        import librosa, soundfile as sf

        tts = gTTS(text=text, lang="vi", slow=False)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            mp3_path = tmp.name
        tts.save(mp3_path)

        audio, _ = librosa.load(mp3_path, sr=SAMPLE_RATE, mono=True)
        sf.write(out_path, audio, SAMPLE_RATE, subtype="PCM_16")
        os.unlink(mp3_path)
        return True

    except Exception as e:
        print(f"    [ERROR] TTS: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Tạo WAV từ ground_truth JSON template")
    parser.add_argument("--input",   required=True, help="Đường dẫn file JSON template")
    parser.add_argument("--out-dir", default=os.path.join("data", "audio"),
                        help="Thư mục lưu WAV (default: data/audio/)")
    parser.add_argument("--force",   action="store_true", help="Ghi đè WAV đã tồn tại")
    parser.add_argument("--dry-run", action="store_true", help="Không tạo audio, chỉ xem")
    args = parser.parse_args()

    # Load template
    if not os.path.exists(args.input):
        print(f"[ERROR] Không tìm thấy: {args.input}")
        sys.exit(1)

    with open(args.input, encoding="utf-8") as f:
        entries = json.load(f)

    os.makedirs(args.out_dir, exist_ok=True)

    print("=" * 65)
    print(f"gen_test_audio — MediVoice VN")
    print(f"Input  : {args.input}")
    print(f"Out    : {args.out_dir}/")
    print(f"Entries: {len(entries)}")
    if args.dry_run:
        print("[DRY RUN] Không tạo audio")
    print("=" * 65)

    done, skipped, failed = [], [], []

    for entry in entries:
        file_name = entry.get("file", "")
        transcript = entry.get("transcript_reference", "").strip()
        region = entry.get("region", "")
        label = f"{region or file_name}"

        if not file_name or not transcript:
            print(f"\n  [SKIP] Entry thiếu file/transcript: {entry}")
            skipped.append(file_name)
            continue

        wav_path = os.path.join(args.out_dir, file_name)
        short_t  = (transcript[:60] + "...") if len(transcript) > 60 else transcript

        print(f"\n  [{label}]")
        print(f"    File      : {file_name}")
        print(f"    Transcript: {short_t}")

        if args.dry_run:
            skipped.append(file_name)
            continue

        if os.path.exists(wav_path) and not args.force:
            size_kb = os.path.getsize(wav_path) // 1024
            print(f"    WAV       : đã có ({size_kb}KB) — bỏ qua. Dùng --force để ghi đè.")
            skipped.append(file_name)
            continue

        print(f"    WAV       : đang tạo gTTS...", end="", flush=True)
        ok = text_to_wav(transcript, wav_path)
        if ok:
            size_kb = os.path.getsize(wav_path) // 1024
            print(f" OK ({size_kb}KB)")
            done.append(file_name)
        else:
            print(" FAILED")
            failed.append(file_name)

    # Summary
    print("\n" + "=" * 65)
    print(f"  Tạo mới  : {len(done)} file(s)")
    print(f"  Bỏ qua   : {len(skipped)} file(s)")
    if failed:
        print(f"  Lỗi      : {len(failed)} file(s) — {failed}")

    if not args.dry_run and (done or skipped):
        gt_flag = f"--gt {args.input}"
        print()
        print("  Bước tiếp theo:")
        print(f"    python -X utf8 tools/bench_ceer.py --full {gt_flag}")
    print("=" * 65)


if __name__ == "__main__":
    main()
