#!/usr/bin/env python
# scripts/download_vietmed.py — DATASET-001: Download VietMed from HuggingFace
# Dataset: leduckhai/VietMed (MIT license, ~16h labeled Vietnamese medical speech)
#   NOT gated — no HF_TOKEN required (verified 2026-06-12, fixes earlier wrong
#   dataset ID "doof-ferb/VietMed" which 404s).
# Output: data/vietmed/
# Usage: python scripts/download_vietmed.py [--split train|dev|test|cv|all]
# Optional: HF_TOKEN env var (higher rate limits) — huggingface.co/settings/tokens

import argparse
import json
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(ROOT / "logs" / "download_vietmed.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

OUT_DIR = ROOT / "data" / "vietmed"
DATASET_ID = "leduckhai/VietMed"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", default="all", choices=["train", "dev", "test", "cv", "all"])
    parser.add_argument("--cache-dir", default=None)
    args = parser.parse_args()

    (ROOT / "logs").mkdir(exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        from datasets import load_dataset, Audio
    except ImportError:
        log.error("datasets not installed: pip install datasets")
        sys.exit(1)

    hf_token = os.environ.get("HF_TOKEN")  # optional — leduckhai/VietMed is not gated

    splits = ["train", "dev", "test", "cv"] if args.split == "all" else [args.split]

    for split in splits:
        log.info(f"Downloading {DATASET_ID} split={split}...")
        try:
            ds = load_dataset(
                DATASET_ID,
                split=split,
                cache_dir=args.cache_dir,
                token=hf_token,
            )
        except Exception as e:
            log.error(
                f"  {split}: {e}\n"
                "  Nếu lỗi 401/403: set HF_TOKEN=<token> trước khi chạy lại."
            )
            continue

        log.info(f"  {split}: {len(ds)} samples — features: {list(ds.features.keys())}")

        # decode=False: keep raw audio bytes, avoid torchcodec (incompatible with
        # this venv's torch version) — we decode manually via soundfile below.
        ds = ds.cast_column("audio", Audio(decode=False))

        split_dir = OUT_DIR / split
        split_dir.mkdir(exist_ok=True)

        # Save metadata as JSONL for inspection
        meta_path = split_dir / "metadata.jsonl"
        with open(meta_path, "w", encoding="utf-8") as mf:
            for i, row in enumerate(ds):
                meta = {k: v for k, v in row.items() if k != "audio"}
                meta["wav_file"] = f"{split}_{i:05d}.wav"
                mf.write(json.dumps(meta, ensure_ascii=False) + "\n")
                if i % 500 == 0:
                    log.info(f"    {split}: {i}/{len(ds)} metadata rows written...")

        log.info(f"  Metadata saved → {meta_path}")

        # Save audio files as WAV 16kHz mono
        audio_dir = split_dir / "audio"
        audio_dir.mkdir(exist_ok=True)

        import io
        import librosa
        import soundfile as sf

        for i, row in enumerate(ds):
            if i % 100 == 0:
                log.info(f"    {split}: saving audio {i}/{len(ds)}...")
            wav_path = audio_dir / f"{split}_{i:05d}.wav"
            if wav_path.exists():
                continue
            audio_bytes = row["audio"]["bytes"]
            arr, sr = sf.read(io.BytesIO(audio_bytes), dtype="float32")
            if sr != 16000:
                arr = librosa.resample(arr, orig_sr=sr, target_sr=16000)
            sf.write(str(wav_path), arr, samplerate=16000, subtype="PCM_16")

        log.info(f"  Audio saved → {audio_dir}  ({len(ds)} files)")

    log.info("=== VietMed download complete ===")
    log.info(f"Location: {OUT_DIR}")


if __name__ == "__main__":
    main()
