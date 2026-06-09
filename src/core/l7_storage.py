# L7 — SQLite + WAL + Fernet Storage
# Input: approved ClinicalRecord | Output: stored record_id
# RULE: Data PHẢI lưu tại VN — không AWS/GCP/Azure ngoài VN
# Allowed: localhost, vngcloud.vn, fptcloud.com, vnpt-technology.vn
# FROZEN PIPELINE LAYER

from __future__ import annotations
import json
import os
import sqlite3
from pathlib import Path
from datetime import datetime

from cryptography.fernet import Fernet

from ..models.clinical_record import ClinicalRecord, RecordStatus
from ..models.doctor_profile import DoctorProfile, DoctorAlias
from .l4_human_gate import assert_approved

_DB_PATH = Path(os.getenv("MEDIVOICE_DB", "medivoice.db"))
_KEY_PATH = Path(os.getenv("MEDIVOICE_KEY", "medivoice.key"))

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet:
        return _fernet
    if _KEY_PATH.exists():
        key = _KEY_PATH.read_bytes()
    else:
        key = Fernet.generate_key()
        _KEY_PATH.write_bytes(key)
    _fernet = Fernet(key)
    return _fernet


def _get_conn(db_path: Path | None = None) -> sqlite3.Connection:
    path = str(db_path or _DB_PATH)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: Path | None = None) -> None:
    """Tạo schema nếu chưa có."""
    conn = _get_conn(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS clinical_records (
            record_id    TEXT PRIMARY KEY,
            facility_id  TEXT NOT NULL,
            patient_id   TEXT,
            doctor_cchn  TEXT NOT NULL,
            status       TEXT NOT NULL,
            created_at   TEXT NOT NULL,
            approved_at  TEXT,
            approved_by  TEXT,
            route        TEXT DEFAULT 'lam_sang',
            form_data_enc BLOB NOT NULL,
            audit_hash   TEXT,
            byt_sync     TEXT DEFAULT 'pending',
            pdf_path     TEXT
        );

        CREATE TABLE IF NOT EXISTS patients (
            patient_id   TEXT PRIMARY KEY,
            facility_id  TEXT NOT NULL,
            data_enc     BLOB NOT NULL,
            created_at   TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            entry_id     TEXT PRIMARY KEY,
            timestamp    TEXT NOT NULL,
            record_id    TEXT NOT NULL,
            actor_cchn   TEXT NOT NULL,
            action       TEXT NOT NULL,
            detail       TEXT DEFAULT '',
            prev_hash    TEXT DEFAULT '',
            entry_hash   TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS doctor_profiles (
            cchn                TEXT PRIMARY KEY,
            name                TEXT NOT NULL,
            region              TEXT NOT NULL,
            primary_specialty   TEXT NOT NULL,
            secondary_specialty TEXT,
            english_level       TEXT DEFAULT 'Basic',
            speaking_speed      TEXT DEFAULT 'Vừa',
            created_at          TEXT NOT NULL,
            updated_at          TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS doctor_aliases (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            cchn             TEXT NOT NULL REFERENCES doctor_profiles(cchn),
            alias_text       TEXT NOT NULL,
            inn              TEXT NOT NULL,
            session_count    INTEGER DEFAULT 0,
            occurrence_count INTEGER DEFAULT 0,
            confirmed_by_bs  INTEGER DEFAULT 0,
            created_at       TEXT NOT NULL,
            last_seen        TEXT NOT NULL,
            UNIQUE(cchn, alias_text)
        );
    """)
    conn.commit()
    conn.close()


def store_record(
    record: ClinicalRecord,
    db_path: Path | None = None,
    conn: sqlite3.Connection | None = None,
) -> str:
    """
    Lưu ClinicalRecord vào SQLite (chỉ sau khi L4 approved).
    form_data được encrypt bằng Fernet.
    conn: nếu truyền vào, dùng connection đó (caller commit/close).
          Nếu None, tự tạo và commit.
    Returns: record_id
    """
    assert_approved(record)    # L4 guard — không bỏ qua

    fernet = _get_fernet()
    form_enc = fernet.encrypt(
        json.dumps(record.form_data, ensure_ascii=False).encode()
    )

    owns_conn = conn is None
    if owns_conn:
        conn = _get_conn(db_path)

    conn.execute("""
        INSERT OR REPLACE INTO clinical_records
        (record_id, facility_id, patient_id, doctor_cchn, status,
         created_at, approved_at, approved_by, route,
         form_data_enc, audit_hash, byt_sync, pdf_path)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        record.record_id,
        record.facility_id,
        record.patient_id,
        record.doctor_cchn,
        record.status.value,
        record.created_at.isoformat(),
        record.approved_at.isoformat() if record.approved_at else None,
        record.approved_by,
        record.route,
        form_enc,
        record.audit_hash,
        record.byt_sync_status,
        record.pdf_path,
    ))

    if owns_conn:
        conn.commit()
        conn.close()

    return record.record_id


def load_record(record_id: str, db_path: Path | None = None) -> dict | None:
    """Đọc và decrypt record từ DB."""
    conn = _get_conn(db_path)
    row = conn.execute(
        "SELECT * FROM clinical_records WHERE record_id=?", (record_id,)
    ).fetchone()
    conn.close()

    if not row:
        return None

    fernet = _get_fernet()
    cols = ["record_id","facility_id","patient_id","doctor_cchn","status",
            "created_at","approved_at","approved_by","route",
            "form_data_enc","audit_hash","byt_sync","pdf_path"]
    data = dict(zip(cols, row))
    data["form_data"] = json.loads(fernet.decrypt(data.pop("form_data_enc")))
    return data


def update_pdf_path(record_id: str, pdf_path: str, db_path: Path | None = None) -> None:
    conn = _get_conn(db_path)
    conn.execute(
        "UPDATE clinical_records SET pdf_path=? WHERE record_id=?",
        (pdf_path, record_id)
    )
    conn.commit()
    conn.close()


# ── DVP — Doctor Profile CRUD (FID-VN-012) ───────────────────────────────────

_DVP_COLS = [
    "cchn", "name", "region", "primary_specialty", "secondary_specialty",
    "english_level", "speaking_speed", "created_at", "updated_at",
]

_ALIAS_COLS = [
    "id", "cchn", "alias_text", "inn",
    "session_count", "occurrence_count", "confirmed_by_bs",
    "created_at", "last_seen",
]


def save_doctor_profile(profile: DoctorProfile, db_path: Path | None = None) -> None:
    """Upsert DoctorProfile vào DB."""
    now = datetime.now().isoformat()
    conn = _get_conn(db_path)
    conn.execute(
        """INSERT OR REPLACE INTO doctor_profiles
           (cchn, name, region, primary_specialty, secondary_specialty,
            english_level, speaking_speed, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (
            profile.cchn, profile.name, profile.region,
            profile.primary_specialty, profile.secondary_specialty,
            profile.english_level, profile.speaking_speed,
            profile.created_at or now, now,
        ),
    )
    conn.commit()
    conn.close()


def load_doctor_profile(cchn: str, db_path: Path | None = None) -> DoctorProfile | None:
    """Đọc DoctorProfile theo cchn — trả None nếu chưa có."""
    conn = _get_conn(db_path)
    row = conn.execute(
        "SELECT cchn, name, region, primary_specialty, secondary_specialty,"
        " english_level, speaking_speed, created_at, updated_at"
        " FROM doctor_profiles WHERE cchn=?",
        (cchn,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    return DoctorProfile(**dict(zip(_DVP_COLS, row)))


def save_alias_occurrence(
    cchn: str,
    alias_text: str,
    inn: str,
    session_id: str,
    db_path: Path | None = None,
) -> None:
    """
    Ghi nhận một lần xuất hiện alias từ L4 correction capture.
    session_count tăng khi session_id mới (dùng last_seen làm proxy).
    """
    now = datetime.now().isoformat()
    conn = _get_conn(db_path)
    row = conn.execute(
        "SELECT id, session_count, last_seen FROM doctor_aliases"
        " WHERE cchn=? AND alias_text=?",
        (cchn, alias_text),
    ).fetchone()
    if row is None:
        conn.execute(
            """INSERT INTO doctor_aliases
               (cchn, alias_text, inn, session_count, occurrence_count,
                confirmed_by_bs, created_at, last_seen)
               VALUES (?,?,?,1,1,0,?,?)""",
            (cchn, alias_text, inn, now, session_id),
        )
    else:
        alias_id, sc, last_seen = row
        new_sc = sc + (1 if last_seen != session_id else 0)
        conn.execute(
            """UPDATE doctor_aliases
               SET occurrence_count = occurrence_count + 1,
                   session_count = ?,
                   last_seen = ?
               WHERE id = ?""",
            (new_sc, session_id, alias_id),
        )
    conn.commit()
    conn.close()


def get_pending_aliases(cchn: str, db_path: Path | None = None) -> list[DoctorAlias]:
    """Aliases đủ điều kiện promote (≥3 lần + ≥2 sessions) chưa BS confirm."""
    conn = _get_conn(db_path)
    rows = conn.execute(
        """SELECT id, cchn, alias_text, inn, session_count, occurrence_count,
                  confirmed_by_bs, created_at, last_seen
           FROM doctor_aliases
           WHERE cchn=? AND confirmed_by_bs=0
             AND occurrence_count >= 3 AND session_count >= 2""",
        (cchn,),
    ).fetchall()
    conn.close()
    return [DoctorAlias(**dict(zip(_ALIAS_COLS, r))) for r in rows]


def confirm_alias(alias_id: int, confirmed: bool, db_path: Path | None = None) -> None:
    """BS confirm (True) hoặc reject (False) alias pending."""
    conn = _get_conn(db_path)
    conn.execute(
        "UPDATE doctor_aliases SET confirmed_by_bs=? WHERE id=?",
        (1 if confirmed else -1, alias_id),
    )
    conn.commit()
    conn.close()


def get_active_aliases(cchn: str, db_path: Path | None = None) -> list[DoctorAlias]:
    """Aliases đã được BS confirm (confirmed_by_bs=1)."""
    conn = _get_conn(db_path)
    rows = conn.execute(
        """SELECT id, cchn, alias_text, inn, session_count, occurrence_count,
                  confirmed_by_bs, created_at, last_seen
           FROM doctor_aliases
           WHERE cchn=? AND confirmed_by_bs=1""",
        (cchn,),
    ).fetchall()
    conn.close()
    return [DoctorAlias(**dict(zip(_ALIAS_COLS, r))) for r in rows]
