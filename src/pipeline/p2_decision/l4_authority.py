# src/pipeline/p2_decision/l4_authority.py
# Stage:    L4_DECISION_AUTHORITY
# Role:     Apply HumanGate — set PENDING_APPROVAL before any record is created.
#           No record filed without explicit doctor approval. Non-negotiable.
# Req:      SRS-L4-001 -- see docs/cl08_operation/SRS.md
# FID:      DS-FID-001 | v1.0
# Policy:   AI_POLICY.md §1 — Human Authorship Non-Negotiable
# Standard: ISO/IEC 42001:2023 Clause 8.5
# Version:  v1.2 -- CA-011 (F1 None crash, F2 string items, F4 FLOW_C constant, F5 module-level constant)

from typing import Any, Dict

from src.pipeline.p1_processing.l3_routing import FLOW_C

# Escalate only on safety-critical flags (drug name errors).
# HIGH_WER / LOW_TRANSLATION_CONFIDENCE are soft flags — doctor reviews output anyway.
_HARD_FLAG_CODES = frozenset({"DRUG_NAME_SUSPECT"})


# @req SRS-L4-001 -- Decide allow/reject. No execution. Human-defined rules only.
def handle(payload: Any) -> Dict[str, Any]:
    """L4_DECISION_AUTHORITY: apply HumanGate — mark output PENDING_APPROVAL."""
    if not isinstance(payload, dict):
        return {"ok": False, "stage": "L4_DECISION_AUTHORITY", "error": "INVALID_PAYLOAD"}

    flow = payload.get("flow", "UNKNOWN")
    doctor_id = payload.get("doctor_id")
    # F1: or [] guards against explicit None value (dict.get default only fires when key missing)
    enforcement_flags = payload.get("enforcement_flags") or []

    # FLOW_C (emergency) bypasses HumanGate — explicitly documented in AI_POLICY.md §Emergency
    if flow == FLOW_C:
        approval_status = "BYPASSED_EMERGENCY"
        requires_gate = False
    else:
        approval_status = "PENDING_APPROVAL"
        requires_gate = True

    # F2: isinstance guard — enforcement_flags items must be dicts
    escalation_required = any(
        isinstance(f, dict) and f.get("code") in _HARD_FLAG_CODES
        for f in enforcement_flags
    )

    return {
        "ok": True,
        "stage": "L4_DECISION_AUTHORITY",
        "data": {
            **payload,
            "approval_status": approval_status,
            "requires_human_gate": requires_gate,
            "escalation_required": escalation_required,
            "authority_note": (
                "AI-assisted draft — requires physician review and explicit approval "
                "before any record is created. (AI_POLICY.md §1)"
            ),
            "doctor_id": doctor_id,
        },
    }
