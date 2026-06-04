# src/pipeline/p0_ingestion/l0_input.py
# Stage:    L0_INPUT
# Role:     Accept raw input. Normalize audio to 16kHz mono. Hash for immutability. Purge.
# Req:      SRS-L0-001..005 -- see docs/cl08_operation/SRS.md
# FID:      MV-FID-001 | MV-FID-002 | v1.2
# Policy:   AI_POLICY.md §4 -- audio deleted immediately after capture (privacy by design)
# Standard: ISO/IEC 42001:2023 Clause 8.5
# Version:  v1.2 -- MV-FID-002: audio normalization (librosa, 16kHz mono)

import hashlib
import time
from typing import Any, Dict, Tuple

try:
    import numpy as np
    import librosa as _librosa
    _AUDIO_PROCESSING_AVAILABLE = True
except ImportError:
    _AUDIO_PROCESSING_AVAILABLE = False

SUPPORTED_FORMATS = {"m4a", "mp3", "wav", "ogg", "aac"}
AUDIO_NORMALIZE_FORMATS = {"m4a", "mp3", "wav"}
AUDIO_SOURCES = {"mobile_mic", "audio_file", "phone"}
MIN_DURATION_SECONDS = 2.0
MAX_DURATION_SECONDS = 600.0
SAMPLE_RATE = 16000
SILENCE_RATIO_THRESHOLD = 0.95
SILENCE_RMS_THRESHOLD = 0.01


# @req SRS-L0-001 -- Accept raw input. Preserve immutability.
# @req SRS-L0-004 -- Accept m4a/wav/mp3 and normalize to 16kHz mono PCM.
def handle(payload: Any) -> Dict[str, Any]:
    """L0_INPUT: validate + normalize audio, hash for immutability, purge audio bytes."""
    if not isinstance(payload, dict):
        return _reject("INVALID_PAYLOAD", "Payload must be a JSON object.")

    # Audio normalization path: source field identifies real audio input
    if payload.get("source") in AUDIO_SOURCES:
        return _handle_audio_source(payload)

    # Legacy / metadata path: audio_data field present (base64 or stub)
    if any(k in payload for k in ("audio_data", "duration_seconds", "format")):
        return _handle_audio_metadata(payload)

    # Non-audio payload (framework tests, future flows) -- pass through
    return {"ok": True, "stage": "L0_INPUT", "data": payload}


def _handle_audio_source(payload: Dict) -> Dict[str, Any]:
    """Audio normalization path (SRS-L0-004/005)."""
    if "session_id" not in payload:
        return _reject("MISSING_FIELD", "Required field missing: session_id")

    fmt = str(payload.get("format", "")).lower()
    if fmt and fmt not in AUDIO_NORMALIZE_FORMATS:
        return _reject(
            "UNSUPPORTED_FORMAT",
            f"Format '{fmt}' not supported. Accepted: {sorted(AUDIO_NORMALIZE_FORMATS)}",
        )

    try:
        audio_array, duration = _normalize_audio(payload)
    except ImportError as exc:
        return _reject("LIBRARY_UNAVAILABLE", str(exc))
    except (OSError, FileNotFoundError) as exc:
        return _reject("AUDIO_LOAD_ERROR", f"Cannot load audio: {exc}")

    dur_check = validate_duration(duration)
    if not dur_check["ok"]:
        return dur_check

    # @req SRS-L0-003 -- reject >95% silence
    if _is_silence(audio_array):
        return _reject(
            "NO_SPEECH_DETECTED",
            "Audio is >95% silence — no speech detected.",
            action="REQUEST_RERECORD",
        )

    content_hash = hashlib.sha256(audio_array.tobytes()).hexdigest()[:16]
    clean = {k: v for k, v in payload.items() if k not in ("audio_path", "_test_audio_array")}

    return {
        "ok": True,
        "stage": "L0_INPUT",
        "data": {
            **clean,
            "input_type": "audio",
            "audio_array": audio_array,
            "sample_rate": SAMPLE_RATE,
            "duration_seconds": round(duration, 2),
            "content_hash": content_hash,
            "audio_retained": False,
            "validated_at": time.time(),
        },
    }


def _handle_audio_metadata(payload: Dict) -> Dict[str, Any]:
    """Legacy audio_data / metadata path (MV-FID-001 text pipeline)."""
    if "session_id" not in payload:
        return _reject("MISSING_FIELD", "Required field missing: session_id")

    duration = float(payload.get("duration_seconds", 0))
    fmt = str(payload.get("format", "")).lower()

    dur_check = validate_duration(duration)
    if not dur_check["ok"]:
        return dur_check

    if fmt and fmt not in SUPPORTED_FORMATS:
        return _reject(
            "UNSUPPORTED_FORMAT",
            f"Format '{fmt}' not supported. Accepted: {sorted(SUPPORTED_FORMATS)}",
        )

    audio_data = payload.get("audio_data", "")
    raw = audio_data.encode() if isinstance(audio_data, str) else (audio_data or b"")
    content_hash = hashlib.sha256(raw).hexdigest()[:16]
    clean = audio_cleanup(payload)

    return {
        "ok": True,
        "stage": "L0_INPUT",
        "data": {**clean, "content_hash": content_hash, "validated_at": time.time()},
    }


def validate_duration(duration_seconds: float) -> Dict[str, Any]:
    """Reject audio that is too short or too long."""
    if duration_seconds < MIN_DURATION_SECONDS:
        return _reject(
            "AUDIO_TOO_SHORT",
            f"Audio duration {duration_seconds}s — minimum {MIN_DURATION_SECONDS} seconds required.",
            action="REQUEST_RERECORD",
        )
    if duration_seconds > MAX_DURATION_SECONDS:
        return _reject(
            "AUDIO_TOO_LONG",
            f"Audio duration {duration_seconds}s — maximum {MAX_DURATION_SECONDS} seconds.",
            action="SPLIT_RECORDING",
        )
    return {"ok": True}


def audio_cleanup(payload: Dict) -> Dict:
    """Remove audio bytes from memory immediately after capture."""
    cleaned = dict(payload)
    cleaned.pop("audio_data", None)
    return cleaned


# @req SRS-L0-004 -- normalize audio to 16kHz mono PCM
def _normalize_audio(payload: Dict) -> Tuple:
    """Load and normalize audio to 16kHz mono float32. Returns (array, duration_seconds).

    Accepts _test_audio_array in payload for test injection (bypasses file I/O).
    """
    if "_test_audio_array" in payload:
        arr = payload["_test_audio_array"]
        return arr, len(arr) / float(SAMPLE_RATE)

    if not _AUDIO_PROCESSING_AVAILABLE:
        raise ImportError(
            "librosa and numpy required for audio normalization. "
            "Run: pip install librosa"
        )

    audio_path = payload.get("audio_path")
    if not audio_path:
        raise OSError("audio_path required when source is audio.")

    arr, _ = _librosa.load(audio_path, sr=SAMPLE_RATE, mono=True)
    return arr, len(arr) / float(SAMPLE_RATE)


# @req SRS-L0-003 -- reject >95% silence
def _is_silence(
    audio_array,
    silence_ratio: float = SILENCE_RATIO_THRESHOLD,
    threshold: float = SILENCE_RMS_THRESHOLD,
) -> bool:
    """Return True if >95% of audio frames are below RMS silence threshold."""
    if not _AUDIO_PROCESSING_AVAILABLE or len(audio_array) == 0:
        return False

    frame_len = 1024
    n_frames = max(1, len(audio_array) // frame_len)
    frames = np.array_split(audio_array[: n_frames * frame_len], n_frames)
    silent_count = sum(1 for f in frames if float(np.sqrt(np.mean(f ** 2))) < threshold)
    return (silent_count / n_frames) > silence_ratio


def _reject(error: str, message: str, action: str = "REJECT") -> Dict[str, Any]:
    return {"ok": False, "stage": "L0_INPUT", "error": error,
            "message": message, "action": action}
