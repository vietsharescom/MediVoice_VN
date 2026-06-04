# src/models/phobert_ner.py
# Module:   PhoBERT-base-v2 + CRF NER — inference only
# Role:     Predict NEREntity list from Vietnamese medical text.
#           Replaces _VI_SYMPTOM_VOCAB rule-based path in L6_AGENT.
# FID:      MV-FID-018
# Standard: ISO/IEC 42001:2023 Clause 8.5
# Version:  v1.0 -- MV-FID-018: PhoBERT + CRF VI NER (Phase 2)

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Label mapping: VietMed-NER types → MediVoice NEREntity types ─────────────
# Priority Phase 2: SYMPTOM, MEDICATION, AGE, GENDER, DIAGNOSIS, TREATMENT
# Vitals kept as regex (numbers need precision) — PhoBERT handles semantics

_VIETMED_TO_MEDIVOICE: Dict[str, Tuple[str, Optional[str]]] = {
    "DISEASESYMTOM":     ("SYMPTOM",   None),
    "DRUGCHEMICAL":      ("MEDICATION", None),
    "AGE":               ("AGE",       None),
    "GENDER":            ("GENDER",    None),
    "DIAGNOSTICS":       ("SYMPTOM",   None),   # Phase 2: diagnostics → SYMPTOM
    "TREATMENT":         ("HISTORY",   None),   # Phase 2: treatments → HISTORY
    "MEDDEVICETECHNIQUE":("SYMPTOM",   None),   # devices/techniques → SYMPTOM
    "ORGAN":             ("BODY_PART", None),   # new type — ignored in SOAP Phase 2
    "DATETIME":          ("ONSET",     None),   # → onset field, not separate entity
    # Low-priority — not mapped Phase 2
    "OCCUPATION":        None,
    "PERSONALCARE":      None,
    "LOCATION":          None,
    "FOODDRINK":         None,
    "ORGANIZATION":      None,
    "UNITCALIBRATOR":    None,   # vitals handled by regex
    "PREVENTIVEMED":     None,
    "SURGERY":           ("HISTORY", None),
}

# Gender normalisation from VI tokens
_GENDER_MAP = {"nam": "male", "bé trai": "male", "nữ": "female", "bé gái": "female"}

MODEL_PATH_ENV = "PHOBERT_NER_MODEL"
DEFAULT_MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "models", "phobert_ner_medivoice.pt"
)


@dataclass
class _TokenSpan:
    """Raw BIO-decoded span before mapping to NEREntity."""
    label: str
    tokens: List[str]
    text: str


class PhoBERTNER:
    """
    PhoBERT-base-v2 + CRF NER inference.

    Usage:
        ner = PhoBERTNER()
        ner.load()  # lazy — call once, skips if already loaded
        entities = ner.predict("Bệnh nhân nam 43 tuổi sốt cao 40 độ")

    If model file absent: predict() returns [] and logs a warning.
    Production inference replaces _extract_vi_entities() in L6_AGENT.
    """

    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._id2label: Dict[int, str] = {}
        self._loaded = False
        self._load_attempted = False

    def load(self, model_path: Optional[str] = None) -> bool:
        """
        Load PhoBERT + CRF from disk. Returns True on success, False if file absent.
        Thread-safe: subsequent calls are no-ops.
        """
        if self._loaded or self._load_attempted:
            return self._loaded
        self._load_attempted = True

        path = model_path or os.environ.get(MODEL_PATH_ENV, DEFAULT_MODEL_PATH)
        path = os.path.normpath(path)

        if not os.path.exists(path):
            logger.warning(
                "PhoBERTNER model not found at %s — VI NER falling back to rule-based. "
                "Run scripts/train_phobert_ner.py to train.", path
            )
            return False

        try:
            import torch
            from transformers import AutoTokenizer

            checkpoint = torch.load(path, map_location="cpu", weights_only=False)
            self._id2label = checkpoint["id2label"]
            self._tokenizer = AutoTokenizer.from_pretrained(
                "vinai/phobert-base-v2", use_fast=True
            )

            from src.models._phobert_crf import PhoBERTCRFModel
            num_labels = len(self._id2label)
            self._model = PhoBERTCRFModel(num_labels=num_labels)
            self._model.load_state_dict(checkpoint["model_state_dict"])
            self._model.eval()
            self._loaded = True
            logger.info("PhoBERTNER loaded from %s (%d labels)", path, num_labels)
            return True
        except Exception as exc:
            logger.error("PhoBERTNER load failed: %s — falling back to rule-based", exc)
            return False

    def predict(self, vi_text: str) -> List:
        """
        Predict NEREntity list from VI text.
        Returns [] if model not loaded (L6 uses rule-based fallback).
        Imports NEREntity at call time to avoid circular import.
        """
        if not self._loaded:
            return []
        if not vi_text or not vi_text.strip():
            return []

        try:
            import torch
            from src.pipeline.p2_decision.l6_soap_generator import NEREntity

            tokens, predictions = self._run_inference(vi_text)
            spans = self._decode_bio(tokens, predictions)
            return self._spans_to_entities(spans, vi_text)
        except Exception as exc:
            logger.error("PhoBERTNER.predict failed: %s", exc)
            return []

    # ── Private ───────────────────────────────────────────────────────────────

    def _run_inference(self, text: str) -> Tuple[List[str], List[str]]:
        """Tokenize + CRF decode → (tokens, labels)."""
        import torch

        # Match training: split into words first, then tokenize with is_split_into_words=True
        words = text.split()
        if not words:
            return [], []

        encoding = self._tokenizer(
            words,
            is_split_into_words=True,
            return_tensors="pt",
            truncation=True,
            max_length=256,
            padding=True,
        )

        with torch.no_grad():
            pred_ids = self._model(
                input_ids=encoding["input_ids"],
                attention_mask=encoding["attention_mask"],
            )

        # Align subword predictions → word-level labels (first subword per word)
        preds = pred_ids[0] if isinstance(pred_ids, list) else pred_ids[0].tolist()
        attn  = encoding["attention_mask"][0].tolist()

        # Fast tokenizer path: word_ids() gives ground-truth word alignment.
        # crf_idx walks CRF output (active tokens only), idx walks full padded sequence.
        try:
            word_ids_list = encoding.word_ids(batch_index=0)
            word_tokens, word_labels = [], []
            seen: set = set()
            crf_idx = 0
            for idx, wid in enumerate(word_ids_list):
                if attn[idx] == 0:
                    continue                        # padding — not in CRF output
                if wid is not None and wid not in seen:
                    seen.add(wid)
                    if wid < len(words):
                        label_id = preds[crf_idx] if crf_idx < len(preds) else 0
                        word_tokens.append(words[wid])
                        word_labels.append(self._id2label.get(int(label_id), "O"))
                crf_idx += 1
            if word_tokens:
                return word_tokens, word_labels
        except Exception:
            pass  # fall through to token-level fallback

        # Fallback: reconstruct words from subword tokens.
        # Handles both SentencePiece (▁ prefix) and BPE (@@ suffix, used by PhoBERT).
        input_ids_list = encoding["input_ids"][0].tolist()
        tokens  = self._tokenizer.convert_ids_to_tokens(input_ids_list)
        special = set(self._tokenizer.all_special_tokens)
        word_tokens, word_labels = [], []
        crf_idx = 0
        prev_tok = None
        for tok, is_real in zip(tokens, attn):
            if not is_real:
                break
            if tok in special:
                crf_idx += 1
                prev_tok = None
                continue
            label_id = preds[crf_idx] if crf_idx < len(preds) else 0
            label    = self._id2label.get(int(label_id), "O")
            crf_idx += 1
            # New word when: SentencePiece ▁ prefix OR prev token did NOT end with @@
            is_new = tok.startswith("▁") or (prev_tok is None) or (not prev_tok.endswith("@@"))
            if is_new:
                word_tokens.append(tok.replace("▁", "").replace("@@", ""))
                word_labels.append(label)
            else:
                word_tokens[-1] += tok.replace("@@", "")
            prev_tok = tok

        return word_tokens, word_labels

    def _decode_bio(self, tokens: List[str], labels: List[str]) -> List[_TokenSpan]:
        """Collapse BIO tags into spans."""
        spans: List[_TokenSpan] = []
        current_label: Optional[str] = None
        current_tokens: List[str] = []

        for token, label in zip(tokens, labels):
            if label.startswith("B-"):
                if current_label:
                    spans.append(_TokenSpan(
                        label=current_label,
                        tokens=current_tokens,
                        text=" ".join(current_tokens).replace("▁", " ").strip(),
                    ))
                current_label = label[2:]
                current_tokens = [token.replace("▁", "")]
            elif label.startswith("I-") and current_label == label[2:]:
                current_tokens.append(token.replace("▁", ""))
            else:
                if current_label:
                    spans.append(_TokenSpan(
                        label=current_label,
                        tokens=current_tokens,
                        text=" ".join(current_tokens).replace("▁", " ").strip(),
                    ))
                current_label = None
                current_tokens = []

        if current_label:
            spans.append(_TokenSpan(
                label=current_label,
                tokens=current_tokens,
                text=" ".join(current_tokens).replace("▁", " ").strip(),
            ))
        return spans

    def _spans_to_entities(self, spans: List[_TokenSpan], vi_text: str) -> List:
        """Map VietMed spans to NEREntity objects."""
        from src.pipeline.p2_decision.l6_soap_generator import NEREntity

        entities = []
        seen_symptoms: set = set()

        for span in spans:
            mapping = _VIETMED_TO_MEDIVOICE.get(span.label)
            if mapping is None:
                continue
            entity_type, _ = mapping

            if entity_type == "BODY_PART" or entity_type == "ONSET":
                continue  # handled separately or by regex

            text = span.text.strip()
            if not text:
                continue

            if entity_type == "AGE":
                digits = re.search(r'\d+', text)
                if digits:
                    entities.append(NEREntity(type="AGE", value=digits.group(), unit="years"))

            elif entity_type == "GENDER":
                normalised = _GENDER_MAP.get(text.lower())
                if normalised:
                    entities.append(NEREntity(type="GENDER", value=normalised))

            elif entity_type == "SYMPTOM":
                if text not in seen_symptoms:
                    seen_symptoms.add(text)
                    entities.append(NEREntity(type="SYMPTOM", value=text))

            elif entity_type == "MEDICATION":
                entities.append(NEREntity(type="MEDICATION", value=text))

            elif entity_type == "HISTORY":
                entities.append(NEREntity(type="HISTORY", value=text))

        return entities


# Module-level singleton — shared across all L6 calls
_ner_instance: Optional[PhoBERTNER] = None


def get_phobert_ner() -> PhoBERTNER:
    """Return singleton PhoBERTNER, loading model on first call."""
    global _ner_instance
    if _ner_instance is None:
        _ner_instance = PhoBERTNER()
        _ner_instance.load()
    return _ner_instance
