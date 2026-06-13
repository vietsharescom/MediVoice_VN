# L1b — Drug Name Correction v2
# Input: raw transcript | Output: transcript với tên thuốc đã chuẩn hóa
# Rule: tên INN giữ nguyên tiếng Anh — KHÔNG dịch sang tiếng Việt
# FROZEN PIPELINE LAYER
# FID-VN-008 — APPROVED 2026-06-10

from __future__ import annotations
import json
import logging
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from rapidfuzz import fuzz, process as rf_process

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "reference"

# Configurable thresholds (Copilot: tune via pilot data, not hardcoded logic)
# STRICT raised 82→88: "soát"→Iron scored 86% (silent FP on clinical text) — CE-103 fix
DRUG_FUZZY_CUTOFF_STRICT: int = 88   # auto-accept (≥88% = high confidence, no flag)
DRUG_FUZZY_CUTOFF_FLAG:   int = 70   # flag for BS review (≥70% <88% = LOW_CONFIDENCE)

# Layer 3b RAG thresholds — FID-VN-011, calibrate via pilot data
RAG_ACCEPT_THRESHOLD: float = 0.68   # auto-accept with LOW_CONFIDENCE flag
RAG_FLAG_THRESHOLD:   float = 0.55   # flag only, require BS confirm

# Filler words PhoWhisper inserts — stripped before window matching
_FILLER_WORDS = {"ừm", "ừ", "ờ", "à", "ơ", "ê", "thì", "là", "mà", "thôi", "nhé"}


@dataclass
class DrugMatch:
    inn: str
    original_text: str
    word_position: int
    confidence: float           # 0.0–1.0
    match_layer: int            # 1=exact, 2=fuzzy, 3=context
    flagged_for_review: bool
    flag_reason: str            # "" | "LOW_CONFIDENCE" | "AMBIGUOUS" | "DOSE_OUT_OF_RANGE" | "CLASS_MISMATCH"
    severity: str               # "" | "LOW" | "MEDIUM" | "HIGH"
    fuzzy_score: float = 0.0   # raw RapidFuzz score; 0.0 for Layer 1


# ─── DB loading ──────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_drug_db() -> dict:
    v200 = DATA_DIR / "drug_db_v200.json"
    legacy = DATA_DIR / "drug_db.json"
    path = v200 if v200.exists() else legacy
    if path == legacy:
        logger.warning("drug_db_v200.json not found — falling back to drug_db.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _normalize(text: str) -> str:
    """Lowercase + strip Vietnamese diacritics."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# ─── Phonological variant generation (FID-VN-019, CT-042) ─────────────────────
# Vietnamese-English contrastive phonology — see fids/FID-VN-019.md WHY for
# academic sources. Rules 1-4 below operate on already-_normalize()'d aliases
# (lowercase, diacritics stripped — except "đ", which NFKD does not decompose).

# Rule 1: aspiration neutralization onset swap (b/p, d/t, g/k/c).
# "đ" -> "t" per FID-VN-019 example ("đa" -> "ta", Metronidazole garble).
_ASPIRATION_MAP: dict[str, tuple[str, ...]] = {
    "b": ("p",), "p": ("b",),
    "d": ("t",), "t": ("d",),
    "đ": ("t",),
    "g": ("k",), "c": ("k",), "k": ("g", "c"),
}

# Rule 2: coda restriction — drop final consonant if it's a voiced obstruent or
# "l" (not in Vietnamese's valid 6-consonant coda set {p,t,k,c,m,n,ng,nh}).
_CODA_DROP_SET = frozenset({"l", "z", "v", "d", "đ"})

# Rule 8: common Vietnamese clinical words — any generated variant containing
# one of these tokens is dropped (false-positive guard, CONS-20260612-001 Round 3).
_PHON_BLACKLIST: frozenset[str] = frozenset({
    "co", "khong", "đau", "met", "ve", "voi", "nay", "la", "ma", "thi",
    "cho", "cua", "se", "roi", "chua", "con", "nua", "them", "it", "nhieu",
    "hay", "nen", "phai", "đuoc", "bi", "sau", "truoc", "trong", "ngoai",
    "tren", "duoi", "khi", "neu", "vi", "tai", "di", "ngoi", "nam", "an",
    "uong", "ngu", "ngay", "vay",
})

_PHON_MIN_VARIANT_LEN = 3  # Rule 7: skip variants <3 chars (excl. spaces)


def _phon_syllable_onset_variants(syllable: str, region: str | None) -> set[str]:
    """Rules 1/3/4 — onset swaps for a single syllable. region: north/central/south/None."""
    variants: set[str] = set()
    if not syllable:
        return variants
    first = syllable[0]

    # Rule 1: aspiration onset swap
    for repl in _ASPIRATION_MAP.get(first, ()):
        variants.add(repl + syllable[1:])

    # Rule 3: "th" -> "t"/"d" onset
    if syllable.startswith("th"):
        variants.add("t" + syllable[2:])
        variants.add("d" + syllable[2:])

    # Rule 4: r/l/n onset swap, split by region (CONS-20260612-001)
    if first in ("l", "n") and region in (None, "north"):
        variants.add(("n" if first == "l" else "l") + syllable[1:])
    if first == "r" and region in (None, "central", "south"):
        variants.add("l" + syllable[1:])
        variants.add("z" + syllable[1:])

    variants.discard(syllable)
    return variants


def _phonological_variants(alias: str, region: str | None = None) -> set[str]:
    """
    Generate Vietnamese phonological spelling variants of an already-normalized
    drug alias (FID-VN-019 v3, rules 1-4 + guards 5-8).

    region: "north"/"central"/"south" for phonetic_variants entries (drives
    Rule 4 split), or None for brands/name_variants (all regions apply).
    """
    tokens = alias.split(" ")
    multi_syllable = len(tokens) >= 2
    # Rule 5: limit to the first and last syllable (same syllable if single-token alias)
    target_indices = {0, len(tokens) - 1}

    results: set[str] = set()
    for idx in target_indices:
        syllable = tokens[idx]
        onset_variants = {syllable} | _phon_syllable_onset_variants(syllable, region)
        for onset_variant in onset_variants:
            candidates = {onset_variant}
            # Rule 2: coda restriction (multi-syllable aliases only — CONSTRAINT 1)
            if (
                multi_syllable
                and len(onset_variant) > 1
                and onset_variant[-1] in _CODA_DROP_SET
            ):
                candidates.add(onset_variant[:-1])
            for candidate in candidates:
                if candidate == syllable:
                    continue
                new_tokens = list(tokens)
                new_tokens[idx] = candidate
                results.add(" ".join(new_tokens))

    # Rule 7 (min length) + Rule 8 (blacklist)
    filtered: set[str] = set()
    for variant in results:
        variant_tokens = variant.split(" ")
        if len("".join(variant_tokens)) < _PHON_MIN_VARIANT_LEN:
            continue
        if any(t in _PHON_BLACKLIST for t in variant_tokens):
            continue
        filtered.add(variant)
    return filtered


def _add_phon_alias(alias_map: dict[str, str], key: str, inn: str) -> None:
    """Insert a generated phonological alias, skipping on INN collision (R-PHON-02)."""
    existing = alias_map.get(key)
    if existing is not None and existing != inn:
        logger.debug(
            "Phonological alias collision: %r already maps to %s, skip %s",
            key, existing, inn,
        )
        return
    alias_map[key] = inn


# ─── Alias map builder ────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _build_alias_map() -> dict[str, str]:
    """
    Build alias → INN map from drug_db_v200:
      brands[] + phonetic_variants{north/central/south}[] + INN itself.
    """
    db = _load_drug_db()
    alias_map: dict[str, str] = {}
    for inn, entry in db.get("by_inn", {}).items():
        alias_map[_normalize(inn)] = inn
        for brand in entry.get("brands", []):
            normalized = _normalize(brand)
            alias_map[normalized] = inn
            for variant in _phonological_variants(normalized):
                _add_phon_alias(alias_map, variant, inn)
        for variant in entry.get("name_variants", []):
            normalized = _normalize(variant)
            alias_map[normalized] = inn
            for phon_variant in _phonological_variants(normalized):
                _add_phon_alias(alias_map, phon_variant, inn)
        # v200: phonetic_variants per region
        # Min 3 syllables (>=2 spaces): 2-syllable prefixes like "ga ba", "am lo"
        # are too generic and match common Vietnamese words in clinical text.
        pv = entry.get("phonetic_variants", {})
        for _region, variants in pv.items():
            for v in variants:
                normalized = _normalize(v)
                # Skip 1- and 2-syllable phonetic prefixes (too generic, match
                # common Vietnamese words) — UNLESS the 2-word phrase is long
                # enough (>=9 chars) to be a distinctive English-loanword garble
                # (e.g. "parasyte mode" for Paracetamol, CT-049).
                if normalized.count(" ") < 2 and len(normalized) < 9:
                    continue
                alias_map[normalized] = inn
                for phon_variant in _phonological_variants(normalized, region=_region):
                    _add_phon_alias(alias_map, phon_variant, inn)
    return alias_map


def _get_alias_map() -> dict[str, str]:
    return _build_alias_map()


# ─── Session-filtered alias map ───────────────────────────────────────────────

def _build_filtered_alias_map(session_context: dict) -> dict[str, str]:
    """
    PRE-FILTER: build alias_map restricted to drugs compatible with
    session_context diagnosis + drug_class_context.
    Falls back to full map if context insufficient.
    [ChatGPT: constrained search space reduces false positive ~70%]
    """
    drug_class_ctx = set(session_context.get("drug_class_context", []))
    diagnosis = _normalize(session_context.get("diagnosis", ""))
    icd10 = session_context.get("diagnosis_icd10", "")

    full = _get_alias_map()
    if not drug_class_ctx and not diagnosis and not icd10:
        return full

    db = _load_drug_db()
    allowed_inns: set[str] = set()
    for inn, entry in db.get("by_inn", {}).items():
        dc = entry.get("drug_class", "")
        compat = entry.get("compatible_diagnoses", [])
        # match by drug_class
        if dc and dc in drug_class_ctx:
            allowed_inns.add(inn)
            continue
        # match by diagnosis text overlap
        if diagnosis and any(diagnosis in _normalize(d) or _normalize(d) in diagnosis for d in compat):
            allowed_inns.add(inn)

    if not allowed_inns:
        return full  # context too narrow → fallback safe

    return {alias: inn for alias, inn in full.items() if inn in allowed_inns}


# ─── Safety engine ────────────────────────────────────────────────────────────

def _run_safety(match: DrugMatch, transcript_fragment: str, session_context: dict | None) -> DrugMatch:
    """
    Layer 4: validate dose + class coherence. Never overrides match, only adds flags.
    [ChatGPT severity scoring; Copilot: dose_range skip when {0,0}]
    """
    db = _load_drug_db()
    entry = db.get("by_inn", {}).get(match.inn, {})
    dose_range = entry.get("dose_range", {"min": 0, "max": 0})

    # Extract dose from fragment (simple heuristic: number before mg/mcg)
    import re
    dose_val: float | None = None
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*mg", transcript_fragment, re.IGNORECASE)
    if m:
        try:
            dose_val = float(m.group(1).replace(",", "."))
        except ValueError:
            pass

    if dose_val is not None and dose_range["min"] > 0:
        if dose_val < dose_range["min"] or dose_val > dose_range["max"]:
            match.flagged_for_review = True
            match.flag_reason = "DOSE_OUT_OF_RANGE"
            match.severity = "HIGH"
            logger.warning("Safety flag: %s %.1fmg out of range [%s, %s]",
                           match.inn, dose_val, dose_range["min"], dose_range["max"])

    # Class mismatch check
    if session_context and not match.flagged_for_review:
        drug_class_ctx = set(session_context.get("drug_class_context", []))
        dc = entry.get("drug_class", "")
        if drug_class_ctx and dc and dc not in drug_class_ctx:
            match.flagged_for_review = True
            match.flag_reason = "CLASS_MISMATCH"
            match.severity = "MEDIUM"

    return match


# ─── Core matching ────────────────────────────────────────────────────────────

def _match_window(words: list[str], i: int, alias_map: dict[str, str]) -> tuple[str | None, int, float]:
    """Layer 1 exact match. Returns (inn, n_words_consumed, confidence)."""
    # Window up to 6 words: drug_db_v200 phonetic_variants for multi-syllable
    # English drug names (e.g. "a zi thro my xin" for Azithromycin) are
    # 5-6 words — without this they can never match (CT-027 follow-up).
    for n in (6, 5, 4, 3, 2, 1):
        if i + n > len(words):
            continue
        candidate = " ".join(words[i:i+n])
        key = _normalize(candidate)
        if key in alias_map:
            return alias_map[key], n, 1.0
    return None, 0, 0.0


def _fuzzy_match(token: str, alias_map: dict[str, str]) -> tuple[str | None, float, bool]:
    """
    Layer 2 fuzzy match with Ambiguity Gate.
    Returns (inn, confidence, is_ambiguous).
    [ChatGPT: top2 gap check; Copilot: configurable cutoff]
    """
    keys = list(alias_map.keys())
    if not keys:
        return None, 0.0, False

    results = rf_process.extract(
        token,
        keys,
        scorer=fuzz.token_sort_ratio,
        limit=2,
        score_cutoff=DRUG_FUZZY_CUTOFF_FLAG,
    )
    if not results:
        return None, 0.0, False

    best_key, best_score, _ = results[0]
    best_inn = alias_map[best_key]

    # Ambiguity Gate: if 2nd candidate close → flag ambiguous
    if len(results) >= 2:
        second_key, second_score, _ = results[1]
        second_inn = alias_map[second_key]
        if second_inn != best_inn and (best_score - second_score) < 8:
            return best_inn, (best_score / 100) * 0.7, True  # ambiguous

    return best_inn, best_score / 100, False


def _rag_fallback_match(
    token: str,
    chan_doan_context: str,
    rag_collection,
    embed_model,
    drug_db: dict,
) -> tuple[str | None, float]:
    """
    Layer 3b: hybrid RAG fallback when alias + fuzzy + prefix miss.
    Returns (inn, combined_score) or (None, 0.0).
    FID-VN-011: 0.65×phonetic + 0.35×semantic.
    """
    try:
        from .drug_rag import hybrid_query_drug
        results = hybrid_query_drug(
            token, chan_doan_context, rag_collection, drug_db,
            embed_model_instance=embed_model, k=1,
        )
        if results and results[0]["score"] >= RAG_FLAG_THRESHOLD:
            return results[0]["inn"], results[0]["score"]
    except Exception as exc:
        logger.debug("RAG fallback error: %s", exc)
    return None, 0.0


def _context_prefix_match(token: str, alias_map: dict[str, str]) -> str | None:
    """
    Layer 3: prefix match within filtered alias_map.
    Returns INN only if exactly 1 unique candidate (no ambiguity).
    """
    norm = _normalize(token)
    if len(norm) < 3:
        return None
    candidates: set[str] = set()
    for key, inn in alias_map.items():
        if key.startswith(norm):
            candidates.add(inn)
    if len(candidates) == 1:
        return next(iter(candidates))
    return None


# ─── Public API — backward compat (unchanged) ─────────────────────────────────

def _build_alias_map_legacy() -> dict[str, str]:
    """Legacy builder for correct_drug_names() — identical to v1 behavior."""
    db = _load_drug_db()
    alias_map: dict[str, str] = {}
    for inn, entry in db.get("by_inn", {}).items():
        alias_map[_normalize(inn)] = inn
        for brand in entry.get("brands", []):
            alias_map[_normalize(brand)] = inn
        for variant in entry.get("name_variants", []):
            alias_map[_normalize(variant)] = inn
    return alias_map


_LEGACY_MAP: dict[str, str] | None = None


def _get_legacy_map() -> dict[str, str]:
    global _LEGACY_MAP
    if _LEGACY_MAP is None:
        _LEGACY_MAP = _build_alias_map_legacy()
    return _LEGACY_MAP


def correct_drug_names(transcript: str) -> str:
    """
    [BACKWARD COMPAT — unchanged signature]
    Exact alias match only (Layer 1 behavior).
    """
    if not transcript:
        return transcript

    alias_map = _get_legacy_map()
    words = transcript.split()
    result = []
    i = 0
    while i < len(words):
        matched = False
        for n in (4, 3, 2, 1):
            if i + n > len(words):
                continue
            candidate = " ".join(words[i:i+n])
            key = _normalize(candidate)
            if key in alias_map:
                result.append(alias_map[key])
                i += n
                matched = True
                break
        if not matched:
            result.append(words[i])
            i += 1
    return " ".join(result)


def extract_drug_candidates(transcript: str) -> list[dict]:
    """
    [BACKWARD COMPAT — unchanged signature]
    Find drug candidates via exact match.
    """
    alias_map = _get_legacy_map()
    candidates = []
    words = transcript.split()
    i = 0
    while i < len(words):
        for n in (4, 3, 2, 1):
            if i + n > len(words):
                continue
            candidate = " ".join(words[i:i+n])
            key = _normalize(candidate)
            if key in alias_map:
                candidates.append({
                    "inn": alias_map[key],
                    "original_text": candidate,
                    "word_position": i,
                })
                i += n
                break
        else:
            i += 1
    return candidates


# ─── v2 API ───────────────────────────────────────────────────────────────────

def correct_drug_names_v2(
    transcript: str,
    session_context: dict | None = None,
    *,
    rag_collection=None,
    embed_model=None,
) -> tuple[str, list[DrugMatch]]:
    """
    4-layer drug name correction with fuzzy matching, context-aware filtering,
    and Safety Rule Engine.

    Returns: (corrected_transcript, list[DrugMatch])
    DrugMatch contains audit fields: confidence, layer, flagged, severity.

    [FID-VN-008 | APPROVED 2026-06-10]
    """
    if not transcript:
        return transcript, []

    # Pre-filter alias map by session context
    if session_context:
        alias_map = _build_filtered_alias_map(session_context)
    else:
        alias_map = _get_alias_map()

    full_alias = _get_alias_map()  # always available for L2 fallback

    # Strip filler words for matching window, keep original for output
    words_raw = transcript.split()
    words = [w for w in words_raw if w.lower() not in _FILLER_WORDS]

    result_words = list(words_raw)  # will replace in place
    matches: list[DrugMatch] = []

    i = 0
    raw_i = 0  # track position in words_raw for result replacement
    while i < len(words):
        # skip filler words in result_words position tracking
        while raw_i < len(words_raw) and words_raw[raw_i].lower() in _FILLER_WORDS:
            raw_i += 1

        # ── Layer 1: Exact match ──────────────────────────────────────────
        inn, n_consumed, conf = _match_window(words, i, alias_map)
        if inn is None:
            inn, n_consumed, conf = _match_window(words, i, full_alias)

        if inn is not None:
            original = " ".join(words[i:i+n_consumed])
            dm = DrugMatch(
                inn=inn, original_text=original, word_position=raw_i,
                confidence=1.0, match_layer=1,
                flagged_for_review=False, flag_reason="", severity="",
                fuzzy_score=0.0,
            )
            fragment = " ".join(words[i:min(i+n_consumed+3, len(words))])
            dm = _run_safety(dm, fragment, session_context)
            matches.append(dm)
            # Replace in result
            for j in range(n_consumed):
                if raw_i + j < len(result_words):
                    result_words[raw_i + j] = inn if j == 0 else ""
            i += n_consumed
            raw_i += n_consumed
            continue

        # ── Layer 2: Fuzzy match ──────────────────────────────────────────
        token_normalized = _normalize(words[i])
        # Min length per n: single word ≥6 chars, 2-word ≥9 chars, 3-word ≥12 chars
        # Prevents common Vietnamese words (3-5 chars) from matching drug names
        _min_len = {1: 6, 2: 9, 3: 12}
        if len(token_normalized) >= 6:
            # Try multi-word token (2-3 words) first
            for n in (3, 2, 1):
                if i + n > len(words):
                    continue
                # Don't greedily consume windows where a downstream word is an exact
                # Layer 1 match — let Layer 1 catch it at its own position (CE-103 fix)
                if n > 1 and any(
                    _normalize(words[i + k]) in full_alias
                    for k in range(1, n)
                ):
                    continue
                multi_token = _normalize(" ".join(words[i:i+n]))
                # Enforce minimum length by n to avoid random phrase false positives
                if len(multi_token.replace(" ", "")) < _min_len[n]:
                    continue
                fuzzy_map = alias_map if alias_map else full_alias
                fuzz_inn, fuzz_conf, is_ambiguous = _fuzzy_match(multi_token, fuzzy_map)
                if fuzz_inn is not None and fuzz_conf >= DRUG_FUZZY_CUTOFF_FLAG / 100:
                    original = " ".join(words[i:i+n])
                    flag = is_ambiguous or fuzz_conf < DRUG_FUZZY_CUTOFF_STRICT / 100
                    reason = "AMBIGUOUS" if is_ambiguous else ("LOW_CONFIDENCE" if flag else "")
                    severity = "HIGH" if is_ambiguous else ("LOW" if flag else "")
                    dm = DrugMatch(
                        inn=fuzz_inn, original_text=original, word_position=raw_i,
                        confidence=fuzz_conf, match_layer=2,
                        flagged_for_review=flag, flag_reason=reason, severity=severity,
                        fuzzy_score=fuzz_conf * 100,
                    )
                    fragment = " ".join(words[i:min(i+n+3, len(words))])
                    dm = _run_safety(dm, fragment, session_context)
                    matches.append(dm)
                    for j in range(n):
                        if raw_i + j < len(result_words):
                            result_words[raw_i + j] = fuzz_inn if j == 0 else ""
                    i += n
                    raw_i += n
                    break
            else:
                # ── Layer 3: Context prefix match ─────────────────────────
                ctx_inn = _context_prefix_match(words[i], alias_map)
                if ctx_inn:
                    dm = DrugMatch(
                        inn=ctx_inn, original_text=words[i], word_position=raw_i,
                        confidence=0.6, match_layer=3,
                        flagged_for_review=True, flag_reason="LOW_CONFIDENCE", severity="LOW",
                        fuzzy_score=0.0,
                    )
                    fragment = " ".join(words[i:min(i+4, len(words))])
                    dm = _run_safety(dm, fragment, session_context)
                    matches.append(dm)
                    result_words[raw_i] = ctx_inn
                    i += 1
                    raw_i += 1
                elif rag_collection is not None and embed_model is not None:
                    # ── Layer 3b: RAG fallback ─────────────────────────────
                    # Try 2-3 word window first, then single word
                    rag_token = " ".join(words[i:min(i+3, len(words))])
                    chan_doan = (session_context or {}).get("diagnosis", "")
                    rag_inn, rag_score = _rag_fallback_match(
                        rag_token, chan_doan, rag_collection, embed_model,
                        _load_drug_db(),
                    )
                    if rag_inn:
                        flag = rag_score < RAG_ACCEPT_THRESHOLD
                        confidence = round(rag_score, 3)
                        dm = DrugMatch(
                            inn=rag_inn, original_text=rag_token, word_position=raw_i,
                            confidence=confidence, match_layer=3,
                            flagged_for_review=True, flag_reason="LOW_CONFIDENCE", severity="LOW",
                            fuzzy_score=round(rag_score * 100, 1),
                        )
                        fragment = " ".join(words[i:min(i+4, len(words))])
                        dm = _run_safety(dm, fragment, session_context)
                        matches.append(dm)
                        result_words[raw_i] = rag_inn
                    i += 1
                    raw_i += 1
                else:
                    i += 1
                    raw_i += 1
        else:
            i += 1
            raw_i += 1

    # Clean up empty strings from multi-word replacements
    corrected = " ".join(w for w in result_words if w)

    # Audit log
    for dm in matches:
        logger.info(
            "DrugMatch layer=%d inn=%s orig=%r conf=%.2f flag=%s reason=%s severity=%s score=%.1f",
            dm.match_layer, dm.inn, dm.original_text,
            dm.confidence, dm.flagged_for_review, dm.flag_reason, dm.severity, dm.fuzzy_score,
        )

    return corrected, matches
