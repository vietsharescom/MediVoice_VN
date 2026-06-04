"""
Unit tests for L6 Form Generator, L7 Storage, Orchestrator.
@verifies SRS-L6-*, SRS-L7-*, SRS-L4-001
"""
import pytest
import tempfile
import sqlite3
from pathlib import Path


# ─── L6 Form Generator ───────────────────────────────────────────────────────

class TestL6FormGenerator:
    def test_generate_benh_an_returns_object(self):
        from src.core.l6_generate_form import generate_benh_an
        form_data = {
            "ly_do": "đau đầu",
            "chan_doan": "cảm cúm",
            "icd_code": "J11",
            "tai_kham": "Sau 3 ngày",
            "don_thuoc": [],
            "sinh_hieu": {
                "nhiet_do": 38.5,
                "huyet_ap_tam_thu": 120,
                "huyet_ap_tam_truong": 80,
                "mach": 80, "nhip_tho": None,
                "can_nang": None, "spo2": None,
            },
        }
        ba = generate_benh_an(form_data, "CCHN-001", "FAC-001")
        assert ba is not None
        assert ba.doctor_cchn == "CCHN-001"

    def test_form_fills_diagnosis(self):
        from src.core.l6_generate_form import generate_benh_an
        form_data = {"chan_doan": "viêm họng cấp", "icd_code": "J02",
                     "don_thuoc": [], "sinh_hieu": {}}
        ba = generate_benh_an(form_data, "CCHN-001", "FAC-001")
        assert ba.kham_benh.chan_doan_ban_dau == "viêm họng cấp"

    def test_form_fills_icd(self):
        from src.core.l6_generate_form import generate_benh_an
        form_data = {"icd_code": "J02.9", "don_thuoc": [], "sinh_hieu": {}}
        ba = generate_benh_an(form_data, "CCHN-001", "FAC-001")
        assert ba.kham_benh.ma_icd10 == "J02.9"

    def test_form_fills_drug_list(self):
        from src.core.l6_generate_form import generate_benh_an
        form_data = {
            "don_thuoc": [{"inn": "Amoxicillin", "ham_luong": "500mg",
                           "so_lan_ngay": "3 lần/ngày", "so_ngay": 5,
                           "duong_dung": "uống"}],
            "sinh_hieu": {},
        }
        ba = generate_benh_an(form_data, "CCHN-001", "FAC-001")
        assert len(ba.don_thuoc.danh_sach_thuoc) == 1
        assert ba.don_thuoc.danh_sach_thuoc[0].ten_thuoc == "Amoxicillin"

    def test_form_fills_sinh_hieu(self):
        from src.core.l6_generate_form import generate_benh_an
        form_data = {
            "don_thuoc": [],
            "sinh_hieu": {"nhiet_do": 37.5, "huyet_ap_tam_thu": 130,
                          "huyet_ap_tam_truong": 85, "mach": 75,
                          "nhip_tho": None, "can_nang": None, "spo2": None},
        }
        ba = generate_benh_an(form_data, "CCHN-001", "FAC-001")
        assert ba.kham_benh.sinh_hieu.nhiet_do == 37.5
        assert ba.kham_benh.sinh_hieu.huyet_ap_tam_thu == 130


# ─── L7 Storage ──────────────────────────────────────────────────────────────

class TestL7Storage:
    def _setup_db(self):
        from src.core.l7_storage import init_db
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        key = tempfile.NamedTemporaryFile(suffix=".key", delete=False)
        key.close()
        db_path = Path(tmp.name)
        key_path = Path(key.name)
        key_path.unlink()  # let l7 create fresh key
        import src.core.l7_storage as l7
        l7._DB_PATH = db_path
        l7._KEY_PATH = key_path
        l7._fernet = None
        init_db(db_path)
        return db_path, key_path

    def test_store_record_requires_approved(self):
        from src.core.l7_storage import store_record
        from src.core.l4_human_gate import HumanGateError
        from src.models.clinical_record import ClinicalRecord
        db, key = self._setup_db()
        r = ClinicalRecord(facility_id="F", doctor_cchn="D")  # DRAFT status
        with pytest.raises(HumanGateError):
            store_record(r, db_path=db)
        db.unlink(missing_ok=True)

    def test_store_and_load_approved_record(self):
        from src.core.l7_storage import store_record, load_record
        from src.core.l4_human_gate import require_human_approval, approve
        from src.models.clinical_record import ClinicalRecord
        db, key = self._setup_db()
        r = ClinicalRecord(facility_id="FAC-TEST", doctor_cchn="CCHN-1",
                           form_data={"chan_doan": "test"})
        r = require_human_approval(r)
        r = approve(r, "CCHN-1")
        rid = store_record(r, db_path=db)
        loaded = load_record(rid, db_path=db)
        assert loaded is not None
        assert loaded["doctor_cchn"] == "CCHN-1"
        assert loaded["form_data"]["chan_doan"] == "test"
        db.unlink(missing_ok=True)

    def test_load_nonexistent_record_returns_none(self):
        from src.core.l7_storage import load_record
        db, key = self._setup_db()
        result = load_record("nonexistent-id", db_path=db)
        assert result is None
        db.unlink(missing_ok=True)

    def test_init_db_creates_tables(self):
        from src.core.l7_storage import init_db
        db, key = self._setup_db()
        conn = sqlite3.connect(str(db))
        tables = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        assert "clinical_records" in tables
        assert "audit_log" in tables
        conn.close()
        db.unlink(missing_ok=True)


# ─── Orchestrator ────────────────────────────────────────────────────────────

class TestOrchestrator:
    def test_stage_result_ok_true(self):
        from src.core.orchestrator import StageResult
        sr = StageResult(stage="L0", ok=True, duration_ms=10.0)
        assert sr.ok is True
        assert sr.error == ""

    def test_stage_result_ok_false(self):
        from src.core.orchestrator import StageResult
        sr = StageResult(stage="L1a", ok=False, error="Model not found")
        assert sr.ok is False

    def test_pipeline_result_defaults(self):
        from src.core.orchestrator import PipelineResult
        pr = PipelineResult()
        assert pr.overall_ok is False
        assert pr.record is None
        assert pr.stages == []

    def test_orchestrator_initializes(self):
        from src.core.orchestrator import Orchestrator
        orch = Orchestrator()
        assert orch.validation_layer is None

    def test_orchestrator_with_validation_layer(self):
        from src.core.orchestrator import Orchestrator
        from src.validation.validation_layer import ValidationLayer
        vl = ValidationLayer()
        orch = Orchestrator(validation_layer=vl)
        assert orch.validation_layer is vl

    def test_run_stage_captures_exception(self):
        from src.core.orchestrator import Orchestrator, StageResult
        orch = Orchestrator()
        result = orch._run_stage("L_TEST", lambda: 1/0)
        assert result is None
        assert any(not s.ok for s in orch._stages)

    def test_run_stage_returns_value_on_success(self):
        from src.core.orchestrator import Orchestrator
        orch = Orchestrator()
        result = orch._run_stage("L_TEST", lambda: "transcript")
        assert result == "transcript"
        assert orch._stages[-1].ok is True

    def test_pipeline_result_stage_summary(self):
        from src.core.orchestrator import PipelineResult, StageResult
        pr = PipelineResult(
            stages=[StageResult("L0", True, 10.0), StageResult("L1a", False, 5.0)]
        )
        summary = pr.stage_summary()
        assert len(summary) == 2
        assert summary[0]["stage"] == "L0"
        assert summary[1]["ok"] is False
