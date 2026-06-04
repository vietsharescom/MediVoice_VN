# src/pipeline/p2_decision/l6_agent.py
# Stage:    L6_AGENT
# Role:     PRIMARY value-creation stage for DS-FID-001.
#           NER extraction + SOAP note generation from translated medical text.
#           Only stage that calls AI tools. Requires L4=PENDING_APPROVAL AND L5=pass.
# Req:      SRS-L6-001 -- see docs/cl08_operation/SRS.md
# FID:      DS-FID-001 | Primary layer
# Policy:   AI_POLICY.md §1 §2 §3 — Human authorship, transparency, drug integrity
# Standard: ISO/IEC 42001:2023 Clause 8.5
# Version:  v1.3 -- MV-FID-017: VI/EN SOAP dispatch via hint_language

import time
from typing import Any, Dict

from src.pipeline.p2_decision.l6_soap_generator import SOAPGenerator


_generator = SOAPGenerator()


# @req SRS-L6-001 -- Execute AI/tools within approved scope. Requires L4=allow AND L5=pass.
def handle(payload: Any) -> Dict[str, Any]:
    """L6_AGENT: extract NER entities, generate SOAP note, validate structure."""
    if not isinstance(payload, dict):
        return {"ok": False, "stage": "L6_AGENT", "error": "INVALID_PAYLOAD"}

    approval_status = payload.get("approval_status", "PENDING_APPROVAL")
    flow = payload.get("flow", "FLOW_A")

    # SRS-L6-001: verify L4 did not block (escalation_required=True means L4 blocked execution)
    if payload.get("escalation_required", False):
        return {
            "ok": False,
            "stage": "L6_AGENT",
            "error": "L4_GATE_BLOCKED",
            "message": "L4 escalation flag set — L6_AGENT cannot execute. (SRS-L6-001)",
        }

    # L6 only operates on FLOW_A in DS-FID-001 scope.
    # Phase 2: replace with FLOW_B/C/D handler when FID approved.
    if flow != "FLOW_A":
        return {
            "ok": False,
            "stage": "L6_AGENT",
            "error": "FLOW_NOT_IMPLEMENTED",
            "data": {"flow": flow},
        }

    processed = payload.get("processed_text") or ""
    original = payload.get("original_text") or ""
    if processed:
        text = processed
        text_source = "processed_text"
    elif original:
        text = original
        text_source = "original_text"
    else:
        text = ""
        text_source = "none"

    if not text:
        is_speech_flow = any(payload.get(k) for k in ("doctor_id", "content_hash"))
        if is_speech_flow:
            return {"ok": False, "stage": "L6_AGENT", "error": "NO_TEXT_FOR_GENERATION",
                    "message": "processed_text is empty — cannot generate SOAP."}
        # Non-speech payload — pass through
        return {"ok": True, "stage": "L6_AGENT",
                "data": {**payload, "l6_skipped": True,
                         "l6_skip_reason": "no text content — non-speech payload"}}

    t0 = time.perf_counter()

    # Extract NER entities — NER-B1: pass original VI text for dual parallel NER
    hint_language = payload.get("hint_language") or "en"
    vi_text = original if hint_language == "vi" and original != text else ""
    entities = _generator.extract_entities(text, vi_text=vi_text)

    # FID-VN-004: VN branch — lam_sang → Mẫu 15/BV-01 directly (no SOAP)
    vn_route = payload.get("vn_route", "lam_sang")
    if vn_route == "lam_sang":
        from src.pipeline.p2_decision.l6_mau15_generator import generate_mau15
        elapsed_ms = (time.perf_counter() - t0) * 1000
        benh_an_dict = generate_mau15(entities, payload)
        return {
            "ok": True,
            "stage": "L6_AGENT",
            "data": {
                **payload,
                "benh_an": benh_an_dict,
                "vn_route": vn_route,
                "ner_entities": [e.to_dict() for e in entities if not e.negated],
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "l6_generation_ms": round(elapsed_ms, 1),
                "approval_status": payload.get("approval_status", "PENDING_APPROVAL"),
                "disclaimer": "AI tạo nháp — Bác sĩ chịu trách nhiệm hoàn toàn.",
            },
        }

    # cdha / nha_khoa — existing Canada SOAP path
    if hint_language == "vi":
        soap = _generator.generate_soap_vi(entities, text)
    else:
        soap = _generator.generate_soap(entities, text)

    # Validate — all 4 sections must be present
    if not _generator.validate_soap(soap):
        return {"ok": False, "stage": "L6_AGENT", "error": "SOAP_INCOMPLETE",
                "message": "Generated SOAP note is missing one or more sections."}

    elapsed_ms = (time.perf_counter() - t0) * 1000

    output_data: Dict[str, Any] = {
        **payload,
        "soap_note": soap.to_dict(),
        "ner_entities": [e.to_dict() for e in entities if not e.negated],
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "l6_generation_ms": round(elapsed_ms, 1),
        "approval_status": approval_status,
        "l6_text_source": text_source,
        "soap_language": hint_language,
    }
    if text_source == "original_text":
        output_data["l6_warning"] = "TEXT_SOURCE_FALLBACK — SOAP generated from untranslated text; NER accuracy degraded."
    return {"ok": True, "stage": "L6_AGENT", "data": output_data}
