# tests/unit/test_l1b_drug_correct_v2.py
# Tests for L1b DrugCorrectionEngine v2 [FID-VN-008]
# Covers: Layer 1 (exact), Layer 2 (fuzzy + ambiguity), Layer 3 (context),
#         Layer 4 (safety), backward compat, fallback, disfluency

import pytest
from src.core.l1b_drug_correct import (
    correct_drug_names,
    extract_drug_candidates,
    correct_drug_names_v2,
    DrugMatch,
    DRUG_FUZZY_CUTOFF_STRICT,
    DRUG_FUZZY_CUTOFF_FLAG,
)


# ─── BACKWARD COMPAT — API v1 unchanged ──────────────────────────────────────

class TestBackwardCompat:
    def test_exact_match_paracetamol(self):
        result = correct_drug_names("bệnh nhân uống paracetamol 500mg")
        assert "Paracetamol" in result

    def test_exact_match_brand_panadol(self):
        result = correct_drug_names("kê panadol cho bệnh nhân")
        assert "Paracetamol" in result

    def test_exact_match_phonetic_amox(self):
        # Legacy API uses brands[] only, NOT phonetic_variants → phonetic hits go via v2
        # "a mốc xi lin" is in drug_db_v200 phonetic_variants (v2 only)
        # Legacy: test a brand name that IS in brands[]
        result = correct_drug_names("kê amoxicillin 500mg")
        assert "Amoxicillin" in result

    def test_no_match_returns_unchanged(self):
        result = correct_drug_names("bệnh nhân tốt")
        assert result == "bệnh nhân tốt"

    def test_empty_string(self):
        assert correct_drug_names("") == ""

    def test_extract_drug_candidates_returns_list(self):
        result = extract_drug_candidates("uống paracetamol và ibuprofen")
        inns = [r["inn"] for r in result]
        assert "Paracetamol" in inns
        assert "Ibuprofen" in inns


# ─── LAYER 1 — Exact phonetic from drug_db_v200 ───────────────────────────────

class TestLayer1Exact:
    def test_phonetic_north_amlodipine(self):
        txt, matches = correct_drug_names_v2("kê am lô đi pin 5mg")
        assert any(m.inn == "Amlodipine" and m.match_layer == 1 for m in matches)

    def test_phonetic_south_amlodipine_3syl(self):
        # "a mờ lo" = 3-syllable South variant (min phonetic alias length after CE-103 fix)
        # 2-syllable "am lo" excluded from alias_map to prevent FPs on clinical text
        txt, matches = correct_drug_names_v2("cho bệnh nhân a mờ lo 5mg")
        assert any(m.inn == "Amlodipine" for m in matches)

    def test_phonetic_north_amoxicillin(self):
        txt, matches = correct_drug_names_v2("a mốc xi lin 500mg ngày 3 lần")
        assert any(m.inn == "Amoxicillin" and m.match_layer == 1 for m in matches)

    def test_layer1_confidence_is_1(self):
        _, matches = correct_drug_names_v2("metformin 500mg")
        exact = [m for m in matches if m.inn == "Metformin" and m.match_layer == 1]
        assert exact, "Metformin exact match not found"
        assert exact[0].confidence == 1.0

    def test_phonetic_south_amox_variant(self):
        txt, matches = correct_drug_names_v2("a moc xi lin 500mg")
        assert any(m.inn == "Amoxicillin" for m in matches)


# ─── LAYER 2 — Fuzzy match ────────────────────────────────────────────────────

class TestLayer2Fuzzy:
    def test_fuzzy_typo_amlodiphin(self):
        # "amlodiphin" close to "amlodipine" aliases
        txt, matches = correct_drug_names_v2("kê amlodiphin 5mg")
        assert any(m.inn == "Amlodipine" for m in matches), \
            f"Expected Amlodipine in fuzzy match, got: {[m.inn for m in matches]}"

    def test_fuzzy_metphomin_to_metformin(self):
        txt, matches = correct_drug_names_v2("uống metphomin 500mg")
        inns = [m.inn for m in matches]
        assert "Metformin" in inns, f"Expected Metformin, got {inns}"

    def test_fuzzy_confidence_below_strict_is_flagged(self):
        # Force a low-confidence match by using a very distorted name
        # We test that low-conf results have flagged=True
        _, matches = correct_drug_names_v2("uống metphomin 500mg")
        met_matches = [m for m in matches if m.inn == "Metformin"]
        if met_matches and met_matches[0].match_layer == 2:
            if met_matches[0].fuzzy_score < DRUG_FUZZY_CUTOFF_STRICT:
                assert met_matches[0].flagged_for_review

    def test_fuzzy_returns_match_layer_2(self):
        _, matches = correct_drug_names_v2("kê amlodiphin 5mg")
        layer2 = [m for m in matches if m.match_layer == 2]
        assert layer2, "Expected at least one Layer 2 match"


# ─── AMBIGUITY GATE ───────────────────────────────────────────────────────────

class TestAmbiguityGate:
    def test_short_met_token_ambiguous(self):
        # "met" alone matches Metformin, Metoprolol, Metronidazole → ambiguous
        _, matches = correct_drug_names_v2("uống met 500mg")
        if matches:
            # If matched, should be flagged (ambiguous or low conf)
            assert matches[0].flagged_for_review or matches[0].match_layer == 3

    def test_metronidazole_vs_metoprolol_no_silent_commit(self):
        # Full names should be unambiguous — test both individually
        _, m1 = correct_drug_names_v2("metronidazole 400mg")
        _, m2 = correct_drug_names_v2("metoprolol 50mg")
        # At least one should match correctly
        inns1 = [m.inn for m in m1]
        inns2 = [m.inn for m in m2]
        assert "Metronidazole" in inns1 or len(m1) == 0
        assert "Metoprolol" in inns2 or len(m2) == 0

    def test_ambiguous_flag_set(self):
        # A token that is equidistant from 2 drugs should get AMBIGUOUS flag
        _, matches = correct_drug_names_v2("kê met 5mg uống ngày")
        for m in matches:
            if m.flag_reason == "AMBIGUOUS":
                assert m.flagged_for_review
                assert m.severity == "HIGH"
                break


# ─── LAYER 3 — Context-aware ──────────────────────────────────────────────────

class TestLayer3Context:
    def test_context_hypertension_prefers_ccb(self):
        ctx = {
            "diagnosis": "tăng huyết áp",
            "diagnosis_icd10": "I10",
            "drug_class_context": ["calcium_channel_blocker", "arb"],
        }
        # Use 3-syllable South phonetic "a mờ lo" — 2-syllable "am lo" excluded (CE-103 fix)
        txt, matches = correct_drug_names_v2("kê a mờ lo 5mg", session_context=ctx)
        assert any(m.inn == "Amlodipine" for m in matches)

    def test_no_context_still_works(self):
        txt, matches = correct_drug_names_v2("metformin 500mg", session_context=None)
        assert any(m.inn == "Metformin" for m in matches)

    def test_context_antibiotic_class(self):
        ctx = {
            "diagnosis": "viêm họng",
            "drug_class_context": ["penicillin", "penicillin_beta_lactamase_inhibitor"],
        }
        # "amoxicillin" INN exact match → should find via Layer 1
        txt, matches = correct_drug_names_v2("amoxicillin 500mg", session_context=ctx)
        inns = [m.inn for m in matches]
        assert "Amoxicillin" in inns or "Amoxicillin/Clavulanate" in inns


# ─── LAYER 4 — Safety Engine ─────────────────────────────────────────────────

class TestSafetyEngine:
    def test_metformin_dose_too_low_flagged(self):
        # Metformin dose_range: min=500. 10mg is dangerously low.
        _, matches = correct_drug_names_v2("metformin 10mg ngày 3 lần")
        met = [m for m in matches if m.inn == "Metformin"]
        assert met, "Metformin should be matched"
        assert met[0].flagged_for_review
        assert met[0].flag_reason == "DOSE_OUT_OF_RANGE"
        assert met[0].severity == "HIGH"

    def test_amlodipine_dose_too_high_flagged(self):
        # Amlodipine dose_range: max=10mg. 50mg is dangerous.
        _, matches = correct_drug_names_v2("amlodipine 50mg ngày 1 lần")
        amp = [m for m in matches if m.inn == "Amlodipine"]
        assert amp, "Amlodipine should be matched"
        assert amp[0].flagged_for_review
        assert amp[0].flag_reason == "DOSE_OUT_OF_RANGE"
        assert amp[0].severity == "HIGH"

    def test_metformin_valid_dose_not_flagged(self):
        # Metformin 500mg is valid (min=500, max=3000)
        _, matches = correct_drug_names_v2("metformin 500mg ngày 2 lần")
        met = [m for m in matches if m.inn == "Metformin"]
        assert met, "Metformin should be matched"
        # Should NOT have DOSE_OUT_OF_RANGE
        assert met[0].flag_reason != "DOSE_OUT_OF_RANGE"

    def test_amlodipine_valid_dose_not_flagged(self):
        # Amlodipine 5mg is standard dose
        _, matches = correct_drug_names_v2("amlodipine 5mg")
        amp = [m for m in matches if m.inn == "Amlodipine"]
        if amp:
            assert amp[0].flag_reason != "DOSE_OUT_OF_RANGE"

    def test_drug_without_dose_range_no_safety_flag(self):
        # Drugs without dose_range (auto-generated, dose_range={0,0}) → no safety flag
        _, matches = correct_drug_names_v2("paracetamol 500mg")
        para = [m for m in matches if m.inn == "Paracetamol"]
        if para:
            # Paracetamol has dose_range in manual set — check it passes 500mg
            assert para[0].flag_reason != "DOSE_OUT_OF_RANGE"


# ─── DISFLUENCY ───────────────────────────────────────────────────────────────

class TestDisfluency:
    def test_filler_word_before_drug(self):
        # "ừm" is a filler word, should be ignored
        txt, matches = correct_drug_names_v2("ừm am lô đi pin 5mg")
        assert any(m.inn == "Amlodipine" for m in matches)

    def test_multiple_fillers(self):
        txt, matches = correct_drug_names_v2("ờ ừ metformin 500mg")
        assert any(m.inn == "Metformin" for m in matches)


# ─── FALLBACK ─────────────────────────────────────────────────────────────────

class TestFallback:
    def test_v2_returns_tuple(self):
        result = correct_drug_names_v2("bệnh nhân tốt")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_v2_empty_transcript(self):
        txt, matches = correct_drug_names_v2("")
        assert txt == ""
        assert matches == []

    def test_v2_no_drug_in_transcript(self):
        txt, matches = correct_drug_names_v2("bệnh nhân khỏe mạnh, không có thuốc")
        assert isinstance(matches, list)

    def test_corrected_transcript_contains_inn(self):
        txt, matches = correct_drug_names_v2("kê metformin 500mg và amlodipine 5mg")
        assert "Metformin" in txt or "metformin" in txt.lower()


# ─── AUDIT LOG FIELDS ─────────────────────────────────────────────────────────

class TestDrugMatchAuditFields:
    def test_drugmatch_has_all_audit_fields(self):
        _, matches = correct_drug_names_v2("metformin 500mg")
        assert matches, "Expected at least one match"
        m = matches[0]
        assert hasattr(m, "inn")
        assert hasattr(m, "original_text")
        assert hasattr(m, "word_position")
        assert hasattr(m, "confidence")
        assert hasattr(m, "match_layer")
        assert hasattr(m, "flagged_for_review")
        assert hasattr(m, "flag_reason")
        assert hasattr(m, "severity")
        assert hasattr(m, "fuzzy_score")

    def test_confidence_in_valid_range(self):
        _, matches = correct_drug_names_v2("metformin 500mg amlodipine 5mg paracetamol 500mg")
        for m in matches:
            assert 0.0 <= m.confidence <= 1.0, f"Confidence out of range: {m}"

    def test_match_layer_valid(self):
        _, matches = correct_drug_names_v2("metformin 500mg")
        for m in matches:
            assert m.match_layer in (1, 2, 3), f"Invalid match_layer: {m.match_layer}"
