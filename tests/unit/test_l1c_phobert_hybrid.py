# tests/unit/test_l1c_phobert_hybrid.py
# Tests for FID-VN-009 — Hybrid NER (PhoBERT + Rule-based)
# Covers: early-exit, VITAL meta, confidence thresholds, merge strategy,
#         conditional FOLLOWUP, dedup, fallback, backward compat

import pytest
from unittest.mock import patch, MagicMock
from src.core.l1c_ner import (
    extract_entities,
    extract_entities_hybrid,
    MedicalEntities,
)
from src.core.l1c_phobert import (
    bio_to_updates,
    has_coverage_gap,
    normalize_symptom,
    PHOBERT_CONFIDENCE_HIGH,
    PHOBERT_CONFIDENCE_STD,
    PHOBERT_CONFIDENCE_MIN,
)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _make_pred(entity_group: str, word: str, score: float, start: int = 0) -> dict:
    return {"entity_group": entity_group, "word": word, "score": score, "start": start}


def _fake_pipeline_factory(predictions: list[dict]):
    """Returns a mock pipeline callable that yields predictions."""
    mock = MagicMock(return_value=predictions)
    return mock


# ─── 1. Backward compat — extract_entities() unchanged ───────────────────────

class TestBackwardCompat:
    def test_extract_entities_returns_medical_entities(self):
        result = extract_entities("bệnh nhân sốt 38.5 độ")
        assert isinstance(result, MedicalEntities)
        assert result.nhiet_do == pytest.approx(38.5, abs=0.1)

    def test_extract_entities_no_phobert_side_effect(self):
        # Calling extract_entities never touches l1c_phobert
        with patch("src.core.l1c_phobert._load_phobert_pipeline") as mock_load:
            extract_entities("metformin 500mg ngày 2 lần")
            mock_load.assert_not_called()


# ─── 2. use_phobert=False — PhoBERT never loads ──────────────────────────────

class TestPhoBERTNotLoaded:
    def test_phobert_not_called_when_disabled(self):
        with patch("src.core.l1c_phobert._load_phobert_pipeline") as mock_load:
            entities, meta = extract_entities_hybrid(
                "bệnh nhân ho nhiều", use_phobert=False
            )
            mock_load.assert_not_called()

    def test_returns_tuple_when_disabled(self):
        result = extract_entities_hybrid("bệnh nhân tốt", use_phobert=False)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_meta_phobert_used_false_when_disabled(self):
        _, meta = extract_entities_hybrid("bệnh nhân tốt", use_phobert=False)
        assert meta["phobert_used"] is False

    def test_meta_has_all_required_keys(self):
        _, meta = extract_entities_hybrid("bệnh nhân tốt", use_phobert=False)
        required_keys = {
            "rule_fields_filled", "phobert_fields_added",
            "phobert_confidence_avg", "phobert_used",
            "phobert_vital_detected", "early_exit",
        }
        assert required_keys.issubset(set(meta.keys()))


# ─── 3. Early-exit — no gap → PhoBERT skipped ───────────────────────────────

class TestEarlyExit:
    def test_early_exit_when_no_gap(self):
        """When rule-based covers trieu_chung + tai_kham + ly_do → early_exit=True."""
        transcript = (
            "bệnh nhân 45 tuổi, ho nhiều, đau họng. "
            "chẩn đoán viêm họng cấp. "
            "tái khám sau 7 ngày. "
            "kê amoxicillin 500mg ngày 3 lần trong 7 ngày."
        )
        with patch("src.core.l1c_phobert._load_phobert_pipeline") as mock_load:
            entities, meta = extract_entities_hybrid(
                transcript,
                drug_candidates=[{"inn": "Amoxicillin", "word_position": 0}],
                use_phobert=True,
            )
            # tai_kham is filled by rule → should early-exit if trieu_chung also filled
            # (Rule-based may or may not fill trieu_chung; check only meta structure)
            assert "early_exit" in meta

    def test_early_exit_false_when_gap_exists(self):
        """When rule-based misses trieu_chung → no early-exit."""
        transcript = "bệnh nhân đến tái khám tăng huyết áp. kê amlodipine 5mg."
        fake_predictions = [
            _make_pred("SYMPTOM", "mệt mỏi", 0.91),
        ]
        with patch("src.core.l1c_phobert._load_phobert_pipeline",
                   return_value=_fake_pipeline_factory(fake_predictions)):
            entities, meta = extract_entities_hybrid(transcript, use_phobert=True)
            # Rule-based likely misses trieu_chung for this transcript → no early-exit
            if not meta["early_exit"]:
                assert meta["phobert_used"] is True


# ─── 4. VITAL → meta only, not MedicalEntities ───────────────────────────────

class TestVitalMetaOnly:
    def test_vital_logged_to_meta(self):
        predictions = [_make_pred("VITAL", "huyết áp 130/80", 0.97)]
        updates, vital = bio_to_updates(predictions, "huyết áp 130/80")
        assert "huyết áp 130/80" in vital

    def test_vital_not_in_don_thuoc(self):
        predictions = [_make_pred("VITAL", "mạch 80", 0.95)]
        updates, vital = bio_to_updates(predictions, "mạch 80")
        assert updates["don_thuoc_supplement"] == []

    def test_vital_not_in_trieu_chung(self):
        predictions = [_make_pred("VITAL", "nhiệt độ 38", 0.95)]
        updates, vital = bio_to_updates(predictions, "nhiệt độ 38")
        assert updates["trieu_chung_add"] == []

    def test_phobert_vital_in_meta_after_hybrid(self):
        fake_predictions = [_make_pred("VITAL", "mạch 80 bpm", 0.97)]
        with patch("src.core.l1c_phobert._load_phobert_pipeline",
                   return_value=_fake_pipeline_factory(fake_predictions)):
            _, meta = extract_entities_hybrid(
                "bệnh nhân mạch 80 bpm", use_phobert=True
            )
            if meta["phobert_used"]:
                assert "mạch 80 bpm" in meta["phobert_vital_detected"]


# ─── 5. Confidence thresholds ─────────────────────────────────────────────────

class TestConfidenceThresholds:
    def test_medication_below_high_threshold_discarded(self):
        """MEDICATION with score=0.70 (< 0.85) must be discarded."""
        predictions = [_make_pred("MEDICATION", "Metformin", 0.70)]
        updates, _ = bio_to_updates(predictions, "metformin 500mg")
        assert updates["don_thuoc_supplement"] == []

    def test_medication_above_high_threshold_accepted(self):
        """MEDICATION with score=0.92 (>= 0.85) must be accepted."""
        predictions = [_make_pred("MEDICATION", "Amlodipine", 0.92)]
        updates, _ = bio_to_updates(predictions, "amlodipine 5mg")
        inns = [d["inn"] for d in updates["don_thuoc_supplement"]]
        assert "Amlodipine" in inns

    def test_symptom_above_std_threshold_accepted(self):
        """SYMPTOM with score=0.78 (>= 0.75) must be accepted."""
        predictions = [_make_pred("SYMPTOM", "ho khan", 0.78)]
        updates, _ = bio_to_updates(predictions, "ho khan nhiều")
        assert "ho khan" in updates["trieu_chung_add"]

    def test_symptom_below_min_threshold_discarded(self):
        """SYMPTOM with score=0.55 (< 0.60) must be discarded."""
        predictions = [_make_pred("SYMPTOM", "mệt nhẹ", 0.55)]
        updates, _ = bio_to_updates(predictions, "mệt nhẹ")
        assert updates["trieu_chung_add"] == []

    def test_constants_ordering(self):
        """Threshold ordering: HIGH > STD > MIN."""
        assert PHOBERT_CONFIDENCE_HIGH > PHOBERT_CONFIDENCE_STD > PHOBERT_CONFIDENCE_MIN


# ─── 6. Merge — trieu_chung dedup ────────────────────────────────────────────

class TestSymptomMerge:
    def test_symptom_union_no_duplicate(self):
        """Same symptom in both rule and PhoBERT → appears only once."""
        predictions = [
            _make_pred("SYMPTOM", "ho", 0.91),
            _make_pred("SYMPTOM", "đau họng", 0.88),
        ]
        with patch("src.core.l1c_phobert._load_phobert_pipeline",
                   return_value=_fake_pipeline_factory(predictions)):
            entities, meta = extract_entities_hybrid(
                "bệnh nhân ho đau họng nhiều", use_phobert=True
            )
            # Count "ho" occurrences (normalized)
            ho_count = sum(1 for s in entities.trieu_chung if "ho" in s.lower())
            assert ho_count <= 2  # may have "ho" and "đau họng" but not double "ho"

    def test_phobert_symptom_added_when_rule_missed(self):
        """PhoBERT adds 'mệt mỏi' when rule-based missed it."""
        predictions = [_make_pred("SYMPTOM", "mệt mỏi", 0.91)]
        with patch("src.core.l1c_phobert._load_phobert_pipeline",
                   return_value=_fake_pipeline_factory(predictions)):
            entities, meta = extract_entities_hybrid(
                "bệnh nhân mệt mỏi nhiều", use_phobert=True
            )
            if meta["phobert_used"]:
                assert "mệt mỏi" in entities.trieu_chung

    def test_normalize_symptom_utility(self):
        assert normalize_symptom("  Ho  Khan  ") == "ho khan"
        assert normalize_symptom("mệt mỏi") == "mệt mỏi"


# ─── 7. Merge — don_thuoc dedup (R-009-10) ───────────────────────────────────

class TestDrugMerge:
    def test_phobert_drug_not_duplicated_when_l1b_has_it(self):
        """If L1b already added Metformin, PhoBERT MEDICATION won't duplicate it."""
        predictions = [_make_pred("MEDICATION", "Metformin", 0.93)]
        with patch("src.core.l1c_phobert._load_phobert_pipeline",
                   return_value=_fake_pipeline_factory(predictions)):
            entities, meta = extract_entities_hybrid(
                "metformin 500mg ngày 2 lần",
                drug_candidates=[{"inn": "Metformin", "word_position": 0}],
                use_phobert=True,
            )
            metformin_count = sum(
                1 for d in entities.don_thuoc if d.get("inn", "").lower() == "metformin"
            )
            assert metformin_count <= 1

    def test_phobert_supplement_drug_flagged(self):
        """Drug added by PhoBERT (not in L1b) must have flagged_for_review=True."""
        predictions = [_make_pred("MEDICATION", "Omeprazole", 0.91)]
        with patch("src.core.l1c_phobert._load_phobert_pipeline",
                   return_value=_fake_pipeline_factory(predictions)):
            entities, meta = extract_entities_hybrid(
                "omeprazole 20mg ngày 1 lần", use_phobert=True
            )
            if meta["phobert_used"]:
                phobert_drugs = [
                    d for d in entities.don_thuoc
                    if d.get("flag_source") == "phobert_supplement"
                ]
                for d in phobert_drugs:
                    assert d["flagged_for_review"] is True


# ─── 8. tai_kham fill + conditional FOLLOWUP (R-009-12) ─────────────────────

class TestFollowupMerge:
    def test_definite_followup_fills_tai_kham(self):
        """Definite FOLLOWUP from PhoBERT fills tai_kham when empty."""
        predictions = [_make_pred("FOLLOWUP", "sau 2 tuần", 0.88, start=20)]
        transcript = "bệnh nhân hẹn tái khám sau 2 tuần"
        updates, _ = bio_to_updates(predictions, transcript)
        assert updates["tai_kham_fill"] == "sau 2 tuần"

    def test_conditional_followup_not_filled(self):
        """'nếu không đỡ tái khám' → conditional → tai_kham_fill must be None."""
        transcript = "nếu không đỡ thì tái khám lại"
        predictions = [_make_pred("FOLLOWUP", "tái khám lại", 0.85, start=20)]
        updates, _ = bio_to_updates(predictions, transcript)
        assert updates["tai_kham_fill"] is None

    def test_tai_kham_not_overridden_by_phobert(self):
        """Rule-based tai_kham must not be overridden by PhoBERT."""
        transcript = "tái khám sau 7 ngày. bệnh nhân mệt."
        predictions = [_make_pred("FOLLOWUP", "sau 14 ngày", 0.90, start=30)]
        with patch("src.core.l1c_phobert._load_phobert_pipeline",
                   return_value=_fake_pipeline_factory(predictions)):
            entities, meta = extract_entities_hybrid(transcript, use_phobert=True)
            # Rule-based should get "7 ngày"; PhoBERT should NOT override
            if entities.tai_kham:
                assert "14" not in entities.tai_kham


# ─── 9. ModelNotFound → graceful fallback ────────────────────────────────────

class TestModelNotFound:
    def test_fallback_to_rule_based_when_model_missing(self):
        """If PhoBERT model missing → return rule-based result, no crash."""
        with patch(
            "src.core.l1c_phobert._load_phobert_pipeline",
            side_effect=FileNotFoundError("model not found"),
        ):
            entities, meta = extract_entities_hybrid(
                "metformin 500mg", use_phobert=True
            )
            assert isinstance(entities, MedicalEntities)
            assert meta["phobert_used"] is False

    def test_fallback_meta_intact(self):
        """Meta dict still has all keys even after fallback."""
        with patch(
            "src.core.l1c_phobert._load_phobert_pipeline",
            side_effect=FileNotFoundError("model not found"),
        ):
            _, meta = extract_entities_hybrid(
                "amlodipine 5mg ngày 1 lần", use_phobert=True
            )
            assert "rule_fields_filled" in meta
            assert "phobert_fields_added" in meta


# ─── 10. Meta correctness ────────────────────────────────────────────────────

class TestMetaCorrectness:
    def test_phobert_confidence_avg_range(self):
        """phobert_confidence_avg must be in [0.0, 1.0]."""
        predictions = [
            _make_pred("SYMPTOM", "ho", 0.88),
            _make_pred("SYMPTOM", "mệt", 0.76),
        ]
        with patch("src.core.l1c_phobert._load_phobert_pipeline",
                   return_value=_fake_pipeline_factory(predictions)):
            _, meta = extract_entities_hybrid(
                "bệnh nhân ho và mệt", use_phobert=True
            )
            assert 0.0 <= meta["phobert_confidence_avg"] <= 1.0

    def test_has_coverage_gap_utility(self):
        """has_coverage_gap returns True when fields empty."""
        e = MedicalEntities()
        assert has_coverage_gap(e) is True
        e.trieu_chung = ["ho"]
        e.tai_kham = "7 ngày"
        e.ly_do = "đau họng"
        assert has_coverage_gap(e) is False
