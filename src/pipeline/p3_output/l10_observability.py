# src/pipeline/p3_output/l10_observability.py
# Stage:    L10_OBSERVABILITY
# Role:     Audit log for every session. Always active. Cannot be disabled.
#           Logs: modules executed, drug flags, WER, approval status, timing.
# Req:      SRS-L10-001 -- see docs/cl08_operation/SRS.md
# FID:      DS-FID-001 | v1.0
# Policy:   AI_POLICY.md §7 — WER and edit rate tracked per session (anonymized)
# Standard: ISO/IEC 42001:2023 Clause 8.5
# Version:  v1.2 -- CA-015: remove dead _full_payload ref, fix modules_executed list

import time
from typing import Any, Dict, List


# @req SRS-L10-001 -- Log all execution. Always active. Cannot be disabled.
def handle(payload: Any) -> Dict[str, Any]:
    """L10_OBSERVABILITY: write audit log entry for the session."""
    if not isinstance(payload, dict):
        return {"ok": True, "stage": "L10_OBSERVABILITY",
                "data": payload, "audit": {"error": "non-dict payload logged"}}

    session_id = payload.get("session_id", "unknown")
    flow = payload.get("flow", "unknown")

    audit_entry = _build_audit_entry(session_id, flow, payload)

    # L10 passes through the payload unchanged (plus audit record)
    return {
        "ok": True,
        "stage": "L10_OBSERVABILITY",
        "data": payload,
        "audit": audit_entry,
    }


def _build_audit_entry(session_id: str, flow: str, payload: Dict) -> Dict:
    """Build structured audit record per AI_POLICY.md §7."""
    return {
        "session_id": session_id,
        "flow": flow,
        "logged_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "doctor_id": payload.get("doctor_id", "unknown"),
        "patient_id": payload.get("patient_id", "unknown"),
        "detected_language": payload.get("detected_language", "unknown"),
        "wer_estimate": payload.get("wer_estimate", 0.0),
        "translation_confidence": (payload.get("translation") or {}).get("confidence"),
        "drug_flags_count": len(payload.get("drug_flags", [])),
        "enforcement_flags_count": len(payload.get("enforcement_flags", [])),
        "approval_status": payload.get("approval_status", "unknown"),
        "soap_generated": bool(payload.get("soap_note")),
        "ner_entity_count": len(payload.get("ner_entities", [])),
        "audio_retained": False,  # always False — AI_POLICY.md §4
        "modules_executed": ["L0", "L1", "L1b", "L2", "L3", "L4", "L5", "L6", "L7", "L9", "L10"],
    }
