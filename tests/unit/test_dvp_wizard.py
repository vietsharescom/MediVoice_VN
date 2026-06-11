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
