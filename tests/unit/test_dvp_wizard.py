# tests/unit/test_dvp_wizard.py
# Drug Pronunciation Enrollment Wizard tests (FID-VN-013 §2.4)
# AC-010, AC-011, AC-012

from __future__ import annotations
import io
import wave
import struct
from unittest.mock import patch

import pytest

from src.models.doctor_profile import DoctorProfile
from src.core.l7_storage import (
    init_db, save_doctor_profile, load_doctor_profile,
    add_confirmed_alias, get_active_aliases,
)


@pytest.fixture
def tmp_db(tmp_path):
    db = tmp_path / "test_dvp_wizard.db"
    init_db(db)
    return db


@pytest.fixture
def sample_profile():
    return DoctorProfile(
        cchn="CCHN-WIZ-TEST",
        name="BS Trần Văn C",
        region="northern",
        primary_specialty="noi_khoa",
        secondary_specialty="tim_mach",
        english_level="Basic",
        speaking_speed="Vừa",
        created_at="2026-06-10T10:00:00",
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


# ── pronunciation-wordlist ─────────────────────────────────────────────────

def test_wordlist_returns_drugs_for_specialty(sample_profile):
    """GET pronunciation-wordlist trả danh sách thuốc theo specialty của BS."""
    from fastapi.testclient import TestClient
    from src.api.main import app

    with patch("src.api.main.load_doctor_profile", return_value=sample_profile):
        client = TestClient(app)
        r = client.get(f"/api/doctors/{sample_profile.cchn}/pronunciation-wordlist?n=5")

    assert r.status_code == 200
    data = r.json()
    assert data["cchn"] == sample_profile.cchn
    assert data["specialty"] == "noi_khoa"
    assert len(data["drugs"]) <= 5
    assert len(data["drugs"]) > 0


def test_wordlist_404_when_doctor_not_registered():
    from fastapi.testclient import TestClient
    from src.api.main import app

    with patch("src.api.main.load_doctor_profile", return_value=None):
        client = TestClient(app)
        r = client.get("/api/doctors/CCHN-NOTFOUND/pronunciation-wordlist")

    assert r.status_code == 404


# ── AC-010: pronunciation-enroll alias proposal logic ──────────────────────

def test_ac010_no_alias_needed_when_transcript_matches_expected(sample_profile):
    """AC-010: transcript khớp expected_inn (case-insensitive) → alias_needed=False."""
    from fastapi.testclient import TestClient
    from src.api.main import app

    with patch("src.api.main.load_doctor_profile", return_value=sample_profile):
        with patch("src.core.l1a_asr.transcribe", return_value="Metformin"):
            client = TestClient(app)
            r = client.post(
                f"/api/doctors/{sample_profile.cchn}/pronunciation-enroll",
                files={"audio": ("t.wav", _wav_bytes(), "audio/wav")},
                data={"expected_inn": "metformin"},
            )

    assert r.status_code == 200
    data = r.json()
    assert data["alias_needed"] is False


def test_ac010_alias_proposed_when_transcript_differs(sample_profile):
    """AC-010: transcript khác expected_inn → alias_needed=True + alias_text đề xuất."""
    from fastapi.testclient import TestClient
    from src.api.main import app

    with patch("src.api.main.load_doctor_profile", return_value=sample_profile):
        with patch("src.core.l1a_asr.transcribe", return_value="am lo di phin"):
            client = TestClient(app)
            r = client.post(
                f"/api/doctors/{sample_profile.cchn}/pronunciation-enroll",
                files={"audio": ("t.wav", _wav_bytes(), "audio/wav")},
                data={"expected_inn": "Amlodipine"},
            )

    assert r.status_code == 200
    data = r.json()
    assert data["alias_needed"] is True
    assert data["alias_text"] == "am lo di phin"
    assert data["expected_inn"] == "Amlodipine"
    assert "Amlodipine" in data["message"]


def test_enroll_404_when_doctor_not_registered():
    from fastapi.testclient import TestClient
    from src.api.main import app

    with patch("src.api.main.load_doctor_profile", return_value=None):
        client = TestClient(app)
        r = client.post(
            "/api/doctors/CCHN-NOTFOUND/pronunciation-enroll",
            files={"audio": ("t.wav", _wav_bytes(), "audio/wav")},
            data={"expected_inn": "Metformin"},
        )

    assert r.status_code == 404


# ── AC-012: audio purge after enroll transcribe ─────────────────────────────

def test_ac012_purge_audio_called_after_enroll(sample_profile):
    """AC-012: pronunciation-enroll gọi purge_audio() cho cả tmp upload và normalized wav."""
    from fastapi.testclient import TestClient
    from src.api.main import app

    with patch("src.api.main.load_doctor_profile", return_value=sample_profile):
        with patch("src.core.l1a_asr.transcribe", return_value="Metformin"):
            with patch("src.api.main.l0_normalize.purge_audio") as mock_purge:
                client = TestClient(app)
                r = client.post(
                    f"/api/doctors/{sample_profile.cchn}/pronunciation-enroll",
                    files={"audio": ("t.wav", _wav_bytes(), "audio/wav")},
                    data={"expected_inn": "Metformin"},
                )

    assert r.status_code == 200
    assert mock_purge.call_count >= 2


# ── FID-VN-015 §3.2 — pronunciation-enroll extended fields ──────────────────

def test_enroll_response_includes_phonetic_f0_contour_and_match_ratio(sample_profile):
    """pronunciation-enroll trả thêm phonetic_text, f0_contour, match_ratio."""
    from fastapi.testclient import TestClient
    from src.api.main import app

    with patch("src.api.main.load_doctor_profile", return_value=sample_profile):
        with patch("src.core.l1a_asr.transcribe", return_value="Metformin"):
            client = TestClient(app)
            r = client.post(
                f"/api/doctors/{sample_profile.cchn}/pronunciation-enroll",
                files={"audio": ("t.wav", _wav_bytes(), "audio/wav")},
                data={"expected_inn": "Metformin"},
            )

    assert r.status_code == 200
    data = r.json()
    assert "phonetic_text" in data and data["phonetic_text"]
    assert "f0_contour" in data and isinstance(data["f0_contour"], list)
    assert "match_ratio" in data and isinstance(data["match_ratio"], (int, float))


# ── FID-VN-015 §3.2 — GET /api/pronunciation-reference/{inn} ────────────────

def test_pronunciation_reference_fallback_when_no_cache():
    """Chưa pre-gen audio mẫu -> audio_url=None, phonetic_text tính trực tiếp."""
    from fastapi.testclient import TestClient
    from src.api.main import app

    client = TestClient(app)
    r = client.get("/api/pronunciation-reference/Paracetamol")

    assert r.status_code == 200
    data = r.json()
    assert data["inn"] == "Paracetamol"
    assert data["audio_url"] is None
    assert data["phonetic_text"]
    assert data["f0_contour"] == []


def test_pronunciation_reference_unknown_drug_still_returns_phonetic():
    from fastapi.testclient import TestClient
    from src.api.main import app

    client = TestClient(app)
    r = client.get("/api/pronunciation-reference/Ibuprofen")

    assert r.status_code == 200
    data = r.json()
    assert data["phonetic_text"]


# ── AC-011: pronunciation-confirm immediate confirmed_by_bs=1 ──────────────

def test_ac011_confirm_yes_inserts_active_alias(tmp_db, sample_profile):
    """AC-011: confirm='yes' → doctor_aliases có row confirmed_by_bs=1, session=1, occurrence=1."""
    from fastapi.testclient import TestClient
    from src.api.main import app

    save_doctor_profile(sample_profile, tmp_db)

    with patch("src.core.l7_storage._DB_PATH", tmp_db):
        client = TestClient(app)
        r = client.post(
            f"/api/doctors/{sample_profile.cchn}/pronunciation-confirm",
            data={
                "alias_text": "am lo di phin",
                "inn": "Amlodipine",
                "confirmed": "yes",
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "confirmed"

        active = get_active_aliases(sample_profile.cchn, tmp_db)

    assert len(active) == 1
    assert active[0].alias_text == "am lo di phin"
    assert active[0].inn == "Amlodipine"
    assert active[0].confirmed_by_bs == 1
    assert active[0].session_count == 1
    assert active[0].occurrence_count == 1


def test_ac011_confirm_no_does_not_insert(tmp_db, sample_profile):
    """AC-011: confirm='no' → không insert alias, status='skipped'."""
    from fastapi.testclient import TestClient
    from src.api.main import app

    save_doctor_profile(sample_profile, tmp_db)

    with patch("src.core.l7_storage._DB_PATH", tmp_db):
        client = TestClient(app)
        r = client.post(
            f"/api/doctors/{sample_profile.cchn}/pronunciation-confirm",
            data={
                "alias_text": "am lo di phin",
                "inn": "Amlodipine",
                "confirmed": "no",
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "skipped"

        active = get_active_aliases(sample_profile.cchn, tmp_db)

    assert len(active) == 0


def test_add_confirmed_alias_direct(tmp_db, sample_profile):
    """add_confirmed_alias() insert trực tiếp với confirmed_by_bs=1/session=1/occurrence=1."""
    save_doctor_profile(sample_profile, tmp_db)
    add_confirmed_alias(sample_profile.cchn, "para", "Paracetamol", tmp_db)

    active = get_active_aliases(sample_profile.cchn, tmp_db)
    assert len(active) == 1
    assert active[0].alias_text == "para"
    assert active[0].inn == "Paracetamol"
    assert active[0].confirmed_by_bs == 1
    assert active[0].session_count == 1
    assert active[0].occurrence_count == 1


# ── FID-VN-016 — get_latest_confirmed_alias ─────────────────────────────────

def test_get_latest_confirmed_alias_returns_none_when_no_confirm(tmp_db, sample_profile):
    from src.core.l7_storage import get_latest_confirmed_alias

    save_doctor_profile(sample_profile, tmp_db)
    assert get_latest_confirmed_alias(sample_profile.cchn, "Paracetamol", tmp_db) is None


def test_get_latest_confirmed_alias_returns_most_recent(tmp_db, sample_profile):
    from src.core.l7_storage import get_latest_confirmed_alias

    save_doctor_profile(sample_profile, tmp_db)
    add_confirmed_alias(sample_profile.cchn, "pa ra xê ta môn", "Paracetamol", tmp_db)
    add_confirmed_alias(sample_profile.cchn, "pa ra xi ta môn", "Paracetamol", tmp_db)

    assert get_latest_confirmed_alias(sample_profile.cchn, "Paracetamol", tmp_db) == "pa ra xi ta môn"


# ── FID-VN-016 §1 — pronunciation-reference: pronunciation_en / vn_phonetic ─

def test_pronunciation_reference_includes_pronunciation_en_when_available():
    """Paracetamol có pronunciation_en trong drug_db_v200.json (pilot data)."""
    from fastapi.testclient import TestClient
    from src.api.main import app

    client = TestClient(app)
    r = client.get("/api/pronunciation-reference/Paracetamol")

    assert r.status_code == 200
    data = r.json()
    assert data["pronunciation_en"]
    assert data["vn_phonetic_default"]
    assert data["vn_phonetic_user"] is None


def test_pronunciation_reference_unknown_drug_pronunciation_en_is_none():
    from fastapi.testclient import TestClient
    from src.api.main import app

    client = TestClient(app)
    r = client.get("/api/pronunciation-reference/Ibuprofen")

    assert r.status_code == 200
    assert r.json()["pronunciation_en"] is None


def test_pronunciation_reference_returns_vn_phonetic_user_after_confirm(tmp_db, sample_profile):
    """Sau khi BS confirm alias, vn_phonetic_user trả bản mới nhất khi truyền ?cchn=."""
    from fastapi.testclient import TestClient
    from src.api.main import app

    save_doctor_profile(sample_profile, tmp_db)
    add_confirmed_alias(sample_profile.cchn, "pa ra xi ta môn", "Paracetamol", tmp_db)

    with patch("src.core.l7_storage._DB_PATH", tmp_db):
        client = TestClient(app)
        r = client.get(
            f"/api/pronunciation-reference/Paracetamol?cchn={sample_profile.cchn}"
        )

    assert r.status_code == 200
    assert r.json()["vn_phonetic_user"] == "pa ra xi ta môn"


# ── FID-VN-017 §2 — pronunciation-reference: stress hint trên vn_phonetic_default ─

def test_pronunciation_reference_default_has_stress_hint_when_pronunciation_en_available():
    """Paracetamol có pronunciation_en -> vn_phonetic_default có 1 âm tiết viết HOA."""
    from fastapi.testclient import TestClient
    from src.api.main import app

    client = TestClient(app)
    r = client.get("/api/pronunciation-reference/Paracetamol")

    assert r.status_code == 200
    data = r.json()
    syllables = data["vn_phonetic_default"].split()
    assert any(s.isupper() for s in syllables)


def test_pronunciation_reference_default_unchanged_without_pronunciation_en():
    """Ibuprofen không có pronunciation_en -> vn_phonetic_default không bị viết HOA."""
    from fastapi.testclient import TestClient
    from src.api.main import app

    client = TestClient(app)
    r = client.get("/api/pronunciation-reference/Ibuprofen")

    assert r.status_code == 200
    data = r.json()
    syllables = data["vn_phonetic_default"].split()
    assert not any(s.isupper() for s in syllables)


def test_pronunciation_reference_user_not_affected_by_stress_hint(tmp_db, sample_profile):
    """vn_phonetic_user (BS confirm) giữ nguyên, không bị viết HOA stress hint."""
    from fastapi.testclient import TestClient
    from src.api.main import app

    save_doctor_profile(sample_profile, tmp_db)
    add_confirmed_alias(sample_profile.cchn, "pa ra xi ta môn", "Paracetamol", tmp_db)

    with patch("src.core.l7_storage._DB_PATH", tmp_db):
        client = TestClient(app)
        r = client.get(
            f"/api/pronunciation-reference/Paracetamol?cchn={sample_profile.cchn}"
        )

    assert r.status_code == 200
    assert r.json()["vn_phonetic_user"] == "pa ra xi ta môn"


# ── FID-VN-016 §1 — pronunciation-enroll: retry_needed cho transcript lộn xộn

def test_enroll_returns_retry_needed_for_garbled_transcript(sample_profile):
    from fastapi.testclient import TestClient
    from src.api.main import app

    garbled = " ".join(["paracetamol"] * 16)

    with patch("src.api.main.load_doctor_profile", return_value=sample_profile):
        with patch("src.core.l1a_asr.transcribe", return_value=garbled):
            client = TestClient(app)
            r = client.post(
                f"/api/doctors/{sample_profile.cchn}/pronunciation-enroll",
                files={"audio": ("t.wav", _wav_bytes(), "audio/wav")},
                data={"expected_inn": "Paracetamol"},
            )

    assert r.status_code == 200
    data = r.json()
    assert data["retry_needed"] is True
    assert data["alias_needed"] is False


# ── FID-VN-018 §1 (CT-043) — dvp-form: chuyên khoa TRƯỚC vùng miền ──────────

def test_dvp_form_specialty_fields_before_region():
    """DOM order: dvp-primary-specialty phải xuất hiện TRƯỚC dvp-region."""
    from pathlib import Path

    html = Path("src/api/static/index.html").read_text(encoding="utf-8")
    idx_specialty = html.index('id="dvp-primary-specialty"')
    idx_region = html.index('id="dvp-region"')

    assert idx_specialty < idx_region
