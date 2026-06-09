# tests/unit/test_a3_dialect_norm.py
# A3-DIALECT-NORM unit tests — FID-VN-010
# 50 test cases: dialect normalization, abbreviation expansion, region detection

import pytest
from src.core.dialect_norm import (
    DIALECT_MAP,
    _CENTRAL_MARKERS,
    _SOUTHERN_MARKERS,
    detect_region,
    normalize_dialect,
    expand_abbreviations,
    normalize_text,
)


# ===========================================================================
# detect_region — auto-detect từ text
# ===========================================================================

class TestDetectRegion:
    def test_central_markers_detected(self):
        assert detect_region("Bệnh nhân nói mô rứa hỉ") == "central"

    def test_southern_markers_detected(self):
        assert detect_region("Hổng có thuốc nha bác sĩ") == "southern"

    def test_northern_fallback_no_markers(self):
        assert detect_region("Bệnh nhân đau đầu và sốt cao") == "northern"

    def test_empty_string_falls_to_northern(self):
        assert detect_region("") == "northern"

    def test_central_wins_when_more_markers(self):
        assert detect_region("mô răng rứa hỉ ni hổng") == "central"  # 5 central vs 1 southern

    def test_southern_wins_when_more_markers(self):
        assert detect_region("hổng dzô bả ảnh nè chỉ mô") == "southern"  # 6 southern vs 1 central

    def test_case_insensitive_detection(self):
        assert detect_region("MÔ RỨA HỈ") == "central"

    def test_single_central_marker(self):
        assert detect_region("bệnh nhân mô rồi") == "central"

    def test_single_southern_marker(self):
        assert detect_region("bệnh nhân hổng ăn được") == "southern"


# ===========================================================================
# normalize_dialect — Central region
# ===========================================================================

class TestNormalizeDialectCentral:
    def test_mo_replaced(self):
        result, subs = normalize_dialect("đau ở mô", "central")
        assert "đâu" in result

    def test_rang_replaced(self):
        result, subs = normalize_dialect("răng không đến", "central")
        assert "sao" in result

    def test_rua_replaced(self):
        result, subs = normalize_dialect("rứa hả", "central")
        assert "vậy" in result

    def test_ni_replaced(self):
        result, subs = normalize_dialect("bữa ni uống thuốc", "central")
        assert "hôm nay" in result

    def test_oi_central_is_sick(self):
        # Critical: ốm = bệnh in central, NOT gầy
        result, subs = normalize_dialect("bệnh nhân bị ốm", "central")
        assert "bệnh" in result
        assert "gầy" not in result

    def test_nac_replaced(self):
        result, subs = normalize_dialect("uống nác nhiều", "central")
        assert "nước" in result

    def test_tuc_nguc_normalized(self):
        result, subs = normalize_dialect("tức ngực khó thở", "central")
        assert "đau tức ngực" in result

    def test_substitutions_list_populated(self):
        _, subs = normalize_dialect("uống nác mô rứa", "central")
        assert len(subs) > 0

    def test_substitution_format(self):
        _, subs = normalize_dialect("mô rứa", "central")
        assert any("→" in s for s in subs)

    def test_multiword_phrase_priority(self):
        # "bây chừ" (2 words) should be matched before single "chừ"
        result, subs = normalize_dialect("bây chừ uống thuốc", "central")
        assert "bây giờ" in result

    def test_bua_ni_replaced(self):
        result, subs = normalize_dialect("bữa ni ổng không uống", "central")
        assert "hôm nay" in result

    def test_chu_not_wrongly_replaced(self):
        # "chứ" trong central map should stay as "chứ"
        result, subs = normalize_dialect("chứ không biết", "central")
        assert "chứ" in result


# ===========================================================================
# normalize_dialect — Southern region
# ===========================================================================

class TestNormalizeDialectSouthern:
    def test_hong_replaced(self):
        result, subs = normalize_dialect("hổng uống được", "southern")
        assert "không" in result

    def test_dzô_replaced(self):
        result, subs = normalize_dialect("dzô phòng khám", "southern")
        assert "vào" in result

    def test_oi_southern_is_thin(self):
        # Critical: ốm = gầy in southern, NOT bệnh
        result, subs = normalize_dialect("bệnh nhân bị ốm", "southern")
        assert "gầy" in result
        assert "bệnh" not in result.replace("bệnh nhân", "")  # "bệnh nhân" stays

    def test_oi_replaced(self):
        result, subs = normalize_dialect("ói nhiều lần", "southern")
        assert "nôn" in result

    def test_chich_replaced(self):
        result, subs = normalize_dialect("chích thuốc vô", "southern")
        assert "tiêm" in result

    def test_binh_replaced(self):
        result, subs = normalize_dialect("bịnh nhân đến", "southern")
        assert "bệnh" in result

    def test_hong_co_phrase(self):
        result, subs = normalize_dialect("hổng có triệu chứng gì", "southern")
        assert "không có" in result

    def test_hong_biet_phrase(self):
        result, subs = normalize_dialect("hổng biết bị bệnh gì", "southern")
        assert "không biết" in result

    def test_subs_returned_for_changes(self):
        _, subs = normalize_dialect("hổng uống ói mửa", "southern")
        assert len(subs) > 0

    def test_hen_particle(self):
        result, subs = normalize_dialect("uống thuốc hen", "southern")
        assert "nhé" in result

    def test_tieu_long_replaced(self):
        result, subs = normalize_dialect("tiêu lỏng 3 ngày nay", "southern")
        assert "tiêu chảy" in result


# ===========================================================================
# normalize_dialect — Northern region
# ===========================================================================

class TestNormalizeDialectNorthern:
    def test_kho_o_replaced(self):
        result, subs = normalize_dialect("người bệnh khó ở", "northern")
        assert "khó chịu" in result

    def test_ue_oai_replaced(self):
        result, subs = normalize_dialect("uể oải mấy ngày", "northern")
        assert "mệt mỏi" in result

    def test_am_oe_replaced(self):
        result, subs = normalize_dialect("cảm giác ậm ọe", "northern")
        assert "buồn nôn" in result

    def test_no_change_on_standard_text(self):
        standard = "bệnh nhân đau đầu sốt cao 38 độ"
        result, subs = normalize_dialect(standard, "northern")
        assert result == standard or len(subs) == 0

    def test_empty_subs_for_no_match(self):
        _, subs = normalize_dialect("bệnh nhân sốt", "northern")
        assert subs == []


# ===========================================================================
# normalize_dialect — auto region detection
# ===========================================================================

class TestNormalizeDialectAuto:
    def test_auto_detects_central(self):
        result, _ = normalize_dialect("đau ở mô rứa hỉ", "auto")
        assert "đâu" in result

    def test_auto_detects_southern(self):
        result, _ = normalize_dialect("hổng uống được nha", "auto")
        assert "không" in result

    def test_auto_falls_to_northern(self):
        result, subs = normalize_dialect("bệnh nhân đau đầu", "auto")
        # Northern has few entries — standard text usually unchanged
        assert isinstance(result, str)


# ===========================================================================
# expand_abbreviations — A3b
# ===========================================================================

class TestExpandAbbreviations:
    def test_ha_expands_in_context(self):
        result = expand_abbreviations("ha 155/95 mmHg")
        assert "huyết áp" in result

    def test_bn_expands(self):
        result = expand_abbreviations("bn 45 tuổi nam")
        assert "bệnh nhân" in result

    def test_xn_expands(self):
        result = expand_abbreviations("cho xn công thức máu")
        assert "xét nghiệm" in result

    def test_sa_expands(self):
        result = expand_abbreviations("sa bụng tổng quát")
        assert "siêu âm" in result

    def test_dtd_expands(self):
        result = expand_abbreviations("chẩn đoán đtđ type 2")
        assert "đái tháo đường" in result

    def test_tha_expands(self):
        result = expand_abbreviations("tiền sử tha 10 năm")
        assert "tăng huyết áp" in result

    def test_bid_expands(self):
        result = expand_abbreviations("uống bid sau ăn")
        assert "2 lần mỗi ngày" in result

    def test_tid_expands(self):
        result = expand_abbreviations("thuốc tid trước ăn")
        assert "3 lần mỗi ngày" in result

    def test_po_expands(self):
        result = expand_abbreviations("kê po viên 500mg")
        assert "uống" in result

    def test_ha_not_replaced_in_hai(self):
        # "ha" word-boundary → must NOT replace "hai" or "than"
        result = expand_abbreviations("hai bệnh nhân")
        assert "hai" in result
        assert "huyết áp bệnh nhân" not in result

    def test_case_insensitive(self):
        result = expand_abbreviations("XN công thức máu HA 130/80")
        assert "xét nghiệm" in result.lower()
        assert "huyết áp" in result.lower()

    def test_ecg_expands(self):
        result = expand_abbreviations("cho ecg và xq ngực")
        assert "điện tâm đồ" in result

    def test_bc_expands(self):
        result = expand_abbreviations("bc tăng cao 12000")
        assert "bạch cầu" in result


# ===========================================================================
# normalize_text — full pipeline (dialect → abbrev)
# ===========================================================================

class TestNormalizeText:
    def test_returns_tuple(self):
        result = normalize_text("bệnh nhân sốt", "northern")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_dialect_then_abbrev(self):
        # Central: "mô" → "đâu" | then "bn" → "bệnh nhân"
        result, subs = normalize_text("bn mô rứa hỉ", "central")
        assert "bệnh nhân" in result
        assert "đâu" in result

    def test_subs_list_str(self):
        _, subs = normalize_text("mô rứa bn ha 155", "central")
        assert all(isinstance(s, str) for s in subs)

    def test_empty_input(self):
        result, subs = normalize_text("", "northern")
        assert result == ""
        assert subs == []

    def test_southern_and_abbrev(self):
        result, subs = normalize_text("hổng có sa bụng", "southern")
        assert "không có" in result
        assert "siêu âm" in result


# ===========================================================================
# DIALECT_MAP structure checks
# ===========================================================================

class TestDialectMapStructure:
    def test_has_central_key(self):
        assert "central" in DIALECT_MAP

    def test_has_southern_key(self):
        assert "southern" in DIALECT_MAP

    def test_has_northern_key(self):
        assert "northern" in DIALECT_MAP

    def test_has_medical_abbrev_key(self):
        assert "medical_abbrev" in DIALECT_MAP

    def test_central_has_sufficient_entries(self):
        assert len(DIALECT_MAP["central"]) >= 30

    def test_southern_has_sufficient_entries(self):
        assert len(DIALECT_MAP["southern"]) >= 20

    def test_medical_abbrev_has_sufficient_entries(self):
        assert len(DIALECT_MAP["medical_abbrev"]) >= 15

    def test_oi_semantic_trap_both_regions(self):
        # "ốm" must be in both central AND southern with DIFFERENT mappings
        assert DIALECT_MAP["central"].get("ốm") == "bệnh"
        assert DIALECT_MAP["southern"].get("ốm") == "gầy"
        assert DIALECT_MAP["central"]["ốm"] != DIALECT_MAP["southern"]["ốm"]

    def test_all_values_are_strings(self):
        for region, entries in DIALECT_MAP.items():
            for k, v in entries.items():
                assert isinstance(v, str), f"{region}[{k!r}] is not str"

    def test_central_markers_subset_of_map(self):
        for marker in _CENTRAL_MARKERS:
            assert marker in DIALECT_MAP["central"], f"Central marker '{marker}' not in central map"

    def test_southern_markers_subset_of_map(self):
        for marker in _SOUTHERN_MARKERS:
            assert marker in DIALECT_MAP["southern"], f"Southern marker '{marker}' not in southern map"
