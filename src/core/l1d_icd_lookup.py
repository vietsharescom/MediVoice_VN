# L1d — ICD-10-VN Lookup
# Input: diagnosis text | Output: ICD-10-VN code + display
# Source: data/reference/icd10vn.json (QĐ5837/QĐ-BYT)
# FROZEN PIPELINE LAYER

from __future__ import annotations
import json
import unicodedata
from pathlib import Path
from functools import lru_cache

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "reference"


@lru_cache(maxsize=1)
def _load_icd_db() -> dict:
    with open(DATA_DIR / "icd10vn.json", encoding="utf-8") as f:
        return json.load(f)


def _norm(text: str) -> str:
    """Lowercase + strip diacritics cho fuzzy search."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def lookup_by_code(code: str) -> dict | None:
    """Tra cứu theo mã ICD-10-VN (VD: 'J02.9')."""
    db = _load_icd_db()
    return db.get("by_code", {}).get(code.upper())


def search_by_text(query: str, max_results: int = 5) -> list[dict]:
    """
    Tìm kiếm ICD-10-VN theo tên bệnh tiếng Việt.
    Returns: list of {code, display, score}
    """
    db = _load_icd_db()
    q = _norm(query)
    results = []

    for code, entry in db.get("by_code", {}).items():
        display = entry.get("display", "")
        display_norm = _norm(display)

        # Exact match → score 1.0
        if q == display_norm:
            results.append({"code": code, "display": display, "score": 1.0})
            continue

        # Substring match
        if q in display_norm:
            score = len(q) / len(display_norm)
            results.append({"code": code, "display": display, "score": score})
        elif display_norm in q:
            score = len(display_norm) / len(q)
            results.append({"code": code, "display": display, "score": score * 0.9})

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:max_results]


def auto_lookup(diagnosis_text: str) -> tuple[str, str]:
    """
    Tự động tra ICD-10-VN từ text chẩn đoán.
    Returns: (icd_code, display_vn) hoặc ("", "") nếu không tìm được.
    """
    if not diagnosis_text:
        return "", ""

    results = search_by_text(diagnosis_text, max_results=1)
    if results and results[0]["score"] >= 0.5:
        return results[0]["code"], results[0]["display"]

    return "", ""


def validate_code(code: str) -> bool:
    """Kiểm tra mã ICD-10-VN có hợp lệ trong database."""
    return lookup_by_code(code) is not None
