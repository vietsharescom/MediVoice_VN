"""
test_vn_router.py — Unit tests for VN-ROUTER-001
FID-VN-004 | AC-001..AC-007
Tests: detect_vn_route() + l6_mau15_generator.generate_mau15()
"""
import pytest
from src.pipeline.p1_processing.l3_routing import detect_vn_route, VN_LAM_SANG, VN_CDHA, VN_NHA_KHOA


# ── detect_vn_route (AC: vn_route detection) ─────────────────────────────────

class TestDetectVnRoute:
    def test_default_is_lam_sang(self):
        """AC: Default route = lam_sang (general clinical)."""
        assert detect_vn_route("Bệnh nhân đau đầu sốt 38.5") == VN_LAM_SANG

    def test_empty_is_lam_sang(self):
        assert detect_vn_route("") == VN_LAM_SANG

    def test_sieu_am_is_cdha(self):
        assert detect_vn_route("Chỉ định siêu âm bụng tổng quát") == VN_CDHA

    def test_xquang_is_cdha(self):
        assert detect_vn_route("Chụp x-quang ngực thẳng") == VN_CDHA

    def test_ct_scan_is_cdha(self):
        assert detect_vn_route("CT scan đầu không tiêm thuốc cản quang") == VN_CDHA

    def test_mri_is_cdha(self):
        assert detect_vn_route("MRI cột sống thắt lưng") == VN_CDHA

    def test_ecg_is_cdha(self):
        assert detect_vn_route("Làm điện tim ECG 12 chuyển đạo") == VN_CDHA

    def test_rang_is_nha_khoa(self):
        assert detect_vn_route("Bệnh nhân đau răng số 6 hàm dưới") == VN_NHA_KHOA

    def test_nha_khoa_is_nha_khoa(self):
        assert detect_vn_route("Khám nha khoa định kỳ") == VN_NHA_KHOA

    def test_nuou_is_nha_khoa(self):
        assert detect_vn_route("Nướu sưng đỏ chảy máu") == VN_NHA_KHOA

    def test_nha_khoa_before_cdha(self):
        """nha_khoa checked first — more specific."""
        # Text has both "răng" and "chụp" → should be nha_khoa
        assert detect_vn_route("Chụp X-quang răng toàn hàm") == VN_NHA_KHOA

    def test_case_insensitive(self):
        assert detect_vn_route("SIÊU ÂM BỤNG") == VN_CDHA

    def test_hypertension_is_lam_sang(self):
        assert detect_vn_route("Tăng huyết áp, kê Amlodipine") == VN_LAM_SANG

    def test_diabetes_is_lam_sang(self):
        assert detect_vn_route("Tiểu đường type 2, HbA1c 8.2%") == VN_LAM_SANG


# ── l3_routing handle() includes vn_route ────────────────────────────────────

class TestL3RoutingOutput:
    def test_handle_includes_vn_route(self):
        from src.pipeline.p1_processing.l3_routing import handle
        payload = {
            "source": "mobile_mic",
            "doctor_id": "DOC-001",
            "original_text": "Bệnh nhân đau đầu sốt",
        }
        result = handle(payload)
        assert result["ok"] is True
        assert "vn_route" in result["data"]
        assert result["data"]["vn_route"] == VN_LAM_SANG

    def test_handle_cdha_vn_route(self):
        from src.pipeline.p1_processing.l3_routing import handle
        payload = {
            "source": "mobile_mic",
            "doctor_id": "DOC-001",
            "original_text": "Chỉ định siêu âm bụng",
        }
        result = handle(payload)
        assert result["ok"] is True
        assert result["data"]["vn_route"] == VN_CDHA


# ── l6_mau15_generator ───────────────────────────────────────────────────────

class TestGenerateMau15:
    """AC-001..006 from FID-VN-004."""

    def _make_entities(self, vitals=None, symptoms=None, meds=None):
        """Helper: create mock NER entity list."""
        from src.pipeline.p2_decision.l6_soap_generator import NEREntity
        entities = []
        for v in (vitals or []):
            entities.append(NEREntity(type="VITAL", value=v))
        for s in (symptoms or []):
            entities.append(NEREntity(type="SYMPTOM", value=s))
        for m in (meds or []):
            entities.append(NEREntity(type="MEDICATION", value=m["name"],
                                      dose=m.get("dose", ""), frequency=m.get("freq", "")))
        return entities

    def test_ac001_lam_sang_returns_benh_an_not_soap(self):
        """AC-001: lam_sang → output has benh_an, not soap_note."""
        from src.pipeline.p2_decision.l6_agent import handle
        payload = {
            "source": "mobile_mic",
            "doctor_id": "DOC-001",
            "approval_status": "PENDING_APPROVAL",
            "flow": "FLOW_A",
            "vn_route": "lam_sang",
            "original_text": "đau đầu sốt",
            "processed_text": "headache fever",
            "hint_language": "en",
        }
        result = handle(payload)
        assert result["ok"] is True
        assert "benh_an" in result["data"], "lam_sang should have benh_an"
        assert "soap_note" not in result["data"], "lam_sang should NOT have soap_note"

    def test_ac002_cdha_returns_soap(self):
        """AC-002: cdha → output has soap_note (Canada flow preserved)."""
        from src.pipeline.p2_decision.l6_agent import handle
        payload = {
            "source": "mobile_mic",
            "doctor_id": "DOC-001",
            "approval_status": "PENDING_APPROVAL",
            "flow": "FLOW_A",
            "vn_route": "cdha",
            "original_text": "siêu âm bụng",
            "processed_text": "abdominal ultrasound",
            "hint_language": "en",
        }
        result = handle(payload)
        assert result["ok"] is True
        assert "soap_note" in result["data"], "cdha should have soap_note"

    def test_ac003_medication_in_benh_an(self):
        """AC-003: lam_sang + medication → don_thuoc has entry."""
        from src.pipeline.p2_decision.l6_mau15_generator import generate_mau15
        entities = self._make_entities(
            meds=[{"name": "Amoxicillin", "dose": "500mg", "freq": "3x daily 5 days"}]
        )
        payload = {"doctor_id": "DOC-001", "facility_id": "FAC-001"}
        result = generate_mau15(entities, payload)
        assert "don_thuoc" in result
        assert len(result["don_thuoc"]) >= 1
        assert result["don_thuoc"][0]["ten_thuoc"] == "Amoxicillin"

    def test_ac004_bp_in_sinh_hieu(self):
        """AC-004: '120/80' vital → sinh_hieu.huyet_ap_tam_thu = 120."""
        from src.pipeline.p2_decision.l6_mau15_generator import generate_mau15
        entities = self._make_entities(vitals=["120/80"])
        payload = {"doctor_id": "DOC-001", "facility_id": "FAC-001"}
        result = generate_mau15(entities, payload)
        assert result["sinh_hieu"]["huyet_ap_tam_thu"] == 120
        assert result["sinh_hieu"]["huyet_ap_tam_truong"] == 80

    def test_ac005_benh_an_has_disclaimer(self):
        """AC-005: All output must have disclaimer (ABSOLUTE RULE #8)."""
        from src.pipeline.p2_decision.l6_mau15_generator import generate_mau15
        entities = self._make_entities()
        payload = {"doctor_id": "DOC-001", "facility_id": "FAC-001"}
        result = generate_mau15(entities, payload)
        assert "disclaimer" in result
        assert "BS" in result["disclaimer"] or "Bác sĩ" in result["disclaimer"]

    def test_ac006_vn_route_label_in_output(self):
        """AC-006: output labels vn_route='lam_sang' and mau_form='15/BV-01'."""
        from src.pipeline.p2_decision.l6_mau15_generator import generate_mau15
        entities = self._make_entities()
        payload = {"doctor_id": "DOC-001", "facility_id": "FAC-001"}
        result = generate_mau15(entities, payload)
        assert result.get("vn_route") == "lam_sang"
        assert "15" in result.get("mau_form", "")
