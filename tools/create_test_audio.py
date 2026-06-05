#!/usr/bin/env python3
"""
tools/create_test_audio.py — Tạo audio test + ground_truth.json từ file .txt

Andy viết text trong data/audio/test_scripts/*.txt
Script này:
  1. Đọc TRANSCRIPT → gTTS → WAV (16kHz mono)
  2. Đọc labels (CHAN_DOAN, THUOC, VITAL_*, TAI_KHAM) → ground_truth.json

Chạy tất cả scripts:
    python tools/create_test_audio.py

Chỉ 1 file:
    python tools/create_test_audio.py tc_001_noi_khoa.txt

Sau khi xong → đo CEER thật:
    python tools/bench_ceer.py --full
"""

import os, sys, json, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPTS_DIR = os.path.join("data", "audio", "test_scripts")
AUDIO_DIR   = os.path.join("data", "audio")
GT_FILE     = os.path.join("data", "audio", "ground_truth.json")

SAMPLE_RATE = 16000


# ─── Text file parser ─────────────────────────────────────────────────────────

def parse_script(path: str) -> dict:
    """
    Parse a .txt test script into structured dict.
    Lines starting with # are comments.
    KEY: value format.
    """
    result = {
        "transcript": "",
        "chan_doan":  "",
        "drugs":      [],
        "vitals": {"huyet_ap": None, "nhiet_do": None, "mach": None,
                   "spo2": None, "can_nang": None},
        "tai_kham":   "",
    }

    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue

            if ":" not in line:
                continue

            key, _, val = line.partition(":")
            key = key.strip().upper()
            val = val.strip()

            if key == "TRANSCRIPT":
                result["transcript"] = val
            elif key == "CHAN_DOAN":
                result["chan_doan"] = val
            elif key == "THUOC" and val:
                result["drugs"].append(_parse_drug(val))
            elif key == "VITAL_HA":
                result["vitals"]["huyet_ap"] = val or None
            elif key == "VITAL_NHIET_DO":
                result["vitals"]["nhiet_do"] = _to_float(val)
            elif key == "VITAL_MACH":
                result["vitals"]["mach"] = _to_float(val)
            elif key == "VITAL_SPO2":
                result["vitals"]["spo2"] = _to_float(val)
            elif key == "VITAL_CAN_NANG":
                result["vitals"]["can_nang"] = _to_float(val)
            elif key == "TAI_KHAM":
                result["tai_kham"] = val

    return result


def _to_float(s: str):
    try:
        return float(s) if s else None
    except ValueError:
        return s if s else None


def _parse_drug(val: str) -> dict:
    """
    'amoxicillin 500mg 2 viên/ngày 7 ngày'
    → {name, dose, frequency, duration}
    """
    parts = val.split()
    name  = parts[0] if parts else val
    dose  = ""
    freq  = ""
    dur   = ""

    # dose: token matching NNNmg / NNNml / NNNmcg
    for p in parts[1:]:
        if re.match(r"^\d+[\.,]?\d*(mg|ml|mcg|g|IU)", p, re.I):
            dose = p
            break

    # everything after name+dose
    rest = val[len(name):].strip()
    if dose:
        rest = rest[rest.find(dose)+len(dose):].strip()

    # heuristic: first token is frequency, rest is duration
    rest_parts = rest.split()
    if rest_parts:
        freq = rest_parts[0]
        dur  = " ".join(rest_parts[1:])

    return {"name": name, "dose": dose, "frequency": freq, "duration": dur}


# ─── TTS → WAV ───────────────────────────────────────────────────────────────

def text_to_wav(text: str, out_path: str) -> bool:
    """gTTS Vietnamese → MP3 → WAV 16kHz mono."""
    try:
        from gtts import gTTS
        import tempfile, librosa, soundfile as sf

        # gTTS → temp mp3
        tts = gTTS(text=text, lang="vi", slow=False)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            mp3_path = tmp.name
        tts.save(mp3_path)

        # mp3 → 16kHz mono numpy → WAV
        audio, _ = librosa.load(mp3_path, sr=SAMPLE_RATE, mono=True)
        sf.write(out_path, audio, SAMPLE_RATE, subtype="PCM_16")
        os.unlink(mp3_path)
        return True

    except Exception as e:
        print(f"    [ERROR] TTS failed: {e}")
        return False


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None

    scripts = sorted([
        f for f in os.listdir(SCRIPTS_DIR)
        if f.endswith(".txt") and (f == target if target else True)
    ])

    if not scripts:
        print(f"[ERROR] Không tìm thấy file .txt trong {SCRIPTS_DIR}/")
        print("        Tạo file theo format: data/audio/test_scripts/tc_NNN_ten.txt")
        sys.exit(1)

    print("=" * 65)
    print("create_test_audio — MediVoice VN | BENCH-002 prep")
    print(f"Scripts: {len(scripts)}")
    print("=" * 65)

    # Load existing ground_truth.json nếu có
    existing_gt = {}
    if os.path.exists(GT_FILE):
        with open(GT_FILE, encoding="utf-8") as f:
            for row in json.load(f):
                existing_gt[row["file"]] = row

    new_entries = []
    errors      = []

    for script_name in scripts:
        script_path = os.path.join(SCRIPTS_DIR, script_name)
        wav_name    = script_name.replace(".txt", ".wav")
        wav_path    = os.path.join(AUDIO_DIR, wav_name)

        print(f"\n  [{script_name}]")

        # Parse
        try:
            data = parse_script(script_path)
        except Exception as e:
            print(f"    [ERROR] Parse failed: {e}")
            errors.append(script_name)
            continue

        if not data["transcript"]:
            print(f"    [SKIP] TRANSCRIPT dòng trống")
            continue

        safe_t = data["transcript"][:70].encode("ascii", "replace").decode()
        print(f"    Transcript : {safe_t}...")

        # TTS → WAV
        if os.path.exists(wav_path):
            print(f"    WAV        : đã tồn tại — bỏ qua TTS (xóa để regenerate)")
        else:
            print(f"    WAV        : đang tạo bằng gTTS...", end="", flush=True)
            ok = text_to_wav(data["transcript"], wav_path)
            if ok:
                size_kb = os.path.getsize(wav_path) // 1024
                print(f" ✅ {wav_name} ({size_kb}KB)")
            else:
                print(f" ❌")
                errors.append(script_name)
                continue

        # Ground truth entry
        entry = {
            "file": wav_name,
            "transcript_reference": data["transcript"],
            "ground_truth": {
                "drugs":    data["drugs"],
                "chan_doan": data["chan_doan"],
                "vitals":   data["vitals"],
                "tai_kham": data["tai_kham"],
            },
        }
        existing_gt[wav_name] = entry
        new_entries.append(wav_name)
        print(f"    GT         : {len(data['drugs'])} thuốc | chan_doan='{data['chan_doan'][:30]}' | vitals={_summarize_vitals(data['vitals'])}")

    # Save ground_truth.json (merge existing + new)
    all_gt = list(existing_gt.values())
    with open(GT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_gt, f, ensure_ascii=False, indent=2)

    # Summary
    print("\n" + "=" * 65)
    print(f"  WAV tạo xong : {len(new_entries)} files → {AUDIO_DIR}/")
    print(f"  Ground truth : {GT_FILE}  ({len(all_gt)} entries)")
    if errors:
        print(f"  Lỗi         : {errors}")
    print()
    print("  Bước tiếp theo:")
    print("    python tools/bench_ceer.py --full")
    print("=" * 65)


def _summarize_vitals(v: dict) -> str:
    parts = []
    if v.get("huyet_ap"):  parts.append(f"HA={v['huyet_ap']}")
    if v.get("nhiet_do"):  parts.append(f"T={v['nhiet_do']}")
    if v.get("mach"):      parts.append(f"M={v['mach']}")
    if v.get("spo2"):      parts.append(f"SpO2={v['spo2']}")
    if v.get("can_nang"):  parts.append(f"CN={v['can_nang']}")
    return ", ".join(parts) if parts else "none"


if __name__ == "__main__":
    main()
