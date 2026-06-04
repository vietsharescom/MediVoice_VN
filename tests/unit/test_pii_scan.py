"""
test_pii_scan.py — Unit tests for L5 PII Scan
GAP-002 | SRS-L5-001, SRS-L5-002
ISO/IEC 42001:2023 Cl.6.1 + NĐ13/2023

Đảm bảo l5_pii_scan.py không bị break silently.
PII scan failure → dữ liệu nhạy cảm rò rỉ → vi phạm NĐ13/2023.
"""
import pytest
from src.core.l5_pii_scan import scan_text, scan_form_data, mask_pii


# ── CCCD (12 chữ số, bắt đầu 0) ─────────────────────────────────────────────

class TestCCCD:
    def test_detects_cccd_in_sentence(self):
        assert "CCCD" in scan_text("CCCD của bệnh nhân là 012345678901")

    def test_detects_cccd_standalone(self):
        assert "CCCD" in scan_text("012345678901")

    def test_does_not_flag_11_digits(self):
        # 11 chữ số không phải CCCD
        assert "CCCD" not in scan_text("12345678901")

    def test_does_not_flag_13_digits(self):
        assert "CCCD" not in scan_text("1234567890123")

    def test_does_not_flag_non_zero_start(self):
        # CCCD phải bắt đầu bằng 0
        assert "CCCD" not in scan_text("112345678901")


# ── CMND (9 chữ số) ──────────────────────────────────────────────────────────

class TestCMND:
    def test_detects_cmnd(self):
        assert "CMND" in scan_text("CMND: 123456789")

    def test_does_not_flag_8_digits(self):
        assert "CMND" not in scan_text("12345678")

    def test_does_not_flag_10_digits(self):
        assert "CMND" not in scan_text("1234567890")


# ── Số điện thoại VN ──────────────────────────────────────────────────────────

class TestSDT:
    def test_detects_viettel(self):
        assert "SDT" in scan_text("liên hệ 0901234567")

    def test_detects_mobifone(self):
        assert "SDT" in scan_text("SĐT: 0701234567")

    def test_detects_vinaphone(self):
        assert "SDT" in scan_text("0841234567")

    def test_does_not_flag_landline(self):
        # Số bàn Đà Nẵng bắt đầu 023 — không phải mobile
        assert "SDT" not in scan_text("0236123456")

    def test_does_not_flag_8_digit_number(self):
        assert "SDT" not in scan_text("01234567")


# ── BHYT (2 chữ cái + 13 số) ─────────────────────────────────────────────────

class TestBHYT:
    def test_detects_bhyt(self):
        assert "BHYT" in scan_text("Thẻ BHYT: BN1234567890123")

    def test_detects_bhyt_standalone(self):
        assert "BHYT" in scan_text("HC1234567890123")

    def test_does_not_flag_short(self):
        assert "BHYT" not in scan_text("BN123456789012")


# ── Email ─────────────────────────────────────────────────────────────────────

class TestEmail:
    def test_detects_email(self):
        assert "EMAIL" in scan_text("email: patient@gmail.com")

    def test_detects_vn_email(self):
        assert "EMAIL" in scan_text("nguyenvana@phongkham.vn")

    def test_does_not_flag_non_email(self):
        assert "EMAIL" not in scan_text("không có email")


# ── Multiple PII types ────────────────────────────────────────────────────────

class TestMultiplePII:
    def test_detects_multiple_types(self):
        text = "CCCD 012345678901 SĐT 0901234567 email test@test.com"
        result = scan_text(text)
        assert "CCCD" in result
        assert "SDT" in result
        assert "EMAIL" in result

    def test_empty_text_returns_empty(self):
        assert scan_text("") == []

    def test_clean_medical_text_no_pii(self):
        # Text khám bệnh bình thường không có PII
        text = "Bệnh nhân đau đầu sốt 38.5. Huyết áp 120/80. Kê Amoxicillin 500mg."
        result = scan_text(text)
        assert result == []


# ── scan_form_data ────────────────────────────────────────────────────────────

class TestScanFormData:
    def test_detects_pii_in_nested_dict(self):
        form = {
            "ten": "Nguyễn Văn A",
            "contact": {"sdt": "0901234567"},
            "chan_doan": "viêm họng",
        }
        result = scan_form_data(form)
        assert "SDT" in result

    def test_no_pii_in_clean_form(self):
        form = {
            "chan_doan": "Viêm họng cấp",
            "don_thuoc": ["Amoxicillin 500mg"],
            "tai_kham": "Sau 5 ngày",
        }
        result = scan_form_data(form)
        assert result == []

    def test_handles_none_values(self):
        form = {"field1": None, "field2": "text"}
        # Should not raise
        result = scan_form_data(form)
        assert isinstance(result, list)


# ── mask_pii ──────────────────────────────────────────────────────────────────

class TestMaskPII:
    def test_masks_cccd(self):
        text = "BN số CCCD: 012345678901 đến khám"
        masked = mask_pii(text)
        assert "012345678901" not in masked
        assert "[CCCD-MASKED]" in masked

    def test_masks_sdt(self):
        text = "SĐT: 0901234567"
        masked = mask_pii(text)
        assert "0901234567" not in masked
        assert "[SDT-MASKED]" in masked

    def test_masks_email(self):
        text = "email: test@gmail.com"
        masked = mask_pii(text)
        assert "test@gmail.com" not in masked
        assert "[EMAIL-MASKED]" in masked

    def test_masks_multiple(self):
        text = "012345678901 và 0901234567"
        masked = mask_pii(text)
        assert "012345678901" not in masked
        assert "0901234567" not in masked

    def test_preserves_non_pii_text(self):
        text = "Chẩn đoán: Viêm họng cấp"
        masked = mask_pii(text)
        assert masked == text  # unchanged
