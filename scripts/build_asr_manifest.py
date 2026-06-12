#!/usr/bin/env python
# scripts/build_asr_manifest.py — FID-VN-007: build ASR fine-tune manifests
#
# Sources:
#   1. Reference voices (always available): data/eval/ref_voice_transcripts.json
#      (57 real BS-voice clips, transcript_gt) -> ref_voice_manifest.jsonl
#   2. VietMed (PA-024, needs HF_TOKEN): data/vietmed/{split}/metadata.jsonl
#      + data/vietmed/{split}/audio/*.wav -> vietmed_manifest.jsonl (all splits combined)
#   3. Pilot audio (not yet recorded, Colab/Kaggle exception 2026-06-11):
#      <pilot_dir>/*.wav + sibling .json/.txt transcript -> pilot_manifest.jsonl
#
# Each manifest line: {"audio": <path>, "text": <transcript>}
#
# Usage:
#   python -X utf8 scripts/build_asr_manifest.py                  # ref voices only
#   python -X utf8 scripts/build_asr_manifest.py --vietmed         # + VietMed (if data/vietmed/ present)
#   python -X utf8 scripts/build_asr_manifest.py --pilot <dir>      # + pilot audio dir
#   python -X utf8 scripts/build_asr_manifest.py --vietmed --pilot data/audio/pilot --combined

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

REF_TRANSCRIPTS = ROOT / "data" / "eval" / "ref_voice_transcripts.json"
AUDIO_ROOT = ROOT / "data" / "audio" / "reference_voices"
MANIFEST_DIR = ROOT / "data" / "asr_manifest"
OUT_PATH = MANIFEST_DIR / "ref_voice_manifest.jsonl"

# bs code (ref_voice_transcripts.json) -> reference_voices subfolder
_BS_FOLDER = {
    "HN": "BS_hanoi",
    "DN": "BS_danang",
    "SG": "BS_saigon",
}

# candidate field names for the transcript text in VietMed metadata.jsonl
_VIETMED_TEXT_FIELDS = ("text", "transcription", "sentence", "transcript")

VIETMED_ROOT = ROOT / "data" / "vietmed"


def build_manifest(transcripts_path: Path = REF_TRANSCRIPTS, audio_root: Path = AUDIO_ROOT) -> list[dict]:
    """Build manifest entries {"audio": <abs path str>, "text": <transcript_gt>} from
    ref_voice_transcripts.json, resolving audio paths via the bs->folder mapping.

    Entries whose audio file does not exist on disk are skipped.
    """
    with open(transcripts_path, encoding="utf-8") as f:
        clips = json.load(f)

    manifest = []
    for clip in clips:
        folder = _BS_FOLDER.get(clip["bs"])
        if folder is None:
            continue
        audio_path = audio_root / folder / clip["file"]
        if not audio_path.exists():
            continue
        manifest.append({"audio": str(audio_path), "text": clip["transcript_gt"]})
    return manifest


def _vietmed_text(entry: dict) -> str | None:
    for field in _VIETMED_TEXT_FIELDS:
        if field in entry and entry[field]:
            return entry[field]
    return None


def build_vietmed_manifest(
    vietmed_root: Path = VIETMED_ROOT, splits: tuple[str, ...] = ("train", "dev", "test", "cv")
) -> list[dict]:
    """Build manifest entries from data/vietmed/{split}/metadata.jsonl + audio/.

    Each metadata.jsonl line is expected to carry a transcript under one of
    _VIETMED_TEXT_FIELDS and an audio filename under "wav_file" (written by
    download_vietmed.py), falling back to "audio"/"file_name"/"audio_name"
    (resolved against {split}/audio/). Entries with missing audio files or
    unrecognized transcript fields are skipped. Returns [] if vietmed_root
    or a split's metadata.jsonl does not exist (dataset not downloaded yet).
    """
    manifest = []
    for split in splits:
        split_dir = vietmed_root / split
        metadata_path = split_dir / "metadata.jsonl"
        if not metadata_path.exists():
            continue
        audio_dir = split_dir / "audio"
        with open(metadata_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                text = _vietmed_text(entry)
                if text is None:
                    continue
                audio_name = entry.get("wav_file") or entry.get("audio") or entry.get("file_name") or entry.get("audio_name")
                if audio_name is None:
                    continue
                audio_path = audio_dir / audio_name
                if not audio_path.exists():
                    continue
                manifest.append({"audio": str(audio_path), "text": text})
    return manifest


def build_pilot_manifest(pilot_dir: Path) -> list[dict]:
    """Build manifest entries from a directory of pilot audio.

    For each *.wav file, looks for a sibling transcript file with the same
    stem and extension .txt (plain text) or .json (with a "text" field).
    Files without a matching transcript are skipped. Returns [] if pilot_dir
    does not exist.
    """
    manifest = []
    if not pilot_dir.exists():
        return manifest

    for audio_path in sorted(pilot_dir.glob("*.wav")):
        txt_path = audio_path.with_suffix(".txt")
        json_path = audio_path.with_suffix(".json")
        text = None
        if txt_path.exists():
            text = txt_path.read_text(encoding="utf-8").strip()
        elif json_path.exists():
            with open(json_path, encoding="utf-8") as f:
                text = json.load(f).get("text")
        if not text:
            continue
        manifest.append({"audio": str(audio_path), "text": text})
    return manifest


def _write_manifest(manifest: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for entry in manifest:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vietmed", action="store_true", help="also build VietMed manifest (data/vietmed/)")
    parser.add_argument("--pilot", default=None, help="also build pilot manifest from this directory")
    parser.add_argument("--combined", action="store_true", help="write a combined manifest of all sources")
    args = parser.parse_args()

    ref_manifest = build_manifest()
    _write_manifest(ref_manifest, OUT_PATH)
    print(f"Wrote {len(ref_manifest)} entries -> {OUT_PATH}")

    combined = list(ref_manifest)

    if args.vietmed:
        vietmed_manifest = build_vietmed_manifest()
        vietmed_out = MANIFEST_DIR / "vietmed_manifest.jsonl"
        _write_manifest(vietmed_manifest, vietmed_out)
        print(f"Wrote {len(vietmed_manifest)} entries -> {vietmed_out}")
        combined.extend(vietmed_manifest)

    if args.pilot:
        pilot_manifest = build_pilot_manifest(Path(args.pilot))
        pilot_out = MANIFEST_DIR / "pilot_manifest.jsonl"
        _write_manifest(pilot_manifest, pilot_out)
        print(f"Wrote {len(pilot_manifest)} entries -> {pilot_out}")
        combined.extend(pilot_manifest)

    if args.combined:
        combined_out = MANIFEST_DIR / "combined_manifest.jsonl"
        _write_manifest(combined, combined_out)
        print(f"Wrote {len(combined)} entries -> {combined_out}")


if __name__ == "__main__":
    main()
