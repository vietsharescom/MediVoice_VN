"""
Unit tests for core pipeline layers L0–L10.
@verifies SRS-L0-*, SRS-L1b-*, SRS-L1c-*, SRS-L1d-*, SRS-L2-*, SRS-L3-*,
          SRS-L4-*, SRS-L5-*, SRS-L8-*, SRS-L10-*
"""
import pytest
import sqlite3
import tempfile
from pathlib import Path


# ─── L1b Drug Correction ─────────────────────────────────────────────────────

class TestL1bDrugCorrection:
    def test_correct_drug_returns_string(self):
        from src.core.l1b_drug_correct import correct_drug_names
        result = correct_drug_names("bệnh nhân dùng Paracetamol")
        assert isinstance(result, str)

    def test_empty_transcript_returns_empty(self):
        from src.core.l1b_drug_correct import correct_drug_names
        assert correct_drug_names("") == ""
        assert correct_drug_names(None) is None

    def test_extract_drug_candidates_returns_list(self):
        from src.core.l1b_drug_correct import extract_drug_candidates
        drugs = extract_drug_candidates("uống Amoxicillin 500mg")
        assert isinstance(drugs, list)

    def test_extract_finds_amoxicillin(self):
        from src.core.l1b_drug_correct import extract_drug_candidates
        drugs = extract_drug_candidates("Amoxicillin 500mg 2 viên")
        inns = [d["inn"] for d in drugs]
        assert "Amoxicillin" in inns

    def test_extract_returns_dict_with_inn_key(self):
        from src.core.l1b_drug_correct import extract_drug_candidates
        drugs = extract_drug_candidates("Paracetamol 500mg")
        if drugs:
            assert "inn" in drugs[0]
            assert "original_text" in drugs[0]
            assert "word_position" in drugs[0]

    def test_drug_not_translated_to_vietnamese(self):
        from src.core.l1b_drug_correct import correct_drug_names
        # INN names must stay in English
        result = correct_drug_names("Paracetamol")
        assert "thuốc hạ sốt" not in result.lower()


# ─── L1c NER ─────────────────────────────────────────────────────────────────

class TestL1cNER:
    def test_extract_entities_returns_medical_entities(self):
        from src.core.l1c_ner import extract_entities, MedicalEntities
        ents = extract_entities("sốt 38.5")
        assert isinstance(ents, MedicalEntities)

    def test_extract_temperature(self):
        from src.core.l1c_ner import extract_entities
        ents = extract_entities("bệnh nhân sốt 38.5")
        assert ents.nhiet_do == 38.5

    def test_extract_blood_pressure(self):
        from src.core.l1c_ner import extract_entities
        ents = extract_entities("huyết áp 120/80")
        assert ents.huyet_ap_tam_thu == 120
        assert ents.huyet_ap_tam_truong == 80

    def test_extract_diagnosis(self):
        from src.core.l1c_ner import extract_entities
        ents = extract_entities("chẩn đoán viêm họng cấp kê thuốc")
        assert "viêm họng cấp" in ents.chan_doan

    def test_extract_tai_kham(self):
        from src.core.l1c_ner import extract_entities
        ents = extract_entities("tái khám sau 7 ngày")
        assert ents.tai_kham != ""
        assert "7" in ents.tai_kham

    def test_extract_no_crash_on_empty(self):
        from src.core.l1c_ner import extract_entities
        ents = extract_entities("")
        assert ents.nhiet_do is None
        assert ents.chan_doan == ""

    def test_extract_drug_context_from_candidates(self):
        from src.core.l1b_drug_correct import extract_drug_candidates
        from src.core.l1c_ner import extract_entities
        txt = "kê Amoxicillin 500mg 2 viên 3 lần ngày 5 ngày"
        drugs = extract_drug_candidates(txt)
        ents = extract_entities(txt, drugs)
        assert len(ents.don_thuoc) > 0
        assert ents.don_thuoc[0]["inn"] == "Amoxicillin"


# ─── L1d ICD Lookup ──────────────────────────────────────────────────────────

class TestL1dICDLookup:
    def test_lookup_by_code_returns_dict(self):
        from src.core.l1d_icd_lookup import lookup_by_code
        result = lookup_by_code("J02.9")
        assert result is not None
        assert isinstance(result, dict)

    def test_lookup_unknown_code_returns_none(self):
        from src.core.l1d_icd_lookup import lookup_by_code
        assert lookup_by_code("ZZZ.999") is None

    def test_auto_lookup_returns_tuple(self):
        from src.core.l1d_icd_lookup import auto_lookup
        code, display = auto_lookup("viêm họng cấp")
        assert isinstance(code, str)
        assert isinstance(display, str)

    def test_auto_lookup_empty_returns_empty(self):
        from src.core.l1d_icd_lookup import auto_lookup
        code, display = auto_lookup("")
        assert code == ""
        assert display == ""

    def test_search_by_text_returns_list(self):
        from src.core.l1d_icd_lookup import search_by_text
        results = search_by_text("viêm phổi", max_results=3)
        assert isinstance(results, list)
        assert len(results) <= 3

    def test_validate_code_known(self):
        from src.core.l1d_icd_lookup import validate_code
        assert validate_code("J02.9") is True

    def test_validate_code_unknown(self):
        from src.core.l1d_icd_lookup import validate_code
        assert validate_code("ZZZ") is False


# ─── L2 Validate ─────────────────────────────────────────────────────────────

class TestL2Validate:
    def test_validate_returns_tuple(self):
        from src.core.l1c_ner import extract_entities
        from src.core.l2_validate import validate
        ents = extract_entities("sốt 38.5 chẩn đoán cảm cúm")
        result = validate(ents)
        assert len(result) == 3
        form_data, scores, conf = result
        assert isinstance(form_data, dict)
        assert isinstance(scores, dict)
        assert isinstance(conf, float)

    def test_confidence_between_0_and_1(self):
        from src.core.l1c_ner import extract_entities
        from src.core.l2_validate import validate
        ents = extract_entities("")
        _, _, conf = validate(ents)
        assert 0.0 <= conf <= 1.0

    def test_form_data_has_required_keys(self):
        from src.core.l1c_ner import extract_entities
        from src.core.l2_validate import validate
        ents = extract_entities("sốt 38.5")
        form_data, _, _ = validate(ents)
        assert "ly_do" in form_data
        assert "sinh_hieu" in form_data
        assert "chan_doan" in form_data
        assert "don_thuoc" in form_data

    def test_full_transcript_high_confidence(self):
        from src.core.l1b_drug_correct import extract_drug_candidates
        from src.core.l1c_ner import extract_entities
        from src.core.l2_validate import validate
        txt = "sốt 38.5 huyết áp 120/80 chẩn đoán viêm họng cấp kê Amoxicillin tái khám sau 5 ngày"
        drugs = extract_drug_candidates(txt)
        ents = extract_entities(txt, drugs)
        _, _, conf = validate(ents)
        assert conf >= 0.5


# ─── L3 Route ────────────────────────────────────────────────────────────────

class TestL3Route:
    def test_default_route_is_lam_sang(self):
        from src.core.l3_route import detect_route
        route = detect_route({"chan_doan": "cảm cúm", "ly_do": "đau đầu"})
        assert route == "lam_sang"

    def test_cdha_keywords_trigger_cdha_route(self):
        from src.core.l3_route import detect_route
        route = detect_route({"chan_doan": "chỉ định siêu âm bụng"})
        assert route == "cdha"

    def test_xquang_triggers_cdha(self):
        from src.core.l3_route import detect_route
        route = detect_route({"chi_dinh": ["chụp x-quang ngực"]})
        assert route == "cdha"

    def test_nha_khoa_keywords(self):
        from src.core.l3_route import detect_route
        route = detect_route({"chan_doan": "sâu răng"})
        assert route == "nha_khoa"

    def test_empty_form_data_returns_lam_sang(self):
        from src.core.l3_route import detect_route
        assert detect_route({}) == "lam_sang"


# ─── L4 Human Gate ───────────────────────────────────────────────────────────

class TestL4HumanGateUnit:
    def test_require_human_approval_changes_status(self):
        from src.core.l4_human_gate import require_human_approval
        from src.models.clinical_record import ClinicalRecord, RecordStatus
        r = ClinicalRecord(facility_id="F", doctor_cchn="D")
        r2 = require_human_approval(r)
        assert r2.status == RecordStatus.PENDING_REVIEW

    def test_approve_with_valid_cchn(self):
        from src.core.l4_human_gate import require_human_approval, approve
        from src.models.clinical_record import ClinicalRecord, RecordStatus
        r = ClinicalRecord(facility_id="F", doctor_cchn="D")
        r = require_human_approval(r)
        r = approve(r, "CCHN-001")
        assert r.status == RecordStatus.APPROVED
        assert r.approved_by == "CCHN-001"

    def test_approve_empty_cchn_raises(self):
        from src.core.l4_human_gate import require_human_approval, approve, HumanGateError
        from src.models.clinical_record import ClinicalRecord
        r = ClinicalRecord(facility_id="F", doctor_cchn="D")
        r = require_human_approval(r)
        with pytest.raises(HumanGateError):
            approve(r, "")

    def test_reject_changes_status(self):
        from src.core.l4_human_gate import require_human_approval, reject
        from src.models.clinical_record import ClinicalRecord, RecordStatus
        r = ClinicalRecord(facility_id="F", doctor_cchn="D")
        r = require_human_approval(r)
        r = reject(r, "CCHN-001", "Output sai")
        assert r.status == RecordStatus.REJECTED
        assert r.rejection_reason == "Output sai"

    def test_assert_approved_raises_for_pending(self):
        from src.core.l4_human_gate import require_human_approval, assert_approved, HumanGateError
        from src.models.clinical_record import ClinicalRecord
        r = ClinicalRecord(facility_id="F", doctor_cchn="D")
        r = require_human_approval(r)
        with pytest.raises(HumanGateError):
            assert_approved(r)

    def test_assert_approved_passes_for_approved(self):
        from src.core.l4_human_gate import require_human_approval, approve, assert_approved
        from src.models.clinical_record import ClinicalRecord
        r = ClinicalRecord(facility_id="F", doctor_cchn="D")
        r = require_human_approval(r)
        r = approve(r, "CCHN-001")
        assert_approved(r)  # Should not raise


# ─── L5 PII Scan ─────────────────────────────────────────────────────────────

class TestL5PiiScan:
    def test_detect_phone_number(self):
        from src.core.l5_pii_scan import scan_text
        result = scan_text("SĐT của bệnh nhân là 0901234567")
        assert "SDT" in result

    def test_detect_cccd(self):
        from src.core.l5_pii_scan import scan_text
        result = scan_text("CCCD số 012345678901")
        assert "CCCD" in result

    def test_detect_email(self):
        from src.core.l5_pii_scan import scan_text
        result = scan_text("email: patient@example.com")
        assert "EMAIL" in result

    def test_no_pii_returns_empty(self):
        from src.core.l5_pii_scan import scan_text
        result = scan_text("bệnh nhân đau đầu sốt")
        assert result == []

    def test_mask_pii_replaces_phone(self):
        from src.core.l5_pii_scan import mask_pii
        result = mask_pii("SĐT 0901234567")
        assert "0901234567" not in result
        assert "MASKED" in result

    def test_scan_form_data_dict(self):
        from src.core.l5_pii_scan import scan_form_data
        form = {"ly_do": "đau đầu", "ghi_chu": "SĐT 0901234567"}
        result = scan_form_data(form)
        assert "SDT" in result


# ─── L8 Error Handler ────────────────────────────────────────────────────────

class TestL8ErrorHandler:
    def test_pipeline_error_has_code(self):
        from src.core.l8_error_handler import PipelineError, PipelineErrorCode
        e = PipelineError(PipelineErrorCode.ASR_FAILED, "test", layer="L1a")
        assert e.code == PipelineErrorCode.ASR_FAILED
        assert e.layer == "L1a"

    def test_with_recovery_returns_fallback_on_exception(self):
        from src.core.l8_error_handler import with_recovery

        @with_recovery("L1a", fallback="")
        def failing_fn():
            raise ValueError("test error")

        result = failing_fn()
        assert result == ""

    def test_with_recovery_returns_value_on_success(self):
        from src.core.l8_error_handler import with_recovery

        @with_recovery("L1a", fallback="")
        def good_fn():
            return "transcript"

        assert good_fn() == "transcript"

    def test_safe_log_does_not_crash_on_exception(self):
        from src.core.l8_error_handler import safe_log

        @safe_log
        def logging_fn():
            raise RuntimeError("audit fail")

        # Should not raise
        logging_fn()


# ─── L10 Audit Log ───────────────────────────────────────────────────────────

class TestL10AuditLogUnit:
    def _get_test_conn(self):
        from src.core.l7_storage import init_db
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        db_path = Path(tmp.name)
        init_db(db_path)
        return sqlite3.connect(str(db_path)), db_path

    def test_log_event_inserts_entry(self):
        from src.core.l10_audit_log import log_event, get_record_history
        conn, db = self._get_test_conn()
        entry_id = log_event(conn, "REC-001", "CCHN-1", "CREATED", "test")
        conn.commit()
        history = get_record_history(conn, "REC-001")
        assert len(history) == 1
        assert history[0]["action"] == "CREATED"
        conn.close()
        db.unlink(missing_ok=True)

    def test_verify_chain_on_clean_log(self):
        from src.core.l10_audit_log import log_event, verify_chain
        conn, db = self._get_test_conn()
        log_event(conn, "R1", "D1", "CREATED")
        log_event(conn, "R1", "D1", "APPROVED")
        conn.commit()
        ok, err = verify_chain(conn)
        assert ok is True
        assert err == ""
        conn.close()
        db.unlink(missing_ok=True)

    def test_chain_has_sha256_hashes(self):
        from src.core.l10_audit_log import log_event
        conn, db = self._get_test_conn()
        log_event(conn, "R1", "D1", "CREATED")
        conn.commit()
        row = conn.execute("SELECT entry_hash FROM audit_log").fetchone()
        assert row is not None
        assert len(row[0]) == 64  # SHA-256 hex
        conn.close()
        db.unlink(missing_ok=True)
