# src/pipeline/p1_processing/l3_routing.py
# Stage:    L3_ROUTING
# Role:     Classify flow type. Output RoutingDecision. No execution.
#           L3_ROUTING is the critical branching module — VISION.md Part 2.
# Req:      SRS-L3-001 -- see docs/cl08_operation/SRS.md
# FID:      DS-FID-001 | v1.0 — classifies FLOW_A (doctor dictation)
# Standard: ISO/IEC 42001:2023 Clause 8.5
# Version:  v1.2 -- CA-010 (NC-001..NC-006 + routing_basis)

from typing import Any, Dict, Tuple

# Flow identifiers (frozen — see VISION.md Part 2)
FLOW_A = "FLOW_A"        # Doctor dictation -> SOAP note
FLOW_B = "FLOW_B"        # Patient triage (DS-FID-004)
FLOW_C = "FLOW_C"        # Emergency handoff (DS-FID-015)
FLOW_D = "FLOW_D"        # Real-time interpretation (DS-FID-010)
FLOW_UNKNOWN = "FLOW_UNKNOWN"  # Unroutable payload

# NC-006: only FLOW_A is active — B/C/D reserved for future FIDs
ENABLED_FLOWS = frozenset({FLOW_A})

_DICTATION_SOURCES  = frozenset({"mobile_mic", "dictation", "voice_note"})
_TRIAGE_SOURCES     = frozenset({"patient_call", "receptionist", "phone"})
_EMERGENCY_SOURCES  = frozenset({"emergency", "paramedic", "ems", "ambulance"})
_INTERPRETER_SOURCES = frozenset({"interpreter_session", "video_call", "live"})


# @req SRS-L3-001 -- Identify request type. Output RoutingDecision. No execution.
def handle(payload: Any) -> Dict[str, Any]:
    """L3_ROUTING: classify input as FLOW_A/B/C/D based on source + context."""
    if not isinstance(payload, dict):
        return {"ok": False, "stage": "L3_ROUTING", "error": "INVALID_PAYLOAD"}

    flow, routing_basis = classify_flow(payload)

    # NC-004: fail closed on unroutable payload
    if flow == FLOW_UNKNOWN:
        return {"ok": False, "stage": "L3_ROUTING", "error": "UNROUTABLE_PAYLOAD"}

    # NC-006: block flows not yet implemented
    if flow not in ENABLED_FLOWS:
        return {
            "ok": False,
            "stage": "L3_ROUTING",
            "error": "FLOW_NOT_IMPLEMENTED",
            "data": {"flow": flow},
        }

    return {
        "ok": True,
        "stage": "L3_ROUTING",
        "data": {
            **payload,
            "flow": flow,
            "routing_decision": {
                "flow": flow,
                "routing_basis": routing_basis,
                "rationale": _routing_rationale(flow),
            },
        },
    }


def classify_flow(payload: Dict) -> Tuple[str, str]:
    """
    Route payload to the correct flow. Returns (flow, routing_basis).

    Source takes absolute priority — doctor_id is fallback only.
    FLOW_A: source in dictation sources, or doctor_id present with no other source
    FLOW_B: source is patient_call / receptionist (DS-FID-004, not yet implemented)
    FLOW_C: source is emergency / paramedic (DS-FID-015, not yet implemented)
    FLOW_D: source is interpreter_session (DS-FID-010, not yet implemented)
    """
    # NC-005: strip whitespace before matching
    source = str(payload.get("source", "")).strip().lower()
    has_doctor = bool(payload.get("doctor_id"))

    # NC-002: source takes priority — doctor_id removed from first condition
    if source in _DICTATION_SOURCES:
        return FLOW_A, "source_match"
    if source in _TRIAGE_SOURCES:
        return FLOW_B, "source_match"
    if source in _EMERGENCY_SOURCES:
        return FLOW_C, "source_match"
    if source in _INTERPRETER_SOURCES:
        return FLOW_D, "source_match"

    # NC-001: fix dead condition — doctor_id is fallback; unknown = FLOW_UNKNOWN
    if has_doctor:
        return FLOW_A, "doctor_id_fallback"
    return FLOW_UNKNOWN, "unknown"


def _routing_rationale(flow: str) -> str:
    rationales = {
        FLOW_A: "Doctor dictation detected — routing to SOAP generation pipeline.",
        FLOW_B: "Patient triage source — routing to Flow B (not yet implemented).",
        FLOW_C: "Emergency source — routing to Flow C MIST handoff (not yet implemented).",
        FLOW_D: "Interpretation session — routing to Flow D (not yet implemented).",
    }
    return rationales.get(flow, "Unknown flow.")
