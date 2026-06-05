"""
Regression tests for NER bugs discovered during real-world testing (2026-06-08).
Each test corresponds to a specific observed failure + the fix applied.

Bug sources: real PhoWhisper transcript from test A-01 (Viêm họng cấp).
"""
from __future__ import annotations
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from core.l1c_ner import extract_entities
from core.l1b_drug_correct import extract_drug_candidates


# ── Real-world transcript (PhoWhisper output, A-01 test) ─────────────────────

_TRANSCRIPT_A01 = (
    "bình nhơn nam bốn mươi hai tuổi nghề nghiệp kết oán lý do vào khám đau họng "
    "ba ngày nay đau tăng khi nuốt bệnh nhân tự uống Paracetamol nhưng không đỡ "
    "khám tổng trạng tỉnh tám tiếp xúc tốt huyết áp một trăm hai mươi tri tám mươi "
    "mặt tám mươi hai lần một phút nhiệt độ ba mươi bảy tám độ cân nặng bảy mươi "
    "ki lô khám hoạt niêm mạc đỏ a bây đen xưng hai bên to không có mủ không có "
    "hạch cổ chẩn đoán viêm hạnh cấp điều trị amo xi lan nằm trần mi li gan c uống "
    "ba lần mỗi ngày trong năm ngày Paracetamol năm trăm ml uống khi sốt trên ba "
    "mươi tám độ tái khám sau năm ngày hoặc sớm hơn nếu số cao không hạt"
)


def _ent_a01():
    drugs = extract_drug_candidates(_TRANSCRIPT_A01)
    return extract_entities(_TRANSCRIPT_A01, drugs)


# ── Bug #1: chan_doan boundary overflow ───────────────────────────────────────
# Before fix: "viêm hạnh cấp điều trị amo xi lan nằm trần mi li gan c uống 3 lần..."
# After fix:  "viêm hạnh cấp" (stops at "điều trị")

class TestChanDoanBoundary:
    def test_chan_doan_stops_before_dieu_tri(self):
        ent = _ent_a01()
        assert "điều trị" not in ent.chan_doan

    def test_chan_doan_does_not_contain_drug_text(self):
        ent = _ent_a01()
        assert "amo xi lan" not in ent.chan_doan
        assert "Paracetamol" not in ent.chan_doan
        assert "uống" not in ent.chan_doan

    def test_chan_doan_boundary_clean_transcript(self):
        t = "chẩn đoán viêm họng cấp điều trị Amoxicillin năm trăm mg uống ba lần mỗi ngày"
        ent = extract_entities(t)
        assert ent.chan_doan == "viêm họng cấp"

    def test_chan_doan_boundary_ke_don(self):
        t = "chẩn đoán tăng huyết áp kê đơn Amlodipine mười mg"
        ent = extract_entities(t)
        assert ent.chan_doan == "tăng huyết áp"

    def test_chan_doan_boundary_tai_kham(self):
        t = "chẩn đoán đau lưng cấp tái khám sau một tuần"
        ent = extract_entities(t)
        assert ent.chan_doan == "đau lưng cấp"


# ── Bug #2: temperature decimal dropped when "phẩy" missing ──────────────────
# PhoWhisper often drops "phẩy" → "ba mươi bảy tám" → should be 37.8, not 37.0

class TestTemperatureDecimalWithoutPhay:
    def test_real_transcript_temp_38_8(self):
        ent = _ent_a01()
        assert ent.nhiet_do == pytest.approx(37.8)

    def test_temp_without_phay_nhiet_do_prefix(self):
        t = "nhiệt độ ba mươi bảy tám độ"
        ent = extract_entities(t)
        assert ent.nhiet_do == pytest.approx(37.8)

    def test_temp_without_phay_sot_prefix(self):
        t = "sốt ba mươi tám năm độ"
        ent = extract_entities(t)
        assert ent.nhiet_do == pytest.approx(38.5)

    def test_temp_with_phay_still_works(self):
        t = "nhiệt độ 37.8"
        ent = extract_entities(t)
        assert ent.nhiet_do == pytest.approx(37.8)

    def test_temp_word_form_with_phay_still_works(self):
        t = "nhiệt độ ba mươi bảy phẩy tám độ"
        ent = extract_entities(t)
        assert ent.nhiet_do == pytest.approx(37.8)

    def test_temp_integer_no_decimal_word_unchanged(self):
        t = "nhiệt độ ba mươi bảy độ"
        ent = extract_entities(t)
        assert ent.nhiet_do == pytest.approx(37.0)


# ── Bug #3: patient self-medication creates false drug entry ──────────────────
# "bệnh nhân tự uống Paracetamol" → must NOT appear in don_thuoc

class TestPatientSelfMedicationFilter:
    def test_real_transcript_no_paracetamol_120(self):
        ent = _ent_a01()
        # No drug with ham_luong "120" or "8" (false positive from BP context bleed)
        hams = [d["ham_luong"] for d in ent.don_thuoc]
        assert "120" not in hams
        assert "8" not in hams

    def test_real_transcript_drug_count_is_one(self):
        ent = _ent_a01()
        # Only the prescribed Paracetamol should remain (Amoxicillin missed by ASR)
        assert len(ent.don_thuoc) == 1

    def test_patient_self_med_excluded(self):
        t = "bệnh nhân tự uống Paracetamol không đỡ huyết áp 120/80 tái khám sau 3 ngày"
        drugs = extract_drug_candidates(t)
        ent = extract_entities(t, drugs)
        # Paracetamol from patient self-medication context → excluded
        assert len(ent.don_thuoc) == 0

    def test_prescribed_drug_included(self):
        t = "chẩn đoán viêm họng kê đơn Amoxicillin 500mg uống 3 lần mỗi ngày trong 5 ngày"
        drugs = extract_drug_candidates(t)
        ent = extract_entities(t, drugs)
        assert any(d["inn"] == "Amoxicillin" for d in ent.don_thuoc)

    def test_dang_dung_excluded(self):
        t = "bệnh nhân đang dùng Metformin 500mg huyết áp 130/80 tái khám sau 1 tháng"
        drugs = extract_drug_candidates(t)
        ent = extract_entities(t, drugs)
        assert len(ent.don_thuoc) == 0


# ── Bug #4: oral drug unit ml → mg correction ─────────────────────────────────
# PhoWhisper: "miligam" → "ml". For oral route, correct to "mg".

class TestDrugUnitMlToMg:
    def test_real_transcript_paracetamol_unit_is_mg(self):
        ent = _ent_a01()
        assert len(ent.don_thuoc) == 1
        assert ent.don_thuoc[0]["ham_luong"] == "500 mg"

    def test_oral_ml_corrected_to_mg(self):
        t = "kê đơn Paracetamol 500 ml uống ba lần mỗi ngày trong 5 ngày"
        drugs = extract_drug_candidates(t)
        ent = extract_entities(t, drugs)
        assert len(ent.don_thuoc) == 1
        assert ent.don_thuoc[0]["ham_luong"] == "500 mg"

    def test_injection_ml_preserved(self):
        t = "kê đơn Metoclopramide 10 ml tiêm bắp một lần"
        drugs = extract_drug_candidates(t)
        ent = extract_entities(t, drugs)
        if ent.don_thuoc:
            # tiêm route → ml should NOT be converted to mg
            assert ent.don_thuoc[0]["ham_luong"] == "10 ml"
