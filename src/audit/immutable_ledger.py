"""
MediVoice VN — Immutable Audit Ledger
ISO/IEC 42001:2023 Clause 9 | Luật AI 134/2025 Điều 24

Adapted from MediVoice AI (Canada) src/audit/ledger.py
Changes for VN:
  - Vietnamese field names + law references
  - Fernet encryption integration
  - BYT sync status field
  - CCHN-based actor identity

IMMUTABLE: Records CANNOT be modified or deleted after creation.
Hash chain ensures tamper detection.
"""

import hashlib
import json
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class AuditRecord:
    """
    Một sự kiện audit không thể thay đổi.
    Luật AI 134/2025: phải lưu đủ để audit compliance.
    """
    event_id: str              # UUID
    timestamp: str             # ISO 8601
    actor_id: str              # CCHN của BS hoặc "SYSTEM"
    actor_role: str            # "bac_si" | "system" | "admin"
    patient_ref: str           # hash của patient ID (không lưu raw)
    action: str                # "draft_created" | "approved" | "rejected" | "exported"
    layer: str                 # "L4_HUMAN_GATE" | "L6_GENERATE" | ...
    record_id: str             # ID của bệnh án liên quan
    details: str               # JSON string — thêm thông tin
    prev_hash: str             # Hash của record trước (chain)
    record_hash: str           # SHA-256 của record này
    byt_sync_status: str       # "not_required" | "pending" | "synced"

    def to_dict(self) -> dict:
        return asdict(self)

    def verify_hash(self) -> bool:
        """Kiểm tra hash có khớp với nội dung không."""
        data = {k: v for k, v in asdict(self).items() if k != "record_hash"}
        computed = _compute_hash(data)
        return computed == self.record_hash


def _compute_hash(data: dict) -> str:
    """SHA-256 hash của record data."""
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ImmutableLedger:
    """
    Append-only audit ledger với SHA-256 hash chain.

    Mỗi record chứa hash của record trước → tamper detection.
    Nếu bất kỳ record nào bị sửa → chain bị phá vỡ → phát hiện.

    Storage: SQLite table 'audit_log' (separate từ patient data).
    """

    TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS audit_log (
        event_id        TEXT PRIMARY KEY,
        timestamp       TEXT NOT NULL,
        actor_id        TEXT NOT NULL,
        actor_role      TEXT NOT NULL,
        patient_ref     TEXT NOT NULL,
        action          TEXT NOT NULL,
        layer           TEXT NOT NULL,
        record_id       TEXT NOT NULL,
        details         TEXT,
        prev_hash       TEXT NOT NULL,
        record_hash     TEXT NOT NULL,
        byt_sync_status TEXT NOT NULL DEFAULT 'not_required'
    )
    """

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(self.TABLE_SQL)
            conn.commit()

    def _get_last_hash(self) -> str:
        """Hash của record cuối cùng trong chain."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT record_hash FROM audit_log ORDER BY timestamp DESC LIMIT 1"
            ).fetchone()
            return row[0] if row else "GENESIS"

    def log(
        self,
        actor_id: str,
        actor_role: str,
        patient_ref: str,
        action: str,
        layer: str,
        record_id: str,
        details: dict | None = None,
        byt_sync_status: str = "not_required",
    ) -> AuditRecord:
        """
        Ghi một sự kiện vào ledger. KHÔNG THỂ SỬA SAU KHI GHI.

        Args:
            actor_id:    CCHN của BS hoặc "SYSTEM"
            actor_role:  "bac_si" | "system" | "admin"
            patient_ref: SHA-256 hash của patient ID
            action:      Loại sự kiện
            layer:       Pipeline layer (L4, L10, etc.)
            record_id:   ID của bệnh án
            details:     Thông tin bổ sung (dict → JSON)
            byt_sync_status: "not_required" | "pending" | "synced"

        Returns:
            AuditRecord đã lưu
        """
        import uuid
        prev_hash = self._get_last_hash()
        timestamp = datetime.utcnow().isoformat() + "Z"
        event_id = str(uuid.uuid4())
        details_str = json.dumps(details or {}, ensure_ascii=False)

        data_for_hash = {
            "event_id": event_id,
            "timestamp": timestamp,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "patient_ref": patient_ref,
            "action": action,
            "layer": layer,
            "record_id": record_id,
            "details": details_str,
            "prev_hash": prev_hash,
            "byt_sync_status": byt_sync_status,
        }
        record_hash = _compute_hash(data_for_hash)

        record = AuditRecord(
            event_id=event_id,
            timestamp=timestamp,
            actor_id=actor_id,
            actor_role=actor_role,
            patient_ref=patient_ref,
            action=action,
            layer=layer,
            record_id=record_id,
            details=details_str,
            prev_hash=prev_hash,
            record_hash=record_hash,
            byt_sync_status=byt_sync_status,
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO audit_log VALUES
                (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    record.event_id, record.timestamp, record.actor_id,
                    record.actor_role, record.patient_ref, record.action,
                    record.layer, record.record_id, record.details,
                    record.prev_hash, record.record_hash, record.byt_sync_status,
                ),
            )
            conn.commit()

        return record

    def verify_chain(self) -> tuple[bool, list[str]]:
        """
        Kiểm tra toàn bộ hash chain còn nguyên vẹn.

        Returns:
            (is_valid, list of error messages)
        """
        errors = []
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM audit_log ORDER BY timestamp ASC"
            ).fetchall()

        cols = [
            "event_id", "timestamp", "actor_id", "actor_role",
            "patient_ref", "action", "layer", "record_id",
            "details", "prev_hash", "record_hash", "byt_sync_status"
        ]
        records = [dict(zip(cols, row)) for row in rows]

        prev_hash = "GENESIS"
        for i, rec in enumerate(records):
            # Verify prev_hash matches
            if rec["prev_hash"] != prev_hash:
                errors.append(
                    f"Chain broken at record {i} ({rec['event_id']}): "
                    f"expected prev_hash={prev_hash}, got {rec['prev_hash']}"
                )

            # Verify record_hash
            data = {k: v for k, v in rec.items() if k != "record_hash"}
            computed = _compute_hash(data)
            if computed != rec["record_hash"]:
                errors.append(
                    f"Tampered record at {i} ({rec['event_id']}): "
                    f"hash mismatch"
                )

            prev_hash = rec["record_hash"]

        return len(errors) == 0, errors

    def get_records_for_patient(self, patient_ref: str) -> list[dict]:
        """Lấy tất cả events của một bệnh nhân."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM audit_log WHERE patient_ref = ? ORDER BY timestamp",
                (patient_ref,)
            ).fetchall()
        cols = [
            "event_id", "timestamp", "actor_id", "actor_role",
            "patient_ref", "action", "layer", "record_id",
            "details", "prev_hash", "record_hash", "byt_sync_status"
        ]
        return [dict(zip(cols, row)) for row in rows]

    def get_records_for_record(self, record_id: str) -> list[dict]:
        """Lấy audit trail của một bệnh án."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM audit_log WHERE record_id = ? ORDER BY timestamp",
                (record_id,)
            ).fetchall()
        cols = [
            "event_id", "timestamp", "actor_id", "actor_role",
            "patient_ref", "action", "layer", "record_id",
            "details", "prev_hash", "record_hash", "byt_sync_status"
        ]
        return [dict(zip(cols, row)) for row in rows]

    def count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]

    # ── READ-ONLY — No delete/update methods (IMMUTABLE) ──────────────────
    # Luật AI 134/2025: audit log phải immutable
    # tests/compliance/test_audit_ledger.py verifies no such methods exist
