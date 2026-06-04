# src/pipeline/p1_processing/l2_enforcer.py
# Stage:    L2_ENFORCER
# Role:     Validate WER, translation confidence, drug name integrity, silence ratio.
#           Reject non-compliant. Flag (never auto-correct) suspicious drug names.
# Req:      SRS-L2-001 -- see docs/cl08_operation/SRS.md
# FID:      DS-FID-001 | v1.0
# Policy:   AI_POLICY.md §3 — Medical Term Integrity
# Standard: ISO/IEC 42001:2023 Clause 8.5
# Version:  v1.3 -- MV-FID-013: bare drug name detection (T-008, CA-006 F6 closure)

import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Tuple

WER_REJECT_THRESHOLD = 0.55   # > 55% WER → reject (Whisper logprob proxy; 0.45 = good transcript)
WER_FLAG_THRESHOLD = 0.35     # > 35% WER → flag for doctor attention
SILENCE_REJECT_THRESHOLD = 0.95   # > 95% silence → reject
TRANSLATION_CONFIDENCE_MIN = 0.60  # below this → flag low translation quality

# Known drug names — fuzzy-match incoming terms against this list
_KNOWN_DRUGS = [
    "lisinopril", "metformin", "amlodipine", "atorvastatin", "amoxicillin",
    "omeprazole", "salbutamol", "paracetamol", "ibuprofen", "aspirin",
    "warfarin", "losartan", "ramipril", "furosemide", "metoprolol",
    "simvastatin", "pantoprazole", "sertraline", "escitalopram", "fluoxetine",
    "prednisolone", "dexamethasone", "insulin", "glipizide", "empagliflozin",
    "clopidogrel", "digoxin", "spironolactone", "hydrochlorothiazide",
]

_DRUG_TERM_RE = re.compile(
    r'\b([A-Za-z][A-Za-z0-9\-]+)\s+(\d+(?:\.\d+)?)\s*(mg|mcg|ml|g|IU|units?)\b',
    re.IGNORECASE,
)

# MV-FID-013: bare word pattern for drug names without dose unit (min 6 chars)
_BARE_DRUG_WORD_RE = re.compile(r'\b([A-Za-z][A-Za-z0-9\-]{5,})\b', re.IGNORECASE)
_BARE_DRUG_SCORE_MIN = 0.88  # fuzzy-match threshold for bare drug flagging


def _safe_float(value: Any, default: float) -> float:
    """CA-006 F3: safe numeric conversion — returns default on ValueError/TypeError."""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        raise


# @req SRS-L2-001 -- Validate schema. Reject non-compliant payload.
def handle(payload: Any) -> Dict[str, Any]:
    """L2_ENFORCER: WER check, silence check, drug name validation."""
    if not isinstance(payload, dict):
        return _reject("INVALID_PAYLOAD", "Payload must be a JSON object.")

    text = payload.get("processed_text") or payload.get("original_text") or ""
    translation = payload.get("translation", {})
    flags: List[Dict] = []

    # CA-006 F3: guard float conversions — reject on non-numeric input
    try:
        wer = float(payload.get("wer_estimate", 0.0))
    except (ValueError, TypeError):
        return _reject("INVALID_PAYLOAD", "wer_estimate must be numeric.")

    try:
        silence_ratio = float(payload.get("silence_ratio", 0.0))
    except (ValueError, TypeError):
        return _reject("INVALID_PAYLOAD", "silence_ratio must be numeric.")

    # Silence check
    if silence_ratio >= SILENCE_REJECT_THRESHOLD:
        return _reject("NO_SPEECH_DETECTED",
                       f"Audio is {silence_ratio*100:.0f}% silence — no usable speech detected.",
                       action="REQUEST_RERECORD")

    # WER check
    if wer > WER_REJECT_THRESHOLD:
        return _reject("WER_TOO_HIGH",
                       f"WER estimate {wer:.0%} exceeds rejection threshold {WER_REJECT_THRESHOLD:.0%}.",
                       action="REQUEST_RERECORD")
    if wer > WER_FLAG_THRESHOLD:
        flags.append({"code": "HIGH_WER", "wer": wer,
                      "message": f"WER {wer:.0%} — transcript may contain errors."})

    # Translation confidence check
    if translation:
        try:
            trans_conf = float(translation.get("confidence", 1.0))
        except (ValueError, TypeError):
            trans_conf = 0.0  # CA-006 F3: unknown confidence → flag as low
        if trans_conf < TRANSLATION_CONFIDENCE_MIN:
            flags.append({"code": "LOW_TRANSLATION_CONFIDENCE", "confidence": trans_conf,
                          "message": "Translation confidence low — review Vietnamese terms carefully."})

    # Drug name integrity check (with-dose + bare)
    drug_flags = check_drug_names(text)
    drug_flags.extend(check_bare_drug_names(text))
    flags.extend(drug_flags)

    result_data = {
        **payload,
        "enforcement_flags": flags,
        "wer_ok": wer <= WER_REJECT_THRESHOLD,  # CA-006 F2: True = passed L2 reject gate
        "drug_flags": drug_flags,
    }

    return {"ok": True, "stage": "L2_ENFORCER", "data": result_data}


def check_drug_names(text: str) -> List[Dict]:
    """
    Flag (never auto-correct) drug names that look like misspellings.
    Returns list of flag dicts for doctor review.
    """
    flags = []
    for m in _DRUG_TERM_RE.finditer(text):
        term = m.group(1).lower()
        best_match, score = _best_drug_match(term)
        if score < 1.0 and score >= 0.75:
            flags.append({
                "code": "DRUG_NAME_SUSPECT",
                "heard": m.group(1),
                "suggested": best_match,
                "confidence": round(score, 2),
                "message": f"Heard: '{m.group(1)}' → Did you mean: '{best_match}'?",
                "action": "FLAG_FOR_REVIEW",
            })
    return flags


def check_bare_drug_names(text: str) -> List[Dict]:
    """
    Flag drug names mentioned without a dose unit (MV-FID-013, CA-006 F6).
    Skips positions already covered by _DRUG_TERM_RE to avoid double-flagging.
    """
    # Mark character positions covered by drug+dose matches
    dosed_spans: set = set()
    for m in _DRUG_TERM_RE.finditer(text):
        dosed_spans.update(range(m.start(1), m.end(1)))

    flags = []
    for m in _BARE_DRUG_WORD_RE.finditer(text):
        if any(pos in dosed_spans for pos in range(m.start(), m.end())):
            continue
        term = m.group(1)
        best_match, score = _best_drug_match(term.lower())
        if score >= _BARE_DRUG_SCORE_MIN:
            flags.append({
                "code": "DRUG_NO_DOSE",
                "heard": term,
                "suggested": best_match,
                "confidence": round(score, 2),
                "message": f"Drug name '{term}' mentioned without dose — verify dose in notes.",
                "action": "FLAG_FOR_REVIEW",
            })
    return flags


def _best_drug_match(term: str) -> Tuple[str, float]:
    """Fuzzy-match a term against the known drug list. Returns (best_match, score)."""
    # CA-006 F1: initialize to 0.0 (not 1.0) — 1.0 sentinel caused exact matches to be overwritten
    best, best_score = term, 0.0
    for known in _KNOWN_DRUGS:
        score = SequenceMatcher(None, term.lower(), known.lower()).ratio()
        if score > best_score:
            best, best_score = known, score
    return best, best_score


def _reject(error: str, message: str, action: str = "REJECT") -> Dict[str, Any]:
    return {"ok": False, "stage": "L2_ENFORCER", "error": error,
            "message": message, "action": action}
