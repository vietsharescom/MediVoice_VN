# tests/unit/test_save_recording.py
# CT-057: lưu mọi lần /api/transcribe vào data/recordings/ (src/core/l0_normalize.py)

import json

from src.core import l0_normalize


class TestSaveRecording:
    def test_copies_audio_and_metadata(self, tmp_path, monkeypatch):
        recordings_dir = tmp_path / "recordings"
        monkeypatch.setattr(l0_normalize, "_RECORDINGS_DIR", recordings_dir)

        wav_path = tmp_path / "audio.wav"
        wav_path.write_bytes(b"RIFF....")

        metadata = {
            "transcript_raw": "benh nhan dau dau",
            "transcript_corrected": "benh nhan dau dau",
            "form_data": {"chan_doan": "dau dau"},
            "confidence_scores": {"chan_doan": 0.9},
            "overall_confidence": 0.9,
            "route": "lam_sang",
            "dvp_specialty": "noi_khoa",
            "dvp_region": "auto",
            "dialect_subs": [],
        }

        l0_normalize.save_recording(str(wav_path), "REC-001", metadata)

        wavs = list(recordings_dir.glob("*.wav"))
        jsons = list(recordings_dir.glob("*.json"))
        assert len(wavs) == 1
        assert len(jsons) == 1
        assert wavs[0].stem == jsons[0].stem
        assert "REC-001" in wavs[0].stem

        saved = json.loads(jsons[0].read_text(encoding="utf-8"))
        assert saved == metadata

        # original file untouched (copy, not move) — purge_audio() still deletes it after
        assert wav_path.exists()

    def test_noop_when_wav_path_missing(self, tmp_path, monkeypatch):
        recordings_dir = tmp_path / "recordings"
        monkeypatch.setattr(l0_normalize, "_RECORDINGS_DIR", recordings_dir)

        l0_normalize.save_recording(str(tmp_path / "does_not_exist.wav"), "REC-002", {})

        assert not recordings_dir.exists()

    def test_noop_when_wav_path_none(self, tmp_path, monkeypatch):
        recordings_dir = tmp_path / "recordings"
        monkeypatch.setattr(l0_normalize, "_RECORDINGS_DIR", recordings_dir)

        l0_normalize.save_recording(None, "REC-003", {})

        assert not recordings_dir.exists()
