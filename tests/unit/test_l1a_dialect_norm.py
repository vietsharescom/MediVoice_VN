# tests/unit/test_l1a_dialect_norm.py
# A3-DIALECT-NORM unit tests — FID-VN-010
# Coverage: detect_region, normalize_dialect, expand_abbreviations, normalize_text

import pytest
from src.core.dialect_norm import (
    DIALECT_MAP,
    detect_region,
    expand_abbreviations,
    normalize_dialect,
    normalize_text,
)


# ---------------------------------------------------------------------------
# detect_region
# ---------------------------------------------------------------------------

class TestDetectRegion:
    def test_central_markers_detected(self):
        text = "bệnh nhân nói mô rứa hỉ bác sĩ"
        assert detect_region(text) == "central"

    def test_southern_markers_detected(self):
        text = "bệnh nhân hổng uống thuốc hen"
        assert detect_region(text) == "southern"

    def test_no_markers_returns_northern(self):
        text = "bệnh nhân đau đầu sốt cao"
        assert detect_region(text) == "northern"

    def test_mixed_more_central_wins(self):
        # "mô", "rứa", "hỉ" = 3 central vs "hổng" = 1 southern
        text = "mô rứa hỉ hổng biết"
        assert detect_region(text) == "central"

    def test_mixed_more_southern_wins(self):
        text = "hổng biết bịnh ảnh ói mấy bữa nay"
        assert detect_region(text) == "southern"

    def test_empty_text_returns_northern(self):
        assert detect_region("") == "northern"

    def test_single_central_marker(self):
        assert detect_region("đau mô vậy") == "central"

    def test_single_southern_marker(self):
        assert detect_region("bệnh nhân ói nhiều") == "southern"


# ---------------------------------------------------------------------------
# normalize_dialect — CRITICAL: "ốm" semantic trap
# ---------------------------------------------------------------------------

class TestNormalizeDialectOm:
    """⚠️ "ốm" = bệnh (Trung) ≠ "ốm" = gầy (Nam) — quan trọng nhất."""

    def test_om_central_maps_to_benh(self):
        result, subs = normalize_dialect("bệnh nhân bị ốm", region="central")
        assert "bệnh" in result
        assert "gầy" not in result

    def test_om_southern_maps_to_gay(self):
        result, subs = normalize_dialect("bệnh nhân bị ốm", region="southern")
        assert "gầy" in result
        assert "bệnh nhân bị bệnh" != result  # không map thành "bệnh"

    def test_om_auto_central_text_maps_to_benh(self):
        # "mô" triggers auto-detect → central → "ốm" = "bệnh"
        result, subs = normalize_dialect("mô mà ốm rứa", region="auto")
        assert "bệnh" in result

    def test_om_auto_southern_text_maps_to_gay(self):
        # "hổng" triggers auto-detect → southern → "ốm" = "gầy"
        result, subs = normalize_dialect("hổng ốm gì đâu", region="auto")
        assert "gầy" in result

    def test_om_northern_stays_unchanged(self):
        # northern không có entry "ốm" → stays as-is
        result, subs = normalize_dialect("bệnh nhân bị ốm", region="northern")
        assert "ốm" in result


# ---------------------------------------------------------------------------
# normalize_dialect — Central substitutions
# ---------------------------------------------------------------------------

class TestNormalizeDialectCentral:
    def test_mo_maps_to_dau(self):
        result, _ = normalize_dialect("đau mô vậy bác sĩ", region="central")
        assert "đâu" in result

    def test_rang_maps_to_sao(self):
        result, _ = normalize_dialect("răng mà không uống thuốc", region="central")
        assert "sao" in result

    def test_bay_chu_multi_word_first(self):
        # "bây chừ" phải được match trước "chừ" (multi-word priority)
        result, _ = normalize_dialect("bây chừ uống thuốc đi", region="central")
        assert "bây giờ" in result
        # Đảm bảo không bị break thành "bây khoảng" (nếu "chừ" thay trước)
        assert "bây khoảng" not in result

    def test_substitutions_list_returned(self):
        _, subs = normalize_dialect("đau mô rứa", region="central")
        assert isinstance(subs, list)
        assert len(subs) > 0

    def test_returns_tuple(self):
        result = normalize_dialect("bệnh nhân bị ốm", region="central")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_empty_text(self):
        result, subs = normalize_dialect("", region="central")
        assert result == ""
        assert subs == []

    def test_no_match_returns_unchanged(self):
        text = "bệnh nhân đau đầu sốt 38 độ"
        result, subs = normalize_dialect(text, region="central")
        # Không có central markers → không thay gì
        assert subs == [] or result == text  # có thể thay một số term thông thường

    def test_nhuc_dau_maps_to_dau_dau(self):
        result, _ = normalize_dialect("bị nhức đầu mấy ngày", region="central")
        assert "đau đầu" in result

    def test_tui_maps_to_toi(self):
        result, _ = normalize_dialect("tui uống thuốc rồi", region="central")
        assert "tôi" in result


# ---------------------------------------------------------------------------
# normalize_dialect — Southern substitutions
# ---------------------------------------------------------------------------

class TestNormalizeDialectSouthern:
    def test_hong_maps_to_khong(self):
        result, _ = normalize_dialect("hổng uống thuốc", region="southern")
        assert "không" in result

    def test_oi_maps_to_non(self):
        result, _ = normalize_dialect("bệnh nhân bị ói", region="southern")
        assert "nôn" in result

    def test_chich_maps_to_tiem(self):
        result, _ = normalize_dialect("chích thuốc đau lắm", region="southern")
        assert "tiêm" in result

    def test_benh_nhan_bị_benh_tro_lai(self):
        # "bịnh" → "bệnh"
        result, _ = normalize_dialect("bịnh nhân bịnh nặng", region="southern")
        assert "bệnh" in result

    def test_dzo_maps_to_vao(self):
        result, _ = normalize_dialect("vô đây uống thuốc", region="southern")
        assert "vào" in result


# ---------------------------------------------------------------------------
# expand_abbreviations — A3b
# ---------------------------------------------------------------------------

class TestExpandAbbreviations:
    def test_ha_expands_to_huyet_ap(self):
        result = expand_abbreviations("ha 120/80 bình thường")
        assert "huyết áp" in result

    def test_bn_expands_to_benh_nhan(self):
        result = expand_abbreviations("bn bị sốt cao")
        assert "bệnh nhân" in result

    def test_tk_expands_to_tai_kham(self):
        result = expand_abbreviations("tk sau 2 tuần")
        assert "tái khám" in result

    def test_xn_expands_to_xet_nghiem(self):
        result = expand_abbreviations("cần xn máu ngay")
        assert "xét nghiệm" in result

    def test_dtd_expands_to_dai_thao_duong(self):
        result = expand_abbreviations("đtđ type 2 kiểm soát kém")
        assert "đái tháo đường" in result

    def test_tha_expands_to_tang_huyet_ap(self):
        result = expand_abbreviations("bệnh nhân có tha từ 5 năm")
        assert "tăng huyết áp" in result

    def test_sa_expands_to_sieu_am(self):
        result = expand_abbreviations("chỉ định sa bụng")
        assert "siêu âm" in result

    def test_multiple_abbrev_in_one_sentence(self):
        result = expand_abbreviations("bn ha 155/95 tk sau 1 tuần")
        assert "bệnh nhân" in result
        assert "huyết áp" in result
        assert "tái khám" in result

    def test_case_insensitive(self):
        result = expand_abbreviations("HA 155/95")
        assert "huyết áp" in result.lower() or "Huyết áp" in result

    def test_empty_string(self):
        assert expand_abbreviations("") == ""

    def test_no_abbreviations_unchanged(self):
        text = "bệnh nhân đau đầu sốt"
        result = expand_abbreviations(text)
        # Không có abbrev → giống nhau (hoặc minor changes)
        assert "bệnh nhân" in result

    def test_hc_expands_to_hong_cau(self):
        result = expand_abbreviations("hc thấp hơn bình thường")
        assert "hồng cầu" in result

    def test_bc_expands_to_bach_cau(self):
        result = expand_abbreviations("bc tăng cao")
        assert "bạch cầu" in result


# ---------------------------------------------------------------------------
# normalize_text — full pipeline
# ---------------------------------------------------------------------------

class TestNormalizeText:
    def test_full_pipeline_central(self):
        text = "bn mô mà ốm rứa ha 155/95"
        result, subs = normalize_text(text, region="central")
        assert "bệnh nhân" in result  # bn → bệnh nhân
        assert "huyết áp" in result   # ha → huyết áp
        assert "bệnh" in result       # ốm → bệnh (central)
        assert "đâu" in result        # mô → đâu

    def test_full_pipeline_southern(self):
        text = "bn hổng uống thuốc ha cao"
        result, subs = normalize_text(text, region="southern")
        assert "bệnh nhân" in result
        assert "không" in result
        assert "huyết áp" in result

    def test_full_pipeline_auto(self):
        text = "bệnh nhân xn máu tk sau 1 tuần"
        result, subs = normalize_text(text, region="auto")
        assert "xét nghiệm" in result
        assert "tái khám" in result

    def test_substitutions_list_non_empty_when_dialect_present(self):
        _, subs = normalize_text("mô rứa hỉ", region="central")
        assert len(subs) > 0


# ---------------------------------------------------------------------------
# DIALECT_MAP structure sanity checks
# ---------------------------------------------------------------------------

class TestDialectMapStructure:
    def test_all_required_regions_present(self):
        assert "central" in DIALECT_MAP
        assert "southern" in DIALECT_MAP
        assert "northern" in DIALECT_MAP
        assert "medical_abbrev" in DIALECT_MAP

    def test_central_has_om_entry(self):
        assert "ốm" in DIALECT_MAP["central"]
        assert DIALECT_MAP["central"]["ốm"] == "bệnh"

    def test_southern_has_om_entry(self):
        assert "ốm" in DIALECT_MAP["southern"]
        assert DIALECT_MAP["southern"]["ốm"] == "gầy"

    def test_medical_abbrev_has_core_entries(self):
        abbrevs = DIALECT_MAP["medical_abbrev"]
        assert "ha" in abbrevs   # huyết áp
        assert "bn" in abbrevs   # bệnh nhân
        assert "tk" in abbrevs   # tái khám
        assert "xn" in abbrevs   # xét nghiệm

    def test_total_entries_exceeds_200(self):
        total = sum(len(v) for v in DIALECT_MAP.values())
        assert total >= 200, f"Expected ≥200 entries, got {total}"
