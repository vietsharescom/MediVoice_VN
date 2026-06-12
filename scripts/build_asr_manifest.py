#!/usr/bin/env python
# scripts/build_asr_manifest.py — FID-VN-007: build ASR fine-tune manifest
# Input:  data/eval/ref_voice_transcripts.json (57 real BS-voice clips, transcript_gt)
# Output: data/asr_manifest/ref_voice_manifest.jsonl — {"audio": <path>, "text": <transcript_gt>}
# Usage: python -X utf8 scripts/build_asr_manifest.py

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

REF_TRANSCRIPTS = ROOT / "data" / "eval" / "ref_voice_transcripts.json"
AUDIO_ROOT = ROOT / "data" / "audio" / "reference_voices"
OUT_PATH = ROOT / "data" / "asr_manifest" / "ref_voice_manifest.jsonl"

# bs code (ref_voice_transcripts.json) -> reference_voices subfolder
_BS_FOLDER = {
    "HN": "BS_hanoi",
    "DN": "BS_danang",
    "SG": "BS_saigon",
}


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


def main():
    manifest = build_manifest()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        for entry in manifest:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"Wrote {len(manifest)} entries -> {OUT_PATH}")


if __name__ == "__main__":
    main()
