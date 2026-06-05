# tests/unit/test_l1c_vn_numbers.py
# FID-VN-005 | VN-NER-002: unit tests for _normalize_vn_numbers() and _vn_to_int()

import pytest
from src.core.l1c_ner import _vn_to_int, _normalize_vn_numbers, extract_entities


# ─── _vn_to_int ───────────────────────────────────────────────────────────────

class TestVnToInt:
    def test_single_digits(self):
        assert _vn_to_int("một") == 1
        assert _vn_to_int("hai") == 2
        assert _vn_to_int("ba") == 3
        assert _vn_to_int("chín") == 9
        assert _vn_to_int("không") == 0

    def test_alternate_forms(self):
        assert _vn_to_int("tư") == 4
        assert _vn_to_int("lăm") == 5
        assert _vn_to_int("bẩy") == 7
        assert _vn_to_int("mốt") == 1

    def test_tens(self):
        assert _vn_to_int("hai mươi") == 20
        assert _vn_to_int("ba mươi") == 30
        assert _vn_to_int("tám mươi") == 80
        assert _vn_to_int("chín mươi") == 90

    def test_tens_with_units(self):
        assert _vn_to_int("ba mươi lăm") == 35
        assert _vn_to_int("bảy mươi lăm") == 75
        assert _vn_to_int("bảy mươi hai") == 72
        assert _vn_to_int("hai mươi hai") == 22
        assert _vn_to_int("sáu mươi bảy") == 67

    def test_ten_to_nineteen(self):
        assert _vn_to_int("mười") == 10
        assert _vn_to_int("mười hai") == 12
        assert _vn_to_int("mười lăm") == 15

    def test_hundreds(self):
        assert _vn_to_int("một trăm") == 100
        assert _vn_to_int("năm trăm") == 500
        assert _vn_to_int("chín trăm") == 900

    def test_hundreds_with_tens(self):
        assert _vn_to_int("một trăm ba mươi") == 130
        assert _vn_to_int("một trăm ba mươi lăm") == 135
        assert _vn_to_int("một trăm hai mươi") == 120
        assert _vn_to_int("hai trăm bảy mươi lăm") == 275

    def test_shorthand_forms(self):
        # "tám lăm" = 85 (common in spoken BP readings)
        assert _vn_to_int("tám lăm") == 85
        assert _vn_to_int("ba mốt") == 31
        assert _vn_to_int("chín lăm") == 95

    def test_returns_none_on_invalid(self):
        assert _vn_to_int("xin chào") is None
        assert _vn_to_int("bệnh nhân") is None
        assert _vn_to_int("") is None


# ─── _normalize_vn_numbers ────────────────────────────────────────────────────

class TestNormalizeVnNumbers:
    def test_bp_standard(self):
        result = _normalize_vn_numbers("huyết áp một trăm ba mươi trên chín mươi")
        assert "130/90" in result

    def test_bp_with_lam_shorthand(self):
        result = _normalize_vn_numbers("huyết áp một trăm ba mươi lăm trên tám lăm")
        assert "135/85" in result

    def test_bp_120_80(self):
        result = _normalize_vn_numbers("huyết áp một trăm hai mươi trên tám mươi")
        assert "120/80" in result

    def test_decimal_phai(self):
        result = _normalize_vn_numbers("sốt ba mươi tám phẩy năm")
        assert "38.5" in result

    def test_ruoi(self):
        result = _normalize_vn_numbers("sốt ba mươi tám rưỡi")
        assert "38.5" in result

    def test_ruoi_with_do(self):
        result = _normalize_vn_numbers("sốt ba mươi tám độ rưỡi")
        assert "38.5" in result

    def test_tens_standalone(self):
        result = _normalize_vn_numbers("mạch tám mươi nhịp")
        assert "80" in result

    def test_hundreds_standalone(self):
        result = _normalize_vn_numbers("năm trăm miligam")
        assert "500" in result

    def test_single_before_unit_vien(self):
        result = _normalize_vn_numbers("hai viên")
        assert "2 viên" in result or "2viên" in result

    def test_single_before_unit_ngay(self):
        result = _normalize_vn_numbers("ba ngày")
        assert "3" in result

    def test_single_before_unit_tuan(self):
        result = _normalize_vn_numbers("một tuần")
        assert "1" in result

    def test_single_before_unit_thang(self):
        result = _normalize_vn_numbers("một tháng")
        assert "1" in result

    def test_single_before_unit_miligam(self):
        result = _normalize_vn_numbers("năm miligam")
        assert "5" in result

    def test_no_change_on_digits(self):
        result = _normalize_vn_numbers("huyết áp 120/80")
        assert "120/80" in result

    def test_no_change_on_plain_text(self):
        result = _normalize_vn_numbers("bệnh nhân đau đầu chóng mặt")
        assert result == "bệnh nhân đau đầu chóng mặt"

    def test_empty_string(self):
        assert _normalize_vn_numbers("") == ""


# ─── Full extract_entities integration (FID-VN-005 acceptance criteria) ──────

class TestExtractEntitiesVnNumbers:
    def test_bp_word_form(self):
        ents = extract_entities("huyết áp một trăm ba mươi trên chín mươi")
        assert ents.huyet_ap_tam_thu == 130
        assert ents.huyet_ap_tam_truong == 90

    def test_mach_word_form(self):
        ents = extract_entities("mạch tám mươi nhịp mỗi phút")
        assert ents.mach == 80.0

    def test_nhiet_do_phai(self):
        ents = extract_entities("sốt ba mươi tám phẩy năm")
        assert ents.nhiet_do == 38.5

    def test_nhiet_do_ruoi(self):
        ents = extract_entities("sốt ba mươi tám rưỡi")
        assert ents.nhiet_do == 38.5

    def test_nhiet_do_ruoi_with_do(self):
        ents = extract_entities("bệnh nhân sốt ba mươi tám độ rưỡi")
        assert ents.nhiet_do == 38.5

    def test_tai_kham_tuan(self):
        ents = extract_entities("tái khám sau một tuần")
        assert ents.tai_kham != ""
        assert "1" in ents.tai_kham
        assert "tuần" in ents.tai_kham

    def test_tai_kham_ngay(self):
        ents = extract_entities("tái khám sau ba ngày nếu không đỡ")
        assert "3" in ents.tai_kham
        assert "ngày" in ents.tai_kham

    def test_tai_kham_thang(self):
        ents = extract_entities("tái khám sau một tháng kèm xét nghiệm")
        assert "1" in ents.tai_kham
        assert "tháng" in ents.tai_kham

    def test_bp_135_85(self):
        ents = extract_entities("huyết áp một trăm ba mươi lăm trên tám lăm")
        assert ents.huyet_ap_tam_thu == 135
        assert ents.huyet_ap_tam_truong == 85

    def test_can_nang_word_form(self):
        ents = extract_entities("cân nặng bảy mươi hai kilogram")
        assert ents.can_nang == 72.0

    def test_nhip_tho_word_form(self):
        ents = extract_entities("nhịp thở hai mươi hai lần mỗi phút")
        assert ents.nhip_tho == 22.0

    def test_existing_numeric_format_unchanged(self):
        ents = extract_entities("huyết áp 120/80 mạch 80 sốt 38.5")
        assert ents.huyet_ap_tam_thu == 120
        assert ents.mach == 80.0
        assert ents.nhiet_do == 38.5

    def test_tc001_transcript(self):
        transcript = (
            "Bệnh nhân nam bốn mươi lăm tuổi đến khám vì đau đầu và chóng mặt. "
            "Huyết áp một trăm ba mươi trên chín mươi. "
            "Mạch tám mươi nhịp mỗi phút. "
            "Chẩn đoán tăng huyết áp độ một. "
            "Kê amoxicillin năm trăm miligam ngày hai viên trong bảy ngày. "
            "Tái khám sau một tuần."
        )
        ents = extract_entities(transcript)
        assert ents.huyet_ap_tam_thu == 130
        assert ents.huyet_ap_tam_truong == 90
        assert ents.mach == 80.0
        assert ents.tai_kham != ""
        assert "1" in ents.tai_kham

    def test_tc002_transcript(self):
        transcript = (
            "Bệnh nhân nữ ba mươi hai tuổi ho có đờm năm ngày, sốt ba mươi tám độ rưỡi. "
            "Huyết áp một trăm hai mươi trên tám mươi. "
            "Nhịp thở hai mươi hai lần mỗi phút. "
            "Chẩn đoán viêm phổi cộng đồng. "
            "Kê azithromycin năm trăm miligam ngày một viên trong năm ngày "
            "và paracetamol năm trăm miligam khi sốt. "
            "Tái khám sau ba ngày nếu không đỡ."
        )
        ents = extract_entities(transcript)
        assert ents.huyet_ap_tam_thu == 120
        assert ents.huyet_ap_tam_truong == 80
        assert ents.nhiet_do == 38.5
        assert ents.nhip_tho == 22.0
        assert "3" in ents.tai_kham

    def test_tc003_transcript(self):
        transcript = (
            "Bệnh nhân nam năm mươi tám tuổi, tái khám tiểu đường type hai. "
            "Cân nặng bảy mươi hai kilogram. "
            "Huyết áp một trăm ba mươi lăm trên tám lăm. "
            "Mạch bảy mươi lăm. "
            "Chẩn đoán đái tháo đường type hai kiểm soát chưa tốt. "
            "Tái khám sau một tháng kèm xét nghiệm HbA1c."
        )
        ents = extract_entities(transcript)
        assert ents.huyet_ap_tam_thu == 135
        assert ents.huyet_ap_tam_truong == 85
        assert ents.can_nang == 72.0
        assert ents.mach == 75.0
        assert "1" in ents.tai_kham
        assert "tháng" in ents.tai_kham
