"""
Tests for src/core/l9a_pdf_export.py
@verifies GAP-004 | P0.2.L9a
Requires: reportlab (in requirements-prod.txt)
"""
from __future__ import annotations
import sys
import importlib.util
from pathlib import Path

import pytest

# Load BenhAnNgoaiTru and related classes from data/reference (same as l6_generate_form.py)
_REPO = Path(__file__).parent.parent.parent
_DATA_REF = _REPO / "data" / "reference"
_spec = importlib.util.spec_from_file_location("mau15bv01", _DATA_REF / "MAU_15BV01_fields.py")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

BenhAnNgoaiTru = _mod.BenhAnNgoaiTru
ThuocKe = _mod.ThuocKe

sys.path.insert(0, str(_REPO / "src"))
from core.l9a_pdf_export import export_pdf


def _minimal_benh_an(record_id: str = "test-1234-5678-abcd") -> BenhAnNgoaiTru:
    ba = BenhAnNgoaiTru(record_id=record_id, doctor_cchn="CCHN-12345")
    ba.hanh_chinh.ho_va_ten = "Nguyễn Văn A"
    ba.ly_do.ly_do = "Đau đầu"
    ba.kham_benh.chan_doan_ra_vien = "Viêm họng cấp"
    ba.kham_benh.ma_icd10 = "J02"
    return ba


# ── File creation ─────────────────────────────────────────────────

class TestExportPdfFileCreation:
    def test_returns_string_path(self, tmp_path):
        ba = _minimal_benh_an()
        result = export_pdf(ba, output_dir=tmp_path)
        assert isinstance(result, str)

    def test_file_exists_after_export(self, tmp_path):
        ba = _minimal_benh_an()
        path = export_pdf(ba, output_dir=tmp_path)
        assert Path(path).exists()

    def test_filename_starts_with_ba(self, tmp_path):
        ba = _minimal_benh_an()
        path = export_pdf(ba, output_dir=tmp_path)
        assert Path(path).name.startswith("BA_")

    def test_filename_contains_record_id_prefix(self, tmp_path):
        ba = _minimal_benh_an(record_id="abcd1234-xxxx")
        path = export_pdf(ba, output_dir=tmp_path)
        assert "abcd1234" in Path(path).name

    def test_output_in_specified_directory(self, tmp_path):
        ba = _minimal_benh_an()
        path = export_pdf(ba, output_dir=tmp_path)
        assert Path(path).parent == tmp_path

    def test_creates_output_dir_if_missing(self, tmp_path):
        out_dir = tmp_path / "new" / "nested"
        ba = _minimal_benh_an()
        path = export_pdf(ba, output_dir=out_dir)
        assert out_dir.exists()
        assert Path(path).exists()

    def test_pdf_extension(self, tmp_path):
        ba = _minimal_benh_an()
        path = export_pdf(ba, output_dir=tmp_path)
        assert path.endswith(".pdf")

    def test_file_is_nonempty(self, tmp_path):
        ba = _minimal_benh_an()
        path = export_pdf(ba, output_dir=tmp_path)
        assert Path(path).stat().st_size > 0

    def test_file_is_valid_pdf(self, tmp_path):
        ba = _minimal_benh_an()
        path = export_pdf(ba, output_dir=tmp_path)
        with open(path, "rb") as f:
            header = f.read(4)
        assert header == b"%PDF"


# ── Record ID edge cases ──────────────────────────────────────────

class TestRecordIdEdgeCases:
    def test_empty_record_id_uses_unknown(self, tmp_path):
        ba = _minimal_benh_an(record_id="")
        path = export_pdf(ba, output_dir=tmp_path)
        assert "UNKNOWN" in Path(path).name

    def test_short_record_id_uses_full(self, tmp_path):
        ba = _minimal_benh_an(record_id="abc")
        path = export_pdf(ba, output_dir=tmp_path)
        assert "abc" in Path(path).name


# ── Content: drugs ────────────────────────────────────────────────

class TestDrugSection:
    def test_no_drugs_still_produces_pdf(self, tmp_path):
        ba = _minimal_benh_an()
        ba.don_thuoc.danh_sach_thuoc = []
        path = export_pdf(ba, output_dir=tmp_path)
        assert Path(path).exists()

    def test_with_drugs_produces_pdf(self, tmp_path):
        ba = _minimal_benh_an()
        ba.don_thuoc.danh_sach_thuoc = [
            ThuocKe(
                ten_thuoc="Amoxicillin",
                ham_luong="500mg",
                duong_dung="uống",
                lieu_dung="1 viên",
                so_lan_ngay="3 lần/ngày",
                so_ngay=5,
            )
        ]
        ba.don_thuoc.tai_kham = "5 ngày"
        path = export_pdf(ba, output_dir=tmp_path)
        assert Path(path).exists()
        assert Path(path).stat().st_size > 0

    def test_multiple_drugs_produce_pdf(self, tmp_path):
        ba = _minimal_benh_an()
        ba.don_thuoc.danh_sach_thuoc = [
            ThuocKe(ten_thuoc=f"Drug{i}", so_ngay=3) for i in range(5)
        ]
        path = export_pdf(ba, output_dir=tmp_path)
        assert Path(path).exists()


# ── Default output directory ──────────────────────────────────────

class TestDefaultOutputDir:
    def test_default_dir_used_when_none(self, tmp_path, monkeypatch):
        import core.l9a_pdf_export as _mod_pdf
        monkeypatch.setattr(_mod_pdf, "_EXPORTS_DIR", tmp_path)
        ba = _minimal_benh_an()
        path = export_pdf(ba, output_dir=None)
        assert Path(path).parent == tmp_path
