#!/usr/bin/env python
# scripts/train_asr_phowhisper.py — FID-VN-007 / TRAIN-001: fine-tune PhoWhisper-medium
# Input:  data/asr_manifest/ref_voice_manifest.jsonl (build_asr_manifest.py)
#         + future: VietMed (data/vietmed/) + pilot audio manifests, once available
# Output: models/asr_phowhisper/ — fine-tuned checkpoint (NOT committed, /models/ gitignored)
#
# --smoke-test: runs 1 training step on the first 2 samples (CPU OK) to validate the
#   data collator + model forward/backward pipeline. Does NOT produce a usable checkpoint —
#   the available data (~17 min) is far too small for a real fine-tune (would overfit).
#   Real fine-tune (TRAIN-001) requires VietMed (16h, needs HF_TOKEN) + pilot audio (50-100h,
#   not yet recorded) + GPU/cloud VM — see fids/FID-VN-007.md.
#
# Usage:
#   python -X utf8 scripts/train_asr_phowhisper.py --smoke-test
#   python -X utf8 scripts/train_asr_phowhisper.py --manifest <path> --epochs 3 --batch 4

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

MODEL_NAME = "vinai/PhoWhisper-medium"
DEFAULT_MANIFEST = ROOT / "data" / "asr_manifest" / "ref_voice_manifest.jsonl"
OUT_DIR = ROOT / "models" / "asr_phowhisper"


def load_manifest(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def build_dataset(manifest: list[dict], processor):
    """Load audio + tokenize text into a HF Dataset with input_features/labels columns."""
    import librosa
    from datasets import Dataset

    def _prepare(example):
        audio, _ = librosa.load(example["audio"], sr=16000)
        features = processor.feature_extractor(audio, sampling_rate=16000)
        labels = processor.tokenizer(example["text"]).input_ids
        return {"input_features": features.input_features[0], "labels": labels}

    ds = Dataset.from_list(manifest)
    return ds.map(_prepare, remove_columns=ds.column_names)


class DataCollatorSpeechSeq2SeqWithPadding:
    """Pads input_features and labels separately (Whisper fine-tuning standard recipe)."""

    def __init__(self, processor):
        self.processor = processor

    def __call__(self, features):
        import torch

        input_features = [{"input_features": f["input_features"]} for f in features]
        batch = self.processor.feature_extractor.pad(input_features, return_tensors="pt")

        label_features = [{"input_ids": f["labels"]} for f in features]
        labels_batch = self.processor.tokenizer.pad(label_features, return_tensors="pt")
        labels = labels_batch["input_ids"].masked_fill(labels_batch["attention_mask"].ne(1), -100)

        batch["labels"] = labels
        return batch


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch", type=int, default=2)
    parser.add_argument("--smoke-test", action="store_true",
                         help="1 training step on 2 samples — validates pipeline only")
    args = parser.parse_args()

    from transformers import (
        Seq2SeqTrainer,
        Seq2SeqTrainingArguments,
        WhisperForConditionalGeneration,
        WhisperProcessor,
    )

    manifest = load_manifest(Path(args.manifest))
    if args.smoke_test:
        manifest = manifest[:2]
        print(f"[smoke-test] using {len(manifest)} sample(s)")

    if not manifest:
        print("Manifest empty — nothing to do.")
        sys.exit(1)

    processor = WhisperProcessor.from_pretrained(MODEL_NAME)
    model = WhisperForConditionalGeneration.from_pretrained(MODEL_NAME)
    model.generation_config.language = "vi"
    model.generation_config.task = "transcribe"
    model.generation_config.forced_decoder_ids = None

    train_ds = build_dataset(manifest, processor)
    collator = DataCollatorSpeechSeq2SeqWithPadding(processor)

    training_args = Seq2SeqTrainingArguments(
        output_dir=str(OUT_DIR),
        per_device_train_batch_size=args.batch,
        num_train_epochs=args.epochs,
        max_steps=1 if args.smoke_test else -1,
        save_strategy="no" if args.smoke_test else "epoch",
        logging_steps=1,
        report_to=[],
    )

    trainer = Seq2SeqTrainer(
        args=training_args,
        model=model,
        train_dataset=train_ds,
        data_collator=collator,
        tokenizer=processor.feature_extractor,
    )
    trainer.train()

    if not args.smoke_test:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        trainer.save_model(str(OUT_DIR))
        processor.save_pretrained(str(OUT_DIR))
        print(f"Saved fine-tuned model -> {OUT_DIR}")
    else:
        print("[smoke-test] OK — pipeline runs end-to-end (no checkpoint saved)")


if __name__ == "__main__":
    main()
