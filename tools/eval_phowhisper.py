#!/usr/bin/env python3
"""
tools/eval_phowhisper.py
T-007: PhoWhisper-medium vs Whisper-small evaluation
─────────────────────────────────────────────────────
Compare transcript quality + WER proxy on T-005 audio files.
Run from project root:
    python tools/eval_phowhisper.py
"""

import os
import sys
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

try:
    import librosa
except ImportError:
    print("ERROR: pip install librosa")
    sys.exit(1)

try:
    import whisper as _whisper_lib
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("WARNING: openai-whisper not found — skipping Whisper-small")

try:
    import torch
    from transformers import WhisperProcessor, WhisperForConditionalGeneration
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("ERROR: pip install transformers torch")
    sys.exit(1)

AUDIO_DIR = os.path.join("data", "audio")
WER_REJECT = 0.55
WER_FLAG   = 0.35
SAMPLE_RATE = 16000

# ─────────────────────────────────────────────────────────────────────────────

def load_audio(path: str) -> np.ndarray:
    audio, _ = librosa.load(path, sr=SAMPLE_RATE, mono=True)
    return audio.astype(np.float32)


def wer_from_logprob(avg_logprob: float) -> float:
    """Same formula as l1_semantic.py: confidence = 1 + avg_logprob → WER = 1 - conf."""
    confidence = max(0.0, min(1.0, 1.0 + avg_logprob))
    return round(1.0 - confidence, 2)


def wer_label(wer: float) -> str:
    if wer > WER_REJECT:
        return "FAIL(reject)"
    if wer > WER_FLAG:
        return "flag"
    return "ok"


def vi_diacritic_ratio(text: str) -> float:
    """Fraction of alphabetic chars that carry Vietnamese diacritics — proxy for VI quality."""
    import re
    vi = re.findall(r'[àáâãèéêìíòóôõùúýăđơưÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝĂĐƠƯ]', text)
    alpha = [c for c in text if c.isalpha()]
    return round(len(vi) / max(len(alpha), 1), 3)

# ─────────────────────────────────────────────────────────────────────────────
# Model loaders

_whisper_model = None
_phow_processor = None
_phow_model = None


def load_whisper_small():
    global _whisper_model
    if _whisper_model is None:
        print("[Whisper-small] Loading model...")
        _whisper_model = _whisper_lib.load_model("small")
        print("[Whisper-small] Ready.")
    return _whisper_model


def load_phowhisper():
    global _phow_processor, _phow_model
    if _phow_model is None:
        print("[PhoWhisper-medium] Loading (first run: download ~300MB)...")
        _phow_processor = WhisperProcessor.from_pretrained("vinai/PhoWhisper-medium")
        _phow_model = WhisperForConditionalGeneration.from_pretrained("vinai/PhoWhisper-medium")
        _phow_model.eval()
        print("[PhoWhisper-medium] Ready.")
    return _phow_processor, _phow_model


# ─────────────────────────────────────────────────────────────────────────────
# Transcription

def transcribe_whisper(audio: np.ndarray) -> dict:
    model = load_whisper_small()
    t0 = time.time()
    result = model.transcribe(audio, fp16=False, language="vi")
    elapsed = time.time() - t0
    text = result.get("text", "").strip()
    segments = result.get("segments", [])
    if segments:
        avg_logprob = sum(s.get("avg_logprob", -0.5) for s in segments) / len(segments)
    else:
        avg_logprob = -0.5
    wer = wer_from_logprob(avg_logprob)
    return {
        "text": text,
        "avg_logprob": round(avg_logprob, 3),
        "wer": wer,
        "elapsed": round(elapsed, 1),
    }


def transcribe_phowhisper(audio: np.ndarray) -> dict:
    processor, model = load_phowhisper()
    t0 = time.time()

    inputs = processor(audio, sampling_rate=SAMPLE_RATE, return_tensors="pt")
    forced_decoder_ids = processor.get_decoder_prompt_ids(language="vi", task="transcribe")

    with torch.no_grad():
        sequences = model.generate(**inputs, forced_decoder_ids=forced_decoder_ids)

    text = processor.batch_decode(sequences, skip_special_tokens=True)[0].strip()
    elapsed = time.time() - t0

    # WER proxy via diacritic ratio:
    # PhoWhisper logprob not exposed in this transformers version.
    # High diacritic density → high VI confidence → low WER proxy.
    # Formula calibrated so dr≈0.30 → wer≈0.20, dr≈0.10 → wer≈0.55
    dr = vi_diacritic_ratio(text)
    wer = round(max(0.05, min(0.95, 0.65 - dr * 1.5)), 2)

    return {
        "text": text,
        "avg_logprob": None,  # not available in this transformers version
        "wer_proxy": "diacritic_ratio",
        "vi_diacritic_ratio": dr,
        "wer": wer,
        "elapsed": round(elapsed, 1),
    }

# ─────────────────────────────────────────────────────────────────────────────

def safe_print(text: str) -> str:
    """Return ASCII-safe preview for Windows console (replace non-ASCII with ?)."""
    return text.encode("ascii", errors="replace").decode("ascii")


def main():
    files = sorted([
        f for f in os.listdir(AUDIO_DIR)
        if f.startswith("test_medivoice_") and f.endswith(".wav")
    ])

    if not files:
        print(f"No test_medivoice_*.wav files found in {AUDIO_DIR}")
        sys.exit(1)

    print("=" * 70)
    print("T-007: PhoWhisper-medium vs Whisper-small Evaluation")
    print(f"Files: {len(files)} | WER reject: >{WER_REJECT} | WER flag: >{WER_FLAG}")
    print("=" * 70)

    results = []
    whisper_pass = 0
    phowhisper_pass = 0

    for i, fname in enumerate(files, 1):
        fpath = os.path.join(AUDIO_DIR, fname)
        print(f"\n[{i}/{len(files)}] {fname}")
        print("-" * 60)

        audio = load_audio(fpath)

        # ── Whisper-small ──
        row = {"file": fname}
        if WHISPER_AVAILABLE:
            w = transcribe_whisper(audio)
            row["whisper"] = w
            w_label = wer_label(w["wer"])
            if w_label != "FAIL(reject)":
                whisper_pass += 1
            print(f"  [Whisper-small]  WER={w['wer']:.0%} ({w_label}) | {w['elapsed']}s")
            print(f"    Transcript: {safe_print(w['text'][:80])}")
        else:
            print("  [Whisper-small]  SKIP (not installed)")

        # ── PhoWhisper-medium ──
        ph = transcribe_phowhisper(audio)
        row["phowhisper"] = ph
        ph_label = wer_label(ph["wer"])
        if ph_label != "FAIL(reject)":
            phowhisper_pass += 1
        lp_str = f"vi_ratio={ph['vi_diacritic_ratio']:.2f}(proxy)"
        print(f"  [PhoWhisper-medium] WER={ph['wer']:.0%} ({ph_label}) | {ph['elapsed']}s | {lp_str}")
        print(f"    Transcript: {safe_print(ph['text'][:80])}")

        # ── Winner ──
        if WHISPER_AVAILABLE:
            if ph["wer"] < w["wer"] - 0.03:
                winner = "PhoWhisper"
            elif w["wer"] < ph["wer"] - 0.03:
                winner = "Whisper"
            else:
                winner = "tie"
            print(f"  Winner: {winner}")
            row["winner"] = winner

        results.append(row)

    # ── Summary ──
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    n = len(files)
    if WHISPER_AVAILABLE:
        print(f"  Whisper-small   PASS: {whisper_pass}/{n}")
    print(f"  PhoWhisper-medium PASS: {phowhisper_pass}/{n}")

    if WHISPER_AVAILABLE:
        ph_wins = sum(1 for r in results if r.get("winner") == "PhoWhisper ↑")
        ws_wins = sum(1 for r in results if r.get("winner") == "Whisper ↑")
        ties    = sum(1 for r in results if r.get("winner") == "tie")
        print(f"\n  PhoWhisper wins: {ph_wins} | Whisper wins: {ws_wins} | Ties: {ties}")

        if phowhisper_pass > whisper_pass:
            verdict = "RECOMMEND: Switch to PhoWhisper-medium"
        elif whisper_pass > phowhisper_pass:
            verdict = "RECOMMEND: Keep Whisper-small"
        else:
            verdict = "NEUTRAL: Equal pass rate — check transcript quality"
        print(f"\n  {verdict}")

    # ── Save results ──
    out_path = os.path.join("data", "audio", "T007_eval_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nDetailed results: {out_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
