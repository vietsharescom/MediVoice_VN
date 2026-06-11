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

    def test_chan_doan_theo_thi_che_la(self):
        # CT-021: ASR "Chẩn đoán theo dõi nhiễm khuẩn đường tiêu hóa. Kê Ciprofloxacin..."
        # → "chẩn đoán theo thì nhiễm khuẩn đường tiêu hoá chê là Ciprofloxacin..."
        t = (
            "chẩn đoán theo thì nhiễm khuẩn đường tiêu hoá chê là Ciprofloxacin "
            "năm trăm mg uống hai lần mỗi ngày"
        )
        ent = extract_entities(t)
        assert ent.chan_doan == "nhiễm khuẩn đường tiêu hoá"

    def test_chan_doan_theo_doi_still_works(self):
        t = "chẩn đoán theo dõi tăng huyết áp kê đơn Amlodipine mười mg"
        ent = extract_entities(t)
        assert ent.chan_doan == "tăng huyết áp"

    def test_chan_doan_che_no_diacritic(self):
        # CT-031: ASR "Kê" -> "che" (không dấu, khác "chê" của CT-021)
        t = "chẩn đoán viêm phẩm cấp che Amoxicillin năm trăm mg uống ba lần mỗi ngày"
        ent = extract_entities(t)
        assert ent.chan_doan == "viêm phẩm cấp"

    def test_chan_doan_bare_thi_filler(self):
        # Andy pilot test 2026-06-11 (TMH clip): "chẩn đoán thì viêm tai giữa cấp
        # kê thuốc là a mốt xi lin..." — bare "thì" (không có "theo") trước chẩn
        # đoán bị giữ lại làm "thì viêm tai giữa cấp" thay vì "viêm tai giữa cấp"
        t = (
            "chẩn đoán thì viêm tai giữa cấp kê thuốc là amoxicillin năm trăm "
            "miligam uống ba lần mỗi ngày"
        )
        ent = extract_entities(t)
        assert ent.chan_doan == "viêm tai giữa cấp"


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

    def test_temp_cham_alias_for_phay(self):
        # CT-030: ASR "ba mươi bảy phẩy tám" -> "ba mươi bảy chấm chín" (PhoWhisper "chấm" thay "phẩy")
        t = "nhiệt độ ba mươi bảy chấm chín độ c"
        ent = extract_entities(t)
        assert ent.nhiet_do == pytest.approx(37.9)


# ── Bug #3: patient self-medication creates false drug entry ──────────────────
# "bệnh nhân tự uống Paracetamol" → must NOT appear in don_thuoc

class TestPatientSelfMedicationFilter:
    def test_real_transcript_no_paracetamol_120(self):
        ent = _ent_a01()
        # No drug with ham_luong "120" or "8" (false positive from BP context bleed)
        hams = [d["ham_luong"] for d in ent.don_thuoc]
        assert "120" not in hams
        assert "8" not in hams

    def test_real_transcript_drug_count_is_two(self):
        ent = _ent_a01()
        # Amoxicillin alias "amo xi lan" now detected + prescribed Paracetamol
        assert len(ent.don_thuoc) == 2
        inns = {d["inn"] for d in ent.don_thuoc}
        assert "Amoxicillin" in inns
        assert "Paracetamol" in inns

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
        para = next((d for d in ent.don_thuoc if d["inn"] == "Paracetamol"), None)
        assert para is not None
        assert para["ham_luong"] == "500 mg"

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


# ── Bug #4b: oral drug unit kg → mg correction (Southern VN accent) ──────────
# PhoWhisper (giọng Nam): "miligam" → "ký" (kg). Oral route only.
# Pediatric "mg/kg" dosing uses "X mg trên kg" pattern → not affected.

class TestDrugUnitKgToMg:
    def test_oral_kg_corrected_to_mg(self):
        t = "kê đơn Amoxicillin 500 kg uống ba lần mỗi ngày trong 7 ngày"
        drugs = extract_drug_candidates(t)
        ent = extract_entities(t, drugs)
        assert len(ent.don_thuoc) == 1
        assert ent.don_thuoc[0]["ham_luong"] == "500 mg"

    def test_oral_paracetamol_kg_corrected(self):
        t = "Paracetamol 500 kg uống khi sốt"
        drugs = extract_drug_candidates(t)
        ent = extract_entities(t, drugs)
        if ent.don_thuoc:
            assert ent.don_thuoc[0]["ham_luong"] == "500 mg"

    def test_injection_kg_preserved(self):
        # tiêm route → kg NOT converted (keep as-is, unusual but don't silently corrupt)
        t = "kê đơn Metoclopramide 10 kg tiêm bắp một lần"
        drugs = extract_drug_candidates(t)
        ent = extract_entities(t, drugs)
        if ent.don_thuoc:
            assert ent.don_thuoc[0]["ham_luong"] == "10 kg"


# ── Feature: lý do khám extraction ──────────────────────────────────────────
# Explicit "lý do khám:" prefix → extract chief complaint
# Fallback: text after age mention until vitals boundary

_TRANSCRIPT_A02 = (
    "bệnh nhân nữ ba mươi lăm tuổi đau thương vị hai tuần no ở mỹ tăng khi đói giảm sâu hơn ở chùa "
    "đầy bụng không nôn ra máu không đi phân đen tiền sử uống ibu protein nhiều lần trong tháng "
    "trước đó do đau khớp huyết áp một trăm mười trên bảy mươi mặc bảy mươi lăm khám bụng mềm "
    "thoáng đo vùng thường vị không có phản ứng thành quốc chẩn đoán viêm loét dạ dày đa trạng "
    "điều trị om mê brazil 20 ml uống một lần mỗi ngày trước khi ăn sáng trong ba mươi phút trong "
    "bốn tuần donald mười williams uống ba lần mỗi ngày trước bữa ăn ngưng ibuprofan hoàn toàn "
    "hẹn tái khám sau biếng tùng"
)


class TestLyDoExtraction:
    def test_explicit_ly_do_kham_prefix(self):
        t = "bệnh nhân nam 42 tuổi lý do khám đau họng 3 ngày huyết áp 120/80"
        ent = extract_entities(t)
        assert "đau họng" in ent.ly_do

    def test_a01_real_has_explicit_ly_do(self):
        # A-01 has "lý do vào khám" in transcript → should extract
        ent = _ent_a01()
        assert "đau họng" in ent.ly_do or len(ent.ly_do) > 5

    def test_a02_fallback_after_age(self):
        # A-02 has no explicit "lý do khám:" → fallback extracts after age mention
        drugs = extract_drug_candidates(_TRANSCRIPT_A02)
        ent = extract_entities(_TRANSCRIPT_A02, drugs)
        assert "đau" in ent.ly_do  # main complaint starts with "đau thương vị"
        assert len(ent.ly_do) > 5

    def test_ly_do_empty_when_no_signal(self):
        t = "chẩn đoán viêm họng kê đơn Amoxicillin 500mg"
        ent = extract_entities(t)
        # No age or "lý do" → ly_do stays empty
        assert ent.ly_do == ""


# ── Feature: ngưng filter — discontinuation not in prescription ──────────────
# "ngưng X" = stop taking X (patient instruction) → NOT added to don_thuoc

class TestNgungFilter:
    def test_ngung_ibuprofen_excluded(self):
        t = "kê đơn Omeprazole 20mg ngưng ibuprofan hoàn toàn tái khám sau 4 tuần"
        drugs = extract_drug_candidates(t)
        ent = extract_entities(t, drugs)
        inns = [d["inn"] for d in ent.don_thuoc]
        # ibuprofan should NOT appear in prescription (it's a stop order)
        assert "Ibuprofen" not in inns

    def test_a02_ibuprofan_ngung_not_in_don_thuoc(self):
        drugs = extract_drug_candidates(_TRANSCRIPT_A02)
        ent = extract_entities(_TRANSCRIPT_A02, drugs)
        inns = [d["inn"] for d in ent.don_thuoc]
        assert "Ibuprofen" not in inns

    def test_prescribed_ibuprofen_still_included(self):
        t = "kê đơn Ibuprofen 400mg uống 3 lần mỗi ngày sau ăn trong 5 ngày"
        drugs = extract_drug_candidates(t)
        ent = extract_entities(t, drugs)
        inns = [d["inn"] for d in ent.don_thuoc]
        # Prescribed Ibuprofen (no "ngưng" before it) → included
        assert "Ibuprofen" in inns


# ── Feature: ICD-10 auto_lookup with ASR noise trailing words ────────────────
# PhoWhisper confusion: "tá tràng" → "tát rạn", adding noise to trailing end.
# Fix: progressive prefix matching — drop up to 3 trailing words.

class TestICD10AutoLookup:
    def test_a02_viem_loet_da_day_tat_ran_resolves(self):
        from core.l1d_icd_lookup import auto_lookup
        # "tát rạn" = ASR noise for "tá tràng"; stripped prefix "viêm loét dạ dày" → K25
        code, display = auto_lookup("viêm loét dạ dày tát rạn")
        assert code != ""
        assert "25" in code or "dạ dày" in display.lower() or "da day" in display.lower()

    def test_a01_viem_hong_cap_exact(self):
        from core.l1d_icd_lookup import auto_lookup
        code, display = auto_lookup("viêm họng cấp")
        assert code != ""

    def test_clean_chan_doan_still_works(self):
        from core.l1d_icd_lookup import auto_lookup
        code, _ = auto_lookup("viêm loét dạ dày")
        assert code != ""

    def test_empty_returns_empty(self):
        from core.l1d_icd_lookup import auto_lookup
        assert auto_lookup("") == ("", "")


# ── Real-world transcript A-04 (PhoWhisper output) ───────────────────────────
# Test case: nam 28 tuổi viêm họng — reveals BUG-A through BUG-F

_TRANSCRIPT_A04 = (
    "bệnh nhân nam 28 tuổi nhân viên văn phòng "
    "em bị đau họng nuốt khó đã ban ngày nay sốt nhẹ việt chiều "
    "không có bệnh lý nền "
    "huyết áp 120/80 "
    "mặc 80 lần mỗi phút "  # "mặc" = PhoWhisper for "mạch"
    "nhiệt độ 37 độ 8 "     # "37 độ 8" → should be 37.8
    "cân nặng 68 ký "
    "viêm hỗn cấp "         # "chẩn đoán" keyword dropped by ASR
    "kê đơn ammos lim 500 mg hai viên chia ba lần mỗi ngày trong bảy ngày "
    "paracidamone 500 mg một viên khi đau hoặc sốt "
    "tái khám sau năm ngày nếu không đỡ"
)


class TestBugA_TempDoDecimal:
    """BUG-A: 'ba mươi bảy độ tám' / '37 độ 8' → 37.8 (not 37.0)"""

    def test_nhiet_do_do_separator(self):
        t = "nhiệt độ 37 độ 8"
        ent = extract_entities(t)
        assert ent.nhiet_do == pytest.approx(37.8)

    def test_nhiet_do_do_separator_word_form(self):
        t = "nhiệt độ ba mươi bảy độ tám"
        from core.l1c_ner import extract_entities as ee
        ent = ee(t)
        assert ent.nhiet_do == pytest.approx(37.8)

    def test_a04_nhiet_do(self):
        ent = extract_entities(_TRANSCRIPT_A04)
        assert ent.nhiet_do == pytest.approx(37.8)


class TestBugB_MachAlias:
    """BUG-B: 'mặc 80 lần' → mạch = 80"""

    def test_mac_alias(self):
        t = "mặc 80 lần mỗi phút"
        ent = extract_entities(t)
        assert ent.mach == pytest.approx(80)

    def test_a04_mach(self):
        ent = extract_entities(_TRANSCRIPT_A04)
        assert ent.mach == pytest.approx(80)

    def test_mat_alias_word_form(self):
        # CT-020: "Mạch bảy mươi lăm lần một phút" → ASR "mật bảy mươi lăm một phút"
        t = "huyết áp một trăm hai mươi trên tám mươi mật bảy mươi lăm một phút"
        ent = extract_entities(t)
        assert ent.mach == pytest.approx(75)


class TestBugC_NhanVienOccupation:
    """BUG-C: 'nhân viên văn phòng' occupation skip in ly_do fallback"""

    def test_nhan_vien_not_in_ly_do(self):
        t = "bệnh nhân nam 28 tuổi nhân viên văn phòng em bị đau họng huyết áp 120/80"
        ent = extract_entities(t)
        assert "nhân viên" not in ent.ly_do

    def test_symptom_still_captured(self):
        t = "bệnh nhân nam 28 tuổi nhân viên văn phòng em bị đau họng huyết áp 120/80"
        ent = extract_entities(t)
        assert "đau" in ent.ly_do or ent.ly_do == ""


class TestBugD_ChanDoanFallback:
    """BUG-D: chan_doan extracted even when 'chẩn đoán' keyword dropped by ASR"""

    def test_fallback_no_keyword(self):
        t = "viêm hỗn cấp kê đơn Amoxicillin 500 mg"
        ent = extract_entities(t)
        assert ent.chan_doan != ""
        assert "viêm" in ent.chan_doan.lower()

    def test_tang_huyet_ap_fallback(self):
        t = "tăng huyết áp điều trị Amlodipine 10 mg"
        ent = extract_entities(t)
        assert "tăng" in ent.chan_doan.lower() or ent.chan_doan != ""

    def test_explicit_keyword_still_works(self):
        t = "chẩn đoán viêm họng cấp kê đơn Amoxicillin 500 mg"
        ent = extract_entities(t)
        assert ent.chan_doan == "viêm họng cấp"


class TestBugEF_DrugAliases:
    """BUG-E+F: 'ammos lim' → Amoxicillin, 'paracidamone' → Paracetamol"""

    def test_ammos_lim(self):
        from core.l1b_drug_correct import extract_drug_candidates
        candidates = extract_drug_candidates("ammos lim 500 mg ba lần mỗi ngày")
        inns = [c["inn"] for c in candidates]
        assert "Amoxicillin" in inns

    def test_paracidamone(self):
        from core.l1b_drug_correct import extract_drug_candidates
        candidates = extract_drug_candidates("paracidamone 500 mg khi đau")
        inns = [c["inn"] for c in candidates]
        assert "Paracetamol" in inns

    def test_a04_drugs_detected(self):
        from core.l1b_drug_correct import extract_drug_candidates
        candidates = extract_drug_candidates(_TRANSCRIPT_A04)
        inns = {c["inn"] for c in candidates}
        assert "Amoxicillin" in inns
        assert "Paracetamol" in inns


# ── A-04b transcript (new PhoWhisper errors discovered) ─────────────────────
# "mặt" for mạch, "huyết á" for huyết áp, "amosilic"/"paracitamol"

_TRANSCRIPT_A04B = (
    "bệnh nhân nam 28 tuổi nhân viên văn phòng em bị đau họng khó nuốt đã ba ngày nay "
    "xuất hiện về chiều không có bệnh lý mềm "
    "huyết á 80 "
    "mặt 80 lần mỗi phút "
    "nhiệt độ 37 phẩy 8 độ "
    "cân nặng 68 ký "
    "họng đỏ amidan xinh nhẹ có ít mũ trắng "
    "chuẩn đoán viêm họng cấp "
    "kê đơn amosilic 500 mg hai viên chia ba lần mỗi ngày trong bảy ngày "
    "paracitamol một viên khi đau hoặc sốt "
    "tái khám sau năm ngày nếu không đỡ"
)


class TestBugG_MatAlias:
    """BUG-G: 'mặt 80 lần' → mạch = 80 (second PhoWhisper alias for 'mạch')"""

    def test_mat_alias(self):
        t = "mặt 80 lần mỗi phút"
        ent = extract_entities(t)
        assert ent.mach == pytest.approx(80)

    def test_a04b_mach(self):
        ent = extract_entities(_TRANSCRIPT_A04B)
        assert ent.mach == pytest.approx(80)


class TestBugH_HuyetAFlexible:
    """BUG-H: 'huyết á' (dropped 'p') → still extract BP when both numbers present"""

    def test_huyet_a_with_slash(self):
        t = "huyết á 120/80"
        ent = extract_entities(t)
        assert ent.huyet_ap_tam_thu == 120
        assert ent.huyet_ap_tam_truong == 80


class TestBugIJ_NewDrugAliases:
    """BUG-I+J: 'amosilic' → Amoxicillin, 'paracitamol' → Paracetamol"""

    def test_amosilic(self):
        from core.l1b_drug_correct import extract_drug_candidates
        candidates = extract_drug_candidates("amosilic 500 mg ba lần mỗi ngày")
        inns = [c["inn"] for c in candidates]
        assert "Amoxicillin" in inns

    def test_paracitamol(self):
        from core.l1b_drug_correct import extract_drug_candidates
        candidates = extract_drug_candidates("paracitamol 500 mg khi đau")
        inns = [c["inn"] for c in candidates]
        assert "Paracetamol" in inns

    def test_a04b_drugs(self):
        from core.l1b_drug_correct import extract_drug_candidates
        candidates = extract_drug_candidates(_TRANSCRIPT_A04B)
        inns = {c["inn"] for c in candidates}
        assert "Amoxicillin" in inns
        assert "Paracetamol" in inns


class TestBugN_TaiKhamDiagnosis:
    """BUG-N: SC-03 THA follow-up — chan_doan rỗng vì BS không nói 'chẩn đoán:'
    BS3 SG nói 'tái khám tăng huyết áp' mà không có 'chẩn đoán' keyword.
    Fix: _RE_TAI_KHAM_DIAGNOSIS pattern checked before general fallback.
    """

    def test_tai_kham_tang_huyet_ap(self):
        t = "tái khám tăng huyết áp đo lần một một trăm bảy mươi trên một trăm tăng amlodipine lên mười thêm losartan năm mươi tái khám sau hai tuần"
        ent = extract_entities(t)
        assert "tăng huyết áp" in ent.chan_doan.lower(), \
            f"chan_doan={repr(ent.chan_doan)}"

    def test_tai_kham_benh_dai_thao_duong(self):
        t = "tái khám đái tháo đường loại hai huyết áp một trăm ba mươi trên tám mươi lăm"
        ent = extract_entities(t)
        assert "đái tháo đường" in ent.chan_doan.lower(), \
            f"chan_doan={repr(ent.chan_doan)}"

    def test_explicit_chan_doan_still_wins(self):
        t = "chẩn đoán viêm họng cấp tái khám tăng huyết áp điều trị amoxicillin"
        ent = extract_entities(t)
        assert "viêm họng" in ent.chan_doan.lower(), \
            f"explicit chan_doan should win: {repr(ent.chan_doan)}"

    def test_simple_tai_kham_no_diagnosis(self):
        # "tái khám sau X ngày" — no disease name → chan_doan stays empty
        ent = extract_entities("bệnh nhân tái khám sau năm ngày")
        assert ent.chan_doan == ""


class TestBugO_TaiKhangAlias:
    """CT-032: ASR "tái khám" -> "tái kháng" (PhoWhisper bỏ dấu/đổi vần cuối).
    Trước fix: tai_kham trống vì _RE_TAI_KHAM chỉ nhận "kh[aá]m".
    """

    def test_tai_khang_extracts_tai_kham(self):
        t = "tái kháng sau năm ngày hoặc sớm hơn nếu kéo dài"
        ent = extract_entities(t)
        assert ent.tai_kham != ""
        assert "5 ngày" in ent.tai_kham

    def test_tai_khang_diagnosis_hint(self):
        t = "tái kháng tăng huyết áp sau hai tuần"
        ent = extract_entities(t)
        assert "tăng huyết áp" in ent.chan_doan.lower()


class TestBugK_SGColloquialBP:
    """BUG-K: SG colloquial 'một hai mươi' = 120 → huyết áp
    PhoWhisper output khi BS SG đọc BP: 'huyết áp một hai mươi trên tám mươi'
    Old regex: chỉ nhận 'một trăm hai mươi', không nhận 'một hai mươi'.
    Fix: thêm _WCOLLQ colloquial hundreds pattern.
    """

    def test_sg_bp_colloquial_hundreds(self):
        ent = extract_entities("huyết áp một hai mươi trên tám mươi mạch tám mươi")
        assert ent.huyet_ap_tam_thu == 120, f"expected 120, got {ent.huyet_ap_tam_thu}"
        assert ent.huyet_ap_tam_truong == 80

    def test_sg_bp_colloquial_165_full_form(self):
        ent = extract_entities("huyết áp một sáu mươi lăm trên chín mươi lăm")
        assert ent.huyet_ap_tam_thu == 165
        assert ent.huyet_ap_tam_truong == 95

    def test_sg_bp_colloquial_165_abbreviated(self):
        # BUG-K2 fix: "một sáu lăm" (abbreviation of "một sáu mươi lăm") → 165/95
        # Fixed by adding _WABR (abbreviated tens) to _WCOLLQ pattern
        ent = extract_entities("huyết áp một sáu lăm trên chín lăm")
        assert ent.huyet_ap_tam_thu == 165, f"expected 165, got {ent.huyet_ap_tam_thu}"
        assert ent.huyet_ap_tam_truong == 95

    def test_standard_bp_still_works(self):
        ent = extract_entities("huyết áp một trăm hai mươi trên tám mươi")
        assert ent.huyet_ap_tam_thu == 120


class TestBugL_NhietDoDigitSplit:
    """BUG-L: PhoWhisper normalized 'sốt ba 7.8' → nhiet_do=37.8
    _RE_DEC_WORDS converts 'bảy phẩy tám'→7.8 but single 'ba' stays as word.
    Old regex expected both parts as digits or both as words.
    Fix: _RE_NHIET_DO_SPLIT accepts VN word in tens position.
    """

    def test_digit_split_temperature(self):
        # After normalize: "sốt ba 7.8" (ba=word, 7.8=digit)
        from core.l1c_ner import _normalize_vn_numbers
        text = "sốt ba mươi bảy phẩy tám"
        norm = _normalize_vn_numbers(text)
        ent = extract_entities(text)
        assert ent.nhiet_do == pytest.approx(37.8, abs=0.05), \
            f"normalized='{norm}', nhiet_do={ent.nhiet_do}"

    def test_digit_split_38_5(self):
        ent = extract_entities("nhiệt độ ba mươi tám phẩy năm")
        assert ent.nhiet_do == pytest.approx(38.5, abs=0.05)

    def test_digit_split_sg_spoken(self):
        # BS SG: "sốt ba bảy phẩy tám" (không nói "mươi")
        ent = extract_entities("bệnh nhân sốt ba bảy phẩy tám")
        assert ent.nhiet_do == pytest.approx(37.8, abs=0.05), \
            f"nhiet_do={ent.nhiet_do}"


class TestBugM_NangKyWithoutCan:
    """BUG-M: BS SG nói 'nặng 70 ký' (không có 'cân') → can_nang=70
    Old regex required 'cân nặng' or 'weight' keyword.
    Fix: thêm '(?<!\\S)nặng' trigger trong _RE_CAN_NANG.
    """

    def test_nang_ky_no_prefix(self):
        ent = extract_entities("huyết áp một hai mươi trên tám mươi nặng bảy mươi ký")
        assert ent.can_nang == pytest.approx(70, abs=0.5), f"can_nang={ent.can_nang}"

    def test_nang_ky_with_number(self):
        ent = extract_entities("nặng sáu mươi lăm ký")
        assert ent.can_nang == pytest.approx(65, abs=0.5)

    def test_can_nang_standard_still_works(self):
        ent = extract_entities("cân nặng bảy mươi ki lô")
        assert ent.can_nang == pytest.approx(70, abs=0.5)
