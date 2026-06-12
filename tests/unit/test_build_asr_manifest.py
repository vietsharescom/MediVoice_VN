# tests/unit/test_build_asr_manifest.py
# FID-VN-007: ASR fine-tune manifest builder

import json
from pathlib import Path

from scripts.build_asr_manifest import build_manifest, build_pilot_manifest, build_vietmed_manifest


class TestBuildManifest:
    def test_manifest_has_57_entries(self):
        manifest = build_manifest()
        assert len(manifest) == 57

    def test_entries_have_audio_and_text(self):
        manifest = build_manifest()
        for entry in manifest:
            assert "audio" in entry
            assert "text" in entry
            assert entry["text"].strip()

    def test_audio_paths_exist(self):
        manifest = build_manifest()
        for entry in manifest:
            assert Path(entry["audio"]).exists(), entry["audio"]

    def test_unknown_bs_code_skipped(self, tmp_path):
        transcripts = tmp_path / "transcripts.json"
        transcripts.write_text(
            '[{"bs": "XX", "file": "nope.wav", "transcript_gt": "abc"}]',
            encoding="utf-8",
        )
        manifest = build_manifest(transcripts_path=transcripts, audio_root=tmp_path)
        assert manifest == []


class TestBuildVietmedManifest:
    def test_missing_root_returns_empty(self, tmp_path):
        manifest = build_vietmed_manifest(vietmed_root=tmp_path / "nope")
        assert manifest == []

    def test_reads_metadata_and_resolves_audio(self, tmp_path):
        split_dir = tmp_path / "train"
        audio_dir = split_dir / "audio"
        audio_dir.mkdir(parents=True)
        (audio_dir / "train_00000.wav").write_bytes(b"")
        (audio_dir / "train_00001.wav").write_bytes(b"")
        metadata = split_dir / "metadata.jsonl"
        metadata.write_text(
            "\n".join([
                json.dumps({"audio": "train_00000.wav", "text": "xin chao"}),
                json.dumps({"audio": "train_00001.wav", "sentence": "cam on"}),
                json.dumps({"audio": "missing.wav", "text": "skip me"}),
                json.dumps({"audio": "train_00000.wav"}),
            ]),
            encoding="utf-8",
        )

        manifest = build_vietmed_manifest(vietmed_root=tmp_path)
        assert len(manifest) == 2
        texts = {entry["text"] for entry in manifest}
        assert texts == {"xin chao", "cam on"}


class TestBuildPilotManifest:
    def test_missing_dir_returns_empty(self, tmp_path):
        manifest = build_pilot_manifest(tmp_path / "nope")
        assert manifest == []

    def test_pairs_wav_with_txt_and_json(self, tmp_path):
        (tmp_path / "clip1.wav").write_bytes(b"")
        (tmp_path / "clip1.txt").write_text("benh nhan dau dau", encoding="utf-8")

        (tmp_path / "clip2.wav").write_bytes(b"")
        (tmp_path / "clip2.json").write_text(
            json.dumps({"text": "ho sot ba ngay"}), encoding="utf-8"
        )

        (tmp_path / "clip3.wav").write_bytes(b"")  # no transcript -> skipped

        manifest = build_pilot_manifest(tmp_path)
        assert len(manifest) == 2
        texts = {entry["text"] for entry in manifest}
        assert texts == {"benh nhan dau dau", "ho sot ba ngay"}
