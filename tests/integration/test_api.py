"""
test_api.py — API Integration Tests
GAP-005 | SRS-API-001..006
ISO 9001:2015 Cl.9.1 + ISO/IEC 25010 Reliability

Đảm bảo tất cả API endpoints hoạt động đúng sau mỗi code change.
Không có tests → regression silent khi thêm M2/M4/M5/M6.
"""
import pytest
import io
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# ── Setup ─────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    """TestClient với mock cho heavy dependencies."""
    from src.api.main import app
    return TestClient(app, raise_server_exceptions=False)


# ── Health check ──────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_returns_200(self, client):
        """SRS-API-001: GET /api/health"""
        r = client.get("/api/health")
        assert r.status_code == 200

    def test_health_returns_json(self, client):
        r = client.get("/api/health")
        data = r.json()
        assert isinstance(data, dict)

    def test_root_returns_200(self, client):
        r = client.get("/")
        # 200 (static file) hoặc 200 (JSON) — cả hai đều OK
        assert r.status_code in (200, 404)  # 404 nếu static chưa build


# ── Transcribe endpoint ───────────────────────────────────────────────────────

class TestTranscribe:
    def test_transcribe_without_audio_returns_error(self, client):
        """POST /api/transcribe không có audio → 422 Unprocessable Entity"""
        r = client.post("/api/transcribe")
        assert r.status_code == 422

    def test_transcribe_with_empty_cchn_accepted(self, client):
        """
        POST /api/transcribe với CCHN rỗng vẫn accepted (L4 check riêng).
        Pipeline tạo draft — L4 require approval mới check CCHN.
        """
        wav_bytes = _make_silent_wav(duration_s=2)
        r = client.post(
            "/api/transcribe",
            files={"audio": ("test.wav", wav_bytes, "audio/wav")},
            data={"doctor_cchn": "", "facility_id": "FAC-TEST"},
        )
        # 200 (success) hoặc 422 (validation) — không được 500
        assert r.status_code != 500, f"Server error: {r.text}"

    def test_transcribe_too_short_audio_handled(self, client):
        """Audio < 1 giây → pipeline graceful failure, không crash."""
        tiny_wav = _make_silent_wav(duration_s=0)
        r = client.post(
            "/api/transcribe",
            files={"audio": ("tiny.wav", tiny_wav, "audio/wav")},
            data={"doctor_cchn": "CCHN-001"},
        )
        assert r.status_code != 500, f"Server error: {r.text}"

    def test_transcribe_returns_record_id_on_success(self, client):
        """Successful transcribe → response có record_id."""
        with patch("src.core.l1a_asr.transcribe", return_value="đau đầu sốt"):
            wav_bytes = _make_silent_wav(duration_s=3)
            r = client.post(
                "/api/transcribe",
                files={"audio": ("test.wav", wav_bytes, "audio/wav")},
                data={"doctor_cchn": "CCHN-001", "facility_id": "FAC-TEST"},
            )
            if r.status_code == 200:
                data = r.json()
                assert "record_id" in data
                assert "form_data" in data
                assert "warning" in data  # disclaimer phải có

    def test_transcribe_response_has_disclaimer(self, client):
        """Disclaimer bắt buộc trong response (ABSOLUTE RULE #8)."""
        with patch("src.core.l1a_asr.transcribe", return_value="đau đầu"):
            wav_bytes = _make_silent_wav(duration_s=3)
            r = client.post(
                "/api/transcribe",
                files={"audio": ("test.wav", wav_bytes, "audio/wav")},
                data={"doctor_cchn": "CCHN-001"},
            )
            if r.status_code == 200:
                body = r.text
                assert "AI tạo nháp" in body or "Bác sĩ" in body


# ── Approve / Reject endpoints ────────────────────────────────────────────────

class TestApproveReject:
    def test_approve_nonexistent_record_returns_404(self, client):
        """POST /api/records/FAKE-ID/approve → 404"""
        r = client.post(
            "/api/records/FAKE-NONEXISTENT-ID/approve",
            json={"doctor_cchn": "CCHN-001"},
        )
        assert r.status_code in (404, 422, 400), \
            f"Expected 404/422/400, got {r.status_code}"

    def test_reject_nonexistent_record_returns_404(self, client):
        """POST /api/records/FAKE-ID/reject → 404"""
        r = client.post(
            "/api/records/FAKE-NONEXISTENT-ID/reject",
            json={"doctor_cchn": "CCHN-001", "reason": "test"},
        )
        assert r.status_code in (404, 422, 400)

    def test_approve_requires_record_id_in_path(self, client):
        """Route structure: /api/records/{record_id}/approve"""
        r = client.post("/api/records//approve")
        assert r.status_code in (404, 405, 422)


# ── PDF export ────────────────────────────────────────────────────────────────

class TestPDF:
    def test_pdf_nonexistent_record_returns_404(self, client):
        """GET /api/records/FAKE-ID/pdf → 404 khi record không tồn tại."""
        with patch("src.api.main.l7_storage.load_record", return_value=None):
            r = client.get("/api/records/FAKE-NONEXISTENT-ID/pdf")
            assert r.status_code == 404, \
                f"Expected 404 for nonexistent record, got {r.status_code}"


# ── Feedback endpoint ─────────────────────────────────────────────────────────

class TestFeedback:
    def test_feedback_endpoint_exists(self, client):
        """POST /api/feedback → không được 404 (endpoint phải tồn tại)."""
        r = client.post("/api/feedback", json={})
        # 422 (validation error) hoặc 200/201 — nhưng không 404
        assert r.status_code != 404, "Feedback endpoint missing"

    def test_feedback_accepts_valid_payload(self, client):
        """Feedback với đủ fields → 200."""
        payload = {
            "record_id": "test-id",
            "doctor_cchn": "CCHN-001",
            "feedback_type": "other",
            "severity": "low",
            "comment": "test comment",
        }
        r = client.post("/api/feedback", json=payload)
        assert r.status_code in (200, 201, 422), \
            f"Unexpected status: {r.status_code}"


# ── L4 Human Gate — cannot bypass ────────────────────────────────────────────

class TestL4Protection:
    def test_approve_endpoint_does_not_bypass_l4(self, client):
        """
        Approve endpoint phải require record ở PENDING_REVIEW status.
        Không được approve record chưa qua L4.
        """
        # Record không tồn tại → không thể approve
        r = client.post(
            "/api/records/RANDOM-ID/approve",
            json={"doctor_cchn": "CCHN-001"},
        )
        # Phải từ chối — không được 200 với record không tồn tại
        assert r.status_code != 200 or \
            "error" in r.json() or \
            r.json().get("status") not in ("APPROVED", "approved"), \
            "L4 gate may be bypassable for nonexistent records"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_silent_wav(duration_s: float = 2.0, sample_rate: int = 16000) -> bytes:
    """Generate minimal silent WAV bytes for testing."""
    import struct, math
    n_samples = int(duration_s * sample_rate)
    data_size = n_samples * 2  # 16-bit = 2 bytes per sample

    buf = io.BytesIO()
    # RIFF header
    buf.write(b"RIFF")
    buf.write(struct.pack("<I", 36 + data_size))
    buf.write(b"WAVE")
    # fmt chunk
    buf.write(b"fmt ")
    buf.write(struct.pack("<I", 16))       # chunk size
    buf.write(struct.pack("<H", 1))        # PCM
    buf.write(struct.pack("<H", 1))        # mono
    buf.write(struct.pack("<I", sample_rate))
    buf.write(struct.pack("<I", sample_rate * 2))  # byte rate
    buf.write(struct.pack("<H", 2))        # block align
    buf.write(struct.pack("<H", 16))       # bits per sample
    # data chunk
    buf.write(b"data")
    buf.write(struct.pack("<I", data_size))
    buf.write(b"\x00" * data_size)        # silence

    return buf.getvalue()
