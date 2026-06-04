# src/pipeline/p3_output/l9_response.py
# Stage:    L9_RESPONSE
# Role:     Format final output per DS-FID-001 JSON contract. No inference. No fabrication.
#           English SOAP + Vietnamese original transcript side-by-side.
# Req:      SRS-L9-001 -- see docs/cl08_operation/SRS.md
# FID:      DS-FID-001 | §4 Contract — Output from L9_RESPONSE
# Policy:   AI_POLICY.md §2 — Transparency: show full chain from speech to note
# Standard: ISO/IEC 42001:2023 Clause 8.5
# Version:  v1.3 -- TEST-AUDIO-HF: pass pipeda_compliant from L5 through to API response

from typing import Any, Dict


# @req SRS-L9-001 -- Format output. No inference. No fabrication.
def handle(payload: Any) -> Dict[str, Any]:
    """L9_RESPONSE: assemble final DS-FID-001 JSON contract output."""
    if not isinstance(payload, dict):
        return {"ok": False, "stage": "L9_RESPONSE", "error": "INVALID_PAYLOAD"}

    flow = payload.get("flow", "FLOW_A")

    # Phase 2: replace with FLOW_B/C/D formatter when FID approved.
    if flow != "FLOW_A":
        return {
            "ok": False,
            "stage": "L9_RESPONSE",
            "error": "FLOW_NOT_IMPLEMENTED",
            "data": {"flow": flow},
        }

    session_id = payload.get("session_id", "")
    original_text = payload.get("original_text", "")
    language = payload.get("detected_language", "en")
    wer_estimate = payload.get("wer_estimate", 0.0)
    confidence = payload.get("confidence", 0.0)
    translation = payload.get("translation")

    # NC-005: type guards — malformed upstream data must not corrupt client contract
    soap_note = payload.get("soap_note", {})
    if not isinstance(soap_note, dict):
        soap_note = {}

    ner_entities = payload.get("ner_entities", [])
    if not isinstance(ner_entities, list):
        ner_entities = []

    approval_status = payload.get("approval_status", "PENDING_APPROVAL")
    generated_at = payload.get("generated_at", "")
    pipeda_compliant = payload.get("pipeda_compliant", False)

    response: Dict[str, Any] = {
        "ok": True,
        "stage": "L9_RESPONSE",
        "session_id": session_id,
        "flow": flow,
        "data": {
            "original_transcript": {
                "language": language,
                "text": original_text,
                "wer_estimate": wer_estimate,
                "confidence": confidence,
            },
            "soap_note": soap_note,
            "ner_entities": ner_entities,
            "status": approval_status,
            "generated_at": generated_at,
            "disclaimer": "AI-assisted draft — requires physician review and explicit approval.",
            "pipeda_compliant": pipeda_compliant,
        },
    }

    # NC-003: isinstance guard — only include translation when it is a populated dict
    if isinstance(translation, dict) and translation:
        response["data"]["translation"] = {
            "text": translation.get("translated_text", ""),
            "confidence": translation.get("confidence", 0.0),
            "preserved_terms": translation.get("preserved_terms", []),
        }

    # Include enforcement flags if any
    enforcement_flags = payload.get("enforcement_flags") or []
    if enforcement_flags:
        response["data"]["enforcement_flags"] = enforcement_flags

    # NC-002: _full_payload removed — L10 receives full L9 result; internal state
    #         must not be exposed in client-facing contract (PIPEDA P5, data minimization)
    # NC-004: _audit_meta removed — modules_executed/processing_time_ms never populated
    #         by Orchestrator; phantom fields reduce trust in observability layer

    return response
