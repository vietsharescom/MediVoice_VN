# src/core/l1c_phobert.py
# L1c PhoBERT NER — lazy load, parallel hybrid supplement
# FID-VN-009 | APPROVED 2026-06-10 | CONS-20260610-003
# FROZEN PIPELINE LAYER

from __future__ import annotations
import re
from functools import lru_cache
from pathlib import Path

# ─── Configuration ────────────────────────────────────────────────────────────

MODEL_PATH = Path("models/ner_phobert/best")

# Entity-type-specific confidence thresholds (CONS-20260610-003 synthesis)
PHOBERT_CONFIDENCE_HIGH: float = 0.85   # MEDICATION, DOSE, FREQUENCY, DURATION
PHOBERT_CONFIDENCE_STD:  float = 0.75   # SYMPTOM, FOLLOWUP
PHOBERT_CONFIDENCE_MIN:  float = 0.60   # discard if below (any entity)

# R-009-12: conditional FOLLOWUP patterns — do not auto-fill tai_kham
_RE_CONDITIONAL_FOLLOWUP = re.compile(
    r"\b(nếu|khi\s*cần|khi\s*có|nếu\s*không|nếu\s*còn|không\s*đỡ|không\s*khỏi)\b",
    re.IGNORECASE,
)


@lru_cache(maxsize=1)
def _load_phobert_pipeline():
    """Lazy load PhoBERT pipeline — first call ~5-10s on CPU, then cached."""
    from transformers import pipeline as hf_pipeline
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"PhoBERT model not found: {MODEL_PATH}")
    return hf_pipeline(
        "token-classification",
        model=str(MODEL_PATH),
        aggregation_strategy="simple",
        device=-1,  # CPU always (Phase 0 offline, no GPU)
    )


def predict_entities(transcript: str) -> list[dict]:
    """Returns HF pipeline output: [{entity_group, score, word, start, end}]"""
    pipe = _load_phobert_pipeline()
    return pipe(transcript)


def normalize_symptom(text: str) -> str:
    """Lowercase + normalize whitespace for dedup comparison."""
    return re.sub(r"\s+", " ", text.lower().strip())


def bio_to_updates(
    predictions: list[dict],
    transcript: str,
) -> tuple[dict, list[str]]:
    """
    Map PhoBERT BIO predictions → field update dict + VITAL log.

    Returns:
        updates: {
            "don_thuoc_supplement": [...],
            "trieu_chung_add": [...],
            "tai_kham_fill": str | None,
        }
        vital_detected: list of VITAL spans (Copilot: log only, not chart)
    """
    updates: dict = {
        "don_thuoc_supplement": [],
        "trieu_chung_add": [],
        "tai_kham_fill": None,
    }
    vital_detected: list[str] = []

    current_medication: dict | None = None

    for pred in predictions:
        entity_group: str = pred.get("entity_group", "")
        score: float = pred.get("score", 0.0)
        word: str = pred.get("word", "").strip()

        if not word:
            continue

        # VITAL — log to meta only, never fill MedicalEntities (Copilot requirement)
        if entity_group == "VITAL":
            vital_detected.append(word)
            current_medication = None
            continue

        # Hard discard below minimum threshold
        if score < PHOBERT_CONFIDENCE_MIN:
            if entity_group == "MEDICATION":
                current_medication = None
            continue

        if entity_group == "MEDICATION":
            if score >= PHOBERT_CONFIDENCE_HIGH:
                current_medication = {
                    "inn": word,
                    "ham_luong": "",
                    "so_lan_ngay": "",
                    "so_ngay": 0,
                    "duong_dung": "uống",
                    "_phobert_score": score,
                }
                updates["don_thuoc_supplement"].append(current_medication)
            else:
                # Below PHOBERT_CONFIDENCE_HIGH but above MIN → discard MEDICATION (safety)
                current_medication = None

        elif entity_group in ("DOSE", "FREQUENCY", "DURATION"):
            if score < PHOBERT_CONFIDENCE_HIGH or current_medication is None:
                continue
            if entity_group == "DOSE":
                current_medication["ham_luong"] = word
            elif entity_group == "FREQUENCY":
                current_medication["so_lan_ngay"] = word
            elif entity_group == "DURATION":
                m = re.search(r"(\d+)", word)
                if m:
                    current_medication["so_ngay"] = int(m.group(1))

        elif entity_group == "SYMPTOM":
            if score >= PHOBERT_CONFIDENCE_STD:
                updates["trieu_chung_add"].append(word)
                current_medication = None

        elif entity_group == "FOLLOWUP":
            if score >= PHOBERT_CONFIDENCE_STD and updates["tai_kham_fill"] is None:
                # R-009-12: reject conditional FOLLOWUP ("nếu không đỡ tái khám")
                start = pred.get("start", 0)
                ctx_start = max(0, start - 60)
                ctx_end = min(len(transcript), start + len(word) + 20)
                context = transcript[ctx_start:ctx_end]
                if not _RE_CONDITIONAL_FOLLOWUP.search(context):
                    updates["tai_kham_fill"] = word
            current_medication = None

        else:
            current_medication = None

    return updates, vital_detected


def has_coverage_gap(entities: object) -> bool:
    """True if any contextual field is empty → trigger PhoBERT supplement."""
    return (
        not getattr(entities, "trieu_chung", []) or
        not getattr(entities, "tai_kham", "") or
        not getattr(entities, "ly_do", "")
    )
