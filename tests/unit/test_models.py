"""
Unit tests for Pydantic data models.
@verifies SRS-L7-001, SRS-L4-004
"""
import pytest
from datetime import date
from src.models.patient import Patient
from src.models.clinical_record import ClinicalRecord, RecordStatus
from src.models.facility import Facility
from src.models.audit_entry import AuditEntry


class TestPatient:
    def test_patient_creates_with_required_fields(self):
        p = Patient(ho_va_ten="Nguyễn Văn A")
        assert p.ho_va_ten == "Nguyễn Văn A"
        assert p.patient_id is not None

    def test_patient_uuid_generated(self):
        p1 = Patient(ho_va_ten="A")
        p2 = Patient(ho_va_ten="B")
        assert p1.patient_id != p2.patient_id

    def test_patient_optional_fields_default_none(self):
        p = Patient(ho_va_ten="Test")
        assert p.sinh_ngay is None
        assert p.cccd_so is None
        assert p.bhyt_so_the is None

    def test_patient_with_full_data(self):
        p = Patient(
            ho_va_ten="Trần Thị B",
            gioi_tinh="Nữ",
            dan_toc="Kinh",
            dia_chi_tinh="Đà Nẵng",
        )
        assert p.gioi_tinh == "Nữ"
        assert p.dia_chi_tinh == "Đà Nẵng"


class TestClinicalRecord:
    def test_record_default_status_is_draft(self):
        r = ClinicalRecord(facility_id="FAC-001", doctor_cchn="CCHN-001")
        assert r.status == RecordStatus.DRAFT

    def test_record_uuid_generated(self):
        r1 = ClinicalRecord(facility_id="F", doctor_cchn="D")
        r2 = ClinicalRecord(facility_id="F", doctor_cchn="D")
        assert r1.record_id != r2.record_id

    def test_record_status_enum_values(self):
        assert RecordStatus.DRAFT.value == "draft"
        assert RecordStatus.PENDING_REVIEW.value == "pending_review"
        assert RecordStatus.APPROVED.value == "approved"
        assert RecordStatus.REJECTED.value == "rejected"

    def test_record_model_copy_update(self):
        r = ClinicalRecord(facility_id="F", doctor_cchn="D")
        r2 = r.model_copy(update={"status": RecordStatus.APPROVED})
        assert r2.status == RecordStatus.APPROVED
        assert r.status == RecordStatus.DRAFT  # original unchanged

    def test_record_confidence_defaults(self):
        r = ClinicalRecord(facility_id="F", doctor_cchn="D")
        assert r.overall_confidence == 0.0
        assert r.form_data == {}
        assert r.pii_detected == []


class TestFacility:
    def test_facility_creation(self):
        f = Facility(
            ten_co_so="Phòng khám Dr. Nam",
            byt_registration_number="GPHN-001",
            province_code="48",
        )
        assert f.ten_co_so == "Phòng khám Dr. Nam"
        assert f.province_code == "48"


class TestAuditEntry:
    def test_audit_entry_is_frozen(self):
        e = AuditEntry(record_id="R1", actor_cchn="CCHN-1", action="CREATED")
        with pytest.raises(Exception):
            e.action = "MODIFIED"  # Should raise (frozen=True)

    def test_audit_entry_uuid(self):
        e1 = AuditEntry(record_id="R", actor_cchn="C", action="A")
        e2 = AuditEntry(record_id="R", actor_cchn="C", action="A")
        assert e1.entry_id != e2.entry_id
