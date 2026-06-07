#!/usr/bin/env python
# scripts/download_vietmed.py — DATASET-001: Download VietMed from HuggingFace
# Dataset: doof-ferb/VietMed (MIT license, ~16h labeled Vietnamese medical speech)
# Output: data/vietmed/
# Usage: python scripts/download_vietmed.py [--split train|validation|test|all]

import argparse
import json
import logging
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
DATASET_ID = "doof-ferb/VietMed"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", default="all", choices=["train", "validation", "test", "all"])
    parser.add_argument("--cache-dir", default=None)
    args = parser.parse_args()

    (ROOT / "logs").mkdir(exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        from datasets import load_dataset, Audio
    except ImportError:
        log.error("datasets not installed: pip install datasets")
        sys.exit(1)

    splits = ["train", "validation", "test"] if args.split == "all" else [args.split]

    for split in splits:
        log.info(f"Downloading {DATASET_ID} split={split}...")
        try:
            ds = load_dataset(
                DATASET_ID,
                split=split,
                cache_dir=args.cache_dir,
                trust_remote_code=True,
            )
        except Exception as e:
            log.warning(f"  {split}: {e} — trying without trust_remote_code")
            ds = load_dataset(DATASET_ID, split=split, cache_dir=args.cache_dir)

        log.info(f"  {split}: {len(ds)} samples — features: {list(ds.features.keys())}")

        split_dir = OUT_DIR / split
        split_dir.mkdir(exist_ok=True)

        # Save metadata as JSONL for inspection
        meta_path = split_dir / "metadata.jsonl"
        with open(meta_path, "w", encoding="utf-8") as mf:
            for i, row in enumerate(ds):
                meta = {k: v for k, v in row.items() if k != "audio"}
                mf.write(json.dumps(meta, ensure_ascii=False) + "\n")
                if i % 500 == 0:
                    log.info(f"    {split}: {i}/{len(ds)} metadata rows written...")

        log.info(f"  Metadata saved → {meta_path}")

        # Save audio files as WAV 16kHz mono
        audio_dir = split_dir / "audio"
        audio_dir.mkdir(exist_ok=True)

        ds = ds.cast_column("audio", Audio(sampling_rate=16000))
        for i, row in enumerate(ds):
            if i % 100 == 0:
                log.info(f"    {split}: saving audio {i}/{len(ds)}...")
            audio_data = row["audio"]
            wav_path = audio_dir / f"{split}_{i:05d}.wav"
            if wav_path.exists():
                continue
            import soundfile as sf
            import numpy as np
            arr = np.array(audio_data["array"], dtype=np.float32)
            sf.write(str(wav_path), arr, samplerate=16000, subtype="PCM_16")

        log.info(f"  Audio saved → {audio_dir}  ({len(ds)} files)")

    log.info("=== VietMed download complete ===")
    log.info(f"Location: {OUT_DIR}")


if __name__ == "__main__":
    main()
