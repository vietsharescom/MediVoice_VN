# tests/unit/test_pronunciation_phonetic.py
# FID-VN-015 §3.1/Q4 — Phiên âm tiếng Việt cho tên thuốc
# (Pronunciation Recognition Lab — Part 3)

from __future__ import annotations

from src.core.pronunciation_phonetic import (
    transliterate_to_vn_phonetic,
    get_reference_phonetic,
)


def test_transliterate_paracetamol_matches_drug_db_brand():
    """Heuristic phải khớp với brand variant đã có trong drug_db.json."""
    assert transliterate_to_vn_phonetic("Paracetamol") == "pa ra xê ta môn"


def test_transliterate_empty_input_returns_empty_string():
    assert transliterate_to_vn_phonetic("") == ""
    assert transliterate_to_vn_phonetic("123") == ""


def test_transliterate_no_duplicate_trailing_syllable():
    """Regression: bug cũ sinh ra âm tiết cuối bị lặp 2 lần."""
    result = transliterate_to_vn_phonetic("Ibuprofen")
    syllables = result.split()
    assert syllables[-1] != syllables[-2]


def test_get_reference_phonetic_uses_drug_db_brand_when_available():
    drug_entry = {"brands": ["para xê ta môn", "Panadol"]}
    assert get_reference_phonetic("Paracetamol", drug_entry) == "para xê ta môn"


def test_get_reference_phonetic_falls_back_to_heuristic():
    assert get_reference_phonetic("Aspirin (Acetylsalicylic acid)", None) == "as pi rin"


def test_get_reference_phonetic_no_brand_match_uses_heuristic():
    drug_entry = {"brands": ["Panadol"]}  # không phải lowercase nhiều âm tiết
    result = get_reference_phonetic("Paracetamol", drug_entry)
    assert result == transliterate_to_vn_phonetic("Paracetamol")
