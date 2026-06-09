# tests/unit/test_l0_vad_chunk.py
# A2-VAD-CHUNK unit tests — FID-VN-010
# Pure function tests + mock silero_vad (không load model thật)

import sys
import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from src.core.l0_normalize import (
    TARGET_SR,
    _merge_short_gaps,
    chunk_audio,
    vad_chunk_audio,
)

SR = TARGET_SR  # 16000


# ---------------------------------------------------------------------------
# _merge_short_gaps — pure function
# ---------------------------------------------------------------------------

class TestMergeShortGaps:
    def test_empty_input(self):
        assert _merge_short_gaps([], gap_samples=8000) == []

    def test_single_segment_unchanged(self):
        ts = [{"start": 0, "end": 8000}]
        result = _merge_short_gaps(ts, gap_samples=8000)
        assert result == [{"start": 0, "end": 8000}]

    def test_two_segments_far_apart_stay_separate(self):
        # Gap = 9000 samples > gap_samples=8000 → không merge
        ts = [{"start": 0, "end": 4000}, {"start": 13000, "end": 17000}]
        result = _merge_short_gaps(ts, gap_samples=8000)
        assert len(result) == 2

    def test_two_segments_close_get_merged(self):
        # Gap = 3000 samples < gap_samples=8000 → merge
        ts = [{"start": 0, "end": 4000}, {"start": 7000, "end": 11000}]
        result = _merge_short_gaps(ts, gap_samples=8000)
        assert len(result) == 1
        assert result[0]["start"] == 0
        assert result[0]["end"] == 11000

    def test_first_two_merge_third_stays(self):
        ts = [
            {"start": 0, "end": 4000},
            {"start": 5000, "end": 9000},    # gap=1000 < 8000 → merge
            {"start": 25000, "end": 30000},  # gap=16000 > 8000 → stay
        ]
        result = _merge_short_gaps(ts, gap_samples=8000)
        assert len(result) == 2
        assert result[0] == {"start": 0, "end": 9000}
        assert result[1] == {"start": 25000, "end": 30000}

    def test_gap_exactly_at_boundary_not_merged(self):
        # Gap = gap_samples chính xác → không merge (strict <)
        ts = [{"start": 0, "end": 4000}, {"start": 12000, "end": 16000}]
        result = _merge_short_gaps(ts, gap_samples=8000)  # gap = 8000
        assert len(result) == 2

    def test_does_not_mutate_input(self):
        ts = [{"start": 0, "end": 4000}, {"start": 5000, "end": 9000}]
        original = [t.copy() for t in ts]
        _merge_short_gaps(ts, gap_samples=8000)
        assert ts == original


# ---------------------------------------------------------------------------
# vad_chunk_audio — patch silero_vad at module attribute level
# Since silero_vad is imported inside vad_chunk_audio with
# "from silero_vad import ...", we patch the silero_vad MODULE attributes
# so the fresh import inside the function gets our mocks.
# ---------------------------------------------------------------------------

def _make_audio(seconds: float) -> np.ndarray:
    return np.zeros(int(seconds * SR), dtype=np.float32)


def _patch_silero(timestamps: list[dict]):
    """Patch silero_vad module-level functions used inside vad_chunk_audio."""
    mock_model = MagicMock()

    def mock_get_speech_timestamps(audio_tensor, model, **kwargs):
        return timestamps

    return (
        patch("silero_vad.load_silero_vad", return_value=mock_model),
        patch("silero_vad.get_speech_timestamps", side_effect=mock_get_speech_timestamps),
    )


class TestVadChunkAudio:
    def test_no_speech_returns_whole_audio_as_one_chunk(self):
        audio = _make_audio(2.0)
        p1, p2 = _patch_silero([])
        with p1, p2:
            result = vad_chunk_audio(audio, sr=SR)
        assert len(result) == 1
        assert np.array_equal(result[0], audio)

    def test_single_speech_segment_returns_one_chunk(self):
        audio = _make_audio(2.0)
        ts = [{"start": 0, "end": len(audio)}]
        p1, p2 = _patch_silero(ts)
        with p1, p2:
            result = vad_chunk_audio(audio, sr=SR)
        assert len(result) == 1

    def test_two_separate_utterances_return_two_chunks(self):
        audio = _make_audio(4.0)
        # Gap 2s > gap_ms=500ms → không merge
        ts = [
            {"start": 0, "end": SR},
            {"start": 3 * SR, "end": 4 * SR},
        ]
        p1, p2 = _patch_silero(ts)
        with p1, p2:
            result = vad_chunk_audio(audio, sr=SR, gap_ms=500.0)
        assert len(result) == 2

    def test_close_utterances_merged_into_one_chunk(self):
        audio = _make_audio(4.0)
        # Gap = 200ms < gap_ms=500ms → merge
        ts = [
            {"start": 0, "end": SR},
            {"start": SR + int(0.2 * SR), "end": 2 * SR},
        ]
        p1, p2 = _patch_silero(ts)
        with p1, p2:
            result = vad_chunk_audio(audio, sr=SR, gap_ms=500.0)
        assert len(result) == 1

    def test_segment_exceeding_max_chunk_split_into_two(self):
        audio = _make_audio(25.0)
        ts = [{"start": 0, "end": len(audio)}]
        p1, p2 = _patch_silero(ts)
        with p1, p2:
            result = vad_chunk_audio(audio, sr=SR, max_chunk_s=20.0)
        assert len(result) == 2

    def test_segment_within_max_chunk_not_split(self):
        audio = _make_audio(15.0)
        ts = [{"start": 0, "end": len(audio)}]
        p1, p2 = _patch_silero(ts)
        with p1, p2:
            result = vad_chunk_audio(audio, sr=SR, max_chunk_s=20.0)
        assert len(result) == 1

    def test_all_chunks_are_nonempty(self):
        audio = _make_audio(3.0)
        ts = [{"start": 0, "end": SR}, {"start": 2 * SR, "end": 3 * SR}]
        p1, p2 = _patch_silero(ts)
        with p1, p2:
            result = vad_chunk_audio(audio, sr=SR, gap_ms=500.0)
        for chunk in result:
            assert len(chunk) > 0

    def test_all_chunks_are_numpy_arrays(self):
        audio = _make_audio(2.0)
        ts = [{"start": 0, "end": len(audio)}]
        p1, p2 = _patch_silero(ts)
        with p1, p2:
            result = vad_chunk_audio(audio, sr=SR)
        for chunk in result:
            assert isinstance(chunk, np.ndarray)

    def test_fallback_when_model_load_raises(self):
        audio = _make_audio(5.0)
        with patch("silero_vad.load_silero_vad", side_effect=RuntimeError("model fail")):
            result = vad_chunk_audio(audio, sr=SR)
        # Fallback → fixed chunk_audio()
        expected = chunk_audio(audio, SR)
        assert len(result) == len(expected)
        assert all(isinstance(c, np.ndarray) for c in result)

    def test_fallback_when_get_speech_timestamps_raises(self):
        audio = _make_audio(5.0)
        mock_model = MagicMock()
        with patch("silero_vad.load_silero_vad", return_value=mock_model), \
             patch("silero_vad.get_speech_timestamps", side_effect=RuntimeError("ts fail")):
            result = vad_chunk_audio(audio, sr=SR)
        assert isinstance(result, list)
        assert all(isinstance(c, np.ndarray) for c in result)

    def test_empty_audio_returns_empty(self):
        audio = np.array([], dtype=np.float32)
        p1, p2 = _patch_silero([])
        with p1, p2:
            result = vad_chunk_audio(audio, sr=SR)
        assert result == []
