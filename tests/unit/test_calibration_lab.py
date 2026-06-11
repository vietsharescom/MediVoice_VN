# tests/unit/test_calibration_lab.py
# FID-VN-014 — Voice Calibration Lab (3-Part Standardized Test)
# AC-001 .. AC-006

from __future__ import annotations
import io
import wave
import struct
from unittest.mock import patch

import numpy as np
import pytest

from src.models.doctor_profile import DoctorProfile
from src.core import calibration_metrics
from src.core.l7_storage import (
    init_db, save_doctor_profile, load_doctor_profile,
    update_calibration_results,
)


@pytest.fixture
def tmp_db(tmp_path):
    db = tmp_path / "test_calibration_lab.db"
    init_db(db)
    return db


@pytest.fixture
def sample_profile():
    return DoctorProfile(
        cchn="CCHN-CALIB-TEST",
        name="BS Lê Thị D",
        region="northern",
        primary_specialty="noi_khoa",
        secondary_specialty=None,
        english_level="Basic",
        speaking_speed="Vừa",
        created_at="2026-06-11T10:00:00",
    )


def _wav_bytes():
    n = 16000
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(struct.pack("<" + "h" * n, *([0] * n)))
    return buf.getvalue()


# ── calibration_metrics — pure functions ────────────────────────────────────

def test_classify_speaking_rate_slow():
    assert calibration_metrics.classify_speaking_rate(word_count=10, duration_sec=10) == "Chậm"


def test_classify_speaking_rate_normal():
    assert calibration_metrics.classify_speaking_rate(word_count=30, duration_sec=10) == "Vừa"


def test_classify_speaking_rate_fast():
    assert calibration_metrics.classify_speaking_rate(word_count=50, duration_sec=10) == "Nhanh"


def test_classify_speaking_rate_zero_duration_defaults_vua():
    assert calibration_metrics.classify_speaking_rate(word_count=0, duration_sec=0) == "Vừa"


def test_classify_pause_style_thresholds():
    assert calibration_metrics.classify_pause_style([]) == "It_ngat"
    assert calibration_metrics.classify_pause_style([1.5]) == "It_ngat"
    assert calibration_metrics.classify_pause_style([1.5, 2.0]) == "Vua_phai"
    assert calibration_metrics.classify_pause_style([1.5, 2.0, 1.8, 2.2]) == "Vua_phai"
    assert calibration_metrics.classify_pause_style([1.5, 2.0, 1.8, 2.2, 1.9]) == "Nhieu_ngat"


def test_detect_pauses_from_audio_silence():
    """1s im lặng hoàn toàn (< pause_threshold mặc định 1.5s) → 0 pauses."""
    y = np.zeros(16000, dtype=np.float32)
    pauses = calibration_metrics.detect_pauses_from_audio(y, sr=16000)
    assert pauses == []


def test_detect_pauses_from_audio_long_silence():
    """2s im lặng (>= 1.5s threshold) → 1 pause."""
    y = np.zeros(32000, dtype=np.float32)
    pauses = calibration_metrics.detect_pauses_from_audio(y, sr=16000)
    assert len(pauses) == 1
    assert pauses[0] >= 1.5


def test_detect_pauses_from_audio_empty():
    assert calibration_metrics.detect_pauses_from_audio(np.array([])) == []
    assert calibration_metrics.detect_pauses_from_audio(None) == []


# ── compute_jitter_shimmer (FID-VN-015 §2.4) ────────────────────────────────

def test_compute_jitter_shimmer_empty_audio():
    assert calibration_metrics.compute_jitter_shimmer(np.array([]), sr=16000) == (0.0, 0.0)
    assert calibration_metrics.compute_jitter_shimmer(None, sr=16000) == (0.0, 0.0)


def test_compute_jitter_shimmer_silence_returns_zero():
    y = np.zeros(16000, dtype=np.float32)
    jitter_pct, shimmer_pct = calibration_metrics.compute_jitter_shimmer(y, sr=16000)
    assert jitter_pct == 0.0
    assert shimmer_pct == 0.0


def test_compute_jitter_shimmer_tone_returns_floats():
    sr = 16000
    t = np.linspace(0, 1.0, sr, endpoint=False)
    y = 0.5 * np.sin(2 * np.pi * 150 * t).astype(np.float32)
    jitter_pct, shimmer_pct = calibration_metrics.compute_jitter_shimmer(y, sr=sr)
    assert isinstance(jitter_pct, float)
    assert isinstance(shimmer_pct, float)
    assert jitter_pct >= 0.0
    assert shimmer_pct >= 0.0


# ── update_calibration_results — storage ────────────────────────────────────

def test_update_calibration_results_partial(tmp_db, sample_profile):
    save_doctor_profile(sample_profile, tmp_db)

    update_calibration_results(
        sample_profile.cchn,
        speaking_rate_class="Nhanh",
        pause_style="It_ngat",
        vtln_warp_factor=1.05,
        db_path=tmp_db,
    )

    updated = load_doctor_profile(sample_profile.cchn, tmp_db)
    assert updated.speaking_rate_class == "Nhanh"
    assert updated.pause_style == "It_ngat"
    assert updated.vtln_warp_factor == pytest.approx(1.05)
    # region không đổi (không truyền)
    assert updated.region == "northern"


def test_update_calibration_results_jitter_shimmer(tmp_db, sample_profile):
    """FID-VN-015 §2.4 — jitter_pct/shimmer_pct lưu vào doctor_profiles."""
    save_doctor_profile(sample_profile, tmp_db)

    update_calibration_results(
        sample_profile.cchn,
        jitter_pct=1.23,
        shimmer_pct=4.56,
        db_path=tmp_db,
    )

    updated = load_doctor_profile(sample_profile.cchn, tmp_db)
    assert updated.jitter_pct == pytest.approx(1.23)
    assert updated.shimmer_pct == pytest.approx(4.56)


def test_update_calibration_results_region_only(tmp_db, sample_profile):
    save_doctor_profile(sample_profile, tmp_db)

    update_calibration_results(sample_profile.cchn, region="central", db_path=tmp_db)

    updated = load_doctor_profile(sample_profile.cchn, tmp_db)
    assert updated.region == "central"
    # các trường khác vẫn None/default
    assert updated.speaking_rate_class is None
    assert updated.pause_style is None


# ── AC-005: backward compat — DoctorProfile load/save round trip ───────────

def test_doctor_profile_round_trip_default_calibration_fields(tmp_db, sample_profile):
    """Profile mới (chưa calibrate) → speaking_rate_class/pause_style = None, vtln=1.0."""
    save_doctor_profile(sample_profile, tmp_db)
    loaded = load_doctor_profile(sample_profile.cchn, tmp_db)

    assert loaded.speaking_rate_class is None
    assert loaded.pause_style is None
    assert loaded.vtln_warp_factor == pytest.approx(1.0)


# ── /api/calibration/passage-text ───────────────────────────────────────────

def test_passage_text_endpoint_returns_passage():
    from fastapi.testclient import TestClient
    from src.api.main import app

    client = TestClient(app)
    r = client.get("/api/calibration/passage-text")

    assert r.status_code == 200
    data = r.json()
    assert "passage" in data
    assert len(data["passage"]) > 50


# ── AC-001: /api/doctors/{cchn}/calibration/region ──────────────────────────

def test_ac001_region_detected_from_central_dialect(sample_profile):
    """AC-001: transcript chứa từ Trung ('mô răng rứa') → region='central'."""
    from fastapi.testclient import TestClient
    from src.api.main import app

    with patch("src.api.main.load_doctor_profile", return_value=sample_profile):
        with patch("src.core.l1a_asr.transcribe", return_value="mô răng rứa hè"):
            with patch("src.api.main.update_calibration_results") as mock_update:
                client = TestClient(app)
                r = client.post(
                    f"/api/doctors/{sample_profile.cchn}/calibration/region",
                    files={"audio": ("t.wav", _wav_bytes(), "audio/wav")},
                )

    assert r.status_code == 200
    data = r.json()
    assert data["region"] == "central"
    mock_update.assert_called_once()
    assert mock_update.call_args.kwargs.get("region") == "central"


def test_region_404_when_doctor_not_registered():
    from fastapi.testclient import TestClient
    from src.api.main import app

    with patch("src.api.main.load_doctor_profile", return_value=None):
        client = TestClient(app)
        r = client.post(
            "/api/doctors/CCHN-NOTFOUND/calibration/region",
            files={"audio": ("t.wav", _wav_bytes(), "audio/wav")},
        )

    assert r.status_code == 404


def test_ac006_purge_audio_called_after_region_test(sample_profile):
    """AC-006: audio purge ngay sau xử lý — region test."""
    from fastapi.testclient import TestClient
    from src.api.main import app

    with patch("src.api.main.load_doctor_profile", return_value=sample_profile):
        with patch("src.core.l1a_asr.transcribe", return_value="xin chào bác sĩ"):
            with patch("src.api.main.update_calibration_results"):
                with patch("src.api.main.l0_normalize.purge_audio") as mock_purge:
                    client = TestClient(app)
                    r = client.post(
                        f"/api/doctors/{sample_profile.cchn}/calibration/region",
                        files={"audio": ("t.wav", _wav_bytes(), "audio/wav")},
                    )

    assert r.status_code == 200
    assert mock_purge.call_count >= 2


# ── /api/doctors/{cchn}/calibration/region-manual ───────────────────────────
# BS tự sửa giọng vùng miền khi auto-detect (lexical) nhận sai (vd Huế -> bị
# detect "northern" do ASR phiên âm marker miền Trung không đúng)

def test_region_manual_override_saves_region(sample_profile):
    from fastapi.testclient import TestClient
    from src.api.main import app

    with patch("src.api.main.load_doctor_profile", return_value=sample_profile):
        with patch("src.api.main.update_calibration_results") as mock_update:
            client = TestClient(app)
            r = client.post(
                f"/api/doctors/{sample_profile.cchn}/calibration/region-manual",
                data={"region": "central"},
            )

    assert r.status_code == 200
    data = r.json()
    assert data["region"] == "central"
    mock_update.assert_called_once_with(sample_profile.cchn, region="central")


def test_region_manual_invalid_region_returns_400(sample_profile):
    from fastapi.testclient import TestClient
    from src.api.main import app

    with patch("src.api.main.load_doctor_profile", return_value=sample_profile):
        client = TestClient(app)
        r = client.post(
            f"/api/doctors/{sample_profile.cchn}/calibration/region-manual",
            data={"region": "invalid"},
        )

    assert r.status_code == 400


def test_region_manual_404_when_doctor_not_registered():
    from fastapi.testclient import TestClient
    from src.api.main import app

    with patch("src.api.main.load_doctor_profile", return_value=None):
        client = TestClient(app)
        r = client.post(
            "/api/doctors/CCHN-NOTFOUND/calibration/region-manual",
            data={"region": "central"},
        )

    assert r.status_code == 404


# ── AC-002/003/004: /api/doctors/{cchn}/calibration/passage ─────────────────

def test_ac002_003_004_passage_test_returns_metrics(sample_profile):
    """AC-002/003/004: passage test trả speaking_rate_class, pause_style, vtln_warp_factor."""
    from fastapi.testclient import TestClient
    from src.api.main import app

    transcript = " ".join(["từ"] * 20)  # 20 từ

    with patch("src.api.main.load_doctor_profile", return_value=sample_profile):
        with patch("src.core.l1a_asr.transcribe", return_value=transcript):
            with patch("src.api.main.vtln.estimate_warp_factor", return_value=1.05):
                with patch("src.api.main.update_calibration_results") as mock_update:
                    client = TestClient(app)
                    r = client.post(
                        f"/api/doctors/{sample_profile.cchn}/calibration/passage",
                        files={"audio": ("t.wav", _wav_bytes(), "audio/wav")},
                    )

    assert r.status_code == 200
    data = r.json()
    assert data["speaking_rate_class"] in ("Chậm", "Vừa", "Nhanh")
    assert data["pause_style"] in ("It_ngat", "Vua_phai", "Nhieu_ngat")
    assert data["vtln_warp_factor"] == pytest.approx(1.05)
    assert "jitter_pct" in data
    assert "shimmer_pct" in data

    mock_update.assert_called_once()
    kwargs = mock_update.call_args.kwargs
    assert kwargs["speaking_rate_class"] == data["speaking_rate_class"]
    assert kwargs["pause_style"] == data["pause_style"]
    assert kwargs["vtln_warp_factor"] == pytest.approx(1.05)
    assert kwargs["jitter_pct"] == data["jitter_pct"]
    assert kwargs["shimmer_pct"] == data["shimmer_pct"]


def test_ac004_vtln_warp_factor_measured_not_applied(sample_profile):
    """AC-004: vtln_warp_factor đo được nhưng KHÔNG gọi apply_vtln_warp (no-op)."""
    from fastapi.testclient import TestClient
    from src.api.main import app

    with patch("src.api.main.load_doctor_profile", return_value=sample_profile):
        with patch("src.core.l1a_asr.transcribe", return_value="một hai ba"):
            with patch("src.api.main.vtln.estimate_warp_factor", return_value=1.1) as mock_warp:
                with patch("src.api.main.vtln.apply_vtln_warp") as mock_apply:
                    with patch("src.api.main.update_calibration_results"):
                        client = TestClient(app)
                        r = client.post(
                            f"/api/doctors/{sample_profile.cchn}/calibration/passage",
                            files={"audio": ("t.wav", _wav_bytes(), "audio/wav")},
                        )

    assert r.status_code == 200
    mock_warp.assert_called_once()
    mock_apply.assert_not_called()


def test_passage_404_when_doctor_not_registered():
    from fastapi.testclient import TestClient
    from src.api.main import app

    with patch("src.api.main.load_doctor_profile", return_value=None):
        client = TestClient(app)
        r = client.post(
            "/api/doctors/CCHN-NOTFOUND/calibration/passage",
            files={"audio": ("t.wav", _wav_bytes(), "audio/wav")},
        )

    assert r.status_code == 404


# ── FID-VN-018 §2 — READING_PASSAGES_BY_REGION / REGION_TEST_SENTENCES ──────

def test_reading_passage_vi_alias_is_northern():
    """Backward-compat — READING_PASSAGE_VI === READING_PASSAGES_BY_REGION["northern"]."""
    assert calibration_metrics.READING_PASSAGE_VI == calibration_metrics.READING_PASSAGES_BY_REGION["northern"]


def test_get_passage_for_region_central_contains_central_marker():
    from src.core.dialect_norm import _CENTRAL_MARKERS

    passage = calibration_metrics.get_passage_for_region("central")
    assert any(m in passage.lower() for m in _CENTRAL_MARKERS)


def test_get_passage_for_region_southern_contains_southern_marker():
    from src.core.dialect_norm import _SOUTHERN_MARKERS

    passage = calibration_metrics.get_passage_for_region("southern")
    assert any(m in passage.lower() for m in _SOUTHERN_MARKERS)


def test_get_passage_for_region_fallback_northern():
    assert calibration_metrics.get_passage_for_region(None) == calibration_metrics.READING_PASSAGES_BY_REGION["northern"]
    assert calibration_metrics.get_passage_for_region("invalid") == calibration_metrics.READING_PASSAGES_BY_REGION["northern"]


def test_get_region_sentence_central_matches_existing_lab_sentence():
    """central giữ nguyên câu CT-038 đã hardcode trong index.html."""
    sentence = calibration_metrics.get_region_sentence("central")
    assert "mô răng rứa" in sentence


def test_get_region_sentence_fallback_northern():
    assert calibration_metrics.get_region_sentence(None) == calibration_metrics.REGION_TEST_SENTENCES["northern"]
    assert calibration_metrics.get_region_sentence("invalid") == calibration_metrics.REGION_TEST_SENTENCES["northern"]


# ── FID-VN-018 §3 — /api/calibration/passage-text & region-sentence (region-aware) ─

def test_passage_text_endpoint_no_cchn_falls_back_northern():
    from fastapi.testclient import TestClient
    from src.api.main import app

    client = TestClient(app)
    r = client.get("/api/calibration/passage-text")

    assert r.status_code == 200
    assert r.json()["passage"] == calibration_metrics.READING_PASSAGES_BY_REGION["northern"]


def test_passage_text_endpoint_uses_profile_region(sample_profile):
    import dataclasses
    from fastapi.testclient import TestClient
    from src.api.main import app

    central_profile = dataclasses.replace(sample_profile, region="central")
    with patch("src.api.main.load_doctor_profile", return_value=central_profile):
        client = TestClient(app)
        r = client.get(f"/api/calibration/passage-text?cchn={sample_profile.cchn}")

    assert r.status_code == 200
    assert r.json()["passage"] == calibration_metrics.READING_PASSAGES_BY_REGION["central"]


def test_region_sentence_endpoint_uses_profile_region(sample_profile):
    import dataclasses
    from fastapi.testclient import TestClient
    from src.api.main import app

    southern_profile = dataclasses.replace(sample_profile, region="southern")
    with patch("src.api.main.load_doctor_profile", return_value=southern_profile):
        client = TestClient(app)
        r = client.get(f"/api/calibration/region-sentence?cchn={sample_profile.cchn}")

    assert r.status_code == 200
    assert r.json()["sentence"] == calibration_metrics.REGION_TEST_SENTENCES["southern"]


def test_region_sentence_endpoint_no_cchn_falls_back_northern():
    from fastapi.testclient import TestClient
    from src.api.main import app

    client = TestClient(app)
    r = client.get("/api/calibration/region-sentence")

    assert r.status_code == 200
    assert r.json()["sentence"] == calibration_metrics.REGION_TEST_SENTENCES["northern"]


# ── FID-VN-018 §3 — calibration_region(): region_match field ───────────────

def test_calibration_region_match_true_when_detected_matches_declared(sample_profile):
    """sample_profile.region == 'northern', transcript trung tính -> region_match=True."""
    from fastapi.testclient import TestClient
    from src.api.main import app

    with patch("src.api.main.load_doctor_profile", return_value=sample_profile):
        with patch("src.core.l1a_asr.transcribe", return_value="xin chào bác sĩ"):
            with patch("src.api.main.update_calibration_results"):
                client = TestClient(app)
                r = client.post(
                    f"/api/doctors/{sample_profile.cchn}/calibration/region",
                    files={"audio": ("t.wav", _wav_bytes(), "audio/wav")},
                )

    assert r.status_code == 200
    data = r.json()
    assert data["region"] == "northern"
    assert data["region_match"] is True


def test_calibration_region_match_false_when_detected_differs_from_declared(sample_profile):
    """sample_profile.region == 'northern', transcript giọng Trung -> region_match=False."""
    from fastapi.testclient import TestClient
    from src.api.main import app

    with patch("src.api.main.load_doctor_profile", return_value=sample_profile):
        with patch("src.core.l1a_asr.transcribe", return_value="mô răng rứa hè"):
            with patch("src.api.main.update_calibration_results"):
                client = TestClient(app)
                r = client.post(
                    f"/api/doctors/{sample_profile.cchn}/calibration/region",
                    files={"audio": ("t.wav", _wav_bytes(), "audio/wav")},
                )

    assert r.status_code == 200
    data = r.json()
    assert data["region"] == "central"
    assert data["region_match"] is False


def test_ac006_purge_audio_called_after_passage_test(sample_profile):
    """AC-006: audio purge ngay sau xử lý — passage test."""
    from fastapi.testclient import TestClient
    from src.api.main import app

    with patch("src.api.main.load_doctor_profile", return_value=sample_profile):
        with patch("src.core.l1a_asr.transcribe", return_value="một hai ba bốn năm"):
            with patch("src.api.main.vtln.estimate_warp_factor", return_value=1.0):
                with patch("src.api.main.update_calibration_results"):
                    with patch("src.api.main.l0_normalize.purge_audio") as mock_purge:
                        client = TestClient(app)
                        r = client.post(
                            f"/api/doctors/{sample_profile.cchn}/calibration/passage",
                            files={"audio": ("t.wav", _wav_bytes(), "audio/wav")},
                        )

    assert r.status_code == 200
    assert mock_purge.call_count >= 2
