# L0 — Audio Normalize
# Input: audio file (any format) | Output: WAV 16kHz mono numpy array + temp file
# FROZEN PIPELINE LAYER — change only via FID

from __future__ import annotations
import os
import tempfile
import numpy as np
from pathlib import Path


TARGET_SR = 16000
CHUNK_DURATION = 10.0   # seconds
OVERLAP = 2.0           # seconds overlap between chunks


def normalize(audio_path: str | Path) -> tuple[np.ndarray, str]:
    """
    Load bất kỳ audio format nào → 16kHz mono numpy array.
    Returns: (audio_array, tmp_wav_path)
    tmp_wav_path là file WAV 16kHz mono đã normalize, caller xóa sau khi dùng.
    """
    import soundfile as sf
    import librosa

    audio_path = str(audio_path)
    audio, sr = librosa.load(audio_path, sr=TARGET_SR, mono=True)

    # Write to temp WAV
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    sf.write(tmp.name, audio, TARGET_SR, subtype="PCM_16")
    tmp.close()

    return audio, tmp.name


def chunk_audio(audio: np.ndarray, sr: int = TARGET_SR) -> list[np.ndarray]:
    """Chia audio thành chunks 10s với overlap 2s cho streaming ASR."""
    chunk_samples = int(CHUNK_DURATION * sr)
    overlap_samples = int(OVERLAP * sr)
    step = chunk_samples - overlap_samples

    chunks = []
    start = 0
    while start < len(audio):
        end = min(start + chunk_samples, len(audio))
        chunks.append(audio[start:end])
        if end == len(audio):
            break
        start += step

    return chunks


def has_speech(audio: np.ndarray, threshold: float = 0.01) -> bool:
    """VAD đơn giản: kiểm tra RMS energy."""
    rms = np.sqrt(np.mean(audio ** 2))
    return float(rms) > threshold
