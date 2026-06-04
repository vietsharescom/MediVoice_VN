# src/pipeline/p2_decision/l5_policy.py
# Stage:    L5_POLICY_ENGINE
# Role:     Apply PIPEDA (Canada) + VN NĐ13/2023 privacy policies. No tool calls. No network.
# Req:      SRS-L5-001..006 -- see docs/cl08_operation/SRS.md
# FID:      MV-FID-003 | v1.0
# Policy:   PIPEDA S.C. 2000, c. 5 (Canada) | NĐ13/2023/NĐ-CP (Vietnam)
# Standard: ISO/IEC 42001:2023 Clause 8.5
# Version:  v1.4 -- GOV-001: add VN PII patterns (CCCD, BHYT, SĐT, CMND, Hộ chiếu)

import re
from typing import Any, Dict, FrozenSet, List

# @req SRS-L5-003 -- PII pattern scan: Canada (PIPEDA) patterns
_PII_PATTERNS = {
    "ohip_number":  re.compile(r'\b\d{4}[-\s]?\d{3}[-\s]?\d{3}[-\s]?\d{2}\b'),
    # FIX F3 (MV-CR-001): separator made optional — catches "123456789" (no-dash SIN)
    "sin_number":   re.compile(r'\b\d{3}[-\s]?\d{3}[-\s]?\d{3}\b'),
    "phone_number": re.compile(
        r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b'
    ),
    "email":        re.compile(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b'),
}

# GOV-001: Vietnam PII patterns (NĐ13/2023/NĐ-CP)
_VN_PII_PATTERNS = {
    "cccd_vn":      re.compile(r'\b\d{12}\b'),                   # Căn cước công dân (12 số)
    "cmnd_vn":      re.compile(r'\b\d{9}\b'),                    # CMND cũ (9 số)
    "bhyt_vn":      re.compile(r'\b[A-Z]{2}\d{13}\b'),           # Bảo hiểm y tế
    "phone_vn":     re.compile(r'\b0[3-9]\d{8}\b'),              # SĐT VN (Viettel/Mobifone/Vinaphone)
    "passport_vn":  re.compile(r'\b[A-Z]\d{7}\b'),               # Hộ chiếu VN
}

ALLOWED_PURPOSES = {"medical_documentation", "clinical_note", "soap_generation"}

# NC-006 (CA-013): explicit allowlist — "False"/"0" strings are truthy in Python
# but mean "not retained". Truthy check alone would block valid payloads.
_AUDIO_RETAINED_TRUTHY: FrozenSet = frozenset({True, 1, "true", "True", "1"})

# FIX F2 (MV-CR-001): PIPEDA P5 data minimization — only declared fields propagate.
# audio_retained is intentionally excluded (consumed by L5, no downstream need).
_DOWNSTREAM_FIELDS: FrozenSet[str] = frozenset({
    "session_id", "doctor_id", "patient_id",
    "flow", "route_id", "l4_decision", "l4_reason",
    "original_text", "processed_text", "translation",
    "transcript", "detected_language", "wer_estimate",
    "intent", "approval_status", "purpose", "consent_given",
    "hint_language",  # MV-FID-017: controls SOAP output language in L6
})


# @req SRS-L5-001 -- verify audio_retained=False
# @req SRS-L5-002 -- verify purpose=medical_documentation
# @req SRS-L5-003 -- PII scan, flag not block
# @req SRS-L5-004 -- pipeda_warning when consent_given=False
# @req SRS-L5-005 -- return policies_applied list
# @req SRS-L5-006 -- no external calls
def handle(payload: Any) -> Dict[str, Any]:
    """L5_POLICY_ENGINE: PIPEDA compliance checks (Canada, Phase 1)."""
    if not isinstance(payload, dict):
        return _block("INVALID_PAYLOAD", "Payload must be a JSON object.", [])

    policies_applied: List[str] = []

    # @req SRS-L5-001 -- audio must have been purged by L0
    if payload.get("audio_retained") in _AUDIO_RETAINED_TRUTHY:
        return _block(
            "PIPEDA_AUDIO_NOT_PURGED",
            "PIPEDA violation: audio_retained=True. "
            "Audio must be purged after transcription (PIPEDA Principle 7 — Safeguards).",
            ["PIPEDA-P7-safeguards"],
        )
    policies_applied.append("PIPEDA-P7-safeguards:audio_purge_verified")

    # @req SRS-L5-002 -- purpose limitation
    purpose = payload.get("purpose", "medical_documentation")
    if purpose not in ALLOWED_PURPOSES:
        return _block(
            "PIPEDA_PURPOSE_VIOLATION",
            f"PIPEDA violation: purpose '{purpose}' not allowed "
            f"(PIPEDA Principle 5 — Limiting Use). Allowed: {sorted(ALLOWED_PURPOSES)}",
            ["PIPEDA-P5-limiting-use"],
        )
    policies_applied.append("PIPEDA-P5-limiting-use:purpose_verified")

    # @req SRS-L5-003 -- PII scan on transcript fields (flag, not block)
    pii_flags = _scan_pii(payload)
    policies_applied.append("PIPEDA-P7-safeguards:pii_scan_complete")

    # @req SRS-L5-004 -- consent warning only — never blocks
    # Warning-only by design: clinical consent assumed in Phase 1 workflow.
    warnings = []
    if "consent_given" in payload and not payload["consent_given"]:
        warnings.append(
            "PIPEDA Principle 3 (Consent): consent_given=False. "
            "Ensure patient consent is documented in clinic records before filing."
        )
    policies_applied.append("PIPEDA-P3-consent:checked")

    # FIX F2 (MV-CR-001): whitelist — only _DOWNSTREAM_FIELDS propagate
    out = {k: v for k, v in payload.items() if k in _DOWNSTREAM_FIELDS}
    out["pipeda_compliant"] = True
    out["policies_applied"] = policies_applied
    out["pii_flags"] = pii_flags
    if warnings:
        out["pipeda_warnings"] = warnings

    return {"ok": True, "stage": "L5_POLICY_ENGINE", "data": out}


def _scan_pii(payload: Dict) -> List[str]:
    # Pattern-based scan only — does not detect names, DOB, MRN, or free-text identifiers.
    translation = payload.get("translation", "")
    if isinstance(translation, dict):
        # NC-004 (CA-013): L1b returns {"translated_text": "...", "confidence": ...}
        # Extract string values explicitly instead of str(dict) repr.
        translation_text = " ".join(str(v) for v in translation.values())
    else:
        translation_text = str(translation)
    text = " ".join([
        str(payload.get("original_text", "")),
        str(payload.get("transcript", "")),
        str(payload.get("processed_text", "")),
        translation_text,
    ])
    flags = [label for label, pattern in _PII_PATTERNS.items() if pattern.search(text)]
    flags += [label for label, pattern in _VN_PII_PATTERNS.items() if pattern.search(text)]
    return flags


def _block(error: str, message: str, policies: List[str]) -> Dict[str, Any]:
    return {
        "ok": False,
        "stage": "L5_POLICY_ENGINE",
        "error": error,
        "message": message,
        "policies_applied": policies,
    }
