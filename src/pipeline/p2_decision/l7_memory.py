# src/pipeline/p2_decision/l7_memory.py
# Stage:    L7_MEMORY_TOOL
# Role:     Store and retrieve per-patient visit history (SQLite local).
#           patient_id MUST be a SHA-256 hash of health card / SIN — never raw PII.
# Req:      SRS-L7-001..008 -- see docs/cl08_operation/SRS.md
# FID:      MV-FID-008 | 2026-05-25 | MV-FID-010 | 2026-05-26
# Policy:   PIPEDA Principle 5 (limiting use), Principle 7 (safeguards)
# Standard: ISO/IEC 42001:2023 Clause 8.5
# Version:  v1.3 -- CA-014: NC-001 soap_note call-site guard, NC-002 narrow except,
#                            NC-006 calendar year retention

import datetime
import json
import os
import sqlite3
import time
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet, InvalidToken

DB_PATH = os.path.join("data", "memory", "patients.db")
_ENV_KEY = "MEDIVOICE_DB_KEY"

MAX_HISTORY = 5
PATIENT_ID_HASH_LEN = 64   # SHA-256 produces exactly 64 hex characters
RETENTION_YEARS = 7        # PIPEDA medical records retention — enforced via _purge_old_visits()

_SHA256_HEX = frozenset('0123456789abcdefABCDEF')


def _get_fernet() -> Optional[Fernet]:
    """Return Fernet instance from env var, or None if not set."""
    raw = os.environ.get(_ENV_KEY, "")
    if not raw:
        return None
    return Fernet(raw.encode())


def _encrypt(fernet: Fernet, text: str) -> str:
    """Encrypt UTF-8 text; return base64-urlsafe ciphertext string."""
    return fernet.encrypt(text.encode()).decode()


def _decrypt(fernet: Fernet, token: str) -> str:
    """Decrypt Fernet token; raises InvalidToken on failure."""
    return fernet.decrypt(token.encode()).decode()

_SCHEMA = """
CREATE TABLE IF NOT EXISTS visits (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id  TEXT    NOT NULL,
    session_id  TEXT,
    doctor_id   TEXT,
    visit_date  TEXT    NOT NULL,
    symptoms    TEXT,
    medications TEXT,
    vitals      TEXT,
    soap_s      TEXT,
    created_at  TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_patient_date ON visits (patient_id, visit_date DESC);
"""


def _is_valid_patient_hash(pid: str) -> bool:
    """SHA-256 hex: exactly 64 characters from [0-9a-fA-F]."""
    return len(pid) == PATIENT_ID_HASH_LEN and all(c in _SHA256_HEX for c in pid)


# @req SRS-L7-001 -- Store visit when patient_id present and SOAP generated.
# @req SRS-L7-002 -- Retrieve last 5 visits for patient_id.
# @req SRS-L7-003 -- Pass-through when patient_id absent.
# @req SRS-L7-004 -- Reject patient_id that is not a valid SHA-256 hex hash.
# @req SRS-L7-005 -- No network calls.
# @req SRS-L7-006 -- Degrade gracefully on DB error.
# @req SRS-L7-007 -- Purge visits older than RETENTION_YEARS on each session start.
# @req SRS-L7-008 -- Return generic error code on DB failure — never expose internals.
def handle(payload: Any) -> Dict[str, Any]:
    """L7_MEMORY_TOOL: store visit + retrieve history. Pass-through if no patient_id."""
    if not isinstance(payload, dict):
        return {"ok": False, "stage": "L7_MEMORY_TOOL", "error": "INVALID_PAYLOAD"}

    patient_id = payload.get("patient_id")

    # SRS-L7-003: patient_id absent (None) → silent pass-through
    if patient_id is None:
        return {
            "ok": True,
            "stage": "L7_MEMORY_TOOL",
            "data": {
                **payload,
                "visit_history": [],
                "visit_count": 0,
                "l7_skipped": True,
                "l7_skip_reason": "no patient_id in payload",
            },
        }

    # SRS-L7-004: patient_id must be a SHA-256 hex hash (exactly 64 hex chars)
    # Empty string, short IDs, long non-hashes, and non-hex strings all rejected here.
    if not isinstance(patient_id, str) or not _is_valid_patient_hash(patient_id):
        return {
            "ok": False,
            "stage": "L7_MEMORY_TOOL",
            "error": "INVALID_PATIENT_ID",
            "message": (
                f"patient_id must be a SHA-256 hex hash ({PATIENT_ID_HASH_LEN} hex chars). "
                "Caller must hash OHIP/SIN before sending. Never send raw health card number."
            ),
        }

    # MV-FID-010: require encryption key before any DB operation
    fernet = _get_fernet()
    if fernet is None:
        return {
            "ok": False,
            "stage": "L7_MEMORY_TOOL",
            "error": "L7_KEY_MISSING",
            "message": f"Environment variable {_ENV_KEY} is not set. Set it to a valid Fernet key.",
        }

    try:
        _ensure_db()

        # SRS-L7-001: store if SOAP was generated (NC-001: must be a non-empty dict)
        soap_note = payload.get("soap_note")
        if isinstance(soap_note, dict) and soap_note:
            _store_visit(patient_id, payload, fernet)

        # SRS-L7-002: retrieve history (exclude current session)
        history = _get_history(patient_id, exclude_session=payload.get("session_id", ""), fernet=fernet)

    except InvalidToken:
        # MV-FID-010: wrong key or tampered ciphertext
        return {
            "ok": False,
            "stage": "L7_MEMORY_TOOL",
            "error": "L7_DECRYPT_ERROR",
        }
    except sqlite3.Error:
        # SRS-L7-006 + SRS-L7-008: DB infra errors degrade gracefully (disk, lock, schema)
        return {
            "ok": True,
            "stage": "L7_MEMORY_TOOL",
            "data": {
                **payload,
                "visit_history": [],
                "visit_count": 0,
                "l7_db_error": "L7_DB_ERROR",
            },
        }
    except Exception:
        # NC-002 (CA-014): unexpected errors fail-closed — SRS-L7-008 generic code, no internals
        return {
            "ok": False,
            "stage": "L7_MEMORY_TOOL",
            "error": "L7_UNEXPECTED_ERROR",
        }

    return {
        "ok": True,
        "stage": "L7_MEMORY_TOOL",
        "data": {
            **payload,
            "visit_history": history,
            "visit_count": len(history),
        },
    }


def _ensure_db() -> None:
    """Create DB and schema if not exists, then purge expired records (SRS-L7-007)."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(_SCHEMA)
    _purge_old_visits()


def _purge_old_visits() -> None:
    """Delete visits older than RETENTION_YEARS — PIPEDA Principle 4 (limiting collection)."""
    if not os.path.exists(DB_PATH):
        return
    # NC-006 (CA-014): calendar year arithmetic — avoids leap year drift (~2 days/7yr)
    today = datetime.date.today()
    try:
        cutoff = today.replace(year=today.year - RETENTION_YEARS).strftime("%Y-%m-%d")
    except ValueError:
        # Feb 29 in a leap year — shift to Feb 28
        cutoff = today.replace(year=today.year - RETENTION_YEARS, day=28).strftime("%Y-%m-%d")
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM visits WHERE visit_date < ?", (cutoff,))


def _store_visit(patient_id: str, payload: Dict, fernet: Fernet) -> None:
    """Extract clinical data from payload, encrypt PHI fields, and persist to SQLite."""
    entities = payload.get("ner_entities", [])
    soap = payload.get("soap_note", {})

    # NC-004: use .get() — skip entities that are missing the 'value' key
    symptoms = [
        e["value"] for e in entities
        if e.get("type") == "SYMPTOM" and e.get("value")
    ]
    medications = [
        {"name": e["value"], "dose": e.get("dose", ""), "frequency": e.get("frequency", "")}
        for e in entities
        if e.get("type") == "MEDICATION" and e.get("value")
    ]
    vitals = {
        e.get("name", "vital"): f"{e.get('value', '')} {e.get('unit', '')}".strip()
        for e in entities
        if e.get("type") == "VITAL" and e.get("value")
    }

    # A10: visit_date in UTC
    visit_date = time.strftime("%Y-%m-%d", time.gmtime())
    created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # MV-FID-010: encrypt PHI text fields before storing
    enc_symptoms    = _encrypt(fernet, json.dumps(symptoms))
    enc_medications = _encrypt(fernet, json.dumps(medications))
    enc_vitals      = _encrypt(fernet, json.dumps(vitals))
    enc_soap_s      = _encrypt(fernet, soap.get("S", ""))

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """INSERT INTO visits
               (patient_id, session_id, doctor_id, visit_date,
                symptoms, medications, vitals, soap_s, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                patient_id,
                payload.get("session_id", ""),
                payload.get("doctor_id", ""),
                visit_date,
                enc_symptoms,
                enc_medications,
                enc_vitals,
                enc_soap_s,
                created_at,
            ),
        )


def _safe_json(s: str, default: Any) -> Any:
    """Parse JSON; return default on corrupt data rather than raising (NC-006)."""
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return default


def _get_history(patient_id: str, exclude_session: str = "", fernet: Optional[Fernet] = None) -> List[Dict]:
    """Return last MAX_HISTORY visits for patient, excluding current session."""
    if not os.path.exists(DB_PATH):
        return []
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT visit_date, symptoms, medications, vitals, soap_s, doctor_id
               FROM visits
               WHERE patient_id = ? AND session_id != ?
               ORDER BY visit_date DESC, id DESC
               LIMIT ?""",
            (patient_id, exclude_session, MAX_HISTORY),
        ).fetchall()

    history = []
    for row in rows:
        # MV-FID-010: decrypt PHI fields — InvalidToken propagates to caller for L7_DECRYPT_ERROR
        raw_symptoms    = _decrypt(fernet, row["symptoms"])    if fernet and row["symptoms"]    else (row["symptoms"]    or "[]")
        raw_medications = _decrypt(fernet, row["medications"]) if fernet and row["medications"] else (row["medications"] or "[]")
        raw_vitals      = _decrypt(fernet, row["vitals"])      if fernet and row["vitals"]      else (row["vitals"]      or "{}")
        raw_soap_s      = _decrypt(fernet, row["soap_s"])      if fernet and row["soap_s"]      else (row["soap_s"]      or "")

        # NC-006: per-row JSON parse — one corrupt row returns defaults, not an exception
        history.append({
            "visit_date":   row["visit_date"],
            "symptoms":     _safe_json(raw_symptoms, []),
            "medications":  _safe_json(raw_medications, []),
            "vitals":       _safe_json(raw_vitals, {}),
            "soap_s":       raw_soap_s,
            "doctor_id":    row["doctor_id"] or "",
        })
    return history
