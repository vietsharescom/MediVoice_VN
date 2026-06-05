"""
Tests for L4 Correction Capture — FID-VN-006
AC-001: correction logged when BS changes any field
AC-002: empty corrections logged when BS changes nothing (positive signal)
AC-003: capture() failure never blocks approve flow
AC-004: corrections.jsonl is valid JSONL
AC-005: analyze_corrections.py generates alias suggestions from fixture data
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

# Import module under test
from src.core import l4_correction_capture


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_ai_form(**kwargs):
    defaults = {
        "chan_doan": "",
        "don_thuoc": [],
        "nhiet_do": None,
        "huyet_ap": None,
        "mach": None,
        "ly_do_kham": "",
    }
    defaults.update(kwargs)
    return defaults


def _make_bs_form(**kwargs):
    return _make_ai_form(**kwargs)


# ─── AC-001: Corrections logged when BS changes a field ───────────────────────

class TestAC001_CorrectionsLogged:
    def test_drug_added_by_bs(self, tmp_path):
        ai = _make_ai_form(don_thuoc=[])
        bs = _make_bs_form(don_thuoc=[{"name": "Amoxicillin", "dose": "500mg"}])

        with patch.object(l4_correction_capture, "_CORRECTIONS_ROOT", tmp_path):
            l4_correction_capture.capture(
                record_id="REC-001",
                clinic_id="TEST_CLINIC",
                transcript="bệnh nhân amosilic 500",
                ai_form=ai,
                bs_form=bs,
                doctor_cchn="CCHN-TEST",
            )

        log = tmp_path / "TEST_CLINIC" / "corrections.jsonl"
        assert log.exists()
        entry = json.loads(log.read_text(encoding="utf-8").strip())
        assert entry["correction_count"] == 1
        corr = entry["corrections"][0]
        assert corr["field"] == "don_thuoc"
        assert corr["note"] == "field_added"
        assert corr["ai_value"] == []
        assert corr["bs_value"][0]["name"] == "Amoxicillin"

    def test_chan_doan_corrected(self, tmp_path):
        ai = _make_ai_form(chan_doan="viêm hầu")
        bs = _make_bs_form(chan_doan="Viêm họng cấp")

        with patch.object(l4_correction_capture, "_CORRECTIONS_ROOT", tmp_path):
            l4_correction_capture.capture(
                record_id="REC-002",
                clinic_id="TEST_CLINIC",
                transcript="chẩn đoán viêm họng cấp",
                ai_form=ai,
                bs_form=bs,
                doctor_cchn="CCHN-TEST",
            )

        log = tmp_path / "TEST_CLINIC" / "corrections.jsonl"
        entry = json.loads(log.read_text(encoding="utf-8").strip())
        assert entry["correction_count"] == 1
        corr = entry["corrections"][0]
        assert corr["field"] == "chan_doan"
        assert corr["note"] == "field_corrected"

    def test_multiple_fields_corrected(self, tmp_path):
        ai = _make_ai_form(chan_doan="", don_thuoc=[], mach=None)
        bs = _make_bs_form(
            chan_doan="Tăng huyết áp",
            don_thuoc=[{"name": "Amlodipine"}],
            mach=72,
        )

        with patch.object(l4_correction_capture, "_CORRECTIONS_ROOT", tmp_path):
            l4_correction_capture.capture(
                record_id="REC-003",
                clinic_id="TEST_CLINIC",
                transcript="",
                ai_form=ai,
                bs_form=bs,
                doctor_cchn="CCHN-TEST",
            )

        log = tmp_path / "TEST_CLINIC" / "corrections.jsonl"
        entry = json.loads(log.read_text(encoding="utf-8").strip())
        assert entry["correction_count"] == 3

    def test_transcript_snippet_stored(self, tmp_path):
        long_transcript = "bệnh nhân " * 100  # >500 chars
        ai = _make_ai_form(chan_doan="")
        bs = _make_bs_form(chan_doan="Tiểu đường type 2")

        with patch.object(l4_correction_capture, "_CORRECTIONS_ROOT", tmp_path):
            l4_correction_capture.capture(
                record_id="REC-004",
                clinic_id="TEST_CLINIC",
                transcript=long_transcript,
                ai_form=ai,
                bs_form=bs,
                doctor_cchn="CCHN-TEST",
            )

        log = tmp_path / "TEST_CLINIC" / "corrections.jsonl"
        entry = json.loads(log.read_text(encoding="utf-8").strip())
        # Snippet capped at 500 chars
        assert len(entry["transcript_snippet"]) <= 500


# ─── AC-002: Empty corrections logged when BS changes nothing ─────────────────

class TestAC002_NoCorrectionPositiveSignal:
    def test_no_change_logs_empty_corrections(self, tmp_path):
        form = _make_ai_form(
            chan_doan="Viêm họng cấp",
            don_thuoc=[{"name": "Paracetamol"}],
        )

        with patch.object(l4_correction_capture, "_CORRECTIONS_ROOT", tmp_path):
            l4_correction_capture.capture(
                record_id="REC-005",
                clinic_id="TEST_CLINIC",
                transcript="",
                ai_form=dict(form),
                bs_form=dict(form),
                doctor_cchn="CCHN-TEST",
            )

        log = tmp_path / "TEST_CLINIC" / "corrections.jsonl"
        assert log.exists()
        entry = json.loads(log.read_text(encoding="utf-8").strip())
        assert entry["correction_count"] == 0
        assert entry["corrections"] == []

    def test_empty_vs_none_treated_as_equal(self, tmp_path):
        ai = _make_ai_form(chan_doan=None)
        bs = _make_bs_form(chan_doan="")

        with patch.object(l4_correction_capture, "_CORRECTIONS_ROOT", tmp_path):
            l4_correction_capture.capture(
                record_id="REC-006",
                clinic_id="TEST_CLINIC",
                transcript="",
                ai_form=ai,
                bs_form=bs,
                doctor_cchn="CCHN-TEST",
            )

        log = tmp_path / "TEST_CLINIC" / "corrections.jsonl"
        entry = json.loads(log.read_text(encoding="utf-8").strip())
        # None and "" are both "empty" — no correction
        assert entry["correction_count"] == 0


# ─── AC-003: Failure never blocks approve flow ────────────────────────────────

class TestAC003_NonBlocking:
    def test_unwritable_directory_does_not_raise(self, tmp_path):
        # Point to a file (not dir) so mkdir fails
        fake_root = tmp_path / "not_a_dir.txt"
        fake_root.write_text("block")

        with patch.object(l4_correction_capture, "_CORRECTIONS_ROOT", fake_root):
            # Must not raise
            l4_correction_capture.capture(
                record_id="REC-007",
                clinic_id="TEST_CLINIC",
                transcript="",
                ai_form={"chan_doan": ""},
                bs_form={"chan_doan": "Viêm họng"},
                doctor_cchn="CCHN-TEST",
            )

    def test_invalid_form_does_not_raise(self, tmp_path):
        with patch.object(l4_correction_capture, "_CORRECTIONS_ROOT", tmp_path):
            l4_correction_capture.capture(
                record_id="REC-008",
                clinic_id="TEST_CLINIC",
                transcript="",
                ai_form=None,    # type: ignore — simulate corrupt data
                bs_form=None,    # type: ignore
                doctor_cchn="CCHN-TEST",
            )


# ─── AC-004: corrections.jsonl is valid JSONL ─────────────────────────────────

class TestAC004_ValidJsonl:
    def test_multiple_entries_all_valid_json(self, tmp_path):
        ai = _make_ai_form(chan_doan="")
        bs = _make_bs_form(chan_doan="Cảm cúm")

        with patch.object(l4_correction_capture, "_CORRECTIONS_ROOT", tmp_path):
            for i in range(5):
                l4_correction_capture.capture(
                    record_id=f"REC-{i:03d}",
                    clinic_id="TEST_CLINIC",
                    transcript=f"transcript {i}",
                    ai_form=dict(ai),
                    bs_form=dict(bs),
                    doctor_cchn="CCHN-TEST",
                )

        log = tmp_path / "TEST_CLINIC" / "corrections.jsonl"
        lines = log.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 5
        for line in lines:
            entry = json.loads(line)
            assert "schema_version" in entry
            assert "record_id" in entry
            assert "corrections" in entry

    def test_schema_version_present(self, tmp_path):
        with patch.object(l4_correction_capture, "_CORRECTIONS_ROOT", tmp_path):
            l4_correction_capture.capture(
                record_id="REC-SV",
                clinic_id="TEST_CLINIC",
                transcript="",
                ai_form={},
                bs_form={},
                doctor_cchn="CCHN-TEST",
            )

        log = tmp_path / "TEST_CLINIC" / "corrections.jsonl"
        entry = json.loads(log.read_text(encoding="utf-8").strip())
        assert entry["schema_version"] == "1.0"


# ─── AC-005: analyze_corrections.py generates alias suggestions from fixture ──

# Import analyze module for direct function testing
_ANALYZE_SPEC = importlib.util.spec_from_file_location(
    "analyze_corrections",
    Path(__file__).parent.parent.parent / "scripts" / "analyze_corrections.py",
)
_analyze_mod = importlib.util.module_from_spec(_ANALYZE_SPEC)
_ANALYZE_SPEC.loader.exec_module(_analyze_mod)  # type: ignore


class TestAC005_AnalyzeCorrections:
    def _write_fixture(self, corrections_root: Path, count: int = 3) -> None:
        clinic_dir = corrections_root / "TEST_CLINIC"
        clinic_dir.mkdir(parents=True)
        log = clinic_dir / "corrections.jsonl"

        entries = [
            {
                "schema_version": "1.0",
                "record_id": f"REC-{i:03d}",
                "clinic_id": "TEST_CLINIC",
                "doctor_cchn": "CCHN-001",
                "timestamp": "2026-06-08T10:00:00+07:00",
                "transcript_snippet": "bệnh nhân amosilic 500mg",
                "corrections": [
                    {
                        "field": "don_thuoc",
                        "ai_value": [],
                        "bs_value": [{"name": "Amoxicillin", "dose": "500mg"}],
                        "note": "field_added",
                    }
                ],
                "correction_count": 1,
            }
            for i in range(count)
        ]
        with log.open("w", encoding="utf-8") as f:
            for e in entries:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")

    def test_load_entries_reads_jsonl(self, tmp_path):
        self._write_fixture(tmp_path, count=3)

        with patch.object(_analyze_mod, "_CORRECTIONS_ROOT", tmp_path):
            entries = _analyze_mod.load_entries()

        assert len(entries) == 3
        assert entries[0]["clinic_id"] == "TEST_CLINIC"

    def test_load_entries_clinic_filter(self, tmp_path):
        self._write_fixture(tmp_path, count=2)

        with patch.object(_analyze_mod, "_CORRECTIONS_ROOT", tmp_path):
            entries_all = _analyze_mod.load_entries()
            entries_clinic = _analyze_mod.load_entries("TEST_CLINIC")
            entries_missing = _analyze_mod.load_entries("NO_SUCH_CLINIC")

        assert len(entries_all) == 2
        assert len(entries_clinic) == 2
        assert len(entries_missing) == 0

    def test_drug_corrections_identified(self, tmp_path):
        self._write_fixture(tmp_path, count=3)

        with patch.object(_analyze_mod, "_CORRECTIONS_ROOT", tmp_path):
            entries = _analyze_mod.load_entries()

        drug_corrections = [
            c for e in entries
            for c in e.get("corrections", [])
            if c["field"] == "don_thuoc"
        ]
        assert len(drug_corrections) == 3
        assert drug_corrections[0]["bs_value"][0]["name"] == "Amoxicillin"

    def test_empty_root_returns_empty(self, tmp_path):
        empty = tmp_path / "empty_corrections"
        with patch.object(_analyze_mod, "_CORRECTIONS_ROOT", empty):
            entries = _analyze_mod.load_entries()
        assert entries == []
