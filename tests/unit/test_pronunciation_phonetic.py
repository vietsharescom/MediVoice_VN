# tests/unit/test_pronunciation_phonetic.py
# FID-VN-015 §3.1/Q4 — Phiên âm tiếng Việt cho tên thuốc
# (Pronunciation Recognition Lab — Part 3)

from __future__ import annotations

from src.core.pronunciation_phonetic import (
    transliterate_to_vn_phonetic,
    get_reference_phonetic,
    get_pronunciation_en,
    is_garbled_transcript,
    apply_stress_hint,
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


# ── FID-VN-016 — get_pronunciation_en / is_garbled_transcript ───────────────

def test_get_pronunciation_en_returns_field_from_drug_entry():
    drug_entry = {"pronunciation_en": "par-a-SEE-ta-mol"}
    assert get_pronunciation_en("Paracetamol", drug_entry) == "par-a-SEE-ta-mol"


def test_get_pronunciation_en_returns_none_when_missing():
    assert get_pronunciation_en("Paracetamol", {"brands": []}) is None
    assert get_pronunciation_en("Paracetamol", None) is None


def test_is_garbled_transcript_false_for_normal_reading():
    assert is_garbled_transcript("pa ra xê ta môn", "Paracetamol") is False


def test_is_garbled_transcript_true_for_repeated_reading():
    transcript = " ".join(["paracetamol"] * 16)  # > 3 x 5 âm tiết kỳ vọng
    assert is_garbled_transcript(transcript, "Paracetamol") is True


def test_is_garbled_transcript_false_for_empty_transcript():
    assert is_garbled_transcript("", "Paracetamol") is False


# ── FID-VN-017 §2 — apply_stress_hint (CT-041a) ─────────────────────────────

def test_apply_stress_hint_uppercases_matching_syllable():
    assert apply_stress_hint("pa ra xê ta môn", "par-a-SEE-ta-mol") == "pa ra XÊ ta môn"


def test_apply_stress_hint_returns_unchanged_when_pronunciation_en_none():
    assert apply_stress_hint("pa ra xê ta môn", None) == "pa ra xê ta môn"


def test_apply_stress_hint_returns_unchanged_when_pronunciation_en_empty():
    assert apply_stress_hint("pa ra xê ta môn", "") == "pa ra xê ta môn"


def test_apply_stress_hint_returns_unchanged_when_vn_phonetic_empty():
    assert apply_stress_hint("", "par-a-SEE-ta-mol") == ""


def test_apply_stress_hint_short_vn_phonetic_metformin():
    """3 âm tiết VN, stress ở giữa (idx_en=1/3 -> idx_vn=1)."""
    vn = transliterate_to_vn_phonetic("Metformin")
    assert apply_stress_hint(vn, "met-FOR-min") == "mêtp HÔR min"


def test_apply_stress_hint_long_vn_phonetic_empagliflozin():
    """5 âm tiết VN, stress đầu từ (idx_en=0 -> idx_vn=0)."""
    vn = transliterate_to_vn_phonetic("Empagliflozin")
    result = apply_stress_hint(vn, "EM-pa-gli-FLOH-zin")
    assert result.split()[0] == vn.split()[0].upper()


# ── FID-VN-017 §2 — get_reference_phonetic with pronunciation_en param ─────

def test_get_reference_phonetic_applies_stress_hint_when_pronunciation_en_given():
    drug_entry = {"brands": ["para xê ta môn", "Panadol"]}
    result = get_reference_phonetic("Paracetamol", drug_entry, "par-a-SEE-ta-mol")
    assert result == "para xê TA môn"


def test_get_reference_phonetic_unchanged_without_pronunciation_en():
    drug_entry = {"brands": ["para xê ta môn", "Panadol"]}
    assert get_reference_phonetic("Paracetamol", drug_entry) == "para xê ta môn"
    assert get_reference_phonetic("Paracetamol", drug_entry, None) == "para xê ta môn"


# ── FID-VN-017 §1 (CT-040) — 9 thuốc tim_mach mới có pronunciation_en ───────

def test_tim_mach_drugs_have_pronunciation_en():
    import json
    from pathlib import Path

    db = json.loads(
        Path("data/reference/drug_db_v200.json").read_text(encoding="utf-8")
    )
    by_inn = db["by_inn"]
    new_drugs = [
        "Warfarin", "Clopidogrel", "Telmisartan", "Olmesartan", "Irbesartan",
        "Nifedipine", "Lercanidipine", "Metoprolol", "Indapamide",
    ]
    for inn in new_drugs:
        entry = by_inn[inn]
        assert entry.get("pronunciation_en"), f"{inn} missing pronunciation_en"
        assert entry.get("pronunciation_en_source")
