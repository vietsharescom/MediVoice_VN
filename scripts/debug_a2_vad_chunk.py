# CT-019 — A2-VAD-CHUNK regression debug
# Offline A/B comparison: whole-file transcribe() vs per-chunk transcribe_chunks()
# Goal: isolate whether the regression ("KHONG NHAN DANG DUOC GI LUON") comes from
#   (a) VAD chunking itself (bad cut points / too-short chunks), and/or
#   (b) initial_prompt (drug list) re-injected into every chunk biasing the decoder
#
# Usage:
#   python -X utf8 scripts/debug_a2_vad_chunk.py [audio_file ...]
#   (defaults to a few real pilot recordings if no args given)

from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core import l0_normalize, l1a_asr
from src.core.l1b_drug_correct import _load_drug_db

DEFAULT_FILES = [
    "data/drive-download-20260609T031416Z-3-001/medivoice_audio_20260608_145949.wav",  # 12.2s
    "data/drive-download-20260609T031416Z-3-001/medivoice_audio_20260608_144750.wav",  # 28.5s
    "data/drive-download-20260609T031416Z-3-001/medivoice_audio_20260608_164734.wav",  # 92.6s
]


def run_one(path: str, drug_db: dict, specialty: str = "noi_khoa") -> None:
    print("=" * 70)
    print(f"FILE: {path}")
    audio, tmp_wav = l0_normalize.normalize(path)
    try:
        dur = len(audio) / l0_normalize.TARGET_SR
        print(f"duration: {dur:.1f}s")

        # --- A: whole-file transcribe (current production behavior) ---
        whole = l1a_asr.transcribe(audio, drug_db=drug_db, specialty=specialty)
        print("\n--- A) WHOLE-FILE (with initial_prompt) ---")
        print(whole)

        # --- B: VAD chunks ---
        chunks = l0_normalize.vad_chunk_audio(audio)
        print(f"\nVAD produced {len(chunks)} chunk(s):")
        for i, c in enumerate(chunks):
            print(f"  chunk {i}: {len(c) / l0_normalize.TARGET_SR:.2f}s")

        # --- C: per-chunk transcribe WITH initial_prompt (what was wired+reverted) ---
        per_chunk_with_prompt = l1a_asr.transcribe_chunks(chunks, drug_db=drug_db, specialty=specialty)
        print("\n--- C) PER-CHUNK transcribe_chunks() WITH initial_prompt (reverted A2 wiring) ---")
        print(per_chunk_with_prompt)

        # --- D: per-chunk transcribe WITHOUT initial_prompt (isolate prompt-bias hypothesis) ---
        per_chunk_no_prompt = l1a_asr.transcribe_chunks(chunks, drug_db=None, specialty=specialty)
        print("\n--- D) PER-CHUNK transcribe_chunks() WITHOUT initial_prompt ---")
        print(per_chunk_no_prompt)

        # --- E: each chunk individually, no prompt (see exactly which chunk hallucinates) ---
        print("\n--- E) PER-CHUNK individual transcripts (no prompt) ---")
        for i, c in enumerate(chunks):
            t = l1a_asr.transcribe(c, drug_db=None, specialty=specialty)
            print(f"  chunk {i} ({len(c) / l0_normalize.TARGET_SR:.2f}s): {t!r}")

    finally:
        l0_normalize.purge_audio(tmp_wav)


def main() -> None:
    files = sys.argv[1:] or DEFAULT_FILES
    drug_db = _load_drug_db()
    for f in files:
        if not Path(f).exists():
            print(f"SKIP (not found): {f}")
            continue
        run_one(f, drug_db)


if __name__ == "__main__":
    main()
