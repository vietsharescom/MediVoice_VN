# tests/unit/test_build_asr_manifest.py
# FID-VN-007: ASR fine-tune manifest builder

from pathlib import Path

from scripts.build_asr_manifest import build_manifest


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
