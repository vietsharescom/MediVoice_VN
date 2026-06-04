# L10 — Immutable Audit Log
# ISO/IEC 42001:2023 | Luật AI 134/2025
# IMMUTABLE: NO delete/update/modify functions allowed
# Each entry: timestamp + actor_cchn + action + SHA-256 hash chain
# FROZEN PIPELINE LAYER

from __future__ import annotations
import hashlib
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path


def _hash_entry(entry_id: str, timestamp: str, record_id: str,
                actor_cchn: str, action: str, detail: str, prev_hash: str) -> str:
    payload = f"{entry_id}|{timestamp}|{record_id}|{actor_cchn}|{action}|{detail}|{prev_hash}"
    return hashlib.sha256(payload.encode()).hexdigest()


def log_event(
    db_conn: sqlite3.Connection,
    record_id: str,
    actor_cchn: str,
    action: str,
    detail: str = "",
) -> str:
    """
    Append-only audit log entry với SHA-256 hash chain.
    Trả về entry_id.
    Không được có hàm xóa/sửa — IMMUTABLE (ISO 42001 + Luật AI 134/2025).
    """
    entry_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()

    # Lấy hash của entry cuối cùng (chain)
    row = db_conn.execute(
        "SELECT entry_hash FROM audit_log ORDER BY timestamp DESC LIMIT 1"
    ).fetchone()
    prev_hash = row[0] if row else ""

    entry_hash = _hash_entry(
        entry_id, timestamp, record_id, actor_cchn, action, detail, prev_hash
    )

    db_conn.execute("""
        INSERT INTO audit_log
        (entry_id, timestamp, record_id, actor_cchn, action, detail, prev_hash, entry_hash)
        VALUES (?,?,?,?,?,?,?,?)
    """, (entry_id, timestamp, record_id, actor_cchn, action, detail, prev_hash, entry_hash))
    db_conn.commit()

    return entry_id


def verify_chain(db_conn: sqlite3.Connection) -> tuple[bool, str]:
    """
    Kiểm tra toàn bộ hash chain của audit log.
    Returns (is_valid, error_message)
    """
    rows = db_conn.execute(
        "SELECT entry_id, timestamp, record_id, actor_cchn, action, detail, prev_hash, entry_hash "
        "FROM audit_log ORDER BY timestamp ASC"
    ).fetchall()

    prev_hash = ""
    for row in rows:
        entry_id, ts, rid, cchn, action, detail, stored_prev, stored_hash = row
        if stored_prev != prev_hash:
            return False, f"Chain break at entry {entry_id}: prev_hash mismatch"
        computed = _hash_entry(entry_id, ts, rid, cchn, action, detail, stored_prev)
        if computed != stored_hash:
            return False, f"Tamper detected at entry {entry_id}"
        prev_hash = stored_hash

    return True, ""


def get_record_history(db_conn: sqlite3.Connection, record_id: str) -> list[dict]:
    """Lấy toàn bộ audit history của một record."""
    rows = db_conn.execute(
        "SELECT entry_id, timestamp, actor_cchn, action, detail "
        "FROM audit_log WHERE record_id=? ORDER BY timestamp ASC",
        (record_id,)
    ).fetchall()
    return [
        {"entry_id": r[0], "timestamp": r[1], "actor_cchn": r[2],
         "action": r[3], "detail": r[4]}
        for r in rows
    ]
