# src/pipeline/p1_processing/l1_semantic.py
# Stage:    L1_SEMANTIC
# Role:     Transcribe audio (PhoWhisper-medium / whisper-small), detect language,
#           route VI through L1b. No decisions. No memory access.
# Req:      SRS-L1-001..009 -- see docs/cl08_operation/SRS.md
# FID:      MV-FID-001 | MV-FID-002 | MV-FID-011 | MV-FID-014 | v1.5
# Standard: ISO/IEC 42001:2023 Clause 8.5
# Version:  v1.5 -- CA-007: race condition fix + audio size limit + wer_estimate integrity

import re
import threading
from typing import Any, Dict, Optional, Tuple

from src.pipeline.p1_processing.l1b_translation import ViEnMedicalTranslator

try:
    import torch
    from transformers import WhisperProcessor, WhisperForConditionalGeneration
    _PHOWHISPER_AVAILABLE = True
except ImportError:
    _PHOWHISPER_AVAILABLE = False

_SAMPLE_RATE = 16000
MAX_AUDIO_SAMPLES = 480_000  # @req SRS-L1-009 -- 30 s at 16 kHz hard ceiling

# Vietnamese detection: diacritics + common medical dictation phrases
_VI_DIACRITICS_RE = re.compile(
    r'[àáâãèéêìíòóôõùúýăđơưÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝĂĐƠƯ]'
)
_VI_PHRASE_RE = re.compile(
    r'\b(bệnh nhân|bác sĩ|đau|thuốc|huyết áp|tiền sử|đang dùng|mỗi ngày'
    r'|tăng|giảm|khám|chẩn đoán|tuổi|ngực|đầu|sốt|buồn nôn|chóng mặt)\b',
    re.IGNORECASE | re.UNICODE,
)
_EN_PHRASE_RE = re.compile(
    r'\b(patient|doctor|blood|pressure|pain|history|currently|taking|fever'
    r'|chest|headache|dizziness|nausea|diagnosis|hypertension|daily)\b',
    re.IGNORECASE,
)

_translator = ViEnMedicalTranslator()

# VI model cache (PhoWhisper-medium — vinai/PhoWhisper-medium)
_phow_processor = None
_phow_model = None
_phow_lock = threading.Lock()  # CA-007 NC-001: thread-safe lazy load

# EN/mixed model cache (whisper-small — openai/whisper-small)
_whisper_processor = None
_whisper_model = None
_whisper_lock = threading.Lock()  # CA-007 NC-001: thread-safe lazy load


# @req SRS-L1-001 -- Normalize and extract meaning. No decisions. No memory access.
# @req SRS-L1-005 -- Transcribe audio using PhoWhisper-medium (VI) or whisper-small (EN/mixed).
def handle(payload: Any) -> Dict[str, Any]:
    """L1_SEMANTIC: ASR (if audio), language detection, VI→EN routing."""
    if not isinstance(payload, dict):
        return {"ok": False, "stage": "L1_SEMANTIC", "error": "INVALID_PAYLOAD"}

    hint_language = payload.get("hint_language", "vi")

    # @req SRS-L1-005 -- audio path: transcribe with ASR before text processing
    # @req SRS-L1-008 -- route to PhoWhisper-medium (vi) or whisper-small (en/mixed)
    # @req SRS-L1-009 -- reject audio_array longer than MAX_AUDIO_SAMPLES
    asr_confidence: Optional[float] = None
    came_from_audio = False
    audio_array = payload.get("audio_array")
    if audio_array is not None:
        # CA-007 NC-002: hard ceiling on audio size — prevents OOM from malicious input
        try:
            if len(audio_array) > MAX_AUDIO_SAMPLES:
                return {"ok": False, "stage": "L1_SEMANTIC", "error": "AUDIO_TOO_LONG"}
        except TypeError:
            return {"ok": False, "stage": "L1_SEMANTIC", "error": "INVALID_AUDIO_ARRAY"}
        transcription = _transcribe(audio_array, hint_language)
        if not transcription["ok"]:
            return {
                "ok": False,
                "stage": "L1_SEMANTIC",
                "error": "TRANSCRIPTION_FAILED",
                "message": transcription.get("error", "ASR transcription failed"),
            }
        # Remove audio_array from payload -- SRS-L0-005 (purge from memory)
        payload = {k: v for k, v in payload.items() if k != "audio_array"}
        # CA-007 NC-004: preserve original transcript when both audio + text submitted
        if "transcript" in payload:
            payload["original_transcript"] = payload["transcript"]
        payload["transcript"] = transcription["text"]
        payload["wer_estimate"] = round(1.0 - transcription["confidence"], 2)
        payload["input_type"] = "audio"
        asr_confidence = transcription["confidence"]
        came_from_audio = True

    # Accept pre-transcribed text (text pipeline or post-ASR)
    text = (
        payload.get("transcript")
        or payload.get("text")
        or payload.get("hint_text")
        or ""
    )

    # CA-007 NC-005: include came_from_audio so is_speech_flow is correct after audio_array removed
    is_speech_flow = came_from_audio or any(
        k in payload
        for k in ("audio_data", "duration_seconds", "session_id",
                  "doctor_id", "hint_language", "content_hash")
    )
    if not text:
        if is_speech_flow:
            return {
                "ok": False,
                "stage": "L1_SEMANTIC",
                "error": "NO_TEXT_AVAILABLE",
                "message": "No transcript provided. ASR required in production.",
            }
        return {"ok": True, "stage": "L1_SEMANTIC", "data": payload}

    # @req SRS-L1-004 -- detect language from transcript
    language = detect_language(text)

    translation_result = None
    if language in ("vi", "mixed"):
        translation_result = _translator.translate(text, source_lang=language)
        # F3 fix: guard against missing key if translator returns error dict
        processed_text = translation_result.get("translated_text", text)
    else:
        processed_text = text

    # CA-007 NC-003: compute confidence + wer_estimate internally — do not trust external value
    # Audio path: asr_confidence already validated; text path: length-based proxy
    confidence = asr_confidence if asr_confidence is not None else _text_length_confidence(text)
    wer_estimate = round(1.0 - confidence, 2)

    result_data: Dict[str, Any] = {
        **payload,
        "original_text": text,
        "processed_text": processed_text,
        "detected_language": language,
        "confidence": confidence,
        "wer_estimate": wer_estimate,
    }
    if translation_result:
        result_data["translation"] = translation_result

    return {"ok": True, "stage": "L1_SEMANTIC", "data": result_data}


# @req SRS-L1-004 -- detect language from transcript
def detect_language(text: str) -> str:
    """Return 'vi', 'en', or 'mixed' based on text content."""
    has_vi_diacritics = bool(_VI_DIACRITICS_RE.search(text))
    has_vi_phrases = bool(_VI_PHRASE_RE.search(text))
    has_en_phrases = bool(_EN_PHRASE_RE.search(text))
    is_vi = has_vi_diacritics or has_vi_phrases
    if is_vi and has_en_phrases:
        return "mixed"
    if is_vi:
        return "vi"
    return "en"


def _text_length_confidence(text: str) -> float:
    """Length-based confidence proxy for non-audio (text) input path only."""
    return 0.91 if len(text) > 80 else (0.85 if len(text) > 30 else 0.70)


# @req SRS-L1-008 -- language-aware confidence: EN fixed, VI diacritic ratio, mixed relaxed
def _compute_confidence(text: str, hint_language: str) -> float:
    """Language-aware ASR confidence proxy (used for audio path only)."""
    if hint_language == "en":
        return 0.85  # whisper-small EN: reliable fixed proxy
    vi_chars = re.findall(r'[àáâãèéêìíòóôõùúýăđơưÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝĂĐƠƯ]', text)
    alpha = [c for c in text if c.isalpha()]
    dr = len(vi_chars) / max(len(alpha), 1)
    if hint_language == "mixed":
        # Relaxed penalty: EN medical terms do not degrade confidence unfairly
        return round(max(0.35, min(0.90, 0.50 + dr * 0.8)), 2)
    # "vi" (default): original diacritic proxy per SRS-L1-007
    return round(max(0.05, min(0.95, 0.35 + dr * 1.5)), 2)


# @req SRS-L1-005 -- PhoWhisper-medium for VI transcription
# @req SRS-L1-006 -- offline, model cached after first download
def _load_phowhisper() -> Tuple:
    """Lazy-load PhoWhisper-medium once (VI — vinai/PhoWhisper-medium)."""
    global _phow_processor, _phow_model
    with _phow_lock:  # CA-007 NC-001: prevent double-load under concurrency
        if _phow_model is None:
            if not _PHOWHISPER_AVAILABLE:
                raise ImportError(
                    "transformers and torch required for audio transcription. "
                    "Run: pip install transformers torch"
                )
            _phow_processor = WhisperProcessor.from_pretrained("vinai/PhoWhisper-medium")
            _phow_model = WhisperForConditionalGeneration.from_pretrained("vinai/PhoWhisper-medium")
            _phow_model.eval()
    return _phow_processor, _phow_model


# @req SRS-L1-008 -- whisper-small for EN/mixed transcription
# @req SRS-L1-006 -- offline, model cached after first download
def _load_whisper_small() -> Tuple:
    """Lazy-load whisper-small once (EN/mixed — openai/whisper-small)."""
    global _whisper_processor, _whisper_model
    with _whisper_lock:  # CA-007 NC-001: prevent double-load under concurrency
        if _whisper_model is None:
            if not _PHOWHISPER_AVAILABLE:
                raise ImportError(
                    "transformers and torch required for audio transcription. "
                    "Run: pip install transformers torch"
                )
            _whisper_processor = WhisperProcessor.from_pretrained("openai/whisper-small")
            _whisper_model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-small")
            _whisper_model.eval()
    return _whisper_processor, _whisper_model


# @req SRS-L1-005 -- transcription with confidence score
# @req SRS-L1-006 -- offline operation (no network calls after first model download)
# @req SRS-L1-008 -- route by hint_language: vi→PhoWhisper, en/mixed→whisper-small
def _transcribe(audio_array, hint_language: str = "vi") -> Dict[str, Any]:
    """Transcribe float32 16kHz mono array using language-appropriate ASR model.

    VI:    PhoWhisper-medium, decoder forced language="vi"
    EN:    whisper-small, decoder forced language="en"
    mixed: whisper-small, auto-detect (no forced language — VI+EN medical terms)

    Confidence proxy per SRS-L1-007/SRS-L1-008:
      EN    → fixed 0.85 (whisper-small EN reliable)
      VI    → clamp(0.35 + dr*1.5, 0.05, 0.95)  where dr = diacritic ratio
      mixed → clamp(0.50 + dr*0.8, 0.35, 0.90)  (relaxed EN-term penalty)
    """
    try:
        if hint_language == "en":
            processor, model = _load_whisper_small()
            forced_decoder_ids = processor.get_decoder_prompt_ids(language="en", task="transcribe")
        elif hint_language == "mixed":
            processor, model = _load_whisper_small()
            forced_decoder_ids = None  # auto-detect: VI+EN mixed content
        else:  # "vi" (default)
            processor, model = _load_phowhisper()
            forced_decoder_ids = processor.get_decoder_prompt_ids(language="vi", task="transcribe")

        inputs = processor(audio_array, sampling_rate=_SAMPLE_RATE, return_tensors="pt")

        with torch.no_grad():
            if forced_decoder_ids is not None:
                sequences = model.generate(**inputs, forced_decoder_ids=forced_decoder_ids)
            else:
                sequences = model.generate(**inputs)

        # F5 fix: guard against empty decode result
        decoded = processor.batch_decode(sequences, skip_special_tokens=True)
        if not decoded:
            return {"ok": False, "error": "EMPTY_TRANSCRIPT"}
        text = decoded[0].strip()
        if not text:
            return {"ok": False, "error": "EMPTY_TRANSCRIPT"}

        confidence = _compute_confidence(text, hint_language)
        return {"ok": True, "text": text, "confidence": confidence}

    except ImportError as exc:
        return {"ok": False, "error": str(exc)}
    except Exception as exc:
        return {"ok": False, "error": f"Transcription error: {exc}"}
