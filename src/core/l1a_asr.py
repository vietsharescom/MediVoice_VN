# L1a — PhoWhisper ASR Streaming
# Input: WAV 16kHz mono | Output: raw transcript (chunked 10s)
# Model: vinai/PhoWhisper-small (BSD-3-Clause, commercial OK)
# FROZEN PIPELINE LAYER

from __future__ import annotations
import logging
import numpy as np

logger = logging.getLogger(__name__)

MODEL_ID = "vinai/PhoWhisper-small"
_pipeline = None   # lazy-loaded


def _load_pipeline():
    """Lazy load PhoWhisper — chỉ load khi cần, tốn ~1.5GB RAM."""
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    try:
        from transformers import pipeline as hf_pipeline
        import torch

        device = 0 if torch.cuda.is_available() else -1
        _pipeline = hf_pipeline(
            "automatic-speech-recognition",
            model=MODEL_ID,
            device=device,
            chunk_length_s=10,
            stride_length_s=2,
        )
        logger.info(f"PhoWhisper loaded: {MODEL_ID} (device={device})")
    except Exception as e:
        logger.warning(f"PhoWhisper không load được: {e}. ASR sẽ trả về rỗng.")
        _pipeline = None

    return _pipeline


def transcribe(audio: np.ndarray, sample_rate: int = 16000) -> str:
    """
    Chuyển audio numpy array → transcript tiếng Việt.
    Nếu model chưa load được, trả về chuỗi rỗng (không crash pipeline).
    """
    pipe = _load_pipeline()
    if pipe is None:
        return ""

    try:
        result = pipe({"array": audio.astype(np.float32), "sampling_rate": sample_rate})
        return result.get("text", "").strip()
    except Exception as e:
        logger.error(f"ASR error: {e}")
        return ""


def transcribe_file(wav_path: str) -> str:
    """Transcribe từ file WAV path."""
    import soundfile as sf
    audio, sr = sf.read(wav_path, dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    return transcribe(audio, sr)


def transcribe_chunks(chunks: list[np.ndarray], sample_rate: int = 16000) -> str:
    """
    Transcribe danh sách chunks, ghép kết quả.
    Dùng cho streaming mode với L0.chunk_audio.
    """
    texts = [transcribe(c, sample_rate) for c in chunks if len(c) > 0]
    return " ".join(t for t in texts if t)
