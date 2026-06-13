# tests/unit/test_pilot_audio_retention.py
# TRAIN-001: opt-in pilot audio retention (src/core/l0_normalize.py)

import json

from src.core import l0_normalize


class TestPilotAudioRetentionEnabled:
    def test_disabled_by_default(self, tmp_path, monkeypatch):
        config_path = tmp_path / "facility_config.json"
        config_path.write_text(json.dumps({"pilot_audio_retention": False}), encoding="utf-8")
        monkeypatch.setattr(l0_normalize, "_FACILITY_CONFIG_PATH", config_path)

        assert l0_normalize.pilot_audio_retention_enabled() is False

    def test_enabled_when_flag_true(self, tmp_path, monkeypatch):
        config_path = tmp_path / "facility_config.json"
        config_path.write_text(json.dumps({"pilot_audio_retention": True}), encoding="utf-8")
        monkeypatch.setattr(l0_normalize, "_FACILITY_CONFIG_PATH", config_path)

        assert l0_normalize.pilot_audio_retention_enabled() is True

    def test_missing_config_returns_false(self, tmp_path, monkeypatch):
        monkeypatch.setattr(l0_normalize, "_FACILITY_CONFIG_PATH", tmp_path / "missing.json")

        assert l0_normalize.pilot_audio_retention_enabled() is False


class TestRetainPilotAudio:
    def test_noop_when_disabled(self, tmp_path, monkeypatch):
        config_path = tmp_path / "facility_config.json"
        config_path.write_text(json.dumps({"pilot_audio_retention": False}), encoding="utf-8")
        monkeypatch.setattr(l0_normalize, "_FACILITY_CONFIG_PATH", config_path)
        pilot_dir = tmp_path / "pilot"
        monkeypatch.setattr(l0_normalize, "_PILOT_AUDIO_DIR", pilot_dir)

        wav_path = tmp_path / "audio.wav"
        wav_path.write_bytes(b"RIFF....")

        l0_normalize.retain_pilot_audio(str(wav_path), "benh nhan dau dau")

        assert not pilot_dir.exists()

    def test_copies_audio_and_transcript_when_enabled(self, tmp_path, monkeypatch):
        config_path = tmp_path / "facility_config.json"
        config_path.write_text(json.dumps({"pilot_audio_retention": True}), encoding="utf-8")
        monkeypatch.setattr(l0_normalize, "_FACILITY_CONFIG_PATH", config_path)
        pilot_dir = tmp_path / "pilot"
        monkeypatch.setattr(l0_normalize, "_PILOT_AUDIO_DIR", pilot_dir)

        wav_path = tmp_path / "audio.wav"
        wav_path.write_bytes(b"RIFF....")

        l0_normalize.retain_pilot_audio(str(wav_path), "benh nhan dau dau")

        wavs = list(pilot_dir.glob("*.wav"))
        txts = list(pilot_dir.glob("*.txt"))
        assert len(wavs) == 1
        assert len(txts) == 1
        assert wavs[0].stem == txts[0].stem
        assert txts[0].read_text(encoding="utf-8") == "benh nhan dau dau"
        # original file untouched (copy, not move) — purge_audio() still deletes it after
        assert wav_path.exists()

    def test_noop_when_wav_path_missing(self, tmp_path, monkeypatch):
        config_path = tmp_path / "facility_config.json"
        config_path.write_text(json.dumps({"pilot_audio_retention": True}), encoding="utf-8")
        monkeypatch.setattr(l0_normalize, "_FACILITY_CONFIG_PATH", config_path)
        pilot_dir = tmp_path / "pilot"
        monkeypatch.setattr(l0_normalize, "_PILOT_AUDIO_DIR", pilot_dir)

        l0_normalize.retain_pilot_audio(str(tmp_path / "does_not_exist.wav"), "text")

        assert not pilot_dir.exists()

    def test_noop_when_wav_path_none(self, tmp_path, monkeypatch):
        config_path = tmp_path / "facility_config.json"
        config_path.write_text(json.dumps({"pilot_audio_retention": True}), encoding="utf-8")
        monkeypatch.setattr(l0_normalize, "_FACILITY_CONFIG_PATH", config_path)
        pilot_dir = tmp_path / "pilot"
        monkeypatch.setattr(l0_normalize, "_PILOT_AUDIO_DIR", pilot_dir)

        l0_normalize.retain_pilot_audio(None, "text")

        assert not pilot_dir.exists()
