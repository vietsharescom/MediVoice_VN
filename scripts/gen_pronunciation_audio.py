# scripts/gen_pronunciation_audio.py
# FID-VN-015 §3.2 / FID-VN-016 §1 — Pre-generate audio mẫu (gTTS) + f0 contour
# cache cho Pronunciation Recognition Lab (Part 3).
#
# Chạy 1 LẦN (offline, cần internet cho gTTS), output:
#   src/api/static/audio/pronunciation/<inn_slug>.mp3
#   src/api/static/audio/pronunciation/_cache.json
#       { "<inn>": {"phonetic_text": "...", "audio_file": "<inn_slug>.mp3",
#                    "f0_contour": [...]} }
#
# FID-VN-016: audio mẫu đọc theo CHUẨN THẾ GIỚI (gTTS tiếng Anh đọc tên INN
# gốc) — không phải phiên âm Việt heuristic. `phonetic_text` (VN heuristic)
# vẫn lưu trong cache để UI hiển thị dòng phiên âm Việt mặc định (dòng 2).
#
# KHÔNG đụng pipeline L0->L10 — chỉ sinh static assets cho UI.
# Audio mẫu (gTTS) KHÔNG chứa giọng BS — không phải biometric data.

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.l1b_drug_correct import _load_drug_db  # noqa: E402
from src.core.pronunciation_phonetic import get_reference_phonetic  # noqa: E402

OUT_DIR = ROOT / "src" / "api" / "static" / "audio" / "pronunciation"
CACHE_FILE = OUT_DIR / "_cache.json"


def _slug(inn: str) -> str:
    base = re.split(r"[\s(]", inn.strip())[0].lower()
    return re.sub(r"[^a-z0-9]", "", base) or "drug"


def main() -> None:
    from gtts import gTTS
    import librosa
    from src.core.vtln import extract_f0_contour

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    db = _load_drug_db()
    cache: dict = {}
    if CACHE_FILE.exists():
        cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))

    for inn, entry in db.get("by_inn", {}).items():
        phonetic = get_reference_phonetic(inn, entry)
        if not phonetic:
            continue

        slug = _slug(inn)
        mp3_path = OUT_DIR / f"{slug}.mp3"
        if not mp3_path.exists():
            # FID-VN-016: audio chuẩn thế giới — gTTS tiếng Anh đọc tên INN gốc
            en_text = re.split(r"[\s(]", inn.strip())[0]
            gTTS(text=en_text, lang="en").save(str(mp3_path))

        y, sr = librosa.load(str(mp3_path), sr=16000, mono=True)
        f0_contour = extract_f0_contour(y, sr=sr)

        cache[inn] = {
            "phonetic_text": phonetic,
            "audio_file": mp3_path.name,
            "f0_contour": f0_contour,
        }
        print(f"OK  {inn} -> {phonetic} ({mp3_path.name})")

    CACHE_FILE.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nĐã ghi {len(cache)} mục vào {CACHE_FILE}")


if __name__ == "__main__":
    main()
