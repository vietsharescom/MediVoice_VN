# tests/unit/test_dvp.py
# DVP — Doctor Voice Profile tests (FID-VN-012)
# AC-001 → AC-010

from __future__ import annotations
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.models.doctor_profile import (
    DoctorProfile, DoctorAlias,
    VALID_SPECIALTIES, VALID_REGIONS,
)
from src.core.l7_storage import (
    init_db, save_doctor_profile, load_doctor_profile,
    save_alias_occurrence, get_pending_aliases, confirm_alias, get_active_aliases,
)
from src.core.l1a_asr import SPECIALTY_DRUG_CLASSES, get_drugs_by_specialty
from src.core.dvp_alias import check_and_promote, apply_active_aliases


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_db(tmp_path):
    db = tmp_path / "test_dvp.db"
    init_db(db)
    return db


@pytest.fixture
def sample_profile():
    return DoctorProfile(
        cchn="CCHN-DVP-TEST",
        name="BS Nguyễn Văn A",
        region="northern",
        primary_specialty="noi_khoa",
        secondary_specialty="tim_mach",
        english_level="Basic",
        speaking_speed="Vừa",
        created_at="2026-06-09T10:00:00",
    )


# ── AC-001: DoctorProfile table created with correct schema ───────────────────

def test_ac001_doctor_profiles_table_created(tmp_db):
    """AC-001: doctor_profiles table tạo đúng schema (cchn PK, region, primary_specialty)."""
    import sqlite3
    conn = sqlite3.connect(str(tmp_db))
    info = conn.execute(
        "PRAGMA table_info(doctor_profiles)"
    ).fetchall()
    conn.close()
    col_names = {row[1] for row in info}
    assert "cchn" in col_names
    assert "region" in col_names
    assert "primary_specialty" in col_names
    assert "english_level" in col_names
    assert "speaking_speed" in col_names


def test_ac001_doctor_aliases_table_created(tmp_db):
    """AC-001: doctor_aliases table tạo đúng schema."""
    import sqlite3
    conn = sqlite3.connect(str(tmp_db))
    info = conn.execute(
        "PRAGMA table_info(doctor_aliases)"
    ).fetchall()
    conn.close()
    col_names = {row[1] for row in info}
    assert "cchn" in col_names
    assert "alias_text" in col_names
    assert "inn" in col_names
    assert "confirmed_by_bs" in col_names
    assert "session_count" in col_names


# ── AC-002: load_doctor_profile returns DoctorProfile or None ─────────────────

def test_ac002_load_returns_none_when_not_exists(tmp_db):
    """AC-002: load_doctor_profile trả None khi chưa có."""
    result = load_doctor_profile("CCHN-NOT-EXIST", tmp_db)
    assert result is None


def test_ac002_load_returns_doctor_profile_after_save(tmp_db, sample_profile):
    """AC-002: load_doctor_profile trả DoctorProfile đúng sau khi save."""
    save_doctor_profile(sample_profile, tmp_db)
    result = load_doctor_profile(sample_profile.cchn, tmp_db)
    assert result is not None
    assert isinstance(result, DoctorProfile)
    assert result.cchn == sample_profile.cchn
    assert result.region == "northern"
    assert result.primary_specialty == "noi_khoa"
    assert result.secondary_specialty == "tim_mach"


def test_ac002_upsert_updates_existing(tmp_db, sample_profile):
    """AC-002: save_doctor_profile upsert — cập nhật đúng khi save lại."""
    save_doctor_profile(sample_profile, tmp_db)
    updated = DoctorProfile(
        cchn=sample_profile.cchn,
        name="BS Nguyễn Văn B",
        region="southern",
        primary_specialty="tim_mach",
    )
    save_doctor_profile(updated, tmp_db)
    result = load_doctor_profile(sample_profile.cchn, tmp_db)
    assert result.region == "southern"
    assert result.primary_specialty == "tim_mach"


# ── AC-003: transcribe() passes specialty to A1 prompt injection ──────────────

def test_ac003_transcribe_receives_specialty(sample_profile):
    """AC-003: response includes dvp_specialty matching doctor profile."""
    import io, wave, struct
    from fastapi.testclient import TestClient
    from src.api.main import app

    n = 16000
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
        w.writeframes(struct.pack("<" + "h" * n, *([0] * n)))
    wav_bytes = buf.getvalue()

    with patch("src.api.main.load_doctor_profile", return_value=sample_profile):
        with patch("src.core.l1a_asr.transcribe", return_value="bs kê metformin 500mg"):
            client = TestClient(app)
            r = client.post(
                "/api/transcribe",
                files={"audio": ("t.wav", wav_bytes, "audio/wav")},
                data={"doctor_cchn": sample_profile.cchn, "facility_id": "FAC-T"},
            )
    assert r.status_code == 200
    data = r.json()
    assert data.get("dvp_specialty") == "noi_khoa"
    assert data.get("dvp_region") == "northern"


# ── AC-004: transcribe() passes region to A3 dialect norm ─────────────────────

def test_ac004_transcribe_passes_region_to_dialect_norm():
    """AC-004: khi profile có region='northern', dialect_normalize nhận region='northern'."""
    import io, wave, struct
    from fastapi.testclient import TestClient
    from src.api.main import app
    from src.models.doctor_profile import DoctorProfile

    profile = DoctorProfile(
        cchn="CCHN-AC004",
        name="BS Test",
        region="central",
        primary_specialty="noi_khoa",
    )
    n = 16000
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
        w.writeframes(struct.pack("<" + "h" * n, *([0] * n)))
    wav_bytes = buf.getvalue()

    captured_region = {}

    original_normalize = __import__(
        "src.core.dialect_norm", fromlist=["normalize_text"]
    ).normalize_text

    def spy_normalize(text, region="auto"):
        captured_region["region"] = region
        return original_normalize(text, region)

    with patch("src.api.main.load_doctor_profile", return_value=profile):
        with patch("src.core.l1a_asr.transcribe", return_value="bây chừ uống thuốc"):
            with patch("src.api.main._dialect_normalize", side_effect=spy_normalize):
                client = TestClient(app)
                client.post(
                    "/api/transcribe",
                    files={"audio": ("t.wav", wav_bytes, "audio/wav")},
                    data={"doctor_cchn": "CCHN-AC004", "facility_id": "FAC-T"},
                )

    assert captured_region.get("region") == "central"


# ── AC-005: profile=None → pipeline backward compat ──────────────────────────

def test_ac005_no_profile_defaults_noi_khoa_auto_region():
    """AC-005: khi không có profile, specialty='noi_khoa' + region='auto' — không crash."""
    import io, wave, struct
    from fastapi.testclient import TestClient
    from src.api.main import app

    n = 16000
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
        w.writeframes(struct.pack("<" + "h" * n, *([0] * n)))
    wav_bytes = buf.getvalue()

    with patch("src.api.main.load_doctor_profile", return_value=None):
        with patch("src.core.l1a_asr.transcribe", return_value=""):
            client = TestClient(app)
            r = client.post(
                "/api/transcribe",
                files={"audio": ("t.wav", wav_bytes, "audio/wav")},
                data={"doctor_cchn": "", "facility_id": "FAC-T"},
            )
    assert r.status_code == 200
    data = r.json()
    assert data.get("dvp_specialty") == "noi_khoa"
    assert data.get("dvp_region") == "auto"


# ── AC-006: 12 specialties have ≥20 drugs ─────────────────────────────────────

def test_ac006_all_12_specialties_exist_in_map():
    """AC-006: tất cả 12 FID-VN-012 specialties có trong SPECIALTY_DRUG_CLASSES."""
    for sp in VALID_SPECIALTIES:
        assert sp in SPECIALTY_DRUG_CLASSES, f"{sp} missing from SPECIALTY_DRUG_CLASSES"


def test_ac006_each_specialty_has_20_drugs():
    """AC-006: mỗi specialty có ít nhất 20 drugs (kể cả supplement pool)."""
    import json
    db_path = Path("data/reference/drug_db_v200.json")
    if not db_path.exists():
        pytest.skip("drug_db_v200.json not found")
    db = json.loads(db_path.read_text(encoding="utf-8"))
    for sp in VALID_SPECIALTIES:
        drugs = get_drugs_by_specialty(db, sp, n=50)
        assert len(drugs) >= 20, f"{sp} has only {len(drugs)} drugs (need ≥20)"


# ── AC-007: DoctorAlias promote rule (≥3 occurrences + ≥2 sessions → pending) ─

def test_ac007_alias_not_promoted_below_threshold(tmp_db, sample_profile):
    """AC-007: alias với <3 occurrences không xuất hiện trong pending."""
    save_doctor_profile(sample_profile, tmp_db)
    save_alias_occurrence(
        sample_profile.cchn, "mét phốt min", "Metformin", "SES-001", tmp_db
    )
    save_alias_occurrence(
        sample_profile.cchn, "mét phốt min", "Metformin", "SES-001", tmp_db
    )
    pending = get_pending_aliases(sample_profile.cchn, tmp_db)
    assert len(pending) == 0  # chưa đủ 3 occurrences


def test_ac007_alias_pending_after_threshold_met(tmp_db, sample_profile):
    """AC-007: alias ≥3 occurrences + ≥2 sessions → xuất hiện trong pending."""
    save_doctor_profile(sample_profile, tmp_db)
    # 3 occurrences từ 2 sessions khác nhau
    save_alias_occurrence(
        sample_profile.cchn, "mét phốt min", "Metformin", "SES-001", tmp_db
    )
    save_alias_occurrence(
        sample_profile.cchn, "mét phốt min", "Metformin", "SES-001", tmp_db
    )
    save_alias_occurrence(
        sample_profile.cchn, "mét phốt min", "Metformin", "SES-002", tmp_db
    )  # session khác → session_count tăng lên 2
    pending = get_pending_aliases(sample_profile.cchn, tmp_db)
    assert len(pending) == 1
    assert pending[0].alias_text == "mét phốt min"
    assert pending[0].inn == "Metformin"
    assert pending[0].occurrence_count >= 3
    assert pending[0].session_count >= 2


def test_ac007_single_session_not_promoted(tmp_db, sample_profile):
    """AC-007: 5 occurrences nhưng chỉ 1 session → không promote (cần ≥2 sessions)."""
    save_doctor_profile(sample_profile, tmp_db)
    for _ in range(5):
        save_alias_occurrence(
            sample_profile.cchn, "xi pro", "Ciprofloxacin", "SES-ONLY", tmp_db
        )
    pending = get_pending_aliases(sample_profile.cchn, tmp_db)
    assert len(pending) == 0  # session_count = 1 < 2


# ── AC-008: Human Gate alias — BS confirm YES/NO ──────────────────────────────

def test_ac008_alias_inactive_before_confirmation(tmp_db, sample_profile):
    """AC-008: alias chưa confirm → không active (confirmed_by_bs=0)."""
    save_doctor_profile(sample_profile, tmp_db)
    save_alias_occurrence(
        sample_profile.cchn, "mét phốt min", "Metformin", "SES-001", tmp_db
    )
    active = get_active_aliases(sample_profile.cchn, tmp_db)
    assert len(active) == 0  # chưa confirm → chưa active


def test_ac008_alias_active_after_bs_confirm(tmp_db, sample_profile):
    """AC-008: sau khi BS confirm → alias active."""
    save_doctor_profile(sample_profile, tmp_db)
    for i, sess in enumerate(["SES-001", "SES-001", "SES-002"]):
        save_alias_occurrence(
            sample_profile.cchn, "mét phốt min", "Metformin", sess, tmp_db
        )
    pending = get_pending_aliases(sample_profile.cchn, tmp_db)
    assert len(pending) == 1
    alias_id = pending[0].id
    # BS confirm YES
    confirm_alias(alias_id, True, tmp_db)
    active = get_active_aliases(sample_profile.cchn, tmp_db)
    assert len(active) == 1
    assert active[0].alias_text == "mét phốt min"


def test_ac008_alias_rejected_not_active(tmp_db, sample_profile):
    """AC-008: BS reject → alias không active, không pending."""
    save_doctor_profile(sample_profile, tmp_db)
    for sess in ["SES-001", "SES-001", "SES-002"]:
        save_alias_occurrence(
            sample_profile.cchn, "xi klo", "Ciprofloxacin", sess, tmp_db
        )
    pending = get_pending_aliases(sample_profile.cchn, tmp_db)
    confirm_alias(pending[0].id, False, tmp_db)
    active = get_active_aliases(sample_profile.cchn, tmp_db)
    assert len(active) == 0
    # Không còn trong pending sau khi reject (confirmed_by_bs=-1)
    still_pending = get_pending_aliases(sample_profile.cchn, tmp_db)
    assert len(still_pending) == 0


# ── AC-009: Registration form validation ──────────────────────────────────────

def test_ac009_register_valid_doctor(tmp_db):
    """AC-009: POST /api/doctors với region + primary_specialty hợp lệ → 200."""
    from fastapi.testclient import TestClient
    from src.api.main import app

    with patch("src.api.main.save_doctor_profile") as mock_save:
        client = TestClient(app)
        r = client.post(
            "/api/doctors",
            data={
                "cchn": "CCHN-999",
                "name": "BS Test",
                "region": "northern",
                "primary_specialty": "noi_khoa",
            },
        )
    assert r.status_code == 200
    data = r.json()
    assert data["cchn"] == "CCHN-999"
    assert data["status"] == "registered"
    mock_save.assert_called_once()


def test_ac009_invalid_region_returns_400():
    """AC-009: region không hợp lệ → 400."""
    from fastapi.testclient import TestClient
    from src.api.main import app

    client = TestClient(app)
    r = client.post(
        "/api/doctors",
        data={
            "cchn": "CCHN-999",
            "name": "BS Test",
            "region": "INVALID_REGION",
            "primary_specialty": "noi_khoa",
        },
    )
    assert r.status_code == 400


def test_ac009_invalid_specialty_returns_400():
    """AC-009: primary_specialty không hợp lệ → 400."""
    from fastapi.testclient import TestClient
    from src.api.main import app

    client = TestClient(app)
    r = client.post(
        "/api/doctors",
        data={
            "cchn": "CCHN-999",
            "name": "BS Test",
            "region": "southern",
            "primary_specialty": "INVALID_SPEC",
        },
    )
    assert r.status_code == 400


def test_ac009_get_doctor_returns_profile():
    """AC-009: GET /api/doctors/{cchn} trả profile đúng."""
    from fastapi.testclient import TestClient
    from src.api.main import app
    from src.models.doctor_profile import DoctorProfile

    profile = DoctorProfile(
        cchn="CCHN-GET-001",
        name="BS Lê Văn B",
        region="southern",
        primary_specialty="tim_mach",
    )
    with patch("src.api.main.load_doctor_profile", return_value=profile):
        client = TestClient(app)
        r = client.get("/api/doctors/CCHN-GET-001")
    assert r.status_code == 200
    data = r.json()
    assert data["region"] == "southern"
    assert data["primary_specialty"] == "tim_mach"


def test_ac009_get_doctor_404_when_not_found():
    """AC-009: GET /api/doctors/{cchn} → 404 khi chưa đăng ký."""
    from fastapi.testclient import TestClient
    from src.api.main import app

    with patch("src.api.main.load_doctor_profile", return_value=None):
        client = TestClient(app)
        r = client.get("/api/doctors/CCHN-NOTFOUND")
    assert r.status_code == 404


# ── apply_active_aliases unit test ────────────────────────────────────────────

def test_apply_active_aliases_substitutes_confirmed(tmp_db, sample_profile):
    """apply_active_aliases thay thế alias đã confirm trong transcript."""
    save_doctor_profile(sample_profile, tmp_db)
    for sess in ["S1", "S1", "S2"]:
        save_alias_occurrence(
            sample_profile.cchn, "mét phốt min", "Metformin", sess, tmp_db
        )
    pending = get_pending_aliases(sample_profile.cchn, tmp_db)
    confirm_alias(pending[0].id, True, tmp_db)

    result, subs = apply_active_aliases(
        "uống mét phốt min mỗi ngày", sample_profile.cchn, tmp_db
    )
    assert "Metformin" in result
    assert len(subs) == 1


def test_apply_active_aliases_no_change_when_empty(tmp_db, sample_profile):
    """apply_active_aliases không thay đổi khi không có alias active."""
    save_doctor_profile(sample_profile, tmp_db)
    result, subs = apply_active_aliases(
        "uống mét phốt min mỗi ngày", sample_profile.cchn, tmp_db
    )
    assert result == "uống mét phốt min mỗi ngày"
    assert subs == []
