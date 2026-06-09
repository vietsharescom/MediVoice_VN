# L0 — Audio Normalize + VAD Chunking
# Input: audio file (any format) | Output: WAV 16kHz mono numpy array + temp file
# FROZEN PIPELINE LAYER — change only via FID
# A2-VAD-CHUNK: FID-VN-010 — silence-aware chunking (replaces fixed 10s chunks)

from __future__ import annotations
import logging
import os
import tempfile
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

TARGET_SR = 16000
CHUNK_DURATION = 10.0   # seconds — fallback fixed-chunk duration
OVERLAP = 2.0           # seconds overlap — fallback only
VAD_MAX_CHUNK_S = 20.0  # max chunk duration for VAD mode (PhoWhisper limit)
VAD_GAP_MS = 500.0      # merge speech segments with silence gap < 500ms


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


def _merge_short_gaps(timestamps: list[dict], gap_samples: int) -> list[dict]:
    """
    Merge speech segments separated by silence < gap_samples.
    Prevents "Kê Ciprofloxacin [300ms pause] 500mg" từ bị split thành 2 chunks.
    """
    if not timestamps:
        return []
    merged = [timestamps[0].copy()]
    for ts in timestamps[1:]:
        if ts["start"] - merged[-1]["end"] < gap_samples:
            merged[-1]["end"] = ts["end"]
        else:
            merged.append(ts.copy())
    return merged


def vad_chunk_audio(
    audio: np.ndarray,
    sr: int = TARGET_SR,
    max_chunk_s: float = VAD_MAX_CHUNK_S,
    gap_ms: float = VAD_GAP_MS,
) -> list[np.ndarray]:
    """
    Chunk audio theo điểm im lặng tự nhiên (A2-VAD-CHUNK, FID-VN-010).
    Mỗi chunk = 1 utterance hoàn chỉnh → không cắt giữa câu BS.
    Max chunk 20s để PhoWhisper không bị truncate.
    Nếu silero-vad không load được → fallback về chunk_audio() cũ (fixed 10s).
    """
    try:
        import torch
        from silero_vad import load_silero_vad, get_speech_timestamps

        model = load_silero_vad()
        audio_tensor = torch.from_numpy(audio.astype(np.float32))

        timestamps = get_speech_timestamps(
            audio_tensor,
            model,
            sampling_rate=sr,
            min_speech_duration_ms=200,
            min_silence_duration_ms=int(gap_ms),
            speech_pad_ms=50,
        )

        if not timestamps:
            # No speech detected — trả về toàn bộ audio làm 1 chunk
            return [audio] if len(audio) > 0 else []

        gap_samples = int(gap_ms / 1000 * sr)
        merged = _merge_short_gaps(timestamps, gap_samples)

        chunks = []
        max_samples = int(max_chunk_s * sr)
        for seg in merged:
            chunk = audio[seg["start"]:seg["end"]]
            if len(chunk) <= max_samples:
                chunks.append(chunk)
            else:
                # Segment quá dài → split tại midpoint
                mid = len(chunk) // 2
                chunks.append(chunk[:mid])
                chunks.append(chunk[mid:])

        return [c for c in chunks if len(c) > 0]

    except Exception as e:
        logger.warning(f"VAD chunk failed ({e}), falling back to fixed chunk_audio()")
        return chunk_audio(audio, sr)


def has_speech(audio: np.ndarray, threshold: float = 0.01) -> bool:
    """VAD đơn giản: kiểm tra RMS energy."""
    rms = np.sqrt(np.mean(audio ** 2))
    return float(rms) > threshold


def purge_audio(wav_path: str | None) -> None:
    """
    Xóa audio khỏi disk sau khi transcription hoàn tất.
    SRS-L0-003: bắt buộc xóa để tuân thủ NĐ13/2023 data minimization.
    Gọi trong finally block — không được để audio lại sau khi xử lý xong.
    """
    if wav_path and os.path.exists(wav_path):
        try:
            os.unlink(wav_path)
        except OSError:
            pass  # best-effort — không crash pipeline nếu file đã bị xóa
