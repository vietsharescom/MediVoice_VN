# src/pipeline/p1_processing/l1b_translation.py
# Module:   L1b_TRANSLATION (sub-component of L1_SEMANTIC)
# Role:     Vietnamese → English medical translation. Drug names NEVER translated.
# Req:      SRS-L1b-001, SRS-L1b-002, SRS-L1b-004 -- see docs/cl08_operation/SRS.md
# FID:      DS-FID-001 | MV-FID-012 | Phase 1 → Phase 2
# Design:   Helsinki-NLP/opus-mt-vi-en via model.generate() (lazy-loaded)
#           Fallback: rule-based medical vocabulary bridge (offline, no download)
# Standard: ISO/IEC 42001:2023 Clause 8.5
# Version:  v1.8 -- EPR-C1/C2: drug regex multi-word + fuzzy threshold 0.75→0.92 (medical safety)

import difflib
import logging
import re
import threading
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Phrase-level Vietnamese → English medical vocabulary (longest-match priority)
_VI_EN_VOCAB: Dict[str, str] = {
    # Patient demographics
    "bệnh nhân nam":         "male patient",
    "bệnh nhân nữ":          "female patient",
    "bệnh nhân":             "patient",
    "nam":                   "male",
    "nữ":                    "female",
    "tuổi":                  "years old",
    # Symptoms
    "đau ngực trái":         "left chest pain",
    "đau ngực phải":         "right chest pain",
    "đau ngực":              "chest pain",
    "đau đầu":               "headache",
    "chóng mặt":             "dizziness",
    "buồn nôn":              "nausea",
    "khó thở":               "shortness of breath",
    "đau bụng":              "abdominal pain",
    "sốt":                   "fever",
    "ho":                    "cough",
    "mệt mỏi":               "fatigue",
    "yếu nửa người phải":    "right hemiparesis",
    "yếu nửa người trái":    "left hemiparesis",
    "yếu nửa người":         "hemiparesis",
    "yếu":                   "weakness",
    "tê":                    "numbness",
    "phù":                   "edema",
    # Stroke / neuro — CA-029
    "nói khó":               "dysarthria",
    "nói không rõ":          "dysarthria",
    "méo miệng":             "facial droop",
    "lệch miệng":            "facial droop",
    "nhồi máu não cấp":      "acute ischemic stroke",
    "nhồi máu não":          "ischemic stroke",
    "xuất huyết não":        "hemorrhagic stroke",
    "liệt nửa người phải":   "right hemiplegia",
    "liệt nửa người trái":   "left hemiplegia",
    "liệt nửa người":        "hemiplegia",
    "đường huyết":           "blood glucose",
    # Stroke clinical findings — CA-030 (trigger KB-016/020/021)
    "ct không xuất huyết":           "CT no hemorrhage",
    "ct sọ não không xuất huyết":    "CT no hemorrhage",
    "chưa thấy xuất huyết":          "CT no hemorrhage",
    "không có xuất huyết":           "CT no hemorrhage",
    "tiêu sợi huyết không phù hợp":  "tPA contraindicated",
    "không phù hợp tiêu sợi huyết":  "tPA contraindicated",
    "chống chỉ định tiêu sợi huyết": "tPA contraindicated",
    "lấy huyết khối":                "thrombectomy",
    "can thiệp mạch não":            "endovascular thrombectomy",
    "can thiệp lấy huyết khối":      "thrombectomy",
    "chụp mạch lấy huyết khối":      "thrombectomy",
    # Medical conditions
    "tăng huyết áp":         "hypertension",
    "đái tháo đường type 2": "type 2 diabetes mellitus",
    "đái tháo đường":        "diabetes mellitus",
    "bệnh tim":              "heart disease",
    "bệnh thận":             "kidney disease",
    "hen suyễn":             "asthma",
    "viêm phổi":             "pneumonia",
    # Vitals
    "huyết áp":              "blood pressure",
    "nhịp tim":              "heart rate",
    "nhiệt độ":              "temperature",
    "cân nặng":              "weight",
    "chiều cao":             "height",
    # Medication actions
    "đang dùng":             "currently on",
    "đang uống":             "currently taking",
    "dùng":                  "on",
    "uống":                  "taking",
    "tôi muốn tăng lên":     "I want to increase to",
    "tôi muốn":              "I want to",
    "tăng lên":              "increase to",
    "giảm xuống":            "decrease to",
    "giảm":                  "reduce",
    # Frequency
    "hai lần mỗi ngày":      "twice daily",
    "một lần mỗi ngày":      "once daily",
    "mỗi ngày":              "daily",
    "mỗi sáng":              "every morning",
    "mỗi tối":               "every evening",
    "mỗi tuần":              "weekly",
    # IV dosing intervals — CA-028
    "mỗi 4 giờ":             "every 4 hours",
    "mỗi 6 giờ":             "every 6 hours",
    "mỗi 8 giờ":             "every 8 hours",
    "mỗi 12 giờ":            "every 12 hours",
    "mỗi 24 giờ":            "every 24 hours",
    # Time / onset
    "sáng sớm":              "early morning",
    "hôm nay":               "today",
    "từ sáng sớm":           "since early morning",
    "3 ngày nay":            "for 3 days",
    "2 ngày":                "for 2 days",
    "từ":                    "since",
    "ngày":                  "days",
    "tuần":                  "weeks",
    "tháng":                 "months",
    "năm":                   "years",
    # Clinical context
    "tiền sử":               "history of",
    "kèm theo":              "accompanied by",
    "kèm":                   "with",
    "có":                    "has",
    # Anatomy
    "ngực trái":             "left chest",
    "ngực phải":             "right chest",
    "ngực":                  "chest",
    "bụng":                  "abdomen",
    "đầu":                   "head",
    "lưng":                  "back",
    # Dental — @req SRS-L1b-005 (MV-FID-016)
    "đau răng hàm dưới bên phải":  "lower right tooth pain",
    "đau răng hàm dưới bên trái":  "lower left tooth pain",
    "đau răng hàm trên bên phải":  "upper right tooth pain",
    "đau răng hàm trên bên trái":  "upper left tooth pain",
    "sâu răng hàm dưới bên phải":  "lower right tooth decay",
    "sâu răng hàm dưới bên trái":  "lower left tooth decay",
    "sâu răng hàm trên bên phải":  "upper right tooth decay",
    "sâu răng hàm trên bên trái":  "upper left tooth decay",
    "đau răng":              "tooth pain",
    "sâu răng":              "tooth decay",
    "đau nướu":              "gum pain",
    "viêm nướu":             "gum inflammation",
    "ê răng":                "tooth sensitivity",
    "răng lung lay":         "loose tooth",
    "nhổ răng":              "tooth extraction",
    "hàm dưới bên phải":    "lower right jaw",
    "hàm dưới bên trái":    "lower left jaw",
    "hàm trên bên phải":    "upper right jaw",
    "hàm trên bên trái":    "upper left jaw",
    "hàm dưới":             "lower jaw",
    "hàm trên":             "upper jaw",
    "khi nhai":              "when chewing",
    "khi cắn":               "when biting",
    "răng":                  "tooth",
    # Common condition shorthand — @req SRS-L1b-006
    "tiểu đường":            "diabetes",
    "huyết áp cao":          "hypertension",
    "cao huyết áp":          "hypertension",
    # Trauma / emergency — CA-025 + CA-026
    "bị tông trực diện":     "head-on collision",
    "bị tông":               "collision trauma",
    "tai nạn xe máy":        "motorcycle accident",
    "tai nạn xe":            "motor vehicle accident",
    "chấn thương nặng":      "severe trauma",
    "chấn thương":           "trauma",
    "té ngã":                "fall injury",
    "dập lá lách":           "splenic laceration",
    "lá lách":               "spleen",
    "tổn thương gan":        "liver laceration",
    "gãy nhiều xương sườn":  "multiple rib fractures",
    "gãy xương sườn":        "rib fracture",
    "xương sườn":            "rib",
    "bầm tím":               "contusion",
    "bụng chướng":           "abdominal distension",
    "ấn đau":                "tenderness on palpation",
    "lơ mơ":                 "altered consciousness",
    "thở nhanh nông":        "rapid shallow breathing",
    "thở nhanh":             "tachypnea",
    "mạch nhanh":            "heart rate",
    "máu ra nhiều":          "major hemorrhage",
    "máu chảy liên tục":     "continuous bleeding",
    "ngủ mê man":            "unconscious",
    "mê man":                "unconscious",
    "kháng sinh":            "antibiotic",
    "liều cao":              "high dose",
    # GI / metabolic symptoms — NER-VOCAB + CA-024
    "tiểu nhiều lần":        "polyuria",
    "tiều nhiều lần":        "polyuria",
    "tiêu chảy":             "diarrhea",
    "đi cầu tiêu chảy":      "diarrhea",
    "ói nôn mửa":            "nausea and vomiting",
    "nôn mửa":               "nausea and vomiting",
    "khó ngủ":               "insomnia",
    "ngủ khó":               "insomnia",
    "mất nước":              "dehydration",
    # Gum symptoms — @req SRS-L1b-006
    "sưng nướu":             "gum swelling",
    # Pediatric / Orthodontic dental — @req SRS-L6-008
    "răng vĩnh viễn mọc":   "permanent teeth eruption",
    "răng vĩnh viễn":        "permanent teeth",
    "răng khôn":             "wisdom teeth",
    "mọc răng":              "teething",
    "răng lệch":             "tooth crowding",
    # Wisdom tooth impaction — CA-017
    "chèn răng số 8":        "impacted wisdom tooth",
    "răng số 8 chèn":        "impacted wisdom tooth",
    "chèn răng":             "tooth impaction",
    "răng số 8":             "wisdom tooth",
    "đề nghị nhổ":           "requesting extraction",
    "nhổ răng số 8":         "wisdom tooth extraction",
}

# F3 fix: only trusted model is allowed (prevents arbitrary path injection)
_ALLOWED_MODELS: frozenset = frozenset({"Helsinki-NLP/opus-mt-vi-en"})

# @req SRS-L1b-005 (MV-FID-016) — word-form ages from MarianMT → digit form
# MarianMT outputs "Twenty-eight-year-old" instead of "28-year-old"; _AGE_RE needs digits.
_WORD_AGE_RE = re.compile(
    r'\b(Zero|One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten'
    r'|Eleven|Twelve|Thirteen|Fourteen|Fifteen|Sixteen|Seventeen|Eighteen|Nineteen'
    r'|Twenty|Twenty-one|Twenty-two|Twenty-three|Twenty-four|Twenty-five'
    r'|Twenty-six|Twenty-seven|Twenty-eight|Twenty-nine'
    r'|Thirty|Thirty-one|Thirty-two|Thirty-three|Thirty-four|Thirty-five'
    r'|Thirty-six|Thirty-seven|Thirty-eight|Thirty-nine'
    r'|Forty|Forty-one|Forty-two|Forty-three|Forty-four|Forty-five'
    r'|Forty-six|Forty-seven|Forty-eight|Forty-nine'
    r'|Fifty|Fifty-one|Fifty-two|Fifty-three|Fifty-four|Fifty-five'
    r'|Fifty-six|Fifty-seven|Fifty-eight|Fifty-nine'
    r'|Sixty|Sixty-one|Sixty-two|Sixty-three|Sixty-four|Sixty-five'
    r'|Sixty-six|Sixty-seven|Sixty-eight|Sixty-nine'
    r'|Seventy|Seventy-one|Seventy-two|Seventy-three|Seventy-four|Seventy-five'
    r'|Seventy-six|Seventy-seven|Seventy-eight|Seventy-nine'
    r'|Eighty|Eighty-one|Eighty-two|Eighty-three|Eighty-four|Eighty-five'
    r'|Eighty-six|Eighty-seven|Eighty-eight|Eighty-nine'
    r'|Ninety|Ninety-one|Ninety-two|Ninety-three|Ninety-four|Ninety-five'
    r'|Ninety-six|Ninety-seven|Ninety-eight|Ninety-nine)'
    r'(-year(?:s)?-old|\s+year(?:s)?\s+old)',
    re.IGNORECASE,
)
_WORD_TO_INT: Dict[str, int] = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "twenty-one": 21, "twenty-two": 22, "twenty-three": 23,
    "twenty-four": 24, "twenty-five": 25, "twenty-six": 26, "twenty-seven": 27,
    "twenty-eight": 28, "twenty-nine": 29,
    "thirty": 30, "thirty-one": 31, "thirty-two": 32, "thirty-three": 33,
    "thirty-four": 34, "thirty-five": 35, "thirty-six": 36, "thirty-seven": 37,
    "thirty-eight": 38, "thirty-nine": 39,
    "forty": 40, "forty-one": 41, "forty-two": 42, "forty-three": 43,
    "forty-four": 44, "forty-five": 45, "forty-six": 46, "forty-seven": 47,
    "forty-eight": 48, "forty-nine": 49,
    "fifty": 50, "fifty-one": 51, "fifty-two": 52, "fifty-three": 53,
    "fifty-four": 54, "fifty-five": 55, "fifty-six": 56, "fifty-seven": 57,
    "fifty-eight": 58, "fifty-nine": 59,
    "sixty": 60, "sixty-one": 61, "sixty-two": 62, "sixty-three": 63,
    "sixty-four": 64, "sixty-five": 65, "sixty-six": 66, "sixty-seven": 67,
    "sixty-eight": 68, "sixty-nine": 69,
    "seventy": 70, "seventy-one": 71, "seventy-two": 72, "seventy-three": 73,
    "seventy-four": 74, "seventy-five": 75, "seventy-six": 76, "seventy-seven": 77,
    "seventy-eight": 78, "seventy-nine": 79,
    "eighty": 80, "eighty-one": 81, "eighty-two": 82, "eighty-three": 83,
    "eighty-four": 84, "eighty-five": 85, "eighty-six": 86, "eighty-seven": 87,
    "eighty-eight": 88, "eighty-nine": 89,
    "ninety": 90, "ninety-one": 91, "ninety-two": 92, "ninety-three": 93,
    "ninety-four": 94, "ninety-five": 95, "ninety-six": 96, "ninety-seven": 97,
    "ninety-eight": 98, "ninety-nine": 99,
}


# Terms MarianMT consistently garbles — pre-replaced before ML translation.
# Longest-match priority (sorted at use time). @req SRS-L1b-006
_ML_PREPROTECT: Dict[str, str] = {
    # Chronic diseases — CA-023: MarianMT garbles these (e.g. "đái tháo đường" → "urinating")
    "đái tháo đường type 2": "type 2 diabetes mellitus",
    "đái tháo đường":        "diabetes mellitus",
    "tiểu đường type 2":     "type 2 diabetes mellitus",
    "tiểu đường":            "diabetes",
    "tăng huyết áp":         "hypertension",
    "cao huyết áp":          "hypertension",
    "huyết áp cao":          "hypertension",
    "rung nhĩ":              "atrial fibrillation",
    "suy tim":               "heart failure",
    "bệnh mạch vành":        "coronary artery disease",
    # Emergency / critical — CA-023
    "huyết áp thấp":         "hypotension",
    "hạ huyết áp":           "hypotension",
    "nhịp tim nhanh":        "tachycardia",
    "nhịp tim chậm":         "bradycardia",
    "cấp cứu nguy kịch":     "emergency critical condition",
    "nguy kịch":             "critical condition",
    "cấp cứu":               "emergency",
    "nhồi máu cơ tim":       "myocardial infarction",
    "đột quỵ":               "stroke",
    "nhiễm trùng huyết":     "sepsis",
    "nhiễm khuẩn huyết":     "sepsis",
    "viêm phổi nặng":        "severe pneumonia",
    "nội khí quản":          "endotracheal intubation",
    "thở máy":               "mechanical ventilation",
    "đặt nội khí quản":      "endotracheal intubation",
    "hôn mê":                "coma",
    "co giật":               "seizure",
    # Dental — @req SRS-L1b-006
    "răng vĩnh viễn mọc":   "permanent teeth eruption",
    "răng vĩnh viễn":        "permanent teeth",
    "răng khôn":             "wisdom teeth",
    "mọc răng":              "teething",
    "răng lệch":             "tooth crowding",
    "sưng nướu":             "gum swelling",
    # Wisdom tooth impaction — CA-017
    "chèn răng số 8":        "impacted wisdom tooth",
    "răng số 8 chèn":        "impacted wisdom tooth",
    "chèn răng":             "tooth impaction",
    "răng số 8":             "wisdom tooth",
    "đề nghị nhổ":           "requesting extraction",
    "nhổ răng số 8":         "wisdom tooth extraction",
    # IV dosing intervals — CA-028
    "mỗi 4 giờ":             "every 4 hours",
    "mỗi 6 giờ":             "every 6 hours",
    "mỗi 8 giờ":             "every 8 hours",
    "mỗi 12 giờ":            "every 12 hours",
    "mỗi 24 giờ":            "every 24 hours",
    # Stroke / neuro — CA-029
    "nói khó":               "dysarthria",
    "méo miệng":             "facial droop",
    "nhồi máu não cấp":      "acute ischemic stroke",
    "nhồi máu não":          "ischemic stroke",
    "xuất huyết não":        "hemorrhagic stroke",
    "đường huyết":           "blood glucose",
    # Stroke clinical findings — CA-030
    "ct không xuất huyết":           "CT no hemorrhage",
    "ct sọ não không xuất huyết":    "CT no hemorrhage",
    "chưa thấy xuất huyết":          "CT no hemorrhage",
    "tiêu sợi huyết không phù hợp":  "tPA contraindicated",
    "không phù hợp tiêu sợi huyết":  "tPA contraindicated",
    "lấy huyết khối":                "thrombectomy",
    "can thiệp mạch não":            "endovascular thrombectomy",
}

# MarianMT synonym outputs that NER cannot match — normalised post-translation.
# @req SRS-L1b-007
_MARIAN_NORMALISE: List[tuple] = [
    (re.compile(r'\btiredness\b', re.IGNORECASE), 'fatigue'),
    (re.compile(r'\btired\b', re.IGNORECASE), 'fatigue'),
    (re.compile(r'\bdizzyness\b', re.IGNORECASE), 'dizziness'),
    (re.compile(r'\bdizzy\b', re.IGNORECASE), 'dizziness'),
    (re.compile(r'\bnauseous\b', re.IGNORECASE), 'nausea'),
    (re.compile(r'\bpalpitation\b', re.IGNORECASE), 'palpitations'),
    (re.compile(r'\bheadaches\b', re.IGNORECASE), 'headache'),
    (re.compile(r'\bswollen\b', re.IGNORECASE), 'swelling'),
    (re.compile(r'\bdifficulty breathing\b', re.IGNORECASE), 'shortness of breath'),
    (re.compile(r'\bhard to breathe\b', re.IGNORECASE), 'shortness of breath'),
    (re.compile(r'\bbreathing difficulty\b', re.IGNORECASE), 'shortness of breath'),
    (re.compile(r'\bstomachache\b', re.IGNORECASE), 'abdominal pain'),
    (re.compile(r'\bstomach\s+ache\b', re.IGNORECASE), 'abdominal pain'),
]


def _normalise_word_age(text: str) -> str:
    """Convert word-form ages to digit form: 'Twenty-eight-year-old' → '28-year-old'."""
    def _replace(m: re.Match) -> str:
        word = m.group(1).lower()
        digit = _WORD_TO_INT.get(word)
        if digit is None:
            return m.group(0)
        suffix = m.group(2)
        # Normalise suffix to canonical hyphenated form
        normalised_suffix = "-year-old" if "old" in suffix.lower() else suffix
        return f"{digit}{normalised_suffix}"
    return _WORD_AGE_RE.sub(_replace, text)

# F2 fix: MarianMT max is 512 tokens; truncate at 450 to leave headroom for special tokens
_MAX_TOKENS: int = 450

# Drug name pattern: one or more tokens + dose + unit (EPR-C1: multi-word drugs e.g. "Panadol Extra 500mg")
_DRUG_DOSE_RE = re.compile(
    r'\b([A-Za-z][A-Za-z0-9\-]*(?:\s+[A-Za-z0-9\-]+)*)\s+(\d+(?:\.\d+)?)\s*(mg|mcg|ml|g|IU|units?)\b',
    re.IGNORECASE,
)


class ViEnMedicalTranslator:
    """
    Phase 1 medical translator: Vietnamese → English.

    Drug names, procedure names, and measurements are NEVER translated.
    Phrase-level vocabulary mapping handles common medical dictation patterns.
    Model backend (Helsinki-NLP/opus-mt-vi-en) loaded via load_translation_model()
    when full ML inference is required in production deployment.
    """

    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._model_load_attempted = False  # try once per session; avoid repeated failures
        self._load_lock = threading.Lock()  # F1 fix: prevent double-load under concurrency

    def _ensure_model_loaded(self) -> None:
        """Lazy-load MarianMT on first translate() call. Silently falls back to vocab bridge."""
        if self._model is not None or self._model_load_attempted:
            return  # fast path — no lock needed
        with self._load_lock:
            if self._model is not None or self._model_load_attempted:
                return  # double-check inside lock
            self._model_load_attempted = True
            try:
                self.load_translation_model()
            except Exception:
                pass  # vocab bridge remains active

    def load_translation_model(self, model_name: str = "Helsinki-NLP/opus-mt-vi-en"):
        """
        Load transformer model for production inference.
        Uses model.generate() — never pipeline() (transformers >= 4.40 bug R-P05).
        """
        # F3 fix: validate model_name against allowlist before loading
        if model_name not in _ALLOWED_MODELS:
            raise ValueError(f"Untrusted model: {model_name!r}. Allowed: {_ALLOWED_MODELS}")
        try:
            from transformers import MarianMTModel, MarianTokenizer
            # nosec B615 -- Phase 1: Helsinki-NLP/opus-mt-vi-en is a trusted public model.
            # Revision pinning deferred to Phase 2 when model version is stabilised.
            self._tokenizer = MarianTokenizer.from_pretrained(model_name)  # nosec B615
            self._model = MarianMTModel.from_pretrained(model_name)  # nosec B615
        except ImportError:
            logger.warning("transformers not installed — MarianMT unavailable, using vocab bridge")

    # @req SRS-L1b-001 -- translate VI→EN preserving drug names verbatim
    # @req SRS-L1b-002 -- return confidence score for every translation output
    def translate(self, text: str, source_lang: str = "vi") -> Dict:
        """
        Translate Vietnamese (or mixed) medical text to English.

        Returns:
            translated_text: English output
            confidence: float 0–1
            preserved_terms: list of drug names/doses kept verbatim
        """
        if not text or not text.strip():
            return {"translated_text": "", "confidence": 1.0, "preserved_terms": []}

        if source_lang == "en":
            return {"translated_text": text, "confidence": 1.0, "preserved_terms": []}

        # Extract drug+dose tokens to protect from MarianMT mutation
        preserved = self._extract_preserved_terms(text)

        self._ensure_model_loaded()

        # NC-003 CA-008: ML only for pure VI — mixed input may contain English clinical terms
        # that MarianMT VI→EN would corrupt (e.g. "blood pressure", "Patient").
        if self._model is not None and source_lang == "vi":
            # @req SRS-L1b-006: pre-protect complex terms MarianMT consistently garbles
            protected = self._preprotect_terms(text)
            result_text = self._model_translate(protected)
            # @req SRS-L1b-005 (MV-FID-016): normalise word-form ages from MarianMT output
            result_text = _normalise_word_age(result_text)
            # @req SRS-L1b-007: normalise MarianMT synonym outputs to NER-standard terms
            result_text = self._normalise_marian_output(result_text)
        else:
            result_text = self._vocab_translate(text)

        # Restore drug names: exact match first, then fuzzy-replace MarianMT-corrupted form.
        # MarianMT cannot be reliably protected with placeholders (it mutates them via
        # SentencePiece tokenization). Fuzzy matching catches near-identical edits only.
        # EPR-C2: threshold raised 0.75→0.92 — prevents wrong-drug substitution (medical safety).
        for term in preserved:
            drug_name = term.split()[0]  # base name without dose
            if re.search(r'\b' + re.escape(drug_name) + r'\b', result_text, re.IGNORECASE):
                continue  # exact form already present — no action needed
            # Find the closest word in the output using sequence similarity
            candidates = re.findall(r'\b[A-Za-z]{3,}\b', result_text)
            best_word, best_score = None, 0.0
            for cand in candidates:
                score = difflib.SequenceMatcher(None, drug_name.lower(), cand.lower()).ratio()
                if score > best_score and score >= 0.92:  # EPR-C2: was 0.75 — near-identical only
                    best_word, best_score = cand, score
            if best_word:
                # Replace corrupted drug + any trailing dose MarianMT may have expanded
                # e.g. "paladon 250 mg" → "panadon 250mg" (replaces both word + dose)
                _dose_suffix = r'(?:\s+\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|iu|milligrams?|units?)?)?'
                result_text = re.sub(
                    r'\b' + re.escape(best_word) + r'\b' + _dose_suffix, term,
                    result_text, count=1, flags=re.IGNORECASE,
                )
            else:
                result_text = result_text.rstrip() + f" {term}"

        confidence = self._estimate_confidence(text, result_text, preserved)

        return {
            "translated_text": result_text.strip(),
            "confidence": confidence,
            "preserved_terms": preserved,
        }

    def _preprotect_terms(self, text: str) -> str:
        """Replace complex VI terms that MarianMT garbles before ML translation. @req SRS-L1b-006"""
        result = text
        for vi_phrase in sorted(_ML_PREPROTECT.keys(), key=len, reverse=True):
            pattern = re.compile(r'\b' + re.escape(vi_phrase) + r'\b', re.IGNORECASE | re.UNICODE)
            result = pattern.sub(_ML_PREPROTECT[vi_phrase], result)
        return result

    def _normalise_marian_output(self, text: str) -> str:
        """Normalise MarianMT synonym outputs to NER-standard English terms. @req SRS-L1b-007"""
        for pattern, replacement in _MARIAN_NORMALISE:
            text = pattern.sub(replacement, text)
        return text

    def _extract_preserved_terms(self, text: str) -> List[str]:
        """Extract drug name + dose tokens that must survive translation verbatim."""
        return [m.group(0) for m in _DRUG_DOSE_RE.finditer(text)]

    def _vocab_translate(self, text: str) -> str:
        """
        Rule-based vocabulary translation.
        Replaces Vietnamese phrases (longest first) with English equivalents.
        English tokens (e.g., code-switched drug names) are preserved as-is.
        """
        result = text
        # Longest phrases first to avoid partial replacement.
        # \b boundaries prevent short entries (e.g. "ho"→"cough") from corrupting
        # English medical words that contain the same letters (e.g. "Cholesterol").
        for vi_phrase in sorted(_VI_EN_VOCAB.keys(), key=len, reverse=True):
            pattern = re.compile(
                r'\b' + re.escape(vi_phrase) + r'\b', re.IGNORECASE | re.UNICODE
            )
            result = pattern.sub(_VI_EN_VOCAB[vi_phrase], result)
        return result

    def _model_translate(self, text: str) -> str:
        """Translate via MarianMT model.generate() (production path)."""
        # F2 fix: explicit truncation — prevents silent truncation at generate() time
        inputs = self._tokenizer(
            text, return_tensors="pt", padding=True,
            truncation=True, max_length=_MAX_TOKENS,
        )
        translated = self._model.generate(**inputs)
        # F4 fix: guard against empty decode result
        # Use len() not `not tensor` — boolean eval of multi-element tensor raises RuntimeError
        if len(translated) == 0 or len(translated[0]) == 0:
            return text  # fallback: return original on degenerate model output
        decoded = self._tokenizer.decode(translated[0], skip_special_tokens=True).strip()
        return decoded if decoded else text

    def _estimate_confidence(self, source: str, translated: str,
                             preserved: List[str]) -> float:
        """Heuristic confidence: penalise if many Vietnamese chars remain after translation."""
        vi_chars = len(re.findall(r'[àáâãèéêìíòóôõùúýăđơưÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝĂĐƠƯ]', translated))
        total_chars = max(len(translated), 1)
        vi_ratio = vi_chars / total_chars
        base = 0.92 if vi_ratio < 0.05 else (0.78 if vi_ratio < 0.15 else 0.55)
        # Boost if all preserved terms found
        if all(t.lower() in translated.lower() for t in preserved):
            base = min(base + 0.03, 1.0)
        return round(base, 2)
