# tests/unit/test_api_suggestions.py
# UI-SUGGEST-001 endpoint unit tests — FID-VN-010
# Tests /api/drug-candidates, /api/terms, /api/dialect-check

import pytest
from fastapi.testclient import TestClient

from src.api.main import app, _SPECIALTY_TERMS

client = TestClient(app)


# ===========================================================================
# GET /api/drug-candidates
# ===========================================================================

class TestDrugCandidatesEndpoint:
    def test_returns_200(self):
        resp = client.get("/api/drug-candidates?q=paracetamol")
        assert resp.status_code == 200

    def test_response_has_candidates_key(self):
        resp = client.get("/api/drug-candidates?q=para")
        assert "candidates" in resp.json()

    def test_response_has_source_key(self):
        resp = client.get("/api/drug-candidates?q=para")
        assert "source" in resp.json()

    def test_empty_query_returns_200_empty(self):
        resp = client.get("/api/drug-candidates?q=")
        assert resp.status_code == 200
        data = resp.json()
        assert data["candidates"] == []

    def test_whitespace_query_returns_empty(self):
        resp = client.get("/api/drug-candidates?q=   ")
        assert resp.status_code == 200
        data = resp.json()
        assert data["candidates"] == []

    def test_q_required(self):
        resp = client.get("/api/drug-candidates")
        assert resp.status_code == 422  # missing required param

    def test_n_param_limits_results(self):
        resp = client.get("/api/drug-candidates?q=amlodipine&n=1")
        data = resp.json()
        assert len(data["candidates"]) <= 1

    def test_n_param_default_3(self):
        resp = client.get("/api/drug-candidates?q=metformin")
        data = resp.json()
        assert len(data["candidates"]) <= 3

    def test_with_diagnosis_context(self):
        resp = client.get("/api/drug-candidates?q=metformin&diagnosis=tiểu+đường")
        assert resp.status_code == 200

    def test_n_out_of_range_rejected(self):
        resp = client.get("/api/drug-candidates?q=test&n=0")
        assert resp.status_code == 422  # ge=1

    def test_candidate_has_inn_field(self):
        resp = client.get("/api/drug-candidates?q=paracetamol")
        data = resp.json()
        if data["candidates"]:
            assert "inn" in data["candidates"][0]

    def test_candidate_has_score_field(self):
        resp = client.get("/api/drug-candidates?q=paracetamol")
        data = resp.json()
        if data["candidates"]:
            assert "score" in data["candidates"][0]

    def test_fuzzy_fallback_source(self):
        # When RAG not available, source should be fuzzy_fallback; when available: hybrid
        resp = client.get("/api/drug-candidates?q=amlodipin")
        data = resp.json()
        assert data["source"] in ("fuzzy_fallback", "rag", "hybrid", "empty_query")


# ===========================================================================
# GET /api/terms
# ===========================================================================

class TestTermsEndpoint:
    def test_returns_200(self):
        resp = client.get("/api/terms")
        assert resp.status_code == 200

    def test_default_specialty_noi_khoa(self):
        resp = client.get("/api/terms")
        data = resp.json()
        assert data["specialty"] == "noi_khoa"

    def test_response_has_terms_key(self):
        resp = client.get("/api/terms")
        data = resp.json()
        assert "terms" in data

    def test_response_has_count_key(self):
        resp = client.get("/api/terms")
        data = resp.json()
        assert "count" in data

    def test_noi_khoa_returns_terms(self):
        resp = client.get("/api/terms?specialty=noi_khoa")
        data = resp.json()
        assert len(data["terms"]) > 0

    def test_each_specialty_returns_terms(self):
        for specialty in _SPECIALTY_TERMS:
            resp = client.get(f"/api/terms?specialty={specialty}")
            data = resp.json()
            assert len(data["terms"]) > 0, f"{specialty} returned no terms"

    def test_unknown_specialty_returns_empty(self):
        resp = client.get("/api/terms?specialty=unknown_xyz")
        data = resp.json()
        assert data["terms"] == []
        assert data["count"] == 0

    def test_term_has_required_fields(self):
        resp = client.get("/api/terms?specialty=noi_khoa")
        data = resp.json()
        for term in data["terms"]:
            assert "term" in term
            assert "icd" in term
            assert "common" in term

    def test_n_param_limits(self):
        resp = client.get("/api/terms?specialty=noi_khoa&n=5")
        data = resp.json()
        assert len(data["terms"]) <= 5

    def test_available_specialties_listed(self):
        resp = client.get("/api/terms")
        data = resp.json()
        assert "available_specialties" in data
        assert "noi_khoa" in data["available_specialties"]

    def test_ho_hap_has_respiratory_terms(self):
        resp = client.get("/api/terms?specialty=ho_hap")
        data = resp.json()
        terms_text = " ".join(t["term"] for t in data["terms"]).lower()
        assert any(kw in terms_text for kw in ["phế quản", "phổi", "hen"])

    def test_ta_mui_hong_has_ent_terms(self):
        resp = client.get("/api/terms?specialty=tai_mui_hong")
        data = resp.json()
        terms_text = " ".join(t["term"] for t in data["terms"]).lower()
        assert any(kw in terms_text for kw in ["amidan", "họng", "viêm"])

    def test_icd_format_nonempty(self):
        resp = client.get("/api/terms?specialty=noi_khoa")
        data = resp.json()
        for t in data["terms"]:
            assert t["icd"], f"Empty ICD for term: {t['term']}"


# ===========================================================================
# POST /api/dialect-check
# ===========================================================================

class TestDialectCheckEndpoint:
    def test_returns_200(self):
        resp = client.post("/api/dialect-check", json={"text": "bệnh nhân mô rứa"})
        assert resp.status_code == 200

    def test_response_has_required_fields(self):
        resp = client.post("/api/dialect-check", json={"text": "test"})
        data = resp.json()
        for key in ("normalized", "substitutions", "region", "changed"):
            assert key in data

    def test_central_dialect_detected(self):
        resp = client.post("/api/dialect-check", json={"text": "bệnh nhân mô rứa hỉ", "region": "auto"})
        data = resp.json()
        assert data["region"] == "central"

    def test_central_substitutions_made(self):
        resp = client.post("/api/dialect-check", json={"text": "uống nác mỗi ngày", "region": "central"})
        data = resp.json()
        assert data["changed"] is True
        assert len(data["substitutions"]) > 0

    def test_southern_hong_replaced(self):
        resp = client.post("/api/dialect-check", json={"text": "hổng uống được nha", "region": "southern"})
        data = resp.json()
        assert "không" in data["normalized"]

    def test_empty_text_returns_empty(self):
        resp = client.post("/api/dialect-check", json={"text": ""})
        data = resp.json()
        assert data["normalized"] == ""
        assert data["substitutions"] == []

    def test_whitespace_text_returns_empty(self):
        resp = client.post("/api/dialect-check", json={"text": "   "})
        data = resp.json()
        assert data["normalized"] == ""

    def test_standard_text_no_changes(self):
        resp = client.post("/api/dialect-check", json={"text": "bệnh nhân đau đầu sốt cao", "region": "northern"})
        data = resp.json()
        assert data["changed"] is False

    def test_oi_central_is_benh(self):
        resp = client.post("/api/dialect-check", json={"text": "bệnh nhân bị ốm", "region": "central"})
        data = resp.json()
        assert "bệnh" in data["normalized"]

    def test_oi_southern_is_gay(self):
        resp = client.post("/api/dialect-check", json={"text": "bệnh nhân bị ốm", "region": "southern"})
        data = resp.json()
        assert "gầy" in data["normalized"]

    def test_text_field_required(self):
        resp = client.post("/api/dialect-check", json={})
        assert resp.status_code == 422

    def test_auto_region_resolved(self):
        resp = client.post("/api/dialect-check", json={"text": "mô rứa hỉ", "region": "auto"})
        data = resp.json()
        assert data["region"] in ("central", "southern", "northern")
        assert data["region"] != "auto"

    def test_abbrev_expanded(self):
        resp = client.post("/api/dialect-check", json={"text": "ha 155/95 bn 45t", "region": "northern"})
        data = resp.json()
        assert "huyết áp" in data["normalized"]
        assert "bệnh nhân" in data["normalized"]


# ===========================================================================
# Specialty terms data integrity
# ===========================================================================

class TestSpecialtyTermsData:
    def test_all_specialties_present(self):
        for sp in ["noi_khoa", "ho_hap", "tieu_hoa", "noi_tiet", "tai_mui_hong", "da_lieu", "co_xuong_khop", "nhi_khoa"]:
            assert sp in _SPECIALTY_TERMS

    def test_all_terms_have_icd(self):
        for sp, terms in _SPECIALTY_TERMS.items():
            for t in terms:
                assert t.get("icd"), f"Missing ICD: {sp}/{t.get('term')}"

    def test_all_terms_have_common(self):
        for sp, terms in _SPECIALTY_TERMS.items():
            for t in terms:
                assert t.get("common"), f"Missing common: {sp}/{t.get('term')}"

    def test_min_10_terms_per_specialty(self):
        for sp, terms in _SPECIALTY_TERMS.items():
            assert len(terms) >= 10, f"{sp} has only {len(terms)} terms"
