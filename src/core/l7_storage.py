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
