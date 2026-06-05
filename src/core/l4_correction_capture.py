"""
L4 Correction Capture — Implicit Supervision (TIER 2 Adaptive Learning)
FID-VN-006 | ISO/IEC 42001:2023 Cl.9.1 (Performance evaluation)

BS edits at L4 = ground-truth labels for NER training data.
Logs AI→BS diffs to data/corrections/{clinic_id}/corrections.jsonl
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_CORRECTIONS_ROOT = Path(__file__).parent.parent.parent / "data" / "corrections"
_SCHEMA_VERSION = "1.0"

# Fields we compare (skip metadata/system fields)
_TRACKED_FIELDS = {
    "chan_doan",
    "don_thuoc",
    "ho_va_ten",
    "tuoi",
    "gioi_tinh",
    "nhiet_do",
    "huyet_ap",
    "mach",
    "ly_do_kham",
    "tien_su",
    "tai_kham",
    "icd_code",
    "icd_display",
}


def capture(
    record_id: str,
    clinic_id: str,
    transcript: str,
    ai_form: dict[str, Any],
    bs_form: dict[str, Any],
    doctor_cchn: str,
) -> None:
    """
    Compare ai_form vs bs_form, log corrections to JSONL.
    Best-effort: exceptions are logged but never re-raised.

    Args:
        record_id:    ClinicalRecord.record_id
        clinic_id:    ClinicalRecord.facility_id
        transcript:   transcript_corrected (context for alias analysis)
        ai_form:      form_data snapshot BEFORE BS edits
        bs_form:      form_data AFTER BS edits
        doctor_cchn:  approving doctor
    """
    try:
        corrections = _diff_forms(ai_form, bs_form)
        entry = {
            "schema_version": _SCHEMA_VERSION,
            "record_id": record_id,
            "clinic_id": clinic_id,
            "doctor_cchn": doctor_cchn,
            "timestamp": datetime.now(timezone.utc).astimezone().isoformat(),
            "transcript_snippet": (transcript or "")[:500],
            "corrections": corrections,
            "correction_count": len(corrections),
        }
        _write_entry(clinic_id, entry)
    except Exception as exc:
        logger.warning("L4 correction capture failed (non-blocking): %s", exc)


def _diff_forms(
    ai: dict[str, Any], bs: dict[str, Any]
) -> list[dict[str, Any]]:
    """Return list of {field, ai_value, bs_value, note} for changed fields."""
    diffs: list[dict[str, Any]] = []
    all_keys = _TRACKED_FIELDS & (set(ai.keys()) | set(bs.keys()))

    for field in sorted(all_keys):
        ai_val = ai.get(field)
        bs_val = bs.get(field)

        if _values_equal(ai_val, bs_val):
            continue

        if field not in ai or ai_val is None or ai_val == [] or ai_val == "":
            note = "field_added"
        elif field not in bs or bs_val is None or bs_val == [] or bs_val == "":
            note = "field_cleared"
        else:
            note = "field_corrected"

        diffs.append({
            "field": field,
            "ai_value": ai_val,
            "bs_value": bs_val,
            "note": note,
        })

    return diffs


def _values_equal(a: Any, b: Any) -> bool:
    """Loose equality: treats None/""/[] as equivalent empty."""
    def _empty(v: Any) -> bool:
        return v is None or v == "" or v == []

    if _empty(a) and _empty(b):
        return True
    return a == b


def _write_entry(clinic_id: str, entry: dict[str, Any]) -> None:
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in clinic_id)
    clinic_dir = _CORRECTIONS_ROOT / safe_id
    clinic_dir.mkdir(parents=True, exist_ok=True)

    log_file = clinic_dir / "corrections.jsonl"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
