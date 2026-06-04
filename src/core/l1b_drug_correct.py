# L1b — Drug Name Correction
# Input: raw transcript | Output: transcript với tên thuốc đã chuẩn hóa
# Rule: tên INN giữ nguyên tiếng Anh — KHÔNG dịch sang tiếng Việt
# FROZEN PIPELINE LAYER

from __future__ import annotations
import json
import unicodedata
from pathlib import Path
from functools import lru_cache

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "reference"


@lru_cache(maxsize=1)
def _load_drug_db() -> dict:
    with open(DATA_DIR / "drug_db.json", encoding="utf-8") as f:
        return json.load(f)


def _normalize_text(text: str) -> str:
    """Lowercase + remove diacritics để fuzzy match."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _build_alias_map() -> dict[str, str]:
    """
    Xây alias map: tên viết tắt / tên thường gặp → INN chuẩn.
    VD: "paracetamol" → "Paracetamol", "amox" → "Amoxicillin"
    """
    db = _load_drug_db()
    alias_map: dict[str, str] = {}

    for inn, entry in db.get("by_inn", {}).items():
        alias_map[_normalize_text(inn)] = inn
        for brand in entry.get("brand_names_vn", []):
            alias_map[_normalize_text(brand)] = inn
        for alias in entry.get("aliases", []):
            alias_map[_normalize_text(alias)] = inn

    return alias_map


_ALIAS_MAP: dict[str, str] | None = None


def _get_alias_map() -> dict[str, str]:
    global _ALIAS_MAP
    if _ALIAS_MAP is None:
        _ALIAS_MAP = _build_alias_map()
    return _ALIAS_MAP


def correct_drug_names(transcript: str) -> str:
    """
    Quét transcript, chuẩn hóa tên thuốc về INN chuẩn.
    VD: "amoxicilin" → "Amoxicillin", "panadol" → "Paracetamol"
    """
    if not transcript:
        return transcript

    alias_map = _get_alias_map()
    words = transcript.split()
    result = []

    i = 0
    while i < len(words):
        matched = False
        for n in (3, 2, 1):
            if i + n > len(words):
                continue
            candidate = " ".join(words[i:i+n])
            key = _normalize_text(candidate)
            if key in alias_map:
                result.append(alias_map[key])
                i += n
                matched = True
                break
        if not matched:
            result.append(words[i])
            i += 1

    return " ".join(result)


def extract_drug_candidates(transcript: str) -> list[dict]:
    """
    Tìm các tên thuốc trong transcript.
    Returns: list of {inn, position, original_text}
    """
    alias_map = _get_alias_map()
    candidates = []
    words = transcript.split()

    i = 0
    while i < len(words):
        for n in (3, 2, 1):
            if i + n > len(words):
                continue
            candidate = " ".join(words[i:i+n])
            key = _normalize_text(candidate)
            if key in alias_map:
                candidates.append({
                    "inn": alias_map[key],
                    "original_text": candidate,
                    "word_position": i,
                })
                i += n
                break
        else:
            i += 1

    return candidates
