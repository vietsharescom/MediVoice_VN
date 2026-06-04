"""
MediVoice AI — Chạy pipeline test với audio files thực tế (T-005)
Chạy: python tools/run_test_audio.py
"""

import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ensure MEDIVOICE_DB_KEY set (generate temp key for testing if absent)
if not os.environ.get("MEDIVOICE_DB_KEY"):
    from cryptography.fernet import Fernet
    os.environ["MEDIVOICE_DB_KEY"] = Fernet.generate_key().decode()
    print("[INFO] MEDIVOICE_DB_KEY not set — using temporary key for this run.\n")

from src.pipeline.p0_ingestion.l0_input    import handle as l0
from src.pipeline.p1_processing.l1_semantic import handle as l1
from src.pipeline.p1_processing.l2_enforcer import handle as l2
from src.pipeline.p1_processing.l3_routing  import handle as l3
from src.pipeline.p2_decision.l4_authority  import handle as l4
from src.pipeline.p2_decision.l5_policy     import handle as l5
from src.pipeline.p2_decision.l6_agent      import handle as l6
from src.pipeline.p2_decision.l7_memory     import handle as l7
from src.pipeline.p3_output.l9_response     import handle as l9

PIPELINE = [("L0", l0), ("L1", l1), ("L2", l2), ("L3", l3),
            ("L4", l4), ("L5", l5), ("L6", l6), ("L7", l7), ("L9", l9)]

AUDIO_DIR = os.path.join("data", "audio")


def run_file(audio_path: str, index: int, total: int) -> dict:
    filename = os.path.basename(audio_path)
    print(f"\n[{index}/{total}] {filename}")
    print("  Đang xử lý", end="", flush=True)

    payload = {
        "source":    "audio_file",
        "audio_path": audio_path,
        "session_id": f"t005-{index:02d}",
        "doctor_id":  "dr-andy-test",
        "consent_given": True,
        "purpose":    "medical_documentation",
    }

    data = payload
    for stage_name, handler in PIPELINE:
        result = handler(data)
        print(".", end="", flush=True)
        if not result.get("ok"):
            print(f"\n  ✗ FAIL at {stage_name}: {result.get('error')} — {result.get('message', '')}")
            return {"file": filename, "status": "FAIL", "stage": stage_name,
                    "error": result.get("error"), "message": result.get("message", "")}
        if "data" not in result:
            print(f"\n  ✗ FAIL at {stage_name}: missing data key")
            return {"file": filename, "status": "FAIL", "stage": stage_name, "error": "MISSING_DATA"}
        data = result["data"]

    print()  # newline after dots

    # L9 restructures output — read from L9 contract keys
    orig = data.get("original_transcript", {})
    transcript  = orig.get("text", "")
    language    = orig.get("language", "?")
    wer         = orig.get("wer_estimate", "?")
    soap        = data.get("soap_note", {})
    translation = data.get("translation", {})
    flags       = data.get("enforcement_flags", [])

    # Safe ASCII print for Windows console
    def safe(s, n=80):
        return s[:n].encode("ascii", "replace").decode() + ("..." if len(s) > n else "")

    print(f"  Transcript : {safe(transcript)}")
    print(f"  Language   : {language}")
    if translation:
        print(f"  Translated : {safe(translation.get('text', ''))}")
    print(f"  WER est.   : {wer}")
    if flags:
        print(f"  Flags      : {[f['code'] for f in flags]}")
    if soap:
        print(f"  SOAP-S     : {safe(str(soap.get('S', '')))}")

    return {
        "file": filename,
        "status": "PASS",
        "transcript": transcript,
        "language": language,
        "wer_estimate": wer,
        "soap_complete": all(k in soap for k in ("S", "O", "A", "P")),
        "flags": [f["code"] for f in flags],
    }


def main():
    # Find files
    prefix = sys.argv[1] if len(sys.argv) > 1 else ""
    all_wav = sorted([
        os.path.join(AUDIO_DIR, f)
        for f in os.listdir(AUDIO_DIR)
        if f.endswith(".wav") and (prefix in f if prefix else True)
    ])

    if not all_wav:
        print(f"Không tìm thấy file WAV trong {AUDIO_DIR}/")
        return

    print("=" * 60)
    print(f"MediVoice AI — Audio Pipeline Test (T-005)")
    print(f"Files: {len(all_wav)}  |  Prefix filter: '{prefix or 'all'}'")
    print("=" * 60)
    print("[INFO] Loading Whisper-small model (lần đầu ~30s)...")

    results = []
    for i, path in enumerate(all_wav, start=1):
        results.append(run_file(path, i, len(all_wav)))

    # Summary
    passed  = [r for r in results if r["status"] == "PASS"]
    failed  = [r for r in results if r["status"] == "FAIL"]
    vi_count = sum(1 for r in passed if r.get("language") in ("vi", "mixed"))

    print("\n" + "=" * 60)
    print(f"KẾT QUẢ: {len(passed)}/{len(results)} PASS | {len(failed)} FAIL")
    print(f"Tiếng Việt phát hiện: {vi_count}/{len(passed)}")
    soap_ok = sum(1 for r in passed if r.get("soap_complete"))
    print(f"SOAP đầy đủ S/O/A/P : {soap_ok}/{len(passed)}")

    if failed:
        print("\nFAIL:")
        for r in failed:
            print(f"  ✗ {r['file']} — {r['stage']}: {r['error']}")

    all_flags = [f for r in passed for f in r.get("flags", [])]
    if all_flags:
        from collections import Counter
        print(f"\nFlags phổ biến: {dict(Counter(all_flags))}")

    # Save report
    report_path = os.path.join("data", "audio", "T005_results.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nBáo cáo chi tiết: {report_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
