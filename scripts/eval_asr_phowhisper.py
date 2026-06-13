#!/usr/bin/env python
# scripts/eval_asr_phowhisper.py — TRAIN-001: evaluate a (fine-tuned) PhoWhisper
# checkpoint against a manifest, computing WER per sample + aggregate.
#
# Input:  manifest JSONL (scripts/build_asr_manifest.py), each line
#         {"audio": <path>, "text": <reference transcript>}
# Output: JSON results file (default data/eval/train001_eval_results.json):
#         {"model": <path>, "manifest": <path>, "n": N,
#          "wer_mean": <float>, "samples": [{"audio", "ref", "hyp", "wer"}, ...]}
#
# Usage:
#   python -X utf8 scripts/eval_asr_phowhisper.py --manifest data/asr_manifest/ref_voice_manifest.jsonl
#   python -X utf8 scripts/eval_asr_phowhisper.py --model models/asr_phowhisper --manifest data/asr_manifest/vietmed_manifest.jsonl --out data/eval/train001_eval_results.json

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

BASE_MODEL = "vinai/PhoWhisper-medium"
DEFAULT_MANIFEST = ROOT / "data" / "asr_manifest" / "ref_voice_manifest.jsonl"
DEFAULT_CHECKPOINT = ROOT / "models" / "asr_phowhisper"
DEFAULT_OUT = ROOT / "data" / "eval" / "train001_eval_results.json"


def load_manifest(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _norm(text: str) -> str:
    """Lowercase + collapse whitespace, matching tools/bench_002b.py normalization."""
    return " ".join(text.lower().split())


def compute_wer(ref: str, hyp: str) -> float | None:
    """Word Error Rate using jiwer. Returns None if ref is empty."""
    if not ref.strip():
        return None
    import jiwer

    return round(jiwer.wer(_norm(ref), _norm(hyp)), 4)


def aggregate(samples: list[dict]) -> float | None:
    """Mean WER over samples with a non-None "wer" value."""
    vals = [s["wer"] for s in samples if s.get("wer") is not None]
    if not vals:
        return None
    return round(sum(vals) / len(vals), 4)


def transcribe_all(manifest: list[dict], model_path: str, limit: int | None = None) -> list[dict]:
    """Run the model on each manifest entry, returning per-sample WER results."""
    import librosa
    from transformers import WhisperForConditionalGeneration, WhisperProcessor

    processor = WhisperProcessor.from_pretrained(model_path)
    model = WhisperForConditionalGeneration.from_pretrained(model_path)
    model.generation_config.language = "vi"
    model.generation_config.task = "transcribe"
    model.generation_config.forced_decoder_ids = None
    model.eval()

    entries = manifest[:limit] if limit else manifest
    results = []
    for entry in entries:
        audio, _ = librosa.load(entry["audio"], sr=16000, duration=30.0)
        features = processor.feature_extractor(audio, sampling_rate=16000, return_tensors="pt")
        predicted_ids = model.generate(features.input_features)
        hyp = processor.tokenizer.batch_decode(predicted_ids, skip_special_tokens=True)[0]
        ref = entry["text"]
        results.append({"audio": entry["audio"], "ref": ref, "hyp": hyp, "wer": compute_wer(ref, hyp)})
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--model", default=str(DEFAULT_CHECKPOINT),
                         help=f"checkpoint dir (default {DEFAULT_CHECKPOINT}) or HF model id (e.g. {BASE_MODEL})")
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--limit", type=int, default=None, help="evaluate only the first N samples")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    manifest = load_manifest(manifest_path)
    if not manifest:
        print(f"Manifest empty: {manifest_path}")
        sys.exit(1)

    model_path = args.model
    if model_path == str(DEFAULT_CHECKPOINT) and not Path(model_path).exists():
        print(f"No fine-tuned checkpoint at {model_path} — falling back to base model {BASE_MODEL}")
        model_path = BASE_MODEL

    print(f"Evaluating model={model_path} on {len(manifest)} manifest entries (limit={args.limit})...")
    samples = transcribe_all(manifest, model_path, limit=args.limit)
    wer_mean = aggregate(samples)

    result = {
        "model": model_path,
        "manifest": str(manifest_path),
        "n": len(samples),
        "wer_mean": wer_mean,
        "samples": samples,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"WER mean: {wer_mean} over {len(samples)} samples")
    print(f"Results written -> {out_path}")


if __name__ == "__main__":
    main()
